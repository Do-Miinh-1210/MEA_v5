using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.RegularExpressions;
using System.Threading.Tasks;
using DocumentFormat.OpenXml.Packaging;
using DocumentFormat.OpenXml.Wordprocessing;
using DW = DocumentFormat.OpenXml.Drawing.Wordprocessing;
using FluentAssertions;
using MatrixExamAI.Desktop.Services;
using MatrixExamAI.Shared.Extensibility;
using Microsoft.Data.Sqlite;
using Xunit;
using ImageHelper = MatrixExamAI.Desktop.Services.ImageHelper;

namespace MatrixExamAI.Desktop.Tests
{
    public class Milestone1Requirement1WordAndImageTests : IDisposable
    {
        private readonly string _tempDir;
        private readonly string _dummyPngPath;
        private readonly byte[] _dummyPngBytes;

        public Milestone1Requirement1WordAndImageTests()
        {
            _tempDir = Path.Combine(Path.GetTempPath(), "MEA_M1R1_Tests_" + Guid.NewGuid().ToString("N"));
            Directory.CreateDirectory(_tempDir);

            // Tạo file ảnh PNG 100x100 hợp lệ tối thiểu
            _dummyPngBytes = CreateDummyPngBytes(100, 100);
            _dummyPngPath = Path.Combine(_tempDir, "test_diagram.png");
            File.WriteAllBytes(_dummyPngPath, _dummyPngBytes);
        }

        public void Dispose()
        {
            try
            {
                if (Directory.Exists(_tempDir))
                {
                    Directory.Delete(_tempDir, true);
                }
            }
            catch
            {
                // Best effort cleanup
            }
        }

        private static byte[] CreateDummyPngBytes(int width, int height)
        {
            // Standard minimal 1x1 PNG or header-valid PNG
            byte[] pngHeader = new byte[] {
                0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A, // PNG signature
                0x00, 0x00, 0x00, 0x0D, // IHDR chunk length 13
                0x49, 0x48, 0x44, 0x52, // "IHDR"
                (byte)((width >> 24) & 0xFF), (byte)((width >> 16) & 0xFF), (byte)((width >> 8) & 0xFF), (byte)(width & 0xFF),
                (byte)((height >> 24) & 0xFF), (byte)((height >> 16) & 0xFF), (byte)((height >> 8) & 0xFF), (byte)(height & 0xFF),
                0x08, 0x06, 0x00, 0x00, 0x00, // 8-bit depth, RGBA, deflate, no filter, no interlace
                0x00, 0x00, 0x00, 0x00, // CRC placeholder
                0x00, 0x00, 0x00, 0x00, // IEND chunk length 0
                0x49, 0x45, 0x4E, 0x44, // "IEND"
                0xAE, 0x42, 0x60, 0x82  // IEND CRC
            };
            return pngHeader;
        }

        #region 1. ImageHelper Core Tests

        [Fact]
        public void ImageHelper_GetImagesDirectory_ShouldReturnValidExistingDirectory()
        {
            string dir = ImageHelper.GetImagesDirectory();
            dir.Should().NotBeNullOrWhiteSpace();
            Directory.Exists(dir).Should().BeTrue();
            dir.Should().Contain("question_images");
        }

        [Fact]
        public void ImageHelper_SaveImageBytes_ShouldCreateUniqueFileInImagesDirectory()
        {
            string savedPath = ImageHelper.SaveImageBytes(_dummyPngBytes, ".png");
            try
            {
                File.Exists(savedPath).Should().BeTrue();
                Path.GetDirectoryName(savedPath)!.Should().Be(ImageHelper.GetImagesDirectory());
                new FileInfo(savedPath).Length.Should().Be(_dummyPngBytes.Length);
            }
            finally
            {
                ImageHelper.DeleteOrphanImage(savedPath);
            }
        }

        [Fact]
        public void ImageHelper_CopyToImagesDir_ShouldCopyFileAndReturnNewPath()
        {
            string? copied = ImageHelper.CopyToImagesDir(_dummyPngPath);
            try
            {
                copied.Should().NotBeNull();
                File.Exists(copied).Should().BeTrue();
                Path.GetDirectoryName(copied)!.Should().Be(ImageHelper.GetImagesDirectory());
            }
            finally
            {
                if (copied != null) ImageHelper.DeleteOrphanImage(copied);
            }
        }

        [Fact]
        public void ImageHelper_NormalizeImageField_ShouldSupportAllFormats()
        {
            // Null & empty
            ImageHelper.NormalizeImageField(null).Should().BeEmpty();
            ImageHelper.NormalizeImageField("").Should().BeEmpty();
            ImageHelper.NormalizeImageField("   ").Should().BeEmpty();

            // Single path
            var single = ImageHelper.NormalizeImageField("C:\\test\\img1.png");
            single.Should().ContainSingle().Which.Should().Be("C:\\test\\img1.png");

            // Pipe-separated
            var piped = ImageHelper.NormalizeImageField("img1.png|img2.png|img3.png");
            piped.Should().HaveCount(3);
            piped.Should().ContainInOrder("img1.png", "img2.png", "img3.png");

            // JSON array string
            var jsonArr = ImageHelper.NormalizeImageField("[\"foo.png\", \"bar.png\"]");
            jsonArr.Should().HaveCount(2);
            jsonArr.Should().ContainInOrder("foo.png", "bar.png");

            // List of strings
            var listInput = new List<string> { "a.png", "b.png" };
            ImageHelper.NormalizeImageField(listInput).Should().Equal(listInput);
        }

        [Fact]
        public void ImageHelper_SerializeImageField_ShouldJoinWithPipe()
        {
            ImageHelper.SerializeImageField(null).Should().BeEmpty();
            ImageHelper.SerializeImageField(new List<string>()).Should().BeEmpty();
            ImageHelper.SerializeImageField(new List<string> { "img1.png", "img2.png" })
                .Should().Be("img1.png|img2.png");
        }

        #endregion

        #region 2. SQLite QuestionBank Images Persistence Tests

        [Fact]
        public async Task QuestionBankService_InsertAndGetQuestion_ShouldPersistImagesListProperly()
        {
            string dbPath = Path.Combine(_tempDir, $"qb_test_{Guid.NewGuid():N}.db");
            var qbService = new QuestionBankService($"Data Source={dbPath};");
            await qbService.InitializeDatabaseAsync();

            var question = new QuestionItem
            {
                QuestionCode = "TOAN_IMG_001",
                Subject = "Toán",
                Grade = 12,
                Topic = "Khảo sát hàm số",
                CognitiveLevel = "Vận dụng",
                QuestionType = "MultipleChoice4",
                Content = "Cho hàm số có đồ thị như hình vẽ bên.",
                Options = new Dictionary<string, string>
                {
                    ["A"] = "$y = 1$",
                    ["B"] = "$y = 2$",
                    ["C"] = "$y = 3$",
                    ["D"] = "$y = 4$"
                },
                CorrectAnswer = "A",
                Images = new List<string> { _dummyPngPath, "C:\\mock\\diagram2.png" }
            };

            // Act: Insert
            long id = await qbService.InsertQuestionAsync(question);
            id.Should().BeGreaterThan(0);

            // Act: Retrieve by Id
            var retrieved = await qbService.GetQuestionByIdAsync(id);
            retrieved.Should().NotBeNull();
            retrieved!.Images.Should().HaveCount(2);
            retrieved.Images[0].Should().Be(_dummyPngPath);
            retrieved.Images[1].Should().Be("C:\\mock\\diagram2.png");

            // Act: Update images
            retrieved.Images.Add("C:\\mock\\diagram3.png");
            bool updated = await qbService.UpdateQuestionAsync(retrieved);
            updated.Should().BeTrue();

            var retrieved2 = await qbService.GetQuestionByIdAsync(id);
            retrieved2!.Images.Should().HaveCount(3);
            retrieved2.Images.Should().Contain("C:\\mock\\diagram3.png");
        }

        #endregion

        #region 3. WordExportService Standard Tab Stops & Formatting Tests

        [Fact]
        public void ExportExamToDocx_Standard35TabStops_ShouldGenerate1985_3969_5953Twips()
        {
            var exporter = new WordExportService();
            var questions = new List<QuestionItem>
            {
                new QuestionItem
                {
                    Subject = "Toán",
                    Grade = 12,
                    QuestionType = "MultipleChoice4",
                    Content = "Nghiệm của phương trình $2^x = 4$ là:",
                    Options = new Dictionary<string, string>
                    {
                        { "A", "$x = 1$" },
                        { "B", "$x = 2$" },
                        { "C", "$x = 3$" },
                        { "D", "$x = 4$" }
                    },
                    CorrectAnswer = "B"
                }
            };

            var options = new ExamExportOptions
            {
                Subject = "Toán",
                Grade = "12",
                TabSpacing = TabSpacingMode.Standard35
            };

            string docxPath = Path.Combine(_tempDir, $"Test_Standard35_{Guid.NewGuid():N}.docx");
            try
            {
                exporter.ExportExamToDocx(docxPath, questions, options);
                File.Exists(docxPath).Should().BeTrue();

                using var doc = WordprocessingDocument.Open(docxPath, false);
                var body = doc.MainDocumentPart!.Document.Body!;

                // 1. Kiểm tra không có bảng cho phương án trắc nghiệm
                var optionPara = body.Elements<Paragraph>().FirstOrDefault(p => p.InnerText.Contains("A.") && p.InnerText.Contains("B."));
                optionPara.Should().NotBeNull();

                var tabs = optionPara!.ParagraphProperties?.Tabs?.Elements<TabStop>().ToList();
                tabs.Should().NotBeNull();
                tabs!.Count.Should().Be(3);

                // Tab stops chuẩn 3.5cm (1985), 7.0cm (3969), 10.5cm (5953) twips
                tabs[0].Position!.Value.Should().Be(1985);
                tabs[1].Position!.Value.Should().Be(3969);
                tabs[2].Position!.Value.Should().Be(5953);

                // 2. Line spacing 1.15 (line 276 dxa)
                var spacing = optionPara.ParagraphProperties?.SpacingBetweenLines;
                spacing.Should().NotBeNull();
                spacing!.Line!.Value.Should().Be("276");

                // 3. Tiêu đề đề thi phẳng (zero borders val="none")
                var headerTable = body.Elements<Table>().FirstOrDefault();
                headerTable.Should().NotBeNull();
                var tblPr = headerTable!.GetFirstChild<TableProperties>();
                tblPr.Should().NotBeNull();
                var borders = tblPr!.TableBorders;
                borders.Should().NotBeNull();
                borders!.TopBorder?.Val?.Value.Should().Be(BorderValues.None);
                borders.BottomBorder?.Val?.Value.Should().Be(BorderValues.None);
                borders.LeftBorder?.Val?.Value.Should().Be(BorderValues.None);
                borders.RightBorder?.Val?.Value.Should().Be(BorderValues.None);
            }
            finally
            {
                if (File.Exists(docxPath)) File.Delete(docxPath);
            }
        }

        [Fact]
        public void ExportExamToDocx_MultipleImages_ShouldHaveUniqueIncrementingDrawingIds()
        {
            var exporter = new WordExportService();
            var questions = new List<QuestionItem>
            {
                new QuestionItem
                {
                    Subject = "Toán",
                    Grade = 12,
                    QuestionType = "MultipleChoice4",
                    Content = "Câu hỏi có 2 hình vẽ:",
                    Options = new Dictionary<string, string> { ["A"] = "1", ["B"] = "2", ["C"] = "3", ["D"] = "4" },
                    Images = new List<string> { _dummyPngPath, _dummyPngPath }
                }
            };

            string docxPath = Path.Combine(_tempDir, $"Test_UniqueIds_{Guid.NewGuid():N}.docx");
            try
            {
                exporter.ExportExamToDocx(docxPath, questions, new ExamExportOptions());

                using var doc = WordprocessingDocument.Open(docxPath, false);
                var body = doc.MainDocumentPart!.Document.Body!;

                var docProperties = body.Descendants<DW.DocProperties>().ToList();
                docProperties.Count.Should().BeGreaterThanOrEqualTo(2);

                var ids = docProperties.Select(dp => dp.Id!.Value).ToList();
                ids.Distinct().Count().Should().Be(ids.Count, "Mỗi DocProperties.Id trong OpenXML Drawing phải là duy nhất, không được trùng lặp");
            }
            finally
            {
                if (File.Exists(docxPath)) File.Delete(docxPath);
            }
        }

        #endregion

        #region 4. WordExportService Marker Scanning & Image Embedding Tests

        [Fact]
        public void ExportToDocx_MarkerScanner_ShouldEmbedReferencedImageAndRemoveMarkerText()
        {
            var exporter = new WordExportService();
            string content = $@"Câu 1. Cho hàm số có đồ thị như hình vẽ:
[HÌNH 1: {_dummyPngPath}]
Mệnh đề nào sau đây đúng?
A. Hàm số đồng biến.	B. Hàm số nghịch biến.	C. Đạt cực đại.	D. Đạt cực tiểu.";

            string docxPath = Path.Combine(_tempDir, $"Test_MarkerEmbed_{Guid.NewGuid():N}.docx");
            try
            {
                exporter.ExportToDocx(docxPath, content, new WordExportOptions());
                File.Exists(docxPath).Should().BeTrue();

                using var doc = WordprocessingDocument.Open(docxPath, false);
                var body = doc.MainDocumentPart!.Document.Body!;

                // 1. Kiểm tra hình ảnh đã được nhúng vào Word
                var drawings = body.Descendants<Drawing>().ToList();
                drawings.Should().NotBeEmpty("Ảnh từ marker [HÌNH 1: path] phải được nhúng vào Word document");

                // 2. Kiểm tra text marker [HÌNH 1: ...] đã được loại bỏ hoàn toàn khỏi văn bản
                string fullText = string.Join("\n", body.Descendants<Text>().Select(t => t.Text));
                fullText.Should().NotContain("[HÌNH 1");
                fullText.Should().NotContain(_dummyPngPath);
            }
            finally
            {
                if (File.Exists(docxPath)) File.Delete(docxPath);
            }
        }

        [Fact]
        public void ExportToDocx_AllMarkerAliases_HinhAnh_Image_Anh_ShouldEmbedSuccessfully()
        {
            var exporter = new WordExportService();
            string content = $@"Câu 1. [HINH_ANH: {_dummyPngPath}]
Câu 2. [IMAGE: {_dummyPngPath}]
Câu 3. [ANH: {_dummyPngPath}]";

            string docxPath = Path.Combine(_tempDir, $"Test_Aliases_{Guid.NewGuid():N}.docx");
            try
            {
                exporter.ExportToDocx(docxPath, content, new WordExportOptions());

                using var doc = WordprocessingDocument.Open(docxPath, false);
                var body = doc.MainDocumentPart!.Document.Body!;

                var drawings = body.Descendants<Drawing>().ToList();
                drawings.Count.Should().Be(3, "Cả 3 loại marker [HINH_ANH], [IMAGE], [ANH] đều phải được nhúng thành công");

                string fullText = string.Join("\n", body.Descendants<Text>().Select(t => t.Text));
                fullText.Should().NotContain("[HINH_ANH");
                fullText.Should().NotContain("[IMAGE");
                fullText.Should().NotContain("[ANH");
            }
            finally
            {
                if (File.Exists(docxPath)) File.Delete(docxPath);
            }
        }

        [Fact]
        public void ExportToDocx_MarkerWithIndexOnly_ShouldResolveFromExtractedImagesList()
        {
            var exporter = new WordExportService();
            string content = @"Câu 1. Cho hình vẽ:
[HÌNH 1]
Hỏi diện tích hình phẳng bằng bao nhiêu?";

            var options = new WordExportOptions
            {
                ExtractedImages = new List<string> { _dummyPngPath }
            };

            string docxPath = Path.Combine(_tempDir, $"Test_IndexOnly_{Guid.NewGuid():N}.docx");
            try
            {
                exporter.ExportToDocx(docxPath, content, options);

                using var doc = WordprocessingDocument.Open(docxPath, false);
                var body = doc.MainDocumentPart!.Document.Body!;

                var drawings = body.Descendants<Drawing>().ToList();
                drawings.Should().NotBeEmpty("Marker [HÌNH 1] không có path phải phân giải được từ ExtractedImages");

                string fullText = string.Join("\n", body.Descendants<Text>().Select(t => t.Text));
                fullText.Should().NotContain("[HÌNH 1]");
            }
            finally
            {
                if (File.Exists(docxPath)) File.Delete(docxPath);
            }
        }

        #endregion

        #region 5. PdfExtractionService Tests

        [Fact]
        public async Task PdfExtractionService_NonExistentFile_ShouldThrowFileNotFoundException()
        {
            var pdfService = new PdfExtractionService();
            var act = async () => await pdfService.ExtractTextAsync("non_existent_file.pdf");
            await act.Should().ThrowAsync<FileNotFoundException>();
        }

        [Fact]
        public void PdfExtractionService_ExtractedImageInfo_ModelIntegrity()
        {
            var info = new ExtractedImageInfo
            {
                ImagePath = _dummyPngPath,
                Index = 1,
                PageNumber = 1,
                X = 100,
                Y = 200,
                Width = 150,
                Height = 120
            };
            info.ImagePath.Should().Be(_dummyPngPath);
            info.Index.Should().Be(1);

            var res = new PdfExtractionResult
            {
                Text = "Test text",
                Images = new List<ExtractedImageInfo> { info }
            };
            res.ImagePaths.Should().ContainSingle().Which.Should().Be(_dummyPngPath);
        }

        #endregion
    }
}
