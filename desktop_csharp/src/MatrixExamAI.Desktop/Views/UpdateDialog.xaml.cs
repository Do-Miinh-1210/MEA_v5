using System;
using System.Threading;
using System.Windows;
using Wpf.Ui.Controls;
using MatrixExamAI.Desktop.Services;

namespace MatrixExamAI.Desktop.Views;

public partial class UpdateDialog : FluentWindow
{
    private readonly UpdateInfo _updateInfo;
    private CancellationTokenSource? _cts;

    // ponytail: Single-window update workflow; upgrade to background background-download notification if non-blocking UX needed.
    public UpdateDialog(UpdateInfo updateInfo)
    {
        InitializeComponent();
        _updateInfo = updateInfo;

        TxtVersionTitle.Text = $"Đã có phiên bản mới: {_updateInfo.TagName}";
        double mb = _updateInfo.FileSize > 0 ? _updateInfo.FileSize / (1024.0 * 1024.0) : 0;
        string sizeText = mb > 0 ? $"{mb:F1} MB" : "Tự động";
        TxtVersionSubtitle.Text = $"Phiên bản hiện tại: v{GitHubUpdateService.Instance.CurrentVersion} • Dung lượng: {sizeText}";

        TxtReleaseNotes.Text = string.IsNullOrWhiteSpace(_updateInfo.ReleaseNotes)
            ? "Bản cập nhật nâng cấp các tính năng mới, cải tiến tốc độ và sửa lỗi hệ thống."
            : _updateInfo.ReleaseNotes;
    }

    private async void BtnUpdateNow_Click(object sender, RoutedEventArgs e)
    {
        BtnUpdateNow.IsEnabled = false;
        BtnCancel.IsEnabled = false;
        PanelProgress.Visibility = Visibility.Visible;
        TxtStatus.Text = "Đang kết nối GitHub CDN...";

        _cts = new CancellationTokenSource();
        var progress = new Progress<UpdateProgressInfo>(p =>
        {
            ProgressBarDownload.Value = p.Percentage;
            double curMb = p.BytesReceived / (1024.0 * 1024.0);
            double totMb = p.TotalBytesToReceive / (1024.0 * 1024.0);
            TxtProgressStatus.Text = $"Đang tải: {curMb:F1} MB / {totMb:F1} MB ({p.Percentage:F0}%)";
        });

        try
        {
            string installerPath = await GitHubUpdateService.Instance.DownloadUpdateAsync(
                _updateInfo.DownloadUrl,
                progress,
                _cts.Token
            );

            TxtProgressStatus.Text = "Tải thành công! Đang kích hoạt bộ cài...";
            TxtStatus.Text = "Đang khởi động trình cài đặt...";

            await System.Threading.Tasks.Task.Delay(500);

            GitHubUpdateService.Instance.ApplyAndExit(installerPath, verySilent: false);
        }
        catch (Exception ex)
        {
            PanelProgress.Visibility = Visibility.Collapsed;
            BtnUpdateNow.IsEnabled = true;
            BtnCancel.IsEnabled = true;
            TxtStatus.Text = "Tải thất bại!";
            System.Windows.MessageBox.Show(
                $"Không thể tải gói cập nhật:\n{ex.Message}\n\nBạn có thể thử lại sau hoặc tải trực tiếp từ GitHub Releases.",
                "Lỗi cập nhật",
                System.Windows.MessageBoxButton.OK,
                MessageBoxImage.Warning
            );
        }
    }

    private void BtnCancel_Click(object sender, RoutedEventArgs e)
    {
        _cts?.Cancel();
        Close();
    }
}
