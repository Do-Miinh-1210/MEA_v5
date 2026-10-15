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
        private bool _isViewLoaded = false;
        private ExamMatrixData _currentMatrixData;

        public ExamMatrixView()
        {
            InitializeComponent();
            _isViewLoaded = true;
            PopulateMatrixPresetsFromFolder();
            _currentMatrixData = MatrixWordExporter.CreateStandardHighSchoolMatrix("TOÁN HỌC", "12");
            RefreshMatrixGrids();
            TxtExamContent.Text = string.Empty;
            TxtExamStats.Text = "Sẵn sàng: Khởi tạo khung hoặc Nạp tệp ma trận";
            InfoExamNotification.IsOpen = false;
        }

        public static string GetMatrixTemplateDirectory()
        {
            string[] candidates = new[]
            {
                Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "data", "matrix_templates"),
                Path.Combine(Directory.GetCurrentDirectory(), "data", "matrix_templates"),
                Path.GetFullPath(Path.Combine(AppContext.BaseDirectory, @"..\..\..\..\..\data\matrix_templates")),
                @"M:\IT\Phần mềm biên soạn tài liệu\MEA_v5.0\data\matrix_templates"
            };

            foreach (var dir in candidates)
            {
                if (Directory.Exists(dir)) return dir;
            }
            return string.Empty;
        }

        private void PopulateMatrixPresetsFromFolder()
        {
            string templateDir = GetMatrixTemplateDirectory();
            if (string.IsNullOrEmpty(templateDir) || !Directory.Exists(templateDir)) return;

            var files = Directory.GetFiles(templateDir, "*.*")
                .Where(f => f.EndsWith(".docx", StringComparison.OrdinalIgnoreCase) || f.EndsWith(".json", StringComparison.OrdinalIgnoreCase))
                .OrderBy(f => Path.GetFileName(f));

            foreach (var file in files)
            {
                string fileName = Path.GetFileName(file);
                if (fileName.Equals("MaTran_Mau_BGD.docx", StringComparison.OrdinalIgnoreCase)) continue;

                CmbMatrixPreset.Items.Add(new ComboBoxItem
                {
                    Content = $"Mẫu: {fileName}",
                    Tag = $"FILE:{file}",
                    Padding = new Thickness(6, 3, 6, 3)
                });
            }
        }

        private void LoadMatrixTemplateFile(string filePath)
        {
            if (!File.Exists(filePath)) return;
            var parseResult = MatrixDocumentParserService.ParseFile(filePath);
            if (parseResult.Success && parseResult.MatrixData != null)
            {
                _currentMatrixData = parseResult.MatrixData;
                SelectComboBoxItem(CmbSubject, _currentMatrixData.Subject);
                SelectComboBoxItem(CmbGrade, _currentMatrixData.Grade);
                SelectComboBoxItem(CmbDuration, $"{_currentMatrixData.DurationMinutes} phút");
                RefreshMatrixGrids();
                TxtExamContent.Text = !string.IsNullOrWhiteSpace(parseResult.ExtractedText) && parseResult.ExtractedText.Contains("Câu 1")
                    ? parseResult.ExtractedText
                    : BuildMatrixOutlineTemplate(_currentMatrixData.Subject, _currentMatrixData.Grade, _currentMatrixData.DurationMinutes);
                int totalQ = _currentMatrixData.Rows?.Sum(r => r.TotalQuestions) ?? 0;
                string fileName = Path.GetFileName(filePath);
                TxtExamStats.Text = $"Đã nạp '{fileName}': {_currentMatrixData.Subject} {_currentMatrixData.Grade} ({totalQ} câu)";
                InfoExamNotification.Severity = Wpf.Ui.Controls.InfoBarSeverity.Success;
                InfoExamNotification.Title = $"Đã nạp thành công: {fileName}";
                InfoExamNotification.Message = parseResult.Message;
                InfoExamNotification.IsOpen = true;
            }
            else
            {
                MessageBox.Show($"Không thể nạp tệp ma trận: {parseResult.Message}", "Lỗi nạp tệp", MessageBoxButton.OK, MessageBoxImage.Warning);
            }
        }

        private void RefreshMatrixGrids()
        {
            if (!_isViewLoaded || _currentMatrixData == null || DgMatrixTopics == null || DgMatrixSpecs == null) return;
            DgMatrixTopics.ItemsSource = null;
            DgMatrixTopics.ItemsSource = _currentMatrixData.Rows;
            DgMatrixSpecs.ItemsSource = null;
            DgMatrixSpecs.ItemsSource = _currentMatrixData.Specs;

            int tnCount = _currentMatrixData.Rows?.Sum(r => r.TnNb + r.TnTh + r.TnVd) ?? 0;
            int dsItems = _currentMatrixData.Rows?.Sum(r => r.DsNb + r.DsTh + r.DsVd) ?? 0;
            int dsQuestions = dsItems > 0 ? (dsItems + 3) / 4 : 0;
            int tlnCount = _currentMatrixData.Rows?.Sum(r => r.TlnNb + r.TlnTh + r.TlnVd) ?? 0;
            int tlCount = _currentMatrixData.Rows?.Sum(r => r.TlNb + r.TlTh + r.TlVd) ?? 0;

            int totalQ = tnCount + dsQuestions + tlnCount + tlCount;
            if (totalQ == 0) totalQ = _currentMatrixData.Rows?.Sum(r => r.TotalQuestions) ?? 0;
            double totalPts = _currentMatrixData.Rows?.Sum(r => r.Points) ?? 0;
            if (totalPts <= 0) totalPts = 10.0;

            int totalNb = _currentMatrixData.Rows?.Sum(r => r.TotalNb) ?? 0;
            int totalTh = _currentMatrixData.Rows?.Sum(r => r.TotalTh) ?? 0;
            int totalVd = _currentMatrixData.Rows?.Sum(r => r.TotalVd) ?? 0;
            int totalItems = totalNb + totalTh + totalVd;
            if (totalItems <= 0) totalItems = 1;

            int pctNb = (int)Math.Round((double)totalNb * 100 / totalItems);
            int pctTh = (int)Math.Round((double)totalTh * 100 / totalItems);
            int pctVd = 100 - pctNb - pctTh;

            var partsSummary = new List<string>();
            if (tnCount > 0) partsSummary.Add($"Phần I (TNKQ): {tnCount} câu");
            if (dsQuestions > 0) partsSummary.Add($"Phần II (Đúng-Sai): {dsQuestions} câu ({dsItems} ý)");
            if (tlnCount > 0) partsSummary.Add($"Phần III (Trả lời ngắn): {tlnCount} câu");
            if (tlCount > 0) partsSummary.Add($"Tự luận: {tlCount} câu");

            string partsText = partsSummary.Count > 0 ? string.Join(", ", partsSummary) : $"{totalQ} câu hỏi";

            if (TxtSummaryHeader != null)
                TxtSummaryHeader.Text = $"{totalQ} câu • {totalPts:F1} điểm";
            if (TxtMatrixFooterSummary != null)
                TxtMatrixFooterSummary.Text = $"Tổng cộng: {totalQ} câu hỏi ({partsText}) | Tổng điểm: {totalPts:F1} điểm | Tỉ lệ: Nhận biết {pctNb}% ({totalNb} lệnh hỏi) • Thông hiểu {pctTh}% ({totalTh} lệnh hỏi) • Vận dụng {pctVd}% ({totalVd} lệnh hỏi)";
        }

        private void CmbMatrixPreset_SelectionChanged(object sender, SelectionChangedEventArgs e)
        {
            if (!_isViewLoaded) return;
            if (CmbMatrixPreset?.SelectedItem is ComboBoxItem item)
            {
                string tag = item.Tag?.ToString() ?? "";
                if (tag == "TIN_11")
                {
                    SelectComboBoxItem(CmbSubject, "Tin học");
                    SelectComboBoxItem(CmbGrade, "11");
                    SelectComboBoxItem(CmbDuration, "45 phút");
                    _currentMatrixData = MatrixWordExporter.CreateInformatics11Matrix();
                    RefreshMatrixGrids();
                    TxtExamContent.Text = BuildMatrixOutlineTemplate("Tin học", "Lớp 11", 45);
                    TxtExamStats.Text = "Ma trận Tin học 11 KNTT: 28 câu (24 TN + 4 Đ/S) - 45 phút";
                    InfoExamNotification.Severity = Wpf.Ui.Controls.InfoBarSeverity.Success;
                    InfoExamNotification.Title = "Đã nạp mẫu ma trận Tin học 11 (KNTT)";
                    InfoExamNotification.Message = "Ma trận và bản đặc tả 28 câu (24 TN + 4 Đúng-Sai) chuẩn Bộ GD&ĐT đã sẵn sàng.";
                    InfoExamNotification.IsOpen = true;
                }
                else if (tag == "TOAN_12")
                {
                    SelectComboBoxItem(CmbSubject, "Toán học");
                    SelectComboBoxItem(CmbGrade, "12");
                    SelectComboBoxItem(CmbDuration, "90 phút");
                    _currentMatrixData = MatrixWordExporter.CreateStandardHighSchoolMatrix("TOÁN HỌC", "12");
                    RefreshMatrixGrids();
                    TxtExamContent.Text = BuildMatrixOutlineTemplate("Toán học", "Lớp 12", 90);
                    TxtExamStats.Text = "Ma trận Toán 12 BGD: 22 câu (12 TN + 4 Đ/S + 6 TLN) - 90 phút";
                    InfoExamNotification.Severity = Wpf.Ui.Controls.InfoBarSeverity.Success;
                    InfoExamNotification.Title = "Đã nạp mẫu ma trận Toán 12";
                    InfoExamNotification.Message = "Ma trận và bản đặc tả 22 câu chuẩn BGD đã sẵn sàng.";
                    InfoExamNotification.IsOpen = true;
                }
                else if (tag == "DOCX_BGD")
                {
                    string templateDir = GetMatrixTemplateDirectory();
                    string targetFile = !string.IsNullOrEmpty(templateDir) ? Path.Combine(templateDir, "MaTran_Mau_BGD.docx") : "";
                    if (File.Exists(targetFile))
                    {
                        LoadMatrixTemplateFile(targetFile);
                    }
                    else
                    {
                        MessageBox.Show("Không tìm thấy tệp MaTran_Mau_BGD.docx trong thư mục matrix_templates.", "Chưa tìm thấy tệp", MessageBoxButton.OK, MessageBoxImage.Information);
                    }
                }
                else if (tag.StartsWith("FILE:", StringComparison.OrdinalIgnoreCase))
                {
                    string path = tag.Substring(5);
                    LoadMatrixTemplateFile(path);
                }
            }
        }

        private void SelectComboBoxItem(ComboBox combo, string text)
        {
            if (combo == null || string.IsNullOrEmpty(text)) return;
            foreach (ComboBoxItem item in combo.Items)
            {
                string content = item.Content?.ToString() ?? "";
                if (content.IndexOf(text, StringComparison.OrdinalIgnoreCase) >= 0 || text.IndexOf(content, StringComparison.OrdinalIgnoreCase) >= 0)
                {
                    combo.SelectedItem = item;
                    return;
                }
            }
        }

        private void BtnAddTopic_Click(object sender, RoutedEventArgs e)
        {
            if (_currentMatrixData == null) return;
            int nextStt = _currentMatrixData.Rows.Count + 1;
            _currentMatrixData.Rows.Add(new MatrixTopicRow
            {
                Stt = nextStt,
                Topic = $"Chủ đề mới {nextStt}",
                Requirements = "Nhận biết kiến thức trọng tâm; thông hiểu và vận dụng giải quyết bài toán.",
                TnNb = 1, TnTh = 1, TnVd = 0,
                Points = 1.0
            });
            RefreshMatrixGrids();
        }

        private void BtnDeleteTopic_Click(object sender, RoutedEventArgs e)
        {
            if (_currentMatrixData == null || _currentMatrixData.Rows.Count <= 1) return;
            if (DgMatrixTopics.SelectedItem is MatrixTopicRow selected)
            {
                _currentMatrixData.Rows.Remove(selected);
            }
            else
            {
                _currentMatrixData.Rows.RemoveAt(_currentMatrixData.Rows.Count - 1);
            }
            for (int i = 0; i < _currentMatrixData.Rows.Count; i++)
            {
                _currentMatrixData.Rows[i].Stt = i + 1;
            }
            RefreshMatrixGrids();
        }

        private void BtnResetMatrix_Click(object sender, RoutedEventArgs e)
        {
            string subject = (CmbSubject.SelectedItem as ComboBoxItem)?.Content?.ToString() ?? "Toán học";
            string gradeStr = (CmbGrade.SelectedItem as ComboBoxItem)?.Content?.ToString() ?? "Lớp 12";
            string durationStr = (CmbDuration.SelectedItem as ComboBoxItem)?.Content?.ToString() ?? "90 phút";
            int.TryParse(System.Text.RegularExpressions.Regex.Replace(durationStr, @"\D", ""), out int duration);
            if (duration <= 0) duration = 90;

            if (subject.IndexOf("tin", StringComparison.OrdinalIgnoreCase) >= 0 || gradeStr.Contains("11"))
            {
                _currentMatrixData = MatrixWordExporter.CreateInformatics11Matrix();
                duration = 45;
            }
            else
            {
                _currentMatrixData = MatrixWordExporter.CreateStandardHighSchoolMatrix(subject, gradeStr);
            }
            _currentMatrixData.DurationMinutes = duration;
            RefreshMatrixGrids();
        }

        private void LoadDefaultSample()
        {
            TxtExamContent.Text = string.Empty;
        }

        private void BtnLoadSample_Click(object sender, RoutedEventArgs e)
        {
            BtnLoadMatrixOutline_Click(sender, e);
        }

        private void BtnImportMatrixFile_Click(object sender, RoutedEventArgs e)
        {
            string templateDir = GetMatrixTemplateDirectory();
            var dlg = new OpenFileDialog
            {
                Title = "Nạp tệp ma trận đề thi",
                Filter = "Tệp văn bản & tài liệu (*.docx;*.txt;*.json;*.pdf)|*.docx;*.txt;*.json;*.pdf|Tệp Word (*.docx)|*.docx|Tệp văn bản (*.txt)|*.txt|Tệp JSON (*.json)|*.json|Tất cả tệp (*.*)|*.*",
                InitialDirectory = !string.IsNullOrEmpty(templateDir) && Directory.Exists(templateDir) ? templateDir : Environment.CurrentDirectory
            };

            if (dlg.ShowDialog() == true)
            {
                try
                {
                    var parseResult = MatrixDocumentParserService.ParseFile(dlg.FileName);
                    if (parseResult.Success && parseResult.MatrixData != null)
                    {
                        _currentMatrixData = parseResult.MatrixData;
                        SelectComboBoxItem(CmbSubject, _currentMatrixData.Subject);
                        SelectComboBoxItem(CmbGrade, _currentMatrixData.Grade);
                        SelectComboBoxItem(CmbDuration, $"{_currentMatrixData.DurationMinutes} phút");
                        RefreshMatrixGrids();

                        TxtExamContent.Text = !string.IsNullOrWhiteSpace(parseResult.ExtractedText) && parseResult.ExtractedText.Contains("Câu 1")
                            ? parseResult.ExtractedText
                            : BuildMatrixOutlineTemplate(_currentMatrixData.Subject, _currentMatrixData.Grade, _currentMatrixData.DurationMinutes);

                        int totalQ = _currentMatrixData.Rows?.Sum(r => r.TotalQuestions) ?? 0;
                        TxtExamStats.Text = $"Đã nhận diện ma trận: {_currentMatrixData.Subject} {_currentMatrixData.Grade} ({_currentMatrixData.Rows.Count} chủ đề, {totalQ} câu)";
                        InfoExamNotification.Severity = Wpf.Ui.Controls.InfoBarSeverity.Success;
                        InfoExamNotification.Title = "Nạp & Nhận diện ma trận thành công";
                        InfoExamNotification.Message = parseResult.Message;
                        InfoExamNotification.IsOpen = true;
                    }
                    else
                    {
                        MessageBox.Show("Không thể trích xuất cấu trúc ma trận từ tệp đã chọn.", "Không nhận diện được", MessageBoxButton.OK, MessageBoxImage.Warning);
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

            if (subject.IndexOf("tin", StringComparison.OrdinalIgnoreCase) >= 0 || gradeStr.Contains("11"))
            {
                _currentMatrixData = MatrixWordExporter.CreateInformatics11Matrix();
                if (duration == 90) duration = 45;
            }
            else
            {
                _currentMatrixData = MatrixWordExporter.CreateStandardHighSchoolMatrix(subject, gradeStr);
            }
            _currentMatrixData.DurationMinutes = duration;
            RefreshMatrixGrids();

            TxtExamContent.Text = BuildMatrixOutlineTemplate(subject, gradeStr, duration);
            int totalQ = _currentMatrixData.Rows?.Sum(r => r.TotalQuestions) ?? 0;
            TxtExamStats.Text = $"Khung ma trận {totalQ} câu: {subject.ToUpper()} - {gradeStr} (Sẵn sàng soạn đề)";
            TabMatrixMain.SelectedIndex = 0;
            InfoExamNotification.Severity = Wpf.Ui.Controls.InfoBarSeverity.Success;
            InfoExamNotification.Title = "Đã khởi tạo bảng ma trận & bản đặc tả thành công";
            InfoExamNotification.Message = $"Bảng ma trận và bản đặc tả {totalQ} câu chuẩn BGD đã được kẻ khung chi tiết.";
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
            int tnCount = _currentMatrixData?.Rows?.Sum(r => r.TnNb + r.TnTh + r.TnVd) ?? 0;
            int dsItems = _currentMatrixData?.Rows?.Sum(r => r.DsNb + r.DsTh + r.DsVd) ?? 0;
            int dsQuestions = dsItems > 0 ? (dsItems + 3) / 4 : 0;
            int tlnCount = _currentMatrixData?.Rows?.Sum(r => r.TlnNb + r.TlnTh + r.TlnVd) ?? 0;

            bool isInformatics = subject.IndexOf("tin", StringComparison.OrdinalIgnoreCase) >= 0 || gradeStr.Contains("11") || tnCount == 24;

            if (isInformatics)
            {
                return BuildMatrixOutlineInformatics11(subject, gradeStr, duration);
            }

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
                sb.AppendLine("*A. [Phương án đúng A]");
                sb.AppendLine("B. [Phương án B]");
                sb.AppendLine("C. [Phương án C]");
                sb.AppendLine("D. [Phương án D]");
                sb.AppendLine("Đáp án: A");
                sb.AppendLine();
            }
            for (int i = 7; i <= 10; i++)
            {
                sb.AppendLine($"Câu {i}. [Thông hiểu - {subject}] [Nhập nội dung câu hỏi thông hiểu tại đây]");
                sb.AppendLine("A. [Phương án A]");
                sb.AppendLine("*B. [Phương án đúng B]");
                sb.AppendLine("C. [Phương án C]");
                sb.AppendLine("D. [Phương án D]");
                sb.AppendLine("Đáp án: B");
                sb.AppendLine();
            }
            for (int i = 11; i <= 12; i++)
            {
                sb.AppendLine($"Câu {i}. [Vận dụng - {subject}] [Nhập nội dung câu hỏi vận dụng tại đây]");
                sb.AppendLine("A. [Phương án A]");
                sb.AppendLine("B. [Phương án B]");
                sb.AppendLine("*C. [Phương án đúng C]");
                sb.AppendLine("D. [Phương án D]");
                sb.AppendLine("Đáp án: C");
                sb.AppendLine();
            }
            sb.AppendLine("PHẦN II. Câu trắc nghiệm đúng sai (4 câu - 4.0 điểm)");
            sb.AppendLine("Thí sinh trả lời từ câu 1 đến câu 4. Trong mỗi ý a), b), c), d) ở mỗi câu, thí sinh chọn đúng hoặc sai.");
            sb.AppendLine();
            for (int i = 1; i <= 2; i++)
            {
                sb.AppendLine($"Câu {i}. [Thông hiểu - {subject}] Cho giả thiết bài toán câu {i}...");
                sb.AppendLine("a) [Đúng] [Mệnh đề a]");
                sb.AppendLine("b) [Đúng] [Mệnh đề b]");
                sb.AppendLine("c) [Sai] [Mệnh đề c]");
                sb.AppendLine("d) [Sai] [Mệnh đề d]");
                sb.AppendLine("Đáp án: a-Đ, b-Đ, c-S, d-S");
                sb.AppendLine();
            }
            for (int i = 3; i <= 4; i++)
            {
                sb.AppendLine($"Câu {i}. [Vận dụng - {subject}] Cho bài toán thực tế câu {i}...");
                sb.AppendLine("a) [Sai] [Mệnh đề a]");
                sb.AppendLine("b) [Đúng] [Mệnh đề b]");
                sb.AppendLine("c) [Đúng] [Mệnh đề c]");
                sb.AppendLine("d) [Sai] [Mệnh đề d]");
                sb.AppendLine("Đáp án: a-S, b-Đ, c-Đ, d-S");
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

        private static string BuildMatrixOutlineInformatics11(string subject, string gradeStr, int duration)
        {
            var sb = new StringBuilder();
            sb.AppendLine("[THÔNG TIN MA TRẬN ĐỀ THI]");
            sb.AppendLine($"Môn học: {subject.ToUpper()} | Khối lớp: {gradeStr} | Thời gian: {duration} phút");
            sb.AppendLine("Cấu trúc đề: 2 Phần • 28 Câu hỏi (24 TNKQ + 4 Đúng-Sai) • Thang điểm: 10.0 điểm");
            sb.AppendLine("Phân bổ nhận thức: Nhận biết 40% (4.0đ) | Thông hiểu 30% (3.0đ) | Vận dụng 30% (3.0đ)");
            sb.AppendLine("==================================================================");
            sb.AppendLine();
            sb.AppendLine("PHẦN I. Câu trắc nghiệm nhiều phương án lựa chọn (24 câu - 6.0 điểm)");
            sb.AppendLine("Thí sinh trả lời từ câu 1 đến câu 24. Mỗi câu hỏi chỉ chọn một phương án đúng nhất.");
            sb.AppendLine();

            string[] topics = {
                "Khái niệm HĐH và phần mềm ứng dụng", "Lịch sử phát triển HĐH", "Quan hệ phần cứng và HĐH", "Vai trò HĐH",
                "Bộ phận chính trong máy tính", "Chức năng của CPU", "Chọn cấu hình máy tính", "Thiết bị vào ra thông dụng",
                "Xử lý kết nối thiết bị số", "Tìm kiếm thông tin trên mạng", "Toán tử logic tìm kiếm", "Lưu trữ đám mây an toàn",
                "Chia sẻ tệp phân quyền", "Dịch vụ mạng trực tuyến", "Ứng xử văn hóa mạng", "Bản quyền phần mềm",
                "Phòng chống lừa đảo số", "Bảo vệ thông tin cá nhân", "Quy tắc an toàn mạng", "Khái niệm cơ sở dữ liệu",
                "Bảng và khóa chính CSDL", "Khai thác dữ liệu quản lý", "Hệ quản trị CSDL", "Chức năng bảo mật DBMS"
            };

            string[] levels = {
                "Nhận biết", "Nhận biết", "Thông hiểu", "Thông hiểu",
                "Nhận biết", "Thông hiểu", "Vận dụng", "Thông hiểu",
                "Vận dụng", "Thông hiểu", "Thông hiểu", "Vận dụng",
                "Vận dụng", "Vận dụng", "Nhận biết", "Nhận biết",
                "Vận dụng", "Vận dụng", "Vận dụng", "Nhận biết",
                "Thông hiểu", "Thông hiểu", "Nhận biết", "Nhận biết"
            };

            char[] ans = { 'A', 'B', 'C', 'D', 'A', 'B', 'C', 'A', 'D', 'B', 'C', 'A', 'B', 'D', 'C', 'A', 'B', 'D', 'C', 'A', 'B', 'C', 'A', 'D' };

            for (int i = 1; i <= 24; i++)
            {
                sb.AppendLine($"Câu {i}. [{levels[i - 1]} - {topics[i - 1]}] [Nội dung câu hỏi {i} môn {subject}]");
                sb.AppendLine(ans[i - 1] == 'A' ? "*A. [Phương án đúng A]" : "A. [Phương án A]");
                sb.AppendLine(ans[i - 1] == 'B' ? "*B. [Phương án đúng B]" : "B. [Phương án B]");
                sb.AppendLine(ans[i - 1] == 'C' ? "*C. [Phương án đúng C]" : "C. [Phương án C]");
                sb.AppendLine(ans[i - 1] == 'D' ? "*D. [Phương án đúng D]" : "D. [Phương án D]");
                sb.AppendLine($"Đáp án: {ans[i - 1]}");
                sb.AppendLine();
            }

            sb.AppendLine("PHẦN II. Câu trắc nghiệm đúng sai (4 câu - 4.0 điểm)");
            sb.AppendLine("Thí sinh trả lời từ câu 1 đến câu 4. Trong mỗi ý a), b), c), d) ở mỗi câu, thí sinh chọn đúng hoặc sai.");
            sb.AppendLine();

            string[] p2Topics = {
                "Bộ phận chính bên trong máy tính và bộ nhớ",
                "Cổng giao tiếp và thiết bị ngoại vi số",
                "An toàn dữ liệu và phòng chống mã độc trên Internet",
                "Lưu trữ đám mây và chia sẻ tài nguyên mạng"
            };

            for (int i = 1; i <= 4; i++)
            {
                sb.AppendLine($"Câu {i}. [{p2Topics[i - 1]}] Cho các nhận định liên quan đến {p2Topics[i - 1]}. Xét tính đúng sai của mỗi ý sau:");
                sb.AppendLine("a) [Đúng] [Nhận định ý a]");
                sb.AppendLine("b) [Đúng] [Nhận định ý b]");
                sb.AppendLine("c) [Sai] [Nhận định ý c]");
                sb.AppendLine("d) [Sai] [Nhận định ý d]");
                sb.AppendLine("Đáp án: a-Đ, b-Đ, c-S, d-S");
                sb.AppendLine();
            }

            return sb.ToString();
        }

        public void GenerateExamWithAi() => BtnAiGenerateExam_Click(this, new RoutedEventArgs());

        public void ApplyAiMatrixConfig(string subject, string gradeStr, string durationStr, string semester, string extraRequirements)
        {
            foreach (ComboBoxItem item in CmbSubject.Items)
            {
                if (item.Content?.ToString()?.Contains(subject, StringComparison.OrdinalIgnoreCase) == true)
                {
                    CmbSubject.SelectedItem = item;
                    break;
                }
            }

            foreach (ComboBoxItem item in CmbGrade.Items)
            {
                if (item.Content?.ToString()?.Contains(gradeStr, StringComparison.OrdinalIgnoreCase) == true)
                {
                    CmbGrade.SelectedItem = item;
                    break;
                }
            }

            foreach (ComboBoxItem item in CmbDuration.Items)
            {
                if (item.Content?.ToString()?.Contains(durationStr, StringComparison.OrdinalIgnoreCase) == true)
                {
                    CmbDuration.SelectedItem = item;
                    break;
                }
            }

            if (!string.IsNullOrWhiteSpace(extraRequirements))
            {
                TxtExamTopic.Text = extraRequirements;
            }

            GenerateExamWithAi();
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

            bool isInformatics = subject.IndexOf("tin", StringComparison.OrdinalIgnoreCase) >= 0 || gradeStr.Contains("11");
            if (isInformatics && duration == 90) duration = 45;

            int tnCount = _currentMatrixData?.Rows?.Sum(r => r.TnNb + r.TnTh + r.TnVd) ?? (isInformatics ? 24 : 12);
            int dsItems = _currentMatrixData?.Rows?.Sum(r => r.DsNb + r.DsTh + r.DsVd) ?? (isInformatics ? 16 : 8);
            int dsQuestions = dsItems > 0 ? (dsItems + 3) / 4 : 4;
            int tlnCount = _currentMatrixData?.Rows?.Sum(r => r.TlnNb + r.TlnTh + r.TlnVd) ?? (isInformatics ? 0 : 6);

            int totalExamQ = tnCount + dsQuestions + tlnCount;

            BtnAiGenerateExam.IsEnabled = false;
            ProgExam.Visibility = Visibility.Visible;
            InfoExamNotification.Severity = Wpf.Ui.Controls.InfoBarSeverity.Informational;
            InfoExamNotification.Title = "Đang soạn đề thi theo ma trận";
            InfoExamNotification.Message = $"Đang truy xuất ngân hàng câu hỏi và khởi tạo đề thi {totalExamQ} câu ({subject} - {gradeStr})...";
            InfoExamNotification.IsOpen = true;

            try
            {
                var matrixConfig = new ExamMatrixConfig
                {
                    Subject = subject,
                    Grade = grade,
                    Part1Count = tnCount,
                    Part2Count = dsQuestions,
                    Part3Count = tlnCount,
                    DurationMinutes = duration,
                    CognitiveDistribution = new Dictionary<string, int>
                    {
                        ["Nhận biết"] = 40,
                        ["Thông hiểu"] = 30,
                        ["Vận dụng"] = 20,
                        ["Vận dụng cao"] = 10
                    }
                };

                string connStr = SqliteSchemaAdapter.GetActiveConnectionString();
                var qbService = new QuestionBankService(connStr);
                await qbService.InitializeDatabaseAsync();

                var draftResult = await qbService.GenerateExamFromMatrixAsync(matrixConfig, qbService);

                if (_currentMatrixData == null || _currentMatrixData.Rows.Count == 0)
                {
                    _currentMatrixData = isInformatics ? MatrixWordExporter.CreateInformatics11Matrix() : MatrixWordExporter.CreateStandardHighSchoolMatrix(subject, gradeStr);
                }
                _currentMatrixData.DurationMinutes = duration;

                if (draftResult != null && draftResult.Success && draftResult.TotalSelectedQuestions > 0)
                {
                    TxtExamContent.Text = FormatDraftResultToExamText(draftResult, subject, gradeStr, duration);
                }
                else
                {
                    TxtExamContent.Text = isInformatics
                        ? BuildSampleExamInformatics11Questions(subject, gradeStr)
                        : BuildSampleExam22Questions(subject, gradeStr);
                }

                if (ChkBraceMathMatrix.IsChecked == true)
                {
                    TxtExamContent.Text = ConvertView.NormalizeContent(TxtExamContent.Text, true, true);
                }

                TxtExamStats.Text = $"Đề thi hoàn chỉnh: {totalExamQ} câu hỏi ({subject} {gradeStr})";
                InfoExamNotification.Severity = Wpf.Ui.Controls.InfoBarSeverity.Success;
                InfoExamNotification.Title = "Soạn đề theo ma trận thành công";
                InfoExamNotification.Message = $"Đã khởi tạo đề thi {totalExamQ} câu chuẩn các mức độ nhận thức cho {subject} {gradeStr}!";
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

            string defaultDir = StorageLocationService.GetDefaultExportDirectory();
            var saveDialog = new Microsoft.Win32.SaveFileDialog
            {
                Filter = "Tài liệu Microsoft Word (*.docx)|*.docx",
                FileName = $"De_Thi_Ma_Tran_BGD_{DateTime.Now:yyyyMMdd_HHmm}.docx",
                InitialDirectory = Directory.Exists(defaultDir) ? defaultDir : Environment.CurrentDirectory,
                Title = "Lưu Đề thi & Ma trận đặc tả Word"
            };

            if (saveDialog.ShowDialog() == true)
            {
                try
                {
                    string? chosenDir = Path.GetDirectoryName(saveDialog.FileName);
                    if (!string.IsNullOrEmpty(chosenDir))
                    {
                        StorageLocationService.SetDefaultExportDirectory(chosenDir);
                    }

                    string subject = (CmbSubject.SelectedItem as ComboBoxItem)?.Content?.ToString() ?? "Toán học";
                    string grade = (CmbGrade.SelectedItem as ComboBoxItem)?.Content?.ToString() ?? "Lớp 12";

                    if (_currentMatrixData == null)
                    {
                        _currentMatrixData = MatrixWordExporter.CreateStandardHighSchoolMatrix(subject, grade);
                    }

                    // Xuất CẢ BẢNG 1 (MA TRẬN 19 CỘT LANDSCAPE) VÀ BẢNG 2 (BẢN ĐẶC TẢ 6 CỘT) CÙNG NỘI DUNG ĐỀ THI
                    MatrixWordExporter.ExportMatrixDocx(saveDialog.FileName, _currentMatrixData, content);

                    if (StorageLocationService.GetOpenAfterExport())
                    {
                        Process.Start(new ProcessStartInfo
                        {
                            FileName = saveDialog.FileName,
                            UseShellExecute = true
                        });
                        return;
                    }

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

        private static string BuildSampleExamInformatics11Questions(string subject, string grade)
        {
            var sb = new StringBuilder();
            sb.AppendLine("SỞ GIÁO DỤC VÀ ĐÀO TẠO                 ĐỀ KIỂM TRA CUỐI HỌC KÌ I - NĂM HỌC 2025 - 2026");
            sb.AppendLine("TRƯỜNG THPT NGUYỄN TRÃI                 Môn thi: TIN HỌC 11 (KNTT - ICT)");
            sb.AppendLine("MÃ ĐỀ: 101                             Thời gian làm bài: 45 phút (không kể thời gian phát đề)");
            sb.AppendLine();

            sb.AppendLine("PHẦN I. Câu trắc nghiệm nhiều phương án lựa chọn (Thí sinh trả lời từ câu 1 đến câu 24. Mỗi câu đúng được 0,25 điểm).");
            sb.AppendLine();

            string[] qTexts = new string[]
            {
                // Câu 1 - NB: Khái niệm HĐH
                "Hệ điều hành nào dưới đây là hệ điều hành mã nguồn mở?\nA. Windows 11.\nB. macOS Sonoma.\nC. Linux Ubuntu.\nD. iOS 17.\nĐáp án: C",
                // Câu 2 - NB: Lịch sử HĐH
                "Giao diện người dùng đồ họa (GUI) lần đầu tiên được thương mại hóa phổ biến trên hệ điều hành nào?\nA. MS-DOS.\nB. Mac OS và Windows.\nC. CP/M.\nD. Unix thuần văn bản.\nĐáp án: B",
                // Câu 3 - TH: Quan hệ phần cứng và HĐH
                "Phát biểu nào sau đây thể hiện đúng nhất vai trò trung gian của hệ điều hành?\nA. Hệ điều hành quản lý, điều phối phần cứng và cung cấp môi trường chạy cho phần mềm ứng dụng.\nB. Hệ điều hành thay thế hoàn toàn chức năng tính toán số học của CPU.\nC. Hệ điều hành là phần mềm ứng dụng chuyên dùng để soạn thảo văn bản.\nD. Hệ điều hành chỉ kích hoạt khi máy tính mất kết nối mạng Internet.\nĐáp án: A",
                // Câu 4 - TH: Phần mềm nguồn mở và đóng
                "Phần mềm thương mại đóng gói có đặc điểm nào dưới đây?\nA. Cung cấp mã nguồn mở miễn phí cho cộng đồng tự do chỉnh sửa.\nB. Người dùng phải mua bản quyền sử dụng và không được phép xem hay sửa đổi mã nguồn.\nC. Bắt buộc phải chạy trực tuyến trên trình duyệt web không cần cài đặt.\nD. Không được nhà sản xuất phát hành bản vá lỗi hay cập nhật bảo mật.\nĐáp án: B",
                // Câu 5 - NB: Bộ phận máy tính
                "Thiết bị nào được ví như \"bộ não\" của máy tính, đảm nhiệm chức năng xử lý dữ liệu và điều khiển mọi hoạt động?\nA. Bộ vi xử lý (CPU).\nB. Bộ nhớ truy cập ngẫu nhiên (RAM).\nC. Bộ nguồn (Power Supply).\nD. Ổ cứng thể rắn (SSD).\nĐáp án: A",
                // Câu 6 - TH: Bộ nhớ trong
                "Khi ngắt nguồn điện cấp cho máy tính, toàn bộ dữ liệu đang lưu trên thiết bị nào sau đây sẽ bị mất?\nA. Ổ đĩa cứng HDD.\nB. Bộ nhớ RAM.\nC. Bộ nhớ ROM trên bo mạch chủ.\nD. Thẻ nhớ flash USB.\nĐáp án: B",
                // Câu 7 - VD: Cấu hình PC
                "Một nhà thiết kế đồ họa 3D và render video 4K cần xây dựng cấu hình máy tính. Thành phần nào sau đây cần ưu tiên đầu tư ngân sách cao nhất?\nA. Bàn phím cơ có đèn nền RGB.\nB. CPU đa nhân tốc độ cao, Card đồ họa rời (GPU) mạnh và RAM tối thiểu 32GB.\nC. Ổ đĩa quang DVD-RW tốc độ đọc cao.\nD. Chuột không dây tiết kiệm pin.\nĐáp án: B",
                // Câu 8 - TH: Cổng giao tiếp
                "Chuẩn cổng kết nối nào hiện nay truyền tải đồng thời cả tín hiệu hình ảnh chất lượng cao và âm thanh số qua một sợi cáp duy nhất?\nA. Cổng VGA.\nB. Cổng HDMI.\nC. Cổng Audio Jack 3.5mm.\nD. Cổng bàn phím PS/2.\nĐáp án: B",
                // Câu 9 - VD: Xử lý ngoại vi
                "Khi cắm thẻ nhớ USB vào máy tính, hệ điều hành thông báo \"USB Device Not Recognized\". Thao tác kiểm tra an toàn đầu tiên cần thực hiện là gì?\nA. Tháo rời bo mạch chủ ra kiểm tra mạch điện.\nB. Cắm thử sang cổng USB khác hoặc khởi động lại máy để nạp lại trình điều khiển (Driver).\nC. Dùng búa gõ nhẹ vào đầu cắm thẻ nhớ USB.\nD. Cài đặt lại toàn bộ hệ điều hành ngay lập tức.\nĐáp án: B",
                // Câu 10 - TH: Cú pháp tìm kiếm
                "Khi tìm kiếm tài liệu trên Google, để giới hạn kết quả chỉ trong các trang web giáo dục của Việt Nam, cú pháp nào sau đây là đúng?\nA. tu_khoa filetype:pdf\nB. tu_khoa site:edu.vn\nC. tu_khoa related:edu.vn\nD. tu_khoa inanchor:vietnam\nĐáp án: B",
                // Câu 11 - TH: Toán tử tìm kiếm
                "Cú pháp tìm kiếm nào trên Google yêu cầu trả về các trang chứa chính xác cụm từ \"Chuyển đổi số trong giáo dục\"?\nA. *Chuyển đổi số trong giáo dục*\nB. \"Chuyển đổi số trong giáo dục\"\nC. [Chuyển đổi số trong giáo dục]\nD. ~Chuyển đổi số trong giáo dục\nĐáp án: B",
                // Câu 12 - VD: Đám mây
                "Để nhiều thành viên trong lớp cùng chỉnh sửa một báo cáo thuyết trình nhóm theo thời gian thực mà không bị ghi đè xung đột, giải pháp tối ưu là gì?\nA. Lưu tệp vào ổ USB rồi chuyền tay nhau từng người sửa.\nB. Tải tệp lên Google Drive và chia sẻ quyền chỉnh sửa (Editor) cho các thành viên.\nC. Nén tệp đính kèm gửi thư điện tử liên tục qua lại sau mỗi câu sửa.\nD. In bài ra giấy rồi lấy bút ghi chú trực tiếp.\nĐáp án: B",
                // Câu 13 - VD: Phân quyền chia sẻ
                "Khi chia sẻ đề cương ôn thi học kì cho toàn thể học sinh trong trường tải về xem, giáo viên nên thiết lập quyền chia sẻ liên kết ở mức nào?\nA. Bất kỳ ai có liên kết đều có quyền Chỉnh sửa (Editor).\nB. Bất kỳ ai có liên kết chỉ có quyền Xem (Viewer).\nC. Bàn giao quyền sở hữu tệp (Transfer Ownership).\nD. Cấp quyền quản trị viên thư mục gốc cá nhân.\nĐáp án: B",
                // Câu 14 - VD: Dịch vụ mạng
                "Em nhận được một email từ địa chỉ lạ mạo danh ngân hàng yêu cầu bấm vào liên kết để xác thực và nhận thưởng 2 triệu đồng. Em nên xử lý như thế nào?\nA. Nhấp ngay vào liên kết và nhập số tài khoản ngân hàng cùng mã OTP.\nB. Chuyển tiếp email cho người thân để cùng nhận thưởng.\nC. Tuyệt đối không bấm vào liên kết, đánh dấu báo cáo lừa đảo (Phishing) và xóa thư.\nD. Trả lời email yêu cầu ngân hàng chuyển khoản trực tiếp.\nĐáp án: C",
                // Câu 15 - NB: Văn hóa mạng
                "Hành vi nào sau đây vi phạm chuẩn mực đạo đức và văn hóa ứng xử trên không gian mạng?\nA. Chia sẻ những bài viết hướng dẫn học tập có bản quyền rõ ràng.\nB. Bình luận xúc phạm danh dự, nhân phẩm hoặc bịa đặt thông tin sai sự thật về người khác.\nC. Lịch sự tranh luận, tôn trọng sự khác biệt trong nhóm thảo luận.\nD. Ghi rõ nguồn trích dẫn khi sử dụng hình ảnh của tác giả khác.\nĐáp án: B",
                // Câu 16 - NB: Bản quyền
                "Hành vi nào dưới đây là tôn trọng bản quyền phần mềm và quyền tác giả?\nA. Sử dụng các công cụ bẻ khóa phần mềm thương mại để dùng miễn phí.\nB. Mua giấy phép bản quyền của nhà sản xuất hoặc dùng phần mềm nguồn mở theo đúng giấy phép.\nC. Sao chép đồ án của bạn học rồi tự nhận là của mình để nộp bài.\nD. Tự ý tải lậu video khóa học có phí để bán lại kiếm tiền.\nĐáp án: B",
                // Câu 17 - VD: An toàn mật khẩu
                "Biện pháp nào giúp bảo vệ tài khoản cá nhân (Google, Facebook) an toàn nhất trước nguy cơ bị đánh cắp mật khẩu?\nA. Đặt mật khẩu ngắn như \"123456\" hoặc ngày tháng năm sinh cho dễ nhớ.\nB. Kích hoạt tính năng xác thực hai yếu tố (2FA) và đặt mật khẩu mạnh dài trên 8 ký tự gồm chữ hoa, chữ thường, số và ký tự đặc biệt.\nC. Dùng chung một mật khẩu duy nhất cho tất cả các dịch vụ trực tuyến.\nD. Luôn lưu mật khẩu tự động trên máy tính ở quán net công cộng.\nĐáp án: B",
                // Câu 18 - VD: Nhận biết lừa đảo
                "Một tin nhắn mạo danh thông báo: \"Tài khoản ngân hàng của quý khách đang bị khóa, vui lòng truy cập http://vietcombank-auth.vip để mở khóa\". Đây là hình thức tấn công nào?\nA. Tấn công từ chối dịch vụ (DDoS).\nB. Tấn công lừa đảo giả mạo (Phishing).\nC. Nhiễm virus qua cổng hồng ngoại.\nD. Tấn công vật lý vào máy tính bàn.\nĐáp án: B",
                // Câu 19 - VD: Luật An ninh mạng
                "Theo Luật An ninh mạng Việt Nam, cá nhân có hành vi cung cấp, chia sẻ thông tin giả mạo, thông tin sai sự thật xuyên tạc trên mạng xã hội sẽ bị xử lý như thế nào?\nA. Không bị xử lý vì mạng xã hội là thế giới ảo tự do ngôn luận.\nB. Được tuyên dương vì đã cung cấp thêm thông tin cho cộng đồng mạng.\nC. Bị xử phạt vi phạm hành chính hoặc truy cứu trách nhiệm hình sự tùy theo tính chất, mức độ hậu quả.\nD. Chỉ bị nhắc nhở bằng miệng mà không có chế tài xử phạt.\nĐáp án: C",
                // Câu 20 - NB: Khái niệm CSDL
                "Khái niệm nào sau đây định nghĩa chính xác nhất về Cơ sở dữ liệu (Database)?\nA. Là tập hợp các linh kiện phần cứng dùng để lưu trữ dữ liệu.\nB. Là tập hợp các dữ liệu có liên quan với nhau, được lưu trữ có cấu trúc trên thiết bị nhớ để nhiều người dùng cùng khai thác.\nC. Là một trang tính Excel đơn lẻ dùng để thống kê chi tiêu hàng ngày.\nD. Là phần mềm dùng để trình chiếu văn bản và hình ảnh.\nĐáp án: B",
                // Câu 21 - TH: Khóa chính
                "Trong bảng CSDL quản lý học sinh gồm các cột: Mã học sinh, Họ và tên, Ngày sinh, Địa chỉ. Cột nào thích hợp nhất để làm Khóa chính (Primary Key)?\nA. Họ và tên.\nB. Ngày sinh.\nC. Mã học sinh.\nD. Địa chỉ.\nĐáp án: C",
                // Câu 22 - TH: Khai thác CSDL
                "Thao tác nào sau đây thuộc nhóm chức năng cập nhật dữ liệu của hệ quản trị cơ sở dữ liệu?\nA. Tìm kiếm danh sách học sinh đạt danh hiệu học sinh xuất sắc.\nB. Lập báo cáo thống kê kết quả học tập của toàn trường.\nC. Bổ sung thêm hồ sơ của một học sinh mới chuyển trường vào bảng HOC_SINH.\nD. Xem thông tin cá nhân của một giáo viên chủ nhiệm.\nĐáp án: C",
                // Câu 23 - NB: Hệ quản trị CSDL
                "Phần mềm nào sau đây là một Hệ quản trị cơ sở dữ liệu quan hệ (RDBMS) phổ biến?\nA. Microsoft Access / MySQL.\nB. Adobe Photoshop.\nC. Google Chrome.\nD. VLC Media Player.\nĐáp án: A",
                // Câu 24 - NB: Bảo mật CSDL
                "Chức năng phân quyền truy cập trong hệ quản trị cơ sở dữ liệu nhằm mục đích gì?\nA. Tăng dung lượng lưu trữ của ổ đĩa cứng máy chủ.\nB. Đảm bảo mỗi người dùng chỉ được thực hiện những quyền hạn nhất định trên dữ liệu được phân công.\nC. Giúp máy tính tự động sửa lỗi nguồn điện khi cúp điện đột ngột.\nD. Tăng tốc độ hiển thị hình ảnh trên giao diện đồ họa.\nĐáp án: B"
            };

            for (int i = 0; i < qTexts.Length; i++)
            {
                sb.AppendLine($"Câu {i + 1}. {qTexts[i]}");
                sb.AppendLine();
            }

            sb.AppendLine("PHẦN II. Câu trắc nghiệm Đúng / Sai (Thí sinh trả lời từ câu 1 đến câu 4. Trong mỗi ý a), b), c), d) ở mỗi câu, thí sinh chọn đúng hoặc sai).");
            sb.AppendLine();

            // 4 câu Đúng - Sai
            sb.AppendLine("Câu 1. Cho các nhận định về các bộ phận chính bên trong máy tính:");
            sb.AppendLine("a) Bo mạch chủ (Mainboard) là bảng mạch chính kết nối các linh kiện như CPU, RAM và các thiết bị ngoại vi.");
            sb.AppendLine("b) Tốc độ xử lý của CPU thường được đo bằng đơn vị Gigabyte (GB).");
            sb.AppendLine("c) Dữ liệu lưu trong bộ nhớ RAM không bị mất đi khi mất nguồn điện cung cấp.");
            sb.AppendLine("d) ROM là bộ nhớ chỉ đọc, lưu trữ các chương trình vi mã khởi động hệ thống (BIOS/UEFI).");
            sb.AppendLine("Đáp án: a: Đ | b: S | c: S | d: Đ");
            sb.AppendLine();

            sb.AppendLine("Câu 2. Cho các nhận định về thiết bị ngoại vi và cổng giao tiếp số:");
            sb.AppendLine("a) Cổng HDMI hỗ trợ truyền tải cả tín hiệu hình ảnh độ nét cao và âm thanh số.");
            sb.AppendLine("b) Chuẩn cổng VGA hỗ trợ truyền tải cả tín hiệu âm thanh vòm kỹ thuật số.");
            sb.AppendLine("c) Cổng USB Type-C có ưu điểm cắm đảo chiều thuận tiện và hỗ trợ tốc độ truyền dữ liệu rất cao.");
            sb.AppendLine("d) Máy quét (Scanner) và máy in (Printer) đều là các thiết bị xuất dữ liệu của máy tính.");
            sb.AppendLine("Đáp án: a: Đ | b: S | c: Đ | d: S");
            sb.AppendLine();

            sb.AppendLine("Câu 3. Cho các nhận định về tìm kiếm thông tin và lưu trữ đám mây:");
            sb.AppendLine("a) Lưu trữ đám mây cho phép người dùng truy cập và đồng bộ tệp tin từ mọi thiết bị có kết nối Internet.");
            sb.AppendLine("b) Khi tìm kiếm trên Google, sử dụng dấu trừ (-) ngay trước một từ khóa giúp loại bỏ các kết quả chứa từ khóa đó.");
            sb.AppendLine("c) Người được chia sẻ tệp trên Google Drive với quyền \"Người chỉnh sửa\" có thể xóa vĩnh viễn tệp gốc của chủ sở hữu.");
            sb.AppendLine("d) Toán tử OR trong tìm kiếm Google yêu cầu trang web kết quả bắt buộc phải xuất hiện đồng thời tất cả các từ khóa.");
            sb.AppendLine("Đáp án: a: Đ | b: Đ | c: S | d: S");
            sb.AppendLine();

            sb.AppendLine("Câu 4. Cho các nhận định về an toàn thông tin và văn hóa ứng xử trên mạng:");
            sb.AppendLine("a) Mật khẩu mạnh nên có độ dài tối thiểu 8 ký tự, bao gồm cả chữ hoa, chữ thường, số và ký tự đặc biệt.");
            sb.AppendLine("b) Việc tải và sử dụng các bản vá bẻ khóa (crack) phần mềm là hành vi vi phạm Luật Sở hữu trí tuệ.");
            sb.AppendLine("c) Kích hoạt xác thực 2 bước (2FA) giúp ngăn chặn kẻ gian chiếm tài khoản ngay cả khi lộ mật khẩu cấp 1.");
            sb.AppendLine("d) Người dùng có thể tùy ý chia sẻ các thông tin chưa kiểm chứng lên mạng xã hội nếu không nhằm mục đích kinh doanh.");
            sb.AppendLine("Đáp án: a: Đ | b: Đ | c: Đ | d: S");
            sb.AppendLine();

            sb.AppendLine("BẢNG ĐÁP ÁN THAM KHẢO");
            sb.AppendLine("| Câu | Phần I | Phần II |");
            sb.AppendLine("|---|---|---|");
            char[] p1Ans = { 'C', 'B', 'A', 'B', 'A', 'B', 'B', 'B', 'B', 'B', 'B', 'B', 'B', 'C', 'B', 'B', 'B', 'B', 'C', 'B', 'C', 'C', 'A', 'B' };
            string[] p2Ans = { "Đ-S-S-Đ", "Đ-S-Đ-S", "Đ-Đ-S-S", "Đ-Đ-Đ-S" };

            for (int i = 1; i <= 24; i++)
            {
                string a1 = p1Ans[i - 1].ToString();
                string a2 = i <= 4 ? p2Ans[i - 1] : "-";
                sb.AppendLine($"| {i} | {a1} | {a2} |");
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
