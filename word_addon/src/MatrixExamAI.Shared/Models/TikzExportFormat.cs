namespace MatrixExamAI.Shared.Models
{
    /// <summary>
    /// Định dạng xuất file hình ảnh từ mã nguồn TikZ.
    /// </summary>
    public enum TikzExportFormat
    {
        /// <summary>
        /// Ảnh raster độ phân giải cao 600 DPI (sắc nét khi in ấn và chèn Word).
        /// </summary>
        Png,

        /// <summary>
        /// Ảnh vector SVG (phóng to không vỡ nét, tương thích Word 2016+ / 365).
        /// </summary>
        Svg,

        /// <summary>
        /// Ảnh vector bản địa Windows Enhanced Metafile (EMF) có thể rã nhóm trong Word.
        /// </summary>
        Emf
    }
}
