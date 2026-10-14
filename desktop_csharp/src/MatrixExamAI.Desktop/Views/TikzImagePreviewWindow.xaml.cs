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

            Loaded += (s, e) => BtnZoomFit_Click(this, new RoutedEventArgs());
        }

        private void SetZoom(double zoom)
        {
            _currentZoom = Math.Clamp(zoom, 0.1, 10.0);
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
            ResetTranslate();
            SetZoom(1.0);
        }

        private void BtnZoom200_Click(object sender, RoutedEventArgs e)
        {
            ResetTranslate();
            SetZoom(2.0);
        }

        private void BtnZoomFit_Click(object sender, RoutedEventArgs e)
        {
            ResetTranslate();
            if (ImgFullPreview.Source is BitmapSource bs && bs.PixelWidth > 0 && bs.PixelHeight > 0 && ScrollViewerContainer != null)
            {
                double availW = Math.Max(100, ScrollViewerContainer.ActualWidth - 40);
                double availH = Math.Max(100, ScrollViewerContainer.ActualHeight - 40);
                double fit = Math.Min(availW / bs.PixelWidth, availH / bs.PixelHeight);
                if (fit > 0.05 && fit < 10) SetZoom(fit);
                else SetZoom(1.0);
            }
            else
            {
                SetZoom(1.0);
            }
        }

        private void ResetTranslate()
        {
            if (ImgTranslateTransform != null)
            {
                ImgTranslateTransform.X = 0;
                ImgTranslateTransform.Y = 0;
            }
        }

        private void ScrollViewerContainer_PreviewMouseWheel(object sender, MouseWheelEventArgs e)
        {
            double factor = e.Delta > 0 ? 1.15 : 0.85;
            SetZoom(_currentZoom * factor);
            e.Handled = true;
        }

        private void Canvas_MouseDown(object sender, MouseButtonEventArgs e)
        {
            if (e.ChangedButton == MouseButton.Left)
            {
                _isDragging = true;
                _lastMousePos = e.GetPosition(ScrollViewerContainer);
                CanvasContainer.CaptureMouse();
            }
        }

        private void Canvas_MouseMove(object sender, MouseEventArgs e)
        {
            if (_isDragging && ImgTranslateTransform != null)
            {
                var cur = e.GetPosition(ScrollViewerContainer);
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
                CanvasContainer.ReleaseMouseCapture();
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
