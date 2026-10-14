namespace MatrixExamAI.Shared.Validation
{
    /// <summary>
    /// Mức độ nghiêm trọng của lỗi phát hiện trong giai đoạn tiền kiểm (Pre-flight).
    /// </summary>
    public enum IssueSeverity
    {
        /// <summary>
        /// Lỗi chắc chắn khiến pdflatex thất bại (cần sửa trước khi biên dịch).
        /// </summary>
        Error,

        /// <summary>
        /// Cảnh báo có thể gây lỗi hoặc sai lệch hiển thị.
        /// </summary>
        Warning,

        /// <summary>
        /// Gợi ý chuẩn phong cách Thầy Đỗ Minh (không gây lỗi biên dịch).
        /// </summary>
        Info
    }
}
