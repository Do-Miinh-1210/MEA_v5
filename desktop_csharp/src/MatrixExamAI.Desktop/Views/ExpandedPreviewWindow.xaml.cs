using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Linq;
using System.Text;
using System.Text.RegularExpressions;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Media;
using System.Windows.Input;
using MatrixExamAI.Desktop.Services;
using MatrixExamAI.Shared.Extensibility;

namespace MatrixExamAI.Desktop.Views
{
    public partial class ExpandedPreviewWindow : Wpf.Ui.Controls.FluentWindow
    {
        private readonly List<QuestionItem> _questions;
        private readonly string _rawText;
        private readonly ExamExportOptions _examOptions;
        private readonly WordExportService _wordService = new WordExportService();
        private static readonly SolidColorBrush DarkBrush = new SolidColorBrush(Color.FromRgb(15, 23, 42));
        private static readonly SolidColorBrush GrayBrush = new SolidColorBrush(Color.FromRgb(71, 85, 105));
        private static readonly SolidColorBrush BlueBrush = new SolidColorBrush(Color.FromRgb(2, 132, 199));
        private static readonly SolidColorBrush BorderColorBrush = new SolidColorBrush(Color.FromRgb(203, 213, 225));

        public ExpandedPreviewWindow(
            List<QuestionItem> questions, 
            string rawText, 
            ExamExportOptions? examOptions = null)
        {
            InitializeComponent();

            _questions = questions ?? new List<QuestionItem>();
            _rawText = rawText ?? string.Empty;
            _examOptions = examOptions ?? new ExamExportOptions
            {
                Subject = "Toán",
                Grade = "12",
                ExamTitle = "KỲ THI TỐT NGHIỆP THPT",
                SchoolName = "SỞ GIÁO DỤC VÀ ĐÀO TẠO",
                ExamYear = DateTime.Now.Year.ToString(),
                TimeMinutes = "90",
                ExamCode = "101",
                IncludeSolution = true,
                HighlightFormulas = true,
                ConvertTablesToWordGrid = true
            };

            LoadData();
        }

        private void LoadData()
        {
            // 1. DataGrid danh sách câu hỏi
            if (_questions.Count > 0)
            {
                var displayList = _questions.Select((q, i) => new QuestionDisplayItem
                {
                    Index = i + 1,
                    SubjectGrade = $"{q.Subject} {q.Grade}",
                    TypeShort = GetTypeShort(q.QuestionType),
                    CognitiveLevel = q.CognitiveLevel,
                    Topic = string.IsNullOrWhiteSpace(q.Topic) ? $"{q.Subject} {q.Grade}" : q.Topic,
                    CorrectAnswer = q.CorrectAnswer,
                    ContentPreview = q.Content.Replace("\r\n", " ").Replace("\n", " "),
                    ExplanationPreview = string.IsNullOrWhiteSpace(q.Explanation) ? "(Không có)" : q.Explanation.Replace("\r\n", " ").Replace("\n", " "),
                    RawItem = q
                }).ToList();

                DgQuestionsExpanded.ItemsSource = displayList;
                TxtGridHeader.Text = $"Bảng danh sách câu hỏi: {_questions.Count} câu";
                RbTabGrid.Content = $"Bảng câu hỏi ({_questions.Count} câu)";
            }
            else
            {
                TxtGridHeader.Text = "Chưa có câu hỏi nào được nhận diện theo khối cấu trúc";
                RbTabGrid.Content = "Bảng câu hỏi (0 câu)";
            }

            // 2. Mã nguồn thô
            TxtRawSource.Text = _rawText;

            // 3. Render Word A4
            RenderWordA4Preview();

            // 4. Footer stats
            int formulaCount = Regex.Matches(_rawText, @"\$\{[\s\S]*?\}\$").Count;
            TxtFooterStats.Text = $"Tổng số: {_questions.Count} câu hỏi • {formulaCount} công thức ${{...}}$ • Sẵn sàng xuất Microsoft Word (.docx)";
        }

        private static string GetTypeShort(string qType)
        {
            return qType switch
            {
                "MultipleChoice4" => "TN",
                "TrueFalse4" => "DS",
                "ShortAnswer" => "TLN",
                "Essay" => "TL",
                _ => qType
            };
        }

        private void RenderWordA4Preview()
        {
            PanelDocContent.Children.Clear();

            // 1. Khung tiêu đề đề thi 2 cột chuẩn THPT (kế thừa m:\LOP\KT15P-1)
            var headerGrid = new Grid { Margin = new Thickness(0, 0, 0, 12) };
            headerGrid.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(1, GridUnitType.Star) });
            headerGrid.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(1, GridUnitType.Star) });

            string schoolText = string.IsNullOrWhiteSpace(_examOptions.SchoolName) ? "SỞ/PHÒNG GD&ĐT" : _examOptions.SchoolName.ToUpper();
            int totalQ = _questions.Count > 0 ? _questions.Count : 20;

            var leftStack = new StackPanel { HorizontalAlignment = HorizontalAlignment.Center };
            leftStack.Children.Add(new TextBlock
            {
                Text = schoolText,
                FontWeight = FontWeights.Bold,
                FontSize = 11,
                FontFamily = new FontFamily("Times New Roman"),
                Foreground = DarkBrush,
                HorizontalAlignment = HorizontalAlignment.Center
            });
            leftStack.Children.Add(new TextBlock
            {
                Text = "ĐỀ KIỂM TRA",
                FontWeight = FontWeights.Bold,
                FontSize = 11,
                FontFamily = new FontFamily("Times New Roman"),
                Foreground = DarkBrush,
                HorizontalAlignment = HorizontalAlignment.Center
            });
            leftStack.Children.Add(new TextBlock
            {
                Text = $"(Đề thi gồm {totalQ:02d} câu)",
                FontStyle = FontStyles.Italic,
                FontSize = 10,
                FontFamily = new FontFamily("Times New Roman"),
                Foreground = GrayBrush,
                HorizontalAlignment = HorizontalAlignment.Center
            });
            Grid.SetColumn(leftStack, 0);
            headerGrid.Children.Add(leftStack);

            var rightStack = new StackPanel { HorizontalAlignment = HorizontalAlignment.Center };
            rightStack.Children.Add(new TextBlock
            {
                Text = $"ĐỀ THI MÔN {_examOptions.Subject.ToUpper()} - LỚP {_examOptions.Grade}",
                FontWeight = FontWeights.Bold,
                FontSize = 11,
                FontFamily = new FontFamily("Times New Roman"),
                Foreground = DarkBrush,
                HorizontalAlignment = HorizontalAlignment.Center
            });
            rightStack.Children.Add(new TextBlock
            {
                Text = $"Môn thi: {_examOptions.Subject.ToUpper()}",
                FontWeight = FontWeights.Bold,
                FontSize = 11,
                FontFamily = new FontFamily("Times New Roman"),
                Foreground = DarkBrush,
                HorizontalAlignment = HorizontalAlignment.Center
            });
            rightStack.Children.Add(new TextBlock
            {
                Text = $"Thời gian làm bài: {_examOptions.TimeMinutes} phút, không kể thời gian phát đề",
                FontStyle = FontStyles.Italic,
                FontSize = 10,
                FontFamily = new FontFamily("Times New Roman"),
                Foreground = GrayBrush,
                HorizontalAlignment = HorizontalAlignment.Center
            });
            rightStack.Children.Add(new TextBlock
            {
                Text = $"Lớp: {_examOptions.Grade}    Năm học: {_examOptions.ExamYear}",
                FontSize = 10,
                FontFamily = new FontFamily("Times New Roman"),
                Foreground = GrayBrush,
                HorizontalAlignment = HorizontalAlignment.Center
            });
            Grid.SetColumn(rightStack, 1);
            headerGrid.Children.Add(rightStack);

            PanelDocContent.Children.Add(headerGrid);

            // 2. Dòng thông tin thí sinh phẳng không viền hộp dàn đều 100%
            var candidateGrid = new Grid { Margin = new Thickness(0, 4, 0, 12) };
            candidateGrid.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(1, GridUnitType.Star) });
            candidateGrid.ColumnDefinitions.Add(new ColumnDefinition { Width = GridLength.Auto });
            candidateGrid.ColumnDefinitions.Add(new ColumnDefinition { Width = GridLength.Auto });

            var nameText = new TextBlock
            {
                Text = "Họ và tên thí sinh: ................................................................",
                FontFamily = new FontFamily("Times New Roman"),
                FontSize = 11,
                Foreground = DarkBrush,
                VerticalAlignment = VerticalAlignment.Center
            };
            var sbdText = new TextBlock
            {
                Text = "Số báo danh: .............................",
                FontFamily = new FontFamily("Times New Roman"),
                FontSize = 11,
                Foreground = DarkBrush,
                Margin = new Thickness(16, 0, 16, 0),
                VerticalAlignment = VerticalAlignment.Center
            };
            var codeText = new TextBlock
            {
                Text = $"Mã đề: {_examOptions.ExamCode}",
                FontWeight = FontWeights.Bold,
                FontFamily = new FontFamily("Times New Roman"),
                FontSize = 11,
                Foreground = DarkBrush,
                HorizontalAlignment = HorizontalAlignment.Right,
                VerticalAlignment = VerticalAlignment.Center
            };
            Grid.SetColumn(nameText, 0);
            Grid.SetColumn(sbdText, 1);
            Grid.SetColumn(codeText, 2);
            candidateGrid.Children.Add(nameText);
            candidateGrid.Children.Add(sbdText);
            candidateGrid.Children.Add(codeText);
            PanelDocContent.Children.Add(candidateGrid);
            PanelDocContent.Children.Add(new Separator { Margin = new Thickness(0, 0, 0, 14), Background = new SolidColorBrush(Color.FromRgb(0xCB, 0xD5, 0xE1)) });

            // 3. Bảng điền đáp án nhanh cho học sinh (Table 1 trong m:\LOP\KT15P-1)
            var tnQuestions = _questions.Where(q => q.QuestionType == "MultipleChoice4").ToList();
            if (tnQuestions.Count > 0)
            {
                var quickSheet = CreateQuickAnswerSheetGrid(tnQuestions.Count);
                if (quickSheet != null) PanelDocContent.Children.Add(quickSheet);
            }

            // 4. Nội dung chi tiết các câu hỏi hoặc văn bản
            if (_questions.Count > 0)
            {
                RenderExamQuestions();
            }
            else
            {
                RenderRawTextParagraphs();
            }
        }

        private FrameworkElement? CreateQuickAnswerSheetGrid(int totalCount)
        {
            if (totalCount <= 0) return null;
            int count = Math.Min(totalCount, 25);

            var border = new Border
            {
                BorderBrush = BorderColorBrush,
                BorderThickness = new Thickness(1),
                CornerRadius = new CornerRadius(3),
                Margin = new Thickness(0, 4, 0, 14),
                Background = Brushes.White
            };

            var grid = new Grid();
            for (int i = 0; i <= count; i++)
            {
                grid.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(1, GridUnitType.Star) });
            }
            grid.RowDefinitions.Add(new RowDefinition { Height = GridLength.Auto });
            grid.RowDefinitions.Add(new RowDefinition { Height = GridLength.Auto });

            // Cột tiêu đề
            var c0 = new Border
            {
                Background = new SolidColorBrush(Color.FromRgb(241, 245, 249)),
                BorderBrush = BorderColorBrush,
                BorderThickness = new Thickness(0, 0, 1, 1),
                Padding = new Thickness(4, 3, 4, 3),
                Child = new TextBlock { Text = "Câu", FontWeight = FontWeights.Bold, FontFamily = new FontFamily("Times New Roman"), FontSize = 10.5, Foreground = DarkBrush, HorizontalAlignment = HorizontalAlignment.Center }
            };
            Grid.SetRow(c0, 0); Grid.SetColumn(c0, 0); grid.Children.Add(c0);

            var a0 = new Border
            {
                Background = new SolidColorBrush(Color.FromRgb(248, 250, 252)),
                BorderBrush = BorderColorBrush,
                BorderThickness = new Thickness(0, 0, 1, 0),
                Padding = new Thickness(4, 3, 4, 3),
                Child = new TextBlock { Text = "Đáp án", FontWeight = FontWeights.Bold, FontFamily = new FontFamily("Times New Roman"), FontSize = 9.5, Foreground = DarkBrush, HorizontalAlignment = HorizontalAlignment.Center }
            };
            Grid.SetRow(a0, 1); Grid.SetColumn(a0, 0); grid.Children.Add(a0);

            for (int i = 1; i <= count; i++)
            {
                var cH = new Border
                {
                    Background = new SolidColorBrush(Color.FromRgb(241, 245, 249)),
                    BorderBrush = BorderColorBrush,
                    BorderThickness = new Thickness(0, 0, i < count ? 1 : 0, 1),
                    Padding = new Thickness(2, 3, 2, 3),
                    Child = new TextBlock { Text = i.ToString(), FontWeight = FontWeights.Bold, FontFamily = new FontFamily("Times New Roman"), FontSize = 10, Foreground = DarkBrush, HorizontalAlignment = HorizontalAlignment.Center }
                };
                Grid.SetRow(cH, 0); Grid.SetColumn(cH, i); grid.Children.Add(cH);

                var cA = new Border
                {
                    BorderBrush = BorderColorBrush,
                    BorderThickness = new Thickness(0, 0, i < count ? 1 : 0, 0),
                    Padding = new Thickness(2, 5, 2, 5),
                    Child = new TextBlock { Text = " ", FontFamily = new FontFamily("Times New Roman"), FontSize = 10, Foreground = DarkBrush, HorizontalAlignment = HorizontalAlignment.Center }
                };
                Grid.SetRow(cA, 1); Grid.SetColumn(cA, i); grid.Children.Add(cA);
            }

            border.Child = grid;
            return border;
        }

        private FrameworkElement? CreateAnswerKeyGrid(List<QuestionItem> tnList)
        {
            if (tnList.Count == 0) return null;
            int count = Math.Min(tnList.Count, 25);

            var border = new Border
            {
                BorderBrush = BorderColorBrush,
                BorderThickness = new Thickness(1),
                CornerRadius = new CornerRadius(3),
                Margin = new Thickness(0, 4, 0, 14),
                Background = Brushes.White
            };

            var grid = new Grid();
            for (int i = 0; i <= count; i++)
            {
                grid.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(1, GridUnitType.Star) });
            }
            grid.RowDefinitions.Add(new RowDefinition { Height = GridLength.Auto });
            grid.RowDefinitions.Add(new RowDefinition { Height = GridLength.Auto });

            // Cột tiêu đề
            var c0 = new Border
            {
                Background = new SolidColorBrush(Color.FromRgb(241, 245, 249)),
                BorderBrush = BorderColorBrush,
                BorderThickness = new Thickness(0, 0, 1, 1),
                Padding = new Thickness(4, 3, 4, 3),
                Child = new TextBlock { Text = "Câu", FontWeight = FontWeights.Bold, FontFamily = new FontFamily("Times New Roman"), FontSize = 10.5, Foreground = DarkBrush, HorizontalAlignment = HorizontalAlignment.Center }
            };
            Grid.SetRow(c0, 0); Grid.SetColumn(c0, 0); grid.Children.Add(c0);

            var a0 = new Border
            {
                Background = new SolidColorBrush(Color.FromRgb(241, 245, 249)),
                BorderBrush = BorderColorBrush,
                BorderThickness = new Thickness(0, 0, 1, 0),
                Padding = new Thickness(4, 3, 4, 3),
                Child = new TextBlock { Text = "Đáp án", FontWeight = FontWeights.Bold, FontFamily = new FontFamily("Times New Roman"), FontSize = 9.5, Foreground = DarkBrush, HorizontalAlignment = HorizontalAlignment.Center }
            };
            Grid.SetRow(a0, 1); Grid.SetColumn(a0, 0); grid.Children.Add(a0);

            for (int i = 1; i <= count; i++)
            {
                var q = tnList[i - 1];
                var cH = new Border
                {
                    Background = new SolidColorBrush(Color.FromRgb(241, 245, 249)),
                    BorderBrush = BorderColorBrush,
                    BorderThickness = new Thickness(0, 0, i < count ? 1 : 0, 1),
                    Padding = new Thickness(2, 3, 2, 3),
                    Child = new TextBlock { Text = i.ToString(), FontWeight = FontWeights.Bold, FontFamily = new FontFamily("Times New Roman"), FontSize = 10, Foreground = DarkBrush, HorizontalAlignment = HorizontalAlignment.Center }
                };
                Grid.SetRow(cH, 0); Grid.SetColumn(cH, i); grid.Children.Add(cH);

                var cA = new Border
                {
                    BorderBrush = BorderColorBrush,
                    BorderThickness = new Thickness(0, 0, i < count ? 1 : 0, 0),
                    Padding = new Thickness(2, 4, 2, 4),
                    Child = new TextBlock { Text = q.CorrectAnswer, FontWeight = FontWeights.Bold, FontFamily = new FontFamily("Times New Roman"), FontSize = 10, Foreground = BlueBrush, HorizontalAlignment = HorizontalAlignment.Center }
                };
                Grid.SetRow(cA, 1); Grid.SetColumn(cA, i); grid.Children.Add(cA);
            }

            border.Child = grid;
            return border;
        }

        private void RenderExamQuestions()
        {
            var tnQuestions = _questions.Where(q => q.QuestionType == "MultipleChoice4").ToList();
            var dsQuestions = _questions.Where(q => q.QuestionType == "TrueFalse4").ToList();
            var tlnQuestions = _questions.Where(q => q.QuestionType == "ShortAnswer").ToList();
            var tlQuestions = _questions.Where(q => q.QuestionType == "Essay").ToList();

            int questionIndex = 1;

            if (tnQuestions.Count > 0)
            {
                PanelDocContent.Children.Add(CreateSectionHeader("PHẦN I. Thí sinh trả lời từ câu 1 đến câu " + tnQuestions.Count + ". Mỗi câu hỏi thí sinh chỉ chọn một phương án."));
                foreach (var q in tnQuestions)
                {
                    PanelDocContent.Children.Add(CreateQuestionElement(questionIndex++, q));
                }
            }

            if (dsQuestions.Count > 0)
            {
                int endIdx = questionIndex + dsQuestions.Count - 1;
                PanelDocContent.Children.Add(CreateSectionHeader($"PHẦN II. Thí sinh trả lời từ câu {questionIndex} đến câu {endIdx}. Trong mỗi ý a), b), c), d) ở mỗi câu, thí sinh chọn đúng hoặc sai."));
                foreach (var q in dsQuestions)
                {
                    PanelDocContent.Children.Add(CreateQuestionElement(questionIndex++, q));
                }
            }

            if (tlnQuestions.Count > 0)
            {
                int endIdx = questionIndex + tlnQuestions.Count - 1;
                PanelDocContent.Children.Add(CreateSectionHeader($"PHẦN III. Thí sinh trả lời từ câu {questionIndex} đến câu {endIdx}."));
                foreach (var q in tlnQuestions)
                {
                    PanelDocContent.Children.Add(CreateQuestionElement(questionIndex++, q));
                }
            }

            if (tlQuestions.Count > 0)
            {
                PanelDocContent.Children.Add(CreateSectionHeader("PHẦN IV. TỰ LUẬN"));
                foreach (var q in tlQuestions)
                {
                    PanelDocContent.Children.Add(CreateQuestionElement(questionIndex++, q));
                }
            }

            // Dòng kết thúc đề
            PanelDocContent.Children.Add(new TextBlock
            {
                Text = "---------- HẾT ----------",
                FontWeight = FontWeights.Bold,
                FontFamily = new FontFamily("Times New Roman"),
                FontSize = 12,
                Foreground = DarkBrush,
                HorizontalAlignment = HorizontalAlignment.Center,
                Margin = new Thickness(0, 16, 0, 14)
            });

            // Phụ lục đáp án & lời giải tham khảo
            if (_examOptions.IncludeSolution && tnQuestions.Count > 0)
            {
                PanelDocContent.Children.Add(CreateSectionHeader("ĐÁP ÁN THAM KHẢO"));
                var ansGrid = CreateAnswerKeyGrid(tnQuestions);
                if (ansGrid != null) PanelDocContent.Children.Add(ansGrid);
            }
        }

        private static FrameworkElement CreateSectionHeader(string title)
        {
            return new Border
            {
                Background = new SolidColorBrush(Color.FromRgb(241, 245, 249)),
                BorderBrush = new SolidColorBrush(Color.FromRgb(203, 213, 225)),
                BorderThickness = new Thickness(1),
                CornerRadius = new CornerRadius(3),
                Padding = new Thickness(8, 4, 8, 4),
                Margin = new Thickness(0, 10, 0, 8),
                Child = new TextBlock
                {
                    Text = title,
                    FontWeight = FontWeights.Bold,
                    FontFamily = new FontFamily("Times New Roman"),
                    FontSize = 11.5,
                    Foreground = new SolidColorBrush(Color.FromRgb(15, 23, 42))
                }
            };
        }

        private static FrameworkElement CreateQuestionElement(int index, QuestionItem q)
        {
            var sp = new StackPanel { Margin = new Thickness(0, 0, 0, 10) };

            // Nội dung câu
            var titleBlock = new TextBlock
            {
                FontFamily = new FontFamily("Times New Roman"),
                FontSize = 12,
                TextWrapping = TextWrapping.Wrap,
                Foreground = DarkBrush,
                Margin = new Thickness(0, 0, 0, 4)
            };
            titleBlock.Inlines.Add(new System.Windows.Documents.Run($"Câu {index}: ") { FontWeight = FontWeights.Bold, Foreground = DarkBrush });
            titleBlock.Inlines.Add(new System.Windows.Documents.Run(q.Content) { Foreground = DarkBrush });
            sp.Children.Add(titleBlock);

            // Các phương án nếu có
            if (q.QuestionType == "MultipleChoice4" && q.Options.Count > 0)
            {
                var optGrid = new Grid { Margin = new Thickness(16, 2, 0, 4) };
                optGrid.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(1, GridUnitType.Star) });
                optGrid.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(1, GridUnitType.Star) });
                optGrid.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(1, GridUnitType.Star) });
                optGrid.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(1, GridUnitType.Star) });

                string[] keys = { "A", "B", "C", "D" };
                for (int i = 0; i < keys.Length; i++)
                {
                    string k = keys[i];
                    string text = q.Options.ContainsKey(k) ? q.Options[k] : "";
                    var tb = new TextBlock
                    {
                        FontFamily = new FontFamily("Times New Roman"),
                        FontSize = 11.5,
                        TextWrapping = TextWrapping.Wrap,
                        Foreground = DarkBrush,
                        Margin = new Thickness(0, 0, 6, 0)
                    };
                    tb.Inlines.Add(new System.Windows.Documents.Run($"{k}. ") { FontWeight = FontWeights.Bold, Foreground = BlueBrush });
                    tb.Inlines.Add(new System.Windows.Documents.Run(text) { Foreground = DarkBrush });
                    Grid.SetColumn(tb, i);
                    optGrid.Children.Add(tb);
                }
                sp.Children.Add(optGrid);
            }
            else if (q.QuestionType == "TrueFalse4" && q.Options.Count > 0)
            {
                var optStack = new StackPanel { Margin = new Thickness(16, 2, 0, 4) };
                string[] keys = { "a", "b", "c", "d" };
                foreach (var k in keys)
                {
                    if (q.Options.TryGetValue(k, out var text))
                    {
                        var tb = new TextBlock
                        {
                            FontFamily = new FontFamily("Times New Roman"),
                            FontSize = 11.5,
                            TextWrapping = TextWrapping.Wrap,
                            Foreground = DarkBrush,
                            Margin = new Thickness(0, 1, 0, 1)
                        };
                        tb.Inlines.Add(new System.Windows.Documents.Run($"{k}) ") { FontWeight = FontWeights.Bold, Foreground = BlueBrush });
                        tb.Inlines.Add(new System.Windows.Documents.Run(text) { Foreground = DarkBrush });
                        optStack.Children.Add(tb);
                    }
                }
                sp.Children.Add(optStack);
            }

            // Lời giải nếu có
            if (!string.IsNullOrWhiteSpace(q.Explanation))
            {
                var solBorder = new Border
                {
                    Background = new SolidColorBrush(Color.FromRgb(248, 250, 252)),
                    BorderBrush = new SolidColorBrush(Color.FromRgb(226, 232, 240)),
                    BorderThickness = new Thickness(1),
                    CornerRadius = new CornerRadius(3),
                    Padding = new Thickness(8, 4, 8, 4),
                    Margin = new Thickness(0, 4, 0, 0)
                };
                var solBlock = new TextBlock
                {
                    FontFamily = new FontFamily("Times New Roman"),
                    FontSize = 11,
                    FontStyle = FontStyles.Italic,
                    TextWrapping = TextWrapping.Wrap,
                    Foreground = GrayBrush
                };
                solBlock.Inlines.Add(new System.Windows.Documents.Run("Hướng dẫn giải: ") { FontWeight = FontWeights.Bold, FontStyle = FontStyles.Normal, Foreground = DarkBrush });
                solBlock.Inlines.Add(new System.Windows.Documents.Run(q.Explanation) { Foreground = GrayBrush });
                solBorder.Child = solBlock;
                sp.Children.Add(solBorder);
            }

            return sp;
        }

        private void RenderRawTextParagraphs()
        {
            var lines = _rawText.Split(new[] { "\r\n", "\r", "\n" }, StringSplitOptions.None);
            foreach (var line in lines)
            {
                if (!string.IsNullOrWhiteSpace(line))
                {
                    PanelDocContent.Children.Add(new TextBlock
                    {
                        Text = line,
                        FontFamily = new FontFamily("Times New Roman"),
                        FontSize = 12,
                        TextWrapping = TextWrapping.Wrap,
                        Foreground = DarkBrush,
                        Margin = new Thickness(0, 0, 0, 4)
                    });
                }
                else
                {
                    PanelDocContent.Children.Add(new Border { Height = 6 });
                }
            }
        }

        private void RbTab_Checked(object sender, RoutedEventArgs e)
        {
            if (BorderWordContainer == null || BorderGridContainer == null || TxtRawSource == null) return;

            if (RbTabWord.IsChecked == true)
            {
                BorderWordContainer.Visibility = Visibility.Visible;
                BorderGridContainer.Visibility = Visibility.Collapsed;
                TxtRawSource.Visibility = Visibility.Collapsed;
            }
            else if (RbTabGrid.IsChecked == true)
            {
                BorderWordContainer.Visibility = Visibility.Collapsed;
                BorderGridContainer.Visibility = Visibility.Visible;
                TxtRawSource.Visibility = Visibility.Collapsed;
            }
            else
            {
                BorderWordContainer.Visibility = Visibility.Collapsed;
                BorderGridContainer.Visibility = Visibility.Collapsed;
                TxtRawSource.Visibility = Visibility.Visible;
            }
        }

        private void BtnExportWord_Click(object sender, RoutedEventArgs e)
        {
            var saveDialog = new Microsoft.Win32.SaveFileDialog
            {
                Filter = "Tài liệu Word (*.docx)|*.docx",
                FileName = $"De_Thi_Chuan_Hoa_{DateTime.Now:yyyyMMdd_HHmm}.docx",
                Title = "Xuất tài liệu Word chuẩn"
            };

            if (saveDialog.ShowDialog() == true)
            {
                try
                {
                    if (_questions.Count > 0)
                    {
                        _wordService.ExportExamToDocx(saveDialog.FileName, _questions, _examOptions);
                    }
                    else
                    {
                        _wordService.ExportToDocx(saveDialog.FileName, _rawText, _examOptions);
                    }

                    var result = MessageBox.Show(
                        $"Đã xuất thành công tài liệu Word chuẩn!\n\nĐường dẫn: {saveDialog.FileName}\n\nBạn có muốn mở ngay tài liệu bằng Microsoft Word không?",
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

        private void BtnCopy_Click(object sender, RoutedEventArgs e)
        {
            SafeClipboard.SetText(_rawText);
            MessageBox.Show("Đã sao chép nội dung văn bản kẹp ${...}$ vào Clipboard!", "Thông báo", MessageBoxButton.OK, MessageBoxImage.Information);
        }

        private void BtnClose_Click(object sender, RoutedEventArgs e)
        {
            Close();
        }

        public Action<System.Windows.Controls.Primitives.ButtonBase>? ButtonClickInterceptor { get; set; }

        public bool HandlePreviewKeyDown(Key key, ModifierKeys modifiers)
        {
            var isCtrl = (modifiers & ModifierKeys.Control) == ModifierKeys.Control;
            var isAlt = (modifiers & ModifierKeys.Alt) == ModifierKeys.Alt;
            var isShift = (modifiers & ModifierKeys.Shift) == ModifierKeys.Shift;

            // Esc: Đóng cửa sổ xem trước riêng biệt
            if (!isCtrl && !isAlt && !isShift && key == Key.Escape)
            {
                Close();
                return true;
            }

            // Ctrl + S: Xuất file Word (.docx)
            if (isCtrl && !isAlt && !isShift && key == Key.S)
            {
                if (ButtonClickInterceptor != null)
                {
                    ButtonClickInterceptor(BtnExportWord);
                }
                else
                {
                    BtnExportWord_Click(BtnExportWord, new RoutedEventArgs());
                }
                return true;
            }

            // Ctrl + C: Sao chép toàn bộ nội dung xem trước vào bộ nhớ tạm
            if (isCtrl && !isAlt && !isShift && key == Key.C)
            {
                if (!TxtRawSource.IsKeyboardFocused || TxtRawSource.SelectionLength == 0)
                {
                    if (ButtonClickInterceptor != null)
                    {
                        ButtonClickInterceptor(BtnCopy);
                    }
                    else
                    {
                        BtnCopy_Click(BtnCopy, new RoutedEventArgs());
                    }
                    return true;
                }
            }

            return false;
        }

        private void ExpandedPreviewWindow_PreviewKeyDown(object sender, KeyEventArgs e)
        {
            var key = e.Key == Key.System ? e.SystemKey : e.Key;
            if (HandlePreviewKeyDown(key, Keyboard.Modifiers))
            {
                e.Handled = true;
            }
        }
    }
}
