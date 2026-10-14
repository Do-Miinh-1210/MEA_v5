using System;
using System.Collections.Generic;

namespace MatrixExamAI.Shared.Extensibility
{
    /// <summary>
    /// Kết quả xử lý từ Trợ lý AI Soạn thảo văn bản.
    /// </summary>
    public class AssistantResponse
    {
        /// <summary>
        /// Cho biết tác vụ AI hoàn thành thành công hay không.
        /// </summary>
        public bool Success { get; set; }

        /// <summary>
        /// Nội dung văn bản phản hồi do AI sinh ra (lời giải, câu hỏi mới, phân tích...).
        /// </summary>
        public string ResultText { get; set; } = string.Empty;

        /// <summary>
        /// Mã TikZ minh họa được trích xuất từ phản hồi (nếu có).
        /// </summary>
        public string? TikzCode { get; set; }

        /// <summary>
        /// Danh sách các gợi ý sư phạm hoặc biến thể câu hỏi kèm theo.
        /// </summary>
        public List<string> Suggestions { get; set; } = new List<string>();

        /// <summary>
        /// Mô hình AI đã thực thi phản hồi.
        /// </summary>
        public string ModelUsed { get; set; } = string.Empty;

        /// <summary>
        /// Thời gian phản hồi tính bằng mili-giây.
        /// </summary>
        public long LatencyMs { get; set; }

        /// <summary>
        /// Thông điệp lỗi chi tiết khi Success = false.
        /// </summary>
        public string? ErrorMessage { get; set; }

        /// <summary>
        /// Tạo phản hồi thành công.
        /// </summary>
        public static AssistantResponse Ok(
            string resultText,
            string modelUsed = "gemini-3.8-flash",
            long latencyMs = 0,
            string? tikzCode = null,
            List<string>? suggestions = null)
        {
            return new AssistantResponse
            {
                Success = true,
                ResultText = resultText,
                ModelUsed = modelUsed,
                LatencyMs = latencyMs,
                TikzCode = tikzCode,
                Suggestions = suggestions ?? new List<string>()
            };
        }

        /// <summary>
        /// Tạo phản hồi thất bại.
        /// </summary>
        public static AssistantResponse Fail(
            string errorMessage,
            string modelUsed = "gemini-3.8-flash",
            long latencyMs = 0)
        {
            return new AssistantResponse
            {
                Success = false,
                ErrorMessage = errorMessage,
                ModelUsed = modelUsed,
                LatencyMs = latencyMs
            };
        }
    }
}
