using System;
using System.IO;
using System.Text;
using System.Threading.Tasks;
using System.Windows;
using System.Windows.Input;
using System.Windows.Media;
using System.Windows.Media.Imaging;
using Microsoft.Win32;
using MatrixExamAI.Desktop.Services;
using MatrixExamAI.Shared.AI;
using MatrixExamAI.Shared.Models;

namespace MatrixExamAI.Desktop.Views
{
    public partial class AiDrawPromptDialog : Window
    {
        public string ResultTikzCode { get; private set; } = string.Empty;
        public string ResultDescription { get; private set; } = string.Empty;
        public byte[]? ResultImageBytes => _imageBytes;

        private byte[]? _imageBytes;
        private string? _imageBase64;
        private string _imageMime = "image/png";

        public AiDrawPromptDialog(string? initialPrompt = null, byte[]? initialImage = null)
        {
            InitializeComponent();

            if (!string.IsNullOrWhiteSpace(initialPrompt))
            {
                TxtInputPrompt.Text = initialPrompt;
            }

            if (initialImage != null && initialImage.Length > 0)
            {
                LoadImageBytes(initialImage);
            }

            LoadActiveProviderInfo();
        }

        private void LoadActiveProviderInfo()
        {
            try
            {
                var (_, provider, model, _, _) = DesktopGeminiFactory.GetActiveConfig();
                string info = $"⚡ Provider hiện tại: {provider} ({model})";
                if (provider.Equals("DeepSeek", StringComparison.OrdinalIgnoreCase))
                {
                    info += " — 🔄 Tự động chuyển Vision sang Gemini/Claude/OpenAI khi gửi ảnh";
                }
                TxtActiveProvider.Text = info;
            }
            catch
            {
                TxtActiveProvider.Text = "⚡ Provider hiện tại: AI (Sẵn sàng)";
            }
        }

        private void LoadImageBytes(byte[] bytes)
        {
            try
            {
                _imageBytes = bytes;

                using var ms = new MemoryStream(bytes);
                var bmp = new BitmapImage();
                bmp.BeginInit();
                bmp.CacheOption = BitmapCacheOption.OnLoad;
                bmp.StreamSource = ms;
                bmp.EndInit();
                bmp.Freeze();

                ImgPreview.Source = bmp;

                // Tối ưu hóa kích thước và dung lượng ảnh cho AI Vision (giảm tải token và tăng tốc suy luận)
                var (optBytes, optMime) = OptimizeImageForAiVision(bmp, bytes, _imageMime);
                _imageBase64 = Convert.ToBase64String(optBytes);
                _imageMime = optMime;

                TxtImageDimensions.Text = $"Kích thước ảnh: {bmp.PixelWidth} × {bmp.PixelHeight} px ({(bytes.Length / 1024.0):F1} KB) [Tối ưu Vision: {(optBytes.Length / 1024.0):F1} KB]";
                TxtImageStatus.Text = "Đã nạp và tối ưu ảnh cho AI Vision thành công.";
                BorderImagePreview.Visibility = Visibility.Visible;
                BtnClearImage.Visibility = Visibility.Visible;
            }
            catch (Exception ex)
            {
                TxtImageStatus.Text = $"Lỗi đọc ảnh: {ex.Message}";
            }
        }

        private static (byte[] Bytes, string Mime) OptimizeImageForAiVision(BitmapSource source, byte[] originalBytes, string originalMime, int maxDimension = 1024)
        {
            try
            {
                int w = source.PixelWidth;
                int h = source.PixelHeight;

                if (w <= maxDimension && h <= maxDimension && originalBytes.Length <= 250 * 1024)
                {
                    return (originalBytes, originalMime);
                }

                double scale = Math.Min(1.0, Math.Min((double)maxDimension / w, (double)maxDimension / h));
                BitmapSource scaled = (scale < 1.0)
                    ? new TransformedBitmap(source, new ScaleTransform(scale, scale))
                    : source;

                var encoder = new JpegBitmapEncoder { QualityLevel = 85 };
                encoder.Frames.Add(BitmapFrame.Create(scaled));
                using var outMs = new MemoryStream();
                encoder.Save(outMs);
                return (outMs.ToArray(), "image/jpeg");
            }
            catch
            {
                return (originalBytes, originalMime);
            }
        }

        private void BtnChooseImage_Click(object sender, RoutedEventArgs e)
        {
            var dlg = new OpenFileDialog
            {
                Title = "Chọn ảnh đề bài / hình vẽ toán học",
                Filter = "Tệp hình ảnh (*.png;*.jpg;*.jpeg;*.bmp;*.webp)|*.png;*.jpg;*.jpeg;*.bmp;*.webp|Tất cả tệp (*.*)|*.*"
            };

            if (dlg.ShowDialog() == true)
            {
                try
                {
                    byte[] bytes = File.ReadAllBytes(dlg.FileName);
                    string ext = Path.GetExtension(dlg.FileName).ToLowerInvariant();
                    _imageMime = ext switch
                    {
                        ".jpg" or ".jpeg" => "image/jpeg",
                        ".webp" => "image/webp",
                        ".bmp" => "image/bmp",
                        _ => "image/png"
                    };
                    LoadImageBytes(bytes);
                }
                catch (Exception ex)
                {
                    MessageBox.Show($"Không thể mở tệp ảnh: {ex.Message}", "Lỗi mở ảnh", MessageBoxButton.OK, MessageBoxImage.Error);
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
                    using var ms = new MemoryStream();
                    var encoder = new PngBitmapEncoder();
                    encoder.Frames.Add(BitmapFrame.Create(image));
                    encoder.Save(ms);
                    _imageMime = "image/png";
                    LoadImageBytes(ms.ToArray());
                }
            }
            else
            {
                MessageBox.Show("Không có dữ liệu ảnh trong Clipboard.\nHãy dùng Win+Shift+S chụp ảnh đề bài rồi nhấn Ctrl+V.", "Chưa có ảnh", MessageBoxButton.OK, MessageBoxImage.Information);
            }
        }

        private void BtnClearImage_Click(object sender, RoutedEventArgs e)
        {
            _imageBytes = null;
            _imageBase64 = null;
            ImgPreview.Source = null;
            BorderImagePreview.Visibility = Visibility.Collapsed;
            BtnClearImage.Visibility = Visibility.Collapsed;
            TxtImageStatus.Text = "Chưa có ảnh (Nhấn Ctrl+V bất cứ đâu để dán ảnh chụp màn hình từ Clipboard)";
        }

        private void BorderImagePreview_MouseLeftButtonDown(object sender, MouseButtonEventArgs e)
        {
            if (ImgPreview.Source != null)
            {
                var viewer = new TikzImagePreviewWindow(ImgPreview.Source, null, 300, "Xem ảnh mẫu bài toán đính kèm")
                {
                    Owner = this
                };
                viewer.ShowDialog();
            }
        }

        private string BuildFullPrompt()
        {
            var sb = new StringBuilder();

            // Nhóm tác vụ
            var tasks = new StringBuilder();
            if (ChkTaskBbt.IsChecked == true) tasks.AppendLine("- Bảng biến thiên (BBT) có khung kẻ ô chuẩn tkz-tab.");
            if (ChkTaskBbtNoFrame.IsChecked == true) tasks.AppendLine("- Bảng biến thiên không khung mở.");
            if (ChkTaskBxd.IsChecked == true) tasks.AppendLine("- Bảng xét dấu (BXD) chuẩn tkz-tab.");
            if (ChkTaskGraph.IsChecked == true) tasks.AppendLine("- Đồ thị hàm số với trục tọa độ Ox, Oy, mũi tên và tiệm cận.");
            if (ChkTaskGeo.IsChecked == true) tasks.AppendLine("- Hình học 2D/3D: nét đứt cho cạnh khuất, nhãn đỉnh, ký hiệu góc vuông.");
            if (ChkTaskCircuit.IsChecked == true) tasks.AppendLine("- Sơ đồ mạch điện chuẩn circuiTikz.");
            if (ChkTaskAll.IsChecked == true) tasks.AppendLine("- Vẽ toàn bộ tất cả chi tiết và sơ đồ trong ảnh.");
            if (ChkTaskNotes.IsChecked == true) tasks.AppendLine("- Thêm chú thích % giải thích tọa độ và cách dựng hình.");

            if (tasks.Length > 0)
            {
                sb.AppendLine("CÁC YÊU CẦU ĐỊNH DẠNG ĐẶC BIỆT:");
                sb.Append(tasks);
                sb.AppendLine();
            }

            string userText = TxtInputPrompt.Text.Trim();
            if (!string.IsNullOrWhiteSpace(userText))
            {
                sb.AppendLine("MÔ TẢ ĐỀ BÀI HOẶC YÊU CẦU CỤ THỂ:");
                sb.AppendLine(userText);
            }
            else if (_imageBytes != null)
            {
                sb.AppendLine("YÊU CẦU: Phân tích hình ảnh mẫu trên và tái tạo chính xác tuyệt đối bằng mã TikZ chuẩn toán học.");
            }

            return sb.ToString().Trim();
        }

        private System.Threading.CancellationTokenSource? _activeCts;
        private bool _isBusy = false;
        private System.Windows.Threading.DispatcherTimer? _analyzeTimer;
        private System.Diagnostics.Stopwatch _analyzeStopwatch = new System.Diagnostics.Stopwatch();
        private string _currentTimerPrefix = "AI đang xử lý";

        private void StartAnalyzeTimer(string prefix)
        {
            _currentTimerPrefix = prefix;
            _analyzeStopwatch.Restart();
            if (_analyzeTimer == null)
            {
                _analyzeTimer = new System.Windows.Threading.DispatcherTimer
                {
                    Interval = TimeSpan.FromMilliseconds(100)
                };
                _analyzeTimer.Tick += (s, e) =>
                {
                    if (_isBusy)
                    {
                        double sec = _analyzeStopwatch.Elapsed.TotalSeconds;
                        TxtStatus.Text = $"⏳ {_currentTimerPrefix}... ({sec:F1}s)";
                    }
                };
            }
            _analyzeTimer.Start();
        }

        private void StopAnalyzeTimer()
        {
            _analyzeTimer?.Stop();
            _analyzeStopwatch.Stop();
        }

        private async void BtnAutoDraw_Click(object sender, RoutedEventArgs e)
        {
            string prompt = BuildFullPrompt();
            if (string.IsNullOrWhiteSpace(prompt) && _imageBytes == null)
            {
                MessageBox.Show("Vui lòng nhập mô tả hình vẽ hoặc dán ảnh bài toán.", "Chưa có thông tin", MessageBoxButton.OK, MessageBoxImage.Warning);
                return;
            }

            _activeCts?.Dispose();
            _activeCts = new System.Threading.CancellationTokenSource(TimeSpan.FromMinutes(5));

            string prefix = _imageBytes != null ? "AI đang phân tích ảnh & lập trình TikZ" : "AI đang xử lý văn bản & dựng mã TikZ";
            StartAnalyzeTimer(prefix);
            SetBusy(true, $"⏳ {prefix}... (0.0s)");

            try
            {
                var req = new TikzPromptRequest
                {
                    Prompt = prompt,
                    ImageBase64 = _imageBase64,
                    ImageMimeType = _imageMime,
                    DiagramType = DetermineDiagramType()
                };

                var result = await DesktopGeminiFactory.GenerateTikzAsync(req, _activeCts.Token);
                StopAnalyzeTimer();
                double elapsed = _analyzeStopwatch.Elapsed.TotalSeconds;

                if (result.Success && !string.IsNullOrWhiteSpace(result.TikzCode))
                {
                    ResultTikzCode = result.TikzCode;
                    ResultDescription = string.IsNullOrWhiteSpace(TxtInputPrompt.Text) ? prompt : TxtInputPrompt.Text.Trim();
                    DialogResult = true;
                    Close();
                }
                else
                {
                    if (_activeCts.IsCancellationRequested)
                    {
                        SetBusy(false, $"Đã tạm dừng sau {elapsed:F1}s.");
                    }
                    else
                    {
                        SetBusy(false, $"❌ Lỗi sau {elapsed:F1}s: {result.ErrorMessage ?? "Không sinh được mã TikZ."}");
                        MessageBox.Show(result.ErrorMessage ?? "Không nhận được phản hồi từ AI. Vui lòng kiểm tra API Key hoặc chọn mô hình khác.", "Lỗi sinh mã", MessageBoxButton.OK, MessageBoxImage.Warning);
                    }
                }
            }
            catch (OperationCanceledException)
            {
                StopAnalyzeTimer();
                SetBusy(false, $"Đã tạm dừng / hủy tác vụ AI sau {_analyzeStopwatch.Elapsed.TotalSeconds:F1}s.");
            }
            catch (Exception ex)
            {
                StopAnalyzeTimer();
                SetBusy(false, $"❌ Ngoại lệ sau {_analyzeStopwatch.Elapsed.TotalSeconds:F1}s: {ex.Message}");
                MessageBox.Show($"Đã xảy ra lỗi: {ex.Message}", "Lỗi", MessageBoxButton.OK, MessageBoxImage.Error);
            }
        }

        private async void BtnDescribeOnly_Click(object sender, RoutedEventArgs e)
        {
            string prompt = BuildFullPrompt();
            if (string.IsNullOrWhiteSpace(prompt) && _imageBytes == null)
            {
                MessageBox.Show("Vui lòng nhập mô tả hình vẽ hoặc dán ảnh bài toán.", "Chưa có thông tin", MessageBoxButton.OK, MessageBoxImage.Warning);
                return;
            }

            _activeCts?.Dispose();
            _activeCts = new System.Threading.CancellationTokenSource(TimeSpan.FromMinutes(5));

            StartAnalyzeTimer("AI đang trích xuất bản thiết kế và mô tả tọa độ");
            SetBusy(true, "⏳ AI đang trích xuất bản thiết kế và mô tả tọa độ... (0.0s)");

            try
            {
                string describePrompt = "Bạn là chuyên gia hình học Toán THPT. Hãy phân tích ảnh hoặc đề bài dưới đây và xuất BẢN MÔ TẢ CHI TIẾT TỌA ĐỘ, các điểm, đoạn thẳng, nét đứt, nhãn và góc để vẽ lại bằng TikZ:\n\n" + prompt;
                var result = await DesktopGeminiFactory.ExecutePromptAsync(describePrompt, _imageBase64, _imageMime, _activeCts.Token);
                StopAnalyzeTimer();
                double elapsed = _analyzeStopwatch.Elapsed.TotalSeconds;

                if (result.Success && !string.IsNullOrWhiteSpace(result.Content))
                {
                    TxtDescResult.Text = result.Content.Trim();
                    BorderDescArea.Visibility = Visibility.Visible;
                    SetBusy(false, $"Đã tạo mô tả chi tiết trong {elapsed:F1}s. Bạn có thể tinh chỉnh trước khi bấm 'Xác nhận vẽ'.");
                }
                else
                {
                    if (_activeCts.IsCancellationRequested)
                    {
                        SetBusy(false, $"Đã tạm dừng sau {elapsed:F1}s.");
                    }
                    else
                    {
                        SetBusy(false, $"❌ Lỗi sau {elapsed:F1}s: {result.ErrorMessage ?? "Không tạo được mô tả."}");
                    }
                }
            }
            catch (OperationCanceledException)
            {
                StopAnalyzeTimer();
                SetBusy(false, $"Đã tạm dừng sau {_analyzeStopwatch.Elapsed.TotalSeconds:F1}s.");
            }
            catch (Exception ex)
            {
                StopAnalyzeTimer();
                SetBusy(false, $"❌ Lỗi sau {_analyzeStopwatch.Elapsed.TotalSeconds:F1}s: {ex.Message}");
            }
        }

        private void BtnConfirmDrawFromDesc_Click(object sender, RoutedEventArgs e)
        {
            string desc = TxtDescResult.Text.Trim();
            if (string.IsNullOrWhiteSpace(desc)) return;

            TxtInputPrompt.Text = desc;
            BtnAutoDraw_Click(sender, e);
        }

        private void BtnStopAi_Click(object sender, RoutedEventArgs e)
        {
            StopAnalyzeTimer();
            if (_activeCts != null && !_activeCts.IsCancellationRequested)
            {
                _activeCts.Cancel();
            }
            SetBusy(false, $"Đã tạm dừng / hủy tác vụ AI sau {_analyzeStopwatch.Elapsed.TotalSeconds:F1}s.");
        }

        private DiagramType DetermineDiagramType()
        {
            if (ChkTaskBbt.IsChecked == true || ChkTaskBbtNoFrame.IsChecked == true) return DiagramType.BBT;
            if (ChkTaskBxd.IsChecked == true) return DiagramType.BXD;
            if (ChkTaskGraph.IsChecked == true) return DiagramType.DoThi;
            if (ChkTaskGeo.IsChecked == true) return DiagramType.HinhKhongGian;
            return DiagramType.Custom;
        }

        private void SetBusy(bool busy, string status)
        {
            _isBusy = busy;
            TxtStatus.Text = status;
            PrgProgress.Visibility = busy ? Visibility.Visible : Visibility.Collapsed;

            // Nút Dừng lại chỉ hiển thị nổi bật khi đang xử lý
            BtnStopAi.Visibility = busy ? Visibility.Visible : Visibility.Collapsed;
            BtnStopAi.IsEnabled = busy;

            BtnAutoDraw.IsEnabled = !busy;
            BtnDescribeOnly.IsEnabled = !busy;
            BtnChooseImage.IsEnabled = !busy;
            BtnPasteImage.IsEnabled = !busy;
            BtnClose.IsEnabled = true; // Luôn cho phép bấm đóng
        }

        private void BtnClose_Click(object sender, RoutedEventArgs e)
        {
            if (_activeCts != null && !_activeCts.IsCancellationRequested)
            {
                _activeCts.Cancel();
            }
            DialogResult = false;
            Close();
        }

        private void AiDrawPromptDialog_KeyDown(object sender, KeyEventArgs e)
        {
            if (e.Key == Key.Escape)
            {
                if (_isBusy)
                {
                    BtnStopAi_Click(this, new RoutedEventArgs());
                    e.Handled = true;
                }
                else
                {
                    DialogResult = false;
                    Close();
                }
            }
            else if (e.Key == Key.V && (Keyboard.Modifiers & ModifierKeys.Control) == ModifierKeys.Control)
            {
                if (!TxtInputPrompt.IsFocused && !TxtDescResult.IsFocused)
                {
                    BtnPasteImage_Click(this, new RoutedEventArgs());
                    e.Handled = true;
                }
            }
        }
    }
}
