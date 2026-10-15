using System;
using System.IO;
using System.Linq;
using System.Threading.Tasks;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Input;
using System.Windows.Media;
using System.Windows.Media.Animation;
using System.Windows.Media.Imaging;
using MatrixExamAI.Desktop.Services;
using MatrixExamAI.Shared.AI;
using MatrixExamAI.Shared.Models;
using MatrixExamAI.Shared.Tikz;

namespace MatrixExamAI.Desktop.Views
{
    public partial class TikzView : UserControl
    {
        private readonly TikzCompilerService _compilerService = new TikzCompilerService();
        private byte[]? _attachedImageBytes;
        private string? _currentGeneratedImagePath;
        private string _lastFigurePrompt = string.Empty;
        private System.Threading.CancellationTokenSource? _activeTikzCts;
        private System.Windows.Threading.DispatcherTimer? _compileTimer;
        private System.Diagnostics.Stopwatch _compileStopwatch = new System.Diagnostics.Stopwatch();
        private Brush? _originalBorderBrush;

        public enum TikzLayoutMode
        {
            Split,
            ImageOnly,
            CodeOnly
        }

        private TikzLayoutMode _currentLayoutMode = TikzLayoutMode.Split;
        private GridLength _lastCodeWidth = new GridLength(3.2, GridUnitType.Star);
        private GridLength _lastPreviewWidth = new GridLength(6.8, GridUnitType.Star);

        private ColumnDefinition ColCode => GridSplitContainer.ColumnDefinitions[0];
        private ColumnDefinition ColSplitter => GridSplitContainer.ColumnDefinitions[1];
        private ColumnDefinition ColPreview => GridSplitContainer.ColumnDefinitions[2];

        public TikzView()
        {
            InitializeComponent();
            CheckToolchainStatus();
            InitializeTemplateLibrary();
            Loaded += (s, e) => InitializeLayout();
        }

        private void InitializeLayout()
        {
            try
            {
                ColCode.Width = new GridLength(3.2, GridUnitType.Star);
                ColPreview.Width = new GridLength(6.8, GridUnitType.Star);
                UpdateModeButtonStyles();
            }
            catch { }
        }

        public void SetLayoutMode(TikzLayoutMode mode)
        {
            _currentLayoutMode = mode;
            switch (mode)
            {
                case TikzLayoutMode.ImageOnly:
                    if (ColCode.Width.Value > 0 && ColCode.Width.GridUnitType == GridUnitType.Star)
                    {
                        _lastCodeWidth = ColCode.Width;
                        _lastPreviewWidth = ColPreview.Width;
                    }
                    ColCode.MinWidth = 0;
                    ColCode.Width = new GridLength(0);
                    ColSplitter.Width = new GridLength(0);
                    ColPreview.MinWidth = 300;
                    ColPreview.Width = new GridLength(1, GridUnitType.Star);
                    CardCode.Visibility = Visibility.Collapsed;
                    SplitterTikz.Visibility = Visibility.Collapsed;
                    CardPreview.Visibility = Visibility.Visible;
                    BtnExpandCode.Visibility = Visibility.Visible;
                    BtnExpandPreviewFromCode.Visibility = Visibility.Collapsed;
                    break;

                case TikzLayoutMode.CodeOnly:
                    if (ColCode.Width.Value > 0 && ColCode.Width.GridUnitType == GridUnitType.Star)
                    {
                        _lastCodeWidth = ColCode.Width;
                        _lastPreviewWidth = ColPreview.Width;
                    }
                    ColPreview.MinWidth = 0;
                    ColPreview.Width = new GridLength(0);
                    ColSplitter.Width = new GridLength(0);
                    ColCode.MinWidth = 300;
                    ColCode.Width = new GridLength(1, GridUnitType.Star);
                    CardPreview.Visibility = Visibility.Collapsed;
                    SplitterTikz.Visibility = Visibility.Collapsed;
                    CardCode.Visibility = Visibility.Visible;
                    BtnExpandCode.Visibility = Visibility.Collapsed;
                    BtnExpandPreviewFromCode.Visibility = Visibility.Visible;
                    break;

                case TikzLayoutMode.Split:
                default:
                    ColCode.MinWidth = 240;
                    ColPreview.MinWidth = 300;
                    ColCode.Width = _lastCodeWidth.Value > 0 ? _lastCodeWidth : new GridLength(3.2, GridUnitType.Star);
                    ColSplitter.Width = new GridLength(8);
                    ColPreview.Width = _lastPreviewWidth.Value > 0 ? _lastPreviewWidth : new GridLength(6.8, GridUnitType.Star);
                    CardCode.Visibility = Visibility.Visible;
                    CardPreview.Visibility = Visibility.Visible;
                    SplitterTikz.Visibility = Visibility.Visible;
                    BtnExpandCode.Visibility = Visibility.Collapsed;
                    BtnExpandPreviewFromCode.Visibility = Visibility.Collapsed;
                    break;
            }
            UpdateModeButtonStyles();
        }

        private void UpdateModeButtonStyles()
        {
            if (BtnModeSplit == null || BtnModeImageOnly == null || BtnModeCodeOnly == null) return;

            var activeBrush = new SolidColorBrush(Color.FromRgb(139, 92, 246)); // #8B5CF6 Accent
            var inactiveBrush = Brushes.Transparent;
            var textActiveBrush = Brushes.White;
            var textInactiveBrush = TryFindResource("TextFillColorSecondaryBrush") as Brush ?? Brushes.Gray;

            BtnModeSplit.Background = _currentLayoutMode == TikzLayoutMode.Split ? activeBrush : inactiveBrush;
            BtnModeSplit.Foreground = _currentLayoutMode == TikzLayoutMode.Split ? textActiveBrush : textInactiveBrush;

            BtnModeImageOnly.Background = _currentLayoutMode == TikzLayoutMode.ImageOnly ? activeBrush : inactiveBrush;
            BtnModeImageOnly.Foreground = _currentLayoutMode == TikzLayoutMode.ImageOnly ? textActiveBrush : textInactiveBrush;

            BtnModeCodeOnly.Background = _currentLayoutMode == TikzLayoutMode.CodeOnly ? activeBrush : inactiveBrush;
            BtnModeCodeOnly.Foreground = _currentLayoutMode == TikzLayoutMode.CodeOnly ? textActiveBrush : textInactiveBrush;
        }

        private void BtnCollapseCode_Click(object sender, RoutedEventArgs e) => SetLayoutMode(TikzLayoutMode.ImageOnly);
        private void BtnExpandCode_Click(object sender, RoutedEventArgs e) => SetLayoutMode(TikzLayoutMode.Split);
        private void BtnExpandPreviewFromCode_Click(object sender, RoutedEventArgs e) => SetLayoutMode(TikzLayoutMode.Split);

        private void BtnModeSplit_Click(object sender, RoutedEventArgs e) => SetLayoutMode(TikzLayoutMode.Split);
        private void BtnModeImageOnly_Click(object sender, RoutedEventArgs e) => SetLayoutMode(TikzLayoutMode.ImageOnly);
        private void BtnModeCodeOnly_Click(object sender, RoutedEventArgs e) => SetLayoutMode(TikzLayoutMode.CodeOnly);

        public void ToggleCodePanel()
        {
            if (_currentLayoutMode == TikzLayoutMode.ImageOnly)
                SetLayoutMode(TikzLayoutMode.Split);
            else
                SetLayoutMode(TikzLayoutMode.ImageOnly);
        }

        private void CheckToolchainStatus()
        {
            try
            {
                var status = TexToolchainDiscovery.Discover();
                if (status.IsPdfLatexAvailable)
                {
                    TxtTexStatus.Text = "pdflatex: Sẵn sàng";
                }
                else
                {
                    TxtTexStatus.Text = "Chưa phát hiện pdflatex (Chế độ xem trước Fallback)";
                }
            }
            catch
            {
                TxtTexStatus.Text = "Chế độ xem trước Tiêu chuẩn";
            }
        }

        /// <summary>
        /// Khởi tạo và nạp dữ liệu thư viện mẫu TikZ phong phú vào 2 ComboBox cascading.
        /// </summary>
        private void InitializeTemplateLibrary()
        {
            try
            {
                CmbTemplateCategory.ItemsSource = TikzTemplateLibrary.Categories;
                CmbTemplateCategory.DisplayMemberPath = "Name";
                if (TikzTemplateLibrary.Categories.Count > 0)
                {
                    CmbTemplateCategory.SelectedIndex = 0;
                }
            }
            catch (Exception ex)
            {
                TxtDiagramStats.Text = $"Lỗi nạp thư viện mẫu: {ex.Message}";
            }
        }

        private void CmbTemplateCategory_SelectionChanged(object sender, SelectionChangedEventArgs e)
        {
            if (CmbTemplateCategory.SelectedItem is TikzTemplateCategory cat)
            {
                CmbTemplateItem.ItemsSource = cat.Templates;
                CmbTemplateItem.DisplayMemberPath = "Title";
                if (cat.Templates.Count > 0)
                {
                    CmbTemplateItem.SelectedIndex = 0;
                }
            }
        }

        private void CmbTemplateItem_SelectionChanged(object sender, SelectionChangedEventArgs e)
        {
            if (CmbTemplateItem.SelectedItem is TikzTemplate tpl)
            {
                TxtTikzCode.Text = tpl.Code;
                TxtDiagramStats.Text = $"Đã nạp mẫu: {tpl.Title} ({tpl.CategoryName})";
                SyncDiagramTypeForTemplate(tpl);
            }
        }

        /// <summary>
        /// Tự động đồng bộ hóa ComboBox DiagramType phù hợp với danh mục mẫu đang chọn.
        /// </summary>
        private void SyncDiagramTypeForTemplate(TikzTemplate tpl)
        {
            switch (tpl.CategoryId)
            {
                case "tables":
                    if (tpl.Tags != null && tpl.Tags.Any(t => t.Equals("bxd", StringComparison.OrdinalIgnoreCase) || t.Contains("xét dấu")))
                    {
                        CmbDiagramType.SelectedIndex = (int)DiagramType.BXD;
                    }
                    else
                    {
                        CmbDiagramType.SelectedIndex = (int)DiagramType.BBT;
                    }
                    break;
                case "graphs":
                    CmbDiagramType.SelectedIndex = (int)DiagramType.DoThi;
                    break;
                case "solid_3d":
                    CmbDiagramType.SelectedIndex = (int)DiagramType.HinhKhongGian;
                    break;
                case "plane_2d":
                case "misc":
                default:
                    CmbDiagramType.SelectedIndex = (int)DiagramType.Custom;
                    break;
            }
        }

        /// <summary>
        /// Xử lý hệ thống phím tắt công thái học toàn diện cho phân hệ TikzView.
        /// </summary>
        private void TikzView_PreviewKeyDown(object sender, KeyEventArgs e)
        {
            // Esc: Tạm dừng / Dừng lại tác vụ đang thực thi, hoặc khôi phục chế độ xem Split nếu đang ẩn
            if (e.Key == Key.Escape)
            {
                if (BtnStopTikzAction.Visibility == Visibility.Visible)
                {
                    BtnStopTikzAction_Click(BtnStopTikzAction, new RoutedEventArgs());
                    e.Handled = true;
                    return;
                }
            }

            // Ctrl + [ hoặc F10: Đóng / Mở nhanh khung mã TikZ (ưu ái bên hình ảnh)
            if ((e.Key == Key.OemOpenBrackets && (Keyboard.Modifiers & ModifierKeys.Control) == ModifierKeys.Control) || e.Key == Key.F10)
            {
                ToggleCodePanel();
                e.Handled = true;
                return;
            }

            // F5 hoặc Ctrl + Enter: Biên dịch hình vẽ
            if (e.Key == Key.F5 || (e.Key == Key.Enter && (Keyboard.Modifiers & ModifierKeys.Control) == ModifierKeys.Control))
            {
                BtnCompile_Click(BtnCompile, new RoutedEventArgs());
                e.Handled = true;
                return;
            }

            // F11: Mở cửa sổ xem hình chi tiết toàn màn hình
            if (e.Key == Key.F11)
            {
                BtnOpenViewerWindow_Click(BtnOpenViewerWindow, new RoutedEventArgs());
                e.Handled = true;
                return;
            }

            // Ctrl + Shift + G: AI sinh mã TikZ
            if (e.Key == Key.G && (Keyboard.Modifiers & (ModifierKeys.Control | ModifierKeys.Shift)) == (ModifierKeys.Control | ModifierKeys.Shift))
            {
                BtnGenerateTikz_Click(BtnGenerateTikz, new RoutedEventArgs());
                e.Handled = true;
                return;
            }

            // Ctrl + Shift + W: Sao chép hình ảnh chất lượng cao để chèn vào Microsoft Word
            if (e.Key == Key.W && (Keyboard.Modifiers & (ModifierKeys.Control | ModifierKeys.Shift)) == (ModifierKeys.Control | ModifierKeys.Shift))
            {
                BtnInsertWord_Click(BtnInsertWord, new RoutedEventArgs());
                e.Handled = true;
                return;
            }

            // Ctrl + Shift + S: Lưu hình vào kho hình vẽ TikZ
            if (e.Key == Key.S && (Keyboard.Modifiers & (ModifierKeys.Control | ModifierKeys.Shift)) == (ModifierKeys.Control | ModifierKeys.Shift))
            {
                BtnSaveFigureBank_Click(BtnSaveFigureBank, new RoutedEventArgs());
                e.Handled = true;
                return;
            }

            // Ctrl + B: Mở duyệt kho hình vẽ TikZ
            if (e.Key == Key.B && (Keyboard.Modifiers & ModifierKeys.Control) == ModifierKeys.Control && (Keyboard.Modifiers & ModifierKeys.Shift) == 0 && !TxtTikzCode.IsKeyboardFocused)
            {
                BtnOpenFigureBank_Click(BtnOpenFigureBank, new RoutedEventArgs());
                e.Handled = true;
                return;
            }

            // Ctrl + S (không có Shift): Lưu file ảnh PNG 600 DPI hoặc vector SVG
            if (e.Key == Key.S && (Keyboard.Modifiers & ModifierKeys.Control) == ModifierKeys.Control && (Keyboard.Modifiers & ModifierKeys.Shift) == 0)
            {
                BtnSavePng_Click(BtnSavePng, new RoutedEventArgs());
                e.Handled = true;
                return;
            }

            // Ctrl + V: Dán ảnh mẫu từ Clipboard khi TextBox không focus văn bản, hoặc Clipboard có dữ liệu ảnh
            if (e.Key == Key.V && (Keyboard.Modifiers & ModifierKeys.Control) == ModifierKeys.Control && (Keyboard.Modifiers & ModifierKeys.Shift) == 0)
            {
                bool isTextEditorFocused = TxtTikzCode.IsKeyboardFocused;
                if (!isTextEditorFocused && SafeClipboard.ContainsImage())
                {
                    BtnPasteImage_Click(BtnPasteImage, new RoutedEventArgs());
                    e.Handled = true;
                    return;
                }
                else if (isTextEditorFocused && SafeClipboard.ContainsImage() && !SafeClipboard.ContainsText())
                {
                    BtnPasteImage_Click(BtnPasteImage, new RoutedEventArgs());
                    e.Handled = true;
                    return;
                }
            }
        }

        private void BtnPasteImage_Click(object sender, RoutedEventArgs e)
        {
            if (SafeClipboard.ContainsImage())
            {
                var image = SafeClipboard.GetImage();
                if (image != null)
                {
                    ImgAttachedPreview.Source = image;
                    BorderAttachedImage.Visibility = Visibility.Visible;

                    // Chuyển đổi sang byte array cho AI Vision Multimodal
                    using var ms = new MemoryStream();
                    var encoder = new PngBitmapEncoder();
                    encoder.Frames.Add(BitmapFrame.Create(image));
                    encoder.Save(ms);
                    _attachedImageBytes = ms.ToArray();

                    InfoTikzNotification.Severity = Wpf.Ui.Controls.InfoBarSeverity.Informational;
                    InfoTikzNotification.Title = "Đã dán ảnh thành công";
                    InfoTikzNotification.Message = "Ảnh bài toán đã sẵn sàng. Bấm 'AI Sinh mã TikZ' (Ctrl+Shift+G) để mô hình phân tích.";
                    InfoTikzNotification.IsOpen = true;
                }
            }
            else
            {
                MessageBox.Show("Không có hình ảnh nào trong Clipboard. Hãy chụp màn hình (Win+Shift+S) rồi dán lại (Ctrl+V).", "Chưa có ảnh", MessageBoxButton.OK, MessageBoxImage.Information);
            }
        }

        private void BtnRemoveImage_Click(object sender, RoutedEventArgs e)
        {
            BorderAttachedImage.Visibility = Visibility.Collapsed;
            _attachedImageBytes = null;
            ImgAttachedPreview.Source = null;
        }

        private void AttachedImage_Click(object sender, MouseButtonEventArgs e)
        {
            if (ImgAttachedPreview.Source != null)
            {
                var viewer = new TikzImagePreviewWindow(ImgAttachedPreview.Source, null, 300, "Ảnh mẫu bài toán đính kèm")
                {
                    Owner = Window.GetWindow(this)
                };
                viewer.ShowDialog();
            }
        }

        private void TikzLeftCard_DragOver(object sender, DragEventArgs e)
        {
            if (e.Data.GetDataPresent(DataFormats.FileDrop))
            {
                e.Effects = DragDropEffects.Copy;
            }
            else
            {
                e.Effects = DragDropEffects.None;
            }
            e.Handled = true;
        }

        private void TikzLeftCard_Drop(object sender, DragEventArgs e)
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

                    InfoTikzNotification.Severity = Wpf.Ui.Controls.InfoBarSeverity.Informational;
                    InfoTikzNotification.Title = "Đã nhận ảnh mẫu";
                    InfoTikzNotification.Message = $"File '{Path.GetFileName(filePath)}' đã sẵn sàng. Bấm 'AI vẽ' (Ctrl+Shift+G) để vẽ hình TikZ.";
                    InfoTikzNotification.IsOpen = true;
                }
                catch (Exception ex)
                {
                    MessageBox.Show($"Không thể đọc ảnh: {ex.Message}", "Lỗi nạp ảnh", MessageBoxButton.OK, MessageBoxImage.Error);
                }
            }
            else if (ext is ".tex" or ".txt")
            {
                try
                {
                    string code = File.ReadAllText(filePath);
                    TxtTikzCode.Text = TikzCodeExtractor.ExtractTikzCode(code);
                    InfoTikzNotification.Severity = Wpf.Ui.Controls.InfoBarSeverity.Success;
                    InfoTikzNotification.Title = "Đã nạp mã LaTeX TikZ";
                    InfoTikzNotification.Message = $"File '{Path.GetFileName(filePath)}' đã nạp thành công. Đang tự động biên dịch...";
                    InfoTikzNotification.IsOpen = true;
                    BtnCompile_Click(this, new RoutedEventArgs());
                }
                catch (Exception ex)
                {
                    MessageBox.Show($"Không thể đọc file: {ex.Message}", "Lỗi đọc file", MessageBoxButton.OK, MessageBoxImage.Error);
                }
            }
        }

        private void TxtFigurePrompt_KeyDown(object sender, KeyEventArgs e)
        {
            if (e.Key == Key.Enter)
            {
                BtnGenerateTikz_Click(BtnGenerateTikz, new RoutedEventArgs());
                e.Handled = true;
            }
        }

        private void BtnGenerateTikz_Click(object sender, RoutedEventArgs e)
        {
            // Bấm "AI vẽ" (Ctrl+Shift+G) luôn mở hộp thoại AI Vẽ Hình TikZ chuẩn bản cũ (tab_tikz.py: _AIPasteDrawDialog)
            var dlg = new AiDrawPromptDialog(TxtFigurePrompt.Text, _attachedImageBytes)
            {
                Owner = Window.GetWindow(this)
            };

            if (dlg.ShowDialog() == true && !string.IsNullOrWhiteSpace(dlg.ResultTikzCode))
            {
                TxtTikzCode.Text = dlg.ResultTikzCode;
                _lastFigurePrompt = dlg.ResultDescription;
                TxtFigurePrompt.Text = dlg.ResultDescription;

                if (dlg.ResultImageBytes != null && dlg.ResultImageBytes.Length > 0)
                {
                    _attachedImageBytes = dlg.ResultImageBytes;
                }

                InfoTikzNotification.Severity = Wpf.Ui.Controls.InfoBarSeverity.Success;
                InfoTikzNotification.Title = "AI Vẽ hình hoàn tất";
                InfoTikzNotification.Message = "Đã sinh mã TikZ chuẩn toán học. Đang tự động biên dịch xem trước...";
                InfoTikzNotification.IsOpen = true;

                BtnCompile_Click(this, new RoutedEventArgs());
            }
        }

        private void BtnAiRedraw_Click(object sender, RoutedEventArgs e)
        {
            if (string.IsNullOrWhiteSpace(_lastFigurePrompt))
            {
                if (!string.IsNullOrWhiteSpace(TxtFigurePrompt.Text))
                {
                    _lastFigurePrompt = TxtFigurePrompt.Text.Trim();
                }
                else
                {
                    MessageBox.Show("Chưa có mô tả hình vẽ nào trước đó để vẽ lại.\nHãy nhập mô tả vào ô đề bài hoặc bấm 'AI vẽ' để bắt đầu.", "Chưa có mô tả", MessageBoxButton.OK, MessageBoxImage.Information);
                    return;
                }
            }

            TxtFigurePrompt.Text = _lastFigurePrompt;
            BtnGenerateTikz_Click(BtnGenerateTikz, new RoutedEventArgs());
        }

        private async void BtnAiOptimize_Click(object sender, RoutedEventArgs e)
        {
            string code = TxtTikzCode.Text.Trim();
            if (string.IsNullOrWhiteSpace(code))
            {
                MessageBox.Show("Chưa có mã TikZ trong trình soạn thảo để tối ưu hóa.", "Thông báo", MessageBoxButton.OK, MessageBoxImage.Information);
                return;
            }

            BtnAiOptimize.IsEnabled = false;
            InfoTikzNotification.Severity = Wpf.Ui.Controls.InfoBarSeverity.Informational;
            InfoTikzNotification.Title = "Đang tối ưu mã TikZ";
            InfoTikzNotification.Message = "AI đang chuẩn hóa tọa độ, loại bỏ lệnh thừa và làm sạch cú pháp...";
            InfoTikzNotification.IsOpen = true;

            try
            {
                string prompt = "Bạn là chuyên gia LaTeX TikZ. Hãy tối ưu hóa đoạn mã TikZ dưới đây: chuẩn hóa tọa độ, loại bỏ các lệnh rác/dư thừa, đảm bảo nét vẽ và nhãn sắc nét, giữ nguyên ý nghĩa toán học. Chỉ trả về khối mã TikZ sạch bắt đầu bằng \\begin{tikzpicture} và kết thúc bằng \\end{tikzpicture}:\n\n" + code;
                var result = await DesktopGeminiFactory.ExecutePromptAsync(prompt);
                if (result.Success && !string.IsNullOrWhiteSpace(result.Content))
                {
                    string clean = TikzCodeExtractor.ExtractTikzCode(result.Content);
                    if (!string.IsNullOrWhiteSpace(clean))
                    {
                        TxtTikzCode.Text = clean;
                        InfoTikzNotification.Severity = Wpf.Ui.Controls.InfoBarSeverity.Success;
                        InfoTikzNotification.Title = "Tối ưu hóa hoàn tất";
                        InfoTikzNotification.Message = "Đã tối ưu mã TikZ. Tự động biên dịch lại hình ảnh.";
                        BtnCompile_Click(this, new RoutedEventArgs());
                    }
                }
                else
                {
                    InfoTikzNotification.Severity = Wpf.Ui.Controls.InfoBarSeverity.Warning;
                    InfoTikzNotification.Title = "Chưa tối ưu được";
                    InfoTikzNotification.Message = result.ErrorMessage ?? "Không nhận được phản hồi từ AI.";
                }
            }
            catch (Exception ex)
            {
                InfoTikzNotification.Severity = Wpf.Ui.Controls.InfoBarSeverity.Error;
                InfoTikzNotification.Title = "Lỗi tối ưu";
                InfoTikzNotification.Message = ex.Message;
            }
            finally
            {
                BtnAiOptimize.IsEnabled = true;
            }
        }

        private void BtnCleanTikzCode_Click(object sender, RoutedEventArgs e)
        {
            string code = TxtTikzCode.Text;
            if (string.IsNullOrWhiteSpace(code)) return;

            string clean = TikzCodeExtractor.ExtractTikzCode(code);
            if (!string.IsNullOrWhiteSpace(clean))
            {
                TxtTikzCode.Text = clean;
                InfoTikzNotification.Severity = Wpf.Ui.Controls.InfoBarSeverity.Success;
                InfoTikzNotification.Title = "Đã lọc mã sạch";
                InfoTikzNotification.Message = "Đã loại bỏ mã rác và văn bản thừa ngoài khối tikzpicture.";
                InfoTikzNotification.IsOpen = true;
            }
        }

        private void BtnClearTikz_Click(object sender, RoutedEventArgs e)
        {
            if (string.IsNullOrWhiteSpace(TxtTikzCode.Text) && string.IsNullOrWhiteSpace(TxtFigurePrompt.Text) && _attachedImageBytes == null)
            {
                return;
            }

            var result = MessageBox.Show(
                "Bạn có chắc muốn xóa trắng mã soạn thảo và hình vẽ hiện tại để bắt đầu vẽ hình mới?",
                "Xác nhận xóa trắng",
                MessageBoxButton.YesNo,
                MessageBoxImage.Question);

            if (result == MessageBoxResult.Yes)
            {
                TxtTikzCode.Text = string.Empty;
                TxtFigurePrompt.Text = string.Empty;
                BtnRemoveImage_Click(sender, e);
                ImgDiagramPreview.Source = null;
                PanelPreviewPlaceholder.Visibility = Visibility.Visible;
                TxtDiagramStats.Text = "Đã xóa trắng trình soạn thảo.";
                _currentGeneratedImagePath = null;

                InfoTikzNotification.Severity = Wpf.Ui.Controls.InfoBarSeverity.Informational;
                InfoTikzNotification.Title = "Đã xóa trắng";
                InfoTikzNotification.Message = "Trình soạn thảo đã sẵn sàng cho hình vẽ mới.";
                InfoTikzNotification.IsOpen = true;
            }
        }

        private void BtnSaveFigureBank_Click(object sender, RoutedEventArgs e)
        {
            string code = TxtTikzCode.Text.Trim();
            if (string.IsNullOrWhiteSpace(code))
            {
                MessageBox.Show("Trình soạn thảo chưa có mã TikZ để lưu vào kho.", "Chưa có mã TikZ", MessageBoxButton.OK, MessageBoxImage.Information);
                return;
            }

            string defaultTitle = !string.IsNullOrWhiteSpace(TxtFigurePrompt.Text)
                ? TxtFigurePrompt.Text.Trim()
                : $"Hình TikZ {DateTime.Now:yyyy-MM-dd HH:mm}";

            bool hasImage = !string.IsNullOrEmpty(_currentGeneratedImagePath) && File.Exists(_currentGeneratedImagePath);

            var dlg = new SaveFigureDialog(defaultTitle, hasImage: hasImage)
            {
                Owner = Window.GetWindow(this)
            };

            if (dlg.ShowDialog() == true)
            {
                try
                {
                    var entry = FigureBankService.SaveFigure(
                        tikzCode: code,
                        title: dlg.ResultTitle,
                        description: dlg.ResultDescription,
                        tags: dlg.ResultTags,
                        source: "manual",
                        pngSourcePath: dlg.ResultSavePng && hasImage ? _currentGeneratedImagePath : null
                    );

                    InfoTikzNotification.Severity = Wpf.Ui.Controls.InfoBarSeverity.Success;
                    InfoTikzNotification.Title = "Đã lưu vào kho hình";
                    InfoTikzNotification.Message = $"Hình '[{entry.Id}] {entry.Title}' đã được lưu an toàn vào kho hình vẽ.";
                    InfoTikzNotification.IsOpen = true;
                }
                catch (Exception ex)
                {
                    MessageBox.Show($"Lỗi lưu hình vào kho: {ex.Message}", "Lỗi lưu kho", MessageBoxButton.OK, MessageBoxImage.Error);
                }
            }
        }

        private void BtnOpenFigureBank_Click(object sender, RoutedEventArgs e)
        {
            var dlg = new FigureBankDialog
            {
                Owner = Window.GetWindow(this)
            };

            if (dlg.ShowDialog() == true && !string.IsNullOrWhiteSpace(dlg.LoadedTikzCode))
            {
                TxtTikzCode.Text = dlg.LoadedTikzCode;
                TxtFigurePrompt.Text = dlg.LoadedTitle;

                if (!string.IsNullOrEmpty(dlg.LoadedPngPath) && File.Exists(dlg.LoadedPngPath))
                {
                    try
                    {
                        using var stream = File.OpenRead(dlg.LoadedPngPath);
                        var bi = new BitmapImage();
                        bi.BeginInit();
                        bi.CacheOption = BitmapCacheOption.OnLoad;
                        bi.StreamSource = stream;
                        bi.EndInit();
                        bi.Freeze();

                        ImgDiagramPreview.Source = bi;
                        _currentGeneratedImagePath = dlg.LoadedPngPath;
                        PanelPreviewPlaceholder.Visibility = Visibility.Collapsed;
                        TxtDiagramStats.Text = $"Đã nạp sẵn từ kho: {bi.PixelWidth}x{bi.PixelHeight} px — '{dlg.LoadedTitle}'";
                        PlayNewImageInsertAnimation();
                    }
                    catch
                    {
                        // Fallback tự động biên dịch lại nếu ảnh lỗi
                        BtnCompile_Click(this, new RoutedEventArgs());
                    }
                }
                else
                {
                    // Tự động biên dịch nếu chưa có ảnh PNG
                    BtnCompile_Click(this, new RoutedEventArgs());
                }

                InfoTikzNotification.Severity = Wpf.Ui.Controls.InfoBarSeverity.Success;
                InfoTikzNotification.Title = "Đã nạp hình từ kho";
                InfoTikzNotification.Message = $"Đã nạp thành công '{dlg.LoadedTitle}' vào trình soạn thảo.";
                InfoTikzNotification.IsOpen = true;
            }
        }

        private void SafeDispatch(Action action)
        {
            if (Dispatcher == null || Dispatcher.HasShutdownStarted || Dispatcher.HasShutdownFinished) return;
            if (Dispatcher.CheckAccess())
            {
                action();
            }
            else
            {
                try
                {
                    Dispatcher.Invoke(action);
                }
                catch (Exception)
                {
                    // Dispatcher terminated or inaccessible
                }
            }
        }

        private double _currentZoom = 1.0;
        private bool _isDragging = false;
        private Point _lastMousePos;
        private string? _lastCompileError;

        private void SetZoom(double zoom)
        {
            _currentZoom = Math.Clamp(zoom, 0.05, 10.0);
            if (ImgScaleTransform != null)
            {
                ImgScaleTransform.ScaleX = _currentZoom;
                ImgScaleTransform.ScaleY = _currentZoom;
            }
            if (TxtZoomLevel != null)
            {
                TxtZoomLevel.Text = $"Thu phóng: {_currentZoom * 100:0}%";
            }
        }

        private void BtnZoomIn_Click(object sender, RoutedEventArgs e) => SetZoom(_currentZoom * 1.25);
        private void BtnZoomOut_Click(object sender, RoutedEventArgs e) => SetZoom(_currentZoom / 1.25);
        private void BtnZoomReset_Click(object sender, RoutedEventArgs e)
        {
            if (ImgTranslateTransform != null)
            {
                ImgTranslateTransform.X = 0;
                ImgTranslateTransform.Y = 0;
            }
            SetZoom(1.0);
        }

        private void BtnZoomFit_Click(object sender, RoutedEventArgs e)
        {
            if (ImgTranslateTransform != null)
            {
                ImgTranslateTransform.X = 0;
                ImgTranslateTransform.Y = 0;
            }
            if (ImgDiagramPreview.Source is BitmapSource bs && bs.PixelWidth > 0 && bs.PixelHeight > 0 && ScrollDiagramContainer != null)
            {
                double imgW = bs.Width > 0 ? bs.Width : bs.PixelWidth;
                double imgH = bs.Height > 0 ? bs.Height : bs.PixelHeight;
                double availW = Math.Max(50, ScrollDiagramContainer.ActualWidth - 32);
                double availH = Math.Max(50, ScrollDiagramContainer.ActualHeight - 32);
                double fit = Math.Min(availW / imgW, availH / imgH) * 0.95;
                if (fit > 0.05 && fit < 10.0) SetZoom(fit);
                else SetZoom(1.0);
            }
            else
            {
                SetZoom(1.0);
            }
        }

        private void ScrollDiagramContainer_PreviewMouseWheel(object sender, MouseWheelEventArgs e)
        {
            double factor = e.Delta > 0 ? 1.15 : 0.85;
            SetZoom(_currentZoom * factor);
            e.Handled = true;
        }

        private void Canvas_MouseDown(object sender, MouseButtonEventArgs e)
        {
            if (e.ChangedButton == MouseButton.Left)
            {
                if (e.ClickCount == 2)
                {
                    BtnOpenViewerWindow_Click(sender, e);
                    e.Handled = true;
                    return;
                }
                _isDragging = true;
                _lastMousePos = e.GetPosition(ScrollDiagramContainer);
                CanvasDiagramContainer.CaptureMouse();
            }
        }

        private void Canvas_MouseMove(object sender, MouseEventArgs e)
        {
            if (_isDragging && ImgTranslateTransform != null)
            {
                var cur = e.GetPosition(ScrollDiagramContainer);
                double dx = cur.X - _lastMousePos.X;
                double dy = cur.Y - _lastMousePos.Y;
                ImgTranslateTransform.X += dx;
                ImgTranslateTransform.Y += dy;
                _lastMousePos = cur;
            }
        }

        private void Canvas_MouseUp(object sender, MouseButtonEventArgs e)
        {
            if (_isDragging)
            {
                _isDragging = false;
                CanvasDiagramContainer.ReleaseMouseCapture();
            }
        }

        private void BorderDiagramWrapper_MouseEnter(object sender, MouseEventArgs e)
        {
            if (BorderDiagramWrapper != null)
            {
                _originalBorderBrush ??= BorderDiagramWrapper.BorderBrush;
                BorderDiagramWrapper.BorderBrush = new SolidColorBrush(Color.FromRgb(139, 92, 246)); // #8B5CF6 Accent
            }
        }

        private void BorderDiagramWrapper_MouseLeave(object sender, MouseEventArgs e)
        {
            if (BorderDiagramWrapper != null && _originalBorderBrush != null)
            {
                BorderDiagramWrapper.BorderBrush = _originalBorderBrush;
            }
        }

        private void BtnOpenViewerWindow_Click(object sender, RoutedEventArgs e)
        {
            if (ImgDiagramPreview.Source == null && string.IsNullOrEmpty(_currentGeneratedImagePath))
            {
                MessageBox.Show("Chưa có hình vẽ nào để mở xem chi tiết.\nHãy bấm 'Biên dịch hình' (F5) hoặc 'AI vẽ' (Ctrl+Shift+G) trước.", "Chưa có hình vẽ", MessageBoxButton.OK, MessageBoxImage.Information);
                return;
            }

            int dpi = 600;
            if (CmbDpi?.SelectedItem is ComboBoxItem dpiItem && int.TryParse(dpiItem.Tag?.ToString(), out int parsedDpi))
            {
                dpi = parsedDpi;
            }

            var viewer = new TikzImagePreviewWindow(ImgDiagramPreview.Source, _currentGeneratedImagePath, dpi)
            {
                Owner = Window.GetWindow(this)
            };
            viewer.ShowDialog();
        }

        private void PlayNewImageInsertAnimation()
        {
            if (ImgScaleTransform == null || BorderDiagramWrapper == null) return;

            try
            {
                // 1. Phóng to nhẹ hình ảnh vừa được chèn/biên dịch: 0.85 -> 1.06 -> _currentZoom
                var scaleAnimX = new DoubleAnimationUsingKeyFrames
                {
                    Duration = TimeSpan.FromMilliseconds(380)
                };
                scaleAnimX.KeyFrames.Add(new DiscreteDoubleKeyFrame(0.85 * _currentZoom, KeyTime.FromTimeSpan(TimeSpan.Zero)));
                scaleAnimX.KeyFrames.Add(new SplineDoubleKeyFrame(1.06 * _currentZoom, KeyTime.FromTimeSpan(TimeSpan.FromMilliseconds(200)))
                {
                    KeySpline = new KeySpline(0.2, 0.8, 0.4, 1.0)
                });
                scaleAnimX.KeyFrames.Add(new SplineDoubleKeyFrame(_currentZoom, KeyTime.FromTimeSpan(TimeSpan.FromMilliseconds(380)))
                {
                    KeySpline = new KeySpline(0.4, 0.0, 0.2, 1.0)
                });

                var scaleAnimY = scaleAnimX.Clone();

                ImgScaleTransform.BeginAnimation(ScaleTransform.ScaleXProperty, scaleAnimX);
                ImgScaleTransform.BeginAnimation(ScaleTransform.ScaleYProperty, scaleAnimY);

                // 2. Viền nhấp nháy phát sáng xanh ngọc (#10B981) báo hiệu hình vừa được nạp thành công
                var borderBrush = new SolidColorBrush(Color.FromRgb(16, 185, 129));
                BorderDiagramWrapper.BorderBrush = borderBrush;
                var colorAnim = new ColorAnimation
                {
                    From = Color.FromRgb(16, 185, 129),
                    To = Color.FromRgb(226, 232, 240),
                    Duration = TimeSpan.FromMilliseconds(650),
                    EasingFunction = new QuadraticEase { EasingMode = EasingMode.EaseOut }
                };
                borderBrush.BeginAnimation(SolidColorBrush.ColorProperty, colorAnim);
            }
            catch
            {
                // Safe fallback
            }
        }

        private void BtnShapeBuilder_Click(object sender, RoutedEventArgs e)
        {
            var dlg = new TikzShapeBuilderDialog
            {
                Owner = Window.GetWindow(this)
            };
            if (dlg.ShowDialog() == true && !string.IsNullOrWhiteSpace(dlg.GeneratedTikzCode))
            {
                TxtTikzCode.Text = dlg.GeneratedTikzCode;
                BtnCompile_Click(this, new RoutedEventArgs());
            }
        }

        private async void BtnCompile_Click(object sender, RoutedEventArgs e)
        {
            string code = TxtTikzCode.Text;
            if (string.IsNullOrWhiteSpace(code)) return;

            int dpi = 600;
            if (CmbDpi?.SelectedItem is ComboBoxItem dpiItem && int.TryParse(dpiItem.Tag?.ToString(), out int parsedDpi))
            {
                dpi = parsedDpi;
            }

            _activeTikzCts?.Dispose();
            _activeTikzCts = new System.Threading.CancellationTokenSource();

            BtnCompile.IsEnabled = false;
            BtnStopTikzAction.Visibility = Visibility.Visible;

            _compileStopwatch.Restart();
            TxtDiagramStats.Text = $"⏳ Đang biên dịch hình vẽ ({dpi} DPI)... (0.0s)";

            if (_compileTimer == null)
            {
                _compileTimer = new System.Windows.Threading.DispatcherTimer
                {
                    Interval = TimeSpan.FromMilliseconds(100)
                };
                _compileTimer.Tick += (s, ev) =>
                {
                    if (BtnCompile.IsEnabled == false)
                    {
                        TxtDiagramStats.Text = $"⏳ Đang biên dịch hình vẽ ({dpi} DPI)... ({_compileStopwatch.Elapsed.TotalSeconds:F1}s)";
                    }
                };
            }
            _compileTimer.Start();

            try
            {
                var compileReq = new TikzCompileRequest
                {
                    TikzCode = code,
                    Dpi = dpi,
                    Format = TikzExportFormat.Png
                };

                var compileResult = await _compilerService.CompileAsync(compileReq, _activeTikzCts.Token);

                SafeDispatch(() =>
                {
                    _compileTimer?.Stop();
                    _compileStopwatch.Stop();
                    double elapsed = _compileStopwatch.Elapsed.TotalSeconds;

                    if (compileResult.Success && !string.IsNullOrEmpty(compileResult.ImagePath) && File.Exists(compileResult.ImagePath))
                    {
                        _currentGeneratedImagePath = compileResult.ImagePath;
                        _lastCompileError = null;
                        BtnAiAutoHeal.Visibility = Visibility.Collapsed;

                        var bi = new BitmapImage();
                        bi.BeginInit();
                        bi.CacheOption = BitmapCacheOption.OnLoad;
                        bi.UriSource = new Uri(compileResult.ImagePath);
                        bi.EndInit();

                        ImgDiagramPreview.Source = bi;
                        PanelPreviewPlaceholder.Visibility = Visibility.Collapsed;
                        TxtDiagramStats.Text = $"Đã biên dịch: {bi.PixelWidth}x{bi.PixelHeight} px ({dpi} DPI) | {elapsed:F1}s ({compileResult.CompilationTimeMs}ms)";

                        PlayNewImageInsertAnimation();

                        InfoTikzNotification.Severity = Wpf.Ui.Controls.InfoBarSeverity.Success;
                        InfoTikzNotification.Title = "Biên dịch thành công";
                        InfoTikzNotification.Message = $"Hình ảnh {dpi} DPI ({bi.PixelWidth}x{bi.PixelHeight} px) hoàn tất trong {elapsed:F1}s. Sẵn sàng chèn Word (Ctrl+Shift+W).";
                        InfoTikzNotification.IsOpen = true;
                    }
                    else
                    {
                        if (_activeTikzCts.IsCancellationRequested)
                        {
                            TxtDiagramStats.Text = $"Đã dừng tiến trình biên dịch sau {elapsed:F1}s.";
                        }
                        else
                        {
                            _lastCompileError = compileResult.ErrorMessage ?? "Lỗi cú pháp LaTeX TikZ";
                            BtnAiAutoHeal.Visibility = Visibility.Visible;
                            TxtDiagramStats.Text = $"Biên dịch không thành công sau {elapsed:F1}s: {_lastCompileError}";
                            InfoTikzNotification.Severity = Wpf.Ui.Controls.InfoBarSeverity.Warning;
                            InfoTikzNotification.Title = "Lỗi biên dịch";
                            InfoTikzNotification.Message = _lastCompileError;
                            InfoTikzNotification.IsOpen = true;
                        }
                    }
                });
            }
            catch (OperationCanceledException)
            {
                SafeDispatch(() =>
                {
                    _compileTimer?.Stop();
                    _compileStopwatch.Stop();
                    TxtDiagramStats.Text = $"Đã dừng tiến trình sau {_compileStopwatch.Elapsed.TotalSeconds:F1}s.";
                });
            }
            catch (Exception ex)
            {
                SafeDispatch(() =>
                {
                    _compileTimer?.Stop();
                    _compileStopwatch.Stop();
                    _lastCompileError = ex.Message;
                    BtnAiAutoHeal.Visibility = Visibility.Visible;
                    TxtDiagramStats.Text = $"Lỗi sau {_compileStopwatch.Elapsed.TotalSeconds:F1}s: {ex.Message}";
                });
            }
            finally
            {
                SafeDispatch(() =>
                {
                    BtnCompile.IsEnabled = true;
                    BtnStopTikzAction.Visibility = Visibility.Collapsed;
                });
            }
        }

        private void BtnStopTikzAction_Click(object sender, RoutedEventArgs e)
        {
            _compileTimer?.Stop();
            _compileStopwatch.Stop();
            if (_activeTikzCts != null && !_activeTikzCts.IsCancellationRequested)
            {
                _activeTikzCts.Cancel();
            }
            BtnStopTikzAction.Visibility = Visibility.Collapsed;
            BtnCompile.IsEnabled = true;
            BtnAiAutoHeal.IsEnabled = true;
            BtnAiEdit.IsEnabled = true;
            TxtDiagramStats.Text = "Đã dừng tác vụ theo yêu cầu.";
            InfoTikzNotification.Severity = Wpf.Ui.Controls.InfoBarSeverity.Informational;
            InfoTikzNotification.Title = "Đã dừng tác vụ";
            InfoTikzNotification.Message = "Đã hủy tác vụ biên dịch / AI thành công.";
            InfoTikzNotification.IsOpen = true;
        }

        private async void BtnAiAutoHeal_Click(object sender, RoutedEventArgs e)
        {
            if (string.IsNullOrWhiteSpace(_lastCompileError)) return;

            _activeTikzCts?.Dispose();
            _activeTikzCts = new System.Threading.CancellationTokenSource();

            BtnAiAutoHeal.IsEnabled = false;
            BtnStopTikzAction.Visibility = Visibility.Visible;
            InfoTikzNotification.Severity = Wpf.Ui.Controls.InfoBarSeverity.Informational;
            InfoTikzNotification.Title = "Đang tự động sửa lỗi";
            InfoTikzNotification.Message = "AI Gemini đang phân tích log lỗi LaTeX và tự động sửa cú pháp TikZ...";
            InfoTikzNotification.IsOpen = true;

            try
            {
                string prompt = $"Mã TikZ sau đây gặp lỗi biên dịch LaTeX:\n{_lastCompileError}\n\nHãy sửa lại mã TikZ hợp lệ, không chứa lỗi cú pháp:\n{TxtTikzCode.Text}";
                var req = new TikzPromptRequest
                {
                    Prompt = prompt,
                    DiagramType = (DiagramType)CmbDiagramType.SelectedIndex
                };
                var res = await DesktopGeminiFactory.GenerateTikzAsync(req, _activeTikzCts.Token);
                if (res.Success && !string.IsNullOrWhiteSpace(res.TikzCode))
                {
                    TxtTikzCode.Text = res.TikzCode;
                    BtnAiAutoHeal.Visibility = Visibility.Collapsed;
                    BtnCompile_Click(this, new RoutedEventArgs());
                }
                else
                {
                    if (!_activeTikzCts.IsCancellationRequested)
                    {
                        MessageBox.Show(res.ErrorMessage ?? "Không thể tự động sửa lỗi bằng AI.", "Thông báo", MessageBoxButton.OK, MessageBoxImage.Warning);
                    }
                }
            }
            catch (OperationCanceledException)
            {
                TxtDiagramStats.Text = "Đã dừng AI sửa lỗi.";
            }
            catch (Exception ex)
            {
                MessageBox.Show($"Lỗi AI Auto-Heal: {ex.Message}", "Lỗi", MessageBoxButton.OK, MessageBoxImage.Error);
            }
            finally
            {
                BtnAiAutoHeal.IsEnabled = true;
                BtnStopTikzAction.Visibility = Visibility.Collapsed;
            }
        }

        private async void BtnAiEdit_Click(object sender, RoutedEventArgs e)
        {
            string currentCode = TxtTikzCode.Text;
            if (string.IsNullOrWhiteSpace(currentCode))
            {
                MessageBox.Show("Chưa có mã TikZ nào để chỉnh sửa.", "Thông báo", MessageBoxButton.OK, MessageBoxImage.Information);
                return;
            }

            string? editRequest = ShowInputPrompt(
                "Yêu cầu AI Chỉnh sửa Hình TikZ",
                "Nhập yêu cầu cần AI chỉnh sửa (ví dụ: 'Đổi màu đồ thị thành xanh', 'Thêm điểm M trên BC', 'Gắn nhãn độ dài a = 4'):");

            if (string.IsNullOrWhiteSpace(editRequest)) return;

            _activeTikzCts?.Dispose();
            _activeTikzCts = new System.Threading.CancellationTokenSource();

            BtnAiEdit.IsEnabled = false;
            BtnStopTikzAction.Visibility = Visibility.Visible;
            InfoTikzNotification.Severity = Wpf.Ui.Controls.InfoBarSeverity.Informational;
            InfoTikzNotification.Title = "Đang áp dụng chỉnh sửa";
            InfoTikzNotification.Message = "AI Gemini đang cập nhật hình vẽ theo yêu cầu...";
            InfoTikzNotification.IsOpen = true;

            try
            {
                string prompt = $"Mã TikZ hiện tại:\n{currentCode}\n\nYêu cầu chỉnh sửa: {editRequest}\nHãy giữ nguyên cấu trúc và chỉ cập nhật theo đúng yêu cầu.";
                var req = new TikzPromptRequest
                {
                    Prompt = prompt,
                    DiagramType = (DiagramType)CmbDiagramType.SelectedIndex
                };
                var res = await DesktopGeminiFactory.GenerateTikzAsync(req, _activeTikzCts.Token);
                if (res.Success && !string.IsNullOrWhiteSpace(res.TikzCode))
                {
                    TxtTikzCode.Text = res.TikzCode;
                    BtnCompile_Click(this, new RoutedEventArgs());
                }
                else
                {
                    if (!_activeTikzCts.IsCancellationRequested)
                    {
                        MessageBox.Show(res.ErrorMessage ?? "Không thể chỉnh sửa mã TikZ.", "Thông báo", MessageBoxButton.OK, MessageBoxImage.Warning);
                    }
                }
            }
            catch (OperationCanceledException)
            {
                TxtDiagramStats.Text = "Đã dừng AI chỉnh sửa.";
            }
            catch (Exception ex)
            {
                MessageBox.Show($"Lỗi AI: {ex.Message}", "Lỗi", MessageBoxButton.OK, MessageBoxImage.Error);
            }
            finally
            {
                BtnAiEdit.IsEnabled = true;
                BtnStopTikzAction.Visibility = Visibility.Collapsed;
            }
        }

        private static string? ShowInputPrompt(string title, string promptText)
        {
            var win = new Window
            {
                Title = title,
                Width = 460,
                Height = 175,
                WindowStartupLocation = WindowStartupLocation.CenterScreen,
                ResizeMode = ResizeMode.NoResize
            };
            var sp = new StackPanel { Margin = new Thickness(14) };
            var txtPrompt = new TextBlock { Text = promptText, TextWrapping = TextWrapping.Wrap, Margin = new Thickness(0, 0, 0, 8), FontSize = 11 };
            var tb = new TextBox { Height = 28, FontSize = 11, Padding = new Thickness(4) };
            var btnPanel = new StackPanel { Orientation = Orientation.Horizontal, HorizontalAlignment = HorizontalAlignment.Right, Margin = new Thickness(0, 12, 0, 0) };
            var btnOk = new Button { Content = "Đồng ý", Width = 75, Height = 26, Margin = new Thickness(0, 0, 6, 0), IsDefault = true };
            var btnCancel = new Button { Content = "Hủy", Width = 75, Height = 26, IsCancel = true };
            btnOk.Click += (s, e) => { win.DialogResult = true; win.Close(); };
            btnCancel.Click += (s, e) => { win.DialogResult = false; win.Close(); };
            btnPanel.Children.Add(btnOk);
            btnPanel.Children.Add(btnCancel);
            sp.Children.Add(txtPrompt);
            sp.Children.Add(tb);
            sp.Children.Add(btnPanel);
            win.Content = sp;
            tb.Focus();
            return win.ShowDialog() == true ? tb.Text.Trim() : null;
        }

        private void BtnCopyEmf_Click(object sender, RoutedEventArgs e)
        {
            if (string.IsNullOrEmpty(_currentGeneratedImagePath) || !File.Exists(_currentGeneratedImagePath) || ImgDiagramPreview.Source == null)
            {
                MessageBox.Show("Chưa có hình ảnh nào được biên dịch. Hãy bấm 'Biên dịch hình' (F5) trước.", "Chưa có ảnh", MessageBoxButton.OK, MessageBoxImage.Information);
                return;
            }

            bool copied = SafeClipboard.SetImage((BitmapSource)ImgDiagramPreview.Source);
            if (copied)
            {
                InfoTikzNotification.Severity = Wpf.Ui.Controls.InfoBarSeverity.Success;
                InfoTikzNotification.Title = "Đã sao chép";
                InfoTikzNotification.Message = "Hình ảnh sắc nét đã sẵn sàng dán trực tiếp vào Microsoft Word (Ctrl+V).";
                InfoTikzNotification.IsOpen = true;
            }
        }

        private void BtnSaveSvg_Click(object sender, RoutedEventArgs e)
        {
            BtnSavePng_Click(sender, e);
        }

        private async void BtnSavePng_Click(object sender, RoutedEventArgs e)
        {
            if (string.IsNullOrEmpty(_currentGeneratedImagePath) || !File.Exists(_currentGeneratedImagePath))
            {
                MessageBox.Show("Chưa có hình ảnh nào được biên dịch. Hãy bấm 'Biên dịch hình' (F5) trước.", "Chưa có ảnh", MessageBoxButton.OK, MessageBoxImage.Information);
                return;
            }

            var dialog = new Microsoft.Win32.SaveFileDialog
            {
                Filter = "Hình ảnh PNG (*.png)|*.png|Vector SVG (*.svg)|*.svg",
                FileName = $"Hinh_TikZ_{DateTime.Now:yyyyMMdd_HHmm}.png"
            };

            if (dialog.ShowDialog() == true)
            {
                try
                {
                    if (dialog.FileName.EndsWith(".svg", StringComparison.OrdinalIgnoreCase))
                    {
                        TxtDiagramStats.Text = "Đang xuất định dạng vector SVG...";
                        var svgReq = new TikzCompileRequest
                        {
                            TikzCode = TxtTikzCode.Text,
                            Format = TikzExportFormat.Svg,
                            OutputDirectory = Path.GetDirectoryName(dialog.FileName),
                            OutputBaseName = Path.GetFileNameWithoutExtension(dialog.FileName)
                        };

                        var svgResult = await _compilerService.CompileAsync(svgReq);
                        if (svgResult.Success && !string.IsNullOrEmpty(svgResult.ImagePath) && File.Exists(svgResult.ImagePath))
                        {
                            if (!string.Equals(svgResult.ImagePath, dialog.FileName, StringComparison.OrdinalIgnoreCase))
                            {
                                File.Copy(svgResult.ImagePath, dialog.FileName, true);
                            }
                            TxtDiagramStats.Text = $"Đã lưu SVG: {Path.GetFileName(dialog.FileName)}";
                            MessageBox.Show($"Đã lưu hình ảnh vector SVG tại:\n{dialog.FileName}", "Lưu Thành Công", MessageBoxButton.OK, MessageBoxImage.Information);
                        }
                        else
                        {
                            string err = svgResult.ErrorMessage ?? "Không thể chuyển đổi sang SVG (Cần Inkscape hoặc Poppler pdftocairo).";
                            TxtDiagramStats.Text = $"Lỗi xuất SVG: {err}";
                            MessageBox.Show($"Không thể xuất vector SVG: {err}", "Lỗi xuất SVG", MessageBoxButton.OK, MessageBoxImage.Warning);
                        }
                    }
                    else
                    {
                        File.Copy(_currentGeneratedImagePath, dialog.FileName, true);
                        TxtDiagramStats.Text = $"Đã lưu PNG: {Path.GetFileName(dialog.FileName)}";
                        MessageBox.Show($"Đã lưu hình ảnh sắc nét tại:\n{dialog.FileName}", "Lưu Thành Công", MessageBoxButton.OK, MessageBoxImage.Information);
                    }
                }
                catch (Exception ex)
                {
                    MessageBox.Show($"Lỗi lưu tệp: {ex.Message}", "Lỗi", MessageBoxButton.OK, MessageBoxImage.Error);
                }
            }
        }

        [System.Runtime.InteropServices.DllImport("oleaut32.dll", PreserveSig = false)]
        private static extern void GetActiveObject(ref Guid rclsid, IntPtr pvReserved, [System.Runtime.InteropServices.MarshalAs(System.Runtime.InteropServices.UnmanagedType.IUnknown)] out object ppunk);

        private static bool TryInsertImageIntoActiveWord(string imagePath)
        {
            try
            {
                var wordType = Type.GetTypeFromProgID("Word.Application");
                if (wordType == null) return false;
                Guid clsid = wordType.GUID;
                GetActiveObject(ref clsid, IntPtr.Zero, out object obj);
                if (obj == null) return false;

                dynamic wordApp = obj;
                dynamic sel = wordApp.Selection;
                if (sel != null)
                {
                    sel.InlineShapes.AddPicture(imagePath);
                    return true;
                }
            }
            catch
            {
                // Word not open or COM busy - safe fallback
            }
            return false;
        }

        private async void BtnInsertWord_Click(object sender, RoutedEventArgs e)
        {
            if (string.IsNullOrEmpty(_currentGeneratedImagePath) || !File.Exists(_currentGeneratedImagePath) || ImgDiagramPreview.Source == null)
            {
                MessageBox.Show("Chưa có hình ảnh nào được biên dịch. Hãy bấm 'Biên dịch hình' (F5) trước.", "Chưa có ảnh", MessageBoxButton.OK, MessageBoxImage.Information);
                return;
            }

            bool copied = SafeClipboard.SetImage((BitmapSource)ImgDiagramPreview.Source);
            bool insertedDirectly = TryInsertImageIntoActiveWord(_currentGeneratedImagePath);

            if (insertedDirectly)
            {
                InfoTikzNotification.Severity = Wpf.Ui.Controls.InfoBarSeverity.Success;
                InfoTikzNotification.Title = "Đã chèn vào Microsoft Word";
                InfoTikzNotification.Message = "Đã chèn trực tiếp hình vẽ TikZ độ nét cao vào tài liệu Word đang mở tại vị trí con trỏ.";
                InfoTikzNotification.IsOpen = true;

                MessageBox.Show("Đã chèn trực tiếp hình ảnh vào tài liệu Microsoft Word đang mở!\nẢnh cũng đã được sao chép vào bộ nhớ đệm (Clipboard).", "Chèn Word Thành Công", MessageBoxButton.OK, MessageBoxImage.Information);
            }
            else if (copied)
            {
                InfoTikzNotification.Severity = Wpf.Ui.Controls.InfoBarSeverity.Success;
                InfoTikzNotification.Title = "Đã sao chép vào Clipboard";
                InfoTikzNotification.Message = "Hình ảnh chất lượng cao đã sẵn sàng trong Clipboard. Bạn có thể nhấn Ctrl+V trực tiếp vào Microsoft Word để dán.";
                InfoTikzNotification.IsOpen = true;

                MessageBox.Show("Đã sao chép hình ảnh chất lượng cao vào Clipboard!\nBạn có thể nhấn Ctrl+V trực tiếp vào Microsoft Word để chèn ngay lập tức.", "Đã sao chép", MessageBoxButton.OK, MessageBoxImage.Information);
            }
            else
            {
                MessageBox.Show("Không thể truy cập bộ nhớ đệm (Clipboard) do ứng dụng khác đang khóa. Vui lòng thử lại sau giây lát.", "Lỗi Clipboard", MessageBoxButton.OK, MessageBoxImage.Warning);
            }
        }
    }
}
