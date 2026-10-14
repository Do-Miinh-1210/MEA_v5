using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Data.Sqlite;

namespace MatrixExamAI.Shared.Extensibility
{
    /// <summary>
    /// Triển khai dịch vụ Ngân hàng câu hỏi SQLite & Trộn đề thi theo Ma trận chuẩn BGD (Phase 3).
    /// </summary>
    public class QuestionBankService : IQuestionBankService, IExamMatrixService
    {
        private readonly string _connectionString;
        private bool _isInitialized;
        private readonly object _initLock = new object();

        static QuestionBankService()
        {
            try
            {
                SQLitePCL.Batteries_V2.Init();
            }
            catch
            {
                // Ignore if already initialized
            }
        }

        public QuestionBankService(string? customConnectionString = null)
        {
            if (!string.IsNullOrWhiteSpace(customConnectionString))
            {
                _connectionString = customConnectionString!;
            }
            else
            {
                string localAppData = Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData);
                string dbDir = Path.Combine(localAppData, "MatrixExamAI");
                Directory.CreateDirectory(dbDir);
                string dbPath = Path.Combine(dbDir, "question_bank.db");
                _connectionString = $"Data Source={dbPath};";
            }
        }

        #region IQuestionBankService Implementation

        public async Task InitializeDatabaseAsync(CancellationToken cancellationToken = default)
        {
            if (_isInitialized) return;

            using (var conn = new SqliteConnection(_connectionString))
            {
                await conn.OpenAsync(cancellationToken);

                using (var cmd = conn.CreateCommand())
                {
                    cmd.CommandText = @"
                        PRAGMA journal_mode=WAL;
                        PRAGMA synchronous=NORMAL;

                        CREATE TABLE IF NOT EXISTS questions (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            question_code TEXT,
                            subject TEXT,
                            grade INTEGER,
                            topic TEXT,
                            cognitive_level TEXT,
                            question_type TEXT,
                            content TEXT,
                            options_json TEXT,
                            correct_answer TEXT,
                            explanation TEXT,
                            tikz_code TEXT,
                            images TEXT,
                            source TEXT,
                            raw_data_json TEXT,
                            created_at TEXT,
                            updated_at TEXT
                        );

                        CREATE INDEX IF NOT EXISTS idx_q_sg ON questions(subject, grade);
                        CREATE INDEX IF NOT EXISTS idx_q_level ON questions(cognitive_level);
                        CREATE INDEX IF NOT EXISTS idx_q_topic ON questions(topic);
                        CREATE INDEX IF NOT EXISTS idx_q_type ON questions(question_type);
                    ";
                    await cmd.ExecuteNonQueryAsync(cancellationToken);

                    // Migration an toàn bổ sung cột images nếu database cũ đã tồn tại
                    try
                    {
                        using var alterCmd = conn.CreateCommand();
                        alterCmd.CommandText = "ALTER TABLE questions ADD COLUMN images TEXT;";
                        await alterCmd.ExecuteNonQueryAsync(cancellationToken);
                    }
                    catch
                    {
                        // Bỏ qua nếu cột đã tồn tại
                    }
                }
            }

            lock (_initLock)
            {
                _isInitialized = true;
            }
        }

        public async Task<long> InsertQuestionAsync(QuestionItem item, CancellationToken cancellationToken = default)
        {
            if (item == null) throw new ArgumentNullException(nameof(item));
            await EnsureInitializedAsync(cancellationToken);

            using (var conn = new SqliteConnection(_connectionString))
            {
                await conn.OpenAsync(cancellationToken);

                using (var cmd = conn.CreateCommand())
                {
                    cmd.CommandText = @"
                        INSERT INTO questions (
                            question_code, subject, grade, topic, cognitive_level,
                            question_type, content, options_json, correct_answer,
                            explanation, tikz_code, images, source, raw_data_json, created_at, updated_at
                        ) VALUES (
                            @code, @subject, @grade, @topic, @level,
                            @qtype, @content, @options, @answer,
                            @explanation, @tikz, @images, @source, @raw, @created, @updated
                        );
                        SELECT last_insert_rowid();
                    ";

                    cmd.Parameters.AddWithValue("@code", item.QuestionCode ?? string.Empty);
                    cmd.Parameters.AddWithValue("@subject", item.Subject ?? "Toán");
                    cmd.Parameters.AddWithValue("@grade", item.Grade);
                    cmd.Parameters.AddWithValue("@topic", item.Topic ?? string.Empty);
                    cmd.Parameters.AddWithValue("@level", item.CognitiveLevel ?? "Thông hiểu");
                    cmd.Parameters.AddWithValue("@qtype", item.QuestionType ?? "MultipleChoice4");
                    cmd.Parameters.AddWithValue("@content", item.Content ?? string.Empty);
                    cmd.Parameters.AddWithValue("@options", JsonSerializer.Serialize(item.Options ?? new Dictionary<string, string>()));
                    cmd.Parameters.AddWithValue("@answer", item.CorrectAnswer ?? string.Empty);
                    cmd.Parameters.AddWithValue("@explanation", item.Explanation ?? string.Empty);
                    cmd.Parameters.AddWithValue("@tikz", item.TikzCode ?? string.Empty);
                    cmd.Parameters.AddWithValue("@images", ImageHelper.SerializeImageField(item.Images));
                    cmd.Parameters.AddWithValue("@source", item.Source ?? string.Empty);
                    cmd.Parameters.AddWithValue("@raw", item.RawDataJson ?? string.Empty);
                    cmd.Parameters.AddWithValue("@created", item.CreatedAt.ToString("o"));
                    cmd.Parameters.AddWithValue("@updated", item.UpdatedAt.ToString("o"));

                    object? result = await cmd.ExecuteScalarAsync(cancellationToken);
                    long newId = result != null ? Convert.ToInt64(result) : 0;
                    item.Id = newId;
                    return newId;
                }
            }
        }

        public async Task<bool> UpdateQuestionAsync(QuestionItem item, CancellationToken cancellationToken = default)
        {
            if (item == null) throw new ArgumentNullException(nameof(item));
            await EnsureInitializedAsync(cancellationToken);

            using (var conn = new SqliteConnection(_connectionString))
            {
                await conn.OpenAsync(cancellationToken);

                using (var cmd = conn.CreateCommand())
                {
                    cmd.CommandText = @"
                        UPDATE questions SET
                            question_code = @code,
                            subject = @subject,
                            grade = @grade,
                            topic = @topic,
                            cognitive_level = @level,
                            question_type = @qtype,
                            content = @content,
                            options_json = @options,
                            correct_answer = @answer,
                            explanation = @explanation,
                            tikz_code = @tikz,
                            images = @images,
                            source = @source,
                            raw_data_json = @raw,
                            updated_at = @updated
                        WHERE id = @id;
                    ";

                    cmd.Parameters.AddWithValue("@id", item.Id);
                    cmd.Parameters.AddWithValue("@code", item.QuestionCode ?? string.Empty);
                    cmd.Parameters.AddWithValue("@subject", item.Subject ?? "Toán");
                    cmd.Parameters.AddWithValue("@grade", item.Grade);
                    cmd.Parameters.AddWithValue("@topic", item.Topic ?? string.Empty);
                    cmd.Parameters.AddWithValue("@level", item.CognitiveLevel ?? "Thông hiểu");
                    cmd.Parameters.AddWithValue("@qtype", item.QuestionType ?? "MultipleChoice4");
                    cmd.Parameters.AddWithValue("@content", item.Content ?? string.Empty);
                    cmd.Parameters.AddWithValue("@options", JsonSerializer.Serialize(item.Options ?? new Dictionary<string, string>()));
                    cmd.Parameters.AddWithValue("@answer", item.CorrectAnswer ?? string.Empty);
                    cmd.Parameters.AddWithValue("@explanation", item.Explanation ?? string.Empty);
                    cmd.Parameters.AddWithValue("@tikz", item.TikzCode ?? string.Empty);
                    cmd.Parameters.AddWithValue("@images", ImageHelper.SerializeImageField(item.Images));
                    cmd.Parameters.AddWithValue("@source", item.Source ?? string.Empty);
                    cmd.Parameters.AddWithValue("@raw", item.RawDataJson ?? string.Empty);
                    cmd.Parameters.AddWithValue("@updated", DateTime.UtcNow.ToString("o"));

                    int rows = await cmd.ExecuteNonQueryAsync(cancellationToken);
                    return rows > 0;
                }
            }
        }

        public async Task<bool> DeleteQuestionAsync(long id, CancellationToken cancellationToken = default)
        {
            await EnsureInitializedAsync(cancellationToken);

            using (var conn = new SqliteConnection(_connectionString))
            {
                await conn.OpenAsync(cancellationToken);

                using (var cmd = conn.CreateCommand())
                {
                    cmd.CommandText = "DELETE FROM questions WHERE id = @id;";
                    cmd.Parameters.AddWithValue("@id", id);
                    int rows = await cmd.ExecuteNonQueryAsync(cancellationToken);
                    return rows > 0;
                }
            }
        }

        public async Task<QuestionItem?> GetQuestionByIdAsync(long id, CancellationToken cancellationToken = default)
        {
            await EnsureInitializedAsync(cancellationToken);

            using (var conn = new SqliteConnection(_connectionString))
            {
                await conn.OpenAsync(cancellationToken);

                using (var cmd = conn.CreateCommand())
                {
                    cmd.CommandText = "SELECT * FROM questions WHERE id = @id LIMIT 1;";
                    cmd.Parameters.AddWithValue("@id", id);

                    using (var reader = await cmd.ExecuteReaderAsync(cancellationToken))
                    {
                        if (await reader.ReadAsync(cancellationToken))
                        {
                            return ReadQuestionFromReader(reader);
                        }
                    }
                }
            }
            return null;
        }

        public async Task<List<QuestionItem>> SearchQuestionsAsync(
            string? keyword = null,
            string? subject = null,
            int? grade = null,
            string? topic = null,
            string? level = null,
            string? questionType = null,
            int limit = 50,
            CancellationToken cancellationToken = default)
        {
            await EnsureInitializedAsync(cancellationToken);
            var results = new List<QuestionItem>();

            using (var conn = new SqliteConnection(_connectionString))
            {
                await conn.OpenAsync(cancellationToken);

                using (var cmd = conn.CreateCommand())
                {
                    var whereClauses = new List<string>();

                    if (!string.IsNullOrWhiteSpace(keyword))
                    {
                        whereClauses.Add("(content LIKE @keyword OR question_code LIKE @keyword OR explanation LIKE @keyword)");
                        cmd.Parameters.AddWithValue("@keyword", $"%{keyword}%");
                    }
                    if (!string.IsNullOrWhiteSpace(subject))
                    {
                        whereClauses.Add("subject = @subject");
                        cmd.Parameters.AddWithValue("@subject", subject);
                    }
                    if (grade.HasValue)
                    {
                        whereClauses.Add("grade = @grade");
                        cmd.Parameters.AddWithValue("@grade", grade.Value);
                    }
                    if (!string.IsNullOrWhiteSpace(topic))
                    {
                        whereClauses.Add("topic = @topic");
                        cmd.Parameters.AddWithValue("@topic", topic);
                    }
                    if (!string.IsNullOrWhiteSpace(level))
                    {
                        whereClauses.Add("cognitive_level = @level");
                        cmd.Parameters.AddWithValue("@level", level);
                    }
                    if (!string.IsNullOrWhiteSpace(questionType))
                    {
                        whereClauses.Add("question_type = @qtype");
                        cmd.Parameters.AddWithValue("@qtype", questionType);
                    }

                    string whereSql = whereClauses.Count > 0
                        ? "WHERE " + string.Join(" AND ", whereClauses)
                        : string.Empty;

                    cmd.CommandText = $"SELECT * FROM questions {whereSql} ORDER BY id DESC LIMIT @limit;";
                    cmd.Parameters.AddWithValue("@limit", Math.Max(1, limit));

                    using (var reader = await cmd.ExecuteReaderAsync(cancellationToken))
                    {
                        while (await reader.ReadAsync(cancellationToken))
                        {
                            results.Add(ReadQuestionFromReader(reader));
                        }
                    }
                }
            }

            return results;
        }

        public async Task<int> GetQuestionCountAsync(
            string? subject = null,
            int? grade = null,
            string? level = null,
            CancellationToken cancellationToken = default)
        {
            await EnsureInitializedAsync(cancellationToken);

            using (var conn = new SqliteConnection(_connectionString))
            {
                await conn.OpenAsync(cancellationToken);

                using (var cmd = conn.CreateCommand())
                {
                    var whereClauses = new List<string>();
                    if (!string.IsNullOrWhiteSpace(subject))
                    {
                        whereClauses.Add("subject = @subject");
                        cmd.Parameters.AddWithValue("@subject", subject);
                    }
                    if (grade.HasValue)
                    {
                        whereClauses.Add("grade = @grade");
                        cmd.Parameters.AddWithValue("@grade", grade.Value);
                    }
                    if (!string.IsNullOrWhiteSpace(level))
                    {
                        whereClauses.Add("cognitive_level = @level");
                        cmd.Parameters.AddWithValue("@level", level);
                    }

                    string whereSql = whereClauses.Count > 0
                        ? "WHERE " + string.Join(" AND ", whereClauses)
                        : string.Empty;

                    cmd.CommandText = $"SELECT COUNT(*) FROM questions {whereSql};";
                    object? val = await cmd.ExecuteScalarAsync(cancellationToken);
                    return val != null ? Convert.ToInt32(val) : 0;
                }
            }
        }

        #endregion

        #region IExamMatrixService Implementation

        public async Task<ExamDraftResult> GenerateExamFromMatrixAsync(
            ExamMatrixConfig config,
            IQuestionBankService questionBank,
            CancellationToken cancellationToken = default)
        {
            if (config == null) throw new ArgumentNullException(nameof(config));
            if (questionBank == null) throw new ArgumentNullException(nameof(questionBank));

            var result = new ExamDraftResult
            {
                Title = config.Title,
                Subject = config.Subject,
                Grade = config.Grade,
                DurationMinutes = config.DurationMinutes
            };

            // Tìm kiếm câu hỏi cho 3 phần
            var part1Candidates = await questionBank.SearchQuestionsAsync(
                subject: config.Subject,
                grade: config.Grade,
                questionType: "MultipleChoice4",
                limit: 200,
                cancellationToken: cancellationToken);

            var part2Candidates = await questionBank.SearchQuestionsAsync(
                subject: config.Subject,
                grade: config.Grade,
                questionType: "TrueFalse4",
                limit: 100,
                cancellationToken: cancellationToken);

            var part3Candidates = await questionBank.SearchQuestionsAsync(
                subject: config.Subject,
                grade: config.Grade,
                questionType: "ShortAnswer",
                limit: 100,
                cancellationToken: cancellationToken);

            // Phân bổ câu hỏi theo mức độ nhận thức
            result.Part1Questions = AllocateQuestionsByCognitiveLevel(part1Candidates, config.Part1Count, config.CognitiveDistribution);
            result.Part2Questions = AllocateQuestionsByCognitiveLevel(part2Candidates, config.Part2Count, config.CognitiveDistribution);
            result.Part3Questions = AllocateQuestionsByCognitiveLevel(part3Candidates, config.Part3Count, config.CognitiveDistribution);

            result.Success = result.TotalSelectedQuestions > 0;
            if (!result.Success)
            {
                result.ErrorMessage = $"Chưa có đủ câu hỏi trong ngân hàng dữ liệu cho môn {config.Subject} lớp {config.Grade}.";
            }

            return result;
        }

        public Task<List<ExamVariant>> MixExamVariantsAsync(
            ExamDraftResult draft,
            int variantCount = 4,
            CancellationToken cancellationToken = default)
        {
            if (draft == null) throw new ArgumentNullException(nameof(draft));
            if (variantCount < 1) variantCount = 4;

            var variants = new List<ExamVariant>();

            for (int i = 0; i < variantCount; i++)
            {
                int examCodeNumber = 101 + i;
                var variant = new ExamVariant
                {
                    ExamCode = examCodeNumber.ToString()
                };

                var rng = new Random(examCodeNumber * 10007);

                // 1. Đảo Phần I (Trắc nghiệm 4 lựa chọn)
                var mixedPart1 = new List<QuestionItem>();
                var part1Order = draft.Part1Questions.OrderBy(_ => rng.Next()).ToList();

                int qNumber = 1;
                foreach (var origQ in part1Order)
                {
                    var clonedQ = CloneQuestion(origQ);

                    // Đảo các phương án A, B, C, D
                    if (clonedQ.Options != null && clonedQ.Options.Count > 1)
                    {
                        string origCorrectLetter = clonedQ.CorrectAnswer.Trim().ToUpperInvariant();
                        string origCorrectText = clonedQ.Options.ContainsKey(origCorrectLetter)
                            ? clonedQ.Options[origCorrectLetter]
                            : string.Empty;

                        var optionValues = clonedQ.Options.Values.OrderBy(_ => rng.Next()).ToList();
                        var newOptions = new Dictionary<string, string>();
                        string[] letters = { "A", "B", "C", "D", "E", "F" };

                        string newCorrectLetter = "A";
                        for (int optIdx = 0; optIdx < optionValues.Count; optIdx++)
                        {
                            string l = optIdx < letters.Length ? letters[optIdx] : $"Opt{optIdx + 1}";
                            newOptions[l] = optionValues[optIdx];

                            if (!string.IsNullOrEmpty(origCorrectText) && optionValues[optIdx] == origCorrectText)
                            {
                                newCorrectLetter = l;
                            }
                        }

                        clonedQ.Options = newOptions;
                        clonedQ.CorrectAnswer = newCorrectLetter;
                    }

                    mixedPart1.Add(clonedQ);
                    variant.AnswerKey[qNumber] = clonedQ.CorrectAnswer;
                    qNumber++;
                }
                variant.Part1Questions = mixedPart1;

                // 2. Đảo Phần II (Đúng/Sai 4 ý)
                var part2Order = draft.Part2Questions.OrderBy(_ => rng.Next()).ToList();
                foreach (var q in part2Order)
                {
                    variant.Part2Questions.Add(CloneQuestion(q));
                    variant.AnswerKey[qNumber] = q.CorrectAnswer;
                    qNumber++;
                }

                // 3. Đảo Phần III (Trả lời ngắn)
                var part3Order = draft.Part3Questions.OrderBy(_ => rng.Next()).ToList();
                foreach (var q in part3Order)
                {
                    variant.Part3Questions.Add(CloneQuestion(q));
                    variant.AnswerKey[qNumber] = q.CorrectAnswer;
                    qNumber++;
                }

                variants.Add(variant);
            }

            return Task.FromResult(variants);
        }

        #endregion

        #region Helper Methods

        private async Task EnsureInitializedAsync(CancellationToken cancellationToken)
        {
            if (!_isInitialized)
            {
                await InitializeDatabaseAsync(cancellationToken);
            }
        }

        private static QuestionItem ReadQuestionFromReader(SqliteDataReader reader)
        {
            var item = new QuestionItem
            {
                Id = reader.GetInt64(reader.GetOrdinal("id")),
                QuestionCode = reader.IsDBNull(reader.GetOrdinal("question_code")) ? string.Empty : reader.GetString(reader.GetOrdinal("question_code")),
                Subject = reader.IsDBNull(reader.GetOrdinal("subject")) ? "Toán" : reader.GetString(reader.GetOrdinal("subject")),
                Grade = reader.IsDBNull(reader.GetOrdinal("grade")) ? 12 : reader.GetInt32(reader.GetOrdinal("grade")),
                Topic = reader.IsDBNull(reader.GetOrdinal("topic")) ? string.Empty : reader.GetString(reader.GetOrdinal("topic")),
                CognitiveLevel = reader.IsDBNull(reader.GetOrdinal("cognitive_level")) ? "Thông hiểu" : reader.GetString(reader.GetOrdinal("cognitive_level")),
                QuestionType = reader.IsDBNull(reader.GetOrdinal("question_type")) ? "MultipleChoice4" : reader.GetString(reader.GetOrdinal("question_type")),
                Content = reader.IsDBNull(reader.GetOrdinal("content")) ? string.Empty : reader.GetString(reader.GetOrdinal("content")),
                CorrectAnswer = reader.IsDBNull(reader.GetOrdinal("correct_answer")) ? string.Empty : reader.GetString(reader.GetOrdinal("correct_answer")),
                Explanation = reader.IsDBNull(reader.GetOrdinal("explanation")) ? string.Empty : reader.GetString(reader.GetOrdinal("explanation")),
                TikzCode = reader.IsDBNull(reader.GetOrdinal("tikz_code")) ? string.Empty : reader.GetString(reader.GetOrdinal("tikz_code")),
                Source = reader.IsDBNull(reader.GetOrdinal("source")) ? string.Empty : reader.GetString(reader.GetOrdinal("source")),
                RawDataJson = reader.IsDBNull(reader.GetOrdinal("raw_data_json")) ? string.Empty : reader.GetString(reader.GetOrdinal("raw_data_json")),
            };

            string optJson = reader.IsDBNull(reader.GetOrdinal("options_json")) ? string.Empty : reader.GetString(reader.GetOrdinal("options_json"));
            if (!string.IsNullOrWhiteSpace(optJson))
            {
                try
                {
                    item.Options = JsonSerializer.Deserialize<Dictionary<string, string>>(optJson) ?? new Dictionary<string, string>();
                }
                catch
                {
                    item.Options = new Dictionary<string, string>();
                }
            }

            // Đọc trường images từ cột SQLite hoặc fallback kiểm tra raw_data_json
            int imgOrd = -1;
            try { imgOrd = reader.GetOrdinal("images"); } catch { }
            if (imgOrd >= 0 && !reader.IsDBNull(imgOrd))
            {
                string imgStr = reader.GetString(imgOrd);
                item.Images = ImageHelper.NormalizeImageField(imgStr);
            }
            else if (!string.IsNullOrWhiteSpace(item.RawDataJson))
            {
                try
                {
                    using var doc = JsonDocument.Parse(item.RawDataJson);
                    if (doc.RootElement.TryGetProperty("images", out var imgElem))
                    {
                        if (imgElem.ValueKind == JsonValueKind.Array)
                        {
                            item.Images = imgElem.EnumerateArray()
                                .Select(x => x.GetString())
                                .Where(x => !string.IsNullOrEmpty(x))
                                .ToList()!;
                        }
                        else if (imgElem.ValueKind == JsonValueKind.String)
                        {
                            item.Images = ImageHelper.NormalizeImageField(imgElem.GetString());
                        }
                    }
                    else if (doc.RootElement.TryGetProperty("question_image", out var qiElem))
                    {
                        item.Images = ImageHelper.NormalizeImageField(qiElem.GetString());
                    }
                }
                catch
                {
                    // Ignore json parsing issues
                }
            }

            string createdStr = reader.IsDBNull(reader.GetOrdinal("created_at")) ? string.Empty : reader.GetString(reader.GetOrdinal("created_at"));
            if (DateTime.TryParse(createdStr, out var dtCreated)) item.CreatedAt = dtCreated;

            string updatedStr = reader.IsDBNull(reader.GetOrdinal("updated_at")) ? string.Empty : reader.GetString(reader.GetOrdinal("updated_at"));
            if (DateTime.TryParse(updatedStr, out var dtUpdated)) item.UpdatedAt = dtUpdated;

            return item;
        }

        private static List<QuestionItem> AllocateQuestionsByCognitiveLevel(
            List<QuestionItem> pool,
            int targetCount,
            Dictionary<string, int> distribution)
        {
            if (pool.Count <= targetCount)
            {
                return new List<QuestionItem>(pool);
            }

            var selected = new List<QuestionItem>();
            var grouped = pool.GroupBy(q => q.CognitiveLevel).ToDictionary(g => g.Key, g => g.ToList());

            foreach (var kvp in distribution)
            {
                string level = kvp.Key;
                int percent = kvp.Value;
                int countNeeded = (int)Math.Round((double)targetCount * percent / 100.0);

                if (grouped.TryGetValue(level, out var list))
                {
                    selected.AddRange(list.Take(countNeeded));
                }
            }

            // Nếu còn thiếu thì lấy thêm từ pool
            if (selected.Count < targetCount)
            {
                var remaining = pool.Except(selected).Take(targetCount - selected.Count);
                selected.AddRange(remaining);
            }

            return selected.Take(targetCount).ToList();
        }

        private static QuestionItem CloneQuestion(QuestionItem orig)
        {
            return new QuestionItem
            {
                Id = orig.Id,
                QuestionCode = orig.QuestionCode,
                Subject = orig.Subject,
                Grade = orig.Grade,
                Topic = orig.Topic,
                CognitiveLevel = orig.CognitiveLevel,
                QuestionType = orig.QuestionType,
                Content = orig.Content,
                Options = orig.Options != null ? new Dictionary<string, string>(orig.Options) : new Dictionary<string, string>(),
                CorrectAnswer = orig.CorrectAnswer,
                Explanation = orig.Explanation,
                TikzCode = orig.TikzCode,
                Images = orig.Images != null ? new List<string>(orig.Images) : new List<string>(),
                Source = orig.Source,
                RawDataJson = orig.RawDataJson,
                CreatedAt = orig.CreatedAt,
                UpdatedAt = orig.UpdatedAt
            };
        }

        /// <summary>
        /// Nạp các câu hỏi mẫu chuẩn Bộ Giáo dục & Đào tạo 2025 vào ngân hàng khi CSDL mới khởi tạo.
        /// </summary>
        public async Task SeedDefaultQuestionsAsync(CancellationToken cancellationToken = default)
        {
            await EnsureInitializedAsync(cancellationToken);
            int currentCount = await GetQuestionCountAsync(cancellationToken: cancellationToken);
            if (currentCount > 0) return;

            var defaultQuestions = new List<QuestionItem>
            {
                new QuestionItem
                {
                    QuestionCode = "TOAN12_C1_001",
                    Subject = "Toán",
                    Grade = 12,
                    Topic = "Khảo sát hàm số",
                    CognitiveLevel = "Nhận biết",
                    QuestionType = "MultipleChoice4",
                    Content = "Cho hàm số $y = f(x)$ có bảng biến thiên trên đoạn $[-2; 3]$. Giá trị cực đại của hàm số đã cho bằng:",
                    Options = new Dictionary<string, string> { ["A"] = "5", ["B"] = "2", ["C"] = "-3", ["D"] = "0" },
                    CorrectAnswer = "A",
                    Explanation = "Dựa vào bảng biến thiên, tại điểm $x = 1$, hàm số đạt cực đại với giá trị cực đại $y_{CĐ} = 5$.",
                    Source = "Đề tham khảo Bộ GD&ĐT 2025"
                },
                new QuestionItem
                {
                    QuestionCode = "TOAN12_C1_002",
                    Subject = "Toán",
                    Grade = 12,
                    Topic = "Khảo sát hàm số",
                    CognitiveLevel = "Thông hiểu",
                    QuestionType = "MultipleChoice4",
                    Content = "Hàm số $y = x^3 - 3x^2 + 2$ đồng biến trên khoảng nào dưới đây?",
                    Options = new Dictionary<string, string> { ["A"] = "$(2; +\\infty)$", ["B"] = "$(0; 2)$", ["C"] = "$(-\\infty; 2)$", ["D"] = "$(0; +\\infty)$" },
                    CorrectAnswer = "A",
                    Explanation = "Ta có $y' = 3x^2 - 6x = 3x(x - 2)$. $y' > 0 \\Leftrightarrow x \\in (-\\infty; 0) \\cup (2; +\\infty)$. Do đó hàm số đồng biến trên $(2; +\\infty)$.",
                    Source = "Đề tham khảo Bộ GD&ĐT 2025"
                },
                new QuestionItem
                {
                    QuestionCode = "TOAN12_C2_001",
                    Subject = "Toán",
                    Grade = 12,
                    Topic = "Nguyên hàm - Tích phân",
                    CognitiveLevel = "Thông hiểu",
                    QuestionType = "MultipleChoice4",
                    Content = "Biết $\\int_{1}^{3} f(x) dx = 4$ và $\\int_{1}^{3} g(x) dx = -1$. Tính tích phân $I = \\int_{1}^{3} [3f(x) - 2g(x)] dx$.",
                    Options = new Dictionary<string, string> { ["A"] = "14", ["B"] = "10", ["C"] = "12", ["D"] = "6" },
                    CorrectAnswer = "A",
                    Explanation = "Ta có $I = 3\\int_{1}^{3} f(x) dx - 2\\int_{1}^{3} g(x) dx = 3(4) - 2(-1) = 12 + 2 = 14$.",
                    Source = "Đề tham khảo Bộ GD&ĐT 2025"
                },
                new QuestionItem
                {
                    QuestionCode = "TOAN12_C3_001",
                    Subject = "Toán",
                    Grade = 12,
                    Topic = "Tọa độ Oxyz",
                    CognitiveLevel = "Nhận biết",
                    QuestionType = "MultipleChoice4",
                    Content = "Trong không gian $Oxyz$, cho mặt phẳng $(P): 2x - 3y + z - 5 = 0$. Véctơ nào dưới đây là một véctơ pháp tuyến của $(P)$?",
                    Options = new Dictionary<string, string> { ["A"] = "$\\vec{n} = (2; -3; 1)$", ["B"] = "$\\vec{n} = (2; 3; 1)$", ["C"] = "$\\vec{n} = (-2; 3; 1)$", ["D"] = "$\\vec{n} = (2; -3; -5)$" },
                    CorrectAnswer = "A",
                    Explanation = "Từ phương trình mặt phẳng, hệ số trước $x, y, z$ là $(2; -3; 1)$, chính là tọa độ véctơ pháp tuyến.",
                    Source = "Đề tham khảo Bộ GD&ĐT 2025"
                },
                new QuestionItem
                {
                    QuestionCode = "TOAN12_C3_002",
                    Subject = "Toán",
                    Grade = 12,
                    Topic = "Tọa độ Oxyz",
                    CognitiveLevel = "Thông hiểu",
                    QuestionType = "MultipleChoice4",
                    Content = "Trong không gian $Oxyz$, mặt cầu $(S): (x - 1)^2 + (y + 2)^2 + (z - 3)^2 = 16$ có tọa độ tâm $I$ và bán kính $R$ là:",
                    Options = new Dictionary<string, string> { ["A"] = "$I(1; -2; 3), R = 4$", ["B"] = "$I(-1; 2; -3), R = 4$", ["C"] = "$I(1; -2; 3), R = 16$", ["D"] = "$I(-1; 2; -3), R = 16$" },
                    CorrectAnswer = "A",
                    Explanation = "Phương trình mặt cầu có tâm $I(a; b; c) = (1; -2; 3)$ và bán kính $R = \\sqrt{16} = 4$.",
                    Source = "Đề tham khảo Bộ GD&ĐT 2025"
                },
                new QuestionItem
                {
                    QuestionCode = "TOAN12_TF_001",
                    Subject = "Toán",
                    Grade = 12,
                    Topic = "Khảo sát hàm số",
                    CognitiveLevel = "Vận dụng",
                    QuestionType = "TrueFalse4",
                    Content = "Cho hàm số $f(x) = x^3 - 3x^2 + 2$. Xét tính đúng sai của các khẳng định sau:",
                    Options = new Dictionary<string, string> {
                        ["a"] = "Hàm số đồng biến trên khoảng $(0; 2)$",
                        ["b"] = "Điểm cực đại của đồ thị hàm số là $(0; 2)$",
                        ["c"] = "Giá trị nhỏ nhất của hàm số trên đoạn $[0; 3]$ bằng $-2$",
                        ["d"] = "Đường thẳng $y = m$ cắt đồ thị tại 3 điểm phân biệt khi $-2 < m < 2$"
                    },
                    CorrectAnswer = "S,Đ,Đ,Đ",
                    Explanation = "a) Sai vì trên $(0;2)$, $y' < 0$ nên nghịch biến. b) Đúng vì tại $x=0$, $y=2$. c) Đúng vì $f(2) = -2$. d) Đúng vì $y_{CT} = -2 < m < y_{CĐ} = 2$.",
                    Source = "Định dạng cấu trúc mới BGD 2025"
                },
                new QuestionItem
                {
                    QuestionCode = "TOAN12_SA_001",
                    Subject = "Toán",
                    Grade = 12,
                    Topic = "Ứng dụng đạo hàm",
                    CognitiveLevel = "Vận dụng cao",
                    QuestionType = "ShortAnswer",
                    Content = "Một công ty sản xuất hộp quà hình hộp chữ nhật không nắp với đáy là hình vuông, thể tích bằng $500\\text{ cm}^3$. Chiều cao của hộp quà (theo cm) để lượng vật liệu làm hộp là ít nhất bằng bao nhiêu?",
                    Options = new Dictionary<string, string>(),
                    CorrectAnswer = "5",
                    Explanation = "Gọi cạnh đáy là $x$, chiều cao là $h$. $V = x^2 h = 500 \\Rightarrow h = \\frac{500}{x^2}$. Diện tích toàn phần không nắp: $S(x) = x^2 + 4xh = x^2 + \\frac{2000}{x}$. $S'(x) = 2x - \\frac{2000}{x^2} = 0 \\Leftrightarrow x = 10$. Suy ra $h = 5\\text{ cm}$.",
                    Source = "Định dạng cấu trúc mới BGD 2025"
                },
                new QuestionItem
                {
                    QuestionCode = "TOAN11_C1_001",
                    Subject = "Toán",
                    Grade = 11,
                    Topic = "Dãy số & Cấp số",
                    CognitiveLevel = "Nhận biết",
                    QuestionType = "MultipleChoice4",
                    Content = "Cho cấp số nhân $(u_n)$ có số hạng đầu $u_1 = 3$ và công bội $q = 2$. Số hạng thứ 5 của cấp số nhân là:",
                    Options = new Dictionary<string, string> { ["A"] = "48", ["B"] = "24", ["C"] = "96", ["D"] = "162" },
                    CorrectAnswer = "A",
                    Explanation = "Áp dụng công thức số hạng tổng quát $u_n = u_1 \\cdot q^{n-1} \\Rightarrow u_5 = 3 \\cdot 2^4 = 48$.",
                    Source = "Sách giáo khoa Toán 11 mới"
                },
                new QuestionItem
                {
                    QuestionCode = "TOAN10_C1_001",
                    Subject = "Toán",
                    Grade = 10,
                    Topic = "Véctơ & Hệ thức lượng",
                    CognitiveLevel = "Thông hiểu",
                    QuestionType = "MultipleChoice4",
                    Content = "Cho tam giác $ABC$ vuông cân tại $A$ có $AB = AC = a$. Độ dài của véctơ tổng $\\vec{AB} + \\vec{AC}$ bằng:",
                    Options = new Dictionary<string, string> { ["A"] = "$a\\sqrt{2}$", ["B"] = "$2a$", ["C"] = "$\\frac{a\\sqrt{2}}{2}$", ["D"] = "$a$" },
                    CorrectAnswer = "A",
                    Explanation = "Dựng hình vuông $ABDC$, ta có $\\vec{AB} + \\vec{AC} = \\vec{AD}$. Độ dài $|\\vec{AD}| = AD = \\sqrt{AB^2 + AC^2} = a\\sqrt{2}$.",
                    Source = "Sách giáo khoa Toán 10 mới"
                }
            };

            foreach (var q in defaultQuestions)
            {
                await InsertQuestionAsync(q, cancellationToken);
            }
        }

        #endregion
    }
}
