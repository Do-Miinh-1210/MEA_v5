using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using System.Text.Json;
using System.Text.Json.Serialization;
using MatrixExamAI.Shared.HtmlModel;

namespace MatrixExamAI.Desktop.Services
{
    public class HtmlModelEntry
    {
        [JsonPropertyName("id")]
        public string Id { get; set; } = string.Empty;

        [JsonPropertyName("title")]
        public string Title { get; set; } = string.Empty;

        [JsonPropertyName("category")]
        public string Category { get; set; } = string.Empty;

        [JsonPropertyName("description")]
        public string Description { get; set; } = string.Empty;

        [JsonPropertyName("tags")]
        public List<string> Tags { get; set; } = new();

        [JsonPropertyName("created_at")]
        public string CreatedAt { get; set; } = string.Empty;

        [JsonPropertyName("source")]
        public string Source { get; set; } = "user"; // "template" | "user" | "ai"

        [JsonPropertyName("html_filename")]
        public string HtmlFilename { get; set; } = string.Empty;

        [JsonIgnore]
        public string? CachedHtmlCode { get; set; }

        [JsonIgnore]
        public bool IsTemplate => Source == "template";
    }

    /// <summary>
    /// Quản lý Kho lưu trữ mô hình mô phỏng 3D HTML (Bao gồm mẫu chuẩn STEM và mô hình tự lưu).
    /// </summary>
    public static class HtmlModelBankService
    {
        private static readonly object _lock = new();
        private static string? _customDir = null;

        public static void SetCustomDirectory(string? dir)
        {
            _customDir = dir;
        }

        public static string GetBankDirectory()
        {
            if (!string.IsNullOrEmpty(_customDir) && Directory.Exists(_customDir))
            {
                return _customDir;
            }

            string localApp = Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData);
            string defDir = Path.Combine(localApp, "MatrixExamAI", "html_models");
            if (!Directory.Exists(defDir))
            {
                Directory.CreateDirectory(defDir);
            }
            return defDir;
        }

        private static string GetIndexFilePath() => Path.Combine(GetBankDirectory(), "index.json");

        /// <summary>
        /// Nạp toàn bộ danh sách mô hình (gồm mẫu chuẩn thư viện + mô hình do người dùng lưu).
        /// </summary>
        public static List<HtmlModelEntry> LoadAllEntries()
        {
            lock (_lock)
            {
                var result = new List<HtmlModelEntry>();

                // 1. Nạp các mẫu chuẩn STEM từ thư viện tích hợp
                var templates = HtmlModelTemplateLibrary.GetAllTemplates();
                foreach (var t in templates)
                {
                    result.Add(new HtmlModelEntry
                    {
                        Id = t.Id,
                        Title = t.Title,
                        Category = t.Category,
                        Description = t.Description,
                        Tags = new List<string> { "3D", "Template", t.Category },
                        CreatedAt = "Mẫu chuẩn",
                        Source = "template",
                        CachedHtmlCode = t.HtmlCode
                    });
                }

                // 2. Nạp các mô hình do người dùng tự lưu từ thư mục cá nhân
                string indexPath = GetIndexFilePath();
                if (File.Exists(indexPath))
                {
                    try
                    {
                        string json = File.ReadAllText(indexPath, Encoding.UTF8);
                        var userEntries = JsonSerializer.Deserialize<List<HtmlModelEntry>>(json);
                        if (userEntries != null)
                        {
                            foreach (var u in userEntries)
                            {
                                u.Source = "user";
                                result.Add(u);
                            }
                        }
                    }
                    catch
                    {
                        // Bỏ qua lỗi đọc file index để không làm sập ứng dụng
                    }
                }

                return result;
            }
        }

        /// <summary>
        /// Lấy mã HTML của một mô hình cụ thể.
        /// </summary>
        public static string GetHtmlCode(HtmlModelEntry entry)
        {
            if (!string.IsNullOrEmpty(entry.CachedHtmlCode))
            {
                return entry.CachedHtmlCode;
            }

            // Nếu là tệp người dùng lưu trên đĩa
            if (!string.IsNullOrEmpty(entry.HtmlFilename))
            {
                string fullPath = Path.Combine(GetBankDirectory(), entry.HtmlFilename);
                if (File.Exists(fullPath))
                {
                    string code = File.ReadAllText(fullPath, Encoding.UTF8);
                    entry.CachedHtmlCode = code;
                    return code;
                }
            }

            return string.Empty;
        }

        /// <summary>
        /// Lưu mô hình HTML mới vào kho lưu trữ cá nhân.
        /// </summary>
        public static HtmlModelEntry SaveUserEntry(string title, string category, string description, string htmlCode)
        {
            lock (_lock)
            {
                string bankDir = GetBankDirectory();
                string id = "user_" + DateTime.Now.ToString("yyyyMMdd_HHmmss");
                string htmlFilename = $"{id}.html";
                string fullPath = Path.Combine(bankDir, htmlFilename);

                File.WriteAllText(fullPath, htmlCode, Encoding.UTF8);

                var entry = new HtmlModelEntry
                {
                    Id = id,
                    Title = string.IsNullOrWhiteSpace(title) ? $"Mô hình 3D ({DateTime.Now:dd/MM/yyyy HH:mm})" : title.Trim(),
                    Category = string.IsNullOrWhiteSpace(category) ? "Mô hình cá nhân tự lưu" : category.Trim(),
                    Description = description?.Trim() ?? string.Empty,
                    Tags = new List<string> { "Cá nhân", category },
                    CreatedAt = DateTime.Now.ToString("dd/MM/yyyy HH:mm"),
                    Source = "user",
                    HtmlFilename = htmlFilename,
                    CachedHtmlCode = htmlCode
                };

                // Cập nhật index.json
                string indexPath = GetIndexFilePath();
                var userEntries = new List<HtmlModelEntry>();
                if (File.Exists(indexPath))
                {
                    try
                    {
                        string json = File.ReadAllText(indexPath, Encoding.UTF8);
                        userEntries = JsonSerializer.Deserialize<List<HtmlModelEntry>>(json) ?? new();
                    }
                    catch { }
                }

                userEntries.Insert(0, entry);
                File.WriteAllText(indexPath, JsonSerializer.Serialize(userEntries, new JsonSerializerOptions { WriteIndented = true }), Encoding.UTF8);

                return entry;
            }
        }

        /// <summary>
        /// Xóa mô hình cá nhân khỏi kho.
        /// </summary>
        public static bool DeleteUserEntry(string id)
        {
            lock (_lock)
            {
                string indexPath = GetIndexFilePath();
                if (!File.Exists(indexPath)) return false;

                try
                {
                    string json = File.ReadAllText(indexPath, Encoding.UTF8);
                    var userEntries = JsonSerializer.Deserialize<List<HtmlModelEntry>>(json) ?? new();
                    var item = userEntries.FirstOrDefault(x => x.Id == id);
                    if (item == null) return false;

                    userEntries.Remove(item);
                    File.WriteAllText(indexPath, JsonSerializer.Serialize(userEntries, new JsonSerializerOptions { WriteIndented = true }), Encoding.UTF8);

                    if (!string.IsNullOrEmpty(item.HtmlFilename))
                    {
                        string filePath = Path.Combine(GetBankDirectory(), item.HtmlFilename);
                        if (File.Exists(filePath))
                        {
                            File.Delete(filePath);
                        }
                    }
                    return true;
                }
                catch
                {
                    return false;
                }
            }
        }
    }
}
