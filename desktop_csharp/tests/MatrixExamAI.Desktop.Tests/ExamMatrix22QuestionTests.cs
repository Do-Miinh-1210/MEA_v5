using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Threading.Tasks;
using FluentAssertions;
using MatrixExamAI.Shared.Extensibility;
using Xunit;

namespace MatrixExamAI.Desktop.Tests
{
    public class ExamMatrix22QuestionTests : IDisposable
    {
        private readonly string _testDbPath;
        private readonly QuestionBankService _qbService;

        public ExamMatrix22QuestionTests()
        {
            _testDbPath = Path.Combine(Path.GetTempPath(), $"MEA_ExamMatrix_{Guid.NewGuid():N}.db");
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

        #region Tier 1 - Normative Tests (Standard 22-Question BGD Matrix)

        [Fact]
        public void ExamMatrixConfig_DefaultValues_ShouldMatchMinistryOfEducationSpecifications()
        {
            // Arrange & Act
            var config = new ExamMatrixConfig();

            // Assert
            config.Title.Should().NotBeNullOrWhiteSpace();
            config.Subject.Should().Be("Toán");
            config.Grade.Should().Be(12);
            config.DurationMinutes.Should().Be(90);

            // Three-part structure: 12 MCQ + 4 TF + 6 SA = 22 questions
            config.Part1Count.Should().Be(12, "Part I: Multiple choice 4 options (12 questions = 3.0 pts)");
            config.Part2Count.Should().Be(4, "Part II: True/False 4 statements (4 questions = 4.0 pts)");
            config.Part3Count.Should().Be(6, "Part III: Short answer numeric (6 questions = 3.0 pts)");
            config.TotalQuestions.Should().Be(22, "Total exam questions must strictly equal 22");

            // Cognitive distribution
            config.CognitiveDistribution["Nhận biết"].Should().Be(40);
            config.CognitiveDistribution["Thông hiểu"].Should().Be(30);
            config.CognitiveDistribution["Vận dụng"].Should().Be(20);
            config.CognitiveDistribution["Vận dụng cao"].Should().Be(10);
            config.CognitiveDistribution.Values.Sum().Should().Be(100, "Cognitive distribution must sum to 100%");
        }

        [Fact]
        public async Task GenerateExamFromMatrix_SufficientQuestionBank_ShouldCreate22QuestionDraft()
        {
            // Arrange: Seed database with enough candidates for each part
            await _qbService.InitializeDatabaseAsync();
            await SeedCandidatesForMatrixAsync(_qbService);

            var config = new ExamMatrixConfig
            {
                Title = "Đề thi tốt nghiệp THPT thử nghiệm 2026",
                Subject = "Toán",
                Grade = 12,
                DurationMinutes = 90
            };

            // Act
            var draft = await _qbService.GenerateExamFromMatrixAsync(config, _qbService);

            // Assert
            draft.Success.Should().BeTrue();
            draft.Title.Should().Be(config.Title);
            draft.Part1Questions.Count.Should().Be(12, "Draft Part I must have exactly 12 MCQ questions");
            draft.Part2Questions.Count.Should().Be(4, "Draft Part II must have exactly 4 True/False questions");
            draft.Part3Questions.Count.Should().Be(6, "Draft Part III must have exactly 6 Short Answer questions");
            draft.TotalSelectedQuestions.Should().Be(22, "Total selected questions must be exactly 22");

            // Verify question types in each part
            draft.Part1Questions.Should().OnlyContain(q => q.QuestionType == "MultipleChoice4");
            draft.Part2Questions.Should().OnlyContain(q => q.QuestionType == "TrueFalse4");
            draft.Part3Questions.Should().OnlyContain(q => q.QuestionType == "ShortAnswer");
        }

        #endregion

        #region Tier 2 - Boundary Value Tests

        [Fact]
        public async Task GenerateExamFromMatrix_EmptyQuestionBank_ShouldReturnFailureWithClearMessage()
        {
            // Arrange: Fresh empty DB
            await _qbService.InitializeDatabaseAsync();
            var config = new ExamMatrixConfig { Subject = "Vật lí", Grade = 10 };

            // Act
            var draft = await _qbService.GenerateExamFromMatrixAsync(config, _qbService);

            // Assert
            draft.Success.Should().BeFalse();
            draft.TotalSelectedQuestions.Should().Be(0);
            draft.ErrorMessage.Should().Contain("Chưa có đủ câu hỏi");
        }

        [Fact]
        public void ExamMatrixConfig_CustomPartCounts_ShouldCalculateTotalAccurately()
        {
            var config = new ExamMatrixConfig
            {
                Part1Count = 20,
                Part2Count = 5,
                Part3Count = 5
            };

            config.TotalQuestions.Should().Be(30);
        }

        #endregion

        #region Tier 3 - Combinatorial & Cognitive Distribution Tests

        [Fact]
        public async Task GenerateExamFromMatrix_CognitiveDistribution_ShouldAllocateQuestionsByLevels()
        {
            await _qbService.InitializeDatabaseAsync();
            await SeedCandidatesForMatrixAsync(_qbService);

            var config = new ExamMatrixConfig();
            var draft = await _qbService.GenerateExamFromMatrixAsync(config, _qbService);

            draft.Success.Should().BeTrue();

            // Part 1 should contain a mix of cognitive levels
            var part1Levels = draft.Part1Questions.Select(q => q.CognitiveLevel).Distinct().ToList();
            part1Levels.Should().Contain("Nhận biết");
            part1Levels.Should().Contain("Thông hiểu");
        }

        #endregion

        #region Tier 4 - Workload & Repetitive Generations

        [Fact]
        public async Task GenerateExamFromMatrix_MultipleConsecutiveCalls_ShouldExecuteDeterministically()
        {
            await _qbService.InitializeDatabaseAsync();
            await SeedCandidatesForMatrixAsync(_qbService);

            var config = new ExamMatrixConfig();

            for (int iteration = 0; iteration < 5; iteration++)
            {
                var draft = await _qbService.GenerateExamFromMatrixAsync(config, _qbService);
                draft.Success.Should().BeTrue();
                draft.TotalSelectedQuestions.Should().Be(22);
            }
        }

        #endregion

        #region Helpers

        private static async Task SeedCandidatesForMatrixAsync(QuestionBankService qb)
        {
            // Seed 20 MCQ questions
            for (int i = 1; i <= 20; i++)
            {
                string level = i <= 8 ? "Nhận biết" : i <= 14 ? "Thông hiểu" : i <= 18 ? "Vận dụng" : "Vận dụng cao";
                await qb.InsertQuestionAsync(new QuestionItem
                {
                    QuestionCode = $"SEED_MCQ_{i:D2}",
                    Subject = "Toán",
                    Grade = 12,
                    Topic = "Khảo sát hàm số",
                    CognitiveLevel = level,
                    QuestionType = "MultipleChoice4",
                    Content = $"Nội dung câu hỏi trắc nghiệm {i}",
                    Options = new Dictionary<string, string> { ["A"] = "1", ["B"] = "2", ["C"] = "3", ["D"] = "4" },
                    CorrectAnswer = "A"
                });
            }

            // Seed 10 True/False questions
            for (int i = 1; i <= 10; i++)
            {
                string level = i <= 5 ? "Thông hiểu" : "Vận dụng";
                await qb.InsertQuestionAsync(new QuestionItem
                {
                    QuestionCode = $"SEED_TF_{i:D2}",
                    Subject = "Toán",
                    Grade = 12,
                    Topic = "Hàm số mũ & Logarit",
                    CognitiveLevel = level,
                    QuestionType = "TrueFalse4",
                    Content = $"Nội dung câu hỏi đúng sai {i}",
                    Options = new Dictionary<string, string> { ["a"] = "Ý a", ["b"] = "Ý b", ["c"] = "Ý c", ["d"] = "Ý d" },
                    CorrectAnswer = "a:Đ, b:S, c:Đ, d:S"
                });
            }

            // Seed 10 Short Answer questions
            for (int i = 1; i <= 10; i++)
            {
                string level = i <= 5 ? "Vận dụng" : "Vận dụng cao";
                await qb.InsertQuestionAsync(new QuestionItem
                {
                    QuestionCode = $"SEED_SA_{i:D2}",
                    Subject = "Toán",
                    Grade = 12,
                    Topic = "Tích phân & Ứng dụng",
                    CognitiveLevel = level,
                    QuestionType = "ShortAnswer",
                    Content = $"Nội dung câu hỏi trả lời ngắn {i}",
                    CorrectAnswer = (i * 10).ToString()
                });
            }
        }

        #endregion
    }
}
