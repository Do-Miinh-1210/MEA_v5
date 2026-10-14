using System;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using MatrixExamAI.Shared.Models;
using MatrixExamAI.Shared.Validation;

namespace MatrixExamAI.Shared.Tikz
{
    /// <summary>
    /// Dịch vụ biên dịch mã TikZ hoàn chỉnh, thực thi TeXLive (pdflatex),
    /// xuất ảnh phân giải cao 600 DPI (pdftoppm / pdftocairo) và vector (inkscape.com).
    /// </summary>
    public class TikzCompilerService : ITikzCompiler
    {
        public TexToolchain Toolchain { get; }

        public TikzCompilerService(TexToolchain? toolchain = null)
        {
            Toolchain = toolchain ?? TexToolchainDiscovery.Discover();
        }

        public async Task<TikzCompileResult> CompileAsync(TikzCompileRequest request, CancellationToken ct = default)
        {
            var stopwatch = Stopwatch.StartNew();

            if (string.IsNullOrWhiteSpace(request.TikzCode))
            {
                stopwatch.Stop();
                return TikzCompileResult.Fail(
                    "Mã TikZ rỗng, không thể biên dịch.",
                    null,
                    null,
                    stopwatch.ElapsedMilliseconds);
            }

            if (!Toolchain.IsPdfLatexAvailable)
            {
                stopwatch.Stop();
                return TikzCompileResult.Fail(
                    "Không tìm thấy trình biên dịch pdflatex.exe trên hệ thống (hãy kiểm tra cài đặt TeX Live hoặc MiKTeX).",
                    null,
                    null,
                    stopwatch.ElapsedMilliseconds);
            }

            // Tạo thư mục tạm độc lập để tránh xung đột ghi tệp tin
            string tempDir = Path.Combine(Path.GetTempPath(), $"MEA_TikZ_{Guid.NewGuid():N}");
            Directory.CreateDirectory(tempDir);

            string texFile = Path.Combine(tempDir, "figure.tex");
            string pdfFile = Path.Combine(tempDir, "figure.pdf");
            string logFile = Path.Combine(tempDir, "figure.log");

            try
            {
                // 1. Tạo tài liệu standalone LaTeX
                string latexDocument = StandaloneLatexBuilder.BuildStandaloneDocument(request.TikzCode, request.Border);
                File.WriteAllText(texFile, latexDocument, new UTF8Encoding(false));

                // 2. Chạy pdflatex
                int timeoutMs = Math.Max(5, request.TimeoutSeconds) * 1000;
                var (exitCode, stdout, stderr) = await RunProcessAsync(
                    Toolchain.PdfLatexPath!,
                    "-interaction=nonstopmode -halt-on-error figure.tex",
                    tempDir,
                    timeoutMs,
                    ct).ConfigureAwait(false);

                string rawLog = File.Exists(logFile) ? File.ReadAllText(logFile) : (stdout + "\n" + stderr);

                if (exitCode != 0 || !File.Exists(pdfFile) || new FileInfo(pdfFile).Length == 0)
                {
                    stopwatch.Stop();
                    var parsedError = LatexErrorLogParser.ParseLog(rawLog);
                    string summary = parsedError != null
                        ? parsedError.ToString()
                        : "Lỗi biên dịch LaTeX không xác định.";

                    return TikzCompileResult.Fail(
                        $"Biên dịch pdflatex thất bại (Mã thoát: {exitCode}): {summary}",
                        parsedError,
                        rawLog,
                        stopwatch.ElapsedMilliseconds);
                }

                // 3. Chuyển đổi sang định dạng đích (PNG 600 DPI, SVG, hoặc EMF)
                string baseName = !string.IsNullOrWhiteSpace(request.OutputBaseName)
                    ? request.OutputBaseName!
                    : $"tikz_{DateTime.Now:yyyyMMdd_HHmmss}_{Guid.NewGuid().ToString("N").Substring(0, 6)}";

                string finalImagePath;
                TikzExportFormat actualFormat = request.Format;

                switch (request.Format)
                {
                    case TikzExportFormat.Svg:
                        finalImagePath = await ConvertToSvgAsync(pdfFile, tempDir, baseName, timeoutMs, ct).ConfigureAwait(false);
                        break;

                    case TikzExportFormat.Emf:
                        finalImagePath = await ConvertToEmfAsync(pdfFile, tempDir, baseName, timeoutMs, ct).ConfigureAwait(false);
                        if (!File.Exists(finalImagePath))
                        {
                            // Fallback sang PNG 600 DPI nếu không có công cụ EMF
                            finalImagePath = await ConvertToPngAsync(pdfFile, tempDir, baseName, request.Dpi, timeoutMs, ct).ConfigureAwait(false);
                            actualFormat = TikzExportFormat.Png;
                        }
                        break;

                    case TikzExportFormat.Png:
                    default:
                        finalImagePath = await ConvertToPngAsync(pdfFile, tempDir, baseName, request.Dpi, timeoutMs, ct).ConfigureAwait(false);
                        actualFormat = TikzExportFormat.Png;
                        break;
                }

                if (!File.Exists(finalImagePath) || new FileInfo(finalImagePath).Length == 0)
                {
                    stopwatch.Stop();
                    return TikzCompileResult.Fail(
                        $"Không tạo được tệp ảnh đầu ra ({actualFormat}).",
                        null,
                        rawLog,
                        stopwatch.ElapsedMilliseconds);
                }

                // 4. Nếu người dùng chỉ định OutputDirectory, sao chép tệp tin ảnh sang đó
                if (!string.IsNullOrWhiteSpace(request.OutputDirectory))
                {
                    Directory.CreateDirectory(request.OutputDirectory!);
                    string targetFile = Path.Combine(request.OutputDirectory!, Path.GetFileName(finalImagePath));
                    File.Copy(finalImagePath, targetFile, true);
                    finalImagePath = targetFile;
                }

                // 5. Tạo chuỗi Preview Data URL cho giao diện WebView2
                string previewDataUrl = CreatePreviewDataUrl(finalImagePath, actualFormat);

                stopwatch.Stop();
                return TikzCompileResult.Ok(
                    finalImagePath,
                    previewDataUrl,
                    actualFormat,
                    stopwatch.ElapsedMilliseconds);
            }
            finally
            {
                // Dọn dẹp tệp tin rác trung gian (.aux, .log, .tex) nhưng giữ lại ảnh kết quả
                CleanupIntermediateFiles(tempDir, texFile, logFile);
            }
        }

        private async Task<string> ConvertToPngAsync(
            string pdfPath,
            string workDir,
            string baseName,
            int dpi,
            int timeoutMs,
            CancellationToken ct)
        {
            string outPrefix = Path.Combine(workDir, baseName);

            // Ưu tiên pdftoppm (TeX Live)
            if (!string.IsNullOrEmpty(Toolchain.PdfToPpmPath) && File.Exists(Toolchain.PdfToPpmPath))
            {
                // pdftoppm -r 600 -png figure.pdf outPrefix
                await RunProcessAsync(
                    Toolchain.PdfToPpmPath!,
                    $"-r {dpi} -png \"{pdfPath}\" \"{outPrefix}\"",
                    workDir,
                    timeoutMs,
                    ct).ConfigureAwait(false);

                string candidate1 = $"{outPrefix}-1.png";
                if (File.Exists(candidate1)) return candidate1;

                string candidate2 = $"{outPrefix}.png";
                if (File.Exists(candidate2)) return candidate2;
            }

            // Dự phòng pdftocairo
            if (!string.IsNullOrEmpty(Toolchain.PdfToCairoPath) && File.Exists(Toolchain.PdfToCairoPath))
            {
                // pdftocairo -png -r 600 figure.pdf outPrefix
                await RunProcessAsync(
                    Toolchain.PdfToCairoPath!,
                    $"-png -r {dpi} \"{pdfPath}\" \"{outPrefix}\"",
                    workDir,
                    timeoutMs,
                    ct).ConfigureAwait(false);

                string candidate1 = $"{outPrefix}-1.png";
                if (File.Exists(candidate1)) return candidate1;

                string candidate2 = $"{outPrefix}.png";
                if (File.Exists(candidate2)) return candidate2;
            }

            // Tìm bất kỳ file png nào sinh ra trong thư mục
            var anyPng = Directory.GetFiles(workDir, "*.png").FirstOrDefault();
            return anyPng ?? string.Empty;
        }

        private async Task<string> ConvertToSvgAsync(
            string pdfPath,
            string workDir,
            string baseName,
            int timeoutMs,
            CancellationToken ct)
        {
            string svgPath = Path.Combine(workDir, $"{baseName}.svg");

            // 1. Thử inkscape.com
            if (!string.IsNullOrEmpty(Toolchain.InkscapePath) && File.Exists(Toolchain.InkscapePath))
            {
                await RunProcessAsync(
                    Toolchain.InkscapePath!,
                    $"\"{pdfPath}\" --export-type=svg --export-filename=\"{svgPath}\" --export-text-to-path",
                    workDir,
                    timeoutMs,
                    ct).ConfigureAwait(false);

                if (File.Exists(svgPath) && new FileInfo(svgPath).Length > 0)
                {
                    return svgPath;
                }
            }

            // 2. Dự phòng pdftocairo -svg
            if (!string.IsNullOrEmpty(Toolchain.PdfToCairoPath) && File.Exists(Toolchain.PdfToCairoPath))
            {
                await RunProcessAsync(
                    Toolchain.PdfToCairoPath!,
                    $"-svg \"{pdfPath}\" \"{svgPath}\"",
                    workDir,
                    timeoutMs,
                    ct).ConfigureAwait(false);

                if (File.Exists(svgPath) && new FileInfo(svgPath).Length > 0)
                {
                    return svgPath;
                }
            }

            return svgPath;
        }

        private async Task<string> ConvertToEmfAsync(
            string pdfPath,
            string workDir,
            string baseName,
            int timeoutMs,
            CancellationToken ct)
        {
            string emfPath = Path.Combine(workDir, $"{baseName}.emf");

            // EMF bắt buộc dùng inkscape.com
            if (!string.IsNullOrEmpty(Toolchain.InkscapePath) && File.Exists(Toolchain.InkscapePath))
            {
                await RunProcessAsync(
                    Toolchain.InkscapePath!,
                    $"\"{pdfPath}\" --export-type=emf --export-filename=\"{emfPath}\" --export-text-to-path",
                    workDir,
                    timeoutMs,
                    ct).ConfigureAwait(false);

                if (File.Exists(emfPath) && new FileInfo(emfPath).Length > 0)
                {
                    return emfPath;
                }
            }

            return emfPath;
        }

        private string CreatePreviewDataUrl(string filePath, TikzExportFormat format)
        {
            try
            {
                byte[] bytes = File.ReadAllBytes(filePath);
                string base64 = Convert.ToBase64String(bytes);

                switch (format)
                {
                    case TikzExportFormat.Svg:
                        return $"data:image/svg+xml;base64,{base64}";
                    case TikzExportFormat.Emf:
                        return $"data:image/x-emf;base64,{base64}";
                    case TikzExportFormat.Png:
                    default:
                        return $"data:image/png;base64,{base64}";
                }
            }
            catch
            {
                return string.Empty;
            }
        }

        private void CleanupIntermediateFiles(string tempDir, string texFile, string logFile)
        {
            try
            {
                string baseNoExt = Path.Combine(tempDir, "figure");
                string[] extsToClean = { ".aux", ".tex", ".pdf" };

                foreach (var ext in extsToClean)
                {
                    string f = baseNoExt + ext;
                    if (File.Exists(f))
                    {
                        File.Delete(f);
                    }
                }
            }
            catch
            {
                // Bỏ qua lỗi xóa tệp tin tạm
            }
        }

        private async Task<(int ExitCode, string StdOut, string StdErr)> RunProcessAsync(
            string fileName,
            string arguments,
            string workingDirectory,
            int timeoutMs,
            CancellationToken ct)
        {
            var startInfo = new ProcessStartInfo
            {
                FileName = fileName,
                Arguments = arguments,
                WorkingDirectory = workingDirectory,
                CreateNoWindow = true,
                UseShellExecute = false,
                RedirectStandardOutput = true,
                RedirectStandardError = true
            };

            using (var process = new Process { StartInfo = startInfo })
            {
                var stdout = new StringBuilder();
                var stderr = new StringBuilder();

                process.OutputDataReceived += (s, e) => { if (e.Data != null) stdout.AppendLine(e.Data); };
                process.ErrorDataReceived += (s, e) => { if (e.Data != null) stderr.AppendLine(e.Data); };

                process.Start();
                process.BeginOutputReadLine();
                process.BeginErrorReadLine();

                var processTask = Task.Run(() =>
                {
                    process.WaitForExit();
                    return process.ExitCode;
                });

                using (var timeoutCts = new CancellationTokenSource(timeoutMs))
                using (var linkedCts = CancellationTokenSource.CreateLinkedTokenSource(ct, timeoutCts.Token))
                {
                    try
                    {
                        var tcs = new TaskCompletionSource<bool>();
                        using (linkedCts.Token.Register(() => tcs.TrySetResult(true)))
                        {
                            var completedTask = await Task.WhenAny(processTask, tcs.Task).ConfigureAwait(false);
                            if (completedTask == processTask)
                            {
                                int exitCode = await processTask.ConfigureAwait(false);
                                return (exitCode, stdout.ToString(), stderr.ToString());
                            }
                            else
                            {
                                // Timeout hoặc cancel
                                try
                                {
                                    if (!process.HasExited)
                                    {
                                        process.Kill();
                                    }
                                }
                                catch { }

                                return (-1, stdout.ToString(), "Tiến trình biên dịch bị quá thời gian (timeout) hoặc bị hủy.");
                            }
                        }
                    }
                    catch
                    {
                        try { if (!process.HasExited) process.Kill(); } catch { }
                        throw;
                    }
                }
            }
        }
    }
}
