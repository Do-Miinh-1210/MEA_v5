using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Input;
using System.Windows.Media;
using System.Windows.Media.Imaging;
using MatrixExamAI.Desktop.Services;

namespace MatrixExamAI.Desktop.Views
{
    public partial class FigureBankDialog : Window
    {
        public class FigureItemViewModel
        {
            public required FigureEntry Entry { get; set; }
            public string Id => Entry.Id;
            public string Title => Entry.Title;
            public string Source => Entry.Source switch
            {
                "ai" => "🤖 AI",
                "manual" => "✋ Thủ công",
                "template" => "📐 Mẫu",
                "nhch" => "🗂 NHCH",
                "rendered" => "💾 Tự lưu",
                _ => Entry.Source
            };
            public string TagsDisplay => string.Join(", ", Entry.Tags);
            public string CreatedAtDisplay => !string.IsNullOrEmpty(Entry.CreatedAt) && Entry.CreatedAt.Length >= 10
                ? Entry.CreatedAt[..10]
                : Entry.CreatedAt;

            public ImageSource? ThumbnailSource { get; set; }
            public bool HasThumbnail => ThumbnailSource != null;
        }

        public string LoadedFigureId { get; private set; } = string.Empty;
        public string LoadedTikzCode { get; private set; } = string.Empty;
        public string LoadedTitle { get; private set; } = string.Empty;
        public string? LoadedPngPath { get; private set; }

        private List<FigureItemViewModel> _allFigures = new();
        private FigureEntry? _selectedEntry;
        private bool _isSyncingSelection = false;

        public FigureBankDialog()
        {
            InitializeComponent();
            Loaded += (s, e) => RefreshFigureList();
        }

        private static BitmapImage? LoadThumbnail(string? path)
        {
            if (string.IsNullOrEmpty(path) || !File.Exists(path)) return null;
            try
            {
                using var stream = File.OpenRead(path);
                var bi = new BitmapImage();
                bi.BeginInit();
                bi.DecodePixelWidth = 200;
                bi.CacheOption = BitmapCacheOption.OnLoad;
                bi.StreamSource = stream;
                bi.EndInit();
                bi.Freeze();
                return bi;
            }
            catch
            {
                return null;
            }
        }

        private void RefreshFigureList()
        {
            try
            {
                string query = TxtSearchQuery.Text.Trim();
                string source = (CmbSourceFilter.SelectedItem as ComboBoxItem)?.Tag?.ToString() ?? "all";

                var entries = FigureBankService.ListFigures(query, source);
                string bankDir = FigureBankService.GetFiguresDirectory();

                _allFigures = entries.Select(e => new FigureItemViewModel
                {
                    Entry = e,
                    ThumbnailSource = LoadThumbnail(e.GetPngPath(bankDir))
                }).ToList();

                ListCardsFigures.ItemsSource = _allFigures;
                GridFigures.ItemsSource = _allFigures;
                TxtTotalCount.Text = $"{entries.Count} hình vẽ";

                if (_allFigures.Count > 0)
                {
                    ListCardsFigures.SelectedIndex = 0;
                    GridFigures.SelectedIndex = 0;
                }
                else
                {
                    ClearPreview();
                }
            }
            catch (Exception ex)
            {
                MessageBox.Show($"Lỗi tải danh sách hình: {ex.Message}", "Lỗi", MessageBoxButton.OK, MessageBoxImage.Error);
            }
        }

        private void ClearPreview()
        {
            _selectedEntry = null;
            TxtSelectedTitle.Text = "Không tìm thấy hình vẽ";
            TxtSelectedMeta.Text = "Hãy thử tìm kiếm với từ khóa khác hoặc chuyển sang nguồn khác.";
            ImgPreview.Source = null;
            PanelNoImage.Visibility = Visibility.Visible;
            TxtTikzCodePreview.Text = string.Empty;
        }

        private void DisplayPreview(FigureEntry entry)
        {
            _selectedEntry = entry;
            TxtSelectedTitle.Text = $"[{entry.Id}] {entry.Title}";
            TxtSelectedMeta.Text = $"Nguồn: {entry.Source} | Ngày tạo: {entry.CreatedAt} | Thẻ: {string.Join(", ", entry.Tags)}";

            string code = FigureBankService.GetTikzCode(entry);
            TxtTikzCodePreview.Text = code;

            string bankDir = FigureBankService.GetFiguresDirectory();
            string? pngPath = entry.GetPngPath(bankDir);

            if (!string.IsNullOrEmpty(pngPath) && File.Exists(pngPath))
            {
                try
                {
                    using var stream = File.OpenRead(pngPath);
                    var bi = new BitmapImage();
                    bi.BeginInit();
                    bi.CacheOption = BitmapCacheOption.OnLoad;
                    bi.StreamSource = stream;
                    bi.EndInit();
                    bi.Freeze();

                    ImgPreview.Source = bi;
                    PanelNoImage.Visibility = Visibility.Collapsed;
                }
                catch
                {
                    ImgPreview.Source = null;
                    PanelNoImage.Visibility = Visibility.Visible;
                }
            }
            else
            {
                ImgPreview.Source = null;
                PanelNoImage.Visibility = Visibility.Visible;
            }
        }

        private void ListCardsFigures_SelectionChanged(object sender, SelectionChangedEventArgs e)
        {
            if (_isSyncingSelection) return;
            if (ListCardsFigures.SelectedItem is FigureItemViewModel vm)
            {
                _isSyncingSelection = true;
                GridFigures.SelectedItem = vm;
                _isSyncingSelection = false;
                DisplayPreview(vm.Entry);
            }
        }

        private void ListCardsFigures_MouseDoubleClick(object sender, MouseButtonEventArgs e)
        {
            BtnLoadFigure_Click(sender, e);
        }

        private void GridFigures_SelectionChanged(object sender, SelectionChangedEventArgs e)
        {
            if (_isSyncingSelection) return;
            if (GridFigures.SelectedItem is FigureItemViewModel vm)
            {
                _isSyncingSelection = true;
                ListCardsFigures.SelectedItem = vm;
                _isSyncingSelection = false;
                DisplayPreview(vm.Entry);
            }
        }

        private void ViewMode_Changed(object sender, RoutedEventArgs e)
        {
            if (CardViewContainer == null || ListViewContainer == null) return;
            if (RbViewCards?.IsChecked == true)
            {
                CardViewContainer.Visibility = Visibility.Visible;
                ListViewContainer.Visibility = Visibility.Collapsed;
            }
            else
            {
                CardViewContainer.Visibility = Visibility.Collapsed;
                ListViewContainer.Visibility = Visibility.Visible;
            }
        }

        private void GridFigures_MouseDoubleClick(object sender, MouseButtonEventArgs e)
        {
            BtnLoadFigure_Click(sender, e);
        }

        private void TxtSearchQuery_TextChanged(object sender, TextChangedEventArgs e)
        {
            RefreshFigureList();
        }

        private void CmbSourceFilter_SelectionChanged(object sender, SelectionChangedEventArgs e)
        {
            if (IsLoaded)
            {
                RefreshFigureList();
            }
        }

        private void BtnLoadFigure_Click(object sender, RoutedEventArgs e)
        {
            if (_selectedEntry == null)
            {
                MessageBox.Show("Vui lòng chọn một hình vẽ trong danh sách trước.", "Chưa chọn hình", MessageBoxButton.OK, MessageBoxImage.Information);
                return;
            }

            string code = TxtTikzCodePreview.Text;
            if (string.IsNullOrWhiteSpace(code))
            {
                MessageBox.Show("Hình này không có mã TikZ để nạp.", "Mã rỗng", MessageBoxButton.OK, MessageBoxImage.Warning);
                return;
            }

            LoadedFigureId = _selectedEntry.Id;
            LoadedTikzCode = code;
            LoadedTitle = _selectedEntry.Title;

            string bankDir = FigureBankService.GetFiguresDirectory();
            string? pngPath = _selectedEntry.GetPngPath(bankDir);
            if (!string.IsNullOrEmpty(pngPath) && File.Exists(pngPath))
            {
                LoadedPngPath = pngPath;
            }

            DialogResult = true;
            Close();
        }

        private void BtnUpdateCode_Click(object sender, RoutedEventArgs e)
        {
            if (_selectedEntry == null)
            {
                MessageBox.Show("Vui lòng chọn hình cần cập nhật trong danh sách.", "Chưa chọn hình", MessageBoxButton.OK, MessageBoxImage.Information);
                return;
            }

            string newCode = TxtTikzCodePreview.Text.Trim();
            if (string.IsNullOrWhiteSpace(newCode))
            {
                MessageBox.Show("Mã TikZ không được để trống.", "Mã rỗng", MessageBoxButton.OK, MessageBoxImage.Warning);
                return;
            }

            var confirm = MessageBox.Show(
                $"Bạn có chắc chắn muốn LƯU ĐÈ (Cập nhật) mã TikZ cho hình '[{_selectedEntry.Id}] {_selectedEntry.Title}'?\nMã nguồn tệp figure_{_selectedEntry.Id}.tex sẽ được ghi đè bằng mã mới này.",
                "Xác nhận lưu đè mã TikZ",
                MessageBoxButton.YesNo,
                MessageBoxImage.Question);

            if (confirm != MessageBoxResult.Yes) return;

            bool updated = FigureBankService.UpdateFigure(_selectedEntry.Id, newCode);
            if (updated)
            {
                MessageBox.Show($"Đã lưu đè thành công mã TikZ cho hình '[{_selectedEntry.Id}] {_selectedEntry.Title}'.", "Thành công", MessageBoxButton.OK, MessageBoxImage.Information);
                string currentId = _selectedEntry.Id;
                RefreshFigureList();
                SelectFigureById(currentId);
            }
            else
            {
                MessageBox.Show("Không thể cập nhật hình trong kho.", "Lỗi", MessageBoxButton.OK, MessageBoxImage.Error);
            }
        }

        private void SelectFigureById(string id)
        {
            var item = _allFigures.FirstOrDefault(f => f.Id == id);
            if (item != null)
            {
                _isSyncingSelection = true;
                ListCardsFigures.SelectedItem = item;
                GridFigures.SelectedItem = item;
                _isSyncingSelection = false;
                DisplayPreview(item.Entry);
            }
        }

        private void BtnCopyCode_Click(object sender, RoutedEventArgs e)
        {
            string code = TxtTikzCodePreview.Text;
            if (string.IsNullOrWhiteSpace(code))
            {
                MessageBox.Show("Chưa có mã TikZ để sao chép.", "Thông báo", MessageBoxButton.OK, MessageBoxImage.Information);
                return;
            }

            SafeClipboard.SetText(code);
            MessageBox.Show("Đã sao chép mã TikZ vào Clipboard.", "Đã sao chép", MessageBoxButton.OK, MessageBoxImage.Information);
        }

        private void BtnDeleteFigure_Click(object sender, RoutedEventArgs e)
        {
            if (_selectedEntry == null) return;

            var confirm = MessageBox.Show(
                $"Bạn có chắc chắn muốn xóa hình '[{_selectedEntry.Id}] {_selectedEntry.Title}' khỏi kho?\nTệp mã nguồn và ảnh render tương ứng sẽ bị xóa vĩnh viễn.",
                "Xác nhận xóa hình",
                MessageBoxButton.YesNo,
                MessageBoxImage.Question);

            if (confirm == MessageBoxResult.Yes)
            {
                bool deleted = FigureBankService.DeleteFigure(_selectedEntry.Id);
                if (deleted)
                {
                    RefreshFigureList();
                }
            }
        }

        private void BtnOpenFolder_Click(object sender, RoutedEventArgs e)
        {
            try
            {
                string dir = FigureBankService.GetFiguresDirectory();
                Process.Start(new ProcessStartInfo
                {
                    FileName = dir,
                    UseShellExecute = true
                });
            }
            catch (Exception ex)
            {
                MessageBox.Show($"Không thể mở thư mục: {ex.Message}", "Lỗi", MessageBoxButton.OK, MessageBoxImage.Error);
            }
        }

        private void BtnPopoutPreview_Click(object sender, RoutedEventArgs e)
        {
            if (ImgPreview.Source != null)
            {
                string bankDir = FigureBankService.GetFiguresDirectory();
                string? pngPath = _selectedEntry?.GetPngPath(bankDir);

                var viewer = new TikzImagePreviewWindow(ImgPreview.Source, pngPath, 600, _selectedEntry?.Title ?? "Xem hình từ kho")
                {
                    Owner = this
                };
                viewer.ShowDialog();
            }
            else
            {
                MessageBox.Show("Hình này chưa có ảnh render để phóng to.", "Chưa có ảnh", MessageBoxButton.OK, MessageBoxImage.Information);
            }
        }

        private void ImgPreview_MouseLeftButtonDown(object sender, MouseButtonEventArgs e)
        {
            if (e.ClickCount == 2)
            {
                BtnPopoutPreview_Click(sender, e);
            }
        }

        private void BtnClose_Click(object sender, RoutedEventArgs e)
        {
            DialogResult = false;
            Close();
        }

        private void FigureBankDialog_KeyDown(object sender, KeyEventArgs e)
        {
            if (e.Key == Key.Escape)
            {
                DialogResult = false;
                Close();
            }
            else if (e.Key == Key.Enter && !TxtSearchQuery.IsFocused)
            {
                BtnLoadFigure_Click(sender, e);
            }
            else if (e.Key == Key.F11)
            {
                WindowState = WindowState == WindowState.Maximized ? WindowState.Normal : WindowState.Maximized;
            }
        }
    }
}
