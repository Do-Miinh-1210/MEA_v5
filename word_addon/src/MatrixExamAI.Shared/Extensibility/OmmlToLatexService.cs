using System;
using System.Collections.Generic;
using System.IO;
using System.Text;
using System.Text.RegularExpressions;
using System.Xml;
using System.Xml.Linq;

namespace MatrixExamAI.Shared.Extensibility
{
    /// <summary>
    /// Chuyển đổi công thức toán Word OpenXML Math (OMML) sang cú pháp LaTeX chuẩn.
    /// Dùng làm cầu nối để MathType ToggleTeX tự động biên dịch lại sang MathType OLE equations.
    /// </summary>
    public class OmmlToLatexService
    {
        private static readonly XNamespace M = "http://schemas.openxmlformats.org/officeDocument/2006/math";
        private static readonly XNamespace W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main";

        // Tra cứu ngược ký tự Unicode sang lệnh LaTeX
        private static readonly Dictionary<string, string> UnicodeToLatexMap = new Dictionary<string, string>
        {
            // Hy Lạp thường
            { "α", @"\alpha " }, { "β", @"\beta " }, { "γ", @"\gamma " }, { "δ", @"\delta " },
            { "ε", @"\varepsilon " }, { "ζ", @"\zeta " }, { "η", @"\eta " }, { "θ", @"\theta " },
            { "ϑ", @"\vartheta " }, { "ι", @"\iota " }, { "κ", @"\kappa " }, { "λ", @"\lambda " },
            { "μ", @"\mu " }, { "ν", @"\nu " }, { "ξ", @"\xi " }, { "π", @"\pi " },
            { "ϖ", @"\varpi " }, { "ρ", @"\rho " }, { "ϱ", @"\varrho " }, { "σ", @"\sigma " },
            { "ς", @"\varsigma " }, { "τ", @"\tau " }, { "υ", @"\upsilon " }, { "φ", @"\varphi " },
            { "ϕ", @"\phi " }, { "χ", @"\chi " }, { "ψ", @"\psi " }, { "ω", @"\omega " },

            // Hy Lạp hoa
            { "Γ", @"\Gamma " }, { "Δ", @"\Delta " }, { "Θ", @"\Theta " }, { "Λ", @"\Lambda " },
            { "Ξ", @"\Xi " }, { "Π", @"\Pi " }, { "Σ", @"\Sigma " }, { "Υ", @"\Upsilon " },
            { "Φ", @"\Phi " }, { "Ψ", @"\Psi " }, { "Ω", @"\Omega " },

            // Toán tử & Quan hệ
            { "±", @"\pm " }, { "∓", @"\mp " }, { "×", @"\times " }, { "÷", @"\div " },
            { "·", @"\cdot " }, { "≠", @"\ne " }, { "≤", @"\le " }, { "≥", @"\ge " },
            { "≈", @"\approx " }, { "≡", @"\equiv " }, { "∼", @"\sim " }, { "∝", @"\propto " },
            { "∞", @"\infty " }, { "∈", @"\in " }, { "∉", @"\notin " }, { "⊂", @"\subset " },
            { "⊆", @"\subseteq " }, { "⊃", @"\supset " }, { "⊇", @"\supseteq " },
            { "∪", @"\cup " }, { "∩", @"\cap " }, { "∀", @"\forall " }, { "∃", @"\exists " },
            { "∅", @"\emptyset " }, { "∇", @"\nabla " }, { "∂", @"\partial " },

            // Mũi tên
            { "→", @"\to " }, { "←", @"\leftarrow " }, { "⇒", @"\Rightarrow " },
            { "⇐", @"\Leftarrow " }, { "⇔", @"\Leftrightarrow " }, { "↔", @"\leftrightarrow " },

            // Tập hợp số
            { "ℝ", @"\mathbb{R}" }, { "ℕ", @"\mathbb{N}" }, { "ℤ", @"\mathbb{Z}" },
            { "ℚ", @"\mathbb{Q}" }, { "ℂ", @"\mathbb{C}" },

            // Ký hiệu khác
            { "∫", @"\int " }, { "∬", @"\iint " }, { "∭", @"\iiint " }, { "∮", @"\oint " },
            { "∑", @"\sum " }, { "∏", @"\prod " }
        };

        /// <summary>
        /// Chuyển đổi đoạn WordOpenXML chứa công thức sang chuỗi LaTeX.
        /// </summary>
        public string ConvertOmmlXmlToLatex(string rawOpenXml)
        {
            if (string.IsNullOrWhiteSpace(rawOpenXml)) return string.Empty;

            try
            {
                // Trích xuất thẻ <m:oMath> hoặc <m:oMathPara>
                Match match = Regex.Match(rawOpenXml, @"<(m:oMath(?:Para)?)[^>]*>[\s\S]*?<\/\1>", RegexOptions.IgnoreCase);
                string omathXml = match.Success ? match.Value : rawOpenXml;

                // Bọc namespace nếu cần thiết để nạp XElement
                if (!omathXml.Contains("xmlns:m="))
                {
                    omathXml = $"<root xmlns:m=\"{M.NamespaceName}\" xmlns:w=\"{W.NamespaceName}\">{omathXml}</root>";
                }

                XElement root = XElement.Parse(omathXml);
                var oMathElements = root.DescendantsAndSelf(M + "oMath");

                var sb = new StringBuilder();
                foreach (var el in oMathElements)
                {
                    sb.Append(ParseElement(el));
                }

                string latex = CleanLatexOutput(sb.ToString());
                return latex;
            }
            catch (Exception)
            {
                // Fallback nếu không parse được XML: loại bỏ thẻ XML và tra ký tự
                return FallbackRegexExtraction(rawOpenXml);
            }
        }

        private string ParseElement(XElement el)
        {
            if (el == null) return string.Empty;

            string localName = el.Name.LocalName;

            switch (localName)
            {
                case "oMath":
                case "oMathPara":
                case "e": // element container
                    return ParseChildren(el);

                case "r": // Math run
                    return ParseRun(el);

                case "f": // Fraction: \frac{num}{den}
                    return ParseFraction(el);

                case "sSup": // Superscript: {base}^{sup}
                    return ParseSuperscript(el);

                case "sSub": // Subscript: {base}_{sub}
                    return ParseSubscript(el);

                case "sSubSup": // Sub-Sup: {base}_{sub}^{sup}
                    return ParseSubSup(el);

                case "rad": // Radical: \sqrt[deg]{e} hoặc \sqrt{e}
                    return ParseRadical(el);

                case "d": // Delimiter: \left( ... \right)
                    return ParseDelimiter(el);

                case "nary": // N-ary: \int, \sum, \prod
                    return ParseNary(el);

                case "func": // Function: \sin, \cos, \lim
                    return ParseFunction(el);

                case "bar": // Bar: \overline{e}
                    return ParseBar(el);

                case "m": // Matrix: \begin{matrix} ... \end{matrix}
                    return ParseMatrix(el);

                case "eqArr": // Equation array: \begin{aligned} ... \end{aligned}
                    return ParseEquationArray(el);

                case "acc": // Accent: \vec{x}, \hat{x}
                    return ParseAccent(el);

                default:
                    return ParseChildren(el);
            }
        }

        private string ParseChildren(XElement parent)
        {
            var sb = new StringBuilder();
            foreach (var node in parent.Nodes())
            {
                if (node is XElement child)
                {
                    // Bỏ qua các thẻ thuộc tính properties (m:fPr, m:dPr, m:radPr, v.v.)
                    if (!child.Name.LocalName.EndsWith("Pr"))
                    {
                        sb.Append(ParseElement(child));
                    }
                }
            }
            return sb.ToString();
        }

        private string ParseRun(XElement rEl)
        {
            var tEls = rEl.Elements(M + "t");
            var sb = new StringBuilder();

            foreach (var t in tEls)
            {
                string text = t.Value;
                foreach (var kv in UnicodeToLatexMap)
                {
                    if (text.Contains(kv.Key))
                    {
                        text = text.Replace(kv.Key, kv.Value);
                    }
                }
                sb.Append(text);
            }
            return sb.ToString();
        }

        private string ParseFraction(XElement fEl)
        {
            var numEl = fEl.Element(M + "num");
            var denEl = fEl.Element(M + "den");

            string num = numEl != null ? ParseElement(numEl) : "";
            string den = denEl != null ? ParseElement(denEl) : "";

            return $@"\frac{{{num}}}{{{den}}}";
        }

        private string ParseSuperscript(XElement el)
        {
            var baseEl = el.Element(M + "e");
            var supEl = el.Element(M + "sup");

            string b = baseEl != null ? ParseElement(baseEl) : "";
            string s = supEl != null ? ParseElement(supEl) : "";

            return $"{WrapIfNeeded(b)}^{{{s}}}";
        }

        private string ParseSubscript(XElement el)
        {
            var baseEl = el.Element(M + "e");
            var subEl = el.Element(M + "sub");

            string b = baseEl != null ? ParseElement(baseEl) : "";
            string s = subEl != null ? ParseElement(subEl) : "";

            return $"{WrapIfNeeded(b)}_{{{s}}}";
        }

        private string ParseSubSup(XElement el)
        {
            var baseEl = el.Element(M + "e");
            var subEl = el.Element(M + "sub");
            var supEl = el.Element(M + "sup");

            string b = baseEl != null ? ParseElement(baseEl) : "";
            string sub = subEl != null ? ParseElement(subEl) : "";
            string sup = supEl != null ? ParseElement(supEl) : "";

            return $"{WrapIfNeeded(b)}_{{{sub}}}^{{{sup}}}";
        }

        private string ParseRadical(XElement radEl)
        {
            var degEl = radEl.Element(M + "deg");
            var eEl = radEl.Element(M + "e");

            bool isDegHidden = true;
            var radPr = radEl.Element(M + "radPr");
            if (radPr != null)
            {
                var degHide = radPr.Element(M + "degHide");
                if (degHide != null && degHide.Attribute(M + "val")?.Value == "0")
                {
                    isDegHidden = false;
                }
            }

            string e = eEl != null ? ParseElement(eEl) : "";

            if (!isDegHidden && degEl != null)
            {
                string deg = ParseElement(degEl).Trim();
                if (!string.IsNullOrEmpty(deg))
                {
                    return $@"\sqrt[{deg}]{{{e}}}";
                }
            }

            return $@"\sqrt{{{e}}}";
        }

        private string ParseDelimiter(XElement dEl)
        {
            string begChr = "(";
            string endChr = ")";

            var dPr = dEl.Element(M + "dPr");
            if (dPr != null)
            {
                var beg = dPr.Element(M + "begChr");
                if (beg != null) begChr = beg.Attribute(M + "val")?.Value ?? "(";

                var end = dPr.Element(M + "endChr");
                if (end != null) endChr = end.Attribute(M + "val")?.Value ?? ")";
            }

            var eEl = dEl.Element(M + "e");
            string content = eEl != null ? ParseElement(eEl) : "";

            string left = EscapeDelimiter(begChr, true);
            string right = EscapeDelimiter(endChr, false);

            return $@"\left{left}{content}\right{right}";
        }

        private string EscapeDelimiter(string chr, bool isLeft)
        {
            if (string.IsNullOrEmpty(chr)) return ".";
            switch (chr)
            {
                case "(": return "(";
                case ")": return ")";
                case "[": return "[";
                case "]": return "]";
                case "{": return @"\{";
                case "}": return @"\}";
                case "|": return "|";
                case "‖": return @"\|";
                default: return chr;
            }
        }

        private string ParseNary(XElement naryEl)
        {
            string op = @"\int ";
            var naryPr = naryEl.Element(M + "naryPr");
            if (naryPr != null)
            {
                var chrEl = naryPr.Element(M + "chr");
                string chrVal = chrEl?.Attribute(M + "val")?.Value ?? "∫";
                if (chrVal == "∑") op = @"\sum ";
                else if (chrVal == "∏") op = @"\prod ";
                else if (chrVal == "∬") op = @"\iint ";
                else if (chrVal == "∭") op = @"\iiint ";
                else if (chrVal == "∮") op = @"\oint ";
            }

            var subEl = naryEl.Element(M + "sub");
            var supEl = naryEl.Element(M + "sup");
            var eEl = naryEl.Element(M + "e");

            string sub = subEl != null ? ParseElement(subEl).Trim() : "";
            string sup = supEl != null ? ParseElement(supEl).Trim() : "";
            string e = eEl != null ? ParseElement(eEl) : "";

            var sb = new StringBuilder(op);
            if (!string.IsNullOrEmpty(sub)) sb.Append($"_{{{sub}}}");
            if (!string.IsNullOrEmpty(sup)) sb.Append($"^{{{sup}}}");
            sb.Append($"{{{e}}}");

            return sb.ToString();
        }

        private string ParseFunction(XElement funcEl)
        {
            var fNameEl = funcEl.Element(M + "fName");
            var eEl = funcEl.Element(M + "e");

            string fName = fNameEl != null ? ParseElement(fNameEl).Trim() : "";
            string e = eEl != null ? ParseElement(eEl) : "";

            if (!fName.StartsWith(@"\"))
            {
                fName = @"\" + fName;
            }

            return $"{fName} {e}";
        }

        private string ParseBar(XElement barEl)
        {
            var eEl = barEl.Element(M + "e");
            string e = eEl != null ? ParseElement(eEl) : "";
            return $@"\overline{{{e}}}";
        }

        private string ParseMatrix(XElement mEl)
        {
            var rows = mEl.Elements(M + "mr");
            var sb = new StringBuilder(@"\begin{matrix}");

            bool firstRow = true;
            foreach (var row in rows)
            {
                if (!firstRow) sb.Append(@" \\ ");
                firstRow = false;

                var cells = row.Elements(M + "e");
                bool firstCell = true;
                foreach (var cell in cells)
                {
                    if (!firstCell) sb.Append(" & ");
                    firstCell = false;
                    sb.Append(ParseElement(cell));
                }
            }
            sb.Append(@"\end{matrix}");
            return sb.ToString();
        }

        private string ParseEquationArray(XElement eqArrEl)
        {
            var rows = eqArrEl.Elements(M + "e");
            var sb = new StringBuilder(@"\begin{aligned}");

            bool first = true;
            foreach (var r in rows)
            {
                if (!first) sb.Append(@" \\ ");
                first = false;
                sb.Append(ParseElement(r));
            }
            sb.Append(@"\end{aligned}");
            return sb.ToString();
        }

        private string ParseAccent(XElement accEl)
        {
            var eEl = accEl.Element(M + "e");
            string e = eEl != null ? ParseElement(eEl) : "";

            string accChr = "→";
            var accPr = accEl.Element(M + "accPr");
            if (accPr != null)
            {
                accChr = accPr.Element(M + "chr")?.Attribute(M + "val")?.Value ?? "→";
            }

            if (accChr == "→" || accChr == "⃗") return $@"\vec{{{e}}}";
            if (accChr == "^" || accChr == "̂") return $@"\hat{{{e}}}";
            if (accChr == "‾" || accChr == "̄") return $@"\overline{{{e}}}";

            return e;
        }

        private string WrapIfNeeded(string text)
        {
            if (text.Length > 1 && !text.StartsWith("{") && !text.StartsWith(@"\"))
            {
                return $"{{{text}}}";
            }
            return text;
        }

        private string CleanLatexOutput(string latex)
        {
            if (string.IsNullOrWhiteSpace(latex)) return string.Empty;

            // Xóa khoảng trắng thừa và chuẩn hóa cú pháp
            string res = Regex.Replace(latex, @"\s+", " ").Trim();
            res = res.Replace(@"\frac {", @"\frac{")
                     .Replace(@"\sqrt {", @"\sqrt{")
                     .Replace(@"^ {", "^{")
                     .Replace(@"_ {", "_{");

            return res;
        }

        private string FallbackRegexExtraction(string xml)
        {
            var matches = Regex.Matches(xml, @"<m:t[^>]*>([^<]+)<\/m:t>", RegexOptions.IgnoreCase);
            var sb = new StringBuilder();
            foreach (Match m in matches)
            {
                string text = m.Groups[1].Value;
                foreach (var kv in UnicodeToLatexMap)
                {
                    if (text.Contains(kv.Key)) text = text.Replace(kv.Key, kv.Value);
                }
                sb.Append(text);
            }
            return sb.ToString().Trim();
        }
    }
}
