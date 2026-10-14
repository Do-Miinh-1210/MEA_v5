using System;
using System.IO;
using System.Text.RegularExpressions;
using MatrixExamAI.Shared.Models;

namespace MatrixExamAI.Shared.Validation
{
    /// <summary>
    /// Bộ phân tích cú pháp tệp tin log của trình biên dịch LaTeX (.log),
    /// trích xuất chính xác số dòng lỗi và thông điệp lỗi để phục vụ chẩn đoán và Auto-Healing.
    /// </summary>
    public static class LatexErrorLogParser
    {
        private static readonly Regex ErrorPrefixRegex = new Regex(@"^!\s*(.*)$", RegexOptions.Multiline | RegexOptions.Compiled);
        private static readonly Regex LineNumberRegex = new Regex(@"^l\.(\d+)\s*(.*)$", RegexOptions.Multiline | RegexOptions.Compiled);

        /// <summary>
        /// Phân tích nội dung log LaTeX hoặc đọc từ tệp tin log trên ổ đĩa.
        /// </summary>
        public static TikzCompilerError? ParseLog(string? logContent)
        {
            if (string.IsNullOrWhiteSpace(logContent))
            {
                return null;
            }

            var errMatch = ErrorPrefixRegex.Match(logContent!);
            if (!errMatch.Success)
            {
                return null;
            }

            string errorDescription = errMatch.Groups[1].Value.Trim();
            int errorLine = 0;
            string? contextSnippet = null;

            // Tìm vị trí dòng lỗi (l.<number>) ngay sau thông báo lỗi
            int searchStart = errMatch.Index;
            var lineMatch = LineNumberRegex.Match(logContent!, searchStart);
            if (lineMatch.Success)
            {
                if (int.TryParse(lineMatch.Groups[1].Value, out int lineNum))
                {
                    errorLine = lineNum;
                }
                contextSnippet = lineMatch.Groups[2].Value.Trim();
            }
            else
            {
                // Thử tìm bất kỳ dòng l.<number> nào trong log
                var anyLineMatch = LineNumberRegex.Match(logContent!);
                if (anyLineMatch.Success)
                {
                    if (int.TryParse(anyLineMatch.Groups[1].Value, out int lineNum))
                    {
                        errorLine = lineNum;
                    }
                    contextSnippet = anyLineMatch.Groups[2].Value.Trim();
                }
            }

            // Trích xuất đoạn trích đoạn log (khoảng 10-15 dòng quanh vị trí lỗi)
            int excerptStart = Math.Max(0, errMatch.Index - 100);
            int excerptLength = Math.Min(logContent!.Length - excerptStart, 600);
            string excerpt = logContent.Substring(excerptStart, excerptLength);

            return new TikzCompilerError
            {
                ErrorLine = errorLine,
                ErrorDescription = errorDescription,
                ContextSnippet = contextSnippet,
                RawLogExcerpt = excerpt
            };
        }

        /// <summary>
        /// Đọc và phân tích tệp tin log từ đường dẫn trên ổ đĩa.
        /// </summary>
        public static TikzCompilerError? ParseLogFile(string logFilePath)
        {
            if (!File.Exists(logFilePath))
            {
                return null;
            }

            try
            {
                string content = File.ReadAllText(logFilePath);
                return ParseLog(content);
            }
            catch
            {
                return null;
            }
        }
    }
}
