using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using System.Text.Json.Serialization;

namespace MatrixExamAI.Desktop.Services
{
    public class FigureEntry
    {
        [JsonPropertyName("id")]
        public string Id { get; set; } = string.Empty;

        [JsonPropertyName("title")]
        public string Title { get; set; } = string.Empty;

        [JsonPropertyName("description")]
        public string Description { get; set; } = string.Empty;

        [JsonPropertyName("tags")]
        public List<string> Tags { get; set; } = new();

        [JsonPropertyName("created_at")]
        public string CreatedAt { get; set; } = string.Empty;

        [JsonPropertyName("source")]
        public string Source { get; set; } = "manual";

        [JsonPropertyName("tex_filename")]
        public string TexFilename { get; set; } = string.Empty;

        [JsonPropertyName("png_filename")]
        public string PngFilename { get; set; } = string.Empty;

        [JsonPropertyName("char_count")]
        public int CharCount { get; set; }

        [JsonPropertyName("tikz_hash")]
        public string TikzHash { get; set; } = string.Empty;

        [JsonIgnore]
        public bool HasPng => !string.IsNullOrEmpty(PngFilename);

        public string GetTexPath(string baseDir) => Path.Combine(baseDir, TexFilename);
        public string? GetPngPath(string baseDir) => HasPng ? Path.Combine(baseDir, PngFilename) : null;
    }

    public class FigureBankService
    {
        private static readonly object _lock = new();
        private static string? _customDir = null;

        public static void SetCustomDirectory(string? dir)
        {
            _customDir = dir;
        }

        public static string GetFiguresDirectory()
        {
            if (!string.IsNullOrEmpty(_customDir) && Directory.Exists(_customDir))
            {
                return _customDir;
            }

            // Kế thừa kho hình sẵn có từ bản cũ (~/.exam_generator/figures)
            string userProfile = Environment.GetFolderPath(Environment.SpecialFolder.UserProfile);
            string legacyDir = Path.Combine(userProfile, ".exam_generator", "figures");
            if (Directory.Exists(legacyDir))
            {
                return legacyDir;
            }

            // Mặc định thư mục AppData cục bộ
            string localApp = Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData);
            string defDir = Path.Combine(localApp, "MatrixExamAI", "figures");
            if (!Directory.Exists(defDir))
            {
                Directory.CreateDirectory(defDir);
            }
            return defDir;
        }

        private static string GetIndexFilePath() => Path.Combine(GetFiguresDirectory(), "index.json");

        public static List<FigureEntry> LoadIndex()
        {
            lock (_lock)
            {
                string bankDir = GetFiguresDirectory();
                string path = GetIndexFilePath();
                var entries = new List<FigureEntry>();

                if (File.Exists(path))
                {
                    try
                    {
                        string json = File.ReadAllText(path, Encoding.UTF8);
                        entries = JsonSerializer.Deserialize<List<FigureEntry>>(json) ?? new List<FigureEntry>();
                    }
                    catch { }
                }

                // Tự động quét và đồng bộ các file figure_*.tex có sẵn trong thư mục chưa được lập chỉ mục
                try
                {
                    if (Directory.Exists(bankDir))
                    {
                        var texFiles = Directory.GetFiles(bankDir, "figure_*.tex");
                        var indexedTex = new HashSet<string>(entries.Select(e => e.TexFilename), StringComparer.OrdinalIgnoreCase);
                        bool updated = false;

                        foreach (var tf in texFiles)
                        {
                            string fileName = Path.GetFileName(tf);
                            if (!indexedTex.Contains(fileName))
                            {
                                string idPart = Path.GetFileNameWithoutExtension(fileName).Replace("figure_", "");
                                string pngName = Path.ChangeExtension(fileName, ".png");
                                string code = File.ReadAllText(tf, Encoding.UTF8);
                                string title = InferFigureTitle(code, idPart);

                                var entry = new FigureEntry
                                {
                                    Id = idPart,
                                    Title = title,
                                    Description = "",
                                    Tags = InferTags(code),
                                    CreatedAt = File.GetCreationTime(tf).ToString("yyyy-MM-ddTHH:mm:ss"),
                                    Source = "manual",
                                    TexFilename = fileName,
                                    PngFilename = File.Exists(Path.Combine(bankDir, pngName)) ? pngName : "",
                                    CharCount = code.Length,
                                    TikzHash = ComputeHash(code)
                                };
                                entries.Add(entry);
                                indexedTex.Add(fileName);
                                updated = true;
                            }
                        }

                        if (updated)
                        {
                            entries = entries.OrderByDescending(e => int.TryParse(e.Id, out int n) ? n : 0).ToList();
                            SaveIndex(entries);
                        }
                    }
                }
                catch { }

                return entries;
            }
        }

        private static string InferFigureTitle(string code, string idPart)
        {
            if (code.Contains("\\tkzTabInit")) return $"Bảng biến thiên #{idPart}";
            if (code.Contains("x={(1cm") || code.Contains("z={(0cm") || code.Contains("3D")) return $"Hình không gian #{idPart}";
            if (code.Contains("begin{axis}")) return $"Đồ thị hàm số #{idPart}";
            return $"Hình vẽ #{idPart}";
        }

        private static List<string> InferTags(string code)
        {
            var tags = new List<string>();
            if (code.Contains("\\tkzTabInit")) tags.Add("BBT");
            if (code.Contains("x={(1cm") || code.Contains("z={(0cm")) tags.Add("3D");
            if (code.Contains("begin{axis}")) tags.Add("Đồ thị");
            if (tags.Count == 0) tags.Add("Hình học");
            return tags;
        }

        public static void SaveIndex(List<FigureEntry> entries)
        {
            lock (_lock)
            {
                string path = GetIndexFilePath();
                string dir = Path.GetDirectoryName(path)!;
                if (!Directory.Exists(dir)) Directory.CreateDirectory(dir);

                var options = new JsonSerializerOptions
                {
                    WriteIndented = true,
                    Encoder = System.Text.Encodings.Web.JavaScriptEncoder.UnsafeRelaxedJsonEscaping
                };
                string json = JsonSerializer.Serialize(entries, options);
                File.WriteAllText(path, json, Encoding.UTF8);
            }
        }

        public static string NextId(List<FigureEntry> existing)
        {
            var used = new HashSet<int>();
            foreach (var item in existing)
            {
                if (int.TryParse(item.Id, out int n))
                {
                    used.Add(n);
                }
            }

            int id = 1;
            while (used.Contains(id))
            {
                id++;
            }
            return $"{id:D3}";
        }

        public static FigureEntry SaveFigure(
            string tikzCode,
            string title,
            string description = "",
            List<string>? tags = null,
            string source = "manual",
            string? pngSourcePath = null,
            byte[]? pngBytes = null)
        {
            if (string.IsNullOrWhiteSpace(tikzCode))
                throw new ArgumentException("Mã TikZ không được để trống.", nameof(tikzCode));

            lock (_lock)
            {
                string bankDir = GetFiguresDirectory();
                var entries = LoadIndex();
                string fid = NextId(entries);

                string texName = $"figure_{fid}.tex";
                string texPath = Path.Combine(bankDir, texName);
                File.WriteAllText(texPath, tikzCode, Encoding.UTF8);

                string pngName = string.Empty;
                if (!string.IsNullOrEmpty(pngSourcePath) && File.Exists(pngSourcePath))
                {
                    pngName = $"figure_{fid}.png";
                    string destPng = Path.Combine(bankDir, pngName);
                    File.Copy(pngSourcePath, destPng, true);
                }
                else if (pngBytes != null && pngBytes.Length > 0)
                {
                    pngName = $"figure_{fid}.png";
                    string destPng = Path.Combine(bankDir, pngName);
                    File.WriteAllBytes(destPng, pngBytes);
                }

                var entry = new FigureEntry
                {
                    Id = fid,
                    Title = string.IsNullOrWhiteSpace(title) ? $"Hình TikZ {DateTime.Now:yyyy-MM-dd HH:mm}" : title.Trim(),
                    Description = description.Trim(),
                    Tags = tags ?? new List<string>(),
                    CreatedAt = DateTime.Now.ToString("yyyy-MM-ddTHH:mm:ss"),
                    Source = source,
                    TexFilename = texName,
                    PngFilename = pngName,
                    CharCount = tikzCode.Length,
                    TikzHash = ComputeHash(tikzCode)
                };

                entries.Insert(0, entry);
                SaveIndex(entries);
                return entry;
            }
        }

        public static List<FigureEntry> ListFigures(string query = "", string sourceFilter = "all")
        {
            var entries = LoadIndex();

            if (!string.IsNullOrWhiteSpace(sourceFilter) && !string.Equals(sourceFilter, "all", StringComparison.OrdinalIgnoreCase))
            {
                entries = entries.Where(e => string.Equals(e.Source, sourceFilter, StringComparison.OrdinalIgnoreCase)).ToList();
            }

            if (!string.IsNullOrWhiteSpace(query))
            {
                string q = query.Trim().ToLowerInvariant();
                entries = entries.Where(e =>
                    e.Title.ToLowerInvariant().Contains(q) ||
                    e.Description.ToLowerInvariant().Contains(q) ||
                    e.Id.ToLowerInvariant().Contains(q) ||
                    e.Tags.Any(t => t.ToLowerInvariant().Contains(q))
                ).ToList();
            }

            return entries;
        }

        public static string GetTikzCode(FigureEntry entry)
        {
            string path = entry.GetTexPath(GetFiguresDirectory());
            return File.Exists(path) ? File.ReadAllText(path, Encoding.UTF8) : string.Empty;
        }

        public static bool DeleteFigure(string id)
        {
            lock (_lock)
            {
                var entries = LoadIndex();
                var target = entries.FirstOrDefault(e => e.Id == id);
                if (target == null) return false;

                string bankDir = GetFiguresDirectory();
                string texPath = target.GetTexPath(bankDir);
                if (File.Exists(texPath))
                {
                    try { File.Delete(texPath); } catch { }
                }

                string? pngPath = target.GetPngPath(bankDir);
                if (!string.IsNullOrEmpty(pngPath) && File.Exists(pngPath))
                {
                    try { File.Delete(pngPath); } catch { }
                }

                entries.Remove(target);
                SaveIndex(entries);
                return true;
            }
        }

        public static bool UpdateFigureMeta(string id, string newTitle, string newDesc, List<string> newTags)
        {
            lock (_lock)
            {
                var entries = LoadIndex();
                var target = entries.FirstOrDefault(e => e.Id == id);
                if (target == null) return false;

                target.Title = newTitle.Trim();
                target.Description = newDesc.Trim();
                target.Tags = newTags;

                SaveIndex(entries);
                return true;
            }
        }

        private static string ComputeHash(string input)
        {
            using var sha = SHA256.Create();
            byte[] bytes = sha.ComputeHash(Encoding.UTF8.GetBytes(input.Trim()));
            return Convert.ToHexString(bytes).ToLowerInvariant()[..16];
        }
    }
}
