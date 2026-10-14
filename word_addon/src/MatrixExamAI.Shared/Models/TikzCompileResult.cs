namespace MatrixExamAI.Shared.Models
{
    /// <summary>
    /// Kết quả thu được sau khi hoàn thành tiến trình biên dịch TikZ.
    /// </summary>
    public class TikzCompileResult
    {
        /// <summary>
        /// Cho biết quá trình biên dịch có thành công hay không.
        /// </summary>
        public bool Success { get; set; }

        /// <summary>
        /// Đường dẫn tuyệt đối tới tệp tin hình ảnh đã xuất thành công trên ổ đĩa.
        /// </summary>
        public string? ImagePath { get; set; }

        /// <summary>
        /// Chuỗi Data URL (ví dụ: data:image/png;base64,... hoặc data:image/svg+xml;utf8,...) dùng hiển thị ngay trên WebView2.
        /// </summary>
        public string? PreviewDataUrl { get; set; }

        /// <summary>
        /// Định dạng ảnh thực tế đã được xuất.
        /// </summary>
        public TikzExportFormat Format { get; set; } = TikzExportFormat.Png;

        /// <summary>
        /// Thông điệp lỗi tóm tắt nếu biên dịch thất bại.
        /// </summary>
        public string? ErrorMessage { get; set; }

        /// <summary>
        /// Chi tiết lỗi phân tích từ LaTeX log (số dòng, mã lỗi, ngữ cảnh).
        /// </summary>
        public TikzCompilerError? ParsedError { get; set; }

        /// <summary>
        /// Toàn bộ log thô sinh ra từ trình biên dịch pdflatex.
        /// </summary>
        public string? RawLatexLog { get; set; }

        /// <summary>
        /// Thời gian thực thi toàn bộ pipeline biên dịch tính bằng mili-giây.
        /// </summary>
        public long CompilationTimeMs { get; set; }

        /// <summary>
        /// Tạo kết quả thành công.
        /// </summary>
        public static TikzCompileResult Ok(
            string imagePath,
            string previewDataUrl,
            TikzExportFormat format,
            long compilationTimeMs)
        {
            return new TikzCompileResult
            {
                Success = true,
                ImagePath = imagePath,
                PreviewDataUrl = previewDataUrl,
                Format = format,
                CompilationTimeMs = compilationTimeMs
            };
        }

        /// <summary>
        /// Tạo kết quả thất bại.
        /// </summary>
        public static TikzCompileResult Fail(
            string errorMessage,
            TikzCompilerError? parsedError,
            string? rawLatexLog,
            long compilationTimeMs)
        {
            return new TikzCompileResult
            {
                Success = false,
                ErrorMessage = errorMessage,
                ParsedError = parsedError,
                RawLatexLog = rawLatexLog,
                CompilationTimeMs = compilationTimeMs
            };
        }
    }
}
