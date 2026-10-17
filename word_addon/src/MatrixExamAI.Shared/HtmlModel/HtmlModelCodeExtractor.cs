using System;
using System.Text.RegularExpressions;

namespace MatrixExamAI.Shared.HtmlModel
{
    /// <summary>
    /// Bộ trích xuất và chuẩn hóa mã HTML / Three.js / KaTeX từ kết quả phản hồi của AI.
    /// </summary>
    public static class HtmlModelCodeExtractor
    {
        private static readonly Regex MarkdownHtmlRegex = new Regex(
            @"```(?:html|htm)?\s*\r?\n(?<code>[\s\S]*?)\r?\n```",
            RegexOptions.IgnoreCase | RegexOptions.Compiled);

        private static readonly Regex DoctypeHtmlRegex = new Regex(
            @"(?i)(<!DOCTYPE\s+html[\s\S]*?</html>)",
            RegexOptions.Compiled);

        private static readonly Regex HtmlTagRegex = new Regex(
            @"(?i)(<html[\s\S]*?</html>)",
            RegexOptions.Compiled);

        /// <summary>
        /// Trích xuất khối mã HTML độc lập từ chuỗi văn bản bất kỳ.
        /// </summary>
        public static string ExtractHtmlCode(string? rawText)
        {
            if (string.IsNullOrWhiteSpace(rawText))
                return string.Empty;

            string text = rawText.Trim();

            // 1. Thử trích xuất từ khối markdown ```html ... ```
            var mdMatch = MarkdownHtmlRegex.Match(text);
            if (mdMatch.Success)
            {
                string code = mdMatch.Groups["code"].Value.Trim();
                if (code.IndexOf("<html", StringComparison.OrdinalIgnoreCase) >= 0 ||
                    code.IndexOf("<!DOCTYPE", StringComparison.OrdinalIgnoreCase) >= 0 ||
                    code.IndexOf("<div", StringComparison.OrdinalIgnoreCase) >= 0)
                {
                    return EnsureHtmlStructure(code);
                }
            }

            // 2. Thử tìm khối <!DOCTYPE html> ... </html>
            var docMatch = DoctypeHtmlRegex.Match(text);
            if (docMatch.Success)
            {
                return docMatch.Groups[1].Value.Trim();
            }

            // 3. Thử tìm khối <html> ... </html>
            var htmlMatch = HtmlTagRegex.Match(text);
            if (htmlMatch.Success)
            {
                return "<!DOCTYPE html>\n" + htmlMatch.Groups[1].Value.Trim();
            }

            // 4. Nếu chuỗi đã chứa mã HTML cơ bản
            if (text.StartsWith("<!DOCTYPE", StringComparison.OrdinalIgnoreCase) ||
                text.StartsWith("<html", StringComparison.OrdinalIgnoreCase))
            {
                return text;
            }

            // 5. Nếu chỉ là đoạn code thân (body/script), bọc thành trang HTML hoàn chỉnh
            if (text.Contains("<canvas") || text.Contains("THREE.") || text.Contains("function") || text.Contains("<script"))
            {
                return WrapIntoFullHtml(text);
            }

            return text;
        }

        private static string EnsureHtmlStructure(string code)
        {
            if (!code.StartsWith("<!DOCTYPE", StringComparison.OrdinalIgnoreCase))
            {
                if (code.StartsWith("<html", StringComparison.OrdinalIgnoreCase))
                {
                    return "<!DOCTYPE html>\n" + code;
                }
                return WrapIntoFullHtml(code);
            }
            return code;
        }

        private static string WrapIntoFullHtml(string bodyContent)
        {
            return $@"<!DOCTYPE html>
<html lang=""vi"">
<head>
    <meta charset=""UTF-8"">
    <meta name=""viewport"" content=""width=device-width, initial-scale=1.0"">
    <title>Mô hình Mô phỏng Trực quan</title>
    <script src=""https://cdn.tailwindcss.com""></script>
    <link rel=""stylesheet"" href=""https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.css"">
    <script src=""https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.js""></script>
    <script src=""https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/contrib/auto-render.min.js""></script>
    <script src=""https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js""></script>
    <style>
        body {{ font-family: 'Inter', system-ui, sans-serif; background: #f8fafc; color: #0f172a; }}
    </style>
</head>
<body class=""min-h-screen p-4 flex flex-col items-center justify-center"">
{bodyContent}
    <script>
        document.addEventListener('DOMContentLoaded', function() {{
            if (typeof renderMathInElement === 'function') {{
                renderMathInElement(document.body, {{
                    delimiters: [
                        {{ left: '$$', right: '$$', display: true }},
                        {{ left: '$', right: '$', display: false }}
                    ]
                }});
            }}
        }});
    </script>
</body>
</html>";
        }
    }
}
