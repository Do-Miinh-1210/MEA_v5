using System;
using System.Diagnostics;
using System.IO;
using System.IO.Compression;
using System.Linq;
using System.Net.Http;
using System.Net.Http.Headers;
using System.Text.Json;
using System.Text.RegularExpressions;
using System.Threading;
using System.Threading.Tasks;
using System.Windows;

namespace MatrixExamAI.Desktop.Services;

public record UpdateInfo(
    string Version,
    string TagName,
    string ReleaseNotes,
    string DownloadUrl,
    long FileSize,
    string AssetName,
    DateTimeOffset? PublishedAt,
    bool IsPatch = false
);

public record UpdateProgressInfo(
    long BytesReceived,
    long TotalBytesToReceive,
    double Percentage
);

public class GitHubUpdateService
{
    public static GitHubUpdateService Instance { get; } = new();

    public string CurrentVersion { get; set; } = "5.2.0.3";
    public string DisplayVersion => "5.2.0.3";
    public string GitHubRepo { get; set; } = "Do-Miinh-1210/MEA_v5";
    public DateTime? LastCheckedTime { get; private set; }

    private readonly HttpClient _httpClient;

    // ponytail: In-memory HttpClient with direct GitHub API polling; upgrade to background polling worker if scheduled checks needed.
    public GitHubUpdateService(HttpClient? httpClient = null)
    {
        _httpClient = httpClient ?? new HttpClient();
        if (_httpClient.DefaultRequestHeaders.UserAgent.Count == 0)
        {
            _httpClient.DefaultRequestHeaders.UserAgent.Add(new ProductInfoHeaderValue("MatrixExamAI-Desktop", CurrentVersion));
        }

        try
        {
            string appData = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "MatrixExamAI");
            string cacheFile = Path.Combine(appData, "last_update_check.txt");
            if (File.Exists(cacheFile) && DateTime.TryParse(File.ReadAllText(cacheFile).Trim(), out var dt))
            {
                LastCheckedTime = dt;
            }
        }
        catch { }
    }

    public string GetLastCheckedDisplayText()
    {
        if (LastCheckedTime.HasValue)
        {
            return $"Lần cập nhật gần nhất: {LastCheckedTime.Value:dd/MM/yyyy HH:mm:ss}";
        }
        return "Lần cập nhật gần nhất: Chưa kiểm tra";
    }

    public void RecordCheckTime(DateTime? time = null)
    {
        LastCheckedTime = time ?? DateTime.Now;
        try
        {
            string appData = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "MatrixExamAI");
            Directory.CreateDirectory(appData);
            File.WriteAllText(Path.Combine(appData, "last_update_check.txt"), LastCheckedTime.Value.ToString("o"));
        }
        catch { }
    }

    public static bool IsNewerVersion(string remote, string local)
    {
        var r = ParseVersionTuple(remote);
        var l = ParseVersionTuple(local);

        if (r.Major != l.Major) return r.Major > l.Major;
        if (r.Minor != l.Minor) return r.Minor > l.Minor;
        if (r.Patch != l.Patch) return r.Patch > l.Patch;
        if (r.Build != l.Build) return r.Build > l.Build;
        if (r.Rank != l.Rank) return r.Rank > l.Rank;
        return r.PrereleaseNumber > l.PrereleaseNumber;
    }

    private static (int Major, int Minor, int Patch, int Build, int Rank, int PrereleaseNumber) ParseVersionTuple(string v)
    {
        string text = (v ?? string.Empty).Trim().TrimStart('v', 'V', ' ').Trim();
        var match = Regex.Match(text, @"^(\d+)(?:\.(\d+))?(?:\.(\d+))?(?:\.(\d+))?(?:[-+]([0-9A-Za-z._-]+))?$");
        if (!match.Success) return (0, 0, 0, 0, 0, 0);

        int major = int.TryParse(match.Groups[1].Value, out int maj) ? maj : 0;
        int minor = int.TryParse(match.Groups[2].Value, out int min) ? min : 0;
        int patch = int.TryParse(match.Groups[3].Value, out int pat) ? pat : 0;
        int build = int.TryParse(match.Groups[4].Value, out int bld) ? bld : 0;
        string suffix = match.Groups[5].Success ? match.Groups[5].Value.ToLowerInvariant() : string.Empty;

        if (string.IsNullOrEmpty(suffix))
        {
            return (major, minor, patch, build, 9, 0); // stable release has highest rank
        }

        var subMatch = Regex.Match(suffix, @"^(alpha|beta|rc)[._-]?(\d*)");
        if (subMatch.Success)
        {
            string label = subMatch.Groups[1].Value;
            int num = int.TryParse(subMatch.Groups[2].Value, out int n) ? n : 0;
            int rank = label switch
            {
                "alpha" => 1,
                "beta" => 2,
                "rc" => 3,
                _ => 5
            };
            return (major, minor, patch, build, rank, num);
        }

        return (major, minor, patch, build, 5, 0);
    }

    public async Task<UpdateInfo?> CheckForUpdateAsync(CancellationToken ct = default)
    {
        RecordCheckTime();
        string repo = Environment.GetEnvironmentVariable("MEA_GITHUB_REPO") ?? GitHubRepo;

        try
        {
            string url = $"https://api.github.com/repos/{repo}/releases/latest";

            using var request = new HttpRequestMessage(HttpMethod.Get, url);
            request.Headers.Accept.Add(new MediaTypeWithQualityHeaderValue("application/vnd.github.v3+json"));

            using var response = await _httpClient.SendAsync(request, HttpCompletionOption.ResponseHeadersRead, ct).ConfigureAwait(false);
            if (response.IsSuccessStatusCode)
            {
                string json = await response.Content.ReadAsStringAsync(ct).ConfigureAwait(false);
                var info = ParseReleaseJson(json);
                if (info != null) return info;
            }

            // Fallback khi unauthenticated GitHub API gặp lỗi 403 Rate Limit: dùng Web redirect
            return await CheckForUpdateViaWebRedirectAsync(repo, ct).ConfigureAwait(false);
        }
        catch
        {
            try
            {
                return await CheckForUpdateViaWebRedirectAsync(repo, ct).ConfigureAwait(false);
            }
            catch
            {
                return null;
            }
        }
    }

    public async Task<UpdateInfo?> CheckForUpdateViaWebRedirectAsync(string repo, CancellationToken ct = default)
    {
        try
        {
            string webUrl = $"https://github.com/{repo}/releases/latest";
            using var req = new HttpRequestMessage(HttpMethod.Get, webUrl);
            using var resp = await _httpClient.SendAsync(req, HttpCompletionOption.ResponseHeadersRead, ct).ConfigureAwait(false);

            var finalUri = resp.RequestMessage?.RequestUri?.ToString() ?? "";
            var match = Regex.Match(finalUri, @"/releases/tag/(v?([0-9A-Za-z._-]+))$");
            if (!match.Success) return null;

            string tagName = match.Groups[1].Value;
            string version = match.Groups[2].Value;

            if (!IsNewerVersion(version, CurrentVersion))
            {
                return null;
            }

            string patchUrl = $"https://github.com/{repo}/releases/download/{tagName}/MatrixExamAI_Patch.zip";
            return new UpdateInfo(
                Version: version,
                TagName: tagName,
                ReleaseNotes: $"Bản phát hành MatrixExamAI Pro {tagName}.",
                DownloadUrl: patchUrl,
                FileSize: 564844,
                AssetName: "MatrixExamAI_Patch.zip",
                PublishedAt: DateTimeOffset.UtcNow,
                IsPatch: true
            );
        }
        catch
        {
            return null;
        }
    }

    public UpdateInfo? ParseReleaseJson(string json)
    {
        try
        {
            using var doc = JsonDocument.Parse(json);
            var root = doc.RootElement;

            if (root.TryGetProperty("draft", out var draftProp) && draftProp.GetBoolean())
            {
                return null;
            }

            string tagName = root.TryGetProperty("tag_name", out var tagProp) ? tagProp.GetString() ?? "" : "";
            string remoteVer = tagName.Trim().TrimStart('v', 'V', ' ').Trim();
            if (string.IsNullOrEmpty(remoteVer) && root.TryGetProperty("name", out var nameProp))
            {
                remoteVer = (nameProp.GetString() ?? "").Trim().TrimStart('v', 'V', ' ').Trim();
            }

            if (string.IsNullOrEmpty(remoteVer) || !IsNewerVersion(remoteVer, CurrentVersion))
            {
                return null;
            }

            string body = root.TryGetProperty("body", out var bodyProp) ? bodyProp.GetString() ?? "" : "";
            DateTimeOffset? publishedAt = null;
            if (root.TryGetProperty("published_at", out var pubProp) && pubProp.TryGetDateTimeOffset(out var dto))
            {
                publishedAt = dto;
            }

            // Find patch zip or installer exe asset
            string downloadUrl = "";
            string assetName = "";
            long fileSize = 0;
            bool isPatch = false;

            if (root.TryGetProperty("assets", out var assetsProp) && assetsProp.ValueKind == JsonValueKind.Array)
            {
                var patchCandidate = assetsProp.EnumerateArray()
                    .FirstOrDefault(a =>
                    {
                        string name = a.TryGetProperty("name", out var np) ? np.GetString() ?? "" : "";
                        return name.EndsWith(".zip", StringComparison.OrdinalIgnoreCase) &&
                               (name.Contains("patch", StringComparison.OrdinalIgnoreCase) || name.Contains("delta", StringComparison.OrdinalIgnoreCase));
                    });

                if (patchCandidate.ValueKind != JsonValueKind.Undefined)
                {
                    isPatch = true;
                    assetName = patchCandidate.TryGetProperty("name", out var np) ? np.GetString() ?? "" : "";
                    downloadUrl = patchCandidate.TryGetProperty("browser_download_url", out var bp) ? bp.GetString() ?? "" : "";
                    fileSize = patchCandidate.TryGetProperty("size", out var sp) ? sp.GetInt64() : 0;
                }
                else
                {
                    var candidates = assetsProp.EnumerateArray()
                        .Where(a =>
                        {
                            string name = a.TryGetProperty("name", out var np) ? np.GetString() ?? "" : "";
                            return name.EndsWith(".exe", StringComparison.OrdinalIgnoreCase) && !name.EndsWith(".zip", StringComparison.OrdinalIgnoreCase);
                        })
                        .Select(a =>
                        {
                            string name = a.TryGetProperty("name", out var np) ? np.GetString() ?? "" : "";
                            string dUrl = a.TryGetProperty("browser_download_url", out var bp) ? bp.GetString() ?? "" : "";
                            long size = a.TryGetProperty("size", out var sp) ? sp.GetInt64() : 0;
                            int score = 0;
                            string low = name.ToLowerInvariant();
                            if (low.Contains("setup") || low.Contains("installer")) score += 4;
                            if (low.Contains("mea") || low.Contains("matrixexam")) score += 2;
                            if (low.Contains("v5") || low.Contains("5.")) score += 2;
                            if (low.Contains("x64") || low.Contains("win64")) score += 1;
                            if (low.Contains("admin") || low.Contains("portable") || low.Contains("debug")) score -= 3;
                            return (Name: name, Url: dUrl, Size: size, Score: score);
                        })
                        .OrderByDescending(c => c.Score)
                        .ToList();

                    if (candidates.Count > 0)
                    {
                        var best = candidates[0];
                        assetName = best.Name;
                        downloadUrl = best.Url;
                        fileSize = best.Size;
                    }
                }
            }

            if (string.IsNullOrEmpty(downloadUrl))
            {
                return null;
            }

            return new UpdateInfo(
                Version: remoteVer,
                TagName: tagName,
                ReleaseNotes: body,
                DownloadUrl: downloadUrl,
                FileSize: fileSize,
                AssetName: assetName,
                PublishedAt: publishedAt,
                IsPatch: isPatch
            );
        }
        catch
        {
            return null;
        }
    }

    public async Task<string> DownloadUpdateAsync(string downloadUrl, string? preferredFileName = null, IProgress<UpdateProgressInfo>? progress = null, CancellationToken ct = default)
    {
        string tempDir = Path.GetTempPath();
        string fileName = preferredFileName;
        if (string.IsNullOrWhiteSpace(fileName))
        {
            try
            {
                var uri = new Uri(downloadUrl);
                fileName = Path.GetFileName(uri.LocalPath);
            }
            catch
            {
                fileName = "MatrixExamAI_Update.bin";
            }
        }

        string destPath = Path.Combine(tempDir, fileName);

        if (File.Exists(destPath))
        {
            try { File.Delete(destPath); } catch { }
        }

        using var response = await _httpClient.GetAsync(downloadUrl, HttpCompletionOption.ResponseHeadersRead, ct).ConfigureAwait(false);
        response.EnsureSuccessStatusCode();

        long totalBytes = response.Content.Headers.ContentLength ?? -1L;

        await using var contentStream = await response.Content.ReadAsStreamAsync(ct).ConfigureAwait(false);
        await using var fileStream = new FileStream(destPath, FileMode.Create, FileAccess.Write, FileShare.None, 8192, true);

        byte[] buffer = new byte[8192];
        long totalRead = 0;
        int read;

        while ((read = await contentStream.ReadAsync(buffer, 0, buffer.Length, ct).ConfigureAwait(false)) > 0)
        {
            await fileStream.WriteAsync(buffer, 0, read, ct).ConfigureAwait(false);
            totalRead += read;
            if (totalBytes > 0 && progress != null)
            {
                double pct = Math.Round((double)totalRead / totalBytes * 100.0, 1);
                progress.Report(new UpdateProgressInfo(totalRead, totalBytes, pct));
            }
        }

        return destPath;
    }

    public void ApplyPatchAndExit(string zipPath)
    {
        if (!File.Exists(zipPath)) return;

        string tempDir = Path.GetTempPath();
        string patchStaging = Path.Combine(tempDir, "MEA_Patch_" + Guid.NewGuid().ToString("N"));
        Directory.CreateDirectory(patchStaging);

        ZipFile.ExtractToDirectory(zipPath, patchStaging, overwriteFiles: true);

        string targetDir = AppDomain.CurrentDomain.BaseDirectory.TrimEnd('\\', '/');
        string exeName = "MatrixExamAI.Desktop.exe";
        int currentPid = Environment.ProcessId;

        string batPath = Path.Combine(tempDir, $"mea_patch_{Guid.NewGuid():N}.bat");
        string batContent = $"""
        @echo off
        chcp 65001 >nul
        set "PID={currentPid}"
        set "TARGET={targetDir}"
        set "PATCH={patchStaging}"
        set "EXENAME={exeName}"

        :WAIT_PROC
        timeout /t 1 /nobreak >nul
        tasklist /fi "PID eq %PID%" 2>nul | find "%PID%" >nul
        if not errorlevel 1 goto WAIT_PROC

        icacls "%TARGET%" /grant *S-1-5-32-545:(OI)(CI)F /t /q >nul 2>&1
        icacls "%TARGET%" /grant Users:(OI)(CI)F /t /q >nul 2>&1
        xcopy /s /e /y "%PATCH%\*" "%TARGET%\" >nul 2>&1
        icacls "%TARGET%" /grant *S-1-5-32-545:(OI)(CI)F /t /q >nul 2>&1
        icacls "%TARGET%" /grant Users:(OI)(CI)F /t /q >nul 2>&1
        rmdir /s /q "%PATCH%" 2>nul
        if exist "{zipPath}" del /f /q "{zipPath}" 2>nul

        start "" "%TARGET%\%EXENAME%"
        del "%~f0" 2>nul
        """;

        File.WriteAllText(batPath, batContent);

        bool canWrite = CanWriteToDirectory(targetDir);
        var startInfo = new ProcessStartInfo
        {
            FileName = "cmd.exe",
            Arguments = $"/c \"{batPath}\"",
            CreateNoWindow = canWrite,
            UseShellExecute = !canWrite,
            Verb = canWrite ? "" : "runas",
            WindowStyle = canWrite ? ProcessWindowStyle.Hidden : ProcessWindowStyle.Normal
        };

        Process.Start(startInfo);

        if (Application.Current != null)
        {
            Application.Current.Dispatcher.Invoke(() => Application.Current.Shutdown());
        }
        else
        {
            Environment.Exit(0);
        }
    }

    private static bool CanWriteToDirectory(string dir)
    {
        try
        {
            string testFile = Path.Combine(dir, ".mea_perm_test_" + Guid.NewGuid().ToString("N"));
            File.WriteAllText(testFile, "test");
            File.Delete(testFile);
            return true;
        }
        catch
        {
            return false;
        }
    }

    public Process? LaunchInstaller(string installerPath, bool verySilent = false)
    {
        if (!File.Exists(installerPath) || !installerPath.EndsWith(".exe", StringComparison.OrdinalIgnoreCase))
        {
            return null;
        }

        var startInfo = new ProcessStartInfo
        {
            FileName = installerPath,
            Arguments = verySilent ? "/VERYSILENT /NORESTART /SUPPRESSMSGBOXES" : "/SILENT",
            UseShellExecute = true
        };

        return Process.Start(startInfo);
    }

    public void ApplyAndExit(string filePath, bool verySilent = false, bool isPatch = false)
    {
        if (isPatch || filePath.EndsWith(".zip", StringComparison.OrdinalIgnoreCase))
        {
            ApplyPatchAndExit(filePath);
        }
        else
        {
            LaunchInstaller(filePath, verySilent);
            if (Application.Current != null)
            {
                Application.Current.Dispatcher.Invoke(() => Application.Current.Shutdown());
            }
            else
            {
                Environment.Exit(0);
            }
        }
    }
}
