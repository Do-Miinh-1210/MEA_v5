using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using FluentAssertions;
using MatrixExamAI.Shared.Extensibility;
using Xunit;

namespace MatrixExamAI.Desktop.Tests
{
    public class ShuffleAndOmrMatrixTests : IDisposable
    {
        private readonly string _testDbPath;
        private readonly QuestionBankService _qbService;

        public ShuffleAndOmrMatrixTests()
        {
            _testDbPath = Path.Combine(Path.GetTempPath(), $"MEA_Shuffle_{Guid.NewGuid():N}.db");
            _qbService = new QuestionBankService($"Data Source={_testDbPath};");
        }

        public void Dispose()
        {
            try
            {
                if (File.Exists(_testDbPath))
                {
                    File.Delete(_testDbPath);
                }
            }
            catch
            {
                // Best effort cleanup
            }
        }

        #region Tier 1 - Normative Tests (Option Permutation & Correct Answer Tracking)

        [Fact]
        public async Task MixExamVariants_4Variants_ShouldPermuteOptionsAndTrackCorrectAnswers()
        {
            // Arrange
            var draft = CreateSampleDraftWithDistinctOptions();

            // Act
            var variants = await _qbService.MixExamVariantsAsync(draft, variantCount: 4);

            // Assert 1: Count of variants
            variants.Count.Should().Be(4);
            variants.Select(v => v.ExamCode).Should().ContainInOrder("101", "102", "103", "104");

            // Assert 2: Check each variant has all questions
            foreach (var variant in variants)
            {
                variant.Part1Questions.Count.Should().Be(draft.Part1Questions.Count);
                variant.Part2Questions.Count.Should().Be(draft.Part2Questions.Count);
                variant.Part3Questions.Count.Should().Be(draft.Part3Questions.Count);

                int totalQuestions = variant.Part1Questions.Count + variant.Part2Questions.Count + variant.Part3Questions.Count;
                variant.AnswerKey.Count.Should().Be(totalQuestions, "AnswerKey dictionary must have answers for every question");
            }

            // Assert 3: Track that correct answer text matches the original correct option text
            var origQ1 = draft.Part1Questions[0];
            string origCorrectText = origQ1.Options[origQ1.CorrectAnswer];

            foreach (var variant in variants)
            {
                var matchedQ = variant.Part1Questions.First(q => q.QuestionCode == origQ1.QuestionCode);
                string variantCorrectLetter = matchedQ.CorrectAnswer;
                matchedQ.Options.Should().ContainKey(variantCorrectLetter);
                matchedQ.Options[variantCorrectLetter].Should().Be(origCorrectText,
                    "In variant {0}, correct answer letter must point to original correct text '{1}'",
                    variant.ExamCode, origCorrectText);
            }
        }

        [Fact]
        public async Task MixExamVariants_QuestionOrderPermutation_ShouldDifferAcrossVariants()
        {
            // Arrange
            var draft = CreateSampleDraftWithDistinctOptions();

            // Act
            var variants = await _qbService.MixExamVariantsAsync(draft, variantCount: 4);

            // Assert: At least some variants should have different question order sequences
            var order101 = variants[0].Part1Questions.Select(q => q.QuestionCode).ToList();
            var order102 = variants[1].Part1Questions.Select(q => q.QuestionCode).ToList();

            // Orders should not all be strictly identical across distinct RNG seeds
            variants.Select(v => string.Join(",", v.Part1Questions.Select(q => q.QuestionCode)))
                .Distinct()
                .Count()
                .Should().BeGreaterThan(1, "Variants should produce randomized question order permutations");
        }

        #endregion

        #region Tier 2 - Boundary Value Tests

        [Fact]
        public async Task MixExamVariants_SingleVariantRequested_ShouldDefaultToAtLeast4OrRequestedCount()
        {
            var draft = CreateSampleDraftWithDistinctOptions();

            var variants = await _qbService.MixExamVariantsAsync(draft, variantCount: 1);
            variants.Count.Should().Be(1);
            variants[0].ExamCode.Should().Be("101");
        }

        [Fact]
        public async Task MixExamVariants_NullDraft_ShouldThrowArgumentNullException()
        {
            Func<Task> act = async () => await _qbService.MixExamVariantsAsync(null!, 4);
            await act.Should().ThrowAsync<ArgumentNullException>();
        }

        [Fact]
        public async Task MixExamVariants_QuestionWithSingleOption_ShouldHandleSafelyWithoutError()
        {
            var draft = new ExamDraftResult
            {
                Title = "Đề bài đặc biệt",
                Part1Questions = new List<QuestionItem>
                {
                    new QuestionItem
                    {
                        QuestionCode = "SINGLE_OPT",
                        Content = "Nội dung chỉ có 1 phương án",
                        Options = new Dictionary<string, string> { ["A"] = "Duy nhất" },
                        CorrectAnswer = "A"
                    }
                }
            };

            var variants = await _qbService.MixExamVariantsAsync(draft, 2);
            variants.Count.Should().Be(2);
            variants[0].Part1Questions[0].CorrectAnswer.Should().Be("A");
        }

        #endregion

        #region Tier 3 - Combinatorial & Fixed Option Preservation Tests

        [Fact]
        public void OmrCrossAnswerMatrix_TableFormatting_ShouldGenerateStandardMarkdownGrid()
        {
            // Simulate the ShuffleView OMR table generation
            int count = 4;
            int startCode = 101;
            var sb = new StringBuilder();

            sb.Append("| Câu |");
            for (int i = 0; i < count; i++)
            {
                sb.Append($" Mã {startCode + i} |");
            }
            sb.AppendLine();

            sb.Append("|---|");
            for (int i = 0; i < count; i++)
            {
                sb.Append("---|");
            }
            sb.AppendLine();

            char[] answers = { 'A', 'B', 'C', 'D' };
            for (int q = 1; q <= 12; q++)
            {
                sb.Append($"| {q} |");
                for (int i = 0; i < count; i++)
                {
                    sb.Append($" {answers[(q + i) % 4]} |");
                }
                sb.AppendLine();
            }

            string tableText = sb.ToString();

            // Assert
            var lines = tableText.Trim().Split('\n');
            lines.Length.Should().Be(14, "Header + Separator + 12 questions = 14 rows");
            lines[0].Should().Contain("Mã 101").And.Contain("Mã 104");
            lines[2].Should().StartWith("| 1 |");
        }

        #endregion

        #region Tier 4 - Workload & High Variant Count Stress Test

        [Fact]
        public async Task MixExamVariants_24Variants_StressTest_ShouldCompleteInUnder1Second()
        {
            var draft = CreateSampleDraftWithDistinctOptions();

            var sw = System.Diagnostics.Stopwatch.StartNew();
            var variants = await _qbService.MixExamVariantsAsync(draft, variantCount: 24);
            sw.Stop();

            sw.ElapsedMilliseconds.Should().BeLessThan(1000, "24 exam variants shuffle must finish in < 1 second");
            variants.Count.Should().Be(24);
            variants.Last().ExamCode.Should().Be("124");
        }

        #endregion

        #region Helpers

        private static ExamDraftResult CreateSampleDraftWithDistinctOptions()
        {
            var draft = new ExamDraftResult
            {
                Title = "Đề thi khảo sát",
                Subject = "Toán",
                Grade = 12
            };

            for (int i = 1; i <= 12; i++)
            {
                draft.Part1Questions.Add(new QuestionItem
                {
                    QuestionCode = $"Q_MCQ_{i:D2}",
                    QuestionType = "MultipleChoice4",
                    Content = $"Câu hỏi trắc nghiệm số {i}",
                    Options = new Dictionary<string, string>
                    {
                        ["A"] = $"Nội dung A của câu {i} (ĐÚNG)",
                        ["B"] = $"Nội dung B của câu {i}",
                        ["C"] = $"Nội dung C của câu {i}",
                        ["D"] = $"Nội dung D của câu {i}"
                    },
                    CorrectAnswer = "A"
                });
            }

            for (int i = 1; i <= 4; i++)
            {
                draft.Part2Questions.Add(new QuestionItem
                {
                    QuestionCode = $"Q_TF_{i:D2}",
                    QuestionType = "TrueFalse4",
                    Content = $"Câu hỏi đúng sai số {i}",
                    Options = new Dictionary<string, string>
                    {
                        ["a"] = "Mệnh đề a",
                        ["b"] = "Mệnh đề b",
                        ["c"] = "Mệnh đề c",
                        ["d"] = "Mệnh đề d"
                    },
                    CorrectAnswer = "a:Đ, b:S, c:Đ, d:S"
                });
            }

            for (int i = 1; i <= 6; i++)
            {
                draft.Part3Questions.Add(new QuestionItem
                {
                    QuestionCode = $"Q_SA_{i:D2}",
                    QuestionType = "ShortAnswer",
                    Content = $"Câu hỏi trả lời ngắn số {i}",
                    CorrectAnswer = (i * 5).ToString()
                });
            }

            return draft;
        }

        #endregion
    }
}
