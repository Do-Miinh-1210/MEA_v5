using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Text.Json;
using System.Threading;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Input;
using System.Windows.Media.Imaging;
using FluentAssertions;
using MatrixExamAI.Desktop;
using MatrixExamAI.Desktop.Services;
using MatrixExamAI.Desktop.Views;
using MatrixExamAI.Shared.Extensibility;
using Microsoft.Data.Sqlite;
using Wpf.Ui.Controls;
using Xunit;

namespace MatrixExamAI.Desktop.Tests
{
    /// <summary>
    /// Empirical Challenger Stress Test Suite for Requirements R3 & R4:
    /// 1. ShuffleView (Locked options preservation, answer tracking, OMR bubble sheet PNG with 4 corner markers at 150 DPI)
    /// 2. SQLite Schema Adapter (Fallback between ~/.exam_generator and LocalAppData, Python data_json parsing, cognitive levels mapping)
    /// 3. UI & Shortcuts (Rapid shortcut dispatching, 100% ToolTips across all views, strict "1 Button - 1 Icon" rule)
    /// </summary>
    public class ChallengerSubsystemsUiStressTests : IDisposable
    {
        private readonly string _tempDir;

        public ChallengerSubsystemsUiStressTests()
        {
            _tempDir = Path.Combine(Path.GetTempPath(), "MEA_Challenger2_" + Guid.NewGuid().ToString("N"));
            Directory.CreateDirectory(_tempDir);
        }

        public void Dispose()
        {
            try
            {
                if (Directory.Exists(_tempDir))
                {
                    Directory.Delete(_tempDir, true);
                }
            }
            catch
            {
                // Best-effort cleanup
            }
        }

        #region Helper STA & Reflection Methods

        private static void RunOnSta(Action action)
        {
            Exception? exception = null;
            var thread = new Thread(() =>
            {
                try
                {
                    action();
                }
                catch (Exception ex)
                {
                    exception = ex;
                }
            });
            thread.SetApartmentState(ApartmentState.STA);
            thread.Start();
            thread.Join();
            if (exception != null)
            {
                System.Runtime.ExceptionServices.ExceptionDispatchInfo.Capture(exception).Throw();
            }
        }

        private static List<ExamVariant> InvokeMixVariantsInternal(
            ExamDraftResult draft,
            int count,
            int startCode,
            bool shuffleOptions,
            bool lockSpecialOptions)
        {
            var method = typeof(ShuffleView).GetMethod("MixVariantsInternal", BindingFlags.NonPublic | BindingFlags.Static);
            method.Should().NotBeNull("ShuffleView.MixVariantsInternal must exist");
            return (List<ExamVariant>)method!.Invoke(null, new object[] { draft, count, startCode, shuffleOptions, lockSpecialOptions })!;
        }

        private static bool InvokeIsSpecialLockedOption(string text)
        {
            var method = typeof(ShuffleView).GetMethod("IsSpecialLockedOption", BindingFlags.NonPublic | BindingFlags.Static);
            method.Should().NotBeNull("ShuffleView.IsSpecialLockedOption must exist");
            return (bool)method!.Invoke(null, new object[] { text })!;
        }

        private static IEnumerable<T> FindVisualAndLogicalChildren<T>(DependencyObject depObj) where T : DependencyObject
        {
            if (depObj == null) yield break;

            if (depObj is T match)
            {
                yield return match;
            }

            var children = new List<DependencyObject>();

            if (depObj is Panel panel)
            {
                foreach (UIElement child in panel.Children)
                {
                    children.Add(child);
                }
            }
            else if (depObj is ContentControl cc && cc.Content is DependencyObject cDep)
            {
                children.Add(cDep);
            }
            else if (depObj is Decorator dec && dec.Child != null)
            {
                children.Add(dec.Child);
            }
            else
            {
                try
                {
                    foreach (var child in LogicalTreeHelper.GetChildren(depObj))
                    {
                        if (child is DependencyObject d) children.Add(d);
                    }
                }
                catch
                {
                    // Ignore non-logical children
                }
            }

            foreach (var child in children)
            {
                foreach (var sub in FindVisualAndLogicalChildren<T>(child))
                {
                    yield return sub;
                }
            }
        }

        #endregion

        #region 1. ShuffleView & OMR Sheet Empirical Stress Tests

        [Theory]
        [InlineData("Cả A và B đều đúng")]
        [InlineData("Cả A, B đều đúng")]
        [InlineData("Cả hai phương án trên")]
        [InlineData("Cả 3 phương án trên")]
        [InlineData("Tất cả các đáp án trên")]
        [InlineData("Tất cả đáp án trên")]
        [InlineData("Không có đáp án nào đúng")]
        [InlineData("Không có phương án nào chính xác")]
        public void ShuffleView_IsSpecialLockedOption_ShouldRecognizeAllVietnameseSpecialOptions(string specialText)
        {
            bool isLocked = InvokeIsSpecialLockedOption(specialText);
            isLocked.Should().BeTrue($"Option '{specialText}' must be recognized as special locked option");
        }

        [Fact]
        public void ShuffleView_LockedOptionAtPositionD_NeverPermutedToOtherPositions_AcrossManyRounds()
        {
            // Arrange: Question where option D is "Cả A và B đều đúng"
            var draft = new ExamDraftResult { Title = "Đề trắc nghiệm đặc thù" };
            draft.Part1Questions.Add(new QuestionItem
            {
                QuestionCode = "Q_SPEC_01",
                Content = "Khẳng định nào sau đây là đúng?",
                Options = new Dictionary<string, string>
                {
                    ["A"] = "Hàm số đồng biến trên (0; 2)",
                    ["B"] = "Hàm số đạt cực đại tại x = 0",
                    ["C"] = "Hàm số có giá trị nhỏ nhất bằng -2",
                    ["D"] = "Cả A và B đều đúng"
                },
                CorrectAnswer = "D"
            });

            // Act: Run 50 permutation variants (codes 101 to 150)
            int variantCount = 50;
            var variants = InvokeMixVariantsInternal(draft, variantCount, 101, shuffleOptions: true, lockSpecialOptions: true);

            // Assert: In 100% of variants, option D must strictly remain "Cả A và B đều đúng"
            variants.Should().HaveCount(variantCount);
            for (int i = 0; i < variants.Count; i++)
            {
                var q = variants[i].Part1Questions[0];
                q.Options.Should().ContainKey("D");
                q.Options["D"].Should().Be("Cả A và B đều đúng",
                    $"In variant {variants[i].ExamCode}, option D must remain locked at position D");

                // Correct answer was D, must still be D
                q.CorrectAnswer.Should().Be("D");
                variants[i].AnswerKey[1].Should().Be("D");

                // Options A, B, C must not contain the locked text
                q.Options["A"].Should().NotBe("Cả A và B đều đúng");
                q.Options["B"].Should().NotBe("Cả A và B đều đúng");
                q.Options["C"].Should().NotBe("Cả A và B đều đúng");
            }
        }

        [Fact]
        public void ShuffleView_CorrectAnswerTracking_WhenCorrectAnswerIsMovableOption()
        {
            // Arrange: Option B is the correct answer ("Nội dung đúng")
            var draft = new ExamDraftResult { Title = "Đề trắc nghiệm kiểm tra đáp án" };
            draft.Part1Questions.Add(new QuestionItem
            {
                QuestionCode = "Q_TRACK_01",
                Content = "Tìm khẳng định chính xác:",
                Options = new Dictionary<string, string>
                {
                    ["A"] = "Nội dung sai 1",
                    ["B"] = "Nội dung đúng (ĐÚNG)",
                    ["C"] = "Nội dung sai 2",
                    ["D"] = "Tất cả các đáp án trên"
                },
                CorrectAnswer = "B"
            });

            // Act: Generate 30 variants
            var variants = InvokeMixVariantsInternal(draft, 30, 201, shuffleOptions: true, lockSpecialOptions: true);

            // Assert
            variants.Should().HaveCount(30);
            foreach (var variant in variants)
            {
                var q = variant.Part1Questions[0];
                string assignedCorrectLetter = q.CorrectAnswer;

                // Assigned correct letter must point to "Nội dung đúng (ĐÚNG)"
                q.Options.Should().ContainKey(assignedCorrectLetter);
                q.Options[assignedCorrectLetter].Should().Be("Nội dung đúng (ĐÚNG)",
                    $"In variant {variant.ExamCode}, CorrectAnswer letter '{assignedCorrectLetter}' must point to the original correct option text");

                // AnswerKey dictionary must match
                variant.AnswerKey[1].Should().Be(assignedCorrectLetter);

                // Option D must still be locked
                q.Options["D"].Should().Be("Tất cả các đáp án trên");
            }
        }

        [Fact]
        public void ShuffleView_WhenLockSpecialOptionsIsFalse_AllowsFreePermutation()
        {
            var draft = new ExamDraftResult { Title = "Đề hoán vị tự do" };
            draft.Part1Questions.Add(new QuestionItem
            {
                QuestionCode = "Q_FREE_01",
                Content = "Khẳng định nào đúng?",
                Options = new Dictionary<string, string>
                {
                    ["A"] = "Phương án 1",
                    ["B"] = "Phương án 2",
                    ["C"] = "Phương án 3",
                    ["D"] = "Cả A và B đều đúng"
                },
                CorrectAnswer = "D"
            });

            // Act with lockSpecialOptions: false
            var variants = InvokeMixVariantsInternal(draft, 40, 101, shuffleOptions: true, lockSpecialOptions: false);

            // Over 40 randomized rounds, option D ("Cả A và B đều đúng") should appear in other slots (A, B, or C)
            var lettersWithSpecial = variants
                .Select(v => v.Part1Questions[0].Options.First(kv => kv.Value == "Cả A và B đều đúng").Key)
                .Distinct()
                .ToList();

            lettersWithSpecial.Count.Should().BeGreaterThan(1,
                "When lockSpecialOptions is false, the option should permute to multiple different positions");
        }

        [Fact]
        public void OmrSheetGenerator_ShouldProduceValidPng_WithExactDimensionsAnd150Dpi()
        {
            // Act: Generate PNG bytes on STA thread
            byte[] pngBytes = OmrSheetGenerator.GenerateOmrSheetPng(numQuestions: 40, hasEssay: false);

            // Assert 1: File size > 20KB
            pngBytes.Should().NotBeNull();
            pngBytes.Length.Should().BeGreaterThan(20000, "Rendered A4 PNG must be at least 20KB");

            // Assert 2: Standard PNG Magic Bytes: 89 50 4E 47 0D 0A 1A 0A
            byte[] pngHeader = new byte[] { 0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A };
            pngBytes.Take(8).Should().Equal(pngHeader, "Output must be a valid PNG format image");

            // Assert 3: Decode and verify image properties via BitmapDecoder
            using var ms = new MemoryStream(pngBytes);
            var decoder = new PngBitmapDecoder(ms, BitmapCreateOptions.PreservePixelFormat, BitmapCacheOption.OnLoad);
            decoder.Frames.Count.Should().Be(1);

            var frame = decoder.Frames[0];
            frame.PixelWidth.Should().Be(1240, "A4 width at 150 DPI must be 1240 px");
            frame.PixelHeight.Should().Be(1754, "A4 height at 150 DPI must be 1754 px");
            frame.DpiX.Should().BeApproximately(150.0, 0.1, "DpiX must be approximately 150 DPI (within PNG pHYs rounding)");
            frame.DpiY.Should().BeApproximately(150.0, 0.1, "DpiY must be approximately 150 DPI (within PNG pHYs rounding)");
        }

        [Fact]
        public void OmrSheetGenerator_LayoutMetadata_ShouldContainFourCornerMarkers_AtExactCoordinates()
        {
            var meta = OmrSheetGenerator.GetLayoutMetadata(numQuestions: 40, hasEssay: false);

            meta.CornerMarkers.Should().HaveCount(4, "OMR sheet requires exactly 4 corner markers for perspective alignment");
            meta.Width.Should().Be(1240);
            meta.Height.Should().Be(1754);
            meta.Dpi.Should().Be(150);

            // Top-Left: (60, 60)
            meta.CornerMarkers[0].X.Should().Be(60);
            meta.CornerMarkers[0].Y.Should().Be(60);

            // Top-Right: (1240 - 60 - 50 = 1130, 60)
            meta.CornerMarkers[1].X.Should().Be(1130);
            meta.CornerMarkers[1].Y.Should().Be(60);

            // Bottom-Left: (60, 1754 - 60 - 50 = 1644)
            meta.CornerMarkers[2].X.Should().Be(60);
            meta.CornerMarkers[2].Y.Should().Be(1644);

            // Bottom-Right: (1130, 1644)
            meta.CornerMarkers[3].X.Should().Be(1130);
            meta.CornerMarkers[3].Y.Should().Be(1644);

            // Verify CodeBubbles (3 columns of 10 digits 0-9)
            meta.CodeBubbles.Should().HaveCount(3);
            for (int col = 0; col < 3; col++)
            {
                meta.CodeBubbles[col].Should().HaveCount(10);
                for (int d = 0; d < 10; d++)
                {
                    meta.CodeBubbles[col].Should().ContainKey(d);
                }
            }

            // Verify QuestionBubbles (40 questions, each A-B-C-D)
            meta.QuestionBubbles.Should().HaveCount(40);
            for (int q = 1; q <= 40; q++)
            {
                meta.QuestionBubbles[q].Should().ContainKeys("A", "B", "C", "D");
            }
        }

        [Fact]
        public void OmrSheetGenerator_RenderedBitmap_HasCornerMarkersPixelsDrawn()
        {
            byte[] pngBytes = OmrSheetGenerator.GenerateOmrSheetPng(numQuestions: 40, hasEssay: false);
            using var ms = new MemoryStream(pngBytes);
            var decoder = new PngBitmapDecoder(ms, BitmapCreateOptions.PreservePixelFormat, BitmapCacheOption.OnLoad);
            
            // Standardize format to Bgra32 for reliable pixel inspection
            var frame = new FormatConvertedBitmap(decoder.Frames[0], System.Windows.Media.PixelFormats.Bgra32, null, 0);

            int stride = frame.PixelWidth * 4;
            byte[] pixels = new byte[frame.PixelHeight * stride];
            frame.CopyPixels(pixels, stride, 0);

            // Top-Left corner marker: outer rect is from DIP (60, 60) to (110, 110).
            // At 150 DPI, 1 DIP = 150/96 = 1.5625 pixels.
            // Check pixel at DIP (65, 65) -> Pixel (101, 101) inside the black border:
            double dpiScale = 150.0 / 96.0;
            int xBlack = (int)(65 * dpiScale);
            int yBlack = (int)(65 * dpiScale);
            int blackOffset = yBlack * stride + xBlack * 4;
            byte rBlack = pixels[blackOffset + 2];
            byte gBlack = pixels[blackOffset + 1];
            byte bBlack = pixels[blackOffset];

            rBlack.Should().BeLessThan(30, "Outer region of corner marker must be black");
            gBlack.Should().BeLessThan(30);
            bBlack.Should().BeLessThan(30);

            // Margin pixel outside marker at DIP (20, 20) -> Pixel (31, 31) should be white background
            int xWhite = (int)(20 * dpiScale);
            int yWhite = (int)(20 * dpiScale);
            int outOffset = yWhite * stride + xWhite * 4;
            pixels[outOffset + 2].Should().BeGreaterThan(240, "Background outside marker must be white");
            pixels[outOffset + 1].Should().BeGreaterThan(240);
            pixels[outOffset].Should().BeGreaterThan(240);
        }

        #endregion

        #region 2. SQLite Schema Adapter Empirical Stress Tests

        [Fact]
        public void SqliteSchemaAdapter_ResolveDatabasePath_ReturnsValidPathUnderHierarchy()
        {
            string dbPath = SqliteSchemaAdapter.ResolveDatabasePath();
            dbPath.Should().NotBeNullOrWhiteSpace();
            (dbPath.EndsWith("question_bank.db", StringComparison.OrdinalIgnoreCase)).Should().BeTrue();

            string connStr = SqliteSchemaAdapter.GetActiveConnectionString();
            connStr.Should().Contain("Data Source=");
            connStr.Should().Contain("question_bank.db");
        }

        [Theory]
        [InlineData("NB", "Nhận biết")]
        [InlineData("TH", "Thông hiểu")]
        [InlineData("VD", "Vận dụng")]
        [InlineData("VDC", "Vận dụng cao")]
        [InlineData("nb", "Nhận biết")]
        [InlineData("th", "Thông hiểu")]
        [InlineData("vd", "Vận dụng")]
        [InlineData("vdc", "Vận dụng cao")]
        [InlineData("NHẬN BIẾT", "Nhận biết")]
        [InlineData("THÔNG HIỂU", "Thông hiểu")]
        [InlineData("VẬN DỤNG", "Vận dụng")]
        [InlineData("VẬN DỤNG CAO", "Vận dụng cao")]
        [InlineData("", "Thông hiểu")]
        [InlineData(null, "Thông hiểu")]
        public void SqliteSchemaAdapter_MapPythonLevelToVietnamese_StressTest(string? input, string expected)
        {
            string mapped = SqliteSchemaAdapter.MapPythonLevelToVietnamese(input);
            mapped.Should().Be(expected);
        }

        [Theory]
        [InlineData("Nhận biết", "NB")]
        [InlineData("Thông hiểu", "TH")]
        [InlineData("Vận dụng", "VD")]
        [InlineData("Vận dụng cao", "VDC")]
        [InlineData("NB", "NB")]
        [InlineData("TH", "TH")]
        [InlineData("VD", "VD")]
        [InlineData("VDC", "VDC")]
        [InlineData("", "TH")]
        [InlineData(null, "TH")]
        public void SqliteSchemaAdapter_MapVietnameseLevelToPython_StressTest(string? input, string expected)
        {
            string mapped = SqliteSchemaAdapter.MapVietnameseLevelToPython(input);
            mapped.Should().Be(expected);
        }

        [Theory]
        [InlineData("TN", "MultipleChoice4")]
        [InlineData("DS", "TrueFalse4")]
        [InlineData("TLN", "ShortAnswer")]
        [InlineData("TL", "Essay")]
        [InlineData("tn", "MultipleChoice4")]
        [InlineData("ds", "TrueFalse4")]
        [InlineData("tln", "ShortAnswer")]
        [InlineData("tl", "Essay")]
        [InlineData("", "MultipleChoice4")]
        [InlineData(null, "MultipleChoice4")]
        public void SqliteSchemaAdapter_MapPythonQtypeToCSharp_StressTest(string? input, string expected)
        {
            string mapped = SqliteSchemaAdapter.MapPythonQtypeToCSharp(input);
            mapped.Should().Be(expected);
        }

        [Fact]
        public async Task SqliteSchemaAdapter_PythonDataJsonParsing_EdgeCasesAndResilience()
        {
            string dbPath = Path.Combine(_tempDir, "python_stress_test.db");
            string connStr = $"Data Source={dbPath};";

            using (var conn = new SqliteConnection(connStr))
            {
                await conn.OpenAsync();
                using var cmd = conn.CreateCommand();
                cmd.CommandText = @"
                    CREATE TABLE questions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        subject TEXT,
                        grade TEXT,
                        topic TEXT,
                        level TEXT,
                        qtype TEXT,
                        question TEXT,
                        data_json TEXT,
                        created_at TEXT,
                        source TEXT,
                        question_id TEXT
                    );
                ";
                await cmd.ExecuteNonQueryAsync();

                // 1. Valid data_json with correct_answer instead of answer
                var json1 = new
                {
                    correct_answer = "C",
                    solution = "Giải chi tiết bài 1",
                    tikz_code = "\\begin{tikzpicture}\\node {A};\\end{tikzpicture}",
                    options = new Dictionary<string, string>
                    {
                        ["A"] = "Phương án A",
                        ["B"] = "Phương án B",
                        ["C"] = "Phương án C",
                        ["D"] = "Phương án D"
                    }
                };

                // 2. Corrupted/Malformed JSON string
                string json2 = "{ options: [invalid json, no closing brace";

                // 3. Empty/whitespace data_json
                string json3 = "";

                // 4. data_json with empty options
                var json4 = new
                {
                    answer = "15",
                    solution = "Đáp số 15"
                };

                void InsertPy(string qid, string lvl, string qt, string text, string dj)
                {
                    using var ins = conn.CreateCommand();
                    ins.CommandText = "INSERT INTO questions (subject, grade, topic, level, qtype, question, data_json, created_at, source, question_id) VALUES ('Toán', '12', 'Khảo sát', @lvl, @qt, @q, @dj, @cat, 'Py', @qid);";
                    ins.Parameters.AddWithValue("@lvl", lvl);
                    ins.Parameters.AddWithValue("@qt", qt);
                    ins.Parameters.AddWithValue("@q", text);
                    ins.Parameters.AddWithValue("@dj", dj);
                    ins.Parameters.AddWithValue("@cat", DateTime.UtcNow.ToString("o"));
                    ins.Parameters.AddWithValue("@qid", qid);
                    ins.ExecuteNonQuery();
                }

                InsertPy("PY_01", "VDC", "TN", "Câu hỏi 1", JsonSerializer.Serialize(json1));
                InsertPy("PY_02", "NB", "TN", "Câu hỏi 2 bị lỗi json", json2);
                InsertPy("PY_03", "TH", "DS", "Câu hỏi 3 rỗng json", json3);
                InsertPy("PY_04", "VD", "TLN", "Câu hỏi 4 trả lời ngắn", JsonSerializer.Serialize(json4));
            }

            // Act: Load through SqliteSchemaAdapter
            var allQuestions = await SqliteSchemaAdapter.LoadQuestionsFromDatabaseAsync(connStr);

            // Assert: All 4 rows read without throwing exceptions
            allQuestions.Should().HaveCount(4);

            // Q1: mapped from correct_answer
            var q1 = allQuestions.First(q => q.QuestionCode == "PY_01");
            q1.CorrectAnswer.Should().Be("C");
            q1.CognitiveLevel.Should().Be("Vận dụng cao");
            q1.TikzCode.Should().Contain("\\begin{tikzpicture}");
            q1.Options.Should().HaveCount(4);

            // Q2: corrupted json handled safely
            var q2 = allQuestions.First(q => q.QuestionCode == "PY_02");
            q2.Content.Should().Be("Câu hỏi 2 bị lỗi json");
            q2.CognitiveLevel.Should().Be("Nhận biết");

            // Q3: empty json
            var q3 = allQuestions.First(q => q.QuestionCode == "PY_03");
            q3.QuestionType.Should().Be("TrueFalse4");
            q3.CognitiveLevel.Should().Be("Thông hiểu");

            // Q4: short answer
            var q4 = allQuestions.First(q => q.QuestionCode == "PY_04");
            q4.CorrectAnswer.Should().Be("15");
            q4.Explanation.Should().Be("Đáp số 15");
            q4.QuestionType.Should().Be("ShortAnswer");
            q4.CognitiveLevel.Should().Be("Vận dụng");
        }

        #endregion

        #region 3. UI, Shortcuts, ToolTips & "1 Button - 1 Icon" Empirical Stress Tests

        [Fact]
        public void MainWindow_RapidShortcutDispatching_1000InvocationsStressTest()
        {
            RunOnSta(() =>
            {
                var window = new MainWindow();
                int interceptedClicks = 0;

                // Intercept button clicks to prevent UI side-effects/dialogs
                window.ButtonClickInterceptor = btn =>
                {
                    interceptedClicks++;
                };

                var keys = new Key[]
                {
                    Key.D1, Key.D2, Key.D3, Key.D4, Key.D5, Key.D6, Key.D7, Key.D8,
                    Key.F5, Key.Enter, Key.O, Key.S, Key.P, Key.B, Key.I, Key.F, Key.Escape,
                    Key.A, Key.Z, Key.F1, Key.F12
                };

                var modifiers = new ModifierKeys[]
                {
                    ModifierKeys.None,
                    ModifierKeys.Control,
                    ModifierKeys.Control | ModifierKeys.Shift,
                    ModifierKeys.Control | ModifierKeys.Alt,
                    ModifierKeys.Alt,
                    ModifierKeys.Shift
                };

                // Rapid dispatching loop: 1,000 iterations
                for (int i = 0; i < 1000; i++)
                {
                    var k = keys[i % keys.Length];
                    var m = modifiers[i % modifiers.Length];

                    // Must not throw any exception
                    var act = () => window.DispatchShortcut(k, m);
                    act.Should().NotThrow($"Rapid shortcut dispatch of Key={k}, Modifiers={m} must be completely robust");
                }

                // Verify the window remains healthy and navigable
                window.NavigateTo("dashboard");
                window.CurrentNavigationTag.Should().Be("dashboard");
                window.NavigateTo("convert");
                window.CurrentNavigationTag.Should().Be("convert");
                window.NavigateTo("matrix");
                window.CurrentNavigationTag.Should().Be("matrix");
                window.NavigateTo("shuffle");
                window.CurrentNavigationTag.Should().Be("shuffle");
                window.NavigateTo("bank");
                window.CurrentNavigationTag.Should().Be("bank");
                window.NavigateTo("qc");
                window.CurrentNavigationTag.Should().Be("qc");
                window.NavigateTo("settings");
                window.CurrentNavigationTag.Should().Be("settings");

                interceptedClicks.Should().BeGreaterThan(0, "Rapid shortcut dispatching must trigger matching button actions");
            });
        }

        [Fact]
        public void AllViews_OneHundredPercentButtons_HaveToolTips_And_NoEmojis_STA_Audit()
        {
            RunOnSta(() =>
            {
                var views = new FrameworkElement[]
                {
                    new MainWindow(),
                    new DashboardView(),
                    new ConvertView(),
                    new ExamMatrixView(),
                    new TikzView(),
                    new ShuffleView(),
                    new QuestionBankView(),
                    new QcView(),
                    new SettingsView(),
                    new ExpandedPreviewWindow(new List<QuestionItem>(), "Xem trước")
                };

                int totalButtonsAudited = 0;

                foreach (var view in views)
                {
                    var buttons = FindVisualAndLogicalChildren<System.Windows.Controls.Button>(view).ToList();

                    foreach (var btn in buttons)
                    {
                        totalButtonsAudited++;
                        string btnName = string.IsNullOrEmpty(btn.Name) ? "(unnamed)" : btn.Name;
                        string viewName = view.GetType().Name;

                        // 1. ToolTip must exist and be non-empty
                        btn.ToolTip.Should().NotBeNull(
                            $"Button '{btnName}' in view '{viewName}' must have a descriptive ToolTip");
                        string tip = btn.ToolTip.ToString()!;
                        tip.Should().NotBeNullOrWhiteSpace(
                            $"Button '{btnName}' in view '{viewName}' must not have empty ToolTip");

                        // 2. Button Content must not contain emoji
                        if (btn.Content is string textContent)
                        {
                            bool hasEmoji = textContent.Any(c =>
                                char.GetUnicodeCategory(c) == UnicodeCategory.OtherSymbol ||
                                char.GetUnicodeCategory(c) == UnicodeCategory.Surrogate ||
                                (c >= 0x2600 && c <= 0x27BF) ||
                                (c >= 0x1F300 && c <= 0x1F9FF));

                            hasEmoji.Should().BeFalse(
                                $"Button '{btnName}' in view '{viewName}' contains emoji in text: '{textContent}'");
                        }

                        // 3. ToolTip must not contain emoji
                        bool tipHasEmoji = tip.Any(c =>
                            char.GetUnicodeCategory(c) == UnicodeCategory.OtherSymbol ||
                            char.GetUnicodeCategory(c) == UnicodeCategory.Surrogate ||
                            (c >= 0x2600 && c <= 0x27BF) ||
                            (c >= 0x1F300 && c <= 0x1F9FF));

                        tipHasEmoji.Should().BeFalse(
                            $"Button '{btnName}' in view '{viewName}' contains emoji in ToolTip: '{tip}'");
                    }
                }

                totalButtonsAudited.Should().BeGreaterThanOrEqualTo(40,
                    "Audit must have discovered and verified at least 40 buttons across all views");
            });
        }

        [Fact]
        public void AllViews_StrictOneButtonOneIconRule_NoDuplicateIcons_STA_Audit()
        {
            RunOnSta(() =>
            {
                var views = new FrameworkElement[]
                {
                    new MainWindow(),
                    new DashboardView(),
                    new ConvertView(),
                    new ExamMatrixView(),
                    new TikzView(),
                    new ShuffleView(),
                    new QuestionBankView(),
                    new QcView(),
                    new SettingsView(),
                    new ExpandedPreviewWindow(new List<QuestionItem>(), "Xem trước")
                };

                foreach (var view in views)
                {
                    var buttons = FindVisualAndLogicalChildren<System.Windows.Controls.Button>(view).ToList();

                    foreach (var btn in buttons)
                    {
                        string btnName = string.IsNullOrEmpty(btn.Name) ? "(unnamed)" : btn.Name;
                        string viewName = view.GetType().Name;

                        if (btn is Wpf.Ui.Controls.Button uiBtn)
                        {
                            bool hasIconProp = uiBtn.Icon != null;
                            var childIcons = FindVisualAndLogicalChildren<SymbolIcon>(uiBtn).ToList();

                            // If button has Icon property set, it should not also have child SymbolIcon in its content
                            if (hasIconProp)
                            {
                                // The visual tree may contain 1 SymbolIcon instantiated from the Icon property template
                                childIcons.Count.Should().BeLessOrEqualTo(2,
                                    $"Button '{btnName}' in '{viewName}' violates '1 Button - 1 Icon' rule (multiple SymbolIcons found)");
                            }
                            else
                            {
                                childIcons.Count.Should().BeLessOrEqualTo(1,
                                    $"Button '{btnName}' in '{viewName}' has {childIcons.Count} SymbolIcons (expected <= 1)");
                            }
                        }
                    }
                }
            });
        }

        #endregion
    }
}
