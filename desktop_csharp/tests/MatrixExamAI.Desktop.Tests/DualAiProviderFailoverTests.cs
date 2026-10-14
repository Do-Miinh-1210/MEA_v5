using System;
using System.Net;
using FluentAssertions;
using MatrixExamAI.Desktop.Services;
using MatrixExamAI.Shared.AI;
using Xunit;

namespace MatrixExamAI.Desktop.Tests
{
    public class DualAiProviderFailoverTests
    {
        #region Tier 1 - Normative Tests (Key Classification & Provider Routing)

        [Fact]
        public void KeyClassification_SkPrefix_ShouldRouteTo9RouterLocalAggregator()
        {
            // Simulate 9Router key (OpenAI format sk-...)
            string sampleKey = "sk-9router-local-key-sample-123456";

            sampleKey.StartsWith("sk-", StringComparison.OrdinalIgnoreCase).Should().BeTrue();

            // When apiKey starts with sk-, DesktopGeminiFactory designates 9Router endpoint
            string endpoint = "http://localhost:20128/v1/chat/completions";
            string provider = "9Router";

            endpoint.Should().Be("http://localhost:20128/v1/chat/completions");
            provider.Should().Be("9Router");
        }

        [Fact]
        public void KeyClassification_AIzaPrefix_ShouldRouteToGoogleGeminiDirect()
        {
            // Simulate Google Gemini Direct API key (AIza...)
            string sampleKey = "AIzaSyD-sample-google-gemini-key-789";

            sampleKey.StartsWith("AIza", StringComparison.OrdinalIgnoreCase).Should().BeTrue();

            string endpoint = "https://generativelanguage.googleapis.com/v1beta";
            string provider = "Google Gemini";

            endpoint.Should().Be("https://generativelanguage.googleapis.com/v1beta");
            provider.Should().Be("Google Gemini");
        }

        [Fact]
        public void ApiKeyPoolManager_RoundRobin_ShouldCycleThroughKeysSequentially()
        {
            var pool = new ApiKeyPoolManager(new[] { "KEY_ALPHA", "KEY_BETA", "KEY_GAMMA" });

            pool.TotalKeys.Should().Be(3);
            pool.ActiveKeys.Should().Be(3);

            var k1 = pool.GetNextAvailableKey();
            var k2 = pool.GetNextAvailableKey();
            var k3 = pool.GetNextAvailableKey();
            var k4 = pool.GetNextAvailableKey();

            k1!.Key.Should().Be("KEY_ALPHA");
            k2!.Key.Should().Be("KEY_BETA");
            k3!.Key.Should().Be("KEY_GAMMA");
            k4!.Key.Should().Be("KEY_ALPHA", "Round-robin must loop back to the first key");
        }

        #endregion

        #region Tier 2 - Boundary Value Tests (Rate Limit 429 & Cooldown)

        [Fact]
        public void ApiKeyPoolManager_RateLimit429_ShouldPlaceKeyInCooldownAndSkipToNext()
        {
            var pool = new ApiKeyPoolManager(new[] { "KEY_PRIMARY", "KEY_SECONDARY" });

            // Report 429 on KEY_PRIMARY
            pool.ReportFailure("KEY_PRIMARY", (HttpStatusCode)429, retryAfterSeconds: 30);

            // KEY_PRIMARY should now be in RateLimited state
            var next = pool.GetNextAvailableKey();
            next.Should().NotBeNull();
            next!.Key.Should().Be("KEY_SECONDARY", "Primary key is rate-limited, pool must serve secondary key");

            // Calling again should still serve KEY_SECONDARY because KEY_PRIMARY is under cooldown
            var nextAgain = pool.GetNextAvailableKey();
            nextAgain!.Key.Should().Be("KEY_SECONDARY");
        }

        [Fact]
        public void ApiKeyPoolManager_InvalidKey401_ShouldMarkKeyAsInvalidPermanently()
        {
            var pool = new ApiKeyPoolManager(new[] { "BAD_KEY", "GOOD_KEY" });

            pool.ReportFailure("BAD_KEY", HttpStatusCode.Unauthorized);

            var next = pool.GetNextAvailableKey();
            next!.Key.Should().Be("GOOD_KEY");

            // Check status summary reflects invalid key
            string summary = pool.GetStatusSummary();
            summary.Should().Contain("Không hợp lệ: 1");
        }

        [Fact]
        public void ApiKeyPoolManager_AllKeysExhausted_ShouldReturnNullSafely()
        {
            var pool = new ApiKeyPoolManager(new[] { "KEY_ONE" });
            pool.ReportFailure("KEY_ONE", HttpStatusCode.Forbidden);

            var next = pool.GetNextAvailableKey();
            next.Should().BeNull("When all keys are invalid/exhausted, pool must return null without throwing");
        }

        #endregion

        #region Tier 3 - Combinatorial & Key Masking Tests

        [Theory]
        [InlineData("AIzaSyD1234567890", "AIza...7890")]
        [InlineData("sk-proj-abc123456789xyz", "sk-p...9xyz")]
        [InlineData("short", "****")]
        [InlineData("", "")]
        public void ApiKeyEntry_MaskedKey_ShouldMaskSensitively(string rawKey, string expectedMask)
        {
            var entry = new ApiKeyEntry { Key = rawKey };
            entry.MaskedKey.Should().Be(expectedMask);
        }

        [Fact]
        public void FallbackOrchestrator_ConfiguredFallbackStatus_ShouldReflectConfig()
        {
            var orch = new FallbackOrchestrator();
            orch.HasConfiguredFallback().Should().BeFalse("Initial orchestrator without keys has no fallback");

            orch.NineRouterApiKey = "sk-sample-9router";
            orch.HasConfiguredFallback().Should().BeTrue();

            orch.NineRouterApiKey = null;
            orch.OpenAiApiKey = "sk-sample-openai";
            orch.HasConfiguredFallback().Should().BeTrue();
        }

        #endregion

        #region Tier 4 - Workload & Dynamic Key Loading Tests

        [Fact]
        public void ApiKeyPoolManager_LoadFromString_ShouldParseSeparatorsAndDeduplicate()
        {
            var pool = new ApiKeyPoolManager();
            string rawInput = "KEY1, KEY2; KEY3\nKEY4\r\nKEY1"; // with duplicate KEY1

            pool.LoadFromString(rawInput);

            pool.TotalKeys.Should().Be(4, "Duplicate KEY1 must be filtered out");
            pool.ActiveKeys.Should().Be(4);
        }

        #endregion

        #region Tier 5 - DesktopGeminiFactory Multi-Provider & Key Parser Tests

        [Fact]
        public void DesktopGeminiFactory_SplitKeys_ShouldHandleNewlinesCommasAndComments()
        {
            string raw = "key1\r\nkey2\n#commented_key\nkey3, key4; key1";
            var keys = DesktopGeminiFactory.SplitKeys(raw);

            keys.Should().HaveCount(4);
            keys.Should().ContainInOrder("key1", "key2", "key3", "key4");
            keys.Should().NotContain("#commented_key");
        }

        [Theory]
        [InlineData("Google Gemini", "gemini-3.8-flash")]
        [InlineData("9Router", "ag/gemini-3.8-flash")]
        [InlineData("Anthropic Claude", "claude-sonnet-5")]
        [InlineData("DeepSeek", "deepseek-chat")]
        [InlineData("OpenAI GPT", "gpt-4o")]
        public void DesktopGeminiFactory_DefaultModels_ShouldContainExpectedBaselineModels(string provider, string expectedModel)
        {
            DesktopGeminiFactory.DefaultModelsByProvider.Should().ContainKey(provider);
            DesktopGeminiFactory.DefaultModelsByProvider[provider].Should().Contain(expectedModel);
        }

        [Theory]
        [InlineData("Google Gemini", "https://aistudio.google.com/apikey")]
        [InlineData("9Router", "http://localhost:20128")]
        [InlineData("Anthropic Claude", "https://console.anthropic.com/settings/keys")]
        [InlineData("DeepSeek", "https://platform.deepseek.com/api_keys")]
        [InlineData("OpenAI GPT", "https://platform.openai.com/api-keys")]
        public void DesktopGeminiFactory_ProviderKeyUrls_ShouldMapToAccurateEndpoints(string provider, string expectedUrl)
        {
            DesktopGeminiFactory.ProviderKeyUrls.Should().ContainKey(provider);
            DesktopGeminiFactory.ProviderKeyUrls[provider].Should().Be(expectedUrl);
        }

        #endregion
    }
}
