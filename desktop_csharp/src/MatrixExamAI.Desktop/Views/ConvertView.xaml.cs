using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Text;
using System.Text.RegularExpressions;
using System.Threading;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Input;
using System.Windows.Media;
using System.Windows.Media.Imaging;
using System.Windows.Threading;
using MatrixExamAI.Desktop.Services;
using MatrixExamAI.Shared.Extensibility;

namespace MatrixExamAI.Desktop.Views
{
    public partial class ConvertView : UserControl
    {
        private readonly PdfExtractionService _pdfService = new PdfExtractionService();
        private readonly WordExportService _wordService = new WordExportService();
        private readonly DispatcherTimer _clockTimer;
        private readonly Stopwatch _stopwatch = new Stopwatch();
        private CancellationTokenSource? _cts;

        private string? _attachedImageBase64;
        private string _attachedImageMime = "image/png";
        private List<QuestionItem> _parsedQuestions = new List<QuestionItem>();

        public enum ConvertLayoutMode
        {
            Split,
            PreviewOnly,
            SourceOnly
        }

        private ConvertLayoutMode _currentLayoutMode = ConvertLayoutMode.Split;
        private GridLength _lastSourceWidth = new GridLength(1, GridUnitType.Star);
        private GridLength _lastPreviewWidth = new GridLength(1, GridUnitType.Star);
        private bool _isOverwriteMode = true;

        public bool IsOverwriteMode
        {
            get => _isOverwriteMode;
            set
            {
                _isOverwriteMode = value;
                UpdateInsertModeButton();
            }
        }

        public ConvertView()
        {
            InitializeComponent();

            _clockTimer = new DispatcherTimer
            {
                Interval = TimeSpan.FromMilliseconds(50)
            };
            _clockTimer.Tick += ClockTimer_Tick;

            LoadDefaultSample();
            PreviewKeyDown += ConvertView_PreviewKeyDown;
            Loaded += (s, e) =>
            {
                UpdateModeButtonStyles();
                UpdateInsertModeButton();
            };
        }

        private void BtnToggleInsertMode_Click(object sender, RoutedEventArgs e)
        {
            IsOverwriteMode = !IsOverwriteMode;
        }

        private void UpdateInsertModeButton()
        {
            if (BtnToggleInsertMode == null) return;
            if (_isOverwriteMode)
            {
                BtnToggleInsertMode.Content = "Ghi đè";
                BtnToggleInsertMode.Icon = new Wpf.Ui.Controls.SymbolIcon { Symbol = Wpf.Ui.Controls.SymbolRegular.ArrowRepeatAll24 };
                BtnToggleInsertMode.ToolTip = "Chế độ: Ghi đè (Nhấp để chuyển sang Nối tiếp)";
                BtnToggleInsertMode.Appearance = Wpf.Ui.Controls.ControlAppearance.Secondary;
            }
            else
            {
                BtnToggleInsertMode.Content = "Nối tiếp";
                BtnToggleInsertMode.Icon = new Wpf.Ui.Controls.SymbolIcon { Symbol = Wpf.Ui.Controls.SymbolRegular.AddCircle24 };
                BtnToggleInsertMode.ToolTip = "Chế độ: Nối tiếp (Nhấp để chuyển sang Ghi đè)";
                BtnToggleInsertMode.Appearance = Wpf.Ui.Controls.ControlAppearance.Info;
            }
        }

        public void TriggerConvertWithAi() => BtnConvert_Click(this, new RoutedEventArgs());
        public void TriggerOpenFile() => BtnOpenFile_Click(this, new RoutedEventArgs());
        public void TriggerAiPrompt() => BtnCopyPrompt_Click(this, new RoutedEventArgs());

        public void InsertQuestionContent(string content)
        {
            if (string.IsNullOrWhiteSpace(content)) return;
            string trimmed = content.Trim();
            if (string.IsNullOrWhiteSpace(TxtInput.Text))
            {
                TxtInput.Text = trimmed;
            }
            else
            {
                TxtInput.Text = TxtInput.Text.TrimEnd() + "\n\n" + trimmed;
            }
            TxtInput.CaretIndex = TxtInput.Text.Length;
            TxtInput.ScrollToEnd();
            TxtInput.Focus();
        }

        public void SetLayoutMode(ConvertLayoutMode mode)
        {
            _currentLayoutMode = mode;
            switch (mode)
            {
                case ConvertLayoutMode.PreviewOnly:
                    if (ColSource.Width.Value > 0 && ColSource.Width.GridUnitType == GridUnitType.Star)
                    {
                        _lastSourceWidth = ColSource.Width;
                        _lastPreviewWidth = ColPreview.Width;
                    }
                    ColSource.MinWidth = 0;
                    ColSource.Width = new GridLength(0);
                    ColSplitter.Width = new GridLength(0);
                    ColPreview.MinWidth = 0;
                    ColPreview.Width = new GridLength(1, GridUnitType.Star);

                    CardSource.Visibility = Visibility.Collapsed;
                    SplitterConvert.Visibility = Visibility.Collapsed;
                    CardPreview.Visibility = Visibility.Visible;

                    Grid.SetColumn(CardPreview, 0);
                    Grid.SetColumnSpan(CardPreview, 3);

                    BtnExpandSource.Visibility = Visibility.Visible;
                    BtnExpandPreviewFromSource.Visibility = Visibility.Collapsed;
                    break;

                case ConvertLayoutMode.SourceOnly:
                    if (ColPreview.Width.Value > 0 && ColPreview.Width.GridUnitType == GridUnitType.Star)
                    {
                        _lastSourceWidth = ColSource.Width;
                        _lastPreviewWidth = ColPreview.Width;
                    }
                    ColPreview.MinWidth = 0;
                    ColPreview.Width = new GridLength(0);
                    ColSplitter.Width = new GridLength(0);
                    ColSource.MinWidth = 0;
                    ColSource.Width = new GridLength(1, GridUnitType.Star);

                    CardPreview.Visibility = Visibility.Collapsed;
                    SplitterConvert.Visibility = Visibility.Collapsed;
                    CardSource.Visibility = Visibility.Visible;

                    Grid.SetColumn(CardSource, 0);
                    Grid.SetColumnSpan(CardSource, 3);

                    BtnExpandSource.Visibility = Visibility.Collapsed;
                    BtnExpandPreviewFromSource.Visibility = Visibility.Visible;
                    break;

                case ConvertLayoutMode.Split:
                default:
                    Grid.SetColumn(CardSource, 0);
                    Grid.SetColumnSpan(CardSource, 1);
                    Grid.SetColumn(SplitterConvert, 1);
                    Grid.SetColumnSpan(SplitterConvert, 1);
                    Grid.SetColumn(CardPreview, 2);
                    Grid.SetColumnSpan(CardPreview, 1);

                    ColSource.MinWidth = 260;
                    ColPreview.MinWidth = 320;
                    ColSource.Width = _lastSourceWidth.Value > 0 ? _lastSourceWidth : new GridLength(1, GridUnitType.Star);
                    ColSplitter.Width = new GridLength(8);
                    ColPreview.Width = _lastPreviewWidth.Value > 0 ? _lastPreviewWidth : new GridLength(1, GridUnitType.Star);

                    CardSource.Visibility = Visibility.Visible;
                    CardPreview.Visibility = Visibility.Visible;
                    SplitterConvert.Visibility = Visibility.Visible;
                    BtnExpandSource.Visibility = Visibility.Collapsed;
                    BtnExpandPreviewFromSource.Visibility = Visibility.Collapsed;
                    break;
            }
            UpdateModeButtonStyles();
        }

        private void UpdateModeButtonStyles()
        {
            if (BtnModeSplit == null || BtnModePreviewOnly == null || BtnModeSourceOnly == null) return;

            var activeBrush = new SolidColorBrush(Color.FromRgb(13, 148, 136)); // #0D9488 Accent
            var inactiveBrush = Brushes.Transparent;
            var textActiveBrush = Brushes.White;
            var textInactiveBrush = TryFindResource("TextFillColorSecondaryBrush") as Brush ?? Brushes.Gray;

            BtnModeSplit.Background = _currentLayoutMode == ConvertLayoutMode.Split ? activeBrush : inactiveBrush;
            BtnModeSplit.Foreground = _currentLayoutMode == ConvertLayoutMode.Split ? textActiveBrush : textInactiveBrush;

            BtnModePreviewOnly.Background = _currentLayoutMode == ConvertLayoutMode.PreviewOnly ? activeBrush : inactiveBrush;
            BtnModePreviewOnly.Foreground = _currentLayoutMode == ConvertLayoutMode.PreviewOnly ? textActiveBrush : textInactiveBrush;

            BtnModeSourceOnly.Background = _currentLayoutMode == ConvertLayoutMode.SourceOnly ? activeBrush : inactiveBrush;
            BtnModeSourceOnly.Foreground = _currentLayoutMode == ConvertLayoutMode.SourceOnly ? textActiveBrush : textInactiveBrush;
        }

        private void BtnCollapseSource_Click(object sender, RoutedEventArgs e) => SetLayoutMode(ConvertLayoutMode.PreviewOnly);
        private void BtnExpandSource_Click(object sender, RoutedEventArgs e) => SetLayoutMode(ConvertLayoutMode.Split);
        private void BtnExpandPreviewFromSource_Click(object sender, RoutedEventArgs e) => SetLayoutMode(ConvertLayoutMode.Split);

        private void BtnModeSplit_Click(object sender, RoutedEventArgs e) => SetLayoutMode(ConvertLayoutMode.Split);
        private void BtnModePreviewOnly_Click(object sender, RoutedEventArgs e) => SetLayoutMode(ConvertLayoutMode.PreviewOnly);
        private void BtnModeSourceOnly_Click(object sender, RoutedEventArgs e) => SetLayoutMode(ConvertLayoutMode.SourceOnly);

        public void ToggleSourcePanel()
        {
            if (_currentLayoutMode == ConvertLayoutMode.PreviewOnly)
                SetLayoutMode(ConvertLayoutMode.Split);
            else
                SetLayoutMode(ConvertLayoutMode.PreviewOnly);
        }

        private void ConvertView_PreviewKeyDown(object sender, KeyEventArgs e)
        {
            if ((e.Key == Key.OemOpenBrackets && (Keyboard.Modifiers & ModifierKeys.Control) == ModifierKeys.Control) || e.Key == Key.F10)
            {
                ToggleSourcePanel();
                e.Handled = true;
            }
        }

        private void ClockTimer_Tick(object? sender, EventArgs e)
        {
            var ts = _stopwatch.Elapsed;
            TxtTimer.Text = $"{ts.Hours:00}:{ts.Minutes:00}:{ts.Seconds:00}.{ts.Milliseconds / 100:0}";
        }

        private void StartStopwatch()
        {
            _stopwatch.Restart();
            _clockTimer.Start();
            DotTimerStatus.Fill = new SolidColorBrush(Color.FromRgb(245, 158, 11)); // Amber running
        }

        private void StopStopwatch()
        {
            _stopwatch.Stop();
            _clockTimer.Stop();
            DotTimerStatus.Fill = new SolidColorBrush(Color.FromRgb(16, 185, 129)); // Green completed
            var ts = _stopwatch.Elapsed;
            TxtTimer.Text = $"{ts.Hours:00}:{ts.Minutes:00}:{ts.Seconds:00}.{ts.Milliseconds / 100:0}";
        }

        private void LoadDefaultSample()
        {
            TxtInput.Text = string.Empty;
        }

        private void UserControl_PreviewKeyDown(object sender, KeyEventArgs e)
        {
            var isCtrl = (Keyboard.Modifiers & ModifierKeys.Control) == ModifierKeys.Control;
            var isShift = (Keyboard.Modifiers & ModifierKeys.Shift) == ModifierKeys.Shift;
            var isAlt = (Keyboard.Modifiers & ModifierKeys.Alt) == ModifierKeys.Alt;

            // Esc: Hủy tiến trình nếu đang chạy
            if (e.Key == Key.Escape && BtnCancel.Visibility == Visibility.Visible)
            {
                BtnCancel_Click(BtnCancel, new RoutedEventArgs());
                e.Handled = true;
                return;
            }

            // F5: Nhận diện câu hỏi & Chuẩn hóa
            if (!isCtrl && !isShift && !isAlt && e.Key == Key.F5)
            {
                BtnConvert_Click(BtnConvert, new RoutedEventArgs());
                e.Handled = true;
                return;
            }

            // Ctrl + Enter: Nhận diện câu hỏi & Chuẩn hóa
            if (isCtrl && !isShift && !isAlt && (e.Key == Key.Enter || e.Key == Key.Return))
            {
                BtnConvert_Click(BtnConvert, new RoutedEventArgs());
                e.Handled = true;
                return;
            }

            // Ctrl + S: Xuất file Word (.docx)
            if (isCtrl && !isShift && !isAlt && e.Key == Key.S)
            {
                BtnExportWord_Click(BtnExportWord, new RoutedEventArgs());
                e.Handled = true;
                return;
            }

            // Ctrl + O: Mở tệp đề thi (PDF, DOCX, TeX, TXT, Ảnh)
            if (isCtrl && !isShift && !isAlt && e.Key == Key.O)
            {
                BtnOpenFile_Click(BtnOpenFile, new RoutedEventArgs());
                e.Handled = true;
                return;
            }

            // Ctrl + Shift + O: Mở ngay tài liệu đề thi trong Microsoft Word
            if (isCtrl && isShift && !isAlt && e.Key == Key.O)
            {
                BtnOpenInWord_Click(BtnOpenInWord, new RoutedEventArgs());
                e.Handled = true;
                return;
            }

            // Ctrl + Shift + F: Mở khung xem trước độc lập toàn màn hình
            if (isCtrl && isShift && !isAlt && e.Key == Key.F)
            {
                BtnExpandPreview_Click(BtnExpandPreview, new RoutedEventArgs());
                e.Handled = true;
                return;
            }

            // Ctrl + Shift + B: Kẹp ${...}$
            if (isCtrl && isShift && !isAlt && e.Key == Key.B)
            {
                BtnQuickBrace_Click(BtnQuickBrace, new RoutedEventArgs());
                e.Handled = true;
                return;
            }

            // Ctrl + Shift + U: Tháo về $...$
            if (isCtrl && isShift && !isAlt && e.Key == Key.U)
            {
                BtnQuickUnbrace_Click(BtnQuickUnbrace, new RoutedEventArgs());
                e.Handled = true;
                return;
            }

            // Ctrl + Shift + P: Sao chép Prompt AI chuẩn LaTeX ex_test
            if (isCtrl && isShift && !isAlt && e.Key == Key.P)
            {
                BtnCopyPrompt_Click(BtnCopyPrompt, new RoutedEventArgs());
                e.Handled = true;
                return;
            }

            // Ctrl + Shift + I: Lọc \item
            if (isCtrl && isShift && !isAlt && e.Key == Key.I)
            {
                BtnFilterItem_Click(BtnFilterItem, new RoutedEventArgs());
                e.Handled = true;
                return;
            }

            // Ctrl + V: Nếu Clipboard chứa ảnh thì ưu tiên dán ảnh đề thi ngay lập tức
            if (isCtrl && !isShift && !isAlt && e.Key == Key.V)
            {
                if (SafeClipboard.ContainsImage())
                {
                    BtnPaste_Click(BtnPaste, new RoutedEventArgs());
                    e.Handled = true;
                    return;
                }
                else if (!TxtInput.IsKeyboardFocused)
                {
                    BtnPaste_Click(BtnPaste, new RoutedEventArgs());
                    e.Handled = true;
                    return;
                }
            }

            // Ctrl + Delete: Xóa trắng khi không ở trong TextBox; hoặc Ctrl + Shift + Delete
            if ((isCtrl && isShift && e.Key == Key.Delete) || (isCtrl && !isShift && e.Key == Key.Delete && !TxtInput.IsKeyboardFocused))
            {
                BtnClear_Click(BtnClear, new RoutedEventArgs());
                e.Handled = true;
                return;
            }
        }

        private void BtnExpandPreview_Click(object sender, RoutedEventArgs e)
        {
            string subject = (CmbSubject.SelectedItem as ComboBoxItem)?.Content?.ToString() ?? "Toán";
            string grade = (CmbGrade.SelectedItem as ComboBoxItem)?.Content?.ToString() ?? "12";

            var examOptions = new ExamExportOptions
            {
                Subject = subject,
                Grade = grade,
                ExamTitle = "KỲ THI TỐT NGHIỆP THPT",
                SchoolName = "SỞ GIÁO DỤC VÀ ĐÀO TẠO",
                ExamYear = DateTime.Now.Year.ToString(),
                TimeMinutes = "90",
                ExamCode = "101",
                IncludeSolution = true,
                HighlightFormulas = true,
                ConvertTablesToWordGrid = ChkAutoTable.IsChecked == true,
                AttachedImageBytes = !string.IsNullOrEmpty(_attachedImageBase64) ? Convert.FromBase64String(_attachedImageBase64) : null
            };

            var expandedWin = new ExpandedPreviewWindow(_parsedQuestions, TxtOutput.Text, examOptions);
            expandedWin.Owner = Window.GetWindow(this);
            expandedWin.Show();
        }

        private void CmbPreviewMode_SelectionChanged(object sender, SelectionChangedEventArgs e)
        {
            if (CmbPreviewMode == null) return;
            switch (CmbPreviewMode.SelectedIndex)
            {
                case 0:
                    if (RbTabWordPreview != null) RbTabWordPreview.IsChecked = true;
                    break;
                case 1:
                    if (RbTabQuestionGrid != null) RbTabQuestionGrid.IsChecked = true;
                    break;
                case 2:
                    if (RbTabRawCode != null) RbTabRawCode.IsChecked = true;
                    break;
            }
        }

        private void RbPreviewTab_Checked(object sender, RoutedEventArgs e)
        {
            if (BorderWordPageContainer == null || TxtOutput == null || BorderQuestionsContainer == null) return;

            if (RbTabWordPreview != null && RbTabWordPreview.IsChecked == true)
            {
                BorderWordPageContainer.Visibility = Visibility.Visible;
                BorderQuestionsContainer.Visibility = Visibility.Collapsed;
                TxtOutput.Visibility = Visibility.Collapsed;
                if (TxtPreviewSubtitle != null) TxtPreviewSubtitle.Text = "Mô phỏng chuẩn Word A4";
                if (CmbPreviewMode != null && CmbPreviewMode.SelectedIndex != 0) CmbPreviewMode.SelectedIndex = 0;
            }
            else if (RbTabQuestionGrid != null && RbTabQuestionGrid.IsChecked == true)
            {
                BorderWordPageContainer.Visibility = Visibility.Collapsed;
                BorderQuestionsContainer.Visibility = Visibility.Visible;
                TxtOutput.Visibility = Visibility.Collapsed;
                if (TxtPreviewSubtitle != null) TxtPreviewSubtitle.Text = "Bảng danh sách & Lời giải";
                if (CmbPreviewMode != null && CmbPreviewMode.SelectedIndex != 1) CmbPreviewMode.SelectedIndex = 1;
            }
            else
            {
                BorderWordPageContainer.Visibility = Visibility.Collapsed;
                BorderQuestionsContainer.Visibility = Visibility.Collapsed;
                TxtOutput.Visibility = Visibility.Visible;
                if (TxtPreviewSubtitle != null) TxtPreviewSubtitle.Text = "Mã nguồn LaTeX ${...}$";
                if (CmbPreviewMode != null && CmbPreviewMode.SelectedIndex != 2) CmbPreviewMode.SelectedIndex = 2;
            }
        }

        private void BtnPaste_Click(object sender, RoutedEventArgs e)
        {
            if (SafeClipboard.ContainsImage())
            {
                var bitmap = SafeClipboard.GetImage();
                if (bitmap != null)
                {
                    using var ms = new MemoryStream();
                    var encoder = new PngBitmapEncoder();
                    encoder.Frames.Add(BitmapFrame.Create(bitmap));
                    encoder.Save(ms);
                    byte[] bytes = ms.ToArray();
                    _attachedImageBase64 = Convert.ToBase64String(bytes);
                    _attachedImageMime = "image/png";

                    ImgAttachedPreview.Source = bitmap;
                    TxtAttachedImageInfo.Text = $"Ảnh dán từ Clipboard ({bytes.Length / 1024} KB)";
                    BorderAttachedImage.Visibility = Visibility.Visible;

                    InfoNotification.Severity = Wpf.Ui.Controls.InfoBarSeverity.Informational;
                    InfoNotification.Title = "Đã nạp ảnh từ Clipboard";
                    InfoNotification.Message = "Đã dán ảnh đề thi thành công. Bấm 'Nhận diện câu hỏi' để AI nhận diện cấu trúc ${...}$ và bảng.";
                    InfoNotification.IsOpen = true;
                }
            }
            else if (SafeClipboard.ContainsText())
            {
                string text = SafeClipboard.GetText();
                if (_isOverwriteMode)
                {
                    TxtInput.Text = text;
                }
                else
                {
                    TxtInput.AppendText(string.IsNullOrEmpty(TxtInput.Text) ? text : "\n\n" + text);
                }
            }
        }

        private async void BtnOpenFile_Click(object sender, RoutedEventArgs e)
        {
            var dialog = new Microsoft.Win32.OpenFileDialog
            {
                Title = "Mở tệp đề thi (PDF, DOCX, TeX, TXT, Ảnh)",
                Filter = "Tất cả tài liệu hỗ trợ (*.pdf;*.docx;*.tex;*.txt;*.png;*.jpg)|*.pdf;*.docx;*.tex;*.txt;*.png;*.jpg;*.jpeg;*.webp;*.bmp|Tài liệu PDF (*.pdf)|*.pdf|Tài liệu Word (*.docx)|*.docx|LaTeX & Văn bản (*.tex;*.txt)|*.tex;*.txt|Ảnh đề thi (*.png;*.jpg;*.jpeg)|*.png;*.jpg;*.jpeg|Tất cả tệp (*.*)|*.*",
                Multiselect = false
            };

            if (dialog.ShowDialog() == true)
            {
                await LoadDocumentFileAsync(dialog.FileName);
            }
        }

        private async Task LoadDocumentFileAsync(string filePath)
        {
            if (string.IsNullOrWhiteSpace(filePath) || !File.Exists(filePath)) return;

            string ext = Path.GetExtension(filePath).ToLowerInvariant();
            if (ext == ".pdf")
            {
                await ProcessPdfFileAsync(filePath);
                return;
            }

            if (ext == ".png" || ext == ".jpg" || ext == ".jpeg" || ext == ".webp" || ext == ".bmp")
            {
                try
                {
                    byte[] bytes = await File.ReadAllBytesAsync(filePath);
                    _attachedImageBase64 = Convert.ToBase64String(bytes);
                    _attachedImageMime = ext switch
                    {
                        ".jpg" or ".jpeg" => "image/jpeg",
                        ".webp" => "image/webp",
                        ".bmp" => "image/bmp",
                        _ => "image/png"
                    };

                    var bitmap = new BitmapImage();
                    bitmap.BeginInit();
                    bitmap.UriSource = new Uri(filePath);
                    bitmap.CacheOption = BitmapCacheOption.OnLoad;
                    bitmap.EndInit();

                    ImgAttachedPreview.Source = bitmap;
                    TxtAttachedImageInfo.Text = $"{Path.GetFileName(filePath)} ({bytes.Length / 1024} KB)";
                    BorderAttachedImage.Visibility = Visibility.Visible;
                    TxtCurrentFile.Text = Path.GetFileName(filePath);

                    InfoNotification.Severity = Wpf.Ui.Controls.InfoBarSeverity.Informational;
                    InfoNotification.Title = "Đã nạp file ảnh đề thi";
                    InfoNotification.Message = $"File '{Path.GetFileName(filePath)}' sẵn sàng. Bấm 'Nhận diện câu hỏi' để AI nhận diện.";
                    InfoNotification.IsOpen = true;
                }
                catch (Exception ex)
                {
                    MessageBox.Show($"Lỗi khi mở file ảnh: {ex.Message}", "Lỗi Đọc Ảnh", MessageBoxButton.OK, MessageBoxImage.Error);
                }
                return;
            }

            if (ext == ".docx")
            {
                try
                {
                    var sb = new StringBuilder();
                    using var doc = DocumentFormat.OpenXml.Packaging.WordprocessingDocument.Open(filePath, false);
                    var body = doc.MainDocumentPart?.Document?.Body;
                    if (body != null)
                    {
                        foreach (var el in body.Elements())
                        {
                            if (el is DocumentFormat.OpenXml.Wordprocessing.Paragraph p)
                            {
                                sb.AppendLine(p.InnerText);
                            }
                            else if (el is DocumentFormat.OpenXml.Wordprocessing.Table tbl)
                            {
                                foreach (var row in tbl.Elements<DocumentFormat.OpenXml.Wordprocessing.TableRow>())
                                {
                                    var cellTexts = row.Elements<DocumentFormat.OpenXml.Wordprocessing.TableCell>().Select(c => c.InnerText.Trim()).ToList();
                                    sb.AppendLine("| " + string.Join(" | ", cellTexts) + " |");
                                }
                                sb.AppendLine();
                            }
                        }
                    }

                    string text = sb.ToString();
                    if (_isOverwriteMode) TxtInput.Text = text;
                    else TxtInput.AppendText(string.IsNullOrEmpty(TxtInput.Text) ? text : "\n\n" + text);

                    TxtCurrentFile.Text = Path.GetFileName(filePath);
                    UpdateInputStats();
                }
                catch (Exception ex)
                {
                    MessageBox.Show($"Lỗi khi đọc file Word: {ex.Message}", "Lỗi Đọc Word", MessageBoxButton.OK, MessageBoxImage.Error);
                }
                return;
            }

            // Mặc định cho .tex, .txt và các tệp văn bản khác
            try
            {
                string text = await File.ReadAllTextAsync(filePath, Encoding.UTF8);
                if (_isOverwriteMode) TxtInput.Text = text;
                else TxtInput.AppendText(string.IsNullOrEmpty(TxtInput.Text) ? text : "\n\n" + text);

                TxtCurrentFile.Text = Path.GetFileName(filePath);
                UpdateInputStats();
            }
            catch (Exception ex)
            {
                MessageBox.Show($"Lỗi khi đọc file: {ex.Message}", "Lỗi Đọc File", MessageBoxButton.OK, MessageBoxImage.Error);
            }
        }

        private async void BtnSelectImage_Click(object sender, RoutedEventArgs e)
        {
            var dialog = new Microsoft.Win32.OpenFileDialog
            {
                Filter = "File hình ảnh (*.png;*.jpg;*.jpeg;*.webp;*.bmp)|*.png;*.jpg;*.jpeg;*.webp;*.bmp|Tất cả tệp (*.*)|*.*",
                Title = "Chọn ảnh chụp / bản scan đề thi"
            };

            if (dialog.ShowDialog() == true)
            {
                await LoadDocumentFileAsync(dialog.FileName);
            }
        }

        private void BtnRemoveImage_Click(object sender, RoutedEventArgs e)
        {
            _attachedImageBase64 = null;
            ImgAttachedPreview.Source = null;
            BorderAttachedImage.Visibility = Visibility.Collapsed;
        }

        private void AttachedImage_Click(object sender, MouseButtonEventArgs e)
        {
            if (ImgAttachedPreview.Source != null)
            {
                var viewer = new TikzImagePreviewWindow(ImgAttachedPreview.Source, null, 300, "Ảnh đề thi đính kèm")
                {
                    Owner = Window.GetWindow(this)
                };
                viewer.ShowDialog();
            }
        }

        private void BtnClear_Click(object sender, RoutedEventArgs e)
        {
            TxtInput.Clear();
            TxtOutput.Clear();
            PanelDocContent.Children.Clear();
            _attachedImageBase64 = null;
            ImgAttachedPreview.Source = null;
            BorderAttachedImage.Visibility = Visibility.Collapsed;
            TxtCurrentFile.Text = "Chưa chọn tệp";
            TxtTimer.Text = "00:00:00.0";
            TxtOutputStats.Text = "Đã dọn sạch vùng soạn thảo";
            TxtFormulaCount.Text = "0 công thức ${...}$";
            TxtTableCount.Text = "0 bảng Table Grid";
            InfoNotification.IsOpen = false;
        }

        private void BtnCancel_Click(object sender, RoutedEventArgs e)
        {
            if (_cts != null && !_cts.IsCancellationRequested)
            {
                _cts.Cancel();
                BtnCancel.Visibility = Visibility.Collapsed;
                ProgExtraction.Visibility = Visibility.Collapsed;
                StopStopwatch();
                InfoNotification.Severity = Wpf.Ui.Controls.InfoBarSeverity.Warning;
                InfoNotification.Title = "Đã hủy tiến trình";
                InfoNotification.Message = "Tiến trình trích xuất / nhận diện AI đã được dừng lại theo yêu cầu.";
                InfoNotification.IsOpen = true;
            }
        }

        private async void BtnSelectPdf_Click(object sender, RoutedEventArgs e)
        {
            var dialog = new Microsoft.Win32.OpenFileDialog
            {
                Filter = "Tài liệu PDF (*.pdf)|*.pdf|Tất cả tệp (*.*)|*.*",
                Title = "Chọn file đề thi PDF"
            };

            if (dialog.ShowDialog() == true)
            {
                await LoadDocumentFileAsync(dialog.FileName);
            }
        }

        private async void LeftCard_Drop(object sender, DragEventArgs e)
        {
            if (e.Data.GetDataPresent(DataFormats.FileDrop))
            {
                var files = (string[])e.Data.GetData(DataFormats.FileDrop);
                if (files != null && files.Length > 0)
                {
                    await LoadDocumentFileAsync(files[0]);
                }
            }
        }

        private void LeftCard_DragOver(object sender, DragEventArgs e)
        {
            if (e.Data.GetDataPresent(DataFormats.FileDrop))
            {
                e.Effects = DragDropEffects.Copy;
                e.Handled = true;
            }
        }

        private async System.Threading.Tasks.Task ProcessPdfFileAsync(string filePath)
        {
            TxtCurrentFile.Text = Path.GetFileName(filePath);
            ProgExtraction.Visibility = Visibility.Visible;
            BtnCancel.Visibility = Visibility.Visible;
            StartStopwatch();

            try
            {
                _cts?.Cancel();
                _cts = new CancellationTokenSource();

                int? pStart = int.TryParse(TxtPageStart.Text.Trim(), out int s) && s > 0 ? s : (int?)null;
                int? pEnd = int.TryParse(TxtPageEnd.Text.Trim(), out int en) && en > 0 ? en : (int?)null;

                var progress = new Progress<(int current, int total, string msg)>(p =>
                {
                    TxtCurrentFile.Text = $"{Path.GetFileName(filePath)} ({p.current}/{p.total} trang)";
                });

                string extracted = await _pdfService.ExtractTextAsync(filePath, pStart, pEnd, progress, _cts.Token);

                if (_isOverwriteMode)
                {
                    TxtInput.Text = extracted;
                }
                else
                {
                    TxtInput.AppendText(string.IsNullOrEmpty(TxtInput.Text) ? extracted : "\n\n" + extracted);
                }

                // Tự động chuyển đổi sau khi trích xuất
                BtnConvert_Click(this, new RoutedEventArgs());

                StopStopwatch();
                InfoNotification.Severity = Wpf.Ui.Controls.InfoBarSeverity.Success;
                InfoNotification.Title = "Trích xuất PDF thành công";
                InfoNotification.Message = $"Đã đọc thành công tài liệu: {Path.GetFileName(filePath)} trong {TxtTimer.Text}.";
                InfoNotification.IsOpen = true;
            }
            catch (OperationCanceledException)
            {
                StopStopwatch();
            }
            catch (Exception ex)
            {
                StopStopwatch();
                MessageBox.Show($"Lỗi khi đọc file PDF: {ex.Message}", "Lỗi Trích xuất PDF", MessageBoxButton.OK, MessageBoxImage.Error);
            }
            finally
            {
                ProgExtraction.Visibility = Visibility.Collapsed;
                BtnCancel.Visibility = Visibility.Collapsed;
            }
        }

        private async void BtnConvert_Click(object sender, RoutedEventArgs e)
        {
            // Kiểm tra nếu có ảnh đính kèm
            if (!string.IsNullOrEmpty(_attachedImageBase64))
            {
                await ProcessAiVisionOcrAsync();
                return;
            }

            string raw = TxtInput.Text;
            if (string.IsNullOrWhiteSpace(raw)) return;

            StartStopwatch();

            string subject = (CmbSubject.SelectedItem as ComboBoxItem)?.Content?.ToString() ?? "Toán";
            int grade = int.TryParse((CmbGrade.SelectedItem as ComboBoxItem)?.Content?.ToString(), out int g) ? g : 12;

            bool braceMath = true;
            bool protectAbs = ChkProtectAbs.IsChecked == true;

            // Chạy bộ phân tích cú pháp đa tầng siêu tốc (QuestionParserEngine)
            var parseResult = QuestionParserEngine.ParseQuestions(raw, subject, grade);

            string converted;
            int questionCount;
            string tierDesc;

            if (parseResult.TotalCount > 0)
            {
                _parsedQuestions = parseResult.Questions;
                converted = parseResult.FormattedDocText;
                questionCount = parseResult.TotalCount;
                tierDesc = parseResult.Tier switch
                {
                    "latex" => "LaTeX ex_test",
                    "exact" => "cấu trúc app",
                    "mixed" => "cấu trúc app + LaTeX",
                    "natural" => "văn bản tự nhiên",
                    _ => parseResult.Tier
                };

                // Cập nhật bảng DataGrid câu hỏi (chuẩn MEA v5.0)
                ApplyQuestionFilter();
                TxtQuestionsHeader.Text = $"Danh sách câu hỏi đã nhận diện: {questionCount} câu ({tierDesc})";
                TxtQuestionsBreakdown.Text = $" (TN: {parseResult.TnCount} | DS: {parseResult.DsCount} | TLN: {parseResult.TlnCount} | TL: {parseResult.TlCount})";
                string qLabel = $"Bảng câu hỏi ({questionCount} câu)";
                RbTabQuestionGrid.Content = qLabel;
                if (CbiPreviewQuestions != null) CbiPreviewQuestions.Content = qLabel;
            }
            else
            {
                _parsedQuestions.Clear();
                ClearQuestionDetail();
                DgQuestions.ItemsSource = null;
                converted = NormalizeContent(raw, braceMath, protectAbs);
                questionCount = Regex.Matches(converted, @"(?i)(?:^|\n)%?\s*Câu\s+\d+|===CAU===").Count;
                tierDesc = "chuẩn hóa text/bảng";
                RbTabQuestionGrid.Content = "Bảng câu hỏi (0 câu)";
                if (CbiPreviewQuestions != null) CbiPreviewQuestions.Content = "Bảng câu hỏi (0 câu)";
            }

            TxtOutput.Text = converted;
            UpdateRichPreview(converted);

            StopStopwatch();

            int formulaCount = Regex.Matches(converted, @"\$\{[\s\S]*?\}\$").Count;
            int tableCount = CountTables(converted);

            TxtOutputStats.Text = $"Hoàn tất trong {TxtTimer.Text} | {questionCount} câu hỏi ({tierDesc})";
            TxtFormulaCount.Text = $"{formulaCount} công thức ${{...}}$";
            TxtTableCount.Text = $"{tableCount} bảng Table Grid";

            InfoNotification.Severity = Wpf.Ui.Controls.InfoBarSeverity.Success;
            InfoNotification.Title = "Chuyển đổi hoàn tất";
            InfoNotification.Message = $"Đã nhận diện {questionCount} câu hỏi ({tierDesc}), {formulaCount} công thức kẹp ${{...}}$ và {tableCount} bảng trong {TxtTimer.Text}.";
            InfoNotification.IsOpen = true;
        }

        private static string GetTypeShort(string qType)
        {
            return qType switch
            {
                "MultipleChoice4" => "TN",
                "TrueFalse4" => "DS",
                "ShortAnswer" => "TLN",
                "Essay" => "TL",
                _ => qType
            };
        }

        private void CmbQTypeFilter_SelectionChanged(object sender, SelectionChangedEventArgs e)
        {
            ApplyQuestionFilter();
        }

        private void ApplyQuestionFilter()
        {
            if (DgQuestions == null || _parsedQuestions == null) return;

            string filterTag = (CmbQTypeFilter?.SelectedItem as ComboBoxItem)?.Tag?.ToString() ?? "ALL";

            var allItems = _parsedQuestions.Select((q, i) => new QuestionDisplayItem
            {
                Index = i + 1,
                SubjectGrade = $"{q.Subject} {q.Grade}",
                TypeShort = GetTypeShort(q.QuestionType),
                CognitiveLevel = q.CognitiveLevel,
                Topic = string.IsNullOrWhiteSpace(q.Topic) ? $"{q.Subject} {q.Grade}" : q.Topic,
                CorrectAnswer = q.CorrectAnswer,
                ContentPreview = q.Content.Replace("\r\n", " ").Replace("\n", " "),
                ExplanationPreview = string.IsNullOrWhiteSpace(q.Explanation) ? "(Đang cập nhật)" : q.Explanation.Replace("\r\n", " ").Replace("\n", " "),
                RawItem = q
            }).ToList();

            List<QuestionDisplayItem> filteredList;
            if (filterTag == "ALL")
            {
                filteredList = allItems;
            }
            else
            {
                filteredList = allItems.Where(item =>
                {
                    return filterTag switch
                    {
                        "TN" => item.RawItem.QuestionType == "MultipleChoice4",
                        "DS" => item.RawItem.QuestionType == "TrueFalse4",
                        "TLN" => item.RawItem.QuestionType == "ShortAnswer",
                        "TL" => item.RawItem.QuestionType == "Essay",
                        _ => true
                    };
                }).ToList();
            }

            DgQuestions.ItemsSource = filteredList;
            if (filteredList.Count > 0)
            {
                DgQuestions.SelectedIndex = 0;
            }
            else
            {
                ClearQuestionDetail();
            }
        }

        private void DgQuestions_SelectionChanged(object sender, SelectionChangedEventArgs e)
        {
            if (DgQuestions.SelectedItem is QuestionDisplayItem item && item.RawItem != null)
            {
                DisplayQuestionDetail(item.RawItem, item.Index);
            }
            else
            {
                ClearQuestionDetail();
            }
        }

        private void DisplayQuestionDetail(QuestionItem q, int index)
        {
            if (TxtDetailTitle == null || TxtDetailQuestionBody == null) return;

            TxtDetailTitle.Text = $"Chi tiết Câu {index} ({q.Subject} {q.Grade})";

            // Hiển thị các Badge phân loại
            if (BadgeDetailType != null && TxtBadgeDetailType != null)
            {
                BadgeDetailType.Visibility = Visibility.Visible;
                TxtBadgeDetailType.Text = GetTypeShort(q.QuestionType) switch
                {
                    "TN" => "Trắc nghiệm 4 lựa chọn",
                    "DS" => "Đúng / Sai 4 ý",
                    "TLN" => "Trả lời ngắn",
                    "TL" => "Tự luận",
                    _ => q.QuestionType
                };
            }

            if (BadgeDetailLevel != null && TxtBadgeDetailLevel != null)
            {
                BadgeDetailLevel.Visibility = Visibility.Visible;
                TxtBadgeDetailLevel.Text = string.IsNullOrWhiteSpace(q.CognitiveLevel) ? "Thông hiểu" : q.CognitiveLevel;
            }

            if (BadgeDetailAns != null && TxtBadgeDetailAns != null)
            {
                if (!string.IsNullOrWhiteSpace(q.CorrectAnswer))
                {
                    BadgeDetailAns.Visibility = Visibility.Visible;
                    TxtBadgeDetailAns.Text = $"Đ/Á: {q.CorrectAnswer}";
                }
                else
                {
                    BadgeDetailAns.Visibility = Visibility.Collapsed;
                }
            }

            // Nội dung câu hỏi
            if (TxtDetailEmptyHint != null) TxtDetailEmptyHint.Visibility = Visibility.Collapsed;
            TxtDetailQuestionBody.Visibility = Visibility.Visible;
            TxtDetailQuestionBody.Text = q.Content;

            // 4 Phương án lựa chọn (A, B, C, D)
            if (PanelDetailOptions != null)
            {
                PanelDetailOptions.Children.Clear();
                if (q.Options != null && q.Options.Count > 0)
                {
                    PanelDetailOptions.Visibility = Visibility.Visible;
                    foreach (var kvp in q.Options.OrderBy(x => x.Key))
                    {
                        var optTb = new TextBlock
                        {
                            Text = $"{kvp.Key}. {kvp.Value}",
                            FontFamily = new FontFamily("Times New Roman, Segoe UI"),
                            FontSize = 11.5,
                            Margin = new Thickness(0, 2, 0, 2),
                            TextWrapping = TextWrapping.Wrap
                        };

                        if (!string.IsNullOrWhiteSpace(q.CorrectAnswer) &&
                            q.CorrectAnswer.Contains(kvp.Key, StringComparison.OrdinalIgnoreCase))
                        {
                            optTb.FontWeight = FontWeights.Bold;
                            optTb.Foreground = new SolidColorBrush(Color.FromRgb(16, 185, 129)); // Highlight xanh lục đáp án đúng
                        }

                        PanelDetailOptions.Children.Add(optTb);
                    }
                }
                else
                {
                    PanelDetailOptions.Visibility = Visibility.Collapsed;
                }
            }

            // Lời giải chi tiết
            if (BorderDetailExplanation != null && TxtDetailExplanation != null)
            {
                if (!string.IsNullOrWhiteSpace(q.Explanation))
                {
                    BorderDetailExplanation.Visibility = Visibility.Visible;
                    TxtDetailExplanation.Text = q.Explanation;
                }
                else
                {
                    BorderDetailExplanation.Visibility = Visibility.Collapsed;
                }
            }
        }

        private void ClearQuestionDetail()
        {
            if (TxtDetailEmptyHint != null) TxtDetailEmptyHint.Visibility = Visibility.Visible;
            if (TxtDetailQuestionBody != null) TxtDetailQuestionBody.Visibility = Visibility.Collapsed;
            if (PanelDetailOptions != null)
            {
                PanelDetailOptions.Children.Clear();
                PanelDetailOptions.Visibility = Visibility.Collapsed;
            }
            if (BorderDetailExplanation != null) BorderDetailExplanation.Visibility = Visibility.Collapsed;
            if (BadgeDetailType != null) BadgeDetailType.Visibility = Visibility.Collapsed;
            if (BadgeDetailLevel != null) BadgeDetailLevel.Visibility = Visibility.Collapsed;
            if (BadgeDetailAns != null) BadgeDetailAns.Visibility = Visibility.Collapsed;
            if (TxtDetailTitle != null) TxtDetailTitle.Text = "Chi tiết câu hỏi được chọn";
        }

        private void BtnCopyDetailLatex_Click(object sender, RoutedEventArgs e)
        {
            if (DgQuestions.SelectedItem is QuestionDisplayItem item && item.RawItem != null)
            {
                var sb = new StringBuilder();
                sb.AppendLine($"% [Câu {item.Index}] - [{item.CognitiveLevel}] - [{item.Topic}]");
                sb.AppendLine(item.RawItem.Content);
                if (item.RawItem.Options != null && item.RawItem.Options.Count > 0)
                {
                    foreach (var opt in item.RawItem.Options.OrderBy(x => x.Key))
                    {
                        sb.AppendLine($"{opt.Key}. {opt.Value}");
                    }
                }
                if (!string.IsNullOrWhiteSpace(item.RawItem.Explanation))
                {
                    sb.AppendLine($"Lời giải: {item.RawItem.Explanation}");
                }

                SafeClipboard.SetText(sb.ToString());
                InfoNotification.Severity = Wpf.Ui.Controls.InfoBarSeverity.Success;
                InfoNotification.Title = $"Đã sao chép Câu {item.Index}";
                InfoNotification.Message = $"Nội dung và lời giải chi tiết Câu {item.Index} đã được lưu vào bộ nhớ tạm.";
                InfoNotification.IsOpen = true;
            }
        }

        private void BtnCopyPrompt_Click(object sender, RoutedEventArgs e)
        {
            string subject = (CmbSubject.SelectedItem as ComboBoxItem)?.Content?.ToString() ?? "Toán";
            int grade = int.TryParse((CmbGrade.SelectedItem as ComboBoxItem)?.Content?.ToString(), out int g) ? g : 12;

            string prompt = GetExTestPromptTemplate(subject, grade);

            SafeClipboard.SetText(prompt);
            InfoNotification.Severity = Wpf.Ui.Controls.InfoBarSeverity.Informational;
            InfoNotification.Title = "Đã sao chép Prompt LaTeX ex_test";
            InfoNotification.Message = "Đã sao chép mẫu prompt chuẩn ex_test vào Clipboard. Hãy dán lên ChatGPT, Gemini hoặc Claude để lấy câu hỏi chuẩn.";
            InfoNotification.IsOpen = true;
        }

        public static string GetExTestPromptTemplate(string subject = "Toán", int grade = 12)
        {
            return $@"Bạn là chuyên gia biên soạn câu hỏi và đề thi môn {subject} lớp {grade} chuẩn Bộ Giáo dục và Đào tạo.
NHIỆM VỤ: Hãy tạo các câu hỏi trắc nghiệm, đúng sai, trả lời ngắn và tự luận theo đúng định dạng chuẩn gói LaTeX ex_test dưới đây:

QUY TẮC CỐT LÕI VÀ LUẬT VÀNG:
1. LUẬT VÀNG (BẮT BUỘC):
   - Đặt dòng comment chú thích `% Câu STT [Mức độ]_[Chủ đề]` (ví dụ: `% Câu 1 [Nhận biết]_[Hàm số]`) trên một dòng riêng biệt NGAY TRƯỚC `\begin{{ex}}` hoặc `\begin{{bt}}`.
   - TUYỆT ĐỐI KHÔNG đặt comment chú thích bên trong `\begin{{ex}}` hoặc cùng dòng với `\begin{{ex}}`.
   - 4 mức độ nhận thức chuẩn: Nhận biết, Thông hiểu, Vận dụng, Vận dụng cao.
2. MỌI CÔNG THỨC TOÁN BẮT BUỘC kẹp trong ${{...}}$ (ví dụ: ${{y = ax^2 + bx + c}}$, ${{\dfrac{{1}}{{2}}}}$, ${{\sqrt{{x}}}}$).
   - Dùng phân số lớn \dfrac{{a}}{{b}}, ngoặc co giãn \left(...\right), \left[...\right], \left\{{...\right\}}.
   - Hệ phương trình dùng môi trường align: \left\{{\begin{{align}} ... \end{{align}}\right.
3. ĐÁP ÁN ĐÚNG:
   - Trắc nghiệm 4 lựa chọn: Đặt dấu \True trước phương án đúng trong \choice {{...}} {{\True ...}} {{...}} {{...}}
   - Đúng / Sai 4 ý: Dùng \choiceTF, ý nào Đúng thì đặt \True {{Mệnh đề a}}, ý nào Sai thì không có \True {{Mệnh đề b}}
   - Trả lời ngắn: Dùng \shortans{{kết quả}}
   - Tự luận: Dùng môi trường \begin{{bt}} ... \end{{bt}}
4. CẤM TUYỆT ĐỐI chèn citation dạng [cite: ...], [source: ...].
5. TOÀN BỘ KẾT QUẢ đặt trong một khối mã Markdown ```latex ... ```, không có bất kỳ văn bản chào hỏi hay giải thích nào bên ngoài khối mã.

MẪU 1: CÂU TRẮC NGHIỆM (TN)
% Câu 1 [Nhận biết]_[Chủ đề bài học]
\begin{{ex}}
Nội dung câu hỏi trắc nghiệm...
\choice
{{Phương án A}}
{{\True Phương án B đúng}}
{{Phương án C}}
{{Phương án D}}
\loigiai{{
Lời giải chi tiết...
}}
\end{{ex}}

MẪU 2: CÂU ĐÚNG / SAI (DS)
% Câu 2 [Thông hiểu]_[Chủ đề bài học]
\begin{{ex}}
Nội dung câu hỏi đúng sai...
\choiceTF
{{\True Mệnh đề a đúng}}
{{Mệnh đề b sai}}
{{\True Mệnh đề c đúng}}
{{Mệnh đề d sai}}
\loigiai{{
Lời giải chi tiết từng ý...
}}
\end{{ex}}

MẪU 3: CÂU TRẢ LỜI NGẮN (TLN)
% Câu 3 [Vận dụng]_[Chủ đề bài học]
\begin{{ex}}
Nội dung câu hỏi trả lời ngắn...
\shortans{{12.5}}
\loigiai{{
Lời giải chi tiết...
}}
\end{{ex}}

MẪU 4: CÂU TỰ LUẬN (TL)
% Câu 4 [Vận dụng cao]_[Chủ đề bài học]
\begin{{bt}}
Nội dung câu hỏi tự luận...
\loigiai{{
Lời giải chi tiết...
}}
\end{{bt}}

Hãy tạo 5 câu TN, 2 câu DS, 2 câu TLN cho môn {subject} lớp {grade}. Bắt đầu ngay ở dòng đầu tiên.";
        }

        private void BtnLoadFile_Click(object sender, RoutedEventArgs e)
        {
            var openDialog = new Microsoft.Win32.OpenFileDialog
            {
                Title = "Tải cấu trúc câu hỏi / đề thi (TeX, TXT, Word)",
                Filter = "Tài liệu hỗ trợ (*.tex;*.txt;*.docx)|*.tex;*.txt;*.docx|LaTeX (*.tex)|*.tex|Văn bản (*.txt)|*.txt|Word Document (*.docx)|*.docx|Tất cả tệp (*.*)|*.*",
                Multiselect = true
            };

            if (openDialog.ShowDialog() == true)
            {
                var sb = new StringBuilder();
                foreach (var file in openDialog.FileNames)
                {
                    try
                    {
                        string ext = Path.GetExtension(file).ToLowerInvariant();
                        if (ext == ".docx")
                        {
                            using var doc = DocumentFormat.OpenXml.Packaging.WordprocessingDocument.Open(file, false);
                            var body = doc.MainDocumentPart?.Document?.Body;
                            if (body != null)
                            {
                                sb.AppendLine(body.InnerText);
                            }
                        }
                        else
                        {
                            string text = File.ReadAllText(file, Encoding.UTF8);
                            sb.AppendLine(text);
                        }
                    }
                    catch (Exception ex)
                    {
                        MessageBox.Show($"Lỗi khi đọc tệp {Path.GetFileName(file)}: {ex.Message}", "Lỗi đọc tệp", MessageBoxButton.OK, MessageBoxImage.Warning);
                    }
                }

                if (sb.Length > 0)
                {
                    TxtInput.Text = sb.ToString();
                    TxtCurrentFile.Text = Path.GetFileName(openDialog.FileName);
                    BtnConvert_Click(this, new RoutedEventArgs());
                }
            }
        }

        private void BtnCopyLatex_Click(object sender, RoutedEventArgs e)
        {
            if (_parsedQuestions.Count > 0)
            {
                var sb = new StringBuilder();
                foreach (var q in _parsedQuestions)
                {
                    sb.AppendLine(@"\begin{ex}");
                    sb.AppendLine(q.Content);
                    if (q.QuestionType == "MultipleChoice4")
                    {
                        sb.AppendLine(@"\choice");
                        string[] keys = { "A", "B", "C", "D" };
                        foreach (var k in keys)
                        {
                            string opt = q.Options.ContainsKey(k) ? q.Options[k] : "";
                            if (q.CorrectAnswer == k) sb.AppendLine($@"{{\True {opt}}}");
                            else sb.AppendLine($@"{{{opt}}}");
                        }
                    }
                    else if (q.QuestionType == "TrueFalse4")
                    {
                        sb.AppendLine(@"\choiceTF");
                        string[] keys = { "a", "b", "c", "d" };
                        foreach (var k in keys)
                        {
                            string opt = q.Options.ContainsKey(k) ? q.Options[k] : "";
                            bool isTrue = q.CorrectAnswer.Contains($"{k}=Đ");
                            if (isTrue) sb.AppendLine($@"{{\True {opt}}}");
                            else sb.AppendLine($@"{{{opt}}}");
                        }
                    }
                    else if (q.QuestionType == "ShortAnswer")
                    {
                        sb.AppendLine($@"\shortans{{{q.CorrectAnswer}}}");
                    }
                    if (!string.IsNullOrWhiteSpace(q.Explanation))
                    {
                        sb.AppendLine($@"\loigiai{{{q.Explanation}}}");
                    }
                    sb.AppendLine(@"\end{ex}");
                    sb.AppendLine();
                }
                SafeClipboard.SetText(sb.ToString().TrimEnd());
                InfoNotification.Severity = Wpf.Ui.Controls.InfoBarSeverity.Informational;
                InfoNotification.Title = "Đã sao chép LaTeX";
                InfoNotification.Message = $"Đã sao chép mã nguồn LaTeX của {_parsedQuestions.Count} câu hỏi vào Clipboard.";
                InfoNotification.IsOpen = true;
            }
            else
            {
                SafeClipboard.SetText(TxtInput.Text);
                InfoNotification.Severity = Wpf.Ui.Controls.InfoBarSeverity.Informational;
                InfoNotification.Title = "Đã sao chép";
                InfoNotification.Message = "Đã sao chép nội dung văn bản nguồn vào Clipboard.";
                InfoNotification.IsOpen = true;
            }
        }

        public static string GenerateFullLatexDocument(string body, string title = "ĐỀ THI CHUẨN HÓA", string subject = "Toán", string grade = "12")
        {
            if (string.IsNullOrWhiteSpace(body)) return string.Empty;
            if (body.Contains(@"\documentclass")) return body;

            var sb = new StringBuilder();
            sb.AppendLine(@"\documentclass[12pt,a4paper]{article}");
            sb.AppendLine(@"\usepackage[utf8]{vietnam}");
            sb.AppendLine(@"\usepackage{amsmath,amssymb,amsfonts}");
            sb.AppendLine(@"\usepackage{geometry}");
            sb.AppendLine(@"\geometry{left=2cm,right=2cm,top=2cm,bottom=2cm}");
            sb.AppendLine(@"\usepackage{tikz}");
            sb.AppendLine(@"\usepackage{tkz-tab}");
            sb.AppendLine(@"\usepackage{pgfplots}");
            sb.AppendLine(@"\pgfplotsset{compat=1.18}");
            sb.AppendLine(@"\usepackage{ex_test}");
            sb.AppendLine();
            sb.AppendLine(@"\begin{document}");
            sb.AppendLine(@"\begin{center}");
            sb.AppendLine($@"\textbf{{\Large {title.ToUpperInvariant()}}}\\");
            sb.AppendLine($@"\textbf{{Môn: {subject} - Khối: {grade}}}\\");
            sb.AppendLine(@"\textit{Thời gian làm bài: 90 phút (không kể thời gian phát đề)}");
            sb.AppendLine(@"\end{center}");
            sb.AppendLine(@"\hrule\vspace{0.5cm}");
            sb.AppendLine();
            sb.AppendLine(body);
            sb.AppendLine();
            sb.AppendLine(@"\end{document}");
            return sb.ToString();
        }

        private void BtnExportLatex_Click(object sender, RoutedEventArgs e)
        {
            var saveDialog = new Microsoft.Win32.SaveFileDialog
            {
                Filter = "LaTeX Source File (*.tex)|*.tex",
                FileName = $"De_Thi_Latex_{DateTime.Now:yyyyMMdd_HHmm}.tex",
                Title = "Lưu tệp mã nguồn LaTeX chuẩn hoàn chỉnh"
            };

            if (saveDialog.ShowDialog() == true)
            {
                try
                {
                    BtnCopyLatex_Click(this, new RoutedEventArgs());
                    string latexText = SafeClipboard.GetText();
                    string subject = (CmbSubject.SelectedItem as ComboBoxItem)?.Content?.ToString() ?? "Toán";
                    string grade = (CmbGrade.SelectedItem as ComboBoxItem)?.Content?.ToString() ?? "12";

                    string fullLatex = GenerateFullLatexDocument(latexText, "Đề Kiểm Tra", subject, grade);
                    File.WriteAllText(saveDialog.FileName, fullLatex, Encoding.UTF8);
                    MessageBox.Show($"Đã xuất tệp LaTeX biên dịch chuẩn thành công tại:\n{saveDialog.FileName}", "Xuất LaTeX Thành Công", MessageBoxButton.OK, MessageBoxImage.Information);
                }
                catch (Exception ex)
                {
                    MessageBox.Show($"Lỗi khi ghi tệp LaTeX: {ex.Message}", "Lỗi Xuất File", MessageBoxButton.OK, MessageBoxImage.Error);
                }
            }
        }

        private async void BtnAddBank_Click(object sender, RoutedEventArgs e)
        {
            if (_parsedQuestions.Count == 0)
            {
                MessageBox.Show("Chưa có câu hỏi nào được nhận diện. Hãy bấm 'Nhận diện câu hỏi' trước.", "Thông báo", MessageBoxButton.OK, MessageBoxImage.Warning);
                return;
            }

            try
            {
                var bankService = new QuestionBankService();
                await bankService.InitializeDatabaseAsync();
                int added = 0;
                foreach (var q in _parsedQuestions)
                {
                    await bankService.InsertQuestionAsync(q);
                    added++;
                }
                MessageBox.Show($"Đã lưu thành công {added} câu hỏi vào Ngân hàng câu hỏi cục bộ!", "Thêm NHCH Thành Công", MessageBoxButton.OK, MessageBoxImage.Information);
            }
            catch (Exception ex)
            {
                MessageBox.Show($"Lỗi khi lưu vào Ngân hàng câu hỏi: {ex.Message}", "Lỗi CSDL", MessageBoxButton.OK, MessageBoxImage.Error);
            }
        }

        private async System.Threading.Tasks.Task ProcessAiVisionOcrAsync()
        {
            ProgExtraction.Visibility = Visibility.Visible;
            BtnCancel.Visibility = Visibility.Visible;
            StartStopwatch();

            try
            {
                _cts?.Cancel();
                _cts = new CancellationTokenSource();

                string subject = (CmbSubject.SelectedItem as ComboBoxItem)?.Content?.ToString() ?? "Toán";
                string grade = (CmbGrade.SelectedItem as ComboBoxItem)?.Content?.ToString() ?? "12";
                string qTypeFilter = (CmbQTypeFilter.SelectedItem as ComboBoxItem)?.Tag?.ToString() ?? "ALL";

                // Xây dựng Prompt OCR chuẩn ex_test theo chỉ đạo mới
                string prompt = $@"Bạn là trợ lý OCR chuyên xử lý đề thi / bài kiểm tra {subject} lớp {grade} THPT Việt Nam.
NHIỆM VỤ: Chuyển hình ảnh đề thi thành các câu hỏi chuẩn gói LaTeX ex_test.

NGUYÊN TẮC BẮT BUỘC:
1. Nhận diện CHÍNH XÁC từng ký tự tiếng Việt có dấu. Giữ nguyên đánh số câu, phương án A/B/C/D, ý đúng/sai a/b/c/d.
2. CÔNG THỨC TOÁN HỌC: Kẹp trong ${{...}}$ (ví dụ: ${{x^2 - 5x + 6 = 0}}$, ${{\frac{{1}}{{2}}}}$, ${{\sqrt{{x+1}}}}$). 
   HỆ PHƯƠNG TRÌNH: Dùng môi trường align thay vì aligned (ví dụ: \left\{{\begin{{align}} ... \end{{align}}\right.).
   Tuyệt đối không dùng ký tự Unicode toán học rời rạc.
3. BẢNG SỐ LIỆU: Giữ đúng định dạng bảng Markdown (| Cột 1 | Cột 2 | \n |---|---|).
4. CẤU TRÚC OUTPUT MỖI CÂU:
   - Trắc nghiệm: \begin{{ex}}%[Mức độ]_[Chủ đề]\n Nội dung... \choice {{A}} {{\True B}} {{C}} {{D}} \loigiai{{...}} \end{{ex}}
   - Đúng / Sai: \begin{{ex}}%[Mức độ]_[Chủ đề]\n Nội dung... \choiceTF {{\True a}} {{b}} {{\True c}} {{d}} \loigiai{{...}} \end{{ex}}
   - Trả lời ngắn: \begin{{ex}}%[Mức độ]_[Chủ đề]\n Nội dung... \shortans{{kết quả}} \loigiai{{...}} \end{{ex}}
   - Tự luận: \begin{{bt}}%[Mức độ]_[Chủ đề]\n Nội dung... \loigiai{{...}} \end{{bt}}

Bộ lọc dạng câu yêu cầu: {qTypeFilter}.
Bắt đầu ngay câu đầu tiên. Không thêm lời mở đầu hay markdown fence ```.";

                var result = await DesktopGeminiFactory.ExecutePromptAsync(prompt, _attachedImageBase64, _attachedImageMime, _cts.Token);

                StopStopwatch();

                if (result.Success)
                {
                    string converted = NormalizeContent(result.Content, true, true);
                    TxtOutput.Text = converted;
                    if (string.IsNullOrWhiteSpace(TxtInput.Text) || TxtInput.Text.Contains("[HÌNH ẢNH"))
                    {
                        TxtInput.Text = converted;
                    }

                    UpdateRichPreview(converted);

                    int questionCount = Regex.Matches(converted, @"===CAU===|(?i)%?\s*Câu\s+\d+").Count;
                    int formulaCount = Regex.Matches(converted, @"\$\{[\s\S]*?\}\$").Count;
                    int tableCount = CountTables(converted);

                    TxtOutputStats.Text = $"AI OCR hoàn tất ({result.ProviderUsed}) trong {TxtTimer.Text} | {questionCount} câu hỏi";
                    TxtFormulaCount.Text = $"{formulaCount} công thức ${{...}}$";
                    TxtTableCount.Text = $"{tableCount} bảng Table Grid";

                    InfoNotification.Severity = Wpf.Ui.Controls.InfoBarSeverity.Success;
                    InfoNotification.Title = "AI Vision OCR thành công!";
                    InfoNotification.Message = $"Mô hình: {result.ModelUsed} ({result.ProviderUsed}) đã nhận diện thành công {questionCount} câu hỏi và {formulaCount} công thức kẹp ${{...}}$ trong {TxtTimer.Text}.";
                    InfoNotification.IsOpen = true;
                }
                else
                {
                    InfoNotification.Severity = Wpf.Ui.Controls.InfoBarSeverity.Error;
                    InfoNotification.Title = "Lỗi nhận diện AI Vision";
                    InfoNotification.Message = result.ErrorMessage ?? "Không thể hoàn thành nhận diện ảnh.";
                    InfoNotification.IsOpen = true;
                }
            }
            catch (OperationCanceledException)
            {
                StopStopwatch();
            }
            catch (Exception ex)
            {
                StopStopwatch();
                InfoNotification.Severity = Wpf.Ui.Controls.InfoBarSeverity.Error;
                InfoNotification.Title = "Ngoại lệ AI Vision";
                InfoNotification.Message = ex.Message;
                InfoNotification.IsOpen = true;
            }
            finally
            {
                ProgExtraction.Visibility = Visibility.Collapsed;
                BtnCancel.Visibility = Visibility.Collapsed;
            }
        }

        private double CurrentWordFontSize
        {
            get
            {
                if (CmbWordFontSize?.SelectedItem is ComboBoxItem item &&
                    double.TryParse(item.Tag?.ToString(), System.Globalization.NumberStyles.Any, System.Globalization.CultureInfo.InvariantCulture, out double size))
                {
                    return size;
                }
                return 12.0;
            }
        }

        private double CurrentWordLineSpacingFactor
        {
            get
            {
                if (CmbWordLineSpacing?.SelectedItem is ComboBoxItem item &&
                    double.TryParse(item.Tag?.ToString(), System.Globalization.NumberStyles.Any, System.Globalization.CultureInfo.InvariantCulture, out double factor))
                {
                    return factor;
                }
                return 1.15;
            }
        }

        private string CurrentWordChoiceLayout
        {
            get
            {
                if (CmbWordChoiceLayout?.SelectedItem is ComboBoxItem item && item.Tag != null)
                {
                    return item.Tag.ToString()!;
                }
                return "auto";
            }
        }

        private void WordPreviewSetting_Changed(object sender, RoutedEventArgs e)
        {
            if (PanelDocContent == null) return;
            string content = !string.IsNullOrWhiteSpace(TxtOutput.Text) ? TxtOutput.Text : TxtInput.Text;
            UpdateRichPreview(content);
        }

        private void UpdateRichPreview(string text)
        {
            if (PanelDocContent == null) return;

            if (_parsedQuestions != null && _parsedQuestions.Count > 0)
            {
                RenderParsedQuestionsToPreview();
                return;
            }

            PanelDocContent.Children.Clear();
            if (string.IsNullOrWhiteSpace(text))
            {
                PanelDocContent.Children.Add(new TextBlock
                {
                    Text = "Chưa có nội dung xem trước.",
                    FontFamily = new FontFamily("Times New Roman"),
                    FontSize = CurrentWordFontSize,
                    Foreground = Brushes.Gray,
                    FontStyle = FontStyles.Italic
                });
                return;
            }

            var lines = text.Split(new[] { "\r\n", "\r", "\n" }, StringSplitOptions.None);
            var tableBuffer = new System.Collections.Generic.List<string>();

            for (int i = 0; i < lines.Length; i++)
            {
                string line = lines[i];
                string trimmed = line.Trim();
                bool isTable = trimmed.StartsWith("|") && trimmed.EndsWith("|") && trimmed.Count(c => c == '|') >= 2;

                if (isTable)
                {
                    tableBuffer.Add(trimmed);
                }
                else
                {
                    if (tableBuffer.Count > 0)
                    {
                        var tableElem = RenderVisualTable(tableBuffer);
                        if (tableElem != null) PanelDocContent.Children.Add(tableElem);
                        tableBuffer.Clear();
                    }

                    if (!string.IsNullOrWhiteSpace(line))
                    {
                        if (TryParseOptionLine(trimmed, out var opts))
                        {
                            var choiceGrid = RenderChoiceGrid(opts);
                            PanelDocContent.Children.Add(choiceGrid);
                        }
                        else
                        {
                            var p = RenderVisualParagraph(line);
                            PanelDocContent.Children.Add(p);
                        }
                    }
                    else
                    {
                        PanelDocContent.Children.Add(new Border { Height = 6 });
                    }
                }
            }

            if (tableBuffer.Count > 0)
            {
                var tableElem = RenderVisualTable(tableBuffer);
                if (tableElem != null) PanelDocContent.Children.Add(tableElem);
                tableBuffer.Clear();
            }
        }

        private void RenderParsedQuestionsToPreview()
        {
            try
            {
                PanelDocContent.Children.Clear();
                if (_parsedQuestions == null || _parsedQuestions.Count == 0) return;

            string subject = _parsedQuestions.FirstOrDefault(q => !string.IsNullOrWhiteSpace(q.Subject))?.Subject ?? "Toán";
            int grade = _parsedQuestions.FirstOrDefault(q => q.Grade > 0)?.Grade ?? 12;

            // Cập nhật thông tin vào khung tiêu đề chuẩn Word A4 có sẵn trên trang
            if (TxtPreviewQuestionCount != null)
                TxtPreviewQuestionCount.Text = $"(Đề thi gồm {_parsedQuestions.Count:D2} câu)";
            if (TxtPreviewSubjectTitle != null)
                TxtPreviewSubjectTitle.Text = $"ĐỀ THI MÔN {subject.ToUpperInvariant()} - LỚP {grade}";
            if (TxtPreviewSubject != null)
                TxtPreviewSubject.Text = $"Môn thi: {subject.ToUpperInvariant()}";
            if (TxtPreviewGradeYear != null)
                TxtPreviewGradeYear.Text = $"Lớp: {grade}  Năm học: 2025-2026";
            if (TxtPreviewExamCode != null)
                TxtPreviewExamCode.Text = "Mã đề: 101";

            var tnQuestions = _parsedQuestions.Where(q => q.QuestionType == "MultipleChoice4").ToList();
            var dsQuestions = _parsedQuestions.Where(q => q.QuestionType == "TrueFalse4").ToList();
            var tlnQuestions = _parsedQuestions.Where(q => q.QuestionType == "ShortAnswer").ToList();
            var tlQuestions = _parsedQuestions.Where(q => q.QuestionType == "Essay" || (q.QuestionType != "MultipleChoice4" && q.QuestionType != "TrueFalse4" && q.QuestionType != "ShortAnswer")).ToList();

            int qIndex = 1;

            // PHẦN I
            if (tnQuestions.Count > 0)
            {
                int startIdx = qIndex;
                int endIdx = qIndex + tnQuestions.Count - 1;
                var secHead = RenderVisualParagraph($"PHẦN I. Thí sinh trả lời từ câu {startIdx} đến câu {endIdx}. Mỗi câu hỏi thí sinh chỉ chọn một phương án.", forceBold: true);
                secHead.Margin = new Thickness(0, 6, 0, 6);
                PanelDocContent.Children.Add(secHead);

                foreach (var q in tnQuestions)
                {
                    RenderSingleQuestionPreview(q, qIndex);
                    qIndex++;
                }
            }

            // PHẦN II
            if (dsQuestions.Count > 0)
            {
                int startIdx = qIndex;
                int endIdx = qIndex + dsQuestions.Count - 1;
                var secHead = RenderVisualParagraph($"PHẦN II. Thí sinh trả lời từ câu {startIdx} đến câu {endIdx}. Trong mỗi ý a), b), c), d) ở mỗi câu hỏi, thí sinh chọn đúng hoặc sai.", forceBold: true);
                secHead.Margin = new Thickness(0, 10, 0, 6);
                PanelDocContent.Children.Add(secHead);

                foreach (var q in dsQuestions)
                {
                    RenderSingleQuestionPreview(q, qIndex);
                    qIndex++;
                }
            }

            // PHẦN III
            if (tlnQuestions.Count > 0)
            {
                int startIdx = qIndex;
                int endIdx = qIndex + tlnQuestions.Count - 1;
                var secHead = RenderVisualParagraph($"PHẦN III. Thí sinh trả lời từ câu {startIdx} đến câu {endIdx}.", forceBold: true);
                secHead.Margin = new Thickness(0, 10, 0, 6);
                PanelDocContent.Children.Add(secHead);

                foreach (var q in tlnQuestions)
                {
                    RenderSingleQuestionPreview(q, qIndex);
                    qIndex++;
                }
            }

            // PHẦN IV
            if (tlQuestions.Count > 0)
            {
                int startIdx = qIndex;
                int endIdx = qIndex + tlQuestions.Count - 1;
                var secHead = RenderVisualParagraph($"PHẦN IV. Tự luận. Thí sinh trình bày lời giải từ câu {startIdx} đến câu {endIdx}.", forceBold: true);
                secHead.Margin = new Thickness(0, 10, 0, 6);
                PanelDocContent.Children.Add(secHead);

                foreach (var q in tlQuestions)
                {
                    RenderSingleQuestionPreview(q, qIndex);
                    qIndex++;
                }
            }

            // Dòng kết thúc đề
            var endPara = RenderVisualParagraph("-------------------- HẾT --------------------", forceBold: true);
            endPara.HorizontalAlignment = HorizontalAlignment.Center;
            endPara.Margin = new Thickness(0, 16, 0, 4);
            PanelDocContent.Children.Add(endPara);

            var notePara = new TextBlock
            {
                Text = "(Thí sinh không được sử dụng tài liệu. Cán bộ coi thi không giải thích gì thêm)",
                FontStyle = FontStyles.Italic,
                FontFamily = new FontFamily("Times New Roman"),
                FontSize = Math.Max(9, CurrentWordFontSize - 2),
                HorizontalAlignment = HorizontalAlignment.Center,
                Margin = new Thickness(0, 0, 0, 16)
            };
            PanelDocContent.Children.Add(notePara);

            // BẢNG ĐÁP ÁN NHANH (ở cuối đề)
            if (ChkWordShowAnswerSheet?.IsChecked == true)
            {
                var answered = _parsedQuestions.Where(q => !string.IsNullOrWhiteSpace(q.CorrectAnswer)).ToList();
                if (answered.Count > 0)
                {
                    var answerTable = RenderAnswerSheetTable(answered);
                    if (answerTable != null)
                    {
                        var answerHeader = RenderVisualParagraph("BẢNG ĐÁP ÁN NHANH", forceBold: true);
                        answerHeader.HorizontalAlignment = HorizontalAlignment.Center;
                        answerHeader.Margin = new Thickness(0, 12, 0, 6);
                        PanelDocContent.Children.Add(answerHeader);
                        PanelDocContent.Children.Add(answerTable);
                    }
                }
            }

            // HƯỚNG DẪN GIẢI CHI TIẾT (ở cuối đề)
            if (ChkWordShowSolutions?.IsChecked == true)
            {
                var solved = _parsedQuestions.Where(q => !string.IsNullOrWhiteSpace(q.Explanation)).ToList();
                if (solved.Count > 0)
                {
                    var solHeader = RenderVisualParagraph("HƯỚNG DẪN GIẢI CHI TIẾT", forceBold: true);
                    solHeader.HorizontalAlignment = HorizontalAlignment.Center;
                    solHeader.Margin = new Thickness(0, 16, 0, 8);
                    PanelDocContent.Children.Add(solHeader);

                    int solIndex = 1;
                    foreach (var q in _parsedQuestions)
                    {
                        if (!string.IsNullOrWhiteSpace(q.Explanation))
                        {
                            var solBorder = new Border
                            {
                                Background = new SolidColorBrush(Color.FromRgb(248, 250, 252)),
                                BorderBrush = new SolidColorBrush(Color.FromRgb(226, 232, 240)),
                                BorderThickness = new Thickness(1),
                                CornerRadius = new CornerRadius(4),
                                Padding = new Thickness(10, 6, 10, 6),
                                Margin = new Thickness(0, 4, 0, 8)
                            };
                            var sp = new StackPanel();
                            var head = RenderVisualParagraph($"Câu {solIndex}.", forceBold: true);
                            var solBody = RenderVisualParagraph($"Lời giải:\n{q.Explanation}");
                            sp.Children.Add(head);
                            sp.Children.Add(solBody);
                            solBorder.Child = sp;
                            PanelDocContent.Children.Add(solBorder);
                        }
                        solIndex++;
                    }
                }
            }
        }
        catch (Exception ex)
        {
            System.Diagnostics.Debug.WriteLine($"[RenderParsedQuestionsToPreview] Error: {ex.Message}");
        }
    }

        private void RenderSingleQuestionPreview(QuestionItem q, int qIndex)
        {
            try
            {
                string cleanContent = Regex.Replace(q.Content ?? "", @"\[(?:HINH_ANH|IMAGE|ANH|H[ÌI]NH(?:\s*\d+)?):\s*[^\]]+\]", "").Trim();
                string qTitle = $"Câu {qIndex}. {cleanContent}";
                var qPara = RenderVisualParagraph(qTitle, forceBold: false);

                var imgCtrl = CreatePreviewImageForQuestion(q, qIndex);

                if (imgCtrl != null)
                {
                    // Dạng 2 cột: Cột trái nội dung + phương án, Cột phải hình ảnh
                    var qGrid = new Grid { Margin = new Thickness(0, 2, 0, 6) };
                    qGrid.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(68, GridUnitType.Star) });
                    qGrid.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(32, GridUnitType.Star) });

                    var leftStack = new StackPanel { Margin = new Thickness(0, 0, 8, 0) };
                    leftStack.Children.Add(qPara);

                    if (q.QuestionType == "MultipleChoice4" && q.Options != null && q.Options.Count > 0)
                    {
                        var choiceGrid = RenderChoiceGrid(q.Options);
                        leftStack.Children.Add(choiceGrid);
                    }
                    else if (q.QuestionType == "TrueFalse4" && q.Options != null && q.Options.Count > 0)
                    {
                        string[] keys = { "a", "b", "c", "d" };
                        foreach (var k in keys)
                        {
                            if (q.Options.ContainsKey(k))
                            {
                                var itemPara = RenderVisualParagraph($"{k}) {q.Options[k]}");
                                leftStack.Children.Add(itemPara);
                            }
                        }
                    }
                    else if (q.QuestionType == "ShortAnswer")
                    {
                        var ansPara = RenderVisualParagraph("Đáp án: | | | | |", forceBold: true);
                        leftStack.Children.Add(ansPara);
                    }
                    else if (q.Options != null && q.Options.Count > 0)
                    {
                        var choiceGrid = RenderChoiceGrid(q.Options);
                        leftStack.Children.Add(choiceGrid);
                    }

                    Grid.SetColumn(leftStack, 0);
                    Grid.SetColumn(imgCtrl, 1);
                    qGrid.Children.Add(leftStack);
                    qGrid.Children.Add(imgCtrl);
                    PanelDocContent.Children.Add(qGrid);
                }
                else
                {
                    PanelDocContent.Children.Add(qPara);

                    if (q.QuestionType == "MultipleChoice4" && q.Options != null && q.Options.Count > 0)
                    {
                        var choiceGrid = RenderChoiceGrid(q.Options);
                        PanelDocContent.Children.Add(choiceGrid);
                    }
                    else if (q.QuestionType == "TrueFalse4" && q.Options != null && q.Options.Count > 0)
                    {
                        string[] keys = { "a", "b", "c", "d" };
                        foreach (var k in keys)
                        {
                            if (q.Options.ContainsKey(k))
                            {
                                var itemPara = RenderVisualParagraph($"{k}) {q.Options[k]}");
                                PanelDocContent.Children.Add(itemPara);
                            }
                        }
                    }
                    else if (q.QuestionType == "ShortAnswer")
                    {
                        var ansPara = RenderVisualParagraph("Đáp án: | | | | |", forceBold: true);
                        PanelDocContent.Children.Add(ansPara);
                    }
                    else if (q.Options != null && q.Options.Count > 0)
                    {
                        var choiceGrid = RenderChoiceGrid(q.Options);
                        PanelDocContent.Children.Add(choiceGrid);
                    }
                }

                PanelDocContent.Children.Add(new Border { Height = 4 });
            }
            catch
            {
                // Fallback cứu hộ: không bao giờ để trống câu hỏi
                try
                {
                    var fallbackTb = new TextBlock
                    {
                        Text = $"Câu {qIndex}. {q.Content ?? string.Empty}",
                        FontFamily = new FontFamily("Times New Roman"),
                        FontSize = CurrentWordFontSize * 1.125,
                        TextWrapping = TextWrapping.Wrap,
                        Foreground = new SolidColorBrush(Color.FromRgb(15, 23, 42)),
                        Margin = new Thickness(0, 2, 0, 2)
                    };
                    PanelDocContent.Children.Add(fallbackTb);

                    if (q.Options != null && q.Options.Count > 0)
                    {
                        foreach (var kvp in q.Options)
                        {
                            var optTb = new TextBlock
                            {
                                Text = $"{kvp.Key}. {kvp.Value}",
                                FontFamily = new FontFamily("Times New Roman"),
                                FontSize = CurrentWordFontSize * 1.125,
                                TextWrapping = TextWrapping.Wrap,
                                Foreground = new SolidColorBrush(Color.FromRgb(15, 23, 42)),
                                Margin = new Thickness(12, 1, 0, 1)
                            };
                            PanelDocContent.Children.Add(optTb);
                        }
                    }
                    PanelDocContent.Children.Add(new Border { Height = 4 });
                }
                catch { }
            }
        }

        private Image? CreatePreviewImageForQuestion(QuestionItem q, int qIndex)
        {
            byte[]? bytes = null;
            if (!string.IsNullOrEmpty(_attachedImageBase64) && qIndex == 1)
            {
                try { bytes = Convert.FromBase64String(_attachedImageBase64); } catch { }
            }
            if (bytes == null && q.Images != null && q.Images.Count > 0)
            {
                foreach (var imgRef in q.Images)
                {
                    if (string.IsNullOrWhiteSpace(imgRef)) continue;
                    if (File.Exists(imgRef))
                    {
                        try { bytes = File.ReadAllBytes(imgRef); break; } catch { }
                    }
                    else
                    {
                        try { bytes = Convert.FromBase64String(imgRef); break; } catch { }
                    }
                }
            }
            if (bytes == null && !string.IsNullOrWhiteSpace(q.Content))
            {
                var match = Regex.Match(q.Content, @"\[(?:HINH_ANH|IMAGE|ANH|H[ÌI]NH(?:\s*\d+)?):\s*([^\]]+)\]", RegexOptions.IgnoreCase);
                if (match.Success)
                {
                    string p = match.Groups[1].Value.Trim();
                    if (File.Exists(p)) { try { bytes = File.ReadAllBytes(p); } catch { } }
                    else
                    {
                        string fallback = Path.Combine(MatrixExamAI.Desktop.Services.ImageHelper.GetImagesDirectory(), p);
                        if (File.Exists(fallback)) { try { bytes = File.ReadAllBytes(fallback); } catch { } }
                    }
                }
            }

            if (bytes != null && bytes.Length > 0)
            {
                try
                {
                    var bmp = new BitmapImage();
                    using (var ms = new MemoryStream(bytes))
                    {
                        bmp.BeginInit();
                        bmp.CacheOption = BitmapCacheOption.OnLoad;
                        bmp.StreamSource = ms;
                        bmp.EndInit();
                    }
                    return new Image
                    {
                        Source = bmp,
                        MaxHeight = 180,
                        MaxWidth = 260,
                        HorizontalAlignment = HorizontalAlignment.Center,
                        VerticalAlignment = VerticalAlignment.Center,
                        Margin = new Thickness(6, 2, 6, 2)
                    };
                }
                catch { }
            }
            return null;
        }

        private static bool TryParseOptionLine(string line, out Dictionary<string, string> options)
        {
            options = new Dictionary<string, string>();
            var m = Regex.Matches(line, @"([A-D])\.\s+([\s\S]*?)(?=(?:[A-D]\.\s+)|$)");
            if (m.Count >= 2)
            {
                foreach (Match match in m)
                {
                    string key = match.Groups[1].Value;
                    string val = match.Groups[2].Value.Trim().TrimEnd('\t', ' ');
                    options[key] = val;
                }
                return options.Count >= 2;
            }
            return false;
        }

        private FrameworkElement RenderChoiceGrid(Dictionary<string, string> options)
        {
            if (options == null || options.Count == 0) return new FrameworkElement();

            string layout = CurrentWordChoiceLayout;
            int cols = 4;
            if (layout == "4col") cols = 4;
            else if (layout == "2col") cols = 2;
            else if (layout == "1col") cols = 1;
            else
            {
                int maxLen = options.Values.Where(v => v != null).Select(v => v.Length).DefaultIfEmpty(0).Max();
                int totalLen = options.Values.Where(v => v != null).Select(v => v.Length).Sum();
                if (maxLen > 55 || totalLen > 110) cols = 1;
                else if (maxLen > 25 || totalLen > 55) cols = 2;
                else cols = 4;
            }

            var grid = new Grid
            {
                Margin = new Thickness(12, 4, 0, 8),
                HorizontalAlignment = HorizontalAlignment.Stretch
            };

            for (int c = 0; c < cols; c++)
            {
                grid.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(1, GridUnitType.Star) });
            }

            var sortedKeys = options.Keys.OrderBy(k => k).ToList();
            int rows = (int)Math.Ceiling((double)sortedKeys.Count / cols);
            for (int r = 0; r < rows; r++)
            {
                grid.RowDefinitions.Add(new RowDefinition { Height = GridLength.Auto });
            }

            for (int i = 0; i < sortedKeys.Count; i++)
            {
                string key = sortedKeys[i];
                string val = options[key];
                int r = i / cols;
                int c = i % cols;

                string optText = $"{key}. {val}";
                var tb = RenderVisualParagraph(optText);
                tb.Margin = new Thickness(0, 2, 8, 2);

                Grid.SetRow(tb, r);
                Grid.SetColumn(tb, c);
                grid.Children.Add(tb);
            }

            return grid;
        }

        private FrameworkElement? RenderAnswerSheetTable(List<QuestionItem> questions)
        {
            if (questions.Count == 0) return null;

            int totalCols = Math.Min(10, questions.Count);
            var container = new Border
            {
                BorderBrush = new SolidColorBrush(Color.FromRgb(203, 213, 225)),
                BorderThickness = new Thickness(1),
                CornerRadius = new CornerRadius(4),
                Margin = new Thickness(0, 4, 0, 10),
                HorizontalAlignment = HorizontalAlignment.Center,
                Background = Brushes.White
            };

            var grid = new Grid();
            for (int c = 0; c < totalCols; c++)
            {
                grid.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(48) });
            }

            int rows = (int)Math.Ceiling((double)questions.Count / totalCols) * 2;
            for (int r = 0; r < rows; r++)
            {
                grid.RowDefinitions.Add(new RowDefinition { Height = GridLength.Auto });
            }

            int chunkIndex = 0;
            for (int i = 0; i < questions.Count; i += totalCols)
            {
                int rHeader = chunkIndex * 2;
                int rVal = rHeader + 1;
                int chunkCount = Math.Min(totalCols, questions.Count - i);

                for (int c = 0; c < chunkCount; c++)
                {
                    int qNum = i + c + 1;
                    var qItem = questions[i + c];

                    var headerCell = new Border
                    {
                        BorderBrush = new SolidColorBrush(Color.FromRgb(226, 232, 240)),
                        BorderThickness = new Thickness(0, 0, c < chunkCount - 1 ? 1 : 0, 1),
                        Background = new SolidColorBrush(Color.FromRgb(241, 245, 249)),
                        Padding = new Thickness(4)
                    };
                    var tbH = new TextBlock
                    {
                        Text = qNum.ToString(),
                        FontWeight = FontWeights.Bold,
                        HorizontalAlignment = HorizontalAlignment.Center,
                        FontSize = 10.5
                    };
                    headerCell.Child = tbH;
                    Grid.SetRow(headerCell, rHeader);
                    Grid.SetColumn(headerCell, c);
                    grid.Children.Add(headerCell);

                    var valCell = new Border
                    {
                        BorderBrush = new SolidColorBrush(Color.FromRgb(226, 232, 240)),
                        BorderThickness = new Thickness(0, 0, c < chunkCount - 1 ? 1 : 0, 0),
                        Padding = new Thickness(4)
                    };
                    var tbV = new TextBlock
                    {
                        Text = qItem.CorrectAnswer,
                        FontWeight = FontWeights.SemiBold,
                        Foreground = new SolidColorBrush(Color.FromRgb(2, 132, 199)),
                        HorizontalAlignment = HorizontalAlignment.Center,
                        FontSize = 11
                    };
                    valCell.Child = tbV;
                    Grid.SetRow(valCell, rVal);
                    Grid.SetColumn(valCell, c);
                    grid.Children.Add(valCell);
                }

                chunkIndex++;
            }

            container.Child = grid;
            return container;
        }

        private FrameworkElement? RenderVisualTable(System.Collections.Generic.List<string> rows)
        {
            var cleanRows = new System.Collections.Generic.List<System.Collections.Generic.List<string>>();

            foreach (var r in rows)
            {
                string clean = r.Replace("|", "").Replace("-", "").Replace(":", "").Trim();
                if (string.IsNullOrEmpty(clean)) continue; // Separator row
                var cells = WordExportService.SplitTableCells(r);
                cleanRows.Add(cells);
            }

            if (cleanRows.Count == 0) return null;

            int colCount = cleanRows.Max(r => r.Count);
            if (colCount == 0) return null;

            var container = new Border
            {
                BorderBrush = new SolidColorBrush(Color.FromRgb(203, 213, 225)), // Slate-300
                BorderThickness = new Thickness(1),
                CornerRadius = new CornerRadius(4),
                Margin = new Thickness(0, 8, 0, 10),
                HorizontalAlignment = HorizontalAlignment.Center,
                Background = Brushes.White
            };

            var grid = new Grid();
            for (int c = 0; c < colCount; c++)
            {
                grid.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(1, GridUnitType.Star) });
            }

            for (int r = 0; r < cleanRows.Count; r++)
            {
                grid.RowDefinitions.Add(new RowDefinition { Height = GridLength.Auto });
                var rowData = cleanRows[r];
                bool isHeader = (r == 0 && cleanRows.Count > 1);

                for (int c = 0; c < colCount; c++)
                {
                    string cellText = (c < rowData.Count) ? rowData[c] : "";
                    var cellBorder = new Border
                    {
                        BorderBrush = new SolidColorBrush(Color.FromRgb(226, 232, 240)),
                        BorderThickness = new Thickness(0, 0, c < colCount - 1 ? 1 : 0, r < cleanRows.Count - 1 ? 1 : 0),
                        Background = isHeader ? new SolidColorBrush(Color.FromRgb(241, 245, 249)) : Brushes.Transparent,
                        Padding = new Thickness(10, 5, 10, 5)
                    };

                    var tb = RenderVisualParagraph(cellText, isHeader);
                    tb.TextAlignment = TextAlignment.Center;
                    tb.HorizontalAlignment = HorizontalAlignment.Center;
                    tb.Margin = new Thickness(0);

                    cellBorder.Child = tb;
                    Grid.SetRow(cellBorder, r);
                    Grid.SetColumn(cellBorder, c);
                    grid.Children.Add(cellBorder);
                }
            }

            container.Child = grid;
            return container;
        }

        private TextBlock RenderVisualParagraph(string line, bool forceBold = false)
        {
            double pt = CurrentWordFontSize;
            double wpfFontSize = pt * 1.125;
            double lineHeight = wpfFontSize * CurrentWordLineSpacingFactor * 1.35;

            var tb = new TextBlock
            {
                FontFamily = new FontFamily("Times New Roman"),
                FontSize = wpfFontSize,
                LineHeight = lineHeight,
                TextWrapping = TextWrapping.Wrap,
                Foreground = new SolidColorBrush(Color.FromRgb(15, 23, 42)),
                Margin = new Thickness(0, 2, 0, 2)
            };

            var regex = new Regex(@"(\$\{[\s\S]*?\}\$|\$\{[^}\n]+?\})", RegexOptions.Singleline);
            var parts = regex.Split(line);

            foreach (var part in parts)
            {
                if (string.IsNullOrEmpty(part)) continue;

                if (part.StartsWith("${") && (part.EndsWith("}$") || part.EndsWith("}")))
                {
                    var run = new System.Windows.Documents.Run(part)
                    {
                        FontStyle = FontStyles.Italic,
                        Foreground = new SolidColorBrush(Color.FromRgb(30, 41, 59))
                    };
                    if (forceBold) run.FontWeight = FontWeights.Bold;
                    tb.Inlines.Add(run);
                }
                else
                {
                    var run = new System.Windows.Documents.Run(part);
                    if (forceBold || Regex.IsMatch(part, @"^(%?\s*Câu\s+\d+|Mệnh đề|Bài\s+\d+|Phần\s+[I|V|X]+|===CAU===|LOAI:|MUCDO:|NOIDUNG:|DAPAN:|LOIGIAI:|Lời giải|Hướng dẫn giải)", RegexOptions.IgnoreCase))
                    {
                        run.FontWeight = FontWeights.Bold;
                    }
                    if (Regex.IsMatch(part, @"^[A-D]\.\s*"))
                    {
                        run.FontWeight = FontWeights.SemiBold;
                        run.Foreground = new SolidColorBrush(Color.FromRgb(2, 132, 199));
                    }
                    tb.Inlines.Add(run);
                }
            }

            return tb;
        }

        private int CountTables(string text)
        {
            if (string.IsNullOrEmpty(text)) return 0;
            var lines = text.Split(new[] { "\r\n", "\r", "\n" }, StringSplitOptions.None);
            int count = 0;
            bool inTable = false;

            foreach (var line in lines)
            {
                string trimmed = line.Trim();
                bool isTableLine = trimmed.StartsWith("|") && trimmed.EndsWith("|") && trimmed.Count(c => c == '|') >= 2;
                if (isTableLine)
                {
                    if (!inTable)
                    {
                        count++;
                        inTable = true;
                    }
                }
                else
                {
                    inTable = false;
                }
            }
            return count;
        }

        private void BtnQuickBrace_Click(object sender, RoutedEventArgs e)
        {
            if (string.IsNullOrWhiteSpace(TxtInput.Text)) return;
            TxtInput.Text = NormalizeContent(TxtInput.Text, true, true);
            BtnConvert_Click(this, new RoutedEventArgs());
        }

        private void BtnQuickUnbrace_Click(object sender, RoutedEventArgs e)
        {
            if (string.IsNullOrWhiteSpace(TxtInput.Text)) return;
            string unbraced = Regex.Replace(TxtInput.Text, @"\$\{([\s\S]*?)\}\$", "$$$1$$");
            TxtInput.Text = unbraced;
            BtnConvert_Click(this, new RoutedEventArgs());
        }

        private void BtnQuickTable_Click(object sender, RoutedEventArgs e)
        {
            if (string.IsNullOrWhiteSpace(TxtInput.Text)) return;
            var lines = TxtInput.Text.Split('\n');
            var sb = new StringBuilder();
            foreach (var l in lines)
            {
                string trimmed = l.Trim();
                if (trimmed.StartsWith("|") && trimmed.EndsWith("|"))
                {
                    var cols = trimmed.Trim('|').Split('|').Select(c => c.Trim());
                    sb.AppendLine("| " + string.Join(" | ", cols) + " |");
                }
                else
                {
                    sb.AppendLine(l);
                }
            }
            TxtInput.Text = sb.ToString().TrimEnd();
            BtnConvert_Click(this, new RoutedEventArgs());
        }

        private void BtnCleanWhitespace_Click(object sender, RoutedEventArgs e)
        {
            if (string.IsNullOrWhiteSpace(TxtInput.Text)) return;
            string cleaned = Regex.Replace(TxtInput.Text, @"\n{3,}", "\n\n").Trim();
            TxtInput.Text = cleaned;
            BtnConvert_Click(this, new RoutedEventArgs());
        }

        private void BtnOptions_Click(object sender, RoutedEventArgs e)
        {
            if (MenuProtectAbs != null && ChkProtectAbs != null)
            {
                MenuProtectAbs.IsChecked = ChkProtectAbs.IsChecked == true;
            }
            if (MenuAutoTable != null && ChkAutoTable != null)
            {
                MenuAutoTable.IsChecked = ChkAutoTable.IsChecked == true;
            }

            if (BtnOptions.ContextMenu != null)
            {
                BtnOptions.ContextMenu.PlacementTarget = BtnOptions;
                BtnOptions.ContextMenu.Placement = System.Windows.Controls.Primitives.PlacementMode.Bottom;
                BtnOptions.ContextMenu.IsOpen = true;
            }
        }

        private void MenuProtectAbs_Click(object sender, RoutedEventArgs e)
        {
            if (MenuProtectAbs != null && ChkProtectAbs != null)
            {
                ChkProtectAbs.IsChecked = MenuProtectAbs.IsChecked;
            }
        }

        private void MenuAutoTable_Click(object sender, RoutedEventArgs e)
        {
            if (MenuAutoTable != null && ChkAutoTable != null)
            {
                ChkAutoTable.IsChecked = MenuAutoTable.IsChecked;
            }
        }

        private void BtnFilterItem_Click(object sender, RoutedEventArgs e)
        {
            if (string.IsNullOrWhiteSpace(TxtInput.Text)) return;
            string filtered = QuestionParserEngine.FilterLatexItems(TxtInput.Text);
            TxtInput.Text = filtered;
            BtnConvert_Click(this, new RoutedEventArgs());

            InfoNotification.Severity = Wpf.Ui.Controls.InfoBarSeverity.Success;
            InfoNotification.Title = "Đã lọc \\item";
            InfoNotification.Message = "Đã lọc sạch các thẻ \\item và phân tách các ý a), b), c), d) thành từng dòng chuẩn hóa.";
            InfoNotification.IsOpen = true;
        }

        private void BtnFromMatrix_Click(object sender, RoutedEventArgs e)
        {
            if (Window.GetWindow(this) is MainWindow mw)
            {
                string matrixExamText = mw.ExamMatrixView.TxtExamContent.Text?.Trim() ?? "";
                if (!string.IsNullOrWhiteSpace(matrixExamText))
                {
                    TxtInput.Text = matrixExamText;
                    BtnConvert_Click(this, new RoutedEventArgs());

                    InfoNotification.Severity = Wpf.Ui.Controls.InfoBarSeverity.Success;
                    InfoNotification.Title = "Đã nạp đề từ Ma trận";
                    InfoNotification.Message = "Đã nạp nội dung đề thi từ phân hệ Ma trận đề thi và tự động nhận diện câu hỏi.";
                    InfoNotification.IsOpen = true;
                }
                else
                {
                    // Nếu bên phân hệ ma trận chưa có nội dung, chuyển sang phân hệ ma trận
                    mw.NavigateTo("matrix");
                }
            }
        }

        private void BtnCopyOutput_Click(object sender, RoutedEventArgs e)
        {
            string outText = string.IsNullOrEmpty(TxtOutput.Text) ? TxtInput.Text : TxtOutput.Text;
            if (string.IsNullOrEmpty(outText)) return;

            string subject = (CmbSubject.SelectedItem as ComboBoxItem)?.Content?.ToString() ?? "Toán";
            string grade = (CmbGrade.SelectedItem as ComboBoxItem)?.Content?.ToString() ?? "12";

            var questions = _parsedQuestions;
            if (questions.Count == 0)
            {
                var parseResult = QuestionParserEngine.ParseQuestions(outText, subject, int.TryParse(grade, out int g) ? g : 12);
                if (parseResult.TotalCount > 0)
                {
                    questions = parseResult.Questions;
                }
            }

            if (questions.Count > 0)
            {
                string fontSizePt = ((int)Math.Round(CurrentWordFontSize * 2)).ToString();
                var examOptions = new ExamExportOptions
                {
                    Subject = subject,
                    Grade = grade,
                    SchoolName = "SỞ GIÁO DỤC VÀ ĐÀO TẠO",
                    ExamTitle = "KỲ THI TỐT NGHIỆP THPT",
                    ExamYear = DateTime.Now.Year.ToString(),
                    TimeMinutes = "90",
                    ExamCode = "101",
                    IncludeSolution = ChkWordShowSolutions.IsChecked == true,
                    HighlightFormulas = true,
                    ConvertTablesToWordGrid = ChkAutoTable.IsChecked == true,
                    FontFamily = "Times New Roman",
                    FontSizePt = fontSizePt
                };

                string html = WordExportService.GenerateHtmlExam(questions, examOptions);
                SafeClipboard.SetHtmlAndText(html, outText);

                InfoNotification.Severity = Wpf.Ui.Controls.InfoBarSeverity.Success;
                InfoNotification.Title = "Đã sao chép chuẩn đề thi";
                InfoNotification.Message = $"Đã sao chép {questions.Count} câu hỏi kèm cấu trúc đề thi (bảng tiêu đề, phiếu trả lời, đáp án). Dán Ctrl+V vào Word sẽ giữ nguyên cấu trúc chuẩn.";
                InfoNotification.IsOpen = true;
            }
            else
            {
                SafeClipboard.SetText(outText);
                InfoNotification.Severity = Wpf.Ui.Controls.InfoBarSeverity.Informational;
                InfoNotification.Title = "Đã sao chép";
                InfoNotification.Message = "Toàn bộ văn bản đã được sao chép vào Clipboard.";
                InfoNotification.IsOpen = true;
            }
        }

        private void ExportExamToFile(string targetFilePath)
        {
            string content = TxtOutput.Text;
            if (string.IsNullOrWhiteSpace(content))
            {
                content = TxtInput.Text;
            }

            string subject = (CmbSubject.SelectedItem as ComboBoxItem)?.Content?.ToString() ?? "Toán";
            string grade = (CmbGrade.SelectedItem as ComboBoxItem)?.Content?.ToString() ?? "12";

            byte[]? attachedImg = null;
            if (!string.IsNullOrEmpty(_attachedImageBase64))
            {
                try { attachedImg = Convert.FromBase64String(_attachedImageBase64); } catch { }
            }

            if (_parsedQuestions.Count == 0)
            {
                string textToParse = !string.IsNullOrWhiteSpace(content) ? content : TxtInput.Text;
                if (!string.IsNullOrWhiteSpace(textToParse))
                {
                    var parseResult = QuestionParserEngine.ParseQuestions(textToParse, subject, int.TryParse(grade, out int g) ? g : 12);
                    if (parseResult.TotalCount > 0)
                    {
                        _parsedQuestions = parseResult.Questions;
                    }
                }
            }

            string fontSizePt = ((int)Math.Round(CurrentWordFontSize * 2)).ToString(); // 11pt -> 22, 12pt -> 24, 13pt -> 26

            if (_parsedQuestions.Count > 0)
            {
                var examOptions = new ExamExportOptions
                {
                    Subject = subject,
                    Grade = grade,
                    SchoolName = "SỞ GIÁO DỤC VÀ ĐÀO TẠO",
                    ExamTitle = "KỲ THI TỐT NGHIỆP THPT",
                    ExamYear = DateTime.Now.Year.ToString(),
                    TimeMinutes = "90",
                    ExamCode = "101",
                    IncludeSolution = ChkWordShowSolutions.IsChecked == true,
                    HighlightFormulas = true,
                    ConvertTablesToWordGrid = ChkAutoTable.IsChecked == true,
                    FontFamily = "Times New Roman",
                    FontSizePt = fontSizePt,
                    AttachedImageBytes = attachedImg
                };

                _wordService.ExportExamToDocx(targetFilePath, _parsedQuestions, examOptions);
            }
            else
            {
                var options = new WordExportOptions
                {
                    ConvertTablesToWordGrid = ChkAutoTable.IsChecked == true,
                    HighlightFormulas = true,
                    FontFamily = "Times New Roman",
                    FontSizePt = fontSizePt
                };

                _wordService.ExportToDocx(targetFilePath, content, options);
            }
        }

        private void BtnExportWord_Click(object sender, RoutedEventArgs e)
        {
            string content = TxtOutput.Text;
            if (string.IsNullOrWhiteSpace(content))
            {
                content = TxtInput.Text;
                if (string.IsNullOrWhiteSpace(content))
                {
                    MessageBox.Show("Chưa có nội dung để xuất Word. Hãy bấm 'Bắt đầu Chuyển đổi' trước.", "Chưa có dữ liệu", MessageBoxButton.OK, MessageBoxImage.Warning);
                    return;
                }
            }

            string defaultDir = StorageLocationService.GetDefaultExportDirectory();
            var saveDialog = new Microsoft.Win32.SaveFileDialog
            {
                Filter = "Tài liệu Microsoft Word (*.docx)|*.docx",
                FileName = $"De_Thi_Chuan_Hoa_{DateTime.Now:yyyyMMdd_HHmm}.docx",
                InitialDirectory = Directory.Exists(defaultDir) ? defaultDir : Environment.CurrentDirectory,
                Title = "Lưu tài liệu Word chuẩn hóa A4"
            };

            if (saveDialog.ShowDialog() == true)
            {
                try
                {
                    string? chosenDir = Path.GetDirectoryName(saveDialog.FileName);
                    if (!string.IsNullOrEmpty(chosenDir))
                    {
                        StorageLocationService.SetDefaultExportDirectory(chosenDir);
                    }

                    StartStopwatch();
                    ExportExamToFile(saveDialog.FileName);
                    StopStopwatch();

                    if (StorageLocationService.GetOpenAfterExport())
                    {
                        Process.Start(new ProcessStartInfo
                        {
                            FileName = saveDialog.FileName,
                            UseShellExecute = true
                        });
                        return;
                    }

                    var result = MessageBox.Show(
                        $"Đã xuất thành công tệp Word Native!\n\nĐường dẫn: {saveDialog.FileName}\nThời gian xuất: {TxtTimer.Text}\n\nBạn có muốn mở ngay tài liệu bằng Microsoft Word không?",
                        "Xuất Word Thành Công",
                        MessageBoxButton.YesNo,
                        MessageBoxImage.Information);

                    if (result == MessageBoxResult.Yes)
                    {
                        Process.Start(new ProcessStartInfo
                        {
                            FileName = saveDialog.FileName,
                            UseShellExecute = true
                        });
                    }
                }
                catch (Exception ex)
                {
                    StopStopwatch();
                    MessageBox.Show($"Lỗi khi tạo file Word: {ex.Message}", "Lỗi Xuất Word", MessageBoxButton.OK, MessageBoxImage.Error);
                }
            }
        }

        private void BtnOpenInWord_Click(object sender, RoutedEventArgs e)
        {
            string content = !string.IsNullOrWhiteSpace(TxtOutput.Text) ? TxtOutput.Text : TxtInput.Text;
            if (string.IsNullOrWhiteSpace(content))
            {
                MessageBox.Show("Chưa có nội dung đề thi để mở trong Word. Vui lòng nhập hoặc chuyển đổi đề thi trước.", "Chưa có dữ liệu", MessageBoxButton.OK, MessageBoxImage.Warning);
                return;
            }

            try
            {
                StartStopwatch();
                string tempFile = Path.Combine(Path.GetTempPath(), $"DeThi_ChuanHoa_{DateTime.Now:yyyyMMdd_HHmmss}.docx");
                ExportExamToFile(tempFile);
                StopStopwatch();

                Process.Start(new ProcessStartInfo
                {
                    FileName = tempFile,
                    UseShellExecute = true
                });

                InfoNotification.Severity = Wpf.Ui.Controls.InfoBarSeverity.Success;
                InfoNotification.Title = "Đã mở trong Word";
                InfoNotification.Message = $"Đã xuất và khởi chạy Microsoft Word để mở tài liệu chuẩn hóa form THPT ({Path.GetFileName(tempFile)}).";
                InfoNotification.IsOpen = true;
            }
            catch (Exception ex)
            {
                StopStopwatch();
                MessageBox.Show($"Lỗi khi mở tài liệu trong Word: {ex.Message}", "Lỗi Mở Word", MessageBoxButton.OK, MessageBoxImage.Error);
            }
        }

        private void UpdateInputStats()
        {
            string text = TxtInput.Text;
            int lines = text.Split('\n').Length;
            int words = string.IsNullOrWhiteSpace(text) ? 0 : text.Split(new[] { ' ', '\r', '\n', '\t' }, StringSplitOptions.RemoveEmptyEntries).Length;
            TxtInputStats.Text = $"{words:N0} từ | {lines:N0} dòng";

            if (TxtSourceStats != null)
            {
                int formulas = Regex.Matches(text, @"\$\{[\s\S]*?\}\$|\$[^$\n]+?\$").Count;
                int tables = CountTables(text);
                int nb = Regex.Matches(text, @"(?i)\[\s*Nhận biết\s*\]").Count;
                int th = Regex.Matches(text, @"(?i)\[\s*Thông hiểu\s*\]").Count;
                int vd = Regex.Matches(text, @"(?i)\[\s*Vận dụng\s*\]").Count;
                int vdc = Regex.Matches(text, @"(?i)\[\s*Vận dụng cao\s*\]").Count;
                TxtSourceStats.Text = $"{words:N0} từ | {lines:N0} dòng | {formulas} công thức | {tables} bảng | Phân loại: {nb} NB, {th} TH, {vd} VD, {vdc} VDC";
            }
        }

        private void TxtInput_TextChanged(object sender, TextChangedEventArgs e)
        {
            UpdateInputStats();
        }

        public static string NormalizeContent(string text, bool braceMath, bool protectAbs)
        {
            if (string.IsNullOrEmpty(text)) return text;

            // 0. Chuẩn hóa hệ phương trình (aligned -> align) và tháo gỡ $ lồng nhau
            text = QuestionParserEngine.NormalizeSystemEquationsAndAlign(text);

            // 0b. Lọc sạch các thẻ \item, \itemch và phân tách các ý a), b), c), d)
            text = QuestionParserEngine.FilterLatexItems(text);

            // 1. Kẹp công thức toán học vào dạng ${...}$ và bảo vệ dấu |x| qua QuestionParserEngine
            if (braceMath)
            {
                text = QuestionParserEngine.NormalizeMathToBracedDollars(
                    text,
                    wrapUnbracedLatex: true,
                    forceMath: QuestionParserEngine.IsExamOrMathContext(text),
                    protectAbs: protectAbs);
            }

            // Nếu không kẹp math nhưng cần bảo vệ dấu '|' của công thức khi format bảng Markdown:
            var mathPipeMasks = new Dictionary<string, string>();
            int maskCounter = 0;
            if (!braceMath && protectAbs)
            {
                text = Regex.Replace(text, @"\$\$.*?\$\$|\$[^$\n]+?\$|\\\[.*?\\\]|\\\(.*?\\\)|\$\{.*?\}\$|\\left\|.*?\\right\|", m =>
                {
                    string val = m.Value;
                    if (val.Contains('|'))
                    {
                        string key = $"@@MATH_PIPE_{maskCounter++}@@";
                        mathPipeMasks[key] = val;
                        return key;
                    }
                    return val;
                }, RegexOptions.Singleline);
            }

            // 2. Chuẩn hóa bảng: Nếu phát hiện các dòng bảng (bắt đầu và kết thúc bằng '|'), chuẩn hóa căn lề các cột
            var lines = text.Split(new[] { "\r\n", "\r", "\n" }, StringSplitOptions.None);
            var sb = new StringBuilder();
            for (int i = 0; i < lines.Length; i++)
            {
                string line = lines[i];
                string trimmed = line.Trim();
                if (trimmed.StartsWith("|") && trimmed.EndsWith("|") && trimmed.Count(c => c == '|') >= 2)
                {
                    var cells = WordExportService.SplitTableCells(trimmed);
                    sb.AppendLine("| " + string.Join(" | ", cells) + " |");
                }
                else
                {
                    sb.AppendLine(line);
                }
            }

            string result = sb.ToString().TrimEnd();

            if (!braceMath && protectAbs && mathPipeMasks.Count > 0)
            {
                foreach (var kvp in mathPipeMasks)
                {
                    result = result.Replace(kvp.Key, kvp.Value);
                }
            }

            return result;
        }

        private static bool HasMatchingOuterBraces(string s)
        {
            s = s.Trim();
            if (!s.StartsWith("{") || !s.EndsWith("}")) return false;
            int depth = 0;
            for (int i = 0; i < s.Length; i++)
            {
                if (s[i] == '{') depth++;
                else if (s[i] == '}')
                {
                    depth--;
                    if (depth == 0) return i == s.Length - 1;
                }
            }
            return false;
        }
    }

    /// <summary>
    /// Dòng hiển thị trong DataGrid danh sách câu hỏi đã nhận diện của ConvertView.
    /// </summary>
    public class QuestionDisplayItem
    {
        public int Index { get; set; }
        public string SubjectGrade { get; set; } = string.Empty;
        public string TypeShort { get; set; } = string.Empty;
        public string CognitiveLevel { get; set; } = string.Empty;
        public string Topic { get; set; } = string.Empty;
        public string CorrectAnswer { get; set; } = string.Empty;
        public string ContentPreview { get; set; } = string.Empty;
        public string ExplanationPreview { get; set; } = string.Empty;
        public QuestionItem RawItem { get; set; } = null!;
    }
}
