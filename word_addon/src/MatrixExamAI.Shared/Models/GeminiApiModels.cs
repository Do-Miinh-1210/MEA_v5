using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace MatrixExamAI.Shared.Models
{
    // =========================================================================
    // GOOGLE GEMINI REST API DTOs (v1beta/models/{model}:generateContent)
    // =========================================================================

    public class GeminiGenerateRequest
    {
        [JsonPropertyName("contents")]
        public List<GeminiContent> Contents { get; set; } = new List<GeminiContent>();

        [JsonPropertyName("systemInstruction")]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public GeminiContent? SystemInstruction { get; set; }

        [JsonPropertyName("generationConfig")]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public GeminiGenerationConfig? GenerationConfig { get; set; }
    }

    public class GeminiContent
    {
        [JsonPropertyName("role")]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public string? Role { get; set; }

        [JsonPropertyName("parts")]
        public List<GeminiPart> Parts { get; set; } = new List<GeminiPart>();
    }

    public class GeminiPart
    {
        [JsonPropertyName("text")]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public string? Text { get; set; }

        [JsonPropertyName("inlineData")]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public GeminiBlob? InlineData { get; set; }
    }

    public class GeminiBlob
    {
        [JsonPropertyName("mimeType")]
        public string MimeType { get; set; } = "image/png";

        [JsonPropertyName("data")]
        public string Data { get; set; } = string.Empty; // Base64
    }

    public class GeminiGenerationConfig
    {
        [JsonPropertyName("temperature")]
        public double Temperature { get; set; } = 0.2;

        [JsonPropertyName("maxOutputTokens")]
        public int MaxOutputTokens { get; set; } = 8192;

        [JsonPropertyName("topP")]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public double? TopP { get; set; }
    }

    public class GeminiGenerateResponse
    {
        [JsonPropertyName("candidates")]
        public List<GeminiCandidate>? Candidates { get; set; }

        [JsonPropertyName("promptFeedback")]
        public GeminiPromptFeedback? PromptFeedback { get; set; }

        [JsonPropertyName("error")]
        public GeminiErrorResponse? Error { get; set; }
    }

    public class GeminiCandidate
    {
        [JsonPropertyName("content")]
        public GeminiContentResponse? Content { get; set; }

        [JsonPropertyName("finishReason")]
        public string? FinishReason { get; set; }
    }

    public class GeminiContentResponse
    {
        [JsonPropertyName("parts")]
        public List<GeminiPartResponse>? Parts { get; set; }

        [JsonPropertyName("role")]
        public string? Role { get; set; }
    }

    public class GeminiPartResponse
    {
        [JsonPropertyName("text")]
        public string? Text { get; set; }
    }

    public class GeminiPromptFeedback
    {
        [JsonPropertyName("blockReason")]
        public string? BlockReason { get; set; }
    }

    public class GeminiErrorResponse
    {
        [JsonPropertyName("code")]
        public int Code { get; set; }

        [JsonPropertyName("message")]
        public string Message { get; set; } = string.Empty;

        [JsonPropertyName("status")]
        public string? Status { get; set; }
    }

    // =========================================================================
    // OPENAI / 9ROUTER COMPATIBLE DTOs (/v1/chat/completions)
    // =========================================================================

    public class OpenAiChatRequest
    {
        [JsonPropertyName("model")]
        public string Model { get; set; } = "gemini-3.8-flash";

        [JsonPropertyName("messages")]
        public List<OpenAiMessage> Messages { get; set; } = new List<OpenAiMessage>();

        [JsonPropertyName("temperature")]
        public double Temperature { get; set; } = 0.2;

        [JsonPropertyName("max_tokens")]
        public int MaxTokens { get; set; } = 8192;
    }

    public class OpenAiMessage
    {
        [JsonPropertyName("role")]
        public string Role { get; set; } = "user";

        [JsonPropertyName("content")]
        public object Content { get; set; } = string.Empty; // string or List<OpenAiContentPart>
    }

    public class OpenAiContentPart
    {
        [JsonPropertyName("type")]
        public string Type { get; set; } = "text";

        [JsonPropertyName("text")]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public string? Text { get; set; }

        [JsonPropertyName("image_url")]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public OpenAiImageUrlContainer? ImageUrl { get; set; }
    }

    public class OpenAiImageUrlContainer
    {
        [JsonPropertyName("url")]
        public string Url { get; set; } = string.Empty; // "data:image/png;base64,..."
    }

    public class OpenAiChatResponse
    {
        [JsonPropertyName("id")]
        public string? Id { get; set; }

        [JsonPropertyName("choices")]
        public List<OpenAiChoice>? Choices { get; set; }

        [JsonPropertyName("error")]
        public OpenAiError? Error { get; set; }
    }

    public class OpenAiChoice
    {
        [JsonPropertyName("index")]
        public int Index { get; set; }

        [JsonPropertyName("message")]
        public OpenAiResponseMessage? Message { get; set; }

        [JsonPropertyName("finish_reason")]
        public string? FinishReason { get; set; }
    }

    public class OpenAiResponseMessage
    {
        [JsonPropertyName("role")]
        public string? Role { get; set; }

        [JsonPropertyName("content")]
        public string? Content { get; set; }
    }

    public class OpenAiError
    {
        [JsonPropertyName("message")]
        public string Message { get; set; } = string.Empty;

        [JsonPropertyName("type")]
        public string? Type { get; set; }

        [JsonPropertyName("code")]
        public object? Code { get; set; }
    }
}
