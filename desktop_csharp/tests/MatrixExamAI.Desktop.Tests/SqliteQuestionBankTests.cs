using System;
using System.Collections.Generic;
using System.IO;
using System.Threading.Tasks;
using FluentAssertions;
using MatrixExamAI.Shared.Extensibility;
using Microsoft.Data.Sqlite;
using Xunit;

namespace MatrixExamAI.Desktop.Tests
{
    public class SqliteQuestionBankTests : IDisposable
    {
        private readonly string _testDbPath;
        private readonly QuestionBankService _qbService;

        public SqliteQuestionBankTests()
        {
            _testDbPath = Path.Combine(Path.GetTempPath(), $"MEA_QB_Test_{Guid.NewGuid():N}.db");
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

        #region Tier 1 - Normative Tests (Schema Parity & Core CRUD)

        [Fact]
        public async Task InitializeDatabase_ShouldCreateStandardQuestionsTableWithIndexes()
        {
            // Act
            await _qbService.InitializeDatabaseAsync();

            // Assert: Verify tables and indexes exist in SQLite schema
            using var conn = new SqliteConnection($"Data Source={_testDbPath};");
            await conn.OpenAsync();

            using var cmd = conn.CreateCommand();
            cmd.CommandText = "SELECT name FROM sqlite_master WHERE type='table' AND name='questions';";
            var tableName = (string?)await cmd.ExecuteScalarAsync();
            tableName.Should().Be("questions");

            // Check columns in questions table
            cmd.CommandText = "PRAGMA table_info(questions);";
            var columns = new List<string>();
            using (var reader = await cmd.ExecuteReaderAsync())
            {
                while (await reader.ReadAsync())
                {
                    columns.Add(reader.GetString(1));
                }
            }

            columns.Should().Contain("id");
            columns.Should().Contain("question_code");
            columns.Should().Contain("subject");
            columns.Should().Contain("grade");
            columns.Should().Contain("topic");
            columns.Should().Contain("cognitive_level");
            columns.Should().Contain("question_type");
            columns.Should().Contain("content");
            columns.Should().Contain("options_json");
            columns.Should().Contain("correct_answer");
            columns.Should().Contain("explanation");
            columns.Should().Contain("tikz_code");
            columns.Should().Contain("source");
            columns.Should().Contain("raw_data_json");
            columns.Should().Contain("created_at");
            columns.Should().Contain("updated_at");
        }

        [Fact]
        public async Task InsertAndGetQuestionById_ShouldPersistAndDeserializeOptionsCorrectly()
        {
            await _qbService.InitializeDatabaseAsync();

            var item = new QuestionItem
            {
                QuestionCode = "TOAN12_TEST_001",
                Subject = "Toán",
                Grade = 12,
                Topic = "Khảo sát hàm số",
                CognitiveLevel = "Nhận biết",
                QuestionType = "MultipleChoice4",
                Content = "Tìm cực đại của hàm số $y = x^3 - 3x$.",
                Options = new Dictionary<string, string>
                {
                    ["A"] = "$y_{CĐ} = 2$",
                    ["B"] = "$y_{CĐ} = -2$",
                    ["C"] = "$y_{CĐ} = 0$",
                    ["D"] = "$y_{CĐ} = 3$"
                },
                CorrectAnswer = "A",
                Explanation = "Ta có $y' = 3x^2 - 3 = 0 \\Leftrightarrow x = \\pm 1$. Điểm cực đại $x = -1 \\Rightarrow y = 2$.",
                Source = "Thầy Đỗ Minh 2026"
            };

            // Act: Insert
            long newId = await _qbService.InsertQuestionAsync(item);
            newId.Should().BeGreaterThan(0);

            // Act: Retrieve
            var retrieved = await _qbService.GetQuestionByIdAsync(newId);

            // Assert
            retrieved.Should().NotBeNull();
            retrieved!.Id.Should().Be(newId);
            retrieved.QuestionCode.Should().Be("TOAN12_TEST_001");
            retrieved.Subject.Should().Be("Toán");
            retrieved.Grade.Should().Be(12);
            retrieved.CognitiveLevel.Should().Be("Nhận biết");
            retrieved.Content.Should().Be(item.Content);
            retrieved.Options.Should().HaveCount(4);
            retrieved.Options["A"].Should().Be("$y_{CĐ} = 2$");
            retrieved.CorrectAnswer.Should().Be("A");
            retrieved.Explanation.Should().Contain("y = 2");
        }

        [Fact]
        public async Task UpdateQuestion_ExistingRecord_ShouldPersistUpdates()
        {
            await _qbService.InitializeDatabaseAsync();

            var item = new QuestionItem
            {
                QuestionCode = "UPDATE_TEST",
                Subject = "Toán",
                Grade = 12,
                Content = "Nội dung ban đầu",
                CorrectAnswer = "A"
            };
            long id = await _qbService.InsertQuestionAsync(item);

            // Update
            item.Content = "Nội dung đã được cập nhật chuẩn ${...}$";
            item.CorrectAnswer = "B";
            item.CognitiveLevel = "Vận dụng cao";

            bool updated = await _qbService.UpdateQuestionAsync(item);
            updated.Should().BeTrue();

            var reloaded = await _qbService.GetQuestionByIdAsync(id);
            reloaded!.Content.Should().Be("Nội dung đã được cập nhật chuẩn ${...}$");
            reloaded.CorrectAnswer.Should().Be("B");
            reloaded.CognitiveLevel.Should().Be("Vận dụng cao");
        }

        [Fact]
        public async Task DeleteQuestion_ExistingRecord_ShouldRemoveFromDatabase()
        {
            await _qbService.InitializeDatabaseAsync();

            var item = new QuestionItem
            {
                QuestionCode = "DELETE_ME",
                Subject = "Toán",
                Grade = 10,
                Content = "Câu hỏi chuẩn bị xóa"
            };
            long id = await _qbService.InsertQuestionAsync(item);

            bool deleted = await _qbService.DeleteQuestionAsync(id);
            deleted.Should().BeTrue();

            var missing = await _qbService.GetQuestionByIdAsync(id);
            missing.Should().BeNull();
        }

        #endregion

        #region Tier 2 - Boundary Value Tests

        [Fact]
        public async Task SearchQuestions_NoMatchKeyword_ShouldReturnEmptyList()
        {
            await _qbService.InitializeDatabaseAsync();
            var results = await _qbService.SearchQuestionsAsync(keyword: "TỪ_KHÓA_KHÔNG_TỒN_TẠI_12345");
            results.Should().BeEmpty();
        }

        [Fact]
        public async Task GetQuestionById_NonExistentId_ShouldReturnNull()
        {
            await _qbService.InitializeDatabaseAsync();
            var result = await _qbService.GetQuestionByIdAsync(999999);
            result.Should().BeNull();
        }

        [Fact]
        public async Task InsertQuestion_NullItem_ShouldThrowArgumentNullException()
        {
            await _qbService.InitializeDatabaseAsync();
            Func<Task> act = async () => await _qbService.InsertQuestionAsync(null!);
            await act.Should().ThrowAsync<ArgumentNullException>();
        }

        #endregion

        #region Tier 3 - Combinatorial & Filter Tests

        [Fact]
        public async Task SearchQuestions_CombinedFilters_ShouldFilterPrecisely()
        {
            await _qbService.InitializeDatabaseAsync();

            // Insert 3 diverse questions
            await _qbService.InsertQuestionAsync(new QuestionItem
            {
                QuestionCode = "Q1",
                Subject = "Toán",
                Grade = 12,
                CognitiveLevel = "Nhận biết",
                QuestionType = "MultipleChoice4",
                Content = "Hàm số đồng biến trên khoảng nào"
            });
            await _qbService.InsertQuestionAsync(new QuestionItem
            {
                QuestionCode = "Q2",
                Subject = "Toán",
                Grade = 12,
                CognitiveLevel = "Vận dụng",
                QuestionType = "MultipleChoice4",
                Content = "Tìm giá trị lớn nhất của hàm số mũ"
            });
            await _qbService.InsertQuestionAsync(new QuestionItem
            {
                QuestionCode = "Q3",
                Subject = "Vật lí",
                Grade = 12,
                CognitiveLevel = "Nhận biết",
                QuestionType = "MultipleChoice4",
                Content = "Chu kì dao động điều hòa"
            });

            // Filter Toán 12 Nhận biết
            var mathNb = await _qbService.SearchQuestionsAsync(
                subject: "Toán",
                grade: 12,
                level: "Nhận biết");

            mathNb.Count.Should().Be(1);
            mathNb[0].QuestionCode.Should().Be("Q1");

            // Filter by keyword "hàm số"
            var keywordMatch = await _qbService.SearchQuestionsAsync(keyword: "hàm số");
            keywordMatch.Count.Should().Be(2);

            // Count checks
            int countMath = await _qbService.GetQuestionCountAsync(subject: "Toán");
            countMath.Should().Be(2);

            int countPhysics = await _qbService.GetQuestionCountAsync(subject: "Vật lí");
            countPhysics.Should().Be(1);
        }

        #endregion

        #region Tier 4 - Workload & Seeding Tests

        [Fact]
        public async Task SeedDefaultQuestions_FreshDatabase_ShouldSeedStandardQuestions()
        {
            await _qbService.InitializeDatabaseAsync();

            // Act
            await _qbService.SeedDefaultQuestionsAsync();

            // Assert
            int total = await _qbService.GetQuestionCountAsync();
            total.Should().BeGreaterThanOrEqualTo(9, "Default seeding contains at least 9 comprehensive curriculum questions");

            var math12 = await _qbService.SearchQuestionsAsync(subject: "Toán", grade: 12);
            math12.Should().NotBeEmpty();

            var tfQ = await _qbService.SearchQuestionsAsync(questionType: "TrueFalse4");
            tfQ.Should().NotBeEmpty();
            tfQ[0].Options.Should().ContainKey("a");

            var saQ = await _qbService.SearchQuestionsAsync(questionType: "ShortAnswer");
            saQ.Should().NotBeEmpty();
            saQ[0].CorrectAnswer.Should().Be("5");
        }

        #endregion
    }
}
