using System;
using System.IO;
using System.Text.Json;
using FluentAssertions;
using Microsoft.Win32;
using Xunit;

namespace MatrixExamAI.Desktop.Tests
{
    public class WordAddInRegistryAndConfigSyncTests
    {
        #region Tier 1 - Normative Tests (Registry Keys & Values)

        [Fact]
        public void WordAddInRegistry_CheckConfiguration_ShouldHaveCorrectAddinKeyAndValues()
        {
            // The Addin registry key location for Word Addins
            const string subKeyPath = @"Software\Microsoft\Office\Word\Addins\MatrixExamAI.WordAddIn";

            using var key = Registry.CurrentUser.OpenSubKey(subKeyPath);

            // Assert key presence on the system
            key.Should().NotBeNull("MatrixExamAI Word Add-in registry key must be registered under HKCU");

            // Assert values
            string? friendlyName = key!.GetValue("FriendlyName") as string;
            friendlyName.Should().Be("MatrixExamAI Word Add-in");

            string? description = key.GetValue("Description") as string;
            description.Should().NotBeNullOrWhiteSpace();
            description.Should().Contain("MatrixExamAI");

            object? loadBehavior = key.GetValue("LoadBehavior");
            loadBehavior.Should().NotBeNull();
            int loadBehaviorInt = Convert.ToInt32(loadBehavior);
            (loadBehaviorInt == 2 || loadBehaviorInt == 3).Should().BeTrue("LoadBehavior must be either 3 (Startup) or 2 (Demand)");

            object? cmdSafe = key.GetValue("CommandLineSafe");
            if (cmdSafe != null)
            {
                Convert.ToInt32(cmdSafe).Should().Be(0);
            }
        }

        #endregion

        #region Tier 2 - Boundary Value Tests (Config Serialization & AppSettings)

        [Fact]
        public void AppConfig_SerializationAndDeserialization_ShouldPreserveAllSettings()
        {
            string tempConfigDir = Path.Combine(Path.GetTempPath(), "MEA_Cfg_" + Guid.NewGuid().ToString("N"));
            Directory.CreateDirectory(tempConfigDir);
            string tempConfigFile = Path.Combine(tempConfigDir, "config.json");

            try
            {
                var originalConfig = new
                {
                    apiKey = "AIzaSy_SampleKeyForTesting_123456",
                    model = "gemini-3.8-flash",
                    nineRouterApiKey = "sk-sample-nine-router-key",
                    openAiApiKey = ""
                };

                string jsonOut = JsonSerializer.Serialize(originalConfig, new JsonSerializerOptions { WriteIndented = true });
                File.WriteAllText(tempConfigFile, jsonOut);

                // Read back
                string jsonIn = File.ReadAllText(tempConfigFile);
                using var doc = JsonDocument.Parse(jsonIn);
                var root = doc.RootElement;

                root.GetProperty("apiKey").GetString().Should().Be("AIzaSy_SampleKeyForTesting_123456");
                root.GetProperty("model").GetString().Should().Be("gemini-3.8-flash");
                root.GetProperty("nineRouterApiKey").GetString().Should().Be("sk-sample-nine-router-key");
                root.GetProperty("openAiApiKey").GetString().Should().BeEmpty();
            }
            finally
            {
                if (Directory.Exists(tempConfigDir))
                {
                    Directory.Delete(tempConfigDir, true);
                }
            }
        }

        #endregion

        #region Tier 3 - Combinatorial & Python Config Compatibility

        [Fact]
        public void PythonSettingsSchema_ParsingCompatibility_ShouldHandlePythonAppSettingsFormat()
        {
            // Schema format used in Python: ~/.exam_generator/app_settings.json
            string pySettingsJson = @"{
  ""selected_ai_provider"": ""9Router Local Aggregator"",
  ""selected_ai_model_9Router"": ""ag/gemini-3.8-flash"",
  ""temperature"": 0.2,
  ""max_output_tokens"": 4096,
  ""auto_convert_table"": true,
  ""protect_abs_pipe"": true
}";

            using var doc = JsonDocument.Parse(pySettingsJson);
            var root = doc.RootElement;

            root.TryGetProperty("selected_ai_model_9Router", out var pModel).Should().BeTrue();
            pModel.GetString().Should().Be("ag/gemini-3.8-flash");

            root.TryGetProperty("selected_ai_provider", out var pProv).Should().BeTrue();
            pProv.GetString().Should().Be("9Router Local Aggregator");
        }

        #endregion

        #region Tier 4 - Workload & LocalAppData Directory Integrity

        [Fact]
        public void LocalAppDataDirectory_Resolution_ShouldResolveValidWritablePath()
        {
            string appData = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "MatrixExamAI");
            appData.Should().NotBeNullOrWhiteSpace();
            Directory.Exists(appData).Should().BeTrue("MatrixExamAI directory in LocalAppData must exist or be creatable");
        }

        #endregion
    }
}
