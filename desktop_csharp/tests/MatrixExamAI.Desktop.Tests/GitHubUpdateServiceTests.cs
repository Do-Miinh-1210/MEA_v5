using System;
using System.IO;
using FluentAssertions;
using MatrixExamAI.Desktop.Services;
using Xunit;

namespace MatrixExamAI.Desktop.Tests;

public class GitHubUpdateServiceTests
{
    [Theory]
    [InlineData("5.2.0", "5.1.0", true)]
    [InlineData("v5.2.0", "5.1.0", true)]
    [InlineData("5.1.1", "5.1.0", true)]
    [InlineData("6.0.0", "5.9.9", true)]
    [InlineData("5.1.0", "5.1.0", false)]
    [InlineData("5.0.9", "5.1.0", false)]
    [InlineData("4.9.0", "5.0.0", false)]
    [InlineData("5.1.0", "5.1.0-rc1", true)]
    [InlineData("5.1.0-rc2", "5.1.0-rc1", true)]
    [InlineData("5.1.0-beta", "5.1.0-alpha", true)]
    [InlineData("5.1.0-alpha", "5.1.0-beta", false)]
    [InlineData("5.1.3.1", "5.1.3", true)]
    [InlineData("v5.1.3.1", "5.1.2.1", true)]
    [InlineData("5.1.3.2", "5.1.3.1", true)]
    [InlineData("5.1.3.2", "5.1.3", true)]
    [InlineData("5.1.3.3", "5.1.3.2", true)]
    [InlineData("5.1.3.4", "5.1.3.3", true)]
    [InlineData("5.1.3.5", "5.1.3.4", true)]
    [InlineData("5.1.3.6", "5.1.3.5", true)]
    [InlineData("5.2.0.1", "5.1.3.6", true)]
    [InlineData("v5.2.0.1", "5.1.3.6", true)]
    [InlineData("5.2.0.2", "5.2.0.1", true)]
    [InlineData("v5.2.0.2", "5.2.0.1", true)]
    [InlineData("5.2.0.3", "5.2.0.2", true)]
    [InlineData("v5.2.0.3", "5.2.0.2", true)]
    [InlineData("5.2.0.4", "5.2.0.3", true)]
    [InlineData("v5.2.0.4", "5.2.0.3", true)]
    [InlineData("5.2.0.3", "5.2.0.4", false)]
    [InlineData("5.3.0.0", "5.2.0.4", true)]
    [InlineData("v5.3.0.0", "5.2.0.4", true)]
    [InlineData("5.2.0.4", "5.3.0.0", false)]
    public void IsNewerVersion_ShouldCorrectlyCompareSemver(string remote, string local, bool expected)
    {
        bool result = GitHubUpdateService.IsNewerVersion(remote, local);
        result.Should().Be(expected);
    }

    [Fact]
    public void ParseReleaseJson_WithPatchZip_ShouldPrioritizePatchOverInstaller()
    {
        var service = new GitHubUpdateService { CurrentVersion = "5.1.0" };

        string json = """
        {
            "tag_name": "v5.1.3.2",
            "name": "MatrixExamAI Pro v5.1.3.2",
            "body": "Delta patch release",
            "published_at": "2026-10-15T00:00:00Z",
            "draft": false,
            "assets": [
                {
                    "name": "MatrixExamAI_Pro_Setup.exe",
                    "browser_download_url": "https://example.com/MatrixExamAI_Pro_Setup.exe",
                    "size": 11000000
                },
                {
                    "name": "MatrixExamAI_Patch.zip",
                    "browser_download_url": "https://example.com/MatrixExamAI_Patch.zip",
                    "size": 520000
                }
            ]
        }
        """;

        var updateInfo = service.ParseReleaseJson(json);

        updateInfo.Should().NotBeNull();
        updateInfo!.IsPatch.Should().BeTrue();
        updateInfo.AssetName.Should().Be("MatrixExamAI_Patch.zip");
        updateInfo.DownloadUrl.Should().Be("https://example.com/MatrixExamAI_Patch.zip");
        updateInfo.FileSize.Should().Be(520000);
    }

    [Fact]
    public void ParseReleaseJson_WithValidNewerRelease_ShouldReturnUpdateInfo()
    {
        var service = new GitHubUpdateService { CurrentVersion = "5.1.0" };

        string json = """
        {
            "tag_name": "v5.2.0",
            "name": "MatrixExamAI Pro v5.2.0",
            "body": "Fix Word Export bug and improve TikZ rendering",
            "published_at": "2026-10-14T10:00:00Z",
            "draft": false,
            "assets": [
                {
                    "name": "checksums.txt",
                    "browser_download_url": "https://github.com/Do-Miinh-1210/MEA_byDoMiinh/releases/download/v5.2.0/checksums.txt",
                    "size": 120
                },
                {
                    "name": "MatrixExamAI-Setup-5.2.0.exe",
                    "browser_download_url": "https://github.com/Do-Miinh-1210/MEA_byDoMiinh/releases/download/v5.2.0/MatrixExamAI-Setup-5.2.0.exe",
                    "size": 94371840
                }
            ]
        }
        """;

        var updateInfo = service.ParseReleaseJson(json);

        updateInfo.Should().NotBeNull();
        updateInfo!.Version.Should().Be("5.2.0");
        updateInfo.TagName.Should().Be("v5.2.0");
        updateInfo.ReleaseNotes.Should().Contain("Fix Word Export bug");
        updateInfo.DownloadUrl.Should().Be("https://github.com/Do-Miinh-1210/MEA_byDoMiinh/releases/download/v5.2.0/MatrixExamAI-Setup-5.2.0.exe");
        updateInfo.AssetName.Should().Be("MatrixExamAI-Setup-5.2.0.exe");
        updateInfo.FileSize.Should().Be(94371840);
    }

    [Fact]
    public void ParseReleaseJson_WithOlderOrEqualVersion_ShouldReturnNull()
    {
        var service = new GitHubUpdateService { CurrentVersion = "5.2.0" };

        string json = """
        {
            "tag_name": "v5.1.0",
            "name": "MatrixExamAI Pro v5.1.0",
            "body": "Older release",
            "draft": false,
            "assets": [
                {
                    "name": "Setup.exe",
                    "browser_download_url": "https://example.com/Setup.exe",
                    "size": 1000
                }
            ]
        }
        """;

        var updateInfo = service.ParseReleaseJson(json);
        updateInfo.Should().BeNull();
    }

    [Fact]
    public void ParseReleaseJson_WhenDraft_ShouldReturnNull()
    {
        var service = new GitHubUpdateService { CurrentVersion = "5.1.0" };

        string json = """
        {
            "tag_name": "v5.3.0",
            "name": "Draft release",
            "body": "Draft",
            "draft": true,
            "assets": [
                {
                    "name": "Setup.exe",
                    "browser_download_url": "https://example.com/Setup.exe",
                    "size": 1000
                }
            ]
        }
        """;

        var updateInfo = service.ParseReleaseJson(json);
        updateInfo.Should().BeNull();
    }

    [Fact]
    public void ParseReleaseJson_WhenNoExeAsset_ShouldReturnNull()
    {
        var service = new GitHubUpdateService { CurrentVersion = "5.1.0" };

        string json = """
        {
            "tag_name": "v5.3.0",
            "name": "Source release",
            "body": "No exe",
            "draft": false,
            "assets": [
                {
                    "name": "source.zip",
                    "browser_download_url": "https://example.com/source.zip",
                    "size": 1000
                }
            ]
        }
        """;

        var updateInfo = service.ParseReleaseJson(json);
        updateInfo.Should().BeNull();
    }

    [Fact]
    public void LaunchInstaller_WithNonExistentFile_ShouldReturnNull()
    {
        var service = new GitHubUpdateService();
        var process = service.LaunchInstaller(@"C:\non_existent_folder_xyz\installer.exe");
        process.Should().BeNull();
    }

    [Fact]
    public void GetLastCheckedDisplayText_WhenRecorded_ReturnsFormattedDate()
    {
        var service = new GitHubUpdateService();
        var testTime = new DateTime(2026, 10, 15, 14, 30, 0);
        service.RecordCheckTime(testTime);

        string display = service.GetLastCheckedDisplayText();
        display.Should().Be("Lần cập nhật gần nhất: 15/10/2026 14:30:00");
    }

    [Fact]
    public void CurrentVersion_ShouldBeAtLeast53018()
    {
        var service = GitHubUpdateService.Instance;
        service.CurrentVersion.Should().Be("5.3.0.20");
        service.DisplayVersion.Should().Be("5.3.0.20");
        GitHubUpdateService.IsNewerVersion("5.3.0.20", "5.3.0.19").Should().BeTrue();
        GitHubUpdateService.IsNewerVersion("5.3.0.19", "5.3.0.20").Should().BeFalse();
    }

    [Fact]
    public void MainWindow_Initialization_ShouldSucceedOnStaThread()
    {
        Exception? ex = null;
        var thread = new System.Threading.Thread(() =>
        {
            try
            {
                var win = new MainWindow();
                win.Should().NotBeNull();
                win.TxtAppVersionTop.Text.Should().Be("v5.3.0.20");
                win.TxtAppVersionBottom.Text.Should().Be("v5.3.0.20");
            }
            catch (Exception e)
            {
                ex = e;
            }
        });
        thread.SetApartmentState(System.Threading.ApartmentState.STA);
        thread.Start();
        thread.Join();

        ex.Should().BeNull();
    }
}
