using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;

namespace MatrixExamAI.Shared.Extensibility
{
    /// <summary>
    /// Giao diện dịch vụ Quản lý Ngân hàng câu hỏi SQLite MatrixExamAI (Phase 3).
    /// </summary>
    public interface IQuestionBankService
    {
        /// <summary>
        /// Khởi tạo cấu trúc bảng CSDL SQLite, thiết lập các index tìm kiếm nếu chưa có.
        /// </summary>
        Task InitializeDatabaseAsync(CancellationToken cancellationToken = default);

        /// <summary>
        /// Thêm mới một câu hỏi kèm mã TikZ và siêu dữ liệu vào ngân hàng CSDL.
        /// </summary>
        Task<long> InsertQuestionAsync(QuestionItem item, CancellationToken cancellationToken = default);

        /// <summary>
        /// Cập nhật thông tin và mã TikZ của câu hỏi theo ID.
        /// </summary>
        Task<bool> UpdateQuestionAsync(QuestionItem item, CancellationToken cancellationToken = default);

        /// <summary>
        /// Xóa câu hỏi khỏi ngân hàng theo ID.
        /// </summary>
        Task<bool> DeleteQuestionAsync(long id, CancellationToken cancellationToken = default);

        /// <summary>
        /// Lấy chi tiết một câu hỏi theo ID.
        /// </summary>
        Task<QuestionItem?> GetQuestionByIdAsync(long id, CancellationToken cancellationToken = default);

        /// <summary>
        /// Tìm kiếm câu hỏi đa tiêu chí (từ khóa, môn, khối lớp, chủ đề, mức độ nhận thức).
        /// </summary>
        Task<List<QuestionItem>> SearchQuestionsAsync(
            string? keyword = null,
            string? subject = null,
            int? grade = null,
            string? topic = null,
            string? level = null,
            string? questionType = null,
            int limit = 50,
            CancellationToken cancellationToken = default);

        /// <summary>
        /// Đếm tổng số lượng câu hỏi trong ngân hàng theo bộ lọc.
        /// </summary>
        Task<int> GetQuestionCountAsync(
            string? subject = null,
            int? grade = null,
            string? level = null,
            CancellationToken cancellationToken = default);
    }
}
