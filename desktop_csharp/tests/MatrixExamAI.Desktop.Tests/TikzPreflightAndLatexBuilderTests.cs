using System;
using System.Linq;
using FluentAssertions;
using MatrixExamAI.Shared.Tikz;
using MatrixExamAI.Shared.Validation;
using Xunit;

namespace MatrixExamAI.Desktop.Tests
{
    public class TikzPreflightAndLatexBuilderTests
    {
        #region Tier 1 - Normative Tests (Validator Rules & AutoFix)

        [Fact]
        public void TikzPreflight_ValidTikzPicture_ShouldReturnZeroBlockingErrors()
        {
            string validTikz = @"\begin{tikzpicture}[scale=1.2]
    \draw[->] (-3,0) -- (3,0) node[right] {$x$};
    \draw[->] (0,-3) -- (0,3) node[above] {$y$};
    \draw[domain=-2:2,smooth,variable=\x,blue] plot ({\x},{\x*\x - 2});
    \node[below left] at (0,0) {$O$};
\end{tikzpicture}";

            var issues = TikzPreflightValidator.Check(validTikz);

            issues.Should().NotContain(i => i.Severity == IssueSeverity.Error);
            TikzPreflightValidator.HasBlockingErrors(validTikz).Should().BeFalse();
        }

        [Fact]
        public void TikzPreflight_ForbiddenLineCapRound_ShouldReportWarningAndAutoFixCleanly()
        {
            string codeWithLineCap = @"\begin{tikzpicture}
    \draw[line cap=round, line width=1.5pt] (0,0) -- (4,0);
\end{tikzpicture}";

            // Act 1: Check
            var issues = TikzPreflightValidator.Check(codeWithLineCap);
            issues.Should().Contain(i => i.Rule == "forbidden_line_cap" && i.Severity == IssueSeverity.Warning);

            // Act 2: AutoFix
            string fixedCode = TikzPreflightValidator.AutoFix(codeWithLineCap);
            fixedCode.Should().NotContain("line cap=round");
            fixedCode.Should().Contain("line width=1.5pt");
        }

        [Fact]
        public void TikzPreflight_TkzTabTypo_ShouldReportErrorAndAutoFixToTkzTabVar()
        {
            string codeWithTypo = @"\begin{tikzpicture}
    \tkzTabInit{$x$/1, $y'$/1, $y$/2}{$-\infty$, $1$, $+\infty$}
    \tkzTabLine{, -, 0, +, }
    \tkzTabVector{+/$+\infty$, -/$-4$, +/$+\infty$}
\end{tikzpicture}";

            // Act 1: Check
            var issues = TikzPreflightValidator.Check(codeWithTypo);
            issues.Should().Contain(i => i.Rule == "invalid_tkztab_command" && i.Severity == IssueSeverity.Error);

            // Act 2: AutoFix
            string fixedCode = TikzPreflightValidator.AutoFix(codeWithTypo);
            fixedCode.Should().NotContain("\\tkzTabVector");
            fixedCode.Should().Contain("\\tkzTabVar");
        }

        [Fact]
        public void TikzPreflight_LegacyPattern_ShouldReportInfoAndAutoFixToPatternsMeta()
        {
            string codeWithLegacy = @"\begin{tikzpicture}
    \fill[pattern=north west lines, pattern color=black!70] (0,0) rectangle (2,2);
\end{tikzpicture}";

            // Act 1: Check
            var issues = TikzPreflightValidator.Check(codeWithLegacy);
            issues.Should().Contain(i => i.Rule == "legacy_pattern");

            // Act 2: AutoFix
            string fixedCode = TikzPreflightValidator.AutoFix(codeWithLegacy);
            fixedCode.Should().NotContain("pattern=north west lines");
            fixedCode.Should().Contain("pattern={Lines[angle=45");
            fixedCode.Should().Contain("pattern color=gray!70");
        }

        [Fact]
        public void StandaloneLatexBuilder_AutoDetectPackages_ShouldIncludePhysicsAndSiunitxForUnits()
        {
            string tikzWithPhysics = @"\begin{tikzpicture}
    \draw (0,0) -- (4,0) node[midway,above] {$\qty{10}{\meter\per\second}$};
    \node at (2,-1) {$\abs{\vec{v}} = \norm{\vec{F}}$};
\end{tikzpicture}";

            string standaloneDoc = StandaloneLatexBuilder.BuildStandaloneDocument(tikzWithPhysics);

            standaloneDoc.Should().Contain(@"\documentclass[border=10pt,tikz,preview]{standalone}");
            standaloneDoc.Should().Contain(@"\usepackage{physics,siunitx}");
            standaloneDoc.Should().Contain(@"\sisetup{per-mode=symbol}");
            standaloneDoc.Should().Contain(@"\PreviewEnvironment{tikzpicture}");
            standaloneDoc.Should().Contain(@"\begin{document}");
            standaloneDoc.Should().Contain(@"\end{document}");
        }

        #endregion

        #region Tier 2 - Boundary Value Tests

        [Fact]
        public void TikzPreflight_UnbalancedBraces_ShouldReportBlockingError()
        {
            string unbalancedOpen = @"\begin{tikzpicture}
    \node at (0,0) {Chưa đóng ngoặc;
\end{tikzpicture}";

            var issues = TikzPreflightValidator.Check(unbalancedOpen);
            issues.Should().Contain(i => i.Rule == "balanced_braces" && i.Severity == IssueSeverity.Error);
            TikzPreflightValidator.HasBlockingErrors(unbalancedOpen).Should().BeTrue();
        }

        [Fact]
        public void TikzPreflight_ExtraClosingBrace_ShouldReportBlockingError()
        {
            string extraClose = @"\begin{tikzpicture}
    \node at (0,0) {Hợp lệ}};
\end{tikzpicture}";

            var issues = TikzPreflightValidator.Check(extraClose);
            issues.Should().Contain(i => i.Rule == "balanced_braces" && i.Severity == IssueSeverity.Error);
        }

        [Fact]
        public void TikzPreflight_MissingBeginEndPair_ShouldReportBlockingError()
        {
            string unclosedEnv = @"\begin{tikzpicture}
    \begin{axis}
        \addplot {x^2};
    % Thiếu \end{axis}
\end{tikzpicture}";

            var issues = TikzPreflightValidator.Check(unclosedEnv);
            issues.Should().Contain(i => i.Rule == "begin_end_pairs" && i.Severity == IssueSeverity.Error);
            TikzPreflightValidator.HasBlockingErrors(unclosedEnv).Should().BeTrue();
        }

        [Fact]
        public void TikzPreflight_AddPlotOutsideAxis_ShouldReportBlockingError()
        {
            string addplotOutside = @"\begin{tikzpicture}
    \addplot[blue] coordinates {(0,0) (1,1)};
\end{tikzpicture}";

            var issues = TikzPreflightValidator.Check(addplotOutside);
            issues.Should().Contain(i => i.Rule == "addplot_in_axis" && i.Severity == IssueSeverity.Error);
        }

        [Fact]
        public void TikzPreflight_EmptyOrWhitespaceCode_ShouldReportError()
        {
            var issues1 = TikzPreflightValidator.Check("");
            issues1.Should().Contain(i => i.Rule == "empty_code" && i.Severity == IssueSeverity.Error);

            var issues2 = TikzPreflightValidator.Check(null);
            issues2.Should().Contain(i => i.Rule == "empty_code");
        }

        #endregion

        #region Tier 3 - Combinatorial & Feature Interop Tests

        [Theory]
        [InlineData(@"\draw (0,0) to[R] (2,0);", "circuitikz")]
        [InlineData(@"\tkzDefPoint(0,0){A}", "tkz-euclide")]
        [InlineData(@"\tdplotsetmaincoords{70}{110}", "tikz-3dplot")]
        [InlineData(@"\tkzTabInit{$x$/1}{0, 1}", "tkz-tab")]
        public void StandaloneLatexBuilder_DomainSpecificCommands_ShouldIncludeDedicatedPackages(string snippet, string expectedPackage)
        {
            string code = $@"\begin{{tikzpicture}}
    {snippet}
\end{{tikzpicture}}";

            string doc = StandaloneLatexBuilder.BuildStandaloneDocument(code);
            doc.Should().Contain(expectedPackage);
        }

        [Fact]
        public void StandaloneLatexBuilder_AutoDetectLibraries_ShouldIncludeCalcPositioningAndArrows()
        {
            string code = @"\begin{tikzpicture}
    \node[above=of A] (B) {$B$};
    \path let \p1 = (A), \p2 = (B) in coordinate (C) at (\x1, \y2);
    \draw[-{Stealth[scale=1.2]}] (A) -- (B);
\end{tikzpicture}";

            string doc = StandaloneLatexBuilder.BuildStandaloneDocument(code);
            doc.Should().Contain("calc");
            doc.Should().Contain("positioning");
            doc.Should().Contain("arrows.meta");
        }

        #endregion

        #region Tier 4 - Workload & AutoFix Full Document Handling

        [Fact]
        public void AutoFix_FullDocumentPreamble_ShouldStripToStandaloneBody()
        {
            string fullDoc = @"\documentclass[12pt]{article}
\usepackage{tikz}
\begin{document}
\begin{tikzpicture}
    \draw (0,0) circle (2cm);
\end{tikzpicture}
\end{document}";

            string fixedCode = TikzPreflightValidator.AutoFix(fullDoc);

            fixedCode.Should().NotContain("\\documentclass");
            fixedCode.Should().NotContain("\\begin{document}");
            fixedCode.Should().Contain("\\begin{tikzpicture}");
            fixedCode.Should().Contain("\\draw (0,0) circle (2cm);");
        }

        #endregion
    }
}
