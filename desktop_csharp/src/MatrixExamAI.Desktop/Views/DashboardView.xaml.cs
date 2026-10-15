using System;
using System.Diagnostics;
using System.IO;
using System.Windows;
using System.Windows.Controls;

namespace MatrixExamAI.Desktop.Views
{
    public partial class DashboardView : UserControl
    {
        public event EventHandler? RequestNavigateToConvert;
        public event EventHandler? RequestNavigateToTikz;

        public DashboardView()
        {
            InitializeComponent();
        }

        private void BtnQuickConvert_Click(object sender, RoutedEventArgs e)
        {
            RequestNavigateToConvert?.Invoke(this, EventArgs.Empty);
        }

        private void BtnTikz_Click(object sender, RoutedEventArgs e)
        {
            RequestNavigateToTikz?.Invoke(this, EventArgs.Empty);
        }

        private void BtnOpenFolder_Click(object sender, RoutedEventArgs e)
        {
            try
            {
                string dir = Services.StorageLocationService.GetDefaultExportDirectory();
                Services.StorageLocationService.OpenFolderInExplorer(dir);
            }
            catch (Exception ex)
            {
                MessageBox.Show($"Không thể mở thư mục: {ex.Message}", "Lỗi", MessageBoxButton.OK, MessageBoxImage.Error);
            }
        }
    }
}
