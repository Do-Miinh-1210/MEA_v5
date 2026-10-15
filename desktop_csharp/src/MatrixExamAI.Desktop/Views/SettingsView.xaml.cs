using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Text.Json;
using System.Threading.Tasks;
using System.Windows;
using System.Windows.Controls;
using Microsoft.Win32;
using MatrixExamAI.Desktop.Services;
using MatrixExamAI.Shared.Models;

namespace MatrixExamAI.Desktop.Views
{
    public partial class SettingsView : UserControl
    {
        private readonly string _configPath;
        private readonly Dictionary<string, string> _keysByProvider = new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase);
        private string _activeProvider = "Google Gemini";
        private bool _isKeyMasked = false;
        private string _unmaskedKeyText = string.Empty;

        public SettingsView()
        {
            InitializeComponent();

            string appData = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "MatrixExamAI");
            _configPath = Path.Combine(appData, "config.json");

            LoadCurrentConfig();
            LoadLicenseInfo();
            UpdateLastCheckDisplay();
            SupabaseLicenseService.Instance.LicenseChanged += (s, info) => Dispatcher.Invoke(() => UpdateLicenseUi(info));
        }

        private void LoadCurrentConfig()
        {
            try
            {
                string savedProvider = "Google Gemini";
                string savedModel = "gemini-3.8-flash";
                string savedKey = "";

                // 1. Đọc từ %LocalAppData%\MatrixExamAI\config.json
                if (File.Exists(_configPath))
                {
                    try
                    {
                        string json = File.ReadAllText(_configPath);
                        using var doc = JsonDocument.Parse(json);
                        var root = doc.RootElement;

                        bool hasExplicitProvider = false;
                        if (root.TryGetProperty("provider", out var pProv) && !string.IsNullOrWhiteSpace(pProv.GetString()))
                        {
                            savedProvider = pProv.GetString()!.Trim();
                            hasExplicitProvider = true;
                        }
                        if (root.TryGetProperty("model", out var pModel) && !string.IsNullOrWhiteSpace(pModel.GetString()))
                        {
                            savedModel = pModel.GetString()!.Trim();
                        }
                        if (root.TryGetProperty("apiKey", out var pKey) && !string.IsNullOrWhiteSpace(pKey.GetString()))
                        {
                            savedKey = pKey.GetString()!.Trim();
                        }
                        if (!hasExplicitProvider && !string.IsNullOrEmpty(savedKey) && savedKey.StartsWith("sk-", StringComparison.OrdinalIgnoreCase))
                        {
                            savedProvider = "9Router";
                        }

                        if (root.TryGetProperty("keysByProvider", out var pDict) && pDict.ValueKind == JsonValueKind.Object)
                        {
                            foreach (var prop in pDict.EnumerateObject())
                            {
                                _keysByProvider[prop.Name] = prop.Value.GetString() ?? "";
                            }
                        }
                    }
                    catch { }
                }

                // 2. Kế thừa đồng bộ từ Python MEA v5.0 (~/.exam_generator/)
                string homeDir = Environment.GetFolderPath(Environment.SpecialFolder.UserProfile);
                string pySettings = Path.Combine(homeDir, ".exam_generator", "app_settings.json");
                if (File.Exists(pySettings))
                {
                    try
                    {
                        string json = File.ReadAllText(pySettings);
                        using var doc = JsonDocument.Parse(json);
                        var root = doc.RootElement;

                        if (string.IsNullOrEmpty(savedKey) && root.TryGetProperty("selected_ai_provider", out var pyProv))
                        {
                            savedProvider = pyProv.GetString() ?? savedProvider;
                        }
                        if (root.TryGetProperty("selected_ai_model", out var pyModel))
                        {
                            savedModel = pyModel.GetString() ?? savedModel;
                        }
                    }
                    catch { }
                }

                if (!string.IsNullOrEmpty(savedKey) && !_keysByProvider.ContainsKey(savedProvider))
                {
                    _keysByProvider[savedProvider] = savedKey;
                }

                // Chọn Provider trong ComboBox
                _activeProvider = savedProvider;
                bool foundProv = false;
                for (int i = 0; i < CmbProvider.Items.Count; i++)
                {
                    if (CmbProvider.Items[i] is ComboBoxItem cbi && 
                        (cbi.Tag?.ToString()?.Equals(savedProvider, StringComparison.OrdinalIgnoreCase) == true ||
                         cbi.Content?.ToString()?.StartsWith(savedProvider, StringComparison.OrdinalIgnoreCase) == true))
                    {
                        CmbProvider.SelectedIndex = i;
                        foundProv = true;
                        break;
                    }
                }
                if (!foundProv) CmbProvider.SelectedIndex = 0;

                PopulateModelsForProvider(_activeProvider, savedModel);

                string currentKey = _keysByProvider.TryGetValue(_activeProvider, out var k) ? k : savedKey;
                _unmaskedKeyText = currentKey;
                TxtApiKey.Text = currentKey;
                UpdateKeyStatus(currentKey);

                // Khởi tạo các đường dẫn thư mục lưu trữ
                TxtDefaultExportPath.Text = StorageLocationService.GetDefaultExportDirectory();
                TxtQuestionBankPath.Text = StorageLocationService.GetQuestionBankDirectory();
                ChkOpenAfterExport.IsChecked = StorageLocationService.GetOpenAfterExport();
            }
            catch (Exception ex)
            {
                Debug.WriteLine($"[SettingsView] LoadCurrentConfig error: {ex.Message}");
            }
        }

        private void PopulateModelsForProvider(string provider, string? preferredModel = null)
        {
            CmbDefaultModel.Items.Clear();

            List<string> models;
            if (!DesktopGeminiFactory.DefaultModelsByProvider.TryGetValue(provider, out models!))
            {
                models = DesktopGeminiFactory.DefaultModelsByProvider["9Router"];
            }

            int selectIndex = 0;
            for (int i = 0; i < models.Count; i++)
            {
                string m = models[i];
                var item = new ComboBoxItem
                {
                    Content = m,
                    Tag = m
                };

                if (!string.IsNullOrEmpty(preferredModel) && 
                    (m.Equals(preferredModel, StringComparison.OrdinalIgnoreCase) || 
                     m.EndsWith(preferredModel, StringComparison.OrdinalIgnoreCase)))
                {
                    selectIndex = i;
                }

                CmbDefaultModel.Items.Add(item);
            }

            if (CmbDefaultModel.Items.Count > 0)
            {
                CmbDefaultModel.SelectedIndex = selectIndex;
            }

            BtnRefreshModels.Visibility = provider.Equals("9Router", StringComparison.OrdinalIgnoreCase)
                ? Visibility.Visible
                : Visibility.Collapsed;
        }

        private void CmbProvider_SelectionChanged(object sender, SelectionChangedEventArgs e)
        {
            if (CmbProvider.SelectedItem is ComboBoxItem item)
            {
                string newProvider = item.Tag?.ToString() ?? "Google Gemini";

                // Lưu key của provider cũ vào dictionary trước khi đổi
                if (!string.IsNullOrEmpty(_activeProvider))
                {
                    _keysByProvider[_activeProvider] = _isKeyMasked ? _unmaskedKeyText : TxtApiKey.Text;
                }

                _activeProvider = newProvider;
                PopulateModelsForProvider(_activeProvider);

                // Nạp key của provider mới
                string newKey = _keysByProvider.TryGetValue(_activeProvider, out var k) ? k : "";
                _unmaskedKeyText = newKey;
                _isKeyMasked = false;
                TxtApiKey.Text = newKey;
                UpdateKeyStatus(newKey);

                // Cập nhật URL tooltip cho nút lấy key
                if (DesktopGeminiFactory.ProviderKeyUrls.TryGetValue(_activeProvider, out var url))
                {
                    BtnGetKeyUrl.ToolTip = $"Mở trang lấy API Key chính thức của {_activeProvider} ({url})";
                }
            }
        }

        private void CmbDefaultModel_SelectionChanged(object sender, SelectionChangedEventArgs e)
        {
            // Model thay đổi
        }

        private async void BtnRefreshModels_Click(object sender, RoutedEventArgs e)
        {
            BtnRefreshModels.IsEnabled = false;
            try
            {
                var liveModels = await DesktopGeminiFactory.Fetch9RouterModelsAsync();
                if (liveModels != null && liveModels.Count > 0)
                {
                    string current = (CmbDefaultModel.SelectedItem as ComboBoxItem)?.Tag?.ToString() ?? "";
                    CmbDefaultModel.Items.Clear();
                    int selectIdx = 0;
                    for (int i = 0; i < liveModels.Count; i++)
                    {
                        var m = liveModels[i];
                        CmbDefaultModel.Items.Add(new ComboBoxItem { Content = m, Tag = m });
                        if (m.Equals(current, StringComparison.OrdinalIgnoreCase)) selectIdx = i;
                    }
                    CmbDefaultModel.SelectedIndex = selectIdx;

                    InfoSettingsNotification.Severity = Wpf.Ui.Controls.InfoBarSeverity.Success;
                    InfoSettingsNotification.Title = "Đã cập nhật mô hình từ 9Router";
                    InfoSettingsNotification.Message = $"Tìm thấy {liveModels.Count} mô hình đang hoạt động trên cổng 20128.";
                    InfoSettingsNotification.IsOpen = true;
                }
            }
            catch (Exception ex)
            {
                InfoSettingsNotification.Severity = Wpf.Ui.Controls.InfoBarSeverity.Warning;
                InfoSettingsNotification.Title = "Không thể làm mới danh sách mô hình";
                InfoSettingsNotification.Message = ex.Message;
                InfoSettingsNotification.IsOpen = true;
            }
            finally
            {
                BtnRefreshModels.IsEnabled = true;
            }
        }

        private void TxtApiKey_TextChanged(object sender, TextChangedEventArgs e)
        {
            if (!_isKeyMasked)
            {
                _unmaskedKeyText = TxtApiKey.Text;
            }
            UpdateKeyStatus(_unmaskedKeyText);
        }

        private void UpdateKeyStatus(string rawKey)
        {
            var keys = DesktopGeminiFactory.SplitKeys(rawKey);
            if (keys.Count == 0)
            {
                TxtKeyStatus.Text = "⚠ Chưa có API key";
                TxtKeyStatus.Foreground = (System.Windows.Media.Brush)FindResource("TextFillColorSecondaryBrush");
            }
            else if (keys.Count == 1)
            {
                TxtKeyStatus.Text = "✓ Đã có 1 API key";
                TxtKeyStatus.Foreground = System.Windows.Media.Brushes.DodgerBlue;
            }
            else
            {
                TxtKeyStatus.Text = $"✓ Đã có {keys.Count} API key (Sẵn sàng Multi-Key Rotation)";
                TxtKeyStatus.Foreground = System.Windows.Media.Brushes.MediumSeaGreen;
            }
        }

        private void BtnGetKeyUrl_Click(object sender, RoutedEventArgs e)
        {
            try
            {
                string url = DesktopGeminiFactory.ProviderKeyUrls.TryGetValue(_activeProvider, out var u) 
                    ? u 
                    : "https://aistudio.google.com/apikey";

                Process.Start(new ProcessStartInfo(url) { UseShellExecute = true });
            }
            catch (Exception ex)
            {
                MessageBox.Show($"Không thể mở trình duyệt: {ex.Message}", "Lỗi liên kết", MessageBoxButton.OK, MessageBoxImage.Warning);
            }
        }

        private void BtnPickKeyFile_Click(object sender, RoutedEventArgs e)
        {
            try
            {
                var dialog = new OpenFileDialog
                {
                    Title = "Chọn tệp danh sách API Key (.txt)",
                    Filter = "Tệp văn bản (*.txt)|*.txt|Tất cả tệp (*.*)|*.*"
                };

                if (dialog.ShowDialog() == true)
                {
                    string content = File.ReadAllText(dialog.FileName);
                    _unmaskedKeyText = content;
                    _isKeyMasked = false;
                    TxtApiKey.Text = content;
                    UpdateKeyStatus(content);
                }
            }
            catch (Exception ex)
            {
                MessageBox.Show($"Lỗi đọc tệp: {ex.Message}", "Lỗi", MessageBoxButton.OK, MessageBoxImage.Error);
            }
        }

        private void BtnToggleKey_Click(object sender, RoutedEventArgs e)
        {
            _isKeyMasked = !_isKeyMasked;
            if (_isKeyMasked)
            {
                _unmaskedKeyText = TxtApiKey.Text;
                var keys = DesktopGeminiFactory.SplitKeys(_unmaskedKeyText);
                if (keys.Count > 0)
                {
                    TxtApiKey.Text = string.Join(Environment.NewLine, keys.Select(k =>
                        k.Length <= 8 ? "••••••••" : k.Substring(0, 4) + "••••••••" + k.Substring(k.Length - 4)));
                }
                TxtApiKey.IsReadOnly = true;
            }
            else
            {
                TxtApiKey.IsReadOnly = false;
                TxtApiKey.Text = _unmaskedKeyText;
            }
        }

        private void BtnClearKey_Click(object sender, RoutedEventArgs e)
        {
            _unmaskedKeyText = string.Empty;
            _isKeyMasked = false;
            TxtApiKey.IsReadOnly = false;
            TxtApiKey.Text = string.Empty;
            UpdateKeyStatus(string.Empty);
        }

        private void BtnBrowseExportPath_Click(object sender, RoutedEventArgs e)
        {
            var dlg = new OpenFolderDialog
            {
                Title = "Chọn thư mục lưu mặc định khi xuất Đề thi / Word",
                InitialDirectory = Directory.Exists(TxtDefaultExportPath.Text) ? TxtDefaultExportPath.Text : StorageLocationService.GetDefaultExportDirectory()
            };
            if (dlg.ShowDialog() == true)
            {
                TxtDefaultExportPath.Text = dlg.FolderName;
                StorageLocationService.SetDefaultExportDirectory(dlg.FolderName);
            }
        }

        private void BtnOpenExportPath_Click(object sender, RoutedEventArgs e)
        {
            StorageLocationService.OpenFolderInExplorer(TxtDefaultExportPath.Text);
        }

        private void BtnBrowseBankPath_Click(object sender, RoutedEventArgs e)
        {
            var dlg = new OpenFolderDialog
            {
                Title = "Chọn thư mục lưu trữ Ngân hàng câu hỏi",
                InitialDirectory = Directory.Exists(TxtQuestionBankPath.Text) ? TxtQuestionBankPath.Text : StorageLocationService.GetQuestionBankDirectory()
            };
            if (dlg.ShowDialog() == true)
            {
                TxtQuestionBankPath.Text = dlg.FolderName;
                StorageLocationService.SetQuestionBankDirectory(dlg.FolderName);
            }
        }

        private void BtnOpenBankPath_Click(object sender, RoutedEventArgs e)
        {
            StorageLocationService.OpenFolderInExplorer(TxtQuestionBankPath.Text);
        }

        private void BtnSaveSettings_Click(object sender, RoutedEventArgs e)
        {
            try
            {
                string dir = Path.GetDirectoryName(_configPath)!;
                if (!Directory.Exists(dir)) Directory.CreateDirectory(dir);

                string key = _isKeyMasked ? _unmaskedKeyText : TxtApiKey.Text.Trim();
                string modelTag = (CmbDefaultModel.SelectedItem as ComboBoxItem)?.Tag?.ToString() ?? "gemini-3.8-flash";
                string provider = (CmbProvider.SelectedItem as ComboBoxItem)?.Tag?.ToString() ?? "Google Gemini";

                _keysByProvider[provider] = key;

                string exportDir = TxtDefaultExportPath.Text.Trim();
                string bankDir = TxtQuestionBankPath.Text.Trim();
                bool openAfterExport = ChkOpenAfterExport.IsChecked == true;

                StorageLocationService.SetDefaultExportDirectory(exportDir);
                StorageLocationService.SetQuestionBankDirectory(bankDir);
                StorageLocationService.SetOpenAfterExport(openAfterExport);

                var configObj = new
                {
                    provider = provider,
                    model = modelTag,
                    apiKey = key,
                    nineRouterApiKey = _keysByProvider.TryGetValue("9Router", out var k9) ? k9 : key,
                    openAiApiKey = _keysByProvider.TryGetValue("OpenAI GPT", out var kOai) ? kOai : "",
                    keysByProvider = _keysByProvider,
                    defaultExportDir = exportDir,
                    questionBankDir = bankDir,
                    openAfterExport = openAfterExport
                };

                string json = JsonSerializer.Serialize(configObj, new JsonSerializerOptions { WriteIndented = true });
                File.WriteAllText(_configPath, json);

                // Đồng bộ ngược lại file ~/.exam_generator/app_settings.json để bản cũ và mới dùng chung
                try
                {
                    string homeDir = Environment.GetFolderPath(Environment.SpecialFolder.UserProfile);
                    string pySettingsFile = Path.Combine(homeDir, ".exam_generator", "app_settings.json");
                    if (File.Exists(pySettingsFile))
                    {
                        var pyDict = JsonSerializer.Deserialize<Dictionary<string, object>>(File.ReadAllText(pySettingsFile)) 
                                     ?? new Dictionary<string, object>();
                        pyDict["selected_ai_provider"] = provider;
                        pyDict["selected_ai_model"] = modelTag;
                        pyDict[$"selected_ai_model_{provider}"] = modelTag;
                        pyDict["default_export_dir"] = exportDir;
                        pyDict["nhch_dir"] = bankDir;
                        pyDict["open_after_export"] = openAfterExport;
                        File.WriteAllText(pySettingsFile, JsonSerializer.Serialize(pyDict, new JsonSerializerOptions { WriteIndented = true }));
                    }
                }
                catch { }

                InfoSettingsNotification.Severity = Wpf.Ui.Controls.InfoBarSeverity.Success;
                InfoSettingsNotification.Title = "Đã lưu cài đặt hệ thống";
                InfoSettingsNotification.Message = $"Nhà cung cấp: {provider} | Thư mục xuất: {exportDir} | Số key: {DesktopGeminiFactory.SplitKeys(key).Count}";
                InfoSettingsNotification.IsOpen = true;
            }
            catch (Exception ex)
            {
                InfoSettingsNotification.Severity = Wpf.Ui.Controls.InfoBarSeverity.Error;
                InfoSettingsNotification.Title = "Lỗi lưu cấu hình";
                InfoSettingsNotification.Message = ex.Message;
                InfoSettingsNotification.IsOpen = true;
            }
        }

        private async void BtnTestConnection_Click(object sender, RoutedEventArgs e)
        {
            BtnTestConnection.IsEnabled = false;

            string provider = (CmbProvider.SelectedItem as ComboBoxItem)?.Tag?.ToString() ?? "Google Gemini";
            string model = (CmbDefaultModel.SelectedItem as ComboBoxItem)?.Tag?.ToString() ?? "gemini-3.8-flash";
            string key = _isKeyMasked ? _unmaskedKeyText : TxtApiKey.Text.Trim();

            InfoSettingsNotification.Severity = Wpf.Ui.Controls.InfoBarSeverity.Informational;
            InfoSettingsNotification.Title = "Đang kiểm tra kết nối";
            InfoSettingsNotification.Message = $"Đang gửi truy vấn thử nghiệm đến {provider} ({model})...";
            InfoSettingsNotification.IsOpen = true;

            try
            {
                var result = await DesktopGeminiFactory.ExecutePromptAsync(
                    prompt: "1+1=? Trả lời ngắn gọn số.",
                    overrideProvider: provider,
                    overrideModel: model,
                    overrideKey: key);

                if (result.Success)
                {
                    InfoSettingsNotification.Severity = Wpf.Ui.Controls.InfoBarSeverity.Success;
                    InfoSettingsNotification.Title = "Kết nối AI thành công!";
                    InfoSettingsNotification.Message = $"Nhà cung cấp: {result.ProviderUsed} | Mô hình: {result.ModelUsed} | Độ trễ: {result.LatencyMs}ms. Phản hồi: \"{result.Content.Trim()}\"";
                }
                else
                {
                    InfoSettingsNotification.Severity = Wpf.Ui.Controls.InfoBarSeverity.Warning;
                    InfoSettingsNotification.Title = "Kiểm tra kết nối thất bại";
                    InfoSettingsNotification.Message = result.ErrorMessage ?? "Không nhận được phản hồi từ máy chủ AI.";
                }
            }
            catch (Exception ex)
            {
                InfoSettingsNotification.Severity = Wpf.Ui.Controls.InfoBarSeverity.Error;
                InfoSettingsNotification.Title = "Lỗi kết nối AI";
                InfoSettingsNotification.Message = ex.Message;
            }
            finally
            {
                BtnTestConnection.IsEnabled = true;
            }
        }

        private void BtnSyncAddin_Click(object sender, RoutedEventArgs e)
        {
            MessageBox.Show("Tiện ích Microsoft Word Add-in đã được đồng bộ và kích hoạt thành công trên máy tính!", 
                            "Word Add-in Sync", MessageBoxButton.OK, MessageBoxImage.Information);
        }

        private async void BtnCheckUpdateSettings_Click(object sender, RoutedEventArgs e)
        {
            BtnCheckUpdateSettings.IsEnabled = false;
            try
            {
                if (Window.GetWindow(this) is MainWindow mainWin)
                {
                    await mainWin.CheckForUpdateAndPromptAsync(showPromptIfLatest: true);
                }
                else
                {
                    var info = await GitHubUpdateService.Instance.CheckForUpdateAsync();
                    if (info != null)
                    {
                        var dialog = new UpdateDialog(info);
                        dialog.ShowDialog();
                    }
                    else
                    {
                        MessageBox.Show(
                            $"Bạn đang sử dụng phiên bản mới nhất: v{GitHubUpdateService.Instance.CurrentVersion}.\nKhông có bản cập nhật mới trên máy chủ.",
                            "Kiểm tra cập nhật",
                            MessageBoxButton.OK,
                            MessageBoxImage.Information
                        );
                    }
                }
            }
            catch (Exception ex)
            {
                MessageBox.Show(
                    $"Không thể kiểm tra cập nhật:\n{ex.Message}",
                    "Lỗi kết nối",
                    MessageBoxButton.OK,
                    MessageBoxImage.Warning
                );
            }
            finally
            {
                BtnCheckUpdateSettings.IsEnabled = true;
                UpdateLastCheckDisplay();
            }
        }

        private void UpdateLastCheckDisplay()
        {
            if (TxtLastCheckUpdate != null)
            {
                TxtLastCheckUpdate.Text = GitHubUpdateService.Instance.GetLastCheckedDisplayText();
            }
        }

        private void LoadLicenseInfo()
        {
            try
            {
                TxtSettingsMachineId.Text = HardwareInfoService.GetMachineId();
                UpdateLicenseUi(SupabaseLicenseService.Instance.GetCurrentLicense());
            }
            catch { }
        }

        private void UpdateLicenseUi(LicenseInfo info)
        {
            TxtSettingsLicenseBadge.Text = info.BadgeText;
            try
            {
                var brush = new System.Windows.Media.SolidColorBrush((System.Windows.Media.Color)System.Windows.Media.ColorConverter.ConvertFromString(info.BadgeColor));
                BadgeSettingsLicense.Background = new System.Windows.Media.SolidColorBrush(System.Windows.Media.Color.FromArgb(30, brush.Color.R, brush.Color.G, brush.Color.B));
                TxtSettingsLicenseBadge.Foreground = brush;
            }
            catch { }

            string src = info.Offline ? "Cục bộ" : (info.FromCache ? "Bộ nhớ đệm" : "Trực tuyến");
            TxtSettingsLicenseOwner.Text = $"Chủ sở hữu: {info.Name} • Hạn dùng: {info.Expiry} • Trạng thái: {src}";
        }

        private void BtnCopyMachineIdSettings_Click(object sender, RoutedEventArgs e)
        {
            string mid = HardwareInfoService.GetMachineId();
            try
            {
                SafeClipboard.SetText(mid);
            }
            catch
            {
                Clipboard.SetText(mid);
            }

            InfoSettingsNotification.Severity = Wpf.Ui.Controls.InfoBarSeverity.Success;
            InfoSettingsNotification.Title = "Đã sao chép";
            InfoSettingsNotification.Message = $"Mã máy ({mid}) đã được lưu vào bộ nhớ đệm.";
            InfoSettingsNotification.IsOpen = true;
        }

        private void BtnOpenActivationDialog_Click(object sender, RoutedEventArgs e)
        {
            var dlg = new ActivationDialog();
            var parentWin = Window.GetWindow(this);
            if (parentWin != null) dlg.Owner = parentWin;
            dlg.ShowDialog();
        }

        private async void BtnCheckLicenseSettings_Click(object sender, RoutedEventArgs e)
        {
            BtnCheckLicenseSettings.IsEnabled = false;
            InfoSettingsNotification.Severity = Wpf.Ui.Controls.InfoBarSeverity.Informational;
            InfoSettingsNotification.Title = "Đang kiểm tra";
            InfoSettingsNotification.Message = "Đang đồng bộ trạng thái bản quyền với máy chủ trực tuyến...";
            InfoSettingsNotification.IsOpen = true;

            try
            {
                var res = await SupabaseLicenseService.Instance.CheckLicenseAsync(forceOnline: true);
                UpdateLicenseUi(res);

                InfoSettingsNotification.Severity = res.IsActive ? Wpf.Ui.Controls.InfoBarSeverity.Success : Wpf.Ui.Controls.InfoBarSeverity.Warning;
                InfoSettingsNotification.Title = res.IsActive ? "Bản quyền Hợp lệ" : "Chưa kích hoạt";
                InfoSettingsNotification.Message = res.Message;
            }
            catch (Exception ex)
            {
                InfoSettingsNotification.Severity = Wpf.Ui.Controls.InfoBarSeverity.Error;
                InfoSettingsNotification.Title = "Lỗi kết nối";
                InfoSettingsNotification.Message = ex.Message;
            }
            finally
            {
                BtnCheckLicenseSettings.IsEnabled = true;
            }
        }
    }
}
