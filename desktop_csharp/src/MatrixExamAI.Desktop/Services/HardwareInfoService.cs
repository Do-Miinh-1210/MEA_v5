using System;
using System.Diagnostics;
using System.Security.Cryptography;
using System.Text;
using Microsoft.Win32;

namespace MatrixExamAI.Desktop.Services;

public static class HardwareInfoService
{
    private static string? _cachedMachineId;

    public static string GetMachineId()
    {
        if (!string.IsNullOrEmpty(_cachedMachineId))
        {
            return _cachedMachineId;
        }

        string rawUuid = GetHardwareUuid();
        using var sha = SHA256.Create();
        byte[] hash = sha.ComputeHash(Encoding.UTF8.GetBytes(rawUuid));
        string hex = Convert.ToHexString(hash).ToUpperInvariant();

        if (hex.Length >= 12)
        {
            _cachedMachineId = $"{hex[..4]}-{hex.Substring(4, 4)}-{hex.Substring(8, 4)}";
        }
        else
        {
            _cachedMachineId = "MEA-PRO-2026";
        }

        return _cachedMachineId;
    }

    public static string GetHardwareUuid()
    {
        // 1. Thử Windows Registry MachineGuid (nhanh nhất, chuẩn xác nhất)
        try
        {
            using var key = Registry.LocalMachine.OpenSubKey(@"SOFTWARE\Microsoft\Cryptography");
            var guid = key?.GetValue("MachineGuid")?.ToString();
            if (!string.IsNullOrWhiteSpace(guid))
            {
                return guid.Trim();
            }
        }
        catch { }

        // 2. Thử wmic csproduct get uuid
        try
        {
            var psi = new ProcessStartInfo
            {
                FileName = "wmic",
                Arguments = "csproduct get uuid",
                RedirectStandardOutput = true,
                UseShellExecute = false,
                CreateNoWindow = true
            };
            using var p = Process.Start(psi);
            if (p != null)
            {
                string output = p.StandardOutput.ReadToEnd();
                p.WaitForExit(3000);
                var lines = output.Split(new[] { '\r', '\n' }, StringSplitOptions.RemoveEmptyEntries);
                foreach (var line in lines)
                {
                    var t = line.Trim();
                    if (!string.IsNullOrEmpty(t) && !t.Equals("UUID", StringComparison.OrdinalIgnoreCase))
                    {
                        return t;
                    }
                }
            }
        }
        catch { }

        // 3. Fallback danh danh phần cứng máy
        return $"{Environment.MachineName}|{Environment.UserName}|{Environment.OSVersion}";
    }

    public static string GetMachineDisplay()
    {
        return $"{Environment.OSVersion} — {Environment.MachineName}";
    }
}
