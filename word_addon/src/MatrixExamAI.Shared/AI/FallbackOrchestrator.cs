using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Linq;
using System.Net.Http;
using System.Net.Http.Headers;
using System.Text;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using MatrixExamAI.Shared.Models;

namespace MatrixExamAI.Shared.AI
{
    /// <summary>
    /// Điều phối dự phòng đa nhà cung cấp (9Router / OpenAI Compatible) khi Google Gemini trực tiếp bị gián đoạn hoặc hết quota.
    /// </summary>
    public class FallbackOrchestrator
    {
        private readonly HttpClient _httpClient;
        private static readonly JsonSerializerOptions JsonOptions = new JsonSerializerOptions
        {
            PropertyNamingPolicy = null,
            PropertyNameCaseInsensitive = true
        };

        /// <summary>
        /// Cấu hình endpoint 9Router (mặc định localhost:20128/v1/chat/completions).
        /// </summary>
        public string NineRouterEndpoint { get; set; } = "http://localhost:20128/v1/chat/completions";

        /// <summary>
        /// API Key 9Router nếu có.
        /// </summary>
        public string? NineRouterApiKey { get; set; }

        /// <summary>
        /// Tên model dùng trên 9Router (mặc định ag/gemini-3.8-flash).
        /// </summary>
        public string NineRouterModel { get; set; } = "ag/gemini-3.8-flash";

        /// <summary>
        /// Cấu hình endpoint OpenAI tương thích (mặc định https://api.openai.com/v1/chat/completions).
        /// </summary>
        public string OpenAiEndpoint { get; set; } = "https://api.openai.com/v1/chat/completions";

        /// <summary>
        /// API Key OpenAI / Proxy tùy chỉnh.
        /// </summary>
        public string? OpenAiApiKey { get; set; }

        /// <summary>
        /// Tên model dùng trên OpenAI / Proxy (mặc định gpt-4o hoặc gemini-3.8-flash qua proxy).
        /// </summary>
        public string OpenAiModel { get; set; } = "gemini-3.8-flash";

        public FallbackOrchestrator(HttpClient? httpClient = null)
        {
            _httpClient = httpClient ?? new HttpClient();
        }

        /// <summary>
        /// Kiểm tra xem có nhà cung cấp dự phòng nào được cấu hình API key hay không.
        /// </summary>
        public bool HasConfiguredFallback()
        {
            return !string.IsNullOrWhiteSpace(NineRouterApiKey) || !string.IsNullOrWhiteSpace(OpenAiApiKey);
        }

        /// <summary>
        /// Thực thi yêu cầu sinh mã TikZ qua nhà cung cấp dự phòng (ưu tiên 9Router, sau đó OpenAI).
        /// </summary>
        public async Task<TikzGenerationResult> ExecuteFallbackAsync(
            TikzPromptRequest request,
            string fullPromptText,
            CancellationToken ct = default)
        {
            var stopwatch = Stopwatch.StartNew();

            string lastErrorDetail = string.Empty;

            // 1. Thử 9Router nếu có key hoặc đang dùng 9Router
            string key9 = !string.IsNullOrWhiteSpace(NineRouterApiKey) ? NineRouterApiKey! : "sk-local-9router";
            if (!string.IsNullOrWhiteSpace(key9))
            {
                string baseModel = !string.IsNullOrWhiteSpace(request.ModelOverride) ? request.ModelOverride! : NineRouterModel;
                var candidateModels = new List<string>();
                if (!string.IsNullOrWhiteSpace(baseModel))
                {
                    candidateModels.Add(baseModel);
                    if (baseModel.StartsWith("ag/", StringComparison.OrdinalIgnoreCase))
                    {
                        if (baseModel.EndsWith("-high", StringComparison.OrdinalIgnoreCase))
                        {
                            candidateModels.Add(baseModel.Substring(0, baseModel.Length - 5));
                        }
                    }
                    else
                    {
                        candidateModels.Add($"ag/{baseModel}");
                    }
                }
                candidateModels.Add("ag/gemini-3.8-flash-high");
                candidateModels.Add("ag/gemini-3.8-flash");
                candidateModels.Add("ag/gemini-3.7-flash-high");
                candidateModels.Add("ag/claude-sonnet-5-5");

                foreach (var modelAttempt in candidateModels.Distinct(StringComparer.OrdinalIgnoreCase))
                {
                    try
                    {
                        var result = await CallOpenAiCompatibleAsync(
                            NineRouterEndpoint,
                            key9,
                            modelAttempt,
                            fullPromptText,
                            request.ImageBase64,
                            request.ImageMimeType,
                            request.Temperature,
                            request.MaxOutputTokens,
                            "9Router",
                            stopwatch,
                            ct).ConfigureAwait(false);

                        if (result.Success)
                        {
                            return result;
                        }
                        lastErrorDetail = result.ErrorMessage ?? "9Router phản hồi không thành công.";
                    }
                    catch (HttpRequestException httpEx)
                    {
                        lastErrorDetail = $"Không thể kết nối đến 9Router tại {NineRouterEndpoint}. Hãy khởi động 9Router (hoặc mở cổng 20128). Chi tiết: {httpEx.Message}";
                        Debug.WriteLine($"[FallbackOrchestrator] 9Router connection error: {httpEx.Message}");
                        break;
                    }
                    catch (Exception ex)
                    {
                        lastErrorDetail = $"Lỗi gọi 9Router: {ex.Message}";
                        Debug.WriteLine($"[FallbackOrchestrator] 9Router error: {ex.Message}");
                    }
                }
            }

            // 2. Thử OpenAI / Custom Proxy nếu có key
            if (!string.IsNullOrWhiteSpace(OpenAiApiKey))
            {
                try
                {
                    var result = await CallOpenAiCompatibleAsync(
                        OpenAiEndpoint,
                        OpenAiApiKey!,
                        OpenAiModel,
                        fullPromptText,
                        request.ImageBase64,
                        request.ImageMimeType,
                        request.Temperature,
                        request.MaxOutputTokens,
                        "OpenAiCompatible",
                        stopwatch,
                        ct).ConfigureAwait(false);

                    if (result.Success)
                    {
                        return result;
                    }
                    lastErrorDetail = result.ErrorMessage ?? "OpenAI phản hồi không thành công.";
                }
                catch (Exception ex)
                {
                    lastErrorDetail = $"Lỗi gọi OpenAI: {ex.Message}";
                    Debug.WriteLine($"[FallbackOrchestrator] OpenAiCompatible error: {ex.Message}");
                }
            }

            stopwatch.Stop();
            string failMsg = !string.IsNullOrWhiteSpace(lastErrorDetail)
                ? lastErrorDetail
                : "Tất cả các dịch vụ dự phòng (9Router / OpenAI) đều không phản hồi hoặc chưa được cấu hình API Key. Vui lòng mở Cài đặt (⚙️) để nhập API Key.";

            return TikzGenerationResult.Fail(
                failMsg,
                "FallbackOrchestrator",
                string.Empty,
                stopwatch.ElapsedMilliseconds);
        }

        private async Task<TikzGenerationResult> CallOpenAiCompatibleAsync(
            string endpoint,
            string apiKey,
            string model,
            string promptText,
            string? imageBase64,
            string imageMimeType,
            double temperature,
            int maxTokens,
            string providerName,
            Stopwatch stopwatch,
            CancellationToken ct)
        {
            var openAiReq = new OpenAiChatRequest
            {
                Model = model,
                Temperature = temperature,
                MaxTokens = maxTokens,
                Stream = false
            };

            var userMsg = new OpenAiMessage { Role = "user" };

            if (!string.IsNullOrEmpty(imageBase64))
            {
                // Multimodal Vision Content Parts
                string mime = string.IsNullOrWhiteSpace(imageMimeType) ? "image/png" : imageMimeType;
                var parts = new List<OpenAiContentPart>
                {
                    new OpenAiContentPart { Type = "text", Text = promptText },
                    new OpenAiContentPart
                    {
                        Type = "image_url",
                        ImageUrl = new OpenAiImageUrlContainer
                        {
                            Url = $"data:{mime};base64,{imageBase64}"
                        }
                    }
                };
                userMsg.Content = parts;
            }
            else
            {
                userMsg.Content = promptText;
            }

            openAiReq.Messages.Add(userMsg);

            string jsonBody = JsonSerializer.Serialize(openAiReq, JsonOptions);
            using (var requestMessage = new HttpRequestMessage(HttpMethod.Post, endpoint))
            {
                requestMessage.Headers.Authorization = new AuthenticationHeaderValue("Bearer", apiKey.Trim());
                requestMessage.Content = new StringContent(jsonBody, Encoding.UTF8, "application/json");

                using (var response = await _httpClient.SendAsync(requestMessage, ct).ConfigureAwait(false))
                {
                    string responseBody = await response.Content.ReadAsStringAsync().ConfigureAwait(false);
                    stopwatch.Stop();

                    if (!response.IsSuccessStatusCode)
                    {
                        return TikzGenerationResult.Fail(
                            $"[HTTP {(int)response.StatusCode}] {response.ReasonPhrase}: {responseBody}",
                            providerName,
                            model,
                            stopwatch.ElapsedMilliseconds,
                            responseBody);
                    }

                    string? assistantContent = null;

                    // Hỗ trợ xử lý cả dạng SSE Stream (data: {...}) và JSON Object chuẩn
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
                                        else if (ch[0].TryGetProperty("message", out var msg) && msg.TryGetProperty("content", out var mVal))
                                        {
                                            sb.Append(mVal.GetString());
                                        }
                                    }
                                }
                                catch { }
                            }
                        }
                        if (sb.Length > 0)
                        {
                            assistantContent = sb.ToString();
                        }
                    }

                    if (assistantContent == null)
                    {
                        var chatResponse = JsonSerializer.Deserialize<OpenAiChatResponse>(responseBody, JsonOptions);
                        assistantContent = chatResponse?.Choices != null && chatResponse.Choices.Count > 0
                            ? chatResponse.Choices[0].Message?.Content
                            : null;
                    }

                    if (string.IsNullOrWhiteSpace(assistantContent))
                    {
                        return TikzGenerationResult.Fail(
                            "Phản hồi từ dịch vụ dự phòng không chứa nội dung sinh mã.",
                            providerName,
                            model,
                            stopwatch.ElapsedMilliseconds,
                            responseBody);
                    }

                    string extractedTikz = TikzCodeExtractor.ExtractTikzCode(assistantContent);
                    return TikzGenerationResult.Ok(
                        extractedTikz,
                        providerName,
                        model,
                        stopwatch.ElapsedMilliseconds,
                        assistantContent ?? string.Empty);
                }
            }
        }
    }
}
