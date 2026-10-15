using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using System.Text.Json.Serialization;

namespace MatrixExamAI.Desktop.Services
{
    public class AiUsageEntry
    {
        [JsonPropertyName("ts")]
        public string Timestamp { get; set; } = string.Empty;

        [JsonPropertyName("provider")]
        public string Provider { get; set; } = string.Empty;

        [JsonPropertyName("model")]
        public string Model { get; set; } = string.Empty;

        [JsonPropertyName("kind")]
        public string Kind { get; set; } = "generate";

        [JsonPropertyName("prompt_chars")]
        public int PromptChars { get; set; }

        [JsonPropertyName("response_chars")]
        public int ResponseChars { get; set; }

        [JsonPropertyName("duration_ms")]
        public int DurationMs { get; set; }

        [JsonPropertyName("ok")]
        public bool IsOk { get; set; } = true;

        [JsonPropertyName("error")]
        public string Error { get; set; } = string.Empty;

        [JsonIgnore]
        public string FormattedTime
        {
            get
            {
                if (DateTime.TryParse(Timestamp, out var dt))
                {
                    return dt.ToString("yyyy-MM-dd HH:mm:ss");
                }
                return Timestamp;
            }
        }

        [JsonIgnore]
        public string FormattedPrompt => PromptChars >= 1000 ? $"{(PromptChars / 1000.0):0.0}K" : PromptChars.ToString();

        [JsonIgnore]
        public string FormattedResponse => ResponseChars >= 1000 ? $"{(ResponseChars / 1000.0):0.0}K" : ResponseChars.ToString();

        [JsonIgnore]
        public string StatusDisplay => IsOk ? "✓" : "✗";
    }

    public class AiUsageStats
    {
        public int TotalRequests { get; set; }
        public double SuccessRate { get; set; }
        public long TotalChars { get; set; }
        public int AvgDurationMs { get; set; }
        public Dictionary<string, int> ProviderBreakdown { get; set; } = new();
        public string QuotaWarning { get; set; } = "Hôm nay chưa dùng AI";
        public List<AiUsageEntry> RecentEntries { get; set; } = new();
    }

    public class AiUsageService
    {
        private static readonly Lazy<AiUsageService> _instance = new(() => new AiUsageService());
        public static AiUsageService Instance => _instance.Value;

        private readonly string _logFilePath;

        public AiUsageService()
        {
            var home = Environment.GetFolderPath(Environment.SpecialFolder.UserProfile);
            var dir = Path.Combine(home, ".exam_generator");
            if (!Directory.Exists(dir))
            {
                Directory.CreateDirectory(dir);
            }
            _logFilePath = Path.Combine(dir, "ai_usage.jsonl");
        }

        public string GetLogDirectory() => Path.GetDirectoryName(_logFilePath) ?? Environment.CurrentDirectory;

        public string GetLogFilePath() => _logFilePath;

        public void Record(string provider, string model, string kind, int promptChars, int responseChars, int durationMs, bool ok, string error = "")
        {
            try
            {
                var entry = new AiUsageEntry
                {
                    Timestamp = DateTime.Now.ToString("s"),
                    Provider = provider,
                    Model = model,
                    Kind = kind,
                    PromptChars = promptChars,
                    ResponseChars = responseChars,
                    DurationMs = durationMs,
                    IsOk = ok,
                    Error = error
                };

                var line = JsonSerializer.Serialize(entry);
                File.AppendAllLines(_logFilePath, new[] { line });
            }
            catch
            {
                // Best effort logging
            }
        }

        public AiUsageStats GetStats(string range = "today")
        {
            var stats = new AiUsageStats();
            var allEntries = LoadAllEntries();

            DateTime now = DateTime.Now;
            DateTime? cutoff = range switch
            {
                "today" => now.Date,
                "7" => now.Date.AddDays(-7),
                "30" => now.Date.AddDays(-30),
                _ => null
            };

            var filtered = allEntries.Where(e =>
            {
                if (!cutoff.HasValue) return true;
                if (DateTime.TryParse(e.Timestamp, out var dt))
                {
                    return dt >= cutoff.Value;
                }
                return false;
            }).ToList();

            stats.TotalRequests = filtered.Count;
            if (filtered.Count > 0)
            {
                int successCount = filtered.Count(e => e.IsOk);
                stats.SuccessRate = Math.Round((double)successCount / filtered.Count * 100, 1);
                stats.TotalChars = filtered.Sum(e => (long)e.PromptChars + e.ResponseChars);
                stats.AvgDurationMs = (int)filtered.Average(e => e.DurationMs);

                foreach (var group in filtered.GroupBy(e => e.Provider))
                {
                    stats.ProviderBreakdown[group.Key] = group.Count();
                }

                int todayRequests = allEntries.Count(e => DateTime.TryParse(e.Timestamp, out var dt) && dt.Date == now.Date);
                if (todayRequests == 0)
                {
                    stats.QuotaWarning = "✓ Hôm nay chưa dùng AI";
                }
                else if (todayRequests > 1400)
                {
                    stats.QuotaWarning = $"⚠️ Cảnh báo Quota cao: Đã gọi {todayRequests}/1500 request hôm nay!";
                }
                else
                {
                    stats.QuotaWarning = $"✓ Hôm nay đã gọi {todayRequests} request (ổn định)";
                }
            }
            else
            {
                stats.QuotaWarning = "✓ Chưa có dữ liệu request trong phạm vi này";
            }

            stats.RecentEntries = allEntries.OrderByDescending(e => e.Timestamp).Take(50).ToList();
            return stats;
        }

        public List<AiUsageEntry> LoadAllEntries()
        {
            var list = new List<AiUsageEntry>();
            if (!File.Exists(_logFilePath)) return list;

            try
            {
                var lines = File.ReadAllLines(_logFilePath);
                foreach (var line in lines)
                {
                    if (string.IsNullOrWhiteSpace(line)) continue;
                    try
                    {
                        var entry = JsonSerializer.Deserialize<AiUsageEntry>(line);
                        if (entry != null)
                        {
                            list.Add(entry);
                        }
                    }
                    catch
                    {
                        // Skip corrupted line
                    }
                }
            }
            catch
            {
                // Ignore read errors
            }

            return list;
        }

        public void ClearLog()
        {
            try
            {
                if (File.Exists(_logFilePath))
                {
                    File.WriteAllText(_logFilePath, string.Empty);
                }
            }
            catch
            {
                // Best effort
            }
        }
    }
}
