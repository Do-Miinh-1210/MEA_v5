using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.RegularExpressions;
using FluentAssertions;
using MatrixExamAI.Desktop.Services;
using MatrixExamAI.Desktop.Views;
using MatrixExamAI.Shared.Extensibility;
using Xunit;

namespace MatrixExamAI.Desktop.Tests
{
    /// <summary>
    /// Bộ kiểm thử Milestone 2 — Yêu cầu R2:
    /// 1. Chuẩn hóa hệ phương trình và align: \begin{aligned} -> \begin{align} và tháo bỏ dấu $ lồng nhau.
    /// 2. Kẹp chuẩn công thức ${...}$ và bảo vệ tuyệt đối dấu trị tuyệt đối |x| trong bảng Markdown.
    /// 3. Lọc \item thông minh: tháo bọc môi trường, tách số dính liền, cấu trúc 4 ý a), b), c), d) và xóa in đậm đầu phương án.
    /// 4. Chuẩn hóa mẫu AI Prompt ex_test tương thích 100% với core/latex_parser.py (luật vàng % Câu STT [Mức độ]_[Chủ đề]).
    /// </summary>
    public class Milestone2Requirement2MathTests
    {
        #region Task 1: System Equations and Align Normalization

        [Fact]
        public void NormalizeSystemEquationsAndAlign_StandaloneAligned_ConvertsToAlignAndCleansInnerDollars()
        {
            // Arrange: Hệ phương trình độc lập dạng \begin{aligned} ... \end{aligned} chứa $ lồng sai
            string input = @"
\begin{aligned}
&2x + $3y$ = 5 \\
&${4x}$ - 5y = -1
\end{aligned}";

            // Act
            string normalized = QuestionParserEngine.NormalizeSystemEquationsAndAlign(input);

            // Assert
            normalized.Should().NotContain("aligned", "Môi trường aligned phải được chuẩn hóa thành align");
            normalized.Should().Contain(@"\begin{align}");
            normalized.Should().Contain(@"\end{align}");
            normalized.Should().NotContain("$3y$");
            normalized.Should().NotContain("${4x}$");
            normalized.Should().Contain("&2x + 3y = 5");
            normalized.Should().Contain("&4x - 5y = -1");
        }

        [Fact]
        public void NormalizeSystemEquationsAndAlign_LeftBraceAligned_PreservesLeftBraceAndConvertsToAlign()
        {
            // Arrange: Hệ phương trình có \left\{ \begin{aligned} ... \end{aligned} \right.
            string input = @"\left\{
\begin{aligned}
&u_1 + u_2 = 10 \\
&u_3 - u_1 = 6
\end{aligned}
\right.";

            // Act
            string normalized = QuestionParserEngine.NormalizeSystemEquationsAndAlign(input);

            // Assert
            normalized.Should().NotContain("aligned");
            normalized.Should().Contain(@"\left\{");
            normalized.Should().Contain(@"\begin{align}");
            normalized.Should().Contain(@"\end{align}");
            normalized.Should().Contain(@"\right.");
        }

        [Fact]
        public void NormalizeSystemEquationsAndAlign_AlignedAsterisk_ConvertsToAlign()
        {
            // Arrange: Môi trường có dấu sao \begin{aligned*} ... \end{aligned*}
            string input = @"\begin{aligned*}
x + 2y &= 4 \\
3x - y &= 5
\end{aligned*}";

            // Act
            string normalized = QuestionParserEngine.NormalizeSystemEquationsAndAlign(input);

            // Assert
            normalized.Should().NotContain("aligned*");
            normalized.Should().NotContain("aligned");
            normalized.Should().Contain(@"\begin{align}");
            normalized.Should().Contain(@"\end{align}");
        }

        [Fact]
        public void NormalizeSystemEquationsAndAlign_MultipleSystemsInText_ConvertsAllCorrectly()
        {
            // Arrange: Nhiều hệ phương trình nối tiếp nhau qua \Leftrightarrow
            string input = @"\left\{ \begin{aligned} x + y = 2 \\ x - y = 0 \end{aligned} \right. \Leftrightarrow \left\{ \begin{aligned} 2x = 2 \\ y = x \end{aligned} \right.";

            // Act
            string normalized = QuestionParserEngine.NormalizeSystemEquationsAndAlign(input);

            // Assert
            normalized.Should().NotContain("aligned");
            int beginAlignCount = Regex.Matches(normalized, @"\\begin\{align\}").Count;
            int endAlignCount = Regex.Matches(normalized, @"\\end\{align\}").Count;
            beginAlignCount.Should().Be(2, "Cả hai hệ đều phải chuyển sang begin{align}");
            endAlignCount.Should().Be(2, "Cả hai hệ đều phải có end{align}");
        }

        #endregion

        #region Task 2: Braced Dollar Wrapping & Absolute Value Protection

        [Fact]
        public void NormalizeMathToBracedDollars_InlineAndBlockMath_WrapsAllFormulasInBracedDollars()
        {
            // Arrange: Đa dạng các loại công thức LaTeX
            string input = @"Cho phương trình $x + 1 = 0$, biểu thức block $$x^2 - 4 = 0$$, phân số \[\frac{a}{b}\] và góc \(\alpha = 30^\circ\).";

            // Act
            string normalized = QuestionParserEngine.NormalizeMathToBracedDollars(input, protectAbs: true);

            // Assert
            normalized.Should().Contain("${x + 1 = 0}$");
            normalized.Should().Contain("${x^2 - 4 = 0}$");
            normalized.Should().Contain(@"${\frac{a}{b}}$");
            normalized.Should().Contain(@"${\alpha = 30^\circ}$");
            normalized.Should().NotContain("$$");
            normalized.Should().NotContain(@"\[");
            normalized.Should().NotContain(@"\(");
        }

        [Fact]
        public void NormalizeMathToBracedDollars_ProtectAbs_PreventsMarkdownTablePipeDelimiterCorruption()
        {
            // Arrange: Bảng Markdown chứa dấu trị tuyệt đối |x| trong các ô
            string tableText = @"| STT | Biểu thức $|x - 2|$ | Kết quả $\left|x\right| \le 1$ |
| :--- | :--- | :--- |
| 1 | $|1 - 2| = 1$ | Sai |
| 2 | $|0 - 2| = 2$ | Đúng |";

            // Act: Gọi trực tiếp QuestionParserEngine.NormalizeMathToBracedDollars với protectAbs = true
            string normalized = QuestionParserEngine.NormalizeMathToBracedDollars(tableText, protectAbs: true);

            // Assert
            normalized.Should().Contain("${|x - 2|}$");
            normalized.Should().Contain(@"${\left|x\right| \le 1}$");
            normalized.Should().Contain("${|1 - 2| = 1}$");
            normalized.Should().Contain("${|0 - 2| = 2}$");

            var rows = normalized.Split(new[] { '\r', '\n' }, StringSplitOptions.RemoveEmptyEntries)
                                 .Where(r => r.Trim().StartsWith("|") && r.Trim().EndsWith("|"))
                                 .ToList();

            rows.Count.Should().Be(4, "Bảng phải có đúng 4 dòng");

            // Tách các ô trong từng dòng: Số cột phải luôn là 3, không bị xé nhỏ do dấu '|' của trị tuyệt đối
            for (int i = 0; i < rows.Count; i++)
            {
                var cells = WordExportService.SplitTableCells(rows[i]);
                cells.Count.Should().Be(3, $"Dòng {i + 1} phải có chính xác 3 cột, không bị ngắt bởi |x|");
            }
        }

        [Fact]
        public void NormalizeMathToBracedDollars_ProtectAbs_CanBeInvokedDirectlyWithoutConvertView()
        {
            // Arrange: Gọi hàm theo signature mặc định (protectAbs = true)
            string input = @"Tìm nghiệm của bất phương trình $|2x - 3| < 5$ và $|x| \ge 1$.";

            // Act
            string result = QuestionParserEngine.NormalizeMathToBracedDollars(input);

            // Assert
            result.Should().Contain("${|2x - 3| < 5}$");
            result.Should().Contain("${|x| \\ge 1}$");
            result.Should().NotContain("${{");
            result.Should().NotContain("}}$");
        }

        [Fact]
        public void NormalizeMathToBracedDollars_UnbracedLeftRightPipe_WrapsIntoBracedDollars()
        {
            // Arrange: Biểu thức \left|...\right| đứng ngoài dấu $
            string input = @"Giá trị tuyệt đối \left| x - 5 \right| đạt giá trị nhỏ nhất khi x = 5.";

            // Act
            string result = QuestionParserEngine.NormalizeMathToBracedDollars(input, protectAbs: true);

            // Assert
            result.Should().Contain(@"${\left| x - 5 \right|}$");
        }

        [Fact]
        public void NormalizeMathToBracedDollars_AbsoluteValueWithEquations_RetainsFormulaIntegrity()
        {
            // Arrange: Phương trình chứa nhiều dấu trị tuyệt đối
            string input = @"$|x| + |y| = 10$ và $\left|x + y\right| = 2$.";

            // Act
            string result = QuestionParserEngine.NormalizeMathToBracedDollars(input, protectAbs: true);

            // Assert
            result.Should().Contain("${|x| + |y| = 10}$");
            result.Should().Contain(@"${\left|x + y\right| = 2}$");
        }

        [Fact]
        public void NormalizeContent_ProtectAbsWithTableRows_MaintainsExactColumnCount()
        {
            // Arrange: Kiểm thử gián tiếp qua ConvertView.NormalizeContent
            string markdownTable = @"| Bước | Biểu thức $|x|$ | Điều kiện |
| :--- | :--- | :--- |
| 1 | $|x| = 3$ | $x = \pm 3$ |";

            // Act
            string output = ConvertView.NormalizeContent(markdownTable, braceMath: true, protectAbs: true);

            // Assert
            var rows = output.Split(new[] { '\r', '\n' }, StringSplitOptions.RemoveEmptyEntries)
                             .Where(r => r.Trim().StartsWith("|"))
                             .ToList();

            rows.Count.Should().Be(3);
            var headerCells = WordExportService.SplitTableCells(rows[0]);
            var dataCells = WordExportService.SplitTableCells(rows[2]);

            headerCells.Count.Should().Be(3);
            dataCells.Count.Should().Be(3);
            dataCells[1].Should().Contain("${|x| = 3}$");
        }

        #endregion

        #region Task 3: Smart \item Filtering

        [Fact]
        public void FilterLatexItems_UnwrapsAllListingEnvironments()
        {
            // Arrange: Chứa các môi trường itemize, enumerate, list, itemchoice
            string input = @"
\begin{itemize}
\item Ý 1
\end{itemize}
\begin{enumerate}
\item Ý 2
\end{enumerate}
\begin{list}{}{}
\item Ý 3
\end{list}";

            // Act
            string result = QuestionParserEngine.FilterLatexItems(input);

            // Assert
            result.Should().NotContain(@"\begin{itemize}");
            result.Should().NotContain(@"\end{itemize}");
            result.Should().NotContain(@"\begin{enumerate}");
            result.Should().NotContain(@"\end{enumerate}");
            result.Should().NotContain(@"\begin{list}");
            result.Should().NotContain(@"\end{list}");
            result.Should().NotContain(@"\item");
        }

        [Fact]
        public void FilterLatexItems_StuckLeadingNumbersAndLetters_SeparatesCleanly()
        {
            // Arrange: Thẻ \item bị dính liền số hoặc chữ tiếng Việt: \item1., \item2., \itema), \itemĐúng
            string input = @"
\item1. Bước 1: Khảo sát hàm số.
\item2. Bước 2: Tìm đường tiệm cận.
\itema) Mệnh đề thứ nhất đúng.
\itemĐúng. Mệnh đề thứ hai đúng.";

            // Act
            string result = QuestionParserEngine.FilterLatexItems(input);

            // Assert
            result.Should().NotContain(@"\item1.");
            result.Should().NotContain(@"\item2.");
            result.Should().NotContain(@"\itema)");
            result.Should().NotContain(@"\itemĐúng");
            result.Should().Contain("1. Bước 1: Khảo sát hàm số.");
            result.Should().Contain("2. Bước 2: Tìm đường tiệm cận.");
            result.Should().Contain("a) Mệnh đề thứ nhất đúng.");
            result.Should().Contain("Đúng. Mệnh đề thứ hai đúng.");
        }

        [Fact]
        public void FilterLatexItems_FourTrueFalseOptions_StructuresAsAlphabeticalAtoD()
        {
            // Arrange: 4 mệnh đề đúng sai trong bài thi
            string input = @"
\item Đúng. Hàm số $y = f(x)$ đồng biến trên $(0; 2)$.
\item Sai. Điểm cực đại của đồ thị hàm số là $(1; 3)$.
\item Đúng. Giá trị lớn nhất trên đoạn $[0; 3]$ bằng 5.
\item Sai. Đồ thị hàm số có hai đường tiệm cận ngang.";

            // Act
            string result = QuestionParserEngine.FilterLatexItems(input);

            // Assert
            result.Should().Contain("a) Đúng. Hàm số $y = f(x)$ đồng biến trên $(0; 2)$.");
            result.Should().Contain("b) Sai. Điểm cực đại của đồ thị hàm số là $(1; 3)$.");
            result.Should().Contain("c) Đúng. Giá trị lớn nhất trên đoạn $[0; 3]$ bằng 5.");
            result.Should().Contain("d) Sai. Đồ thị hàm số có hai đường tiệm cận ngang.");
            result.Should().NotContain(@"\item");
        }

        [Fact]
        public void FilterLatexItems_UnboldsOptionHeaders_RemovesLatexAndMarkdownBoldMarkup()
        {
            // Arrange: Các phương án có in đậm đầu dòng dạng \textbf{a)}, \textbf{Đúng.}, **a)**, **Đúng.**
            string input = @"
\item \textbf{a)} \textbf{Đúng.} Đồ thị cắt trục tung tại điểm $(0; 1)$.
\item \textbf{b)} \textbf{Sai.} Hàm số có 3 điểm cực trị.
\item **c)** **Đúng.** Tiếp tuyến có hệ số góc bằng 2.
\item[**d**] **Sai.** Phương trình có 4 nghiệm phân biệt.";

            // Act
            string result = QuestionParserEngine.FilterLatexItems(input);

            // Assert
            result.Should().Contain("a) Đúng. Đồ thị cắt trục tung tại điểm $(0; 1)$.");
            result.Should().Contain("b) Sai. Hàm số có 3 điểm cực trị.");
            result.Should().Contain("c) Đúng. Tiếp tuyến có hệ số góc bằng 2.");
            result.Should().Contain("d) Sai. Phương trình có 4 nghiệm phân biệt.");
            result.Should().NotContain(@"\textbf{a)}");
            result.Should().NotContain(@"\textbf{Đúng.}");
            result.Should().NotContain("**a)**");
            result.Should().NotContain("**Đúng.**");
            result.Should().NotContain(@"\item");
        }

        [Fact]
        public void FilterLatexItems_StuckLeadingDigitWithBold_FormatsCleanly()
        {
            // Arrange: \item\textbf{1.} Bước 1
            string input = @"\item\textbf{1.} Bước 1: Tính đạo hàm. \item\textbf{2.} Bước 2: Lập bảng biến thiên.";

            // Act
            string result = QuestionParserEngine.FilterLatexItems(input);

            // Assert
            result.Should().Contain("1. Bước 1: Tính đạo hàm.");
            result.Should().Contain("2. Bước 2: Lập bảng biến thiên.");
            result.Should().NotContain(@"\textbf");
            result.Should().NotContain(@"\item");
        }

        [Fact]
        public void FilterLatexItems_NoResidualItemTags_CompletelyEliminatesItemMarkers()
        {
            // Arrange: Hỗn hợp nhiều loại \item, \itemch, \item[...]
            string input = @"\item[A.] Phương án 1 \itemch Phương án 2 \item Phương án 3";

            // Act
            string result = QuestionParserEngine.FilterLatexItems(input);

            // Assert
            result.Should().NotContain(@"\item");
            result.Should().NotContain(@"\itemch");
        }

        #endregion

        #region Task 4: AI Prompt Template Alignment (ex_test & core/latex_parser.py compatibility)

        [Fact]
        public void ConvertView_GetExTestPromptTemplate_HeaderCommentImmediatelyPrecedesBeginEx()
        {
            // Act
            string prompt = ConvertView.GetExTestPromptTemplate("Toán", 12);

            // Assert
            prompt.Should().NotBeNullOrWhiteSpace();

            string normalizedPrompt = prompt.Replace("\r\n", "\n");

            // Luật vàng: comment % Câu STT [Mức độ]_[Chủ đề] nằm ở dòng riêng ngay trước \begin{ex}
            normalizedPrompt.Should().Contain("% Câu 1 [Nhận biết]_[Chủ đề bài học]\n\\begin{ex}");
            normalizedPrompt.Should().Contain("% Câu 2 [Thông hiểu]_[Chủ đề bài học]\n\\begin{ex}");
            normalizedPrompt.Should().Contain("% Câu 3 [Vận dụng]_[Chủ đề bài học]\n\\begin{ex}");
            normalizedPrompt.Should().Contain("% Câu 4 [Vận dụng cao]_[Chủ đề bài học]\n\\begin{bt}");

            // Tuyệt đối không được đặt comment cùng dòng: \begin{ex}%[Nhận biết]...
            prompt.Should().NotContain(@"\begin{ex}%");
            prompt.Should().NotContain(@"\begin{bt}%");
        }

        [Fact]
        public void ConvertView_GetExTestPromptTemplate_MatchesPythonLatexParserRegex()
        {
            // Act
            string prompt = ConvertView.GetExTestPromptTemplate("Toán", 12);

            // Regex đối chuẩn từ core/latex_parser.py dòng 54-57:
            // _HEADER_RE = re.compile(r'%\s*Câu\s*\d+\s*\[([^\]]*)\]_\[([^\]]*)\]\s*\n\s*\\begin\{(ex|bt|vd)\}', re.DOTALL)
            var pythonHeaderRegex = new Regex(
                @"%\s*Câu\s*\d+\s*\[([^\]]*)\]_\[([^\]]*)\]\s*\r?\n\s*\\begin\{(ex|bt|vd)\}",
                RegexOptions.Compiled);

            var matches = pythonHeaderRegex.Matches(prompt);

            // Assert
            matches.Count.Should().Be(4, "Mẫu prompt phải có đúng 4 câu ví dụ (TN, DS, TLN, TL) khớp hoàn hảo regex của parser Python");

            matches[0].Groups[1].Value.Trim().Should().Be("Nhận biết");
            matches[0].Groups[2].Value.Trim().Should().Be("Chủ đề bài học");
            matches[0].Groups[3].Value.Trim().Should().Be("ex");

            matches[1].Groups[1].Value.Trim().Should().Be("Thông hiểu");
            matches[1].Groups[2].Value.Trim().Should().Be("Chủ đề bài học");
            matches[1].Groups[3].Value.Trim().Should().Be("ex");

            matches[2].Groups[1].Value.Trim().Should().Be("Vận dụng");
            matches[2].Groups[2].Value.Trim().Should().Be("Chủ đề bài học");
            matches[2].Groups[3].Value.Trim().Should().Be("ex");

            matches[3].Groups[1].Value.Trim().Should().Be("Vận dụng cao");
            matches[3].Groups[2].Value.Trim().Should().Be("Chủ đề bài học");
            matches[3].Groups[3].Value.Trim().Should().Be("bt");
        }

        [Fact]
        public void ConvertView_GetExTestPromptTemplate_ContainsAllExTestQuestionTypesAndDirectives()
        {
            // Act
            string prompt = ConvertView.GetExTestPromptTemplate("Toán", 12);

            // Assert: Đầy đủ các cấu trúc ex_test chuẩn
            prompt.Should().Contain(@"\choice", "Phải có dạng trắc nghiệm 4 lựa chọn");
            prompt.Should().Contain(@"\choiceTF", "Phải có dạng Đúng/Sai 4 ý");
            prompt.Should().Contain(@"\shortans", "Phải có dạng trả lời ngắn");
            prompt.Should().Contain(@"\begin{bt}", "Phải có dạng tự luận bt");
            prompt.Should().Contain(@"\loigiai", "Phải có lời giải");
            prompt.Should().Contain(@"\True", "Phải có nhãn đáp án đúng");
            prompt.Should().Contain(@"\dfrac", "Phải khuyến khích dùng phân số dfrac");
            prompt.Should().Contain(@"\left\{", "Phải có hệ phương trình ngoặc nhọn");
            prompt.Should().Contain("LUẬT VÀNG", "Phải nhấn mạnh luật vàng cho AI");
        }

        [Fact]
        public void ConvertView_GetExTestPromptTemplate_InterpolatesSubjectAndGrade()
        {
            // Act
            string promptPhys = ConvertView.GetExTestPromptTemplate("Vật lí", 11);

            // Assert
            promptPhys.Should().Contain("môn Vật lí lớp 11");
            promptPhys.Should().Contain("cho môn Vật lí lớp 11.");
        }

        #endregion
    }
}
