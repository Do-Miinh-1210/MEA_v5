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

        /// <summary>
        /// Mô tả chi tiết nguyên nhân lỗi dịch sang tiếng Việt dễ hiểu cho giáo viên.
        /// </summary>
        public string? VietnameseDescription { get; set; }

        /// <summary>
        /// Hướng dẫn cụ thể cách khắc phục lỗi bằng tiếng Việt.
        /// </summary>
        public string? FixSuggestion { get; set; }

        public override string ToString()
        {
            var desc = !string.IsNullOrWhiteSpace(VietnameseDescription)
                ? VietnameseDescription
                : ErrorDescription;

            var linePrefix = ErrorLine > 0 ? $"[Dòng {ErrorLine}] " : string.Empty;
            var suggestion = !string.IsNullOrWhiteSpace(FixSuggestion)
                ? $" → Cách khắc phục: {FixSuggestion}"
                : string.Empty;

            return $"{linePrefix}{desc}.{suggestion}";
        }
    }
}
