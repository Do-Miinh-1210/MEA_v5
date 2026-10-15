using System;
using System.Threading.Tasks;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Media;
using System.Windows.Media.Imaging;
using Wpf.Ui.Controls;
using MatrixExamAI.Desktop.Services;

namespace MatrixExamAI.Desktop.Views;

public partial class ActivationDialog : FluentWindow
{
    private readonly SupabaseLicenseService _licenseService;
    private readonly string _machineId;
    public string MachineIdText => TxtMachineId.Text;

    public ActivationDialog()
    {
        InitializeComponent();

        _licenseService = SupabaseLicenseService.Instance;
        _machineId = HardwareInfoService.GetMachineId();

        TxtMachineId.Text = _machineId;
        TxtHardwareDisplay.Text = HardwareInfoService.GetMachineDisplay();

        Loaded += ActivationDialog_Loaded;
    }

    private void ActivationDialog_Loaded(object sender, RoutedEventArgs e)
    {
        UpdateLicenseDisplay(_licenseService.GetCurrentLicense());
        UpdateVietQrImage();
    }

    private void UpdateLicenseDisplay(LicenseInfo info)
    {
        TxtBadgeStatus.Text = info.BadgeText;

        try
        {
            var brush = new SolidColorBrush((Color)ColorConverter.ConvertFromString(info.BadgeColor));
            BadgeLicenseStatus.Background = new SolidColorBrush(Color.FromArgb(30, brush.Color.R, brush.Color.G, brush.Color.B));
            TxtBadgeStatus.Foreground = brush;
        }
        catch
        {
            BadgeLicenseStatus.Background = new SolidColorBrush(Color.FromArgb(30, 16, 185, 129));
            TxtBadgeStatus.Foreground = new SolidColorBrush(Color.FromRgb(16, 185, 129));
        }

        string source = info.Offline ? "Cục bộ (Độc lập)" : (info.FromCache ? "Bộ nhớ đệm (Cache)" : "Supabase Cloud Trực tiếp");
        TxtLicenseDetail.Text = $"Chủ sở hữu: {info.Name} • Hạn dùng: {info.Expiry} • Nguồn: {source}";
    }

    private void UpdateVietQrImage()
    {
        try
        {
            if (CmbPricingPackage.SelectedItem is ComboBoxItem item && item.Tag is string tag)
            {
                var parts = tag.Split('|');
                string pkg = parts.Length > 0 ? parts[0] : "pro";
                string dur = parts.Length > 1 ? parts[1] : "6";
                string amt = parts.Length > 2 ? parts[2] : "1099000";

                string pkgCode = $"{pkg.ToUpperInvariant()}-{dur}T";
                string qrUrl = SupabaseLicenseService.GetVietQrUrl(_machineId, pkgCode, amt);

                var bitmap = new BitmapImage();
                bitmap.BeginInit();
                bitmap.UriSource = new Uri(qrUrl, UriKind.Absolute);
                bitmap.CacheOption = BitmapCacheOption.OnLoad;
                bitmap.EndInit();

                ImgVietQr.Source = bitmap;
            }
        }
        catch (Exception ex)
        {
            System.Diagnostics.Debug.WriteLine($"[ActivationDialog] QR load error: {ex.Message}");
        }
    }

    private void BtnCopyMid_Click(object sender, RoutedEventArgs e)
    {
        try
        {
            SafeClipboard.SetText(_machineId);
            ShowNotification(InfoBarSeverity.Success, "Đã sao chép", $"Đã sao chép Mã máy ({_machineId}) vào bộ nhớ đệm. Hãy gửi mã này cho Admin để kích hoạt.");
        }
        catch
        {
            Clipboard.SetText(_machineId);
            ShowNotification(InfoBarSeverity.Success, "Đã sao chép", $"Đã sao chép Mã máy ({_machineId}).");
        }
    }

    private async void BtnRefreshStatus_Click(object sender, RoutedEventArgs e)
    {
        BtnRefreshStatus.IsEnabled = false;
        ShowNotification(InfoBarSeverity.Informational, "Đang kiểm tra...", "Đang kết nối tới Supabase Cloud để đối soát bản quyền...");

        try
        {
            var result = await _licenseService.CheckLicenseAsync(forceOnline: true);
            UpdateLicenseDisplay(result);

            if (result.IsActive)
            {
                ShowNotification(InfoBarSeverity.Success, "Bản quyền Hợp lệ", $"Thiết bị của bạn đã được kích hoạt thành công gói {result.DisplayTier}!");
            }
            else
            {
                ShowNotification(InfoBarSeverity.Warning, "Chưa kích hoạt", "Máy tính này chưa được cấp phép kích hoạt trên Supabase Cloud. Hãy đăng ký hoặc nhập mã bản quyền.");
            }
        }
        catch (Exception ex)
        {
            ShowNotification(InfoBarSeverity.Error, "Lỗi kết nối", ex.Message);
        }
        finally
        {
            BtnRefreshStatus.IsEnabled = true;
        }
    }

    private async void BtnActivateOnline_Click(object sender, RoutedEventArgs e)
    {
        string key = TxtLicenseKey.Text.Trim();
        string owner = TxtOwnerName.Text.Trim();

        if (string.IsNullOrEmpty(key))
        {
            ShowNotification(InfoBarSeverity.Warning, "Thiếu thông tin", "Vui lòng nhập Mã bản quyền (License Key) được cấp để kích hoạt.");
            return;
        }

        BtnActivateOnline.IsEnabled = false;
        ShowNotification(InfoBarSeverity.Informational, "Đang kích hoạt...", "Đang gửi yêu cầu kích hoạt bản quyền lên Supabase Cloud...");

        try
        {
            var res = await _licenseService.ActivateWithKeyAsync(key, owner);
            UpdateLicenseDisplay(res);

            if (res.Ok && res.IsActive)
            {
                ShowNotification(InfoBarSeverity.Success, "Kích hoạt Thành công", res.Message);
            }
            else
            {
                ShowNotification(InfoBarSeverity.Error, "Kích hoạt thất bại", res.Message);
            }
        }
        catch (Exception ex)
        {
            ShowNotification(InfoBarSeverity.Error, "Lỗi kích hoạt", ex.Message);
        }
        finally
        {
            BtnActivateOnline.IsEnabled = true;
        }
    }

    private void CmbPricingPackage_SelectionChanged(object sender, SelectionChangedEventArgs e)
    {
        if (IsLoaded)
        {
            UpdateVietQrImage();
        }
    }

    private void ShowNotification(InfoBarSeverity severity, string title, string message)
    {
        InfoActivation.Severity = severity;
        InfoActivation.Title = title;
        InfoActivation.Message = message;
        InfoActivation.IsOpen = true;
    }

    private void BtnClose_Click(object sender, RoutedEventArgs e)
    {
        Close();
    }
}
