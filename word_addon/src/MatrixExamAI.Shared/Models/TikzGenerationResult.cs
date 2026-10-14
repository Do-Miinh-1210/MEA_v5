namespace MatrixExamAI.Shared.Models
{
    /// <summary>
    /// Kết quả phản hồi từ AI Engine sau khi sinh hoặc chỉnh sửa mã TikZ.
    /// </summary>
    public class TikzGenerationResult
    {
        /// <summary>
        /// Trạng thái thành công của yêu cầu sinh mã.
        /// </summary>
        public bool Success { get; set; }

        /// <summary>
        /// Mã nguồn TikZ thuần túy đã được trích xuất và chuẩn hóa.
        /// </summary>
        public string TikzCode { get; set; } = string.Empty;

        /// <summary>
        /// Toàn bộ văn bản phản hồi thô nhận từ API.
        /// </summary>
        public string RawResponse { get; set; } = string.Empty;

        /// <summary>
        /// Thông điệp lỗi nếu quá trình sinh mã thất bại.
        /// </summary>
        public string? ErrorMessage { get; set; }

        /// <summary>
        /// Tên nhà cung cấp AI đã xử lý yêu cầu (GeminiDirect, 9Router, OpenAI).
        /// </summary>
        public string ProviderUsed { get; set; } = string.Empty;

        /// <summary>
        /// Tên mô hình AI đã thực thi (ví dụ: gemini-3.8-flash).
        /// </summary>
        public string ModelUsed { get; set; } = string.Empty;

        /// <summary>
        /// Thời gian phản hồi tính bằng mili-giây (latency).
        /// </summary>
        public long LatencyMs { get; set; }

        /// <summary>
        /// Bí danh cho LatencyMs để tương thích với các bộ điều khiển và bridge.
        /// </summary>
        public long ExecutionTimeMs
        {
            get => LatencyMs;
            set => LatencyMs = value;
        }

        /// <summary>
        /// Số lượt tự sửa lỗi (Auto-Healing iterations) đã thực hiện để có kết quả hợp lệ.
        /// </summary>
        public int HealingAttempts { get; set; }

        /// <summary>
        /// Tạo kết quả thành công.
        /// </summary>
        public static TikzGenerationResult Ok(
            string tikzCode,
            string provider,
            string model,
            long latencyMs,
            string rawResponse = "",
            int healingAttempts = 0)
        {
            return new TikzGenerationResult
            {
                Success = true,
                TikzCode = tikzCode,
                ProviderUsed = provider,
                ModelUsed = model,
                LatencyMs = latencyMs,
                RawResponse = rawResponse,
                HealingAttempts = healingAttempts
            };
        }

        /// <summary>
        /// Tạo kết quả thất bại.
        /// </summary>
        public static TikzGenerationResult Fail(
            string errorMessage,
            string provider = "",
            string model = "",
            long latencyMs = 0,
            string rawResponse = "",
            int healingAttempts = 0)
        {
            return new TikzGenerationResult
            {
                Success = false,
                ErrorMessage = errorMessage,
                ProviderUsed = provider,
                ModelUsed = model,
                LatencyMs = latencyMs,
                RawResponse = rawResponse,
                HealingAttempts = healingAttempts
            };
        }
    }
}
