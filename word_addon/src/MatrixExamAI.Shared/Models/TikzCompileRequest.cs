namespace MatrixExamAI.Shared.Models
{
    /// <summary>
    /// Tham số yêu cầu biên dịch mã nguồn TikZ sang tệp tin ảnh.
    /// </summary>
    public class TikzCompileRequest
    {
        /// <summary>
        /// Mã nguồn TikZ thuần túy (từ \begin{tikzpicture} đến \end{tikzpicture}).
        /// </summary>
        public string TikzCode { get; set; } = string.Empty;

        /// <summary>
        /// Định dạng xuất ảnh mong muốn (PNG, SVG, EMF).
        /// </summary>
        public TikzExportFormat Format { get; set; } = TikzExportFormat.Png;

        /// <summary>
        /// Độ phân giải DPI khi xuất ảnh raster PNG (mặc định 600 DPI sắc nét tuyệt đối).
        /// </summary>
        public int Dpi { get; set; } = 600;

        /// <summary>
        /// Khoảng cách viền lề bao quanh hình trong document standalone (mặc định 10pt).
        /// </summary>
        public string Border { get; set; } = "10pt";

        /// <summary>
        /// Thời gian tối đa cho phép tiến trình biên dịch chạy (mặc định 15 giây).
        /// </summary>
        public int TimeoutSeconds { get; set; } = 15;

        /// <summary>
        /// Thư mục đích để lưu ảnh (nếu null, hệ thống sẽ lưu trong thư mục tạm có quản lý vòng đời).
        /// </summary>
        public string? OutputDirectory { get; set; }

        /// <summary>
        /// Tên tệp tin xuất (không kèm phần mở rộng, mặc định sinh GUID ngẫu nhiên).
        /// </summary>
        public string? OutputBaseName { get; set; }
    }
}
