using System;
using System.Diagnostics;
using System.IO;
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
    DateTimeOffset? PublishedAt
);

public record UpdateProgressInfo(
    long BytesReceived,
    long TotalBytesToReceive,
    double Percentage
);

public class GitHubUpdateService
{
    public static GitHubUpdateService Instance { get; } = new();

    public string CurrentVersion { get; set; } = "5.1.0";
    public string GitHubRepo { get; set; } = "Do-Miinh-1210/MEA_v5";

    private readonly HttpClient _httpClient;

    // ponytail: In-memory HttpClient with direct GitHub API polling; upgrade to background polling worker if scheduled checks needed.
    public GitHubUpdateService(HttpClient? httpClient = null)
    {
        _httpClient = httpClient ?? new HttpClient();
        if (_httpClient.DefaultRequestHeaders.UserAgent.Count == 0)
        {
            _httpClient.DefaultRequestHeaders.UserAgent.Add(new ProductInfoHeaderValue("MatrixExamAI-Desktop", CurrentVersion));
        }
    }

    public static bool IsNewerVersion(string remote, string local)
    {
        var r = ParseVersionTuple(remote);
        var l = ParseVersionTuple(local);

        if (r.Major != l.Major) return r.Major > l.Major;
        if (r.Minor != l.Minor) return r.Minor > l.Minor;
        if (r.Patch != l.Patch) return r.Patch > l.Patch;
        if (r.Rank != l.Rank) return r.Rank > l.Rank;
        return r.PrereleaseNumber > l.PrereleaseNumber;
    }

    private static (int Major, int Minor, int Patch, int Rank, int PrereleaseNumber) ParseVersionTuple(string v)
    {
        string text = (v ?? string.Empty).Trim().TrimStart('v', 'V', ' ').Trim();
        var match = Regex.Match(text, @"^(\d+)(?:\.(\d+))?(?:\.(\d+))?(?:[-+]([0-9A-Za-z._-]+))?$");
        if (!match.Success) return (0, 0, 0, 0, 0);

        int major = int.TryParse(match.Groups[1].Value, out int maj) ? maj : 0;
        int minor = int.TryParse(match.Groups[2].Value, out int min) ? min : 0;
        int patch = int.TryParse(match.Groups[3].Value, out int pat) ? pat : 0;
        string suffix = match.Groups[4].Success ? match.Groups[4].Value.ToLowerInvariant() : string.Empty;

        if (string.IsNullOrEmpty(suffix))
        {
            return (major, minor, patch, 9, 0); // stable release has highest rank
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
            return (major, minor, patch, rank, num);
        }

        return (major, minor, patch, 5, 0);
    }

    public async Task<UpdateInfo?> CheckForUpdateAsync(CancellationToken ct = default)
    {
        try
        {
            string repo = Environment.GetEnvironmentVariable("MEA_GITHUB_REPO") ?? GitHubRepo;
            string url = $"https://api.github.com/repos/{repo}/releases/latest";

            using var request = new HttpRequestMessage(HttpMethod.Get, url);
            request.Headers.Accept.Add(new MediaTypeWithQualityHeaderValue("application/vnd.github.v3+json"));

            using var response = await _httpClient.SendAsync(request, HttpCompletionOption.ResponseHeadersRead, ct).ConfigureAwait(false);
            if (!response.IsSuccessStatusCode)
            {
                return null;
            }

            string json = await response.Content.ReadAsStringAsync(ct).ConfigureAwait(false);
            return ParseReleaseJson(json);
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

            // Find best installer .exe asset
            string downloadUrl = "";
            string assetName = "";
            long fileSize = 0;

            if (root.TryGetProperty("assets", out var assetsProp) && assetsProp.ValueKind == JsonValueKind.Array)
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
                PublishedAt: publishedAt
            );
        }
        catch
        {
            return null;
        }
    }

    public async Task<string> DownloadUpdateAsync(string downloadUrl, IProgress<UpdateProgressInfo>? progress = null, CancellationToken ct = default)
    {
        string tempDir = Path.GetTempPath();
        string destPath = Path.Combine(tempDir, "MatrixExamAI_Setup_Update.exe");

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

    public void ApplyAndExit(string installerPath, bool verySilent = false)
    {
        LaunchInstaller(installerPath, verySilent);
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
