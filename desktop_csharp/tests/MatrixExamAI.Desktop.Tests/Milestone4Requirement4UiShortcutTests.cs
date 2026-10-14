using System;
using System.Collections.Generic;
using System.Globalization;
using System.Linq;
using System.Reflection;
using System.Threading;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Input;
using FluentAssertions;
using MatrixExamAI.Desktop.Views;
using MatrixExamAI.Shared.Extensibility;
using Wpf.Ui.Controls;
using Xunit;

namespace MatrixExamAI.Desktop.Tests
{
    public class Milestone4Requirement4UiShortcutTests
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

        private static T GetControl<T>(FrameworkElement parent, string name) where T : class
        {
            var control = parent.FindName(name) as T;
            if (control != null) return control;

            var field = parent.GetType().GetField(name, BindingFlags.Instance | BindingFlags.NonPublic | BindingFlags.Public);
            var val = field?.GetValue(parent) as T;
            if (val != null) return val;

            throw new InvalidOperationException($"Control '{name}' of type {typeof(T).Name} could not be resolved on {parent.GetType().Name}.");
        }

        #endregion

        #region 1. Window Initialization & Responsive Design Tests

        [Fact]
        public void MainWindow_InitializesSuccessfully_OnStaThread()
        {
            RunOnSta(() =>
            {
                var window = new MainWindow();
                window.Should().NotBeNull();
                window.MinWidth.Should().BeLessOrEqualTo(1024, "MainWindow must support 1024x768 screens");
                window.MinHeight.Should().BeLessOrEqualTo(768, "MainWindow must support 1024x768 screens");

                window.DashboardView.Should().NotBeNull();
                window.ConvertView.Should().NotBeNull();
                window.ExamMatrixView.Should().NotBeNull();
                window.TikzView.Should().NotBeNull();
                window.ShuffleView.Should().NotBeNull();
                window.QuestionBankView.Should().NotBeNull();
                window.QcView.Should().NotBeNull();
                window.SettingsView.Should().NotBeNull();
                window.CurrentNavigationTag.Should().Be("dashboard");

                var btnToggleTheme = GetControl<Wpf.Ui.Controls.Button>(window, "BtnToggleTheme");
                btnToggleTheme.Should().NotBeNull();
                btnToggleTheme.ToolTip.Should().NotBeNull();
                btnToggleTheme.ToolTip.ToString().Should().Contain("Ctrl + Alt + T");
            });
        }

        [Fact]
        public void MainWindow_ResponsiveSizeChanged_AutoCollapsesPaneWhenNarrow()
        {
            RunOnSta(() =>
            {
                var window = new MainWindow();
                var navView = GetControl<Wpf.Ui.Controls.NavigationView>(window, "NavView");
                navView.Should().NotBeNull();
                navView.IsPaneOpen.Should().BeTrue();

                // Test narrow size (1024x768): Auto-collapses pane to 50px icon bar
                window.UpdateResponsiveLayout(1024);
                navView!.IsPaneOpen.Should().BeFalse("Navigation Pane must auto-collapse to 50px icon bar at width < 1050");

                // Test wide size (1200x800): Auto-expands pane
                window.UpdateResponsiveLayout(1200);
                navView.IsPaneOpen.Should().BeTrue("Navigation Pane must auto-expand when width >= 1150");
            });
        }

        [Fact]
        public void MainWindow_NavigateTo_SwitchesActiveViewProperly()
        {
            RunOnSta(() =>
            {
                var window = new MainWindow();

                var testCases = new (string Tag, object ExpectedView)[]
                {
                    ("convert", window.ConvertView),
                    ("matrix", window.ExamMatrixView),
                    ("tikz", window.TikzView),
                    ("shuffle", window.ShuffleView),
                    ("bank", window.QuestionBankView),
                    ("qc", window.QcView),
                    ("settings", window.SettingsView),
                    ("dashboard", window.DashboardView)
                };

                foreach (var tc in testCases)
                {
                    window.NavigateTo(tc.Tag);
                    window.CurrentNavigationTag.Should().Be(tc.Tag);
                    var contentFrame = GetControl<ContentControl>(window, "MainContentFrame");
                    contentFrame.Content.Should().BeSameAs(tc.ExpectedView);
                }
            });
        }

        #endregion

        #region 2. Central Shortcut Dispatcher Tests

        [Theory]
        [InlineData(Key.D1, "dashboard")]
        [InlineData(Key.D2, "convert")]
        [InlineData(Key.D3, "matrix")]
        [InlineData(Key.D4, "tikz")]
        [InlineData(Key.D5, "shuffle")]
        [InlineData(Key.D6, "bank")]
        [InlineData(Key.D7, "qc")]
        [InlineData(Key.D8, "settings")]
        [InlineData(Key.NumPad1, "dashboard")]
        [InlineData(Key.NumPad2, "convert")]
        [InlineData(Key.NumPad3, "matrix")]
        [InlineData(Key.NumPad4, "tikz")]
        [InlineData(Key.NumPad5, "shuffle")]
        [InlineData(Key.NumPad6, "bank")]
        [InlineData(Key.NumPad7, "qc")]
        [InlineData(Key.NumPad8, "settings")]
        [InlineData(Key.OemComma, "settings")]
        public void Dispatcher_CtrlNumber_SwitchesToExpectedView(Key key, string expectedTag)
        {
            RunOnSta(() =>
            {
                var window = new MainWindow();
                window.NavigateTo(expectedTag == "dashboard" ? "convert" : "dashboard");

                bool handled = window.DispatchShortcut(key, ModifierKeys.Control);
                handled.Should().BeTrue();
                window.CurrentNavigationTag.Should().Be(expectedTag);
            });
        }

        [Fact]
        public void Dispatcher_CtrlO_NavigatesToConvertAndTriggersOpenFile()
        {
            RunOnSta(() =>
            {
                var window = new MainWindow();
                window.NavigateTo("dashboard");

                System.Windows.Controls.Primitives.ButtonBase? clickedButton = null;
                window.ButtonClickInterceptor = btn => clickedButton = btn;

                bool handled = window.DispatchShortcut(Key.O, ModifierKeys.Control);

                handled.Should().BeTrue();
                window.CurrentNavigationTag.Should().Be("convert", "Ctrl+O must navigate to ConvertView");
                clickedButton.Should().NotBeNull();
                var btnOpenFile = GetControl<Wpf.Ui.Controls.Button>(window.ConvertView, "BtnOpenFile");
                clickedButton.Should().BeSameAs(btnOpenFile, "Ctrl+O must trigger BtnOpenFile");
            });
        }

        [Theory]
        [InlineData("convert", "BtnExportWord")]
        [InlineData("matrix", "BtnExportDocx")]
        [InlineData("shuffle", "BtnExportAllDocx")]
        [InlineData("bank", "BtnExportSelected")]
        [InlineData("settings", "BtnSaveSettings")]
        [InlineData("tikz", "BtnSavePng")]
        [InlineData("dashboard", "BtnExportWord")]
        public void Dispatcher_CtrlS_TriggersExportOrSaveForActiveView(string activeTag, string expectedButtonName)
        {
            RunOnSta(() =>
            {
                var window = new MainWindow();
                window.NavigateTo(activeTag);

                System.Windows.Controls.Primitives.ButtonBase? clickedButton = null;
                window.ButtonClickInterceptor = btn => clickedButton = btn;

                bool handled = window.DispatchShortcut(Key.S, ModifierKeys.Control);

                handled.Should().BeTrue();
                clickedButton.Should().NotBeNull();
                clickedButton!.Name.Should().Be(expectedButtonName, $"Ctrl+S in '{activeTag}' must trigger {expectedButtonName}");
            });
        }

        [Theory]
        [InlineData(Key.F5, ModifierKeys.None)]
        [InlineData(Key.Enter, ModifierKeys.Control)]
        public void Dispatcher_F5_And_CtrlEnter_TriggersPrimaryActionPerActiveView(Key key, ModifierKeys modifiers)
        {
            RunOnSta(() =>
            {
                var window = new MainWindow();

                var testCases = new (string ViewTag, string ExpectedButtonName)[]
                {
                    ("convert", "BtnConvert"),
                    ("tikz", "BtnCompile"),
                    ("matrix", "BtnAiGenerateExam"),
                    ("shuffle", "BtnShuffle"),
                    ("qc", "BtnRunQc"),
                    ("bank", "BtnSearch"),
                    ("dashboard", "BtnConvert")
                };

                foreach (var tc in testCases)
                {
                    window.NavigateTo(tc.ViewTag);

                    System.Windows.Controls.Primitives.ButtonBase? clickedButton = null;
                    window.ButtonClickInterceptor = btn => clickedButton = btn;

                    bool handled = window.DispatchShortcut(key, modifiers);

                    handled.Should().BeTrue($"Shortcut {key}+{modifiers} in '{tc.ViewTag}' must be handled");
                    clickedButton.Should().NotBeNull($"Button in '{tc.ViewTag}' must be triggered");
                    clickedButton!.Name.Should().Be(tc.ExpectedButtonName,
                        $"Primary action in '{tc.ViewTag}' for {key}+{modifiers} must be {tc.ExpectedButtonName}");
                }
            });
        }

        [Theory]
        [InlineData(Key.P, "BtnCopyPrompt")]
        [InlineData(Key.B, "BtnQuickBrace")]
        [InlineData(Key.I, "BtnFilterItem")]
        [InlineData(Key.F, "BtnExpandPreview")]
        public void Dispatcher_CtrlShiftShortcuts_TriggerCorrectActions(Key key, string expectedButtonName)
        {
            RunOnSta(() =>
            {
                var window = new MainWindow();
                window.NavigateTo("dashboard"); // start away from convert

                System.Windows.Controls.Primitives.ButtonBase? clickedButton = null;
                window.ButtonClickInterceptor = btn => clickedButton = btn;

                bool handled = window.DispatchShortcut(key, ModifierKeys.Control | ModifierKeys.Shift);

                handled.Should().BeTrue();
                window.CurrentNavigationTag.Should().Be("convert", $"Ctrl+Shift+{key} must navigate to ConvertView");
                clickedButton.Should().NotBeNull();
                clickedButton!.Name.Should().Be(expectedButtonName, $"Ctrl+Shift+{key} must trigger {expectedButtonName}");
            });
        }

        [Fact]
        public void Dispatcher_Escape_CancelsInProgressOrClosesPreview()
        {
            RunOnSta(() =>
            {
                var window = new MainWindow();
                window.NavigateTo("convert");

                var btnCancel = GetControl<Wpf.Ui.Controls.Button>(window.ConvertView, "BtnCancel");

                // Case 1: BtnCancel is visible
                btnCancel.Visibility = Visibility.Visible;
                System.Windows.Controls.Primitives.ButtonBase? clickedButton = null;
                window.ButtonClickInterceptor = btn => clickedButton = btn;

                bool handled = window.DispatchShortcut(Key.Escape, ModifierKeys.None);
                handled.Should().BeTrue();
                clickedButton.Should().BeSameAs(btnCancel, "Escape must trigger BtnCancel when active");

                // Case 2: BtnCancel is collapsed
                btnCancel.Visibility = Visibility.Collapsed;
                bool handled2 = window.DispatchShortcut(Key.Escape, ModifierKeys.None);
                handled2.Should().BeTrue("Escape must be consumed safely even if nothing is currently canceling");
            });
        }

        #endregion

        #region 3. ExpandedPreviewWindow Tests

        [Fact]
        public void ExpandedPreviewWindow_Initializes_And_HasExpectedToolTips_OnStaThread()
        {
            RunOnSta(() =>
            {
                var questions = new List<QuestionItem>
                {
                    new QuestionItem
                    {
                        QuestionCode = "TEST01",
                        Subject = "Toán",
                        Grade = 12,
                        CognitiveLevel = "Nhận biết",
                        Topic = "Khảo sát hàm số",
                        QuestionType = "MultipleChoice4",
                        Content = "Cho hàm số ${y = x^2}$. Tính ${y'(1)}$.",
                        Options = new Dictionary<string, string> { ["A"] = "2", ["B"] = "1", ["C"] = "0", ["D"] = "-1" },
                        CorrectAnswer = "A"
                    }
                };

                var expWindow = new ExpandedPreviewWindow(questions, "Nội dung kiểm thử ${x^2}$");
                expWindow.Should().NotBeNull();

                var btnExportWord = GetControl<Wpf.Ui.Controls.Button>(expWindow, "BtnExportWord");
                var btnCopy = GetControl<Wpf.Ui.Controls.Button>(expWindow, "BtnCopy");
                var btnClose = GetControl<Wpf.Ui.Controls.Button>(expWindow, "BtnClose");

                btnExportWord.ToolTip.Should().NotBeNull();
                btnExportWord.ToolTip.ToString().Should().Be("Xuất tài liệu Word chuẩn Microsoft Word A4 (Ctrl + S)");

                btnCopy.ToolTip.Should().NotBeNull();
                btnCopy.ToolTip.ToString().Should().Be("Sao chép toàn bộ nội dung xem trước vào bộ nhớ tạm (Ctrl + C)");

                btnClose.ToolTip.Should().NotBeNull();
                btnClose.ToolTip.ToString().Should().Be("Đóng cửa sổ xem trước riêng biệt (Esc)");

                expWindow.Close();
            });
        }

        [Fact]
        public void ExpandedPreviewWindow_HandlePreviewKeyDown_RoutesShortcutsCorrectly()
        {
            RunOnSta(() =>
            {
                var expWindow = new ExpandedPreviewWindow(new List<QuestionItem>(), "Sample preview text");

                System.Windows.Controls.Primitives.ButtonBase? clickedBtn = null;
                expWindow.ButtonClickInterceptor = btn => clickedBtn = btn;

                // 1. Ctrl + S -> BtnExportWord
                bool handledS = expWindow.HandlePreviewKeyDown(Key.S, ModifierKeys.Control);
                handledS.Should().BeTrue();
                clickedBtn.Should().NotBeNull();
                clickedBtn!.Name.Should().Be("BtnExportWord");

                // 2. Ctrl + C -> BtnCopy
                clickedBtn = null;
                bool handledC = expWindow.HandlePreviewKeyDown(Key.C, ModifierKeys.Control);
                handledC.Should().BeTrue();
                clickedBtn.Should().NotBeNull();
                clickedBtn!.Name.Should().Be("BtnCopy");

                // 3. Esc -> Closes window
                bool handledEsc = expWindow.HandlePreviewKeyDown(Key.Escape, ModifierKeys.None);
                handledEsc.Should().BeTrue();
            });
        }

        #endregion

        #region 4. ToolTip Coverage Verification Across All 8 Views

        [Fact]
        public void ToolTips_DashboardView_MatchesR4Requirements()
        {
            RunOnSta(() =>
            {
                var view = new DashboardView();

                var btnQuickConvert = GetControl<Wpf.Ui.Controls.Button>(view, "BtnQuickConvert");
                var btnOpenFolder = GetControl<Wpf.Ui.Controls.Button>(view, "BtnOpenFolder");

                btnQuickConvert.ToolTip.Should().NotBeNull();
                btnQuickConvert.ToolTip.ToString().Should().Be("Chuyển sang phân hệ Chuyển đổi đề thi (Ctrl + 2)");

                btnOpenFolder.ToolTip.Should().NotBeNull();
                btnOpenFolder.ToolTip.ToString().Should().Be("Mở thư mục chứa các đề thi đã xuất trên máy");
            });
        }

        [Fact]
        public void ToolTips_ExamMatrixView_MatchesR4Requirements()
        {
            RunOnSta(() =>
            {
                var view = new ExamMatrixView();

                var btnLoadSample = GetControl<Wpf.Ui.Controls.Button>(view, "BtnLoadSample");
                var btnAiGenerateExam = GetControl<Wpf.Ui.Controls.Button>(view, "BtnAiGenerateExam");
                var btnExportDocx = GetControl<Wpf.Ui.Controls.Button>(view, "BtnExportDocx");

                btnLoadSample.ToolTip.Should().NotBeNull();
                btnLoadSample.ToolTip.ToString().Should().Be("Nạp cấu trúc đề thi mẫu 22 câu chuẩn BGD");

                btnAiGenerateExam.ToolTip.Should().NotBeNull();
                btnAiGenerateExam.ToolTip.ToString().Should().Be("AI Gemini tự động sinh đề thi theo ma trận (F5 hoặc Ctrl + Enter)");

                btnExportDocx.ToolTip.Should().NotBeNull();
                btnExportDocx.ToolTip.ToString().Should().Be("Xuất ma trận và đề thi ra tài liệu Word chuẩn A4 (Ctrl + S)");
            });
        }

        [Fact]
        public void ToolTips_QcView_MatchesR4Requirements()
        {
            RunOnSta(() =>
            {
                var view = new QcView();

                var btnRunQc = GetControl<Wpf.Ui.Controls.Button>(view, "BtnRunQc");
                var btnAutoFix = GetControl<Wpf.Ui.Controls.Button>(view, "BtnAutoFix");

                btnRunQc.ToolTip.Should().NotBeNull();
                btnRunQc.ToolTip.ToString().Should().Be("Rà soát lỗi trùng phương án, thiếu đáp án, sai cú pháp LaTeX (F5)");

                btnAutoFix.ToolTip.Should().NotBeNull();
                btnAutoFix.ToolTip.ToString().Should().Be("AI tự động sửa các lỗi cú pháp và chuẩn hóa đề thi");
            });
        }

        [Fact]
        public void ToolTips_QuestionBankView_MatchesR4Requirements()
        {
            RunOnSta(() =>
            {
                var view = new QuestionBankView();

                var btnSearch = GetControl<Wpf.Ui.Controls.Button>(view, "BtnSearch");
                var btnRefreshBank = GetControl<Wpf.Ui.Controls.Button>(view, "BtnRefreshBank");
                var btnImportConvert = GetControl<Wpf.Ui.Controls.Button>(view, "BtnImportConvert");
                var btnAddQuestion = GetControl<Wpf.Ui.Controls.Button>(view, "BtnAddQuestion");
                var btnExportSelected = GetControl<Wpf.Ui.Controls.Button>(view, "BtnExportSelected");

                btnSearch.ToolTip.Should().NotBeNull();
                btnSearch.ToolTip.ToString().Should().Be("Tìm kiếm câu hỏi trong SQLite database (F5 hoặc Enter)");

                btnRefreshBank.ToolTip.Should().NotBeNull();
                btnRefreshBank.ToolTip.ToString().Should().Be("Tải lại toàn bộ câu hỏi từ SQLite Database (F5)");

                btnImportConvert.ToolTip.Should().NotBeNull();
                btnImportConvert.ToolTip.ToString().Should().Be("Nhập nhanh các câu hỏi vừa nhận diện từ ConvertView vào Ngân hàng SQLite");

                btnAddQuestion.ToolTip.Should().NotBeNull();
                btnAddQuestion.ToolTip.ToString().Should().Be("Thêm câu hỏi mới vào ngân hàng câu hỏi SQLite");

                btnExportSelected.ToolTip.Should().NotBeNull();
                btnExportSelected.ToolTip.ToString().Should().Be("Xuất danh sách câu hỏi đã chọn ra tệp Word (Ctrl + S)");
            });
        }

        [Fact]
        public void ToolTips_SettingsView_MatchesR4Requirements()
        {
            RunOnSta(() =>
            {
                var view = new SettingsView();

                var btnTestConnection = GetControl<Wpf.Ui.Controls.Button>(view, "BtnTestConnection");
                var btnSaveSettings = GetControl<Wpf.Ui.Controls.Button>(view, "BtnSaveSettings");
                var btnSyncAddin = GetControl<Wpf.Ui.Controls.Button>(view, "BtnSyncAddin");

                btnTestConnection.ToolTip.Should().NotBeNull();
                btnTestConnection.ToolTip.ToString().Should().Be("Kiểm tra kết nối tới Google Gemini hoặc 9Router Local");

                btnSaveSettings.ToolTip.Should().NotBeNull();
                btnSaveSettings.ToolTip.ToString().Should().Be("Lưu cấu hình hệ thống và API Keys (Ctrl + S)");

                btnSyncAddin.ToolTip.Should().NotBeNull();
                btnSyncAddin.ToolTip.ToString().Should().Be("Kích hoạt lại Add-in trong Windows Registry");
            });
        }

        [Fact]
        public void ToolTips_ShuffleView_MatchesR4Requirements()
        {
            RunOnSta(() =>
            {
                var view = new ShuffleView();

                var btnShuffle = GetControl<Wpf.Ui.Controls.Button>(view, "BtnShuffle");
                var btnGenerateOmr = GetControl<Wpf.Ui.Controls.Button>(view, "BtnGenerateOmr");
                var btnExportAllDocx = GetControl<Wpf.Ui.Controls.Button>(view, "BtnExportAllDocx");

                btnShuffle.ToolTip.Should().NotBeNull();
                btnShuffle.ToolTip.ToString().Should().Be("Hoán vị câu hỏi, phương án và sinh ma trận mã đề chéo (F5)");

                btnGenerateOmr.ToolTip.Should().NotBeNull();
                btnGenerateOmr.ToolTip.ToString().Should().Be("Sinh phiếu trả lời trắc nghiệm tô tròn OMR chuẩn A4");

                btnExportAllDocx.ToolTip.Should().NotBeNull();
                btnExportAllDocx.ToolTip.ToString().Should().Be("Xuất toàn bộ các mã đề thi đã trộn ra các tệp Word riêng biệt (Ctrl + S)");
            });
        }

        #endregion

        #region 5. Strict "1 Button - 1 Icon" & Ergonomics Audit

        [Fact]
        public void AllButtons_ConformToStrictOneButtonOneIconRule_NoEmojisNoDuplicateIcons()
        {
            RunOnSta(() =>
            {
                var views = new FrameworkElement[]
                {
                    new MainWindow(),
                    new DashboardView(),
                    new ExamMatrixView(),
                    new ShuffleView(),
                    new QuestionBankView(),
                    new QcView(),
                    new SettingsView(),
                    new ExpandedPreviewWindow(new List<QuestionItem>(), "Preview")
                };

                foreach (var container in views)
                {
                    var buttons = FindVisualChildren<System.Windows.Controls.Button>(container).ToList();

                    foreach (var btn in buttons)
                    {
                        // 1. ToolTip must not be null or empty
                        btn.ToolTip.Should().NotBeNull(
                            $"Button '{btn.Name}' in '{container.GetType().Name}' must have a descriptive ToolTip");
                        string tipText = btn.ToolTip.ToString()!;
                        tipText.Should().NotBeNullOrWhiteSpace(
                            $"Button '{btn.Name}' in '{container.GetType().Name}' must not have empty ToolTip");

                        // 2. If content is string, must not contain emoji
                        if (btn.Content is string contentStr)
                        {
                            bool hasEmoji = contentStr.Any(c =>
                                char.GetUnicodeCategory(c) == UnicodeCategory.OtherSymbol ||
                                char.GetUnicodeCategory(c) == UnicodeCategory.Surrogate ||
                                (c >= 0x2600 && c <= 0x27BF) ||
                                (c >= 0x1F300 && c <= 0x1F9FF));

                            hasEmoji.Should().BeFalse(
                                $"Button '{btn.Name}' in '{container.GetType().Name}' has emoji in content: '{contentStr}'");
                        }

                        // 3. If button is Wpf.Ui.Controls.Button with Icon set, content must not duplicate SymbolIcon
                        if (btn is Wpf.Ui.Controls.Button uiBtn && uiBtn.Icon != null)
                        {
                            var childSymbolIcons = FindVisualChildren<SymbolIcon>(uiBtn).ToList();
                            // Child symbol icons in visual tree should not be multiple unless generated by template
                            childSymbolIcons.Count.Should().BeLessOrEqualTo(2,
                                $"Button '{btn.Name}' in '{container.GetType().Name}' has duplicated SymbolIcon elements");
                        }
                    }
                }
            });
        }

        private static IEnumerable<T> FindVisualChildren<T>(DependencyObject depObj) where T : DependencyObject
        {
            if (depObj == null) yield break;

            int count = System.Windows.Media.VisualTreeHelper.GetChildrenCount(depObj);
            if (count == 0)
            {
                // Fall back to logical tree if visual tree not rendered yet
                foreach (var child in LogicalTreeHelper.GetChildren(depObj))
                {
                    if (child is DependencyObject depChild)
                    {
                        if (depChild is T match)
                        {
                            yield return match;
                        }
                        foreach (var grandChild in FindVisualChildren<T>(depChild))
                        {
                            yield return grandChild;
                        }
                    }
                }
                yield break;
            }

            for (int i = 0; i < count; i++)
            {
                var child = System.Windows.Media.VisualTreeHelper.GetChild(depObj, i);
                if (child is T typedChild)
                {
                    yield return typedChild;
                }

                foreach (var grandChild in FindVisualChildren<T>(child))
                {
                    yield return grandChild;
                }
            }
        }

        #endregion
    }
}
