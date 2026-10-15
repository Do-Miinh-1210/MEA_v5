using System;
using System.Collections.ObjectModel;
using System.ComponentModel;
using System.Linq;
using System.Runtime.CompilerServices;
using System.Text;
using System.Windows;
using System.Windows.Controls;

namespace MatrixExamAI.Desktop.Views
{
    public class QuickGenRow : INotifyPropertyChanged
    {
        private int _stt;
        private string _topic = string.Empty;
        private string _questionType = "TN";
        private string _level = "NB";
        private int _count = 1;
        private double _pointsPerQuestion = 0.25;
        private string _requirement = string.Empty;

        public int Stt
        {
            get => _stt;
            set { _stt = value; OnPropertyChanged(); }
        }

        public string Topic
        {
            get => _topic;
            set { _topic = value; OnPropertyChanged(); }
        }

        public string QuestionType
        {
            get => _questionType;
            set { _questionType = value; OnPropertyChanged(); }
        }

        public string Level
        {
            get => _level;
            set { _level = value; OnPropertyChanged(); }
        }

        public int Count
        {
            get => _count;
            set { _count = value; OnPropertyChanged(); }
        }

        public double PointsPerQuestion
        {
            get => _pointsPerQuestion;
            set { _pointsPerQuestion = value; OnPropertyChanged(); }
        }

        public string Requirement
        {
            get => _requirement;
            set { _requirement = value; OnPropertyChanged(); }
        }

        public event PropertyChangedEventHandler? PropertyChanged;
        protected void OnPropertyChanged([CallerMemberName] string? name = null) =>
            PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(name));
    }

    public partial class QuickGenDialog : Window
    {
        public ObservableCollection<QuickGenRow> Rows { get; } = new();
        public string Subject => (CmbSubject.SelectedItem as ComboBoxItem)?.Content?.ToString() ?? "Toán";
        public string Grade => (CmbGrade.SelectedItem as ComboBoxItem)?.Content?.ToString() ?? "12";
        public string Semester => (CmbSemester.SelectedItem as ComboBoxItem)?.Content?.ToString() ?? "Giữa kì II";
        public string Year => TxtYear.Text.Trim();
        public string Duration => (CmbDuration.SelectedItem as ComboBoxItem)?.Content?.ToString() ?? "90 phút";
        public string AdditionalRequirement => TxtAiRequirement.Text.Trim();

        public string GeneratedExamPrompt { get; private set; } = string.Empty;

        public QuickGenDialog()
        {
            InitializeComponent();
            DgQuickRows.ItemsSource = Rows;

            // Nạp 3 hàng mẫu ban đầu
            Rows.Add(new QuickGenRow { Stt = 1, Topic = "Hàm số và đồ thị", QuestionType = "TN", Level = "NB", Count = 1, PointsPerQuestion = 0.25 });
            Rows.Add(new QuickGenRow { Stt = 2, Topic = "Đạo hàm và ứng dụng", QuestionType = "TN", Level = "NB", Count = 1, PointsPerQuestion = 0.25 });
            Rows.Add(new QuickGenRow { Stt = 3, Topic = "Nguyên hàm và tích phân", QuestionType = "TN", Level = "NB", Count = 1, PointsPerQuestion = 0.25 });

            UpdateSummary();
        }

        private void UpdateSummary()
        {
            int totalQuestions = Rows.Sum(r => Math.Max(0, r.Count));
            double totalPoints = Rows.Sum(r => Math.Max(0, r.Count) * Math.Max(0, r.PointsPerQuestion));
            TxtSummary.Text = $"Tổng số: {totalQuestions} câu | Tổng điểm: {totalPoints:0.0} điểm";
        }

        private void ReindexRows()
        {
            for (int i = 0; i < Rows.Count; i++)
            {
                Rows[i].Stt = i + 1;
            }
            UpdateSummary();
        }

        private void BtnAddRow_Click(object sender, RoutedEventArgs e)
        {
            Rows.Add(new QuickGenRow
            {
                Stt = Rows.Count + 1,
                Topic = "Chủ đề " + (Rows.Count + 1),
                QuestionType = "TN",
                Level = "TH",
                Count = 1,
                PointsPerQuestion = 0.25
            });
            UpdateSummary();
        }

        private void BtnAdd5SampleRows_Click(object sender, RoutedEventArgs e)
        {
            string[] sampleTopics = { "Hàm số lượng giác", "Phương trình lượng giác", "Cấp số cộng và cấp số nhân", "Giới hạn dãy số", "Hình học không gian" };
            foreach (var t in sampleTopics)
            {
                Rows.Add(new QuickGenRow
                {
                    Stt = Rows.Count + 1,
                    Topic = t,
                    QuestionType = "TN",
                    Level = "TH",
                    Count = 1,
                    PointsPerQuestion = 0.25
                });
            }
            UpdateSummary();
        }

        private void BtnClearAllRows_Click(object sender, RoutedEventArgs e)
        {
            Rows.Clear();
            UpdateSummary();
        }

        private void BtnDeleteRow_Click(object sender, RoutedEventArgs e)
        {
            if (sender is FrameworkElement elem && elem.DataContext is QuickGenRow row)
            {
                Rows.Remove(row);
                ReindexRows();
            }
        }

        private void DgQuickRows_CellEditEnding(object sender, DataGridCellEditEndingEventArgs e)
        {
            Dispatcher.InvokeAsync(UpdateSummary, System.Windows.Threading.DispatcherPriority.Background);
        }

        private void RowData_Changed(object sender, SelectionChangedEventArgs e)
        {
            UpdateSummary();
        }

        private void TxtAiRequirement_GotFocus(object sender, RoutedEventArgs e)
        {
            if (TxtAiRequirement.Text.StartsWith("VD:"))
            {
                TxtAiRequirement.Text = "";
                TxtAiRequirement.Foreground = System.Windows.Media.Brushes.Black;
            }
        }

        private void TxtAiRequirement_LostFocus(object sender, RoutedEventArgs e)
        {
            if (string.IsNullOrWhiteSpace(TxtAiRequirement.Text))
            {
                TxtAiRequirement.Text = "VD: Câu hỏi phải có bảng số liệu, câu hỏi thực tế, không quá khó...";
                TxtAiRequirement.Foreground = new System.Windows.Media.SolidColorBrush(System.Windows.Media.Color.FromRgb(100, 116, 139));
            }
        }

        private void BtnApply15m_Click(object sender, RoutedEventArgs e)
        {
            Rows.Clear();
            string[] topics = { "Khảo sát hàm số", "Cực trị hàm số", "Đồng biến nghịch biến", "Tiệm cận đồ thị", "Tọa độ không gian", "Vectơ không gian", "Góc và khoảng cách" };
            for (int i = 0; i < 7; i++)
            {
                Rows.Add(new QuickGenRow { Stt = i + 1, Topic = topics[i], QuestionType = "TN", Level = i < 4 ? "NB" : "TH", Count = 1, PointsPerQuestion = 1.4 });
            }
            CmbDuration.SelectedIndex = 0;
            UpdateSummary();
            MessageBox.Show("Đã áp dụng mẫu đề 15 phút (7 câu Trắc nghiệm).", "Thông báo", MessageBoxButton.OK, MessageBoxImage.Information);
        }

        private void BtnApply45m_Click(object sender, RoutedEventArgs e)
        {
            Rows.Clear();
            // 12 TN
            for (int i = 1; i <= 12; i++)
                Rows.Add(new QuickGenRow { Stt = Rows.Count + 1, Topic = $"Chủ đề {i}", QuestionType = "TN", Level = i <= 6 ? "NB" : (i <= 10 ? "TH" : "VD"), Count = 1, PointsPerQuestion = 0.25 });
            // 2 DS
            for (int i = 1; i <= 2; i++)
                Rows.Add(new QuickGenRow { Stt = Rows.Count + 1, Topic = $"Chủ đề Đúng/Sai {i}", QuestionType = "DS", Level = "TH", Count = 1, PointsPerQuestion = 2.0 });
            // 3 TLN
            for (int i = 1; i <= 3; i++)
                Rows.Add(new QuickGenRow { Stt = Rows.Count + 1, Topic = $"Chủ đề Trả lời ngắn {i}", QuestionType = "TLN", Level = "VD", Count = 1, PointsPerQuestion = 1.0 });

            CmbDuration.SelectedIndex = 1;
            UpdateSummary();
            MessageBox.Show("Đã áp dụng mẫu đề 45 phút chuẩn BGD 2025 (12 TN + 2 DS + 3 TLN).", "Thông báo", MessageBoxButton.OK, MessageBoxImage.Information);
        }

        private void BtnApply60m_Click(object sender, RoutedEventArgs e)
        {
            Rows.Clear();
            for (int i = 1; i <= 15; i++)
                Rows.Add(new QuickGenRow { Stt = Rows.Count + 1, Topic = $"Chủ đề {i}", QuestionType = "TN", Level = i <= 8 ? "NB" : "TH", Count = 1, PointsPerQuestion = 0.2 });
            for (int i = 1; i <= 3; i++)
                Rows.Add(new QuickGenRow { Stt = Rows.Count + 1, Topic = $"Chủ đề Đúng/Sai {i}", QuestionType = "DS", Level = "TH", Count = 1, PointsPerQuestion = 1.33 });
            for (int i = 1; i <= 4; i++)
                Rows.Add(new QuickGenRow { Stt = Rows.Count + 1, Topic = $"Chủ đề Trả lời ngắn {i}", QuestionType = "TLN", Level = "VD", Count = 1, PointsPerQuestion = 0.75 });

            CmbDuration.SelectedIndex = 2;
            UpdateSummary();
            MessageBox.Show("Đã áp dụng mẫu đề 60 phút (15 TN + 3 DS + 4 TLN).", "Thông báo", MessageBoxButton.OK, MessageBoxImage.Information);
        }

        private void BtnApply90m_Click(object sender, RoutedEventArgs e)
        {
            Rows.Clear();
            // Chuẩn 22 câu THPT Bộ GD&ĐT 2025
            for (int i = 1; i <= 12; i++)
                Rows.Add(new QuickGenRow { Stt = Rows.Count + 1, Topic = $"Chủ đề {i}", QuestionType = "TN", Level = i <= 6 ? "NB" : (i <= 10 ? "TH" : "VD"), Count = 1, PointsPerQuestion = 0.25 });
            for (int i = 1; i <= 4; i++)
                Rows.Add(new QuickGenRow { Stt = Rows.Count + 1, Topic = $"Chủ đề Đúng/Sai {i}", QuestionType = "DS", Level = i <= 2 ? "TH" : "VD", Count = 1, PointsPerQuestion = 1.0 });
            for (int i = 1; i <= 6; i++)
                Rows.Add(new QuickGenRow { Stt = Rows.Count + 1, Topic = $"Chủ đề Trả lời ngắn {i}", QuestionType = "TLN", Level = i <= 4 ? "VD" : "VDC", Count = 1, PointsPerQuestion = 0.5 });

            CmbDuration.SelectedIndex = 3;
            UpdateSummary();
            MessageBox.Show("Đã áp dụng mẫu đề 90 phút thi tốt nghiệp THPT chuẩn BGD 2025 (12 TN + 4 DS + 6 TLN).", "Thông báo", MessageBoxButton.OK, MessageBoxImage.Information);
        }

        private void BtnCancel_Click(object sender, RoutedEventArgs e)
        {
            DialogResult = false;
            Close();
        }

        private void BtnCreateExam_Click(object sender, RoutedEventArgs e)
        {
            if (Rows.Count == 0)
            {
                MessageBox.Show("Vui lòng thêm ít nhất một hàng cấu trúc câu hỏi trước khi tạo đề.", "Thông báo", MessageBoxButton.OK, MessageBoxImage.Warning);
                return;
            }

            var sb = new StringBuilder();
            sb.AppendLine($"% ĐỀ THI TẠO NHANH CHUẨN BGD 2025");
            sb.AppendLine($"% Môn: {Subject} | Lớp: {Grade} | Kỳ: {Semester} | Năm học: {Year} | Thời lượng: {Duration}");
            if (!string.IsNullOrWhiteSpace(AdditionalRequirement) && !AdditionalRequirement.StartsWith("VD:"))
            {
                sb.AppendLine($"% Yêu cầu thêm: {AdditionalRequirement}");
            }
            sb.AppendLine();

            var tnRows = Rows.Where(r => r.QuestionType == "TN").ToList();
            var dsRows = Rows.Where(r => r.QuestionType == "DS").ToList();
            var tlnRows = Rows.Where(r => r.QuestionType == "TLN").ToList();
            var tlRows = Rows.Where(r => r.QuestionType == "TL").ToList();

            int qNum = 1;

            if (tnRows.Count > 0)
            {
                int endQ = qNum + tnRows.Sum(r => r.Count) - 1;
                sb.AppendLine($"PHẦN I. Câu trắc nghiệm nhiều phương án lựa chọn. Thí sinh trả lời từ câu {qNum} đến câu {endQ}. Mỗi câu hỏi thí sinh chỉ chọn một phương án.");
                foreach (var r in tnRows)
                {
                    for (int k = 0; k < r.Count; k++)
                    {
                        sb.AppendLine($"Câu {qNum}. [% {r.Level}]_[{r.Topic}] Nội dung câu hỏi trắc nghiệm về {r.Topic}:");
                        sb.AppendLine($"A. Phương án A.");
                        sb.AppendLine($"B. Phương án B.");
                        sb.AppendLine($"C. Phương án C.");
                        sb.AppendLine($"D. Phương án D.");
                        sb.AppendLine($"Lời giải:\nGiải thích chi tiết cho câu {qNum}. Chọn A.\n");
                        qNum++;
                    }
                }
            }

            if (dsRows.Count > 0)
            {
                int endQ = qNum + dsRows.Sum(r => r.Count) - 1;
                sb.AppendLine($"PHẦN II. Câu trắc nghiệm đúng sai. Thí sinh trả lời từ câu {qNum} đến câu {endQ}. Trong mỗi ý a), b), c), d) ở mỗi câu, thí sinh chọn đúng hoặc sai.");
                foreach (var r in dsRows)
                {
                    for (int k = 0; k < r.Count; k++)
                    {
                        sb.AppendLine($"Câu {qNum}. [% {r.Level}]_[{r.Topic}] Cho bài toán về {r.Topic}. Xét tính đúng sai của các mệnh đề sau:");
                        sb.AppendLine($"a) Mệnh đề thứ nhất liên quan đến {r.Topic}.");
                        sb.AppendLine($"b) Mệnh đề thứ hai liên quan đến {r.Topic}.");
                        sb.AppendLine($"c) Mệnh đề thứ ba liên quan đến {r.Topic}.");
                        sb.AppendLine($"d) Mệnh đề thứ tư liên quan đến {r.Topic}.");
                        sb.AppendLine($"Lời giải:\nGiải thích tính đúng sai cho từng ý a, b, c, d của câu {qNum}.\n");
                        qNum++;
                    }
                }
            }

            if (tlnRows.Count > 0)
            {
                int endQ = qNum + tlnRows.Sum(r => r.Count) - 1;
                sb.AppendLine($"PHẦN III. Câu trắc nghiệm trả lời ngắn. Thí sinh trả lời từ câu {qNum} đến câu {endQ}.");
                foreach (var r in tlnRows)
                {
                    for (int k = 0; k < r.Count; k++)
                    {
                        sb.AppendLine($"Câu {qNum}. [% {r.Level}]_[{r.Topic}] Tính giá trị hoặc giải bài toán về {r.Topic}.");
                        sb.AppendLine($"Đáp án: 10\n");
                        qNum++;
                    }
                }
            }

            if (tlRows.Count > 0)
            {
                int endQ = qNum + tlRows.Sum(r => r.Count) - 1;
                sb.AppendLine($"PHẦN IV. Tự luận. Thí sinh trình bày lời giải từ câu {qNum} đến câu {endQ}.");
                foreach (var r in tlRows)
                {
                    for (int k = 0; k < r.Count; k++)
                    {
                        sb.AppendLine($"Câu {qNum}. [% {r.Level}]_[{r.Topic}] Trình bày lời giải chi tiết cho bài toán {r.Topic}:");
                        sb.AppendLine($"Lời giải:\nCác bước thực hiện bài toán tự luận câu {qNum}.\n");
                        qNum++;
                    }
                }
            }

            GeneratedExamPrompt = sb.ToString();
            DialogResult = true;
            Close();
        }
    }
}
