using System;
using System.Linq;
using FluentAssertions;
using MatrixExamAI.Shared.Extensibility;
using Xunit;

namespace MatrixExamAI.Desktop.Tests
{
    public class AiVisionOcrParsingTests
    {
        private readonly ConvertService _convertService;

        public AiVisionOcrParsingTests()
        {
            _convertService = new ConvertService();
        }

        #region Tier 1 - Normative Tests (Structured OCR ===CAU===)

        [Fact]
        public void ParseExtractedQuestions_FullStructure_ShouldParseMetaAndAllQuestionTypesAccurately()
        {
            string aiResponse = @"META: {""subject"": ""Toán"", ""grade"": 12, ""topic"": ""Khảo sát hàm số""}

===CAU===
LOAI: TN
MUCDO: NB
CHUONG: Ứng dụng đạo hàm
NOIDUNG: Cho hàm số ${y = f(x)}$ có bảng biến thiên. Hàm số đồng biến trên khoảng nào?
A: $(1; +\infty)$
B: $(-\infty; 1)$
C: $(0; 2)$
D: $(-1; 1)$
DAPAN: A
LOIGIAI: Dựa vào bảng biến thiên, dấu của ${y'}$ dương trên ${(1; +\infty)}$.
===KETCAU===

===CAU===
LOAI: DS
MUCDO: TH
CHUONG: Hàm số phân thức
NOIDUNG: Cho hàm số ${y = \frac{2x+1}{x-1}}$. Xét tính đúng sai của các khẳng định sau:
a: Tập xác định của hàm số là $\mathbb{R} \setminus \{1\}$
b: Tiệm cận đứng của đồ thị là đường thẳng $x = 1$
c: Tiệm cận ngang của đồ thị là đường thẳng $y = 1$
d: Hàm số nghịch biến trên từng khoảng xác định
DAPAN: a:Đ, b:Đ, c:S, d:Đ
LOIGIAI: Tiệm cận ngang là $y = 2$, nên ý c sai.
===KETCAU===

===CAU===
LOAI: TLN
MUCDO: VD
CHUONG: Tối ưu hóa
NOIDUNG: Tìm giá trị lớn nhất của hàm số ${y = -x^2 + 4x + 5}$ trên đoạn $[0; 3]$.
DAPAN: 9
LOIGIAI: Tọa độ đỉnh parabol $x = 2 \in [0; 3] \Rightarrow y(2) = 9$.
===KETCAU===

===CAU===
LOAI: TL
MUCDO: VDC
CHUONG: Tương giao đồ thị
NOIDUNG: Tìm các giá trị thực của tham số $m$ để đồ thị cắt trục hoành tại 3 điểm phân biệt.
DAPAN: $m \in (-2; 2)$
LOIGIAI: Lập bảng biến thiên và biện luận số nghiệm.
===KETCAU===";

            // Act
            var result = ConvertService.ParseExtractedQuestions(aiResponse);

            // Assert Meta
            result.Subject.Should().Be("Toán");
            result.Grade.Should().Be(12);
            result.Topic.Should().Be("Khảo sát hàm số");
            result.Questions.Count.Should().Be(4);

            // Question 1: MCQ (TN)
            var q1 = result.Questions[0];
            q1.QuestionType.Should().Be("MultipleChoice4");
            q1.CognitiveLevel.Should().Be("Nhận biết");
            q1.Topic.Should().Be("Ứng dụng đạo hàm");
            q1.Options.Should().ContainKey("A").WhoseValue.Should().Be("$(1; +\\infty)$");
            q1.Options.Should().ContainKey("B");
            q1.Options.Should().ContainKey("C");
            q1.Options.Should().ContainKey("D");
            q1.CorrectAnswer.Should().Be("A");
            q1.Explanation.Should().Contain("bảng biến thiên");

            // Question 2: True/False (DS)
            var q2 = result.Questions[1];
            q2.QuestionType.Should().Be("TrueFalse4");
            q2.CognitiveLevel.Should().Be("Thông hiểu");
            q2.Options.Should().ContainKey("a");
            q2.Options.Should().ContainKey("b");
            q2.Options.Should().ContainKey("c");
            q2.Options.Should().ContainKey("d");
            q2.CorrectAnswer.Should().Be("a:Đ, b:Đ, c:S, d:Đ");

            // Question 3: Short Answer (TLN)
            var q3 = result.Questions[2];
            q3.QuestionType.Should().Be("ShortAnswer");
            q3.CognitiveLevel.Should().Be("Vận dụng");
            q3.CorrectAnswer.Should().Be("9");

            // Question 4: Essay (TL)
            var q4 = result.Questions[3];
            q4.QuestionType.Should().Be("Essay");
            q4.CognitiveLevel.Should().Be("Vận dụng cao");

            // Formatted doc text
            result.FormattedDocText.Should().Contain("Câu 1.");
            result.FormattedDocText.Should().Contain("Câu 2.");
            result.FormattedDocText.Should().Contain("Câu 3.");
            result.FormattedDocText.Should().Contain("Câu 4.");
        }

        #endregion

        #region Tier 2 - Boundary Value Tests

        [Fact]
        public void ParseTextDirectly_EmptyOrWhitespace_ShouldReturnFailureResult()
        {
            var res1 = _convertService.ParseTextDirectly("");
            res1.Success.Should().BeFalse();
            res1.ErrorMessage.Should().Contain("rỗng");

            var res2 = _convertService.ParseTextDirectly("   \n\t  ");
            res2.Success.Should().BeFalse();
        }

        [Fact]
        public void ParseTextDirectly_WithCitationTags_ShouldStripCitationsAndParseCorrectly()
        {
            string textWithCites = @"[cite: 1, 2] [source: https://moet.gov.vn]
===CAU===
LOAI: TN
MUCDO: TH
NOIDUNG: Câu hỏi có gắn nhãn trích dẫn nguồn [cite: 3].
A: Đáp án A
B: Đáp án B
C: Đáp án C
D: Đáp án D
DAPAN: B
===KETCAU===";

            var res = _convertService.ParseTextDirectly(textWithCites);

            res.Success.Should().BeTrue();
            res.Questions.Count.Should().Be(1);
            res.Questions[0].Content.Should().NotContain("[cite: 3]");
            res.Questions[0].CorrectAnswer.Should().Be("B");
        }

        [Fact]
        public void ParseTextDirectly_NaturalFormat_ShouldParseStandardVietnameseExamText()
        {
            string naturalText = @"Câu 1: Cho hàm số $f(x) = x^2$. Giá trị $f(2)$ bằng:
A. 4
B. 2
C. 1
D. 0
Đáp án: A
Lời giải: Ta có $f(2) = 2^2 = 4$.

Câu 2: Tập xác định của hàm số $y = \sqrt{x - 1}$ là:
A. $[1; +\infty)$
B. $(1; +\infty)$
C. $(-\infty; 1]$
D. $\mathbb{R}$
Đáp án: A";

            var res = _convertService.ParseTextDirectly(naturalText, subject: "Toán", grade: 12);

            res.Success.Should().BeTrue();
            res.Questions.Count.Should().Be(2);
            res.Questions[0].Options["A"].Should().Be("4");
            res.Questions[0].CorrectAnswer.Should().Be("A");
            res.Questions[0].Explanation.Should().Contain("f(2) = 2^2 = 4");
            res.Questions[1].CorrectAnswer.Should().Be("A");
        }

        [Fact]
        public void ParseTextDirectly_LatexExFormat_ShouldParseExAndChoiceTags()
        {
            string latexText = @"\begin{ex}
Cho cấp số cộng $(u_n)$ có $u_1 = 2$ và công sai $d = 3$. Tìm $u_2$.
\choice
{\True $5$}
{$6$}
{$7$}
{$8$}
\loigiai{
Ta có $u_2 = u_1 + d = 2 + 3 = 5$.
}
\end{ex}";

            var res = _convertService.ParseTextDirectly(latexText, subject: "Toán", grade: 11);

            res.Success.Should().BeTrue();
            res.Questions.Count.Should().Be(1);
            var q = res.Questions[0];
            q.Options["A"].Should().Be("$5$");
            q.CorrectAnswer.Should().Be("A");
            q.Explanation.Should().Contain("u_2 = u_1 + d");
        }

        #endregion

        #region Tier 3 - Combinatorial & Cognitive Level Mapping Tests

        [Theory]
        [InlineData("NB", "Nhận biết")]
        [InlineData("TH", "Thông hiểu")]
        [InlineData("VD", "Vận dụng")]
        [InlineData("VDC", "Vận dụng cao")]
        [InlineData("NHAN BIET", "Nhận biết")]
        [InlineData("THONG HIEU", "Thông hiểu")]
        [InlineData("VAN DUNG", "Vận dụng")]
        [InlineData("CAO", "Vận dụng cao")]
        public void CognitiveLevelMapping_ShouldMapStandardAndLongForms(string inputLevel, string expectedLevel)
        {
            string block = $@"===CAU===
LOAI: TN
MUCDO: {inputLevel}
NOIDUNG: Thử nghiệm phân loại mức độ nhận thức.
A: 1
B: 2
C: 3
D: 4
DAPAN: A
===KETCAU===";

            var result = ConvertService.ParseExtractedQuestions(block);
            result.Questions.Count.Should().Be(1);
            result.Questions[0].CognitiveLevel.Should().Be(expectedLevel);
        }

        [Theory]
        [InlineData("TN", "MultipleChoice4")]
        [InlineData("DS", "TrueFalse4")]
        [InlineData("TLN", "ShortAnswer")]
        [InlineData("TL", "Essay")]
        [InlineData("CHOICE", "MultipleChoice4")]
        [InlineData("TRUEFALSE", "TrueFalse4")]
        public void QuestionTypeMapping_ShouldMapAllStandardVariants(string inputType, string expectedType)
        {
            string block = $@"===CAU===
LOAI: {inputType}
MUCDO: TH
NOIDUNG: Kiểm tra dạng câu hỏi.
DAPAN: A
===KETCAU===";

            var result = ConvertService.ParseExtractedQuestions(block);
            result.Questions.Count.Should().Be(1);
            result.Questions[0].QuestionType.Should().Be(expectedType);
        }

        #endregion

        #region Tier 4 - Workload & Prompt Catalog Tests

        [Fact]
        public void GetChatbotPromptTemplate_ShouldContainStandardRulesAndPreserveParameters()
        {
            string prompt = _convertService.GetChatbotPromptTemplate(subject: "Vật lí", grade: 11, topic: "Điện tích - Điện trường");

            prompt.Should().Contain("Vật lí");
            prompt.Should().Contain("11");
            prompt.Should().Contain("Điện tích - Điện trường");
            prompt.Should().Contain("===CAU===");
            prompt.Should().Contain("===KETCAU===");
            prompt.Should().Contain("MUCDO: NB");
            prompt.Should().Contain("CÔNG THỨC TOÁN");
        }

        [Fact]
        public void ParseExtractedQuestions_50QuestionsBatch_ShouldParseAllAccurately()
        {
            var sb = new System.Text.StringBuilder();
            sb.AppendLine(@"META: {""subject"": ""Toán"", ""grade"": 12, ""topic"": ""Tổng ôn""}");

            for (int i = 1; i <= 50; i++)
            {
                sb.AppendLine("===CAU===");
                sb.AppendLine("LOAI: TN");
                sb.AppendLine(i % 4 == 0 ? "MUCDO: VDC" : i % 3 == 0 ? "MUCDO: VD" : i % 2 == 0 ? "MUCDO: TH" : "MUCDO: NB");
                sb.AppendLine($"CHUONG: Chủ đề số {i}");
                sb.AppendLine($"NOIDUNG: Câu hỏi số {i} với công thức ${{x^{i} + {i}}}$.");
                sb.AppendLine($"A: Phương án A{i}");
                sb.AppendLine($"B: Phương án B{i}");
                sb.AppendLine($"C: Phương án C{i}");
                sb.AppendLine($"D: Phương án D{i}");
                sb.AppendLine($"DAPAN: {(i % 4 == 0 ? "D" : i % 3 == 0 ? "C" : i % 2 == 0 ? "B" : "A")}");
                sb.AppendLine($"LOIGIAI: Lời giải cho câu số {i}.");
                sb.AppendLine("===KETCAU===");
                sb.AppendLine();
            }

            var result = ConvertService.ParseExtractedQuestions(sb.ToString());

            result.Questions.Count.Should().Be(50);
            result.Questions.First().Content.Should().Contain("Câu hỏi số 1");
            result.Questions.Last().Content.Should().Contain("Câu hỏi số 50");
        }

        #endregion
    }
}
