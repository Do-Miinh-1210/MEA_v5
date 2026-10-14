using System;
using System.Collections.Generic;
using System.IO;
using System.Windows;
using System.Windows.Media.Imaging;
using Microsoft.Win32;
using SharedImageHelper = MatrixExamAI.Shared.Extensibility.ImageHelper;

namespace MatrixExamAI.Desktop.Services
{
    /// <summary>
    /// Dịch vụ quản lý hình ảnh cho giao diện Desktop WPF (Kế thừa trọn vẹn ui/image_helper.py).
    /// Cung cấp hộp thoại chọn ảnh, tự động sao chép vào kho ảnh tập trung, chuẩn hóa và nạp BitmapImage.
    /// </summary>
    public static class ImageHelper
    {
        public const string ImageFileFilter = "Hình ảnh (*.png;*.jpg;*.jpeg;*.gif;*.bmp;*.webp)|*.png;*.jpg;*.jpeg;*.gif;*.bmp;*.webp|PNG (*.png)|*.png|JPEG (*.jpg;*.jpeg)|*.jpg;*.jpeg|Tất cả tệp (*.*)|*.*";

        /// <summary>
        /// Đường dẫn thư mục lưu trữ ảnh câu hỏi tập trung (%LocalAppData%/MatrixExamAI/question_images).
        /// </summary>
        public static string GetImagesDirectory() => SharedImageHelper.GetImagesDirectory();

        /// <summary>
        /// Lưu mảng byte ảnh trực tiếp vào kho ảnh tập trung với tên định danh unique.
        /// </summary>
        public static string SaveImageBytes(byte[] bytes, string? extension = ".png") => SharedImageHelper.SaveImageBytes(bytes, extension);

        /// <summary>
        /// Copy một file ảnh nguồn vào kho ảnh tập trung với tên định danh unique.
        /// </summary>
        public static string? CopyToImagesDir(string sourcePath) => SharedImageHelper.CopyToImagesDir(sourcePath);

        /// <summary>
        /// Mở hộp thoại chọn 1 ảnh, copy vào IMAGES_DIR, trả về đường dẫn mới.
        /// Trả về null nếu người dùng hủy hoặc có lỗi (tương đương pick_and_copy_image trong Python).
        /// </summary>
        public static string? PickAndCopyImage(Window? owner = null)
        {
            var dlg = new OpenFileDialog
            {
                Title = "Chọn hình ảnh",
                Filter = ImageFileFilter,
                Multiselect = false
            };

            bool? result = owner != null ? dlg.ShowDialog(owner) : dlg.ShowDialog();
            if (result == true && !string.IsNullOrWhiteSpace(dlg.FileName))
            {
                try
                {
                    return SharedImageHelper.CopyToImagesDir(dlg.FileName);
                }
                catch (Exception ex)
                {
                    MessageBox.Show(
                        $"Không thể copy ảnh:\n{ex.Message}",
                        "Lỗi sao chép ảnh",
                        MessageBoxButton.OK,
                        MessageBoxImage.Error);
                }
            }

            return null;
        }

        /// <summary>
        /// Mở hộp thoại cho phép CHỌN NHIỀU ảnh cùng lúc (Ctrl/Shift + click).
        /// Mỗi ảnh được copy vào IMAGES_DIR với tên unique. Trả list path mới.
        /// (Tương đương pick_and_copy_images trong Python).
        /// </summary>
        public static List<string> PickAndCopyImages(Window? owner = null)
        {
            var dlg = new OpenFileDialog
            {
                Title = "Chọn 1 hoặc nhiều hình ảnh (Ctrl/Shift để chọn nhiều)",
                Filter = ImageFileFilter,
                Multiselect = true
            };

            var outList = new List<string>();
            bool? result = owner != null ? dlg.ShowDialog(owner) : dlg.ShowDialog();
            if (result == true && dlg.FileNames != null && dlg.FileNames.Length > 0)
            {
                foreach (var fn in dlg.FileNames)
                {
                    try
                    {
                        string? copied = SharedImageHelper.CopyToImagesDir(fn);
                        if (!string.IsNullOrEmpty(copied))
                        {
                            outList.Add(copied);
                        }
                    }
                    catch
                    {
                        // Tiếp tục xử lý các ảnh còn lại nếu 1 ảnh gặp lỗi
                    }
                }
            }

            return outList;
        }

        /// <summary>
        /// Chuẩn hoá trường ảnh cũ/mới về List[string] (tương đương normalize_image_field trong Python).
        /// </summary>
        public static List<string> NormalizeImageField(object? value) => SharedImageHelper.NormalizeImageField(value);

        /// <summary>
        /// Chuyển danh sách đường dẫn ảnh thành chuỗi pipe-separated "|" (tương đương serialize_image_field trong Python).
        /// </summary>
        public static string SerializeImageField(IEnumerable<string>? paths) => SharedImageHelper.SerializeImageField(paths);

        /// <summary>
        /// Xóa file ảnh an toàn nếu nằm trong IMAGES_DIR.
        /// </summary>
        public static bool DeleteOrphanImage(string? imagePath) => SharedImageHelper.DeleteOrphanImage(imagePath);

        /// <summary>
        /// Nạp BitmapImage từ đường dẫn ảnh an toàn, không khóa file trên đĩa (tương đương load_tk_image).
        /// </summary>
        public static BitmapImage? LoadBitmapImage(string? imagePath, int maxW = 360, int maxH = 240)
        {
            if (string.IsNullOrWhiteSpace(imagePath) || !File.Exists(imagePath))
                return null;

            try
            {
                var bi = new BitmapImage();
                bi.BeginInit();
                bi.CacheOption = BitmapCacheOption.OnLoad;
                bi.UriSource = new Uri(Path.GetFullPath(imagePath), UriKind.Absolute);
                if (maxW > 0) bi.DecodePixelWidth = maxW;
                bi.EndInit();
                bi.Freeze();
                return bi;
            }
            catch
            {
                return null;
            }
        }
    }
}
