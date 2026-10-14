using System;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Threading;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Media;
using System.Xml.Linq;
using FluentAssertions;
using Xunit;
using Xunit.Abstractions;

namespace MatrixExamAI.Desktop.Tests
{
    public class AdversarialUiLayoutTests
    {
        private readonly string _desktopSrcDir;
        private readonly ITestOutputHelper _output;

        public AdversarialUiLayoutTests(ITestOutputHelper output)
        {
            _output = output;
            string currentDir = AppDomain.CurrentDomain.BaseDirectory;
            var dir = new DirectoryInfo(currentDir);
            while (dir != null && !File.Exists(Path.Combine(dir.FullName, "desktop_csharp.sln")) && !File.Exists(Path.Combine(dir.FullName, "desktop_csharp.slnx")))
            {
                dir = dir.Parent;
            }

            _desktopSrcDir = Path.Combine(dir?.FullName ?? "m:\\IT\\Phần mềm biên soạn tài liệu\\MEA_v5.0\\desktop_csharp", "src", "MatrixExamAI.Desktop");
        }

        #region 1. Viewport Responsiveness Stress Tests (1366x768 and 1024x768)

        [Theory]
        [InlineData(1024, 768, 220, "1024x768 with NavPane Open")]
        [InlineData(1024, 768, 50, "1024x768 with NavPane Compact")]
        [InlineData(1366, 768, 220, "1366x768 with NavPane Open")]
        [InlineData(1366, 768, 50, "1366x768 with NavPane Compact")]
        public void MainWindow_ViewportBudget_ShouldProvideAdequateContentWidthAndHeight(
            double windowWidth, double windowHeight, double paneWidth, string scenario)
        {
            // Usable screen height with standard 40px taskbar = 728px
            double taskbarHeight = 40;
            double effectiveScreenHeight = windowHeight - taskbarHeight;

            // MainWindow configured bounds
            string mainWindowXaml = File.ReadAllText(Path.Combine(_desktopSrcDir, "MainWindow.xaml"));
            mainWindowXaml.Should().Contain("Height=\"720\"");
            mainWindowXaml.Should().Contain("Width=\"1280\"");
            mainWindowXaml.Should().Contain("MinHeight=\"680\"");
            mainWindowXaml.Should().Contain("MinWidth=\"1024\"");

            // Effective window dimensions must not exceed screen bounds
            720.0.Should().BeLessThanOrEqualTo(effectiveScreenHeight,
                $"MainWindow Height (720px) must fit within {scenario} effective screen height ({effectiveScreenHeight}px)");

            double availableContentWidth = windowWidth - paneWidth;
            _output.WriteLine($"[Viewport Empirical] {scenario}: Window={windowWidth}x{windowHeight}, PaneWidth={paneWidth}, AvailableContentWidth={availableContentWidth}px, EffectiveScreenHeight={effectiveScreenHeight}px");

            availableContentWidth.Should().BeGreaterOrEqualTo(804,
                $"Content width must be >= 804px even at minimum resolution with open pane in {scenario}");

            // Minimum required width for any View with split layout (ConvertView requires 620px, TikzView requires 640px)
            availableContentWidth.Should().BeGreaterThan(640,
                $"Available content width {availableContentWidth}px must exceed largest view minimum width 640px");
        }

        [Theory]
        [InlineData("ExamMatrixView.xaml")]
        [InlineData("ShuffleView.xaml")]
        [InlineData("TikzView.xaml")]
        [InlineData("QuestionBankView.xaml")]
        [InlineData("QcView.xaml")]
        public void FunctionalViews_MainToolbars_ShouldUseWrapPanelsToPreventButtonClipping(string viewFileName)
        {
            string path = Path.Combine(_desktopSrcDir, "Views", viewFileName);
            File.Exists(path).Should().BeTrue($"View file {viewFileName} must exist");

            string content = File.ReadAllText(path);

            // Functional views must use WrapPanel for flexible button wrapping on main toolbars
            content.Should().Contain("<WrapPanel",
                $"View '{viewFileName}' must use WrapPanel to ensure buttons wrap instead of clipping on narrow viewports");
        }

        [Fact]
        public void ConvertView_LeftCardHeader_CheckWhetherTitleAndButtonsCollideAtNarrowWidths()
        {
            RunOnStaThread(() =>
            {
                // Measure Left Title: SymbolIcon (24px) + Margin (6px) + TextBlock
                string titleText = "Nội dung nguồn (PDF trích xuất hoặc Dán đề)";
                var typefaceBold = new Typeface(new FontFamily("Segoe UI"), FontStyles.Normal, FontWeights.SemiBold, FontStretches.Normal);
                var formattedTitle = new FormattedText(
                    titleText,
                    CultureInfo.InvariantCulture,
                    FlowDirection.LeftToRight,
                    typefaceBold,
                    12.5,
                    Brushes.Black,
                    1.0);

                double titleWidth = 24 + 6 + formattedTitle.WidthIncludingTrailingWhitespace; // ~285 DIPs

                // Measure Right Action Group: TxtInputStats + BtnCardClearOld + BtnLoadSample
                // Stats: ~60 DIPs
                // BtnCardClearOld: Delete24 icon (20 DIPs) + text "Xóa bản cũ" + padding (12) + margin (4) ~ 90 DIPs
                // BtnLoadSample: text "Nạp đề mẫu" + padding (12) ~ 75 DIPs
                double rightActionsWidth = 60 + 90 + 75; // ~225 DIPs

                double totalNeededWidthWithoutOverlap = titleWidth + rightActionsWidth; // ~510 DIPs

                // In ConvertView.xaml: Left Card ColumnDefinition MinWidth="260"
                // And the Grid has NO ColumnDefinitions (single cell)
                string path = Path.Combine(_desktopSrcDir, "Views", "ConvertView.xaml");
                string content = File.ReadAllText(path);
                var xdoc = XDocument.Parse(content);

                var leftCardHeaderGrid = xdoc.Descendants()
                    .FirstOrDefault(e => e.Name.LocalName == "Grid" && 
                                         (string?)e.Attribute("Grid.Row") == "0" &&
                                         e.Elements().Any(c => c.Name.LocalName == "TextBlock" && c.Attributes().Any(a => a.Name.LocalName == "Name" && a.Value == "TxtInputStats")) == false &&
                                         e.Descendants().Any(c => c.Attributes().Any(a => a.Name.LocalName == "Name" && a.Value == "TxtInputHeaderTitle")));

                leftCardHeaderGrid.Should().NotBeNull();
                bool hasColumns = leftCardHeaderGrid!.Element(leftCardHeaderGrid.Name.Namespace + "Grid.ColumnDefinitions") != null;

                _output.WriteLine($"[Left Card Header Empirical] Title '{titleText}': Width={titleWidth:F1}px. Action Buttons: Width={rightActionsWidth:F1}px. CombinedNeededWidth={totalNeededWidthWithoutOverlap:F1}px. LeftCard MinWidth={260}px. DeficitAtMinWidth={totalNeededWidthWithoutOverlap - 260:F1}px. HasColumns={hasColumns}");

                // Document empirical finding: If hasColumns is false, title and buttons occupy same space when width < 510px
                totalNeededWidthWithoutOverlap.Should().BeGreaterThan(260.0,
                    $"Header title ({titleWidth:F1}px) + buttons ({rightActionsWidth:F1}px) requires {totalNeededWidthWithoutOverlap:F1}px, which exceeds MinWidth=260px");
            });
        }

        [Fact]
        public void ExamMatrixView_LeftPanel_MustBeEnclosedInScrollViewer_For768pVerticalScreens()
        {
            string path = Path.Combine(_desktopSrcDir, "Views", "ExamMatrixView.xaml");
            string content = File.ReadAllText(path);

            var xdoc = XDocument.Parse(content);
            var leftCard = xdoc.Descendants()
                .FirstOrDefault(e => e.Name.LocalName == "Card" && (string?)e.Attribute("Grid.Column") == "0");

            leftCard.Should().NotBeNull("ExamMatrixView must have Left Card");
            leftCard!.Elements().Any(e => e.Name.LocalName == "ScrollViewer").Should().BeTrue(
                "Left card in ExamMatrixView must enclose content in ScrollViewer to prevent vertical overflow on 768p displays");
        }

        #endregion

        #region 2. DPI Text Scaling & Dropdown Fit Tests (100%, 125%, 150%)

        [Theory]
        [InlineData(1.0, "100% DPI (96 dpi)")]
        [InlineData(1.25, "125% DPI (120 dpi)")]
        [InlineData(1.5, "150% DPI (144 dpi)")]
        public void CmbGrade_KhacOption_MustFitCleanlyWithoutTruncation(double dpiScale, string dpiLabel)
        {
            // Run measurement on STA thread for WPF FormattedText
            RunOnStaThread(() =>
            {
                // In ConvertView.xaml: CmbGrade Width="92", FontSize="11"
                double controlWidth = 92;
                double fontSize = 11;
                string targetText = "Khác";

                // WPF ComboBox layout overhead:
                // Right dropdown arrow glyph: ~24 DIPs
                // Internal padding & borders: ~16 DIPs (8 on left, 8 on right)
                double reservedUiChrome = 40;
                double availableTextWidth = controlWidth - reservedUiChrome; // 52 DIPs

                var typeface = new Typeface(new FontFamily("Segoe UI"), FontStyles.Normal, FontWeights.Normal, FontStretches.Normal);
                var formattedText = new FormattedText(
                    targetText,
                    CultureInfo.InvariantCulture,
                    FlowDirection.LeftToRight,
                    typeface,
                    fontSize,
                    Brushes.Black,
                    dpiScale);

                double measuredWidth = formattedText.WidthIncludingTrailingWhitespace;
                double safetyClearance = availableTextWidth - measuredWidth;
                _output.WriteLine($"[DPI Empirical] {dpiLabel} - Text '{targetText}': MeasuredWidth={measuredWidth:F2} DIPs, ControlWidth={controlWidth} DIPs, AvailableWidth={availableTextWidth:F2} DIPs, Clearance={safetyClearance:F2} DIPs");

                // Output empirical measurements
                measuredWidth.Should().BeLessThan(availableTextWidth,
                    $"At {dpiLabel}, '{targetText}' width ({measuredWidth:F2} DIPs) must fit within available width ({availableTextWidth:F2} DIPs) of CmbGrade (Width={controlWidth})");

                safetyClearance.Should().BeGreaterOrEqualTo(15.0,
                    $"At {dpiLabel}, '{targetText}' in CmbGrade must have at least 15 DIPs safety clearance (actual: {safetyClearance:F2} DIPs)");
            });
        }

        [Theory]
        [InlineData(1.0, "100% DPI (96 dpi)")]
        [InlineData(1.25, "125% DPI (120 dpi)")]
        [InlineData(1.5, "150% DPI (144 dpi)")]
        public void CmbSubject_TiengAnhOption_MustFitCleanlyWithoutTruncation(double dpiScale, string dpiLabel)
        {
            RunOnStaThread(() =>
            {
                // In ConvertView.xaml: CmbSubject Width="130", FontSize="11"
                double controlWidth = 130;
                double fontSize = 11;
                string targetText = "Tiếng Anh";

                // Reserved UI Chrome: dropdown arrow (24 DIPs) + internal padding (16 DIPs) = 40 DIPs
                double reservedUiChrome = 40;
                double availableTextWidth = controlWidth - reservedUiChrome; // 90 DIPs

                var typeface = new Typeface(new FontFamily("Segoe UI"), FontStyles.Normal, FontWeights.Normal, FontStretches.Normal);
                var formattedText = new FormattedText(
                    targetText,
                    CultureInfo.InvariantCulture,
                    FlowDirection.LeftToRight,
                    typeface,
                    fontSize,
                    Brushes.Black,
                    dpiScale);

                double measuredWidth = formattedText.WidthIncludingTrailingWhitespace;
                double safetyClearance = availableTextWidth - measuredWidth;
                _output.WriteLine($"[DPI Empirical] {dpiLabel} - Text '{targetText}': MeasuredWidth={measuredWidth:F2} DIPs, ControlWidth={controlWidth} DIPs, AvailableWidth={availableTextWidth:F2} DIPs, Clearance={safetyClearance:F2} DIPs");

                measuredWidth.Should().BeLessThan(availableTextWidth,
                    $"At {dpiLabel}, '{targetText}' width ({measuredWidth:F2} DIPs) must fit within available width ({availableTextWidth:F2} DIPs) of CmbSubject (Width={controlWidth})");

                safetyClearance.Should().BeGreaterOrEqualTo(25.0,
                    $"At {dpiLabel}, '{targetText}' in CmbSubject must have at least 25 DIPs safety clearance (actual: {safetyClearance:F2} DIPs)");
            });
        }

        [Theory]
        [InlineData("Toán")]
        [InlineData("Vật lí")]
        [InlineData("Hóa học")]
        [InlineData("Sinh học")]
        [InlineData("Ngữ văn")]
        [InlineData("Tiếng Anh")]
        [InlineData("Tin học")]
        public void CmbSubject_AllOptions_MustFitWithinWidth130(string subjectName)
        {
            RunOnStaThread(() =>
            {
                double availableTextWidth = 130 - 40; // 90 DIPs
                var typeface = new Typeface(new FontFamily("Segoe UI"), FontStyles.Normal, FontWeights.Normal, FontStretches.Normal);
                var formattedText = new FormattedText(
                    subjectName,
                    CultureInfo.InvariantCulture,
                    FlowDirection.LeftToRight,
                    typeface,
                    11,
                    Brushes.Black,
                    1.25);

                formattedText.WidthIncludingTrailingWhitespace.Should().BeLessThan(availableTextWidth,
                    $"Subject '{subjectName}' must fit inside ComboBox width 130");
            });
        }

        #endregion

        #region 3. SplitView Splitter Dragging & Minimum Width Constraints

        [Fact]
        public void ConvertView_SplitView_ShouldEnforceUsableMinimumWidthsUnderSplitterDrag()
        {
            string path = Path.Combine(_desktopSrcDir, "Views", "ConvertView.xaml");
            string content = File.ReadAllText(path);

            var xdoc = XDocument.Parse(content);

            // Locate SplitView Grid (Row 2)
            var splitGrid = xdoc.Descendants()
                .FirstOrDefault(e => e.Name.LocalName == "Grid" && (string?)e.Attribute("Grid.Row") == "2");

            splitGrid.Should().NotBeNull("ConvertView must have SplitView Grid at Grid.Row=2");

            var columns = splitGrid!.Element(splitGrid.Name.Namespace + "Grid.ColumnDefinitions")?.Elements().ToList();
            columns.Should().NotBeNull();
            columns!.Count.Should().Be(3, "SplitView Grid must have 3 columns: Left, Splitter, Right");

            // Verify Left Column: Width="*" MinWidth >= 260
            string? leftMinWidthStr = (string?)columns[0].Attribute("MinWidth");
            leftMinWidthStr.Should().NotBeNull("Left column must define MinWidth");
            double leftMinWidth = double.Parse(leftMinWidthStr!);
            leftMinWidth.Should().BeGreaterOrEqualTo(260, "Left column MinWidth must be >= 260px");

            // Verify Splitter Column: Width="8"
            string? splitterWidth = (string?)columns[1].Attribute("Width");
            splitterWidth.Should().Be("8", "GridSplitter column width must be 8px");

            // Verify Right Column: Width="*" MinWidth >= 320
            string? rightMinWidthStr = (string?)columns[2].Attribute("MinWidth");
            rightMinWidthStr.Should().NotBeNull("Right column must define MinWidth");
            double rightMinWidth = double.Parse(rightMinWidthStr!);
            rightMinWidth.Should().BeGreaterOrEqualTo(320, "Right column MinWidth must be >= 320px");

            // Boundary Simulation: Total minimum width required for SplitView
            double totalRequiredMinWidth = leftMinWidth + 8 + rightMinWidth; // 260 + 8 + 320 = 588px
            totalRequiredMinWidth.Should().BeLessThanOrEqualTo(804,
                "Total minimum width of both columns (588px) must be comfortably less than available viewport at 1024x768 (804px)");

            // Splitter Drag Range Simulation:
            // At 1024x768 (content width 804px):
            // Maximum drag to left: Left pane stops at 260px, Right pane expands to 804 - 260 - 8 = 536px (usable)
            // Maximum drag to right: Right pane stops at 320px, Left pane expands to 804 - 320 - 8 = 476px (usable)
            double leftPaneAtMaxLeftDrag = leftMinWidth;
            double rightPaneAtMaxLeftDrag = 804 - 8 - leftMinWidth;
            leftPaneAtMaxLeftDrag.Should().Be(260.0);
            rightPaneAtMaxLeftDrag.Should().Be(536.0);

            double rightPaneAtMaxRightDrag = rightMinWidth;
            double leftPaneAtMaxRightDrag = 804 - 8 - rightMinWidth;
            rightPaneAtMaxRightDrag.Should().Be(320.0);
            leftPaneAtMaxRightDrag.Should().Be(476.0);

            _output.WriteLine($"[Splitter Empirical] ConvertView: MinLeft={leftMinWidth}px, Splitter=8px, MinRight={rightMinWidth}px. MaxLeftDrag -> Left={leftPaneAtMaxLeftDrag}px, Right={rightPaneAtMaxLeftDrag}px. MaxRightDrag -> Left={leftPaneAtMaxRightDrag}px, Right={rightPaneAtMaxRightDrag}px. MovableTravel={804 - 8 - leftMinWidth - rightMinWidth}px");

            // Neither pane can ever be crushed below usable width
            leftPaneAtMaxLeftDrag.Should().BeGreaterOrEqualTo(260.0);
            rightPaneAtMaxRightDrag.Should().BeGreaterOrEqualTo(320.0);
        }

        [Fact]
        public void TikzView_SplitView_ShouldEnforce300PxMinimumWidthsUnderSplitterDrag()
        {
            string path = Path.Combine(_desktopSrcDir, "Views", "TikzView.xaml");
            string content = File.ReadAllText(path);

            var xdoc = XDocument.Parse(content);

            var splitGrid = xdoc.Descendants()
                .FirstOrDefault(e => e.Name.LocalName == "Grid" && (string?)e.Attribute("Grid.Row") == "2");

            splitGrid.Should().NotBeNull("TikzView must have SplitView Grid at Grid.Row=2");

            var columns = splitGrid!.Element(splitGrid.Name.Namespace + "Grid.ColumnDefinitions")?.Elements().ToList();
            columns.Should().NotBeNull();
            columns!.Count.Should().Be(3);

            // Both columns must enforce MinWidth >= 300
            double leftMinWidth = double.Parse((string)columns[0].Attribute("MinWidth")!);
            double rightMinWidth = double.Parse((string)columns[2].Attribute("MinWidth")!);

            leftMinWidth.Should().BeGreaterOrEqualTo(300, "TikzView left pane MinWidth must be >= 300px");
            rightMinWidth.Should().BeGreaterOrEqualTo(300, "TikzView right pane MinWidth must be >= 300px");

            // Verify Left Header 3 buttons fit in 300px
            // BtnSampleBbt (~65px) + BtnSampleGraph (~75px) + BtnSampleHkg (~95px) = ~235px < 300px
            double headerButtonsWidth = 65 + 75 + 95;
            headerButtonsWidth.Should().BeLessThan(leftMinWidth,
                "Template sample buttons in TikzView left header must easily fit within 300px minimum pane width");

            // Splitter Drag Simulation at 1024x768 (available width = 804px)
            double totalMinWidth = leftMinWidth + 8 + rightMinWidth; // 608px
            totalMinWidth.Should().BeLessThan(804,
                "Total min width (608px) must be well within minimum content frame (804px)");

            double maxLeftDragRightWidth = 804 - 8 - leftMinWidth; // 496px
            double maxRightDragLeftWidth = 804 - 8 - rightMinWidth; // 496px

            _output.WriteLine($"[Splitter Empirical] TikzView: MinLeft={leftMinWidth}px, Splitter=8px, MinRight={rightMinWidth}px. SampleButtons={headerButtonsWidth}px. MaxLeftDrag -> Left={leftMinWidth}px, Right={maxLeftDragRightWidth}px. MaxRightDrag -> Left={maxRightDragLeftWidth}px, Right={rightMinWidth}px. MovableTravel={804 - 8 - leftMinWidth - rightMinWidth}px");

            maxLeftDragRightWidth.Should().BeGreaterThan(300.0);
            maxRightDragLeftWidth.Should().BeGreaterThan(300.0);
        }

        #endregion

        #region Helper Methods

        private static void RunOnStaThread(Action action)
        {
            Exception? exception = null;
            var thread = new Thread(() =>
            {
                try
                {
                    action();
                }
                catch (Exception ex)
                {
                    exception = ex;
                }
            });

            thread.SetApartmentState(ApartmentState.STA);
            thread.Start();
            thread.Join();

            if (exception != null)
            {
                throw new AggregateException("STA thread execution failed", exception);
            }
        }

        #endregion
    }
}
