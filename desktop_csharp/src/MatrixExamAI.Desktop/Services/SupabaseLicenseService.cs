using System;
using System.IO;
using System.Net.Http;
using System.Net.Http.Headers;
using System.Security.Cryptography;
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
    public string Signature { get; set; } = string.Empty;

    public bool IsActive => string.Equals(Status, "active", StringComparison.OrdinalIgnoreCase) ||
                            string.Equals(Status, "trial", StringComparison.OrdinalIgnoreCase);

    public string DisplayTier => (Tier ?? "PRO").ToUpperInvariant();

    public string BadgeText => IsActive
        ? (string.Equals(Status, "trial", StringComparison.OrdinalIgnoreCase) ? $"DÙNG THỬ {DisplayTier}" : $"ĐÃ KÍCH HOẠT {DisplayTier}")
        : "CHƯA KÍCH HOẠT";

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

    // Ẩn giấu chuỗi nhạy cảm (String Obfuscation via XOR masking) chống công cụ REA / dnSpy / strings
    private static readonly byte[] ObfuscatedUrl = [
        0x32, 0x2E, 0x2E, 0x2A, 0x29, 0x60, 0x75, 0x75, 0x28, 0x30, 0x33, 0x36, 0x3B, 0x20, 0x36, 0x22,
        0x28, 0x36, 0x2B, 0x29, 0x2B, 0x2C, 0x35, 0x38, 0x35, 0x38, 0x2C, 0x39, 0x74, 0x29, 0x2F, 0x2A,
        0x3B, 0x38, 0x3B, 0x29, 0x3F, 0x74, 0x39, 0x35
    ];

    private static readonly byte[] ObfuscatedKey = [
        0x29, 0x38, 0x05, 0x2A, 0x2F, 0x38, 0x36, 0x33, 0x29, 0x32, 0x3B, 0x38, 0x36, 0x3F, 0x05, 0x6E,
        0x22, 0x1B, 0x6D, 0x6C, 0x05, 0x0C, 0x34, 0x15, 0x6C, 0x1F, 0x1F, 0x6F, 0x1B, 0x36, 0x23, 0x31,
        0x10, 0x0A, 0x1B, 0x3F, 0x3D, 0x05, 0x0C, 0x3D, 0x2D, 0x00, 0x13, 0x1D, 0x6E, 0x10
    ];

    private static readonly byte[] ObfuscatedSalt = [
        0x17, 0x1F, 0x1B, 0x05, 0x2C, 0x6F, 0x05, 0x09, 0x1F, 0x19, 0x0F, 0x08, 0x1F, 0x05, 0x09, 0x1B,
        0x16, 0x0E, 0x05, 0x63, 0x1C, 0x62, 0x68, 0x1B, 0x6E, 0x05, 0x1E, 0x15, 0x17, 0x13, 0x14, 0x12,
        0x05, 0x17, 0x1B, 0x0E, 0x12
    ];

    public static string SupabaseUrl => Deobfuscate(ObfuscatedUrl);
    public static string SupabaseAnonKey => Deobfuscate(ObfuscatedKey);
    private static string SecretSalt => Deobfuscate(ObfuscatedSalt);

    private static string Deobfuscate(byte[] data, byte mask = 0x5A)
    {
        var chars = new char[data.Length];
        for (int i = 0; i < data.Length; i++) chars[i] = (char)(data[i] ^ mask);
        return new string(chars);
    }

    public const string BankId = "VCB";
    public const string BankAccountNo = "1017919118";
    public const string BankAccountName = "DO HUYNH BINH MINH";
    public const string AdminPhone = "033.999.8261";
    public const string AdminEmail = "domiinh.369@gmail.com";

    private readonly HttpClient _httpClient;
    private readonly string _cacheFilePath;
    private readonly string _pyCacheFilePath;
    private string _machineId;
    private LicenseInfo? _currentLicense;
    private readonly bool _isCustomCache;

    public event EventHandler<LicenseInfo>? LicenseChanged;

    public SupabaseLicenseService(HttpClient? httpClient = null, string? customCachePath = null, string? customMachineId = null)
    {
        _httpClient = httpClient ?? new HttpClient();
        _httpClient.Timeout = TimeSpan.FromSeconds(8);
        _machineId = !string.IsNullOrWhiteSpace(customMachineId) ? customMachineId : HardwareInfoService.GetMachineId();

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
        _currentLicense = LoadCache() ?? CreateDefaultFallback(_machineId);
        return _currentLicense;
    }

    public async Task<LicenseInfo> CheckLicenseAsync(bool forceOnline = false, CancellationToken ct = default)
    {
        string mid = _machineId;

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
                if (doc.RootElement.ValueKind == JsonValueKind.Array)
                {
                    if (doc.RootElement.GetArrayLength() > 0)
                    {
                        var row = doc.RootElement[0];
                        string status = row.TryGetProperty("status", out var pSt) ? (pSt.GetString() ?? "active") : "active";
                        string tier = row.TryGetProperty("tier", out var pTr) ? (pTr.GetString() ?? "premium") : "premium";
                        string name = row.TryGetProperty("name", out var pNm) ? (pNm.GetString() ?? "Thầy Đỗ Minh") : "Thầy Đỗ Minh";
                        string expiry = row.TryGetProperty("expiry", out var pEx) && !string.IsNullOrWhiteSpace(pEx.GetString()) ? pEx.GetString()! : "Vĩnh viễn";

                        var info = new LicenseInfo
                        {
                            Ok = true,
                            MachineId = mid,
                            Status = status,
                            Tier = tier,
                            Name = name,
                            Expiry = expiry,
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
                    else
                    {
                        var unreg = new LicenseInfo
                        {
                            Ok = false,
                            MachineId = mid,
                            Status = "unregistered",
                            Tier = "trial",
                            Name = "Chưa đăng ký",
                            Expiry = "Chưa kích hoạt",
                            Message = "Thiết bị chưa được đăng ký trên hệ thống. Hãy nhập mã bản quyền để kích hoạt!",
                            FromCache = false,
                            Offline = false
                        };
                        _currentLicense = unreg;
                        LicenseChanged?.Invoke(this, unreg);
                        return unreg;
                    }
                }
            }
        }
        catch (Exception ex)
        {
            System.Diagnostics.Debug.WriteLine($"[SupabaseLicenseService] Check error: {ex.Message}");
        }

        // Fallback khi offline hoặc lỗi mạng: ưu tiên cache đã ký số, nếu không có về chế độ dùng thử
        var fallback = LoadCache() ?? CreateDefaultFallback(mid);
        fallback.Offline = true;
        _currentLicense = fallback;
        LicenseChanged?.Invoke(this, fallback);
        return fallback;
    }

    public async Task<LicenseInfo> ActivateWithKeyAsync(string licenseKey, string ownerName, CancellationToken ct = default)
    {
        string mid = _machineId;
        string key = (licenseKey ?? "").Trim().ToUpperInvariant();
        string name = string.IsNullOrWhiteSpace(ownerName) ? "Thầy Đỗ Minh" : ownerName.Trim();

        // 1. Kiểm tra thuật toán mã bản quyền & Checksum bảo mật
        if (!VerifyLicenseKey(key, out string tier))
        {
            return new LicenseInfo
            {
                Ok = false,
                MachineId = mid,
                Status = "invalid_key",
                Message = "Mã kích hoạt không đúng định dạng hoặc sai mã bảo mật Checksum!"
            };
        }

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

        // Kích hoạt offline dự phòng nếu không có mạng (Chỉ khi key hợp lệ)
        var localActivated = new LicenseInfo
        {
            Ok = true,
            MachineId = mid,
            Status = "active",
            Tier = tier,
            Name = name,
            Expiry = "Vĩnh viễn (Cục bộ)",
            IssuedAt = DateTime.UtcNow.ToString("o"),
            LastCheck = DateTime.UtcNow.ToString("o"),
            Message = $"Đã kích hoạt cục bộ gói {tier.ToUpper()} (Chế độ độc lập)",
            FromCache = false,
            Offline = true
        };

        SaveCache(localActivated);
        _currentLicense = localActivated;
        LicenseChanged?.Invoke(this, localActivated);
        return localActivated;
    }

    public static bool VerifyLicenseKey(string key, out string tier)
    {
        tier = "pro";
        if (string.IsNullOrWhiteSpace(key)) return false;
        key = key.Trim().ToUpperInvariant();

        // 1. Khóa tác giả & Master Key đặc quyền
        if (key.StartsWith("MEA-VIP-DOMINH") || key.Contains("DOMINH-VIP") || key == "MEA-VIP-DOMINH-2026")
        {
            tier = "premium";
            return true;
        }
        if (key.StartsWith("MEA-PRO-DOMINH"))
        {
            tier = "pro";
            return true;
        }

        // 2. Thuật toán Algorithmic Product Key chuẩn: MEA-{TIER}-{SERIAL}-{CHECKSUM}
        var parts = key.Split('-');
        if (parts.Length == 4 && parts[0] == "MEA")
        {
            string reqTier = parts[1];
            string serial = parts[2];
            string checksum = parts[3];

            if ((reqTier is "PRO" or "VIP" or "PREMIUM") && serial.Length >= 4 && checksum.Length == 4)
            {
                string expectedCrc = ComputeKeyChecksum(reqTier, serial);
                if (string.Equals(checksum, expectedCrc, StringComparison.OrdinalIgnoreCase))
                {
                    tier = (reqTier is "VIP" or "PREMIUM") ? "premium" : "pro";
                    return true;
                }
            }
        }

        return false;
    }

    public static string ComputeKeyChecksum(string tier, string serial)
    {
        string input = $"{tier.ToUpperInvariant()}:{serial.ToUpperInvariant()}:{SecretSalt}";
        using var sha = SHA256.Create();
        byte[] hash = sha.ComputeHash(Encoding.UTF8.GetBytes(input));
        return Convert.ToHexString(hash)[..4].ToUpperInvariant();
    }

    public static string GenerateLicenseKey(string tier, string serial)
    {
        string normTier = (tier.Equals("VIP", StringComparison.OrdinalIgnoreCase) || 
                           tier.Equals("PREMIUM", StringComparison.OrdinalIgnoreCase)) ? "VIP" : "PRO";
        string normSerial = serial.Trim().ToUpperInvariant();
        string crc = ComputeKeyChecksum(normTier, normSerial);
        return $"MEA-{normTier}-{normSerial}-{crc}";
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
            Status = "trial",
            Tier = "pro",
            Name = "Bản dùng thử (Trial)",
            Expiry = "Chế độ dùng thử",
            Message = "Bản quyền MatrixExamAI Pro (Chế độ dùng thử)",
            FromCache = false,
            Offline = true
        };
    }

    public static string ComputeSignature(LicenseInfo info, string machineId)
    {
        string payload = $"{machineId}|{info.Status}|{info.Tier}|{info.Expiry}|{info.IssuedAt}|{info.Name}";
        using var hmac = new HMACSHA256(Encoding.UTF8.GetBytes(SecretSalt + machineId));
        byte[] hash = hmac.ComputeHash(Encoding.UTF8.GetBytes(payload));
        return Convert.ToHexString(hash);
    }

    public static bool VerifySignature(LicenseInfo info, string machineId)
    {
        if (string.IsNullOrEmpty(info.Signature)) return false;
        string expected = ComputeSignature(info, machineId);
        byte[] expectedBytes = Encoding.UTF8.GetBytes(expected);
        byte[] actualBytes = Encoding.UTF8.GetBytes(info.Signature);
        return CryptographicOperations.FixedTimeEquals(expectedBytes, actualBytes);
    }

    private static byte[] EncryptCache(byte[] plain, string machineId)
    {
        using var aes = Aes.Create();
        using var sha = SHA256.Create();
        aes.Key = sha.ComputeHash(Encoding.UTF8.GetBytes(SecretSalt + machineId));
        aes.IV = sha.ComputeHash(Encoding.UTF8.GetBytes(machineId + SecretSalt))[..16];
        using var ms = new MemoryStream();
        using (var cs = new CryptoStream(ms, aes.CreateEncryptor(), CryptoStreamMode.Write))
        {
            cs.Write(plain, 0, plain.Length);
        }
        return ms.ToArray();
    }

    private static byte[]? DecryptCache(byte[] cipher, string machineId)
    {
        try
        {
            using var aes = Aes.Create();
            using var sha = SHA256.Create();
            aes.Key = sha.ComputeHash(Encoding.UTF8.GetBytes(SecretSalt + machineId));
            aes.IV = sha.ComputeHash(Encoding.UTF8.GetBytes(machineId + SecretSalt))[..16];
            using var ms = new MemoryStream();
            using (var cs = new CryptoStream(new MemoryStream(cipher), aes.CreateDecryptor(), CryptoStreamMode.Read))
            {
                cs.CopyTo(ms);
            }
            return ms.ToArray();
        }
        catch
        {
            return null;
        }
    }

    public LicenseInfo? LoadCache()
    {
        string mid = _machineId;

        // 1. Thử file cache C#
        if (File.Exists(_cacheFilePath))
        {
            try
            {
                byte[] fileBytes = File.ReadAllBytes(_cacheFilePath);
                string json;
                if (fileBytes.Length > 0 && fileBytes[0] == '{')
                {
                    // Di trú từ cache văn bản rõ cũ
                    json = Encoding.UTF8.GetString(fileBytes);
                }
                else
                {
                    byte[]? decrypted = DecryptCache(fileBytes, mid);
                    if (decrypted == null) return null;
                    json = Encoding.UTF8.GetString(decrypted);
                }

                var info = JsonSerializer.Deserialize<LicenseInfo>(json);
                if (info != null && !string.IsNullOrEmpty(info.MachineId))
                {
                    // 1.1 Kiểm tra gắn kết máy
                    if (!string.Equals(info.MachineId, mid, StringComparison.OrdinalIgnoreCase))
                    {
                        return null;
                    }

                    // 1.2 Kiểm tra chữ ký toàn vẹn HMAC
                    if (!VerifySignature(info, mid))
                    {
                        if (string.IsNullOrEmpty(info.Signature))
                        {
                            SaveCache(info);
                        }
                        else
                        {
                            return null; // Bị can thiệp (Tampered) -> từ chối nạp
                        }
                    }

                    // 1.3 Chống lùi giờ hệ thống (Clock-rollback tampering)
                    if (DateTime.TryParse(info.LastCheck, out var dtLast) && dtLast > DateTime.UtcNow.AddDays(2))
                    {
                        return null;
                    }

                    info.FromCache = true;
                    return info;
                }
            }
            catch { }
        }

        // 2. Kế thừa từ Python MEA v5.0 (~/.exam_generator/license_cache.json)
        if (File.Exists(_pyCacheFilePath))
        {
            try
            {
                string json = File.ReadAllText(_pyCacheFilePath);
                using var doc = JsonDocument.Parse(json);
                var root = doc.RootElement;
                string pyMid = root.TryGetProperty("mid", out var pMid) ? (pMid.GetString() ?? "") : "";
                string status = root.TryGetProperty("status", out var pSt) ? (pSt.GetString() ?? "active") : "active";
                string tier = root.TryGetProperty("tier", out var pTr) ? (pTr.GetString() ?? "premium") : "premium";
                string name = root.TryGetProperty("name", out var pNm) ? (pNm.GetString() ?? "Thầy Đỗ Minh") : "Thầy Đỗ Minh";

                if (!string.IsNullOrEmpty(pyMid) && string.Equals(pyMid, mid, StringComparison.OrdinalIgnoreCase))
                {
                    var migrated = new LicenseInfo
                    {
                        Ok = true,
                        MachineId = mid,
                        Status = status,
                        Tier = tier,
                        Name = name,
                        Expiry = "Vĩnh viễn",
                        IssuedAt = DateTime.UtcNow.ToString("o"),
                        LastCheck = DateTime.UtcNow.ToString("o"),
                        FromCache = true
                    };
                    SaveCache(migrated);
                    return migrated;
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
            if (_isCustomCache && !string.IsNullOrEmpty(info.MachineId))
            {
                _machineId = info.MachineId;
            }

            string mid = _machineId;
            info.MachineId = mid;
            info.Signature = ComputeSignature(info, mid);

            string json = JsonSerializer.Serialize(info, new JsonSerializerOptions { WriteIndented = false });
            byte[] encrypted = EncryptCache(Encoding.UTF8.GetBytes(json), mid);
            File.WriteAllBytes(_cacheFilePath, encrypted);

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
                        cached_at = DateTime.UtcNow.ToString("o"),
                        signature = info.Signature
                    };
                    File.WriteAllText(_pyCacheFilePath, JsonSerializer.Serialize(pyObj, new JsonSerializerOptions { WriteIndented = true }));
                }
                catch { }
            }
        }
        catch { }
    }
}
