using System.Threading;
using System.Threading.Tasks;
using MatrixExamAI.Shared.Models;

namespace MatrixExamAI.Shared.Tikz
{
    /// <summary>
    /// Giao diện dịch vụ biên dịch mã TikZ sang các định dạng hình ảnh (PNG 600 DPI, SVG, EMF).
    /// </summary>
    public interface ITikzCompiler
    {
        /// <summary>
        /// Chuỗi công cụ TeX và đồ họa hiện diện trên hệ thống máy trạm.
        /// </summary>
        TexToolchain Toolchain { get; }

        /// <summary>
        /// Biên dịch mã nguồn TikZ sang tệp tin ảnh theo các tham số được chỉ định.
        /// </summary>
        Task<TikzCompileResult> CompileAsync(TikzCompileRequest request, CancellationToken ct = default);
    }
}
