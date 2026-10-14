using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;

namespace MatrixExamAI.Shared.Extensibility
{
    /// <summary>
    /// Tiện ích quản lý và chuẩn hóa tệp hình ảnh câu hỏi (Port 100% logic từ ui/image_helper.py).
    /// Quản lý kho ảnh tập trung tại %LocalAppData%/MatrixExamAI/question_images.
    /// </summary>
    public static class ImageHelper
    {
        private static readonly object _dirLock = new object();

        /// <summary>
        /// Đường dẫn thư mục lưu trữ ảnh câu hỏi tập trung.
        /// </summary>
        public static string GetImagesDirectory()
        {
            string localAppData = Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData);
            string dir = Path.Combine(localAppData, "MatrixExamAI", "question_images");
            if (!Directory.Exists(dir))
            {
                lock (_dirLock)
                {
                    if (!Directory.Exists(dir))
                    {
                        Directory.CreateDirectory(dir);
                    }
                }
            }
            return dir;
        }

        /// <summary>
        /// Lưu mảng byte ảnh trực tiếp vào kho ảnh tập trung với tên định danh unique.
        /// </summary>
        public static string SaveImageBytes(byte[] bytes, string? extension = ".png")
        {
            if (bytes == null || bytes.Length == 0)
                throw new ArgumentException("Mảng byte hình ảnh không được rỗng.", nameof(bytes));

            string ext = string.IsNullOrWhiteSpace(extension) ? ".png" : extension!;
            if (!ext.StartsWith(".")) ext = "." + ext;

            string dir = GetImagesDirectory();
            string fileName = $"img_{Guid.NewGuid():N}{ext.ToLowerInvariant()}";
            string dstPath = Path.Combine(dir, fileName);

            File.WriteAllBytes(dstPath, bytes);
            return dstPath;
        }

        /// <summary>
        /// Copy một file ảnh nguồn vào thư mục lưu trữ tập trung với tên định danh unique.
        /// Trả về đường dẫn tệp mới trong kho ảnh.
        /// </summary>
        public static string? CopyToImagesDir(string sourcePath)
        {
            if (string.IsNullOrWhiteSpace(sourcePath) || !File.Exists(sourcePath))
                return null;

            string dir = GetImagesDirectory();
            string fullSource = Path.GetFullPath(sourcePath);

            // Nếu ảnh đã nằm trong kho ảnh tập trung thì không cần copy lại
            if (fullSource.StartsWith(dir, StringComparison.OrdinalIgnoreCase))
                return fullSource;

            string ext = Path.GetExtension(sourcePath);
            if (string.IsNullOrWhiteSpace(ext)) ext = ".png";

            string fileName = $"img_{Guid.NewGuid():N}{ext.ToLowerInvariant()}";
            string dstPath = Path.Combine(dir, fileName);

            File.Copy(sourcePath, dstPath, overwrite: true);
            return dstPath;
        }

        /// <summary>
        /// Chuẩn hoá trường ảnh cũ/mới về List[string] (tương đương normalize_image_field trong Python).
        /// Hỗ trợ null, string rỗng, string đơn lẻ, pipe-separated ("a.png|b.png"), json array hoặc IEnumerable.
        /// </summary>
        public static List<string> NormalizeImageField(object? value)
        {
            if (value == null)
                return new List<string>();

            if (value is IEnumerable<string> strList)
            {
                return strList
                    .Where(s => !string.IsNullOrWhiteSpace(s))
                    .Select(s => s.Trim())
                    .ToList();
            }

            string sVal = value.ToString()?.Trim() ?? string.Empty;
            if (string.IsNullOrWhiteSpace(sVal))
                return new List<string>();

            // JSON array dạng ["path1", "path2"]
            if (sVal.StartsWith("[") && sVal.EndsWith("]"))
            {
                try
                {
                    var parsed = JsonSerializer.Deserialize<List<string>>(sVal);
                    if (parsed != null)
                    {
                        return parsed
                            .Where(x => !string.IsNullOrWhiteSpace(x))
                            .Select(x => x.Trim())
                            .ToList();
                    }
                }
                catch
                {
                    // Fall through to separator check
                }
            }

            // Pipe-separated ("a.png|b.png")
            if (sVal.Contains("|"))
            {
                return sVal.Split(new[] { '|' }, StringSplitOptions.RemoveEmptyEntries)
                    .Select(p => p.Trim())
                    .Where(p => !string.IsNullOrEmpty(p))
                    .ToList();
            }

            return new List<string> { sVal };
        }

        /// <summary>
        /// Chuyển danh sách đường dẫn ảnh thành chuỗi pipe-separated "|" để lưu vào CSDL SQLite / str field.
        /// Tương đương serialize_image_field trong Python.
        /// </summary>
        public static string SerializeImageField(IEnumerable<string>? paths)
        {
            if (paths == null) return string.Empty;

            var clean = paths
                .Where(p => !string.IsNullOrWhiteSpace(p))
                .Select(p => p.Trim())
                .ToList();

            return clean.Count > 0 ? string.Join("|", clean) : string.Empty;
        }

        /// <summary>
        /// Xóa an toàn file ảnh nếu nó nằm trong kho ảnh tập trung (IMAGES_DIR).
        /// </summary>
        public static bool DeleteOrphanImage(string? imagePath)
        {
            if (string.IsNullOrWhiteSpace(imagePath) || !File.Exists(imagePath))
                return false;

            try
            {
                string dir = GetImagesDirectory();
                string fullPath = Path.GetFullPath(imagePath);
                if (fullPath.StartsWith(dir, StringComparison.OrdinalIgnoreCase))
                {
                    File.Delete(fullPath);
                    return true;
                }
            }
            catch
            {
                // Ignore failure on delete
            }
            return false;
        }
    }
}
