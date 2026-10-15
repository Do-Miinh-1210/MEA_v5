using System;
using System.IO;
using System.Linq;
using System.Xml.Linq;
using FluentAssertions;
using Xunit;

namespace MatrixExamAI.Desktop.Tests
{
    public class UiLayoutAndDpiBoundaryTests
    {
        private readonly string _desktopSrcDir;

        public UiLayoutAndDpiBoundaryTests()
        {
            // Base directory for desktop XAML sources
            string currentDir = AppDomain.CurrentDomain.BaseDirectory;
            // Navigate up to desktop_csharp directory
            var dir = new DirectoryInfo(currentDir);
            while (dir != null && !File.Exists(Path.Combine(dir.FullName, "desktop_csharp.sln")) && !File.Exists(Path.Combine(dir.FullName, "desktop_csharp.slnx")))
            {
                dir = dir.Parent;
            }

            _desktopSrcDir = Path.Combine(dir?.FullName ?? "m:\\IT\\Phần mềm biên soạn tài liệu\\MEA_v5.0\\desktop_csharp", "src", "MatrixExamAI.Desktop");
        }

        #region Tier 1 - Normative Tests (ConvertView Right Header Grid & Dropdowns)

        [Fact]
        public void ConvertViewXaml_RightHeader_ShouldBeTwoColumnGridToPreventOverlap()
        {
            string xamlPath = Path.Combine(_desktopSrcDir, "Views", "ConvertView.xaml");
            File.Exists(xamlPath).Should().BeTrue();

            string content = File.ReadAllText(xamlPath);
            var doc = XDocument.Parse(content);

            // Verify header has 2-column Grid separating preview tabs and action buttons
            content.Should().Contain("RbTabWordPreview");
            content.Should().Contain("RbTabRawCode");
            content.Should().Contain("BtnCopyOutput");
            content.Should().Contain("Sẵn sàng xuất Word");

            // Look for right header Grid
            content.Should().Contain("<ColumnDefinition Width=\"*\" />");
            content.Should().Contain("<ColumnDefinition Width=\"Auto\" />");
        }

        [Fact]
        public void ConvertViewXaml_DropdownWidths_ShouldBeSufficientForDpiScaling()
        {
            string xamlPath = Path.Combine(_desktopSrcDir, "Views", "ConvertView.xaml");
            string content = File.ReadAllText(xamlPath);

            // CmbGrade Width must fit grade name cleanly (Width >= 50, currently 58)
            content.Should().MatchRegex(@"x:Name=""CmbGrade""[^>]*Width=""(?:5[0-9]|[6-9][0-9]|[1-9][0-9]{2})""",
                "CmbGrade width must be compact to fit grade without pushing toolbar");

            // CmbSubject Width must fit subject name cleanly (Width >= 80, currently 82)
            content.Should().MatchRegex(@"x:Name=""CmbSubject""[^>]*Width=""(?:8[0-9]|9[0-9]|[1-9][0-9]{2})""",
                "CmbSubject width must be compact to fit subject name without pushing toolbar");

            // CmbQTypeFilter Width must be >= 155
            content.Should().MatchRegex(@"x:Name=""CmbQTypeFilter""[^>]*Width=""(?:15[5-9]|1[6-9][0-9]|[2-9][0-9]{2})""",
                "CmbQTypeFilter width must be >= 155px");

            // TxtCurrentFile must have CharacterEllipsis
            content.Should().Contain("TextTrimming=\"CharacterEllipsis\"");
        }

        [Fact]
        public void ConvertViewXaml_DataGrid_ShouldHaveScrollBarsAndCompactHeaderStyle()
        {
            string xamlPath = Path.Combine(_desktopSrcDir, "Views", "ConvertView.xaml");
            string content = File.ReadAllText(xamlPath);

            // DataGrid DgQuestions must have horizontal and vertical scrollbars enabled
            content.Should().Contain("HorizontalScrollBarVisibility=\"Auto\"",
                "DataGrid must enable horizontal scrollbar to prevent text clipping on narrow viewports");
            content.Should().Contain("VerticalScrollBarVisibility=\"Auto\"",
                "DataGrid must enable vertical scrollbar");
            content.Should().Contain("CanUserResizeColumns=\"True\"",
                "DataGrid must allow teachers to dynamically adjust column widths");

            // Explicit column header style with compact padding
            content.Should().Contain("<DataGrid.ColumnHeaderStyle>",
                "DataGrid must define explicit column header style to eliminate Wpf.Ui oversized margin clipping");
            content.Should().Contain("Property=\"Padding\" Value=\"6,4,6,4\"",
                "DataGridColumnHeader must use compact padding to fit Vietnamese labels");

            // Cell tooltips on text columns
            content.Should().Contain("Property=\"ToolTip\" Value=\"{Binding SubjectGrade}\"");
            content.Should().Contain("Property=\"ToolTip\" Value=\"{Binding ContentPreview}\"");
            content.Should().Contain("Property=\"ToolTip\" Value=\"{Binding ExplanationPreview}\"");
        }

        [Fact]
        public void ConvertViewXaml_QuestionDetailDrawer_ShouldBePresentWithExplanation()
        {
            string xamlPath = Path.Combine(_desktopSrcDir, "Views", "ConvertView.xaml");
            string content = File.ReadAllText(xamlPath);

            // Question detail drawer must be present to fulfill 'Sao nó không hiện luôn lời giải'
            content.Should().Contain("x:Name=\"BorderQuestionDetail\"",
                "Question Detail drawer must exist below DgQuestions");
            content.Should().Contain("x:Name=\"TxtDetailQuestionBody\"",
                "Question body TextBlock must exist in detail drawer");
            content.Should().Contain("x:Name=\"PanelDetailOptions\"",
                "Options panel must exist in detail drawer");
            content.Should().Contain("x:Name=\"BorderDetailExplanation\"",
                "Explanation card must exist in detail drawer");
            content.Should().Contain("x:Name=\"TxtDetailExplanation\"",
                "Explanation text must be displayed in detail drawer");
            content.Should().Contain("x:Name=\"BtnCopyDetailLatex\"",
                "Quick copy button for selected question must exist in detail drawer");
        }

        [Fact]
        public void ConvertViewXaml_ToolbarRow2_ShouldBeUnclippedAndProperlyEscaped()
        {
            string xamlPath = Path.Combine(_desktopSrcDir, "Views", "ConvertView.xaml");
            string content = File.ReadAllText(xamlPath);

            // BtnQuickBrace must escape curly braces to prevent WPF MarkupExtension parser corrupting 'Kẹp ${...}$'
            content.Should().Contain("Content=\"{}{Kẹp ${...}$}\"",
                "Button content must be escaped with {}{} so it renders 'Kẹp ${...}$' cleanly without corruption");

            // Top toolbar must host BtnToggleInsertMode next to BtnPaste
            content.Should().Contain("x:Name=\"BtnToggleInsertMode\"",
                "BtnToggleInsertMode must be housed in top toolbar next to paste button");

            // Top toolbar must host BtnCopyOutput and BtnExpandPreview
            content.Should().Contain("x:Name=\"BtnCopyOutput\"",
                "BtnCopyOutput must be housed in top toolbar");
            content.Should().Contain("x:Name=\"BtnExpandPreview\"",
                "BtnExpandPreview must be housed in top toolbar");

            // Top toolbar Row 2 must host all 3 preview mode tabs on a single unclipped line
            content.Should().Contain("x:Name=\"RbTabWordPreview\"",
                "RbTabWordPreview must be housed in top toolbar Row 2");
            content.Should().Contain("x:Name=\"RbTabQuestionGrid\"",
                "RbTabQuestionGrid must be housed in top toolbar Row 2");
            content.Should().Contain("x:Name=\"RbTabRawCode\"",
                "RbTabRawCode must be housed in top toolbar Row 2");
            content.Should().Contain("Content=\"Mã nguồn kẹp ${...}$\"",
                "RbTabRawCode must display clean 'Mã nguồn kẹp ${...}$' without extra leading curly braces");
        }

        #endregion

        #region Tier 2 - Boundary Value Tests (WrapPanels & 768p ScrollViewers)

        [Fact]
        public void ExamMatrixViewXaml_ConfigurationToolbar_ShouldUseWrapPanelForButtonWrapping()
        {
            string xamlPath = Path.Combine(_desktopSrcDir, "Views", "ExamMatrixView.xaml");
            string content = File.ReadAllText(xamlPath);

            content.Should().Contain("<WrapPanel Orientation=\"Horizontal\"",
                "ExamMatrixView must use WrapPanel to allow buttons to dynamically wrap on small resolutions");
        }

        [Fact]
        public void ShuffleViewXaml_ConfigurationToolbar_ShouldUseWrapPanelForButtonWrapping()
        {
            string xamlPath = Path.Combine(_desktopSrcDir, "Views", "ShuffleView.xaml");
            string content = File.ReadAllText(xamlPath);

            content.Should().Contain("<WrapPanel Orientation=\"Horizontal\"",
                "ShuffleView must use WrapPanel to prevent button clipping on window resize");
        }

        [Fact]
        public void ExamMatrixViewXaml_LeftConfigPanel_ShouldIncludeScrollViewerFor768pVerticalScreens()
        {
            string xamlPath = Path.Combine(_desktopSrcDir, "Views", "ExamMatrixView.xaml");
            string content = File.ReadAllText(xamlPath);

            content.Should().Contain("<ScrollViewer VerticalScrollBarVisibility=\"Auto\"",
                "Left panel must include ScrollViewer so buttons are not lost on low-vertical (768p) displays");
        }

        [Fact]
        public void TikzViewXaml_SplitViewColumns_ShouldEnforceMinWidthAtLeast300Px()
        {
            string xamlPath = Path.Combine(_desktopSrcDir, "Views", "TikzView.xaml");
            string content = File.ReadAllText(xamlPath);

            content.Should().MatchRegex(@"<ColumnDefinition\s+Width=""\*""\s+MinWidth=""300""\s*/>",
                "TikzView split columns must have MinWidth of at least 300px to prevent one side from collapsing completely");
        }

        #endregion

        #region Tier 3 - Combinatorial & Baseline Window Layout Tests

        [Fact]
        public void MainWindowXaml_BaselineDimensions_ShouldBe1280x720WithSafeMinimumBounds()
        {
            string xamlPath = Path.Combine(_desktopSrcDir, "MainWindow.xaml");
            string content = File.ReadAllText(xamlPath);

            content.Should().Contain("Height=\"720\"");
            content.Should().Contain("Width=\"1280\"");
            content.Should().Contain("MinHeight=\"680\"");
            content.Should().Contain("MinWidth=\"1024\"");
        }

        [Fact]
        public void AppManifest_DpiAwareness_ShouldDeclarePerMonitorV2()
        {
            string manifestPath = Path.Combine(_desktopSrcDir, "app.manifest");
            File.Exists(manifestPath).Should().BeTrue();

            string content = File.ReadAllText(manifestPath);

            content.Should().Contain("PerMonitorV2");
            content.Should().Contain("true/PM");
        }

        #endregion

        #region Tier 4 - Uniform Margins Across Views

        [Fact]
        public void StandardPageMargins_AllFunctionalViews_ShouldFollow16_12_16_14Standard()
        {
            string viewsDir = Path.Combine(_desktopSrcDir, "Views");
            var gridViews = new[]
            {
                "ConvertView.xaml",
                "ExamMatrixView.xaml",
                "TikzView.xaml",
                "ShuffleView.xaml",
                "QuestionBankView.xaml",
                "QcView.xaml"
            };

            foreach (var viewName in gridViews)
            {
                string path = Path.Combine(viewsDir, viewName);
                string text = File.ReadAllText(path);
                text.Should().Contain("Margin=\"16,12,16,14\"",
                    "Grid-based View '{0}' must follow standard page margin 16,12,16,14", viewName);
            }

            // Scrollable form views (SettingsView, DashboardView)
            var formViews = new[] { "SettingsView.xaml", "DashboardView.xaml" };
            foreach (var viewName in formViews)
            {
                string path = Path.Combine(viewsDir, viewName);
                string text = File.ReadAllText(path);
                text.Should().Contain("Margin=\"20,16,20,20\"",
                    "Form View '{0}' must follow standard scrollable margin 20,16,20,20", viewName);
            }
        }

        #endregion
    }
}
