using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Text.RegularExpressions;
using MatrixExamAI.Shared.Extensibility;

namespace MatrixExamAI.Desktop.Services
{
    public enum QcSeverity
    {
        Info,
        Warning,
        Error
    }

    public class QcIssue
    {
        public int QuestionNumber { get; set; }
        public string QuestionCode { get; set; } = string.Empty;
        public string RuleName { get; set; } = string.Empty;
        public QcSeverity Severity { get; set; } = QcSeverity.Warning;
        public string Description { get; set; } = string.Empty;
        public string Snippet { get; set; } = string.Empty;
    }

    public class QcInspectionReport
    {
        public DateTime Timestamp { get; set; } = DateTime.Now;
        public int TotalQuestions { get; set; }
        public List<QcIssue> Issues { get; set; } = new List<QcIssue>();

        public int ErrorCount => Issues.Count(i => i.Severity == QcSeverity.Error);
        public int WarningCount => Issues.Count(i => i.Severity == QcSeverity.Warning);
        public int InfoCount => Issues.Count(i => i.Severity == QcSeverity.Info);
        public bool IsPassed => ErrorCount == 0;

        public string SummaryText
        {
            get
            {
                if (IsPassed && WarningCount == 0)
                {
                    return $"Đề thi hợp lệ: 0 lỗi, 0 cảnh báo ({TotalQuestions} câu kiểm tra)";
                }
                if (IsPassed)
                {
                    return $"Đề thi hợp lệ: 0 lỗi nghiêm trọng, {WarningCount} cảnh báo ({TotalQuestions} câu)";
                }
                return $"Phát hiện {ErrorCount} lỗi nghiêm trọng, {WarningCount} cảnh báo ({TotalQuestions} câu)";
            }
        }

        public string DetailedReportText { get; set; } = string.Empty;
    }

    public class AutoFixResult
    {
        public string FixedContent { get; set; } = string.Empty;
        public int FixesCount { get; set; }
        public List<string> AppliedFixes { get; set; } = new List<string>();
    }

    /// <summary>
    /// Dịch vụ Thẩm định Đề thi (Quality Control - QC) tự động:
    /// Kiểm tra trùng lặp phương án, thiếu đáp án đúng, lỗi cú pháp LaTeX, vi phạm chuẩn format BGD.
    /// Tích hợp cơ chế AI Auto-Fix tự động sửa lỗi cú pháp và định dạng.
    /// </summary>
    public class QcInspectionService
    {
        private static readonly Regex DollarRegex = new Regex(@"(?<!\\)\$", RegexOptions.Compiled);
        private static readonly Regex CitationRegex = new Regex(@"\[(?:cite|source|tham khảo):[^\]]+\]", RegexOptions.IgnoreCase | RegexOptions.Compiled);
        private static readonly Regex ItemNoSpaceRegex = new Regex(@"\\item([0-9A-Za-zÀ-ỹ])", RegexOptions.Compiled);
        private static readonly Regex BeginEnvRegex = new Regex(@"\\begin\{([a-zA-Z*]+)\}", RegexOptions.Compiled);
        private static readonly Regex EndEnvRegex = new Regex(@"\\end\{([a-zA-Z*]+)\}", RegexOptions.Compiled);

        /// <summary>
        /// Quét và kiểm tra chất lượng từ văn bản đề thi thô.
        /// </summary>
        public QcInspectionReport InspectText(
            string text,
            bool checkDupOptions = true,
            bool checkMissingAns = true,
            bool checkLatexSyntax = true,
            bool checkFormat = true)
        {
            var report = new QcInspectionReport();
            if (string.IsNullOrWhiteSpace(text))
            {
                report.DetailedReportText = "[THÔNG BÁO] Chưa có nội dung đề thi để thẩm định QC.";
                return report;
            }

            // Tách các khối câu hỏi theo định dạng % Câu X hoặc Câu X: hoặc ===CAU===
            var parsedQuestions = ParseQuestionsFromRawText(text);
            report.TotalQuestions = parsedQuestions.Count > 0 ? parsedQuestions.Count : 1;

            if (parsedQuestions.Count > 0)
            {
                for (int i = 0; i < parsedQuestions.Count; i++)
                {
                    var q = parsedQuestions[i];
                    InspectSingleQuestion(q, i + 1, report, checkDupOptions, checkMissingAns, checkLatexSyntax, checkFormat);
                }
            }
            else
            {
                // Kiểm tra text tổng thể
                InspectGlobalText(text, report, checkLatexSyntax, checkFormat);
            }

            BuildReportText(report);
            return report;
        }

        /// <summary>
        /// Quét và kiểm tra danh sách câu hỏi cấu trúc QuestionItem.
        /// </summary>
        public QcInspectionReport InspectQuestions(
            IEnumerable<QuestionItem> questions,
            bool checkDupOptions = true,
            bool checkMissingAns = true,
            bool checkLatexSyntax = true,
            bool checkFormat = true)
        {
            var report = new QcInspectionReport();
            var list = questions?.ToList() ?? new List<QuestionItem>();
            report.TotalQuestions = list.Count;

            int idx = 1;
            foreach (var q in list)
            {
                InspectSingleQuestion(q, idx++, report, checkDupOptions, checkMissingAns, checkLatexSyntax, checkFormat);
            }

            BuildReportText(report);
            return report;
        }

        private void InspectSingleQuestion(
            QuestionItem q,
            int questionNumber,
            QcInspectionReport report,
            bool checkDupOptions,
            bool checkMissingAns,
            bool checkLatexSyntax,
            bool checkFormat)
        {
            string code = !string.IsNullOrEmpty(q.QuestionCode) ? q.QuestionCode : $"Câu {questionNumber}";

            // 1. Kiểm tra Trùng lặp phương án
            if (checkDupOptions && q.Options != null && q.Options.Count > 1)
            {
                var trimmedOptions = q.Options
                    .Where(kv => !string.IsNullOrWhiteSpace(kv.Value))
                    .Select(kv => new { Key = kv.Key, Normalized = kv.Value.Trim().ToLowerInvariant(), Original = kv.Value.Trim() })
                    .ToList();

                var duplicates = trimmedOptions
                    .GroupBy(x => x.Normalized)
                    .Where(g => g.Count() > 1)
                    .ToList();

                foreach (var dupGroup in duplicates)
                {
                    var keys = string.Join(", ", dupGroup.Select(x => x.Key));
                    report.Issues.Add(new QcIssue
                    {
                        QuestionNumber = questionNumber,
                        QuestionCode = code,
                        RuleName = "Trùng lặp phương án",
                        Severity = QcSeverity.Error,
                        Description = $"Các phương án ({keys}) có nội dung hoàn toàn trùng lặp: \"{dupGroup.First().Original}\"",
                        Snippet = dupGroup.First().Original
                    });
                }
            }

            // 2. Kiểm tra Thiếu phương án (cho MultipleChoice4)
            if (checkDupOptions && (q.QuestionType == "MultipleChoice4" || q.QuestionType == "TN"))
            {
                if (q.Options == null || q.Options.Count < 4)
                {
                    int count = q.Options?.Count ?? 0;
                    report.Issues.Add(new QcIssue
                    {
                        QuestionNumber = questionNumber,
                        QuestionCode = code,
                        RuleName = "Thiếu phương án trắc nghiệm",
                        Severity = QcSeverity.Error,
                        Description = $"Câu trắc nghiệm 4 lựa chọn chỉ có {count} phương án (yêu cầu tối thiểu 4 phương án A, B, C, D).",
                        Snippet = q.Content
                    });
                }
            }

            // 3. Kiểm tra Thiếu đáp án đúng
            if (checkMissingAns)
            {
                bool missing = string.IsNullOrWhiteSpace(q.CorrectAnswer);
                if (missing)
                {
                    report.Issues.Add(new QcIssue
                    {
                        QuestionNumber = questionNumber,
                        QuestionCode = code,
                        RuleName = "Thiếu đáp án đúng",
                        Severity = QcSeverity.Error,
                        Description = "Câu hỏi chưa thiết lập đáp án đúng (CorrectAnswer rỗng).",
                        Snippet = q.Content
                    });
                }
                else if (q.Options != null && q.Options.Count > 0)
                {
                    string ansKey = q.CorrectAnswer.Trim().ToUpperInvariant();
                    if (!q.Options.ContainsKey(ansKey))
                    {
                        // Kiểm tra xem CorrectAnswer có phải là nội dung text của một phương án không
                        bool matchesValue = q.Options.Values.Any(v => v.Trim().Equals(q.CorrectAnswer.Trim(), StringComparison.OrdinalIgnoreCase));
                        if (!matchesValue && !q.QuestionType.Contains("Short") && !q.QuestionType.Contains("TrueFalse"))
                        {
                            report.Issues.Add(new QcIssue
                            {
                                QuestionNumber = questionNumber,
                                QuestionCode = code,
                                RuleName = "Đáp án không khớp phương án",
                                Severity = QcSeverity.Warning,
                                Description = $"Đáp án đúng '{q.CorrectAnswer}' không tồn tại trong danh sách khóa phương án (A, B, C, D).",
                                Snippet = q.CorrectAnswer
                            });
                        }
                    }
                }
            }

            // 4. Kiểm tra Cú pháp LaTeX
            if (checkLatexSyntax)
            {
                string fullText = (q.Content ?? "") + " " + string.Join(" ", q.Options?.Values ?? Enumerable.Empty<string>()) + " " + (q.Explanation ?? "");

                // Cân xứng dấu $
                int dollarCount = DollarRegex.Matches(fullText).Count;
                if ((dollarCount % 2) != 0)
                {
                    report.Issues.Add(new QcIssue
                    {
                        QuestionNumber = questionNumber,
                        QuestionCode = code,
                        RuleName = "Lỗi cú pháp LaTeX ($ không cân xứng)",
                        Severity = QcSeverity.Error,
                        Description = $"Phát hiện số lượng dấu $ không chẵn ({dollarCount} dấu $). Có công thức chưa được đóng dấu $ hợp lệ.",
                        Snippet = ExtractFirstBrokenDollarSnippet(fullText)
                    });
                }

                // Cân xứng ngoặc nhọn { và }
                int openBraces = fullText.Count(c => c == '{');
                int closeBraces = fullText.Count(c => c == '}');
                if (openBraces != closeBraces)
                {
                    report.Issues.Add(new QcIssue
                    {
                        QuestionNumber = questionNumber,
                        QuestionCode = code,
                        RuleName = "Lỗi cú pháp LaTeX (Dấu { } không cân xứng)",
                        Severity = QcSeverity.Error,
                        Description = $"Phát hiện số lượng dấu {{ ({openBraces}) và }} ({closeBraces}) không khớp nhau.",
                        Snippet = ""
                    });
                }

                // Kiểm tra cặp \begin{} và \end{}
                var begins = BeginEnvRegex.Matches(fullText).Cast<Match>().Select(m => m.Groups[1].Value).ToList();
                var ends = EndEnvRegex.Matches(fullText).Cast<Match>().Select(m => m.Groups[1].Value).ToList();
                if (begins.Count != ends.Count)
                {
                    report.Issues.Add(new QcIssue
                    {
                        QuestionNumber = questionNumber,
                        QuestionCode = code,
                        RuleName = "Môi trường LaTeX chưa đóng",
                        Severity = QcSeverity.Error,
                        Description = $"Phát hiện {begins.Count} môi trường \\begin nhưng chỉ có {ends.Count} thẻ \\end.",
                        Snippet = string.Join(", ", begins)
                    });
                }
            }

            // 5. Kiểm tra Chuẩn format BGD & Rác AI
            if (checkFormat)
            {
                string content = q.Content ?? string.Empty;

                // Citation rác AI: [cite: ...]
                var citationMatch = CitationRegex.Match(content);
                if (citationMatch.Success)
                {
                    report.Issues.Add(new QcIssue
                    {
                        QuestionNumber = questionNumber,
                        QuestionCode = code,
                        RuleName = "Tồn tại citation rác từ AI",
                        Severity = QcSeverity.Warning,
                        Description = $"Phát hiện nhãn trích dẫn AI '{citationMatch.Value}'. Cần loại bỏ trước khi in đề.",
                        Snippet = citationMatch.Value
                    });
                }

                // Dính số đầu chữ \item1.
                var itemMatch = ItemNoSpaceRegex.Match(content);
                if (itemMatch.Success)
                {
                    report.Issues.Add(new QcIssue
                    {
                        QuestionNumber = questionNumber,
                        QuestionCode = code,
                        RuleName = "Dính ký tự thẻ \\item",
                        Severity = QcSeverity.Warning,
                        Description = $"Thẻ \\item bị dính liền ký tự: '{itemMatch.Value}'. Cần có dấu cách giữa \\item và nội dung.",
                        Snippet = itemMatch.Value
                    });
                }

                // Dùng \begin{aligned} thay vì \begin{align} ở công thức độc lập
                if (content.Contains(@"\begin{aligned}") && !content.Contains(@"\left\{") && !content.Contains(@"\begin{cases}"))
                {
                    report.Issues.Add(new QcIssue
                    {
                        QuestionNumber = questionNumber,
                        QuestionCode = code,
                        RuleName = "Khuyến nghị chuẩn hóa hệ phương trình",
                        Severity = QcSeverity.Info,
                        Description = "Phát hiện môi trường \\begin{aligned} độc lập. Nên chuẩn hóa sang \\begin{align} theo quy chuẩn 2025.",
                        Snippet = @"\begin{aligned}"
                    });
                }
            }
        }

        private void InspectGlobalText(string text, QcInspectionReport report, bool checkLatexSyntax, bool checkFormat)
        {
            if (checkLatexSyntax)
            {
                int dollarCount = DollarRegex.Matches(text).Count;
                if ((dollarCount % 2) != 0)
                {
                    report.Issues.Add(new QcIssue
                    {
                        QuestionNumber = 0,
                        QuestionCode = "TOÀN VĂN",
                        RuleName = "Lỗi cú pháp LaTeX ($ không cân xứng)",
                        Severity = QcSeverity.Error,
                        Description = $"Số lượng dấu $ trong tài liệu là số lẻ ({dollarCount}). Có ít nhất 1 công thức toán chưa đóng dấu $.",
                        Snippet = ExtractFirstBrokenDollarSnippet(text)
                    });
                }
            }

            if (checkFormat)
            {
                var citMatch = CitationRegex.Match(text);
                if (citMatch.Success)
                {
                    report.Issues.Add(new QcIssue
                    {
                        QuestionNumber = 0,
                        QuestionCode = "TOÀN VĂN",
                        RuleName = "Tồn tại citation rác từ AI",
                        Severity = QcSeverity.Warning,
                        Description = $"Phát hiện nhãn trích dẫn '{citMatch.Value}' trong tài liệu.",
                        Snippet = citMatch.Value
                    });
                }
            }
        }

        /// <summary>
        /// AI Auto-Fix tự động chuẩn hóa cú pháp LaTeX, sửa lỗi dính chữ, loại bỏ citation rác.
        /// </summary>
        public AutoFixResult AutoFix(string text)
        {
            var result = new AutoFixResult();
            if (string.IsNullOrEmpty(text))
            {
                result.FixedContent = string.Empty;
                return result;
            }

            string fixedText = text;

            // 1. Loại bỏ các nhãn citation rác: [cite: 1], [source: abc]
            int citCount = CitationRegex.Matches(fixedText).Count;
            if (citCount > 0)
            {
                fixedText = CitationRegex.Replace(fixedText, "");
                result.AppliedFixes.Add($"Đã loại bỏ {citCount} nhãn citation rác từ AI ([cite: ...]).");
                result.FixesCount += citCount;
            }

            // 2. Sửa lỗi dính chữ \item1. -> \item 1., \itemĐúng -> \item Đúng
            int itemFixCount = ItemNoSpaceRegex.Matches(fixedText).Count;
            if (itemFixCount > 0)
            {
                fixedText = ItemNoSpaceRegex.Replace(fixedText, @"\item $1");
                result.AppliedFixes.Add($"Đã chèn dấu cách cho {itemFixCount} thẻ \\item bị dính liền ký tự.");
                result.FixesCount += itemFixCount;
            }

            // 3. Chuẩn hóa hệ phương trình \begin{aligned} -> \begin{align}
            string beforeAlign = fixedText;
            fixedText = QuestionParserEngine.NormalizeSystemEquationsAndAlign(fixedText);
            if (fixedText != beforeAlign)
            {
                result.AppliedFixes.Add("Đã chuẩn hóa các môi trường hệ phương trình sang \\begin{align}.");
                result.FixesCount++;
            }

            // 4. Kẹp chuẩn công thức toán học và sửa dấu $ không cân xứng
            int dollarCount = DollarRegex.Matches(fixedText).Count;
            if ((dollarCount % 2) != 0)
            {
                // Thêm dấu $ vào cuối dòng có công thức bị hở
                var lines = fixedText.Split(new[] { "\r\n", "\r", "\n" }, StringSplitOptions.None);
                for (int i = 0; i < lines.Length; i++)
                {
                    int lineDollars = DollarRegex.Matches(lines[i]).Count;
                    if ((lineDollars % 2) != 0)
                    {
                        lines[i] = lines[i].TrimEnd() + "$";
                        result.AppliedFixes.Add($"Đã tự động đóng dấu $ bị thiếu ở dòng {i + 1}.");
                        result.FixesCount++;
                        break;
                    }
                }
                fixedText = string.Join("\r\n", lines);
            }

            // 5. Chuẩn hóa khoảng trắng thừa
            fixedText = Regex.Replace(fixedText, @"[ \t]+(?=\r?\n)", "");

            result.FixedContent = fixedText;
            return result;
        }

        private static List<QuestionItem> ParseQuestionsFromRawText(string text)
        {
            var list = new List<QuestionItem>();
            if (string.IsNullOrWhiteSpace(text)) return list;

            // Tách theo % Câu X hoặc Câu X:
            var questionBlocks = Regex.Split(text, @"(?=(?:^|\n)\s*(?:%\s*Câu|\bCâu\s*\d+[\s\.:]))", RegexOptions.Multiline);

            int qNum = 1;
            foreach (var block in questionBlocks)
            {
                string trimmed = block.Trim();
                if (string.IsNullOrWhiteSpace(trimmed)) continue;

                var item = new QuestionItem
                {
                    QuestionCode = $"Câu {qNum}",
                    Content = trimmed,
                    QuestionType = "MultipleChoice4"
                };

                // Trích xuất các phương án A. B. C. D.
                var optMatches = Regex.Matches(trimmed, @"(?:^|\s)([A-D])[\.\)]\s*(.*?)(?=(?:[A-D][\.\)]|$))", RegexOptions.Singleline);
                if (optMatches.Count >= 2)
                {
                    item.Options = new Dictionary<string, string>();
                    foreach (Match m in optMatches)
                    {
                        string letter = m.Groups[1].Value.ToUpperInvariant();
                        string val = m.Groups[2].Value.Trim();
                        // Dọn dẹp dấu chấm hoặc ngắt dòng cuối phương án
                        val = Regex.Replace(val, @"[\r\n]+", " ").Trim();
                        item.Options[letter] = val;
                    }
                }

                // Trích xuất đáp án nếu có
                var ansMatch = Regex.Match(trimmed, @"(?:Đáp án|Đ/a|Key|Answer)[\s:]*([A-D0-9\.\,\-]+)", RegexOptions.IgnoreCase);
                if (ansMatch.Success)
                {
                    item.CorrectAnswer = ansMatch.Groups[1].Value.Trim().ToUpperInvariant();
                }

                list.Add(item);
                qNum++;
            }

            return list;
        }

        private static string ExtractFirstBrokenDollarSnippet(string text)
        {
            var lines = text.Split(new[] { "\r\n", "\r", "\n" }, StringSplitOptions.None);
            foreach (var l in lines)
            {
                if ((DollarRegex.Matches(l).Count % 2) != 0)
                {
                    return l.Trim();
                }
            }
            return text.Length > 80 ? text.Substring(0, 80) + "..." : text;
        }

        private static void BuildReportText(QcInspectionReport report)
        {
            var sb = new StringBuilder();
            sb.AppendLine("[KẾT QUẢ THẨM ĐỊNH ĐỀ THI - BỘ GIÁO DỤC 2025/2026]");
            sb.AppendLine($"Thời gian quét: {report.Timestamp:dd/MM/yyyy HH:mm:ss}");
            sb.AppendLine($"Số lượng câu hỏi thẩm định: {report.TotalQuestions} câu");
            sb.AppendLine($"Trạng thái tổng quan: {report.SummaryText}");
            sb.AppendLine(new string('=', 70));

            if (report.Issues.Count == 0)
            {
                sb.AppendLine("[✓ THÀNH CÔNG] 100% câu hỏi đạt tiêu chuẩn chất lượng:");
                sb.AppendLine("  • Không phát hiện câu hỏi nào thiếu đáp án đúng.");
                sb.AppendLine("  • Không có phương án trắc nghiệm nào bị trùng lặp nội dung.");
                sb.AppendLine("  • Các biểu thức toán học đều đóng mở dấu $ cân xứng.");
                sb.AppendLine("  • Định dạng các thẻ \\item, môi trường align đạt chuẩn Bộ GD&ĐT.");
            }
            else
            {
                // Danh sách lỗi & cảnh báo chi tiết
                sb.AppendLine($"DANH SÁCH {report.Issues.Count} VẤN ĐỀ ĐƯỢC PHÁT HIỆN:");
                sb.AppendLine();

                int idx = 1;
                foreach (var issue in report.Issues)
                {
                    string tag = issue.Severity == QcSeverity.Error ? "[✗ LỖI NGHIÊM TRỌNG]" :
                                 issue.Severity == QcSeverity.Warning ? "[! CẢNH BÁO]" : "[ℹ THÔNG TIN]";

                    sb.AppendLine($"{idx++}. {tag} [{issue.QuestionCode}] — {issue.RuleName}");
                    sb.AppendLine($"   Chi tiết: {issue.Description}");
                    if (!string.IsNullOrWhiteSpace(issue.Snippet))
                    {
                        sb.AppendLine($"   Đoạn trích: \"{issue.Snippet}\"");
                    }
                    sb.AppendLine();
                }
            }

            sb.AppendLine(new string('=', 70));
            if (report.IsPassed)
            {
                sb.AppendLine("KẾT LUẬN: ĐỀ THI ĐỦ ĐIỀU KIỆN XUẤT BẢN WORD, IN ẤN VÀ TỔ CHỨC KIỂM TRA.");
            }
            else
            {
                sb.AppendLine("KẾT LUẬN: ĐỀ THI CẦN ĐƯỢC CHỈNH SỬA CÁC LỖI TRÊN TRƯỚC KHI XUẤT BẢN (Hoặc bấm 'AI Tự động sửa lỗi').");
            }

            report.DetailedReportText = sb.ToString();
        }
    }
}
