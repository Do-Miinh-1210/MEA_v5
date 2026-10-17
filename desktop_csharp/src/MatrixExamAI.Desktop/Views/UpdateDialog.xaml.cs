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
        string sizeText;
        if (_updateInfo.IsPatch)
        {
            double kb = _updateInfo.FileSize > 0 ? _updateInfo.FileSize / 1024.0 : 0;
            sizeText = kb > 0 ? $"{kb:F0} KB (Bản vá vi mô Delta-Patch)" : "Bản vá vi mô Delta-Patch";
        }
        else
        {
            sizeText = mb > 0 ? $"{mb:F1} MB (Bộ cài đầy đủ)" : "Tự động";
        }
        TxtVersionSubtitle.Text = $"Phiên bản hiện tại: v{GitHubUpdateService.Instance.CurrentVersion} • {sizeText}";

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
            if (totMb < 1.0)
            {
                double curKb = p.BytesReceived / 1024.0;
                double totKb = p.TotalBytesToReceive / 1024.0;
                TxtProgressStatus.Text = $"Đang tải: {curKb:F0} KB / {totKb:F0} KB ({p.Percentage:F0}%)";
            }
            else
            {
                TxtProgressStatus.Text = $"Đang tải: {curMb:F1} MB / {totMb:F1} MB ({p.Percentage:F0}%)";
            }
        });

        try
        {
            string downloadedPath = await GitHubUpdateService.Instance.DownloadUpdateAsync(
                _updateInfo.DownloadUrl,
                _updateInfo.AssetName,
                progress,
                _cts.Token
            );

            TxtProgressStatus.Text = _updateInfo.IsPatch
                ? "Tải xong bản vá! Đang thay thế mã nguồn..."
                : "Tải thành công! Đang tự động cập nhật ngầm...";
            TxtStatus.Text = "Ứng dụng sẽ tự khởi động lại trong 2 giây...";

            await System.Threading.Tasks.Task.Delay(500);

            GitHubUpdateService.Instance.ApplyAndExit(downloadedPath, verySilent: true, isPatch: _updateInfo.IsPatch);
        }
        catch (Exception ex)
        {
            if (_updateInfo.IsPatch && _updateInfo.AssetName.Contains("delta", StringComparison.OrdinalIgnoreCase))
            {
                try
                {
                    TxtStatus.Text = "Đang chuyển sang tải bản vá đầy đủ...";
                    TxtProgressStatus.Text = "Tải bản vá toàn diện MatrixExamAI_Patch.zip...";
                    ProgressBarDownload.Value = 0;
                    string patchUrl = _updateInfo.DownloadUrl.Replace("MatrixExamAI_Delta.zip", "MatrixExamAI_Patch.zip");
                    string fullPatchPath = await GitHubUpdateService.Instance.DownloadUpdateAsync(
                        patchUrl,
                        "MatrixExamAI_Patch.zip",
                        progress,
                        _cts?.Token ?? CancellationToken.None
                    );
                    TxtStatus.Text = "Ứng dụng sẽ tự khởi động lại trong 2 giây...";
                    await System.Threading.Tasks.Task.Delay(500);
                    GitHubUpdateService.Instance.ApplyAndExit(fullPatchPath, verySilent: true, isPatch: true);
                    return;
                }
                catch (Exception fbEx)
                {
                    ex = fbEx;
                }
            }

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
