using System.Threading;
using System.Threading.Tasks;

namespace MatrixExamAI.Shared.Extensibility
{
    /// <summary>
    /// Giao diện dịch vụ Trợ lý AI Soạn thảo & Phân tích văn bản trên tài liệu Word (Phase 2).
    /// </summary>
    public interface IAIAssistantService
    {
        /// <summary>
        /// Xử lý yêu cầu tổng quát từ văn bản được chọn theo tùy chọn trong AssistantRequest.
        /// </summary>
        Task<AssistantResponse> ProcessAsync(AssistantRequest request, CancellationToken cancellationToken = default);

        /// <summary>
        /// Phân tích và giải thích kiến thức trọng tâm, bẫy thường gặp của câu hỏi đang chọn.
        /// </summary>
        Task<AssistantResponse> ExplainQuestionAsync(string selectedText, string? prompt = null, CancellationToken cancellationToken = default);

        /// <summary>
        /// Viết lại bài toán hoặc phát triển câu hỏi tương đương thay số giữ nguyên cấu trúc toán học.
        /// </summary>
        Task<AssistantResponse> RewriteMathProblemAsync(string selectedText, string? parameters = null, CancellationToken cancellationToken = default);

        /// <summary>
        /// Sinh lời giải chi tiết từng bước chuẩn mực Bộ GD&ĐT cho câu hỏi đang chọn.
        /// </summary>
        Task<AssistantResponse> GenerateStepByStepSolutionAsync(string selectedText, CancellationToken cancellationToken = default);
    }
}
