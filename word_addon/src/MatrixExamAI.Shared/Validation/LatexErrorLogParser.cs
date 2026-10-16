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

            var (vietnameseDesc, fixSuggestion) = TranslateToVietnamese(errorDescription, contextSnippet);

            return new TikzCompilerError
            {
                ErrorLine = errorLine,
                ErrorDescription = errorDescription,
                ContextSnippet = contextSnippet,
                RawLogExcerpt = excerpt,
                VietnameseDescription = vietnameseDesc,
                FixSuggestion = fixSuggestion
            };
        }

        /// <summary>
        /// Dịch thông điệp lỗi LaTeX sang tiếng Việt dễ hiểu và đề xuất cách khắc phục cụ thể.
        /// </summary>
        public static (string VietnameseDesc, string FixSuggestion) TranslateToVietnamese(string errorDescription, string? contextSnippet)
        {
            if (string.IsNullOrWhiteSpace(errorDescription))
            {
                return ("Lỗi biên dịch LaTeX không xác định", "Bấm 'Sửa lỗi bằng AI' để tự động phát hiện và khắc phục.");
            }

            string err = errorDescription.Trim();

            // 1. Lỗi ngắt dòng sai vị trí: There's no line here to end
            if (err.Contains("There's no line here to end", StringComparison.OrdinalIgnoreCase))
            {
                return (
                    "Lỗi ngắt dòng sai vị trí (gọi lệnh '\\\\' ở nơi không thể xuống dòng)",
                    "Kiểm tra xem mã có bị nhân đôi dấu gạch chéo ngược '\\\\' thay vì 1 dấu '\\' không (bấm nút 'Lọc mã' để sửa tự động), hoặc tránh đặt '\\\\' bên trong công thức $...$."
                );
            }

            // 2. Lệnh không xác định: Undefined control sequence
            if (err.Contains("Undefined control sequence", StringComparison.OrdinalIgnoreCase))
            {
                string snippet = !string.IsNullOrWhiteSpace(contextSnippet) ? $" '{contextSnippet}'" : string.Empty;
                return (
                    $"Lệnh LaTeX/TikZ không tồn tại hoặc sai chính tả{snippet}",
                    "Kiểm tra lại tên lệnh tại dòng báo lỗi hoặc bổ sung các gói thư viện TikZ cần thiết (ví dụ: patterns, calc, positioning, arrows.meta)."
                );
            }

            // 3. Thiếu dấu dollar: Missing $ inserted
            if (err.Contains("Missing $ inserted", StringComparison.OrdinalIgnoreCase))
            {
                return (
                    "Thiếu ký hiệu '$' để mở hoặc đóng công thức toán học",
                    "Kẹp các biểu thức toán học, ký tự Hy Lạp, phân số hoặc biến số vào giữa cặp dấu $...$."
                );
            }

            // 4. Thừa ngoặc nhọn hoặc quên $: Extra }, or forgotten $
            if (err.Contains("Extra }, or forgotten $", StringComparison.OrdinalIgnoreCase))
            {
                return (
                    "Thừa dấu ngoặc nhọn '}' hoặc quên đóng/mở công thức toán '$'",
                    "Rà soát lại số lượng cặp ngoặc nhọn { } và các cặp dấu $ trên dòng này."
                );
            }

            // 5. Lỗi đường vẽ TikZ: Giving up on this path
            if (err.Contains("Giving up on this path", StringComparison.OrdinalIgnoreCase))
            {
                return (
                    "Đường vẽ TikZ không hợp lệ hoặc thiếu dấu chấm phẩy ';' kết thúc lệnh",
                    "Đảm bảo cuối mỗi câu lệnh \\draw, \\node, \\fill... phải kết thúc bằng dấu ';' và tọa độ có dạng (x,y)."
                );
            }

            // 6. Tọa độ vượt giới hạn: Dimension too large
            if (err.Contains("Dimension too large", StringComparison.OrdinalIgnoreCase))
            {
                return (
                    "Tọa độ hoặc thông số tính toán vượt quá giới hạn TeX",
                    "Giảm tỉ lệ scale (ví dụ: scale=0.8) hoặc thu hẹp miền domain của hàm số trong plot."
                );
            }

            // 7. Missing \endcsname inserted
            if (err.Contains("Missing \\endcsname inserted", StringComparison.OrdinalIgnoreCase) || err.Contains("Missing \\endcsname", StringComparison.OrdinalIgnoreCase))
            {
                return (
                    "Tham số hoặc tên biến chứa ký tự đặc biệt không hợp lệ",
                    "Kiểm tra các nhãn node hoặc thuộc tính trong cặp ngoặc vuông [ ... ]."
                );
            }

            // 8. Thuộc tính không xác định: Package pgfkeys Error: I do not know the key
            if (err.Contains("I do not know the key", StringComparison.OrdinalIgnoreCase))
            {
                return (
                    "Tùy chọn/thuộc tính TikZ không hợp lệ hoặc sai chính tả",
                    "Kiểm tra lại từ khóa cấu hình trong cặp ngoặc vuông [ ... ], ví dụ: 'color', 'fill', 'thick'."
                );
            }

            // 9. Đoạn văn bị ngắt giữa chừng: Paragraph ended before ... was complete
            if (err.Contains("Paragraph ended before", StringComparison.OrdinalIgnoreCase))
            {
                return (
                    "Đoạn mã bị ngắt dòng khi lệnh chưa hoàn thành",
                    "Kiểm tra xem câu lệnh phía trên đã đóng đủ ngoặc nhọn '}' trước khi xuống dòng chưa."
                );
            }

            // 10. Không tìm thấy file: File `...' not found
            if (err.Contains("not found", StringComparison.OrdinalIgnoreCase))
            {
                return (
                    "Không tìm thấy tệp hoặc gói thư viện TeX cần nạp",
                    "Kiểm tra lại tên gói thư viện hoặc đường dẫn tệp ảnh được nhúng."
                );
            }

            // 11. Tràn số học: Arithmetic overflow
            if (err.Contains("Arithmetic overflow", StringComparison.OrdinalIgnoreCase))
            {
                return (
                    "Tràn số học trong phép tính toán tọa độ",
                    "Kiểm tra tránh phép chia cho 0 hoặc giảm miền giá trị trong lệnh plot hàm số."
                );
            }

            // 12. Bảng biến thiên tkz-tab: Package tkz-tab Error
            if (err.Contains("tkz-tab", StringComparison.OrdinalIgnoreCase))
            {
                return (
                    "Lỗi cấu trúc bảng biến thiên tkz-tab",
                    "Kiểm tra số lượng cột giữa \\tkzTabInit, \\tkzTabLine và \\tkzTabVar phải đồng bộ với nhau."
                );
            }

            // 13. Môi trường không xác định: Environment ... undefined
            if (err.Contains("Environment", StringComparison.OrdinalIgnoreCase) && err.Contains("undefined", StringComparison.OrdinalIgnoreCase))
            {
                return (
                    "Môi trường LaTeX không xác định",
                    "Kiểm tra lại chính tả tên môi trường sau \\begin{...} và \\end{...}."
                );
            }

            // 14. Mở đóng thẻ không khớp
            if (err.Contains("ended by", StringComparison.OrdinalIgnoreCase))
            {
                return (
                    "Mở môi trường và đóng môi trường không khớp nhau",
                    "Đảm bảo tên môi trường trong \\begin{...} và \\end{...} phải trùng khớp hoàn toàn."
                );
            }

            // 15. Dừng khẩn cấp: Emergency stop
            if (err.Contains("Emergency stop", StringComparison.OrdinalIgnoreCase))
            {
                return (
                    "Trình biên dịch pdflatex dừng khẩn cấp do gặp lỗi cú pháp nghiêm trọng",
                    "Bấm 'Sửa lỗi bằng AI' hoặc 'Lọc mã' để phục hồi lại cấu trúc mã TikZ hợp lệ."
                );
            }

            return ($"Lỗi cú pháp LaTeX: {err}", "Bấm 'Sửa lỗi bằng AI' để tự động phát hiện và vá lỗi.");
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
