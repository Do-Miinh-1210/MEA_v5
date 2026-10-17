using System;
using System.Diagnostics;
using System.IO;
using System.Windows;
using System.Windows.Input;
using System.Windows.Media;
using System.Windows.Media.Imaging;
using Microsoft.Win32;
using MatrixExamAI.Desktop.Services;

namespace MatrixExamAI.Desktop.Views
{
    public partial class TikzImagePreviewWindow : Window
    {
        private double _currentZoom = 1.0;
        private bool _isDragging = false;
        private Point _lastMousePos;
        private string? _filePath;
        private ImageSource? _currentSource;

        public TikzImagePreviewWindow(ImageSource? imageSource, string? filePath = null, int dpi = 600, string? title = null)
        {
            InitializeComponent();
            _filePath = filePath;
            _currentSource = imageSource;

            if (!string.IsNullOrWhiteSpace(title))
            {
                TxtTitleInfo.Text = title;
            }
            else
            {
                TxtTitleInfo.Text = $"Xem hình vẽ TikZ chi tiết ({dpi} DPI)";
            }

            if (imageSource != null)
            {
                ImgFullPreview.Source = imageSource;
                if (imageSource is BitmapSource bs)
                {
                    TxtResolutionInfo.Text = $"{bs.PixelWidth} × {bs.PixelHeight} px ({dpi} DPI)";
                }
            }

            Loaded += (s, e) =>
            {
                Dispatcher.BeginInvoke(System.Windows.Threading.DispatcherPriority.Loaded, new Action(() =>
                {
                    BtnZoomFit_Click(this, new RoutedEventArgs());
                }));
            };
        }

        private void CenterContent(double zoom)
        {
            _currentZoom = Math.Clamp(zoom, 0.05, 15.0);
            if (ImgScaleTransform != null)
            {
                ImgScaleTransform.ScaleX = _currentZoom;
                ImgScaleTransform.ScaleY = _currentZoom;
            }

            if (ImgTranslateTransform != null && CanvasContainer != null)
            {
                double cardW = (ImgFullPreview.Source is BitmapSource bs && bs.Width > 0) ? (bs.Width + 34) : 400;
                double cardH = (ImgFullPreview.Source is BitmapSource bs2 && bs2.Height > 0) ? (bs2.Height + 34) : 300;
                double canvasW = CanvasContainer.ActualWidth > 0 ? CanvasContainer.ActualWidth : cardW;
                double canvasH = CanvasContainer.ActualHeight > 0 ? CanvasContainer.ActualHeight : cardH;

                ImgTranslateTransform.X = (canvasW / 2.0) * (1.0 - _currentZoom);
                ImgTranslateTransform.Y = (canvasH / 2.0) * (1.0 - _currentZoom);
            }

            if (TxtZoomLevel != null)
            {
                TxtZoomLevel.Text = $"Thu phóng: {_currentZoom * 100:0}%";
            }
        }

        private void SetZoomAt(double targetZoom, Point focalPoint)
        {
            double newZoom = Math.Clamp(targetZoom, 0.05, 15.0);
            if (Math.Abs(newZoom - _currentZoom) < 0.0001) return;

            if (ImgTranslateTransform != null && ViewportContainer != null && CanvasContainer != null)
            {
                double ratio = newZoom / _currentZoom;
                double cardW = (ImgFullPreview.Source is BitmapSource bs && bs.Width > 0) ? (bs.Width + 34) : 400;
                double cardH = (ImgFullPreview.Source is BitmapSource bs2 && bs2.Height > 0) ? (bs2.Height + 34) : 300;
                double canvasW = CanvasContainer.ActualWidth > 0 ? CanvasContainer.ActualWidth : cardW;
                double canvasH = CanvasContainer.ActualHeight > 0 ? CanvasContainer.ActualHeight : cardH;

                double originX = (ViewportContainer.ActualWidth - canvasW) / 2.0;
                double originY = (ViewportContainer.ActualHeight - canvasH) / 2.0;

                ImgTranslateTransform.X = (focalPoint.X - originX) - (focalPoint.X - originX - ImgTranslateTransform.X) * ratio;
                ImgTranslateTransform.Y = (focalPoint.Y - originY) - (focalPoint.Y - originY - ImgTranslateTransform.Y) * ratio;
            }

            _currentZoom = newZoom;
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

        private void BtnZoomIn_Click(object sender, RoutedEventArgs e)
        {
            Point center = new Point(ViewportContainer.ActualWidth / 2.0, ViewportContainer.ActualHeight / 2.0);
            SetZoomAt(_currentZoom * 1.25, center);
        }

        private void BtnZoomOut_Click(object sender, RoutedEventArgs e)
        {
            Point center = new Point(ViewportContainer.ActualWidth / 2.0, ViewportContainer.ActualHeight / 2.0);
            SetZoomAt(_currentZoom / 1.25, center);
        }

        private void BtnZoomReset_Click(object sender, RoutedEventArgs e) => CenterContent(1.0);

        private void BtnZoom200_Click(object sender, RoutedEventArgs e) => CenterContent(2.0);

        private void BtnZoomFit_Click(object sender, RoutedEventArgs e)
        {
            if (ImgFullPreview.Source is BitmapSource bs && ViewportContainer != null)
            {
                double imgW = bs.Width > 0 ? bs.Width : bs.PixelWidth;
                double imgH = bs.Height > 0 ? bs.Height : bs.PixelHeight;

                double cardW = imgW + 34;
                double cardH = imgH + 34;

                double availW = Math.Max(100, ViewportContainer.ActualWidth - 48);
                double availH = Math.Max(100, ViewportContainer.ActualHeight - 48);

                double fit = Math.Min(availW / cardW, availH / cardH);
                fit = Math.Clamp(fit * 0.95, 0.05, 5.0);

                CenterContent(fit);
            }
            else
            {
                CenterContent(1.0);
            }
        }

        private void Window_PreviewMouseWheel(object sender, MouseWheelEventArgs e)
        {
            double factor = e.Delta > 0 ? 1.15 : (1.0 / 1.15);
            Point mousePos = e.GetPosition(ViewportContainer);
            SetZoomAt(_currentZoom * factor, mousePos);
            e.Handled = true;
        }

        private void Canvas_MouseDown(object sender, MouseButtonEventArgs e)
        {
            if (e.ChangedButton == MouseButton.Left)
            {
                if (e.ClickCount == 2)
                {
                    BtnZoomFit_Click(sender, e);
                    e.Handled = true;
                    return;
                }
                _isDragging = true;
                _lastMousePos = e.GetPosition(ViewportContainer);
                ViewportContainer.CaptureMouse();
            }
        }

        private void Canvas_MouseMove(object sender, MouseEventArgs e)
        {
            if (_isDragging && ImgTranslateTransform != null)
            {
                var cur = e.GetPosition(ViewportContainer);
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
                ViewportContainer.ReleaseMouseCapture();
            }
        }

        private void BtnCopyImage_Click(object sender, RoutedEventArgs e)
        {
            if (ImgFullPreview.Source is BitmapSource bs)
            {
                try
                {
                    SafeClipboard.SetImage(bs);
                    MessageBox.Show("Đã sao chép hình ảnh vào bộ nhớ đệm (Clipboard)!", "Sao chép thành công", MessageBoxButton.OK, MessageBoxImage.Information);
                }
                catch (Exception ex)
                {
                    MessageBox.Show($"Không thể sao chép ảnh: {ex.Message}", "Lỗi sao chép", MessageBoxButton.OK, MessageBoxImage.Warning);
                }
            }
        }

        private void BtnSaveImage_Click(object sender, RoutedEventArgs e)
        {
            if (ImgFullPreview.Source is not BitmapSource bs)
            {
                MessageBox.Show("Không có hình ảnh để lưu.", "Thông báo", MessageBoxButton.OK, MessageBoxImage.Information);
                return;
            }

            var dlg = new SaveFileDialog
            {
                Title = "Lưu hình vẽ TikZ độ nét cao",
                Filter = "Tệp hình ảnh PNG (*.png)|*.png|Tệp JPEG (*.jpg)|*.jpg|Tệp Bitmap (*.bmp)|*.bmp",
                FileName = $"TikZ_Figure_{DateTime.Now:yyyyMMdd_HHmmss}.png"
            };

            if (dlg.ShowDialog() == true)
            {
                try
                {
                    using var fs = new FileStream(dlg.FileName, FileMode.Create);
                    var encoder = new PngBitmapEncoder();
                    encoder.Frames.Add(BitmapFrame.Create(bs));
                    encoder.Save(fs);
                    MessageBox.Show($"Đã lưu ảnh thành công:\n{dlg.FileName}", "Lưu hoàn tất", MessageBoxButton.OK, MessageBoxImage.Information);
                }
                catch (Exception ex)
                {
                    MessageBox.Show($"Lỗi khi lưu ảnh: {ex.Message}", "Lỗi lưu file", MessageBoxButton.OK, MessageBoxImage.Error);
                }
            }
        }

        private void BtnOpenExternal_Click(object sender, RoutedEventArgs e)
        {
            if (!string.IsNullOrEmpty(_filePath) && File.Exists(_filePath))
            {
                try
                {
                    Process.Start(new ProcessStartInfo
                    {
                        FileName = _filePath,
                        UseShellExecute = true
                    });
                }
                catch (Exception ex)
                {
                    MessageBox.Show($"Không thể mở file ngoài: {ex.Message}", "Lỗi mở file", MessageBoxButton.OK, MessageBoxImage.Warning);
                }
            }
            else
            {
                MessageBox.Show("Không tìm thấy đường dẫn file ảnh gốc trên ổ đĩa để mở ngoài.", "Chưa có file cục bộ", MessageBoxButton.OK, MessageBoxImage.Information);
            }
        }

        private void BtnClose_Click(object sender, RoutedEventArgs e)
        {
            Close();
        }

        private void TikzImagePreviewWindow_KeyDown(object sender, KeyEventArgs e)
        {
            if (e.Key == Key.Escape)
            {
                Close();
                e.Handled = true;
                return;
            }

            if (e.Key == Key.C && (Keyboard.Modifiers & ModifierKeys.Control) == ModifierKeys.Control)
            {
                BtnCopyImage_Click(sender, e);
                e.Handled = true;
                return;
            }

            if (e.Key == Key.S && (Keyboard.Modifiers & ModifierKeys.Control) == ModifierKeys.Control)
            {
                BtnSaveImage_Click(sender, e);
                e.Handled = true;
                return;
            }

            if (e.Key == Key.OemPlus || e.Key == Key.Add)
            {
                BtnZoomIn_Click(sender, e);
                e.Handled = true;
                return;
            }

            if (e.Key == Key.OemMinus || e.Key == Key.Subtract)
            {
                BtnZoomOut_Click(sender, e);
                e.Handled = true;
                return;
            }

            if (e.Key == Key.D0 && (Keyboard.Modifiers & ModifierKeys.Control) == ModifierKeys.Control)
            {
                BtnZoomReset_Click(sender, e);
                e.Handled = true;
                return;
            }
        }
    }
}
