using System;
using System.Text.Json;
using System.Text.Json.Serialization;

namespace MatrixExamAI.Shared.Models
{
    /// <summary>
    /// Gói tin yêu cầu chuẩn JSON-RPC 2.0 truyền qua postMessage.
    /// </summary>
    public class JsonRpcRequest
    {
        [JsonPropertyName("jsonrpc")]
        public string JsonRpc { get; set; } = "2.0";

        [JsonPropertyName("id")]
        public object? Id { get; set; }

        [JsonPropertyName("method")]
        public string Method { get; set; } = string.Empty;

        [JsonPropertyName("params")]
        public JsonElement? Params { get; set; }
    }

    /// <summary>
    /// Gói tin phản hồi chuẩn JSON-RPC 2.0.
    /// </summary>
    public class JsonRpcResponse
    {
        [JsonPropertyName("jsonrpc")]
        public string JsonRpc { get; set; } = "2.0";

        [JsonPropertyName("id")]
        public object? Id { get; set; }

        [JsonPropertyName("result")]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public object? Result { get; set; }

        [JsonPropertyName("error")]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public JsonRpcError? Error { get; set; }

        public static JsonRpcResponse CreateSuccess(object? id, object? result)
        {
            return new JsonRpcResponse
            {
                Id = id,
                Result = result
            };
        }

        public static JsonRpcResponse CreateError(object? id, int code, string message, object? data = null)
        {
            return new JsonRpcResponse
            {
                Id = id,
                Error = new JsonRpcError
                {
                    Code = code,
                    Message = message,
                    Data = data
                }
            };
        }
    }

    /// <summary>
    /// Thông tin lỗi chuẩn JSON-RPC 2.0.
    /// </summary>
    public class JsonRpcError
    {
        [JsonPropertyName("code")]
        public int Code { get; set; }

        [JsonPropertyName("message")]
        public string Message { get; set; } = string.Empty;

        [JsonPropertyName("data")]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public object? Data { get; set; }
    }
}
