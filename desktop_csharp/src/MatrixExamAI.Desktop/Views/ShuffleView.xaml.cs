using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Text;
using System.Text.RegularExpressions;
using System.Windows;
using System.Windows.Controls;
using MatrixExamAI.Desktop.Services;
using MatrixExamAI.Shared.Extensibility;

namespace MatrixExamAI.Desktop.Views
{
    public partial class ShuffleView : UserControl
    {
        private readonly WordExportService _wordService = new WordExportService();
        private List<ExamVariant> _currentVariants = new List<ExamVariant>();
        private ExamDraftResult _baseDraft = new ExamDraftResult();

        public ShuffleView()
        {
            InitializeComponent();
            LoadDefaultSample();
        }

        private void LoadDefaultSample()
        {
            _baseDraft = BuildBaseDraftQuestions();
            GenerateAndDisplayShuffleVariants(4, 101, true, true);
        }

        private void BtnShuffle_Click(object sender, RoutedEventArgs e)
        {
            int startCode = 101;
            if (int.TryParse(TxtStartCode.Text, out int parsed))
            {
                startCode = parsed;
            }

            int count = 4;
            if (CmbExamCodesCount.SelectedIndex == 1) count = 8;
            else if (CmbExamCodesCount.SelectedIndex == 2) count = 12;
            else if (CmbExamCodesCount.SelectedIndex == 3) count = 24;

            bool shuffleOptions = ChkShuffleOptions.IsChecked ?? true;
            bool lockSpecialOptions = ChkPreserveAllAbove.IsChecked ?? true;

            GenerateAndDisplayShuffleVariants(count, startCode, shuffleOptions, lockSpecialOptions);
        }

        private void GenerateAndDisplayShuffleVariants(int count, int startCode, bool shuffleOptions, bool lockSpecialOptions)
        {
            if (_baseDraft == null || _baseDraft.TotalSelectedQuestions == 0)
            {
                _baseDraft = BuildBaseDraftQuestions();
            }

            _currentVariants = MixVariantsInternal(_baseDraft, count, startCode, shuffleOptions, lockSpecialOptions);

            var sb = new StringBuilder();
            sb.AppendLine($"BẢNG ĐÁP ÁN ĐỐI CHIẾU HOÁN VỊ ({count} MÃ ĐỀ: {startCode} - {startCode + count - 1})");
            sb.AppendLine("Quy chuẩn Bộ Giáo dục & Đào tạo — Hoán vị câu hỏi & phương án đồng bộ");
            sb.AppendLine();

            // Header row
            sb.Append("| Câu |");
            foreach (var variant in _currentVariants)
            {
                sb.Append($" Mã {variant.ExamCode} |");
            }
            sb.AppendLine();

            // Separator row
            sb.Append("|---|");
            foreach (var _ in _currentVariants)
            {
                sb.Append("---|");
            }
            sb.AppendLine();

            // Phần I: Câu 1 đến 12 (Trắc nghiệm nhiều lựa chọn)
            for (int q = 1; q <= 12; q++)
            {
                sb.Append($"| {q} |");
                foreach (var variant in _currentVariants)
                {
                    string ans = variant.AnswerKey.ContainsKey(q) ? variant.AnswerKey[q] : "-";
                    sb.Append($" {ans} |");
                }
                sb.AppendLine();
            }

            // Phần II: Câu 13 đến 16 (Đúng / Sai)
            for (int q = 13; q <= 16; q++)
            {
                int p2Index = q - 12;
                sb.Append($"| {q} (Đ/S {p2Index}) |");
                foreach (var variant in _currentVariants)
                {
                    string ans = variant.AnswerKey.ContainsKey(q) ? variant.AnswerKey[q] : "-";
                    sb.Append($" {ans} |");
                }
                sb.AppendLine();
            }

            // Phần III: Câu 17 đến 22 (Trả lời ngắn)
            for (int q = 17; q <= 22; q++)
            {
                int p3Index = q - 16;
                sb.Append($"| {q} (TLN {p3Index}) |");
                foreach (var variant in _currentVariants)
                {
                    string ans = variant.AnswerKey.ContainsKey(q) ? variant.AnswerKey[q] : "-";
                    sb.Append($" {ans} |");
                }
                sb.AppendLine();
            }

            TxtShuffleMatrixResult.Text = sb.ToString();
            TxtShuffleStats.Text = $"Đã hoán vị thành công {count} mã đề (từ {startCode} đến {startCode + count - 1})";

            InfoShuffleNotification.Severity = Wpf.Ui.Controls.InfoBarSeverity.Success;
            InfoShuffleNotification.Title = "Trộn đề thành công";
            InfoShuffleNotification.Message = $"Đã sinh ma trận đáp án cho {count} mã đề. Sẵn sàng xuất tệp Word hoặc in Phiếu OMR.";
            InfoShuffleNotification.IsOpen = true;
        }

        private static List<ExamVariant> MixVariantsInternal(
            ExamDraftResult draft,
            int variantCount,
            int startCode,
            bool shuffleOptions,
            bool lockSpecialOptions)
        {
            var variants = new List<ExamVariant>();

            for (int i = 0; i < variantCount; i++)
            {
                int codeNum = startCode + i;
                var variant = new ExamVariant
                {
                    ExamCode = codeNum.ToString()
                };

                // Seed ngẫu nhiên theo mã đề để đảm bảo tính nhất quán và lặp lại được
                var rng = new Random(codeNum * 99991);

                // 1. Phần I: Hoán vị thứ tự câu hỏi và phương án A-B-C-D
                var shuffledPart1 = draft.Part1Questions.OrderBy(_ => rng.Next()).ToList();
                int qNum = 1;

                foreach (var origQ in shuffledPart1)
                {
                    var q = CloneQuestion(origQ);

                    if (shuffleOptions && q.Options != null && q.Options.Count > 1)
                    {
                        string origCorrectLetter = q.CorrectAnswer.Trim().ToUpperInvariant();
                        string origCorrectText = q.Options.ContainsKey(origCorrectLetter) ? q.Options[origCorrectLetter] : string.Empty;

                        // Kiểm tra khóa phương án đặc thù: "Cả A và B", "Tất cả", "Không có"
                        var nonLocked = new List<KeyValuePair<string, string>>();
                        var locked = new List<KeyValuePair<string, string>>();

                        foreach (var kv in q.Options)
                        {
                            bool isSpecial = lockSpecialOptions && IsSpecialLockedOption(kv.Value);
                            if (isSpecial)
                            {
                                locked.Add(kv);
                            }
                            else
                            {
                                nonLocked.Add(kv);
                            }
                        }

                        // Xáo trộn các phương án không bị khóa
                        var shuffledValues = nonLocked.Select(x => x.Value).OrderBy(_ => rng.Next()).ToList();

                        // Tái cấu trúc lại bảng A, B, C, D
                        string[] letters = { "A", "B", "C", "D", "E", "F" };
                        var newOptions = new Dictionary<string, string>();
                        string newCorrectLetter = "A";

                        int valIdx = 0;
                        for (int letterIdx = 0; letterIdx < q.Options.Count; letterIdx++)
                        {
                            string l = letterIdx < letters.Length ? letters[letterIdx] : $"Opt{letterIdx + 1}";

                            // Nếu vị trí này vốn là phương án bị khóa, giữ nguyên phương án bị khóa
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

                    variant.Part1Questions.Add(q);
                    variant.AnswerKey[qNum] = q.CorrectAnswer;
                    qNum++;
                }

                // 2. Phần II: Hoán vị các câu hỏi Đúng / Sai
                var shuffledPart2 = draft.Part2Questions.OrderBy(_ => rng.Next()).ToList();
                foreach (var origQ in shuffledPart2)
                {
                    var q = CloneQuestion(origQ);
                    variant.Part2Questions.Add(q);
                    variant.AnswerKey[qNum] = q.CorrectAnswer;
                    qNum++;
                }

                // 3. Phần III: Hoán vị các câu hỏi Trả lời ngắn
                var shuffledPart3 = draft.Part3Questions.OrderBy(_ => rng.Next()).ToList();
                foreach (var origQ in shuffledPart3)
                {
                    var q = CloneQuestion(origQ);
                    variant.Part3Questions.Add(q);
                    variant.AnswerKey[qNum] = q.CorrectAnswer;
                    qNum++;
                }

                variants.Add(variant);
            }

            return variants;
        }

        private static bool IsSpecialLockedOption(string text)
        {
            if (string.IsNullOrWhiteSpace(text)) return false;
            string t = text.Trim().ToLowerInvariant();
            return t.StartsWith("cả a và b") ||
                   t.StartsWith("cả a, b") ||
                   t.StartsWith("cả hai") ||
                   t.StartsWith("cả 3") ||
                   t.StartsWith("tất cả các đáp án") ||
                   t.StartsWith("tất cả đáp án trên") ||
                   t.StartsWith("không có đáp án nào") ||
                   t.StartsWith("không có phương án nào");
        }

        private static QuestionItem CloneQuestion(QuestionItem src)
        {
            var clone = new QuestionItem
            {
                Id = src.Id,
                QuestionCode = src.QuestionCode,
                Subject = src.Subject,
                Grade = src.Grade,
                Topic = src.Topic,
                CognitiveLevel = src.CognitiveLevel,
                QuestionType = src.QuestionType,
                Content = src.Content,
                CorrectAnswer = src.CorrectAnswer,
                Explanation = src.Explanation,
                TikzCode = src.TikzCode,
                Source = src.Source,
                RawDataJson = src.RawDataJson
            };

            if (src.Options != null)
            {
                clone.Options = new Dictionary<string, string>(src.Options);
            }

            return clone;
        }

        private void BtnExportAllDocx_Click(object sender, RoutedEventArgs e)
        {
            if (_currentVariants == null || _currentVariants.Count == 0)
            {
                MessageBox.Show("Chưa có danh sách mã đề nào được trộn. Hãy bấm 'Tiến hành Trộn đề' trước.", "Thông báo", MessageBoxButton.OK, MessageBoxImage.Warning);
                return;
            }

            var saveDialog = new Microsoft.Win32.SaveFileDialog
            {
                Filter = "Thư mục xuất / Tệp Word cơ sở (*.docx)|*.docx",
                FileName = $"De_Thi_Tron_{_currentVariants.First().ExamCode}_{_currentVariants.Last().ExamCode}_{DateTime.Now:yyyyMMdd_HHmm}.docx",
                Title = "Chọn nơi lưu toàn bộ các tệp Word đề hoán vị"
            };

            if (saveDialog.ShowDialog() == true)
            {
                try
                {
                    string targetDir = Path.GetDirectoryName(saveDialog.FileName)!;
                    string baseName = Path.GetFileNameWithoutExtension(saveDialog.FileName);

                    var exportedFiles = new List<string>();

                    // 1. Xuất từng file Word riêng cho từng mã đề
                    foreach (var variant in _currentVariants)
                    {
                        string variantFilePath = Path.Combine(targetDir, $"De_Thi_Ma_{variant.ExamCode}.docx");
                        string examText = BuildVariantExamText(variant);
                        _wordService.ExportToDocx(variantFilePath, examText);
                        exportedFiles.Add(variantFilePath);
                    }

                    // 2. Xuất bảng đáp án ma trận đối chiếu
                    string matrixFilePath = Path.Combine(targetDir, "Bang_Dap_An_Ma_Tran_Doi_Chieu.docx");
                    _wordService.ExportToDocx(matrixFilePath, TxtShuffleMatrixResult.Text);
                    exportedFiles.Add(matrixFilePath);

                    var res = MessageBox.Show(
                        $"Đã xuất thành công {exportedFiles.Count} tệp Word (gồm {_currentVariants.Count} mã đề riêng biệt + 1 Bảng đáp án đối chiếu) tại:\n{targetDir}\n\nBạn có muốn mở ngay thư mục chứa các tệp không?",
                        "Xuất Toàn Bộ Mã Đề Thành Công",
                        MessageBoxButton.YesNo,
                        MessageBoxImage.Information);

                    if (res == MessageBoxResult.Yes)
                    {
                        Process.Start(new ProcessStartInfo
                        {
                            FileName = targetDir,
                            UseShellExecute = true
                        });
                    }
                }
                catch (Exception ex)
                {
                    MessageBox.Show($"Lỗi xuất Word hàng loạt: {ex.Message}", "Lỗi", MessageBoxButton.OK, MessageBoxImage.Error);
                }
            }
        }

        private void BtnGenerateOmr_Click(object sender, RoutedEventArgs e)
        {
            var saveDialog = new Microsoft.Win32.SaveFileDialog
            {
                Filter = "Ảnh phiếu trả lời trắc nghiệm PNG (*.png)|*.png",
                FileName = $"Phieu_Tra_Loi_OMR_A4_{DateTime.Now:yyyyMMdd_HHmm}.png",
                Title = "Lưu Phiếu trả lời trắc nghiệm chuẩn OMR A4"
            };

            if (saveDialog.ShowDialog() == true)
            {
                try
                {
                    OmrSheetGenerator.SaveOmrSheet(saveDialog.FileName, numQuestions: 40, hasEssay: true);

                    var res = MessageBox.Show(
                        $"Đã tạo thành công Phiếu trả lời trắc nghiệm OMR chuẩn A4 (150 DPI) có 4 Corner Markers:\n{saveDialog.FileName}\n\nBạn có muốn mở xem ngay tệp ảnh PNG không?",
                        "Tạo Phiếu OMR Thành Công",
                        MessageBoxButton.YesNo,
                        MessageBoxImage.Information);

                    if (res == MessageBoxResult.Yes)
                    {
                        Process.Start(new ProcessStartInfo
                        {
                            FileName = saveDialog.FileName,
                            UseShellExecute = true
                        });
                    }
                }
                catch (Exception ex)
                {
                    MessageBox.Show($"Lỗi sinh phiếu OMR: {ex.Message}", "Lỗi", MessageBoxButton.OK, MessageBoxImage.Error);
                }
            }
        }

        private static string BuildVariantExamText(ExamVariant variant)
        {
            var sb = new StringBuilder();
            sb.AppendLine("BỘ GIÁO DỤC VÀ ĐÀO TẠO                 ĐỀ THI TỐT NGHIỆP THPT");
            sb.AppendLine($"ĐỀ THI CHÍNH THỨC                      MÃ ĐỀ THI: {variant.ExamCode}");
            sb.AppendLine("                                       Môn thi: TOÁN HỌC — Thời gian: 90 phút");
            sb.AppendLine();

            sb.AppendLine("PHẦN I. Câu trắc nghiệm nhiều phương án lựa chọn (Thí sinh trả lời từ câu 1 đến câu 12. Mỗi câu đúng được 0,25 điểm).");
            sb.AppendLine();

            int qNum = 1;
            foreach (var q in variant.Part1Questions)
            {
                sb.AppendLine($"% Câu {qNum} [{q.CognitiveLevel}]_[{q.Topic}]");
                sb.AppendLine(q.Content);
                if (q.Options != null)
                {
                    foreach (var kv in q.Options.OrderBy(x => x.Key))
                    {
                        sb.AppendLine($"{kv.Key}. {kv.Value}");
                    }
                }
                sb.AppendLine();
                qNum++;
            }

            sb.AppendLine("PHẦN II. Câu trắc nghiệm Đúng / Sai (Thí sinh trả lời từ câu 1 đến câu 4. Mỗi câu gồm 4 ý a, b, c, d).");
            sb.AppendLine();

            int p2Num = 1;
            foreach (var q in variant.Part2Questions)
            {
                sb.AppendLine($"% Câu {p2Num++} [{q.CognitiveLevel}]_[{q.Topic}]");
                sb.AppendLine(q.Content);
                sb.AppendLine();
            }

            sb.AppendLine("PHẦN III. Câu trắc nghiệm Trả lời ngắn (Thí sinh trả lời từ câu 1 đến câu 6. Mỗi câu đúng được 0,5 điểm).");
            sb.AppendLine();

            int p3Num = 1;
            foreach (var q in variant.Part3Questions)
            {
                sb.AppendLine($"% Câu {p3Num++} [{q.CognitiveLevel}]_[{q.Topic}]");
                sb.AppendLine(q.Content);
                sb.AppendLine();
            }

            return sb.ToString();
        }

        private static ExamDraftResult BuildBaseDraftQuestions()
        {
            var draft = new ExamDraftResult { Success = true };

            char[] p1Ans = { 'B', 'A', 'D', 'C', 'A', 'C', 'B', 'D', 'A', 'B', 'D', 'C' };
            for (int i = 1; i <= 12; i++)
            {
                var q = new QuestionItem
                {
                    QuestionCode = $"Q_P1_{i:D2}",
                    Subject = "Toán",
                    Grade = 12,
                    Topic = i <= 6 ? "Khảo sát hàm số" : (i <= 10 ? "Nguyên hàm - Tích phân" : "Hình Oxyz"),
                    CognitiveLevel = i <= 6 ? "Nhận biết" : (i <= 10 ? "Thông hiểu" : "Vận dụng"),
                    QuestionType = "MultipleChoice4",
                    Content = i == 1
                        ? "Cho hàm số $y = f(x)$ có bảng biến thiên. Hàm số đồng biến trên khoảng nào?"
                        : (i == 4
                            ? "Khẳng định nào sau đây là đúng về tích phân của hàm số liên tục?"
                            : $"Câu hỏi trắc nghiệm số {i} với công thức toán ${i}x^2 + 1 = 0$."),
                    Options = new Dictionary<string, string>
                    {
                        ["A"] = "$(-\\infty; -1)$",
                        ["B"] = "$(-1; 1)$",
                        ["C"] = "$(1; 2)$",
                        ["D"] = i == 4 ? "Cả A và B đều đúng" : "$(-2; 2)$"
                    },
                    CorrectAnswer = p1Ans[i - 1].ToString()
                };
                draft.Part1Questions.Add(q);
            }

            for (int i = 1; i <= 4; i++)
            {
                draft.Part2Questions.Add(new QuestionItem
                {
                    QuestionCode = $"Q_P2_{i:D2}",
                    Subject = "Toán",
                    Grade = 12,
                    Topic = "Khảo sát hàm số & Tọa độ Oxyz",
                    CognitiveLevel = i <= 2 ? "Thông hiểu" : "Vận dụng",
                    QuestionType = "TrueFalse4",
                    Content = $"Cho hàm số và các điều kiện hình học câu {i}. Xét tính đúng sai của 4 ý sau:\na) Tập xác định $D = \\mathbb{{R}}$.\nb) Đạo hàm luôn dương.\nc) Có tiệm cận đứng $x = 1$.\nd) Đồ thị đi qua điểm $(0; 1)$.",
                    CorrectAnswer = "a: Đ | b: Đ | c: S | d: Đ"
                });
            }

            string[] p3Ans = { "7200", "15", "4", "25", "100", "12" };
            for (int i = 1; i <= 6; i++)
            {
                draft.Part3Questions.Add(new QuestionItem
                {
                    QuestionCode = $"Q_P3_{i:D2}",
                    Subject = "Toán",
                    Grade = 12,
                    Topic = "Ứng dụng thực tế tối ưu hóa",
                    CognitiveLevel = i <= 4 ? "Vận dụng" : "Vận dụng cao",
                    QuestionType = "ShortAnswer",
                    Content = i == 1
                        ? "Một bác nông dân có $240\\text{ m}$ hàng rào muốn rào một mảnh đất hình chữ nhật sát một bờ sông thẳng để làm trang trại chăn nuôi. Hỏi diện tích lớn nhất mảnh đất mà bác có thể rào được là bao nhiêu mét vuông?"
                        : $"Giải bài toán ứng dụng thực tế câu {i}. Tìm giá trị số thực tối giản của bài toán:",
                    CorrectAnswer = p3Ans[i - 1]
                });
            }

            return draft;
        }
    }
}
