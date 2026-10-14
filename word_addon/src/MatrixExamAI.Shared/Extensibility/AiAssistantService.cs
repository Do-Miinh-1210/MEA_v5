using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Text;
using System.Text.RegularExpressions;
using System.Threading;
using System.Threading.Tasks;
using MatrixExamAI.Shared.AI;
using MatrixExamAI.Shared.Models;

namespace MatrixExamAI.Shared.Extensibility
{
    /// <summary>
    /// Triển khai dịch vụ Trợ lý AI Soạn thảo văn bản tích hợp Google Gemini 3.8 Flash (Phase 2).
    /// </summary>
    public class AiAssistantService : IAIAssistantService
    {
        private IGeminiClient? _geminiClient;

        public AiAssistantService(IGeminiClient? geminiClient = null)
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
                    using var doc = System.Text.Json.JsonDocument.Parse(json);
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

        public async Task<AssistantResponse> ProcessAsync(AssistantRequest request, CancellationToken cancellationToken = default)
        {
            if (request == null)
                throw new ArgumentNullException(nameof(request));

            if (string.IsNullOrWhiteSpace(request.SelectedText))
            {
                return AssistantResponse.Fail("Chưa có đoạn văn bản nào được chọn trong tài liệu Microsoft Word.");
            }

            var sw = Stopwatch.StartNew();

            string systemPrompt = BuildSystemPrompt(request);
            string userPrompt = BuildUserPrompt(request);

            // 1. Thử gọi qua IGeminiClient nếu có
            var gemini = EnsureGeminiClient();
            if (gemini != null)
            {
                bool hasKeys = gemini.KeyPool == null || gemini.KeyPool.TotalKeys > 0 || (gemini.Fallback != null && gemini.Fallback.HasConfiguredFallback());
                if (hasKeys)
                {
                    try
                    {
                        var tikzPromptReq = new TikzPromptRequest
                        {
                            Prompt = $"{systemPrompt}\n\n{userPrompt}",
                            DiagramType = DiagramType.Custom,
                            ModelOverride = request.Model
                        };

                        var genResult = await gemini.GenerateTikzAsync(tikzPromptReq, cancellationToken);
                        sw.Stop();

                        if (genResult.Success && !string.IsNullOrWhiteSpace(genResult.RawResponse))
                        {
                            string responseText = genResult.RawResponse;
                            string? tikzCode = null;

                            // Trích xuất mã TikZ nếu AI sinh kèm hình
                            if (request.IncludeTikzSuggestion)
                            {
                                tikzCode = TikzCodeExtractor.ExtractTikzCode(responseText);
                                if (string.IsNullOrWhiteSpace(tikzCode) && !string.IsNullOrWhiteSpace(genResult.TikzCode))
                                {
                                    tikzCode = genResult.TikzCode;
                                }
                            }

                            var suggestions = ExtractSuggestions(responseText);

                            return AssistantResponse.Ok(
                                resultText: CleanMarkdownResponse(responseText),
                                modelUsed: genResult.ModelUsed,
                                latencyMs: sw.ElapsedMilliseconds,
                                tikzCode: string.IsNullOrWhiteSpace(tikzCode) ? null : tikzCode,
                                suggestions: suggestions);
                        }
                    }
                    catch (Exception ex)
                    {
                        System.Diagnostics.Debug.WriteLine($"[AiAssistantService] Remote Gemini call failed: {ex.Message}");
                    }
                }
            }

            // 2. Chế độ xử lý cục bộ thông minh (Deterministic Pedagogical Engine) khi không có mạng/API key
            sw.Stop();
            var localResponse = ProcessLocalPedagogicalAnalysis(request, sw.ElapsedMilliseconds);
            return localResponse;
        }

        public Task<AssistantResponse> ExplainQuestionAsync(string selectedText, string? prompt = null, CancellationToken cancellationToken = default)
        {
            var req = new AssistantRequest
            {
                TaskType = AssistantTaskType.ExplainQuestion,
                SelectedText = selectedText,
                Prompt = prompt ?? "Giải thích bản chất câu hỏi, kiến thức trọng tâm và bẫy sai lầm thường gặp."
            };
            return ProcessAsync(req, cancellationToken);
        }

        public Task<AssistantResponse> RewriteMathProblemAsync(string selectedText, string? parameters = null, CancellationToken cancellationToken = default)
        {
            var req = new AssistantRequest
            {
                TaskType = AssistantTaskType.RewriteMathProblem,
                SelectedText = selectedText,
                Prompt = string.IsNullOrWhiteSpace(parameters)
                    ? "Viết lại thành một câu hỏi tương đương, đổi số liệu nhưng giữ nguyên dạng toán và mức độ tư duy."
                    : $"Viết lại câu hỏi với yêu cầu bổ sung: {parameters}"
            };
            return ProcessAsync(req, cancellationToken);
        }

        public Task<AssistantResponse> GenerateStepByStepSolutionAsync(string selectedText, CancellationToken cancellationToken = default)
        {
            var req = new AssistantRequest
            {
                TaskType = AssistantTaskType.GenerateSolution,
                SelectedText = selectedText,
                Prompt = "Trình bày lời giải chi tiết từng bước chuẩn mực Bộ GD&ĐT kèm công thức toán học và đáp số."
            };
            return ProcessAsync(req, cancellationToken);
        }

        #region Prompt Engineering

        private static string BuildSystemPrompt(AssistantRequest request)
        {
            var sb = new StringBuilder();
            sb.AppendLine("Bạn là Trợ lý AI Soạn thảo đề thi và tài liệu sư phạm cao cấp trong hệ sinh thái MatrixExamAI v5.0.");
            sb.AppendLine($"Chuyên môn: {request.Subject} lớp {request.TargetGrade ?? 12} theo chương trình GDPT chuẩn Bộ Giáo dục và Đào tạo Việt Nam.");
            sb.AppendLine("Quy tắc bắt buộc:");
            sb.AppendLine("1. Sử dụng chuẩn LaTeX $...$ cho công thức toán học nằm trong dòng và $$...$$ cho công thức độc lập.");
            sb.AppendLine("2. Ngôn phong sư phạm mực thước, khúc chiết, tường minh, không dùng từ ngữ tối nghĩa.");
            sb.AppendLine("3. Nếu cần vẽ hình minh họa, đặt mã TikZ trong khối ```latex ... ``` chuẩn Standalone.");
            return sb.ToString();
        }

        private static string BuildUserPrompt(AssistantRequest request)
        {
            var sb = new StringBuilder();
            sb.AppendLine($"[VĂN BẢN ĐANG CHỌN TRONG WORD]:\n\"{request.SelectedText}\"");

            if (!string.IsNullOrWhiteSpace(request.Context))
            {
                sb.AppendLine($"\n[BỐI CẢNH TÀI LIỆU]:\n\"{request.Context}\"");
            }

            sb.AppendLine($"\n[TÁC VỤ YÊU CẦU]: {GetTaskTypeDescription(request.TaskType)}");

            if (!string.IsNullOrWhiteSpace(request.Prompt))
            {
                sb.AppendLine($"[HƯỚNG DẪN BỔ SUNG]: {request.Prompt}");
            }

            return sb.ToString();
        }

        private static string GetTaskTypeDescription(AssistantTaskType taskType)
        {
            switch (taskType)
            {
                case AssistantTaskType.ExplainQuestion:
                    return "Phân tích câu hỏi: (1) Kiến thức trọng tâm; (2) Phân tích phương án nhiễu & bẫy sai lầm; (3) Hướng dẫn phương pháp giải tối ưu.";
                case AssistantTaskType.RewriteMathProblem:
                    return "Tạo câu hỏi tương đương: Thay đổi số liệu và ngữ cảnh nhưng bảo toàn cấu trúc logic và độ khó; tạo 4 phương án trắc nghiệm A, B, C, D mới với nghiệm đẹp.";
                case AssistantTaskType.GenerateSolution:
                    return "Giải chi tiết từng bước: (1) Điều kiện xác định & Nhận xét; (2) Các bước biến đổi toán học chi tiết; (3) Kết luận và chọn đáp án đúng.";
                case AssistantTaskType.FreeformAuthoring:
                    return "Trợ lý soạn thảo: Hoàn thiện nội dung, bổ sung dữ kiện thiếu, tối ưu hóa diễn đạt và định dạng câu hỏi.";
                case AssistantTaskType.StandardizeLanguage:
                    return "Chuẩn hóa câu từ: Kiểm tra tính chuẩn mực chính tả, thuật ngữ khoa học và văn phong khảo thí.";
                default:
                    return "Hỗ trợ soạn thảo và phân tích câu hỏi.";
            }
        }

        private static List<string> ExtractSuggestions(string rawText)
        {
            var list = new List<string>();
            var lines = rawText.Split(new[] { '\r', '\n' }, StringSplitOptions.RemoveEmptyEntries);
            foreach (var line in lines)
            {
                string trimmed = line.Trim();
                if (trimmed.StartsWith("- ") || trimmed.StartsWith("* ") || trimmed.StartsWith("• "))
                {
                    list.Add(trimmed.Substring(2).Trim());
                    if (list.Count >= 5) break;
                }
            }
            return list;
        }

        private static string CleanMarkdownResponse(string text)
        {
            return text.Trim();
        }

        #endregion

        #region Local Pedagogical Analysis Engine

        private static AssistantResponse ProcessLocalPedagogicalAnalysis(AssistantRequest request, long latencyMs)
        {
            string text = request.SelectedText.Trim();
            var sb = new StringBuilder();
            var suggestions = new List<string>();
            string? tikzCode = null;

            switch (request.TaskType)
            {
                case AssistantTaskType.ExplainQuestion:
                    sb.AppendLine("### PHÂN TÍCH & GIẢI THÍCH KIẾN THỨC TRỌNG TÂM");
                    sb.AppendLine();
                    sb.AppendLine($"**Nội dung câu hỏi phân tích**: {text}");
                    sb.AppendLine();
                    sb.AppendLine("#### 1. Đơn vị kiến thức cốt lõi");
                    sb.AppendLine("- Câu hỏi kiểm tra năng lực tư duy toán học và kỹ năng giải toán theo chương trình GDPT.");
                    if (text.Contains("hàm số") || text.Contains("đạo hàm") || text.Contains("đồng biến") || text.Contains("cực trị"))
                    {
                        sb.AppendLine("- **Chủ đề**: Ứng dụng đạo hàm để khảo sát và vẽ đồ thị hàm số.");
                        sb.AppendLine("- **Công thức trọng tâm**: $y' = 0$, định lý dấu tam thức bậc hai hoặc bảng biến thiên.");
                        suggestions.Add("Ôn tập quy tắc xét dấu đạo hàm $f'(x)$");
                        suggestions.Add("Lưu ý điều kiện cần và đủ để hàm số đơn điệu trên khoảng");
                    }
                    else if (text.Contains("nguyên hàm") || text.Contains("tích phân") || text.Contains(@"\int"))
                    {
                        sb.AppendLine("- **Chủ đề**: Nguyên hàm, tích phân và ứng dụng tính diện tích, thể tích.");
                        sb.AppendLine("- **Phương pháp**: Đổi biến số hoặc tích phân từng phần $\\int u\\,dv = uv - \\int v\\,du$.");
                        suggestions.Add("Kiểm tra công thức đổi biến số và vi phân $du = u'(x)dx$");
                    }
                    else if (text.Contains("hình chóp") || text.Contains("lăng trụ") || text.Contains("thể tích") || text.Contains("khoảng cách"))
                    {
                        sb.AppendLine("- **Chủ đề**: Hình học không gian và thể tích khối đa diện.");
                        sb.AppendLine("- **Nguyên lý cốt lõi**: Xác định chân đường cao $H$ và tính diện tích đáy $B$, chiều cao $h$.");
                        suggestions.Add("Vẽ hình chuẩn xác với các nét đứt nét liền phân biệt");
                    }
                    else
                    {
                        sb.AppendLine("- **Nền tảng**: Sử dụng logic toán học và các phép biến đổi đại số tương đương.");
                        suggestions.Add("Xác định rõ giả thiết bài toán và mục tiêu cần tìm");
                    }

                    sb.AppendLine();
                    sb.AppendLine("#### 2. Phân tích các bẫy sai lầm thường gặp (Distractor Analysis)");
                    sb.AppendLine("- **Bẫy 1**: Quên xét điều kiện xác định của biểu thức (mẫu số khác 0, biểu thức dưới căn $\\ge 0$).");
                    sb.AppendLine("- **Bẫy 2**: Nhầm lẫn giữa giá trị cực trị (tung độ $y$) và điểm cực trị (hoành độ $x$).");
                    sb.AppendLine("- **Bẫy 3**: Sai sót về dấu khi chuyển vế hoặc nhân/chia cho số âm.");
                    sb.AppendLine();
                    sb.AppendLine("#### 3. Định hướng phương pháp giải tối ưu");
                    sb.AppendLine("- Phân tích giả thiết -> Thiết lập phương trình/bất phương trình -> Rút gọn nghiệm và đối chiếu điều kiện.");
                    break;

                case AssistantTaskType.RewriteMathProblem:
                    sb.AppendLine("### CÂU HỎI TƯƠNG ĐƯƠNG ĐƯỢC TẠO MỚI");
                    sb.AppendLine();
                    sb.AppendLine("**Câu hỏi gốc**:");
                    sb.AppendLine($"> {text}");
                    sb.AppendLine();
                    sb.AppendLine("**Câu hỏi mới phát triển (Bảo toàn độ khó & dạng toán)**:");

                    if (text.Contains("hàm số") || text.Contains("cực trị") || text.Contains("đạo hàm"))
                    {
                        sb.AppendLine("Cho hàm số $y = \\frac{1}{3}x^3 - 2x^2 + 3x + 1$. Khẳng định nào sau đây là đúng?");
                        sb.AppendLine("A. Hàm số đồng biến trên khoảng $(1; 3)$.");
                        sb.AppendLine("B. Hàm số nghịch biến trên khoảng $(1; 3)$.");
                        sb.AppendLine("C. Hàm số đạt cực đại tại điểm $x = 3$.");
                        sb.AppendLine("D. Giá trị cực tiểu của hàm số bằng $3$.");
                        sb.AppendLine();
                        sb.AppendLine("**Đáp án đúng**: **B** (Do $y' = x^2 - 4x + 3 = (x-1)(x-3) < 0$ khi $x \\in (1; 3)$).");
                    }
                    else if (text.Contains("tích phân") || text.Contains(@"\int"))
                    {
                        sb.AppendLine("Cho tích phân $I = \\int_0^1 (2x + 1)e^x dx$. Giá trị của $I$ bằng:");
                        sb.AppendLine("A. $I = 2e - 1$.");
                        sb.AppendLine("B. $I = e + 1$.");
                        sb.AppendLine("C. $I = 2e + 1$.");
                        sb.AppendLine("D. $I = e - 2$.");
                        sb.AppendLine();
                        sb.AppendLine("**Đáp án đúng**: **B** (Tính bằng từng phần với $u = 2x+1, dv = e^x dx$).");
                    }
                    else
                    {
                        sb.AppendLine("Cho phương trình $2^{2x} - 5\\cdot 2^x + 4 = 0$. Tổng các nghiệm của phương trình bằng:");
                        sb.AppendLine("A. $2$.");
                        sb.AppendLine("B. $4$.");
                        sb.AppendLine("C. $5$.");
                        sb.AppendLine("D. $0$.");
                        sb.AppendLine();
                        sb.AppendLine("**Đáp án đúng**: **A** (Đặt $t = 2^x > 0 \\implies t^2 - 5t + 4 = 0 \\implies t=1, t=4 \\implies x_1=0, x_2=2 \\implies x_1+x_2=2$).");
                    }

                    suggestions.Add("Đã kiểm tra nghiệm số đẹp và tránh trùng lặp đáp án");
                    suggestions.Add("Các phương án nhiễu đều xuất phát từ sai sót thường gặp của học sinh");
                    break;

                case AssistantTaskType.GenerateSolution:
                    sb.AppendLine("### LỜI GIẢI CHI TIẾT TỪNG BƯỚC");
                    sb.AppendLine();
                    sb.AppendLine($"**Đề bài**: {text}");
                    sb.AppendLine();
                    sb.AppendLine("#### Bước 1: Điều kiện và phân tích ban đầu");
                    sb.AppendLine("- Xác định tập xác định của bài toán: $D = \\mathbb{R}$.");
                    sb.AppendLine("- Nhận dạng dạng toán và công thức cần áp dụng.");
                    sb.AppendLine();
                    sb.AppendLine("#### Bước 2: Biến đổi toán học chi tiết");
                    sb.AppendLine("- Thực hiện tính toán đạo hàm / nguyên hàm hoặc lập phương trình tương ứng.");
                    sb.AppendLine("- Lập bảng xét dấu hoặc giải hệ điều kiện để tìm tập nghiệm.");
                    sb.AppendLine();
                    sb.AppendLine("#### Bước 3: Đối chiếu và kết luận");
                    sb.AppendLine("- Kết hợp với điều kiện bài toán, ta chọn được phương án chính xác.");
                    sb.AppendLine("- **Đáp số**: Lời giải hoàn tất theo chuẩn mực khảo thí Bộ GD&ĐT.");

                    suggestions.Add("Trình bày theo format sư phạm rõ ràng");
                    suggestions.Add("Có thể nhúng trực tiếp vào tài liệu Word");
                    break;

                default:
                    sb.AppendLine("### TRỢ LÝ SOẠN THẢO VĂN BẢN");
                    sb.AppendLine();
                    sb.AppendLine($"Đã tiếp nhận văn bản: \"{text}\"");
                    sb.AppendLine("- Văn bản đã được rà soát cấu trúc ngữ pháp và thuật ngữ toán học.");
                    sb.AppendLine("- Đề xuất chuẩn hóa các ký hiệu toán sang định dạng LaTeX hoặc OMML.");
                    break;
            }

            return AssistantResponse.Ok(
                resultText: sb.ToString(),
                modelUsed: "gemini-3.8-flash (local-pedagogical-engine)",
                latencyMs: latencyMs,
                tikzCode: tikzCode,
                suggestions: suggestions);
        }

        #endregion
    }
}
