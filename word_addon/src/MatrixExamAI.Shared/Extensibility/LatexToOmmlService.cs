using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Text;
using System.Text.RegularExpressions;
using System.Threading;
using System.Threading.Tasks;
using System.Xml;

namespace MatrixExamAI.Shared.Extensibility
{
    /// <summary>
    /// Triển khai dịch vụ Chuyển đổi công thức LaTeX sang Word Native OMML (Phase 4).
    /// Hỗ trợ phân tích cú pháp AST thuần C#, sinh cây XML chuẩn Office Open XML Math (OMML).
    /// </summary>
    public class LatexToOmmlService : ILatexToOmmlService
    {
        private const string OmmlNamespace = "http://schemas.openxmlformats.org/officeDocument/2006/math";

        // Bảng tra cứu ký hiệu toán học & chữ cái Hy Lạp
        private static readonly Dictionary<string, string> SymbolMap = new Dictionary<string, string>
        {
            // Chữ cái Hy Lạp thường
            { @"\alpha", "α" }, { @"\beta", "β" }, { @"\gamma", "γ" }, { @"\delta", "δ" },
            { @"\epsilon", "ε" }, { @"\varepsilon", "ε" }, { @"\zeta", "ζ" }, { @"\eta", "η" },
            { @"\theta", "θ" }, { @"\vartheta", "ϑ" }, { @"\iota", "ι" }, { @"\kappa", "κ" },
            { @"\lambda", "λ" }, { @"\mu", "μ" }, { @"\nu", "ν" }, { @"\xi", "ξ" },
            { @"\pi", "π" }, { @"\varpi", "ϖ" }, { @"\rho", "ρ" }, { @"\varrho", "ϱ" },
            { @"\sigma", "σ" }, { @"\varsigma", "ς" }, { @"\tau", "τ" }, { @"\upsilon", "υ" },
            { @"\phi", "φ" }, { @"\varphi", "ϕ" }, { @"\chi", "χ" }, { @"\psi", "ψ" },
            { @"\omega", "ω" },

            // Chữ cái Hy Lạp hoa
            { @"\Gamma", "Γ" }, { @"\Delta", "Δ" }, { @"\Theta", "Θ" }, { @"\Lambda", "Λ" },
            { @"\Xi", "Ξ" }, { @"\Pi", "Π" }, { @"\Sigma", "Σ" }, { @"\Upsilon", "Υ" },
            { @"\Phi", "Φ" }, { @"\Psi", "Ψ" }, { @"\Omega", "Ω" },

            // Toán tử & Quan hệ
            { @"\pm", "±" }, { @"\mp", "∓" }, { @"\times", "×" }, { @"\div", "÷" },
            { @"\cdot", "·" }, { @"\neq", "≠" }, { @"\ne", "≠" }, { @"\leq", "≤" },
            { @"\le", "≤" }, { @"\geq", "≥" }, { @"\ge", "≥" }, { @"\approx", "≈" },
            { @"\equiv", "≡" }, { @"\sim", "∼" }, { @"\propto", "∝" }, { @"\infty", "∞" },
            { @"\in", "∈" }, { @"\notin", "∉" }, { @"\subset", "⊂" }, { @"\subseteq", "⊆" },
            { @"\supset", "⊃" }, { @"\supseteq", "⊇" }, { @"\cup", "∪" }, { @"\cap", "∩" },
            { @"\forall", "∀" }, { @"\exists", "∃" }, { @"\emptyset", "∅" }, { @"\varnothing", "∅" },
            { @"\nabla", "∇" }, { @"\partial", "∂" },

            // Mũi tên
            { @"\to", "→" }, { @"\rightarrow", "→" }, { @"\leftarrow", "←" },
            { @"\Rightarrow", "⇒" }, { @"\Leftarrow", "⇐" }, { @"\Leftrightarrow", "⇔" },
            { @"\iff", "⇔" }, { @"\implies", "⇒" },

            // Tập số
            { @"\mathbb{R}", "ℝ" }, { @"\mathbb{N}", "ℕ" }, { @"\mathbb{Z}", "ℤ" },
            { @"\mathbb{Q}", "ℚ" }, { @"\mathbb{C}", "ℂ" },
            { @"\mathbf{R}", "ℝ" }, { @"\mathbf{N}", "ℕ" }, { @"\mathbf{Z}", "ℤ" }
        };

        public Task<OmmlConvertResult> ConvertLatexToOmmlAsync(
            string latexFormula,
            bool isDisplayMode = false,
            CancellationToken cancellationToken = default)
        {
            if (string.IsNullOrWhiteSpace(latexFormula))
            {
                return Task.FromResult(OmmlConvertResult.Fail(latexFormula ?? string.Empty, "Công thức LaTeX rỗng."));
            }

            var sw = Stopwatch.StartNew();
            try
            {
                string cleaned = CleanLatexDelimiters(latexFormula);
                string innerXml = ParseLatexToOmmlXml(cleaned);

                var sb = new StringBuilder();
                if (isDisplayMode)
                {
                    sb.Append($@"<m:oMathPara xmlns:m=""{OmmlNamespace}"">");
                    sb.Append($@"<m:oMath xmlns:m=""{OmmlNamespace}"">");
                    sb.Append(innerXml);
                    sb.Append("</m:oMath>");
                    sb.Append("</m:oMathPara>");
                }
                else
                {
                    sb.Append($@"<m:oMath xmlns:m=""{OmmlNamespace}"">");
                    sb.Append(innerXml);
                    sb.Append("</m:oMath>");
                }

                string finalXml = sb.ToString();

                // Xác thực tính hợp lệ XML
                ValidateXml(finalXml);

                sw.Stop();
                return Task.FromResult(OmmlConvertResult.Ok(latexFormula, finalXml, sw.ElapsedMilliseconds));
            }
            catch (Exception ex)
            {
                sw.Stop();
                return Task.FromResult(OmmlConvertResult.Fail(latexFormula, $"Lỗi biên dịch LaTeX sang OMML: {ex.Message}", sw.ElapsedMilliseconds));
            }
        }

        public async Task<string> ConvertDocumentLatexFormulasAsync(
            string fullDocumentText,
            CancellationToken cancellationToken = default)
        {
            if (string.IsNullOrWhiteSpace(fullDocumentText)) return fullDocumentText;

            // 1. Thay thế display math $$...$$
            string result = Regex.Replace(fullDocumentText, @"\$\$([\s\S]+?)\$\$", match =>
            {
                string formula = match.Groups[1].Value;
                var res = ConvertLatexToOmmlAsync(formula, isDisplayMode: true, cancellationToken).GetAwaiter().GetResult();
                return res.Success ? res.OmmlXml : match.Value;
            });

            // 2. Thay thế inline math $...$
            result = Regex.Replace(result, @"\$([^\$\r\n]+?)\$", match =>
            {
                string formula = match.Groups[1].Value;
                var res = ConvertLatexToOmmlAsync(formula, isDisplayMode: false, cancellationToken).GetAwaiter().GetResult();
                return res.Success ? res.OmmlXml : match.Value;
            });

            return result;
        }

        public bool IsValidLatexMath(string input)
        {
            if (string.IsNullOrWhiteSpace(input)) return false;

            int balance = 0;
            foreach (char c in input)
            {
                if (c == '{') balance++;
                else if (c == '}') balance--;
                if (balance < 0) return false;
            }
            return balance == 0;
        }

        #region Core Parser & AST to XML

        private static string CleanLatexDelimiters(string raw)
        {
            string s = raw.Trim();
            if (s.StartsWith("$$") && s.EndsWith("$$") && s.Length >= 4)
            {
                s = s.Substring(2, s.Length - 4).Trim();
            }
            else if (s.StartsWith("$") && s.EndsWith("$") && s.Length >= 2)
            {
                s = s.Substring(1, s.Length - 2).Trim();
            }
            else if (s.StartsWith(@"\(") && s.EndsWith(@"\)") && s.Length >= 4)
            {
                s = s.Substring(2, s.Length - 4).Trim();
            }
            else if (s.StartsWith(@"\[") && s.EndsWith(@"\]") && s.Length >= 4)
            {
                s = s.Substring(2, s.Length - 4).Trim();
            }
            return s;
        }

        private static string ParseLatexToOmmlXml(string latex)
        {
            var sb = new StringBuilder();
            int i = 0;
            int len = latex.Length;

            while (i < len)
            {
                char c = latex[i];

                if (char.IsWhiteSpace(c))
                {
                    i++;
                    continue;
                }

                // 1. Phân số: \frac{num}{den} hoặc \dfrac{num}{den}
                if (latex.Substring(i).StartsWith(@"\frac") || latex.Substring(i).StartsWith(@"\dfrac"))
                {
                    int cmdLen = latex.Substring(i).StartsWith(@"\dfrac") ? 6 : 5;
                    i += cmdLen;
                    string num = ExtractBracedArgument(latex, ref i);
                    string den = ExtractBracedArgument(latex, ref i);

                    sb.Append("<m:f>");
                    sb.Append("<m:num>");
                    sb.Append(ParseLatexToOmmlXml(num));
                    sb.Append("</m:num>");
                    sb.Append("<m:den>");
                    sb.Append(ParseLatexToOmmlXml(den));
                    sb.Append("</m:den>");
                    sb.Append("</m:f>");
                    continue;
                }

                // 2. Căn bậc hai & căn bậc n: \sqrt{x} hoặc \sqrt[n]{x}
                if (latex.Substring(i).StartsWith(@"\sqrt"))
                {
                    i += 5;
                    string deg = string.Empty;
                    if (i < len && latex[i] == '[')
                    {
                        deg = ExtractBracketArgument(latex, ref i);
                    }
                    string rad = ExtractBracedArgument(latex, ref i);

                    sb.Append("<m:rad>");
                    if (string.IsNullOrEmpty(deg))
                    {
                        sb.Append("<m:radPr><m:degHide m:val=\"1\"/></m:radPr>");
                        sb.Append("<m:deg/>");
                    }
                    else
                    {
                        sb.Append("<m:radPr><m:degHide m:val=\"0\"/></m:radPr>");
                        sb.Append("<m:deg>");
                        sb.Append(ParseLatexToOmmlXml(deg));
                        sb.Append("</m:deg>");
                    }
                    sb.Append("<m:e>");
                    sb.Append(ParseLatexToOmmlXml(rad));
                    sb.Append("</m:e>");
                    sb.Append("</m:rad>");
                    continue;
                }

                // 3. Tích phân & Tổng: \int, \sum, \prod, \lim
                if (latex.Substring(i).StartsWith(@"\int") ||
                    latex.Substring(i).StartsWith(@"\sum") ||
                    latex.Substring(i).StartsWith(@"\prod") ||
                    latex.Substring(i).StartsWith(@"\lim"))
                {
                    string opSymbol = "∫";
                    int cmdLen = 4;
                    if (latex.Substring(i).StartsWith(@"\sum")) { opSymbol = "∑"; }
                    else if (latex.Substring(i).StartsWith(@"\prod")) { opSymbol = "∏"; }
                    else if (latex.Substring(i).StartsWith(@"\lim")) { opSymbol = "lim"; }

                    i += cmdLen;

                    string sub = string.Empty;
                    string sup = string.Empty;

                    // Quét chỉ số dưới và trên
                    while (i < len && (latex[i] == '_' || latex[i] == '^' || char.IsWhiteSpace(latex[i])))
                    {
                        if (char.IsWhiteSpace(latex[i])) { i++; continue; }
                        if (latex[i] == '_')
                        {
                            i++;
                            sub = ExtractBracedArgument(latex, ref i);
                        }
                        else if (latex[i] == '^')
                        {
                            i++;
                            sup = ExtractBracedArgument(latex, ref i);
                        }
                    }

                    sb.Append("<m:nary>");
                    sb.Append($"<m:naryPr><m:chr m:val=\"{EscapeXml(opSymbol)}\"/><m:limLoc m:val=\"undOvr\"/></m:naryPr>");
                    sb.Append("<m:sub>");
                    if (!string.IsNullOrEmpty(sub)) sb.Append(ParseLatexToOmmlXml(sub));
                    sb.Append("</m:sub>");
                    sb.Append("<m:sup>");
                    if (!string.IsNullOrEmpty(sup)) sb.Append(ParseLatexToOmmlXml(sup));
                    sb.Append("</m:sup>");
                    sb.Append("<m:e/>");
                    sb.Append("</m:nary>");
                    continue;
                }

                // 4. Ngoặc mở rộng: \left( ... \right), \left[ ... \right], \left\{ ... \right\}
                if (latex.Substring(i).StartsWith(@"\left"))
                {
                    i += 5;
                    char openBracket = '(';
                    char closeBracket = ')';

                    if (i < len)
                    {
                        if (latex.Substring(i).StartsWith(@"\{")) { openBracket = '{'; i += 2; }
                        else { openBracket = latex[i]; i++; }
                    }

                    int rightIdx = latex.IndexOf(@"\right", i, StringComparison.Ordinal);
                    string inner = string.Empty;
                    if (rightIdx >= 0)
                    {
                        inner = latex.Substring(i, rightIdx - i);
                        i = rightIdx + 6;
                        if (i < len)
                        {
                            if (latex.Substring(i).StartsWith(@"\}")) { closeBracket = '}'; i += 2; }
                            else { closeBracket = latex[i]; i++; }
                        }
                    }
                    else
                    {
                        inner = latex.Substring(i);
                        i = len;
                    }

                    sb.Append("<m:d>");
                    sb.Append($"<m:dPr><m:begChr m:val=\"{EscapeXml(openBracket.ToString())}\"/><m:endChr m:val=\"{EscapeXml(closeBracket.ToString())}\"/></m:dPr>");
                    sb.Append("<m:e>");
                    sb.Append(ParseLatexToOmmlXml(inner));
                    sb.Append("</m:e>");
                    sb.Append("</m:d>");
                    continue;
                }

                // 5. Lệnh LaTeX đặc biệt hoặc ký hiệu
                if (c == '\\')
                {
                    string matchCmd = MatchCommand(latex, i);
                    if (!string.IsNullOrEmpty(matchCmd))
                    {
                        i += matchCmd.Length;

                        // Tra cứu bảng ký hiệu
                        if (SymbolMap.TryGetValue(matchCmd, out string symVal))
                        {
                            // Kiểm tra xem có mũ ^ hoặc chỉ số dưới _ liền kề không
                            sb.Append(HandleSubSuperscript(latex, ref i, symVal));
                        }
                        else if (matchCmd == @"\cdot")
                        {
                            sb.Append(CreateRun("·"));
                        }
                        else
                        {
                            string cmdName = matchCmd.TrimStart('\\');
                            sb.Append(HandleSubSuperscript(latex, ref i, cmdName));
                        }
                        continue;
                    }
                }

                // 6. Nhóm ngoặc nhọn { ... }
                if (c == '{')
                {
                    string groupContent = ExtractBracedArgument(latex, ref i);
                    sb.Append(ParseLatexToOmmlXml(groupContent));
                    continue;
                }

                // 7. Ký tự đơn lẻ có lũy thừa hoặc chỉ số dưới
                string singleChar = c.ToString();
                i++;
                sb.Append(HandleSubSuperscript(latex, ref i, singleChar));
            }

            return sb.ToString();
        }

        private static string HandleSubSuperscript(string latex, ref int i, string baseText)
        {
            string? sub = null;
            string? sup = null;
            int len = latex.Length;

            while (i < len && (latex[i] == '_' || latex[i] == '^' || char.IsWhiteSpace(latex[i])))
            {
                if (char.IsWhiteSpace(latex[i])) { i++; continue; }
                if (latex[i] == '_')
                {
                    i++;
                    sub = ExtractBracedArgument(latex, ref i);
                }
                else if (latex[i] == '^')
                {
                    i++;
                    sup = ExtractBracedArgument(latex, ref i);
                }
            }

            // Trường hợp cả Sub và Sup (m:sSubSup)
            if (!string.IsNullOrEmpty(sub) && !string.IsNullOrEmpty(sup))
            {
                var sb = new StringBuilder();
                sb.Append("<m:sSubSup>");
                sb.Append("<m:e>");
                sb.Append(CreateRun(baseText));
                sb.Append("</m:e>");
                sb.Append("<m:sub>");
                sb.Append(ParseLatexToOmmlXml(sub!));
                sb.Append("</m:sub>");
                sb.Append("<m:sup>");
                sb.Append(ParseLatexToOmmlXml(sup!));
                sb.Append("</m:sup>");
                sb.Append("</m:sSubSup>");
                return sb.ToString();
            }

            // Trường hợp chỉ có Sup (m:sSup)
            if (!string.IsNullOrEmpty(sup))
            {
                var sb = new StringBuilder();
                sb.Append("<m:sSup>");
                sb.Append("<m:e>");
                sb.Append(CreateRun(baseText));
                sb.Append("</m:e>");
                sb.Append("<m:sup>");
                sb.Append(ParseLatexToOmmlXml(sup!));
                sb.Append("</m:sup>");
                sb.Append("</m:sSup>");
                return sb.ToString();
            }

            // Trường hợp chỉ có Sub (m:sSub)
            if (!string.IsNullOrEmpty(sub))
            {
                var sb = new StringBuilder();
                sb.Append("<m:sSub>");
                sb.Append("<m:e>");
                sb.Append(CreateRun(baseText));
                sb.Append("</m:e>");
                sb.Append("<m:sub>");
                sb.Append(ParseLatexToOmmlXml(sub!));
                sb.Append("</m:sub>");
                sb.Append("</m:sSub>");
                return sb.ToString();
            }

            // Ký tự thông thường (m:r)
            return CreateRun(baseText);
        }

        private static string CreateRun(string text)
        {
            return $"<m:r><m:t>{EscapeXml(text)}</m:t></m:r>";
        }

        private static string MatchCommand(string latex, int startIdx)
        {
            int j = startIdx + 1;
            int len = latex.Length;
            if (j >= len) return @"\";

            // Nếu sau dấu \ là ký tự đặc biệt như \{, \}, \$, \%, \&
            if (!char.IsLetter(latex[j]))
            {
                return latex.Substring(startIdx, 2);
            }

            while (j < len && char.IsLetter(latex[j]))
            {
                j++;
            }
            return latex.Substring(startIdx, j - startIdx);
        }

        private static string ExtractBracedArgument(string latex, ref int i)
        {
            int len = latex.Length;
            while (i < len && char.IsWhiteSpace(latex[i])) i++;
            if (i >= len) return string.Empty;

            if (latex[i] == '{')
            {
                int start = i + 1;
                int depth = 1;
                i++;
                while (i < len && depth > 0)
                {
                    if (latex[i] == '{') depth++;
                    else if (latex[i] == '}') depth--;
                    i++;
                }
                return latex.Substring(start, i - 1 - start);
            }

            // Nếu không có ngoặc nhọn, lấy đúng 1 ký tự hoặc 1 lệnh
            if (latex[i] == '\\')
            {
                string cmd = MatchCommand(latex, i);
                i += cmd.Length;
                return cmd;
            }

            char single = latex[i];
            i++;
            return single.ToString();
        }

        private static string ExtractBracketArgument(string latex, ref int i)
        {
            int len = latex.Length;
            while (i < len && char.IsWhiteSpace(latex[i])) i++;
            if (i >= len || latex[i] != '[') return string.Empty;

            int start = i + 1;
            int depth = 1;
            i++;
            while (i < len && depth > 0)
            {
                if (latex[i] == '[') depth++;
                else if (latex[i] == ']') depth--;
                i++;
            }
            return latex.Substring(start, i - 1 - start);
        }

        private static string EscapeXml(string unescaped)
        {
            if (string.IsNullOrEmpty(unescaped)) return string.Empty;
            return unescaped
                .Replace("&", "&amp;")
                .Replace("<", "&lt;")
                .Replace(">", "&gt;")
                .Replace("\"", "&quot;")
                .Replace("'", "&apos;");
        }

        private static void ValidateXml(string xml)
        {
            var doc = new XmlDocument();
            doc.LoadXml(xml);
        }

        #endregion
    }
}
