using System;
using System.Diagnostics;
using System.Threading;
using System.Threading.Tasks;
using MatrixExamAI.Shared.Models;
using MatrixExamAI.Shared.Tikz;
using MatrixExamAI.Shared.Validation;

namespace MatrixExamAI.Shared.AI
{
    /// <summary>
    /// Bản triển khai vòng lặp tự sửa lỗi mã TikZ (Auto-Healing Loop) tối đa 3 lần:
    /// Trích xuất dòng lỗi và nguyên nhân từ log pdflatex -> Đưa vào Prompt sửa lỗi AI -> Biên dịch lại -> Hoàn tất.
    /// </summary>
    public class AutoHealingService : ITikzAutoHealer
    {
        private readonly IGeminiClient _geminiClient;
        private readonly ITikzCompiler _compiler;

        public event EventHandler<AutoHealingProgressEventArgs>? ProgressChanged;

        public AutoHealingService(IGeminiClient geminiClient, ITikzCompiler compiler)
        {
            _geminiClient = geminiClient ?? throw new ArgumentNullException(nameof(geminiClient));
            _compiler = compiler ?? throw new ArgumentNullException(nameof(compiler));
        }

        public async Task<TikzGenerationResult> AutoHealAsync(
            string brokenCode,
            string latexLog,
            TikzPromptRequest originalRequest,
            int maxAttempts = 3,
            CancellationToken ct = default)
        {
            var stopwatch = Stopwatch.StartNew();

            string currentBrokenCode = brokenCode;
            string currentLog = latexLog;
            int attempts = 0;
            string lastErrorDescription = string.Empty;

            while (attempts < maxAttempts)
            {
                attempts++;
                ct.ThrowIfCancellationRequested();

                // 1. Phân tích log LaTeX để trích xuất dòng lỗi và mô tả
                var parsedError = LatexErrorLogParser.ParseLog(currentLog);
                string errorSnippet = parsedError != null
                    ? parsedError.ToString()
                    : "Lỗi cú pháp không sinh được PDF từ pdflatex.";

                lastErrorDescription = errorSnippet;

                // Phát sự kiện bắt đầu vòng lặp sửa lỗi
                OnProgressChanged(new AutoHealingProgressEventArgs
                {
                    Attempt = attempts,
                    MaxAttempts = maxAttempts,
                    ErrorSnippet = errorSnippet,
                    FaultyCode = currentBrokenCode,
                    IsSuccess = false
                });

                // 2. Tạo prompt sửa lỗi chuyên dụng
                string healPrompt = PromptCatalog.GetAutoHealingPrompt(currentBrokenCode, errorSnippet, attempts);

                var healRequest = new TikzPromptRequest
                {
                    Prompt = healPrompt,
                    DiagramType = originalRequest?.DiagramType ?? DiagramType.Custom,
                    Temperature = 0.1, // Giảm nhiệt độ để AI tập trung chính xác vào sửa lỗi
                    MaxOutputTokens = originalRequest?.MaxOutputTokens ?? 8192,
                    ModelOverride = originalRequest?.ModelOverride
                };

                // 3. Gọi AI sinh mã sửa đổi
                var aiResult = await _geminiClient.GenerateTikzAsync(healRequest, ct).ConfigureAwait(false);
                if (!aiResult.Success || string.IsNullOrWhiteSpace(aiResult.TikzCode))
                {
                    // Lượt sửa lỗi này thất bại trong việc gọi AI
                    continue;
                }

                // 4. Áp dụng Auto-Fix nhanh (loại bỏ line cap=round, đổi patterns...)
                string repairedCode = TikzPreflightValidator.AutoFix(aiResult.TikzCode);

                // 5. Thử biên dịch lại mã đã sửa
                var compileReq = new TikzCompileRequest
                {
                    TikzCode = repairedCode,
                    Format = TikzExportFormat.Png,
                    TimeoutSeconds = 15
                };

                var compileResult = await _compiler.CompileAsync(compileReq, ct).ConfigureAwait(false);

                if (compileResult.Success)
                {
                    // Tự sửa lỗi thành công!
                    stopwatch.Stop();

                    OnProgressChanged(new AutoHealingProgressEventArgs
                    {
                        Attempt = attempts,
                        MaxAttempts = maxAttempts,
                        ErrorSnippet = "Đã tự sửa lỗi thành công và biên dịch hoàn tất.",
                        FaultyCode = currentBrokenCode,
                        RepairedCode = repairedCode,
                        IsSuccess = true
                    });

                    return TikzGenerationResult.Ok(
                        repairedCode,
                        aiResult.ProviderUsed,
                        aiResult.ModelUsed,
                        stopwatch.ElapsedMilliseconds,
                        aiResult.RawResponse,
                        healingAttempts: attempts);
                }

                // Nếu biên dịch vẫn lỗi, cập nhật mã nguồn và log lỗi mới cho vòng lặp tiếp theo
                currentBrokenCode = repairedCode;
                currentLog = compileResult.RawLatexLog ?? string.Empty;
            }

            stopwatch.Stop();
            return TikzGenerationResult.Fail(
                $"Đã thử tự sửa lỗi {attempts}/{maxAttempts} lần nhưng mã TikZ vẫn không biên dịch được. Lỗi cuối cùng: {lastErrorDescription}",
                "AutoHealingService",
                string.Empty,
                stopwatch.ElapsedMilliseconds,
                currentLog,
                healingAttempts: attempts);
        }

        private void OnProgressChanged(AutoHealingProgressEventArgs args)
        {
            try
            {
                ProgressChanged?.Invoke(this, args);
            }
            catch
            {
                // Không để ngoại lệ từ listener làm gián đoạn pipeline
            }
        }
    }
}
