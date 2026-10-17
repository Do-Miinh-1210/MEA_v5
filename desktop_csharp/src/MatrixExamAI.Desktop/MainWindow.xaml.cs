using System;
using System.Windows;
using System.Windows.Input;
using Wpf.Ui.Appearance;
using Wpf.Ui.Controls;
using MatrixExamAI.Desktop.Views;
using MatrixExamAI.Desktop.Services;

namespace MatrixExamAI.Desktop
{
    public partial class MainWindow : FluentWindow
    {
        private readonly DashboardView _dashboardView;
        private readonly ConvertView _convertView;
        private readonly TikzView _tikzView;
        private readonly ExamMatrixView _examMatrixView;
        private readonly ShuffleView _shuffleView;
        private readonly QuestionBankView _questionBankView;
        private readonly QcView _qcView;
        private readonly AiUsageView _aiUsageView;
        private readonly SettingsView _settingsView;

        public DashboardView DashboardView => _dashboardView;
        public ConvertView ConvertView => _convertView;
        public TikzView TikzView => _tikzView;
        public ExamMatrixView ExamMatrixView => _examMatrixView;
        public ShuffleView ShuffleView => _shuffleView;
        public QuestionBankView QuestionBankView => _questionBankView;
        public QcView QcView => _qcView;
        public AiUsageView AiUsageView => _aiUsageView;
        public SettingsView SettingsView => _settingsView;
        public string CurrentNavigationTag { get; private set; } = "dashboard";

        public Action<System.Windows.Controls.Primitives.ButtonBase>? ButtonClickInterceptor { get; set; }
        private UpdateInfo? _pendingUpdateInfo;

        public MainWindow()
        {
            InitializeComponent();

            _dashboardView = new DashboardView();
            _convertView = new ConvertView();
            _tikzView = new TikzView();
            _examMatrixView = new ExamMatrixView();
            _shuffleView = new ShuffleView();
            _questionBankView = new QuestionBankView();
            _qcView = new QcView();
            _aiUsageView = new AiUsageView();
            _settingsView = new SettingsView();

            // Kết nối nạp đề đang soạn từ ConvertView sang phân hệ Trộn đề
            _shuffleView.RequestLoadDraftFromConvert = () => _convertView.TxtInput.Text;

            // Lắng nghe sự kiện điều hướng từ các nút trên Dashboard
            _dashboardView.RequestNavigateToConvert += (s, e) => NavigateTo("convert");
            _dashboardView.RequestNavigateToTikz += (s, e) => NavigateTo("tikz");

            // Tự động thu gọn thanh menu khi màn hình hẹp (Split Screen / Snap)
            SizeChanged += MainWindow_SizeChanged;

            // Đồng bộ trạng thái Bản quyền trực tuyến
            UpdateStatusBarLicense(SupabaseLicenseService.Instance.GetCurrentLicense());
            SupabaseLicenseService.Instance.LicenseChanged += (s, info) => Dispatcher.Invoke(() => UpdateStatusBarLicense(info));
            _ = Task.Run(async () => await SupabaseLicenseService.Instance.CheckLicenseAsync(forceOnline: false));

            // Kiểm tra cập nhật tự động khi khởi động
            _ = Task.Run(async () => await CheckForUpdateSilentlyOnStartupAsync());

            // Hiển thị số hiệu phiên bản trên TitleBar và StatusBar
            string verText = $"v{GitHubUpdateService.Instance.CurrentVersion}";
            TxtAppVersionTop.Text = verText;
            TxtAppVersionBottom.Text = verText;
            Title = $"MatrixExamAI Pro {verText} • Trợ lý Soạn đề & Chuyển đổi Tài liệu AI";
            MainTitleBar.Title = $"MatrixExamAI Pro {verText} • Trợ lý Soạn đề & Chuyển đổi Tài liệu AI";

            // Mặc định khởi tạo: mở trang Tổng quan Dashboard
            NavigateTo("dashboard");
        }

        public void UpdateResponsiveLayout(double windowWidth)
        {
            if (windowWidth < 1050)
            {
                if (NavView.IsPaneOpen)
                {
                    NavView.IsPaneOpen = false; // Thu gọn thành icon (50px) để dành chỗ cho nội dung
                }
            }
            else if (windowWidth >= 1150)
            {
                if (!NavView.IsPaneOpen)
                {
                    NavView.IsPaneOpen = true; // Tự động mở rộng khi cửa sổ đủ rộng
                }
            }
        }

        private void MainWindow_SizeChanged(object sender, SizeChangedEventArgs e)
        {
            UpdateResponsiveLayout(e.NewSize.Width);
        }

        private void BtnTogglePane_Click(object sender, RoutedEventArgs e)
        {
            NavView.IsPaneOpen = !NavView.IsPaneOpen;
        }

        private void SetActiveItem(NavigationViewItem activeItem)
        {
            NavItemDashboard.IsActive = (NavItemDashboard == activeItem);
            NavItemConvert.IsActive = (NavItemConvert == activeItem);
            NavItemMatrix.IsActive = (NavItemMatrix == activeItem);
            NavItemTikz.IsActive = (NavItemTikz == activeItem);
            NavItemShuffle.IsActive = (NavItemShuffle == activeItem);
            NavItemBank.IsActive = (NavItemBank == activeItem);
            NavItemAiUsage.IsActive = (NavItemAiUsage == activeItem);
            NavItemQc.IsActive = (NavItemQc == activeItem);
            NavItemSettings.IsActive = (NavItemSettings == activeItem);
        }

        public void NavigateTo(string tag)
        {
            CurrentNavigationTag = tag.ToLowerInvariant();
            switch (CurrentNavigationTag)
            {
                case "dashboard":
                    MainContentFrame.Content = _dashboardView;
                    SetActiveItem(NavItemDashboard);
                    break;
                case "convert":
                    MainContentFrame.Content = _convertView;
                    SetActiveItem(NavItemConvert);
                    break;
                case "matrix":
                    MainContentFrame.Content = _examMatrixView;
                    SetActiveItem(NavItemMatrix);
                    break;
                case "tikz":
                    MainContentFrame.Content = _tikzView;
                    SetActiveItem(NavItemTikz);
                    break;
                case "shuffle":
                    MainContentFrame.Content = _shuffleView;
                    SetActiveItem(NavItemShuffle);
                    break;
                case "bank":
                    MainContentFrame.Content = _questionBankView;
                    SetActiveItem(NavItemBank);
                    break;
                case "ai_usage":
                    MainContentFrame.Content = _aiUsageView;
                    SetActiveItem(NavItemAiUsage);
                    _aiUsageView.RefreshData();
                    break;
                case "qc":
                    MainContentFrame.Content = _qcView;
                    SetActiveItem(NavItemQc);
                    break;
                case "settings":
                    MainContentFrame.Content = _settingsView;
                    SetActiveItem(NavItemSettings);
                    break;
            }
        }

        private void BtnQuickGen_Click(object sender, RoutedEventArgs e)
        {
            var dlg = new QuickGenDialog
            {
                Owner = this
            };

            if (dlg.ShowDialog() == true && !string.IsNullOrWhiteSpace(dlg.GeneratedExamPrompt))
            {
                NavigateTo("convert");
                _convertView.TxtInput.Text = dlg.GeneratedExamPrompt;
                _convertView.TriggerConvertWithAi();
            }
        }

        private void BtnAiMatrix_Click(object sender, RoutedEventArgs e)
        {
            var dlg = new AiMatrixDialog
            {
                Owner = this
            };

            if (dlg.ShowDialog() == true)
            {
                NavigateTo("matrix");
                _examMatrixView.ApplyAiMatrixConfig(dlg.Subject, dlg.Grade, dlg.Duration, dlg.Semester, dlg.ExtraRequirements);
            }
        }

        private void BtnSmartPrompt_Click(object sender, RoutedEventArgs e)
        {
            var dlg = new SmartPromptDialog
            {
                Owner = this
            };

            if (dlg.ShowDialog() == true)
            {
                if (dlg.GeneratedMatrixConfig != null)
                {
                    NavigateTo("matrix");
                    _examMatrixView.ApplyAiMatrixConfig(
                        dlg.GeneratedMatrixConfig.Subject,
                        dlg.GeneratedMatrixConfig.Grade,
                        dlg.GeneratedMatrixConfig.Duration,
                        dlg.GeneratedMatrixConfig.Semester,
                        dlg.GeneratedMatrixConfig.ExtraRequirements
                    );
                }
                else if (!string.IsNullOrWhiteSpace(dlg.GeneratedQuestionLatex))
                {
                    NavigateTo("convert");
                    _convertView.InsertQuestionContent(dlg.GeneratedQuestionLatex);
                }
            }
        }

        private void BtnChooseSource_Click(object sender, RoutedEventArgs e)
        {
            var dlg = new SourceMethodDialog
            {
                Owner = this
            };

            if (dlg.ShowDialog() == true)
            {
                if (dlg.SelectedMode == "bank_only")
                {
                    NavigateTo("bank");
                }
                else if (dlg.SelectedMode == "mixed")
                {
                    NavigateTo("matrix");
                    System.Windows.MessageBox.Show($"Đã chọn phương thức: Kết hợp ({dlg.BankRatio}% từ Ngân hàng câu hỏi, {100 - dlg.BankRatio}% tạo bằng AI).", "Nguồn tạo đề", System.Windows.MessageBoxButton.OK, System.Windows.MessageBoxImage.Information);
                }
                else
                {
                    NavigateTo("convert");
                }
            }
        }

        private void BtnGuide_Click(object sender, RoutedEventArgs e)
        {
            var dlg = new QuickGuideDialog
            {
                Owner = this
            };
            dlg.ShowDialog();
        }

        private void BtnAiGen_Click(object sender, RoutedEventArgs e)
        {
            if (CurrentNavigationTag == "matrix")
            {
                _examMatrixView.GenerateExamWithAi();
            }
            else
            {
                NavigateTo("convert");
                _convertView.TriggerConvertWithAi();
            }
        }

        private void BtnQuickShuffle_Click(object sender, RoutedEventArgs e)
        {
            NavigateTo("shuffle");
        }

        private void NavItem_Click(object sender, RoutedEventArgs e)
        {
            if (sender is NavigationViewItem item && item.Tag is string tag)
            {
                NavigateTo(tag);
            }
        }

        private void NavView_SelectionChanged(NavigationView sender, RoutedEventArgs args)
        {
            if (sender.SelectedItem is NavigationViewItem selectedItem && selectedItem.Tag is string tag)
            {
                NavigateTo(tag);
            }
        }

        private void BtnToggleTheme_Click(object sender, RoutedEventArgs e)
        {
            var currentTheme = ApplicationThemeManager.GetAppTheme();
            if (currentTheme == ApplicationTheme.Dark)
            {
                ApplicationThemeManager.Apply(ApplicationTheme.Light);
            }
            else
            {
                ApplicationThemeManager.Apply(ApplicationTheme.Dark);
            }
        }

        private async void BtnCheckUpdate_Click(object sender, RoutedEventArgs e)
        {
            await CheckForUpdateAndPromptAsync(showPromptIfLatest: true);
        }

        private async System.Threading.Tasks.Task CheckForUpdateSilentlyOnStartupAsync()
        {
            try
            {
                var info = await GitHubUpdateService.Instance.CheckForUpdateAsync();
                if (info != null)
                {
                    Dispatcher.Invoke(() =>
                    {
                        _pendingUpdateInfo = info;
                        TxtUpdateNoticeTitle.Text = $"Đã có bản cập nhật mới: v{info.Version}";
                        TxtUpdateNoticeMessage.Text = $"Phiên bản {info.Version} ({info.AssetName}) đã sẵn sàng tải về. Nhấn nút bên cạnh để cập nhật ngay.";
                        BorderUpdateNotice.Visibility = Visibility.Visible;
                    });
                }
            }
            catch
            {
                // Khởi động không gây gián đoạn nếu mất kết nối mạng
            }
        }

        private void BtnCloseUpdateNotice_Click(object sender, RoutedEventArgs e)
        {
            BorderUpdateNotice.Visibility = Visibility.Collapsed;
        }

        private void BtnUpdateNoticeAction_Click(object sender, RoutedEventArgs e)
        {
            if (_pendingUpdateInfo != null)
            {
                var dialog = new UpdateDialog(_pendingUpdateInfo) { Owner = this };
                dialog.ShowDialog();
            }
            else
            {
                _ = CheckForUpdateAndPromptAsync(showPromptIfLatest: true);
            }
        }

        public async System.Threading.Tasks.Task CheckForUpdateAndPromptAsync(bool showPromptIfLatest)
        {
            try
            {
                var info = await GitHubUpdateService.Instance.CheckForUpdateAsync();
                if (info != null)
                {
                    _pendingUpdateInfo = info;
                    TxtUpdateNoticeTitle.Text = $"Đã có bản cập nhật mới: v{info.Version}";
                    TxtUpdateNoticeMessage.Text = $"Phiên bản {info.Version} ({info.AssetName}) đã sẵn sàng tải về. Nhấn nút bên cạnh để cập nhật ngay.";
                    BorderUpdateNotice.Visibility = Visibility.Visible;

                    var dialog = new UpdateDialog(info) { Owner = this };
                    dialog.ShowDialog();
                }
                else if (showPromptIfLatest)
                {
                    System.Windows.MessageBox.Show(
                        $"Bạn đang sử dụng phiên bản mới nhất: v{GitHubUpdateService.Instance.CurrentVersion}.\nKhông có bản cập nhật mới trên máy chủ.",
                        "Kiểm tra cập nhật",
                        System.Windows.MessageBoxButton.OK,
                        MessageBoxImage.Information
                    );
                }
            }
            catch (Exception ex)
            {
                if (showPromptIfLatest)
                {
                    System.Windows.MessageBox.Show(
                        $"Không thể kiểm tra cập nhật:\n{ex.Message}",
                        "Lỗi kết nối",
                        System.Windows.MessageBoxButton.OK,
                        MessageBoxImage.Warning
                    );
                }
            }
        }

        private void TriggerButtonClick(System.Windows.Controls.Primitives.ButtonBase? button)
        {
            if (button == null || !button.IsEnabled) return;
            if (ButtonClickInterceptor != null)
            {
                ButtonClickInterceptor(button);
                return;
            }
            button.RaiseEvent(new RoutedEventArgs(System.Windows.Controls.Primitives.ButtonBase.ClickEvent));
        }

        public bool DispatchShortcut(Key key, ModifierKeys modifiers)
        {
            var isCtrl = (modifiers & ModifierKeys.Control) == ModifierKeys.Control;
            var isAlt = (modifiers & ModifierKeys.Alt) == ModifierKeys.Alt;
            var isShift = (modifiers & ModifierKeys.Shift) == ModifierKeys.Shift;

            // 1. Ctrl + Alt + T: Đổi theme Sáng / Tối
            if (isCtrl && isAlt && !isShift && key == Key.T)
            {
                BtnToggleTheme_Click(this, new RoutedEventArgs());
                return true;
            }

            // 2. Ctrl + 1..8: Chuyển phân hệ nhanh
            if (isCtrl && !isAlt && !isShift)
            {
                switch (key)
                {
                    case Key.D1:
                    case Key.NumPad1:
                        NavigateTo("dashboard");
                        return true;
                    case Key.D2:
                    case Key.NumPad2:
                        NavigateTo("convert");
                        return true;
                    case Key.D3:
                    case Key.NumPad3:
                        NavigateTo("matrix");
                        return true;
                    case Key.D4:
                    case Key.NumPad4:
                        NavigateTo("tikz");
                        return true;
                    case Key.D5:
                    case Key.NumPad5:
                        NavigateTo("shuffle");
                        return true;
                    case Key.D6:
                    case Key.NumPad6:
                        NavigateTo("bank");
                        return true;
                    case Key.D7:
                    case Key.NumPad7:
                        NavigateTo("qc");
                        return true;
                    case Key.D8:
                    case Key.NumPad8:
                    case Key.OemComma:
                        NavigateTo("settings");
                        return true;
                    case Key.D9:
                    case Key.NumPad9:
                        NavigateTo("ai_usage");
                        return true;
                }
            }

            // 3. Ctrl + O: Navigate to ConvertView and trigger open file dialog
            if (isCtrl && !isAlt && !isShift && key == Key.O)
            {
                NavigateTo("convert");
                TriggerButtonClick(_convertView.BtnOpenFile);
                return true;
            }

            // 4. Ctrl + S: Trigger export Word or save settings for active view
            if (isCtrl && !isAlt && !isShift && key == Key.S)
            {
                switch (CurrentNavigationTag)
                {
                    case "convert":
                        TriggerButtonClick(_convertView.BtnExportWord);
                        return true;
                    case "matrix":
                        TriggerButtonClick(_examMatrixView.BtnExportDocx);
                        return true;
                    case "shuffle":
                        TriggerButtonClick(_shuffleView.BtnExportAllDocx);
                        return true;
                    case "bank":
                        TriggerButtonClick(_questionBankView.BtnExportSelected);
                        return true;
                    case "settings":
                        TriggerButtonClick(_settingsView.BtnSaveSettings);
                        return true;
                    case "tikz":
                        TriggerButtonClick(_tikzView.BtnSavePng);
                        return true;
                    default:
                        NavigateTo("convert");
                        TriggerButtonClick(_convertView.BtnExportWord);
                        return true;
                }
            }

            // 5. F5 / Ctrl + Enter: Trigger primary action of active view
            bool isF5 = !isCtrl && !isAlt && !isShift && key == Key.F5;
            bool isCtrlEnter = isCtrl && !isAlt && !isShift && (key == Key.Enter || key == Key.Return);
            if (isF5 || isCtrlEnter)
            {
                switch (CurrentNavigationTag)
                {
                    case "convert":
                        TriggerButtonClick(_convertView.BtnConvert);
                        return true;
                    case "tikz":
                        TriggerButtonClick(_tikzView.BtnCompile);
                        return true;
                    case "matrix":
                        TriggerButtonClick(_examMatrixView.BtnAiGenerateExam);
                        return true;
                    case "shuffle":
                        TriggerButtonClick(_shuffleView.BtnShuffle);
                        return true;
                    case "qc":
                        TriggerButtonClick(_qcView.BtnRunQc);
                        return true;
                    case "bank":
                        TriggerButtonClick(_questionBankView.BtnSearch);
                        return true;
                    case "dashboard":
                        NavigateTo("convert");
                        TriggerButtonClick(_convertView.BtnConvert);
                        return true;
                    default:
                        return false;
                }
            }

            // 6. Ctrl + Shift + P: Navigate to ConvertView and trigger BtnCopyPrompt
            if (isCtrl && isShift && !isAlt && key == Key.P)
            {
                NavigateTo("convert");
                TriggerButtonClick(_convertView.BtnCopyPrompt);
                return true;
            }

            // 7. Ctrl + Shift + B: Navigate to ConvertView and trigger BtnQuickBrace
            if (isCtrl && isShift && !isAlt && key == Key.B)
            {
                NavigateTo("convert");
                TriggerButtonClick(_convertView.BtnQuickBrace);
                return true;
            }

            // 8. Ctrl + Shift + I: Navigate to ConvertView and trigger BtnFilterItem
            if (isCtrl && isShift && !isAlt && key == Key.I)
            {
                NavigateTo("convert");
                TriggerButtonClick(_convertView.BtnFilterItem);
                return true;
            }

            // 9. Ctrl + Shift + F: Trigger BtnExpandPreview
            if (isCtrl && isShift && !isAlt && key == Key.F)
            {
                if (CurrentNavigationTag != "convert")
                {
                    NavigateTo("convert");
                }
                TriggerButtonClick(_convertView.BtnExpandPreview);
                return true;
            }

            // 10. Esc: Close active floating preview or cancel
            if (!isCtrl && !isAlt && !isShift && key == Key.Escape)
            {
                bool closedFloating = false;
                if (Application.Current != null)
                {
                    foreach (Window win in Application.Current.Windows)
                    {
                        if (win is ExpandedPreviewWindow expWin && expWin.IsVisible)
                        {
                            expWin.Close();
                            closedFloating = true;
                            break;
                        }
                    }
                }
                if (closedFloating) return true;

                if (CurrentNavigationTag == "convert" && _convertView.BtnCancel.Visibility == Visibility.Visible)
                {
                    TriggerButtonClick(_convertView.BtnCancel);
                    return true;
                }
                return true;
            }

            // 11. F10 or Ctrl + [: Toggle Source/Code panel in ConvertView and TikzView
            if ((!isCtrl && !isAlt && !isShift && key == Key.F10) || (isCtrl && !isAlt && !isShift && key == Key.OemOpenBrackets))
            {
                if (CurrentNavigationTag == "convert")
                {
                    _convertView.ToggleSourcePanel();
                    return true;
                }
                if (CurrentNavigationTag == "tikz")
                {
                    _tikzView.ToggleCodePanel();
                    return true;
                }
            }

            // 12. Ctrl + H: Open Quick Guide
            if (isCtrl && !isAlt && !isShift && key == Key.H)
            {
                TriggerButtonClick(BtnGuide);
                return true;
            }

            return false;
        }

        private void MainWindow_PreviewKeyDown(object sender, KeyEventArgs e)
        {
            var key = e.Key == Key.System ? e.SystemKey : e.Key;
            if (DispatchShortcut(key, Keyboard.Modifiers))
            {
                e.Handled = true;
            }
        }

        private void UpdateStatusBarLicense(LicenseInfo info)
        {
            if (TxtStatusBarLicense == null) return;
            string owner = string.IsNullOrWhiteSpace(info.Name) ? "Giáo viên MEA" : info.Name;
            if (owner.Length > 24) owner = owner[..22] + "...";
            TxtStatusBarLicense.Text = $"Bản quyền: {owner} ({info.DisplayTier})";
            try
            {
                var brush = new System.Windows.Media.SolidColorBrush((System.Windows.Media.Color)System.Windows.Media.ColorConverter.ConvertFromString(info.BadgeColor));
                TxtStatusBarLicense.Foreground = brush;
            }
            catch { }
        }

        private void TxtStatusBarLicense_MouseLeftButtonDown(object sender, MouseButtonEventArgs e)
        {
            var dlg = new ActivationDialog { Owner = this };
            dlg.ShowDialog();
        }
    }
}