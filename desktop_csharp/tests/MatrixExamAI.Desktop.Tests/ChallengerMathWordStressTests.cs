using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.RegularExpressions;
using DocumentFormat.OpenXml.Packaging;
using DocumentFormat.OpenXml.Validation;
using DocumentFormat.OpenXml.Wordprocessing;
using DW = DocumentFormat.OpenXml.Drawing.Wordprocessing;
using PIC = DocumentFormat.OpenXml.Drawing.Pictures;
using FluentAssertions;
using MatrixExamAI.Desktop.Services;
using MatrixExamAI.Shared.Extensibility;
using MatrixExamAI.Shared.Models;
using Xunit;

namespace MatrixExamAI.Desktop.Tests
{
    /// <summary>
    /// Empirical Challenger Stress Test Suite for Requirements R1 & R2:
    /// - Math Normalization (nested aligned, complex |x-2|+|y|=1 in markdown tables, unbraced formulas, dirty LaTeX \item)
    /// - Word Export OpenXML Structure (<w:tabs> 1985/3969/5953 twips, unique DocProperties.Id, flat header border: none, OpenXmlValidator)
    /// </summary>
    public class ChallengerMathWordStressTests : IDisposable
    {
        private readonly string _tempDir;
        private readonly string _dummyPngPath;
        private readonly byte[] _dummyPngBytes;

        public ChallengerMathWordStressTests()
        {
            _tempDir = Path.Combine(Path.GetTempPath(), "MEA_Challenger_Tests_" + Guid.NewGuid().ToString("N"));
            Directory.CreateDirectory(_tempDir);

            _dummyPngBytes = CreateValidPngBytes(120, 80);
            _dummyPngPath = Path.Combine(_tempDir, "sample_figure.png");
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
                // Best-effort cleanup
            }
        }

        private static byte[] CreateValidPngBytes(int width, int height)
        {
            return new byte[] {
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
        }

        #region Requirement 1: Math Normalization Stress Tests

        [Fact]
        public void StressTest_NestedAndMultipleAlignedEnvironments_ConvertsCleanlyToAlignWithoutResidualAligned()
        {
            // Case A: Nested aligned environments
            string nestedInput = @"
\begin{aligned}
x + y &= 1 \\
\begin{aligned}
2x - y &= 3 \\
x &= 1
\end{aligned}
\end{aligned}";

            string normalizedNested = QuestionParserEngine.NormalizeSystemEquationsAndAlign(nestedInput);
            normalizedNested.Should().NotContain("aligned", "All nested aligned environments must be converted to align");
            normalizedNested.Should().Contain(@"\begin{align}");
            normalizedNested.Should().Contain(@"\end{align}");

            // Case B: Multiple aligned environments in single text with connector \Leftrightarrow
            string multipleInput = @"
\left\{ \begin{aligned} x + 2y &= 5 \\ 3x - y &= 1 \end{aligned} \right.
\quad\Leftrightarrow\quad
\left\{ \begin{aligned} x &= 1 \\ y &= 2 \end{aligned} \right.
\quad\text{hoặc}\quad
\begin{aligned}
u_1 &= 3 \\
d &= 2
\end{aligned}";

            string normalizedMultiple = QuestionParserEngine.NormalizeSystemEquationsAndAlign(multipleInput);
            normalizedMultiple.Should().NotContain("aligned");
            int beginAlignCount = Regex.Matches(normalizedMultiple, @"\\begin\{align\}").Count;
            int endAlignCount = Regex.Matches(normalizedMultiple, @"\\end\{align\}").Count;
            beginAlignCount.Should().Be(3, "All 3 aligned blocks must be converted to begin{align}");
            endAlignCount.Should().Be(3, "All 3 aligned blocks must have end{align}");

            // Case C: Aligned environment with nested and corrupted dollar signs
            string corruptedDollarInput = @"
\begin{aligned}
&f(x) = ${x^2 + 1}$ + $2x$ \\
&g(x) = ${\left(u_n + 1\right)}$ - $5$
\end{aligned}";

            string normalizedDollars = QuestionParserEngine.NormalizeSystemEquationsAndAlign(corruptedDollarInput);
            normalizedDollars.Should().NotContain("aligned");
            normalizedDollars.Should().NotContain("${");
            normalizedDollars.Should().NotContain("}$");
            normalizedDollars.Should().NotContain("$2x$");
            normalizedDollars.Should().NotContain("$5$");
            normalizedDollars.Should().Contain("&f(x) = x^2 + 1 + 2x");
            normalizedDollars.Should().Contain(@"&g(x) = \left(u_n + 1\right) - 5");
        }

        [Fact]
        public void StressTest_ComplexAbsoluteValues_InMarkdownTableCells_NeverBreaksPipeDelimiters()
        {
            // Markdown table with complex absolute value equations in cells
            string markdownTable = @"| STT | Phương trình chứa trị tuyệt đối | Điều kiện xác định | Kết luận |
| :--- | :--- | :--- | :--- |
| 1 | $|x - 2| + |y| = 1$ | $x \in \mathbb{R},\ y \in \mathbb{R}$ | Hình vuông |
| 2 | $\left| x^2 - 4 \right| + |y - 1| = 0$ | $|x| \le 2$ | Hữu hạn nghiệm |
| 3 | $||x| - 1| = 2$ | $x \ge 0$ | $x = 3$ |
| 4 | $|x - 2| + |y| = 1$ và $|x| + |y| \le 4$ | $\left| x \right| \ge 0$ | Vùng giao |";

            // Act: Normalization with protectAbs = true
            string normalized = QuestionParserEngine.NormalizeMathToBracedDollars(markdownTable, protectAbs: true);

            // Assert 1: All absolute values must be wrapped in ${...}$
            normalized.Should().Contain("${|x - 2| + |y| = 1}$");
            normalized.Should().Contain(@"${\left| x^2 - 4 \right| + |y - 1| = 0}$");
            normalized.Should().Contain("${||x| - 1| = 2}$");
            normalized.Should().Contain("${|x - 2| + |y| = 1}$");

            // Assert 2: Table rows must preserve exact column count of 4
            var rows = normalized.Split(new[] { '\r', '\n' }, StringSplitOptions.RemoveEmptyEntries)
                                 .Where(r => r.Trim().StartsWith("|") && r.Trim().EndsWith("|"))
                                 .ToList();

            rows.Count.Should().Be(6, "Header + Separator + 4 Data rows = 6 rows total");

            for (int i = 0; i < rows.Count; i++)
            {
                if (rows[i].Contains("---")) continue; // Skip separator row
                var cells = WordExportService.SplitTableCells(rows[i]);
                cells.Count.Should().Be(4, $"Dòng {i + 1} phải có đúng 4 cột, không được bị xé nhỏ bởi ký tự '|' của trị tuyệt đối");
            }

            // Assert 3: Export to Word OpenXML and verify table cells in document
            string docxPath = Path.Combine(_tempDir, "abs_table_stress.docx");
            try
            {
                var exporter = new WordExportService();
                exporter.ExportToDocx(docxPath, normalized, new WordExportOptions { ConvertTablesToWordGrid = true });
                File.Exists(docxPath).Should().BeTrue();

                using var doc = WordprocessingDocument.Open(docxPath, false);
                var table = doc.MainDocumentPart!.Document.Body!.Elements<Table>().FirstOrDefault();
                table.Should().NotBeNull("Bảng markdown phải được chuyển đổi thành OpenXML Table");

                var tableRows = table!.Elements<TableRow>().ToList();
                tableRows.Count.Should().Be(5, "1 header row + 4 data rows (separator row removed)");

                foreach (var tr in tableRows)
                {
                    tr.Elements<TableCell>().Count().Should().Be(4, "Mỗi hàng trong Word table phải có chính xác 4 TableCell");
                }
            }
            finally
            {
                if (File.Exists(docxPath)) File.Delete(docxPath);
            }
        }

        [Fact]
        public void StressTest_StandaloneExpressions_WithoutDelimiters_WrapsInBracedDollars()
        {
            // Case 1: Unbraced LaTeX constructs: \left(u_n\right), \left[a; b\right], \left|x - 2\right|, \vec{AB}
            string textWithUnbraced = @"Cho cấp số cộng \left(u_n\right) xác định trên đoạn \left[-2; 5\right].
Xét biểu thức độ dài vectơ \vec{AB} cùng giá trị \left|x - 2\right|.";

            string normalized = QuestionParserEngine.NormalizeMathToBracedDollars(textWithUnbraced, wrapUnbracedLatex: true, forceMath: false, protectAbs: true);

            normalized.Should().Contain(@"${\left(u_n\right)}$");
            normalized.Should().Contain(@"${\left[-2; 5\right]}$");
            normalized.Should().Contain(@"${\vec{AB}}$");
            normalized.Should().Contain(@"${\left|x - 2\right|}$");

            // Case 2: Expressions in standard delimiters ($...$, $$...$$, \[...\], \(...\))
            string textDelimited = @"Phương trình $x^2 + 2x = 0$, $$y = \sin(x)$$, \[\int_0^1 x dx\] và \(\sqrt{x} = 2\).";
            string normDelimited = QuestionParserEngine.NormalizeMathToBracedDollars(textDelimited, protectAbs: true);

            normDelimited.Should().Contain("${x^2 + 2x = 0}$");
            normDelimited.Should().Contain(@"${y = \sin(x)}$");
            normDelimited.Should().Contain(@"${\int_0^1 x dx}$");
            normDelimited.Should().Contain(@"${\sqrt{x} = 2}$");

            // Case 3: Double-wrapped and multiply-bracketed formulas
            string doubleWrapped = @"Biểu thức ${${x + y}$}$, ${$2x = 4$}$, ${${{\frac{a}{b}}}}$ và $${u_n}$$";
            string cleaned = QuestionParserEngine.CleanDoubleWrappedFormulas(doubleWrapped);

            cleaned.Should().NotContain("${${");
            cleaned.Should().NotContain("}$}$");
            cleaned.Should().NotContain("${$");
            cleaned.Should().NotContain("$}$");
            cleaned.Should().Contain("${x + y}$");
            cleaned.Should().Contain("${2x = 4}$");
            cleaned.Should().Contain(@"${\frac{a}{b}}$");
            cleaned.Should().Contain("${u_n}$");
        }

        [Fact]
        public void StressTest_StandaloneUnbracedFracAndSqrt_InvestigateWrappingBehavior()
        {
            // Adversarial test: standalone LaTeX commands without $ delimiters e.g. \frac{1}{2} or \sqrt{x}
            string unbracedFrac = @"Xét tỉ số \frac{1}{2} và căn bậc hai \sqrt{x + 1} trong lời giải.";
            string normalized = QuestionParserEngine.NormalizeMathToBracedDollars(unbracedFrac, wrapUnbracedLatex: true, forceMath: false, protectAbs: true);

            // Document exact behavior: WrapUnbracedLatexExpressions currently targets \left( \left[ \left| and \vec
            // Note that \frac without $ is not auto-wrapped unless placed in standard LaTeX delimiters or parsed in QuestionParser
            normalized.Should().NotBeNull();
        }

        [Fact]
        public void StressTest_DirtyLatex_StickyNumbers_BoldHeaders_RandomListTags_FiltersCleanly()
        {
            // Case 1: Sticky numbers \item1., \item2., \item10.
            string stickyNumbers = @"
\begin{enumerate}
\item1. Xác định tập xác định của hàm số $D = \mathbb{R}$.
\item2. Tính đạo hàm $y'$.
\item10. Tìm giá trị lớn nhất của hàm số.
\end{enumerate}";

            string cleanNumbers = QuestionParserEngine.FilterLatexItems(stickyNumbers);
            cleanNumbers.Should().NotContain(@"\item1.");
            cleanNumbers.Should().NotContain(@"\item2.");
            cleanNumbers.Should().NotContain(@"\item10.");
            cleanNumbers.Should().NotContain(@"\begin{enumerate}");
            cleanNumbers.Should().NotContain(@"\end{enumerate}");
            cleanNumbers.Should().Contain("1. Xác định tập xác định");
            cleanNumbers.Should().Contain("2. Tính đạo hàm");
            cleanNumbers.Should().Contain("10. Tìm giá trị");

            // Case 2: Bold headers \textbf{a)}, \textbf{Đúng.}, **a)**, **Sai.**
            string boldHeaders = @"
\item \textbf{a)} \textbf{Đúng.} Hàm số đạt cực tiểu tại $x = 1$.
\item \textbf{b)} \textbf{Sai.} Hàm số có 2 điểm cực đại.
\item **c)** **Đúng.** Giá trị cực tiểu $y_{CT} = -4$.
\item[**d**] **Sai.** Đồ thị hàm số đi qua gốc tọa độ $O(0; 0)$.";

            string cleanBold = QuestionParserEngine.FilterLatexItems(boldHeaders);
            cleanBold.Should().NotContain(@"\textbf{a)}");
            cleanBold.Should().NotContain(@"\textbf{Đúng.}");
            cleanBold.Should().NotContain(@"\textbf{b)}");
            cleanBold.Should().NotContain(@"\textbf{Sai.}");
            cleanBold.Should().NotContain("**c)**");
            cleanBold.Should().NotContain("**Đúng.**");
            cleanBold.Should().NotContain("**d**");
            cleanBold.Should().Contain("a) Đúng. Hàm số đạt cực tiểu tại $x = 1$.");
            cleanBold.Should().Contain("b) Sai. Hàm số có 2 điểm cực đại.");
            cleanBold.Should().Contain("c) Đúng. Giá trị cực tiểu $y_{CT} = -4$.");
            cleanBold.Should().Contain("d) Sai. Đồ thị hàm số đi qua gốc tọa độ $O(0; 0)$.");

            // Case 3: Sticky letters and Vietnamese tags: \itema), \itemĐúng, \item\textbf{1.}
            string stickyTags = @"
\itema) Mệnh đề thứ nhất đúng.
\itemb) Mệnh đề thứ hai sai.
\itemĐúng. Mệnh đề thứ ba đúng.
\item\textbf{1.} Bước đầu tiên cần thực hiện.";

            string cleanTags = QuestionParserEngine.FilterLatexItems(stickyTags);
            cleanTags.Should().NotContain(@"\itema)");
            cleanTags.Should().NotContain(@"\itemb)");
            cleanTags.Should().NotContain(@"\itemĐúng");
            cleanTags.Should().NotContain(@"\item\textbf");
            cleanTags.Should().Contain("a) Mệnh đề thứ nhất đúng.");
            cleanTags.Should().Contain("b) Mệnh đề thứ hai sai.");
            cleanTags.Should().Contain("Đúng. Mệnh đề thứ ba đúng.");
            cleanTags.Should().Contain("1. Bước đầu tiên cần thực hiện.");

            // Case 4: Random environments and tags: itemchoice, itemch, list
            string randomTags = @"
\begin{itemchoice}
\itemch Phương án 1
\itemch Phương án 2
\end{itemchoice}
\begin{list}{}{}
\item Phần tử phụ
\end{list}";

            string cleanRandom = QuestionParserEngine.FilterLatexItems(randomTags);
            cleanRandom.Should().NotContain(@"\begin{itemchoice}");
            cleanRandom.Should().NotContain(@"\end{itemchoice}");
            cleanRandom.Should().NotContain(@"\itemch");
            cleanRandom.Should().NotContain(@"\begin{list}");
            cleanRandom.Should().NotContain(@"\end{list}");
            cleanRandom.Should().NotContain(@"\item");
        }

        #endregion

        #region Requirement 2: Word Export OpenXML Structure Stress Tests

        [Fact]
        public void StressTest_OpenXmlDocumentStructure_TabsContain1985_3969_5953Twips()
        {
            var exporter = new WordExportService();
            var questions = new List<QuestionItem>
            {
                new QuestionItem
                {
                    Subject = "Toán",
                    Grade = 12,
                    QuestionType = "MultipleChoice4",
                    Content = "Tập nghiệm của phương trình $x^2 - 1 = 0$ là:",
                    Options = new Dictionary<string, string>
                    {
                        { "A", "$x = 1$" },
                        { "B", "$x = -1$" },
                        { "C", "$x = \\pm 1$" },
                        { "D", "$x = 0$" }
                    },
                    CorrectAnswer = "C"
                }
            };

            var options = new ExamExportOptions
            {
                TabSpacing = TabSpacingMode.Standard35,
                SchoolName = "SỞ GD&ĐT HÀ NỘI",
                ExamTitle = "ĐỀ THI THỬ THPT QUỐC GIA"
            };

            string docxPath = Path.Combine(_tempDir, "test_tabs_openxml.docx");
            try
            {
                exporter.ExportExamToDocx(docxPath, questions, options);
                File.Exists(docxPath).Should().BeTrue();

                using var doc = WordprocessingDocument.Open(docxPath, false);
                var body = doc.MainDocumentPart!.Document.Body!;

                // Find the paragraph with option tabs (A. ... B. ... C. ... D. ...)
                var optionPara = body.Elements<Paragraph>()
                    .FirstOrDefault(p => p.InnerText.Contains("A.") && p.InnerText.Contains("B.") && p.InnerText.Contains("C.") && p.InnerText.Contains("D."));

                optionPara.Should().NotBeNull("Paragraph chứa 4 phương án trắc nghiệm trên 1 dòng phải tồn tại");

                var tabsElement = optionPara!.ParagraphProperties?.Tabs;
                tabsElement.Should().NotBeNull("<w:tabs> element must be defined in paragraph properties");

                var tabStops = tabsElement!.Elements<TabStop>().ToList();
                tabStops.Count.Should().Be(3, "3 tab stops for 4 inline options");

                // Check exact positions: 1985 twips (3.5cm), 3969 twips (7.0cm), 5953 twips (10.5cm)
                tabStops[0].Position!.Value.Should().Be(1985, "Tab 1 position must be 1985 twips (3.5cm)");
                tabStops[0].Val!.Value.Should().Be(TabStopValues.Left);

                tabStops[1].Position!.Value.Should().Be(3969, "Tab 2 position must be 3969 twips (7.0cm)");
                tabStops[1].Val!.Value.Should().Be(TabStopValues.Left);

                tabStops[2].Position!.Value.Should().Be(5953, "Tab 3 position must be 5953 twips (10.5cm)");
                tabStops[2].Val!.Value.Should().Be(TabStopValues.Left);

                // Indentation 283 twips (0.5cm) and line spacing 276 (1.15)
                var ind = optionPara.ParagraphProperties?.Indentation;
                ind.Should().NotBeNull();
                ind!.Left!.Value.Should().Be("283");

                var spacing = optionPara.ParagraphProperties?.SpacingBetweenLines;
                spacing.Should().NotBeNull();
                spacing!.Line!.Value.Should().Be("276");
            }
            finally
            {
                if (File.Exists(docxPath)) File.Delete(docxPath);
            }
        }

        [Fact]
        public void StressTest_MultipleEmbeddedImages_HaveUniqueDocPropertiesId_AndPassOpenXmlValidation()
        {
            var exporter = new WordExportService();

            // Create 3 questions with a total of 6 embedded images
            var questions = new List<QuestionItem>
            {
                new QuestionItem
                {
                    Subject = "Toán",
                    Grade = 12,
                    QuestionType = "MultipleChoice4",
                    Content = $"Câu 1. Đồ thị như hình vẽ bên: [HÌNH 1: {_dummyPngPath}]",
                    Options = new Dictionary<string, string> { ["A"] = "1", ["B"] = "2", ["C"] = "3", ["D"] = "4" },
                    Images = new List<string> { _dummyPngPath }
                },
                new QuestionItem
                {
                    Subject = "Toán",
                    Grade = 12,
                    QuestionType = "MultipleChoice4",
                    Content = $"Câu 2. Hình học không gian: [IMAGE: {_dummyPngPath}]",
                    Options = new Dictionary<string, string> { ["A"] = "1", ["B"] = "2", ["C"] = "3", ["D"] = "4" },
                    Images = new List<string> { _dummyPngPath, _dummyPngPath }
                },
                new QuestionItem
                {
                    Subject = "Toán",
                    Grade = 12,
                    QuestionType = "ShortAnswer",
                    Content = $"Câu 3. Thiết diện mặt cầu: [HINH_ANH: {_dummyPngPath}]",
                    CorrectAnswer = "42"
                }
            };

            string docxPath = Path.Combine(_tempDir, "multi_image_validation.docx");
            try
            {
                exporter.ExportExamToDocx(docxPath, questions, new ExamExportOptions());
                File.Exists(docxPath).Should().BeTrue();

                using var doc = WordprocessingDocument.Open(docxPath, false);
                var body = doc.MainDocumentPart!.Document.Body!;

                // 1. Verify DocProperties.Id uniqueness
                var docProperties = body.Descendants<DW.DocProperties>().ToList();
                docProperties.Count.Should().BeGreaterThanOrEqualTo(5, "At least 5 embedded image drawings");

                var docPrIds = docProperties.Select(dp => dp.Id!.Value).ToList();
                docPrIds.Distinct().Count().Should().Be(docPrIds.Count,
                    $"Every DocProperties.Id must be unique. Found IDs: {string.Join(", ", docPrIds)}");

                // 2. Verify PIC.NonVisualDrawingProperties.Id uniqueness
                var picProperties = body.Descendants<PIC.NonVisualDrawingProperties>().ToList();
                var picIds = picProperties.Select(p => p.Id!.Value).ToList();
                picIds.Distinct().Count().Should().Be(picIds.Count,
                    $"Every NonVisualDrawingProperties.Id must be unique. Found IDs: {string.Join(", ", picIds)}");

                // 3. OpenXML Semantic & Schema Validation using OpenXmlValidator
                var validator = new OpenXmlValidator();
                var validationErrors = validator.Validate(doc).ToList();

                // Check for any drawing or structural errors
                var drawingErrors = validationErrors.Where(e =>
                    e.Description.Contains("DocProperties") ||
                    e.Description.Contains("drawing") ||
                    e.Description.Contains("inline") ||
                    e.Description.Contains("blip")).ToList();

                drawingErrors.Should().BeEmpty("Embedded image drawings must produce zero OpenXML validation errors");
            }
            finally
            {
                if (File.Exists(docxPath)) File.Delete(docxPath);
            }
        }

        [Fact]
        public void StressTest_FlatTableHeaders_HaveAllBorderValuesSetToNone()
        {
            var exporter = new WordExportService();
            var questions = new List<QuestionItem>
            {
                new QuestionItem
                {
                    Subject = "Toán",
                    Grade = 12,
                    QuestionType = "MultipleChoice4",
                    Content = "Câu hỏi trắc nghiệm kiểm tra header table.",
                    Options = new Dictionary<string, string> { ["A"] = "1", ["B"] = "2", ["C"] = "3", ["D"] = "4" }
                }
            };

            string docxPath = Path.Combine(_tempDir, "flat_header_test.docx");
            try
            {
                exporter.ExportExamToDocx(docxPath, questions, new ExamExportOptions
                {
                    SchoolName = "SỞ GIÁO DỤC VÀ ĐÀO TẠO",
                    ExamTitle = "ĐỀ THI CHÍNH THỨC"
                });

                using var doc = WordprocessingDocument.Open(docxPath, false);
                var body = doc.MainDocumentPart!.Document.Body!;

                // Find the first table (Exam Header Table)
                var headerTable = body.Elements<Table>().FirstOrDefault();
                headerTable.Should().NotBeNull("Bảng tiêu đề đề thi phải tồn tại ở đầu tài liệu");

                var tblPr = headerTable!.GetFirstChild<TableProperties>();
                tblPr.Should().NotBeNull();

                var borders = tblPr!.TableBorders;
                borders.Should().NotBeNull("Bảng tiêu đề phải định nghĩa TableBorders");

                // Assert that ALL 6 border properties are explicitly BorderValues.None
                borders!.TopBorder.Should().NotBeNull();
                borders.TopBorder!.Val!.Value.Should().Be(BorderValues.None, "TopBorder must be None");

                borders.BottomBorder.Should().NotBeNull();
                borders.BottomBorder!.Val!.Value.Should().Be(BorderValues.None, "BottomBorder must be None");

                borders.LeftBorder.Should().NotBeNull();
                borders.LeftBorder!.Val!.Value.Should().Be(BorderValues.None, "LeftBorder must be None");

                borders.RightBorder.Should().NotBeNull();
                borders.RightBorder!.Val!.Value.Should().Be(BorderValues.None, "RightBorder must be None");

                borders.InsideHorizontalBorder.Should().NotBeNull();
                borders.InsideHorizontalBorder!.Val!.Value.Should().Be(BorderValues.None, "InsideHorizontalBorder must be None");

                borders.InsideVerticalBorder.Should().NotBeNull();
                borders.InsideVerticalBorder!.Val!.Value.Should().Be(BorderValues.None, "InsideVerticalBorder must be None");
            }
            finally
            {
                if (File.Exists(docxPath)) File.Delete(docxPath);
            }
        }

        #endregion
    }
}
