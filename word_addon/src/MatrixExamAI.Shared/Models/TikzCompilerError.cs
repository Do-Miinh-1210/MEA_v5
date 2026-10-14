namespace MatrixExamAI.Shared.Models
{
    /// <summary>
    /// Thông tin chi tiết về lỗi dòng lệnh trích xuất từ log của trình biên dịch LaTeX.
    /// </summary>
    public class TikzCompilerError
    {
        /// <summary>
        /// Số thứ tự dòng gặp lỗi trong file LaTeX / mã TikZ (1-based, 0 nếu không xác định).
        /// </summary>
        public int ErrorLine { get; set; }

        /// <summary>
        /// Mô tả tóm tắt nguyên nhân lỗi (ví dụ: Package tikz Error: Giving up on this path...).
        /// </summary>
        public string ErrorDescription { get; set; } = string.Empty;

        /// <summary>
        /// Đoạn mã dòng lệnh tại vị trí phát sinh lỗi.
        /// </summary>
        public string? ContextSnippet { get; set; }

        /// <summary>
        /// Đoạn trích dẫn nguyên văn từ file log LaTeX quanh vị trí lỗi.
        /// </summary>
        public string? RawLogExcerpt { get; set; }

        public override string ToString()
        {
            if (ErrorLine > 0)
            {
                return $"[Dòng {ErrorLine}] {ErrorDescription}";
            }
            return ErrorDescription;
        }
    }
}
