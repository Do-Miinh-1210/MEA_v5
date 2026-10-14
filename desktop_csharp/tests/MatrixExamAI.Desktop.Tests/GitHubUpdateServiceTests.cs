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
    public void IsNewerVersion_ShouldCorrectlyCompareSemver(string remote, string local, bool expected)
    {
        bool result = GitHubUpdateService.IsNewerVersion(remote, local);
        result.Should().Be(expected);
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
}
