using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Input;
using System.Windows.Media.Imaging;
using Microsoft.Win32;
using MatrixExamAI.Desktop.Services;
using MatrixExamAI.Shared.HtmlModel;
using Wpf.Ui.Controls;
using MessageBox = System.Windows.MessageBox;
using MessageBoxButton = System.Windows.MessageBoxButton;
using MessageBoxImage = System.Windows.MessageBoxImage;
using Color = System.Windows.Media.Color;
using SolidColorBrush = System.Windows.Media.SolidColorBrush;

namespace MatrixExamAI.Desktop.Views
{
    public enum HtmlModelLayoutMode
    {
        Split,
        ModelOnly,
        CodeOnly
    }

    public partial class HtmlModelView : UserControl
    {
        private readonly List<HtmlModelTemplateItem> _templates = new List<HtmlModelTemplateItem>();
        private HtmlModelLayoutMode _currentLayoutMode = HtmlModelLayoutMode.Split;
        private GridLength _lastCodeWidth = new GridLength(1, GridUnitType.Star);
        private GridLength _lastPreviewWidth = new GridLength(1.8, GridUnitType.Star);

        private byte[]? _attachedImageBytes;
        private string _lastPrompt = string.Empty;
        private bool _isWebViewInitialized = false;
        private string? _tempHtmlPath;

        public HtmlModelView()
        {
            InitializeComponent();

            Loaded += (s, e) =>
            {
                Dispatcher.BeginInvoke(new Action(async () =>
                {
                    InitializeCategoriesAndTemplates();
                    InitializeLayout();
                    await InitializeWebViewAsync();

                    // Mặc định nạp mẫu Câu 6 Khối tròn xoay của người dùng
                    if (string.IsNullOrWhiteSpace(TxtHtmlCode.Text) && _templates.Count > 0)
                    {
                        var defaultItem = _templates.FirstOrDefault(t => t.Id == "solid_rev_cau6") ?? _templates[0];
                        TxtHtmlCode.Text = defaultItem.HtmlCode;
                        await RunModelAsync();
                    }
                }), System.Windows.Threading.DispatcherPriority.Loaded);
            };
        }

        private async Task InitializeWebViewAsync()
        {
            try
            {
                if (!_isWebViewInitialized)
                {
                    await WebViewControl.EnsureCoreWebView2Async(null);
                    _isWebViewInitialized = true;
                    TxtWebStatus.Text = "WebView2: Sẵn sàng";
                    IconWebStatus.Symbol = SymbolRegular.CheckmarkCircle24;
                    IconWebStatus.Foreground = new SolidColorBrush(Color.FromRgb(16, 185, 129));
                }
            }
            catch (Exception ex)
            {
                TxtWebStatus.Text = "WebView2: Chế độ Web ngoài";
                IconWebStatus.Symbol = SymbolRegular.Globe24;
                IconWebStatus.Foreground = new SolidColorBrush(Color.FromRgb(2, 132, 199));
                Debug.WriteLine($"WebView2 initialization notice: {ex.Message}");
            }
        }

        private void InitializeCategoriesAndTemplates()
        {
            try
            {
                _templates.Clear();
                _templates.AddRange(HtmlModelTemplateLibrary.GetAllTemplates());

                CmbCategory.ItemsSource = HtmlModelTemplateLibrary.Categories;
                if (CmbCategory.Items.Count > 0)
                {
                    CmbCategory.SelectedIndex = 0;
                }

                UpdateTemplateItemsForCategory(HtmlModelTemplateLibrary.Categories[0]);
            }
            catch (Exception ex)
            {
                Debug.WriteLine($"Error initializing templates: {ex.Message}");
            }
        }

        private void UpdateTemplateItemsForCategory(string category)
        {
            var matched = _templates.Where(t => t.Category.Equals(category, StringComparison.OrdinalIgnoreCase)).ToList();
            if (matched.Count == 0)
            {
                matched = _templates.ToList();
            }

            CmbTemplateItem.ItemsSource = matched;
            if (matched.Count > 0)
            {
                CmbTemplateItem.SelectedIndex = 0;
            }
        }

        private void CmbCategory_SelectionChanged(object sender, SelectionChangedEventArgs e)
        {
            if (CmbCategory.SelectedItem is string cat)
            {
                UpdateTemplateItemsForCategory(cat);
            }
        }

        private void CmbTemplateItem_SelectionChanged(object sender, SelectionChangedEventArgs e)
        {
            if (CmbTemplateItem.SelectedItem is HtmlModelTemplateItem item && !string.IsNullOrWhiteSpace(item.HtmlCode))
            {
                TxtPrompt.Text = item.Title;
            }
        }

        private async void BtnOpenModelBank_Click(object sender, RoutedEventArgs e)
        {
            var dlg = new HtmlModelBankDialog();
            dlg.Owner = Window.GetWindow(this);
            if (dlg.ShowDialog() == true && !string.IsNullOrWhiteSpace(dlg.SelectedHtmlCode))
            {
                TxtHtmlCode.Text = dlg.SelectedHtmlCode;
                InfoHtmlNotification.Severity = InfoBarSeverity.Success;
                InfoHtmlNotification.Title = "Đã nạp mô hình từ kho";
                InfoHtmlNotification.Message = "Đã nạp thành công mô hình từ kho lưu trữ. Đang khởi chạy mô phỏng...";
                InfoHtmlNotification.IsOpen = true;

                await RunModelAsync();
            }
        }

        private void BtnSaveModelBank_Click(object sender, RoutedEventArgs e)
        {
            string code = TxtHtmlCode.Text.Trim();
            if (string.IsNullOrWhiteSpace(code))
            {
                System.Windows.MessageBox.Show("Chưa có mã nguồn HTML để lưu vào kho.", "Thông báo", MessageBoxButton.OK, MessageBoxImage.Warning);
                return;
            }

            string title = TxtPrompt.Text.Trim();
            if (string.IsNullOrWhiteSpace(title))
            {
                var match = System.Text.RegularExpressions.Regex.Match(code, @"<title>(.*?)</title>", System.Text.RegularExpressions.RegexOptions.IgnoreCase);
                title = match.Success ? match.Groups[1].Value.Trim() : $"Mô hình 3D {DateTime.Now:dd/MM/yyyy HH:mm}";
            }

            string category = CmbCategory.SelectedItem as string ?? "Mô hình cá nhân tự lưu";
            var entry = HtmlModelBankService.SaveUserEntry(title, category, "Mô hình được lưu từ phiên làm việc MatrixExamAI.", code);

            InfoHtmlNotification.Severity = InfoBarSeverity.Success;
            InfoHtmlNotification.Title = "Đã lưu vào kho mô hình";
            InfoHtmlNotification.Message = $"Đã lưu thành công '{entry.Title}' vào kho lưu trữ cá nhân!";
            InfoHtmlNotification.IsOpen = true;
        }

        private void BtnLoadTemplate_Click(object sender, RoutedEventArgs e)
        {
            BtnOpenModelBank_Click(sender, e);
        }

        #region LAYOUT MODES (SPLIT, MODEL ONLY, CODE ONLY)

        private void InitializeLayout()
        {
            SetLayoutMode(_currentLayoutMode);
        }

        public void SetLayoutMode(HtmlModelLayoutMode mode)
        {
            _currentLayoutMode = mode;
            switch (mode)
            {
                case HtmlModelLayoutMode.ModelOnly:
                    if (ColCode.Width.Value > 0 && ColCode.Width.GridUnitType == GridUnitType.Star)
                    {
                        _lastCodeWidth = ColCode.Width;
                        _lastPreviewWidth = ColPreview.Width;
                    }
                    ColCode.MinWidth = 0;
                    ColCode.Width = new GridLength(0);
                    ColSplitter.Width = new GridLength(0);
                    ColPreview.MinWidth = 0;
                    ColPreview.Width = new GridLength(1, GridUnitType.Star);

                    CardCode.Visibility = Visibility.Collapsed;
                    SplitterHtml.Visibility = Visibility.Collapsed;
                    CardPreview.Visibility = Visibility.Visible;

                    Grid.SetColumn(CardPreview, 0);
                    Grid.SetColumnSpan(CardPreview, 3);

                    BtnExpandCode.Visibility = Visibility.Visible;
                    BtnExpandPreviewFromCode.Visibility = Visibility.Collapsed;
                    break;

                case HtmlModelLayoutMode.CodeOnly:
                    if (ColCode.Width.Value > 0 && ColCode.Width.GridUnitType == GridUnitType.Star)
                    {
                        _lastCodeWidth = ColCode.Width;
                        _lastPreviewWidth = ColPreview.Width;
                    }
                    ColPreview.MinWidth = 0;
                    ColPreview.Width = new GridLength(0);
                    ColSplitter.Width = new GridLength(0);
                    ColCode.MinWidth = 0;
                    ColCode.Width = new GridLength(1, GridUnitType.Star);

                    CardPreview.Visibility = Visibility.Collapsed;
                    SplitterHtml.Visibility = Visibility.Collapsed;
                    CardCode.Visibility = Visibility.Visible;

                    Grid.SetColumn(CardCode, 0);
                    Grid.SetColumnSpan(CardCode, 3);

                    BtnExpandCode.Visibility = Visibility.Collapsed;
                    BtnExpandPreviewFromCode.Visibility = Visibility.Visible;
                    break;

                case HtmlModelLayoutMode.Split:
                default:
                    ColCode.MinWidth = 280;
                    ColCode.Width = _lastCodeWidth.Value > 0 ? _lastCodeWidth : new GridLength(1, GridUnitType.Star);

                    ColSplitter.Width = new GridLength(8);

                    ColPreview.MinWidth = 300;
                    ColPreview.Width = _lastPreviewWidth.Value > 0 ? _lastPreviewWidth : new GridLength(1.8, GridUnitType.Star);

                    Grid.SetColumn(CardCode, 0);
                    Grid.SetColumnSpan(CardCode, 1);
                    Grid.SetColumn(CardPreview, 2);
                    Grid.SetColumnSpan(CardPreview, 1);

                    CardCode.Visibility = Visibility.Visible;
                    SplitterHtml.Visibility = Visibility.Visible;
                    CardPreview.Visibility = Visibility.Visible;

                    BtnExpandCode.Visibility = Visibility.Collapsed;
                    BtnExpandPreviewFromCode.Visibility = Visibility.Collapsed;
                    break;
            }
        }

        private void BtnModeSplit_Click(object sender, RoutedEventArgs e) => SetLayoutMode(HtmlModelLayoutMode.Split);
        private void BtnModeModelOnly_Click(object sender, RoutedEventArgs e) => SetLayoutMode(HtmlModelLayoutMode.ModelOnly);
        private void BtnModeCodeOnly_Click(object sender, RoutedEventArgs e) => SetLayoutMode(HtmlModelLayoutMode.CodeOnly);
        private void BtnCollapseCode_Click(object sender, RoutedEventArgs e) => SetLayoutMode(HtmlModelLayoutMode.ModelOnly);
        private void BtnExpandCode_Click(object sender, RoutedEventArgs e) => SetLayoutMode(HtmlModelLayoutMode.Split);
        private void BtnExpandPreviewFromCode_Click(object sender, RoutedEventArgs e) => SetLayoutMode(HtmlModelLayoutMode.Split);

        #endregion

        #region CHẠY MÔ HÌNH VÀ HIỂN THỊ WEBVIEW2

        private async void BtnRun_Click(object sender, RoutedEventArgs e)
        {
            await RunModelAsync();
        }

        public async Task RunModelAsync()
        {
            string html = TxtHtmlCode.Text.Trim();
            if (string.IsNullOrWhiteSpace(html))
            {
                System.Windows.MessageBox.Show("Chưa có mã nguồn HTML để hiển thị mô hình.\nHãy chọn 'Mẫu chuẩn' hoặc bấm 'AI tạo' để bắt đầu.", "Thông báo", MessageBoxButton.OK, MessageBoxImage.Information);
                return;
            }

            html = HtmlModelCodeExtractor.ExtractHtmlCode(html);
            TxtHtmlCode.Text = html;

            var sw = Stopwatch.StartNew();
            TxtModelStats.Text = "⏳ Đang nạp mô hình...";

            try
            {
                // Lưu vào tệp tạm thời để hỗ trợ trọn vẹn Three.js và CDN cục bộ
                string tempDir = Path.Combine(Path.GetTempPath(), "MatrixExamAI_HtmlModel");
                Directory.CreateDirectory(tempDir);
                _tempHtmlPath = Path.Combine(tempDir, "preview.html");
                File.WriteAllText(_tempHtmlPath, html, Encoding.UTF8);

                await InitializeWebViewAsync();

                if (_isWebViewInitialized && WebViewControl.CoreWebView2 != null)
                {
                    WebViewControl.CoreWebView2.Navigate(new Uri(_tempHtmlPath).AbsoluteUri);
                    PanelPlaceholder.Visibility = Visibility.Collapsed;
                }
                else
                {
                    // Fallback nếu WebView2 chưa cài đặt: mở trực tiếp bằng trình duyệt mặc định
                    Process.Start(new ProcessStartInfo(_tempHtmlPath) { UseShellExecute = true });
                    PanelPlaceholder.Visibility = Visibility.Visible;
                }

                sw.Stop();
                int lineCount = html.Split('\n').Length;
                double sizeKb = Encoding.UTF8.GetByteCount(html) / 1024.0;
                TxtModelStats.Text = $"Mô hình 3D: {lineCount} dòng ({sizeKb:F1} KB)";
                TxtRenderTime.Text = $"Thời gian nạp: {sw.ElapsedMilliseconds} ms";
            }
            catch (Exception ex)
            {
                TxtModelStats.Text = $"Lỗi nạp mô hình: {ex.Message}";
                System.Windows.MessageBox.Show($"Không thể hiển thị mô hình: {ex.Message}", "Lỗi hiển thị", MessageBoxButton.OK, MessageBoxImage.Error);
            }
        }

        private void BtnOpenInBrowser_Click(object sender, RoutedEventArgs e)
        {
            try
            {
                string html = TxtHtmlCode.Text.Trim();
                if (string.IsNullOrWhiteSpace(html))
                {
                    System.Windows.MessageBox.Show("Chưa có mã HTML để mở trên trình duyệt.", "Thông báo", MessageBoxButton.OK, MessageBoxImage.Information);
                    return;
                }

                string tempDir = Path.Combine(Path.GetTempPath(), "MatrixExamAI_HtmlModel");
                Directory.CreateDirectory(tempDir);
                string path = Path.Combine(tempDir, $"simulation_{DateTime.Now:yyyyMMdd_HHmmss}.html");
                File.WriteAllText(path, html, Encoding.UTF8);

                Process.Start(new ProcessStartInfo(path) { UseShellExecute = true });

                InfoHtmlNotification.Severity = InfoBarSeverity.Success;
                InfoHtmlNotification.Title = "Đã mở trên trình duyệt Web";
                InfoHtmlNotification.Message = $"Tệp mô hình đã được mở trực tiếp trên trình duyệt Web mặc định: {Path.GetFileName(path)}";
                InfoHtmlNotification.IsOpen = true;
            }
            catch (Exception ex)
            {
                System.Windows.MessageBox.Show($"Lỗi mở trình duyệt: {ex.Message}", "Lỗi", MessageBoxButton.OK, MessageBoxImage.Error);
            }
        }

        private void BtnCopyHtml_Click(object sender, RoutedEventArgs e)
        {
            string html = TxtHtmlCode.Text.Trim();
            if (string.IsNullOrWhiteSpace(html)) return;

            try
            {
                System.Windows.Clipboard.SetText(html);
                InfoHtmlNotification.Severity = InfoBarSeverity.Success;
                InfoHtmlNotification.Title = "Đã sao chép HTML";
                InfoHtmlNotification.Message = "Toàn bộ mã nguồn HTML / Three.js đã được lưu vào bộ nhớ đệm.";
                InfoHtmlNotification.IsOpen = true;
            }
            catch (Exception ex)
            {
                System.Windows.MessageBox.Show($"Lỗi sao chép: {ex.Message}", "Lỗi", MessageBoxButton.OK, MessageBoxImage.Error);
            }
        }

        private void BtnFullscreen_Click(object sender, RoutedEventArgs e)
        {
            BtnOpenInBrowser_Click(sender, e);
        }

        #endregion

        #region AI TẠO, SỬA ĐỔI, TỐI ƯU VÀ DÁN ẢNH

        private async void BtnAiGenerate_Click(object sender, RoutedEventArgs e)
        {
            string prompt = TxtPrompt.Text.Trim();
            if (string.IsNullOrWhiteSpace(prompt) && _attachedImageBytes == null)
            {
                System.Windows.MessageBox.Show("Vui lòng nhập mô tả đề bài / mô hình 3D hoặc dán ảnh bài toán.", "Chưa có thông tin", MessageBoxButton.OK, MessageBoxImage.Warning);
                return;
            }

            var dlg = new AiDrawPromptDialog(prompt, _attachedImageBytes)
            {
                Owner = Window.GetWindow(this),
                Title = "AI Tạo Mô hình Mô phỏng 3D HTML & Khoa học"
            };

            if (dlg.ShowDialog() == true)
            {
                string desc = dlg.ResultDescription;
                byte[]? imgBytes = dlg.ResultImageBytes;
                _lastPrompt = desc;
                TxtPrompt.Text = desc;

                if (imgBytes != null && imgBytes.Length > 0)
                {
                    _attachedImageBytes = imgBytes;
                    LoadAttachedImage(imgBytes);
                }

                await ExecuteAiGenerationAsync(desc, imgBytes);
            }
        }

        private async Task ExecuteAiGenerationAsync(string prompt, byte[]? imgBytes)
        {
            string category = CmbCategory.SelectedItem as string ?? "Toán học & Khoa học 3D";
            string? base64 = (imgBytes != null && imgBytes.Length > 0) ? Convert.ToBase64String(imgBytes) : null;

            BtnAiGenerate.IsEnabled = false;
            TxtModelStats.Text = "⏳ AI đang phân tích và lập trình mô hình 3D HTML...";
            var sw = Stopwatch.StartNew();

            try
            {
                var result = await DesktopGeminiFactory.GenerateHtmlModelAsync(prompt, category, base64);
                sw.Stop();

                if (result.Success && !string.IsNullOrWhiteSpace(result.Content))
                {
                    string html = HtmlModelCodeExtractor.ExtractHtmlCode(result.Content);
                    TxtHtmlCode.Text = html;

                    InfoHtmlNotification.Severity = InfoBarSeverity.Success;
                    InfoHtmlNotification.Title = "AI Tạo mô hình thành công";
                    InfoHtmlNotification.Message = $"Mô hình 3D đã được tạo trong {sw.ElapsedMilliseconds} ms ({result.ModelUsed}).";
                    InfoHtmlNotification.IsOpen = true;

                    await RunModelAsync();
                }
                else
                {
                    System.Windows.MessageBox.Show($"AI không thể tạo mô hình: {result.ErrorMessage}", "Lỗi sinh mã", MessageBoxButton.OK, MessageBoxImage.Error);
                }
            }
            catch (Exception ex)
            {
                System.Windows.MessageBox.Show($"Lỗi trong quá trình AI tạo mô hình: {ex.Message}", "Lỗi", MessageBoxButton.OK, MessageBoxImage.Error);
            }
            finally
            {
                BtnAiGenerate.IsEnabled = true;
            }
        }

        private async void BtnAiRegenerate_Click(object sender, RoutedEventArgs e)
        {
            string prompt = string.IsNullOrWhiteSpace(_lastPrompt) ? TxtPrompt.Text.Trim() : _lastPrompt;
            if (string.IsNullOrWhiteSpace(prompt) && _attachedImageBytes == null)
            {
                System.Windows.MessageBox.Show("Chưa có mô tả trước đó để tạo lại.\nHãy nhập mô tả vào ô đề bài.", "Chưa có mô tả", MessageBoxButton.OK, MessageBoxImage.Information);
                return;
            }

            await ExecuteAiGenerationAsync(prompt, _attachedImageBytes);
        }

        private async void BtnAiEdit_Click(object sender, RoutedEventArgs e)
        {
            string currentHtml = TxtHtmlCode.Text.Trim();
            if (string.IsNullOrWhiteSpace(currentHtml))
            {
                System.Windows.MessageBox.Show("Chưa có mã nguồn HTML để chỉnh sửa.", "Thông báo", MessageBoxButton.OK, MessageBoxImage.Information);
                return;
            }

            var dlg = new AiEditPromptDialog(currentHtml, _attachedImageBytes)
            {
                Owner = Window.GetWindow(this),
                Title = "AI Chỉnh Sửa & Bổ Sung Mô Hình 3D HTML"
            };

            if (dlg.ShowDialog() == true)
            {
                string editReq = dlg.ResultDescription ?? string.Empty;
                byte[]? imgBytes = dlg.ResultImageBytes;
                string? base64 = (imgBytes != null && imgBytes.Length > 0) ? Convert.ToBase64String(imgBytes) : null;

                BtnAiEdit.IsEnabled = false;
                TxtModelStats.Text = "⏳ AI đang chỉnh sửa mã HTML theo yêu cầu...";
                var sw = Stopwatch.StartNew();

                try
                {
                    var result = await DesktopGeminiFactory.EditHtmlModelAsync(currentHtml, editReq, base64);
                    sw.Stop();

                    if (result.Success && !string.IsNullOrWhiteSpace(result.Content))
                    {
                        string updatedHtml = HtmlModelCodeExtractor.ExtractHtmlCode(result.Content);
                        TxtHtmlCode.Text = updatedHtml;

                        InfoHtmlNotification.Severity = InfoBarSeverity.Success;
                        InfoHtmlNotification.Title = "AI Sửa mô hình hoàn tất";
                        InfoHtmlNotification.Message = $"Đã cập nhật mô hình 3D trong {sw.ElapsedMilliseconds} ms ({result.ModelUsed}).";
                        InfoHtmlNotification.IsOpen = true;

                        await RunModelAsync();
                    }
                    else
                    {
                        System.Windows.MessageBox.Show($"AI không thể chỉnh sửa: {result.ErrorMessage}", "Lỗi chỉnh sửa", MessageBoxButton.OK, MessageBoxImage.Error);
                    }
                }
                catch (Exception ex)
                {
                    System.Windows.MessageBox.Show($"Lỗi trong quá trình AI chỉnh sửa: {ex.Message}", "Lỗi", MessageBoxButton.OK, MessageBoxImage.Error);
                }
                finally
                {
                    BtnAiEdit.IsEnabled = true;
                }
            }
        }

        private async void BtnAiOptimize_Click(object sender, RoutedEventArgs e)
        {
            string currentHtml = TxtHtmlCode.Text.Trim();
            if (string.IsNullOrWhiteSpace(currentHtml)) return;

            BtnAiOptimize.IsEnabled = false;
            TxtModelStats.Text = "⏳ AI đang tối ưu Three.js & KaTeX...";
            var sw = Stopwatch.StartNew();

            try
            {
                var result = await DesktopGeminiFactory.OptimizeHtmlModelAsync(currentHtml);
                sw.Stop();

                if (result.Success && !string.IsNullOrWhiteSpace(result.Content))
                {
                    string optHtml = HtmlModelCodeExtractor.ExtractHtmlCode(result.Content);
                    TxtHtmlCode.Text = optHtml;

                    InfoHtmlNotification.Severity = InfoBarSeverity.Success;
                    InfoHtmlNotification.Title = "AI Tối ưu hoàn tất";
                    InfoHtmlNotification.Message = $"Đã tối ưu hóa mã nguồn mô hình trong {sw.ElapsedMilliseconds} ms.";
                    InfoHtmlNotification.IsOpen = true;

                    await RunModelAsync();
                }
                else
                {
                    System.Windows.MessageBox.Show($"Lỗi tối ưu: {result.ErrorMessage}", "Lỗi", MessageBoxButton.OK, MessageBoxImage.Error);
                }
            }
            catch (Exception ex)
            {
                System.Windows.MessageBox.Show($"Lỗi tối ưu: {ex.Message}", "Lỗi", MessageBoxButton.OK, MessageBoxImage.Error);
            }
            finally
            {
                BtnAiOptimize.IsEnabled = true;
            }
        }

        private async void BtnAiAutoFix_Click(object sender, RoutedEventArgs e)
        {
            string currentHtml = TxtHtmlCode.Text.Trim();
            if (string.IsNullOrWhiteSpace(currentHtml)) return;

            string fixPrompt = "Sửa tất cả các lỗi cú pháp JavaScript, lỗi khai báo Three.js, lỗi KaTeX và đảm bảo trang mô phỏng chạy mượt mà 100%.";
            BtnAiAutoFix.IsEnabled = false;

            try
            {
                var result = await DesktopGeminiFactory.EditHtmlModelAsync(currentHtml, fixPrompt, null);
                if (result.Success && !string.IsNullOrWhiteSpace(result.Content))
                {
                    TxtHtmlCode.Text = HtmlModelCodeExtractor.ExtractHtmlCode(result.Content);
                    await RunModelAsync();
                    BtnAiAutoFix.Visibility = Visibility.Collapsed;
                }
            }
            catch (Exception ex)
            {
                System.Windows.MessageBox.Show($"Lỗi tự sửa: {ex.Message}", "Lỗi", MessageBoxButton.OK, MessageBoxImage.Error);
            }
            finally
            {
                BtnAiAutoFix.IsEnabled = true;
            }
        }

        #endregion

        #region XỬ LÝ ẢNH MẪU CLIPBOARD VÀ DRAG & DROP

        private void BtnPasteImage_Click(object sender, RoutedEventArgs e)
        {
            if (System.Windows.Clipboard.ContainsImage())
            {
                try
                {
                    var img = System.Windows.Clipboard.GetImage();
                    if (img != null)
                    {
                        using var ms = new MemoryStream();
                        var encoder = new PngBitmapEncoder();
                        encoder.Frames.Add(BitmapFrame.Create(img));
                        encoder.Save(ms);
                        byte[] bytes = ms.ToArray();

                        LoadAttachedImage(bytes);

                        InfoHtmlNotification.Severity = InfoBarSeverity.Informational;
                        InfoHtmlNotification.Title = "Đã dán ảnh đề bài";
                        InfoHtmlNotification.Message = "Đã nhận ảnh mẫu từ Clipboard. Bấm 'AI tạo' (Ctrl+Shift+G) để dựng mô hình 3D.";
                        InfoHtmlNotification.IsOpen = true;
                    }
                }
                catch (Exception ex)
                {
                    System.Windows.MessageBox.Show($"Lỗi dán ảnh: {ex.Message}", "Lỗi", MessageBoxButton.OK, MessageBoxImage.Error);
                }
            }
            else
            {
                System.Windows.MessageBox.Show("Bộ nhớ tạm (Clipboard) không có dữ liệu hình ảnh.", "Thông báo", MessageBoxButton.OK, MessageBoxImage.Information);
            }
        }

        private void LoadAttachedImage(byte[] bytes)
        {
            _attachedImageBytes = bytes;
            using var ms = new MemoryStream(bytes);
            var bi = new BitmapImage();
            bi.BeginInit();
            bi.CacheOption = BitmapCacheOption.OnLoad;
            bi.StreamSource = ms;
            bi.EndInit();
            bi.Freeze();

            ImgAttachedPreview.Source = bi;
            BorderAttachedImage.Visibility = Visibility.Visible;
        }

        private void BtnRemoveImage_Click(object sender, RoutedEventArgs e)
        {
            _attachedImageBytes = null;
            ImgAttachedPreview.Source = null;
            BorderAttachedImage.Visibility = Visibility.Collapsed;
        }

        private void AttachedImage_Click(object sender, MouseButtonEventArgs e)
        {
            if (ImgAttachedPreview.Source != null)
            {
                var viewer = new TikzImagePreviewWindow(ImgAttachedPreview.Source, null, 300, "Ảnh đề bài / mô hình đính kèm")
                {
                    Owner = Window.GetWindow(this)
                };
                viewer.ShowDialog();
            }
        }

        private void HtmlLeftCard_DragOver(object sender, DragEventArgs e)
        {
            if (e.Data.GetDataPresent(DataFormats.FileDrop))
                e.Effects = DragDropEffects.Copy;
            else
                e.Effects = DragDropEffects.None;
            e.Handled = true;
        }

        private async void HtmlLeftCard_Drop(object sender, DragEventArgs e)
        {
            if (!e.Data.GetDataPresent(DataFormats.FileDrop)) return;
            var files = (string[])e.Data.GetData(DataFormats.FileDrop);
            if (files == null || files.Length == 0) return;

            string filePath = files[0];
            string ext = Path.GetExtension(filePath).ToLowerInvariant();

            if (ext is ".png" or ".jpg" or ".jpeg" or ".webp" or ".bmp")
            {
                try
                {
                    byte[] bytes = File.ReadAllBytes(filePath);
                    LoadAttachedImage(bytes);
                }
                catch (Exception ex)
                {
                    System.Windows.MessageBox.Show($"Không thể đọc ảnh: {ex.Message}", "Lỗi", MessageBoxButton.OK, MessageBoxImage.Error);
                }
            }
            else if (ext is ".html" or ".htm" or ".txt")
            {
                try
                {
                    string code = File.ReadAllText(filePath, Encoding.UTF8);
                    TxtHtmlCode.Text = HtmlModelCodeExtractor.ExtractHtmlCode(code);
                    await RunModelAsync();
                }
                catch (Exception ex)
                {
                    System.Windows.MessageBox.Show($"Không thể đọc tệp: {ex.Message}", "Lỗi", MessageBoxButton.OK, MessageBoxImage.Error);
                }
            }
        }

        #endregion

        #region FILE I/O & TIỆN ÍCH

        private void BtnSaveHtml_Click(object sender, RoutedEventArgs e)
        {
            string html = TxtHtmlCode.Text.Trim();
            if (string.IsNullOrWhiteSpace(html)) return;

            var sfd = new SaveFileDialog
            {
                Filter = "HTML Files (*.html)|*.html|All Files (*.*)|*.*",
                FileName = $"MoHinh3D_{DateTime.Now:yyyyMMdd_HHmmss}.html",
                Title = "Lưu tệp mô hình mô phỏng HTML 3D"
            };

            if (sfd.ShowDialog() == true)
            {
                try
                {
                    File.WriteAllText(sfd.FileName, html, Encoding.UTF8);
                    InfoHtmlNotification.Severity = InfoBarSeverity.Success;
                    InfoHtmlNotification.Title = "Đã lưu tệp HTML";
                    InfoHtmlNotification.Message = $"Tệp đã lưu thành công tại: {sfd.FileName}";
                    InfoHtmlNotification.IsOpen = true;
                }
                catch (Exception ex)
                {
                    System.Windows.MessageBox.Show($"Không thể lưu file: {ex.Message}", "Lỗi", MessageBoxButton.OK, MessageBoxImage.Error);
                }
            }
        }

        private async void BtnOpenHtml_Click(object sender, RoutedEventArgs e)
        {
            var ofd = new OpenFileDialog
            {
                Filter = "HTML Files (*.html;*.htm)|*.html;*.htm|All Files (*.*)|*.*",
                Title = "Mở tệp mô hình mô phỏng HTML 3D"
            };

            if (ofd.ShowDialog() == true)
            {
                try
                {
                    string content = File.ReadAllText(ofd.FileName, Encoding.UTF8);
                    TxtHtmlCode.Text = HtmlModelCodeExtractor.ExtractHtmlCode(content);
                    await RunModelAsync();
                }
                catch (Exception ex)
                {
                    System.Windows.MessageBox.Show($"Không thể mở file: {ex.Message}", "Lỗi", MessageBoxButton.OK, MessageBoxImage.Error);
                }
            }
        }

        private void BtnCleanCode_Click(object sender, RoutedEventArgs e)
        {
            string code = TxtHtmlCode.Text.Trim();
            if (!string.IsNullOrWhiteSpace(code))
            {
                TxtHtmlCode.Text = HtmlModelCodeExtractor.ExtractHtmlCode(code);
            }
        }

        private void BtnClear_Click(object sender, RoutedEventArgs e)
        {
            TxtHtmlCode.Text = string.Empty;
            PanelPlaceholder.Visibility = Visibility.Visible;
            TxtModelStats.Text = "Đã xóa trắng";
        }

        private void TxtPrompt_KeyDown(object sender, KeyEventArgs e)
        {
            if (e.Key == Key.Enter)
            {
                BtnAiGenerate_Click(BtnAiGenerate, new RoutedEventArgs());
                e.Handled = true;
            }
        }

        private async void HtmlModelView_PreviewKeyDown(object sender, KeyEventArgs e)
        {
            if (e.Key == Key.F5)
            {
                await RunModelAsync();
                e.Handled = true;
            }
            else if (e.Key == Key.Enter && (Keyboard.Modifiers & ModifierKeys.Control) == ModifierKeys.Control)
            {
                await RunModelAsync();
                e.Handled = true;
            }
            else if (e.Key == Key.G && (Keyboard.Modifiers & ModifierKeys.Control) == ModifierKeys.Control && (Keyboard.Modifiers & ModifierKeys.Shift) == ModifierKeys.Shift)
            {
                BtnAiGenerate_Click(BtnAiGenerate, new RoutedEventArgs());
                e.Handled = true;
            }
            else if (e.Key == Key.V && (Keyboard.Modifiers & ModifierKeys.Control) == ModifierKeys.Control && System.Windows.Clipboard.ContainsImage())
            {
                BtnPasteImage_Click(BtnPasteImage, new RoutedEventArgs());
                e.Handled = true;
            }
            else if (e.Key == Key.B && (Keyboard.Modifiers & ModifierKeys.Control) == ModifierKeys.Control)
            {
                BtnOpenModelBank_Click(BtnOpenModelBank, new RoutedEventArgs());
                e.Handled = true;
            }
            else if (e.Key == Key.S && (Keyboard.Modifiers & ModifierKeys.Control) == ModifierKeys.Control && (Keyboard.Modifiers & ModifierKeys.Shift) == ModifierKeys.Shift)
            {
                BtnSaveModelBank_Click(BtnSaveModelBank, new RoutedEventArgs());
                e.Handled = true;
            }
            else if (e.Key == Key.S && (Keyboard.Modifiers & ModifierKeys.Control) == ModifierKeys.Control)
            {
                BtnSaveHtml_Click(BtnSaveHtml, new RoutedEventArgs());
                e.Handled = true;
            }
        }

        #endregion
    }
}
