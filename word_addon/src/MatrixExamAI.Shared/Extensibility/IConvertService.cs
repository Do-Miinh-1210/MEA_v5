using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;

namespace MatrixExamAI.Shared.Extensibility
{
    /// <summary>
    /// Yêu cầu chuyển đổi đề thi từ ảnh / tài liệu (Phân hệ Convert AI Vision).
    /// </summary>
    public class ConvertRequest
    {
        /// <summary>
        /// Dữ liệu ảnh Base64 (nếu chuyển đổi từ ảnh/clipboard).
        /// </summary>
        public string? ImageBase64 { get; set; }

        /// <summary>
        /// Định dạng MIME của ảnh (image/png, image/jpeg...).
        /// </summary>
        public string? ImageMimeType { get; set; } = "image/png";

        /// <summary>
        /// Văn bản thô đầu vào (nếu chuyển đổi từ tài liệu text/Word/PDF text layer).
        /// </summary>
        public string? RawInputText { get; set; }

        /// <summary>
        /// Bộ lọc ép kiểu câu hỏi: "auto", "TN" (Trắc nghiệm), "DS" (Đúng/Sai), "TLN" (Trả lời ngắn), "TL" (Tự luận).
        /// </summary>
        public string QtypeFilter { get; set; } = "auto";

        /// <summary>
        /// Có tự động yêu cầu AI giải chi tiết luôn hay không.
        /// </summary>
        public bool IncludeSolution { get; set; } = true;

        /// <summary>
        /// Ghi đè mô hình AI (mặc định: gemini-3.8-flash).
        /// </summary>
        public string? ModelOverride { get; set; }
    }

    /// <summary>
    /// Kết quả chuyển đổi câu hỏi đề thi từ Convert Service.
    /// </summary>
    public class ConvertResult
    {
        public bool Success { get; set; }
        public string? ErrorMessage { get; set; }
        public string? ModelUsed { get; set; }
        public long LatencyMs { get; set; }

        /// <summary>
        /// Môn học suy luận được từ đề (Toán, Vật lý...).
        /// </summary>
        public string Subject { get; set; } = "Toán";

        /// <summary>
        /// Khối lớp học suy luận được (10, 11, 12).
        /// </summary>
        public int Grade { get; set; } = 12;

        /// <summary>
        /// Chuyên đề kiến thức chính.
        /// </summary>
        public string Topic { get; set; } = string.Empty;

        /// <summary>
        /// Danh sách câu hỏi đã được trích xuất và phân tích cấu trúc.
        /// </summary>
        public List<QuestionItem> Questions { get; set; } = new List<QuestionItem>();

        /// <summary>
        /// Văn bản đề thi đã được format chuẩn hóa sẵn sàng chèn vào Word.
        /// </summary>
        public string FormattedDocText { get; set; } = string.Empty;

        /// <summary>
        /// Văn bản thô nhận diện được từ AI.
        /// </summary>
        public string RawAiResponse { get; set; } = string.Empty;

        public static ConvertResult Fail(string error, long latencyMs = 0) => new ConvertResult
        {
            Success = false,
            ErrorMessage = error,
            LatencyMs = latencyMs
        };

        public static ConvertResult Ok(
            List<QuestionItem> questions,
            string formattedDocText,
            string rawAiResponse,
            string subject = "Toán",
            int grade = 12,
            string topic = "",
            string modelUsed = "gemini-3.8-flash",
            long latencyMs = 0) => new ConvertResult
        {
            Success = true,
            Questions = questions,
            FormattedDocText = formattedDocText,
            RawAiResponse = rawAiResponse,
            Subject = subject,
            Grade = grade,
            Topic = topic,
            ModelUsed = modelUsed,
            LatencyMs = latencyMs
        };
    }

    /// <summary>
    /// Giao diện dịch vụ Convert Đề thi AI Vision (Ảnh / Tài liệu / Clipboard -> Câu hỏi cấu trúc Word).
    /// </summary>
    public interface IConvertService
    {
        /// <summary>
        /// Nhận diện ảnh chụp bài toán hoặc văn bản đề thi và trích xuất thành danh sách câu hỏi chuẩn cấu trúc.
        /// </summary>
        Task<ConvertResult> ConvertContentAsync(ConvertRequest request, CancellationToken cancellationToken = default);

        /// <summary>
        /// Phân tích trực tiếp văn bản thô / LaTeX ex_test / Natural format (không tốn lượt gọi AI).
        /// </summary>
        ConvertResult ParseTextDirectly(string rawText, string subject = "Toán", int grade = 12);

        /// <summary>
        /// Lấy mẫu prompt chuẩn để người dùng sao chép gửi cho ChatGPT / Claude / Gemini bên ngoài.
        /// </summary>
        string GetChatbotPromptTemplate(string subject = "Toán", int grade = 12, string topic = "");
    }
}
