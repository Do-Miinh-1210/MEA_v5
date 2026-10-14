using System;
using System.Collections.Generic;
using System.IO;
using System.Threading;
using System.Windows;
using System.Windows.Media;
using System.Windows.Media.Imaging;

namespace MatrixExamAI.Desktop.Services
{
    /// <summary>
    /// Thông tin tọa độ các ô bong bóng OMR phục vụ chấm thi tự động.
    /// Kế thừa trực tiếp từ layout_meta trong omr_exam/sheet_generator.py.
    /// </summary>
    public class OmrLayoutMetadata
    {
        public int Width { get; set; } = 1240;
        public int Height { get; set; } = 1754;
        public int Dpi { get; set; } = 150;
        public List<Point> CornerMarkers { get; set; } = new List<Point>();
        public Dictionary<int, Dictionary<int, Point>> CodeBubbles { get; set; } = new Dictionary<int, Dictionary<int, Point>>();
        public Dictionary<int, Dictionary<string, Point>> QuestionBubbles { get; set; } = new Dictionary<int, Dictionary<string, Point>>();
        public bool HasEssay { get; set; }
    }

    /// <summary>
    /// Bộ sinh phiếu trả lời trắc nghiệm chuẩn OMR (Optical Mark Recognition).
    /// Thiết kế chuẩn A4 150 DPI (1240 x 1754 px), 4 mốc định vị góc (Corner Markers) cho camera nắn phối cảnh,
    /// vùng tô Mã đề thi (3 cột 0-9), vùng tô đáp án trắc nghiệm A-B-C-D và vùng tự luận.
    /// Kế thừa hoàn chỉnh từ omr_exam/sheet_generator.py.
    /// </summary>
    public static class OmrSheetGenerator
    {
        public const int A4Width = 1240;
        public const int A4Height = 1754;
        public const int MarkerSize = 50;
        public const int MarginX = 60;
        public const int MarginY = 60;

        /// <summary>
        /// Tạo ảnh phiếu OMR dạng PNG dưới dạng mảng byte.
        /// Tự động điều phối luồng STA an toàn khi chạy từ xUnit/MTA thread pool.
        /// </summary>
        public static byte[] GenerateOmrSheetPng(
            int numQuestions = 40,
            bool hasEssay = false,
            string examTitle = "PHIẾU TRẢ LỜI TRẮC NGHIỆM")
        {
            if (Thread.CurrentThread.GetApartmentState() == ApartmentState.STA)
            {
                return RenderOmrSheetInternal(numQuestions, hasEssay, examTitle, out _);
            }

            byte[]? result = null;
            Exception? error = null;

            var thread = new Thread(() =>
            {
                try
                {
                    result = RenderOmrSheetInternal(numQuestions, hasEssay, examTitle, out _);
                }
                catch (Exception ex)
                {
                    error = ex;
                }
            });

            thread.SetApartmentState(ApartmentState.STA);
            thread.IsBackground = true;
            thread.Start();
            thread.Join();

            if (error != null) throw new InvalidOperationException($"Lỗi vẽ phiếu OMR: {error.Message}", error);
            return result ?? Array.Empty<byte>();
        }

        /// <summary>
        /// Tạo và lưu phiếu OMR ra tệp ảnh PNG trên ổ đĩa.
        /// </summary>
        public static string SaveOmrSheet(
            string outputPath,
            int numQuestions = 40,
            bool hasEssay = false,
            string examTitle = "PHIẾU TRẢ LỜI TRẮC NGHIỆM")
        {
            if (string.IsNullOrWhiteSpace(outputPath)) throw new ArgumentNullException(nameof(outputPath));

            string? dir = Path.GetDirectoryName(outputPath);
            if (!string.IsNullOrEmpty(dir) && !Directory.Exists(dir!))
            {
                Directory.CreateDirectory(dir!);
            }

            byte[] bytes = GenerateOmrSheetPng(numQuestions, hasEssay, examTitle);
            File.WriteAllBytes(outputPath, bytes);
            return outputPath;
        }

        /// <summary>
        /// Trích xuất Metadata tọa độ các ô tô trắc nghiệm và mã đề phục vụ chấm điểm.
        /// </summary>
        public static OmrLayoutMetadata GetLayoutMetadata(int numQuestions = 40, bool hasEssay = false)
        {
            var meta = new OmrLayoutMetadata
            {
                Width = A4Width,
                Height = A4Height,
                Dpi = 150,
                HasEssay = hasEssay
            };

            // 4 Corner Markers
            meta.CornerMarkers.Add(new Point(MarginX, MarginY));
            meta.CornerMarkers.Add(new Point(A4Width - MarginX - MarkerSize, MarginY));
            meta.CornerMarkers.Add(new Point(MarginX, A4Height - MarginY - MarkerSize));
            meta.CornerMarkers.Add(new Point(A4Width - MarginX - MarkerSize, A4Height - MarginY - MarkerSize));

            // Mã đề: 3 cột, mỗi cột 10 số (0-9)
            int codeBoxX1 = A4Width / 2 + 30;
            int codeBoxY1 = MarginY + 70;
            int colSpacing = 55;
            int codeStartX = codeBoxX1 + 35;
            int codeStartY = codeBoxY1 + 45;

            for (int c = 0; c < 3; c++)
            {
                meta.CodeBubbles[c] = new Dictionary<int, Point>();
                int cx = codeStartX + c * colSpacing;
                for (int digit = 0; digit < 10; digit++)
                {
                    int cy = codeStartY + digit * 17;
                    meta.CodeBubbles[c][digit] = new Point(cx, cy);
                }
            }

            // Câu hỏi
            int ansStartY = MarginY + 280;
            int numCols = numQuestions <= 30 ? 2 : (hasEssay ? 3 : 4);
            int questionsPerCol = (int)Math.Ceiling((double)numQuestions / numCols);
            int colWidth = (A4Width - 2 * MarginX - 60) / numCols;
            string[] labels = { "A", "B", "C", "D" };
            int optSpacing = 38;

            for (int q = 1; q <= numQuestions; q++)
            {
                int colIdx = (q - 1) / questionsPerCol;
                int rowIdx = (q - 1) % questionsPerCol;
                int baseX = MarginX + 30 + colIdx * colWidth;
                int cy = ansStartY + rowIdx * 28;

                meta.QuestionBubbles[q] = new Dictionary<string, Point>();
                for (int i = 0; i < labels.Length; i++)
                {
                    int cx = baseX + 50 + i * optSpacing;
                    meta.QuestionBubbles[q][labels[i]] = new Point(cx, cy);
                }
            }

            return meta;
        }

        private static byte[] RenderOmrSheetInternal(
            int numQuestions,
            bool hasEssay,
            string examTitle,
            out OmrLayoutMetadata layoutMeta)
        {
            layoutMeta = GetLayoutMetadata(numQuestions, hasEssay);

            var visual = new DrawingVisual();
            using (var dc = visual.RenderOpen())
            {
                // 1. Nền trắng
                dc.DrawRectangle(Brushes.White, null, new Rect(0, 0, A4Width, A4Height));

                var penBlack2 = new Pen(Brushes.Black, 2.0);
                var penBlack3 = new Pen(Brushes.Black, 3.0);
                var penBlack1 = new Pen(Brushes.Black, 1.0);
                var penWhite3 = new Pen(Brushes.White, 3.0);

                var tfBold22 = new Typeface(new FontFamily("Arial"), FontStyles.Normal, FontWeights.Bold, FontStretches.Normal);
                var tfBold16 = new Typeface(new FontFamily("Arial"), FontStyles.Normal, FontWeights.Bold, FontStretches.Normal);
                var tfNormal12 = new Typeface(new FontFamily("Arial"), FontStyles.Normal, FontWeights.Normal, FontStretches.Normal);
                var tfBold11 = new Typeface(new FontFamily("Arial"), FontStyles.Normal, FontWeights.Bold, FontStretches.Normal);

                // 2. Vẽ 4 mốc định vị góc (Corner Markers 50x50)
                foreach (var pt in layoutMeta.CornerMarkers)
                {
                    // Lớp đen ngoài
                    dc.DrawRectangle(Brushes.Black, null, new Rect(pt.X, pt.Y, MarkerSize, MarkerSize));
                    // Lớp viền trắng
                    dc.DrawRectangle(null, penWhite3, new Rect(pt.X + 8, pt.Y + 8, MarkerSize - 16, MarkerSize - 16));
                    // Lớp đen tâm
                    dc.DrawRectangle(Brushes.Black, null, new Rect(pt.X + 16, pt.Y + 16, MarkerSize - 32, MarkerSize - 32));
                }

                // 3. Tiêu đề phiếu
                var titleText = new FormattedText(
                    examTitle.ToUpperInvariant(),
                    System.Globalization.CultureInfo.InvariantCulture,
                    FlowDirection.LeftToRight,
                    tfBold22,
                    22,
                    Brushes.Black,
                    1.25);
                double titleX = (A4Width - titleText.Width) / 2.0;
                dc.DrawText(titleText, new Point(titleX, MarginY + 12));

                // 4. Khung Thông tin thí sinh (Bên trái)
                double infoX1 = MarginX + MarkerSize + 25;
                double infoY1 = MarginY + 65;
                double infoW = (A4Width / 2.0) - infoX1 - 10;
                double infoH = 190;
                dc.DrawRectangle(null, penBlack2, new Rect(infoX1, infoY1, infoW, infoH));

                void DrawText(string t, double x, double y, Typeface tf, double sz, Brush brush)
                {
                    var ft = new FormattedText(t, System.Globalization.CultureInfo.InvariantCulture, FlowDirection.LeftToRight, tf, sz, brush, 1.25);
                    dc.DrawText(ft, new Point(x, y));
                }

                DrawText("Họ và tên thí sinh: ................................................................", infoX1 + 14, infoY1 + 14, tfNormal12, 12.5, Brushes.Black);
                DrawText("Ngày sinh: .................... Lớp: .................. Phòng thi: ............", infoX1 + 14, infoY1 + 50, tfNormal12, 12.5, Brushes.Black);
                DrawText("Chữ ký Giám thị 1: ................... Giám thị 2: ....................", infoX1 + 14, infoY1 + 86, tfNormal12, 12.5, Brushes.Black);
                DrawText("Số báo danh (SBD): .............................................................", infoX1 + 14, infoY1 + 122, tfNormal12, 12.5, Brushes.Black);
                DrawText("LƯU Ý: Dùng bút chì 2B tô ĐEN KÍN ô tròn. Tuyệt đối không gạch chéo.", infoX1 + 14, infoY1 + 158, tfBold11, 11, Brushes.DarkRed);

                // 5. Khung MÃ ĐỀ THI (Bên phải)
                double codeBoxX1 = A4Width / 2.0 + 20;
                double codeBoxY1 = MarginY + 65;
                double codeBoxW = (A4Width - MarginX - MarkerSize - 25) - codeBoxX1;
                double codeBoxH = 220;
                dc.DrawRectangle(null, penBlack2, new Rect(codeBoxX1, codeBoxY1, codeBoxW, codeBoxH));

                DrawText("MÃ ĐỀ THI", codeBoxX1 + (codeBoxW - 80) / 2.0, codeBoxY1 + 10, tfBold16, 15, Brushes.Black);

                // Bong bóng mã đề
                double bubbleRadius = 11.0;
                for (int c = 0; c < 3; c++)
                {
                    for (int digit = 0; digit < 10; digit++)
                    {
                        var pt = layoutMeta.CodeBubbles[c][digit];
                        dc.DrawEllipse(Brushes.White, penBlack2, pt, bubbleRadius, bubbleRadius);

                        var dt = new FormattedText(
                            digit.ToString(),
                            System.Globalization.CultureInfo.InvariantCulture,
                            FlowDirection.LeftToRight,
                            tfBold11,
                            11.5,
                            Brushes.Black,
                            1.25);
                        dc.DrawText(dt, new Point(pt.X - dt.Width / 2.0, pt.Y - dt.Height / 2.0));
                    }
                }

                // 6. VÙNG TÔ ĐÁP ÁN TRẮC NGHIỆM
                int ansStartY = MarginY + 300;
                int numCols = numQuestions <= 30 ? 2 : (hasEssay ? 3 : 4);
                int questionsPerCol = (int)Math.Ceiling((double)numQuestions / numCols);
                int colWidth = (A4Width - 2 * MarginX - 60) / numCols;
                string[] labels = { "A", "B", "C", "D" };

                for (int q = 1; q <= numQuestions; q++)
                {
                    int colIdx = (q - 1) / questionsPerCol;
                    int rowIdx = (q - 1) % questionsPerCol;
                    int baseX = MarginX + 30 + colIdx * colWidth;
                    int cy = ansStartY + rowIdx * 28;

                    // Số thứ tự câu (vd: 01., 12.)
                    string qLabel = $"{q:D2}.";
                    DrawText(qLabel, baseX, cy - 8, tfBold16, 13.5, Brushes.Black);

                    // 4 ô tròn A, B, C, D
                    foreach (string lbl in labels)
                    {
                        var pt = layoutMeta.QuestionBubbles[q][lbl];
                        dc.DrawEllipse(Brushes.White, penBlack2, pt, bubbleRadius, bubbleRadius);

                        var lt = new FormattedText(
                            lbl,
                            System.Globalization.CultureInfo.InvariantCulture,
                            FlowDirection.LeftToRight,
                            tfBold11,
                            11.5,
                            Brushes.Black,
                            1.25);
                        dc.DrawText(lt, new Point(pt.X - lt.Width / 2.0, pt.Y - lt.Height / 2.0));
                    }
                }

                // 7. VÙNG TỰ LUẬN (Nếu có)
                if (hasEssay)
                {
                    int tlStartY = ansStartY + questionsPerCol * 28 + 25;
                    dc.DrawLine(penBlack3, new Point(MarginX, tlStartY), new Point(A4Width - MarginX, tlStartY));
                    DrawText("PHẦN TRẢ LỜI CÂU HỎI TỰ LUẬN (TL):", MarginX + 20, tlStartY + 10, tfBold16, 13.5, Brushes.Black);

                    for (int line = 1; line <= 6; line++)
                    {
                        int ly = tlStartY + 25 + line * 32;
                        if (ly < A4Height - MarginY - MarkerSize - 10)
                        {
                            dc.DrawLine(penBlack1, new Point(MarginX + 30, ly), new Point(A4Width - MarginX - 30, ly));
                        }
                    }
                }
            }

            var rtb = new RenderTargetBitmap(A4Width, A4Height, 150, 150, PixelFormats.Pbgra32);
            rtb.Render(visual);

            var encoder = new PngBitmapEncoder();
            encoder.Frames.Add(BitmapFrame.Create(rtb));

            using (var ms = new MemoryStream())
            {
                encoder.Save(ms);
                return ms.ToArray();
            }
        }
    }
}
