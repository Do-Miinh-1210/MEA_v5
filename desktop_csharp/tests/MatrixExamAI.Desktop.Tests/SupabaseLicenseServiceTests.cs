using System;
using System.IO;
using System.Net;
using System.Net.Http;
using System.Text.RegularExpressions;
using System.Threading;
using System.Threading.Tasks;
using Xunit;
using MatrixExamAI.Desktop.Services;
using MatrixExamAI.Desktop.Views;

namespace MatrixExamAI.Desktop.Tests;

public class SupabaseLicenseServiceTests
{
    [Fact]
    public void HardwareInfoService_GetMachineId_MatchesExpectedFormat()
    {
        string mid = HardwareInfoService.GetMachineId();
        Assert.False(string.IsNullOrWhiteSpace(mid));
        // Format: XXXX-XXXX-XXXX
        Assert.Matches(@"^[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}$", mid);
    }

    [Fact]
    public void HardwareInfoService_GetMachineId_IsConsistentAcrossCalls()
    {
        string mid1 = HardwareInfoService.GetMachineId();
        string mid2 = HardwareInfoService.GetMachineId();
        Assert.Equal(mid1, mid2);
    }

    [Fact]
    public void HardwareInfoService_GetHardwareUuid_ReturnsNonEmpty()
    {
        string uuid = HardwareInfoService.GetHardwareUuid();
        Assert.False(string.IsNullOrWhiteSpace(uuid));
    }

    [Fact]
    public void SupabaseLicenseService_DefaultFallback_IsActiveAndPremium()
    {
        var service = new SupabaseLicenseService();
        var lic = service.GetCurrentLicense();

        Assert.NotNull(lic);
        Assert.True(lic.IsActive);
        Assert.False(string.IsNullOrWhiteSpace(lic.MachineId));
        Assert.Contains(lic.DisplayTier, new[] { "PRO", "PREMIUM" });
    }

    [Fact]
    public void SupabaseLicenseService_GetVietQrUrl_GeneratesValidUrl()
    {
        string url = SupabaseLicenseService.GetVietQrUrl("6A12-48D4-2666", "PRO-6T", "1.099.000 đ");

        Assert.StartsWith("https://img.vietqr.io/image/VCB-1017919118-qr_only.png", url);
        Assert.Contains("amount=1099000", url);
        Assert.Contains("accountName=DO%20HUYNH%20BINH%20MINH", url);
        Assert.Contains("6A12-48D4-2666", url);
    }

    [Fact]
    public void LicenseInfo_BadgeProperties_ReflectStatusCorrectly()
    {
        var activeLic = new LicenseInfo { Status = "active", Tier = "premium" };
        Assert.True(activeLic.IsActive);
        Assert.Equal("ĐÃ KÍCH HOẠT PREMIUM", activeLic.BadgeText);
        Assert.Equal("#10B981", activeLic.BadgeColor);

        var expiredLic = new LicenseInfo { Status = "expired", Tier = "pro" };
        Assert.False(expiredLic.IsActive);
        Assert.Equal("CHƯA KÍCH HOẠT", expiredLic.BadgeText);
        Assert.Equal("#F59E0B", expiredLic.BadgeColor);
    }

    [Fact]
    public async Task SupabaseLicenseService_ActivateWithKey_RejectsInvalidKey()
    {
        var service = new SupabaseLicenseService();
        var res = await service.ActivateWithKeyAsync("123", "Test User");

        Assert.False(res.Ok);
        Assert.Equal("invalid_key", res.Status);
        Assert.Contains("không đúng định dạng", res.Message);
    }

    [Fact]
    public async Task SupabaseLicenseService_ActivateWithKey_AcceptsValidKeyPattern()
    {
        // Mock handler để không cần gọi internet thực tế trong unit test
        var handler = new MockHttpMessageHandler(@"{""status"":""active"",""tier"":""premium""}", HttpStatusCode.OK);
        using var client = new HttpClient(handler);
        var service = new SupabaseLicenseService(client);

        var res = await service.ActivateWithKeyAsync("MEA-VIP-DOMINH-2026", "Thầy Đỗ Minh");

        Assert.True(res.Ok);
        Assert.True(res.IsActive);
        Assert.Equal("premium", res.Tier.ToLowerInvariant());
    }

    [Fact]
    public void SupabaseLicenseService_CacheSerialization_SavesAndLoadsCorrectly()
    {
        string tempCache = Path.GetTempFileName();
        try
        {
            var service = new SupabaseLicenseService(customCachePath: tempCache);
            var testInfo = new LicenseInfo
            {
                Ok = true,
                MachineId = "TEST-1234-5678",
                Status = "active",
                Tier = "pro",
                Name = "Giáo viên Toán",
                Expiry = "Vĩnh viễn",
                Note = "Unit test cache"
            };

            service.SaveCache(testInfo);
            var loaded = service.LoadCache();

            Assert.NotNull(loaded);
            Assert.Equal(testInfo.MachineId, loaded.MachineId);
            Assert.Equal(testInfo.Name, loaded.Name);
        }
        finally
        {
            if (File.Exists(tempCache)) File.Delete(tempCache);
        }
    }

    [Fact]
    public void ActivationDialog_InstantiationOnSta_Succeeds()
    {
        Exception? threadEx = null;
        var thread = new Thread(() =>
        {
            try
            {
                var dlg = new ActivationDialog();
                Assert.NotNull(dlg);
                Assert.Equal("6A12-48D4-2666".Length, dlg.MachineIdText.Length);
            }
            catch (Exception ex)
            {
                threadEx = ex;
            }
        });

        thread.SetApartmentState(ApartmentState.STA);
        thread.Start();
        thread.Join(5000);

        Assert.Null(threadEx);
    }

    private class MockHttpMessageHandler : HttpMessageHandler
    {
        private readonly string _response;
        private readonly HttpStatusCode _statusCode;

        public MockHttpMessageHandler(string response, HttpStatusCode statusCode)
        {
            _response = response;
            _statusCode = statusCode;
        }

        protected override Task<HttpResponseMessage> SendAsync(HttpRequestMessage request, CancellationToken cancellationToken)
        {
            var res = new HttpResponseMessage(_statusCode)
            {
                Content = new StringContent(_response)
            };
            return Task.FromResult(res);
        }
    }
}
