using System;
using System.Collections.Generic;

namespace MatrixExamAI.Shared.Tikz
{
    /// <summary>
    /// Đại diện cho một mẫu hình vẽ hoặc bảng biểu LaTeX TikZ chuẩn sư phạm.
    /// </summary>
    public class TikzTemplate
    {
        /// <summary>
        /// Định danh duy nhất của mẫu.
        /// </summary>
        public string Id { get; set; } = string.Empty;

        /// <summary>
        /// Tiêu đề hiển thị của mẫu.
        /// </summary>
        public string Title { get; set; } = string.Empty;

        /// <summary>
        /// Tên mẫu (bí danh của Title để tương thích).
        /// </summary>
        public string Name
        {
            get => Title;
            set => Title = value;
        }

        /// <summary>
        /// Định danh danh mục chứa mẫu.
        /// </summary>
        public string CategoryId { get; set; } = string.Empty;

        /// <summary>
        /// Tên danh mục (bí danh của CategoryName để tương thích).
        /// </summary>
        public string Category
        {
            get => CategoryName;
            set => CategoryName = value;
        }

        /// <summary>
        /// Tên hiển thị của danh mục.
        /// </summary>
        public string CategoryName { get; set; } = string.Empty;

        /// <summary>
        /// Các thẻ phân loại tìm kiếm.
        /// </summary>
        public string[] Tags { get; set; } = Array.Empty<string>();

        /// <summary>
        /// Từ khóa toán học tra cứu nhanh.
        /// </summary>
        public string[] Keywords { get; set; } = Array.Empty<string>();

        /// <summary>
        /// Mô tả chi tiết và ghi chú toán học sư phạm của mẫu.
        /// </summary>
        public string Description { get; set; } = string.Empty;

        /// <summary>
        /// Mã nguồn LaTeX TikZ đầy đủ (\begin{tikzpicture}...\end{tikzpicture}).
        /// </summary>
        public string Code { get; set; } = string.Empty;

        public override string ToString() => Title;
    }

    /// <summary>
    /// Phân nhóm chuyên đề mẫu TikZ (Hình học phẳng 2D, Không gian 3D, Đồ thị, BBT & BXD, Biểu đồ...).
    /// </summary>
    public class TikzTemplateCategory
    {
        /// <summary>
        /// Định danh danh mục (vd: plane_2d, solid_3d, graphs, tables, misc).
        /// </summary>
        public string Id { get; set; } = string.Empty;

        /// <summary>
        /// Tên hiển thị của danh mục (kèm biểu tượng nếu có).
        /// </summary>
        public string Name { get; set; } = string.Empty;

        /// <summary>
        /// Biểu tượng Fluent UI tương ứng (vd: Shapes24, Cube24, DataTrending24, Table24, ChartMultiple24).
        /// </summary>
        public string Icon { get; set; } = "Shapes24";

        /// <summary>
        /// Danh sách các mẫu TikZ thuộc danh mục này.
        /// </summary>
        public List<TikzTemplate> Templates { get; set; } = new List<TikzTemplate>();

        public override string ToString() => Name;
    }
}
