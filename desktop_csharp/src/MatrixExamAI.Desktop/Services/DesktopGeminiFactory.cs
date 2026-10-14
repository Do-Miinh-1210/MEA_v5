using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Net.Http;
using System.Net.Http.Headers;
using System.Text;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using MatrixExamAI.Shared.AI;
using MatrixExamAI.Shared.Models;

namespace MatrixExamAI.Desktop.Services
{
    public class AiExecutionResult
    {
        public bool Success { get; set; }
        public string Content { get; set; } = string.Empty;
        public string ProviderUsed { get; set; } = string.Empty;
        public string ModelUsed { get; set; } = string.Empty;
        public long LatencyMs { get; set; }
        public string? ErrorMessage { get; set; }
    }

    public static class DesktopGeminiFactory
    {
        private static readonly HttpClient _httpClient = new HttpClient { Timeout = TimeSpan.FromSeconds(120) };
        private static readonly JsonSerializerOptions JsonOptions = new JsonSerializerOptions
        {
            PropertyNamingPolicy = null,
            PropertyNameCaseInsensitive = true
        };

        public static readonly Dictionary<string, List<string>> DefaultModelsByProvider = new Dictionary<string, List<string>>(StringComparer.OrdinalIgnoreCase)
        {
            ["Google Gemini"] = new List<string>
            {
                "gemini-3.8-flash",
                "gemini-3.1-pro",
                "gemini-3.8-live",
                "gemini-3.6-flash",
                "gemini-3.5-flash-lite",
                "gemini-2.5-pro",
                "gemini-2.5-flash"
            },
            ["9Router"] = new List<string>
            {
                "ag/gemini-3.8-flash",
                "ag/gemini-3.8-flash-high",
                "ag/gemini-3.7-flash-high",
                "ag/gemini-3.6-flash-high",
                "ag/gemini-3.1-pro-low",
                "ag/claude-sonnet-5-5",
                "ag/claude-sonnet-4-6",
                "ag/gpt-oss-120b-medium",
                "gemini-3.8-flash"
            },
            ["Anthropic Claude"] = new List<string>
            {
                "claude-sonnet-5",
                "claude-sonnet-4-6",
                "claude-sonnet-4-5",
                "claude-opus-5",
                "claude-haiku-4-5"
            },
            ["DeepSeek"] = new List<string>
            {
                "deepseek-chat",
                "deepseek-reasoner",
                "deepseek-v4.1-flash"
            },
            ["OpenAI GPT"] = new List<string>
            {
                "gpt-4o",
                "gpt-4o-mini",
                "gpt-4.5"
            }
        };

        public static readonly Dictionary<string, string> ProviderKeyUrls = new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase)
        {
            ["Google Gemini"] = "https://aistudio.google.com/apikey",
            ["9Router"] = "http://localhost:20128",
            ["Anthropic Claude"] = "https://console.anthropic.com/settings/keys",
            ["DeepSeek"] = "https://platform.deepseek.com/api_keys",
            ["OpenAI GPT"] = "https://platform.openai.com/api-keys",
            ["OpenAI"] = "https://platform.openai.com/api-keys"
        };

        public static List<string> SplitKeys(string raw)
        {
            if (string.IsNullOrWhiteSpace(raw)) return new List<string>();
            return raw.Split(new[] { '\r', '\n', ',', ';' }, StringSplitOptions.RemoveEmptyEntries)
                      .Select(k => k.Trim())
                      .Where(k => !string.IsNullOrEmpty(k) && !k.StartsWith("#"))
                      .Distinct()
                      .ToList();
        }

        public static (string ApiKey, string Provider, string Model, string Endpoint, List<string> Keys) GetActiveConfig()
        {
            string apiKey = string.Empty;
            string model = "ag/gemini-3.8-flash";
            string provider = "9Router";
            string endpoint = "http://localhost:20128/v1/chat/completions";
            var keys = new List<string>();

            try
            {
                string appData = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "MatrixExamAI");
                string configFile = Path.Combine(appData, "config.json");
                if (File.Exists(configFile))
                {
                    string json = File.ReadAllText(configFile);
                    using var doc = JsonDocument.Parse(json);
                    var root = doc.RootElement;

                    bool hasExplicitProvider = false;
                    if (root.TryGetProperty("provider", out var pProv) && !string.IsNullOrWhiteSpace(pProv.GetString()))
                    {
                        provider = pProv.GetString()!.Trim();
                        hasExplicitProvider = true;
                    }
                    if (root.TryGetProperty("model", out var pModel) && !string.IsNullOrWhiteSpace(pModel.GetString()))
                    {
                        model = pModel.GetString()!.Trim();
                    }
                    if (root.TryGetProperty("apiKey", out var pKey) && !string.IsNullOrWhiteSpace(pKey.GetString()))
                    {
                        apiKey = pKey.GetString()!.Trim();
                    }

                    if (!hasExplicitProvider && !string.IsNullOrEmpty(apiKey) && apiKey.StartsWith("sk-", StringComparison.OrdinalIgnoreCase))
                    {
                        provider = "9Router";
                    }

                    // Check per-provider key
                    if (root.TryGetProperty("keysByProvider", out var pDict) && pDict.ValueKind == JsonValueKind.Object)
                    {
                        if (pDict.TryGetProperty(provider, out var pProvKey) && !string.IsNullOrWhiteSpace(pProvKey.GetString()))
                        {
                            apiKey = pProvKey.GetString()!.Trim();
                        }
                    }
                }

                // Fallback từ Python ~/.exam_generator/
                if (string.IsNullOrWhiteSpace(apiKey))
                {
                    string homeDir = Environment.GetFolderPath(Environment.SpecialFolder.UserProfile);
                    string pySettingsFile = Path.Combine(homeDir, ".exam_generator", "app_settings.json");
                    if (File.Exists(pySettingsFile))
                    {
                        try
                        {
                            string json = File.ReadAllText(pySettingsFile);
                            using var doc = JsonDocument.Parse(json);
                            var root = doc.RootElement;
                            if (root.TryGetProperty("selected_ai_provider", out var pyProv) && !string.IsNullOrWhiteSpace(pyProv.GetString()))
                            {
                                provider = pyProv.GetString()!.Trim();
                            }
                            if (root.TryGetProperty("selected_ai_model", out var pyModel) && !string.IsNullOrWhiteSpace(pyModel.GetString()))
                            {
                                model = pyModel.GetString()!.Trim();
                            }
                        }
                        catch { }
                    }

                    // Đọc key từ biến môi trường nếu có
                    string? envKey = Environment.GetEnvironmentVariable("NINEROUTER_API_KEY")
                                  ?? Environment.GetEnvironmentVariable("GEMINI_API_KEY")
                                  ?? Environment.GetEnvironmentVariable("GOOGLE_API_KEY");
                    if (!string.IsNullOrWhiteSpace(envKey))
                    {
                        apiKey = envKey.Trim();
                    }
                }

                // Chuẩn hóa tên Provider
                if (provider.Equals("Google", StringComparison.OrdinalIgnoreCase) || provider.Equals("Gemini", StringComparison.OrdinalIgnoreCase))
                {
                    provider = "Google Gemini";
                }
                else if (provider.StartsWith("OpenAI", StringComparison.OrdinalIgnoreCase))
                {
                    provider = "OpenAI GPT";
                }

                // Cập nhật endpoint tương ứng
                if (provider.Equals("Google Gemini", StringComparison.OrdinalIgnoreCase))
                {
                    endpoint = "https://generativelanguage.googleapis.com/v1beta";
                }
                else if (provider.Equals("Anthropic Claude", StringComparison.OrdinalIgnoreCase) || provider.Equals("Claude", StringComparison.OrdinalIgnoreCase))
                {
                    provider = "Anthropic Claude";
                    endpoint = "https://api.anthropic.com/v1/messages";
                }
                else if (provider.Equals("DeepSeek", StringComparison.OrdinalIgnoreCase))
                {
                    endpoint = "https://api.deepseek.com/v1/chat/completions";
                }
                else if (provider.Equals("OpenAI GPT", StringComparison.OrdinalIgnoreCase) || provider.Equals("OpenAI", StringComparison.OrdinalIgnoreCase))
                {
                    endpoint = "https://api.openai.com/v1/chat/completions";
                }
                else
                {
                    provider = "9Router";
                    endpoint = "http://localhost:20128/v1/chat/completions";
                }

                keys = SplitKeys(apiKey);
            }
            catch (Exception ex)
            {
                Debug.WriteLine($"[DesktopGeminiFactory] GetActiveConfig exception: {ex.Message}");
            }

            return (apiKey, provider, model, endpoint, keys);
        }

        public static async Task<List<string>> Fetch9RouterModelsAsync()
        {
            try
            {
                using var cts = new CancellationTokenSource(TimeSpan.FromSeconds(3));
                var response = await _httpClient.GetAsync("http://localhost:20128/v1/models", cts.Token).ConfigureAwait(false);
                if (response.IsSuccessStatusCode)
                {
                    string body = await response.Content.ReadAsStringAsync().ConfigureAwait(false);
                    using var doc = JsonDocument.Parse(body);
                    if (doc.RootElement.TryGetProperty("data", out var data) && data.ValueKind == JsonValueKind.Array)
                    {
                        var list = new List<string>();
                        foreach (var item in data.EnumerateArray())
                        {
                            if (item.TryGetProperty("id", out var idProp) && !string.IsNullOrWhiteSpace(idProp.GetString()))
                            {
                                list.Add(idProp.GetString()!.Trim());
                            }
                        }
                        if (list.Count > 0) return list;
                    }
                }
            }
            catch { }

            return DefaultModelsByProvider["9Router"];
        }

        public static GeminiClient CreateClient()
        {
            var (apiKey, provider, model, endpoint, keys) = GetActiveConfig();
            var client = new GeminiClient();

            if (keys.Count > 0)
            {
                client.KeyPool.SetKeys(keys);
            }
            else if (!string.IsNullOrWhiteSpace(apiKey))
            {
                client.KeyPool.SetKeys(new[] { apiKey });
            }

            client.DefaultModel = model;

            if (provider == "9Router")
            {
                client.Fallback.NineRouterApiKey = keys.FirstOrDefault() ?? apiKey;
                client.Fallback.NineRouterEndpoint = endpoint;
                client.Fallback.NineRouterModel = model;
            }

            return client;
        }

        /// <summary>
        /// Sinh mã TikZ từ văn bản hoặc hình ảnh sử dụng AI Provider đang kích hoạt (Google Gemini, 9Router, Claude, DeepSeek, OpenAI).
        /// </summary>
        public static async Task<TikzGenerationResult> GenerateTikzAsync(TikzPromptRequest request, CancellationToken ct = default)
        {
            var sw = Stopwatch.StartNew();
            string promptText = !string.IsNullOrEmpty(request.ImageBase64)
                ? PromptCatalog.GetVisionPrompt(request.Prompt, request.DiagramType)
                : PromptCatalog.GetDrawPrompt(request.Prompt, request.DiagramType);

            var execResult = await ExecutePromptAsync(
                promptText,
                request.ImageBase64,
                string.IsNullOrWhiteSpace(request.ImageMimeType) ? "image/png" : request.ImageMimeType,
                ct).ConfigureAwait(false);

            sw.Stop();

            if (!execResult.Success)
            {
                return TikzGenerationResult.Fail(
                    execResult.ErrorMessage ?? "Không thể hoàn thành sinh mã TikZ từ AI.",
                    execResult.ProviderUsed,
                    execResult.ModelUsed,
                    sw.ElapsedMilliseconds);
            }

            string tikzCode = TikzCodeExtractor.ExtractTikzCode(execResult.Content);
            if (string.IsNullOrWhiteSpace(tikzCode))
            {
                return TikzGenerationResult.Fail(
                    "AI không trả về khối mã TikZ hợp lệ.",
                    execResult.ProviderUsed,
                    execResult.ModelUsed,
                    sw.ElapsedMilliseconds,
                    execResult.Content);
            }

            return TikzGenerationResult.Ok(
                tikzCode,
                execResult.ProviderUsed,
                execResult.ModelUsed,
                sw.ElapsedMilliseconds,
                execResult.Content);
        }

        /// <summary>
        /// Thực thi truy vấn AI văn bản và Vision hỗ trợ đa nhà cung cấp với Multi-Key Rotation và Fallback.
        /// </summary>
        public static async Task<AiExecutionResult> ExecutePromptAsync(
            string prompt,
            string? imageBase64 = null,
            string imageMimeType = "image/png",
            CancellationToken ct = default,
            string? overrideProvider = null,
            string? overrideModel = null,
            string? overrideKey = null)
        {
            var sw = Stopwatch.StartNew();
            var (cfgApiKey, cfgProvider, cfgModel, cfgEndpoint, cfgKeys) = GetActiveConfig();

            string provider = overrideProvider ?? cfgProvider;
            string model = overrideModel ?? cfgModel;
            string rawKey = overrideKey ?? cfgApiKey;

            var keys = SplitKeys(rawKey);
            if (keys.Count == 0 && !string.IsNullOrWhiteSpace(rawKey))
            {
                keys.Add(rawKey.Trim());
            }

            if (keys.Count == 0 && provider != "9Router")
            {
                return new AiExecutionResult
                {
                    Success = false,
                    ErrorMessage = $"Chưa cấu hình API Key cho {provider}. Vui lòng mở Cài đặt (⚙️) để nhập API Key.",
                    LatencyMs = sw.ElapsedMilliseconds
                };
            }

            // Nếu 9Router không có key, vẫn có thể dùng local dummy key
            if (keys.Count == 0 && provider == "9Router")
            {
                keys.Add("dummy_key_for_local");
            }

            string endpoint;
            if (provider.Equals("Google Gemini", StringComparison.OrdinalIgnoreCase))
                endpoint = "https://generativelanguage.googleapis.com/v1beta";
            else if (provider.Equals("Anthropic Claude", StringComparison.OrdinalIgnoreCase) || provider.Equals("Claude", StringComparison.OrdinalIgnoreCase))
                endpoint = "https://api.anthropic.com/v1/messages";
            else if (provider.Equals("DeepSeek", StringComparison.OrdinalIgnoreCase))
                endpoint = "https://api.deepseek.com/v1/chat/completions";
            else if (provider.Equals("OpenAI GPT", StringComparison.OrdinalIgnoreCase) || provider.Equals("OpenAI", StringComparison.OrdinalIgnoreCase))
                endpoint = "https://api.openai.com/v1/chat/completions";
            else
                endpoint = "http://localhost:20128/v1/chat/completions";

            string lastErrorMessage = string.Empty;

            // Vòng lặp xoay vòng Multi-Key Rotation
            foreach (var key in keys)
            {
                string cleanKey = key.Trim();
                if (string.IsNullOrEmpty(cleanKey)) continue;

                if (provider.Equals("Google Gemini", StringComparison.OrdinalIgnoreCase))
                {
                    // ── 1. GOOGLE GEMINI DIRECT REST API ──
                    string geminiUrl = $"{endpoint}/models/{model}:generateContent?key={cleanKey}";
                    var partsList = new List<object> { new { text = prompt } };
                    if (!string.IsNullOrEmpty(imageBase64))
                    {
                        partsList.Add(new
                        {
                            inline_data = new
                            {
                                mime_type = imageMimeType,
                                data = imageBase64
                            }
                        });
                    }

                    var geminiReq = new
                    {
                        contents = new[] { new { role = "user", parts = partsList.ToArray() } },
                        generationConfig = new { temperature = 0.2, maxOutputTokens = 4096 }
                    };

                    try
                    {
                        string jsonPayload = JsonSerializer.Serialize(geminiReq, JsonOptions);
                        using var content = new StringContent(jsonPayload, Encoding.UTF8, "application/json");
                        using var response = await _httpClient.PostAsync(geminiUrl, content, ct).ConfigureAwait(false);
                        string responseBody = await response.Content.ReadAsStringAsync().ConfigureAwait(false);

                        if (response.IsSuccessStatusCode)
                        {
                            try
                            {
                                using var doc = JsonDocument.Parse(responseBody);
                                if (doc.RootElement.TryGetProperty("candidates", out var candidates) && candidates.GetArrayLength() > 0)
                                {
                                    var firstCandidate = candidates[0];
                                    if (firstCandidate.TryGetProperty("content", out var cContent) &&
                                        cContent.TryGetProperty("parts", out var parts) && parts.GetArrayLength() > 0)
                                    {
                                        var sb = new StringBuilder();
                                        foreach (var p in parts.EnumerateArray())
                                        {
                                            if (p.TryGetProperty("text", out var pText)) sb.Append(pText.GetString());
                                        }

                                        sw.Stop();
                                        return new AiExecutionResult
                                        {
                                            Success = true,
                                            Content = sb.ToString(),
                                            ProviderUsed = "Google Gemini",
                                            ModelUsed = model,
                                            LatencyMs = sw.ElapsedMilliseconds
                                        };
                                    }
                                }
                            }
                            catch (JsonException)
                            {
                                lastErrorMessage = $"[Google Gemini phản hồi dạng văn bản] {responseBody.Trim()}";
                            }
                        }

                        lastErrorMessage = $"[Gemini HTTP {(int)response.StatusCode}] {response.ReasonPhrase}: {responseBody}";
                        if (responseBody.Contains("RESOURCE_EXHAUSTED", StringComparison.OrdinalIgnoreCase) ||
                            (int)response.StatusCode == 429)
                        {
                            // Quota hết → xoay vòng sang key tiếp theo
                            continue;
                        }
                    }
                    catch (Exception ex)
                    {
                        lastErrorMessage = ex.Message;
                    }
                }
                else if (provider.Equals("Anthropic Claude", StringComparison.OrdinalIgnoreCase))
                {
                    // ── 2. ANTHROPIC CLAUDE DIRECT REST API ──
                    try
                    {
                        var messagesObj = new object[] { new { role = "user", content = prompt } };
                        var claudeReq = new
                        {
                            model = model,
                            max_tokens = 4096,
                            messages = messagesObj
                        };

                        string jsonPayload = JsonSerializer.Serialize(claudeReq, JsonOptions);
                        using var requestMessage = new HttpRequestMessage(HttpMethod.Post, endpoint);
                        requestMessage.Headers.Add("x-api-key", cleanKey);
                        requestMessage.Headers.Add("anthropic-version", "2023-06-01");
                        requestMessage.Content = new StringContent(jsonPayload, Encoding.UTF8, "application/json");

                        using var response = await _httpClient.SendAsync(requestMessage, ct).ConfigureAwait(false);
                        string responseBody = await response.Content.ReadAsStringAsync().ConfigureAwait(false);

                        if (response.IsSuccessStatusCode)
                        {
                            try
                            {
                                using var doc = JsonDocument.Parse(responseBody);
                                if (doc.RootElement.TryGetProperty("content", out var cArray) && cArray.GetArrayLength() > 0)
                                {
                                    string text = cArray[0].GetProperty("text").GetString() ?? string.Empty;
                                    sw.Stop();
                                    return new AiExecutionResult
                                    {
                                        Success = true,
                                        Content = text,
                                        ProviderUsed = "Anthropic Claude",
                                        ModelUsed = model,
                                        LatencyMs = sw.ElapsedMilliseconds
                                    };
                                }
                            }
                            catch (JsonException)
                            {
                                lastErrorMessage = $"[Anthropic Claude phản hồi dạng văn bản] {responseBody.Trim()}";
                            }
                        }

                        lastErrorMessage = $"[Claude HTTP {(int)response.StatusCode}] {response.ReasonPhrase}: {responseBody}";
                        if ((int)response.StatusCode == 429) continue;
                    }
                    catch (Exception ex)
                    {
                        lastErrorMessage = ex.Message;
                    }
                }
                else
                {
                    // ── 3. OPENAI-COMPATIBLE (9Router / DeepSeek / OpenAI) ──
                    // Tạo danh sách candidate models: đối với 9Router, ưu tiên tiền tố ag/ để định tuyến chính xác qua Antigravity
                    var candidateModels = new List<string>();
                    if (provider.Equals("9Router", StringComparison.OrdinalIgnoreCase))
                    {
                        if (model.StartsWith("ag/", StringComparison.OrdinalIgnoreCase))
                        {
                            candidateModels.Add(model);
                            candidateModels.Add(model.Substring(3));
                        }
                        else
                        {
                            candidateModels.Add($"ag/{model}");
                            candidateModels.Add(model);
                        }
                    }
                    else
                    {
                        candidateModels.Add(model);
                    }

                    foreach (var modelAttempt in candidateModels)
                    {
                        try
                        {
                            var openAiReq = new
                            {
                                model = modelAttempt,
                                temperature = 0.2,
                                max_tokens = 4096,
                                stream = false,
                                messages = new object[]
                                {
                                    new
                                    {
                                        role = "user",
                                        content = string.IsNullOrEmpty(imageBase64)
                                            ? (object)prompt
                                            : new object[]
                                            {
                                                new { type = "text", text = prompt },
                                                new { type = "image_url", image_url = new { url = $"data:{imageMimeType};base64,{imageBase64}" } }
                                            }
                                    }
                                }
                            };

                            string jsonPayload = JsonSerializer.Serialize(openAiReq, JsonOptions);
                            using var requestMessage = new HttpRequestMessage(HttpMethod.Post, endpoint);
                            requestMessage.Headers.Authorization = new AuthenticationHeaderValue("Bearer", cleanKey);
                            requestMessage.Content = new StringContent(jsonPayload, Encoding.UTF8, "application/json");

                            using var response = await _httpClient.SendAsync(requestMessage, ct).ConfigureAwait(false);
                            string responseBody = await response.Content.ReadAsStringAsync().ConfigureAwait(false);

                            if (response.IsSuccessStatusCode)
                            {
                                // Xử lý nếu trả về SSE chunks
                                if (responseBody.Contains("data:") && !responseBody.TrimStart().StartsWith("{"))
                                {
                                    var sb = new StringBuilder();
                                    foreach (var line in responseBody.Split(new[] { '\r', '\n' }, StringSplitOptions.RemoveEmptyEntries))
                                    {
                                        string t = line.Trim();
                                        if (t.StartsWith("data:") && t.Length > 5)
                                        {
                                            string chunkJson = t.Substring(5).Trim();
                                            if (chunkJson == "[DONE]") continue;
                                            try
                                            {
                                                using var cdoc = JsonDocument.Parse(chunkJson);
                                                if (cdoc.RootElement.TryGetProperty("choices", out var ch) && ch.GetArrayLength() > 0)
                                                {
                                                    if (ch[0].TryGetProperty("delta", out var delta) && delta.TryGetProperty("content", out var cVal))
                                                    {
                                                        sb.Append(cVal.GetString());
                                                    }
                                                }
                                            }
                                            catch { }
                                        }
                                    }

                                    if (sb.Length > 0)
                                    {
                                        sw.Stop();
                                        return new AiExecutionResult
                                        {
                                            Success = true,
                                            Content = sb.ToString(),
                                            ProviderUsed = provider,
                                            ModelUsed = modelAttempt,
                                            LatencyMs = sw.ElapsedMilliseconds
                                        };
                                    }
                                }

                                // Xử lý JSON phản hồi chuẩn
                                try
                                {
                                    using var doc = JsonDocument.Parse(responseBody);
                                    if (doc.RootElement.TryGetProperty("choices", out var choices) && choices.GetArrayLength() > 0)
                                    {
                                        var firstChoice = choices[0];
                                        if (firstChoice.TryGetProperty("message", out var msg) && msg.TryGetProperty("content", out var pContent))
                                        {
                                            string content = pContent.GetString() ?? string.Empty;
                                            sw.Stop();
                                            return new AiExecutionResult
                                            {
                                                Success = true,
                                                Content = content,
                                                ProviderUsed = provider,
                                                ModelUsed = modelAttempt,
                                                LatencyMs = sw.ElapsedMilliseconds
                                            };
                                        }
                                    }
                                }
                                catch (JsonException)
                                {
                                    lastErrorMessage = $"[{provider} phản hồi dạng văn bản] {responseBody.Trim()}";
                                }
                            }

                            if (string.IsNullOrEmpty(lastErrorMessage))
                            {
                                lastErrorMessage = $"[{provider} HTTP {(int)response.StatusCode}] {response.ReasonPhrase}: {responseBody.Trim()}";
                            }

                            // Nếu 404 hoặc model_not_found/No active credentials và còn candidate model khác → thử candidate tiếp theo
                            if (((int)response.StatusCode == 404 || responseBody.Contains("model_not_found", StringComparison.OrdinalIgnoreCase) || responseBody.Contains("No active credentials", StringComparison.OrdinalIgnoreCase))
                                && modelAttempt != candidateModels.Last())
                            {
                                continue;
                            }

                            // Nếu 429 → xoay vòng sang key tiếp theo
                            if ((int)response.StatusCode == 429 || responseBody.Contains("quota", StringComparison.OrdinalIgnoreCase))
                            {
                                break;
                            }
                        }
                        catch (Exception ex)
                        {
                            lastErrorMessage = ex.Message;
                        }
                    }
                }
            }

            sw.Stop();
            return new AiExecutionResult
            {
                Success = false,
                ProviderUsed = provider,
                ModelUsed = model,
                LatencyMs = sw.ElapsedMilliseconds,
                ErrorMessage = string.IsNullOrEmpty(lastErrorMessage)
                    ? $"Không nhận được phản hồi hợp lệ từ máy chủ {provider}."
                    : lastErrorMessage
            };
        }
    }
}
