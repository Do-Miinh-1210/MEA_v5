using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Net;
using System.Net.Http;
using System.Text;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using MatrixExamAI.Shared.Models;

namespace MatrixExamAI.Shared.AI
{
    /// <summary>
    /// Bản triển khai thuần C# gọi trực tiếp Google Gemini REST API (v1beta/models/gemini-3.8-flash:generateContent),
    /// tích hợp xoay vòng API key, xử lý thị giác đa phương thức (multimodal vision) và chuyển hướng dự phòng (fallback).
    /// </summary>
    public class GeminiClient : IGeminiClient
    {
        private readonly HttpClient _httpClient;
        private static readonly JsonSerializerOptions JsonOptions = new JsonSerializerOptions
        {
            PropertyNamingPolicy = null,
            PropertyNameCaseInsensitive = true
        };

        public ApiKeyPoolManager KeyPool { get; }
        public FallbackOrchestrator Fallback { get; }
        public string ActiveProvider { get; set; } = "Google Gemini";
        public string DefaultModel { get; set; } = "gemini-3.8-flash";
        public string BaseUrl { get; set; } = "https://generativelanguage.googleapis.com/v1beta";

        public GeminiClient(
            ApiKeyPoolManager? keyPool = null,
            FallbackOrchestrator? fallback = null,
            HttpClient? httpClient = null)
        {
            KeyPool = keyPool ?? new ApiKeyPoolManager();
            Fallback = fallback ?? new FallbackOrchestrator(httpClient);
            _httpClient = httpClient ?? new HttpClient();
        }

        public async Task<TikzGenerationResult> GenerateTikzAsync(TikzPromptRequest request, CancellationToken ct = default)
        {
            var stopwatch = Stopwatch.StartNew();

            string model = !string.IsNullOrWhiteSpace(request.ModelOverride)
                ? request.ModelOverride!
                : DefaultModel;

            // Xây dựng prompt chuẩn Thầy Đỗ Minh
            string fullPromptText;
            if (!string.IsNullOrEmpty(request.ImageBase64))
            {
                string extra = !string.IsNullOrWhiteSpace(request.ExtraPrompt)
                    ? request.ExtraPrompt!
                    : request.Prompt;

                fullPromptText = PromptCatalog.GetVisionPrompt(
                    extra,
                    request.DiagramType,
                    request.EnableNotes,
                    request.BbtNoFrame,
                    request.ReferenceExamples ?? string.Empty);
            }
            else
            {
                fullPromptText = PromptCatalog.GetDrawPrompt(
                    request.Prompt,
                    request.DiagramType,
                    request.ReferenceExamples ?? string.Empty);
            }

            // 1. Nếu Provider là 9Router, OpenAI GPT hoặc DeepSeek -> định tuyến trực tiếp qua FallbackOrchestrator
            if (ActiveProvider.Equals("9Router", StringComparison.OrdinalIgnoreCase) ||
                ActiveProvider.Equals("OpenAI GPT", StringComparison.OrdinalIgnoreCase) ||
                ActiveProvider.Equals("DeepSeek", StringComparison.OrdinalIgnoreCase))
            {
                if (ActiveProvider.Equals("9Router", StringComparison.OrdinalIgnoreCase) &&
                    string.IsNullOrWhiteSpace(Fallback.NineRouterApiKey) &&
                    KeyPool.TotalKeys > 0)
                {
                    Fallback.NineRouterApiKey = KeyPool.GetNextAvailableKey()?.Key;
                }
                var fallbackRes = await Fallback.ExecuteFallbackAsync(request, fullPromptText, ct).ConfigureAwait(false);
                return fallbackRes;
            }

            // 2. Google Gemini: Xoay vòng key và dự phòng
            int attempts = 0;
            int maxKeyAttempts = Math.Max(1, KeyPool.TotalKeys);
            string lastError = string.Empty;

            while (attempts < maxKeyAttempts)
            {
                var keyEntry = KeyPool.GetNextAvailableKey();
                if (keyEntry == null)
                {
                    break;
                }

                attempts++;
                string apiKey = keyEntry.Key;

                // Nếu API key có tiền tố sk- (9Router / OpenAI), định tuyến qua Fallback Orchestrator
                if (apiKey.StartsWith("sk-", StringComparison.OrdinalIgnoreCase))
                {
                    if (string.IsNullOrWhiteSpace(Fallback.NineRouterApiKey))
                    {
                        Fallback.NineRouterApiKey = apiKey;
                    }
                    var fallbackRes = await Fallback.ExecuteFallbackAsync(request, fullPromptText, ct).ConfigureAwait(false);
                    if (fallbackRes.Success)
                    {
                        KeyPool.ReportSuccess(apiKey);
                        return fallbackRes;
                    }

                    KeyPool.ReportFailure(apiKey, HttpStatusCode.BadRequest);
                    lastError = fallbackRes.ErrorMessage ?? "9Router/OpenAI fallback failed.";
                    continue;
                }

                try
                {
                    var geminiReq = BuildGeminiRequest(request, fullPromptText);
                    string jsonPayload = JsonSerializer.Serialize(geminiReq, JsonOptions);

                    string endpoint = $"{BaseUrl}/models/{model}:generateContent?key={apiKey}";
                    using (var content = new StringContent(jsonPayload, Encoding.UTF8, "application/json"))
                    using (var response = await _httpClient.PostAsync(endpoint, content, ct).ConfigureAwait(false))
                    {
                        string responseBody = await response.Content.ReadAsStringAsync().ConfigureAwait(false);

                        if (response.IsSuccessStatusCode)
                        {
                            KeyPool.ReportSuccess(apiKey);
                            stopwatch.Stop();

                            var geminiResp = JsonSerializer.Deserialize<GeminiGenerateResponse>(responseBody, JsonOptions);
                            string? textContent = ExtractTextFromGeminiResponse(geminiResp);

                            if (string.IsNullOrWhiteSpace(textContent))
                            {
                                return TikzGenerationResult.Fail(
                                    "Google Gemini phản hồi thành công nhưng không có nội dung văn bản (có thể bị bộ lọc an toàn chặn).",
                                    "GeminiDirect",
                                    model,
                                    stopwatch.ElapsedMilliseconds,
                                    responseBody);
                            }

                            string extractedTikz = TikzCodeExtractor.ExtractTikzCode(textContent);
                            return TikzGenerationResult.Ok(
                                extractedTikz,
                                "GeminiDirect",
                                model,
                                stopwatch.ElapsedMilliseconds,
                                textContent ?? string.Empty);
                        }

                        // Xử lý mã lỗi HTTP
                        int? retryAfter = null;
                        if (response.Headers.RetryAfter != null && response.Headers.RetryAfter.Delta.HasValue)
                        {
                            retryAfter = (int)response.Headers.RetryAfter.Delta.Value.TotalSeconds;
                        }

                        KeyPool.ReportFailure(apiKey, response.StatusCode, retryAfter);
                        lastError = $"[HTTP {(int)response.StatusCode}] {response.ReasonPhrase}: {responseBody}";

                        // Nếu là lỗi 429 hoặc 403, tiếp tục vòng lặp thử key tiếp theo
                        if (response.StatusCode == (HttpStatusCode)429 ||
                            response.StatusCode == HttpStatusCode.Forbidden ||
                            response.StatusCode == HttpStatusCode.Unauthorized)
                        {
                            continue;
                        }

                        // Lỗi khác (400, 500...), cũng thử key tiếp theo hoặc thoát ra fallback
                    }
                }
                catch (HttpRequestException httpEx)
                {
                    lastError = $"Lỗi kết nối mạng Gemini: {httpEx.Message}";
                    KeyPool.ReportFailure(apiKey, HttpStatusCode.ServiceUnavailable);
                }
                catch (Exception ex)
                {
                    lastError = $"Ngoại lệ khi gọi Gemini: {ex.Message}";
                }
            }

            // Nếu toàn bộ key Gemini đều thất bại, chuyển hướng sang Fallback (9Router / OpenAI)
            if (Fallback.HasConfiguredFallback())
            {
                var fallbackResult = await Fallback.ExecuteFallbackAsync(request, fullPromptText, ct).ConfigureAwait(false);
                if (fallbackResult.Success)
                {
                    return fallbackResult;
                }
            }

            stopwatch.Stop();
            return TikzGenerationResult.Fail(
                $"Không thể hoàn thành sinh mã TikZ qua Gemini. Lý do: {lastError}. {KeyPool.GetStatusSummary()}",
                "GeminiClient",
                model,
                stopwatch.ElapsedMilliseconds);
        }

        public async Task<TikzGenerationResult> EditTikzAsync(string currentCode, string editRequest, CancellationToken ct = default)
        {
            string prompt = PromptCatalog.GetEditPrompt(currentCode, editRequest);
            var req = new TikzPromptRequest
            {
                Prompt = prompt,
                DiagramType = DiagramType.Custom
            };
            return await GenerateTikzAsync(req, ct).ConfigureAwait(false);
        }

        public async Task<TikzGenerationResult> OptimizeTikzAsync(string currentCode, CancellationToken ct = default)
        {
            string prompt = PromptCatalog.GetOptimizationPrompt(currentCode);
            var req = new TikzPromptRequest
            {
                Prompt = prompt,
                DiagramType = DiagramType.Custom
            };
            return await GenerateTikzAsync(req, ct).ConfigureAwait(false);
        }

        private GeminiGenerateRequest BuildGeminiRequest(TikzPromptRequest request, string promptText)
        {
            var geminiReq = new GeminiGenerateRequest
            {
                GenerationConfig = new GeminiGenerationConfig
                {
                    Temperature = request.Temperature,
                    MaxOutputTokens = request.MaxOutputTokens
                }
            };

            var userContent = new GeminiContent { Role = "user" };

            // Text part
            userContent.Parts.Add(new GeminiPart { Text = promptText });

            // Multimodal image part nếu có
            if (!string.IsNullOrEmpty(request.ImageBase64))
            {
                string mime = string.IsNullOrWhiteSpace(request.ImageMimeType) ? "image/png" : request.ImageMimeType;
                userContent.Parts.Add(new GeminiPart
                {
                    InlineData = new GeminiBlob
                    {
                        MimeType = mime,
                        Data = request.ImageBase64!
                    }
                });
            }

            geminiReq.Contents.Add(userContent);
            return geminiReq;
        }

        private string? ExtractTextFromGeminiResponse(GeminiGenerateResponse? response)
        {
            if (response?.Candidates == null || response.Candidates.Count == 0)
            {
                return null;
            }

            var parts = response.Candidates[0].Content?.Parts;
            if (parts == null || parts.Count == 0)
            {
                return null;
            }

            var sb = new StringBuilder();
            foreach (var part in parts)
            {
                if (!string.IsNullOrEmpty(part.Text))
                {
                    sb.Append(part.Text);
                }
            }

            return sb.ToString();
        }
    }
}
