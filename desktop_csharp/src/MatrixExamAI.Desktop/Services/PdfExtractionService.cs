using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using System.Text.RegularExpressions;
using System.Threading;
using System.Threading.Tasks;
using UglyToad.PdfPig;
using UglyToad.PdfPig.Content;

namespace MatrixExamAI.Desktop.Services
{
    public class ExtractedImageInfo
    {
        public string ImagePath { get; set; } = string.Empty;
        public int Index { get; set; }
        public int PageNumber { get; set; }
        public double X { get; set; }
        public double Y { get; set; }
        public double Width { get; set; }
        public double Height { get; set; }
    }

    public class PdfExtractionResult
    {
        public string Text { get; set; } = string.Empty;
        public List<ExtractedImageInfo> Images { get; set; } = new List<ExtractedImageInfo>();
        public List<string> ImagePaths => Images.Select(i => i.ImagePath).ToList();
    }

    public class PdfExtractionService
    {
        /// <summary>
        /// Trích xuất toàn bộ văn bản từ file PDF, tự động nhận diện và trích xuất hình ảnh sơ đồ/đồ thị,
        /// lưu vào kho ảnh tập trung và chèn marker [HÌNH N: path] vào đúng ngữ cảnh văn bản.
        /// </summary>
        public async Task<string> ExtractTextAsync(
            string filePath, 
            int? startPage = null,
            int? endPage = null,
            IProgress<(int current, int total, string message)>? progress = null,
            CancellationToken cancellationToken = default)
        {
            var result = await ExtractWithImagesAsync(filePath, startPage, endPage, progress, cancellationToken);
            return result.Text;
        }

        /// <summary>
        /// Trích xuất đầy đủ văn bản và danh sách hình ảnh sơ đồ từ tệp PDF.
        /// </summary>
        public async Task<PdfExtractionResult> ExtractWithImagesAsync(
            string filePath,
            int? startPage = null,
            int? endPage = null,
            IProgress<(int current, int total, string message)>? progress = null,
            CancellationToken cancellationToken = default)
        {
            if (!File.Exists(filePath))
                throw new FileNotFoundException("Không tìm thấy tệp PDF chỉ định.", filePath);

            return await Task.Run(() =>
            {
                var sb = new StringBuilder();
                var allImages = new List<ExtractedImageInfo>();

                using var document = PdfDocument.Open(filePath);
                int totalPages = document.NumberOfPages;

                int fromPage = Math.Max(1, startPage ?? 1);
                int toPage = Math.Min(totalPages, endPage ?? totalPages);
                if (fromPage > toPage)
                {
                    fromPage = 1;
                    toPage = totalPages;
                }

                int pagesToProcess = toPage - fromPage + 1;
                int processedCount = 0;
                int globalImageIndex = 0;

                for (int i = fromPage; i <= toPage; i++)
                {
                    cancellationToken.ThrowIfCancellationRequested();

                    processedCount++;
                    progress?.Report((processedCount, pagesToProcess, $"Đang trích xuất trang {i}/{totalPages}..."));

                    var page = document.GetPage(i);
                    string pageText = page.Text ?? string.Empty;

                    // 1. Trích xuất hình ảnh sơ đồ từ trang PDF
                    var pageImages = ExtractPageImages(page, i, ref globalImageIndex);
                    if (pageImages.Count > 0)
                    {
                        allImages.AddRange(pageImages);
                        pageText = InsertImageMarkersIntoPageText(pageText, pageImages, page.Height);
                    }

                    if (!string.IsNullOrWhiteSpace(pageText))
                    {
                        sb.AppendLine($"--- Trang {i} ---");
                        sb.AppendLine(pageText);
                        sb.AppendLine();
                    }
                }

                progress?.Report((pagesToProcess, pagesToProcess, $"Hoàn thành trích xuất {pagesToProcess} trang ({allImages.Count} hình ảnh)."));

                return new PdfExtractionResult
                {
                    Text = sb.ToString(),
                    Images = allImages
                };
            }, cancellationToken);
        }

        /// <summary>
        /// Trích xuất hình ảnh từ 1 trang PDF qua PdfPig, áp dụng bộ lọc hình ảnh trang trí,
        /// lọc ảnh scan toàn trang và sắp xếp theo thứ tự đọc tự nhiên từ trên xuống dưới.
        /// </summary>
        public List<ExtractedImageInfo> ExtractPageImages(Page page, int pageNumber, ref int globalImageIndex, string? targetDir = null)
        {
            var result = new List<ExtractedImageInfo>();
            IEnumerable<IPdfImage> images;
            try
            {
                images = page.GetImages();
            }
            catch
            {
                return result;
            }

            var imageList = images.ToList();
            if (imageList.Count == 0) return result;

            double pageWidth = page.Width;
            double pageHeight = page.Height;
            double pageArea = pageWidth * pageHeight;

            var validImages = new List<(IPdfImage img, double top, double left)>();

            foreach (var img in imageList)
            {
                var bounds = img.Bounds;
                double w = bounds.Width;
                double h = bounds.Height;
                double area = w * h;

                // 1. Bỏ qua ảnh lỗi hoặc không có diện tích
                if (w <= 0 || h <= 0) continue;

                // 2. Lọc bỏ icon, logo nhỏ (< 40px cạnh hoặc < 30pt bounds)
                if (img.WidthInSamples < 40 || img.HeightInSamples < 40) continue;
                if (w < 30 || h < 30) continue;

                // 3. Lọc bỏ background / scan full trang (> 90% diện tích trang)
                if (pageArea > 0 && (area / pageArea) > 0.90) continue;
                if (w >= pageWidth * 0.95 && h >= pageHeight * 0.95) continue;

                validImages.Add((img, bounds.Top, bounds.Left));
            }

            if (validImages.Count == 0) return result;

            // Sắp xếp theo thứ tự đọc: trên xuống dưới (top giảm dần), trái sang phải (left tăng dần)
            // Nhóm sai số hàng 20pt
            var sorted = validImages
                .OrderByDescending(x => Math.Round(x.top / 20.0) * 20.0)
                .ThenBy(x => x.left)
                .ToList();

            string outDir = !string.IsNullOrWhiteSpace(targetDir) ? targetDir! : ImageHelper.GetImagesDirectory();
            if (!Directory.Exists(outDir)) Directory.CreateDirectory(outDir);

            foreach (var item in sorted)
            {
                byte[]? data = null;
                try
                {
                    if (item.img.TryGetPng(out byte[]? pngBytes) && pngBytes != null && pngBytes.Length > 0)
                    {
                        data = pngBytes;
                    }
                    else
                    {
                        var raw = item.img.RawBytes;
                        if (!raw.IsEmpty)
                        {
                            data = raw.ToArray();
                        }
                    }
                }
                catch
                {
                    // Skip image on read failure
                }

                if (data == null || data.Length == 0) continue;

                globalImageIndex++;
                string fileName = $"img_{Guid.NewGuid():N}.png";
                string filePath = Path.Combine(outDir, fileName);

                try
                {
                    File.WriteAllBytes(filePath, data);
                    result.Add(new ExtractedImageInfo
                    {
                        ImagePath = filePath,
                        Index = globalImageIndex,
                        PageNumber = pageNumber,
                        X = item.img.Bounds.Left,
                        Y = item.img.Bounds.Top,
                        Width = item.img.Bounds.Width,
                        Height = item.img.Bounds.Height
                    });
                }
                catch
                {
                    // Tiếp tục nếu 1 ảnh không thể ghi ra đĩa
                }
            }

            return result;
        }

        /// <summary>
        /// Chèn các marker [HÌNH N: path] vào nội dung trang text dựa theo tọa độ Y tương đối.
        /// </summary>
        private static string InsertImageMarkersIntoPageText(string pageText, List<ExtractedImageInfo> pageImages, double pageHeight)
        {
            if (pageImages == null || pageImages.Count == 0) return pageText;

            if (string.IsNullOrWhiteSpace(pageText))
            {
                var sb = new StringBuilder();
                foreach (var img in pageImages)
                {
                    sb.AppendLine($"[HÌNH {img.Index}: {img.ImagePath}]");
                }
                return sb.ToString();
            }

            var lines = pageText.Split(new[] { "\r\n", "\r", "\n" }, StringSplitOptions.None).ToList();
            if (lines.Count == 0)
            {
                return string.Join("\n", pageImages.Select(img => $"[HÌNH {img.Index}: {img.ImagePath}]"));
            }

            // Gán mỗi ảnh vào dòng tương ứng theo vị trí dọc
            // Trong PDF: Y=pageHeight ở trên cùng, Y=0 ở dưới cùng
            // Do đó relativeY = (1.0 - (Y / pageHeight)) tương ứng với chỉ số dòng từ 0 đến N-1
            var insertMap = new Dictionary<int, List<string>>();

            foreach (var img in pageImages)
            {
                double normalizedY = pageHeight > 0 ? Math.Clamp(1.0 - (img.Y / pageHeight), 0.0, 1.0) : 0.0;
                int targetLine = (int)Math.Round(normalizedY * (lines.Count - 1));

                // Tìm dòng chứa gợi ý như "hình vẽ", "hình bên", "đồ thị", "Câu" trong phạm vi lân cận +-2 dòng
                int bestLine = targetLine;
                for (int offset = 0; offset >= -2; offset--)
                {
                    int checkIdx = targetLine + offset;
                    if (checkIdx >= 0 && checkIdx < lines.Count)
                    {
                        string lineCheck = lines[checkIdx];
                        if (Regex.IsMatch(lineCheck, @"(?i)(hình vẽ|hình bên|như hình|đồ thị|bảng biến thiên)"))
                        {
                            bestLine = checkIdx;
                            break;
                        }
                    }
                }

                if (!insertMap.TryGetValue(bestLine, out var list))
                {
                    list = new List<string>();
                    insertMap[bestLine] = list;
                }
                list.Add($"[HÌNH {img.Index}: {img.ImagePath}]");
            }

            var outputLines = new List<string>();
            for (int i = 0; i < lines.Count; i++)
            {
                outputLines.Add(lines[i]);
                if (insertMap.TryGetValue(i, out var markers))
                {
                    foreach (var m in markers)
                    {
                        outputLines.Add(m);
                    }
                }
            }

            return string.Join("\n", outputLines);
        }
    }
}
