using System.Threading;
using System.Threading.Tasks;

namespace MatrixExamAI.Shared.Extensibility
{
    /// <summary>
    /// Giao diện dịch vụ Chuyển đổi công thức toán LaTeX sang Word Native OMML (Phase 4).
    /// </summary>
    public interface ILatexToOmmlService
    {
        /// <summary>
        /// Chuyển đổi một chuỗi công thức LaTeX (ví dụ: \frac{a}{b}, x^2 + y^2 = r^2) sang cây XML OMML chuẩn.
        /// </summary>
        Task<OmmlConvertResult> ConvertLatexToOmmlAsync(
            string latexFormula,
            bool isDisplayMode = false,
            CancellationToken cancellationToken = default);

        /// <summary>
        /// Quét toàn bộ văn bản tài liệu Word và chuyển đổi tất cả các công thức toán $...$ hoặc $$...$$ sang OMML XML.
        /// </summary>
        Task<string> ConvertDocumentLatexFormulasAsync(
            string fullDocumentText,
            CancellationToken cancellationToken = default);

        /// <summary>
        /// Kiểm tra xem một chuỗi có chứa cú pháp công thức toán LaTeX hợp lệ hay không.
        /// </summary>
        bool IsValidLatexMath(string input);
    }
}
