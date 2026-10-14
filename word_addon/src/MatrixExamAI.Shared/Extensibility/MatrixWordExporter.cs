using System;
using System.Collections.Generic;
using System.IO;
using System.IO.Compression;
using System.Linq;
using System.Security;
using System.Text;

namespace MatrixExamAI.Shared.Extensibility
{
    /// <summary>
    /// Model đại diện cho một hàng trong Bảng 1: Ma trận đề thi (chuẩn BGD 19 cột Landscape).
    /// </summary>
    public class MatrixTopicRow
    {
        public int Stt { get; set; }
        public string Topic { get; set; } = string.Empty;
        public string Requirements { get; set; } = string.Empty;

        // Số câu: TN (NB, TH, VD), DS (NB, TH, VD), TLN (NB, TH, VD), TL (NB, TH, VD)
        public int TnNb { get; set; }
        public int TnTh { get; set; }
        public int TnVd { get; set; }

        public int DsNb { get; set; }
        public int DsTh { get; set; }
        public int DsVd { get; set; }

        public int TlnNb { get; set; }
        public int TlnTh { get; set; }
        public int TlnVd { get; set; }

        public int TlNb { get; set; }
        public int TlTh { get; set; }
        public int TlVd { get; set; }

        public double Points { get; set; } = 1.0;

        public int TotalNb => TnNb + DsNb + TlnNb + TlNb;
        public int TotalTh => TnTh + DsTh + TlnTh + TlTh;
        public int TotalVd => TnVd + DsVd + TlnVd + TlVd;
        public int TotalQuestions => TotalNb + TotalTh + TotalVd;
    }

    /// <summary>
    /// Model đại diện cho một hàng trong Bảng 2: Bản đặc tả đề thi (chuẩn BGD 6 cột).
    /// </summary>
    public class MatrixSpecRow
    {
        public string Stt { get; set; } = string.Empty;
        public string Topic { get; set; } = string.Empty;
        public string CognitiveLevel { get; set; } = "Nhận biết"; // Nhận biết, Thông hiểu, Vận dụng, Vận dụng cao
        public string QuestionType { get; set; } = "TN"; // TN, DS, TLN, TL
        public string QuestionCodes { get; set; } = string.Empty; // Ví dụ: "Câu 1, 2"
        public string RequiredOutcome { get; set; } = string.Empty; // Yêu cầu cần đạt
    }

    /// <summary>
    /// Dữ liệu toàn diện của Ma trận & Bản đặc tả đề thi chuẩn Bộ GD&ĐT 2025.
    /// </summary>
    public class ExamMatrixData
    {
        public string Title { get; set; } = "MA TRẬN ĐỀ KIỂM TRA ĐỊNH KỲ";
        public string Subject { get; set; } = "TOÁN HỌC";
        public string Grade { get; set; } = "12";
        public string SchoolYear { get; set; } = "2025 - 2026";
        public int DurationMinutes { get; set; } = 90;
        public double TotalPoints { get; set; } = 10.0;

        public List<MatrixTopicRow> Rows { get; set; } = new List<MatrixTopicRow>();
        public List<MatrixSpecRow> Specs { get; set; } = new List<MatrixSpecRow>();
    }

    /// <summary>
    /// Dịch vụ xuất tệp Microsoft Word (.docx) chứa BẢNG 1: MA TRẬN ĐỀ KIỂM TRA (19 cột Landscape A4)
    /// và BẢNG 2: BẢN ĐẶC TẢ ĐỀ KIỂM TRA (6 cột) chuẩn Công văn 7991/BGDĐT ngày 17/12/2024.
    /// Hoàn toàn độc lập, kế thừa chuẩn xác từ export/matrix_exporter.py và export/template_matrix.py.
    /// </summary>
    public class MatrixWordExporter
    {
        /// <summary>
        /// Tạo mẫu ma trận chuẩn THPT 2025 với 4 mức độ nhận thức (Nhận biết, Thông hiểu, Vận dụng, Vận dụng cao).
        /// </summary>
        public static ExamMatrixData CreateStandardHighSchoolMatrix(string subject = "TOÁN HỌC", string grade = "12")
        {
            var data = new ExamMatrixData
            {
                Title = $"MA TRẬN VÀ BẢN ĐẶC TẢ ĐỀ KIỂM TRA MÔN {subject.ToUpperInvariant()}",
                Subject = subject,
                Grade = grade,
                SchoolYear = "2025 - 2026",
                DurationMinutes = 90,
                TotalPoints = 10.0
            };

            // 3 chủ đề mẫu chuẩn THPT
            data.Rows.Add(new MatrixTopicRow
            {
                Stt = 1,
                Topic = "Ứng dụng đạo hàm để khảo sát và vẽ đồ thị hàm số",
                Requirements = "Nhận biết tính đơn điệu, cực trị, đường tiệm cận; thông hiểu bảng biến thiên; vận dụng bài toán tiếp tuyến và thực tế.",
                TnNb = 4, TnTh = 2, TnVd = 1,
                DsNb = 0, DsTh = 1, DsVd = 1,
                TlnNb = 0, TlnTh = 1, TlnVd = 1,
                Points = 4.0
            });

            data.Rows.Add(new MatrixTopicRow
            {
                Stt = 2,
                Topic = "Nguyên hàm, tích phân và ứng dụng",
                Requirements = "Nhận biết nguyên hàm cơ bản; thông hiểu tích phân từng phần; vận dụng tính diện tích hình phẳng, thể tích khối tròn xoay.",
                TnNb = 2, TnTh = 2, TnVd = 1,
                DsNb = 0, DsTh = 1, DsVd = 0,
                TlnNb = 0, TlnTh = 1, TlnVd = 1,
                Points = 3.5
            });

            data.Rows.Add(new MatrixTopicRow
            {
                Stt = 3,
                Topic = "Phương pháp tọa độ trong không gian Oxyz",
                Requirements = "Nhận biết tọa độ vectơ, mặt cầu; thông hiểu phương trình mặt phẳng, đường thẳng; vận dụng khoảng cách và góc.",
                TnNb = 2, TnTh = 1, TnVd = 0,
                DsNb = 0, DsTh = 1, DsVd = 0,
                TlnNb = 0, TlnTh = 0, TlnVd = 1,
                Points = 2.5
            });

            // Bản đặc tả 6 cột
            data.Specs.Add(new MatrixSpecRow
            {
                Stt = "1",
                Topic = "Ứng dụng đạo hàm khảo sát hàm số",
                CognitiveLevel = "Nhận biết",
                QuestionType = "TN",
                QuestionCodes = "Câu 1, 2, 3, 4",
                RequiredOutcome = "Nhận biết khoảng đồng biến, nghịch biến, điểm cực trị của hàm số qua bảng biến thiên hoặc đồ thị."
            });
            data.Specs.Add(new MatrixSpecRow
            {
                Stt = "",
                Topic = "",
                CognitiveLevel = "Thông hiểu",
                QuestionType = "TN",
                QuestionCodes = "Câu 5, 6",
                RequiredOutcome = "Tìm đường tiệm cận đứng, tiệm cận ngang và GTLN-GTNN của hàm số trên đoạn."
            });
            data.Specs.Add(new MatrixSpecRow
            {
                Stt = "",
                Topic = "",
                CognitiveLevel = "Thông hiểu",
                QuestionType = "DS",
                QuestionCodes = "Câu 13 (a, b)",
                RequiredOutcome = "Xét tính đúng sai về chiều biến thiên và tiệm cận của hàm số phân thức bậc nhất/bậc nhất."
            });
            data.Specs.Add(new MatrixSpecRow
            {
                Stt = "",
                Topic = "",
                CognitiveLevel = "Vận dụng",
                QuestionType = "TLN",
                QuestionCodes = "Câu 17",
                RequiredOutcome = "Giải quyết bài toán tối ưu hóa diện tích, chi phí sản xuất trong thực tiễn liên quan đến hàm số."
            });
            data.Specs.Add(new MatrixSpecRow
            {
                Stt = "2",
                Topic = "Nguyên hàm và tích phân",
                CognitiveLevel = "Nhận biết",
                QuestionType = "TN",
                QuestionCodes = "Câu 7, 8",
                RequiredOutcome = "Tìm họ nguyên hàm của các hàm số lũy thừa, lượng giác, mũ cơ bản."
            });
            data.Specs.Add(new MatrixSpecRow
            {
                Stt = "",
                Topic = "",
                CognitiveLevel = "Vận dụng",
                QuestionType = "TLN",
                QuestionCodes = "Câu 18",
                RequiredOutcome = "Ứng dụng tích phân tính diện tích mảnh vườn hình parabol hoặc thể tích bồn chứa xăng dầu."
            });
            data.Specs.Add(new MatrixSpecRow
            {
                Stt = "3",
                Topic = "Hình học tọa độ Oxyz",
                CognitiveLevel = "Nhận biết",
                QuestionType = "TN",
                QuestionCodes = "Câu 9, 10",
                RequiredOutcome = "Xác định tọa độ tâm, bán kính mặt cầu và tọa độ vectơ pháp tuyến mặt phẳng."
            });
            data.Specs.Add(new MatrixSpecRow
            {
                Stt = "",
                Topic = "",
                CognitiveLevel = "Vận dụng cao",
                QuestionType = "TLN",
                QuestionCodes = "Câu 22",
                RequiredOutcome = "Tìm tọa độ điểm trên mặt cầu sao cho khoảng cách tới mặt phẳng đạt cực trị trong mô hình 3D thực tế."
            });

            return data;
        }

        /// <summary>
        /// Xuất ra tệp Word (.docx) chuẩn Landscape A4 chứa cả Bảng 1 (Ma trận 19 cột) và Bảng 2 (Bản đặc tả 6 cột).
        /// </summary>
        public static void ExportMatrixDocx(string filePath, ExamMatrixData matrix, string? examContent = null)
        {
            if (string.IsNullOrWhiteSpace(filePath)) throw new ArgumentNullException(nameof(filePath));
            if (matrix == null) throw new ArgumentNullException(nameof(matrix));

            byte[] bytes = GenerateDocxBytes(matrix, examContent);
            string? dir = Path.GetDirectoryName(filePath);
            if (!string.IsNullOrEmpty(dir) && !Directory.Exists(dir!))
            {
                Directory.CreateDirectory(dir!);
            }
            File.WriteAllBytes(filePath, bytes);
        }

        /// <summary>
        /// Tạo mảng byte của tệp Word (.docx) OpenXML tiêu chuẩn.
        /// </summary>
        public static byte[] GenerateDocxBytes(ExamMatrixData matrix, string? examContent = null)
        {
            using (var memoryStream = new MemoryStream())
            {
                using (var archive = new ZipArchive(memoryStream, ZipArchiveMode.Create, true))
                {
                    // 1. [Content_Types].xml
                    AddZipEntry(archive, "[Content_Types].xml", GetContentTypesXml());

                    // 2. _rels/.rels
                    AddZipEntry(archive, "_rels/.rels", GetRootRelsXml());

                    // 3. word/_rels/document.xml.rels
                    AddZipEntry(archive, "word/_rels/document.xml.rels", GetDocumentRelsXml());

                    // 4. word/styles.xml
                    AddZipEntry(archive, "word/styles.xml", GetStylesXml());

                    // 5. word/document.xml
                    string documentXml = BuildDocumentXml(matrix, examContent);
                    AddZipEntry(archive, "word/document.xml", documentXml);
                }

                return memoryStream.ToArray();
            }
        }

        private static void AddZipEntry(ZipArchive archive, string entryName, string content)
        {
            var entry = archive.CreateEntry(entryName, CompressionLevel.Optimal);
            using (var stream = entry.Open())
            using (var writer = new StreamWriter(stream, Encoding.UTF8))
            {
                writer.Write(content);
            }
        }

        private static string GetContentTypesXml()
        {
            return @"<?xml version=""1.0"" encoding=""UTF-8"" standalone=""yes""?>
<Types xmlns=""http://schemas.openxmlformats.org/package/2006/content-types"">
  <Default Extension=""rels"" ContentType=""application/vnd.openxmlformats-package.relationships+xml""/>
  <Default Extension=""xml"" ContentType=""application/xml""/>
  <Override PartName=""/word/document.xml"" ContentType=""application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml""/>
  <Override PartName=""/word/styles.xml"" ContentType=""application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml""/>
</Types>";
        }

        private static string GetRootRelsXml()
        {
            return @"<?xml version=""1.0"" encoding=""UTF-8"" standalone=""yes""?>
<Relationships xmlns=""http://schemas.openxmlformats.org/package/2006/relationships"">
  <Relationship Id=""rId1"" Type=""http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument"" Target=""word/document.xml""/>
</Relationships>";
        }

        private static string GetDocumentRelsXml()
        {
            return @"<?xml version=""1.0"" encoding=""UTF-8"" standalone=""yes""?>
<Relationships xmlns=""http://schemas.openxmlformats.org/package/2006/relationships"">
  <Relationship Id=""rId1"" Type=""http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles"" Target=""styles.xml""/>
</Relationships>";
        }

        private static string GetStylesXml()
        {
            return @"<?xml version=""1.0"" encoding=""UTF-8"" standalone=""yes""?>
<w:styles xmlns:w=""http://schemas.openxmlformats.org/wordprocessingml/2006/main"">
  <w:docDefaults>
    <w:rPrDefault>
      <w:rPr>
        <w:rFonts w:ascii=""Times New Roman"" w:hAnsi=""Times New Roman"" w:cs=""Times New Roman""/>
        <w:sz w:val=""22""/>
      </w:rPr>
    </w:rPrDefault>
    <w:pPrDefault>
      <w:pPr>
        <w:spacing w:line=""276"" w:lineRule=""auto"" w:before=""0"" w:after=""0""/>
      </w:pPr>
    </w:pPrDefault>
  </w:docDefaults>
  <w:style w:type=""paragraph"" w:default=""1"" w:styleId=""Normal"">
    <w:name w:val=""Normal""/>
  </w:style>
</w:styles>";
        }

        private static string BuildDocumentXml(ExamMatrixData matrix, string? examContent)
        {
            var sb = new StringBuilder();
            sb.Append(@"<?xml version=""1.0"" encoding=""UTF-8"" standalone=""yes""?>
<w:document xmlns:w=""http://schemas.openxmlformats.org/wordprocessingml/2006/main"">
<w:body>");

            // ── Tiêu đề chính ──
            sb.Append(CreateParagraph(matrix.Title.ToUpperInvariant(), bold: true, fontSize: 26, align: "center", spaceAfter: 60));
            string subtitle = $"Môn: {matrix.Subject.ToUpperInvariant()} — Lớp: {matrix.Grade} — Thời gian làm bài: {matrix.DurationMinutes} phút — Năm học: {matrix.SchoolYear}";
            sb.Append(CreateParagraph(subtitle, bold: false, fontSize: 22, align: "center", italic: true, spaceAfter: 180));

            // ── BẢNG 1: MA TRẬN ĐỀ KIỂM TRA (19 cột Landscape A4) ──
            sb.Append(CreateParagraph("BẢNG 1: MA TRẬN ĐỀ KIỂM TRA (THEO CÔNG VĂN 7991/BGDĐT)", bold: true, fontSize: 23, align: "center", spaceAfter: 100));
            sb.Append(BuildMatrix19ColTable(matrix));
            sb.Append(CreateParagraph("", spaceAfter: 200));

            // ── BẢNG 2: BẢN ĐẶC TẢ ĐỀ KIỂM TRA (6 cột) ──
            sb.Append(CreateParagraph("BẢNG 2: BẢN ĐẶC TẢ ĐỀ KIỂM TRA", bold: true, fontSize: 23, align: "center", spaceAfter: 100));
            sb.Append(BuildSpecification6ColTable(matrix));
            sb.Append(CreateParagraph("", spaceAfter: 240));

            // ── NỘI DUNG ĐỀ THI (Nếu kèm theo) ──
            if (!string.IsNullOrWhiteSpace(examContent))
            {
                sb.Append(CreateParagraph("NỘI DUNG ĐỀ THI HOÀN CHỈNH", bold: true, fontSize: 24, align: "center", spaceAfter: 140));
                var lines = examContent.Split(new[] { "\r\n", "\r", "\n" }, StringSplitOptions.None);
                foreach (var line in lines)
                {
                    string trimmed = line.Trim();
                    if (trimmed.StartsWith("PHẦN I") || trimmed.StartsWith("PHẦN II") || trimmed.StartsWith("PHẦN III") || trimmed.StartsWith("BẢNG ĐÁP ÁN"))
                    {
                        sb.Append(CreateParagraph(line, bold: true, fontSize: 22, spaceBefore: 120, spaceAfter: 60));
                    }
                    else if (trimmed.StartsWith("% Câu"))
                    {
                        sb.Append(CreateParagraph(line, bold: true, fontSize: 21, italic: true, spaceBefore: 80, spaceAfter: 40));
                    }
                    else
                    {
                        sb.Append(CreateParagraph(line, fontSize: 22, spaceAfter: 40));
                    }
                }
            }

            // ── Thiết lập trang A4 Landscape (Ngang: 29.7cm x 21.0cm, Lề 1.5cm) ──
            // 29.7 cm = 16838 twips, 21.0 cm = 11906 twips, 1.5 cm = 850 twips
            sb.Append(@"<w:sectPr>
  <w:pgSz w:w=""16838"" w:h=""11906"" w:orient=""landscape""/>
  <w:pgMar w:top=""850"" w:right=""850"" w:bottom=""850"" w:left=""850"" w:header=""708"" w:footer=""708"" w:gutter=""0""/>
</w:sectPr>");

            sb.Append("</w:body></w:document>");
            return sb.ToString();
        }

        private static string CreateParagraph(string text, bool bold = false, bool italic = false, int fontSize = 22, string align = "left", int spaceBefore = 0, int spaceAfter = 0)
        {
            string esc = SecurityElement.Escape(text) ?? string.Empty;
            var sb = new StringBuilder();
            sb.Append("<w:p><w:pPr>");
            if (align != "left")
            {
                sb.Append($"<w:jc w:val=\"{align}\"/>");
            }
            sb.Append($"<w:spacing w:before=\"{spaceBefore}\" w:after=\"{spaceAfter}\"/>");
            sb.Append("</w:pPr>");

            sb.Append("<w:r><w:rPr>");
            if (bold) sb.Append("<w:b/>");
            if (italic) sb.Append("<w:i/>");
            sb.Append($"<w:sz w:val=\"{fontSize}\"/><w:szCs w:val=\"{fontSize}\"/>");
            sb.Append("</w:rPr>");
            sb.Append($"<w:t xml:space=\"preserve\">{esc}</w:t>");
            sb.Append("</w:r></w:p>");
            return sb.ToString();
        }

        private static string BuildMatrix19ColTable(ExamMatrixData matrix)
        {
            var sb = new StringBuilder();
            sb.Append(@"<w:tbl>
  <w:tblPr>
    <w:tblW w:w=""15138"" w:type=""dxa""/>
    <w:jc w:val=""center""/>
    <w:tblBorders>
      <w:top w:val=""single"" w:sz=""4"" w:space=""0"" w:color=""auto""/>
      <w:left w:val=""single"" w:sz=""4"" w:space=""0"" w:color=""auto""/>
      <w:bottom w:val=""single"" w:sz=""4"" w:space=""0"" w:color=""auto""/>
      <w:right w:val=""single"" w:sz=""4"" w:space=""0"" w:color=""auto""/>
      <w:insideH w:val=""single"" w:sz=""4"" w:space=""0"" w:color=""auto""/>
      <w:insideV w:val=""single"" w:sz=""4"" w:space=""0"" w:color=""auto""/>
    </w:tblBorders>
    <w:tblCellMar>
      <w:top w:w=""80"" w:type=""dxa""/>
      <w:left w:w=""100"" w:type=""dxa""/>
      <w:bottom w:w=""80"" w:type=""dxa""/>
      <w:right w:w=""100"" w:type=""dxa""/>
    </w:tblCellMar>
  </w:tblPr>");

            // 19 grid columns (widths in twips)
            // Col 0: TT (500)
            // Col 1: Chủ đề (2200)
            // Col 2: Nội dung (2800)
            // Col 3-14: TN (3), DS (3), TLN (3), TL (3) = 12 * 680 = 8160
            // Col 15-17: Tổng NB, TH, VD = 3 * 700 = 2100
            // Col 18: % điểm = 750
            int[] colWidths = new int[]
            {
                500, 2000, 2500,
                680, 680, 680,
                680, 680, 680,
                680, 680, 680,
                680, 680, 680,
                700, 700, 700,
                800
            };

            sb.Append("<w:tblGrid>");
            foreach (int w in colWidths)
            {
                sb.Append($"<w:gridCol w:w=\"{w}\"/>");
            }
            sb.Append("</w:tblGrid>");

            string headerShd = "D9E2F3";
            string footerShd = "E2EFDA";

            // ── ROW 0 ──
            sb.Append("<w:tr>");
            sb.Append(MakeCell("TT", 500, bold: true, align: "center", fill: headerShd, vMerge: "restart"));
            sb.Append(MakeCell("Chủ đề /\nChương", 2000, bold: true, align: "center", fill: headerShd, vMerge: "restart"));
            sb.Append(MakeCell("Nội dung /\nĐơn vị kiến thức", 2500, bold: true, align: "center", fill: headerShd, vMerge: "restart"));
            sb.Append(MakeCell("Mức độ đánh giá", 680 * 12, bold: true, align: "center", fill: headerShd, gridSpan: 12));
            sb.Append(MakeCell("Tổng", 700 * 3, bold: true, align: "center", fill: headerShd, gridSpan: 3, vMerge: "restart"));
            sb.Append(MakeCell("Tỉ lệ %\ntổng điểm", 800, bold: true, align: "center", fill: headerShd, vMerge: "restart"));
            sb.Append("</w:tr>");

            // ── ROW 1 ──
            sb.Append("<w:tr>");
            sb.Append(MakeCell("", 500, fill: headerShd, vMerge: "continue"));
            sb.Append(MakeCell("", 2000, fill: headerShd, vMerge: "continue"));
            sb.Append(MakeCell("", 2500, fill: headerShd, vMerge: "continue"));
            sb.Append(MakeCell("Trắc nghiệm khách quan", 680 * 9, bold: true, align: "center", fill: headerShd, gridSpan: 9));
            sb.Append(MakeCell("Tự luận", 680 * 3, bold: true, align: "center", fill: headerShd, gridSpan: 3));
            sb.Append(MakeCell("", 700 * 3, fill: headerShd, gridSpan: 3, vMerge: "continue"));
            sb.Append(MakeCell("", 800, fill: headerShd, vMerge: "continue"));
            sb.Append("</w:tr>");

            // ── ROW 2 ──
            sb.Append("<w:tr>");
            sb.Append(MakeCell("", 500, fill: headerShd, vMerge: "continue"));
            sb.Append(MakeCell("", 2000, fill: headerShd, vMerge: "continue"));
            sb.Append(MakeCell("", 2500, fill: headerShd, vMerge: "continue"));
            sb.Append(MakeCell("Nhiều lựa chọn\n(TN)", 680 * 3, bold: true, align: "center", fill: headerShd, gridSpan: 3));
            sb.Append(MakeCell("Đúng – Sai\n(DS)", 680 * 3, bold: true, align: "center", fill: headerShd, gridSpan: 3));
            sb.Append(MakeCell("Trả lời ngắn\n(TLN)", 680 * 3, bold: true, align: "center", fill: headerShd, gridSpan: 3));
            sb.Append(MakeCell("Tự luận\n(TL)", 680 * 3, bold: true, align: "center", fill: headerShd, gridSpan: 3));
            sb.Append(MakeCell("", 700 * 3, fill: headerShd, gridSpan: 3, vMerge: "continue"));
            sb.Append(MakeCell("", 800, fill: headerShd, vMerge: "continue"));
            sb.Append("</w:tr>");

            // ── ROW 3 ──
            sb.Append("<w:tr>");
            sb.Append(MakeCell("", 500, fill: headerShd, vMerge: "continue"));
            sb.Append(MakeCell("", 2000, fill: headerShd, vMerge: "continue"));
            sb.Append(MakeCell("", 2500, fill: headerShd, vMerge: "continue"));

            // 4 qtypes x 3 levels
            for (int i = 0; i < 4; i++)
            {
                sb.Append(MakeCell("NB", 680, bold: true, align: "center", fill: headerShd, fontSize: 18));
                sb.Append(MakeCell("TH", 680, bold: true, align: "center", fill: headerShd, fontSize: 18));
                sb.Append(MakeCell("VD", 680, bold: true, align: "center", fill: headerShd, fontSize: 18));
            }

            // Tổng x 3 levels
            sb.Append(MakeCell("NB", 700, bold: true, align: "center", fill: headerShd, fontSize: 18));
            sb.Append(MakeCell("TH", 700, bold: true, align: "center", fill: headerShd, fontSize: 18));
            sb.Append(MakeCell("VD", 700, bold: true, align: "center", fill: headerShd, fontSize: 18));

            sb.Append(MakeCell("", 800, fill: headerShd, vMerge: "continue"));
            sb.Append("</w:tr>");

            // ── DATA ROWS ──
            double totalPointsAll = matrix.Rows.Sum(r => r.Points);
            if (totalPointsAll <= 0) totalPointsAll = 10.0;

            foreach (var row in matrix.Rows)
            {
                sb.Append("<w:tr>");
                sb.Append(MakeCell(row.Stt.ToString(), 500, align: "center"));
                sb.Append(MakeCell(row.Topic, 2000, align: "left", bold: true));
                sb.Append(MakeCell(row.Requirements, 2500, align: "left", fontSize: 18));

                // TN
                sb.Append(MakeCell(NumStr(row.TnNb), 680, align: "center"));
                sb.Append(MakeCell(NumStr(row.TnTh), 680, align: "center"));
                sb.Append(MakeCell(NumStr(row.TnVd), 680, align: "center"));

                // DS
                sb.Append(MakeCell(NumStr(row.DsNb), 680, align: "center"));
                sb.Append(MakeCell(NumStr(row.DsTh), 680, align: "center"));
                sb.Append(MakeCell(NumStr(row.DsVd), 680, align: "center"));

                // TLN
                sb.Append(MakeCell(NumStr(row.TlnNb), 680, align: "center"));
                sb.Append(MakeCell(NumStr(row.TlnTh), 680, align: "center"));
                sb.Append(MakeCell(NumStr(row.TlnVd), 680, align: "center"));

                // TL
                sb.Append(MakeCell(NumStr(row.TlNb), 680, align: "center"));
                sb.Append(MakeCell(NumStr(row.TlTh), 680, align: "center"));
                sb.Append(MakeCell(NumStr(row.TlVd), 680, align: "center"));

                // Tổng NB, TH, VD
                sb.Append(MakeCell(NumStr(row.TotalNb), 700, align: "center", bold: true));
                sb.Append(MakeCell(NumStr(row.TotalTh), 700, align: "center", bold: true));
                sb.Append(MakeCell(NumStr(row.TotalVd), 700, align: "center", bold: true));

                // % Điểm
                double pct = (row.Points / totalPointsAll) * 100.0;
                sb.Append(MakeCell($"{pct:0.#}%", 800, align: "center", bold: true));

                sb.Append("</w:tr>");
            }

            // ── 3 FOOTER ROWS ──
            // 1. Tổng số câu
            int sumTnNb = matrix.Rows.Sum(r => r.TnNb);
            int sumTnTh = matrix.Rows.Sum(r => r.TnTh);
            int sumTnVd = matrix.Rows.Sum(r => r.TnVd);

            int sumDsNb = matrix.Rows.Sum(r => r.DsNb);
            int sumDsTh = matrix.Rows.Sum(r => r.DsTh);
            int sumDsVd = matrix.Rows.Sum(r => r.DsVd);

            int sumTlnNb = matrix.Rows.Sum(r => r.TlnNb);
            int sumTlnTh = matrix.Rows.Sum(r => r.TlnTh);
            int sumTlnVd = matrix.Rows.Sum(r => r.TlnVd);

            int sumTlNb = matrix.Rows.Sum(r => r.TlNb);
            int sumTlTh = matrix.Rows.Sum(r => r.TlTh);
            int sumTlVd = matrix.Rows.Sum(r => r.TlVd);

            int sumTotNb = matrix.Rows.Sum(r => r.TotalNb);
            int sumTotTh = matrix.Rows.Sum(r => r.TotalTh);
            int sumTotVd = matrix.Rows.Sum(r => r.TotalVd);
            int sumTotalAllQuestions = matrix.Rows.Sum(r => r.TotalQuestions);

            sb.Append("<w:tr>");
            sb.Append(MakeCell("Tổng số câu", 5000, bold: true, align: "center", fill: footerShd, gridSpan: 3));
            sb.Append(MakeCell(NumStr(sumTnNb), 680, bold: true, align: "center", fill: footerShd));
            sb.Append(MakeCell(NumStr(sumTnTh), 680, bold: true, align: "center", fill: footerShd));
            sb.Append(MakeCell(NumStr(sumTnVd), 680, bold: true, align: "center", fill: footerShd));

            sb.Append(MakeCell(NumStr(sumDsNb), 680, bold: true, align: "center", fill: footerShd));
            sb.Append(MakeCell(NumStr(sumDsTh), 680, bold: true, align: "center", fill: footerShd));
            sb.Append(MakeCell(NumStr(sumDsVd), 680, bold: true, align: "center", fill: footerShd));

            sb.Append(MakeCell(NumStr(sumTlnNb), 680, bold: true, align: "center", fill: footerShd));
            sb.Append(MakeCell(NumStr(sumTlnTh), 680, bold: true, align: "center", fill: footerShd));
            sb.Append(MakeCell(NumStr(sumTlnVd), 680, bold: true, align: "center", fill: footerShd));

            sb.Append(MakeCell(NumStr(sumTlNb), 680, bold: true, align: "center", fill: footerShd));
            sb.Append(MakeCell(NumStr(sumTlTh), 680, bold: true, align: "center", fill: footerShd));
            sb.Append(MakeCell(NumStr(sumTlVd), 680, bold: true, align: "center", fill: footerShd));

            sb.Append(MakeCell(NumStr(sumTotNb), 700, bold: true, align: "center", fill: footerShd));
            sb.Append(MakeCell(NumStr(sumTotTh), 700, bold: true, align: "center", fill: footerShd));
            sb.Append(MakeCell(NumStr(sumTotVd), 700, bold: true, align: "center", fill: footerShd));

            sb.Append(MakeCell(sumTotalAllQuestions.ToString(), 800, bold: true, align: "center", fill: footerShd));
            sb.Append("</w:tr>");

            // 2. Tổng số điểm
            sb.Append("<w:tr>");
            sb.Append(MakeCell("Tổng số điểm", 5000, bold: true, align: "center", fill: footerShd, gridSpan: 3));
            sb.Append(MakeCell((sumTnNb * 0.25).ToString("0.##"), 680, bold: true, align: "center", fill: footerShd));
            sb.Append(MakeCell((sumTnTh * 0.25).ToString("0.##"), 680, bold: true, align: "center", fill: footerShd));
            sb.Append(MakeCell((sumTnVd * 0.25).ToString("0.##"), 680, bold: true, align: "center", fill: footerShd));

            sb.Append(MakeCell((sumDsNb * 1.0).ToString("0.##"), 680, bold: true, align: "center", fill: footerShd));
            sb.Append(MakeCell((sumDsTh * 1.0).ToString("0.##"), 680, bold: true, align: "center", fill: footerShd));
            sb.Append(MakeCell((sumDsVd * 1.0).ToString("0.##"), 680, bold: true, align: "center", fill: footerShd));

            sb.Append(MakeCell((sumTlnNb * 0.5).ToString("0.##"), 680, bold: true, align: "center", fill: footerShd));
            sb.Append(MakeCell((sumTlnTh * 0.5).ToString("0.##"), 680, bold: true, align: "center", fill: footerShd));
            sb.Append(MakeCell((sumTlnVd * 0.5).ToString("0.##"), 680, bold: true, align: "center", fill: footerShd));

            sb.Append(MakeCell((sumTlNb * 1.0).ToString("0.##"), 680, bold: true, align: "center", fill: footerShd));
            sb.Append(MakeCell((sumTlTh * 1.0).ToString("0.##"), 680, bold: true, align: "center", fill: footerShd));
            sb.Append(MakeCell((sumTlVd * 1.0).ToString("0.##"), 680, bold: true, align: "center", fill: footerShd));

            // Tổng điểm theo mức độ
            double ptsNb = (sumTnNb * 0.25) + (sumDsNb * 1.0) + (sumTlnNb * 0.5) + (sumTlNb * 1.0);
            double ptsTh = (sumTnTh * 0.25) + (sumDsTh * 1.0) + (sumTlnTh * 0.5) + (sumTlTh * 1.0);
            double ptsVd = (sumTnVd * 0.25) + (sumDsVd * 1.0) + (sumTlnVd * 0.5) + (sumTlVd * 1.0);

            sb.Append(MakeCell(ptsNb.ToString("0.##"), 700, bold: true, align: "center", fill: footerShd));
            sb.Append(MakeCell(ptsTh.ToString("0.##"), 700, bold: true, align: "center", fill: footerShd));
            sb.Append(MakeCell(ptsVd.ToString("0.##"), 700, bold: true, align: "center", fill: footerShd));

            sb.Append(MakeCell(totalPointsAll.ToString("0.##"), 800, bold: true, align: "center", fill: footerShd));
            sb.Append("</w:tr>");

            // 3. Tỉ lệ %
            sb.Append("<w:tr>");
            sb.Append(MakeCell("Tỉ lệ %", 5000, bold: true, align: "center", fill: footerShd, gridSpan: 3));
            sb.Append(MakeCell(PctStr(sumTnNb * 0.25, totalPointsAll), 680, bold: true, align: "center", fill: footerShd));
            sb.Append(MakeCell(PctStr(sumTnTh * 0.25, totalPointsAll), 680, bold: true, align: "center", fill: footerShd));
            sb.Append(MakeCell(PctStr(sumTnVd * 0.25, totalPointsAll), 680, bold: true, align: "center", fill: footerShd));

            sb.Append(MakeCell(PctStr(sumDsNb * 1.0, totalPointsAll), 680, bold: true, align: "center", fill: footerShd));
            sb.Append(MakeCell(PctStr(sumDsTh * 1.0, totalPointsAll), 680, bold: true, align: "center", fill: footerShd));
            sb.Append(MakeCell(PctStr(sumDsVd * 1.0, totalPointsAll), 680, bold: true, align: "center", fill: footerShd));

            sb.Append(MakeCell(PctStr(sumTlnNb * 0.5, totalPointsAll), 680, bold: true, align: "center", fill: footerShd));
            sb.Append(MakeCell(PctStr(sumTlnTh * 0.5, totalPointsAll), 680, bold: true, align: "center", fill: footerShd));
            sb.Append(MakeCell(PctStr(sumTlnVd * 0.5, totalPointsAll), 680, bold: true, align: "center", fill: footerShd));

            sb.Append(MakeCell(PctStr(sumTlNb * 1.0, totalPointsAll), 680, bold: true, align: "center", fill: footerShd));
            sb.Append(MakeCell(PctStr(sumTlTh * 1.0, totalPointsAll), 680, bold: true, align: "center", fill: footerShd));
            sb.Append(MakeCell(PctStr(sumTlVd * 1.0, totalPointsAll), 680, bold: true, align: "center", fill: footerShd));

            sb.Append(MakeCell(PctStr(ptsNb, totalPointsAll), 700, bold: true, align: "center", fill: footerShd));
            sb.Append(MakeCell(PctStr(ptsTh, totalPointsAll), 700, bold: true, align: "center", fill: footerShd));
            sb.Append(MakeCell(PctStr(ptsVd, totalPointsAll), 700, bold: true, align: "center", fill: footerShd));

            sb.Append(MakeCell("100%", 800, bold: true, align: "center", fill: footerShd));
            sb.Append("</w:tr>");

            sb.Append("</w:tbl>");
            return sb.ToString();
        }

        private static string BuildSpecification6ColTable(ExamMatrixData matrix)
        {
            var sb = new StringBuilder();
            sb.Append(@"<w:tbl>
  <w:tblPr>
    <w:tblW w:w=""15138"" w:type=""dxa""/>
    <w:jc w:val=""center""/>
    <w:tblBorders>
      <w:top w:val=""single"" w:sz=""4"" w:space=""0"" w:color=""auto""/>
      <w:left w:val=""single"" w:sz=""4"" w:space=""0"" w:color=""auto""/>
      <w:bottom w:val=""single"" w:sz=""4"" w:space=""0"" w:color=""auto""/>
      <w:right w:val=""single"" w:sz=""4"" w:space=""0"" w:color=""auto""/>
      <w:insideH w:val=""single"" w:sz=""4"" w:space=""0"" w:color=""auto""/>
      <w:insideV w:val=""single"" w:sz=""4"" w:space=""0"" w:color=""auto""/>
    </w:tblBorders>
    <w:tblCellMar>
      <w:top w:w=""100"" w:type=""dxa""/>
      <w:left w:w=""120"" w:type=""dxa""/>
      <w:bottom w:w=""100"" w:type=""dxa""/>
      <w:right w:w=""120"" w:type=""dxa""/>
    </w:tblCellMar>
  </w:tblPr>");

            // 6 Columns: STT(700), Nội dung(3000), Mức độ(1800), Dạng(1400), Mã câu(2200), Yêu cầu cần đạt(6038)
            int[] colWidths = new int[] { 700, 3000, 1800, 1400, 2200, 6038 };

            sb.Append("<w:tblGrid>");
            foreach (int w in colWidths)
            {
                sb.Append($"<w:gridCol w:w=\"{w}\"/>");
            }
            sb.Append("</w:tblGrid>");

            string headerShd = "D9E2F3";

            // Header row
            sb.Append("<w:tr>");
            sb.Append(MakeCell("STT", 700, bold: true, align: "center", fill: headerShd));
            sb.Append(MakeCell("Nội dung kiến thức", 3000, bold: true, align: "center", fill: headerShd));
            sb.Append(MakeCell("Mức độ nhận thức", 1800, bold: true, align: "center", fill: headerShd));
            sb.Append(MakeCell("Dạng câu hỏi", 1400, bold: true, align: "center", fill: headerShd));
            sb.Append(MakeCell("Số câu / Mã câu", 2200, bold: true, align: "center", fill: headerShd));
            sb.Append(MakeCell("Yêu cầu cần đạt", 6038, bold: true, align: "center", fill: headerShd));
            sb.Append("</w:tr>");

            // Data rows
            int idx = 1;
            foreach (var spec in matrix.Specs)
            {
                string sttDisplay = !string.IsNullOrEmpty(spec.Stt) ? spec.Stt : (string.IsNullOrEmpty(spec.Topic) ? "" : (idx++).ToString());
                sb.Append("<w:tr>");
                sb.Append(MakeCell(sttDisplay, 700, align: "center"));
                sb.Append(MakeCell(spec.Topic, 3000, align: "left", bold: !string.IsNullOrEmpty(spec.Topic)));
                sb.Append(MakeCell(spec.CognitiveLevel, 1800, align: "center"));
                sb.Append(MakeCell(spec.QuestionType, 1400, align: "center"));
                sb.Append(MakeCell(spec.QuestionCodes, 2200, align: "center"));
                sb.Append(MakeCell(spec.RequiredOutcome, 6038, align: "left"));
                sb.Append("</w:tr>");
            }

            sb.Append("</w:tbl>");
            return sb.ToString();
        }

        private static string MakeCell(
            string text,
            int width,
            bool bold = false,
            string align = "left",
            string? fill = null,
            int gridSpan = 1,
            string? vMerge = null,
            int fontSize = 20)
        {
            var sb = new StringBuilder();
            sb.Append("<w:tc><w:tcPr>");
            sb.Append($"<w:tcW w:w=\"{width}\" w:type=\"dxa\"/>");
            if (gridSpan > 1)
            {
                sb.Append($"<w:gridSpan w:val=\"{gridSpan}\"/>");
            }
            if (!string.IsNullOrEmpty(vMerge))
            {
                if (vMerge == "restart") sb.Append("<w:vMerge w:val=\"restart\"/>");
                else if (vMerge == "continue") sb.Append("<w:vMerge/>");
            }
            if (!string.IsNullOrEmpty(fill))
            {
                sb.Append($"<w:shd w:val=\"clear\" w:color=\"auto\" w:fill=\"{fill}\"/>");
            }
            sb.Append("<w:vAlign w:val=\"center\"/>");
            sb.Append("</w:tcPr>");

            var lines = (text ?? string.Empty).Split(new[] { "\n" }, StringSplitOptions.None);
            for (int i = 0; i < lines.Length; i++)
            {
                string line = lines[i];
                string esc = SecurityElement.Escape(line) ?? string.Empty;
                sb.Append("<w:p><w:pPr>");
                if (align != "left")
                {
                    sb.Append($"<w:jc w:val=\"{align}\"/>");
                }
                sb.Append("<w:spacing w:line=\"240\" w:lineRule=\"auto\" w:before=\"0\" w:after=\"0\"/>");
                sb.Append("</w:pPr>");

                if (!string.IsNullOrEmpty(esc))
                {
                    sb.Append("<w:r><w:rPr>");
                    if (bold) sb.Append("<w:b/>");
                    sb.Append($"<w:sz w:val=\"{fontSize}\"/><w:szCs w:val=\"{fontSize}\"/>");
                    sb.Append("</w:rPr>");
                    sb.Append($"<w:t xml:space=\"preserve\">{esc}</w:t>");
                    sb.Append("</w:r>");
                }
                sb.Append("</w:p>");
            }

            sb.Append("</w:tc>");
            return sb.ToString();
        }

        private static string NumStr(int val)
        {
            return val > 0 ? val.ToString() : "";
        }

        private static string PctStr(double val, double total)
        {
            if (total <= 0 || val <= 0) return "";
            double pct = (val / total) * 100.0;
            return $"{pct:0.#}%";
        }
    }
}
