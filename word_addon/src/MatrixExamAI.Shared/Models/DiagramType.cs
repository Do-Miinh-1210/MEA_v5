namespace MatrixExamAI.Shared.Models
{
    /// <summary>
    /// Các danh mục hình vẽ toán học TikZ phổ biến theo phong cách Thầy Đỗ Minh.
    /// </summary>
    public enum DiagramType
    {
        /// <summary>
        /// Bảng biến thiên 3 dòng (tkz-tab, mũi tên biến thiên thủ công).
        /// </summary>
        BBT,

        /// <summary>
        /// Bảng xét dấu hàm số / đạo hàm (2 dòng).
        /// </summary>
        BXD,

        /// <summary>
        /// Đồ thị hàm số, hệ trục tọa độ Oxy, tiệm cận và gióng điểm cực trị.
        /// </summary>
        DoThi,

        /// <summary>
        /// Hình học không gian 3D (tikz-3dplot, nét đứt 0.4pt, nét thấy 0.6pt).
        /// </summary>
        HinhKhongGian,

        /// <summary>
        /// Hình học phẳng / Tùy biến khác.
        /// </summary>
        Custom
    }
}
