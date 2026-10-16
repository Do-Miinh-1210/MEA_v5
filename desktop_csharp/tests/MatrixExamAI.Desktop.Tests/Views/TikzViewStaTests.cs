using System;
using System.Globalization;
using System.Linq;
using System.Reflection;
using System.Threading;
using System.Windows;
using System.Windows.Controls;
using FluentAssertions;
using MatrixExamAI.Desktop.Views;
using MatrixExamAI.Shared.Models;
using MatrixExamAI.Shared.Tikz;
using Xunit;

namespace MatrixExamAI.Desktop.Tests.Views
{
    public class TikzViewStaTests
    {
        #region STA Thread Execution Helper

        private static void RunOnSta(Action action)
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
                System.Runtime.ExceptionServices.ExceptionDispatchInfo.Capture(exception).Throw();
            }
        }

        private static T GetControl<T>(TikzView view, string name) where T : class
        {
            var control = view.FindName(name) as T;
            if (control != null) return control;

            var field = typeof(TikzView).GetField(name, BindingFlags.Instance | BindingFlags.NonPublic | BindingFlags.Public);
            var val = field?.GetValue(view) as T;
            if (val != null) return val;

            throw new InvalidOperationException($"Control '{name}' of type {typeof(T).Name} could not be resolved on TikzView.");
        }

        #endregion

        #region STA UI Facts

        [Fact]
        public void TikzView_InitializesSuccessfully_OnStaThread()
        {
            RunOnSta(() =>
            {
                // Act
                var view = new TikzView();

                // Assert
                view.Should().NotBeNull("TikzView must instantiate cleanly on an STA thread");

                var txtTexStatus = GetControl<TextBlock>(view, "TxtTexStatus");
                txtTexStatus.Should().NotBeNull();
                txtTexStatus.Text.Should().NotBeNullOrWhiteSpace();

                var txtTikzCode = GetControl<Wpf.Ui.Controls.TextBox>(view, "TxtTikzCode");
                txtTikzCode.Should().NotBeNull();

                var cmbDiagramType = GetControl<ComboBox>(view, "CmbDiagramType");
                cmbDiagramType.Should().NotBeNull();

                var cmbCategory = GetControl<ComboBox>(view, "CmbTemplateCategory");
                cmbCategory.Should().NotBeNull();

                var cmbItem = GetControl<ComboBox>(view, "CmbTemplateItem");
                cmbItem.Should().NotBeNull();

                var btnCompile = GetControl<Wpf.Ui.Controls.Button>(view, "BtnCompile");
                btnCompile.Should().NotBeNull();

                var btnGenerateTikz = GetControl<Wpf.Ui.Controls.Button>(view, "BtnGenerateTikz");
                btnGenerateTikz.Should().NotBeNull();

                var btnPasteImage = GetControl<Wpf.Ui.Controls.Button>(view, "BtnPasteImage");
                btnPasteImage.Should().NotBeNull();

                var btnSavePng = GetControl<Wpf.Ui.Controls.Button>(view, "BtnSavePng");
                btnSavePng.Should().NotBeNull();

                var btnInsertWord = GetControl<Wpf.Ui.Controls.Button>(view, "BtnInsertWord");
                btnInsertWord.Should().NotBeNull();
            });
        }

        [Fact]
        public void TikzView_ToolTips_ContainExpectedShortcuts()
        {
            RunOnSta(() =>
            {
                // Arrange
                var view = new TikzView();

                var btnCompile = GetControl<Wpf.Ui.Controls.Button>(view, "BtnCompile");
                var btnGenerateTikz = GetControl<Wpf.Ui.Controls.Button>(view, "BtnGenerateTikz");
                var btnPasteImage = GetControl<Wpf.Ui.Controls.Button>(view, "BtnPasteImage");
                var btnSavePng = GetControl<Wpf.Ui.Controls.Button>(view, "BtnSavePng");
                var btnInsertWord = GetControl<Wpf.Ui.Controls.Button>(view, "BtnInsertWord");

                // Assert BtnCompile (F5 / Ctrl+Enter)
                btnCompile.ToolTip.Should().NotBeNull("BtnCompile must have a descriptive ToolTip");
                string compileTip = btnCompile.ToolTip.ToString()!;
                compileTip.Should().Contain("F5", "Compile button tooltip must mention F5 shortcut");
                compileTip.Should().Contain("Ctrl+Enter", "Compile button tooltip must mention Ctrl+Enter shortcut");

                // Assert BtnGenerateTikz (Ctrl+Shift+G)
                btnGenerateTikz.ToolTip.Should().NotBeNull("BtnGenerateTikz must have a ToolTip");
                btnGenerateTikz.ToolTip.ToString().Should().Contain("Ctrl+Shift+G",
                    "AI generation button tooltip must mention Ctrl+Shift+G shortcut");

                // Assert BtnPasteImage (Ctrl+V)
                btnPasteImage.ToolTip.Should().NotBeNull("BtnPasteImage must have a ToolTip");
                btnPasteImage.ToolTip.ToString().Should().Contain("Ctrl+V",
                    "Paste image button tooltip must mention Ctrl+V shortcut");

                // Assert BtnSavePng (Ctrl+S)
                btnSavePng.ToolTip.Should().NotBeNull("BtnSavePng must have a ToolTip");
                btnSavePng.ToolTip.ToString().Should().Contain("Ctrl+S",
                    "Save PNG button tooltip must mention Ctrl+S shortcut");

                // Assert BtnInsertWord (Ctrl+Shift+W)
                btnInsertWord.ToolTip.Should().NotBeNull("BtnInsertWord must have a ToolTip");
                btnInsertWord.ToolTip.ToString().Should().Contain("Ctrl+Shift+W",
                    "Insert Word button tooltip must mention Ctrl+Shift+W shortcut");
            });
        }

        [Fact]
        public void TikzView_TemplateSelection_AutoPopulatesEditor()
        {
            RunOnSta(() =>
            {
                // Arrange
                var view = new TikzView();
                var cmbCategory = GetControl<ComboBox>(view, "CmbTemplateCategory");
                var cmbItem = GetControl<ComboBox>(view, "CmbTemplateItem");
                var txtTikzCode = GetControl<Wpf.Ui.Controls.TextBox>(view, "TxtTikzCode");

                cmbCategory.Items.Count.Should().BeGreaterOrEqualTo(1, "Template categories must be populated");

                // Act & Assert across all categories in the UI
                for (int catIdx = 0; catIdx < cmbCategory.Items.Count; catIdx++)
                {
                    cmbCategory.SelectedIndex = catIdx;
                    var selectedCat = cmbCategory.SelectedItem as TikzTemplateCategory;
                    selectedCat.Should().NotBeNull();

                    cmbItem.Items.Count.Should().BeGreaterThan(0,
                        $"Category '{selectedCat!.Name}' must have template items");

                    // Select first template
                    cmbItem.SelectedIndex = 0;
                    var selectedTpl = cmbItem.SelectedItem as TikzTemplate;
                    selectedTpl.Should().NotBeNull();

                    // Verify editor code auto-population
                    txtTikzCode.Text.Should().NotBeNullOrWhiteSpace(
                        $"Selecting template '{selectedTpl!.Title}' must auto-populate the code editor");
                    txtTikzCode.Text.Should().Be(selectedTpl.Code);
                    txtTikzCode.Text.Should().Contain(@"\begin{tikzpicture}");
                    txtTikzCode.Text.Should().Contain(@"\end{tikzpicture}");
                }
            });
        }

        [Fact]
        public void TikzView_Buttons_ConformToSingleIconStandard()
        {
            RunOnSta(() =>
            {
                // Arrange
                var view = new TikzView();
                var actionButtons = new[]
                {
                    GetControl<Wpf.Ui.Controls.Button>(view, "BtnPasteImage"),
                    GetControl<Wpf.Ui.Controls.Button>(view, "BtnGenerateTikz"),
                    GetControl<Wpf.Ui.Controls.Button>(view, "BtnCompile"),
                    GetControl<Wpf.Ui.Controls.Button>(view, "BtnSavePng"),
                    GetControl<Wpf.Ui.Controls.Button>(view, "BtnInsertWord"),
                    GetControl<Wpf.Ui.Controls.Button>(view, "BtnRemoveImage")
                };

                // Assert
                foreach (var btn in actionButtons)
                {
                    btn.Should().NotBeNull();

                    // 1. Must declare a dedicated Wpf.Ui SymbolIcon
                    btn.Icon.Should().NotBeNull($"Button '{btn.Name}' must have a dedicated Wpf.Ui SymbolIcon");

                    // 2. Content must not embed emojis
                    if (btn.Content is string text)
                    {
                        text.Should().NotBeNullOrWhiteSpace();

                        // Detect unicode emojis / symbols
                        bool hasEmoji = text.Any(c =>
                            char.GetUnicodeCategory(c) == UnicodeCategory.OtherSymbol ||
                            char.GetUnicodeCategory(c) == UnicodeCategory.Surrogate ||
                            (c >= 0x2600 && c <= 0x27BF) || // Miscellaneous Symbols & Dingbats
                            (c >= 0x1F300 && c <= 0x1F9FF));

                        hasEmoji.Should().BeFalse(
                            $"Button '{btn.Name}' with content '{text}' must adhere to '1 button - 1 icon' and not mix emojis with SymbolIcon");
                    }
                }
            });
        }

        [Fact]
        public void TikzView_DiagramType_IsAlignedWithEnum()
        {
            RunOnSta(() =>
            {
                // Arrange
                var view = new TikzView();
                var cmbDiagramType = GetControl<ComboBox>(view, "CmbDiagramType");

                // Assert
                cmbDiagramType.Should().NotBeNull();
                cmbDiagramType.Items.Count.Should().Be(5,
                    "CmbDiagramType must contain exactly 5 items mapping 1:1 to DiagramType enum");

                var expectedEnumMappings = new (int Index, DiagramType Type, string ExpectedTag)[]
                {
                    (0, DiagramType.BBT, "BBT"),
                    (1, DiagramType.BXD, "BXD"),
                    (2, DiagramType.DoThi, "DoThi"),
                    (3, DiagramType.HinhKhongGian, "HinhKhongGian"),
                    (4, DiagramType.Custom, "Custom")
                };

                foreach (var mapping in expectedEnumMappings)
                {
                    var item = cmbDiagramType.Items[mapping.Index] as ComboBoxItem;
                    item.Should().NotBeNull($"Item at index {mapping.Index} must be a ComboBoxItem");
                    item!.Tag.Should().NotBeNull($"Tag at index {mapping.Index} must not be null");
                    item.Tag.ToString().Should().Be(mapping.ExpectedTag,
                        $"Index {mapping.Index} of CmbDiagramType must have Tag '{mapping.ExpectedTag}' matching DiagramType.{mapping.Type}");
                }
            });
        }

        [Fact]
        public void TikzView_DiagramType_AutoSyncsWithTemplateCategory()
        {
            RunOnSta(() =>
            {
                // Arrange
                var view = new TikzView();
                var cmbCategory = GetControl<ComboBox>(view, "CmbTemplateCategory");
                var cmbDiagramType = GetControl<ComboBox>(view, "CmbDiagramType");

                // Test Graphs category sync
                for (int i = 0; i < cmbCategory.Items.Count; i++)
                {
                    if (cmbCategory.Items[i] is TikzTemplateCategory cat && cat.Id == "graphs")
                    {
                        cmbCategory.SelectedIndex = i;
                        cmbDiagramType.SelectedIndex.Should().Be((int)DiagramType.DoThi,
                            "Selecting 'graphs' category must auto-sync CmbDiagramType to DiagramType.DoThi (2)");
                        break;
                    }
                }

                // Test 3D category sync
                for (int i = 0; i < cmbCategory.Items.Count; i++)
                {
                    if (cmbCategory.Items[i] is TikzTemplateCategory cat && cat.Id == "solid_3d")
                    {
                        cmbCategory.SelectedIndex = i;
                        cmbDiagramType.SelectedIndex.Should().Be((int)DiagramType.HinhKhongGian,
                            "Selecting 'solid_3d' category must auto-sync CmbDiagramType to DiagramType.HinhKhongGian (3)");
                        break;
                    }
                }
            });
        }

        [Fact]
        public void TikzView_SplitColumns_HaveSafeMinimumWidthOf300()
        {
            RunOnSta(() =>
            {
                // Arrange
                var view = new TikzView();
                var rootGrid = view.Content as Grid;
                rootGrid.Should().NotBeNull();

                // Row 2 is the SplitView Grid
                var splitGrid = rootGrid!.Children.OfType<Grid>().FirstOrDefault(g => Grid.GetRow(g) == 2);
                splitGrid.Should().NotBeNull("SplitView Grid must exist at Row 2 of TikzView");

                // Assert
                splitGrid!.ColumnDefinitions.Count.Should().Be(3);
                splitGrid.ColumnDefinitions[0].MinWidth.Should().BeGreaterOrEqualTo(300,
                    "Left split column must have MinWidth >= 300 to prevent panel collapse");
                splitGrid.ColumnDefinitions[2].MinWidth.Should().BeGreaterOrEqualTo(300,
                    "Right split column must have MinWidth >= 300 to prevent panel collapse");
            });
        }

        [Fact]
        public void TikzView_Toolbar_ContainsAllPaletteButtonsAndDirectPromptInput()
        {
            RunOnSta(() =>
            {
                var view = new TikzView();
                var txtPrompt = GetControl<Wpf.Ui.Controls.TextBox>(view, "TxtFigurePrompt");
                var btnDraw = GetControl<Wpf.Ui.Controls.Button>(view, "BtnGenerateTikz");
                var btnShape = GetControl<Wpf.Ui.Controls.Button>(view, "BtnShapeBuilder");
                var btnRedraw = GetControl<Wpf.Ui.Controls.Button>(view, "BtnAiRedraw");
                var btnEdit = GetControl<Wpf.Ui.Controls.Button>(view, "BtnAiEdit");
                var btnOpt = GetControl<Wpf.Ui.Controls.Button>(view, "BtnAiOptimize");
                var btnPaste = GetControl<Wpf.Ui.Controls.Button>(view, "BtnPasteImage");
                var btnClean = GetControl<Wpf.Ui.Controls.Button>(view, "BtnCleanTikzCode");
                var btnClear = GetControl<Wpf.Ui.Controls.Button>(view, "BtnClearTikz");
                var btnCompile = GetControl<Wpf.Ui.Controls.Button>(view, "BtnCompile");

                txtPrompt.Should().NotBeNull();
                btnDraw.Should().NotBeNull();
                btnShape.Should().NotBeNull();
                btnRedraw.Should().NotBeNull();
                btnEdit.Should().NotBeNull();
                btnOpt.Should().NotBeNull();
                btnPaste.Should().NotBeNull();
                btnClean.Should().NotBeNull();
                btnClear.Should().NotBeNull();
                btnCompile.Should().NotBeNull();

                // Verify semantic colors
                btnDraw.Background.ToString().Should().Contain("7C3AED"); // Violet
                btnShape.Background.ToString().Should().Contain("D97706"); // Amber
                btnRedraw.Background.ToString().Should().Contain("F59E0B"); // Orange
                btnEdit.Background.ToString().Should().Contain("2563EB"); // Blue
                btnOpt.Background.ToString().Should().Contain("9333EA"); // Purple
                btnCompile.Background.ToString().Should().Contain("059669"); // Emerald
                btnClear.Background.ToString().Should().Contain("DC2626"); // Red
            });
        }

        [Fact]
        public void AiDrawPromptDialog_InstantiatesOnSta_AndInitializesPromptProperly()
        {
            RunOnSta(() =>
            {
                var dlg = new AiDrawPromptDialog("Cho hình chóp S.ABCD đáy hình vuông");
                dlg.Should().NotBeNull();
                var txtPrompt = dlg.FindName("TxtInputPrompt") as Wpf.Ui.Controls.TextBox;
                txtPrompt.Should().NotBeNull();
                txtPrompt!.Text.Should().Be("Cho hình chóp S.ABCD đáy hình vuông");

                var chkGeo = dlg.FindName("ChkTaskGeo") as CheckBox;
                chkGeo.Should().NotBeNull();
                chkGeo!.IsChecked.Should().BeTrue();

                dlg.Close();
            });
        }

        [Fact]
        public void TikzShapeBuilderDialog_InstantiatesOnSta_HasGenerousHeightAndCompileButton()
        {
            RunOnSta(() =>
            {
                var dlg = new TikzShapeBuilderDialog();
                dlg.Should().NotBeNull();

                var txtParam1 = dlg.FindName("TxtParam1") as Wpf.Ui.Controls.TextBox;
                txtParam1.Should().NotBeNull();
                txtParam1!.Height.Should().BeGreaterOrEqualTo(32, "Input box must not truncate text vertically");
                txtParam1.VerticalContentAlignment.Should().Be(VerticalAlignment.Center);

                var txtParam2 = dlg.FindName("TxtParam2") as Wpf.Ui.Controls.TextBox;
                txtParam2.Should().NotBeNull();
                txtParam2!.Height.Should().BeGreaterOrEqualTo(32);

                var btnInsertAndCompile = dlg.FindName("BtnInsertAndCompile") as Wpf.Ui.Controls.Button;
                btnInsertAndCompile.Should().NotBeNull();
                btnInsertAndCompile!.Content.ToString().Should().Contain("Biên dịch");

                var btnInsert = dlg.FindName("BtnInsert") as Wpf.Ui.Controls.Button;
                btnInsert.Should().NotBeNull();

                dlg.AutoCompileRequested.Should().BeFalse();

                dlg.Close();
            });
        }

        [Fact]
        public void TikzView_TemplateCategories_AreSeparatedFromPersonalBank_AndButtonsHaveAccentStyle()
        {
            RunOnSta(() =>
            {
                var view = new TikzView();
                view.Should().NotBeNull();

                var cmbCategory = GetControl<ComboBox>(view, "CmbTemplateCategory");
                cmbCategory.Should().NotBeNull();
                var items = cmbCategory.ItemsSource as System.Collections.IEnumerable;
                items.Should().NotBeNull();

                var list = items!.Cast<TikzTemplateCategory>().ToList();
                list.Count.Should().Be(5, "Category dropdown must strictly contain the 5 pedagogical curriculum categories");
                list.Should().NotContain(c => c.Id == "user_figures", "Personal figure bank must be separated from template category dropdown");

                var btnCompile = GetControl<Wpf.Ui.Controls.Button>(view, "BtnCompile");
                btnCompile.Should().NotBeNull();
                btnCompile.Style.Should().NotBeNull("Buttons must use AccentVibrantButtonStyle to prevent hover white-out");
            });
        }

        [Fact]
        public void TikzView_And_ShapeBuilderDialog_Support_BothLightAndDarkThemes_WithoutCrashing()
        {
            RunOnSta(() =>
            {
                // Verify TikzView instantiates cleanly on STA thread
                var view = new TikzView();
                view.Should().NotBeNull();

                var btnCompile = GetControl<Wpf.Ui.Controls.Button>(view, "BtnCompile");
                btnCompile.Should().NotBeNull();
                btnCompile.Style.Should().NotBeNull("Compile button must have vibrant style");

                // Verify TikzShapeBuilderDialog instantiates cleanly on STA thread
                var dlg = new TikzShapeBuilderDialog();
                dlg.Should().NotBeNull();
                var btnInsertAndCompile = dlg.FindName("BtnInsertAndCompile") as Wpf.Ui.Controls.Button;
                btnInsertAndCompile.Should().NotBeNull();
                btnInsertAndCompile!.Style.Should().NotBeNull();

                dlg.Close();
            });
        }

        [Fact]
        public void TikzView_TemplateFilter_HasSingleUnifiedSelector_AndCategoryIsCollapsed()
        {
            RunOnSta(() =>
            {
                var view = new TikzView();
                view.Should().NotBeNull();

                var cmbCategory = GetControl<ComboBox>(view, "CmbTemplateCategory");
                cmbCategory.Should().NotBeNull();
                cmbCategory.Visibility.Should().Be(Visibility.Collapsed, "Redundant category dropdown must be collapsed to prevent duplicate filtering");

                var cmbItem = GetControl<ComboBox>(view, "CmbTemplateItem");
                cmbItem.Should().NotBeNull();
                cmbItem.Visibility.Should().Be(Visibility.Visible);
                cmbItem.Width.Should().BeGreaterOrEqualTo(260);

                var cmbDiagram = GetControl<ComboBox>(view, "CmbDiagramType");
                cmbDiagram.Should().NotBeNull();

                // Changing DiagramType must automatically filter templates in CmbTemplateItem
                cmbDiagram.SelectedIndex = 3; // HinhKhongGian
                var solidItems = cmbItem.ItemsSource as System.Collections.IEnumerable;
                solidItems.Should().NotBeNull();
                var solidList = solidItems!.Cast<TikzTemplate>().ToList();
                solidList.Should().NotBeEmpty();
                solidList.Should().OnlyContain(t => t.CategoryId == "solid_3d");

                cmbDiagram.SelectedIndex = 2; // DoThi
                var graphItems = cmbItem.ItemsSource as System.Collections.IEnumerable;
                graphItems.Should().NotBeNull();
                var graphList = graphItems!.Cast<TikzTemplate>().ToList();
                graphList.Should().NotBeEmpty();
                graphList.Should().OnlyContain(t => t.CategoryId == "graphs");
            });
        }

        #endregion
    }
}
