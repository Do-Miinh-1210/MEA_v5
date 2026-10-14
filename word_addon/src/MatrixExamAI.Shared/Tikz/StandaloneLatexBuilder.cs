using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using MatrixExamAI.Shared.AI;

namespace MatrixExamAI.Shared.Tikz
{
    /// <summary>
    /// Xây dựng tài liệu LaTeX standalone hoàn chỉnh từ mã nguồn TikZ thuần túy,
    /// tự động quét cú pháp để nạp chính xác các gói (packages) và thư viện TikZ cần thiết.
    /// </summary>
    public static class StandaloneLatexBuilder
    {
        /// <summary>
        /// Tạo nội dung tệp tin .tex standalone hoàn chỉnh sẵn sàng để pdflatex biên dịch.
        /// </summary>
        public static string BuildStandaloneDocument(string tikzCode, string border = "10pt")
        {
            string code = TikzCodeExtractor.ExtractTikzCode(tikzCode);
            if (string.IsNullOrWhiteSpace(code))
            {
                code = (tikzCode ?? string.Empty).Trim();
            }

            var packages = new List<string>
            {
                @"\usepackage{iftex}",
                @"\ifPDFTeX",
                @"  \usepackage[utf8]{inputenc}",
                @"  \usepackage[T5]{fontenc}",
                @"\fi",
                @"\usepackage{amsmath,amssymb,amsfonts,mathtools,bm}",
                @"\usepackage{tikz}",
                @"\usepackage{pgfplots}"
            };

            var extraConfigs = new List<string>
            {
                @"\pgfplotsset{compat=1.18}"
            };

            string codeLower = code.ToLowerInvariant();

            // 1. Quét gói Vật lý / Hóa học
            if (code.Contains(@"\qty") || code.Contains(@"\SI") || code.Contains(@"\norm") ||
                code.Contains(@"\abs") || code.Contains(@"\dd") || code.Contains(@"\dv"))
            {
                packages.Add(@"\usepackage{physics,siunitx}");
                extraConfigs.Add(@"\sisetup{per-mode=symbol}");
            }

            if (code.Contains(@"\ce") || code.Contains(@"\ch") || code.Contains(@"\chemfig"))
            {
                packages.Add(@"\usepackage[version=4]{mhchem}");
                packages.Add(@"\usepackage{chemfig}");
            }

            // 2. Mạch điện circuitikz
            if (codeLower.Contains("circuitikz") || code.Contains("to["))
            {
                if (codeLower.Contains("american"))
                {
                    packages.Add(@"\usepackage[american]{circuitikz}");
                }
                else
                {
                    packages.Add(@"\usepackage[european]{circuitikz}");
                }
            }

            // 3. Đồ thị Pgfplots bổ sung
            if (code.Contains("pgfplots") || code.Contains(@"\begin{axis}") || code.Contains(@"\addplot"))
            {
                extraConfigs.Add(@"\usepgfplotslibrary{fillbetween,statistics}");
            }

            // 4. Hình học Euclid phẳng tkz-euclide
            if (code.Contains(@"\tkz") && !code.Contains(@"\tkzTab"))
            {
                packages.Add(@"\usepackage{tkz-euclide}");
            }

            // 5. Hình học không gian 3D tikz-3dplot
            if (codeLower.Contains("tdplot"))
            {
                packages.Add(@"\usepackage{tikz-3dplot}");
            }

            // 6. Bảng biến thiên / bảng xét dấu tkz-tab
            if (code.Contains(@"\tkzTab"))
            {
                packages.Add(@"\usepackage{tkz-tab}");
            }

            // 7. Bảng biểu tabular / multirow
            if (code.Contains("tabular") || code.Contains("table") || code.Contains("multirow") || code.Contains(@"\toprule"))
            {
                packages.Add(@"\usepackage{float,caption,subcaption,booktabs,multirow,array}");
            }

            // ── QUÉT CÁC THƯ VIỆN TIKZ (TIKZ LIBRARIES) ──
            var libraries = new List<string> { "arrows.meta" };

            if (code.Contains("$") || code.Contains("calc"))
            {
                libraries.Add("calc");
            }

            if (code.Contains("intersection"))
            {
                libraries.Add("intersections");
            }

            if (code.Contains("above=") || code.Contains("below=") || code.Contains("left=") ||
                code.Contains("right=") || code.Contains("positioning"))
            {
                libraries.Add("positioning");
            }

            if (code.Contains("ellipse") || code.Contains("polygon") || code.Contains("star") || code.Contains("shapes.geometric"))
            {
                libraries.Add("shapes.geometric");
            }

            if (code.Contains("pattern"))
            {
                libraries.Add("patterns.meta");
            }

            if (code.Contains("decorat"))
            {
                libraries.Add("decorations.markings");
                libraries.Add("decorations.pathmorphing");
            }

            if (code.Contains("pic") || code.Contains("angle") || code.Contains("right angle"))
            {
                libraries.Add("angles");
                libraries.Add("quotes");
                extraConfigs.Add(@"\tikzset{right angle/.style={angle}}");
            }

            if (code.Contains("circle through"))
            {
                libraries.Add("through");
            }

            if (code.Contains("background"))
            {
                libraries.Add("backgrounds");
            }

            if (code.Contains("fit="))
            {
                libraries.Add("fit");
            }

            if (code.Contains("mark="))
            {
                libraries.Add("plotmarks");
            }

            if (code.Contains("chain"))
            {
                libraries.Add("chains");
            }

            if (code.Contains("matrix"))
            {
                libraries.Add("matrix");
            }

            if (code.Contains("perspective"))
            {
                libraries.Add("perspective");
            }

            if (code.Contains("canvas is"))
            {
                libraries.Add("3d");
            }

            // Loại bỏ trùng lặp thư viện nhưng giữ thứ tự
            var uniqueLibs = libraries.Distinct().ToList();

            var sb = new StringBuilder();
            sb.AppendLine($@"\documentclass[border={border},tikz,preview]{{standalone}}");
            sb.AppendLine("% --- PACKAGES TU DONG PHAT HIEN THEO CHUAN TIKZ AI SKILL ---");
            foreach (var pkg in packages)
            {
                sb.AppendLine(pkg);
            }

            sb.AppendLine($@"\usetikzlibrary{{{string.Join(", ", uniqueLibs)}}}");

            if (extraConfigs.Count > 0)
            {
                sb.AppendLine("% --- CAU HINH BO SUNG ---");
                foreach (var cfg in extraConfigs)
                {
                    sb.AppendLine(cfg);
                }
            }

            sb.AppendLine(@"\PreviewEnvironment{tikzpicture}");
            sb.AppendLine(@"\PreviewEnvironment{circuitikz}");
            sb.AppendLine(@"\pagestyle{empty}");
            sb.AppendLine(@"\begin{document}");
            sb.AppendLine(code);
            sb.AppendLine(@"\end{document}");

            return sb.ToString();
        }
    }
}
