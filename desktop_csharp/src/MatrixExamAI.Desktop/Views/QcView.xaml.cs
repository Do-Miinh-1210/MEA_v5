using System;
using System.Text;
using System.Windows;
using System.Windows.Controls;
using MatrixExamAI.Desktop.Services;

namespace MatrixExamAI.Desktop.Views
{
    public partial class QcView : UserControl
    {
        private readonly QcInspectionService _qcService = new QcInspectionService();
        private string _lastRawExamText = string.Empty;

        public QcView()
        {
            InitializeComponent();
            TxtQcReport.Text = string.Empty;
            TxtQcSummary.Text = "Sẵn sàng: Nhập nội dung đề thi hoặc nạp từ ConvertView để kiểm định chất lượng.";
        }

        private void LoadDefaultSampleAndRunQc()
        {
            TxtQcReport.Text = string.Empty;
        }

        private void BtnRunQc_Click(object sender, RoutedEventArgs e)
        {
            string currentText = TxtQcReport.Text;

            // Nếu ô văn bản đang chứa báo cáo QC cũ hoặc rỗng, dùng đề mẫu hoặc dữ liệu thô gần nhất
            if (string.IsNullOrWhiteSpace(currentText) || currentText.StartsWith("[KẾT QUẢ THẨM ĐỊNH") || currentText.StartsWith("[KẾT QUẢ KIỂM TRA"))
            {
                if (string.IsNullOrWhiteSpace(_lastRawExamText))
                {
                    _lastRawExamText = GetSampleExamText();
                }
                currentText = _lastRawExamText;
            }
            else
            {
                _lastRawExamText = currentText;
            }

            ExecuteInspection(currentText);
        }

        private void ExecuteInspection(string examText)
        {
            bool checkDup = ChkCheckDupOptions.IsChecked ?? true;
            bool checkAns = ChkCheckMissingAns.IsChecked ?? true;
            bool checkLatex = ChkCheckLatexSyntax.IsChecked ?? true;
            bool checkFormat = ChkCheckFormat.IsChecked ?? true;

            var report = _qcService.InspectText(examText, checkDup, checkAns, checkLatex, checkFormat);

            TxtQcReport.Text = report.DetailedReportText;
            TxtQcSummary.Text = report.SummaryText;

            if (report.IsPassed && report.WarningCount == 0)
            {
                TxtQcSummary.Foreground = System.Windows.Media.Brushes.ForestGreen;
                InfoQcNotification.Severity = Wpf.Ui.Controls.InfoBarSeverity.Success;
                InfoQcNotification.Title = "Thẩm định hoàn tất — Xuất sắc";
                InfoQcNotification.Message = $"Đã quét {report.TotalQuestions} câu hỏi. 100% đạt tiêu chuẩn in ấn và xuất bản Bộ GD&ĐT!";
            }
            else if (report.IsPassed)
            {
                TxtQcSummary.Foreground = System.Windows.Media.Brushes.DarkOrange;
                InfoQcNotification.Severity = Wpf.Ui.Controls.InfoBarSeverity.Warning;
                InfoQcNotification.Title = "Thẩm định hoàn tất — Có cảnh báo";
                InfoQcNotification.Message = $"Đề thi hợp lệ nhưng có {report.WarningCount} cảnh báo cần lưu ý trước khi in.";
            }
            else
            {
                TxtQcSummary.Foreground = System.Windows.Media.Brushes.Crimson;
                InfoQcNotification.Severity = Wpf.Ui.Controls.InfoBarSeverity.Error;
                InfoQcNotification.Title = "Phát hiện lỗi nghiêm trọng";
                InfoQcNotification.Message = $"Phát hiện {report.ErrorCount} lỗi cần chỉnh sửa. Bấm 'AI Tự động sửa lỗi' để khắc phục.";
            }

            InfoQcNotification.IsOpen = true;
        }

        private void BtnAutoFix_Click(object sender, RoutedEventArgs e)
        {
            string textToFix = _lastRawExamText;
            if (string.IsNullOrWhiteSpace(textToFix) || textToFix.StartsWith("[KẾT QUẢ"))
            {
                textToFix = GetSampleExamTextWithErrors();
            }

            var fixResult = _qcService.AutoFix(textToFix);
            _lastRawExamText = fixResult.FixedContent;

            // Chạy lại kiểm tra trên văn bản đã sửa
            ExecuteInspection(_lastRawExamText);

            string fixesSummary = fixResult.AppliedFixes.Count > 0
                ? string.Join("\n• ", fixResult.AppliedFixes)
                : "Không phát hiện lỗi cú pháp cần sửa.";

            MessageBox.Show(
                $"AI đã hoàn thành tự động sửa lỗi ({fixResult.FixesCount} sửa đổi):\n• {fixesSummary}\n\nĐề thi đã được cập nhật và kiểm tra lại thành công!",
                "AI Tự Động Sửa Lỗi Thành Công",
                MessageBoxButton.OK,
                MessageBoxImage.Information);
        }

        private static string GetSampleExamText()
        {
            return @"% Câu 1 [Nhận biết]_[Hàm số]
Cho hàm số $y = f(x)$ liên tục trên $\mathbb{R}$ và có đạo hàm $f'(x) = x(x - 1)^2$. Số điểm cực trị của hàm số là:
A. 1.
B. 2.
C. 3.
D. 0.
Đáp án: A

% Câu 2 [Thông hiểu]_[Nguyên hàm]
Tìm nguyên hàm của hàm số $f(x) = 2x + \cos(x)$.
A. $F(x) = x^2 + \sin(x) + C$.
B. $F(x) = x^2 - \sin(x) + C$.
C. $F(x) = 2 - \sin(x) + C$.
D. $F(x) = x^2 + \cos(x) + C$.
Đáp án: A

% Câu 3 [Vận dụng]_[Hệ phương trình]
Cho hệ phương trình:
\begin{align}
2x + y = 5 \\
x - 3y = -1
\end{align}
Nghiệm $(x; y)$ của hệ là:
A. $(2; 1)$.
B. $(1; 2)$.
C. $(3; -1)$.
D. $(-1; 3)$.
Đáp án: A";
        }

        private static string GetSampleExamTextWithErrors()
        {
            return @"% Câu 1 [Nhận biết]_[Hàm số]
Cho hàm số $y = f(x có đạo hàm $f'(x) = 0$. [cite: 1]
A. $x = 1$.
B. $x = 2$.
C. $x = 1$.
D. $x = 4$.
Đáp án: A

% Câu 2 [Thông hiểu]_[Hệ phương trình]
Giải hệ phương trình sau:
\begin{aligned}
2x + y = 5 \\
x - y = 1
\end{aligned}
\item1.Phương án thử nghiệm thứ nhất.
Đáp án: B";
        }
    }
}
