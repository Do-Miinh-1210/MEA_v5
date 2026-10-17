using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Input;
using System.Text;
using MatrixExamAI.Desktop.Services;

namespace MatrixExamAI.Desktop.Views
{
    public partial class HtmlModelBankDialog : Window
    {
        private List<HtmlModelEntry> _allEntries = new();
        private HtmlModelEntry? _selectedEntry = null;

        public string? SelectedHtmlCode { get; private set; }

        public HtmlModelBankDialog()
        {
            InitializeComponent();
            Loaded += HtmlModelBankDialog_Loaded;
        }

        private void HtmlModelBankDialog_Loaded(object sender, RoutedEventArgs e)
        {
            ReloadData();
        }

        public void ReloadData()
        {
            _allEntries = HtmlModelBankService.LoadAllEntries();
            TxtTotalCount.Text = $"{_allEntries.Count} mô hình";
            ApplyFilter();
        }

        private void ApplyFilter()
        {
            string query = TxtSearchQuery.Text?.Trim().ToLowerInvariant() ?? string.Empty;
            string categoryTag = (CmbCategoryFilter.SelectedItem as ComboBoxItem)?.Tag?.ToString() ?? "all";
            string sourceTag = (CmbSourceFilter.SelectedItem as ComboBoxItem)?.Tag?.ToString() ?? "all";

            var filtered = _allEntries.Where(item =>
            {
                // 1. Lọc theo nguồn
                if (sourceTag == "template" && !item.IsTemplate) return false;
                if (sourceTag == "user" && item.IsTemplate) return false;

                // 2. Lọc theo chuyên đề
                if (categoryTag != "all")
                {
                    if (categoryTag == "user" && item.IsTemplate) return false;
                    if (categoryTag == "tron_xoay" && !item.Category.Contains("Khối tròn xoay")) return false;
                    if (categoryTag == "khong_gian" && !item.Category.Contains("Hình không gian")) return false;
                    if (categoryTag == "oxyz" && !item.Category.Contains("Oxyz")) return false;
                    if (categoryTag == "mat_cong" && !item.Category.Contains("Mặt cong") && !item.Category.Contains("Đồ thị")) return false;
                    if (categoryTag == "vat_ly" && !item.Category.Contains("Vật lý")) return false;
                    if (categoryTag == "hoa_hoc" && !item.Category.Contains("Hóa học")) return false;
                    if (categoryTag == "sinh_hoc" && !item.Category.Contains("Sinh học")) return false;
                }

                // 3. Lọc theo từ khóa tìm kiếm
                if (!string.IsNullOrEmpty(query))
                {
                    bool matchTitle = item.Title.ToLowerInvariant().Contains(query);
                    bool matchCat = item.Category.ToLowerInvariant().Contains(query);
                    bool matchDesc = item.Description.ToLowerInvariant().Contains(query);
                    bool matchTags = item.Tags.Any(t => t.ToLowerInvariant().Contains(query));
                    if (!matchTitle && !matchCat && !matchDesc && !matchTags) return false;
                }

                return true;
            }).ToList();

            ListModels.ItemsSource = filtered;

            if (filtered.Count > 0)
            {
                ListModels.SelectedIndex = 0;
            }
            else
            {
                ClearDetail();
            }
        }

        private void ListModels_SelectionChanged(object sender, SelectionChangedEventArgs e)
        {
            _selectedEntry = ListModels.SelectedItem as HtmlModelEntry;
            if (_selectedEntry == null)
            {
                ClearDetail();
                return;
            }

            TxtDetailTitle.Text = _selectedEntry.Title;
            TxtDetailCategory.Text = $"Chuyên đề: {_selectedEntry.Category}";
            TxtDetailDescription.Text = string.IsNullOrWhiteSpace(_selectedEntry.Description)
                ? "Không có mô tả kỹ thuật."
                : _selectedEntry.Description;

            string code = HtmlModelBankService.GetHtmlCode(_selectedEntry);
            TxtCodePreview.Text = code;

            BtnDeleteModel.Visibility = _selectedEntry.IsTemplate ? Visibility.Collapsed : Visibility.Visible;
            TxtDetailStatus.Text = $"Đã chọn '{_selectedEntry.Title}' • Dung lượng mã: {code.Length:N0} ký tự.";
        }

        private void ClearDetail()
        {
            _selectedEntry = null;
            TxtDetailTitle.Text = "Không tìm thấy mô hình phù hợp";
            TxtDetailCategory.Text = "Chuyên đề: —";
            TxtDetailDescription.Text = "Vui lòng thay đổi từ khóa tìm kiếm hoặc bộ lọc chuyên đề.";
            TxtCodePreview.Text = string.Empty;
            BtnDeleteModel.Visibility = Visibility.Collapsed;
            TxtDetailStatus.Text = "Không có mô hình nào được chọn.";
        }

        private void TxtSearchQuery_TextChanged(object sender, TextChangedEventArgs e)
        {
            ApplyFilter();
        }

        private void CmbCategoryFilter_SelectionChanged(object sender, SelectionChangedEventArgs e)
        {
            if (IsLoaded) ApplyFilter();
        }

        private void CmbSourceFilter_SelectionChanged(object sender, SelectionChangedEventArgs e)
        {
            if (IsLoaded) ApplyFilter();
        }

        private void BtnApplyModel_Click(object sender, RoutedEventArgs e)
        {
            if (_selectedEntry == null) return;

            string code = HtmlModelBankService.GetHtmlCode(_selectedEntry);
            if (string.IsNullOrWhiteSpace(code))
            {
                MessageBox.Show("Mô hình này không có mã nguồn HTML hợp lệ.", "Thông báo", MessageBoxButton.OK, MessageBoxImage.Warning);
                return;
            }

            SelectedHtmlCode = code;
            DialogResult = true;
            Close();
        }

        private void BtnOpenInBrowser_Click(object sender, RoutedEventArgs e)
        {
            if (_selectedEntry == null) return;
            string code = HtmlModelBankService.GetHtmlCode(_selectedEntry);
            if (string.IsNullOrWhiteSpace(code)) return;

            try
            {
                string tempDir = Path.Combine(Path.GetTempPath(), "MatrixExamAI_HtmlModel");
                Directory.CreateDirectory(tempDir);
                string previewFile = Path.Combine(tempDir, "preview.html");
                File.WriteAllText(previewFile, code, Encoding.UTF8);

                Process.Start(new ProcessStartInfo(previewFile) { UseShellExecute = true });
            }
            catch (Exception ex)
            {
                MessageBox.Show($"Không thể mở trình duyệt: {ex.Message}", "Lỗi", MessageBoxButton.OK, MessageBoxImage.Error);
            }
        }

        private void BtnCopyHtml_Click(object sender, RoutedEventArgs e)
        {
            if (_selectedEntry == null) return;
            string code = HtmlModelBankService.GetHtmlCode(_selectedEntry);
            if (!string.IsNullOrWhiteSpace(code))
            {
                Clipboard.SetText(code);
                TxtDetailStatus.Text = "✓ Đã sao chép toàn bộ mã nguồn HTML vào Clipboard!";
            }
        }

        private void BtnDeleteModel_Click(object sender, RoutedEventArgs e)
        {
            if (_selectedEntry == null || _selectedEntry.IsTemplate) return;

            var confirm = MessageBox.Show(
                $"Bạn có chắc chắn muốn xóa mô hình '{_selectedEntry.Title}' khỏi kho lưu trữ không?",
                "Xác nhận xóa",
                MessageBoxButton.YesNo,
                MessageBoxImage.Question);

            if (confirm == MessageBoxResult.Yes)
            {
                HtmlModelBankService.DeleteUserEntry(_selectedEntry.Id);
                ReloadData();
            }
        }

        private void BtnOpenFolder_Click(object sender, RoutedEventArgs e)
        {
            try
            {
                string dir = HtmlModelBankService.GetBankDirectory();
                Process.Start(new ProcessStartInfo("explorer.exe", dir) { UseShellExecute = true });
            }
            catch (Exception ex)
            {
                MessageBox.Show($"Không thể mở thư mục: {ex.Message}", "Lỗi", MessageBoxButton.OK, MessageBoxImage.Error);
            }
        }

        private void HtmlModelBankDialog_KeyDown(object sender, KeyEventArgs e)
        {
            if (e.Key == Key.Escape)
            {
                DialogResult = false;
                Close();
            }
            else if (e.Key == Key.Enter && Keyboard.Modifiers == ModifierKeys.None && !TxtSearchQuery.IsFocused)
            {
                BtnApplyModel_Click(sender, e);
            }
        }
    }
}
