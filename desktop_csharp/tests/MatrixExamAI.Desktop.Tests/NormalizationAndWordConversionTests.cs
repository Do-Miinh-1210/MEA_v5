using System;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Text.RegularExpressions;
using DocumentFormat.OpenXml.Packaging;
using DocumentFormat.OpenXml.Wordprocessing;
using FluentAssertions;
using MatrixExamAI.Desktop.Services;
using System.Collections.Generic;
using MatrixExamAI.Desktop.Views;
using MatrixExamAI.Shared.Extensibility;
using MatrixExamAI.Shared.Models;
using Xunit;

namespace MatrixExamAI.Desktop.Tests
{
    public class NormalizationAndWordConversionTests : IDisposable
    {
        private readonly string _tempDir;

        public NormalizationAndWordConversionTests()
        {
            _tempDir = Path.Combine(Path.GetTempPath(), "MEA_Tests_" + Guid.NewGuid().ToString("N"));
            Directory.CreateDirectory(_tempDir);
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

        #region Tier 1 - Normative Tests

        [Fact]
        public void Normalization_SampleExam_ShouldExtract2Questions13Formulas1TableInLessThan200Ms()
        {
            // Arrange - Authoritative sample from ConvertView.xaml.cs & ORIGINAL_REQUEST.md
            string sampleInput = @"% Câu 1 [Nhận biết]_[Hàm số bậc hai]
Cho hàm số $y = ax^2 + bx + c$ với điều kiện $|x| < 3$ và thỏa mãn bảng biến thiên sau:
| x | -\infty | 1 | +\infty |
|---|---|---|---|
| y' | - | 0 | + |
| y | +\infty | -4 | +\infty |

Mệnh đề nào sau đây đúng?
A. Hàm số đồng biến trên khoảng $(1; +\infty)$.
B. Giá trị nhỏ nhất của hàm số là $-4$.
C. Hàm số nghịch biến trên khoảng $(-\infty; 1)$.
D. Tọa độ đỉnh parabol là $I(1; -4)$.

% Câu 2 [Thông hiểu]_[Bất phương trình]
Tập nghiệm của bất phương trình $|2x - 1| \le 5$ là đoạn $[a; b]$. Tính giá trị $P = a + b$.
A. $P = 1$.
B. $P = 2$.
C. $P = -1$.
D. $P = 0$.";

            // Act: measure execution time
            var sw = Stopwatch.StartNew();
            string normalized = ConvertView.NormalizeContent(sampleInput, braceMath: true, protectAbs: true);
            sw.Stop();

            // Assert 1: Execution time strictly < 200ms (0.2s)
            sw.ElapsedMilliseconds.Should().BeLessThan(200, "Normalization must complete in under 0.2s per requirement");

            // Assert 2: Exactly 2 questions identified
            int questionCount = Regex.Matches(normalized, @"(?i)(?:^|\n)%?\s*Câu\s+\d+|===CAU===").Count;
            questionCount.Should().Be(2, "Sample exam contains exactly 2 questions");

            // Assert 3: Exactly 13 formulas wrapped with ${...}$
            var formulas = Regex.Matches(normalized, @"\$\{.*?\}");
            formulas.Count.Should().Be(13, "Sample exam must have exactly 13 formulas wrapped in ${...}$");

            // Assert 4: Exactly 1 table grid detected
            int tableLineCount = normalized.Split('\n')
                .Count(line => line.Trim().StartsWith("|") && line.Trim().EndsWith("|") && line.Count(c => c == '|') >= 2);
            tableLineCount.Should().BeGreaterThanOrEqualTo(4, "Markdown table has 4 rows (header + separator + 2 data rows)");

            // Assert 5: Absolute value formulas are properly wrapped with outer braces
            normalized.Should().Contain("${|x| < 3}$");
            normalized.Should().Contain("${|2x - 1| \\le 5}$");
        }

        [Fact]
        public void NativeDocxExport_ValidContent_ShouldGenerateOpenXmlA4DocumentWithCorrectStructure()
        {
            // Arrange
            string docxPath = Path.Combine(_tempDir, "sample_export.docx");
            string content = @"Câu 1: Cho hàm số ${y = x^2 - 4x + 3}$.
Bảng giá trị của hàm số:
| x | 0 | 1 | 2 | 3 |
|---|---|---|---|---|
| y | 3 | 0 | -1 | 0 |

Tìm tọa độ đỉnh:
A. ${I(2; -1)}$
B. ${I(1; 0)}$
C. ${I(0; 3)}$
D. ${I(-2; 1)}$";

            var wordService = new WordExportService();
            var options = new WordExportOptions
            {
                ConvertTablesToWordGrid = true,
                HighlightFormulas = true,
                FontFamily = "Times New Roman",
                FontSizePt = "24" // 12pt
            };

            // Act
            wordService.ExportToDocx(docxPath, content, options);

            // Assert: File exists and is valid OpenXML WordprocessingDocument
            File.Exists(docxPath).Should().BeTrue();
            new FileInfo(docxPath).Length.Should().BeGreaterThan(1000);

            using var doc = WordprocessingDocument.Open(docxPath, false);
            var mainPart = doc.MainDocumentPart;
            mainPart.Should().NotBeNull();
            var body = mainPart!.Document.Body;
            body.Should().NotBeNull();

            // 1. Check A4 dimensions and Pedagogical Margins
            var sectionProps = body!.Elements<SectionProperties>().FirstOrDefault();
            sectionProps.Should().NotBeNull();
            var pageSize = sectionProps!.Elements<PageSize>().FirstOrDefault();
            pageSize.Should().NotBeNull();
            pageSize!.Width!.Value.Should().Be(11906, "A4 width is 11906 twips (210mm)");
            pageSize.Height!.Value.Should().Be(16838, "A4 height is 16838 twips (297mm)");

            var pageMargin = sectionProps.Elements<PageMargin>().FirstOrDefault();
            pageMargin.Should().NotBeNull();
            pageMargin!.Top!.Value.Should().Be(1134, "Top margin is 2cm (1134 twips)");
            pageMargin.Bottom!.Value.Should().Be(1134, "Bottom margin is 2cm (1134 twips)");
            pageMargin.Left!.Value.Should().Be(1417, "Left margin is 2.5cm (1417 twips)");
            pageMargin.Right!.Value.Should().Be(1134, "Right margin is 2cm (1134 twips)");

            // 2. Check Table Structure
            var table = body.Elements<Table>().FirstOrDefault();
            table.Should().NotBeNull("Word Table element must be created for markdown table");

            var rows = table!.Elements<TableRow>().ToList();
            rows.Count.Should().Be(2, "Header row + 1 data row (separator row is excluded)");

            var headerCells = rows[0].Elements<TableCell>().ToList();
            headerCells.Count.Should().Be(5, "Table has 5 columns (x, 0, 1, 2, 3)");

            // Verify header shading
            var headerShading = headerCells[0].TableCellProperties?.Elements<Shading>().FirstOrDefault();
            headerShading.Should().NotBeNull();
            headerShading!.Fill!.Value.Should().Be("F1F5F9");

            // 3. Check Math Runs formatting (Italic)
            var mathRuns = body.Descendants<Run>()
                .Where(r => r.InnerText.StartsWith("${") && (r.InnerText.EndsWith("}") || r.InnerText.EndsWith("}$")))
                .ToList();
            mathRuns.Should().NotBeEmpty();
            foreach (var run in mathRuns)
            {
                run.RunProperties?.Italic.Should().NotBeNull("Math runs must be formatted as italic");
                run.RunProperties?.Color?.Val?.Value.Should().Be("0F172A", "Formulas should use Slate-900 color");
            }

            // 4. Check Question Heading bold run
            var headingRun = body.Descendants<Run>()
                .FirstOrDefault(r => r.InnerText.Contains("Câu 1"));
            headingRun.Should().NotBeNull();
            headingRun!.RunProperties?.Bold.Should().NotBeNull("Question heading must be bold");
        }

        #endregion

        #region Tier 2 - Boundary Value Tests

        [Fact]
        public void Normalization_EmptyOrWhitespace_ShouldReturnInputSafely()
        {
            ConvertView.NormalizeContent("", true, true).Should().BeEmpty();
            ConvertView.NormalizeContent(null!, true, true).Should().BeNull();
            ConvertView.NormalizeContent("   \n\t  ", true, true).Trim().Should().BeEmpty();
        }

        [Fact]
        public void Normalization_CurrencyAmounts_ShouldNotBeWrappedAsFormulas()
        {
            string input = "Giá sản phẩm là $100$ và $250.50$.";
            string output = ConvertView.NormalizeContent(input, braceMath: true, protectAbs: true);

            output.Should().Contain("$100$");
            output.Should().Contain("$250.50$");
            output.Should().NotContain("${100}$");
            output.Should().NotContain("${250.50}$");
        }

        [Fact]
        public void Normalization_LaTeXBrackets_ShouldBeConvertedToBracedFormulas()
        {
            string input = @"Phương trình \[x^2 + 2x + 1 = 0\] và biểu thức \(a + b = c\) cùng $$f(x) = \sin(x)$$.";
            string output = ConvertView.NormalizeContent(input, braceMath: true, protectAbs: true);

            output.Should().Contain("${x^2 + 2x + 1 = 0}$");
            output.Should().Contain("${a + b = c}$");
            output.Should().Contain("${f(x) = \\sin(x)}$");
        }

        [Fact]
        public void Normalization_AlreadyBracedFormula_ShouldNotDoubleWrap()
        {
            string input = "Biểu thức ${x + 1}$ và ${\\frac{a}{b}}$ đã có ngoặc nhọn.";
            string output = ConvertView.NormalizeContent(input, braceMath: true, protectAbs: true);

            output.Should().Contain("${x + 1}$");
            output.Should().Contain("${\\frac{a}{b}}$");
            output.Should().NotContain("${{");
        }

        [Fact]
        public void Normalization_PipeInsideAbsoluteValue_ShouldNotBreakMarkdownTable()
        {
            string tableWithAbs = @"| Giá trị x | Biểu thức $|x - 2|$ | Kết quả |
|---|---|---|
| 0 | $|0 - 2| = 2$ | 2 |
| 3 | $|3 - 2| = 1$ | 1 |";

            string output = ConvertView.NormalizeContent(tableWithAbs, braceMath: true, protectAbs: true);

            var rows = output.Split('\n').Where(l => l.Trim().StartsWith("|")).ToList();
            rows.Count.Should().Be(4);

            var cellsRow1 = WordExportService.SplitTableCells(rows[0]);
            cellsRow1.Count.Should().Be(3, "Pipe inside $|x - 2|$ must not split the table cell");
        }

        #endregion

        #region Tier 3 - Combinatorial / Pairwise Tests

        [Theory]
        [InlineData(true, true)]
        [InlineData(true, false)]
        [InlineData(false, true)]
        [InlineData(false, false)]
        public void Normalization_FlagsCombination_ShouldExecuteDeterministically(bool braceMath, bool protectAbs)
        {
            string input = "Cho hàm số $y = |x| + 1$.\n| A | B |\n|---|---|\n| 1 | 2 |";
            string result = ConvertView.NormalizeContent(input, braceMath, protectAbs);

            result.Should().NotBeNullOrWhiteSpace();
            if (braceMath)
            {
                result.Should().Contain("${");
            }
            else
            {
                result.Should().NotContain("${");
            }
        }

        [Theory]
        [InlineData("Arial", "20")]
        [InlineData("Calibri", "22")]
        [InlineData("Times New Roman", "24")]
        public void NativeDocxExport_DifferentFontSettings_ShouldApplyCorrectFontToOpenXml(string font, string sizePt)
        {
            string docxPath = Path.Combine(_tempDir, $"font_test_{font}.docx");
            var wordService = new WordExportService();
            var options = new WordExportOptions
            {
                FontFamily = font,
                FontSizePt = sizePt
            };

            wordService.ExportToDocx(docxPath, "Nội dung kiểm tra font chữ ${x^2}$.", options);

            using var doc = WordprocessingDocument.Open(docxPath, false);
            var runs = doc.MainDocumentPart!.Document.Body!.Descendants<Run>().ToList();
            runs.Should().NotBeEmpty();

            var firstRun = runs.First();
            firstRun.RunProperties?.RunFonts?.Ascii?.Value.Should().Be(font);
            firstRun.RunProperties?.FontSize?.Val?.Value.Should().Be(sizePt);
        }

        #endregion

        #region Tier 4 - Workload & Stress Tests

        [Fact]
        public void Normalization_HeavyExamWorkload_100Questions_ShouldProcessInUnder1Second()
        {
            var sb = new System.Text.StringBuilder();
            for (int i = 1; i <= 100; i++)
            {
                sb.AppendLine($"% Câu {i} [Thông hiểu]");
                sb.AppendLine($"Tính đạo hàm của $f(x) = {i}x^2 + |x - {i}| + \\sqrt{{{i}x}}$ trên khoảng $(0; +\\infty)$.");
                sb.AppendLine($"A. $f'(x) = {2 * i}x + 1$");
                sb.AppendLine($"B. $f'(x) = {2 * i}x - 1$");
                sb.AppendLine($"C. $f'(x) = {i}x$");
                sb.AppendLine($"D. $f'(x) = 0$");
                sb.AppendLine();
            }

            string heavyInput = sb.ToString();

            var sw = Stopwatch.StartNew();
            string normalized = ConvertView.NormalizeContent(heavyInput, braceMath: true, protectAbs: true);
            sw.Stop();

            sw.ElapsedMilliseconds.Should().BeLessThan(1000, "100 questions normalization must take < 1 second");
            int countFormulas = Regex.Matches(normalized, @"\$\{.*?\}").Count;
            countFormulas.Should().Be(600, "100 questions with 6 formulas each = 600 formulas wrapped");
        }

        [Fact]
        public void Normalization_LatexChoiceSnippet_ShouldRecognize1QuestionAndWrapAllFormulas()
        {
            string latexSnippet = @"\begin{ex}
Cho cấp số cộng \left(u_n\right) có $u_1 = -2$ và công sai $d = 3$. Giá trị của $u_2$ bằng
\choice
{$1$}
{$-5$}
{$-6$}
{\True $1$}
\loigiai{
Ta có $u_2 = u_1 + d = -2 + 3 = 1$.
}
\end{ex}";

            var result = QuestionParserEngine.ParseQuestions(latexSnippet, "Toán", 12);

            result.TotalCount.Should().Be(1);
            result.TnCount.Should().Be(1);
            result.Tier.Should().Be("latex");

            var q = result.Questions[0];
            q.QuestionType.Should().Be("MultipleChoice4");
            q.CorrectAnswer.Should().Be("D");
            q.Options["A"].Should().Be("${1}$");
            q.Options["B"].Should().Be("${-5}$");
            q.Options["C"].Should().Be("${-6}$");
            q.Options["D"].Should().Be("${1}$");

            q.Content.Should().Contain(@"${\left(u_n\right)}$");
            q.Content.Should().Contain(@"${u_1 = -2}$");
            q.Content.Should().Contain(@"${d = 3}$");
            q.Content.Should().Contain(@"${u_2}$");

            q.Explanation.Should().Contain(@"${u_2 = u_1 + d = -2 + 3 = 1}$");

            result.FormattedDocText.Should().Contain("Câu 1.");
            result.FormattedDocText.Should().Contain("Đáp án: D");
            result.FormattedDocText.Should().Contain("Lời giải:");
        }

        [Fact]
        public void Normalization_FormulaDoubleWrapAndSolutionVariants_ShouldBeCleanedAndIncluded()
        {
            // Test 1: Clean double wrapped formulas
            string doubleWrapped = @"Cho dãy số ${${\left(u_n\right)}$}$ với ${$u_1 = 1$}$ và ${{{u_n = 2u_{n-1}}}}$";
            string cleaned = QuestionParserEngine.CleanDoubleWrappedFormulas(doubleWrapped);
            cleaned.Should().NotContain("${${");
            cleaned.Should().NotContain("}$}$");
            cleaned.Should().Contain(@"${\left(u_n\right)}$");
            cleaned.Should().Contain(@"${u_1 = 1}$");
            cleaned.Should().Contain(@"${u_n = 2u_{n-1}}$");

            // Test 2: loigiai with optional brackets [Hướng dẫn]
            string latexWithCustomLoigiai = @"\begin{ex}
Tính giới hạn của dãy số $\lim \frac{1}{n}$.
\choice
{\True $0$}
{$1$}
{$-1$}
{$+\infty$}
\loigiai[Phương pháp]{
Áp dụng công thức cơ bản $\lim \frac{1}{n^k} = 0$.
}
\end{ex}";
            var res2 = QuestionParserEngine.ParseQuestions(latexWithCustomLoigiai, "Toán", 12);
            res2.TotalCount.Should().Be(1);
            res2.Questions[0].Explanation.Should().Contain(@"${\lim \frac{1}{n^k} = 0}$");
            res2.FormattedDocText.Should().Contain("Lời giải:");

            // Test 3: Question without loigiai should still emit 'Lời giải: (Đang cập nhật)'
            string latexNoLoigiai = @"\begin{ex}
Giải phương trình $x + 1 = 0$.
\choice
{\True $-1$}
{$1$}
{$0$}
{$2$}
\end{ex}";
            var res3 = QuestionParserEngine.ParseQuestions(latexNoLoigiai, "Toán", 12);
            res3.TotalCount.Should().Be(1);
            res3.FormattedDocText.Should().Contain("Lời giải: (Đang cập nhật)");

            // Test 4: User snippet with \begin{aligned} converted to align and inner dollars cleaned
            string userAlignedSnippet = @"$
\left\{
\begin{aligned}
&u_1 + ${\left(u_1 + 4d\right)}$ = 18 \\
&${\left(u_1 + 2d\right)}$ + ${\left(u_1 + 6d\right)}$ = 26
\end{aligned}
\right.
\Leftrightarrow
\left\{
\begin{aligned}
&2u_1 + 4d = 18 \\
&2u_1 + 8d = 26
\end{aligned}
\right.
\Leftrightarrow
\left\{
\begin{aligned}
&u_1 + 2d = 9 \\
&u_1 + 4d = 13
\end{aligned}
\right.
$";
            string normalizedAligned = QuestionParserEngine.NormalizeMathToBracedDollars(userAlignedSnippet);
            normalizedAligned.Should().NotContain("aligned");
            normalizedAligned.Should().Contain(@"\begin{align}");
            normalizedAligned.Should().Contain(@"\end{align}");
            normalizedAligned.Should().NotContain(@"&u_1 + ${");
            normalizedAligned.Should().Contain(@"&u_1 + \left(u_1 + 4d\right) = 18");
            normalizedAligned.Should().StartWith("${");
            normalizedAligned.Should().EndWith("}$");
        }

        [Fact]
        public void ExportExamToDocx_StandardThptStructure_ShouldGenerateValidDocx()
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
                    CorrectAnswer = "B",
                    Explanation = @"Ta có $2^x = 4 = 2^2 \Leftrightarrow x = 2$."
                }
            };

            var options = new ExamExportOptions
            {
                Subject = "Toán",
                Grade = "12",
                ExamTitle = "KỲ THI TỐT NGHIỆP THPT",
                SchoolName = "SỞ GIÁO DỤC VÀ ĐÀO TẠO",
                ExamYear = "2025-2026",
                TimeMinutes = "90",
                ExamCode = "101",
                IncludeSolution = true,
                HighlightFormulas = true,
                ConvertTablesToWordGrid = true
            };

            string tempPath = Path.Combine(Path.GetTempPath(), $"TestExamExport_{Guid.NewGuid():N}.docx");
            try
            {
                exporter.ExportExamToDocx(tempPath, questions, options);
                File.Exists(tempPath).Should().BeTrue();
                new FileInfo(tempPath).Length.Should().BeGreaterThan(1000);
            }
            finally
            {
                if (File.Exists(tempPath)) File.Delete(tempPath);
            }
        }

        [Fact]
        public void XamlViews_ConvertViewAndExpandedWindow_ShouldInitializeCleanly()
        {
            Exception? error = null;
            var thread = new System.Threading.Thread(() =>
            {
                try
                {
                    var cv = new MatrixExamAI.Desktop.Views.ConvertView();
                    cv.Should().NotBeNull();
                    var ew = new MatrixExamAI.Desktop.Views.ExpandedPreviewWindow(new List<QuestionItem>(), "test");
                    ew.Should().NotBeNull();
                }
                catch (Exception ex)
                {
                    error = ex;
                }
            });
            thread.SetApartmentState(System.Threading.ApartmentState.STA);
            thread.Start();
            thread.Join();

            error.Should().BeNull();
        }

        [Fact]
        public void XamlViews_MainWindow_ShouldInitializeCleanlyAndSupportNavigation()
        {
            Exception? error = null;
            var thread = new System.Threading.Thread(() =>
            {
                try
                {
                    var win = new MatrixExamAI.Desktop.MainWindow();
                    win.Should().NotBeNull();
                    win.NavigateTo("convert");
                    win.NavigateTo("dashboard");
                }
                catch (Exception ex)
                {
                    error = ex;
                }
            });
            thread.SetApartmentState(System.Threading.ApartmentState.STA);
            thread.Start();
            thread.Join();

            error.Should().BeNull();
        }

        [Fact]
        public void WordExport_KT15P1_Parity_GeneratesQuickAnswerSheetAndTabbedOptionsWithoutBorders()
        {
            // Arrange
            string docxPath = Path.Combine(_tempDir, "kt15p1_parity_export.docx");
            var questions = new List<QuestionItem>
            {
                new QuestionItem
                {
                    Content = "Tìm tập nghiệm của phương trình $x^2 - 4 = 0$.",
                    QuestionType = "MultipleChoice4",
                    CorrectAnswer = "A",
                    Options = new Dictionary<string, string>
                    {
                        { "A", "$S = \\{-2; 2\\}$." },
                        { "B", "$S = \\{2\\}$." },
                        { "C", "$S = \\{-2\\}$." },
                        { "D", "$S = \\emptyset$." }
                    },
                    Explanation = "Phương trình tương đương $x = 2$ hoặc $x = -2$."
                },
                new QuestionItem
                {
                    Content = "Giá trị lớn nhất của hàm số $y = -x^2 + 2x$ trên $\\mathbb{R}$ bằng:",
                    QuestionType = "MultipleChoice4",
                    CorrectAnswer = "C",
                    Options = new Dictionary<string, string>
                    {
                        { "A", "$0$." },
                        { "B", "$-1$." },
                        { "C", "$1$." },
                        { "D", "$2$." }
                    },
                    Explanation = "Đỉnh parabol $I(1; 1)$ có tung độ $y = 1$."
                }
            };

            var options = new ExamExportOptions
            {
                SchoolName = "SỞ GD&ĐT HÀ NỘI",
                ExamTitle = "ĐỀ KIỂM TRA 15 PHÚT",
                Subject = "TOÁN",
                Grade = "10",
                ExamYear = "2024-2025",
                TimeMinutes = "15",
                ExamCode = "101",
                IncludeSolution = true
            };

            // Act
            var exportService = new WordExportService();
            exportService.ExportExamToDocx(docxPath, questions, options);

            // Assert
            File.Exists(docxPath).Should().BeTrue();
            using var doc = WordprocessingDocument.Open(docxPath, false);
            var body = doc.MainDocumentPart!.Document.Body!;
            var tables = body.Elements<Table>().ToList();

            // 1. Should have at least 3 tables:
            // Table 0: Header (2 cols, no borders)
            // Table 1: Quick answer sheet for students (bordered)
            // Table 2: Answer key at the end (bordered)
            tables.Count.Should().BeGreaterOrEqualTo(3, "Must have Header Table, Student Quick Answer Sheet, and Answer Key Table");

            // 2. Table 0 (Header): No borders
            var headerTable = tables[0];
            var headerBorders = headerTable.GetFirstChild<TableProperties>()?.GetFirstChild<TableBorders>();
            headerBorders?.TopBorder?.Val?.Value.Should().Be(BorderValues.None);

            // 3. Table 1 (Quick answer sheet): Bordered, contains "Câu" và "Đáp án"
            var studentSheet = tables[1];
            studentSheet.InnerText.Should().Contain("Câu");
            studentSheet.InnerText.Should().Contain("Đáp án");

            // 4. Candidate line: Paragraph with "Họ và tên:" and "Mã đề 101"
            var paragraphs = body.Elements<Paragraph>().ToList();
            paragraphs.Any(p => p.InnerText.Contains("Họ và tên:") && p.InnerText.Contains("Mã đề 101")).Should().BeTrue();

            // 5. Options formatting: Must be paragraphs with TabStops, NOT table cells
            var optionParagraphs = paragraphs.Where(p => p.InnerText.Contains("A.") && p.InnerText.Contains("B.")).ToList();
            optionParagraphs.Count.Should().BeGreaterThan(0, "4-choice options must be formatted in a paragraph");
            optionParagraphs.All(p => p.ParagraphProperties?.Tabs != null).Should().BeTrue("Options paragraphs must define tab stops for alignment without table borders");

            // 6. Answer key table at the end (under ĐÁP ÁN THAM KHẢO)
            paragraphs.Any(p => p.InnerText.Contains("ĐÁP ÁN THAM KHẢO")).Should().BeTrue();
            var answerKeyTable = tables[2];
            answerKeyTable.InnerText.Should().Contain("Câu");
            answerKeyTable.InnerText.Should().Contain("Đáp án");
        }

        [Fact]
        public void WordExportService_GenerateHtmlExam_GeneratesCompleteExamStructureForClipboard()
        {
            var questions = new List<QuestionItem>
            {
                new QuestionItem
                {
                    QuestionCode = "Q1",
                    Content = "Tìm tập xác định của hàm số $y = \\sqrt{x - 2}$.",
                    QuestionType = "MultipleChoice4",
                    Options = new Dictionary<string, string>
                    {
                        { "A", "$[2; +\\infty)$" },
                        { "B", "$(2; +\\infty)$" },
                        { "C", "$(-\\infty; 2]$" },
                        { "D", "$\\mathbb{R} \\setminus \\{2\\}$" }
                    },
                    CorrectAnswer = "A"
                }
            };

            var options = new ExamExportOptions
            {
                SchoolName = "SỞ GIÁO DỤC VÀ ĐÀO TẠO",
                ExamTitle = "KỲ THI TỐT NGHIỆP THPT",
                Subject = "TOÁN",
                Grade = "12",
                ExamCode = "101",
                IncludeSolution = true
            };

            string html = WordExportService.GenerateHtmlExam(questions, options);

            html.Should().NotBeNullOrWhiteSpace();
            html.Should().Contain("SỞ GIÁO DỤC VÀ ĐÀO TẠO");
            html.Should().Contain("KỲ THI TỐT NGHIỆP THPT");
            html.Should().Contain("Mã đề: 101");
            html.Should().Contain("PHẦN I.");
            html.Should().Contain("Câu");
            html.Should().Contain("Đáp án");
            html.Should().Contain("<table");
            html.Should().Contain("ĐÁP ÁN THAM KHẢO");
        }

        [Fact]
        public void QuestionParserEngine_NaturalHeader_ParsesMetadataAndQuestionsCorrectly()
        {
            // Arrange
            string rawExam = @"% Câu 1 [Nhận biết]_[Hàm số bậc hai]
Cho hàm số $y = ax^2 + bx + c$. Mệnh đề nào sau đây đúng?
A. Hàm số đồng biến trên $\mathbb{R}$.
B. Hàm số nghịch biến trên $\mathbb{R}$.
C. Hàm số có đỉnh parabol.
D. Đồ thị là đường thẳng.
Lời giải:
Đồ thị hàm số bậc hai luôn là một đường parabol. Chọn C.

% Câu 2 [Thông hiểu]_[Bất phương trình]
Giải bất phương trình $x - 1 > 0$.
A. $x > 1$.
B. $x < 1$.
C. $x > -1$.
D. $x < -1$.";

            // Act
            var result = QuestionParserEngine.ParseQuestions(rawExam);
            var parsedQuestions = result.Questions;

            // Assert
            parsedQuestions.Count.Should().Be(2, "Both natural % Câu N headers must be parsed as distinct questions");

            var q1 = parsedQuestions[0];
            q1.CognitiveLevel.Should().Be("Nhận biết");
            q1.Topic.Should().Be("Hàm số bậc hai");
            q1.Options.Should().ContainKey("A");
            q1.Options.Should().ContainKey("B");
            q1.Options.Should().ContainKey("C");
            q1.Options.Should().ContainKey("D");
            q1.Explanation.Should().Contain("parabol");

            var q2 = parsedQuestions[1];
            q2.CognitiveLevel.Should().Be("Thông hiểu");
            q2.Topic.Should().Be("Bất phương trình");
        }

        [Fact]
        public void SystemEquationNormalization_AlignedToAlignAndRemovesNestedDollarSigns()
        {
            // Arrange
            string inputWithAligned = @"$
\left\{
\begin{aligned}
&u_1 + ${\left(u_1 + 4d\right)}$ = 18 \\
&${\left(u_1 + 2d\right)}$ + ${\left(u_1 + 6d\right)}$ = 26
\end{aligned}
\right.
$";

            // Act
            string normalized = QuestionParserEngine.NormalizeSystemEquationsAndAlign(inputWithAligned);

            // Assert
            normalized.Should().NotContain("aligned", "aligned environment must be standardized to align");
            normalized.Should().Contain(@"\begin{align}", "Must contain \\begin{align}");
            normalized.Should().Contain(@"\end{align}", "Must contain \\end{align}");
            normalized.Should().NotContain(@"${\left(", "Nested ${...}$ inside math equation must be unwrapped cleanly");
        }

        [Fact]
        public void FilterLatexItems_TrueFalseItemChoiceAndInlineItems_FormatsToCleanAlphabeticalSubItems()
        {
            // Case 1: \begin{itemchoice} \itemch ... \end{itemchoice}
            string itemChoiceInput = @"\begin{itemchoice}
\itemch Đúng. Ta có $u_1 = 2$.
\itemch Đúng. Công sai $d = 3$.
\itemch Sai. Ta có $u_{10} = 29$.
\itemch Đúng. Tổng $S_{10} = 155$.
\end{itemchoice}";

            string res1 = QuestionParserEngine.FilterLatexItems(itemChoiceInput);
            res1.Should().Contain("a) Đúng. Ta có $u_1 = 2$.");
            res1.Should().Contain("b) Đúng. Công sai $d = 3$.");
            res1.Should().Contain("c) Sai. Ta có $u_{10} = 29$.");
            res1.Should().Contain("d) Đúng. Tổng $S_{10} = 155$.");
            res1.Should().NotContain(@"\itemch");
            res1.Should().NotContain(@"\begin{itemchoice}");

            // Case 2: Inline \item Đúng. ... \item Sai. ...
            string inlineInput = @"\item Đúng. Hàm số liên tục trên [0; 2]. \item Sai. Điểm cực đại là 3. \item Đúng. Đạo hàm dương. \item Sai. Cắt trục hoành tại 2 điểm.";
            string res2 = QuestionParserEngine.FilterLatexItems(inlineInput);
            res2.Should().Contain("a) Đúng. Hàm số liên tục trên [0; 2].");
            res2.Should().Contain("b) Sai. Điểm cực đại là 3.");
            res2.Should().Contain("c) Đúng. Đạo hàm dương.");
            res2.Should().Contain("d) Sai. Cắt trục hoành tại 2 điểm.");
            res2.Should().NotContain(@"\item");

            // Case 3: Stuck items: \item1. và \itema) và \itemĐúng
            string stuckInput = @"\item1. Bước 1: Tìm TXĐ. \item2. Bước 2: Khảo sát.";
            string res3 = QuestionParserEngine.FilterLatexItems(stuckInput);
            res3.Should().Contain("1. Bước 1: Tìm TXĐ.");
            res3.Should().Contain("2. Bước 2: Khảo sát.");
            res3.Should().NotContain(@"\item");

            // Case 4: Bracket items: \item[a)] Đúng. \item[b)] Sai.
            string bracketInput = @"\item[a)] Đúng. \item[b)] Sai. \item[c)] Đúng. \item[d)] Sai.";
            string res4 = QuestionParserEngine.FilterLatexItems(bracketInput);
            res4.Should().Contain("a) Đúng.");
            res4.Should().Contain("b) Sai.");
            res4.Should().Contain("c) Đúng.");
            res4.Should().Contain("d) Sai.");
            res4.Should().NotContain(@"\item");
        }

        [Fact]
        public void WordExport_CreateFormattedParagraph_BoldsOnlyPrefixLabelNotFollowingContent()
        {
            var options = new WordExportOptions { FontFamily = "Times New Roman", FontSizePt = "24" };

            // 1. "Lời giải: Thay n = 3 vào biểu thức" -> CHỈ "Lời giải: " in đậm
            string solLine = "Lời giải: Thay ${n = 3}$ vào biểu thức ta được kết quả.";
            // Gọi reflection hoặc export gián tiếp qua ExportToDocx
            string tmpDocx = Path.Combine(Path.GetTempPath(), $"Test_BoldPrefix_{Guid.NewGuid():N}.docx");
            try
            {
                var exporter = new WordExportService();
                exporter.ExportToDocx(tmpDocx, solLine, options);

                using var doc = WordprocessingDocument.Open(tmpDocx, false);
                var body = doc.MainDocumentPart!.Document.Body!;
                var para = body.Elements<Paragraph>().FirstOrDefault(p => p.InnerText.Contains("Lời giải:"));
                para.Should().NotBeNull();

                var runs = para!.Elements<Run>().ToList();
                runs.Count.Should().BeGreaterOrEqualTo(2);

                // Run đầu tiên chứa "Lời giải: " phải IN ĐẬM
                var run0 = runs[0];
                run0.InnerText.Should().Be("Lời giải: ");
                run0.RunProperties?.Bold.Should().NotBeNull();

                // Run tiếp theo chứa "Thay " tuyệt đối KHÔNG ĐƯỢC IN ĐẬM (Khắc phục bug media_1791893578717_f4e4240b.png)
                var run1 = runs[1];
                run1.InnerText.Should().Be("Thay ");
                run1.RunProperties?.Bold.Should().BeNull("Nội dung sau nhãn tiêu đề tuyệt đối không được in đậm!");
            }
            finally
            {
                if (File.Exists(tmpDocx)) File.Delete(tmpDocx);
            }
        }

        [Fact]
        public void WordExport_DocDefaultsAndStyles_StrictlyUsesTimesNewRomanForAllScriptTypes()
        {
            string tmpDocx = Path.Combine(Path.GetTempPath(), $"Test_TNRStyles_{Guid.NewGuid():N}.docx");
            try
            {
                var exporter = new WordExportService();
                exporter.ExportToDocx(tmpDocx, "Câu 1. Cho hàm số ${f(x) = x^2}$.", new WordExportOptions { FontFamily = "Times New Roman" });

                using var doc = WordprocessingDocument.Open(tmpDocx, false);
                var stylesPart = doc.MainDocumentPart!.StyleDefinitionsPart;
                stylesPart.Should().NotBeNull("Tài liệu Word phải có StyleDefinitionsPart để đảm bảo định dạng font nhất quán");

                var docDefaults = stylesPart!.Styles!.Elements<DocDefaults>().FirstOrDefault();
                docDefaults.Should().NotBeNull("Tài liệu Word phải có DocDefaults");

                var rFonts = docDefaults!.RunPropertiesDefault?.RunPropertiesBaseStyle?.Elements<RunFonts>().FirstOrDefault();
                rFonts.Should().NotBeNull();
                rFonts!.Ascii?.Value.Should().Be("Times New Roman");
                rFonts.HighAnsi?.Value.Should().Be("Times New Roman");
                rFonts.EastAsia?.Value.Should().Be("Times New Roman");
                rFonts.ComplexScript?.Value.Should().Be("Times New Roman");

                // Normal Style
                var normalStyle = stylesPart.Styles.Elements<Style>().FirstOrDefault(s => s.StyleId == "Normal");
                normalStyle.Should().NotBeNull("Tài liệu Word phải có Normal style");
                var normalFonts = normalStyle!.StyleRunProperties?.Elements<RunFonts>().FirstOrDefault();
                normalFonts.Should().NotBeNull();
                normalFonts!.Ascii?.Value.Should().Be("Times New Roman");
                normalFonts.EastAsia?.Value.Should().Be("Times New Roman");
            }
            finally
            {
                if (File.Exists(tmpDocx)) File.Delete(tmpDocx);
            }
        }

        [Fact]
        public void ExportToDocx_MarkdownTableOptions_ShouldConvertOptionsToTabbedParagraphsAndNotWordTable()
        {
            string tmpDocx = Path.Combine(Path.GetTempPath(), $"Test_TabOptions_Markdown_{Guid.NewGuid():N}.docx");
            try
            {
                var exporter = new WordExportService();
                string content = @"Câu 1. Cho hàm số ${y = f(x)}$.
| A. ${5/4}$ | B. ${3/4}$ | C. ${1/2}$ | D. ${1}$ |";

                exporter.ExportToDocx(tmpDocx, content, new WordExportOptions { ConvertTablesToWordGrid = true, FontFamily = "Times New Roman" });

                using var doc = WordprocessingDocument.Open(tmpDocx, false);
                var body = doc.MainDocumentPart!.Document.Body!;

                // 1. Phải KHÔNG CÓ bất kỳ Table nào được tạo cho các phương án trắc nghiệm
                var tables = body.Elements<Table>().ToList();
                tables.Count.Should().Be(0, "Phương án trắc nghiệm phải dùng cấu trúc Tab, tuyệt đối không được bọc trong Word Table Grid");

                // 2. Phương án phải được định dạng trong 1 Paragraph với Tab Stops
                var optionPara = body.Elements<Paragraph>().FirstOrDefault(p => p.InnerText.Contains("A.") && p.InnerText.Contains("B."));
                optionPara.Should().NotBeNull("Phương án A, B, C, D phải nằm trong đoạn văn có tab");
                optionPara!.ParagraphProperties?.Tabs.Should().NotBeNull("Đoạn văn phương án phải có cấu trúc Tab Stops");
                
                var tabs = optionPara.ParagraphProperties!.Tabs!.Elements<TabStop>().ToList();
                tabs.Count.Should().Be(3, "4 phương án trên 1 dòng phải có đúng 3 điểm dừng TabStop (5.0cm, 9.5cm, 14.0cm)");
                tabs[0].Position!.Value.Should().Be(2835);
                tabs[1].Position!.Value.Should().Be(5386);
                tabs[2].Position!.Value.Should().Be(7937);

                // 3. Phải có ký tự TabChar (<w:tab/>) ngăn cách giữa các phương án
                var tabChars = optionPara.Descendants<TabChar>().ToList();
                tabChars.Count.Should().Be(3, "Phải có đúng 3 thẻ <w:tab/> ngăn cách giữa A, B, C, D");

                // 4. Nhãn A., B., C., D. phải in đậm
                var boldRuns = optionPara.Elements<Run>().Where(r => r.RunProperties?.Bold != null).Select(r => r.InnerText).ToList();
                boldRuns.Should().Contain(r => r.Contains("A."));
                boldRuns.Should().Contain(r => r.Contains("B."));
                boldRuns.Should().Contain(r => r.Contains("C."));
                boldRuns.Should().Contain(r => r.Contains("D."));
            }
            finally
            {
                if (File.Exists(tmpDocx)) File.Delete(tmpDocx);
            }
        }

        [Fact]
        public void ExportToDocx_TabSeparatedOptions_ShouldCreateTabStopsWithIndentation()
        {
            string tmpDocx = Path.Combine(Path.GetTempPath(), $"Test_TabOptions_Tabs_{Guid.NewGuid():N}.docx");
            try
            {
                var exporter = new WordExportService();
                string content = "Câu 2. Cho cấp số cộng:\nA. 1\tB. -6\tC. 5\tD. -1";

                exporter.ExportToDocx(tmpDocx, content, new WordExportOptions { FontFamily = "Times New Roman" });

                using var doc = WordprocessingDocument.Open(tmpDocx, false);
                var body = doc.MainDocumentPart!.Document.Body!;

                var optionPara = body.Elements<Paragraph>().FirstOrDefault(p => p.InnerText.Contains("A. 1"));
                optionPara.Should().NotBeNull();
                optionPara!.ParagraphProperties?.Indentation?.Left?.Value.Should().Be("283", "Thụt lề phương án chuẩn 0.5cm (283 twips)");
                optionPara.ParagraphProperties?.Tabs.Should().NotBeNull();
                optionPara.Descendants<TabChar>().Count().Should().Be(3);
            }
            finally
            {
                if (File.Exists(tmpDocx)) File.Delete(tmpDocx);
            }
        }

        [Fact]
        public void WordExportService_QuestionWithImage_ShouldEmbedImagePartIntoDocument()
        {
            string tmpDocx = Path.Combine(Path.GetTempPath(), $"Test_ImageEmbed_{Guid.NewGuid():N}.docx");
            try
            {
                var exporter = new WordExportService();
                
                // 1x1 transparent PNG base64
                string tinyPngBase64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==";

                var questions = new List<QuestionItem>
                {
                    new QuestionItem
                    {
                        QuestionType = "MultipleChoice4",
                        Content = "Cho đồ thị hàm số như hình vẽ sau:",
                        Options = new Dictionary<string, string>
                        {
                            ["A"] = "y = x^2",
                            ["B"] = "y = x^3",
                            ["C"] = "y = 2x",
                            ["D"] = "y = 1/x"
                        },
                        Images = new List<string> { tinyPngBase64 }
                    }
                };

                exporter.ExportExamToDocx(tmpDocx, questions, new ExamExportOptions { FontFamily = "Times New Roman" });

                using var doc = WordprocessingDocument.Open(tmpDocx, false);
                doc.MainDocumentPart!.ImageParts.Count().Should().BeGreaterOrEqualTo(1, "Document must have at least 1 embedded image part");
            }
            finally
            {
                if (File.Exists(tmpDocx)) File.Delete(tmpDocx);
            }
        }

        [Fact]
        public void ConvertService_LatexChoiceWithNestedFractions_ShouldNotSplitOptions()
        {
            string latexInput = @"\begin{ex}
Giá trị của biểu thức $P$ là
\choice
{\True $\dfrac{5}{4}$}
{$\dfrac{1}{2}$}
{$\dfrac{3}{4}$}
{$\dfrac{7}{4}$}
\loigiai{
Ta tính được $P = \dfrac{5}{4}$.
}
\end{ex}";

            var result = QuestionParserEngine.ParseQuestions(latexInput, "Toán", 12);
            result.TotalCount.Should().Be(1);

            var q = result.Questions[0];
            q.CorrectAnswer.Should().Be("A");
            q.Options.Should().ContainKey("A");
            q.Options["A"].Should().Contain(@"\dfrac{5}{4}");
            q.Options["A"].Should().NotBe(@"\dfrac{5");
            q.Options["B"].Should().Contain(@"\dfrac{1}{2}");
            q.Options["B"].Should().NotBe("4}");
            q.Options["C"].Should().Contain(@"\dfrac{3}{4}");
            q.Options["D"].Should().Contain(@"\dfrac{7}{4}");
        }

        [Fact]
        public void ExportExamToDocx_QuestionWithImage_ShouldRenderTwoColumnBorderlessTable()
        {
            var exporter = new WordExportService();
            string tmpDocx = Path.Combine(Path.GetTempPath(), $"MEA_TwoCol_{Guid.NewGuid():N}.docx");
            try
            {
                string tinyPngBase64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==";
                var questions = new List<QuestionItem>
                {
                    new QuestionItem
                    {
                        QuestionType = "MultipleChoice4",
                        Content = "Đồ thị hàm số như hình vẽ bên:",
                        Options = new Dictionary<string, string>
                        {
                            ["A"] = "y = x",
                            ["B"] = "y = 2x",
                            ["C"] = "y = 3x",
                            ["D"] = "y = 4x"
                        },
                        Images = new List<string> { tinyPngBase64 }
                    }
                };

                exporter.ExportExamToDocx(tmpDocx, questions, new ExamExportOptions());

                using var doc = WordprocessingDocument.Open(tmpDocx, false);
                var body = doc.MainDocumentPart!.Document.Body!;
                var tables = body.Descendants<Table>().ToList();

                // Phải có bảng 2 cột không viền cho câu hỏi có hình
                var questionTable = tables.FirstOrDefault(t => t.InnerText.Contains("Đồ thị hàm số như hình vẽ bên"));

                questionTable.Should().NotBeNull("Câu hỏi có hình phải được dàn dạng bảng 2 cột không viền");
                var cells = questionTable!.Elements<TableRow>().First().Elements<TableCell>().ToList();
                cells[0].InnerText.Should().Contain("Đồ thị hàm số như hình vẽ bên");
                cells[1].Descendants<DocumentFormat.OpenXml.Drawing.Wordprocessing.Inline>().Should().NotBeEmpty("Cột 2 phải chứa hình ảnh");
            }
            finally
            {
                if (File.Exists(tmpDocx)) File.Delete(tmpDocx);
            }
        }

        [Fact]
        public void FormatWordReadyText_StandardHighSchoolExamFormat_ShouldIncludeHeadersSectionsAndAnswersAtBottom()
        {
            var questions = new List<QuestionItem>
            {
                new QuestionItem
                {
                    QuestionType = "MultipleChoice4",
                    Content = "Nghiệm của phương trình $2^x = 4$ là",
                    Options = new Dictionary<string, string>
                    {
                        ["A"] = "x = 1",
                        ["B"] = "x = 2",
                        ["C"] = "x = 3",
                        ["D"] = "x = 4"
                    },
                    CorrectAnswer = "B",
                    Explanation = "Ta có $2^x = 4 = 2^2 \\Leftrightarrow x = 2$."
                }
            };

            string formatted = QuestionParserEngine.FormatWordReadyText(questions);

            // Kiểm tra Tiêu đề đề thi
            formatted.Should().Contain("SỞ GIÁO DỤC VÀ ĐÀO TẠO");
            formatted.Should().Contain("ĐỀ KIỂM TRA CHÍNH THỨC");
            formatted.Should().Contain("Mã đề 101");

            // Kiểm tra phân nhóm phần
            formatted.Should().Contain("PHẦN I. Thí sinh trả lời từ câu 1 đến câu 1.");
            formatted.Should().Contain("Câu 1.");

            // Kiểm tra kết thúc đề
            formatted.Should().Contain("-------------------- HẾT --------------------");

            // Kiểm tra Bảng đáp án và Lời giải ở cuối đề
            formatted.Should().Contain("BẢNG ĐÁP ÁN");
            formatted.Should().Contain("1.B");
            formatted.Should().Contain("HƯỚNG DẪN GIẢI CHI TIẾT");
            formatted.Should().Contain("Đáp án: B");
            formatted.Should().Contain("Lời giải:");
        }

        [Fact]
        public void ParseQuestions_NaturalText_WithArrowAnswerAndSplitFractions_ShouldParseCorrectly()
        {
            string raw = @"Câu 1. Cho dãy số $\left(u_n\right)$ có số hạng tổng quát $u_n = \dfrac{2n - 1}{n + 1}$ với mọi $n \ge 1$. Số hạng thứ ba $u_3$ của dãy số bằng
A. $\dfrac{5
B. 4}$
C. $\dfrac{3
D. 4
-> Đáp án: A
Lời giải:
Thay $n = 3$ vào công thức số hạng tổng quát, ta được:
$u_3 = \dfrac{2 \cdot 3 - 1}{3 + 1} = \dfrac{5}{4}$.";

            var result = QuestionParserEngine.ParseQuestions(raw);
            result.Should().NotBeNull();
            result.Questions.Should().HaveCount(1);

            var q = result.Questions[0];
            q.CorrectAnswer.Should().Be("A");
            q.Content.Should().NotContain("-> Đáp án");
            q.Explanation.Should().Contain("Thay");
            q.Options.Should().ContainKey("A");
            q.Options["A"].Should().Contain("5}{4");
        }

        #endregion
    }
}
