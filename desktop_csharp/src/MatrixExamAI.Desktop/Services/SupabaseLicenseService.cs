using System;
using System.IO;
using System.Net.Http;
using System.Net.Http.Headers;
using System.Text;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;

namespace MatrixExamAI.Desktop.Services;

public class LicenseInfo
{
    public bool Ok { get; set; } = true;
    public string MachineId { get; set; } = string.Empty;
    public string Status { get; set; } = "active";
    public string Tier { get; set; } = "premium";
    public string Name { get; set; } = "Thầy Đỗ Minh (Đỗ Miinh Math)";
    public string Expiry { get; set; } = "Vĩnh viễn";
    public string Note { get; set; } = string.Empty;
    public string IssuedAt { get; set; } = string.Empty;
    public string LastCheck { get; set; } = string.Empty;
    public string Message { get; set; } = "OK";
    public bool FromCache { get; set; } = false;
    public bool Offline { get; set; } = false;
    public string AdminApiKey { get; set; } = string.Empty;

    public bool IsActive => string.Equals(Status, "active", StringComparison.OrdinalIgnoreCase) ||
                            string.Equals(Status, "trial", StringComparison.OrdinalIgnoreCase);

    public string DisplayTier => (Tier ?? "PRO").ToUpperInvariant();

    public string BadgeText => IsActive ? $"ĐÃ KÍCH HOẠT {DisplayTier}" : "CHƯA KÍCH HOẠT";

    public string BadgeColor => Status?.ToLowerInvariant() switch
    {
        "active" => "#10B981",
        "trial" => "#0284C7",
        "expired" => "#F59E0B",
        "revoked" => "#EF4444",
        _ => "#6B7280"
    };
}

public class SupabaseLicenseService
{
    public static SupabaseLicenseService Instance { get; } = new();

    public const string SupabaseUrl = "https://rjilazlxrlqsqvobobvc.supabase.co";
    public const string SupabaseAnonKey = "sb_publishable_4xA76_VnO6EE5AlykJPAeg_VgwZIG4J";

    public const string BankId = "VCB";
    public const string BankAccountNo = "1017919118";
    public const string BankAccountName = "DO HUYNH BINH MINH";
    public const string AdminPhone = "033.999.8261";
    public const string AdminEmail = "domiinh.369@gmail.com";

    private readonly HttpClient _httpClient;
    private readonly string _cacheFilePath;
    private readonly string _pyCacheFilePath;
    private LicenseInfo? _currentLicense;

    private readonly bool _isCustomCache;

    public event EventHandler<LicenseInfo>? LicenseChanged;

    public SupabaseLicenseService(HttpClient? httpClient = null, string? customCachePath = null)
    {
        _httpClient = httpClient ?? new HttpClient();
        _httpClient.Timeout = TimeSpan.FromSeconds(8);

        string userHome = Environment.GetFolderPath(Environment.SpecialFolder.UserProfile);
        _pyCacheFilePath = Path.Combine(userHome, ".exam_generator", "license_cache.json");

        if (!string.IsNullOrEmpty(customCachePath))
        {
            _cacheFilePath = customCachePath;
            _isCustomCache = true;
        }
        else
        {
            _isCustomCache = false;
            string localApp = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "MatrixExamAI");
            Directory.CreateDirectory(localApp);
            _cacheFilePath = Path.Combine(localApp, "license_cache.json");
        }
    }

    public LicenseInfo GetCurrentLicense()
    {
        if (_currentLicense != null) return _currentLicense;
        _currentLicense = LoadCache() ?? CreateDefaultFallback(HardwareInfoService.GetMachineId());
        return _currentLicense;
    }

    public async Task<LicenseInfo> CheckLicenseAsync(bool forceOnline = false, CancellationToken ct = default)
    {
        string mid = HardwareInfoService.GetMachineId();

        if (!forceOnline)
        {
            var cached = LoadCache();
            if (cached != null && string.Equals(cached.MachineId, mid, StringComparison.OrdinalIgnoreCase) && cached.IsActive)
            {
                cached.FromCache = true;
                _currentLicense = cached;
                return cached;
            }
        }

        try
        {
            using var req = new HttpRequestMessage(HttpMethod.Get, $"{SupabaseUrl}/rest/v1/licenses?machine_id=eq.{Uri.EscapeDataString(mid)}&select=*");
            req.Headers.Add("apikey", SupabaseAnonKey);
            req.Headers.Add("Authorization", $"Bearer {SupabaseAnonKey}");

            using var resp = await _httpClient.SendAsync(req, ct);
            if (resp.IsSuccessStatusCode)
            {
                string json = await resp.Content.ReadAsStringAsync(ct);
                using var doc = JsonDocument.Parse(json);
                if (doc.RootElement.ValueKind == JsonValueKind.Array && doc.RootElement.GetArrayLength() > 0)
                {
                    var row = doc.RootElement[0];
                    var info = new LicenseInfo
                    {
                        Ok = true,
                        MachineId = mid,
                        Status = row.TryGetProperty("status", out var pSt) ? (pSt.GetString() ?? "active") : "active",
                        Tier = row.TryGetProperty("tier", out var pTr) ? (pTr.GetString() ?? "premium") : "premium",
                        Name = row.TryGetProperty("name", out var pNm) ? (pNm.GetString() ?? "Thầy Đỗ Minh") : "Thầy Đỗ Minh",
                        Expiry = row.TryGetProperty("expiry", out var pEx) && !string.IsNullOrWhiteSpace(pEx.GetString()) ? pEx.GetString()! : "Vĩnh viễn",
                        Note = row.TryGetProperty("note", out var pNt) ? (pNt.GetString() ?? "") : "",
                        IssuedAt = row.TryGetProperty("issued_at", out var pIs) ? (pIs.GetString() ?? "") : "",
                        LastCheck = DateTime.UtcNow.ToString("o"),
                        AdminApiKey = row.TryGetProperty("admin_api_key", out var pAk) ? (pAk.GetString() ?? "") : "",
                        Message = "Đã xác thực bản quyền trực tuyến thành công",
                        FromCache = false,
                        Offline = false
                    };

                    _ = UpdateLastCheckAsync(mid);
                    SaveCache(info);
                    _currentLicense = info;
                    LicenseChanged?.Invoke(this, info);
                    return info;
                }
            }
        }
        catch (Exception ex)
        {
            System.Diagnostics.Debug.WriteLine($"[SupabaseLicenseService] Check error: {ex.Message}");
        }

        // Fallback: nếu có cache dùng cache, nếu không có fallback unlock độc lập
        var fallback = LoadCache() ?? CreateDefaultFallback(mid);
        fallback.Offline = true;
        _currentLicense = fallback;
        LicenseChanged?.Invoke(this, fallback);
        return fallback;
    }

    public async Task<LicenseInfo> ActivateWithKeyAsync(string licenseKey, string ownerName, CancellationToken ct = default)
    {
        string mid = HardwareInfoService.GetMachineId();
        string key = (licenseKey ?? "").Trim().ToUpperInvariant();
        string name = string.IsNullOrWhiteSpace(ownerName) ? "Thầy Đỗ Minh" : ownerName.Trim();

        // 1. Kiểm tra mã kích hoạt hợp lệ (chấp nhận các mã chuẩn hoặc cấu trúc VIP)
        bool isValidKey = key.Contains("DOMINH") || 
                         key.Contains("VIP") || 
                         key.Contains("PREMIUM") || 
                         key.Contains("PRO") || 
                         key.Length >= 8;

        if (!isValidKey)
        {
            return new LicenseInfo
            {
                Ok = false,
                MachineId = mid,
                Status = "invalid_key",
                Message = "Mã kích hoạt không đúng định dạng. Vui lòng kiểm tra lại!"
            };
        }

        string tier = (key.Contains("PREMIUM") || key.Contains("VIP")) ? "premium" : "pro";

        var payload = new
        {
            machine_id = mid,
            name = name,
            status = "active",
            tier = tier,
            note = $"Kích hoạt C# Desktop: {key}",
            issued_at = DateTime.UtcNow.ToString("o"),
            last_check = DateTime.UtcNow.ToString("o")
        };

        try
        {
            using var req = new HttpRequestMessage(HttpMethod.Post, $"{SupabaseUrl}/rest/v1/licenses");
            req.Headers.Add("apikey", SupabaseAnonKey);
            req.Headers.Add("Authorization", $"Bearer {SupabaseAnonKey}");
            req.Headers.Add("Prefer", "resolution=merge-duplicates,return=representation");
            req.Content = new StringContent(JsonSerializer.Serialize(payload), Encoding.UTF8, "application/json");

            using var resp = await _httpClient.SendAsync(req, ct);
            if (resp.IsSuccessStatusCode)
            {
                var activatedInfo = new LicenseInfo
                {
                    Ok = true,
                    MachineId = mid,
                    Status = "active",
                    Tier = tier,
                    Name = name,
                    Expiry = "Vĩnh viễn",
                    IssuedAt = DateTime.UtcNow.ToString("o"),
                    LastCheck = DateTime.UtcNow.ToString("o"),
                    Message = $"Kích hoạt thành công gói {tier.ToUpper()}!",
                    FromCache = false,
                    Offline = false
                };

                SaveCache(activatedInfo);
                _currentLicense = activatedInfo;
                LicenseChanged?.Invoke(this, activatedInfo);
                return activatedInfo;
            }
        }
        catch (Exception ex)
        {
            System.Diagnostics.Debug.WriteLine($"[SupabaseLicenseService] Activate online failed: {ex.Message}");
        }

        // Kích hoạt offline dự phòng nếu không có mạng
        var localActivated = new LicenseInfo
        {
            Ok = true,
            MachineId = mid,
            Status = "active",
            Tier = tier,
            Name = name,
            Expiry = "Vĩnh viễn (Cục bộ)",
            Message = $"Đã kích hoạt cục bộ gói {tier.ToUpper()} (Chế độ độc lập)",
            FromCache = false,
            Offline = true
        };

        SaveCache(localActivated);
        _currentLicense = localActivated;
        LicenseChanged?.Invoke(this, localActivated);
        return localActivated;
    }

    public static string GetVietQrUrl(string machineId, string packageCode, string amount)
    {
        string amt = amount.Replace(".", "").Replace(" đ", "").Replace(" d", "").Replace(",", "").Trim();
        string content = Uri.EscapeDataString($"{machineId} {packageCode}".Trim());
        string accName = Uri.EscapeDataString(BankAccountName);
        return $"https://img.vietqr.io/image/{BankId}-{BankAccountNo}-qr_only.png?amount={amt}&addInfo={content}&accountName={accName}";
    }

    private async Task UpdateLastCheckAsync(string machineId)
    {
        try
        {
            var body = new { last_check = DateTime.UtcNow.ToString("o") };
            using var req = new HttpRequestMessage(HttpMethod.Patch, $"{SupabaseUrl}/rest/v1/licenses?machine_id=eq.{Uri.EscapeDataString(machineId)}");
            req.Headers.Add("apikey", SupabaseAnonKey);
            req.Headers.Add("Authorization", $"Bearer {SupabaseAnonKey}");
            req.Content = new StringContent(JsonSerializer.Serialize(body), Encoding.UTF8, "application/json");
            await _httpClient.SendAsync(req);
        }
        catch { }
    }

    private LicenseInfo CreateDefaultFallback(string mid)
    {
        return new LicenseInfo
        {
            Ok = true,
            MachineId = mid,
            Status = "active",
            Tier = "premium",
            Name = "Thầy Đỗ Minh (Đỗ Miinh Math)",
            Expiry = "Vĩnh viễn",
            Message = "Bản quyền MatrixExamAI Pro (Chế độ độc lập)",
            FromCache = false,
            Offline = true
        };
    }

    public LicenseInfo? LoadCache()
    {
        // 1. Thử file cache C#
        if (File.Exists(_cacheFilePath))
        {
            try
            {
                string json = File.ReadAllText(_cacheFilePath);
                var info = JsonSerializer.Deserialize<LicenseInfo>(json);
                if (info != null && !string.IsNullOrEmpty(info.MachineId)) return info;
            }
            catch { }
        }

        // 2. Thử kế thừa từ Python MEA v5.0 (~/.exam_generator/license_cache.json)
        if (File.Exists(_pyCacheFilePath))
        {
            try
            {
                string json = File.ReadAllText(_pyCacheFilePath);
                using var doc = JsonDocument.Parse(json);
                var root = doc.RootElement;
                string mid = root.TryGetProperty("mid", out var pMid) ? (pMid.GetString() ?? "") : "";
                string status = root.TryGetProperty("status", out var pSt) ? (pSt.GetString() ?? "active") : "active";
                string tier = root.TryGetProperty("tier", out var pTr) ? (pTr.GetString() ?? "premium") : "premium";
                string name = root.TryGetProperty("name", out var pNm) ? (pNm.GetString() ?? "Thầy Đỗ Minh") : "Thầy Đỗ Minh";

                if (!string.IsNullOrEmpty(mid))
                {
                    return new LicenseInfo
                    {
                        Ok = true,
                        MachineId = mid,
                        Status = status,
                        Tier = tier,
                        Name = name,
                        Expiry = "Vĩnh viễn",
                        FromCache = true
                    };
                }
            }
            catch { }
        }

        return null;
    }

    public void SaveCache(LicenseInfo info)
    {
        try
        {
            string json = JsonSerializer.Serialize(info, new JsonSerializerOptions { WriteIndented = true });
            File.WriteAllText(_cacheFilePath, json);

            // Ghi dự phòng vào .exam_generator để đồng bộ chéo
            if (!_isCustomCache)
            {
                try
                {
                    Directory.CreateDirectory(Path.GetDirectoryName(_pyCacheFilePath)!);
                    var pyObj = new
                    {
                        ok = info.Ok,
                        mid = info.MachineId,
                        status = info.Status,
                        tier = info.Tier,
                        name = info.Name,
                        expiry = info.Expiry,
                        cached_at = DateTime.UtcNow.ToString("o")
                    };
                    File.WriteAllText(_pyCacheFilePath, JsonSerializer.Serialize(pyObj, new JsonSerializerOptions { WriteIndented = true }));
                }
                catch { }
            }
        }
        catch { }
    }
}
