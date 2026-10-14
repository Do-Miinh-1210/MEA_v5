using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Text.RegularExpressions;

namespace MatrixExamAI.Shared.Extensibility
{
    /// <summary>
    /// Kết quả phân tích cú pháp câu hỏi theo quy trình đa tầng (Multi-tier Parser Engine).
    /// </summary>
    public class ParseEngineResult
    {
        public List<QuestionItem> Questions { get; set; } = new List<QuestionItem>();
        public string Tier { get; set; } = "none"; // "exact", "latex", "mixed", "natural", "none"
        public string FormattedDocText { get; set; } = string.Empty;
        public int TotalCount => Questions.Count;
        public int TnCount => Questions.Count(q => q.QuestionType == "MultipleChoice4");
        public int DsCount => Questions.Count(q => q.QuestionType == "TrueFalse4");
        public int TlnCount => Questions.Count(q => q.QuestionType == "ShortAnswer");
        public int TlCount => Questions.Count(q => q.QuestionType == "Essay");
    }

    /// <summary>
    /// Bộ máy phân tích cú pháp câu hỏi và chuẩn hóa toán học siêu tốc (Port từ MEA v5.0 Python).
    /// Hỗ trợ hoàn chỉnh:
    /// 1. Tầng 1: Cấu trúc App (===CAU===...===KETCAU===) và LaTeX ex_test (\begin{ex|bt|vd}...\choice).
    /// 2. Tầng 2: Cấu trúc Tự nhiên (Câu 1: ... A. ... B. ... Đáp án: ... Lời giải: ...).
    /// 3. Chuẩn hóa công thức toán học sang ${...}$, tự động bọc công thức ngoài dấu $ (\left(u_n\right), \frac...), bảo vệ |x|.
    /// </summary>
    public static class QuestionParserEngine
    {
        private static readonly Regex ExactBlockRegex = new Regex(@"===\s*CAU\s*===(.*?)===\s*KETCAU\s*===", RegexOptions.Singleline | RegexOptions.IgnoreCase);
        private static readonly Regex LatexBlockRegex = new Regex(@"\\begin\{(ex|bt|vd)\}([\s\S]*?)\\end\{\1\}", RegexOptions.Singleline);
        private static readonly Regex NaturalHeaderRegex = new Regex(@"(?m)^%?\s*(?:Câu|Bài|CÂU|BÀI)\s*(\d+)(?:[:.]|\s*\[|\s|$)");

        #region Public Entry Points

        /// <summary>
        /// Điểm vào chính: Nhận diện câu hỏi từ văn bản tự do theo quy trình 3 tầng.
        /// </summary>
        public static ParseEngineResult ParseQuestions(string text, string subject = "Toán", int grade = 12)
        {
            var result = new ParseEngineResult();
            if (string.IsNullOrWhiteSpace(text)) return result;

            // Xóa sạch các thẻ trích dẫn do AI sinh ra [cite: 41, 42]
            text = CleanCitations(text);

            // 1. Kiểm tra cấu trúc App (===CAU===)
            var exactMatches = ExactBlockRegex.Matches(text);
            var latexMatches = LatexBlockRegex.Matches(text);

            if (exactMatches.Count > 0 && latexMatches.Count == 0)
            {
                var qs = ParseAppStruct(text, subject, grade);
                if (qs.Count > 0)
                {
                    result.Questions = qs;
                    result.Tier = "exact";
                    result.FormattedDocText = FormatWordReadyText(qs);
                    return result;
                }
            }

            if (latexMatches.Count > 0 && exactMatches.Count == 0)
            {
                var qs = ParseLatex(text, subject, grade);
                if (qs.Count > 0)
                {
                    result.Questions = qs;
                    result.Tier = "latex";
                    result.FormattedDocText = FormatWordReadyText(qs);
                    return result;
                }
            }

            if (exactMatches.Count > 0 && latexMatches.Count > 0)
            {
                var exactQs = ParseAppStruct(text, subject, grade);
                var latexQs = ParseLatex(text, subject, grade);
                var combined = new List<QuestionItem>();
                combined.AddRange(exactQs);
                combined.AddRange(latexQs);
                if (combined.Count > 0)
                {
                    result.Questions = combined;
                    result.Tier = "mixed";
                    result.FormattedDocText = FormatWordReadyText(combined);
                    return result;
                }
            }

            // 2. Kiểm tra văn bản tự nhiên (Câu 1: A. ... B. ...)
            var naturalQs = ParseNatural(text, subject, grade);
            if (naturalQs.Count > 0)
            {
                result.Questions = naturalQs;
                result.Tier = "natural";
                result.FormattedDocText = FormatWordReadyText(naturalQs);
                return result;
            }

            // Fallback: Không nhận diện được câu nào
            result.Tier = "none";
            return result;
        }

        #endregion

        #region Balanced Braces Parser

        public static int FindMatchingBrace(string text, int openPos)
        {
            if (openPos < 0 || openPos >= text.Length || text[openPos] != '{') return -1;
            int depth = 0;
            for (int i = openPos; i < text.Length; i++)
            {
                if (text[i] == '{') depth++;
                else if (text[i] == '}')
                {
                    depth--;
                    if (depth == 0) return i;
                }
            }
            return text.Length - 1;
        }

        public static string ExtractBraceContent(string text, int openPos)
        {
            if (openPos < 0 || openPos >= text.Length || text[openPos] != '{') return string.Empty;
            int closePos = FindMatchingBrace(text, openPos);
            if (closePos > openPos)
            {
                return text.Substring(openPos + 1, closePos - openPos - 1);
            }
            return text.Substring(openPos + 1);
        }

        public static List<string> ExtractBraceGroups(string text, int startPos, int count)
        {
            var groups = new List<string>();
            int pos = startPos;
            for (int i = 0; i < count; i++)
            {
                int idx = text.IndexOf('{', pos);
                if (idx == -1) break;
                string content = ExtractBraceContent(text, idx);
                groups.Add(content);
                int end = FindMatchingBrace(text, idx);
                pos = (end >= 0 ? end : idx) + 1;
            }
            return groups;
        }

        private static int FindOutermostLoigiai(string body)
        {
            var matches = Regex.Matches(body, @"\\loigiai\s*(?:\[[^\]]*\])?\s*\{");
            foreach (Match m in matches)
            {
                int depth = 0;
                for (int i = 0; i < m.Index; i++)
                {
                    if (body[i] == '{') depth++;
                    else if (body[i] == '}') depth--;
                }
                if (depth <= 1) return m.Index;
            }
            return -1;
        }

        private static string UnwrapImmini(string body)
        {
            var m = Regex.Match(body, @"\\immini\s*\{");
            if (!m.Success) return body;

            string before = body.Substring(0, m.Index).Trim();
            int b1Start = body.IndexOf('{', m.Index);
            string content = ExtractBraceContent(body, b1Start);
            int b1End = FindMatchingBrace(body, b1Start);

            string afterB1 = body.Substring(b1End + 1);
            string restStripped = afterB1.TrimStart();
            int b2Offset = b1End + 1 + (afterB1.Length - restStripped.Length);
            string afterImmini = string.Empty;
            string tikzContent = string.Empty;

            if (restStripped.StartsWith("{"))
            {
                int b2End = FindMatchingBrace(body, b2Offset);
                tikzContent = ExtractBraceContent(body, b2Offset);
                afterImmini = b2End >= 0 && b2End + 1 < body.Length ? body.Substring(b2End + 1) : string.Empty;
            }
            else
            {
                afterImmini = afterB1;
            }

            if (!string.IsNullOrWhiteSpace(tikzContent))
            {
                var choiceMatch = Regex.Match(content, @"\\choice\b|\\choiceTF\b");
                if (choiceMatch.Success)
                {
                    content = content.Substring(0, choiceMatch.Index) + "\n" + tikzContent.Trim() + "\n" + content.Substring(choiceMatch.Index);
                }
                else
                {
                    content += "\n" + tikzContent.Trim();
                }
            }

            var parts = new List<string>();
            if (!string.IsNullOrWhiteSpace(before)) parts.Add(before);
            parts.Add(content);
            if (!string.IsNullOrWhiteSpace(afterImmini)) parts.Add(afterImmini.Trim());

            return string.Join("\n", parts);
        }

        #endregion

        #region LaTeX Parser Implementation

        private static List<QuestionItem> ParseLatex(string text, string subject, int grade)
        {
            var list = new List<QuestionItem>();
            if (string.IsNullOrWhiteSpace(text)) return list;

            // 1. Trích xuất metadata từ comment header: % Câu N [Mức độ]_[Chủ đề]
            var headerMap = new Dictionary<int, (string Level, string Topic)>();
            var headerRe = new Regex(@"%\s*Câu\s*\d+\s*\[([^\]]*)\](?:_\[([^\]]*)\])?\s*\n\s*\\begin\{(ex|bt|vd)\}", RegexOptions.Singleline | RegexOptions.IgnoreCase);
            foreach (Match hm in headerRe.Matches(text))
            {
                int beginPos = text.IndexOf(@"\begin", hm.Index, StringComparison.Ordinal);
                if (beginPos >= 0)
                {
                    string lvl = hm.Groups[1].Value.Trim();
                    string top = hm.Groups[2].Success ? hm.Groups[2].Value.Trim() : string.Empty;
                    headerMap[beginPos] = (lvl, top);
                }
            }

            // 2. Trích xuất chủ đề từ \section{...} nếu có
            string sectionTopic = string.Empty;
            var secMatch = Regex.Match(text, @"\\section\*?\{([^}]+)\}");
            if (secMatch.Success)
            {
                sectionTopic = CleanLatexMarkup(secMatch.Groups[1].Value);
            }

            // 3. Tìm các khối \begin{ex|bt|vd}...\end{\1}
            var matches = LatexBlockRegex.Matches(text);
            int qIndex = 1;

            foreach (Match m in matches)
            {
                string envType = m.Groups[1].Value;
                string body = m.Groups[2].Value.Trim();

                // Kiểm tra metadata header nếu có
                string itemLevel = "Thông hiểu";
                string itemTopic = string.IsNullOrWhiteSpace(sectionTopic) ? $"{subject} {grade}" : sectionTopic;

                if (headerMap.TryGetValue(m.Index, out var meta))
                {
                    if (!string.IsNullOrWhiteSpace(meta.Level)) itemLevel = NormalizeLevel(meta.Level);
                    if (!string.IsNullOrWhiteSpace(meta.Topic)) itemTopic = meta.Topic;
                }

                var q = ParseOneLatexQuestion(body, envType, itemLevel, itemTopic, subject, grade, qIndex);
                if (q != null)
                {
                    list.Add(q);
                    qIndex++;
                }
            }

            return list;
        }

        private static QuestionItem? ParseOneLatexQuestion(string body, string envType, string level, string topic, string subject, int grade, int index)
        {
            if (string.IsNullOrWhiteSpace(body)) return null;

            // Xóa comment ID cũ %[...]
            body = Regex.Replace(body, @"^\s*%\[[^\]]*\](?:\s*%\[[^\]]*\])?\s*", "", RegexOptions.Multiline);

            // 1. Trích xuất lời giải \loigiai{...} hoặc \begin{loigiai}...\end{loigiai}
            string solution = string.Empty;
            var envLoigiai = Regex.Match(body, @"\\begin\{loigiai\}([\s\S]*?)\\end\{loigiai\}");
            if (envLoigiai.Success)
            {
                solution = envLoigiai.Groups[1].Value;
                body = (body.Substring(0, envLoigiai.Index) + " " + body.Substring(envLoigiai.Index + envLoigiai.Length)).Trim();
            }
            else
            {
                int loigiaiPos = FindOutermostLoigiai(body);
                if (loigiaiPos >= 0)
                {
                    int braceStart = body.IndexOf('{', loigiaiPos);
                    if (braceStart >= 0)
                    {
                        solution = ExtractBraceContent(body, braceStart);
                        int braceEnd = FindMatchingBrace(body, braceStart);
                        string after = (braceEnd >= 0 && braceEnd + 1 < body.Length) ? body.Substring(braceEnd + 1) : string.Empty;
                        body = (body.Substring(0, loigiaiPos) + " " + after).Trim();
                    }
                }
                else
                {
                    // Fallback nếu \loigiai nằm bên trong
                    var innerMatch = Regex.Match(body, @"\\loigiai\s*(?:\[[^\]]*\])?\s*\{");
                    if (innerMatch.Success)
                    {
                        int bStart = body.IndexOf('{', innerMatch.Index);
                        if (bStart >= 0)
                        {
                            solution = ExtractBraceContent(body, bStart);
                            int bEnd = FindMatchingBrace(body, bStart);
                            string after = bEnd >= 0 && bEnd + 1 < body.Length ? body.Substring(bEnd + 1) : string.Empty;
                            body = (body.Substring(0, innerMatch.Index) + " " + after).Trim();
                        }
                    }
                }
            }

            // 2. Tháo bọc \immini
            body = UnwrapImmini(body);

            var item = new QuestionItem
            {
                QuestionCode = $"TEX_{grade}_{index:D2}",
                Subject = subject,
                Grade = grade,
                Topic = topic,
                CognitiveLevel = level,
                Explanation = NormalizeMathToBracedDollars(CleanLatexMarkup(solution), wrapUnbracedLatex: true, forceMath: true)
            };

            // 3. Phân tích dạng câu hỏi
            // A. Dạng Đúng/Sai: \choiceTF
            var choiceTfMatch = Regex.Match(body, @"\\choiceTF\s*(?:\[[^\]]*\])?\s*");
            if (choiceTfMatch.Success)
            {
                item.QuestionType = "TrueFalse4";
                string qText = body.Substring(0, choiceTfMatch.Index).Trim();
                item.Content = NormalizeMathToBracedDollars(CleanLatexMarkup(qText), wrapUnbracedLatex: true, forceMath: true);

                string after = body.Substring(choiceTfMatch.Index + choiceTfMatch.Length);
                var rawItems = ExtractBraceGroups(after, 0, 4);
                string[] labels = { "a", "b", "c", "d" };
                var tfAnswers = new List<string>();

                for (int i = 0; i < rawItems.Count && i < 4; i++)
                {
                    string raw = rawItems[i].Trim();
                    bool isTrue = raw.Contains(@"\True") || Regex.IsMatch(raw, @"\\choice\*\[True\]", RegexOptions.IgnoreCase);
                    string clean = Regex.Replace(raw, @"\\True\s*|\\choice\*\[True\]\s*", "", RegexOptions.IgnoreCase);
                    clean = NormalizeMathToBracedDollars(CleanLatexMarkup(clean), wrapUnbracedLatex: true, forceMath: true);

                    item.Options[labels[i]] = clean;
                    tfAnswers.Add($"{labels[i]}={(isTrue ? "Đ" : "S")}");
                }
                item.CorrectAnswer = string.Join(", ", tfAnswers);
                return item;
            }

            // B. Dạng Trắc nghiệm 4 lựa chọn: \choice
            var choiceMatch = Regex.Match(body, @"\\choice\b\s*");
            if (choiceMatch.Success)
            {
                item.QuestionType = "MultipleChoice4";
                string qText = body.Substring(0, choiceMatch.Index).Trim();
                item.Content = NormalizeMathToBracedDollars(CleanLatexMarkup(qText), wrapUnbracedLatex: true, forceMath: true);

                string after = body.Substring(choiceMatch.Index + choiceMatch.Length);
                var rawOpts = ExtractBraceGroups(after, 0, 4);
                string[] labels = { "A", "B", "C", "D" };
                string detectedAnswer = "A";

                for (int i = 0; i < rawOpts.Count && i < 4; i++)
                {
                    string raw = rawOpts[i].Trim();
                    bool isTrue = raw.Contains(@"\True") || Regex.IsMatch(raw, @"\\choice\*\[True\]", RegexOptions.IgnoreCase);
                    string clean = Regex.Replace(raw, @"\\True\s*|\\choice\*\[True\]\s*", "", RegexOptions.IgnoreCase);
                    clean = NormalizeMathToBracedDollars(CleanLatexMarkup(clean), wrapUnbracedLatex: true, forceMath: true);

                    item.Options[labels[i]] = clean;
                    if (isTrue) detectedAnswer = labels[i];
                }
                item.CorrectAnswer = detectedAnswer;
                return item;
            }

            // C. Dạng Trả lời ngắn: \shortans
            var shortansMatch = Regex.Match(body, @"\\shortans\s*(?:\[[^\]]*\])?\s*\{");
            if (shortansMatch.Success)
            {
                item.QuestionType = "ShortAnswer";
                string qText = body.Substring(0, shortansMatch.Index).Trim();
                item.Content = NormalizeMathToBracedDollars(CleanLatexMarkup(qText), wrapUnbracedLatex: true, forceMath: true);

                int bStart = body.IndexOf('{', shortansMatch.Index);
                if (bStart >= 0)
                {
                    string ans = ExtractBraceContent(body, bStart);
                    item.CorrectAnswer = NormalizeMathToBracedDollars(CleanLatexMarkup(ans), wrapUnbracedLatex: true, forceMath: true).Trim();
                }
                return item;
            }

            // D. Dạng Tự luận: \begin{bt} hoặc mặc định
            item.QuestionType = "Essay";
            item.Content = NormalizeMathToBracedDollars(CleanLatexMarkup(body), wrapUnbracedLatex: true, forceMath: true);
            return item;
        }

        #endregion

        #region App Struct Parser (===CAU===)

        private static List<QuestionItem> ParseAppStruct(string text, string subject, int grade)
        {
            var list = new List<QuestionItem>();
            var matches = ExactBlockRegex.Matches(text);
            int index = 1;

            foreach (Match m in matches)
            {
                string block = m.Groups[1].Value.Trim();
                var item = new QuestionItem
                {
                    QuestionCode = $"APP_{grade}_{index:D2}",
                    Subject = subject,
                    Grade = grade,
                    Topic = $"{subject} {grade}",
                    CognitiveLevel = "Thông hiểu",
                    QuestionType = "MultipleChoice4"
                };

                var lines = block.Split(new[] { "\r\n", "\r", "\n" }, StringSplitOptions.None);
                var contentLines = new List<string>();
                var solLines = new List<string>();
                bool inSolution = false;

                foreach (var line in lines)
                {
                    string trimmed = line.Trim();
                    if (string.IsNullOrEmpty(trimmed)) continue;

                    if (trimmed.StartsWith("LOAI:", StringComparison.OrdinalIgnoreCase))
                    {
                        string qTypeStr = trimmed.Substring(5).Trim().ToUpperInvariant();
                        if (qTypeStr == "TN") item.QuestionType = "MultipleChoice4";
                        else if (qTypeStr == "DS") item.QuestionType = "TrueFalse4";
                        else if (qTypeStr == "TLN") item.QuestionType = "ShortAnswer";
                        else if (qTypeStr == "TL") item.QuestionType = "Essay";
                        continue;
                    }

                    if (trimmed.StartsWith("MUCDO:", StringComparison.OrdinalIgnoreCase))
                    {
                        item.CognitiveLevel = NormalizeLevel(trimmed.Substring(6).Trim());
                        continue;
                    }

                    if (trimmed.StartsWith("CHUONG:", StringComparison.OrdinalIgnoreCase) || trimmed.StartsWith("CHUDE:", StringComparison.OrdinalIgnoreCase))
                    {
                        item.Topic = trimmed.Substring(trimmed.IndexOf(':') + 1).Trim();
                        continue;
                    }

                    if (trimmed.StartsWith("DAPAN:", StringComparison.OrdinalIgnoreCase))
                    {
                        item.CorrectAnswer = trimmed.Substring(6).Trim();
                        continue;
                    }

                    if (trimmed.StartsWith("LOIGIAI:", StringComparison.OrdinalIgnoreCase))
                    {
                        inSolution = true;
                        string solStart = trimmed.Substring(8).Trim();
                        if (!string.IsNullOrEmpty(solStart)) solLines.Add(solStart);
                        continue;
                    }

                    if (inSolution)
                    {
                        solLines.Add(line);
                        continue;
                    }

                    // Tùy chọn A, B, C, D hoặc a, b, c, d
                    var optMatch = Regex.Match(trimmed, @"^([A-Da-d])[:.]\s*(.*)$");
                    if (optMatch.Success)
                    {
                        string key = optMatch.Groups[1].Value;
                        string val = optMatch.Groups[2].Value.Trim();
                        item.Options[key] = NormalizeMathToBracedDollars(val, wrapUnbracedLatex: true, forceMath: true);
                        continue;
                    }

                    if (trimmed.StartsWith("NOIDUNG:", StringComparison.OrdinalIgnoreCase))
                    {
                        string cStart = trimmed.Substring(8).Trim();
                        if (!string.IsNullOrEmpty(cStart)) contentLines.Add(cStart);
                        continue;
                    }

                    contentLines.Add(line);
                }

                item.Content = NormalizeMathToBracedDollars(string.Join("\n", contentLines).Trim(), wrapUnbracedLatex: true, forceMath: true);
                item.Explanation = NormalizeMathToBracedDollars(string.Join("\n", solLines).Trim(), wrapUnbracedLatex: true, forceMath: true);

                list.Add(item);
                index++;
            }

            return list;
        }

        #endregion

        #region Natural Text Parser

        private static List<QuestionItem> ParseNatural(string text, string subject, int grade)
        {
            var list = new List<QuestionItem>();
            var matches = NaturalHeaderRegex.Matches(text);
            if (matches.Count == 0) return list;

            var blocks = new List<string>();
            for (int i = 0; i < matches.Count; i++)
            {
                int start = matches[i].Index;
                int end = (i + 1 < matches.Count) ? matches[i + 1].Index : text.Length;
                blocks.Add(text.Substring(start, end - start).Trim());
            }

            int index = 1;
            foreach (var block in blocks)
            {
                var item = new QuestionItem
                {
                    QuestionCode = $"NAT_{grade}_{index:D2}",
                    Subject = subject,
                    Grade = grade,
                    Topic = $"{subject} {grade}",
                    CognitiveLevel = "Thông hiểu",
                    QuestionType = "MultipleChoice4"
                };

                var lines = block.Split(new[] { "\r\n", "\r", "\n" }, StringSplitOptions.None);
                var contentLines = new List<string>();
                var solLines = new List<string>();
                bool inSolution = false;

                foreach (var line in lines)
                {
                    string trimmed = line.Trim();
                    if (string.IsNullOrEmpty(trimmed)) continue;

                    var ansMatch = Regex.Match(trimmed, @"^(?:[-=>*•\s]*)(?:Đáp án|ĐA|Đ/A|Đáp số|Answer)[:\s]+(.*)$", RegexOptions.IgnoreCase);
                    if (ansMatch.Success)
                    {
                        item.CorrectAnswer = ansMatch.Groups[1].Value.Trim();
                        continue;
                    }

                    var solMatch = Regex.Match(trimmed, @"^(?:Lời giải|Giải|Hướng dẫn giải|Hướng dẫn)[:\s]*(.*)$", RegexOptions.IgnoreCase);
                    if (solMatch.Success)
                    {
                        inSolution = true;
                        string solStart = solMatch.Groups[1].Value.Trim();
                        if (!string.IsNullOrEmpty(solStart)) solLines.Add(solStart);
                        continue;
                    }

                    if (inSolution)
                    {
                        solLines.Add(line);
                        continue;
                    }

                    // Phương án TN A./B./C./D.
                    var optMatch = Regex.Match(trimmed, @"^([A-D])[.:\)]\s*(.*)$");
                    if (optMatch.Success)
                    {
                        string k = optMatch.Groups[1].Value.ToUpperInvariant();
                        string v = optMatch.Groups[2].Value.Trim();
                        item.Options[k] = NormalizeMathToBracedDollars(v, wrapUnbracedLatex: true, forceMath: true);
                        continue;
                    }

                    // Mệnh đề DS a./b./c./d.
                    var tfMatch = Regex.Match(trimmed, @"^([a-d])[.:\)]\s*(.*)$");
                    if (tfMatch.Success)
                    {
                        item.QuestionType = "TrueFalse4";
                        string k = tfMatch.Groups[1].Value.ToLowerInvariant();
                        string v = tfMatch.Groups[2].Value.Trim();
                        item.Options[k] = NormalizeMathToBracedDollars(v, wrapUnbracedLatex: true, forceMath: true);
                        continue;
                    }

                    // Bỏ tiêu đề "Câu N:" ở dòng đầu tiên và trích xuất mức độ/chủ đề nếu có (% Câu 1 [Nhận biết]_[Hàm số bậc hai])
                    if (contentLines.Count == 0)
                    {
                        var metaMatch = Regex.Match(trimmed, @"^%?\s*(?:Câu|Bài|CÂU|BÀI)\s*\d+[:.]?\s*(?:\[(?<lvl>[^\]]+)\])?(?:_\[?(?<top>[^\]\r\n]+)\]?)?(?<rest>.*)$", RegexOptions.IgnoreCase);
                        if (metaMatch.Success)
                        {
                            if (metaMatch.Groups["lvl"].Success && !string.IsNullOrWhiteSpace(metaMatch.Groups["lvl"].Value))
                            {
                                item.CognitiveLevel = NormalizeLevel(metaMatch.Groups["lvl"].Value.Trim());
                            }
                            if (metaMatch.Groups["top"].Success && !string.IsNullOrWhiteSpace(metaMatch.Groups["top"].Value))
                            {
                                item.Topic = metaMatch.Groups["top"].Value.Trim();
                            }
                            string rest = metaMatch.Groups["rest"].Value.Trim();
                            if (!string.IsNullOrEmpty(rest))
                            {
                                contentLines.Add(rest);
                            }
                            continue;
                        }

                        string stripped = NaturalHeaderRegex.Replace(trimmed, "").Trim();
                        if (!string.IsNullOrEmpty(stripped)) contentLines.Add(stripped);
                        continue;
                    }

                    contentLines.Add(line);
                }

                // Heuristic healing for broken fractions across options (e.g. A. $\dfrac{5 / B. 4}$)
                if (item.Options.ContainsKey("A") && item.Options.ContainsKey("B"))
                {
                    string aVal = item.Options["A"];
                    string bVal = item.Options["B"];
                    if ((aVal.Contains(@"\dfrac{") || aVal.Contains(@"\frac{")) && 
                        Regex.IsMatch(aVal, @"\\d?frac\{[^{}]*$") && 
                        Regex.IsMatch(bVal, @"^[^{}]*\}"))
                    {
                        var mB = Regex.Match(bVal, @"^([^{}]*)\}\$?(\s*.*)$");
                        if (mB.Success)
                        {
                            string den = mB.Groups[1].Value.Trim();
                            string restB = mB.Groups[2].Value.Trim();
                            item.Options["A"] = NormalizeMathToBracedDollars(aVal + "}{" + den + "}", wrapUnbracedLatex: true, forceMath: true);
                            if (!string.IsNullOrEmpty(restB))
                            {
                                item.Options["B"] = NormalizeMathToBracedDollars(restB, wrapUnbracedLatex: true, forceMath: true);
                            }
                        }
                    }
                }
                if (item.Options.ContainsKey("C") && item.Options.ContainsKey("D"))
                {
                    string cVal = item.Options["C"];
                    string dVal = item.Options["D"];
                    if ((cVal.Contains(@"\dfrac{") || cVal.Contains(@"\frac{")) && 
                        Regex.IsMatch(cVal, @"\\d?frac\{[^{}]*$") && 
                        Regex.IsMatch(dVal, @"^[^{}]*\}?"))
                    {
                        var mD = Regex.Match(dVal, @"^([^{}]*)\}?\$?(\s*.*)$");
                        if (mD.Success)
                        {
                            string den = mD.Groups[1].Value.Trim();
                            string restD = mD.Groups[2].Value.Trim();
                            item.Options["C"] = NormalizeMathToBracedDollars(cVal + "}{" + den + "}", wrapUnbracedLatex: true, forceMath: true);
                            if (!string.IsNullOrEmpty(restD))
                            {
                                item.Options["D"] = NormalizeMathToBracedDollars(restD, wrapUnbracedLatex: true, forceMath: true);
                            }
                        }
                    }
                }

                item.Content = NormalizeMathToBracedDollars(string.Join("\n", contentLines).Trim(), wrapUnbracedLatex: true, forceMath: true);
                item.Explanation = NormalizeMathToBracedDollars(string.Join("\n", solLines).Trim(), wrapUnbracedLatex: true, forceMath: true);

                if (item.Options.Count == 0 && !string.IsNullOrEmpty(item.CorrectAnswer))
                {
                    if (Regex.IsMatch(item.CorrectAnswer, @"^[\d\.,\-\+/]+$"))
                    {
                        item.QuestionType = "ShortAnswer";
                    }
                }

                list.Add(item);
                index++;
            }

            return list;
        }

        #endregion

        #region Math Normalization & LaTeX Cleaning

        /// <summary>
        /// Chuẩn hóa mọi công thức toán học về chuẩn ${...}$, tự động bọc các biểu thức toán ngoài dấu $
        /// và bảo vệ dấu giá trị tuyệt đối |x| không bị nhầm lẫn với ký tự phân tách bảng markdown.
        /// </summary>
        public static string NormalizeMathToBracedDollars(string text, bool protectAbs = true)
        {
            return NormalizeMathToBracedDollars(text, wrapUnbracedLatex: true, forceMath: false, protectAbs: protectAbs);
        }

        /// <summary>
        /// Chuẩn hóa mọi công thức toán học về chuẩn ${...}$ với các tùy chọn nâng cao.
        /// </summary>
        public static string NormalizeMathToBracedDollars(string text, bool wrapUnbracedLatex, bool forceMath, bool protectAbs = true)
        {
            if (string.IsNullOrEmpty(text)) return text;

            // 0. Chuẩn hóa hệ phương trình (aligned -> align) và tháo bỏ ký tự $ / ${...}$ lồng sai bên trong hệ
            text = NormalizeSystemEquationsAndAlign(text);

            var mathPipeMasks = new Dictionary<string, string>();
            int maskCounter = 0;

            if (protectAbs)
            {
                // Mask các công thức toán chứa ký tự '|' (trị tuyệt đối hoặc chuẩn vector)
                // để tránh bị nhầm lẫn với dấu phân cách cột của bảng Markdown (| col1 | col2 |).
                text = Regex.Replace(text, @"\$\{[\s\S]*?\}\$|\$\$.*?\$\$|\\\[[\s\S]*?\\\]|\\\(.*?\\\)|(?<!\\)\$([^\$\n]+?)(?<!\\)\$|(?<!\\)\$([\s\S]+?)(?<!\\)\$|\\left\|[\s\S]*?\\right\|", m =>
                {
                    string val = m.Value;
                    if (val.Contains('|'))
                    {
                        string inner = val;
                        if (inner.StartsWith("${") && inner.EndsWith("}$") && inner.Length >= 4)
                            inner = inner.Substring(2, inner.Length - 4);
                        else if (inner.StartsWith("$$") && inner.EndsWith("$$") && inner.Length >= 4)
                            inner = inner.Substring(2, inner.Length - 4);
                        else if (inner.StartsWith("\\[") && inner.EndsWith("\\]") && inner.Length >= 4)
                            inner = inner.Substring(2, inner.Length - 4);
                        else if (inner.StartsWith("\\(") && inner.EndsWith("\\)") && inner.Length >= 4)
                            inner = inner.Substring(2, inner.Length - 4);
                        else if (inner.StartsWith("$") && inner.EndsWith("$") && inner.Length >= 2)
                            inner = inner.Substring(1, inner.Length - 2);

                        string key = $"@@MATH_PIPE_{maskCounter++}@@";
                        mathPipeMasks[key] = WrapInBracedDollar(inner);
                        return key;
                    }
                    return val;
                }, RegexOptions.Singleline);
            }

            // 1. Chuẩn hóa LaTeX \(...\) và \[...\]
            text = Regex.Replace(text, @"\\\[([\s\S]*?)\\\]", m => WrapInBracedDollar(m.Groups[1].Value));
            text = Regex.Replace(text, @"\\\(([\s\S]*?)\\\)", m => WrapInBracedDollar(m.Groups[1].Value));

            // 2. Chuẩn hóa Block Math $$...$$
            text = Regex.Replace(text, @"\$\$([\s\S]*?)\$\$", m => WrapInBracedDollar(m.Groups[1].Value));

            // 2.5. Chuẩn hóa multiline math $...$ chứa hệ phương trình hoặc công thức nhiều dòng
            text = Regex.Replace(text, @"(?<!\\)\$([\s\S]+?)(?<!\\)\$", m =>
            {
                string inner = m.Groups[1].Value.Trim();
                if (string.IsNullOrWhiteSpace(inner)) return m.Value;
                if (inner.Contains(@"\begin{") || inner.Contains(@"\left\{") || inner.Contains(@"\Leftrightarrow") || inner.Contains(@"\\"))
                {
                    return WrapInBracedDollar(inner);
                }
                if (!inner.Contains("\n"))
                {
                    if (!forceMath && Regex.IsMatch(inner, @"^\d+(?:[.,]\d+)?$") && !IsExamOrMathContext(text))
                        return m.Value;
                    return WrapInBracedDollar(inner);
                }
                return m.Value;
            });

            // 3. Chuẩn hóa Inline Math $...$ còn lại
            text = Regex.Replace(text, @"(?<!\\)\$([^\$\n]+?)(?<!\\)\$", m =>
            {
                string inner = m.Groups[1].Value.Trim();
                if (string.IsNullOrWhiteSpace(inner)) return m.Value;
                if (!forceMath && Regex.IsMatch(inner, @"^\d+(?:[.,]\d+)?$") && !IsExamOrMathContext(text))
                    return m.Value;
                return WrapInBracedDollar(inner);
            });

            // 4. Bọc các biểu thức LaTeX toán học đứng trần ngoài dấu $ (ví dụ \left(u_n\right), \vec{a}, \frac{a}{b})
            if (wrapUnbracedLatex)
            {
                text = WrapUnbracedLatexExpressions(text);
            }

            // 5. Phục hồi các công thức chứa '|' đã được bọc chuẩn ${...}$
            if (protectAbs && mathPipeMasks.Count > 0)
            {
                foreach (var kvp in mathPipeMasks)
                {
                    text = text.Replace(kvp.Key, kvp.Value);
                }
            }

            return CleanDoubleWrappedFormulas(text);
        }

        /// <summary>
        /// Chuẩn hóa công thức hệ phương trình:
        /// 1. Đổi môi trường aligned sang align (\begin{aligned} -> \begin{align}, \end{aligned} -> \end{align}).
        /// 2. Loại bỏ các ký tự $, ${, }$ bị lồng sai bên trong hệ phương trình (ví dụ: &u_1 + ${\left(u_1 + 4d\right)}$ = 18).
        /// </summary>
        public static string NormalizeSystemEquationsAndAlign(string text)
        {
            if (string.IsNullOrEmpty(text)) return string.Empty;

            // 1. Quét các khối \begin{aligned}...\end{aligned} hoặc \begin{align}...\end{align}
            text = Regex.Replace(text, @"\\begin\{(?:aligned\*?|align\*?)\}([\s\S]*?)\\end\{(?:aligned\*?|align\*?)\}", m =>
            {
                string inner = m.Groups[1].Value;
                // Loại bỏ mọi $ hoặc ${ hoặc }$ bị lồng bên trong hệ
                inner = Regex.Replace(inner, @"\$\{\s*([\s\S]*?)\s*\}\$", "$1");
                inner = Regex.Replace(inner, @"\$\{\s*([\s\S]*?)\s*\}", "$1");
                inner = Regex.Replace(inner, @"\$([^\$\n]+?)\$", "$1");
                inner = inner.Replace("${", "").Replace("}$", "").Replace("$", "");
                return $"\\begin{{align}}{inner}\\end{{align}}";
            });

            // 2. Quét các khối \left\{...\right. chứa hệ phương trình
            text = Regex.Replace(text, @"\\left\\\{\s*([\s\S]*?)\s*\\right\.", m =>
            {
                string inner = m.Groups[1].Value;
                if (inner.Contains(@"\begin{align}") || inner.Contains(@"\begin{aligned"))
                {
                    inner = inner.Replace(@"\begin{aligned*}", @"\begin{align}")
                                 .Replace(@"\end{aligned*}", @"\end{align}")
                                 .Replace(@"\begin{aligned}", @"\begin{align}")
                                 .Replace(@"\end{aligned}", @"\end{align}");
                    inner = Regex.Replace(inner, @"\$\{\s*([\s\S]*?)\s*\}\$", "$1");
                    inner = Regex.Replace(inner, @"\$\{\s*([\s\S]*?)\s*\}", "$1");
                    inner = Regex.Replace(inner, @"\$([^\$\n]+?)\$", "$1");
                    inner = inner.Replace("${", "").Replace("}$", "").Replace("$", "");
                    return $"\\left\\{{{inner}\\right.";
                }
                return m.Value;
            });

            // 3. Nếu còn bất kỳ \begin{aligned} hoặc \end{aligned} nào khác, chuyển sang \begin{align} và \end{align}
            text = text.Replace(@"\begin{aligned*}", @"\begin{align}")
                       .Replace(@"\end{aligned*}", @"\end{align}")
                       .Replace(@"\begin{aligned}", @"\begin{align}")
                       .Replace(@"\end{aligned}", @"\end{align}");

            return text;
        }

        public static bool IsExamOrMathContext(string text)
        {
            if (string.IsNullOrEmpty(text)) return false;
            return text.Contains(@"\begin{") ||
                   text.Contains(@"\choice") ||
                   text.Contains(@"\choiceTF") ||
                   text.Contains(@"\shortans") ||
                   text.Contains(@"\loigiai") ||
                   text.Contains(@"\left(") ||
                   text.Contains(@"\left[") ||
                   text.Contains(@"\frac") ||
                   text.Contains(@"\sqrt") ||
                   text.Contains(@"\alpha") ||
                   text.Contains(@"\vec") ||
                   text.Contains("===CAU===") ||
                   Regex.IsMatch(text, @"(?i)(?:^|\n)%?\s*Câu\s+\d+");
        }

        private static string WrapInBracedDollar(string inner)
        {
            if (string.IsNullOrWhiteSpace(inner)) return string.Empty;
            inner = inner.Trim();
            // Tháo bỏ các lớp bọc dư thừa nếu bị lồng
            while ((inner.StartsWith("${") && inner.EndsWith("}$") && inner.Length >= 4) ||
                   (inner.StartsWith("${") && inner.EndsWith("}") && inner.Length >= 3) ||
                   (inner.StartsWith("$") && inner.EndsWith("$") && inner.Length >= 2))
            {
                if (inner.StartsWith("${") && inner.EndsWith("}$"))
                    inner = inner.Substring(2, inner.Length - 4).Trim();
                else if (inner.StartsWith("${") && inner.EndsWith("}"))
                    inner = inner.Substring(2, inner.Length - 3).Trim();
                else if (inner.StartsWith("$") && inner.EndsWith("$"))
                    inner = inner.Substring(1, inner.Length - 2).Trim();
            }

            // Tháo bỏ các cặp ngoặc nhọn { ... } lồng nhau dư thừa ở ngoài cùng
            while (inner.StartsWith("{") && inner.EndsWith("}") && inner.Length >= 2 && HasMatchingOuterBraces(inner))
            {
                inner = inner.Substring(1, inner.Length - 2).Trim();
            }

            return $"${{{inner}}}$";
        }

        private static bool HasMatchingOuterBraces(string s)
        {
            s = s.Trim();
            if (!s.StartsWith("{") || !s.EndsWith("}")) return false;
            int depth = 0;
            for (int i = 0; i < s.Length; i++)
            {
                if (s[i] == '{') depth++;
                else if (s[i] == '}')
                {
                    depth--;
                    if (depth == 0) return i == s.Length - 1;
                }
            }
            return false;
        }

        /// <summary>
        /// Quét các lệnh LaTeX toán học đứng ngoài cặp $ và bọc vào ${...}$ (ví dụ \left(u_n\right)).
        /// </summary>
        private static string WrapUnbracedLatexExpressions(string text)
        {
            if (string.IsNullOrEmpty(text)) return string.Empty;

            // Tách text thành các phần trong ${...}$ hoặc $...$ và phần text ngoài
            var parts = Regex.Split(text, @"(\$\{[\s\S]*?\}\$|\$[^$\n]+?\$)");
            var sb = new StringBuilder();

            for (int i = 0; i < parts.Length; i++)
            {
                string part = parts[i];
                if ((part.StartsWith("${") && part.EndsWith("}$")) || (part.StartsWith("$") && part.EndsWith("$")))
                {
                    sb.Append(part);
                }
                else
                {
                    // Đang ở ngoài công thức toán: Tìm các cụm \left(...\right), \left[...\right] hoặc \left|...\right|
                    string handled = Regex.Replace(part, @"\\left\s*([(\[|])([\s\S]*?)\\right\s*([)\]|])", m =>
                    {
                        return $"${{\\left{m.Groups[1].Value}{m.Groups[2].Value}\\right{m.Groups[3].Value}}}$";
                    });

                    // Bọc các ký hiệu vector \vec{...}
                    handled = Regex.Replace(handled, @"(?<!\$)\\vec\{[^}]+\}", m => $"${{{m.Value}}}$");

                    sb.Append(handled);
                }
            }

            return CleanDoubleWrappedFormulas(sb.ToString());
        }

        public static string CleanDoubleWrappedFormulas(string text)
        {
            if (string.IsNullOrEmpty(text)) return string.Empty;

            string prev;
            do
            {
                prev = text;
                // 1. ${${...}$}$ (nested ${...}$ inside ${...}$)
                text = Regex.Replace(text, @"\$\{\s*\$\{\s*([\s\S]*?)\s*\}\$\s*\}\$", m => WrapInBracedDollar(m.Groups[1].Value));
                // 2. ${${...}}$ (nested ${...} inside ${...}$)
                text = Regex.Replace(text, @"\$\{\s*\$\{\s*([\s\S]*?)\s*\}\s*\}\$", m => WrapInBracedDollar(m.Groups[1].Value));
                // 3. ${$...$}$ (nested $...$ inside ${...}$)
                text = Regex.Replace(text, @"\$\{\s*\$\s*([\s\S]*?)\s*\$\s*\}\$", m => WrapInBracedDollar(m.Groups[1].Value));
                // 4. ${$...}$ (nested $... inside ${...}$)
                text = Regex.Replace(text, @"\$\{\s*\$\s*([\s\S]*?)\s*\}\$", m => WrapInBracedDollar(m.Groups[1].Value));
                // 5. $${...}$$ (double dollar wrapped)
                text = Regex.Replace(text, @"\$\s*\$\{\s*([\s\S]*?)\s*\}\s*\$", m => WrapInBracedDollar(m.Groups[1].Value));
                // 6. Bắt trường hợp ${{{foo}}}$ -> ${foo}$
                text = Regex.Replace(text, @"\$\{\s*\{\s*([\s\S]*?)\s*\}\s*\}\$", m => WrapInBracedDollar(m.Groups[1].Value));
            } while (text != prev);

            return text;
        }

        /// <summary>
        /// Lọc và chuyển đổi các danh sách \item, \itemch, itemchoice, itemize thành các ý a), b), c), d) hoặc các dòng riêng biệt.
        /// Giải quyết triệt để lỗi dính chữ \item với nội dung hoặc dính số đầu dòng và loại bỏ in đậm đầu phương án.
        /// </summary>
        public static string FilterLatexItems(string text)
        {
            if (string.IsNullOrWhiteSpace(text)) return string.Empty;

            // Fast-path: nếu không chứa bất kỳ từ khóa item nào thì trả về nguyên bản
            if (!text.Contains(@"\item") &&
                !text.Contains(@"\begin{item") &&
                !text.Contains(@"\begin{enum") &&
                !text.Contains(@"\begin{list"))
            {
                return text;
            }

            // 1. Tháo bọc các môi trường liệt kê
            text = Regex.Replace(text, @"\\begin\{(?:itemchoice|itemize|enumerate|list)\}(?:\[[^\]]*\])?(?:\{[^}]*\})?", "", RegexOptions.IgnoreCase);
            text = Regex.Replace(text, @"\\end\{(?:itemchoice|itemize|enumerate|list)\}", "", RegexOptions.IgnoreCase);

            // 2. Chuẩn hóa \itemch thành \item
            text = Regex.Replace(text, @"\\itemch\b\s*", @"\item ");

            // 3. Tách và chuẩn hóa các trường hợp \item bị dính liền chữ/số tiếng Việt/Anh hoặc lệnh \textbf
            // Ví dụ: \item1. -> \item 1. ; \itema) -> \item a) ; \itemĐúng -> \item Đúng ; \item\textbf -> \item \textbf
            text = Regex.Replace(text, @"\\item(?=[a-zA-Z0-9\p{L}\\])", @"\item ");

            // 4. Tìm tất cả các thẻ \item
            var itemPattern = new Regex(@"\\item\s*(?:\[([^\]]*)\])?\s*", RegexOptions.IgnoreCase);
            var matches = itemPattern.Matches(text);

            if (matches.Count == 0)
            {
                return text.Trim();
            }

            var sb = new StringBuilder();

            // Lấy phần lời dẫn trước \item đầu tiên (nếu có)
            if (matches[0].Index > 0)
            {
                string preamble = text.Substring(0, matches[0].Index).Trim();
                if (!string.IsNullOrWhiteSpace(preamble))
                {
                    sb.AppendLine(preamble);
                }
            }

            // Thu thập danh sách các item
            var itemsList = new List<(string? bracketLabel, string body)>();
            for (int i = 0; i < matches.Count; i++)
            {
                var curMatch = matches[i];
                string? bracketLabel = curMatch.Groups[1].Success ? curMatch.Groups[1].Value.Trim() : null;
                int contentStart = curMatch.Index + curMatch.Length;
                int contentEnd = (i + 1 < matches.Count) ? matches[i + 1].Index : text.Length;
                string itemContent = text.Substring(contentStart, contentEnd - contentStart).Trim();
                if (!string.IsNullOrWhiteSpace(itemContent))
                {
                    itemsList.Add((bracketLabel, itemContent));
                }
            }

            if (itemsList.Count == 0)
            {
                return sb.ToString().Trim();
            }

            // Kiểm tra xem có phải bộ ý a, b, c, d (ví dụ bài Đúng/Sai hoặc 4 mệnh đề) không
            bool isSubLetterList = itemsList.Count <= 4 && (
                itemsList.Any(it => Regex.IsMatch(UnboldOptionHeader(it.body), @"^(?:Đúng|Sai|True|False|Mệnh đề)\b", RegexOptions.IgnoreCase)) ||
                itemsList.Any(it => it.bracketLabel != null && Regex.IsMatch(UnboldOptionHeader(it.bracketLabel), @"^[a-dA-D][\.\)]?$")) ||
                itemsList.Any(it => Regex.IsMatch(UnboldOptionHeader(it.body), @"^[a-dA-D][\.\)]")) ||
                text.Contains(@"\choiceTF") ||
                Regex.IsMatch(text, @"(?i)(?:đúng\s*[-/]\s*sai|true\s*[-/]\s*false)")
            );

            string[] defaultLabels = { "a", "b", "c", "d" };

            for (int i = 0; i < itemsList.Count; i++)
            {
                var (bracketLabel, bodyContent) = itemsList[i];
                string lineLabel = string.Empty;

                bodyContent = UnboldOptionHeader(bodyContent);

                // Nếu nội dung đã tự bắt đầu bằng a), b), c), d) hoặc A., B., C., D.
                var existingLetterMatch = Regex.Match(bodyContent, @"^([a-dA-D])[\.\)]\s*");
                if (existingLetterMatch.Success)
                {
                    lineLabel = $"{existingLetterMatch.Groups[1].Value.ToLowerInvariant()}) ";
                    bodyContent = bodyContent.Substring(existingLetterMatch.Length).Trim();
                    bodyContent = UnboldOptionHeader(bodyContent);
                }
                else if (!string.IsNullOrEmpty(bracketLabel))
                {
                    string cleanBracket = UnboldOptionHeader(bracketLabel!).Trim();
                    var bMatch = Regex.Match(cleanBracket, @"^([a-dA-D])[\.\)]?$");
                    if (bMatch.Success)
                    {
                        lineLabel = $"{bMatch.Groups[1].Value.ToLowerInvariant()}) ";
                    }
                    else
                    {
                        lineLabel = $"{cleanBracket} ";
                    }
                }
                else if (isSubLetterList && i < defaultLabels.Length)
                {
                    lineLabel = $"{defaultLabels[i]}) ";
                }
                else
                {
                    // Kiểm tra xem có số thứ tự sẵn: 1., 2., (1), (2), -
                    var numMatch = Regex.Match(bodyContent, @"^(?:\(?\d+[\.\)]|[-•*])\s*");
                    if (numMatch.Success)
                    {
                        lineLabel = numMatch.Value.Trim() + " ";
                        bodyContent = bodyContent.Substring(numMatch.Length).Trim();
                        bodyContent = UnboldOptionHeader(bodyContent);
                    }
                    else
                    {
                        lineLabel = "- ";
                    }
                }

                sb.AppendLine($"{lineLabel}{bodyContent}");
            }

            string result = sb.ToString().TrimEnd();
            // Dọn dẹp triệt để bất kỳ \item hoặc \itemch còn sót lại
            result = Regex.Replace(result, @"\\item(?:ch)?\b(?:\s*\[[^\]]*\])?\s*", "");
            return result;
        }

        private static string UnboldOptionHeader(string content)
        {
            if (string.IsNullOrWhiteSpace(content)) return string.Empty;
            content = content.Trim();
            string prev;
            do
            {
                prev = content;
                // \textbf{...}, \mathbf{...}, \bf{...}, \textrm{...}
                content = Regex.Replace(content, @"^\\(?:textbf|mathbf|bf|textrm)\{([^}]+)\}", "$1");
                // {\bf ...}
                content = Regex.Replace(content, @"^\{\\bf\s+([^}]+)\}", "$1");
                // **...**
                content = Regex.Replace(content, @"^\*\*([^*]+)\*\*", "$1");
                // __...__
                content = Regex.Replace(content, @"^__([^_]+)__", "$1");
                content = content.Trim();
            } while (content != prev);
            return content;
        }

        public static string CleanLatexMarkup(string text)
        {
            if (string.IsNullOrEmpty(text)) return string.Empty;

            // Bỏ comment LaTeX (% ...)
            text = Regex.Replace(text, @"(?<!\\)%.*$", "", RegexOptions.Multiline);

            // Bỏ thẻ citation [cite: 41, 42]
            text = CleanCitations(text);

            // Lọc và chuyển đổi danh sách \item, \itemch, itemchoice, itemize
            text = FilterLatexItems(text);

            // Xóa \begin{center} quanh \begin{tikzpicture} hoặc \begin{tabular}
            text = Regex.Replace(text, @"\\begin\{center\}\s*(\\begin\{(?:tikzpicture|tabular)\}(?:\[[^\]]*\])?(?:\{[^}]*\})?[\s\S]*?\\end\{(?:tikzpicture|tabular)\})\s*\\end\{center\}", "$1", RegexOptions.Singleline);

            // Xóa environment wrappers
            string[] envs = { "itemize", "enumerate", "itemchoice", "align", "align*", "center" };
            foreach (var env in envs)
            {
                text = Regex.Replace(text, $@"\\begin\{{{env}\}}", "");
                text = Regex.Replace(text, $@"\\end\{{{env}\}}", "");
            }

            // Xóa các lệnh markup nhưng GIỮ nội dung
            string[] cmds = { "textbf", "textit", "underline", "emph", "text", "mathrm" };
            foreach (var cmd in cmds)
            {
                text = Regex.Replace(text, $@"\\{cmd}\{{([^}}]*)\}}", "$1");
            }

            // Xóa các lệnh rác không cần thiết
            text = Regex.Replace(text, @"\\(?:caulc|cauds|caukq|Opensolutionfile|Closesolutionfile|indapan|allowdisplaybreaks|immmark|hfill)\b[^\n]*", "");

            // Xóa triệt để các thẻ \item nếu còn sót lại
            text = Regex.Replace(text, @"\\item\b\s*", "");

            // Dọn dòng trống dư thừa
            text = Regex.Replace(text, @"\n\s*\n+", "\n");
            text = Regex.Replace(text, @"[ \t]+", " ");

            return text.Trim();
        }

        public static string CleanCitations(string text)
        {
            if (string.IsNullOrEmpty(text)) return string.Empty;
            return Regex.Replace(text, @"\[cite[a-z]*:\s*[\d,\s]+\]|\[source:\s*[^\]]+\]", "", RegexOptions.IgnoreCase);
        }

        private static string NormalizeLevel(string raw)
        {
            string key = raw.Trim().ToLowerInvariant();
            if (key == "nb" || key.Contains("nhận biết") || key.Contains("nhan biet")) return "Nhận biết";
            if (key == "th" || key.Contains("thông hiểu") || key.Contains("thong hieu")) return "Thông hiểu";
            if (key == "vdc" || key.Contains("vận dụng cao") || key.Contains("van dung cao")) return "Vận dụng cao";
            if (key == "vd" || key.Contains("vận dụng") || key.Contains("van dung")) return "Vận dụng";
            return "Thông hiểu";
        }

        #endregion

        #region Word-Ready Formatter (export/question_formatter.py port)

        /// <summary>
        /// Chuyển đổi danh sách câu hỏi thành văn bản định dạng chuẩn Word (paste vào Word đẹp ngay).
        /// </summary>
        public static string FormatWordReadyText(IEnumerable<QuestionItem> questions)
        {
            if (questions == null) return string.Empty;
            var list = questions.ToList();
            if (list.Count == 0) return string.Empty;

            var sb = new StringBuilder();
            string subject = list.FirstOrDefault(q => !string.IsNullOrWhiteSpace(q.Subject))?.Subject ?? "Toán";
            int grade = list.FirstOrDefault(q => q.Grade > 0)?.Grade ?? 12;

            // Tiêu đề đề thi chuẩn Sư phạm THPT (2 cột phẳng mô phỏng trang Word)
            sb.AppendLine("SỞ GIÁO DỤC VÀ ĐÀO TẠO\t\t\tĐỀ KIỂM TRA CHÍNH THỨC");
            sb.AppendLine($"TRƯỜNG THPT ........................\t\t\tMôn: {subject.ToUpperInvariant()} - Khối {grade}");
            sb.AppendLine($"(Đề thi gồm {list.Count:D2} câu)\t\t\tThời gian làm bài: 90 phút (không kể phát đề)");
            sb.AppendLine();
            sb.AppendLine("Họ và tên thí sinh: ................................................................   Số báo danh: ................   Mã đề 101");
            sb.AppendLine(new string('─', 75));
            sb.AppendLine();

            var tnQuestions = list.Where(q => q.QuestionType == "MultipleChoice4").ToList();
            var dsQuestions = list.Where(q => q.QuestionType == "TrueFalse4").ToList();
            var tlnQuestions = list.Where(q => q.QuestionType == "ShortAnswer").ToList();
            var tlQuestions = list.Where(q => q.QuestionType == "Essay" || (q.QuestionType != "MultipleChoice4" && q.QuestionType != "TrueFalse4" && q.QuestionType != "ShortAnswer")).ToList();

            int globalIndex = 1;

            if (tnQuestions.Count > 0)
            {
                int startIdx = globalIndex;
                int endIdx = globalIndex + tnQuestions.Count - 1;
                sb.AppendLine($"PHẦN I. Thí sinh trả lời từ câu {startIdx} đến câu {endIdx}. Mỗi câu hỏi thí sinh chỉ chọn một phương án.");
                sb.AppendLine();

                foreach (var q in tnQuestions)
                {
                    string content = EnsureTerminator(q.Content);
                    sb.AppendLine($"Câu {globalIndex}. {content}");

                    if (q.Options.Count > 0)
                    {
                        var parts = new List<string>();
                        string[] keys = { "A", "B", "C", "D" };
                        foreach (var k in keys)
                        {
                            string v = q.Options.ContainsKey(k) ? q.Options[k] : string.Empty;
                            parts.Add($"{k}. {EnsureTerminator(v)}");
                        }

                        int maxLen = q.Options.Values.Select(v => (v ?? "").Length).DefaultIfEmpty(0).Max();
                        int totalLen = q.Options.Values.Sum(v => (v ?? "").Length);

                        if (maxLen <= 35 && totalLen <= 120 && parts.Count == 4)
                        {
                            sb.AppendLine(string.Join("\t", parts));
                        }
                        else if (maxLen <= 70 && totalLen <= 220 && parts.Count == 4)
                        {
                            sb.AppendLine($"{parts[0]}\t{parts[1]}");
                            sb.AppendLine($"{parts[2]}\t{parts[3]}");
                        }
                        else
                        {
                            foreach (var part in parts)
                            {
                                sb.AppendLine(part);
                            }
                        }
                    }
                    sb.AppendLine();
                    globalIndex++;
                }
            }

            if (dsQuestions.Count > 0)
            {
                int startIdx = globalIndex;
                int endIdx = globalIndex + dsQuestions.Count - 1;
                sb.AppendLine($"PHẦN II. Thí sinh trả lời từ câu {startIdx} đến câu {endIdx}. Trong mỗi ý a), b), c), d) ở mỗi câu, thí sinh chọn đúng hoặc sai.");
                sb.AppendLine();

                foreach (var q in dsQuestions)
                {
                    string content = EnsureTerminator(q.Content);
                    sb.AppendLine($"Câu {globalIndex}. {content}");

                    string[] keys = { "a", "b", "c", "d" };
                    foreach (var k in keys)
                    {
                        string v = q.Options.ContainsKey(k) ? q.Options[k] : string.Empty;
                        sb.AppendLine($"{k}) {EnsureTerminator(v)}");
                    }
                    sb.AppendLine();
                    globalIndex++;
                }
            }

            if (tlnQuestions.Count > 0)
            {
                int startIdx = globalIndex;
                int endIdx = globalIndex + tlnQuestions.Count - 1;
                sb.AppendLine($"PHẦN III. Thí sinh trả lời từ câu {startIdx} đến câu {endIdx}.");
                sb.AppendLine();

                foreach (var q in tlnQuestions)
                {
                    string content = EnsureTerminator(q.Content);
                    sb.AppendLine($"Câu {globalIndex}. {content}");
                    sb.AppendLine("Đáp án: | | | | |");
                    sb.AppendLine();
                    globalIndex++;
                }
            }

            if (tlQuestions.Count > 0)
            {
                int startIdx = globalIndex;
                int endIdx = globalIndex + tlQuestions.Count - 1;
                sb.AppendLine($"PHẦN IV. Tự luận. Thí sinh trình bày lời giải từ câu {startIdx} đến câu {endIdx}.");
                sb.AppendLine();

                foreach (var q in tlQuestions)
                {
                    string content = EnsureTerminator(q.Content);
                    sb.AppendLine($"Câu {globalIndex}. {content}");
                    sb.AppendLine();
                    globalIndex++;
                }
            }

            sb.AppendLine("-------------------- HẾT --------------------");
            sb.AppendLine("(Thí sinh không được sử dụng tài liệu. Cán bộ coi thi không giải thích gì thêm)");
            sb.AppendLine();

            bool hasAnyAnswer = list.Any(q => !string.IsNullOrWhiteSpace(q.CorrectAnswer));
            if (hasAnyAnswer)
            {
                sb.AppendLine("═══════════════════════════════════════════════════════════════");
                sb.AppendLine("                      BẢNG ĐÁP ÁN");
                sb.AppendLine("═══════════════════════════════════════════════════════════════");

                if (tnQuestions.Count > 0)
                {
                    sb.AppendLine("PHẦN I (Trắc nghiệm nhiều lựa chọn):");
                    var ansList = new List<string>();
                    for (int i = 0; i < tnQuestions.Count; i++)
                    {
                        string ans = tnQuestions[i].CorrectAnswer;
                        if (string.IsNullOrWhiteSpace(ans)) ans = "?";
                        ansList.Add($"{i + 1}.{ans}");
                    }
                    for (int i = 0; i < ansList.Count; i += 10)
                    {
                        var chunk = ansList.Skip(i).Take(10);
                        sb.AppendLine(string.Join("\t", chunk));
                    }
                    sb.AppendLine();
                }

                if (dsQuestions.Count > 0)
                {
                    sb.AppendLine("PHẦN II (Trắc nghiệm Đúng/Sai):");
                    int dsIdx = 1;
                    foreach (var q in dsQuestions)
                    {
                        string ans = !string.IsNullOrWhiteSpace(q.CorrectAnswer) ? q.CorrectAnswer : "Đang cập nhật";
                        sb.AppendLine($"Câu {dsIdx}: {ans}");
                        dsIdx++;
                    }
                    sb.AppendLine();
                }

                if (tlnQuestions.Count > 0)
                {
                    sb.AppendLine("PHẦN III (Trả lời ngắn):");
                    int tlnIdx = 1;
                    foreach (var q in tlnQuestions)
                    {
                        string ans = !string.IsNullOrWhiteSpace(q.CorrectAnswer) ? q.CorrectAnswer : "Đang cập nhật";
                        sb.AppendLine($"Câu {tlnIdx}: {ans}");
                        tlnIdx++;
                    }
                    sb.AppendLine();
                }
            }

            bool hasAnySolution = list.Any(q => !string.IsNullOrWhiteSpace(q.Explanation));
            if (hasAnySolution || hasAnyAnswer)
            {
                sb.AppendLine("═══════════════════════════════════════════════════════════════");
                sb.AppendLine("                 HƯỚNG DẪN GIẢI CHI TIẾT");
                sb.AppendLine("═══════════════════════════════════════════════════════════════");

                int solIdx = 1;
                foreach (var q in list)
                {
                    sb.AppendLine($"Câu {solIdx}.");
                    if (!string.IsNullOrWhiteSpace(q.CorrectAnswer))
                    {
                        sb.AppendLine($"Đáp án: {q.CorrectAnswer}");
                    }

                    if (!string.IsNullOrWhiteSpace(q.Explanation))
                    {
                        string exp = FilterLatexItems(q.Explanation).Trim();
                        if (exp.StartsWith("Lời giải", StringComparison.OrdinalIgnoreCase) || exp.StartsWith("Hướng dẫn", StringComparison.OrdinalIgnoreCase))
                        {
                            sb.AppendLine(exp);
                        }
                        else
                        {
                            sb.AppendLine($"Lời giải:\n{exp}");
                        }
                    }
                    else
                    {
                        sb.AppendLine("Lời giải: (Đang cập nhật)");
                    }
                    sb.AppendLine();
                    solIdx++;
                }
            }

            return sb.ToString().TrimEnd();
        }

        private static string EnsureTerminator(string text)
        {
            text = (text ?? string.Empty).TrimEnd();
            if (string.IsNullOrEmpty(text)) return string.Empty;
            char last = text[text.Length - 1];
            if (last == '.' || last == '!' || last == '?' || last == ':' || last == ';') return text;
            return text + ".";
        }

        #endregion
    }
}
