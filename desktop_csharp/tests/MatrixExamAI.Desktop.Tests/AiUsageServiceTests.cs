using System;
using System.IO;
using MatrixExamAI.Desktop.Services;
using Xunit;

namespace MatrixExamAI.Desktop.Tests
{
    public class AiUsageServiceTests
    {
        [Fact]
        public void AiUsageService_SingletonInstance_IsNotNull()
        {
            var instance = AiUsageService.Instance;
            Assert.NotNull(instance);
        }

        [Fact]
        public void AiUsageService_GetStats_ReturnsValidKpis()
        {
            var service = AiUsageService.Instance;
            var stats = service.GetStats("all");

            Assert.NotNull(stats);
            Assert.True(stats.TotalRequests >= 0);
            Assert.True(stats.SuccessRate >= 0.0 && stats.SuccessRate <= 100.0);
            Assert.NotNull(stats.ProviderBreakdown);
            Assert.NotNull(stats.RecentEntries);
            Assert.NotNull(stats.QuotaWarning);
        }

        [Theory]
        [InlineData("today")]
        [InlineData("7")]
        [InlineData("30")]
        [InlineData("all")]
        public void AiUsageService_GetStats_SupportsAllRanges(string range)
        {
            var service = AiUsageService.Instance;
            var stats = service.GetStats(range);

            Assert.NotNull(stats);
            Assert.NotNull(stats.RecentEntries);
        }

        [Fact]
        public void AiUsageService_Record_RecordsEntrySuccessfully()
        {
            var service = AiUsageService.Instance;
            string testModel = "test-gemini-flash";
            string testProvider = "UnitTests";

            service.Record(testProvider, testModel, "convert", 100, 200, 150, true);

            var stats = service.GetStats("today");
            Assert.NotNull(stats);
            Assert.Contains(stats.RecentEntries, e => e.Model == testModel && e.Provider == testProvider);
        }
    }
}
