using System;
using System.IO;

namespace MatrixExamAI.Shared.Tikz
{
    /// <summary>
    /// Thông tin về các công cụ biên dịch TeX và chuyển đổi hình ảnh được phát hiện trên máy trạm.
    /// </summary>
    public class TexToolchain
    {
        public string? PdfLatexPath { get; set; }
        public string? PdfToPpmPath { get; set; }
        public string? PdfToCairoPath { get; set; }
        public string? InkscapePath { get; set; }

        public bool IsPdfLatexAvailable => !string.IsNullOrEmpty(PdfLatexPath) && File.Exists(PdfLatexPath);
        public bool IsRasterAvailable => (!string.IsNullOrEmpty(PdfToPpmPath) && File.Exists(PdfToPpmPath)) ||
                                         (!string.IsNullOrEmpty(PdfToCairoPath) && File.Exists(PdfToCairoPath));
        public bool IsVectorAvailable => !string.IsNullOrEmpty(InkscapePath) && File.Exists(InkscapePath);

        public override string ToString()
        {
            return $"pdflatex: {PdfLatexPath ?? "chưa tìm thấy"}, pdftoppm/pdftocairo: {PdfToPpmPath ?? PdfToCairoPath ?? "chưa tìm thấy"}, inkscape.com: {InkscapePath ?? "chưa tìm thấy"}";
        }
    }

    /// <summary>
    /// Tự động phát hiện các công cụ TeXLive / MiKTeX / Poppler / Inkscape trên môi trường Windows.
    /// </summary>
    public static class TexToolchainDiscovery
    {
        private static TexToolchain? _cached;
        private static readonly object _syncLock = new object();

        /// <summary>
        /// Quét và trả về bộ công cụ đã phát hiện trên máy trạm.
        /// </summary>
        public static TexToolchain Discover(bool forceRefresh = false)
        {
            if (_cached != null && !forceRefresh)
            {
                return _cached;
            }

            lock (_syncLock)
            {
                if (_cached != null && !forceRefresh)
                {
                    return _cached;
                }

                var toolchain = new TexToolchain();

                // 1. Tìm pdflatex.exe
                toolchain.PdfLatexPath = FindExecutable("pdflatex.exe", new[]
                {
                    @"C:\texlive\2026\bin\windows\pdflatex.exe",
                    @"C:\texlive\2025\bin\windows\pdflatex.exe",
                    @"C:\Program Files\MiKTeX\miktex\bin\x64\pdflatex.exe",
                    @"C:\Program Files (x86)\MiKTeX\miktex\bin\pdflatex.exe"
                });

                // 2. Tìm pdftoppm.exe
                toolchain.PdfToPpmPath = FindExecutable("pdftoppm.exe", new[]
                {
                    @"C:\texlive\2026\bin\windows\pdftoppm.exe",
                    @"C:\texlive\2025\bin\windows\pdftoppm.exe"
                });

                // 3. Tìm pdftocairo.exe
                toolchain.PdfToCairoPath = FindExecutable("pdftocairo.exe", new[]
                {
                    @"C:\texlive\2026\bin\windows\pdftocairo.exe",
                    @"C:\texlive\2025\bin\windows\pdftocairo.exe"
                });

                // 4. Tìm inkscape.com (LƯU Ý: Phải là .com console wrapper, không phải .exe GUI!)
                toolchain.InkscapePath = FindExecutable("inkscape.com", new[]
                {
                    @"C:\Program Files\Inkscape\bin\inkscape.com",
                    @"C:\Program Files\Inkscape\inkscape.com",
                    @"C:\Program Files (x86)\Inkscape\bin\inkscape.com",
                    @"C:\Program Files (x86)\Inkscape\inkscape.com"
                });

                _cached = toolchain;
                return toolchain;
            }
        }

        private static string? FindExecutable(string exeName, string[] standardPaths)
        {
            // 1. Kiểm tra trong biến môi trường PATH
            string? inPath = FindInPath(exeName);
            if (!string.IsNullOrEmpty(inPath) && File.Exists(inPath))
            {
                return inPath;
            }

            // 2. Kiểm tra các thư mục cài đặt tiêu chuẩn
            foreach (var path in standardPaths)
            {
                if (File.Exists(path))
                {
                    return path;
                }
            }

            return null;
        }

        private static string? FindInPath(string exeName)
        {
            string? pathEnv = Environment.GetEnvironmentVariable("PATH");
            if (string.IsNullOrEmpty(pathEnv))
            {
                return null;
            }

            string[] paths = pathEnv!.Split(new[] { Path.PathSeparator }, StringSplitOptions.RemoveEmptyEntries);
            foreach (var dir in paths)
            {
                try
                {
                    string candidate = Path.Combine(dir.Trim(), exeName);
                    if (File.Exists(candidate))
                    {
                        return candidate;
                    }
                }
                catch
                {
                    // Bỏ qua đường dẫn không hợp lệ trong PATH
                }
            }

            return null;
        }
    }
}
