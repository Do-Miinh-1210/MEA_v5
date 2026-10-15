using System;
using System.IO;
using System.Threading;
using System.Windows.Controls;
using MatrixExamAI.Desktop.Services;
using MatrixExamAI.Desktop.Views;
using Xunit;

namespace MatrixExamAI.Desktop.Tests
{
    public class StorageLocationServiceTests
    {
        [Fact]
        public void DefaultExportDirectory_ReturnsValidPath_AndPersistsChange()
        {
            string original = StorageLocationService.GetDefaultExportDirectory();
            Assert.False(string.IsNullOrWhiteSpace(original));

            string tempTestDir = Path.Combine(Path.GetTempPath(), "MEA_TestExport_" + Guid.NewGuid().ToString("N"));
            try
            {
                StorageLocationService.SetDefaultExportDirectory(tempTestDir);
                string updated = StorageLocationService.GetDefaultExportDirectory();
                Assert.Equal(tempTestDir, updated);
                Assert.True(Directory.Exists(tempTestDir));
            }
            finally
            {
                // Restore original
                StorageLocationService.SetDefaultExportDirectory(original);
                if (Directory.Exists(tempTestDir))
                {
                    try { Directory.Delete(tempTestDir, true); } catch { }
                }
            }
        }

        [Fact]
        public void QuestionBankDirectory_ReturnsValidPath_AndPersistsChange()
        {
            string original = StorageLocationService.GetQuestionBankDirectory();
            Assert.False(string.IsNullOrWhiteSpace(original));

            string tempTestDir = Path.Combine(Path.GetTempPath(), "MEA_TestBank_" + Guid.NewGuid().ToString("N"));
            try
            {
                StorageLocationService.SetQuestionBankDirectory(tempTestDir);
                string updated = StorageLocationService.GetQuestionBankDirectory();
                Assert.Equal(tempTestDir, updated);
                Assert.True(Directory.Exists(tempTestDir));
            }
            finally
            {
                // Restore original
                StorageLocationService.SetQuestionBankDirectory(original);
                if (Directory.Exists(tempTestDir))
                {
                    try { Directory.Delete(tempTestDir, true); } catch { }
                }
            }
        }

        [Fact]
        public void OpenAfterExport_PersistsFlag()
        {
            bool orig = StorageLocationService.GetOpenAfterExport();
            try
            {
                StorageLocationService.SetOpenAfterExport(false);
                Assert.False(StorageLocationService.GetOpenAfterExport());

                StorageLocationService.SetOpenAfterExport(true);
                Assert.True(StorageLocationService.GetOpenAfterExport());
            }
            finally
            {
                StorageLocationService.SetOpenAfterExport(orig);
            }
        }

        [Fact]
        public void ShuffleView_And_SettingsView_StorageControls_Exist_OnSTA()
        {
            Exception? threadEx = null;
            var t = new Thread(() =>
            {
                try
                {
                    var settingsView = new SettingsView();
                    Assert.NotNull(settingsView.FindName("TxtDefaultExportPath"));
                    Assert.NotNull(settingsView.FindName("BtnBrowseExportPath"));
                    Assert.NotNull(settingsView.FindName("BtnOpenExportPath"));
                    Assert.NotNull(settingsView.FindName("TxtQuestionBankPath"));
                    Assert.NotNull(settingsView.FindName("BtnBrowseBankPath"));
                    Assert.NotNull(settingsView.FindName("BtnOpenBankPath"));
                    Assert.NotNull(settingsView.FindName("ChkOpenAfterExport"));

                    var shuffleView = new ShuffleView();
                    Assert.NotNull(shuffleView.FindName("TxtShuffleOutputDir"));
                    Assert.NotNull(shuffleView.FindName("BtnBrowseShuffleOutputDir"));
                    Assert.NotNull(shuffleView.FindName("BtnOpenShuffleOutputDir"));
                }
                catch (Exception ex)
                {
                    threadEx = ex;
                }
            });
            t.SetApartmentState(ApartmentState.STA);
            t.Start();
            t.Join();

            Assert.Null(threadEx);
        }
    }
}
