using System;
using System.Collections.Generic;
using System.Text;
using System.Text.RegularExpressions;
using System.Threading;
using System.Threading.Tasks;
using System.Windows;
using System.Windows.Controls;
using MatrixExamAI.Desktop.Services;

namespace MatrixExamAI.Desktop.Views
{
    public class GeneratedExamConfig
    {
        public string Subject { get; set; } = "Toán";
        public string Grade { get; set; } = "12";
        public string Duration { get; set; } = "90 phút";
        public string Semester { get; set; } = "Cuối kì I";
        public string ExtraRequirements { get; set; } = string.Empty;
    }

    public partial class SmartPromptDialog : Window
    {
        public GeneratedExamConfig? GeneratedMatrixConfig { get; private set; }
        public string? GeneratedQuestionLatex { get; private set; }

        private CancellationTokenSource? _cts;
        private readonly Dictionary<int, string> _promptTemplates = new();

        public SmartPromptDialog()
        {
            InitializeComponent();
            InitPromptTemplates();
            if (LstPromptTemplates.Items.Count > 0)
            {
                LstPromptTemplates.SelectedIndex = 0;
            }
        }

        private void InitPromptTemplates()
        {
            _promptTemplates[0] = ConvertView.GetExTestPromptTemplate("Toán", 12);

            _promptTemplates[1] = @"Bạn là chuyên gia xây dựng ma trận và bản đặc tả đề thi chuẩn Bộ Giáo dục & Đào tạo 2025.
NHIỆM VỤ: Hãy xây dựng bảng ma trận 3 phần (Trắc nghiệm nhiều lựa chọn, Đúng/Sai, Trả lời ngắn) cho đề kiểm tra định kỳ môn Toán lớp 12.
CẤU TRÚC BẮT BUỘC:
- Phần I (3,0 điểm): 12 câu trắc nghiệm nhiều lựa chọn (mỗi câu 0,25 điểm).
- Phần II (4,0 điểm): 4 câu trắc nghiệm Đúng/Sai (mỗi câu 4 ý a, b, c, d; tính điểm lũy tiến 0.1 - 0.25 - 0.5 - 1.0 điểm).
- Phần III (3,0 điểm): 6 câu trả lời ngắn (mỗi câu 0,5 điểm).
Phân bổ nhận thức: ~40% Nhận biết, ~30% Thông hiểu, ~20% Vận dụng, ~10% Vận dụng cao.";

            _promptTemplates[2] = @"Bạn là giáo viên Toán THPT giàu kinh nghiệm đổi mới phương pháp giảng dạy.
NHIỆM VỤ: Hãy biên soạn 3 câu hỏi trắc nghiệm Toán 12 có ngữ cảnh thực tế (kinh tế, tài chính, chuyển động vật lý, sinh học, kỹ thuật đo đạc) theo chuẩn cấu trúc LaTeX ex_test.
Yêu cầu:
1. Có bảng số liệu hoặc hàm số mô tả hiện tượng thực tế.
2. Công thức toán kẹp trong ${...}$.
3. Đặt đáp án đúng bằng \True trong \choice.
4. Có phần \loigiai giải thích chi tiết ý nghĩa thực tiễn của bài toán.";

            _promptTemplates[3] = @"Bạn là trợ lý kiểm định chất lượng đề thi (QC Auditor) của MatrixExamAI.
NHIỆM VỤ: Kiểm tra toàn diện văn bản đề thi LaTeX dưới đây:
1. Phát hiện câu hỏi thiếu đáp án đúng \True trong môi trường \choice.
2. Kiểm tra dấu đóng/mở ngoặc ${...}$, \begin{ex} ... \end{ex}, \loigiai{...}.
3. Tách các thẻ \item thừa nếu có.
4. Chuẩn hóa môi trường aligned sang align khi ở dạng công thức hệ độc lập.
5. Xuất lại mã nguồn sạch sẽ, sẵn sàng biên dịch sang Word không lỗi.";

            _promptTemplates[4] = @"Bạn là chuyên gia lập trình đồ họa TikZ trong LaTeX Toán THPT.
NHIỆM VỤ: Hãy viết mã nguồn TikZ hoàn chỉnh cho hình vẽ hình học không gian (chóp S.ABCD đáy hình vuông, SA vuông góc đáy, có góc giữa mặt phẳng và mặt phẳng).
Yêu cầu:
1. Dùng gói \usepackage{tikz}, \usepackage{tkz-euclide}.
2. Đoạn khuất dùng nét đứt [dashed], đoạn thấy dùng nét liền.
3. Ký hiệu góc vuông tại chân đường cao A.
4. Đặt toàn bộ mã trong môi trường \begin{tikzpicture}[scale=1] ... \end{tikzpicture}.";
        }

        private void BtnPreset15m_Click(object sender, RoutedEventArgs e)
        {
            TxtExamPromptInput.Text = "Đề kiểm tra 15 phút môn Toán 12 chương Đạo hàm, gồm 7 câu trắc nghiệm 4 lựa chọn (4 Nhận biết, 3 Thông hiểu).";
        }

        private void BtnPreset45m_Click(object sender, RoutedEventArgs e)
        {
            TxtExamPromptInput.Text = "Đề kiểm tra 1 tiết 45 phút môn Toán 12 chương Đạo hàm và ứng dụng, gồm 12 câu trắc nghiệm (3 điểm), 2 câu đúng sai (4 điểm) và 3 câu trả lời ngắn (3 điểm).";
        }

        private void BtnPreset60m_Click(object sender, RoutedEventArgs e)
        {
            TxtExamPromptInput.Text = "Đề kiểm tra 60 phút môn Toán 12 giữa kỳ 1, gồm 15 câu trắc nghiệm, 3 câu đúng sai, 4 câu trả lời ngắn và 1 câu tự luận nâng cao.";
        }

        private void BtnPreset90m_Click(object sender, RoutedEventArgs e)
        {
            TxtExamPromptInput.Text = "Đề kiểm tra 90 phút môn Toán 12 cuối kỳ 1 chuẩn Bộ GD&ĐT 2025, gồm 12 câu trắc nghiệm nhiều lựa chọn, 4 câu đúng sai và 6 câu trả lời ngắn.";
        }

        private async void BtnParseExamPrompt_Click(object sender, RoutedEventArgs e)
        {
            string input = TxtExamPromptInput.Text?.Trim() ?? string.Empty;
            if (string.IsNullOrWhiteSpace(input))
            {
                MessageBox.Show("Vui lòng nhập mô tả yêu cầu đề thi.", "Chưa có thông tin", MessageBoxButton.OK, MessageBoxImage.Warning);
                return;
            }

            SetBusy(true, "AI đang phân tích mô tả đề thi...");
            _cts?.Dispose();
            _cts = new CancellationTokenSource();

            try
            {
                // Quy tắc phân tích thông minh: kết hợp trích xuất rule-based và AI prompt
                var config = ParseConfigFromText(input);

                string aiPrompt = $@"Bạn là chuyên gia sư phạm THPT. Hãy phân tích yêu cầu tạo đề kiểm tra sau:
""{input}""

Hãy xuất BẢN TÓM TẮT CẤU TRÚC VÀ MA TRẬN ĐỀ THI ngắn gọn, rõ ràng theo định dạng sau:
1. Môn học: {config.Subject} | Khối lớp: {config.Grade} | Thời lượng: {config.Duration} | Học kỳ: {config.Semester}
2. Cấu trúc câu hỏi: Số lượng câu Trắc nghiệm (TN), Đúng/Sai (DS), Trả lời ngắn (TLN), Tự luận (TL)
3. Ma trận phân bổ chủ đề và 4 mức độ nhận thức (Nhận biết, Thông hiểu, Vận dụng, Vận dụng cao)
4. Lời khuyên sư phạm khi ra đề.";

                var aiResult = await DesktopGeminiFactory.ExecutePromptAsync(prompt: aiPrompt, ct: _cts.Token);

                string resultText;
                if (aiResult.Success && !string.IsNullOrWhiteSpace(aiResult.Content))
                {
                    resultText = aiResult.Content.Trim();
                }
                else
                {
                    // Fallback phân tích nội bộ nếu chưa có API Key hoặc offline
                    resultText = $"[Phân tích tự động nội bộ]\n" +
                                 $"• Môn học: {config.Subject}\n" +
                                 $"• Khối lớp: {config.Grade}\n" +
                                 $"• Thời lượng: {config.Duration}\n" +
                                 $"• Học kỳ: {config.Semester}\n" +
                                 $"• Yêu cầu: {input}\n\n" +
                                 $"Cấu trúc đề được chuẩn hóa theo mẫu Bộ GD&ĐT 2025. Bấm 'Áp dụng vào Tạo đề / Ma trận' để nạp ngay cấu trúc này.";
                }

                TxtParsedDetails.Text = resultText;
                TxtParsedSummary.Text = $"✅ Phân tích thành công: Môn {config.Subject} Lớp {config.Grade} • {config.Duration} • {config.Semester}";
                BorderParsedSummary.Visibility = Visibility.Visible;

                GeneratedMatrixConfig = config;
                BtnApplyToMatrix.IsEnabled = true;
                SetBusy(false, "Đã phân tích xong cấu trúc đề thi.");
            }
            catch (OperationCanceledException)
            {
                SetBusy(false, "Đã hủy tác vụ phân tích.");
            }
            catch (Exception ex)
            {
                SetBusy(false, $"Lỗi phân tích: {ex.Message}");
                MessageBox.Show($"Đã xảy ra lỗi: {ex.Message}", "Lỗi", MessageBoxButton.OK, MessageBoxImage.Error);
            }
        }

        private static GeneratedExamConfig ParseConfigFromText(string text)
        {
            var cfg = new GeneratedExamConfig();
            string lower = text.ToLowerInvariant();

            // Môn
            if (lower.Contains("vật lý") || lower.Contains("vật lí") || lower.Contains("môn lý") || lower.Contains("môn lí")) cfg.Subject = "Vật lý";
            else if (lower.Contains("hóa học") || lower.Contains("môn hóa")) cfg.Subject = "Hóa học";
            else if (lower.Contains("sinh học") || lower.Contains("môn sinh")) cfg.Subject = "Sinh học";
            else if (lower.Contains("ngữ văn") || lower.Contains("văn học") || lower.Contains("môn văn")) cfg.Subject = "Ngữ văn";
            else if (lower.Contains("tiếng anh") || lower.Contains("anh văn") || lower.Contains("môn anh")) cfg.Subject = "Tiếng Anh";
            else if (lower.Contains("lịch sử") || lower.Contains("môn sử")) cfg.Subject = "Lịch sử";
            else if (lower.Contains("địa lý") || lower.Contains("địa lí") || lower.Contains("môn địa")) cfg.Subject = "Địa lý";
            else if (lower.Contains("tin học") || lower.Contains("môn tin")) cfg.Subject = "Tin học";
            else cfg.Subject = "Toán";

            // Lớp
            var mGrade = Regex.Match(text, @"(?:lớp|khối)\s*([0-9]{1,2})", RegexOptions.IgnoreCase);
            if (mGrade.Success) cfg.Grade = mGrade.Groups[1].Value;

            // Thời gian
            if (lower.Contains("15 phút") || lower.Contains("15p")) cfg.Duration = "15 phút";
            else if (lower.Contains("45 phút") || lower.Contains("45p") || lower.Contains("1 tiết")) cfg.Duration = "45 phút";
            else if (lower.Contains("60 phút") || lower.Contains("60p")) cfg.Duration = "60 phút";
            else if (lower.Contains("90 phút") || lower.Contains("90p") || lower.Contains("học kỳ") || lower.Contains("học kì") || lower.Contains("thpt")) cfg.Duration = "90 phút";

            // Học kỳ
            if (lower.Contains("giữa kì 1") || lower.Contains("giữa kỳ 1") || lower.Contains("giữa kì i") || lower.Contains("giữa kỳ i")) cfg.Semester = "Giữa kì I";
            else if (lower.Contains("cuối kì 1") || lower.Contains("cuối kỳ 1") || lower.Contains("cuối kì i") || lower.Contains("cuối kỳ i") || lower.Contains("học kỳ 1") || lower.Contains("học kì 1")) cfg.Semester = "Cuối kì I";
            else if (lower.Contains("giữa kì 2") || lower.Contains("giữa kỳ 2") || lower.Contains("giữa kì ii") || lower.Contains("giữa kỳ ii")) cfg.Semester = "Giữa kì II";
            else if (lower.Contains("cuối kì 2") || lower.Contains("cuối kỳ 2") || lower.Contains("cuối kì ii") || lower.Contains("cuối kỳ ii") || lower.Contains("học kỳ 2") || lower.Contains("học kì 2")) cfg.Semester = "Cuối kì II";

            cfg.ExtraRequirements = text;
            return cfg;
        }

        private void BtnApplyToMatrix_Click(object sender, RoutedEventArgs e)
        {
            if (GeneratedMatrixConfig == null)
            {
                GeneratedMatrixConfig = ParseConfigFromText(TxtExamPromptInput.Text);
            }
            DialogResult = true;
            Close();
        }

        private void BtnCopyLatexPrompt_Click(object sender, RoutedEventArgs e)
        {
            string subj = GeneratedMatrixConfig?.Subject ?? "Toán";
            int grade = int.TryParse(GeneratedMatrixConfig?.Grade ?? "12", out int g) ? g : 12;
            string prompt = ConvertView.GetExTestPromptTemplate(subj, grade);
            SafeClipboard.SetText(prompt);
            MessageBox.Show("Đã sao chép Prompt chuẩn LaTeX ex_test vào Clipboard! Bạn có thể dán trực tiếp lên ChatGPT, Gemini hoặc Claude.",
                            "Đã sao chép", MessageBoxButton.OK, MessageBoxImage.Information);
        }

        private async void BtnGenerateSingleQuestion_Click(object sender, RoutedEventArgs e)
        {
            string req = TxtQuestionRequirement.Text?.Trim() ?? string.Empty;
            if (string.IsNullOrWhiteSpace(req))
            {
                MessageBox.Show("Vui lòng nhập yêu cầu nội dung câu hỏi.", "Chưa có thông tin", MessageBoxButton.OK, MessageBoxImage.Warning);
                return;
            }

            string subject = (CmbQuestionSubject.SelectedItem as ComboBoxItem)?.Content?.ToString() ?? "Toán";
            string grade = (CmbQuestionGrade.SelectedItem as ComboBoxItem)?.Content?.ToString() ?? "12";
            string qType = (CmbQuestionType.SelectedItem as ComboBoxItem)?.Tag?.ToString() ?? "TN";
            string level = (CmbQuestionLevel.SelectedItem as ComboBoxItem)?.Content?.ToString() ?? "Thông hiểu";

            SetBusy(true, "AI đang biên soạn câu hỏi...");
            _cts?.Dispose();
            _cts = new CancellationTokenSource();

            try
            {
                string prompt = $@"Bạn là chuyên gia biên soạn đề thi môn {subject} lớp {grade} chuẩn Bộ GD&ĐT.
NHIỆM VỤ: Hãy tạo duy nhất 01 câu hỏi theo định dạng chuẩn gói LaTeX ex_test với các yêu cầu sau:
- Thể loại: {qType} (TN: trắc nghiệm 4 lựa chọn có \choice và \True; DS: đúng sai 4 ý có \choiceTF và \True; TLN: trả lời ngắn có \shortans; TL: tự luận \begin{{bt}} ... \end{{bt}})
- Mức độ nhận thức: {level}
- Yêu cầu nội dung: {req}
- Dòng đầu tiên BẮT BUỘC là: % Câu 1 [{level}]_[{subject} {grade}]
- Mọi công thức toán kẹp trong ${{...}}$
- Có phần lời giải chi tiết \loigiai{{ ... }}
- Chỉ xuất khối mã LaTeX ```latex ... ```, không kèm lời chào hỏi.";

                var result = await DesktopGeminiFactory.ExecutePromptAsync(prompt: prompt, ct: _cts.Token);
                if (result.Success && !string.IsNullOrWhiteSpace(result.Content))
                {
                    string content = result.Content.Trim();
                    // Loại bỏ ```latex ... ``` nếu có
                    if (content.StartsWith("```latex", StringComparison.OrdinalIgnoreCase))
                    {
                        content = content.Substring(8);
                    }
                    else if (content.StartsWith("```"))
                    {
                        content = content.Substring(3);
                    }
                    if (content.EndsWith("```"))
                    {
                        content = content.Substring(0, content.Length - 3);
                    }
                    content = content.Trim();

                    TxtQuestionOutput.Text = content;
                    GeneratedQuestionLatex = content;
                    BtnInsertQuestionToEditor.IsEnabled = true;
                    BtnCopySingleQuestion.IsEnabled = true;
                    SetBusy(false, $"Đã tạo xong câu hỏi ({result.ProviderUsed} • {result.LatencyMs}ms).");
                }
                else
                {
                    SetBusy(false, $"Lỗi: {result.ErrorMessage ?? "Không sinh được câu hỏi."}");
                    MessageBox.Show(result.ErrorMessage ?? "Không thể tạo câu hỏi. Vui lòng kiểm tra API Key hoặc kết nối mạng.", "Lỗi tạo câu hỏi", MessageBoxButton.OK, MessageBoxImage.Warning);
                }
            }
            catch (OperationCanceledException)
            {
                SetBusy(false, "Đã hủy tác vụ tạo câu hỏi.");
            }
            catch (Exception ex)
            {
                SetBusy(false, $"Lỗi: {ex.Message}");
                MessageBox.Show($"Đã xảy ra lỗi: {ex.Message}", "Lỗi", MessageBoxButton.OK, MessageBoxImage.Error);
            }
        }

        private void BtnInsertQuestionToEditor_Click(object sender, RoutedEventArgs e)
        {
            if (string.IsNullOrWhiteSpace(GeneratedQuestionLatex))
            {
                GeneratedQuestionLatex = TxtQuestionOutput.Text.Trim();
            }
            DialogResult = true;
            Close();
        }

        private void BtnCopySingleQuestion_Click(object sender, RoutedEventArgs e)
        {
            string content = TxtQuestionOutput.Text.Trim();
            if (!string.IsNullOrWhiteSpace(content))
            {
                SafeClipboard.SetText(content);
                MessageBox.Show("Đã sao chép mã câu hỏi LaTeX vào Clipboard!", "Đã sao chép", MessageBoxButton.OK, MessageBoxImage.Information);
            }
        }

        private void LstPromptTemplates_SelectionChanged(object sender, SelectionChangedEventArgs e)
        {
            int idx = LstPromptTemplates.SelectedIndex;
            if (_promptTemplates.TryGetValue(idx, out string? tmpl))
            {
                TxtTemplateContent.Text = tmpl;
            }
        }

        private void BtnCopyTemplate_Click(object sender, RoutedEventArgs e)
        {
            string content = TxtTemplateContent.Text?.Trim() ?? string.Empty;
            if (!string.IsNullOrWhiteSpace(content))
            {
                SafeClipboard.SetText(content);
                MessageBox.Show("Đã sao chép mẫu Prompt sư phạm vào Clipboard!", "Đã sao chép", MessageBoxButton.OK, MessageBoxImage.Information);
            }
        }

        private void BtnLoadTemplateToEditor_Click(object sender, RoutedEventArgs e)
        {
            string content = TxtTemplateContent.Text?.Trim() ?? string.Empty;
            if (!string.IsNullOrWhiteSpace(content))
            {
                GeneratedQuestionLatex = content;
                DialogResult = true;
                Close();
            }
        }

        private void SetBusy(bool busy, string status)
        {
            TxtStatus.Text = status;
            PrgProgressVisible(busy);
            BtnParseExamPrompt.IsEnabled = !busy;
            BtnGenerateSingleQuestion.IsEnabled = !busy;
        }

        private void PrgProgressVisible(bool visible)
        {
            PrgBusy.Visibility = visible ? Visibility.Visible : Visibility.Collapsed;
        }

        private void BtnClose_Click(object sender, RoutedEventArgs e)
        {
            _cts?.Cancel();
            Close();
        }
    }
}
