using System;
using System.Collections.Generic;
using System.Linq;
using System.Windows;
using System.Windows.Input;

namespace MatrixExamAI.Desktop.Views
{
    public partial class SaveFigureDialog : Window
    {
        public string ResultTitle { get; private set; } = string.Empty;
        public string ResultDescription { get; private set; } = string.Empty;
        public List<string> ResultTags { get; private set; } = new();
        public bool ResultSavePng { get; private set; } = true;

        public SaveFigureDialog(string defaultTitle = "", string defaultTags = "", bool hasImage = true)
        {
            InitializeComponent();
            TxtTitle.Text = defaultTitle;
            TxtTags.Text = defaultTags;
            ChkSavePng.IsChecked = hasImage;
            ChkSavePng.IsEnabled = hasImage;
            if (!hasImage)
            {
                ChkSavePng.Content = "Lưu kèm ảnh PNG (Chưa có ảnh biên dịch sẵn, chỉ lưu mã .tex)";
            }
            Loaded += (s, e) => TxtTitle.Focus();
        }

        private void BtnSave_Click(object sender, RoutedEventArgs e)
        {
            string title = TxtTitle.Text.Trim();
            if (string.IsNullOrWhiteSpace(title))
            {
                MessageBox.Show("Vui lòng nhập tên cho hình vẽ.", "Thiếu thông tin", MessageBoxButton.OK, MessageBoxImage.Warning);
                TxtTitle.Focus();
                return;
            }

            ResultTitle = title;
            ResultDescription = TxtDescription.Text.Trim();
            ResultTags = TxtTags.Text
                .Split(new[] { ',', ';' }, StringSplitOptions.RemoveEmptyEntries)
                .Select(t => t.Trim())
                .Where(t => !string.IsNullOrEmpty(t))
                .ToList();
            ResultSavePng = ChkSavePng.IsChecked == true;

            DialogResult = true;
            Close();
        }

        private void BtnCancel_Click(object sender, RoutedEventArgs e)
        {
            DialogResult = false;
            Close();
        }

        private void SaveFigureDialog_KeyDown(object sender, KeyEventArgs e)
        {
            if (e.Key == Key.Escape)
            {
                DialogResult = false;
                Close();
            }
            else if (e.Key == Key.Enter && (Keyboard.Modifiers & ModifierKeys.Control) == ModifierKeys.Control)
            {
                BtnSave_Click(sender, e);
            }
            else if (e.Key == Key.Enter && !TxtDescription.IsFocused)
            {
                BtnSave_Click(sender, e);
            }
        }
    }
}
