using System;
using System.Threading;
using FluentAssertions;
using MatrixExamAI.Desktop.Services;
using Xunit;

namespace MatrixExamAI.Desktop.Tests
{
    public class SafeClipboardTests
    {
        [Fact]
        public void SafeClipboard_SetTextAndGetText_ShouldNotThrowAndHandleTextGracefully()
        {
            var thread = new Thread(() =>
            {
                // Test null safety
                SafeClipboard.SetText(null!).Should().BeFalse("Null text should return false without exception");

                // Test valid text setting
                string testString = "MatrixExamAI SafeClipboard Test " + Guid.NewGuid().ToString("N");
                bool setResult = SafeClipboard.SetText(testString);
                
                // If clipboard is available on the machine, verify content
                if (setResult)
                {
                    string retrieved = SafeClipboard.GetText();
                    retrieved.Should().Be(testString);
                    SafeClipboard.ContainsText().Should().BeTrue();
                }
            });
            thread.SetApartmentState(ApartmentState.STA);
            thread.Start();
            thread.Join();
        }

        [Fact]
        public void SafeClipboard_ContainsImage_OnEmptyClipboard_ShouldNotThrow()
        {
            var thread = new Thread(() =>
            {
                // Must not throw even if clipboard doesn't have an image
                var action = () => SafeClipboard.ContainsImage();
                action.Should().NotThrow();

                var getImageAction = () => SafeClipboard.GetImage();
                getImageAction.Should().NotThrow();
            });
            thread.SetApartmentState(ApartmentState.STA);
            thread.Start();
            thread.Join();
        }
    }
}
