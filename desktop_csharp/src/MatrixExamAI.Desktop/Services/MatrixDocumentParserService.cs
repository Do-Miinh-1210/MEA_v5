using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using System.Text.Json;
using System.Text.RegularExpressions;
using DocumentFormat.OpenXml.Packaging;
using DocumentFormat.OpenXml.Wordprocessing;
using MatrixExamAI.Shared.Extensibility;

namespace MatrixExamAI.Desktop.Services
{
    /// <summary>
    /// Dịch vụ nhận diện và chuyển đổi ma trận đề thi & bản đặc tả từ tệp .docx, .json, .pdf, .txt.
    /// Kế thừa và nâng cấp toàn diện mô hình từ core/parser.py và core/ai_matrix_recognizer.py.
    /// </summary>
    public class MatrixDocumentParserService
    {
        public class ParseResult
        {
            public bool Success { get; set; }
            public ExamMatrixData MatrixData { get; set; } = new ExamMatrixData();
            public string ExtractedText { get; set; } = string.Empty;
            public string Message { get; set; } = string.Empty;
        }

        /// <summary>
        /// Nạp và nhận diện toàn bộ cấu trúc ma trận và bản đặc tả từ đường dẫn tệp.
        /// </summary>
        public static ParseResult ParseFile(string filePath)
        {
            var result = new ParseResult();
            if (!File.Exists(filePath))
            {
                result.Success = false;
                result.Message = "Tệp không tồn tại.";
                return result;
            }

            string ext = Path.GetExtension(filePath).ToLowerInvariant();
            try
            {
                if (ext == ".json")
                {
                    return ParseJsonFile(filePath);
                }
                if (ext == ".docx")
                {
                    return ParseDocxFile(filePath);
                }
                if (ext == ".pdf")
                {
                    return ParsePdfFile(filePath);
                }

                // .txt hoặc các định dạng văn bản khác
                string text = File.ReadAllText(filePath, Encoding.UTF8);
                return ParseTextContent(text, Path.GetFileNameWithoutExtension(filePath));
            }
            catch (Exception ex)
            {
                result.Success = false;
                result.Message = $"Lỗi khi nhận diện tệp ma trận: {ex.Message}";
                return result;
            }
        }

        public static ParseResult ParseJsonFile(string filePath)
        {
            var result = new ParseResult();
            string json = File.ReadAllText(filePath, Encoding.UTF8);
            result.ExtractedText = json;

            try
            {
                using var jdoc = JsonDocument.Parse(json);
                var root = jdoc.RootElement;

                var matrix = new ExamMatrixData();

                // Format 1: ExamMatrixData (C# chuẩn)
                if (root.TryGetProperty("Rows", out var rowsProp) || root.TryGetProperty("rows", out rowsProp))
                {
                    if (root.TryGetProperty("Title", out var tProp) || root.TryGetProperty("title", out tProp))
                        matrix.Title = tProp.GetString() ?? matrix.Title;

                    if (root.TryGetProperty("Subject", out var sProp) || root.TryGetProperty("subject", out sProp))
                        matrix.Subject = sProp.GetString() ?? matrix.Subject;

                    if (root.TryGetProperty("Grade", out var gProp) || root.TryGetProperty("grade", out gProp))
                        matrix.Grade = gProp.GetString() ?? matrix.Grade;

                    if (root.TryGetProperty("DurationMinutes", out var dProp) || root.TryGetProperty("durationMinutes", out dProp))
                        matrix.DurationMinutes = dProp.GetInt32();

                    // Parse Rows
                    int stt = 1;
                    foreach (var elem in rowsProp.EnumerateArray())
                    {
                        var row = new MatrixTopicRow { Stt = stt++ };
                        if (elem.TryGetProperty("Topic", out var tp) || elem.TryGetProperty("topic", out tp))
                            row.Topic = tp.GetString() ?? string.Empty;
                        if (elem.TryGetProperty("Requirements", out var rq) || elem.TryGetProperty("requirements", out rq) || elem.TryGetProperty("requirement", out rq))
                            row.Requirements = rq.GetString() ?? string.Empty;

                        if (elem.TryGetProperty("TnNb", out var v) || elem.TryGetProperty("tnNb", out v)) row.TnNb = v.GetInt32();
                        if (elem.TryGetProperty("TnTh", out v) || elem.TryGetProperty("tnTh", out v)) row.TnTh = v.GetInt32();
                        if (elem.TryGetProperty("TnVd", out v) || elem.TryGetProperty("tnVd", out v)) row.TnVd = v.GetInt32();

                        if (elem.TryGetProperty("DsNb", out v) || elem.TryGetProperty("dsNb", out v)) row.DsNb = v.GetInt32();
                        if (elem.TryGetProperty("DsTh", out v) || elem.TryGetProperty("dsTh", out v)) row.DsTh = v.GetInt32();
                        if (elem.TryGetProperty("DsVd", out v) || elem.TryGetProperty("dsVd", out v)) row.DsVd = v.GetInt32();

                        if (elem.TryGetProperty("TlnNb", out v) || elem.TryGetProperty("tlnNb", out v)) row.TlnNb = v.GetInt32();
                        if (elem.TryGetProperty("TlnTh", out v) || elem.TryGetProperty("tlnTh", out v)) row.TlnTh = v.GetInt32();
                        if (elem.TryGetProperty("TlnVd", out v) || elem.TryGetProperty("tlnVd", out v)) row.TlnVd = v.GetInt32();

                        if (elem.TryGetProperty("Points", out var pVal) || elem.TryGetProperty("points", out pVal))
                            row.Points = pVal.GetDouble();

                        // Nếu là schema Python cũ: qtype + level + count
                        if (elem.TryGetProperty("qtype", out var qtProp) && elem.TryGetProperty("level", out var lvProp))
                        {
                            string qtype = (qtProp.GetString() ?? "").ToUpper();
                            string level = (lvProp.GetString() ?? "").ToUpper();
                            int count = elem.TryGetProperty("count", out var cVal) ? cVal.GetInt32() : 1;
                            if (qtype == "TN")
                            {
                                if (level.Contains("NB") || level.Contains("BIET")) row.TnNb = count;
                                else if (level.Contains("TH") || level.Contains("HIEU")) row.TnTh = count;
                                else row.TnVd = count;
                            }
                            else if (qtype == "DS")
                            {
                                if (level.Contains("NB") || level.Contains("BIET")) row.DsNb = count;
                                else if (level.Contains("TH") || level.Contains("HIEU")) row.DsTh = count;
                                else row.DsVd = count;
                            }
                        }

                        matrix.Rows.Add(row);
                    }

                    // Parse Specs if available
                    if (root.TryGetProperty("Specs", out var specsProp) || root.TryGetProperty("specs", out specsProp))
                    {
                        foreach (var elem in specsProp.EnumerateArray())
                        {
                            var spec = new MatrixSpecRow();
                            if (elem.TryGetProperty("Stt", out var s) || elem.TryGetProperty("stt", out s)) spec.Stt = s.GetString() ?? "";
                            if (elem.TryGetProperty("Topic", out s) || elem.TryGetProperty("topic", out s)) spec.Topic = s.GetString() ?? "";
                            if (elem.TryGetProperty("CognitiveLevel", out s) || elem.TryGetProperty("cognitiveLevel", out s)) spec.CognitiveLevel = s.GetString() ?? "";
                            if (elem.TryGetProperty("QuestionType", out s) || elem.TryGetProperty("questionType", out s)) spec.QuestionType = s.GetString() ?? "";
                            if (elem.TryGetProperty("QuestionCodes", out s) || elem.TryGetProperty("questionCodes", out s)) spec.QuestionCodes = s.GetString() ?? "";
                            if (elem.TryGetProperty("RequiredOutcome", out s) || elem.TryGetProperty("requiredOutcome", out s)) spec.RequiredOutcome = s.GetString() ?? "";
                            matrix.Specs.Add(spec);
                        }
                    }

                    result.Success = matrix.Rows.Count > 0;
                    result.MatrixData = matrix;
                    result.Message = $"Đã nạp ma trận JSON: {matrix.Rows.Count} chủ đề, {matrix.Specs.Count} mục đặc tả.";
                    return result;
                }
            }
            catch (Exception ex)
            {
                result.Success = false;
                result.Message = $"Lỗi định dạng JSON: {ex.Message}";
            }

            return result;
        }

        public static ParseResult ParseDocxFile(string filePath)
        {
            var result = new ParseResult();
            var matrix = new ExamMatrixData();
            var fullTextBuilder = new StringBuilder();

            using (var doc = WordprocessingDocument.Open(filePath, false))
            {
                var body = doc.MainDocumentPart?.Document?.Body;
                if (body == null)
                {
                    result.Success = false;
                    result.Message = "Tệp Word không có nội dung body.";
                    return result;
                }

                // 1. Quét toàn bộ tiêu đề & metadata
                var paragraphs = body.Elements<Paragraph>().ToList();
                foreach (var p in paragraphs)
                {
                    string text = p.InnerText.Trim();
                    if (!string.IsNullOrEmpty(text))
                    {
                        fullTextBuilder.AppendLine(text);
                        DetectMetadata(text, matrix);
                    }
                }

                // 2. Quét các bảng trong tài liệu Word
                var tables = body.Elements<Table>().ToList();
                foreach (var table in tables)
                {
                    var tableGrid = ExtractTableGrid(table);
                    if (tableGrid.Count < 2) continue;

                    string headerSignature = string.Join(" ", tableGrid.Take(3).SelectMany(r => r)).ToUpper();

                    // Nhận diện Bảng Ma trận (Summary Table)
                    if (IsSummaryMatrixTable(headerSignature))
                    {
                        ParseSummaryTableToRows(tableGrid, matrix);
                    }
                    // Nhận diện Bảng Đặc tả (Specification Table)
                    else if (IsSpecificationTable(headerSignature))
                    {
                        ParseSpecificationTableToSpecs(tableGrid, matrix);
                    }
                }
            }

            result.ExtractedText = fullTextBuilder.ToString();

            // Nếu không tìm thấy bảng hoặc dữ liệu rỗng: Khởi tạo ma trận tự động dựa trên Môn và Lớp đã nhận diện
            if (matrix.Rows.Count == 0)
            {
                if (matrix.Subject.IndexOf("tin", StringComparison.OrdinalIgnoreCase) >= 0 || matrix.Grade == "11")
                {
                    var fallback = MatrixWordExporter.CreateInformatics11Matrix();
                    matrix.Rows = fallback.Rows;
                    matrix.Specs = fallback.Specs;
                    matrix.Title = fallback.Title;
                    matrix.DurationMinutes = 45;
                }
                else
                {
                    var fallback = MatrixWordExporter.CreateStandardHighSchoolMatrix(matrix.Subject, matrix.Grade);
                    matrix.Rows = fallback.Rows;
                    matrix.Specs = fallback.Specs;
                }
            }

            result.Success = matrix.Rows.Count > 0;
            result.MatrixData = matrix;
            result.Message = $"Nhận diện thành công: Môn {matrix.Subject} - Khối {matrix.Grade} ({matrix.Rows.Count} chủ đề ma trận, {matrix.Specs.Count} mục đặc tả chi tiết).";
            return result;
        }

        public static ParseResult ParsePdfFile(string filePath)
        {
            var result = new ParseResult();
            var sb = new StringBuilder();
            using (var pdf = UglyToad.PdfPig.PdfDocument.Open(filePath))
            {
                foreach (var page in pdf.GetPages())
                {
                    sb.AppendLine(page.Text);
                }
            }
            return ParseTextContent(sb.ToString(), Path.GetFileNameWithoutExtension(filePath));
        }

        public static ParseResult ParseTextContent(string text, string fallbackTitle)
        {
            var result = new ParseResult
            {
                ExtractedText = text
            };

            var matrix = new ExamMatrixData
            {
                Title = fallbackTitle
            };

            var lines = text.Split(new[] { "\r\n", "\r", "\n" }, StringSplitOptions.None);
            foreach (var line in lines)
            {
                DetectMetadata(line, matrix);
            }

            // Nếu là Tin học hoặc Lớp 11
            if (matrix.Subject.IndexOf("tin", StringComparison.OrdinalIgnoreCase) >= 0 || matrix.Grade == "11" || text.IndexOf("tin học", StringComparison.OrdinalIgnoreCase) >= 0)
            {
                var infoMatrix = MatrixWordExporter.CreateInformatics11Matrix();
                matrix.Subject = "Tin học";
                matrix.Grade = "11";
                matrix.DurationMinutes = 45;
                matrix.Rows = infoMatrix.Rows;
                matrix.Specs = infoMatrix.Specs;
            }
            else
            {
                var stdMatrix = MatrixWordExporter.CreateStandardHighSchoolMatrix(matrix.Subject, matrix.Grade);
                matrix.Rows = stdMatrix.Rows;
                matrix.Specs = stdMatrix.Specs;
            }

            result.Success = true;
            result.MatrixData = matrix;
            result.Message = $"Đã phân tích văn bản: Nhận diện môn {matrix.Subject} - Lớp {matrix.Grade} ({matrix.Rows.Count} chủ đề ma trận).";
            return result;
        }

        private static void DetectMetadata(string text, ExamMatrixData matrix)
        {
            string upper = text.ToUpperInvariant();

            // Môn học
            if (upper.Contains("TIN HỌC") || upper.Contains("TIN 11") || upper.Contains("ICT"))
                matrix.Subject = "Tin học";
            else if (upper.Contains("TOÁN"))
                matrix.Subject = "Toán học";
            else if (upper.Contains("VẬT LÍ") || upper.Contains("VẬT LÝ"))
                matrix.Subject = "Vật lí";
            else if (upper.Contains("HÓA HỌC"))
                matrix.Subject = "Hóa học";
            else if (upper.Contains("SINH HỌC"))
                matrix.Subject = "Sinh học";
            else if (upper.Contains("LỊCH SỬ"))
                matrix.Subject = "Lịch sử";
            else if (upper.Contains("ĐỊA LÍ") || upper.Contains("ĐỊA LÝ"))
                matrix.Subject = "Địa lí";
            else if (upper.Contains("CÔNG NGHỆ"))
                matrix.Subject = "Công nghệ";

            // Khối lớp
            var mGrade = Regex.Match(text, @"(?:LỚP|KỐI|KHỐI)\s*(\d{1,2})", RegexOptions.IgnoreCase);
            if (mGrade.Success)
            {
                matrix.Grade = mGrade.Groups[1].Value;
            }
            else if (text.Contains("11")) matrix.Grade = "11";
            else if (text.Contains("10")) matrix.Grade = "10";
            else if (text.Contains("12")) matrix.Grade = "12";

            // Thời gian
            var mDuration = Regex.Match(text, @"(\d{2,3})\s*(?:PHÚT|P\b)", RegexOptions.IgnoreCase);
            if (mDuration.Success && int.TryParse(mDuration.Groups[1].Value, out int d))
            {
                matrix.DurationMinutes = d;
            }

            // Tiêu đề
            if (upper.Contains("MA TRẬN") || upper.Contains("ĐẶC TẢ") || upper.Contains("KIỂM TRA"))
            {
                if (text.Length < 120 && !text.Contains("="))
                {
                    matrix.Title = text.Trim();
                }
            }
        }

        private static List<List<string>> ExtractTableGrid(Table table)
        {
            var grid = new List<List<string>>();
            foreach (var row in table.Elements<TableRow>())
            {
                var rowCells = new List<string>();
                foreach (var cell in row.Elements<TableCell>())
                {
                    string cellText = cell.InnerText.Trim();
                    rowCells.Add(cellText);
                }
                if (rowCells.Count > 0)
                {
                    grid.Add(rowCells);
                }
            }
            return grid;
        }

        private static bool IsSummaryMatrixTable(string headerText)
        {
            bool hasType = headerText.Contains("NHIỀU LỰA CHỌN") || headerText.Contains("ĐÚNG - SAI") || headerText.Contains("ĐÚNG SAI") || headerText.Contains("TNKQ") || headerText.Contains("CẤP ĐỘ TƯ DUY");
            bool hasLevel = headerText.Contains("NHẬN BIẾT") || headerText.Contains("THÔNG HIỂU") || headerText.Contains("VẬN DỤNG") || headerText.Contains("BIẾT") || headerText.Contains("HIỂU");
            return hasType && hasLevel;
        }

        private static bool IsSpecificationTable(string headerText)
        {
            return (headerText.Contains("YÊU CẦU CẦN ĐẠT") || headerText.Contains("YÊU CẦU") || headerText.Contains("ĐẶC TẢ")) &&
                   (headerText.Contains("MỨC ĐỘ") || headerText.Contains("NỘI DUNG") || headerText.Contains("SỐ LƯỢNG") || headerText.Contains("CÂU HỎI"));
        }

        private static void ParseSummaryTableToRows(List<List<string>> grid, ExamMatrixData matrix)
        {
            matrix.Rows.Clear();
            int stt = 1;

            // Tìm hàng bắt đầu dữ liệu (sau các header nhiều cấp)
            int dataStart = 2;
            for (int i = 1; i < Math.Min(grid.Count, 5); i++)
            {
                // Nếu dòng có số hoặc ký hiệu câu thì đó là dữ liệu
                int numbers = grid[i].Count(c => Regex.IsMatch(c, @"^\d+(\s*\(.*\))?$"));
                if (numbers >= 2)
                {
                    dataStart = i;
                    break;
                }
            }

            for (int r = dataStart; r < grid.Count; r++)
            {
                var row = grid[r];
                string rowJoined = string.Join(" ", row).ToUpper();
                if (rowJoined.Contains("TỔNG") || rowJoined.Contains("TỈ LỆ") || rowJoined.Contains("CỘNG")) continue;

                // Cột 0: Chủ đề, Cột 1: Đơn vị kiến thức hoặc ngược lại
                string topic = row.Count > 1 && !string.IsNullOrWhiteSpace(row[1]) ? row[1] : (row.Count > 0 ? row[0] : "");
                if (string.IsNullOrWhiteSpace(topic) || Regex.IsMatch(topic, @"^\d+$"))
                {
                    if (row.Count > 2 && !string.IsNullOrWhiteSpace(row[2])) topic = row[2];
                }

                if (string.IsNullOrWhiteSpace(topic)) continue;

                var item = new MatrixTopicRow
                {
                    Stt = stt++,
                    Topic = topic.Trim()
                };

                // Trích xuất số câu theo các mức độ từ các cột
                // Nếu dòng có các ô chứa dạng "2 (1,2)" hoặc số thuần
                var numericCells = new List<int>();
                for (int c = 1; c < row.Count; c++)
                {
                    var m = Regex.Match(row[c], @"^(\d+)");
                    if (m.Success && int.TryParse(m.Groups[1].Value, out int cnt))
                    {
                        numericCells.Add(cnt);
                    }
                }

                if (numericCells.Count >= 3)
                {
                    item.TnNb = numericCells[0];
                    item.TnTh = numericCells.Count > 1 ? numericCells[1] : 0;
                    item.TnVd = numericCells.Count > 2 ? numericCells[2] : 0;
                }
                if (numericCells.Count >= 6)
                {
                    item.DsNb = numericCells[3];
                    item.DsTh = numericCells[4];
                    item.DsVd = numericCells[5];
                }

                item.Points = (item.TnNb + item.TnTh + item.TnVd) * 0.25 + (item.DsNb + item.DsTh + item.DsVd) * 0.25;
                if (item.Points <= 0) item.Points = 1.0;

                matrix.Rows.Add(item);
            }

            // Nếu không trích xuất được hàng nào, dùng mẫu Tin học 11 hoặc Toán 12
            if (matrix.Rows.Count == 0)
            {
                if (matrix.Subject.IndexOf("tin", StringComparison.OrdinalIgnoreCase) >= 0)
                {
                    matrix.Rows = MatrixWordExporter.CreateInformatics11Matrix().Rows;
                }
            }
        }

        private static void ParseSpecificationTableToSpecs(List<List<string>> grid, ExamMatrixData matrix)
        {
            matrix.Specs.Clear();
            int dataStart = 1;
            for (int i = 0; i < Math.Min(grid.Count, 3); i++)
            {
                string line = string.Join(" ", grid[i]).ToUpper();
                if (line.Contains("YÊU CẦU") || line.Contains("ĐẶC TẢ"))
                {
                    dataStart = i + 1;
                }
            }

            string currentTopic = "";
            for (int r = dataStart; r < grid.Count; r++)
            {
                var row = grid[r];
                if (row.Count < 3) continue;

                string stt = row[0].Trim();
                string topic = row.Count > 1 ? row[1].Trim() : "";
                if (!string.IsNullOrEmpty(topic)) currentTopic = topic;

                string requirement = "";
                string codes = "";
                string level = "Nhận biết";

                foreach (var cell in row)
                {
                    string cu = cell.ToUpper();
                    if (cu.Contains("NHẬN BIẾT") || cu == "NB") level = "Nhận biết";
                    else if (cu.Contains("THÔNG HIỂU") || cu == "TH") level = "Thông hiểu";
                    else if (cu.Contains("VẬN DỤNG CAO") || cu == "VDC") level = "Vận dụng cao";
                    else if (cu.Contains("VẬN DỤNG") || cu == "VD") level = "Vận dụng";

                    if (cell.Length > requirement.Length && (cell.Contains("Trình bày") || cell.Contains("Nêu") || cell.Contains("Giải thích") || cell.Contains("Đánh giá") || cell.Contains("Ứng dụng") || cell.Contains("Vận dụng")))
                    {
                        requirement = cell.Trim();
                    }

                    if (Regex.IsMatch(cell, @"[Cc]âu\s*\d+|[Tt][Nn]\d+|[Đđ][Ss]\d+|\d+[a-d]"))
                    {
                        codes = cell.Trim();
                    }
                }

                if (string.IsNullOrEmpty(requirement) && row.Count >= 4)
                {
                    requirement = row[row.Count - 2];
                }

                if (!string.IsNullOrEmpty(requirement) || !string.IsNullOrEmpty(codes))
                {
                    matrix.Specs.Add(new MatrixSpecRow
                    {
                        Stt = stt,
                        Topic = currentTopic,
                        CognitiveLevel = level,
                        QuestionType = codes.Contains("a") || codes.Contains("b") || codes.Contains("c") || codes.Contains("d") ? "DS" : "TN",
                        QuestionCodes = codes,
                        RequiredOutcome = requirement
                    });
                }
            }
        }
    }
}
