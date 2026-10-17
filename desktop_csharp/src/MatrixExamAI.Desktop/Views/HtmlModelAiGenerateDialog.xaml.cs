using System;
using System.IO;
using System.Text;
using System.Windows;
using System.Windows.Input;
using System.Windows.Media.Imaging;
using Microsoft.Win32;

namespace MatrixExamAI.Desktop.Views
{
    public partial class HtmlModelAiGenerateDialog : Window
    {
        private byte[]? _imageBytes = null;

        public string ResultDescription { get; private set; } = string.Empty;
        public byte[]? ResultImageBytes => _imageBytes;

        public HtmlModelAiGenerateDialog(string initialPrompt = "", byte[]? initialImage = null)
        {
            InitializeComponent();

            TxtUserPrompt.Text = initialPrompt ?? string.Empty;
            _imageBytes = initialImage;

            Loaded += (s, e) =>
            {
                TxtUserPrompt.Focus();
                if (_imageBytes != null && _imageBytes.Length > 0)
                {
                    LoadImageToPreview(_imageBytes);
                }
            };
        }

        private void BtnPasteImage_Click(object sender, RoutedEventArgs e)
        {
            PasteImageFromClipboard();
        }

        private void PasteImageFromClipboard()
        {
            if (Clipboard.ContainsImage())
            {
                try
                {
                    var bitmap = Clipboard.GetImage();
                    if (bitmap != null)
                    {
                        var encoder = new PngBitmapEncoder();
                        encoder.Frames.Add(BitmapFrame.Create(bitmap));
                        using var ms = new MemoryStream();
                        encoder.Save(ms);
                        _imageBytes = ms.ToArray();
                        LoadImageToPreview(_imageBytes);
                        TxtStatus.Text = "✓ Đã dán ảnh thành công từ Clipboard.";
                    }
                }
                catch (Exception ex)
                {
                    MessageBox.Show($"Không thể dán ảnh: {ex.Message}", "Lỗi dán ảnh", MessageBoxButton.OK, MessageBoxImage.Warning);
                }
            }
            else
            {
                MessageBox.Show("Clipboard không chứa hình ảnh hợp lệ.\nHãy chụp màn hình (Win+Shift+S) rồi thử lại.", "Không tìm thấy ảnh", MessageBoxButton.OK, MessageBoxImage.Information);
            }
        }

        private void BtnChooseImage_Click(object sender, RoutedEventArgs e)
        {
            var ofd = new OpenFileDialog
            {
                Title = "Chọn ảnh bài toán hoặc mô hình 3D",
                Filter = "Tệp hình ảnh (*.png;*.jpg;*.jpeg;*.bmp;*.webp)|*.png;*.jpg;*.jpeg;*.bmp;*.webp|Tất cả tệp (*.*)|*.*"
            };

            if (ofd.ShowDialog() == true)
            {
                try
                {
                    _imageBytes = File.ReadAllBytes(ofd.FileName);
                    LoadImageToPreview(_imageBytes);
                    TxtStatus.Text = $"✓ Đã chọn ảnh: {Path.GetFileName(ofd.FileName)}";
                }
                catch (Exception ex)
                {
                    MessageBox.Show($"Không thể đọc ảnh: {ex.Message}", "Lỗi đọc tệp", MessageBoxButton.OK, MessageBoxImage.Error);
                }
            }
        }

        private void BtnClearImage_Click(object sender, RoutedEventArgs e)
        {
            _imageBytes = null;
            ImgPreview.Source = null;
            BorderImagePreview.Visibility = Visibility.Collapsed;
            BorderDropZone.Visibility = Visibility.Visible;
            BtnClearImage.Visibility = Visibility.Collapsed;
            TxtStatus.Text = "Đã xóa ảnh đính kèm.";
        }

        private void LoadImageToPreview(byte[] bytes)
        {
            try
            {
                using var ms = new MemoryStream(bytes);
                var bitmap = new BitmapImage();
                bitmap.BeginInit();
                bitmap.CacheOption = BitmapCacheOption.OnLoad;
                bitmap.StreamSource = ms;
                bitmap.EndInit();
                bitmap.Freeze();

                ImgPreview.Source = bitmap;
                TxtImageDimensions.Text = $"Kích thước: {bitmap.PixelWidth} × {bitmap.PixelHeight} px";
                TxtImageSize.Text = $"Dung lượng: {bytes.Length / 1024.0:F1} KB";

                BorderDropZone.Visibility = Visibility.Collapsed;
                BorderImagePreview.Visibility = Visibility.Visible;
                BtnClearImage.Visibility = Visibility.Visible;
            }
            catch (Exception ex)
            {
                MessageBox.Show($"Lỗi hiển thị ảnh: {ex.Message}", "Lỗi", MessageBoxButton.OK, MessageBoxImage.Error);
            }
        }

        private void BorderDropZone_DragOver(object sender, DragEventArgs e)
        {
            if (e.Data.GetDataPresent(DataFormats.FileDrop))
            {
                e.Effects = DragDropEffects.Copy;
                e.Handled = true;
            }
        }

        private void BorderDropZone_Drop(object sender, DragEventArgs e)
        {
            if (e.Data.GetDataPresent(DataFormats.FileDrop))
            {
                string[] files = (string[])e.Data.GetData(DataFormats.FileDrop);
                if (files != null && files.Length > 0)
                {
                    string file = files[0];
                    string ext = Path.GetExtension(file).ToLowerInvariant();
                    if (ext == ".png" || ext == ".jpg" || ext == ".jpeg" || ext == ".bmp" || ext == ".webp")
                    {
                        try
                        {
                            _imageBytes = File.ReadAllBytes(file);
                            LoadImageToPreview(_imageBytes);
                            TxtStatus.Text = $"✓ Đã tải ảnh thả: {Path.GetFileName(file)}";
                        }
                        catch (Exception ex)
                        {
                            MessageBox.Show($"Không thể đọc ảnh: {ex.Message}", "Lỗi", MessageBoxButton.OK, MessageBoxImage.Error);
                        }
                    }
                }
            }
        }

        private void BorderDropZone_MouseLeftButtonDown(object sender, MouseButtonEventArgs e)
        {
            BtnChooseImage_Click(sender, e);
        }

        private void BorderImagePreview_MouseLeftButtonDown(object sender, MouseButtonEventArgs e)
        {
            if (ImgPreview.Source != null)
            {
                var viewer = new TikzImagePreviewWindow(ImgPreview.Source, null, 300, "Ảnh đề bài / mô hình đính kèm");
                viewer.Owner = this;
                viewer.ShowDialog();
            }
        }

        private void BtnTextOnly_Click(object sender, RoutedEventArgs e)
        {
            _imageBytes = null;
            ProceedWithGeneration();
        }

        private void BtnAnalyzeAndGenerate_Click(object sender, RoutedEventArgs e)
        {
            ProceedWithGeneration();
        }

        private void ProceedWithGeneration()
        {
            string prompt = TxtUserPrompt.Text.Trim();
            if (string.IsNullOrWhiteSpace(prompt) && _imageBytes == null)
            {
                MessageBox.Show("Vui lòng nhập đề bài hoặc đính kèm ảnh minh họa để AI có cơ sở lập trình mô hình.", "Chưa có thông tin", MessageBoxButton.OK, MessageBoxImage.Information);
                TxtUserPrompt.Focus();
                return;
            }

            var sb = new StringBuilder();
            sb.AppendLine(prompt);

            // Bổ sung các chỉ định chuyên đề đã chọn
            var options = new System.Collections.Generic.List<string>();
            if (ChkSolidRev.IsChecked == true) options.Add("Khối tròn xoay & tích phân (LatheGeometry xoay quanh trục)");
            if (ChkSpatial.IsChecked == true) options.Add("Hình học không gian 3D & mặt phẳng thiết diện");
            if (ChkOxyz.IsChecked == true) options.Add("Hệ trục tọa độ Oxyz & vector");
            if (ChkSurface.IsChecked == true) options.Add("Mặt cong 3D & đồ thị hàm số");
            if (ChkPhysics.IsChecked == true) options.Add("Mô phỏng dao động vật lý & sóng");
            if (ChkChemistry.IsChecked == true) options.Add("Cấu trúc phân tử 3D CPK");
            if (ChkBiology.IsChecked == true) options.Add("Chuỗi xoắn kép ADN");

            if (options.Count > 0)
            {
                sb.AppendLine();
                sb.AppendLine($"[CHUYÊN ĐỀ ƯU TIÊN]: {string.Join(", ", options)}.");
            }

            ResultDescription = sb.ToString().Trim();
            DialogResult = true;
            Close();
        }

        private void BtnCancel_Click(object sender, RoutedEventArgs e)
        {
            DialogResult = false;
            Close();
        }

        private void HtmlModelAiGenerateDialog_KeyDown(object sender, KeyEventArgs e)
        {
            if (e.Key == Key.Escape)
            {
                DialogResult = false;
                Close();
            }
            else if (e.Key == Key.V && (Keyboard.Modifiers & ModifierKeys.Control) == ModifierKeys.Control && Clipboard.ContainsImage())
            {
                PasteImageFromClipboard();
                e.Handled = true;
            }
            else if (e.Key == Key.Enter && (Keyboard.Modifiers & ModifierKeys.Control) == ModifierKeys.Control)
            {
                ProceedWithGeneration();
                e.Handled = true;
            }
        }
    }
}
