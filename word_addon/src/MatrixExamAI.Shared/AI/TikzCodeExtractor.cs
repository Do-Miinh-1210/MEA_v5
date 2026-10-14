using System.Text.RegularExpressions;

namespace MatrixExamAI.Shared.AI
{
    /// <summary>
    /// Bộ tiện ích trích xuất và chuẩn hóa mã nguồn TikZ từ phản hồi thô của AI hoặc tài liệu LaTeX.
    /// </summary>
    public static class TikzCodeExtractor
    {
        private static readonly Regex DocumentRegex = new Regex(@"\\begin\{document\}([\s\S]*?)\\end\{document\}", RegexOptions.Compiled);
        private static readonly Regex FenceRegex = new Regex(@"```(?:latex|tex|tikz)?\s*([\s\S]*?)```", RegexOptions.Compiled);
        private static readonly Regex TikzRegex = new Regex(@"(\\begin\{tikzpicture\}[\s\S]*?\\end\{tikzpicture\})", RegexOptions.Compiled);
        private static readonly Regex CircuitRegex = new Regex(@"(\\begin\{circuitikz\}[\s\S]*?\\end\{circuitikz\})", RegexOptions.Compiled);
        private static readonly Regex AxisRegex = new Regex(@"(\\begin\{axis\}[\s\S]*?\\end\{axis\})", RegexOptions.Compiled);
        private static readonly Regex DocumentClassRegex = new Regex(@"\\documentclass(?:\[[^\]]*\])?\{[^}]*\}", RegexOptions.Compiled);

        /// <summary>
        /// Trích xuất mã TikZ thuần túy bắt đầu từ \begin{tikzpicture} đến \end{tikzpicture} (hoặc circuitikz).
        /// </summary>
        public static string ExtractTikzCode(string? rawText)
        {
            if (string.IsNullOrWhiteSpace(rawText))
            {
                return string.Empty;
            }

            string text = rawText!.Trim();

            // 1. Trích xuất giữa \begin{document} và \end{document}
            var docMatch = DocumentRegex.Match(text);
            if (docMatch.Success)
            {
                text = docMatch.Groups[1].Value.Trim();
            }

            // 2. Bỏ qua markdown fence nếu có bọc bên ngoài
            var fenceMatch = FenceRegex.Match(text);
            if (fenceMatch.Success)
            {
                text = fenceMatch.Groups[1].Value.Trim();
            }

            // 3. Ưu tiên tìm môi trường tikzpicture
            var tikzMatch = TikzRegex.Match(text);
            if (tikzMatch.Success)
            {
                return tikzMatch.Groups[1].Value.Trim();
            }

            // 4. Tìm môi trường circuitikz
            var circuitMatch = CircuitRegex.Match(text);
            if (circuitMatch.Success)
            {
                return circuitMatch.Groups[1].Value.Trim();
            }

            // 5. Nếu AI chỉ trả về \begin{axis}...\end{axis}, tự động bọc trong tikzpicture
            var axisMatch = AxisRegex.Match(text);
            if (axisMatch.Success)
            {
                return "\\begin{tikzpicture}[every node/.style={font=\\normalsize}]\n"
                    + axisMatch.Groups[1].Value.Trim()
                    + "\n\\end{tikzpicture}";
            }

            // 6. Loại bỏ \documentclass nếu còn sót lại ở đầu chuỗi
            if (text.Contains("\\documentclass"))
            {
                text = DocumentClassRegex.Replace(text, string.Empty).Trim();
            }

            return text.Trim();
        }
    }
}
