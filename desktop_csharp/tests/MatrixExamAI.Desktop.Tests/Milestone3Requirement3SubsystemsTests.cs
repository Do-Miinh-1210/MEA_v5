using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using System.Threading.Tasks;
using DocumentFormat.OpenXml.Packaging;
using DocumentFormat.OpenXml.Wordprocessing;
using FluentAssertions;
using MatrixExamAI.Desktop.Services;
using MatrixExamAI.Desktop.Views;
using MatrixExamAI.Shared.Extensibility;
using Microsoft.Data.Sqlite;
using Xunit;

namespace MatrixExamAI.Desktop.Tests
{
    /// <summary>
    /// Bộ kiểm thử Milestone 3 — Yêu cầu R3 (Core Subsystems Completion):
    /// 1. ExamMatrixView & MatrixWordExporter: Ma trận 4 mức độ nhận thức BGD 2025, xuất Bảng 1 (19 cột Landscape A4) & Bảng 2 (6 cột) chuẩn OpenXML.
    /// 2. ShuffleView & OmrSheetGenerator: Trộn hoán vị câu hỏi/phương án, khóa đáp án đặc thù, bảng ma trận đối chiếu, xuất file Word và sinh ảnh phiếu OMR.
    /// 3. QuestionBankView & SqliteSchemaAdapter: Kết nối SQLite thật, adapter tương thích schema Python/C#, tìm kiếm và lọc đa tiêu chí.
    /// 4. QcView & QcInspectionService: Thẩm định chất lượng đề thi tự động và công cụ AI Auto-Fix sửa lỗi cú pháp, định dạng.
    /// </summary>
    public class Milestone3Requirement3SubsystemsTests : IDisposable
    {
        private readonly List<string> _tempFilesToClean = new List<string>();

        public void Dispose()
        {
            foreach (var file in _tempFilesToClean)
            {
                try
                {
                    if (File.Exists(file)) File.Delete(file);
                }
                catch
                {
                    // Best effort cleanup
                }
            }
        }

        private string GetTempPath(string extension)
        {
            string path = Path.Combine(Path.GetTempPath(), $"MEA_M3R3_Test_{Guid.NewGuid():N}{extension}");
            _tempFilesToClean.Add(path);
            return path;
        }

        #region 1. ExamMatrixView & MatrixWordExporter Tests

        [Fact]
        public void MatrixWordExporter_CreateStandardHighSchoolMatrix_ShouldContain4CognitiveLevels()
        {
            // Act
            var matrix = MatrixWordExporter.CreateStandardHighSchoolMatrix("TOÁN HỌC", "12");

            // Assert
            matrix.Should().NotBeNull();
            matrix.Subject.Should().Be("TOÁN HỌC");
            matrix.Grade.Should().Be("12");
            matrix.DurationMinutes.Should().Be(90);
            matrix.TotalPoints.Should().Be(10.0);
            matrix.Rows.Should().NotBeEmpty();

            // Kiểm tra 4 mức độ nhận thức xuất hiện trong bảng đặc tả (NB, TH, VD, VDC)
            var levels = matrix.Specs.Select(s => s.CognitiveLevel).Distinct().ToList();
            levels.Should().Contain("Nhận biết");
            levels.Should().Contain("Thông hiểu");
            levels.Should().Contain("Vận dụng");
            levels.Should().Contain("Vận dụng cao");
        }

        [Fact]
        public void MatrixWordExporter_ExportMatrixDocx_ShouldGenerateValidLandscapeDocxPackageWith19ColsAnd6Cols()
        {
            // Arrange
            string docxPath = GetTempPath(".docx");
            var matrix = MatrixWordExporter.CreateStandardHighSchoolMatrix("TOÁN HỌC", "12");
            string examContent = @"% Câu 1 [Nhận biết]_[Hàm số]
Cho hàm số $y = x^3 - 3x$. Tìm khoảng đồng biến.
A. $(-\infty; -1)$.
B. $(-1; 1)$.
C. $(1; 2)$.
D. $(-2; 2)$.
Đáp án: A";

            // Act: Xuất file Word
            MatrixWordExporter.ExportMatrixDocx(docxPath, matrix, examContent);

            // Assert: File tồn tại và có kích thước hợp lệ
            File.Exists(docxPath).Should().BeTrue();
            new FileInfo(docxPath).Length.Should().BeGreaterThan(5000, "Tệp Word OpenXML hợp lệ phải chứa đủ các phần XML nén");

            // Kiểm tra cấu trúc OpenXML bằng WordprocessingDocument chính thức
            using (var doc = WordprocessingDocument.Open(docxPath, false))
            {
                var body = doc.MainDocumentPart?.Document?.Body;
                body.Should().NotBeNull();

                // 1. Kiểm tra thiết lập trang A4 Landscape (Ngang 29.7cm x 21.0cm)
                var sectPr = body!.Elements<SectionProperties>().LastOrDefault();
                sectPr.Should().NotBeNull();
                var pageSize = sectPr!.GetFirstChild<PageSize>();
                pageSize.Should().NotBeNull();
                pageSize!.Orient?.Value.Should().Be(PageOrientationValues.Landscape);
                pageSize.Width?.Value.Should().Be(16838U);  // 29.7cm trong dxa
                pageSize.Height?.Value.Should().Be(11906U); // 21.0cm trong dxa

                // 2. Kiểm tra có đủ 2 bảng: Bảng 1 (Ma trận 19 cột) và Bảng 2 (Bản đặc tả 6 cột)
                var tables = body.Elements<Table>().ToList();
                tables.Count.Should().BeGreaterThanOrEqualTo(2, "Tài liệu phải chứa ít nhất 2 bảng: Bảng ma trận và Bảng đặc tả");

                // Bảng 1: 19 cột grid
                var table1 = tables[0];
                var grid1 = table1.GetFirstChild<TableGrid>();
                grid1.Should().NotBeNull();
                grid1!.Elements<GridColumn>().Count().Should().Be(19, "Bảng 1 (Ma trận) phải có đúng 19 cột theo chuẩn Công văn 7991/BGDĐT");

                // Bảng 2: 6 cột grid
                var table2 = tables[1];
                var grid2 = table2.GetFirstChild<TableGrid>();
                grid2.Should().NotBeNull();
                grid2!.Elements<GridColumn>().Count().Should().Be(6, "Bảng 2 (Bản đặc tả) phải có đúng 6 cột theo chuẩn Bộ GD&ĐT");

                // 3. Kiểm tra nội dung đề thi được nhúng kèm vào tài liệu
                string fullDocText = body.InnerText;
                fullDocText.Should().Contain("BẢNG 1: MA TRẬN ĐỀ KIỂM TRA");
                fullDocText.Should().Contain("BẢNG 2: BẢN ĐẶC TẢ ĐỀ KIỂM TRA");
                fullDocText.Should().Contain("Cho hàm số $y = x^3 - 3x$");
                fullDocText.Should().Contain("Đáp án: A");
            }
        }

        #endregion

        #region 2. ShuffleView & OmrSheetGenerator Tests

        [Fact]
        public void OmrSheetGenerator_GenerateOmrSheetPng_ShouldProduceValidPngWith4CornerMarkers()
        {
            // Act: Sinh ảnh phiếu OMR PNG
            byte[] pngBytes = OmrSheetGenerator.GenerateOmrSheetPng(numQuestions: 40, hasEssay: true, examTitle: "PHIẾU TRẢ LỜI TRẮC NGHIỆM");

            // Assert
            pngBytes.Should().NotBeNull();
            pngBytes.Length.Should().BeGreaterThan(10000, "Ảnh phiếu OMR 150 DPI phải có dung lượng tối thiểu > 10KB");

            // Kiểm tra PNG magic bytes header: 89 50 4E 47 0D 0A 1A 0A
            byte[] pngMagic = { 0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A };
            pngBytes.Take(8).Should().Equal(pngMagic, "Định dạng ảnh xuất ra phải là PNG hợp lệ");

            // Kiểm tra metadata tọa độ các ô tròn
            var meta = OmrSheetGenerator.GetLayoutMetadata(40, true);
            meta.Width.Should().Be(1240);
            meta.Height.Should().Be(1754);
            meta.CornerMarkers.Should().HaveCount(4, "Phiếu OMR phải có 4 mốc định vị góc để camera nắn phối cảnh");
            meta.CodeBubbles.Should().HaveCount(3, "Phiếu OMR phải có 3 cột tô mã đề thi");
            meta.QuestionBubbles.Should().HaveCount(40, "Phiếu OMR phải có đủ tọa độ bong bóng cho 40 câu hỏi");
            meta.QuestionBubbles[1].Should().ContainKeys("A", "B", "C", "D");
        }

        [Fact]
        public void OmrSheetGenerator_SaveOmrSheet_ShouldWriteFileToDisk()
        {
            // Arrange
            string filePath = GetTempPath(".png");

            // Act
            string savedPath = OmrSheetGenerator.SaveOmrSheet(filePath, numQuestions: 22, hasEssay: false);

            // Assert
            File.Exists(savedPath).Should().BeTrue();
            new FileInfo(savedPath).Length.Should().BeGreaterThan(5000);
        }

        [Fact]
        public async Task QuestionBankService_MixExamVariantsAsync_ShouldPermuteOptionsAndTrackCorrectAnswers()
        {
            // Arrange
            var qbService = new QuestionBankService($"Data Source={GetTempPath(".db")};");
            var draft = new ExamDraftResult { Success = true };

            draft.Part1Questions.Add(new QuestionItem
            {
                QuestionCode = "Q01",
                Content = "Câu hỏi 1",
                Options = new Dictionary<string, string>
                {
                    ["A"] = "Phương án 1",
                    ["B"] = "Phương án 2 (Đúng)",
                    ["C"] = "Phương án 3",
                    ["D"] = "Phương án 4"
                },
                CorrectAnswer = "B"
            });

            // Act: Trộn 4 mã đề
            var variants = await qbService.MixExamVariantsAsync(draft, variantCount: 4);

            // Assert
            variants.Should().HaveCount(4);
            variants.Select(v => v.ExamCode).Should().Equal("101", "102", "103", "104");

            foreach (var variant in variants)
            {
                variant.Part1Questions.Should().HaveCount(1);
                var mixedQ = variant.Part1Questions[0];

                // Đáp án đúng mới phải trỏ chính xác về nội dung "Phương án 2 (Đúng)"
                string newCorrectKey = mixedQ.CorrectAnswer;
                mixedQ.Options.Should().ContainKey(newCorrectKey);
                mixedQ.Options[newCorrectKey].Should().Be("Phương án 2 (Đúng)", "Thuật toán hoán vị phải bảo toàn chính xác đáp án đúng");

                // AnswerKey trong variant phải khớp
                variant.AnswerKey[1].Should().Be(newCorrectKey);
            }
        }

        #endregion

        #region 3. QuestionBankView & SqliteSchemaAdapter Tests

        [Fact]
        public void SqliteSchemaAdapter_MappingFunctions_ShouldConvertBothWaysAccurately()
        {
            // 1. Mức độ nhận thức Python -> Tiếng Việt
            SqliteSchemaAdapter.MapPythonLevelToVietnamese("NB").Should().Be("Nhận biết");
            SqliteSchemaAdapter.MapPythonLevelToVietnamese("TH").Should().Be("Thông hiểu");
            SqliteSchemaAdapter.MapPythonLevelToVietnamese("VD").Should().Be("Vận dụng");
            SqliteSchemaAdapter.MapPythonLevelToVietnamese("VDC").Should().Be("Vận dụng cao");
            SqliteSchemaAdapter.MapPythonLevelToVietnamese("Nhận biết").Should().Be("Nhận biết");

            // 2. Tiếng Việt -> Python
            SqliteSchemaAdapter.MapVietnameseLevelToPython("Nhận biết").Should().Be("NB");
            SqliteSchemaAdapter.MapVietnameseLevelToPython("Thông hiểu").Should().Be("TH");
            SqliteSchemaAdapter.MapVietnameseLevelToPython("Vận dụng").Should().Be("VD");
            SqliteSchemaAdapter.MapVietnameseLevelToPython("Vận dụng cao").Should().Be("VDC");

            // 3. Dạng câu hỏi Python -> C#
            SqliteSchemaAdapter.MapPythonQtypeToCSharp("TN").Should().Be("MultipleChoice4");
            SqliteSchemaAdapter.MapPythonQtypeToCSharp("DS").Should().Be("TrueFalse4");
            SqliteSchemaAdapter.MapPythonQtypeToCSharp("TLN").Should().Be("ShortAnswer");
            SqliteSchemaAdapter.MapPythonQtypeToCSharp("TL").Should().Be("Essay");

            // 4. C# -> Python
            SqliteSchemaAdapter.MapCSharpQtypeToPython("MultipleChoice4").Should().Be("TN");
            SqliteSchemaAdapter.MapCSharpQtypeToPython("TrueFalse4").Should().Be("DS");
            SqliteSchemaAdapter.MapCSharpQtypeToPython("ShortAnswer").Should().Be("TLN");
            SqliteSchemaAdapter.MapCSharpQtypeToPython("Essay").Should().Be("TL");
        }

        [Fact]
        public async Task SqliteSchemaAdapter_PythonSchemaCompatibility_ShouldReadPythonJsonAndColumns()
        {
            // Arrange: Tạo SQLite database mô phỏng schema gốc của Python (storage/database.py)
            string dbPath = GetTempPath(".db");
            string connStr = $"Data Source={dbPath};";

            using (var conn = new SqliteConnection(connStr))
            {
                await conn.OpenAsync();
                using var cmd = conn.CreateCommand();
                cmd.CommandText = @"
                    CREATE TABLE questions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        subject TEXT,
                        grade TEXT,
                        topic TEXT,
                        level TEXT,
                        qtype TEXT,
                        question TEXT,
                        data_json TEXT,
                        created_at TEXT,
                        source TEXT,
                        question_id TEXT
                    );
                ";
                await cmd.ExecuteNonQueryAsync();

                // Chèn câu hỏi mẫu định dạng Python
                var pyData = new
                {
                    qtype = "TN",
                    level = "NB",
                    topic = "Khảo sát hàm số",
                    question = "Cho hàm số y = f(x). Điểm cực đại là gì?",
                    solution = "Lời giải chi tiết từ Python",
                    options = new Dictionary<string, string>
                    {
                        ["A"] = "Điểm A(0; 1)",
                        ["B"] = "Điểm B(1; 2)",
                        ["C"] = "Điểm C(2; 3)",
                        ["D"] = "Điểm D(3; 4)"
                    },
                    answer = "B",
                    tikz_code = "\\begin{tikzpicture}\\draw (0,0) -- (1,1);\\end{tikzpicture}"
                };

                using var insertCmd = conn.CreateCommand();
                insertCmd.CommandText = @"
                    INSERT INTO questions (subject, grade, topic, level, qtype, question, data_json, created_at, source, question_id)
                    VALUES (@subj, @grd, @top, @lvl, @qt, @q, @dj, @cat, @src, @qid);
                ";
                insertCmd.Parameters.AddWithValue("@subj", "Toán");
                insertCmd.Parameters.AddWithValue("@grd", "12");
                insertCmd.Parameters.AddWithValue("@top", "Khảo sát hàm số");
                insertCmd.Parameters.AddWithValue("@lvl", "NB");
                insertCmd.Parameters.AddWithValue("@qt", "TN");
                insertCmd.Parameters.AddWithValue("@q", "Cho hàm số y = f(x). Điểm cực đại là gì?");
                insertCmd.Parameters.AddWithValue("@dj", JsonSerializer.Serialize(pyData));
                insertCmd.Parameters.AddWithValue("@cat", DateTime.Now.ToString("o"));
                insertCmd.Parameters.AddWithValue("@src", "Python MEA v5.0");
                insertCmd.Parameters.AddWithValue("@qid", "PY_Q001");
                await insertCmd.ExecuteNonQueryAsync();
            }

            // Act: Đọc database qua adapter
            var items = await SqliteSchemaAdapter.LoadQuestionsFromDatabaseAsync(connStr, keyword: "cực đại", levelFilter: "Nhận biết");

            // Assert
            items.Should().HaveCount(1);
            var item = items[0];
            item.QuestionCode.Should().Be("PY_Q001");
            item.Subject.Should().Be("Toán");
            item.Grade.Should().Be(12);
            item.CognitiveLevel.Should().Be("Nhận biết", "Level 'NB' của Python phải được map thành 'Nhận biết'");
            item.QuestionType.Should().Be("MultipleChoice4", "Qtype 'TN' phải được map thành 'MultipleChoice4'");
            item.Content.Should().Contain("Điểm cực đại là gì?");
            item.Options.Should().HaveCount(4);
            item.Options["B"].Should().Be("Điểm B(1; 2)");
            item.CorrectAnswer.Should().Be("B");
            item.Explanation.Should().Be("Lời giải chi tiết từ Python");
            item.TikzCode.Should().Contain("\\begin{tikzpicture}");
        }

        [Fact]
        public async Task SqliteSchemaAdapter_ImportQuestionsAsync_ShouldPersistNewQuestionsSuccessfully()
        {
            // Arrange
            string dbPath = GetTempPath(".db");
            string connStr = $"Data Source={dbPath};";

            var newQuestions = new List<QuestionItem>
            {
                new QuestionItem
                {
                    QuestionCode = "IMPORT_01",
                    Subject = "Toán",
                    Grade = 12,
                    Topic = "Nguyên hàm",
                    CognitiveLevel = "Thông hiểu",
                    QuestionType = "MultipleChoice4",
                    Content = "Tìm nguyên hàm của f(x) = e^x",
                    Options = new Dictionary<string, string> { ["A"] = "e^x + C", ["B"] = "e^x - C", ["C"] = "x e^x", ["D"] = "1" },
                    CorrectAnswer = "A"
                }
            };

            // Act: Import vào database
            int imported = await SqliteSchemaAdapter.ImportQuestionsAsync(newQuestions, connStr);

            // Assert
            imported.Should().Be(1);

            var retrieved = await SqliteSchemaAdapter.LoadQuestionsFromDatabaseAsync(connStr, keyword: "e^x");
            retrieved.Should().HaveCount(1);
            retrieved[0].QuestionCode.Should().Be("IMPORT_01");
            retrieved[0].Topic.Should().Be("Nguyên hàm");
            retrieved[0].CorrectAnswer.Should().Be("A");
        }

        [Fact]
        public async Task SqliteSchemaAdapter_DeleteAndClearQuestionsAsync_ShouldRemoveRecordsCorrectly()
        {
            // Arrange
            string dbPath = GetTempPath(".db");
            string connStr = $"Data Source={dbPath};";

            var items = new List<QuestionItem>
            {
                new QuestionItem { QuestionCode = "DEL_01", Content = "Câu hỏi xóa 1", CognitiveLevel = "NB" },
                new QuestionItem { QuestionCode = "DEL_02", Content = "Câu hỏi xóa 2", CognitiveLevel = "TH" },
                new QuestionItem { QuestionCode = "DEL_03", Content = "Câu hỏi xóa 3", CognitiveLevel = "VD" }
            };

            await SqliteSchemaAdapter.ImportQuestionsAsync(items, connStr);
            var loaded = await SqliteSchemaAdapter.LoadQuestionsFromDatabaseAsync(connStr);
            loaded.Should().HaveCount(3);

            // Act 1: Xóa 1 câu hỏi
            long targetId = loaded.First(x => x.QuestionCode == "DEL_01").Id;
            int deletedCount = await SqliteSchemaAdapter.DeleteQuestionsAsync(new[] { targetId }, connStr);
            deletedCount.Should().Be(1);

            var remaining = await SqliteSchemaAdapter.LoadQuestionsFromDatabaseAsync(connStr);
            remaining.Should().HaveCount(2);
            remaining.Should().NotContain(x => x.QuestionCode == "DEL_01");

            // Act 2: Xóa sạch toàn bộ ngân hàng
            int clearedCount = await SqliteSchemaAdapter.ClearAllQuestionsAsync(connStr);
            clearedCount.Should().Be(2);

            var afterClear = await SqliteSchemaAdapter.LoadQuestionsFromDatabaseAsync(connStr);
            afterClear.Should().BeEmpty();
        }

        #endregion

        #region 4. QcView & QcInspectionService Tests

        [Fact]
        public void QcInspectionService_DuplicateOptionsCheck_ShouldFlagDuplicateOptionTexts()
        {
            // Arrange
            var qcService = new QcInspectionService();
            var questions = new List<QuestionItem>
            {
                new QuestionItem
                {
                    QuestionCode = "QC_DUP_01",
                    QuestionType = "MultipleChoice4",
                    Content = "Phương trình $x^2 - 4 = 0$ có nghiệm là:",
                    Options = new Dictionary<string, string>
                    {
                        ["A"] = "$x = 2$",
                        ["B"] = "$x = -2$",
                        ["C"] = "$x = 2$", // Trùng với A!
                        ["D"] = "$x = 4$"
                    },
                    CorrectAnswer = "A"
                }
            };

            // Act
            var report = qcService.InspectQuestions(questions, checkDupOptions: true);

            // Assert
            report.IsPassed.Should().BeFalse("Đề thi có phương án trùng lặp phải bị đánh dấu không đạt");
            report.ErrorCount.Should().BeGreaterThanOrEqualTo(1);
            var issue = report.Issues.FirstOrDefault(i => i.RuleName.Contains("Trùng lặp"));
            issue.Should().NotBeNull();
            issue!.Severity.Should().Be(QcSeverity.Error);
            issue.Description.Should().Contain("A, C");
        }

        [Fact]
        public void QcInspectionService_MissingCorrectAnswerCheck_ShouldFlagEmptyAnswers()
        {
            // Arrange
            var qcService = new QcInspectionService();
            var questions = new List<QuestionItem>
            {
                new QuestionItem
                {
                    QuestionCode = "QC_NO_ANS",
                    QuestionType = "MultipleChoice4",
                    Content = "Câu hỏi quên gán đáp án đúng",
                    Options = new Dictionary<string, string>
                    {
                        ["A"] = "Phương án 1",
                        ["B"] = "Phương án 2",
                        ["C"] = "Phương án 3",
                        ["D"] = "Phương án 4"
                    },
                    CorrectAnswer = "" // Thiếu!
                }
            };

            // Act
            var report = qcService.InspectQuestions(questions, checkMissingAns: true);

            // Assert
            report.IsPassed.Should().BeFalse();
            var issue = report.Issues.FirstOrDefault(i => i.RuleName.Contains("Thiếu đáp án"));
            issue.Should().NotBeNull();
            issue!.Severity.Should().Be(QcSeverity.Error);
        }

        [Fact]
        public void QcInspectionService_UnbalancedLatexSyntax_ShouldDetectOddDollarCount()
        {
            // Arrange
            var qcService = new QcInspectionService();
            string brokenLatexText = @"% Câu 1 [Nhận biết]_[Hàm số]
Cho hàm số $y = f(x có cực trị tại $x = 1$.
A. 1.
B. 2.
C. 3.
D. 4.
Đáp án: A";

            // Act
            var report = qcService.InspectText(brokenLatexText, checkLatexSyntax: true);

            // Assert
            var issue = report.Issues.FirstOrDefault(i => i.RuleName.Contains("LaTeX") && i.RuleName.Contains("$"));
            issue.Should().NotBeNull();
            issue!.Severity.Should().Be(QcSeverity.Error);
        }

        [Fact]
        public void QcInspectionService_FormattingNonCompliance_ShouldFlagCitationsAndItemSpacing()
        {
            // Arrange
            var qcService = new QcInspectionService();
            string textWithFormattingIssues = @"% Câu 1 [Nhận biết]_[Hàm số]
Cho hàm số $y = f(x)$. [cite: 10]
\item1.Phương án bị dính số đầu dòng.
A. 1.
B. 2.
C. 3.
D. 4.
Đáp án: A";

            // Act
            var report = qcService.InspectText(textWithFormattingIssues, checkFormat: true);

            // Assert
            var citIssue = report.Issues.FirstOrDefault(i => i.RuleName.Contains("citation"));
            citIssue.Should().NotBeNull();
            citIssue!.Severity.Should().Be(QcSeverity.Warning);

            var itemIssue = report.Issues.FirstOrDefault(i => i.RuleName.Contains("\\item"));
            itemIssue.Should().NotBeNull();
            itemIssue!.Severity.Should().Be(QcSeverity.Warning);
        }

        [Fact]
        public void QcInspectionService_AutoFix_ShouldCleanCitationsAndFixItemSpacing()
        {
            // Arrange
            var qcService = new QcInspectionService();
            string rawText = @"% Câu 1 [Nhận biết]_[Hàm số]
Cho hàm số $y = f(x)$ có đạo hàm $f'(x) = 0$. [cite: 1]
\begin{aligned}
2x + y = 5 \\
x - y = 1
\end{aligned}
\item1.Phương án dính liền.
Đáp án: A";

            // Act
            var fixResult = qcService.AutoFix(rawText);

            // Assert
            fixResult.Should().NotBeNull();
            fixResult.FixesCount.Should().BeGreaterThanOrEqualTo(2);
            fixResult.FixedContent.Should().NotContain("[cite: 1]", "Auto-Fix phải loại bỏ citation rác từ AI");
            fixResult.FixedContent.Should().Contain(@"\item 1.", "Auto-Fix phải tách khoảng trắng giữa \\item và số");
            fixResult.FixedContent.Should().Contain(@"\begin{align}", "Auto-Fix phải chuẩn hóa aligned sang align");
            fixResult.AppliedFixes.Should().NotBeEmpty();
        }

        #endregion
    }
}
