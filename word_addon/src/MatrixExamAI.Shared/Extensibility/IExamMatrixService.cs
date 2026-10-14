using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;

namespace MatrixExamAI.Shared.Extensibility
{
    /// <summary>
    /// Giao diện dịch vụ Thiết lập Ma trận & Trộn đề thi hoán vị chuẩn BGD (Phase 3).
    /// </summary>
    public interface IExamMatrixService
    {
        /// <summary>
        /// Tạo bản thảo đề thi gốc từ ngân hàng câu hỏi theo cấu hình Ma trận chuẩn BGD.
        /// </summary>
        Task<ExamDraftResult> GenerateExamFromMatrixAsync(
            ExamMatrixConfig config,
            IQuestionBankService questionBank,
            CancellationToken cancellationToken = default);

        /// <summary>
        /// Trộn đề và sinh các mã đề thi hoán vị (101, 102, 103, 104...) kèm bảng đáp án.
        /// </summary>
        Task<List<ExamVariant>> MixExamVariantsAsync(
            ExamDraftResult draft,
            int variantCount = 4,
            CancellationToken cancellationToken = default);
    }
}
