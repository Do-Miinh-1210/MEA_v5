using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.RegularExpressions;

namespace MatrixExamAI.Shared.Validation
{
    /// <summary>
    /// Bộ tiền kiểm (Pre-flight Validator) phân tích cú pháp mã TikZ trước khi gọi pdflatex,
    /// phát hiện ngay các lỗi phổ biến trong mili-giây và hỗ trợ tự động sửa nhanh (Auto-Fix).
    /// </summary>
    public static class TikzPreflightValidator
    {
        private static readonly Regex CommandStartRegex = new Regex(@"^\s*\\(draw|node|coordinate|fill|path|addplot)\b", RegexOptions.Compiled);
        private static readonly Regex LineCapRegex = new Regex(@"\bline\s+cap\s*=\s*round\b", RegexOptions.IgnoreCase | RegexOptions.Compiled);
        private static readonly Regex TkzTabTypoRegex = new Regex(@"\\tkzTab(?:Vector|Variation|Vectors)\b", RegexOptions.Compiled);
        private static readonly Regex LegacyPatternNwRegex = new Regex(@"\bpattern\s*=\s*north\s*west\s*lines\b", RegexOptions.IgnoreCase | RegexOptions.Compiled);
        private static readonly Regex LegacyPatternNeRegex = new Regex(@"\bpattern\s*=\s*north\s*east\s*lines\b", RegexOptions.IgnoreCase | RegexOptions.Compiled);
        private static readonly Regex LegacyPatternColorRegex = new Regex(@"\bpattern\s+color\s*=\s*black(!70)?\b", RegexOptions.IgnoreCase | RegexOptions.Compiled);

        /// <summary>
        /// Thực hiện kiểm tra toàn bộ danh mục quy tắc cú pháp trên mã TikZ.
        /// </summary>
        public static List<ValidationIssue> Check(string? code)
        {
            var issues = new List<ValidationIssue>();

            if (string.IsNullOrWhiteSpace(code))
            {
                issues.Add(new ValidationIssue(IssueSeverity.Error, 0, "Mã TikZ rỗng.", "empty_code"));
                return issues;
            }

            string text = code!;

            CheckBalancedBraces(text, issues);
            CheckBeginEndPairs(text, issues);
            CheckTikzPicturePresent(text, issues);
            CheckAddPlotInAxis(text, issues);
            CheckPgfPlotsYVariable(text, issues);
            CheckImplicitMultiplication(text, issues);
            CheckLikelyMissingSemicolon(text, issues);
            CheckTkzTabCommands(text, issues);
            CheckForbiddenLineCap(text, issues);
            CheckLegacyPatterns(text, issues);
            CheckDocumentClassPresent(text, issues);
            CheckUnicodeMathOutsideDollar(text, issues);

            // Sắp xếp issues theo mức độ nghiêm trọng (Error -> Warning -> Info) rồi theo số dòng
            return issues
                .OrderBy(i => i.Severity)
                .ThenBy(i => i.Line)
                .ToList();
        }

        /// <summary>
        /// Kiểm tra xem mã nguồn có chứa lỗi nghiêm trọng (Error) khiến pdflatex chắc chắn thất bại hay không.
        /// </summary>
        public static bool HasBlockingErrors(string? code)
        {
            var issues = Check(code);
            return issues.Any(i => i.Severity == IssueSeverity.Error);
        }

        /// <summary>
        /// Áp dụng các bản vá tự động (Auto-Fix) đối với những lỗi có thể khắc phục an toàn.
        /// </summary>
        public static string AutoFix(string code)
        {
            if (string.IsNullOrWhiteSpace(code)) return string.Empty;

            string fixedCode = code;

            // 1. Loại bỏ \documentclass và preamble nếu người dùng vô tình dán cả tài liệu
            if (fixedCode.Contains("\\documentclass"))
            {
                var docMatch = Regex.Match(fixedCode, @"\\begin\{document\}\s*([\s\S]*?)\\end\{document\}");
                if (docMatch.Success)
                {
                    fixedCode = docMatch.Groups[1].Value.Trim();
                }
                else
                {
                    fixedCode = Regex.Replace(fixedCode, @"\\documentclass(?:\[[^\]]*\])?\{[^}]*\}", "").Trim();
                }
            }

            // 2. Sửa lỗi chính tả lệnh tkz-tab (\tkzTabVector -> \tkzTabVar)
            fixedCode = TkzTabTypoRegex.Replace(fixedCode, @"\tkzTabVar");

            // 3. Xóa line cap=round (quy tắc bắt buộc của Thầy Đỗ Minh)
            fixedCode = Regex.Replace(fixedCode, @",\s*line\s+cap\s*=\s*round", "", RegexOptions.IgnoreCase);
            fixedCode = Regex.Replace(fixedCode, @"line\s+cap\s*=\s*round\s*,\s*", "", RegexOptions.IgnoreCase);
            fixedCode = LineCapRegex.Replace(fixedCode, "");
            fixedCode = Regex.Replace(fixedCode, @"\[\s*\]", "");

            // 4. Chuẩn hóa pattern cũ sang patterns.meta
            fixedCode = LegacyPatternNwRegex.Replace(fixedCode, "pattern={Lines[angle=45, distance=4pt, line width=0.3pt]}");
            fixedCode = LegacyPatternNeRegex.Replace(fixedCode, "pattern={Lines[angle=135, distance=4pt, line width=0.3pt]}");
            fixedCode = LegacyPatternColorRegex.Replace(fixedCode, "pattern color=gray!70");

            return fixedCode.Trim();
        }

        // =========================================================================
        // CÁC QUY TẮC KIỂM TRA CHI TIẾT
        // =========================================================================

        private static void CheckBalancedBraces(string code, List<ValidationIssue> issues)
        {
            int openCount = 0;
            string[] lines = code.Split(new[] { "\r\n", "\r", "\n" }, StringSplitOptions.None);

            for (int i = 0; i < lines.Length; i++)
            {
                int lineNo = i + 1;
                string cleanLine = StripComments(lines[i]);

                foreach (char ch in cleanLine)
                {
                    if (ch == '{')
                    {
                        openCount++;
                    }
                    else if (ch == '}')
                    {
                        openCount--;
                        if (openCount < 0)
                        {
                            issues.Add(new ValidationIssue(
                                IssueSeverity.Error,
                                lineNo,
                                "Thừa dấu `}` — đóng ngoặc nhiều hơn mở.",
                                "balanced_braces"));
                            openCount = 0; // Reset để bắt tiếp
                        }
                    }
                }
            }

            if (openCount > 0)
            {
                issues.Add(new ValidationIssue(
                    IssueSeverity.Error,
                    0,
                    $"Thiếu {openCount} dấu `}}` — không cân bằng ngoặc nhọn.",
                    "balanced_braces"));
            }
        }

        private static void CheckBeginEndPairs(string code, List<ValidationIssue> issues)
        {
            var stack = new Stack<(int Line, string Env)>();
            string[] lines = code.Split(new[] { "\r\n", "\r", "\n" }, StringSplitOptions.None);

            var beginRegex = new Regex(@"\\begin\{([a-zA-Z0-9*]+)\}");
            var endRegex = new Regex(@"\\end\{([a-zA-Z0-9*]+)\}");

            for (int i = 0; i < lines.Length; i++)
            {
                int lineNo = i + 1;
                string cleanLine = StripComments(lines[i]);

                foreach (Match m in beginRegex.Matches(cleanLine))
                {
                    stack.Push((lineNo, m.Groups[1].Value));
                }

                foreach (Match m in endRegex.Matches(cleanLine))
                {
                    string env = m.Groups[1].Value;
                    if (stack.Count == 0)
                    {
                        issues.Add(new ValidationIssue(
                            IssueSeverity.Error,
                            lineNo,
                            $"Lệnh `\\end{{{env}}}` không có `\\begin` tương ứng.",
                            "begin_end_pairs"));
                        continue;
                    }

                    var top = stack.Pop();
                    if (!string.Equals(top.Env, env, StringComparison.Ordinal))
                    {
                        issues.Add(new ValidationIssue(
                            IssueSeverity.Error,
                            lineNo,
                            $"Lệnh `\\end{{{env}}}` không khớp với `\\begin{{{top.Env}}}` ở dòng {top.Line}.",
                            "begin_end_pairs"));
                    }
                }
            }

            while (stack.Count > 0)
            {
                var unclosed = stack.Pop();
                issues.Add(new ValidationIssue(
                    IssueSeverity.Error,
                    unclosed.Line,
                    $"Lệnh `\\begin{{{unclosed.Env}}}` không có `\\end` tương ứng.",
                    "begin_end_pairs"));
            }
        }

        private static void CheckTikzPicturePresent(string code, List<ValidationIssue> issues)
        {
            if (code.Contains("\\begin{tikzpicture}") ||
                code.Contains("\\tkzTabInit") ||
                code.Contains("\\begin{circuitikz}") ||
                code.Contains("\\begin{tabular}"))
            {
                return;
            }

            issues.Add(new ValidationIssue(
                IssueSeverity.Error,
                0,
                "Không tìm thấy khối `\\begin{tikzpicture}` hoặc `\\begin{circuitikz}` trong mã nguồn.",
                "tikzpicture_present"));
        }

        private static void CheckAddPlotInAxis(string code, List<ValidationIssue> issues)
        {
            int inAxis = 0;
            string[] lines = code.Split(new[] { "\r\n", "\r", "\n" }, StringSplitOptions.None);

            for (int i = 0; i < lines.Length; i++)
            {
                int lineNo = i + 1;
                string cleanLine = StripComments(lines[i]);

                if (cleanLine.Contains("\\begin{axis}") || cleanLine.Contains("\\begin{semilogxaxis}") ||
                    cleanLine.Contains("\\begin{semilogyaxis}") || cleanLine.Contains("\\begin{loglogaxis}"))
                {
                    inAxis++;
                }

                if (cleanLine.Contains("\\end{axis}") || cleanLine.Contains("\\end{semilogxaxis}") ||
                    cleanLine.Contains("\\end{semilogyaxis}") || cleanLine.Contains("\\end{loglogaxis}"))
                {
                    inAxis = Math.Max(0, inAxis - 1);
                }

                if (inAxis == 0 && cleanLine.Contains("\\addplot"))
                {
                    issues.Add(new ValidationIssue(
                        IssueSeverity.Error,
                        lineNo,
                        "Lệnh `\\addplot` phải nằm bên trong môi trường `\\begin{axis}...\\end{axis}`.",
                        "addplot_in_axis"));
                }
            }
        }

        private static void CheckPgfPlotsYVariable(string code, List<ValidationIssue> issues)
        {
            string[] lines = code.Split(new[] { "\r\n", "\r", "\n" }, StringSplitOptions.None);
            var yParametricRegex = new Regex(@"\([^)]*\by\b[^)]*\)");

            for (int i = 0; i < lines.Length; i++)
            {
                int lineNo = i + 1;
                string cleanLine = StripComments(lines[i]);

                if (cleanLine.Contains("\\addplot") && cleanLine.Contains("(") && !cleanLine.Contains("variable="))
                {
                    if (yParametricRegex.IsMatch(cleanLine))
                    {
                        issues.Add(new ValidationIssue(
                            IssueSeverity.Warning,
                            lineNo,
                            "Pgfplots: phát hiện dùng `y` làm biến tự do — hãy khai báo `variable=\\t` và dùng `\\t` thay `y`.",
                            "pgfplots_y_variable"));
                    }
                }
            }
        }

        private static void CheckImplicitMultiplication(string code, List<ValidationIssue> issues)
        {
            string[] lines = code.Split(new[] { "\r\n", "\r", "\n" }, StringSplitOptions.None);
            var implicitMultRegex = new Regex(@"\b\d+[a-zA-Z]\b");
            var unitRegex = new Regex(@"\b\d+(pt|cm|mm|in|em|ex)\b", RegexOptions.IgnoreCase);

            for (int i = 0; i < lines.Length; i++)
            {
                int lineNo = i + 1;
                string cleanLine = StripComments(lines[i]);

                if (cleanLine.Contains("\\addplot"))
                {
                    var matches = Regex.Matches(cleanLine, @"\{([^{}]+)\}");
                    foreach (Match m in matches)
                    {
                        string expr = m.Groups[1].Value;
                        if (implicitMultRegex.IsMatch(expr) && !unitRegex.IsMatch(expr))
                        {
                            issues.Add(new ValidationIssue(
                                IssueSeverity.Warning,
                                lineNo,
                                $"Biểu thức pgfplots `{expr}` có thể thiếu toán tử nhân `*` (ví dụ: `2x` nên viết là `2*x`).",
                                "implicit_multiplication",
                                fixable: true));
                            break;
                        }
                    }
                }
            }
        }

        private static void CheckLikelyMissingSemicolon(string code, List<ValidationIssue> issues)
        {
            string[] lines = code.Split(new[] { "\r\n", "\r", "\n" }, StringSplitOptions.None);

            for (int i = 0; i < lines.Length; i++)
            {
                int lineNo = i + 1;
                string cleanLine = StripComments(lines[i]).Trim();

                if (string.IsNullOrEmpty(cleanLine)) continue;
                if (!CommandStartRegex.IsMatch(cleanLine)) continue;

                // Các trường hợp hợp lệ không cần kết thúc bằng ; ngay dòng này
                if (cleanLine.EndsWith(";") || cleanLine.EndsWith("{") || cleanLine.EndsWith(",")) continue;
                if (cleanLine.Contains("\\foreach") || cleanLine.EndsWith("}")) continue;
                if (cleanLine.StartsWith("\\path") && !cleanLine.Contains(";")) continue; // \path node ...

                issues.Add(new ValidationIssue(
                    IssueSeverity.Warning,
                    lineNo,
                    "Có thể thiếu dấu chấm phẩy (;) ở cuối câu lệnh TikZ.",
                    "missing_semicolon"));
            }
        }

        private static void CheckTkzTabCommands(string code, List<ValidationIssue> issues)
        {
            string[] lines = code.Split(new[] { "\r\n", "\r", "\n" }, StringSplitOptions.None);

            for (int i = 0; i < lines.Length; i++)
            {
                int lineNo = i + 1;
                string cleanLine = StripComments(lines[i]);

                var match = TkzTabTypoRegex.Match(cleanLine);
                if (match.Success)
                {
                    issues.Add(new ValidationIssue(
                        IssueSeverity.Error,
                        lineNo,
                        $"Lệnh `{match.Value}` không tồn tại trong gói tkz-tab — lệnh chuẩn là `\\tkzTabVar`.",
                        "invalid_tkztab_command",
                        fixable: true));
                }
            }
        }

        private static void CheckForbiddenLineCap(string code, List<ValidationIssue> issues)
        {
            string[] lines = code.Split(new[] { "\r\n", "\r", "\n" }, StringSplitOptions.None);

            for (int i = 0; i < lines.Length; i++)
            {
                int lineNo = i + 1;
                string cleanLine = StripComments(lines[i]);

                if (LineCapRegex.IsMatch(cleanLine))
                {
                    issues.Add(new ValidationIssue(
                        IssueSeverity.Warning,
                        lineNo,
                        "Phát hiện `line cap=round` — quy tắc Thầy Đỗ Minh cấm dùng thuộc tính này.",
                        "forbidden_line_cap",
                        fixable: true));
                }
            }
        }

        private static void CheckLegacyPatterns(string code, List<ValidationIssue> issues)
        {
            string[] lines = code.Split(new[] { "\r\n", "\r", "\n" }, StringSplitOptions.None);

            for (int i = 0; i < lines.Length; i++)
            {
                int lineNo = i + 1;
                string cleanLine = StripComments(lines[i]);

                if (LegacyPatternNwRegex.IsMatch(cleanLine) || LegacyPatternNeRegex.IsMatch(cleanLine))
                {
                    issues.Add(new ValidationIssue(
                        IssueSeverity.Info,
                        lineNo,
                        "Khuyến nghị dùng `patterns.meta` (Lines[angle=45, distance=4pt, line width=0.3pt]) thay vì pattern cũ.",
                        "legacy_pattern",
                        fixable: true));
                }
            }
        }

        private static void CheckDocumentClassPresent(string code, List<ValidationIssue> issues)
        {
            if (code.Contains("\\documentclass"))
            {
                issues.Add(new ValidationIssue(
                    IssueSeverity.Warning,
                    1,
                    "Mã nguồn có chứa `\\documentclass` — hệ thống tự động bọc preamble, bạn nên loại bỏ để tránh xung đột.",
                    "documentclass_present",
                    fixable: true));
            }
        }

        private static void CheckUnicodeMathOutsideDollar(string code, List<ValidationIssue> issues)
        {
            const string unicodeMath = "²³√≠≤≥πα∫∑∞×÷±";
            string[] lines = code.Split(new[] { "\r\n", "\r", "\n" }, StringSplitOptions.None);

            for (int i = 0; i < lines.Length; i++)
            {
                int lineNo = i + 1;
                string cleanLine = StripComments(lines[i]);

                // Bóc tách các phần nằm ngoài $...$
                bool inMath = false;
                var outsideChars = new List<char>();

                foreach (char ch in cleanLine)
                {
                    if (ch == '$')
                    {
                        inMath = !inMath;
                    }
                    else if (!inMath)
                    {
                        outsideChars.Add(ch);
                    }
                }

                string outsideStr = new string(outsideChars.ToArray());
                foreach (char u in unicodeMath)
                {
                    if (outsideStr.IndexOf(u) >= 0)
                    {
                        issues.Add(new ValidationIssue(
                            IssueSeverity.Info,
                            lineNo,
                            $"Ký hiệu toán học `{u}` nằm ngoài `$...$` — nên đặt trong môi trường toán học hoặc dùng lệnh LaTeX.",
                            "unicode_math_outside_dollar"));
                        break;
                    }
                }
            }
        }

        private static string StripComments(string line)
        {
            int idx = line.IndexOf('%');
            while (idx >= 0)
            {
                if (idx == 0 || line[idx - 1] != '\\')
                {
                    return line.Substring(0, idx);
                }
                idx = line.IndexOf('%', idx + 1);
            }
            return line;
        }
    }
}
