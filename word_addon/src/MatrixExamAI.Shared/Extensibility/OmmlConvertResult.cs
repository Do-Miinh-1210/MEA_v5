using System;

namespace MatrixExamAI.Shared.Extensibility
{
    /// <summary>
    /// Kết quả chuyển đổi từ công thức LaTeX sang Office Math Markup Language (OMML) chuẩn Word Native (Phase 4).
    /// </summary>
    public class OmmlConvertResult
    {
        /// <summary>
        /// Trạng thái thành công của quá trình biên dịch cú pháp.
        /// </summary>
        public bool Success { get; set; }

        /// <summary>
        /// Chuỗi công thức LaTeX gốc ban đầu.
        /// </summary>
        public string OriginalLatex { get; set; } = string.Empty;

        /// <summary>
        /// Mã XML OMML cấu trúc cây hợp lệ (&lt;m:oMath&gt;...&lt;/m:oMath&gt;) để nhúng vào Word.
        /// </summary>
        public string OmmlXml { get; set; } = string.Empty;

        /// <summary>
        /// Thông điệp lỗi chi tiết khi Success = false.
        /// </summary>
        public string? ErrorMessage { get; set; }

        /// <summary>
        /// Thời gian xử lý chuyển đổi tính bằng mili-giây.
        /// </summary>
        public long LatencyMs { get; set; }

        /// <summary>
        /// Tạo kết quả thành công.
        /// </summary>
        public static OmmlConvertResult Ok(string originalLatex, string ommlXml, long latencyMs = 0)
        {
            return new OmmlConvertResult
            {
                Success = true,
                OriginalLatex = originalLatex,
                OmmlXml = ommlXml,
                LatencyMs = latencyMs
            };
        }

        /// <summary>
        /// Tạo kết quả thất bại.
        /// </summary>
        public static OmmlConvertResult Fail(string originalLatex, string errorMessage, long latencyMs = 0)
        {
            return new OmmlConvertResult
            {
                Success = false,
                OriginalLatex = originalLatex,
                ErrorMessage = errorMessage,
                LatencyMs = latencyMs
            };
        }
    }
}
