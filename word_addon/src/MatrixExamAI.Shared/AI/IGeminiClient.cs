using System.Threading;
using System.Threading.Tasks;
using MatrixExamAI.Shared.Models;

namespace MatrixExamAI.Shared.AI
{
    /// <summary>
    /// Giao diện dịch vụ AI Gemini Client chuyên trách sinh và tối ưu mã TikZ.
    /// </summary>
    public interface IGeminiClient
    {
        /// <summary>
        /// Bộ quản lý xoay vòng và hạn mức API Key.
        /// </summary>
        ApiKeyPoolManager KeyPool { get; }

        /// <summary>
        /// Bộ điều phối dự phòng (9Router / OpenAI).
        /// </summary>
        FallbackOrchestrator Fallback { get; }

        /// <summary>
        /// Tên model mặc định (mặc định gemini-3.8-flash).
        /// </summary>
        string DefaultModel { get; set; }

        /// <summary>
        /// Sinh mã TikZ từ yêu cầu prompt và ảnh tùy chọn (multimodal).
        /// </summary>
        Task<TikzGenerationResult> GenerateTikzAsync(TikzPromptRequest request, CancellationToken ct = default);

        /// <summary>
        /// Chỉnh sửa mã TikZ hiện có theo yêu cầu người dùng.
        /// </summary>
        Task<TikzGenerationResult> EditTikzAsync(string currentCode, string editRequest, CancellationToken ct = default);

        /// <summary>
        /// Tối ưu hóa mã TikZ hiện có theo 5 lớp cấu trúc Layering Rules của Thầy Đỗ Minh.
        /// </summary>
        Task<TikzGenerationResult> OptimizeTikzAsync(string currentCode, CancellationToken ct = default);
    }
}
