using System;
using System.Threading;
using System.Threading.Tasks;
using MatrixExamAI.Shared.Models;

namespace MatrixExamAI.Shared.AI
{
    /// <summary>
    /// Tham số sự kiện phát tiến độ tự sửa lỗi mã TikZ.
    /// </summary>
    public class AutoHealingProgressEventArgs : EventArgs
    {
        public int Attempt { get; set; }
        public int MaxAttempts { get; set; }
        public string ErrorSnippet { get; set; } = string.Empty;
        public string FaultyCode { get; set; } = string.Empty;
        public string? RepairedCode { get; set; }
        public bool IsSuccess { get; set; }
    }

    /// <summary>
    /// Giao diện dịch vụ tự phục hồi mã TikZ gặp lỗi thông qua vòng lặp phản hồi thông minh với AI.
    /// </summary>
    public interface ITikzAutoHealer
    {
        /// <summary>
        /// Sự kiện phát ra mỗi khi một lượt sửa lỗi được tiến hành.
        /// </summary>
        event EventHandler<AutoHealingProgressEventArgs>? ProgressChanged;

        /// <summary>
        /// Thực hiện vòng lặp tự sửa lỗi mã TikZ dựa trên thông báo lỗi của trình biên dịch (tối đa 3 lượt).
        /// </summary>
        Task<TikzGenerationResult> AutoHealAsync(
            string brokenCode,
            string latexLog,
            TikzPromptRequest originalRequest,
            int maxAttempts = 3,
            CancellationToken ct = default);
    }
}
