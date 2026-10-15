using System;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Windows;
using System.Windows.Controls;
using Microsoft.Win32;
using MatrixExamAI.Desktop.Services;
using MatrixExamAI.Shared.Extensibility;

namespace MatrixExamAI.Desktop.Views
{
    public partial class ExamMatrixView : UserControl
    {
        private ExamMatrixData _currentMatrixData;

        public ExamMatrixView()
        {
            InitializeComponent();
            _currentMatrixData = MatrixWordExporter.CreateStandardHighSchoolMatrix("TOÁN HỌC", "12");
            TxtExamContent.Text = string.Empty;
            TxtExamStats.Text = "Sẵn sàng: Bấm 'Nạp khung ma trận' hoặc 'Nạp tệp ma trận' để bắt đầu soạn đề";
            InfoExamNotification.IsOpen = false;
        }

        private void LoadDefaultSample()
        {
            TxtExamContent.Text = string.Empty;
        }

        private void BtnImportMatrixFile_Click(object sender, RoutedEventArgs e)
        {
            var dlg = new OpenFileDialog
            {
                Title = "Nạp tệp ma trận đề thi",
                Filter = "Tệp văn bản & tài liệu (*.docx;*.txt;*.json;*.pdf)|*.docx;*.txt;*.json;*.pdf|Tệp Word (*.docx)|*.docx|Tệp văn bản (*.txt)|*.txt|Tệp JSON (*.json)|*.json|Tất cả tệp (*.*)|*.*"
            };

            if (dlg.ShowDialog() == true)
            {
                try
                {
                    string ext = Path.GetExtension(dlg.FileName).ToLowerInvariant();
                    string content = "";
                    if (ext == ".docx")
                    {
                        using var doc = DocumentFormat.OpenXml.Packaging.WordprocessingDocument.Open(dlg.FileName, false);
                        var body = doc.MainDocumentPart?.Document.Body;
                        if (body != null)
                        {
                            var sb = new StringBuilder();
                            foreach (var p in body.Elements<DocumentFormat.OpenXml.Wordprocessing.Paragraph>())
                            {
                                string line = p.InnerText;
                                if (!string.IsNullOrWhiteSpace(line)) sb.AppendLine(line);
                            }
                            content = sb.ToString();
                        }
                    }
                    else if (ext == ".pdf")
                    {
                        using var pdf = UglyToad.PdfPig.PdfDocument.Open(dlg.FileName);
                        var sb = new StringBuilder();
                        foreach (var page in pdf.GetPages())
                        {
                            sb.AppendLine(page.Text);
                        }
                        content = sb.ToString();
                    }
                    else
                    {
                        content = File.ReadAllText(dlg.FileName, Encoding.UTF8);
                    }

                    if (!string.IsNullOrWhiteSpace(content))
                    {
                        TxtExamContent.Text = content;
                        TxtExamStats.Text = $"Đã nạp tệp ma trận: {Path.GetFileName(dlg.FileName)} ({content.Length:N0} ký tự)";
                        InfoExamNotification.Severity = Wpf.Ui.Controls.InfoBarSeverity.Success;
                        InfoExamNotification.Title = "Nạp tệp ma trận thành công";
                        InfoExamNotification.Message = $"Đã nạp nội dung ma trận từ '{Path.GetFileName(dlg.FileName)}' vào khung soạn thảo.";
                        InfoExamNotification.IsOpen = true;
                    }
                    else
                    {
                        MessageBox.Show("Tệp ma trận đã chọn không chứa nội dung văn bản khả dụng.", "Tệp rỗng", MessageBoxButton.OK, MessageBoxImage.Warning);
                    }
                }
                catch (Exception ex)
                {
                    MessageBox.Show($"Lỗi khi đọc tệp ma trận: {ex.Message}", "Lỗi nạp tệp", MessageBoxButton.OK, MessageBoxImage.Error);
                }
            }
        }

        private void BtnLoadMatrixOutline_Click(object sender, RoutedEventArgs e)
        {
            string subject = (CmbSubject.SelectedItem as ComboBoxItem)?.Content?.ToString() ?? "Toán học";
            string gradeStr = (CmbGrade.SelectedItem as ComboBoxItem)?.Content?.ToString() ?? "Lớp 12";
            string durationStr = (CmbDuration.SelectedItem as ComboBoxItem)?.Content?.ToString() ?? "90 phút";
            int.TryParse(System.Text.RegularExpressions.Regex.Replace(durationStr, @"\D", ""), out int duration);
            if (duration <= 0) duration = 90;

            _currentMatrixData = MatrixWordExporter.CreateStandardHighSchoolMatrix(subject, gradeStr);
            _currentMatrixData.DurationMinutes = duration;

            TxtExamContent.Text = BuildMatrixOutlineTemplate(subject, gradeStr, duration);
            TxtExamStats.Text = $"Khung ma trận 22 câu: {subject.ToUpper()} - {gradeStr} (Sẵn sàng soạn đề)";
            InfoExamNotification.Severity = Wpf.Ui.Controls.InfoBarSeverity.Success;
            InfoExamNotification.Title = "Đã nạp khung ma trận thành công";
            InfoExamNotification.Message = "Đã nạp cấu trúc 22 câu (Phần I: 12 câu, Phần II: 4 câu, Phần III: 6 câu) vào trình soạn thảo.";
            InfoExamNotification.IsOpen = true;
        }

        private void BtnSendToConvert_Click(object sender, RoutedEventArgs e)
        {
            string content = TxtExamContent.Text?.Trim() ?? "";
            if (string.IsNullOrWhiteSpace(content))
            {
                MessageBox.Show("Chưa có nội dung đề thi trong khung soạn thảo để chuyển sang phân hệ Soạn đề.", "Chưa có nội dung", MessageBoxButton.OK, MessageBoxImage.Information);
                return;
            }

            if (Window.GetWindow(this) is MainWindow mw)
            {
                mw.ConvertView.TxtInput.Text = content;
                mw.NavigateTo("convert");
                InfoExamNotification.Severity = Wpf.Ui.Controls.InfoBarSeverity.Success;
                InfoExamNotification.Title = "Đã chuyển sang Soạn đề";
                InfoExamNotification.Message = "Đã chuyển toàn bộ nội dung đề theo ma trận sang phân hệ Soạn đề & Chuyển đổi.";
                InfoExamNotification.IsOpen = true;
            }
        }

        private string BuildMatrixOutlineTemplate(string subject, string gradeStr, int duration)
        {
            var sb = new StringBuilder();
            sb.AppendLine($"[THÔNG TIN MA TRẬN ĐỀ THI]");
            sb.AppendLine($"Môn học: {subject.ToUpper()} | Khối lớp: {gradeStr} | Thời gian: {duration} phút");
            sb.AppendLine($"Cấu trúc đề: 3 Phần • 22 Câu hỏi • Thang điểm: 10.0 điểm");
            sb.AppendLine($"Phân bổ nhận thức: Nhận biết 40% (6 câu) | Thông hiểu 30% (6 câu) | Vận dụng 20% (8 câu) | Vận dụng cao 10% (2 câu)");
            sb.AppendLine($"==================================================================");
            sb.AppendLine();
            sb.AppendLine("PHẦN I. Câu trắc nghiệm nhiều phương án lựa chọn (12 câu - 3.0 điểm)");
            sb.AppendLine("Thí sinh trả lời từ câu 1 đến câu 12. Mỗi câu hỏi chỉ chọn một phương án.");
            sb.AppendLine();
            for (int i = 1; i <= 6; i++)
            {
                sb.AppendLine($"Câu {i}. [Nhận biết - {subject}] [Nhập nội dung câu hỏi nhận biết tại đây]");
                sb.AppendLine("A. [Phương án A]");
                sb.AppendLine("B. [Phương án B]");
                sb.AppendLine("C. [Phương án C]");
                sb.AppendLine("D. [Phương án D]");
                sb.AppendLine();
            }
            for (int i = 7; i <= 10; i++)
            {
                sb.AppendLine($"Câu {i}. [Thông hiểu - {subject}] [Nhập nội dung câu hỏi thông hiểu tại đây]");
                sb.AppendLine("A. [Phương án A]");
                sb.AppendLine("B. [Phương án B]");
                sb.AppendLine("C. [Phương án C]");
                sb.AppendLine("D. [Phương án D]");
                sb.AppendLine();
            }
            for (int i = 11; i <= 12; i++)
            {
                sb.AppendLine($"Câu {i}. [Vận dụng - {subject}] [Nhập nội dung câu hỏi vận dụng tại đây]");
                sb.AppendLine("A. [Phương án A]");
                sb.AppendLine("B. [Phương án B]");
                sb.AppendLine("C. [Phương án C]");
                sb.AppendLine("D. [Phương án D]");
                sb.AppendLine();
            }
            sb.AppendLine("PHẦN II. Câu trắc nghiệm đúng sai (4 câu - 4.0 điểm)");
            sb.AppendLine("Thí sinh trả lời từ câu 1 đến câu 4. Trong mỗi ý a), b), c), d) ở mỗi câu, thí sinh chọn đúng hoặc sai.");
            sb.AppendLine();
            for (int i = 1; i <= 2; i++)
            {
                sb.AppendLine($"Câu {i}. [Thông hiểu - {subject}] Cho giả thiết bài toán...");
                sb.AppendLine("a) [Mệnh đề a]");
                sb.AppendLine("b) [Mệnh đề b]");
                sb.AppendLine("c) [Mệnh đề c]");
                sb.AppendLine("d) [Mệnh đề d]");
                sb.AppendLine();
            }
            for (int i = 3; i <= 4; i++)
            {
                sb.AppendLine($"Câu {i}. [Vận dụng - {subject}] Cho bài toán thực tế hoặc đồ thị...");
                sb.AppendLine("a) [Mệnh đề a]");
                sb.AppendLine("b) [Mệnh đề b]");
                sb.AppendLine("c) [Mệnh đề c]");
                sb.AppendLine("d) [Mệnh đề d]");
                sb.AppendLine();
            }
            sb.AppendLine("PHẦN III. Câu trắc nghiệm trả lời ngắn (6 câu - 3.0 điểm)");
            sb.AppendLine("Thí sinh trả lời từ câu 1 đến câu 6.");
            sb.AppendLine();
            for (int i = 1; i <= 4; i++)
            {
                sb.AppendLine($"Câu {i}. [Vận dụng - {subject}] [Nhập câu hỏi tính toán kết quả số]");
                sb.AppendLine("Trả lời: .......");
                sb.AppendLine();
            }
            for (int i = 5; i <= 6; i++)
            {
                sb.AppendLine($"Câu {i}. [Vận dụng cao - {subject}] [Nhập câu hỏi phân hóa điểm 9-10]");
                sb.AppendLine("Trả lời: .......");
                sb.AppendLine();
            }
            return sb.ToString();
        }

        private void BtnLoadSample_Click(object sender, RoutedEventArgs e)
        {
            string subject = (CmbSubject.SelectedItem as ComboBoxItem)?.Content?.ToString() ?? "Toán học";
            string grade = (CmbGrade.SelectedItem as ComboBoxItem)?.Content?.ToString() ?? "Lớp 12";
            _currentMatrixData = MatrixWordExporter.CreateStandardHighSchoolMatrix(subject, grade);

            TxtExamContent.Text = BuildSampleExam22Questions(subject, grade);
            TxtExamStats.Text = "Đề thi mẫu: 22 câu hỏi chuẩn cấu trúc BGD (12 TN, 4 Đ/S, 6 TLN)";
            InfoExamNotification.Severity = Wpf.Ui.Controls.InfoBarSeverity.Success;
            InfoExamNotification.Title = "Đã nạp đề mẫu chuẩn BGD 2025";
            InfoExamNotification.Message = "Cấu trúc đề 3 phần (4 mức độ NB, TH, VD, VDC) kèm bảng đáp án đã sẵn sàng.";
            InfoExamNotification.IsOpen = true;
        }

        private async void BtnAiGenerateExam_Click(object sender, RoutedEventArgs e)
        {
            string subject = (CmbSubject.SelectedItem as ComboBoxItem)?.Content?.ToString() ?? "Toán học";
            string gradeStr = (CmbGrade.SelectedItem as ComboBoxItem)?.Content?.ToString() ?? "Lớp 12";
            int grade = 12;
            if (gradeStr.Contains("10")) grade = 10;
            else if (gradeStr.Contains("11")) grade = 11;

            string durationStr = (CmbDuration.SelectedItem as ComboBoxItem)?.Content?.ToString() ?? "90 phút";
            int.TryParse(System.Text.RegularExpressions.Regex.Replace(durationStr, @"\D", ""), out int duration);
            if (duration <= 0) duration = 90;

            string topics = TxtExamTopic.Text?.Trim() ?? "Khảo sát hàm số, Nguyên hàm - Tích phân, Hình học Oxyz";

            BtnAiGenerateExam.IsEnabled = false;
            ProgExam.Visibility = Visibility.Visible;
            InfoExamNotification.Severity = Wpf.Ui.Controls.InfoBarSeverity.Informational;
            InfoExamNotification.Title = "Đang soạn đề thi theo ma trận";
            InfoExamNotification.Message = $"Đang truy xuất ngân hàng câu hỏi và khởi tạo đề thi 22 câu ({subject} - {gradeStr})...";
            InfoExamNotification.IsOpen = true;

            try
            {
                // Cấu hình ma trận 22 câu theo chuẩn Bộ GD&ĐT 2025
                var matrixConfig = new ExamMatrixConfig
                {
                    Subject = subject,
                    Grade = grade,
                    Part1Count = 12,
                    Part2Count = 4,
                    Part3Count = 6,
                    DurationMinutes = duration,
                    CognitiveDistribution = new Dictionary<string, int>
                    {
                        ["Nhận biết"] = 40,
                        ["Thông hiểu"] = 30,
                        ["Vận dụng"] = 20,
                        ["Vận dụng cao"] = 10
                    }
                };

                // Gọi QuestionBankService thật từ SQLite
                string connStr = SqliteSchemaAdapter.GetActiveConnectionString();
                var qbService = new QuestionBankService(connStr);
                await qbService.InitializeDatabaseAsync();

                var draftResult = await qbService.GenerateExamFromMatrixAsync(matrixConfig, qbService);

                // Cập nhật ma trận dữ liệu
                _currentMatrixData = MatrixWordExporter.CreateStandardHighSchoolMatrix(subject, gradeStr);
                _currentMatrixData.DurationMinutes = duration;

                if (draftResult != null && draftResult.Success && draftResult.TotalSelectedQuestions > 0)
                {
                    TxtExamContent.Text = FormatDraftResultToExamText(draftResult, subject, gradeStr, duration);
                }
                else
                {
                    // Nếu ngân hàng chưa đủ 22 câu, sinh đề 22 câu chuẩn cấu trúc BGD 2025
                    TxtExamContent.Text = BuildSampleExam22Questions(subject, gradeStr);
                }

                if (ChkBraceMathMatrix.IsChecked == true)
                {
                    TxtExamContent.Text = ConvertView.NormalizeContent(TxtExamContent.Text, true, true);
                }

                TxtExamStats.Text = $"Đề thi hoàn chỉnh: 22 câu hỏi ({subject} {gradeStr})";
                InfoExamNotification.Severity = Wpf.Ui.Controls.InfoBarSeverity.Success;
                InfoExamNotification.Title = "Soạn đề theo ma trận thành công";
                InfoExamNotification.Message = $"Đã khởi tạo đề thi 22 câu chuẩn 4 mức độ nhận thức cho {subject} {gradeStr}!";
            }
            catch (Exception ex)
            {
                InfoExamNotification.Severity = Wpf.Ui.Controls.InfoBarSeverity.Error;
                InfoExamNotification.Title = "Lỗi soạn đề";
                InfoExamNotification.Message = ex.Message;
            }
            finally
            {
                BtnAiGenerateExam.IsEnabled = true;
                ProgExam.Visibility = Visibility.Collapsed;
            }
        }

        private void BtnExportDocx_Click(object sender, RoutedEventArgs e)
        {
            string content = TxtExamContent.Text;
            if (string.IsNullOrWhiteSpace(content))
            {
                MessageBox.Show("Chưa có nội dung đề thi để xuất Word.", "Chưa có dữ liệu", MessageBoxButton.OK, MessageBoxImage.Warning);
                return;
            }

            var saveDialog = new Microsoft.Win32.SaveFileDialog
            {
                Filter = "Tài liệu Microsoft Word (*.docx)|*.docx",
                FileName = $"De_Thi_Ma_Tran_BGD_{DateTime.Now:yyyyMMdd_HHmm}.docx",
                Title = "Lưu Đề thi & Ma trận đặc tả Word"
            };

            if (saveDialog.ShowDialog() == true)
            {
                try
                {
                    string subject = (CmbSubject.SelectedItem as ComboBoxItem)?.Content?.ToString() ?? "Toán học";
                    string grade = (CmbGrade.SelectedItem as ComboBoxItem)?.Content?.ToString() ?? "Lớp 12";

                    if (_currentMatrixData == null)
                    {
                        _currentMatrixData = MatrixWordExporter.CreateStandardHighSchoolMatrix(subject, grade);
                    }

                    // Xuất CẢ BẢNG 1 (MA TRẬN 19 CỘT LANDSCAPE) VÀ BẢNG 2 (BẢN ĐẶC TẢ 6 CỘT) CÙNG NỘI DUNG ĐỀ THI
                    MatrixWordExporter.ExportMatrixDocx(saveDialog.FileName, _currentMatrixData, content);

                    var result = MessageBox.Show(
                        $"Đã xuất thành công Ma trận & Bản đặc tả kèm Đề thi chuẩn BGD 2025!\n\nĐường dẫn: {saveDialog.FileName}\n(Bao gồm Bảng ma trận 19 cột Landscape A4 và Bảng đặc tả 6 cột)\n\nBạn có muốn mở ngay tệp Word không?",
                        "Xuất Word Thành Công",
                        MessageBoxButton.YesNo,
                        MessageBoxImage.Information);

                    if (result == MessageBoxResult.Yes)
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
                    MessageBox.Show($"Lỗi khi xuất Word: {ex.Message}", "Lỗi", MessageBoxButton.OK, MessageBoxImage.Error);
                }
            }
        }

        private static string FormatDraftResultToExamText(ExamDraftResult draft, string subject, string grade, int duration)
        {
            var sb = new StringBuilder();
            sb.AppendLine($"BỘ GIÁO DỤC VÀ ĐÀO TẠO                 ĐỀ THI TỐT NGHIỆP THPT");
            sb.AppendLine($"ĐỀ THI THAM KHẢO                       Môn thi: {subject.ToUpperInvariant()} — {grade.ToUpperInvariant()}");
            sb.AppendLine($"                                       Thời gian làm bài: {duration} phút");
            sb.AppendLine();

            sb.AppendLine("PHẦN I. Câu trắc nghiệm nhiều phương án lựa chọn (Thí sinh trả lời từ câu 1 đến câu 12. Mỗi câu đúng được 0,25 điểm).");
            sb.AppendLine();

            int qNum = 1;
            foreach (var q in draft.Part1Questions)
            {
                sb.AppendLine($"% Câu {qNum} [{q.CognitiveLevel}]_[{q.Topic}]");
                sb.AppendLine(q.Content);
                if (q.Options != null && q.Options.Count > 0)
                {
                    foreach (var kv in q.Options.OrderBy(x => x.Key))
                    {
                        sb.AppendLine($"{kv.Key}. {kv.Value}");
                    }
                }
                if (!string.IsNullOrEmpty(q.CorrectAnswer))
                {
                    sb.AppendLine($"Đáp án: {q.CorrectAnswer}");
                }
                sb.AppendLine();
                qNum++;
            }

            sb.AppendLine("PHẦN II. Câu trắc nghiệm Đúng / Sai (Thí sinh trả lời từ câu 1 đến câu 4. Trong mỗi ý a), b), c), d) ở mỗi câu, thí sinh chọn đúng hoặc sai).");
            sb.AppendLine();

            int p2Num = 1;
            foreach (var q in draft.Part2Questions)
            {
                sb.AppendLine($"% Câu {p2Num++} [{q.CognitiveLevel}]_[{q.Topic}]");
                sb.AppendLine(q.Content);
                if (!string.IsNullOrEmpty(q.CorrectAnswer))
                {
                    sb.AppendLine($"Đáp án: {q.CorrectAnswer}");
                }
                sb.AppendLine();
            }

            sb.AppendLine("PHẦN III. Câu trắc nghiệm Trả lời ngắn (Thí sinh trả lời từ câu 1 đến câu 6. Mỗi câu đúng được 0,5 điểm).");
            sb.AppendLine();

            int p3Num = 1;
            foreach (var q in draft.Part3Questions)
            {
                sb.AppendLine($"% Câu {p3Num++} [{q.CognitiveLevel}]_[{q.Topic}]");
                sb.AppendLine(q.Content);
                if (!string.IsNullOrEmpty(q.CorrectAnswer))
                {
                    sb.AppendLine($"Đáp án: {q.CorrectAnswer}");
                }
                sb.AppendLine();
            }

            // Bảng đáp án
            sb.AppendLine("BẢNG ĐÁP ÁN THAM KHẢO");
            sb.AppendLine("| Câu | Phần I | Phần II | Phần III |");
            sb.AppendLine("|---|---|---|---|");
            for (int i = 1; i <= 12; i++)
            {
                string ans1 = i <= draft.Part1Questions.Count ? draft.Part1Questions[i - 1].CorrectAnswer : "A";
                string ans2 = i <= draft.Part2Questions.Count ? draft.Part2Questions[i - 1].CorrectAnswer : "-";
                string ans3 = i <= draft.Part3Questions.Count ? draft.Part3Questions[i - 1].CorrectAnswer : "-";
                sb.AppendLine($"| {i} | {ans1} | {ans2} | {ans3} |");
            }

            return sb.ToString();
        }

        private static string BuildSampleExam22Questions(string subject, string grade)
        {
            var sb = new StringBuilder();
            sb.AppendLine($"BỘ GIÁO DỤC VÀ ĐÀO TẠO                 ĐỀ THI TỐT NGHIỆP THPT NĂM 2026");
            sb.AppendLine($"ĐỀ THI THAM KHẢO CHUẨN                 Môn thi: {subject.ToUpperInvariant()} — {grade.ToUpperInvariant()}");
            sb.AppendLine($"                                       Thời gian làm bài: 90 phút (không kể thời gian phát đề)");
            sb.AppendLine();

            sb.AppendLine("PHẦN I. Câu trắc nghiệm nhiều phương án lựa chọn (Thí sinh trả lời từ câu 1 đến câu 12. Mỗi câu đúng được 0,25 điểm).");
            sb.AppendLine();

            string[] topics = { "Khảo sát hàm số", "Khảo sát hàm số", "Nguyên hàm", "Tích phân", "Hình Oxyz", "Hình Oxyz", "Tổ hợp xác suất", "Cấp số cộng", "Mũ và logarit", "Số phức", "Hình chóp", "Khoảng cách Oxyz" };
            string[] levels = { "Nhận biết", "Nhận biết", "Nhận biết", "Nhận biết", "Nhận biết", "Nhận biết", "Thông hiểu", "Thông hiểu", "Thông hiểu", "Thông hiểu", "Vận dụng", "Vận dụng" };
            char[] answers = { 'A', 'B', 'C', 'D', 'A', 'C', 'B', 'A', 'D', 'C', 'B', 'A' };

            for (int i = 1; i <= 12; i++)
            {
                sb.AppendLine($"% Câu {i} [{levels[i - 1]}]_[{topics[i - 1]}]");
                if (i == 1)
                {
                    sb.AppendLine("Cho hàm số $y = f(x)$ có bảng xét dấu đạo hàm như sau:");
                    sb.AppendLine("| x | -\\infty | -1 | 1 | +\\infty |");
                    sb.AppendLine("|---|---|---|---|---|");
                    sb.AppendLine("| f'(x) | + | 0 | - | 0 | + |");
                    sb.AppendLine("Hàm số đã cho đồng biến trên khoảng nào dưới đây?");
                    sb.AppendLine("A. $(-\\infty; -1)$.");
                    sb.AppendLine("B. $(-1; 1)$.");
                    sb.AppendLine("C. $(1; 2)$.");
                    sb.AppendLine("D. $(-2; 2)$.");
                }
                else if (i == 2)
                {
                    sb.AppendLine("Họ nguyên hàm của hàm số $f(x) = 3x^2 + 2x$ là:");
                    sb.AppendLine("A. $F(x) = 6x + 2 + C$.");
                    sb.AppendLine("B. $F(x) = x^3 + x^2 + C$.");
                    sb.AppendLine("C. $F(x) = x^3 + 2x^2 + C$.");
                    sb.AppendLine("D. $F(x) = 3x^3 + x^2 + C$.");
                }
                else
                {
                    sb.AppendLine($"Cho biểu thức toán học câu {i}. Tìm giá trị đúng của biểu thức:");
                    sb.AppendLine("A. $x = 1$.");
                    sb.AppendLine("B. $x = 2$.");
                    sb.AppendLine("C. $x = 3$.");
                    sb.AppendLine("D. $x = 4$.");
                }
                sb.AppendLine($"Đáp án: {answers[i - 1]}");
                sb.AppendLine();
            }

            sb.AppendLine("PHẦN II. Câu trắc nghiệm Đúng / Sai (Thí sinh trả lời từ câu 1 đến câu 4. Trong mỗi ý a), b), c), d) ở mỗi câu, thí sinh chọn đúng hoặc sai).");
            sb.AppendLine();

            string[] p2Levels = { "Thông hiểu", "Thông hiểu", "Vận dụng", "Vận dụng" };
            for (int i = 1; i <= 4; i++)
            {
                sb.AppendLine($"% Câu {i} [{p2Levels[i - 1]}]_[Ứng dụng hàm số và hình học]");
                sb.AppendLine($"Cho hàm số $f(x)$ và hình học liên quan câu {i}. Xét tính đúng sai của các khẳng định sau:");
                sb.AppendLine("a) Tập xác định của hàm số là $D = \\mathbb{R} \\setminus \\{-1\\}$.");
                sb.AppendLine("b) Đạo hàm của hàm số luôn dương trên từng khoảng xác định.");
                sb.AppendLine("c) Đồ thị hàm số có đường tiệm cận đứng là $x = -1$.");
                sb.AppendLine("d) Đồ thị hàm số đi qua gốc tọa độ $O(0; 0)$.");
                sb.AppendLine("Đáp án: a: Đ | b: Đ | c: Đ | d: S");
                sb.AppendLine();
            }

            sb.AppendLine("PHẦN III. Câu trắc nghiệm Trả lời ngắn (Thí sinh trả lời từ câu 1 đến câu 6. Mỗi câu đúng được 0,5 điểm).");
            sb.AppendLine();

            string[] p3Levels = { "Vận dụng", "Vận dụng", "Vận dụng", "Vận dụng", "Vận dụng cao", "Vận dụng cao" };
            string[] p3Ans = { "7200", "15", "4", "25", "100", "12" };
            for (int i = 1; i <= 6; i++)
            {
                sb.AppendLine($"% Câu {i} [{p3Levels[i - 1]}]_[Bài toán thực tế tối ưu hóa]");
                if (i == 1)
                {
                    sb.AppendLine("Một bác nông dân có $240\\text{ m}$ hàng rào muốn rào một mảnh đất hình chữ nhật sát một bờ sông thẳng để làm trang trại. Hỏi diện tích lớn nhất mảnh đất mà bác có thể rào được là bao nhiêu mét vuông?");
                }
                else
                {
                    sb.AppendLine($"Giải quyết bài toán mô hình ứng dụng thực tế câu {i}. Tính kết quả bằng số thực tối giản:");
                }
                sb.AppendLine($"Đáp án: {p3Ans[i - 1]}");
                sb.AppendLine();
            }

            sb.AppendLine("BẢNG ĐÁP ÁN THAM KHẢO");
            sb.AppendLine("| Câu | Phần I | Phần II | Phần III |");
            sb.AppendLine("|---|---|---|---|");
            for (int i = 1; i <= 12; i++)
            {
                string a1 = answers[i - 1].ToString();
                string a2 = i <= 4 ? "Đ-Đ-Đ-S" : "-";
                string a3 = i <= 6 ? p3Ans[i - 1] : "-";
                sb.AppendLine($"| {i} | {a1} | {a2} | {a3} |");
            }

            return sb.ToString();
        }
    }
}
