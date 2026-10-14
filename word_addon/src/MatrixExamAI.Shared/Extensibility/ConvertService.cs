using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Text;
using System.Text.Json;
using System.Text.RegularExpressions;
using System.Threading;
using System.Threading.Tasks;
using MatrixExamAI.Shared.AI;
using MatrixExamAI.Shared.Models;

namespace MatrixExamAI.Shared.Extensibility
{
    /// <summary>
    /// Bản triển khai dịch vụ Convert Đề thi AI Vision: Chuyển đổi ảnh đề thi / clipboard / tài liệu
    /// thành các câu hỏi trắc nghiệm & tự luận chuẩn cấu trúc, giữ nguyên công thức LaTeX.
    /// </summary>
    public class ConvertService : IConvertService
    {
        private IGeminiClient? _geminiClient;

        public ConvertService(IGeminiClient? geminiClient = null)
        {
            _geminiClient = geminiClient;
        }

        private IGeminiClient EnsureGeminiClient()
        {
            if (_geminiClient != null) return _geminiClient;

            var client = new GeminiClient();
            try
            {
                string appData = System.IO.Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "MatrixExamAI");
                string configFile = System.IO.Path.Combine(appData, "config.json");
                if (System.IO.File.Exists(configFile))
                {
                    string json = System.IO.File.ReadAllText(configFile);
                    using var doc = JsonDocument.Parse(json);
                    var root = doc.RootElement;
                    if (root.TryGetProperty("apiKey", out var pKey) && !string.IsNullOrWhiteSpace(pKey.GetString()))
                    {
                        client.KeyPool.SetKeys(new[] { pKey.GetString()! });
                    }
                    if (root.TryGetProperty("model", out var pModel) && !string.IsNullOrWhiteSpace(pModel.GetString()))
                    {
                        client.DefaultModel = pModel.GetString()!;
                    }
                    if (root.TryGetProperty("nineRouterApiKey", out var p9R) && !string.IsNullOrWhiteSpace(p9R.GetString()))
                    {
                        client.Fallback.NineRouterApiKey = p9R.GetString();
                    }
                    if (root.TryGetProperty("openAiApiKey", out var pOai) && !string.IsNullOrWhiteSpace(pOai.GetString()))
                    {
                        client.Fallback.OpenAiApiKey = pOai.GetString();
                    }
                }

                if (client.KeyPool.TotalKeys == 0)
                {
                    string? envKey = Environment.GetEnvironmentVariable("GEMINI_API_KEY") 
                                  ?? Environment.GetEnvironmentVariable("GOOGLE_API_KEY");
                    if (!string.IsNullOrWhiteSpace(envKey))
                    {
                        client.KeyPool.AddKey(envKey!.Trim());
                    }
                }
            }
            catch { }

            _geminiClient = client;
            return client;
        }

        public async Task<ConvertResult> ConvertContentAsync(ConvertRequest request, CancellationToken cancellationToken = default)
        {
            if (request == null) throw new ArgumentNullException(nameof(request));

            var sw = Stopwatch.StartNew();

            bool hasImage = !string.IsNullOrWhiteSpace(request.ImageBase64);
            bool hasText = !string.IsNullOrWhiteSpace(request.RawInputText);

            if (!hasImage && !hasText)
            {
                return ConvertResult.Fail("Vui lòng dán ảnh đề thi (Ctrl+V) hoặc chọn file trước khi nhận diện.", sw.ElapsedMilliseconds);
            }

            string systemPrompt = BuildConvertPrompt(request.QtypeFilter, request.IncludeSolution);

            string userPrompt = hasText
                ? $"Nội dung văn bản đề thi cần nhận diện và chuẩn hóa:\n\n{request.RawInputText}"
                : "Hãy nhận diện toàn bộ đề thi / bài kiểm tra trong ảnh và trích xuất thành các khối câu hỏi chuẩn theo cấu trúc yêu cầu.";

            string model = !string.IsNullOrWhiteSpace(request.ModelOverride) ? request.ModelOverride! : "gemini-3.8-flash";

            var gemini = EnsureGeminiClient();

            if (gemini != null)
            {
                bool hasKeys = gemini.KeyPool == null || gemini.KeyPool.TotalKeys > 0 || (gemini.Fallback != null && gemini.Fallback.HasConfiguredFallback());
                if (hasKeys)
                {
                    try
                    {
                        var tikzReq = new TikzPromptRequest
                        {
                            Prompt = $"{systemPrompt}\n\n{userPrompt}",
                            DiagramType = DiagramType.Custom,
                            ModelOverride = model,
                            ImageBase64 = hasImage ? request.ImageBase64 : null,
                            ImageMimeType = (hasImage && !string.IsNullOrEmpty(request.ImageMimeType)) ? request.ImageMimeType! : "image/png"
                        };

                        var genResult = await gemini.GenerateTikzAsync(tikzReq, cancellationToken).ConfigureAwait(false);
                        sw.Stop();

                        if (genResult.Success && !string.IsNullOrWhiteSpace(genResult.RawResponse))
                        {
                            string rawResponse = genResult.RawResponse;
                            var parseData = ParseExtractedQuestions(rawResponse);

                            return ConvertResult.Ok(
                                questions: parseData.Questions,
                                formattedDocText: parseData.FormattedDocText,
                                rawAiResponse: rawResponse,
                                subject: parseData.Subject,
                                grade: parseData.Grade,
                                topic: parseData.Topic,
                                modelUsed: genResult.ModelUsed,
                                latencyMs: sw.ElapsedMilliseconds
                            );
                        }
                        else
                        {
                            string err = genResult.ErrorMessage ?? "Không nhận được phản hồi từ AI Vision.";
                            return ConvertResult.Fail(err, sw.ElapsedMilliseconds);
                        }
                    }
                    catch (Exception ex)
                    {
                        sw.Stop();
                        return ConvertResult.Fail($"Lỗi trong quá trình nhận diện AI: {ex.Message}", sw.ElapsedMilliseconds);
                    }
                }
            }

            // Fallback nếu chưa cấu hình API Key
            sw.Stop();
            return ConvertResult.Fail("Chưa cấu hình API Key. Vui lòng bấm biểu tượng Cài đặt (⚙️) ở góc trên bên phải để nhập API Key Google Gemini hoặc 9Router.", sw.ElapsedMilliseconds);
        }

        /// <summary>
        /// Phân tích trực tiếp văn bản thô / LaTeX ex_test / Natural format (không tốn lượt gọi AI).
        /// </summary>
        public ConvertResult ParseTextDirectly(string rawText, string subject = "Toán", int grade = 12)
        {
            if (string.IsNullOrWhiteSpace(rawText))
            {
                return ConvertResult.Fail("Văn bản câu hỏi đang rỗng. Vui lòng dán văn bản hoặc tải file trước khi nhận diện.");
            }

            // Loại bỏ các thẻ citation [cite: ...]
            string cleaned = Regex.Replace(rawText, @"\[cite[a-z]*:\s*[\d,\s]+\]", "", RegexOptions.IgnoreCase);
            cleaned = Regex.Replace(cleaned, @"\[source:\s*[^\]]+\]", "", RegexOptions.IgnoreCase);

            var sw = Stopwatch.StartNew();

            // Tầng 1: Cấu trúc app ===CAU=== ... ===KETCAU===
            if (cleaned.Contains("===CAU==="))
            {
                var parsed = ParseExtractedQuestions(cleaned);
                if (parsed.Questions.Count > 0)
                {
                    sw.Stop();
                    return ConvertResult.Ok(
                        parsed.Questions,
                        parsed.FormattedDocText,
                        cleaned,
                        parsed.Subject,
                        parsed.Grade,
                        parsed.Topic,
                        "Local Parser (Structured)",
                        sw.ElapsedMilliseconds);
                }
            }

            // Tầng 2: LaTeX ex_test (\begin{ex} / \begin{bt} / \begin{vd})
            if (Regex.IsMatch(cleaned, @"\\begin\{(?:ex|bt|vd)\}"))
            {
                var latexData = ParseLatexQuestions(cleaned, subject, grade);
                if (latexData.Questions.Count > 0)
                {
                    sw.Stop();
                    return ConvertResult.Ok(
                        latexData.Questions,
                        latexData.FormattedDocText,
                        cleaned,
                        subject,
                        grade,
                        latexData.Topic,
                        "Local Parser (LaTeX ex_test)",
                        sw.ElapsedMilliseconds);
                }
            }

            // Tầng 3: Natural Parser (Câu 1:, Câu 2:, Bài 1: ...)
            if (Regex.IsMatch(cleaned, @"(?m)^(?:Câu|Bài)\s*\d+[:.]"))
            {
                var naturalData = ParseNaturalQuestions(cleaned, subject, grade);
                if (naturalData.Questions.Count > 0)
                {
                    sw.Stop();
                    return ConvertResult.Ok(
                        naturalData.Questions,
                        naturalData.FormattedDocText,
                        cleaned,
                        subject,
                        grade,
                        naturalData.Topic,
                        "Local Parser (Natural Text)",
                        sw.ElapsedMilliseconds);
                }
            }

            sw.Stop();
            return ConvertResult.Fail("Không nhận diện được cấu trúc câu hỏi nào (chưa có ===CAU===, \\begin{ex} hoặc Câu N: A. B. C. D.). Bạn có thể bấm '🤖 Gọi AI ngay' để đồng bộ.", sw.ElapsedMilliseconds);
        }

        /// <summary>
        /// Lấy mẫu prompt chuẩn để người dùng sao chép gửi cho ChatGPT / Claude / Gemini bên ngoài.
        /// </summary>
        public string GetChatbotPromptTemplate(string subject = "Toán", int grade = 12, string topic = "")
        {
            if (string.IsNullOrWhiteSpace(topic)) topic = $"{subject} lớp {grade}";

            return $@"Bạn là AI chuyên gia biên soạn đề {subject} THPT Việt Nam, 10+ năm kinh nghiệm.
Hãy tạo BỘ CÂU HỎI theo YÊU CẦU bên dưới và tuân thủ TUYỆT ĐỐI cấu trúc app.

════════════════════════════════════════════════════════════════
[★] YÊU CẦU CỦA TÔI — BẠN ĐỌC KỸ TRƯỚC KHI LÀM
════════════════════════════════════════════════════════════════
• Môn:     [{subject}]
• Lớp:     [{grade}]
• Chủ đề:  [{topic}]

CƠ CẤU CÂU HỎI (điền số câu mỗi loại; để 0 nếu không cần):
• TN  — Trắc nghiệm 4 phương án A/B/C/D :  [10] câu
• DS  — Đúng/Sai 4 ý a/b/c/d            :  [2] câu
• TLN — Trả lời ngắn (đáp án là 1 số)   :  [2] câu
• TL  — Tự luận trình bày các bước       :  [0] câu
→ TỔNG CỘNG: [14] câu

PHÂN BỔ MỨC ĐỘ (% hoặc số câu — tổng = 100%):
• NB (Nhận biết)  : [40%]
• TH (Thông hiểu) : [40%]
• VD (Vận dụng)   : [20%]

════════════════════════════════════════════════════════════════
QUY TẮC BẮT BUỘC — KHÔNG ĐƯỢC VI PHẠM
════════════════════════════════════════════════════════════════
[1] CÔNG THỨC TOÁN:
- Luôn bọc trong $...$ hoặc ${{...}}$, ví dụ: $y = x^3 - 3x + 1$, $\frac{{a}}{{b}}$, $\sqrt{{x}}$.
- Tuyệt đối không dùng Unicode toán học (x², √, ≠, ≤, ≥).

[2] ĐỊNH DẠNG XUẤT CÂU HỎI (CHUẨN APP):
Mỗi câu hỏi PHẢI nằm trong khối:
===CAU===
LOAI: TN (hoặc DS, TLN, TL)
MUCDO: NB (hoặc TH, VD, VDC)
CHUONG: Tên chương/chủ đề
NOIDUNG: Nội dung câu hỏi...
A. Phương án A (nếu là TN)
B. Phương án B
C. Phương án C
D. Phương án D
DAPAN: A (hoặc a=Đ, b=S, c=Đ, d=S nếu là DS; hoặc 1 số nếu là TLN)
LOIGIAI: Lời giải chi tiết...
===KETCAU===";
        }

        private static ParsedConvertData ParseNaturalQuestions(string text, string subject, int grade)
        {
            var data = new ParsedConvertData
            {
                Subject = subject,
                Grade = grade,
                Topic = $"{subject} {grade}"
            };

            var questionMatches = Regex.Matches(text, @"(?m)^(?:Câu|Bài)\s*(\d+)[:.]\s*");
            if (questionMatches.Count == 0) return data;

            var blocks = new List<string>();
            for (int i = 0; i < questionMatches.Count; i++)
            {
                int startIndex = questionMatches[i].Index;
                int endIndex = (i + 1 < questionMatches.Count) ? questionMatches[i + 1].Index : text.Length;
                blocks.Add(text.Substring(startIndex, endIndex - startIndex).Trim());
            }

            var docTextBuilder = new StringBuilder();
            int questionIndex = 1;

            foreach (var block in blocks)
            {
                var item = new QuestionItem
                {
                    Subject = subject,
                    Grade = grade,
                    Topic = data.Topic,
                    QuestionCode = $"NAT_{grade}_{questionIndex:D2}",
                    QuestionType = "MultipleChoice4",
                    CognitiveLevel = "Thông hiểu"
                };

                var lines = block.Split(new[] { "\r\n", "\r", "\n" }, StringSplitOptions.None);
                var contentLines = new List<string>();
                var solutionLines = new List<string>();
                bool inSolution = false;

                foreach (var line in lines)
                {
                    string trimmed = line.Trim();

                    var ansMatch = Regex.Match(trimmed, @"^(?:[-=>*•\s]*)(?:Đáp án|ĐA|Đ/A|Answer)[:\s]+(.*)$", RegexOptions.IgnoreCase);
                    if (ansMatch.Success)
                    {
                        item.CorrectAnswer = ansMatch.Groups[1].Value.Trim();
                        continue;
                    }

                    var solMatch = Regex.Match(trimmed, @"^(?:Lời giải|Giải|Hướng dẫn giải|Hướng dẫn)[:\s]*(.*)$", RegexOptions.IgnoreCase);
                    if (solMatch.Success)
                    {
                        inSolution = true;
                        if (!string.IsNullOrWhiteSpace(solMatch.Groups[1].Value))
                            solutionLines.Add(solMatch.Groups[1].Value.Trim());
                        continue;
                    }

                    if (inSolution)
                    {
                        solutionLines.Add(line);
                        continue;
                    }

                    var optMatch = Regex.Match(trimmed, @"^([A-D])[.:\)]\s*(.*)$");
                    if (optMatch.Success)
                    {
                        string k = optMatch.Groups[1].Value.ToUpperInvariant();
                        string v = optMatch.Groups[2].Value.Trim();
                        item.Options[k] = v;
                        continue;
                    }

                    var tfMatch = Regex.Match(trimmed, @"^([a-d])[.:\)]\s*(.*)$");
                    if (tfMatch.Success)
                    {
                        item.QuestionType = "TrueFalse4";
                        string k = tfMatch.Groups[1].Value.ToLowerInvariant();
                        string v = tfMatch.Groups[2].Value.Trim();
                        item.Options[k] = v;
                        continue;
                    }

                    if (contentLines.Count == 0 && Regex.IsMatch(trimmed, @"^(?:Câu|Bài)\s*\d+[:.]\s*$"))
                    {
                        continue;
                    }

                    if (contentLines.Count == 0)
                    {
                        string strippedHeader = Regex.Replace(trimmed, @"^(?:Câu|Bài)\s*\d+[:.]\s*", "");
                        contentLines.Add(strippedHeader);
                        continue;
                    }

                    contentLines.Add(line);
                }

                item.Content = string.Join("\n", contentLines).Trim();
                item.Explanation = string.Join("\n", solutionLines).Trim();

                if (item.Options.Count == 0 && !string.IsNullOrWhiteSpace(item.CorrectAnswer))
                {
                    if (Regex.IsMatch(item.CorrectAnswer, @"^[\d\.,\-\+/]+$"))
                    {
                        item.QuestionType = "ShortAnswer";
                    }
                }

                data.Questions.Add(item);

                docTextBuilder.AppendLine($"Câu {questionIndex}. {item.Content}");
                if (item.Options.Count > 0)
                {
                    foreach (var kvp in item.Options)
                    {
                        docTextBuilder.AppendLine($"{kvp.Key}. {kvp.Value}");
                    }
                }
                if (!string.IsNullOrWhiteSpace(item.CorrectAnswer))
                {
                    docTextBuilder.AppendLine($"-> Đáp án: {item.CorrectAnswer}");
                }
                if (!string.IsNullOrWhiteSpace(item.Explanation))
                {
                    docTextBuilder.AppendLine($"Lời giải:\n{item.Explanation}");
                }
                docTextBuilder.AppendLine();

                questionIndex++;
            }

            data.FormattedDocText = QuestionParserEngine.FormatWordReadyText(data.Questions);
            return data;
        }

        private static ParsedConvertData ParseLatexQuestions(string text, string subject, int grade)
        {
            var data = new ParsedConvertData
            {
                Subject = subject,
                Grade = grade,
                Topic = $"{subject} {grade}"
            };

            var exMatches = Regex.Matches(text, @"\\begin\{(ex|bt|vd)\}([\s\S]*?)\\end\{\1\}");
            if (exMatches.Count == 0) return data;

            var docTextBuilder = new StringBuilder();
            int questionIndex = 1;

            foreach (Match m in exMatches)
            {
                string tag = m.Groups[1].Value;
                string body = m.Groups[2].Value.Trim();

                var item = new QuestionItem
                {
                    Subject = subject,
                    Grade = grade,
                    Topic = data.Topic,
                    QuestionCode = $"TEX_{grade}_{questionIndex:D2}",
                    QuestionType = tag == "bt" ? "Essay" : "MultipleChoice4",
                    CognitiveLevel = "Thông hiểu"
                };

                var loigiaiMatch = Regex.Match(body, @"\\loigiai\s*(?:\[[^\]]*\])?\s*\{");
                if (loigiaiMatch.Success)
                {
                    int openPos = body.IndexOf('{', loigiaiMatch.Index);
                    if (openPos >= 0)
                    {
                        item.Explanation = QuestionParserEngine.ExtractBraceContent(body, openPos).Trim();
                        int closePos = QuestionParserEngine.FindMatchingBrace(body, openPos);
                        string before = body.Substring(0, loigiaiMatch.Index).Trim();
                        string after = (closePos >= 0 && closePos + 1 < body.Length) ? body.Substring(closePos + 1).Trim() : "";
                        body = (before + " " + after).Trim();
                    }
                }

                var choiceMatch = Regex.Match(body, @"\\choice\b\s*");
                if (choiceMatch.Success)
                {
                    item.QuestionType = "MultipleChoice4";
                    int startIdx = choiceMatch.Index + choiceMatch.Length;
                    var opts = QuestionParserEngine.ExtractBraceGroups(body, startIdx, 4);
                    string[] keys = new[] { "A", "B", "C", "D" };

                    for (int i = 0; i < opts.Count && i < 4; i++)
                    {
                        string optText = opts[i].Trim();
                        if (optText.Contains(@"\True"))
                        {
                            item.CorrectAnswer = keys[i];
                            optText = optText.Replace(@"\True", "").Trim();
                        }
                        item.Options[keys[i]] = optText;
                    }

                    body = body.Substring(0, choiceMatch.Index).Trim();
                }

                var choiceTfMatch = Regex.Match(body, @"\\choiceTF\b\s*");
                if (choiceTfMatch.Success)
                {
                    item.QuestionType = "TrueFalse4";
                    int startIdx = choiceTfMatch.Index + choiceTfMatch.Length;
                    var opts = QuestionParserEngine.ExtractBraceGroups(body, startIdx, 4);
                    string[] keys = new[] { "a", "b", "c", "d" };
                    var tfAnswers = new List<string>();

                    for (int i = 0; i < opts.Count && i < 4; i++)
                    {
                        string optText = opts[i].Trim();
                        bool isTrue = optText.Contains(@"\True");
                        optText = optText.Replace(@"\True", "").Trim();
                        item.Options[keys[i]] = optText;
                        tfAnswers.Add($"{keys[i]}={(isTrue ? "Đ" : "S")}");
                    }
                    item.CorrectAnswer = string.Join(", ", tfAnswers);
                    body = body.Substring(0, choiceTfMatch.Index).Trim();
                }

                var shortansMatch = Regex.Match(body, @"\\shortans\s*(?:\[[^\]]*\])?\s*\{");
                if (shortansMatch.Success)
                {
                    int openPos = body.IndexOf('{', shortansMatch.Index);
                    if (openPos >= 0)
                    {
                        item.QuestionType = "ShortAnswer";
                        item.CorrectAnswer = QuestionParserEngine.ExtractBraceContent(body, openPos).Trim();
                        body = body.Substring(0, shortansMatch.Index).Trim();
                    }
                }

                item.Content = body;
                data.Questions.Add(item);

                questionIndex++;
            }

            data.FormattedDocText = QuestionParserEngine.FormatWordReadyText(data.Questions);
            return data;
        }

        #region Prompt Construction

        private static string BuildConvertPrompt(string qtypeFilter, bool includeSolution)
        {
            var sb = new StringBuilder();

            sb.AppendLine("Bạn là trợ lý OCR AI chuyên nghiệp xử lý đề thi / bài kiểm tra Toán THPT Việt Nam (chuẩn Bộ Giáo dục & Đào tạo).");
            sb.AppendLine("NHIỆM VỤ: Nhận diện ảnh đề thi và chuyển thành các khối câu hỏi chuẩn cấu trúc.");
            sb.AppendLine();
            sb.AppendLine("════════════════════════════════════════════════════════════════════════");
            sb.AppendLine("[1] NGUYÊN TẮC QUAN TRỌNG VỀ CÔNG THỨC TOÁN HỌC:");
            sb.AppendLine("════════════════════════════════════════════════════════════════════════");
            sb.AppendLine("- TẤT CẢ công thức toán học PHẢI được giữ nguyên dưới dạng LaTeX chuẩn: $...$ hoặc ${...}$.");
            sb.AppendLine("- TUYỆT ĐỐI KHÔNG chuyển đổi công thức sang Equation Word hay MathType, chỉ dùng LaTeX text.");
            sb.AppendLine("- Nhận diện chính xác từng ký tự tiếng Việt có dấu đầy đủ.");
            sb.AppendLine("- Giữ NGUYÊN đánh số thứ tự câu, các phương án A, B, C, D hoặc a, b, c, d.");
            sb.AppendLine("- Nếu câu có hình ảnh / đồ thị / bảng biến thiên trong đề, chèn marker [HÌNH: <mô tả chi tiết bằng tiếng Việt>] vào đúng vị trí nội dung.");
            sb.AppendLine();

            if (qtypeFilter == "TN")
            {
                sb.AppendLine("[!] CHẾ ĐỘ ÉP LOẠI - TRẮC NGHIỆM 4 LỰA CHỌN (TN): Tất cả câu hỏi đều có 4 phương án A, B, C, D.");
            }
            else if (qtypeFilter == "DS")
            {
                sb.AppendLine("[!] CHẾ ĐỘ ÉP LOẠI - ĐÚNG / SAI (DS): Tất cả câu hỏi đều có 4 mệnh đề a, b, c, d.");
            }
            else if (qtypeFilter == "TLN")
            {
                sb.AppendLine("[!] CHẾ ĐỘ ÉP LOẠI - TRẢ LỜI NGẮN (TLN): Đáp án là một số nguyên hoặc số thập phân.");
            }
            else if (qtypeFilter == "TL")
            {
                sb.AppendLine("[!] CHẾ ĐỘ ÉP LOẠI - TỰ LUẬN (TL): Yêu cầu trình bày các bước giải toán.");
            }

            sb.AppendLine();
            sb.AppendLine("════════════════════════════════════════════════════════════════════════");
            sb.AppendLine("[2] ĐỊNH DẠNG ĐẦU RA BẮT BUỘC:");
            sb.AppendLine("════════════════════════════════════════════════════════════════════════");
            sb.AppendLine("1. Dòng đầu tiên xuất META dạng JSON:");
            sb.AppendLine("META: {\"subject\": \"Toán\", \"grade\": \"12\", \"topic\": \"Chủ đề chính\"}");
            sb.AppendLine();
            sb.AppendLine("2. Mỗi câu hỏi bọc trong cặp thẻ ===CAU=== và ===KETCAU===:");
            sb.AppendLine("===CAU===");
            sb.AppendLine("LOAI: TN | DS | TLN | TL");
            sb.AppendLine("MUCDO: NB | TH | VD | VDC");
            sb.AppendLine("CHUONG: Tên chuyên đề kiến thức");
            sb.AppendLine("NOIDUNG: Nội dung câu hỏi (chứa công thức toán dạng $...$)");
            sb.AppendLine("A: Phương án A (nếu là TN)");
            sb.AppendLine("B: Phương án B (nếu là TN)");
            sb.AppendLine("C: Phương án C (nếu là TN)");
            sb.AppendLine("D: Phương án D (nếu là TN)");
            sb.AppendLine("a: Mệnh đề a (nếu là DS)");
            sb.AppendLine("b: Mệnh đề b (nếu là DS)");
            sb.AppendLine("c: Mệnh đề c (nếu là DS)");
            sb.AppendLine("d: Mệnh đề d (nếu là DS)");
            sb.AppendLine("DAPAN: Đáp án đúng (vd: A hoặc a:Đ, b:S, c:Đ, d:S hoặc giá trị số)");
            if (includeSolution)
            {
                sb.AppendLine("LOIGIAI: Lời giải chi tiết từng bước (nếu trong ảnh có hoặc tự động suy luận giải ngắn gọn)");
            }
            sb.AppendLine("===KETCAU===");

            return sb.ToString();
        }

        #endregion

        #region Output Parsing

        public class ParsedConvertData
        {
            public string Subject { get; set; } = "Toán";
            public int Grade { get; set; } = 12;
            public string Topic { get; set; } = string.Empty;
            public List<QuestionItem> Questions { get; set; } = new List<QuestionItem>();
            public string FormattedDocText { get; set; } = string.Empty;
        }

        public static ParsedConvertData ParseExtractedQuestions(string rawResponse)
        {
            var data = new ParsedConvertData();
            if (string.IsNullOrWhiteSpace(rawResponse)) return data;

            // 1. Phân tích META
            var metaMatch = Regex.Match(rawResponse, @"META:\s*(\{[^\r\n]+\})", RegexOptions.IgnoreCase);
            if (metaMatch.Success)
            {
                try
                {
                    using var doc = JsonDocument.Parse(metaMatch.Groups[1].Value);
                    var root = doc.RootElement;
                    if (root.TryGetProperty("subject", out var pSub) && !string.IsNullOrWhiteSpace(pSub.GetString()))
                        data.Subject = pSub.GetString()!;
                    if (root.TryGetProperty("grade", out var pG))
                    {
                        if (pG.ValueKind == JsonValueKind.Number && pG.TryGetInt32(out int gVal))
                            data.Grade = gVal;
                        else if (pG.ValueKind == JsonValueKind.String && int.TryParse(pG.GetString(), out int gsVal))
                            data.Grade = gsVal;
                    }
                    if (root.TryGetProperty("topic", out var pTop) && !string.IsNullOrWhiteSpace(pTop.GetString()))
                        data.Topic = pTop.GetString()!;
                }
                catch
                {
                    // Ignore JSON parse errors in meta
                }
            }

            // 2. Phân tích từng khối ===CAU=== ... ===KETCAU===
            var blockMatches = Regex.Matches(rawResponse, @"===CAU===([\s\S]*?)===KETCAU===", RegexOptions.IgnoreCase);
            var docTextBuilder = new StringBuilder();
            int questionIndex = 1;

            foreach (Match block in blockMatches)
            {
                string blockContent = block.Groups[1].Value.Trim();
                if (string.IsNullOrWhiteSpace(blockContent)) continue;

                var item = new QuestionItem
                {
                    Subject = data.Subject,
                    Grade = data.Grade,
                    Topic = data.Topic,
                    QuestionCode = $"CV_{data.Grade}_{questionIndex:D2}"
                };

                // Phân tích các dòng trong khối
                string[] lines = blockContent.Split(new[] { "\r\n", "\r", "\n" }, StringSplitOptions.None);
                string currentKey = "";
                var contentLines = new List<string>();
                var solutionLines = new List<string>();

                foreach (var line in lines)
                {
                    string trimmed = line.Trim();

                    if (trimmed.StartsWith("LOAI:", StringComparison.OrdinalIgnoreCase))
                    {
                        currentKey = "LOAI";
                        string val = trimmed.Substring(5).Trim();
                        item.QuestionType = MapQuestionType(val);
                    }
                    else if (trimmed.StartsWith("MUCDO:", StringComparison.OrdinalIgnoreCase))
                    {
                        currentKey = "MUCDO";
                        string val = trimmed.Substring(6).Trim();
                        item.CognitiveLevel = MapCognitiveLevel(val);
                    }
                    else if (trimmed.StartsWith("CHUONG:", StringComparison.OrdinalIgnoreCase))
                    {
                        currentKey = "CHUONG";
                        string val = trimmed.Substring(7).Trim();
                        if (!string.IsNullOrWhiteSpace(val)) item.Topic = val;
                    }
                    else if (trimmed.StartsWith("NOIDUNG:", StringComparison.OrdinalIgnoreCase))
                    {
                        currentKey = "NOIDUNG";
                        contentLines.Add(trimmed.Substring(8).Trim());
                    }
                    else if (Regex.IsMatch(trimmed, @"^[A-D][.:\)]\s*"))
                    {
                        currentKey = "OPT";
                        string optKey = trimmed.Substring(0, 1).ToUpperInvariant();
                        string optVal = trimmed.Substring(2).Trim();
                        item.Options[optKey] = optVal;
                    }
                    else if (Regex.IsMatch(trimmed, @"^[a-d][.:\)]\s*"))
                    {
                        currentKey = "TF_OPT";
                        string optKey = trimmed.Substring(0, 1).ToLowerInvariant();
                        string optVal = trimmed.Substring(2).Trim();
                        item.Options[optKey] = optVal;
                    }
                    else if (trimmed.StartsWith("DAPAN:", StringComparison.OrdinalIgnoreCase))
                    {
                        currentKey = "DAPAN";
                        item.CorrectAnswer = trimmed.Substring(6).Trim();
                    }
                    else if (trimmed.StartsWith("LOIGIAI:", StringComparison.OrdinalIgnoreCase))
                    {
                        currentKey = "LOIGIAI";
                        solutionLines.Add(trimmed.Substring(8).Trim());
                    }
                    else
                    {
                        // Dòng nối dài
                        if (currentKey == "NOIDUNG") contentLines.Add(line);
                        else if (currentKey == "LOIGIAI") solutionLines.Add(line);
                    }
                }

                item.Content = string.Join("\n", contentLines).Trim();
                item.Explanation = string.Join("\n", solutionLines).Trim();

                data.Questions.Add(item);

                // Tạo định dạng văn bản chuẩn Word
                docTextBuilder.AppendLine($"Câu {questionIndex}. {item.Content}");

                if (item.Options.Count > 0)
                {
                    foreach (var kvp in item.Options)
                    {
                        docTextBuilder.AppendLine($"{kvp.Key}. {kvp.Value}");
                    }
                }

                if (!string.IsNullOrWhiteSpace(item.CorrectAnswer))
                {
                    docTextBuilder.AppendLine($"-> Đáp án: {item.CorrectAnswer}");
                }

                if (!string.IsNullOrWhiteSpace(item.Explanation))
                {
                    docTextBuilder.AppendLine($"Lời giải:\n{item.Explanation}");
                }

                docTextBuilder.AppendLine();
                questionIndex++;
            }

            // Nếu không tìm thấy khối ===CAU=== nào (AI trả về dạng text tự do)
            if (data.Questions.Count == 0)
            {
                data.FormattedDocText = rawResponse.Trim();
            }
            else
            {
                data.FormattedDocText = QuestionParserEngine.FormatWordReadyText(data.Questions);
            }

            return data;
        }

        private static string MapQuestionType(string raw)
        {
            raw = raw.Trim().ToUpperInvariant();
            if (raw == "TN" || raw.Contains("CHOICE") || raw.Contains("TRAC")) return "MultipleChoice4";
            if (raw == "DS" || raw.Contains("TRUE") || raw.Contains("DUNG")) return "TrueFalse4";
            if (raw == "TLN" || raw.Contains("SHORT") || raw.Contains("NGAN")) return "ShortAnswer";
            if (raw == "TL" || raw.Contains("ESSAY") || raw.Contains("LUAN")) return "Essay";
            return "MultipleChoice4";
        }

        private static string MapCognitiveLevel(string raw)
        {
            raw = raw.Trim().ToUpperInvariant();
            if (raw == "NB" || raw.Contains("BIET")) return "Nhận biết";
            if (raw == "TH" || raw.Contains("HIEU")) return "Thông hiểu";
            if (raw == "VD" || raw.Contains("DUNG")) return "Vận dụng";
            if (raw == "VDC" || raw.Contains("CAO")) return "Vận dụng cao";
            return "Thông hiểu";
        }

        #endregion
    }
}
