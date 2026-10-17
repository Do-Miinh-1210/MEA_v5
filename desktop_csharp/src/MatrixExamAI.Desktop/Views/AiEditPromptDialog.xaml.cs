using System;
using System.IO;
using System.Windows;
using System.Windows.Input;
using System.Windows.Media.Imaging;
using Microsoft.Win32;

namespace MatrixExamAI.Desktop.Views
{
    public partial class AiEditPromptDialog : Window
    {
        public string? ResultDescription { get; private set; }
        public byte[]? ResultImageBytes { get; private set; }
        public string? ResultImageBase64 { get; private set; }

        public AiEditPromptDialog(string? initialPrompt = null, byte[]? initialImage = null)
        {
            InitializeComponent();

            if (!string.IsNullOrWhiteSpace(initialPrompt))
            {
                TxtEditRequest.Text = initialPrompt;
                TxtEditRequest.SelectAll();
            }

            if (initialImage != null && initialImage.Length > 0)
            {
                LoadImageBytes(initialImage);
            }

            Loaded += (s, e) =>
            {
                TxtEditRequest.Focus();
            };
        }

        private void LoadImageBytes(byte[] bytes)
        {
            try
            {
                using var ms = new MemoryStream(bytes);
                var bi = new BitmapImage();
                bi.BeginInit();
                bi.CacheOption = BitmapCacheOption.OnLoad;
                bi.StreamSource = ms;
                bi.EndInit();
                bi.Freeze();

                ImgPreview.Source = bi;
                TxtImageDimensions.Text = $"Kích thước: {bi.PixelWidth} x {bi.PixelHeight} px";
                TxtImageSize.Text = $"Dung lượng: {bytes.Length / 1024.0:F1} KB";

                BorderImagePreview.Visibility = Visibility.Visible;
                BorderDropZone.Visibility = Visibility.Collapsed;
                BtnClearImage.Visibility = Visibility.Visible;

                ResultImageBytes = bytes;
                ResultImageBase64 = Convert.ToBase64String(bytes);
                TxtStatus.Text = "✓ Đã nhận ảnh mẫu. AI sẽ dùng thị giác máy tính Vision để chỉnh sửa hình.";
            }
            catch (Exception ex)
            {
                MessageBox.Show($"Không thể nạp tệp hình ảnh: {ex.Message}", "Lỗi ảnh", MessageBoxButton.OK, MessageBoxImage.Warning);
            }
        }

        private void ClearImage()
        {
            ResultImageBytes = null;
            ResultImageBase64 = null;
            ImgPreview.Source = null;
            BorderImagePreview.Visibility = Visibility.Collapsed;
            BorderDropZone.Visibility = Visibility.Visible;
            BtnClearImage.Visibility = Visibility.Collapsed;
            TxtStatus.Text = "Đã gỡ ảnh đính kèm.";
        }

        private void BtnPasteImage_Click(object sender, RoutedEventArgs e)
        {
            if (Clipboard.ContainsImage())
            {
                try
                {
                    var image = Clipboard.GetImage();
                    if (image != null)
                    {
                        using var ms = new MemoryStream();
                        var encoder = new PngBitmapEncoder();
                        encoder.Frames.Add(BitmapFrame.Create(image));
                        encoder.Save(ms);
                        LoadImageBytes(ms.ToArray());
                    }
                }
                catch (Exception ex)
                {
                    MessageBox.Show($"Không thể dán ảnh từ Clipboard: {ex.Message}", "Lỗi", MessageBoxButton.OK, MessageBoxImage.Error);
                }
            }
            else if (Clipboard.ContainsFileDropList())
            {
                var files = Clipboard.GetFileDropList();
                foreach (string file in files)
                {
                    string ext = Path.GetExtension(file).ToLowerInvariant();
                    if (ext is ".png" or ".jpg" or ".jpeg" or ".webp" or ".bmp")
                    {
                        LoadImageBytes(File.ReadAllBytes(file));
                        return;
                    }
                }
                MessageBox.Show("Tệp trong Clipboard không phải định dạng hình ảnh hợp lệ (.png, .jpg, .webp).", "Thông báo", MessageBoxButton.OK, MessageBoxImage.Information);
            }
            else
            {
                MessageBox.Show("Không có hình ảnh nào trong Clipboard.\nHãy dùng tổ hợp phím Win+Shift+S để chụp màn hình vùng bài toán/hình vẽ rồi dán vào đây.", "Chưa có ảnh", MessageBoxButton.OK, MessageBoxImage.Information);
            }
        }

        private void BtnChooseImage_Click(object sender, RoutedEventArgs e)
        {
            var dlg = new OpenFileDialog
            {
                Title = "Chọn hình ảnh bài toán cần AI chỉnh sửa",
                Filter = "Tệp hình ảnh (*.png;*.jpg;*.jpeg;*.webp;*.bmp)|*.png;*.jpg;*.jpeg;*.webp;*.bmp|Tất cả tệp (*.*)|*.*"
            };

            if (dlg.ShowDialog() == true)
            {
                LoadImageBytes(File.ReadAllBytes(dlg.FileName));
            }
        }

        private void BtnClearImage_Click(object sender, RoutedEventArgs e)
        {
            ClearImage();
        }

        private void BorderDropZone_MouseLeftButtonDown(object sender, MouseButtonEventArgs e)
        {
            BtnPasteImage_Click(sender, e);
        }

        private void BorderDropZone_DragOver(object sender, DragEventArgs e)
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

        private void BorderDropZone_Drop(object sender, DragEventArgs e)
        {
            if (!e.Data.GetDataPresent(DataFormats.FileDrop)) return;
            var files = (string[])e.Data.GetData(DataFormats.FileDrop);
            if (files != null && files.Length > 0)
            {
                string ext = Path.GetExtension(files[0]).ToLowerInvariant();
                if (ext is ".png" or ".jpg" or ".jpeg" or ".webp" or ".bmp")
                {
                    LoadImageBytes(File.ReadAllBytes(files[0]));
                }
            }
        }

        private void BorderImagePreview_MouseLeftButtonDown(object sender, MouseButtonEventArgs e)
        {
            if (ImgPreview.Source != null)
            {
                var viewer = new TikzImagePreviewWindow(ImgPreview.Source, null, 300, "Ảnh minh họa yêu cầu chỉnh sửa")
                {
                    Owner = this
                };
                viewer.ShowDialog();
            }
        }

        private void AiEditPromptDialog_KeyDown(object sender, KeyEventArgs e)
        {
            if (e.Key == Key.V && (Keyboard.Modifiers & ModifierKeys.Control) == ModifierKeys.Control)
            {
                if (Clipboard.ContainsImage())
                {
                    BtnPasteImage_Click(sender, e);
                    e.Handled = true;
                    return;
                }
            }

            if (e.Key == Key.Enter && (Keyboard.Modifiers & ModifierKeys.Control) == ModifierKeys.Control)
            {
                BtnOk_Click(sender, e);
                e.Handled = true;
                return;
            }

            if (e.Key == Key.Escape)
            {
                DialogResult = false;
                Close();
                e.Handled = true;
            }
        }

        private void BtnOk_Click(object sender, RoutedEventArgs e)
        {
            string text = TxtEditRequest.Text?.Trim() ?? string.Empty;

            if (string.IsNullOrWhiteSpace(text) && ResultImageBytes == null)
            {
                MessageBox.Show("Vui lòng nhập nội dung yêu cầu chỉnh sửa hoặc dán ảnh minh họa trước khi bấm Đồng ý.", "Chưa có nội dung", MessageBoxButton.OK, MessageBoxImage.Information);
                TxtEditRequest.Focus();
                return;
            }

            if (string.IsNullOrWhiteSpace(text) && ResultImageBytes != null)
            {
                text = "Chỉnh sửa và hoàn thiện mã TikZ khớp chính xác với hình ảnh minh họa được đính kèm.";
            }

            ResultDescription = text;
            DialogResult = true;
            Close();
        }

        private void BtnCancel_Click(object sender, RoutedEventArgs e)
        {
            DialogResult = false;
            Close();
        }
    }
}
