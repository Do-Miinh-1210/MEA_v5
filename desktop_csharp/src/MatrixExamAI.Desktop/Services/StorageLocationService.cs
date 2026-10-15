using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Text.Json;

namespace MatrixExamAI.Desktop.Services
{
    public static class StorageLocationService
    {
        private static readonly string AppDataDir = Path.Combine(
            Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
            "MatrixExamAI");
        private static readonly string ConfigPath = Path.Combine(AppDataDir, "config.json");
        private static readonly string PySettingsPath = Path.Combine(
            Environment.GetFolderPath(Environment.SpecialFolder.UserProfile),
            ".exam_generator", "app_settings.json");

        private static string? _cachedExportDir;
        private static string? _cachedBankDir;
        private static bool? _cachedOpenAfterExport;

        public static string GetDefaultExportDirectory()
        {
            if (!string.IsNullOrEmpty(_cachedExportDir) && Directory.Exists(_cachedExportDir))
            {
                return _cachedExportDir;
            }

            string saved = ReadConfigProperty("defaultExportDir");
            if (string.IsNullOrEmpty(saved))
            {
                saved = ReadPyConfigProperty("default_export_dir");
            }

            if (!string.IsNullOrEmpty(saved))
            {
                _cachedExportDir = saved;
                EnsureDirectory(saved);
                return saved;
            }

            string defaultDir = Path.Combine(
                Environment.GetFolderPath(Environment.SpecialFolder.MyDocuments),
                "MatrixExamAI", "XuatDe");
            EnsureDirectory(defaultDir);
            _cachedExportDir = defaultDir;
            return defaultDir;
        }

        public static void SetDefaultExportDirectory(string path)
        {
            if (string.IsNullOrWhiteSpace(path)) return;
            EnsureDirectory(path);
            _cachedExportDir = path;
            WriteConfigProperty("defaultExportDir", path);
            WritePyConfigProperty("default_export_dir", path);
        }

        public static string GetQuestionBankDirectory()
        {
            if (!string.IsNullOrEmpty(_cachedBankDir) && Directory.Exists(_cachedBankDir))
            {
                return _cachedBankDir;
            }

            string saved = ReadConfigProperty("questionBankDir");
            if (string.IsNullOrEmpty(saved))
            {
                saved = ReadPyConfigProperty("nhch_dir");
            }

            if (!string.IsNullOrEmpty(saved))
            {
                _cachedBankDir = saved;
                EnsureDirectory(saved);
                return saved;
            }

            string defaultDir = Path.Combine(
                Environment.GetFolderPath(Environment.SpecialFolder.UserProfile),
                ".exam_generator");
            EnsureDirectory(defaultDir);
            _cachedBankDir = defaultDir;
            return defaultDir;
        }

        public static void SetQuestionBankDirectory(string path)
        {
            if (string.IsNullOrWhiteSpace(path)) return;
            EnsureDirectory(path);
            _cachedBankDir = path;
            WriteConfigProperty("questionBankDir", path);
            WritePyConfigProperty("nhch_dir", path);
        }

        public static bool GetOpenAfterExport()
        {
            if (_cachedOpenAfterExport.HasValue) return _cachedOpenAfterExport.Value;

            string saved = ReadConfigProperty("openAfterExport");
            if (bool.TryParse(saved, out bool val))
            {
                _cachedOpenAfterExport = val;
                return val;
            }

            string pySaved = ReadPyConfigProperty("open_after_export");
            if (bool.TryParse(pySaved, out bool pyVal))
            {
                _cachedOpenAfterExport = pyVal;
                return pyVal;
            }

            _cachedOpenAfterExport = true;
            return true;
        }

        public static void SetOpenAfterExport(bool val)
        {
            _cachedOpenAfterExport = val;
            WriteConfigProperty("openAfterExport", val.ToString().ToLowerInvariant());
            WritePyConfigProperty("open_after_export", val);
        }

        public static void OpenFolderInExplorer(string folderPath)
        {
            try
            {
                if (string.IsNullOrWhiteSpace(folderPath))
                {
                    folderPath = GetDefaultExportDirectory();
                }
                EnsureDirectory(folderPath);
                Process.Start(new ProcessStartInfo
                {
                    FileName = folderPath,
                    UseShellExecute = true
                });
            }
            catch (Exception ex)
            {
                Debug.WriteLine($"[StorageLocationService] OpenFolderInExplorer error: {ex.Message}");
            }
        }

        private static void EnsureDirectory(string path)
        {
            try
            {
                if (!Directory.Exists(path))
                {
                    Directory.CreateDirectory(path);
                }
            }
            catch { }
        }

        private static string ReadConfigProperty(string propertyName)
        {
            try
            {
                if (!File.Exists(ConfigPath)) return string.Empty;
                string json = File.ReadAllText(ConfigPath);
                using var doc = JsonDocument.Parse(json);
                if (doc.RootElement.TryGetProperty(propertyName, out var prop))
                {
                    return prop.GetString() ?? string.Empty;
                }
            }
            catch { }
            return string.Empty;
        }

        private static void WriteConfigProperty(string propertyName, string value)
        {
            try
            {
                EnsureDirectory(AppDataDir);
                var dict = new Dictionary<string, object>();
                if (File.Exists(ConfigPath))
                {
                    try
                    {
                        dict = JsonSerializer.Deserialize<Dictionary<string, object>>(File.ReadAllText(ConfigPath))
                               ?? new Dictionary<string, object>();
                    }
                    catch { }
                }

                dict[propertyName] = value;
                string json = JsonSerializer.Serialize(dict, new JsonSerializerOptions { WriteIndented = true });
                File.WriteAllText(ConfigPath, json);
            }
            catch { }
        }

        private static string ReadPyConfigProperty(string propertyName)
        {
            try
            {
                if (!File.Exists(PySettingsPath)) return string.Empty;
                string json = File.ReadAllText(PySettingsPath);
                using var doc = JsonDocument.Parse(json);
                if (doc.RootElement.TryGetProperty(propertyName, out var prop))
                {
                    if (prop.ValueKind == JsonValueKind.String)
                        return prop.GetString() ?? string.Empty;
                    return prop.ToString();
                }
            }
            catch { }
            return string.Empty;
        }

        private static void WritePyConfigProperty(string propertyName, object value)
        {
            try
            {
                string dir = Path.GetDirectoryName(PySettingsPath)!;
                EnsureDirectory(dir);
                var dict = new Dictionary<string, object>();
                if (File.Exists(PySettingsPath))
                {
                    try
                    {
                        dict = JsonSerializer.Deserialize<Dictionary<string, object>>(File.ReadAllText(PySettingsPath))
                               ?? new Dictionary<string, object>();
                    }
                    catch { }
                }

                dict[propertyName] = value;
                string json = JsonSerializer.Serialize(dict, new JsonSerializerOptions { WriteIndented = true });
                File.WriteAllText(PySettingsPath, json);
            }
            catch { }
        }
    }
}
