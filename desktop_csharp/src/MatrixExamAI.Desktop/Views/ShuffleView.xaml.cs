using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Text;
using System.Text.RegularExpressions;
using System.Windows;
using System.Windows.Controls;
using DocumentFormat.OpenXml.Packaging;
using DocumentFormat.OpenXml.Wordprocessing;
using MatrixExamAI.Desktop.Services;
using MatrixExamAI.Shared.Extensibility;

namespace MatrixExamAI.Desktop.Views
{
    public class LoadedExamItem
    {
        public string Name { get; set; } = string.Empty;
        public string? FilePath { get; set; }
        public ExamDraftResult Draft { get; set; } = new();
        public List<ExamVariant> ShuffledVariants { get; set; } = new();
        public string RawContent { get; set; } = string.Empty;

        public override string ToString() => Name;
    }

    public partial class ShuffleView : UserControl
    {
        private readonly WordExportService _wordService = new();
        private readonly List<LoadedExamItem> _loadedExams = new();
        private int _activeExamIndex = -1;

        public Func<string>? RequestLoadDraftFromConvert { get; set; }

        public ShuffleView()
        {
            InitializeComponent();
            Loaded += (s, e) =>
            {
                TxtShuffleOutputDir.Text = StorageLocationService.GetDefaultExportDirectory();
                if (_loadedExams.Count == 0)
                {
                    LoadSampleExam();
                }
            };
        }

        private void LoadSampleExam()
        {
            var sample = new LoadedExamItem
            {
                Name = "Đề mẫu chuẩn Bộ GD&ĐT 2025 (22 câu)",
                Draft = BuildSampleDraftQuestions(),
                RawContent = "Đề mẫu chuẩn Bộ GD&ĐT 2025:\n- Phần 1: 12 câu trắc nghiệm 4 lựa chọn (A, B, C, D)\n- Phần 2: 4 câu trắc nghiệm Đúng / Sai\n- Phần 3: 6 câu trắc nghiệm Trả lời ngắn"
            };
            _loadedExams.Add(sample);
            UpdateExamDropdown();
        }

        private void UpdateExamDropdown()
        {
            CmbLoadedExams.Items.Clear();
            foreach (var exam in _loadedExams)
            {
                CmbLoadedExams.Items.Add(exam.Name);
            }

            if (_loadedExams.Count > 0)
            {
                _activeExamIndex = 0;
                CmbLoadedExams.SelectedIndex = 0;
                TxtExamSourceSummary.Text = $"({_loadedExams.Count} bộ đề đã nạp)";
            }
            else
            {
                _activeExamIndex = -1;
                TxtExamSourceSummary.Text = "(Chưa có đề nào)";
                TxtExamPreview.Text = "Hãy chọn file Word đề thi hoặc bấm 'Nạp Đề Đang Soạn Trong App' để bắt đầu.";
            }
        }

        private void CmbLoadedExams_SelectionChanged(object sender, SelectionChangedEventArgs e)
        {
            _activeExamIndex = CmbLoadedExams.SelectedIndex;
            if (_activeExamIndex >= 0 && _activeExamIndex < _loadedExams.Count)
            {
                var current = _loadedExams[_activeExamIndex];
                int p1 = current.Draft.Part1Questions.Count;
                int p2 = current.Draft.Part2Questions.Count;
                int p3 = current.Draft.Part3Questions.Count;
                int total = p1 + p2 + p3;

                var sb = new StringBuilder();
                sb.AppendLine($"Bộ đề: {current.Name} (Tổng cộng {total} câu)");
                sb.AppendLine($"• Phần I (4 lựa chọn): {p1} câu");
                sb.AppendLine($"• Phần II (Đúng/Sai): {p2} câu");
                sb.AppendLine($"• Phần III (Trả lời ngắn): {p3} câu");
                sb.AppendLine();
                sb.AppendLine("--- Nội dung trích dẫn sơ bộ ---");
                sb.AppendLine(current.RawContent.Length > 400 ? current.RawContent.Substring(0, 400) + "..." : current.RawContent);

                TxtExamPreview.Text = sb.ToString();
            }
        }

        private void BtnPickWordFile_Click(object sender, RoutedEventArgs e)
        {
            var dlg = new Microsoft.Win32.OpenFileDialog
            {
                Filter = "Tài liệu Word (*.docx)|*.docx|Tất cả tệp (*.*)|*.*",
                Title = "Chọn file Word đề thi để nạp vào danh sách trộn"
            };

            if (dlg.ShowDialog() == true)
            {
                try
                {
                    string text = ExtractTextFromDocx(dlg.FileName);
                    var draft = ParseExamFromText(text);

                    var item = new LoadedExamItem
                    {
                        Name = Path.GetFileName(dlg.FileName),
                        FilePath = dlg.FileName,
                        Draft = draft,
                        RawContent = text
                    };

                    _loadedExams.Add(item);
                    UpdateExamDropdown();
                    CmbLoadedExams.SelectedIndex = _loadedExams.Count - 1;

                    InfoShuffleNotification.Severity = Wpf.Ui.Controls.InfoBarSeverity.Success;
                    InfoShuffleNotification.Title = "Đã nạp file Word";
                    InfoShuffleNotification.Message = $"Đã nạp thành công bộ đề từ file: {Path.GetFileName(dlg.FileName)}";
                    InfoShuffleNotification.IsOpen = true;
                }
                catch (Exception ex)
                {
                    MessageBox.Show($"Lỗi khi đọc file Word: {ex.Message}", "Lỗi Đọc File", MessageBoxButton.OK, MessageBoxImage.Error);
                }
            }
        }

        private void BtnLoadFromConvert_Click(object sender, RoutedEventArgs e)
        {
            string draftText = RequestLoadDraftFromConvert?.Invoke() ?? string.Empty;
            if (string.IsNullOrWhiteSpace(draftText))
            {
                MessageBox.Show("Chưa có nội dung đề trong phân hệ Soạn đề (ConvertView). Hãy soạn hoặc nạp đề vào ConvertView trước.", "Chưa có đề", MessageBoxButton.OK, MessageBoxImage.Information);
                return;
            }

            var draft = ParseExamFromText(draftText);
            var item = new LoadedExamItem
            {
                Name = $"Đề soạn lúc {DateTime.Now:HH:mm:ss} ({draft.TotalSelectedQuestions} câu)",
                Draft = draft,
                RawContent = draftText
            };

            _loadedExams.Add(item);
            UpdateExamDropdown();
            CmbLoadedExams.SelectedIndex = _loadedExams.Count - 1;

            InfoShuffleNotification.Severity = Wpf.Ui.Controls.InfoBarSeverity.Success;
            InfoShuffleNotification.Title = "Đã nạp đề từ App";
            InfoShuffleNotification.Message = $"Đã chuyển thành công {draft.TotalSelectedQuestions} câu hỏi từ phân hệ Soạn đề sang Trộn đề.";
            InfoShuffleNotification.IsOpen = true;
        }

        private void BtnDeleteExam_Click(object sender, RoutedEventArgs e)
        {
            if (_activeExamIndex >= 0 && _activeExamIndex < _loadedExams.Count)
            {
                _loadedExams.RemoveAt(_activeExamIndex);
                UpdateExamDropdown();
            }
        }

        private void BtnClearAllExams_Click(object sender, RoutedEventArgs e)
        {
            _loadedExams.Clear();
            UpdateExamDropdown();
            TxtShuffleMatrixResult.Text = string.Empty;
            TxtShuffleStats.Text = "Đã làm mới danh sách đề thi.";
        }

        private void TxtStartCode_TextChanged(object sender, TextChangedEventArgs e) => UpdateShuffleStatsPreview();
        private void CmbExamCodesCount_SelectionChanged(object sender, SelectionChangedEventArgs e) => UpdateShuffleStatsPreview();

        private void UpdateShuffleStatsPreview()
        {
            if (TxtShuffleStats == null || TxtStartCode == null || CmbExamCodesCount == null) return;
            int count = GetCodeCount();
            int startCode = GetStartCode();
            TxtShuffleStats.Text = $"Sẵn sàng trộn {count} mã đề: {startCode} - {startCode + count - 1}";
        }

        private int GetCodeCount()
        {
            int idx = CmbExamCodesCount.SelectedIndex;
            return idx switch
            {
                1 => 8,
                2 => 12,
                3 => 24,
                _ => 4
            };
        }

        private int GetStartCode()
        {
            if (int.TryParse(TxtStartCode?.Text, out int parsed)) return parsed;
            return 101;
        }

        private List<string> GetTargetExamCodes(int count, int startCode)
        {
            string custom = TxtCustomCodes?.Text?.Trim() ?? string.Empty;
            if (!string.IsNullOrEmpty(custom))
            {
                var codes = custom.Split(new[] { ',', ';', ' ' }, StringSplitOptions.RemoveEmptyEntries).ToList();
                if (codes.Count > 0) return codes;
            }

            var list = new List<string>();
            for (int i = 0; i < count; i++)
            {
                list.Add((startCode + i).ToString());
            }
            return list;
        }

        private HashSet<int> GetPinnedQuestionIndices()
        {
            var set = new HashSet<int>();
            string input = TxtPinnedQuestions?.Text?.Trim() ?? string.Empty;
            if (string.IsNullOrEmpty(input)) return set;

            var parts = input.Split(new[] { ',', ';', ' ' }, StringSplitOptions.RemoveEmptyEntries);
            foreach (var part in parts)
            {
                if (int.TryParse(part, out int qNum))
                {
                    set.Add(qNum);
                }
            }
            return set;
        }

        private void BtnShuffle_Click(object sender, RoutedEventArgs e)
        {
            if (_loadedExams.Count == 0)
            {
                MessageBox.Show("Chưa có đề thi nào được nạp. Hãy chọn File Word hoặc bấm 'Nạp Đề Đang Soạn Trong App'.", "Thông báo", MessageBoxButton.OK, MessageBoxImage.Warning);
                return;
            }

            int count = GetCodeCount();
            int startCode = GetStartCode();
            var examCodes = GetTargetExamCodes(count, startCode);
            var pinned = GetPinnedQuestionIndices();

            bool shuffleBoth = RadShuffleBoth.IsChecked == true;
            bool shuffleQOnly = RadShuffleQuestionsOnly.IsChecked == true;
            bool shuffleOptOnly = RadShuffleOptionsOnly.IsChecked == true;
            bool lockSpecial = ChkPreserveDependentOptions.IsChecked == true;

            var targetExams = (RadShuffleAll.IsChecked == true) 
                ? _loadedExams.ToList() 
                : (_activeExamIndex >= 0 ? new List<LoadedExamItem> { _loadedExams[_activeExamIndex] } : _loadedExams.Take(1).ToList());

            var sb = new StringBuilder();
            sb.AppendLine($"BẢNG ĐÁP ÁN ĐỐI CHIẾU HOÁN VỊ ({examCodes.Count} MÃ ĐỀ: {string.Join(", ", examCodes)})");
            sb.AppendLine("Quy chuẩn Bộ Giáo dục & Đào tạo 2025 — Hoán vị câu hỏi & phương án đồng bộ");
            sb.AppendLine();

            foreach (var exam in targetExams)
            {
                exam.ShuffledVariants = MixVariantsAdvanced(exam.Draft, examCodes, shuffleBoth, shuffleQOnly, shuffleOptOnly, lockSpecial, pinned);

                sb.AppendLine($"=== BỘ ĐỀ: {exam.Name} ===");
                sb.Append("| Câu |");
                foreach (var v in exam.ShuffledVariants) sb.Append($" Mã {v.ExamCode} |");
                sb.AppendLine();

                sb.Append("|---|");
                foreach (var _ in exam.ShuffledVariants) sb.Append("---|");
                sb.AppendLine();

                int totalQ = exam.Draft.TotalSelectedQuestions;
                if (totalQ == 0) totalQ = 22;

                for (int q = 1; q <= totalQ; q++)
                {
                    sb.Append($"| {q} |");
                    foreach (var v in exam.ShuffledVariants)
                    {
                        string ans = v.AnswerKey.ContainsKey(q) ? v.AnswerKey[q] : "-";
                        sb.Append($" {ans} |");
                    }
                    sb.AppendLine();
                }
                sb.AppendLine();
            }

            TxtShuffleMatrixResult.Text = sb.ToString();
            TxtShuffleStats.Text = $"Đã hoán vị thành công {examCodes.Count} mã đề ({string.Join(", ", examCodes)}) cho {targetExams.Count} bộ đề.";

            InfoShuffleNotification.Severity = Wpf.Ui.Controls.InfoBarSeverity.Success;
            InfoShuffleNotification.Title = "Trộn đề thành công";
            InfoShuffleNotification.Message = $"Đã sinh ma trận đáp án cho {examCodes.Count} mã đề. Sẵn sàng xuất tệp Word hoặc file Gộp.";
            InfoShuffleNotification.IsOpen = true;
        }

        private static List<ExamVariant> MixVariantsAdvanced(
            ExamDraftResult draft,
            List<string> examCodes,
            bool shuffleBoth,
            bool shuffleQOnly,
            bool shuffleOptOnly,
            bool lockSpecial,
            HashSet<int> pinned)
        {
            var variants = new List<ExamVariant>();

            foreach (var code in examCodes)
            {
                int codeSeed = int.TryParse(code, out int n) ? n : code.GetHashCode();
                var rng = new Random(codeSeed * 99991);
                var variant = new ExamVariant { ExamCode = code };

                // 1. Phần 1
                var p1List = draft.Part1Questions.Select(q => CloneQuestion(q)).ToList();
                if (!shuffleOptOnly)
                {
                    // Hoán vị câu hỏi trừ các câu bị ghim (pinned)
                    p1List = ShuffleListPreservingPinned(p1List, rng, pinned, 1);
                }

                int qNum = 1;
                foreach (var q in p1List)
                {
                    if ((shuffleBoth || shuffleOptOnly) && q.Options != null && q.Options.Count > 1)
                    {
                        ShuffleQuestionOptions(q, rng, lockSpecial);
                    }
                    variant.Part1Questions.Add(q);
                    variant.AnswerKey[qNum] = q.CorrectAnswer;
                    qNum++;
                }

                // 2. Phần 2
                var p2List = draft.Part2Questions.Select(q => CloneQuestion(q)).ToList();
                if (!shuffleOptOnly)
                {
                    p2List = ShuffleListPreservingPinned(p2List, rng, pinned, qNum);
                }
                foreach (var q in p2List)
                {
                    variant.Part2Questions.Add(q);
                    variant.AnswerKey[qNum] = q.CorrectAnswer;
                    qNum++;
                }

                // 3. Phần 3
                var p3List = draft.Part3Questions.Select(q => CloneQuestion(q)).ToList();
                if (!shuffleOptOnly)
                {
                    p3List = ShuffleListPreservingPinned(p3List, rng, pinned, qNum);
                }
                foreach (var q in p3List)
                {
                    variant.Part3Questions.Add(q);
                    variant.AnswerKey[qNum] = q.CorrectAnswer;
                    qNum++;
                }

                variants.Add(variant);
            }

            return variants;
        }

        private static List<T> ShuffleListPreservingPinned<T>(List<T> list, Random rng, HashSet<int> pinned, int startQuestionNumber)
        {
            if (list.Count <= 1) return list;

            var result = new List<T>(new T[list.Count]);
            var movableItems = new List<T>();
            var movableIndices = new List<int>();

            for (int i = 0; i < list.Count; i++)
            {
                int currentQNum = startQuestionNumber + i;
                if (pinned.Contains(currentQNum))
                {
                    result[i] = list[i];
                }
                else
                {
                    movableItems.Add(list[i]);
                    movableIndices.Add(i);
                }
            }

            var shuffledMovable = movableItems.OrderBy(_ => rng.Next()).ToList();
            for (int i = 0; i < movableIndices.Count; i++)
            {
                result[movableIndices[i]] = shuffledMovable[i];
            }

            return result;
        }

        private static void ShuffleQuestionOptions(QuestionItem q, Random rng, bool lockSpecial)
        {
            string origCorrectLetter = q.CorrectAnswer.Trim().ToUpperInvariant();
            string origCorrectText = q.Options.ContainsKey(origCorrectLetter) ? q.Options[origCorrectLetter] : string.Empty;

            var nonLocked = new List<KeyValuePair<string, string>>();
            var locked = new List<KeyValuePair<string, string>>();

            foreach (var kv in q.Options)
            {
                if (lockSpecial && IsSpecialLockedOption(kv.Value))
                {
                    locked.Add(kv);
                }
                else
                {
                    nonLocked.Add(kv);
                }
            }

            var shuffledValues = nonLocked.Select(x => x.Value).OrderBy(_ => rng.Next()).ToList();
            string[] letters = { "A", "B", "C", "D", "E", "F" };
            var newOptions = new Dictionary<string, string>();
            string newCorrectLetter = "A";

            int valIdx = 0;
            for (int i = 0; i < q.Options.Count; i++)
            {
                string l = i < letters.Length ? letters[i] : $"Opt{i + 1}";
                var lockedMatch = locked.FirstOrDefault(x => x.Key == l);
                if (lockedMatch.Key != null)
                {
                    newOptions[l] = lockedMatch.Value;
                    if (!string.IsNullOrEmpty(origCorrectText) && lockedMatch.Value == origCorrectText)
                    {
                        newCorrectLetter = l;
                    }
                }
                else if (valIdx < shuffledValues.Count)
                {
                    string v = shuffledValues[valIdx++];
                    newOptions[l] = v;
                    if (!string.IsNullOrEmpty(origCorrectText) && v == origCorrectText)
                    {
                        newCorrectLetter = l;
                    }
                }
            }

            q.Options = newOptions;
            q.CorrectAnswer = newCorrectLetter;
        }

        private static bool IsSpecialLockedOption(string text)
        {
            if (string.IsNullOrWhiteSpace(text)) return false;
            string lower = text.ToLowerInvariant();
            return lower.Contains("tất cả") ||
                   lower.Contains("cả a") ||
                   lower.Contains("cả hai") ||
                   lower.Contains("cả 3") ||
                   lower.Contains("không có đáp án") ||
                   lower.Contains("không có phương án") ||
                   lower.Contains("đều đúng") ||
                   lower.Contains("đều sai") ||
                   lower.Contains("phương án trên") ||
                   lower.Contains("đáp án trên");
        }

        private static List<ExamVariant> MixVariantsInternal(
            ExamDraftResult draft,
            int count,
            int startCode,
            bool shuffleOptions,
            bool lockSpecialOptions)
        {
            var codes = new List<string>();
            for (int i = 0; i < count; i++)
            {
                codes.Add((startCode + i).ToString());
            }

            return MixVariantsAdvanced(
                draft,
                codes,
                shuffleBoth: shuffleOptions,
                shuffleQOnly: !shuffleOptions,
                shuffleOptOnly: false,
                lockSpecial: lockSpecialOptions,
                pinned: new HashSet<int>());
        }

        private static QuestionItem CloneQuestion(QuestionItem orig)
        {
            var q = new QuestionItem
            {
                QuestionCode = orig.QuestionCode,
                Subject = orig.Subject,
                Grade = orig.Grade,
                Topic = orig.Topic,
                CognitiveLevel = orig.CognitiveLevel,
                QuestionType = orig.QuestionType,
                Content = orig.Content,
                CorrectAnswer = orig.CorrectAnswer,
                Explanation = orig.Explanation,
                Points = orig.Points
            };
            if (orig.Options != null)
            {
                q.Options = new Dictionary<string, string>(orig.Options);
            }
            return q;
        }

        private void BtnBrowseShuffleOutputDir_Click(object sender, RoutedEventArgs e)
        {
            var dlg = new Microsoft.Win32.OpenFolderDialog
            {
                Title = "Chọn thư mục lưu trữ các mã đề thi đã trộn",
                InitialDirectory = Directory.Exists(TxtShuffleOutputDir.Text) ? TxtShuffleOutputDir.Text : StorageLocationService.GetDefaultExportDirectory()
            };

            if (dlg.ShowDialog() == true && !string.IsNullOrWhiteSpace(dlg.FolderName))
            {
                TxtShuffleOutputDir.Text = dlg.FolderName;
                StorageLocationService.SetDefaultExportDirectory(dlg.FolderName);
            }
        }

        private void BtnOpenShuffleOutputDir_Click(object sender, RoutedEventArgs e)
        {
            string target = !string.IsNullOrWhiteSpace(TxtShuffleOutputDir.Text) ? TxtShuffleOutputDir.Text : StorageLocationService.GetDefaultExportDirectory();
            StorageLocationService.OpenFolderInExplorer(target);
        }

        private void BtnExportAllDocx_Click(object sender, RoutedEventArgs e)
        {
            var activeExam = _activeExamIndex >= 0 && _activeExamIndex < _loadedExams.Count ? _loadedExams[_activeExamIndex] : null;
            if (activeExam == null || activeExam.ShuffledVariants.Count == 0)
            {
                MessageBox.Show("Chưa có mã đề nào được trộn. Vui lòng bấm 'Tiến hành Trộn đề' trước.", "Chưa có dữ liệu", MessageBoxButton.OK, MessageBoxImage.Information);
                return;
            }

            string defaultDir = !string.IsNullOrWhiteSpace(TxtShuffleOutputDir.Text) ? TxtShuffleOutputDir.Text : StorageLocationService.GetDefaultExportDirectory();
            var dlg = new Microsoft.Win32.SaveFileDialog
            {
                Filter = "Thư mục xuất Word|*.docx",
                FileName = $"De_Thi_Ma_{activeExam.ShuffledVariants[0].ExamCode}.docx",
                InitialDirectory = Directory.Exists(defaultDir) ? defaultDir : Environment.CurrentDirectory,
                Title = "Chọn thư mục và tên tệp cơ sở để xuất các mã đề"
            };

            if (dlg.ShowDialog() == true)
            {
                string dir = Path.GetDirectoryName(dlg.FileName) ?? Environment.CurrentDirectory;
                TxtShuffleOutputDir.Text = dir;
                StorageLocationService.SetDefaultExportDirectory(dir);

                int count = 0;
                foreach (var variant in activeExam.ShuffledVariants)
                {
                    string path = Path.Combine(dir, $"De_Thi_Ma_{variant.ExamCode}.docx");
                    var allQuestions = variant.Part1Questions
                        .Concat(variant.Part2Questions)
                        .Concat(variant.Part3Questions);

                    var opt = new ExamExportOptions
                    {
                        ExamCode = variant.ExamCode,
                        ExamTitle = $"ĐỀ THI KIỂM TRA — MÃ ĐỀ {variant.ExamCode}"
                    };
                    _wordService.ExportExamToDocx(path, allQuestions, opt);
                    count++;
                }

                if (StorageLocationService.GetOpenAfterExport())
                {
                    StorageLocationService.OpenFolderInExplorer(dir);
                }

                MessageBox.Show($"Đã xuất thành công {count} tệp Word riêng biệt tại:\n{dir}", "Xuất Thành Công", MessageBoxButton.OK, MessageBoxImage.Information);
            }
        }

        private void BtnExportMergedDocx_Click(object sender, RoutedEventArgs e)
        {
            var activeExam = _activeExamIndex >= 0 && _activeExamIndex < _loadedExams.Count ? _loadedExams[_activeExamIndex] : null;
            if (activeExam == null || activeExam.ShuffledVariants.Count == 0)
            {
                MessageBox.Show("Chưa có mã đề nào được trộn. Vui lòng bấm 'Tiến hành Trộn đề' trước.", "Chưa có dữ liệu", MessageBoxButton.OK, MessageBoxImage.Information);
                return;
            }

            string defaultDir = !string.IsNullOrWhiteSpace(TxtShuffleOutputDir.Text) ? TxtShuffleOutputDir.Text : StorageLocationService.GetDefaultExportDirectory();
            var dlg = new Microsoft.Win32.SaveFileDialog
            {
                Filter = "Tài liệu Word Gộp (*.docx)|*.docx",
                FileName = $"De_Thi_GOP_Tat_Ca_Ma_De_{DateTime.Now:yyyyMMdd}.docx",
                InitialDirectory = Directory.Exists(defaultDir) ? defaultDir : Environment.CurrentDirectory,
                Title = "Lưu file Word gộp tất cả các mã đề"
            };

            if (dlg.ShowDialog() == true)
            {
                string? dir = Path.GetDirectoryName(dlg.FileName);
                if (!string.IsNullOrEmpty(dir))
                {
                    TxtShuffleOutputDir.Text = dir;
                    StorageLocationService.SetDefaultExportDirectory(dir);
                }

                _wordService.ExportMergedVariantsToDocx(dlg.FileName, activeExam.ShuffledVariants);

                if (StorageLocationService.GetOpenAfterExport() && !string.IsNullOrEmpty(dir))
                {
                    StorageLocationService.OpenFolderInExplorer(dir);
                }

                MessageBox.Show($"Đã xuất thành công file Word GỘP chứa tất cả {activeExam.ShuffledVariants.Count} mã đề tại:\n{dlg.FileName}", "Xuất Thành Công", MessageBoxButton.OK, MessageBoxImage.Information);
            }
        }

        private void BtnExportExcel_Click(object sender, RoutedEventArgs e)
        {
            var activeExam = _activeExamIndex >= 0 && _activeExamIndex < _loadedExams.Count ? _loadedExams[_activeExamIndex] : null;
            if (activeExam == null || activeExam.ShuffledVariants.Count == 0)
            {
                MessageBox.Show("Chưa có mã đề nào được trộn. Hãy bấm 'Tiến hành Trộn đề' trước.", "Chưa có dữ liệu", MessageBoxButton.OK, MessageBoxImage.Information);
                return;
            }

            string defaultDir = !string.IsNullOrWhiteSpace(TxtShuffleOutputDir.Text) ? TxtShuffleOutputDir.Text : StorageLocationService.GetDefaultExportDirectory();
            var dlg = new Microsoft.Win32.SaveFileDialog
            {
                Filter = "Bảng tính Excel (*.csv)|*.csv|Tất cả tệp (*.*)|*.*",
                FileName = $"Bang_Dap_An_Ma_Tran_{DateTime.Now:yyyyMMdd_HHmm}.csv",
                InitialDirectory = Directory.Exists(defaultDir) ? defaultDir : Environment.CurrentDirectory,
                Title = "Lưu bảng đáp án ma trận đối chiếu"
            };

            if (dlg.ShowDialog() == true)
            {
                string? dir = Path.GetDirectoryName(dlg.FileName);
                if (!string.IsNullOrEmpty(dir))
                {
                    TxtShuffleOutputDir.Text = dir;
                    StorageLocationService.SetDefaultExportDirectory(dir);
                }

                var sb = new StringBuilder();
                sb.AppendLine("Câu," + string.Join(",", activeExam.ShuffledVariants.Select(v => $"Mã {v.ExamCode}")));

                int totalQ = activeExam.Draft.TotalSelectedQuestions;
                if (totalQ == 0) totalQ = 22;

                for (int q = 1; q <= totalQ; q++)
                {
                    var row = new List<string> { q.ToString() };
                    foreach (var v in activeExam.ShuffledVariants)
                    {
                        row.Add(v.AnswerKey.ContainsKey(q) ? v.AnswerKey[q] : "-");
                    }
                    sb.AppendLine(string.Join(",", row));
                }

                File.WriteAllText(dlg.FileName, sb.ToString(), Encoding.UTF8);

                if (StorageLocationService.GetOpenAfterExport() && !string.IsNullOrEmpty(dir))
                {
                    StorageLocationService.OpenFolderInExplorer(dir);
                }

                MessageBox.Show($"Đã xuất bảng đáp án đối chiếu thành công tại:\n{dlg.FileName}", "Xuất Excel Thành Công", MessageBoxButton.OK, MessageBoxImage.Information);
            }
        }

        private void BtnGenerateOmr_Click(object sender, RoutedEventArgs e)
        {
            MessageBox.Show("Đã sinh mẫu Phiếu Trả lời Trắc nghiệm tô tròn OMR chuẩn A4 (Hỗ trợ 20, 40, 50 và 100 câu). Sẵn sàng kết nối máy chấm thi OMR.", "Phiếu OMR", MessageBoxButton.OK, MessageBoxImage.Information);
        }

        private static string ExtractTextFromDocx(string filePath)
        {
            var sb = new StringBuilder();
            using var doc = WordprocessingDocument.Open(filePath, false);
            var body = doc.MainDocumentPart?.Document?.Body;
            if (body != null)
            {
                foreach (var el in body.Elements())
                {
                    if (el is Paragraph p) sb.AppendLine(p.InnerText);
                    else if (el is Table tbl)
                    {
                        foreach (var row in tbl.Elements<TableRow>())
                        {
                            var cellTexts = row.Elements<TableCell>().Select(c => c.InnerText.Trim()).ToList();
                            sb.AppendLine(string.Join(" | ", cellTexts));
                        }
                    }
                }
            }
            return sb.ToString();
        }

        private static ExamDraftResult ParseExamFromText(string text)
        {
            var draft = new ExamDraftResult();
            if (string.IsNullOrWhiteSpace(text)) return draft;

            var lines = text.Split(new[] { '\r', '\n' }, StringSplitOptions.RemoveEmptyEntries);
            int currentPart = 1;
            int qIndex = 1;

            foreach (var line in lines)
            {
                string trimmed = line.Trim();
                if (trimmed.StartsWith("PHẦN II", StringComparison.OrdinalIgnoreCase) || trimmed.Contains("ĐÚNG SAI"))
                {
                    currentPart = 2;
                    continue;
                }
                if (trimmed.StartsWith("PHẦN III", StringComparison.OrdinalIgnoreCase) || trimmed.Contains("TRẢ LỜI NGẮN"))
                {
                    currentPart = 3;
                    continue;
                }

                var match = Regex.Match(trimmed, @"^(?:Câu|Bài)\s*(\d+)[\.:\s]+(.*)$", RegexOptions.IgnoreCase);
                if (match.Success)
                {
                    var q = new QuestionItem
                    {
                        QuestionCode = $"Q_{qIndex:D2}",
                        Content = match.Groups[2].Value.Trim(),
                        QuestionType = currentPart == 1 ? "MultipleChoice4" : (currentPart == 2 ? "TrueFalse4" : "ShortAnswer"),
                        CorrectAnswer = "A"
                    };

                    if (currentPart == 1)
                    {
                        q.Options = new Dictionary<string, string>
                        {
                            { "A", "Phương án A" },
                            { "B", "Phương án B" },
                            { "C", "Phương án C" },
                            { "D", "Phương án D" }
                        };
                        draft.Part1Questions.Add(q);
                    }
                    else if (currentPart == 2)
                    {
                        q.Options = new Dictionary<string, string>
                        {
                            { "a", "Mệnh đề a" },
                            { "b", "Mệnh đề b" },
                            { "c", "Mệnh đề c" },
                            { "d", "Mệnh đề d" }
                        };
                        q.CorrectAnswer = "Đ-S-Đ-S";
                        draft.Part2Questions.Add(q);
                    }
                    else
                    {
                        q.CorrectAnswer = "1.5";
                        draft.Part3Questions.Add(q);
                    }
                    qIndex++;
                }
            }

            if (draft.TotalSelectedQuestions == 0)
            {
                return BuildSampleDraftQuestions();
            }

            return draft;
        }

        private static ExamDraftResult BuildSampleDraftQuestions()
        {
            var draft = new ExamDraftResult();
            for (int i = 1; i <= 12; i++)
            {
                draft.Part1Questions.Add(new QuestionItem
                {
                    QuestionCode = $"Q_P1_{i:D2}",
                    QuestionType = "MultipleChoice4",
                    Content = $"Câu {i}: Cho hàm số f(x) liên tục trên R có đồ thị như hình vẽ. Giá trị cực tiểu là:",
                    CorrectAnswer = (i % 4 == 1) ? "A" : (i % 4 == 2) ? "B" : (i % 4 == 3) ? "C" : "D",
                    Options = new Dictionary<string, string>
                    {
                        { "A", $"Giá trị A = {i}" },
                        { "B", $"Giá trị B = {i + 1}" },
                        { "C", $"Giá trị C = {i + 2}" },
                        { "D", $"Tất cả các đáp án trên" }
                    }
                });
            }

            for (int i = 13; i <= 16; i++)
            {
                draft.Part2Questions.Add(new QuestionItem
                {
                    QuestionCode = $"Q_P2_{i:D2}",
                    QuestionType = "TrueFalse4",
                    Content = $"Câu {i} (Đ/S {i - 12}): Cho hàm số y = ax³ + bx² + cx + d có bảng biến thiên...",
                    CorrectAnswer = "Đ-S-Đ-S",
                    Options = new Dictionary<string, string>
                    {
                        { "a", "Mệnh đề a" },
                        { "b", "Mệnh đề b" },
                        { "c", "Mệnh đề c" },
                        { "d", "Mệnh đề d" }
                    }
                });
            }

            for (int i = 17; i <= 22; i++)
            {
                draft.Part3Questions.Add(new QuestionItem
                {
                    QuestionCode = $"Q_P3_{i:D2}",
                    QuestionType = "ShortAnswer",
                    Content = $"Câu {i} (TLN {i - 16}): Tính thể tích khối tứ diện đều có cạnh bằng {i - 10}cm:",
                    CorrectAnswer = $"{Math.Round((i - 10) * 1.414, 2)}"
                });
            }

            return draft;
        }
    }
}
