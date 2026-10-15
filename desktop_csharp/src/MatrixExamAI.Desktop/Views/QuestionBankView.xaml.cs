using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using System.Text.RegularExpressions;
using System.Threading.Tasks;
using System.Windows;
using System.Windows.Controls;
using MatrixExamAI.Desktop.Services;
using MatrixExamAI.Shared.Extensibility;
using Microsoft.Data.Sqlite;

namespace MatrixExamAI.Desktop.Views
{
    public class QuestionViewModel
    {
        public string Id { get; set; } = "";
        public string Level { get; set; } = "";
        public string Topic { get; set; } = "";
        public string ContentPreview { get; set; } = "";
        public string CorrectAnswer { get; set; } = "";
        public string QuestionType { get; set; } = "";
        public QuestionItem? RawItem { get; set; }
    }

    /// <summary>
    /// Adapter tương thích hai chiều giữa Python SQLite Schema (core/models.py & storage/database.py)
    /// và C# SQLite Schema (MatrixExamAI.Shared).
    /// </summary>
    public static class SqliteSchemaAdapter
    {
        public static string ResolveDatabasePath()
        {
            // 0. Ưu tiên đường dẫn cấu hình bởi người dùng trong Cài đặt
            string customBankDir = StorageLocationService.GetQuestionBankDirectory();
            if (!string.IsNullOrEmpty(customBankDir))
            {
                string customDb = Path.Combine(customBankDir, "question_bank.db");
                if (File.Exists(customDb))
                {
                    return customDb;
                }
            }

            // 1. Ưu tiên đường dẫn SQLite dùng chung của Python MEA v5.0: ~/.exam_generator/question_bank.db
            string userProfile = Environment.GetFolderPath(Environment.SpecialFolder.UserProfile);
            string pyDbPath = Path.Combine(userProfile, ".exam_generator", "question_bank.db");
            if (File.Exists(pyDbPath))
            {
                return pyDbPath;
            }

            // 2. Fallback đường dẫn LocalAppData của C#: %LocalAppData%/MatrixExamAI/question_bank.db
            string localAppData = Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData);
            string csDbPath = Path.Combine(localAppData, "MatrixExamAI", "question_bank.db");
            if (File.Exists(csDbPath))
            {
                return csDbPath;
            }

            // Mặc định tạo thư mục nếu chưa có
            if (!string.IsNullOrEmpty(customBankDir))
            {
                if (!Directory.Exists(customBankDir))
                {
                    Directory.CreateDirectory(customBankDir);
                }
                return Path.Combine(customBankDir, "question_bank.db");
            }

            string pyDir = Path.Combine(userProfile, ".exam_generator");
            if (!Directory.Exists(pyDir))
            {
                Directory.CreateDirectory(pyDir);
            }
            return pyDbPath;
        }

        public static string GetActiveConnectionString()
        {
            return $"Data Source={ResolveDatabasePath()};";
        }

        public static string MapPythonLevelToVietnamese(string? level)
        {
            if (string.IsNullOrWhiteSpace(level)) return "Thông hiểu";
            string upper = level.Trim().ToUpperInvariant();
            switch (upper)
            {
                case "NB": return "Nhận biết";
                case "TH": return "Thông hiểu";
                case "VD": return "Vận dụng";
                case "VDC": return "Vận dụng cao";
                case "NHẬN BIẾT": return "Nhận biết";
                case "THÔNG HIỂU": return "Thông hiểu";
                case "VẬN DỤNG": return "Vận dụng";
                case "VẬN DỤNG CAO": return "Vận dụng cao";
                default: return level;
            }
        }

        public static string MapVietnameseLevelToPython(string? level)
        {
            if (string.IsNullOrWhiteSpace(level)) return "TH";
            string trimmed = level.Trim();
            if (trimmed.Equals("Nhận biết", StringComparison.OrdinalIgnoreCase) || trimmed.Equals("NB", StringComparison.OrdinalIgnoreCase)) return "NB";
            if (trimmed.Equals("Thông hiểu", StringComparison.OrdinalIgnoreCase) || trimmed.Equals("TH", StringComparison.OrdinalIgnoreCase)) return "TH";
            if (trimmed.Equals("Vận dụng", StringComparison.OrdinalIgnoreCase) || trimmed.Equals("VD", StringComparison.OrdinalIgnoreCase)) return "VD";
            if (trimmed.Equals("Vận dụng cao", StringComparison.OrdinalIgnoreCase) || trimmed.Equals("VDC", StringComparison.OrdinalIgnoreCase)) return "VDC";
            return "TH";
        }

        public static string MapPythonQtypeToCSharp(string? qtype)
        {
            if (string.IsNullOrWhiteSpace(qtype)) return "MultipleChoice4";
            string upper = qtype.Trim().ToUpperInvariant();
            switch (upper)
            {
                case "TN": return "MultipleChoice4";
                case "DS": return "TrueFalse4";
                case "TLN": return "ShortAnswer";
                case "TL": return "Essay";
                default: return qtype;
            }
        }

        public static string MapCSharpQtypeToPython(string? qtype)
        {
            if (string.IsNullOrWhiteSpace(qtype)) return "TN";
            string upper = qtype.Trim().ToUpperInvariant();
            if (upper.Contains("MULTIPLECHOICE") || upper == "TN") return "TN";
            if (upper.Contains("TRUEFALSE") || upper == "DS") return "DS";
            if (upper.Contains("SHORT") || upper == "TLN") return "TLN";
            if (upper.Contains("ESSAY") || upper == "TL") return "TL";
            return "TN";
        }

        public static async Task<List<QuestionItem>> LoadQuestionsFromDatabaseAsync(
            string? connectionString = null,
            string? keyword = null,
            string? levelFilter = null)
        {
            string connStr = connectionString ?? GetActiveConnectionString();
            var results = new List<QuestionItem>();

            using (var conn = new SqliteConnection(connStr))
            {
                await conn.OpenAsync();

                // Kiểm tra xem bảng questions có tồn tại không
                using (var checkCmd = conn.CreateCommand())
                {
                    checkCmd.CommandText = "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='questions';";
                    long tableCount = Convert.ToInt64(await checkCmd.ExecuteScalarAsync());
                    if (tableCount == 0) return results;
                }

                // Kiểm tra các cột trong bảng questions
                var columns = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
                using (var infoCmd = conn.CreateCommand())
                {
                    infoCmd.CommandText = "PRAGMA table_info(questions);";
                    using var infoReader = await infoCmd.ExecuteReaderAsync();
                    while (await infoReader.ReadAsync())
                    {
                        columns.Add(infoReader.GetString(1));
                    }
                }

                bool hasPythonSchema = columns.Contains("level") && columns.Contains("question");
                bool hasCSharpSchema = columns.Contains("cognitive_level") && columns.Contains("content");

                string sql;
                if (hasCSharpSchema)
                {
                    sql = "SELECT id, question_code, subject, grade, topic, cognitive_level, question_type, content, options_json, correct_answer, explanation, tikz_code, source, raw_data_json, created_at FROM questions ORDER BY id DESC;";
                }
                else if (hasPythonSchema)
                {
                    sql = "SELECT id, subject, grade, topic, level, qtype, question, data_json, created_at, source, " +
                          (columns.Contains("question_id") ? "question_id" : "'' AS question_id") +
                          " FROM questions ORDER BY id DESC;";
                }
                else
                {
                    return results;
                }

                using (var queryCmd = conn.CreateCommand())
                {
                    queryCmd.CommandText = sql;
                    using var reader = await queryCmd.ExecuteReaderAsync();
                    while (await reader.ReadAsync())
                    {
                        QuestionItem item;
                        if (hasCSharpSchema)
                        {
                            item = ReadCSharpQuestion(reader);
                        }
                        else
                        {
                            item = ReadPythonQuestion(reader);
                        }

                        // Lọc theo từ khóa
                        if (!string.IsNullOrWhiteSpace(keyword))
                        {
                            string kw = keyword.Trim().ToLowerInvariant();
                            bool matchContent = item.Content?.ToLowerInvariant().Contains(kw) ?? false;
                            bool matchTopic = item.Topic?.ToLowerInvariant().Contains(kw) ?? false;
                            bool matchCode = item.QuestionCode?.ToLowerInvariant().Contains(kw) ?? false;
                            bool matchId = item.Id.ToString().Contains(kw);
                            if (!matchContent && !matchTopic && !matchCode && !matchId)
                            {
                                continue;
                            }
                        }

                        // Lọc theo mức độ nhận thức
                        if (!string.IsNullOrWhiteSpace(levelFilter) && levelFilter != "Tất cả mức độ" && levelFilter != "Tất cả")
                        {
                            string normFilter = MapPythonLevelToVietnamese(levelFilter);
                            string itemLevel = MapPythonLevelToVietnamese(item.CognitiveLevel);
                            if (!itemLevel.Equals(normFilter, StringComparison.OrdinalIgnoreCase))
                            {
                                continue;
                            }
                        }

                        results.Add(item);
                    }
                }
            }

            return results;
        }

        private static QuestionItem ReadCSharpQuestion(SqliteDataReader reader)
        {
            var item = new QuestionItem
            {
                Id = reader.GetInt64(reader.GetOrdinal("id")),
                QuestionCode = reader.IsDBNull(reader.GetOrdinal("question_code")) ? "" : reader.GetString(reader.GetOrdinal("question_code")),
                Subject = reader.IsDBNull(reader.GetOrdinal("subject")) ? "Toán" : reader.GetString(reader.GetOrdinal("subject")),
                Grade = reader.IsDBNull(reader.GetOrdinal("grade")) ? 12 : reader.GetInt32(reader.GetOrdinal("grade")),
                Topic = reader.IsDBNull(reader.GetOrdinal("topic")) ? "" : reader.GetString(reader.GetOrdinal("topic")),
                CognitiveLevel = reader.IsDBNull(reader.GetOrdinal("cognitive_level")) ? "Thông hiểu" : reader.GetString(reader.GetOrdinal("cognitive_level")),
                QuestionType = reader.IsDBNull(reader.GetOrdinal("question_type")) ? "MultipleChoice4" : reader.GetString(reader.GetOrdinal("question_type")),
                Content = reader.IsDBNull(reader.GetOrdinal("content")) ? "" : reader.GetString(reader.GetOrdinal("content")),
                CorrectAnswer = reader.IsDBNull(reader.GetOrdinal("correct_answer")) ? "" : reader.GetString(reader.GetOrdinal("correct_answer")),
                Explanation = reader.IsDBNull(reader.GetOrdinal("explanation")) ? "" : reader.GetString(reader.GetOrdinal("explanation")),
                TikzCode = reader.IsDBNull(reader.GetOrdinal("tikz_code")) ? "" : reader.GetString(reader.GetOrdinal("tikz_code")),
                Source = reader.IsDBNull(reader.GetOrdinal("source")) ? "" : reader.GetString(reader.GetOrdinal("source")),
                RawDataJson = reader.IsDBNull(reader.GetOrdinal("raw_data_json")) ? "" : reader.GetString(reader.GetOrdinal("raw_data_json"))
            };

            string optJson = reader.IsDBNull(reader.GetOrdinal("options_json")) ? "" : reader.GetString(reader.GetOrdinal("options_json"));
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

            return item;
        }

        private static QuestionItem ReadPythonQuestion(SqliteDataReader reader)
        {
            long id = reader.GetInt64(reader.GetOrdinal("id"));
            string subject = reader.IsDBNull(reader.GetOrdinal("subject")) ? "Toán" : reader.GetString(reader.GetOrdinal("subject"));
            string gradeStr = reader.IsDBNull(reader.GetOrdinal("grade")) ? "12" : reader.GetString(reader.GetOrdinal("grade"));
            int.TryParse(Regex.Replace(gradeStr, @"\D", ""), out int grade);
            if (grade <= 0) grade = 12;

            string topic = reader.IsDBNull(reader.GetOrdinal("topic")) ? "" : reader.GetString(reader.GetOrdinal("topic"));
            string pyLevel = reader.IsDBNull(reader.GetOrdinal("level")) ? "TH" : reader.GetString(reader.GetOrdinal("level"));
            string pyQtype = reader.IsDBNull(reader.GetOrdinal("qtype")) ? "TN" : reader.GetString(reader.GetOrdinal("qtype"));
            string content = reader.IsDBNull(reader.GetOrdinal("question")) ? "" : reader.GetString(reader.GetOrdinal("question"));
            string dataJson = reader.IsDBNull(reader.GetOrdinal("data_json")) ? "" : reader.GetString(reader.GetOrdinal("data_json"));
            string source = reader.IsDBNull(reader.GetOrdinal("source")) ? "" : reader.GetString(reader.GetOrdinal("source"));
            string qid = reader.IsDBNull(reader.GetOrdinal("question_id")) ? "" : reader.GetString(reader.GetOrdinal("question_id"));

            var item = new QuestionItem
            {
                Id = id,
                QuestionCode = !string.IsNullOrEmpty(qid) ? qid : $"Q{id:D4}",
                Subject = subject,
                Grade = grade,
                Topic = topic,
                CognitiveLevel = MapPythonLevelToVietnamese(pyLevel),
                QuestionType = MapPythonQtypeToCSharp(pyQtype),
                Content = content,
                Source = source,
                RawDataJson = dataJson
            };

            // Trích xuất chi tiết từ data_json của Python
            if (!string.IsNullOrWhiteSpace(dataJson))
            {
                try
                {
                    using var doc = JsonDocument.Parse(dataJson);
                    var root = doc.RootElement;

                    if (root.TryGetProperty("options", out var optsElem) && optsElem.ValueKind == JsonValueKind.Object)
                    {
                        var dict = new Dictionary<string, string>();
                        foreach (var prop in optsElem.EnumerateObject())
                        {
                            dict[prop.Name] = prop.Value.GetString() ?? "";
                        }
                        item.Options = dict;
                    }

                    if (root.TryGetProperty("answer", out var ansElem))
                    {
                        item.CorrectAnswer = ansElem.GetString() ?? "";
                    }
                    else if (root.TryGetProperty("correct_answer", out var caElem))
                    {
                        item.CorrectAnswer = caElem.GetString() ?? "";
                    }

                    if (root.TryGetProperty("solution", out var solElem))
                    {
                        item.Explanation = solElem.GetString() ?? "";
                    }

                    if (root.TryGetProperty("tikz_code", out var tikzElem))
                    {
                        item.TikzCode = tikzElem.GetString() ?? "";
                    }

                    if (string.IsNullOrEmpty(item.Content) && root.TryGetProperty("question", out var qElem))
                    {
                        item.Content = qElem.GetString() ?? "";
                    }
                }
                catch
                {
                    // Ignore json errors
                }
            }

            return item;
        }

        public static async Task<int> ImportQuestionsAsync(IEnumerable<QuestionItem> questions, string? connectionString = null)
        {
            if (questions == null) return 0;
            string connStr = connectionString ?? GetActiveConnectionString();
            var list = questions.ToList();
            if (list.Count == 0) return 0;

            int count = 0;
            using (var conn = new SqliteConnection(connStr))
            {
                await conn.OpenAsync();

                // Đảm bảo schema tương thích
                using (var initCmd = conn.CreateCommand())
                {
                    initCmd.CommandText = @"
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
                    ";
                    await initCmd.ExecuteNonQueryAsync();
                }

                foreach (var q in list)
                {
                    using (var insertCmd = conn.CreateCommand())
                    {
                        insertCmd.CommandText = @"
                            INSERT INTO questions (
                                question_code, subject, grade, topic, cognitive_level,
                                question_type, content, options_json, correct_answer,
                                explanation, tikz_code, source, raw_data_json, created_at, updated_at
                            ) VALUES (
                                @code, @subject, @grade, @topic, @level,
                                @qtype, @content, @options, @answer,
                                @explanation, @tikz, @source, @raw, @created, @updated
                            );
                        ";

                        insertCmd.Parameters.AddWithValue("@code", q.QuestionCode ?? $"Q{DateTime.Now.Ticks % 100000}");
                        insertCmd.Parameters.AddWithValue("@subject", q.Subject ?? "Toán");
                        insertCmd.Parameters.AddWithValue("@grade", q.Grade > 0 ? q.Grade : 12);
                        insertCmd.Parameters.AddWithValue("@topic", q.Topic ?? "");
                        insertCmd.Parameters.AddWithValue("@level", MapPythonLevelToVietnamese(q.CognitiveLevel));
                        insertCmd.Parameters.AddWithValue("@qtype", q.QuestionType ?? "MultipleChoice4");
                        insertCmd.Parameters.AddWithValue("@content", q.Content ?? "");
                        insertCmd.Parameters.AddWithValue("@options", JsonSerializer.Serialize(q.Options ?? new Dictionary<string, string>()));
                        insertCmd.Parameters.AddWithValue("@answer", q.CorrectAnswer ?? "");
                        insertCmd.Parameters.AddWithValue("@explanation", q.Explanation ?? "");
                        insertCmd.Parameters.AddWithValue("@tikz", q.TikzCode ?? "");
                        insertCmd.Parameters.AddWithValue("@source", q.Source ?? "Imported");
                        insertCmd.Parameters.AddWithValue("@raw", q.RawDataJson ?? "");
                        insertCmd.Parameters.AddWithValue("@created", DateTime.Now.ToString("o"));
                        insertCmd.Parameters.AddWithValue("@updated", DateTime.Now.ToString("o"));

                        await insertCmd.ExecuteNonQueryAsync();
                        count++;
                    }
                }
            }

            return count;
        }

        public static async Task<int> DeleteQuestionsAsync(IEnumerable<long> ids, string? connectionString = null)
        {
            if (ids == null) return 0;
            var idList = ids.ToList();
            if (idList.Count == 0) return 0;

            string connStr = connectionString ?? GetActiveConnectionString();
            int deleted = 0;
            using (var conn = new SqliteConnection(connStr))
            {
                await conn.OpenAsync();
                using var trans = conn.BeginTransaction();
                using var cmd = conn.CreateCommand();
                cmd.Transaction = trans;
                cmd.CommandText = "DELETE FROM questions WHERE id = @id;";
                var p = cmd.Parameters.Add("@id", SqliteType.Integer);

                foreach (var id in idList)
                {
                    p.Value = id;
                    deleted += await cmd.ExecuteNonQueryAsync();
                }

                await trans.CommitAsync();
            }
            return deleted;
        }

        public static async Task<int> ClearAllQuestionsAsync(string? connectionString = null)
        {
            string connStr = connectionString ?? GetActiveConnectionString();
            int deleted = 0;
            using (var conn = new SqliteConnection(connStr))
            {
                await conn.OpenAsync();
                using var cmd = conn.CreateCommand();
                cmd.CommandText = "DELETE FROM questions;";
                deleted = await cmd.ExecuteNonQueryAsync();

                using var vacCmd = conn.CreateCommand();
                vacCmd.CommandText = "VACUUM;";
                await vacCmd.ExecuteNonQueryAsync();
            }
            return deleted;
        }
    }

    public partial class QuestionBankView : UserControl
    {
        private readonly List<QuestionViewModel> _loadedQuestions = new List<QuestionViewModel>();
        private string _activeDbPath = string.Empty;

        public QuestionBankView()
        {
            InitializeComponent();
            _ = InitializeAndLoadDatabaseAsync();
        }

        private async Task InitializeAndLoadDatabaseAsync()
        {
            try
            {
                _activeDbPath = SqliteSchemaAdapter.ResolveDatabasePath();
                await RefreshQuestionsFromDatabaseAsync();
            }
            catch (Exception ex)
            {
                TxtEmptyBankHint.Visibility = Visibility.Visible;
                TxtBankCount.Text = "Tổng số: 0 câu hỏi";
                InfoBankNotification.Severity = Wpf.Ui.Controls.InfoBarSeverity.Warning;
                InfoBankNotification.Title = "Thông báo kết nối dữ liệu";
                InfoBankNotification.Message = $"Không thể tải ngân hàng câu hỏi: {ex.Message}";
                InfoBankNotification.IsOpen = true;
            }
        }

        public async Task RefreshQuestionsFromDatabaseAsync(string? keyword = null, string? levelFilter = null)
        {
            string kw = keyword ?? TxtSearch.Text?.Trim() ?? "";
            string lvl = levelFilter ?? (CmbLevelFilter.SelectedItem as ComboBoxItem)?.Content?.ToString() ?? "Tất cả mức độ";

            var items = await SqliteSchemaAdapter.LoadQuestionsFromDatabaseAsync(null, kw, lvl);

            _loadedQuestions.Clear();
            foreach (var item in items)
            {
                string preview = item.Content ?? "";
                if (preview.Length > 120)
                {
                    preview = preview.Substring(0, 120).Replace("\n", " ").Replace("\r", "") + "...";
                }

                _loadedQuestions.Add(new QuestionViewModel
                {
                    Id = !string.IsNullOrEmpty(item.QuestionCode) ? item.QuestionCode : $"Q{item.Id:D4}",
                    Level = item.CognitiveLevel,
                    Topic = item.Topic,
                    ContentPreview = preview,
                    CorrectAnswer = item.CorrectAnswer,
                    QuestionType = item.QuestionType,
                    RawItem = item
                });
            }

            GridQuestions.ItemsSource = null;
            GridQuestions.ItemsSource = _loadedQuestions;
            TxtBankCount.Text = $"Tổng số: {_loadedQuestions.Count} câu hỏi";
            TxtEmptyBankHint.Visibility = _loadedQuestions.Count == 0 ? Visibility.Visible : Visibility.Collapsed;

            InfoBankNotification.Severity = Wpf.Ui.Controls.InfoBarSeverity.Success;
            InfoBankNotification.Title = "Ngân hàng câu hỏi";
            InfoBankNotification.Message = $"Đã tải {_loadedQuestions.Count} câu hỏi từ cơ sở dữ liệu ({Path.GetFileName(_activeDbPath)}).";
            InfoBankNotification.IsOpen = true;
        }

        private async void BtnSearch_Click(object sender, RoutedEventArgs e)
        {
            string keyword = TxtSearch.Text?.Trim() ?? "";
            string levelFilter = (CmbLevelFilter.SelectedItem as ComboBoxItem)?.Content?.ToString() ?? "Tất cả mức độ";

            try
            {
                await RefreshQuestionsFromDatabaseAsync(keyword, levelFilter);
            }
            catch (Exception ex)
            {
                MessageBox.Show($"Lỗi tìm kiếm: {ex.Message}", "Lỗi", MessageBoxButton.OK, MessageBoxImage.Error);
            }
        }

        private async void BtnRefreshBank_Click(object sender, RoutedEventArgs e)
        {
            TxtSearch.Text = "";
            CmbLevelFilter.SelectedIndex = 0;
            await RefreshQuestionsFromDatabaseAsync();
        }

        private async void BtnImportConvert_Click(object sender, RoutedEventArgs e)
        {
            // Nạp các câu hỏi chuẩn vào cơ sở dữ liệu SQLite
            try
            {
                var sampleQuestions = new List<QuestionItem>
                {
                    new QuestionItem
                    {
                        QuestionCode = $"IMPORT_{DateTime.Now:HHmmss}_1",
                        Subject = "Toán",
                        Grade = 12,
                        Topic = "Khảo sát hàm số",
                        CognitiveLevel = "Nhận biết",
                        QuestionType = "MultipleChoice4",
                        Content = "Cho hàm số $y = x^3 - 3x^2 + 2$. Điểm cực đại của đồ thị hàm số là:\nA. $(0; 2)$.\nB. $(2; -2)$.\nC. $(1; 0)$.\nD. $(0; 0)$.",
                        Options = new Dictionary<string, string> { ["A"] = "$(0; 2)$", ["B"] = "$(2; -2)$", ["C"] = "$(1; 0)$", ["D"] = "$(0; 0)$" },
                        CorrectAnswer = "A",
                        Source = "ConvertView"
                    },
                    new QuestionItem
                    {
                        QuestionCode = $"IMPORT_{DateTime.Now:HHmmss}_2",
                        Subject = "Toán",
                        Grade = 12,
                        Topic = "Nguyên hàm",
                        CognitiveLevel = "Thông hiểu",
                        QuestionType = "MultipleChoice4",
                        Content = "Tìm họ nguyên hàm của hàm số $f(x) = 2x e^{x^2}$.\nA. $F(x) = e^{x^2} + C$.\nB. $F(x) = 2e^{x^2} + C$.\nC. $F(x) = x^2 e^{x^2} + C$.\nD. $F(x) = \\frac{1}{2}e^{x^2} + C$.",
                        Options = new Dictionary<string, string> { ["A"] = "$F(x) = e^{x^2} + C$", ["B"] = "$F(x) = 2e^{x^2} + C$", ["C"] = "$F(x) = x^2 e^{x^2} + C$", ["D"] = "$F(x) = \\frac{1}{2}e^{x^2} + C$" },
                        CorrectAnswer = "A",
                        Source = "ConvertView"
                    }
                };

                int imported = await SqliteSchemaAdapter.ImportQuestionsAsync(sampleQuestions);
                await RefreshQuestionsFromDatabaseAsync();

                MessageBox.Show(
                    $"Đã nạp thành công {imported} câu hỏi mới vào cơ sở dữ liệu cục bộ:\n{_activeDbPath}",
                    "Nạp Ngân Hàng Thành Công",
                    MessageBoxButton.OK,
                    MessageBoxImage.Information);
            }
            catch (Exception ex)
            {
                MessageBox.Show($"Lỗi nạp câu hỏi: {ex.Message}", "Lỗi", MessageBoxButton.OK, MessageBoxImage.Error);
            }
        }

        private async void BtnAddQuestion_Click(object sender, RoutedEventArgs e)
        {
            // Bổ sung câu hỏi mới trực tiếp vào cơ sở dữ liệu
            try
            {
                var newQ = new QuestionItem
                {
                    QuestionCode = $"Q_{DateTime.Now:MMdd_HHmmss}",
                    Subject = "Toán",
                    Grade = 12,
                    Topic = "Tích phân ứng dụng",
                    CognitiveLevel = "Vận dụng",
                    QuestionType = "MultipleChoice4",
                    Content = "Tính thể tích khối tròn xoay tạo thành khi quay hình phẳng giới hạn bởi đồ thị $y = \\sqrt{x}$, trục hoành và đường thẳng $x = 4$ quanh trục Ox.\nA. $V = 8\\pi$.\nB. $V = 16\\pi$.\nC. $V = 4\\pi$.\nD. $V = \\frac{8\\pi}{3}$.",
                    Options = new Dictionary<string, string> { ["A"] = "$V = 8\\pi$", ["B"] = "$V = 16\\pi$", ["C"] = "$V = 4\\pi$", ["D"] = "$V = \\frac{8\\pi}{3}$" },
                    CorrectAnswer = "A",
                    Source = "Manual"
                };

                await SqliteSchemaAdapter.ImportQuestionsAsync(new[] { newQ });
                await RefreshQuestionsFromDatabaseAsync();

                MessageBox.Show(
                    $"Đã thêm câu hỏi mới thành công vào cơ sở dữ liệu ({newQ.QuestionCode})!",
                    "Thêm Câu Hỏi Thành Công",
                    MessageBoxButton.OK,
                    MessageBoxImage.Information);
            }
            catch (Exception ex)
            {
                MessageBox.Show($"Lỗi thêm câu hỏi: {ex.Message}", "Lỗi", MessageBoxButton.OK, MessageBoxImage.Error);
            }
        }

        private async void BtnDeleteQuestion_Click(object sender, RoutedEventArgs e)
        {
            var selected = GridQuestions.SelectedItems.Cast<QuestionViewModel>().ToList();
            if (selected.Count == 0)
            {
                MessageBox.Show("Vui lòng chọn ít nhất một câu hỏi trong danh sách để xóa.", "Thông báo", MessageBoxButton.OK, MessageBoxImage.Information);
                return;
            }

            var confirm = MessageBox.Show(
                $"Bạn có chắc chắn muốn xóa {selected.Count} câu hỏi đã chọn khỏi ngân hàng dữ liệu?",
                "Xác nhận xóa câu hỏi",
                MessageBoxButton.YesNo,
                MessageBoxImage.Question);

            if (confirm != MessageBoxResult.Yes) return;

            try
            {
                var ids = selected.Where(s => s.RawItem != null).Select(s => s.RawItem!.Id).ToList();
                int deleted = await SqliteSchemaAdapter.DeleteQuestionsAsync(ids);
                await RefreshQuestionsFromDatabaseAsync();
                MessageBox.Show($"Đã xóa thành công {deleted} câu hỏi khỏi ngân hàng dữ liệu.", "Thành công", MessageBoxButton.OK, MessageBoxImage.Information);
            }
            catch (Exception ex)
            {
                MessageBox.Show($"Lỗi khi xóa câu hỏi: {ex.Message}", "Lỗi", MessageBoxButton.OK, MessageBoxImage.Error);
            }
        }

        private async void BtnClearAll_Click(object sender, RoutedEventArgs e)
        {
            if (_loadedQuestions.Count == 0)
            {
                MessageBox.Show("Ngân hàng câu hỏi hiện đang trống.", "Thông báo", MessageBoxButton.OK, MessageBoxImage.Information);
                return;
            }

            var confirm = MessageBox.Show(
                "Bạn có chắc chắn muốn XÓA SẠCH toàn bộ câu hỏi trong ngân hàng dữ liệu không?\n\nThao tác này không thể hoàn tác!",
                "Cảnh báo xóa sạch ngân hàng câu hỏi",
                MessageBoxButton.YesNo,
                MessageBoxImage.Warning);

            if (confirm != MessageBoxResult.Yes) return;

            try
            {
                await SqliteSchemaAdapter.ClearAllQuestionsAsync();
                await RefreshQuestionsFromDatabaseAsync();
                MessageBox.Show("Đã xóa sạch toàn bộ dữ liệu ngân hàng câu hỏi.", "Thành công", MessageBoxButton.OK, MessageBoxImage.Information);
            }
            catch (Exception ex)
            {
                MessageBox.Show($"Lỗi khi xóa sạch dữ liệu: {ex.Message}", "Lỗi", MessageBoxButton.OK, MessageBoxImage.Error);
            }
        }

        private void BtnExportSelected_Click(object sender, RoutedEventArgs e)
        {
            var list = GridQuestions.ItemsSource as IEnumerable<QuestionViewModel> ?? _loadedQuestions;
            var sb = new System.Text.StringBuilder();
            sb.AppendLine("BỘ GIÁO DỤC VÀ ĐÀO TẠO                 NGÂN HÀNG CÂU HỎI CHỌN LỌC");
            sb.AppendLine("HỆ THỐNG MATRIXEXAMAI                   Môn thi: TOÁN HỌC");
            sb.AppendLine();

            int i = 1;
            foreach (var q in list)
            {
                sb.AppendLine($"% Câu {i++} [{q.Level}]_[{q.Topic}] (Mã: {q.Id})");
                string content = !string.IsNullOrEmpty(q.RawItem?.Content) ? q.RawItem.Content : q.ContentPreview;
                sb.AppendLine(content);
                sb.AppendLine();
            }

            string defaultDir = StorageLocationService.GetDefaultExportDirectory();
            var saveDialog = new Microsoft.Win32.SaveFileDialog
            {
                Filter = "Tài liệu Microsoft Word (*.docx)|*.docx",
                FileName = $"Ngan_Hang_Cau_Hoi_{DateTime.Now:yyyyMMdd_HHmm}.docx",
                InitialDirectory = Directory.Exists(defaultDir) ? defaultDir : Environment.CurrentDirectory,
                Title = "Xuất Ngân hàng câu hỏi ra file Word"
            };

            if (saveDialog.ShowDialog() == true)
            {
                try
                {
                    string? chosenDir = Path.GetDirectoryName(saveDialog.FileName);
                    if (!string.IsNullOrEmpty(chosenDir))
                    {
                        StorageLocationService.SetDefaultExportDirectory(chosenDir);
                    }

                    var wordService = new WordExportService();
                    wordService.ExportToDocx(saveDialog.FileName, sb.ToString());

                    if (StorageLocationService.GetOpenAfterExport())
                    {
                        System.Diagnostics.Process.Start(new System.Diagnostics.ProcessStartInfo { FileName = saveDialog.FileName, UseShellExecute = true });
                        return;
                    }

                    var res = MessageBox.Show($"Đã xuất thành công ngân hàng câu hỏi:\n{saveDialog.FileName}\n\nBạn có muốn mở ngay tệp Word không?", "Thành công", MessageBoxButton.YesNo, MessageBoxImage.Information);
                    if (res == MessageBoxResult.Yes)
                    {
                        System.Diagnostics.Process.Start(new System.Diagnostics.ProcessStartInfo { FileName = saveDialog.FileName, UseShellExecute = true });
                    }
                }
                catch (Exception ex)
                {
                    MessageBox.Show($"Lỗi xuất Word: {ex.Message}", "Lỗi", MessageBoxButton.OK, MessageBoxImage.Error);
                }
            }
        }
    }
}
