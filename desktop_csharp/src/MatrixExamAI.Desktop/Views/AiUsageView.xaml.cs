using System;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Windows;
using System.Windows.Controls;
using MatrixExamAI.Desktop.Services;

namespace MatrixExamAI.Desktop.Views
{
    public partial class AiUsageView : UserControl
    {
        public AiUsageView()
        {
            InitializeComponent();
            Loaded += (s, e) => RefreshData();
        }

        private string GetCurrentRange()
        {
            if (Rad7Days?.IsChecked == true) return "7";
            if (Rad30Days?.IsChecked == true) return "30";
            if (RadAll?.IsChecked == true) return "all";
            return "today";
        }

        public void RefreshData()
        {
            try
            {
                string range = GetCurrentRange();
                var stats = AiUsageService.Instance.GetStats(range);

                TxtKpiTotalRequests.Text = stats.TotalRequests.ToString("N0");
                TxtKpiSuccessRate.Text = $"{stats.SuccessRate:0.0}%";
                TxtKpiTotalChars.Text = stats.TotalChars >= 1000000 
                    ? $"{(stats.TotalChars / 1000000.0):0.0}M" 
                    : (stats.TotalChars >= 1000 ? $"{(stats.TotalChars / 1000.0):0.0}K" : stats.TotalChars.ToString("N0"));

                TxtKpiAvgDuration.Text = stats.TotalRequests > 0 
                    ? (stats.AvgDurationMs >= 1000 ? $"{(stats.AvgDurationMs / 1000.0):0.1}s" : $"{stats.AvgDurationMs}ms")
                    : "—";

                if (stats.ProviderBreakdown.Count > 0)
                {
                    TxtProviderBreakdown.Text = string.Join("\n", stats.ProviderBreakdown.Select(kv => $"• {kv.Key}: {kv.Value} request"));
                }
                else
                {
                    TxtProviderBreakdown.Text = "(Chưa có request nào)";
                }

                TxtQuotaWarning.Text = stats.QuotaWarning;

                DataGridRecentRequests.ItemsSource = stats.RecentEntries;
            }
            catch (Exception ex)
            {
                Debug.WriteLine($"[AiUsageView] Error refreshing: {ex.Message}");
            }
        }

        private void BtnRefresh_Click(object sender, RoutedEventArgs e)
        {
            RefreshData();
        }

        private void Filter_Checked(object sender, RoutedEventArgs e)
        {
            RefreshData();
        }

        private void BtnOpenLogDir_Click(object sender, RoutedEventArgs e)
        {
            try
            {
                var dir = AiUsageService.Instance.GetLogDirectory();
                if (Directory.Exists(dir))
                {
                    Process.Start(new ProcessStartInfo
                    {
                        FileName = dir,
                        UseShellExecute = true
                    });
                }
            }
            catch (Exception ex)
            {
                MessageBox.Show($"Không thể mở thư mục log: {ex.Message}", "Lỗi", MessageBoxButton.OK, MessageBoxImage.Error);
            }
        }

        private void BtnClearLog_Click(object sender, RoutedEventArgs e)
        {
            var res = MessageBox.Show(
                "Bạn có chắc chắn muốn xóa toàn bộ lịch sử log sử dụng AI không?\nThao tác này không thể hoàn tác.",
                "Xác nhận xóa log",
                MessageBoxButton.YesNo,
                MessageBoxImage.Warning);

            if (res == MessageBoxResult.Yes)
            {
                AiUsageService.Instance.ClearLog();
                RefreshData();
            }
        }
    }
}
