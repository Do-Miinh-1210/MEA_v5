using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.RegularExpressions;
using DocumentFormat.OpenXml;
using DocumentFormat.OpenXml.Packaging;
using DocumentFormat.OpenXml.Wordprocessing;
using A = DocumentFormat.OpenXml.Drawing;
using DW = DocumentFormat.OpenXml.Drawing.Wordprocessing;
using PIC = DocumentFormat.OpenXml.Drawing.Pictures;
using MatrixExamAI.Shared.Extensibility;
using MatrixExamAI.Shared.Models;
using MatrixExamAI.Shared.Tikz;

namespace MatrixExamAI.Desktop.Services
{
    public enum TabSpacingMode
    {
        Standard35, // 3.5cm (1985 twips), 7.0cm (3969 twips), 10.5cm (5953 twips) - Chuẩn Bộ GD&ĐT THPT
        Wide45      // 5.0cm (2835 twips), 9.5cm (5386 twips), 14.0cm (7937 twips)
    }

    public class WordExportOptions
    {
        public bool ConvertTablesToWordGrid { get; set; } = true;
        public bool HighlightFormulas { get; set; } = true;
        public string FontFamily { get; set; } = "Times New Roman";
        public string FontSizePt { get; set; } = "24"; // 24 half-points = 12pt
        public TabSpacingMode TabSpacing { get; set; } = TabSpacingMode.Wide45;
        public List<string> ExtractedImages { get; set; } = new List<string>();
    }

    public class ExamExportOptions : WordExportOptions
    {
        public ExamExportOptions()
        {
            TabSpacing = TabSpacingMode.Wide45;
        }

        public string Subject { get; set; } = "Toán";
        public string Grade { get; set; } = "12";
        public string SchoolName { get; set; } = "SỞ GIÁO DỤC VÀ ĐÀO TẠO";
        public string ExamTitle { get; set; } = "ĐỀ KIỂM TRA CHÍNH THỨC";
        public string ExamYear { get; set; } = "2025-2026";
        public string TimeMinutes { get; set; } = "90";
        public string ExamCode { get; set; } = "101";
        public bool IncludeSolution { get; set; } = true;
        public byte[]? AttachedImageBytes { get; set; }
        public bool? IncludeStudentAnswerSheet { get; set; }
    }

    public class WordExportService
    {
        /// <summary>
        /// Xuất bộ câu hỏi ra tệp Word (.docx) chuẩn cấu trúc đề thi THPT Quốc gia (Port 100% từ word_exporter.py của MEA v5.0).
        /// Bao gồm: Khung tiêu đề 2 cột, dòng thông tin thí sinh, phân chia PHẦN I, II, III, IV,
        /// bảng phương án 4 cột/2 cột cân đối, chuyển đổi nhúng ảnh TikZ và bảng đáp án + lời giải chi tiết.
        /// </summary>
        public void ExportExamToDocx(string filePath, IEnumerable<QuestionItem> questions, ExamExportOptions? options = null)
        {
            options ??= new ExamExportOptions();
            var qList = questions.ToList();

            using var wordDocument = WordprocessingDocument.Create(filePath, WordprocessingDocumentType.Document);
            var mainPart = wordDocument.AddMainDocumentPart();
            mainPart.Document = new Document();
            AddDocumentDefaultStyles(mainPart, options.FontFamily, options.FontSizePt);
            var body = mainPart.Document.AppendChild(new Body());

            // 1. Khổ giấy A4 và lề chuẩn: 1.0cm trên/dưới, 1.5cm trái/phải (chuẩn word_exporter.py)
            ApplyA4PageSettings(body, top: 567, bottom: 567, left: 850, right: 850);

            // 2. Tiêu đề đề thi 2 cột chuẩn THPT
            var headerTable = CreateExamHeaderTable(qList.Count, options);
            body.AppendChild(headerTable);

            // 3. Dòng thông tin thí sinh phẳng không viền + gạch phân cách
            var candidatePara = CreateCandidateParagraph(options);
            body.AppendChild(candidatePara);
            body.AppendChild(CreateHorizontalRuleParagraph());

            // 4. Phân nhóm câu hỏi
            var tnQuestions = qList.Where(q => q.QuestionType == "MultipleChoice4").ToList();
            var dsQuestions = qList.Where(q => q.QuestionType == "TrueFalse4").ToList();
            var tlnQuestions = qList.Where(q => q.QuestionType == "ShortAnswer").ToList();
            var tlQuestions = qList.Where(q => q.QuestionType == "Essay" || (q.QuestionType != "MultipleChoice4" && q.QuestionType != "TrueFalse4" && q.QuestionType != "ShortAnswer")).ToList();

            // Nếu có ảnh đính kèm ban đầu từ người dùng
            if (options.AttachedImageBytes != null && options.AttachedImageBytes.Length > 0)
            {
                AddImageToBody(mainPart, body, options.AttachedImageBytes);
            }

            int globalIndex = 1;

            // ── PHẦN I: Trắc nghiệm 4 lựa chọn ──
            if (tnQuestions.Count > 0)
            {
                var secPara = CreateSectionHeadingParagraph($"PHẦN I. Thí sinh trả lời từ câu 1 đến câu {tnQuestions.Count}. Mỗi câu hỏi thí sinh chỉ chọn một phương án.", options);
                body.AppendChild(secPara);

                // Bảng điền đáp án nhanh cho học sinh (chỉ chèn nếu được yêu cầu hoặc đề kiểm tra 15 phút)
                bool showAnswerSheet = options.IncludeStudentAnswerSheet ??
                    (options.ExamTitle?.IndexOf("15 PHÚT", StringComparison.OrdinalIgnoreCase) >= 0);
                if (showAnswerSheet)
                {
                    var quickSheetTable = CreateStudentAnswerSheetTable(tnQuestions.Count, options);
                    body.AppendChild(quickSheetTable);
                }

                foreach (var q in tnQuestions)
                {
                    var imgBytesList = ExtractQuestionImagesBytes(q);
                    string cleanContent = CleanImageTagsFromContent(q.Content);

                    if (imgBytesList.Count > 0)
                    {
                        var qTable = CreateQuestionWithImageTable(
                            mainPart,
                            $"Câu {globalIndex}. {cleanContent}",
                            q.Options,
                            "MultipleChoice4",
                            imgBytesList,
                            options);
                        body.AppendChild(qTable);
                    }
                    else
                    {
                        var qPara = CreateFormattedParagraph($"Câu {globalIndex}. {cleanContent}", options);
                        body.AppendChild(qPara);

                        if (q.Options.Count > 0)
                        {
                            AppendOptionsParagraphs(body, q.Options, options);
                        }
                    }

                    globalIndex++;
                }
            }

            // ── PHẦN II: Đúng / Sai 4 ý ──
            if (dsQuestions.Count > 0)
            {
                int startIdx = globalIndex;
                int endIdx = globalIndex + dsQuestions.Count - 1;
                var secPara = CreateSectionHeadingParagraph($"PHẦN II. Thí sinh trả lời từ câu {startIdx} đến câu {endIdx}. Trong mỗi ý a), b), c), d) ở mỗi câu hỏi, thí sinh chọn đúng hoặc sai.", options);
                body.AppendChild(secPara);

                foreach (var q in dsQuestions)
                {
                    var imgBytesList = ExtractQuestionImagesBytes(q);
                    string cleanContent = CleanImageTagsFromContent(q.Content);

                    if (imgBytesList.Count > 0)
                    {
                        var qTable = CreateQuestionWithImageTable(
                            mainPart,
                            $"Câu {globalIndex}. {cleanContent}",
                            q.Options,
                            "TrueFalse4",
                            imgBytesList,
                            options);
                        body.AppendChild(qTable);
                    }
                    else
                    {
                        var qPara = CreateFormattedParagraph($"Câu {globalIndex}. {cleanContent}", options);
                        body.AppendChild(qPara);

                        string[] keys = { "a", "b", "c", "d" };
                        foreach (var k in keys)
                        {
                            if (q.Options.ContainsKey(k))
                            {
                                var itemPara = CreateFormattedParagraph($"{k}) {q.Options[k]}", options);
                                body.AppendChild(itemPara);
                            }
                        }
                    }

                    globalIndex++;
                }
            }

            // ── PHẦN III: Trả lời ngắn ──
            if (tlnQuestions.Count > 0)
            {
                int startIdx = globalIndex;
                int endIdx = globalIndex + tlnQuestions.Count - 1;
                var secPara = CreateSectionHeadingParagraph($"PHẦN III. Thí sinh trả lời từ câu {startIdx} đến câu {endIdx}.", options);
                body.AppendChild(secPara);

                foreach (var q in tlnQuestions)
                {
                    var imgBytesList = ExtractQuestionImagesBytes(q);
                    string cleanContent = CleanImageTagsFromContent(q.Content);

                    if (imgBytesList.Count > 0)
                    {
                        var qTable = CreateQuestionWithImageTable(
                            mainPart,
                            $"Câu {globalIndex}. {cleanContent}",
                            null,
                            "ShortAnswer",
                            imgBytesList,
                            options);
                        body.AppendChild(qTable);
                    }
                    else
                    {
                        var qPara = CreateFormattedParagraph($"Câu {globalIndex}. {cleanContent}", options);
                        body.AppendChild(qPara);
                        var ansPara = CreateFormattedParagraph("Đáp án: | | | | |", options);
                        body.AppendChild(ansPara);
                    }

                    globalIndex++;
                }
            }

            // ── PHẦN IV: Tự luận ──
            if (tlQuestions.Count > 0)
            {
                int startIdx = globalIndex;
                int endIdx = globalIndex + tlQuestions.Count - 1;
                var secPara = CreateSectionHeadingParagraph($"PHẦN IV. Tự luận. Thí sinh trình bày lời giải từ câu {startIdx} đến câu {endIdx}.", options);
                body.AppendChild(secPara);

                foreach (var q in tlQuestions)
                {
                    var imgBytesList = ExtractQuestionImagesBytes(q);
                    string cleanContent = CleanImageTagsFromContent(q.Content);

                    if (imgBytesList.Count > 0)
                    {
                        var qTable = CreateQuestionWithImageTable(
                            mainPart,
                            $"Câu {globalIndex}. {cleanContent}",
                            null,
                            "Essay",
                            imgBytesList,
                            options);
                        body.AppendChild(qTable);
                    }
                    else
                    {
                        var qPara = CreateFormattedParagraph($"Câu {globalIndex}. {cleanContent}", options);
                        body.AppendChild(qPara);
                    }

                    globalIndex++;
                }
            }

            // Dòng kết thúc đề
            var endPara = new Paragraph(
                new ParagraphProperties(
                    new SpacingBetweenLines { Line = "240", LineRule = LineSpacingRuleValues.Auto, Before = "120", After = "40" },
                    new Justification { Val = JustificationValues.Center }),
                new Run(
                    new RunProperties(CreateRunFonts(options.FontFamily), new FontSize { Val = options.FontSizePt }, new Bold()),
                    new Text("HẾT") { Space = SpaceProcessingModeValues.Preserve }));
            body.AppendChild(endPara);

            // ── PHẦN LỜI GIẢI CHI TIẾT & BẢNG ĐÁP ÁN (nếu chọn) ──
            if (options.IncludeSolution)
            {
                var ansTitlePara = new Paragraph(
                    new ParagraphProperties(
                        new SpacingBetweenLines { Line = "240", LineRule = LineSpacingRuleValues.Auto, Before = "240", After = "80" },
                        new Justification { Val = JustificationValues.Center }),
                    new Run(
                        new RunProperties(CreateRunFonts(options.FontFamily), new FontSize { Val = "26" }, new Bold()),
                        new Text("ĐÁP ÁN THAM KHẢO") { Space = SpaceProcessingModeValues.Preserve }));
                body.AppendChild(ansTitlePara);

                // Bảng đáp án nhanh trắc nghiệm
                if (tnQuestions.Count > 0)
                {
                    var ansTable = CreateQuickAnswerTable(tnQuestions, options);
                    body.AppendChild(ansTable);
                }

                var solTitlePara = new Paragraph(
                    new ParagraphProperties(
                        new SpacingBetweenLines { Line = "240", LineRule = LineSpacingRuleValues.Auto, Before = "240", After = "120" },
                        new Justification { Val = JustificationValues.Center }),
                    new Run(
                        new RunProperties(CreateRunFonts(options.FontFamily), new FontSize { Val = "26" }, new Bold()),
                        new Text("HƯỚNG DẪN GIẢI CHI TIẾT") { Space = SpaceProcessingModeValues.Preserve }));
                body.AppendChild(solTitlePara);

                // Chi tiết từng câu
                int solIdx = 1;
                foreach (var q in qList)
                {
                    var headSolPara = new Paragraph(
                        new ParagraphProperties(new SpacingBetweenLines { Line = "240", LineRule = LineSpacingRuleValues.Auto, Before = "100", After = "40" }),
                        new Run(
                            new RunProperties(CreateRunFonts(options.FontFamily), new FontSize { Val = options.FontSizePt }, new Bold()),
                            new Text($"Câu {solIdx}. ") { Space = SpaceProcessingModeValues.Preserve }));

                    if (q.QuestionType == "MultipleChoice4" && !string.IsNullOrWhiteSpace(q.CorrectAnswer))
                    {
                        headSolPara.AppendChild(new Run(
                            new RunProperties(CreateRunFonts(options.FontFamily), new FontSize { Val = options.FontSizePt }, new Bold()),
                            new Text($"Chọn {q.CorrectAnswer}.") { Space = SpaceProcessingModeValues.Preserve }));
                    }
                    else if (q.QuestionType == "ShortAnswer" && !string.IsNullOrWhiteSpace(q.CorrectAnswer))
                    {
                        headSolPara.AppendChild(new Run(
                            new RunProperties(CreateRunFonts(options.FontFamily), new FontSize { Val = options.FontSizePt }, new Bold()),
                            new Text($"Đáp số: {q.CorrectAnswer}.") { Space = SpaceProcessingModeValues.Preserve }));
                    }
                    body.AppendChild(headSolPara);

                    // In lời giải chi tiết
                    string solText = string.IsNullOrWhiteSpace(q.Explanation) ? "(Đang cập nhật lời giải)" : q.Explanation;
                    solText = QuestionParserEngine.FilterLatexItems(solText);
                    var solLines = solText.Split(new[] { "\r\n", "\r", "\n" }, StringSplitOptions.None);

                    if (solLines.Any(l => Regex.IsMatch(l.Trim(), @"^[a-d]\)")))
                    {
                        var headPara = CreateFormattedParagraph("Lời giải:", options);
                        body.AppendChild(headPara);
                        foreach (var sLine in solLines)
                        {
                            if (string.IsNullOrWhiteSpace(sLine)) continue;
                            var solPara = CreateFormattedParagraph(sLine.Trim(), options);
                            body.AppendChild(solPara);
                        }
                    }
                    else
                    {
                        bool isFirstSolLine = true;
                        foreach (var sLine in solLines)
                        {
                            if (string.IsNullOrWhiteSpace(sLine)) continue;
                            string lineToFormat = isFirstSolLine &&
                                !sLine.Trim().StartsWith("Lời giải", StringComparison.OrdinalIgnoreCase) &&
                                !sLine.Trim().StartsWith("Hướng dẫn", StringComparison.OrdinalIgnoreCase)
                                ? $"Lời giải: {sLine.Trim()}"
                                : sLine.Trim();
                            var solPara = CreateFormattedParagraph(lineToFormat, options);
                            body.AppendChild(solPara);
                            isFirstSolLine = false;
                        }
                    }

                    solIdx++;
                }
            }

            mainPart.Document.Save();
        }

        private static Table CreateExamHeaderTable(int totalCount, ExamExportOptions options)
        {
            var table = new Table();
            var tblPr = new TableProperties(
                new TableBorders(
                    new TopBorder { Val = BorderValues.None },
                    new BottomBorder { Val = BorderValues.None },
                    new LeftBorder { Val = BorderValues.None },
                    new RightBorder { Val = BorderValues.None },
                    new InsideHorizontalBorder { Val = BorderValues.None },
                    new InsideVerticalBorder { Val = BorderValues.None }),
                new TableWidth { Type = TableWidthUnitValues.Pct, Width = "5000" },
                new TableJustification { Val = TableRowAlignmentValues.Center });
            table.AppendChild(tblPr);

            var row = new TableRow();

            // Cột trái: SỞ GD&ĐT / ĐỀ KIỂM TRA / (Đề thi gồm {N} câu)
            var cellLeft = new TableCell(
                new TableCellProperties(new TableCellWidth { Type = TableWidthUnitValues.Pct, Width = "2000" }));
            AddCenteredLine(cellLeft, string.IsNullOrWhiteSpace(options.SchoolName) ? "SỞ/PHÒNG GD&ĐT" : options.SchoolName.ToUpper(), bold: true, sizePt: "24", options: options);
            AddCenteredLine(cellLeft, string.IsNullOrWhiteSpace(options.ExamTitle) ? "ĐỀ KIỂM TRA" : options.ExamTitle.ToUpper(), bold: true, sizePt: "24", options: options);
            AddCenteredLine(cellLeft, $"(Đề thi gồm {totalCount:02d} câu)", bold: false, italic: false, sizePt: "24", options: options);
            row.AppendChild(cellLeft);

            // Cột phải: ĐỀ THI MÔN... / Môn thi: ... / Thời gian làm bài: ... / Lớp: ... Năm học: ...
            var cellRight = new TableCell(
                new TableCellProperties(new TableCellWidth { Type = TableWidthUnitValues.Pct, Width = "3000" }));
            string subjectUpper = (options.Subject ?? "TOÁN").ToUpper();
            AddCenteredLine(cellRight, $"ĐỀ THI MÔN {subjectUpper} - LỚP {options.Grade}", bold: true, sizePt: "24", options: options);
            AddCenteredLine(cellRight, $"Môn thi: {subjectUpper}", bold: true, sizePt: "24", options: options);
            AddCenteredLine(cellRight, $"Thời gian làm bài {options.TimeMinutes}, không kể thời gian phát đề", bold: false, italic: false, sizePt: "24", options: options);
            AddCenteredLine(cellRight, $"Lớp: {options.Grade}  Năm học: {options.ExamYear}", bold: false, sizePt: "24", options: options);
            row.AppendChild(cellRight);

            table.AppendChild(row);
            return table;
        }

        private static void AddCenteredLine(TableCell cell, string text, bool bold = false, bool italic = false, string sizePt = "24", ExamExportOptions? options = null)
        {
            string font = options?.FontFamily ?? "Times New Roman";
            var p = new Paragraph(
                new ParagraphProperties(
                    new SpacingBetweenLines { Line = "220", LineRule = LineSpacingRuleValues.Auto, After = "20", Before = "0" },
                    new Justification { Val = JustificationValues.Center }));

            var runPr = new RunProperties(
                new RunFonts { Ascii = font, HighAnsi = font, ComplexScript = font },
                new FontSize { Val = sizePt });
            if (bold) runPr.Bold = new Bold();
            if (italic) runPr.Italic = new Italic();

            p.AppendChild(new Run(runPr, new Text(text) { Space = SpaceProcessingModeValues.Preserve }));
            cell.AppendChild(p);
        }

        private static Paragraph CreateCandidateParagraph(ExamExportOptions options)
        {
            var p = new Paragraph(
                new ParagraphProperties(
                    new SpacingBetweenLines { Line = "240", LineRule = LineSpacingRuleValues.Auto, Before = "40", After = "80" },
                    new Justification { Val = JustificationValues.Both },
                    new Tabs(
                        new TabStop { Val = TabStopValues.Left, Position = 283 },
                        new TabStop { Val = TabStopValues.Left, Position = 2835 },
                        new TabStop { Val = TabStopValues.Left, Position = 5386 },
                        new TabStop { Val = TabStopValues.Left, Position = 7937 }
                    )));

            var runPr = new RunProperties(
                CreateRunFonts(options.FontFamily),
                new FontSize { Val = options.FontSizePt });

            var boldPr = new RunProperties(
                CreateRunFonts(options.FontFamily),
                new FontSize { Val = options.FontSizePt },
                new Bold());

            p.AppendChild(new Run(runPr, new Text("Họ và tên: …………………………………………..   Số báo danh: ………………\t") { Space = SpaceProcessingModeValues.Preserve }));
            string codeStr = string.IsNullOrWhiteSpace(options.ExamCode) ? "Mã đề: ………" : $"Mã đề {options.ExamCode}";
            p.AppendChild(new Run(boldPr, new Text(codeStr) { Space = SpaceProcessingModeValues.Preserve }));
            return p;
        }

        private static Paragraph CreateHorizontalRuleParagraph()
        {
            var p = new Paragraph(
                new ParagraphProperties(
                    new SpacingBetweenLines { Line = "240", LineRule = LineSpacingRuleValues.Auto, Before = "0", After = "120" },
                    new ParagraphBorders(
                        new BottomBorder { Val = BorderValues.Single, Size = 6, Space = 1, Color = "1F497D" }
                    )
                )
            );
            return p;
        }

        private static Paragraph CreateSectionHeadingParagraph(string text, WordExportOptions options)
        {
            var p = new Paragraph(
                new ParagraphProperties(
                    new SpacingBetweenLines { Line = "260", LineRule = LineSpacingRuleValues.Auto, Before = "140", After = "80" }));

            var runPr = new RunProperties(
                CreateRunFonts(options.FontFamily),
                new FontSize { Val = options.FontSizePt },
                new Bold());

            p.AppendChild(new Run(runPr, new Text(text) { Space = SpaceProcessingModeValues.Preserve }));
            return p;
        }

        private static Table CreateStudentAnswerSheetTable(int count, ExamExportOptions options)
        {
            var table = new Table();
            var tblPr = new TableProperties(
                new TableBorders(
                    new TopBorder { Val = BorderValues.Single, Size = 4, Space = 0, Color = "000000" },
                    new BottomBorder { Val = BorderValues.Single, Size = 4, Space = 0, Color = "000000" },
                    new LeftBorder { Val = BorderValues.Single, Size = 4, Space = 0, Color = "000000" },
                    new RightBorder { Val = BorderValues.Single, Size = 4, Space = 0, Color = "000000" },
                    new InsideHorizontalBorder { Val = BorderValues.Single, Size = 4, Space = 0, Color = "000000" },
                    new InsideVerticalBorder { Val = BorderValues.Single, Size = 4, Space = 0, Color = "000000" }),
                new TableWidth { Type = TableWidthUnitValues.Pct, Width = "5000" },
                new TableJustification { Val = TableRowAlignmentValues.Center });
            table.AppendChild(tblPr);

            var rowHead = new TableRow();
            var rowAns = new TableRow();

            // Ô tiêu đề "Câu"
            var cellHead0 = new TableCell(
                new Paragraph(
                    new ParagraphProperties(
                        new SpacingBetweenLines { Line = "220", LineRule = LineSpacingRuleValues.Auto, Before = "20", After = "20" },
                        new Justification { Val = JustificationValues.Center }),
                    new Run(new RunProperties(CreateRunFonts(options.FontFamily), new Bold(), new FontSize { Val = "22" }), new Text("Câu"))));
            rowHead.AppendChild(cellHead0);

            // Ô tiêu đề "Đáp án"
            var cellAns0 = new TableCell(
                new Paragraph(
                    new ParagraphProperties(
                        new SpacingBetweenLines { Line = "220", LineRule = LineSpacingRuleValues.Auto, Before = "40", After = "40" },
                        new Justification { Val = JustificationValues.Center }),
                    new Run(new RunProperties(CreateRunFonts(options.FontFamily), new Bold(), new FontSize { Val = "22" }), new Text("Đáp án"))));
            rowAns.AppendChild(cellAns0);

            for (int i = 1; i <= count; i++)
            {
                var cellH = new TableCell(
                    new Paragraph(
                        new ParagraphProperties(
                            new SpacingBetweenLines { Line = "220", LineRule = LineSpacingRuleValues.Auto, Before = "20", After = "20" },
                            new Justification { Val = JustificationValues.Center }),
                        new Run(new RunProperties(CreateRunFonts(options.FontFamily), new Bold(), new FontSize { Val = "22" }), new Text(i.ToString()))));
                rowHead.AppendChild(cellH);

                var cellA = new TableCell(
                    new Paragraph(
                        new ParagraphProperties(
                            new SpacingBetweenLines { Line = "220", LineRule = LineSpacingRuleValues.Auto, Before = "40", After = "40" },
                            new Justification { Val = JustificationValues.Center }),
                        new Run(new RunProperties(CreateRunFonts(options.FontFamily), new FontSize { Val = "22" }), new Text(" ") { Space = SpaceProcessingModeValues.Preserve })));
                rowAns.AppendChild(cellA);
            }

            table.AppendChild(rowHead);
            table.AppendChild(rowAns);
            return table;
        }

        private static string EnsureDot(string text)
        {
            var t = (text ?? "").Trim();
            if (!string.IsNullOrEmpty(t) && !t.EndsWith(".") && !t.EndsWith("?") && !t.EndsWith("!") && !t.EndsWith(":") && !t.EndsWith(";"))
            {
                t += ".";
            }
            return t;
        }

        private static void AppendFormattedRuns(Paragraph p, string text, WordExportOptions options)
        {
            if (string.IsNullOrEmpty(text)) return;

            var regex = new Regex(@"(\$\{[\s\S]*?\}\$|\$\{[^}\n]+?\}|\$[^$\n]+?\$)", RegexOptions.Singleline);
            var parts = regex.Split(text);

            foreach (var part in parts)
            {
                if (string.IsNullOrEmpty(part)) continue;

                var run = new Run();
                var runPr = new RunProperties(
                    CreateRunFonts(options.FontFamily),
                    new FontSize { Val = options.FontSizePt }
                );

                if ((part.StartsWith("${") && (part.EndsWith("}$") || part.EndsWith("}"))) ||
                    (part.StartsWith("$") && part.EndsWith("$") && part.Length > 1))
                {
                    runPr.Italic = new Italic();
                    if (options.HighlightFormulas)
                    {
                        runPr.Color = new Color { Val = "0F172A" };
                    }
                    run.AppendChild(runPr);
                    run.AppendChild(new Text(part) { Space = SpaceProcessingModeValues.Preserve });
                    p.AppendChild(run);
                }
                else
                {
                    // Nếu trong văn bản thường chứa \t thì tách và chèn thẻ <w:tab/> chuẩn OpenXml
                    if (part.Contains('\t'))
                    {
                        var subParts = part.Split('\t');
                        for (int sIdx = 0; sIdx < subParts.Length; sIdx++)
                        {
                            if (sIdx > 0)
                            {
                                p.AppendChild(new Run(new TabChar()));
                            }
                            if (!string.IsNullOrEmpty(subParts[sIdx]))
                            {
                                var subRun = new Run();
                                var subRunPr = new RunProperties(
                                    CreateRunFonts(options.FontFamily),
                                    new FontSize { Val = options.FontSizePt }
                                );
                                subRun.AppendChild(subRunPr);
                                subRun.AppendChild(new Text(subParts[sIdx]) { Space = SpaceProcessingModeValues.Preserve });
                                p.AppendChild(subRun);
                            }
                        }
                    }
                    else
                    {
                        run.AppendChild(runPr);
                        run.AppendChild(new Text(part) { Space = SpaceProcessingModeValues.Preserve });
                        p.AppendChild(run);
                    }
                }
            }
        }

        private static void AppendOptionsParagraphs(OpenXmlElement container, Dictionary<string, string> optionsDict, WordExportOptions options, bool isNarrow = false)
        {
            if (optionsDict == null || optionsDict.Count == 0) return;

            int maxLen = optionsDict.Values.Select(v => (v ?? "").Length).DefaultIfEmpty(0).Max();
            int totalLen = optionsDict.Values.Sum(v => (v ?? "").Length);
            string[] keys = { "A", "B", "C", "D" };

            if (!isNarrow && maxLen <= 35 && totalLen <= 120 && optionsDict.Count == 4)
            {
                // 4 phương án trên 1 dòng: Standard35 tại 3.5cm (1985), 7.0cm (3969), 10.5cm (5953) hoặc Wide45 tại 5.0cm (2835), 9.5cm (5386), 14.0cm (7937)
                var p = new Paragraph();
                var pPr = new ParagraphProperties(
                    new SpacingBetweenLines { Line = "276", LineRule = LineSpacingRuleValues.Auto, Before = "0", After = "160" },
                    new Indentation { Left = "283" } // 0.5 cm
                );
                var tabs = options.TabSpacing == TabSpacingMode.Standard35
                    ? new Tabs(
                        new TabStop { Val = TabStopValues.Left, Position = 1985 },
                        new TabStop { Val = TabStopValues.Left, Position = 3969 },
                        new TabStop { Val = TabStopValues.Left, Position = 5953 }
                    )
                    : new Tabs(
                        new TabStop { Val = TabStopValues.Left, Position = 2835 },
                        new TabStop { Val = TabStopValues.Left, Position = 5386 },
                        new TabStop { Val = TabStopValues.Left, Position = 7937 }
                    );
                pPr.AppendChild(tabs);
                p.AppendChild(pPr);

                for (int i = 0; i < keys.Length; i++)
                {
                    string k = keys[i];
                    string v = EnsureDot(optionsDict.ContainsKey(k) ? optionsDict[k] : "");
                    if (i > 0)
                    {
                        p.AppendChild(new Run(new TabChar()));
                    }

                    var lblRun = new Run(
                        new RunProperties(CreateRunFonts(options.FontFamily), new Bold(), new FontSize { Val = options.FontSizePt }),
                        new Text($"{k}. ") { Space = SpaceProcessingModeValues.Preserve });
                    p.AppendChild(lblRun);

                    AppendFormattedRuns(p, v, options);
                }

                container.AppendChild(p);
            }
            else if (maxLen <= 70 && totalLen <= 220 && optionsDict.Count == 4)
            {
                // 2x2: (A, B) và (C, D)
                string[][] pairs = { new[] { "A", "B" }, new[] { "C", "D" } };
                for (int rowIdx = 0; rowIdx < pairs.Length; rowIdx++)
                {
                    var pair = pairs[rowIdx];
                    var p = new Paragraph();
                    var pPr = new ParagraphProperties(
                        new SpacingBetweenLines { Line = "276", LineRule = LineSpacingRuleValues.Auto, Before = "0", After = rowIdx == pairs.Length - 1 ? "160" : "40" },
                        new Indentation { Left = "283" }
                    );
                    int pos2 = isNarrow ? 3120 : (options.TabSpacing == TabSpacingMode.Standard35 ? 3969 : 4252);
                    var tabs = new Tabs(new TabStop { Val = TabStopValues.Left, Position = pos2 });
                    pPr.AppendChild(tabs);
                    p.AppendChild(pPr);

                    for (int i = 0; i < pair.Length; i++)
                    {
                        string k = pair[i];
                        string v = EnsureDot(optionsDict.ContainsKey(k) ? optionsDict[k] : "");
                        if (i > 0)
                        {
                            p.AppendChild(new Run(new TabChar()));
                        }

                        var lblRun = new Run(
                            new RunProperties(CreateRunFonts(options.FontFamily), new Bold(), new FontSize { Val = options.FontSizePt }),
                            new Text($"{k}. ") { Space = SpaceProcessingModeValues.Preserve });
                        p.AppendChild(lblRun);

                        AppendFormattedRuns(p, v, options);
                    }

                    container.AppendChild(p);
                }
            }
            else
            {
                // Mỗi phương án 1 dòng riêng
                var sortedKeys = optionsDict.Keys.OrderBy(k => k).ToList();
                for (int i = 0; i < sortedKeys.Count; i++)
                {
                    string k = sortedKeys[i];
                    string v = EnsureDot(optionsDict[k]);
                    var p = new Paragraph();
                    var pPr = new ParagraphProperties(
                        new SpacingBetweenLines { Line = "276", LineRule = LineSpacingRuleValues.Auto, Before = "0", After = i == sortedKeys.Count - 1 ? "160" : "40" },
                        new Indentation { Left = "283" }
                    );
                    p.AppendChild(pPr);

                    var lblRun = new Run(
                        new RunProperties(CreateRunFonts(options.FontFamily), new Bold(), new FontSize { Val = options.FontSizePt }),
                        new Text($"{k}. ") { Space = SpaceProcessingModeValues.Preserve });
                    p.AppendChild(lblRun);

                    AppendFormattedRuns(p, v, options);
                    container.AppendChild(p);
                }
            }
        }

        private static Table CreateQuickAnswerTable(List<QuestionItem> tnList, WordExportOptions options)
        {
            var table = new Table();
            table.AppendChild(new TableProperties(
                new TableBorders(
                    new TopBorder { Val = BorderValues.Single, Size = 4, Space = 0, Color = "000000" },
                    new BottomBorder { Val = BorderValues.Single, Size = 4, Space = 0, Color = "000000" },
                    new LeftBorder { Val = BorderValues.Single, Size = 4, Space = 0, Color = "000000" },
                    new RightBorder { Val = BorderValues.Single, Size = 4, Space = 0, Color = "000000" },
                    new InsideHorizontalBorder { Val = BorderValues.Single, Size = 4, Space = 0, Color = "000000" },
                    new InsideVerticalBorder { Val = BorderValues.Single, Size = 4, Space = 0, Color = "000000" }),
                new TableWidth { Type = TableWidthUnitValues.Pct, Width = "5000" },
                new TableJustification { Val = TableRowAlignmentValues.Center }));

            var rowHead = new TableRow();
            var rowAns = new TableRow();

            // Ô tiêu đề bên trái
            var cellHead0 = new TableCell(
                new Paragraph(
                    new ParagraphProperties(
                        new SpacingBetweenLines { Line = "220", LineRule = LineSpacingRuleValues.Auto, Before = "20", After = "20" },
                        new Justification { Val = JustificationValues.Center }),
                    new Run(new RunProperties(CreateRunFonts(options.FontFamily), new Bold(), new FontSize { Val = "22" }), new Text("Câu"))));
            rowHead.AppendChild(cellHead0);

            var cellAns0 = new TableCell(
                new Paragraph(
                    new ParagraphProperties(
                        new SpacingBetweenLines { Line = "220", LineRule = LineSpacingRuleValues.Auto, Before = "20", After = "20" },
                        new Justification { Val = JustificationValues.Center }),
                    new Run(new RunProperties(CreateRunFonts(options.FontFamily), new Bold(), new FontSize { Val = "22" }), new Text("Đáp án"))));
            rowAns.AppendChild(cellAns0);

            for (int i = 0; i < tnList.Count; i++)
            {
                var q = tnList[i];
                var cellH = new TableCell(
                    new Paragraph(
                        new ParagraphProperties(
                            new SpacingBetweenLines { Line = "220", LineRule = LineSpacingRuleValues.Auto, Before = "20", After = "20" },
                            new Justification { Val = JustificationValues.Center }),
                        new Run(new RunProperties(CreateRunFonts(options.FontFamily), new Bold(), new FontSize { Val = "22" }), new Text((i + 1).ToString()))));
                rowHead.AppendChild(cellH);

                var cellA = new TableCell(
                    new Paragraph(
                        new ParagraphProperties(
                            new SpacingBetweenLines { Line = "220", LineRule = LineSpacingRuleValues.Auto, Before = "20", After = "20" },
                            new Justification { Val = JustificationValues.Center }),
                        new Run(new RunProperties(CreateRunFonts(options.FontFamily), new Bold(), new FontSize { Val = "22" }, new Color { Val = "0F172A" }), new Text(q.CorrectAnswer ?? ""))));
                rowAns.AppendChild(cellA);
            }

            table.AppendChild(rowHead);
            table.AppendChild(rowAns);
            return table;
        }

        private static void TryEmbedTikzOrImage(MainDocumentPart mainPart, Body body, QuestionItem q)
        {
            try
            {
                // 1. Nhúng danh sách ảnh từ q.Images (hỗ trợ cả đường dẫn tệp lẫn Base64)
                if (q.Images != null && q.Images.Count > 0)
                {
                    foreach (var imgRef in q.Images)
                    {
                        if (string.IsNullOrWhiteSpace(imgRef)) continue;
                        byte[]? imgBytes = null;
                        if (File.Exists(imgRef))
                        {
                            try { imgBytes = File.ReadAllBytes(imgRef); } catch { }
                        }
                        else
                        {
                            try { imgBytes = Convert.FromBase64String(imgRef); } catch { }
                        }

                        if (imgBytes != null && imgBytes.Length > 0)
                        {
                            AddImageToBody(mainPart, body, imgBytes);
                        }
                    }
                }

                // 2. Nhúng ảnh nếu nội dung câu hỏi có đánh dấu [HINH_ANH: path] hoặc [IMAGE: path] hoặc [HÌNH N: path]
                if (!string.IsNullOrWhiteSpace(q.Content))
                {
                    var imgTagMatches = Regex.Matches(q.Content, @"\[(?:HINH_ANH|IMAGE|ANH|H[ÌI]NH(?:\s*\d+)?):\s*([^\]]+)\]", RegexOptions.IgnoreCase);
                    foreach (Match m in imgTagMatches)
                    {
                        string p = m.Groups[1].Value.Trim();
                        if (File.Exists(p))
                        {
                            try
                            {
                                byte[] imgBytes = File.ReadAllBytes(p);
                                AddImageToBody(mainPart, body, imgBytes);
                            }
                            catch { }
                        }
                        else if (File.Exists(Path.Combine(ImageHelper.GetImagesDirectory(), p)))
                        {
                            try
                            {
                                byte[] imgBytes = File.ReadAllBytes(Path.Combine(ImageHelper.GetImagesDirectory(), p));
                                AddImageToBody(mainPart, body, imgBytes);
                            }
                            catch { }
                        }
                    }
                }

                // 3. Nếu câu hỏi có mã TikZ, biên dịch sang PNG 300 DPI và nhúng vào Word
                if (!string.IsNullOrWhiteSpace(q.TikzCode))
                {
                    var compiler = new TikzCompilerService();
                    if (compiler.Toolchain.IsPdfLatexAvailable)
                    {
                        var req = new TikzCompileRequest
                        {
                            TikzCode = q.TikzCode,
                            Format = TikzExportFormat.Png,
                            Dpi = 300,
                            TimeoutSeconds = 8
                        };
                        var compileTask = compiler.CompileAsync(req);
                        compileTask.Wait(8000);
                        if (compileTask.IsCompletedSuccessfully && compileTask.Result.Success && !string.IsNullOrEmpty(compileTask.Result.ImagePath) && File.Exists(compileTask.Result.ImagePath))
                        {
                            byte[] imgBytes = File.ReadAllBytes(compileTask.Result.ImagePath);
                            AddImageToBody(mainPart, body, imgBytes);
                        }
                    }
                }
            }
            catch { }
        }

        private static int _nextDrawingId = 0;

        public static void AddImageToBody(MainDocumentPart mainPart, Body body, byte[] imageBytes, long maxEmus = 4500000L)
        {
            AddImageToContainer(mainPart, body, imageBytes, maxEmus);
        }

        public static void AddImageToContainer(MainDocumentPart mainPart, OpenXmlElement container, byte[] imageBytes, long maxEmus = 4500000L)
        {
            if (imageBytes == null || imageBytes.Length == 0) return;

            var imagePart = mainPart.AddImagePart(ImagePartType.Png);
            using (var stream = new MemoryStream(imageBytes))
            {
                imagePart.FeedData(stream);
            }
            string relId = mainPart.GetIdOfPart(imagePart);

            long cx = 3600000L; // ~10cm
            long cy = 2520000L; // ~7cm

            if (imageBytes.Length >= 24 && imageBytes[0] == 0x89 && imageBytes[1] == 0x50) // PNG
            {
                int w = (imageBytes[16] << 24) | (imageBytes[17] << 16) | (imageBytes[18] << 8) | imageBytes[19];
                int h = (imageBytes[20] << 24) | (imageBytes[21] << 16) | (imageBytes[22] << 8) | imageBytes[23];
                if (w > 0 && h > 0)
                {
                    cx = (long)(w * 914400.0 / 96.0);
                    cy = (long)(h * 914400.0 / 96.0);
                    if (cx > maxEmus)
                    {
                        double scale = (double)maxEmus / cx;
                        cx = maxEmus;
                        cy = (long)(cy * scale);
                    }
                }
            }

            uint drawingId = (uint)System.Threading.Interlocked.Increment(ref _nextDrawingId);

            var element = new Drawing(
                new DW.Inline(
                    new DW.Extent() { Cx = cx, Cy = cy },
                    new DW.EffectExtent() { LeftEdge = 0L, TopEdge = 0L, RightEdge = 0L, BottomEdge = 0L },
                    new DW.DocProperties() { Id = (UInt32Value)drawingId, Name = $"Figure_{drawingId}" },
                    new DW.NonVisualGraphicFrameDrawingProperties(new A.GraphicFrameLocks() { NoChangeAspect = true }),
                    new A.Graphic(
                        new A.GraphicData(
                            new PIC.Picture(
                                new PIC.NonVisualPictureProperties(
                                    new PIC.NonVisualDrawingProperties() { Id = (UInt32Value)drawingId, Name = $"Figure_{drawingId}.png" },
                                    new PIC.NonVisualPictureDrawingProperties()),
                                new PIC.BlipFill(
                                    new A.Blip() { Embed = relId, CompressionState = A.BlipCompressionValues.Print },
                                    new A.Stretch(new A.FillRectangle())),
                                new PIC.ShapeProperties(
                                    new A.Transform2D(
                                        new A.Offset() { X = 0L, Y = 0L },
                                        new A.Extents() { Cx = cx, Cy = cy }),
                                    new A.PresetGeometry(new A.AdjustValueList()) { Preset = A.ShapeTypeValues.Rectangle }))
                        ) { Uri = "http://schemas.openxmlformats.org/drawingml/2006/picture" })
                )
                {
                    DistanceFromTop = (UInt32Value)0U,
                    DistanceFromBottom = (UInt32Value)0U,
                    DistanceFromLeft = (UInt32Value)0U,
                    DistanceFromRight = (UInt32Value)0U
                });

            var p = new Paragraph(
                new ParagraphProperties(
                    new SpacingBetweenLines { Line = "240", LineRule = LineSpacingRuleValues.Auto, After = "120" },
                    new Justification { Val = JustificationValues.Center }),
                new Run(element));
            container.AppendChild(p);
        }

        private static string CleanImageTagsFromContent(string? content)
        {
            if (string.IsNullOrWhiteSpace(content)) return string.Empty;
            return Regex.Replace(content, @"\[(?:HINH_ANH|IMAGE|ANH|H[ÌI]NH(?:\s*\d+)?):\s*[^\]]+\]", "").Trim();
        }

        private static List<byte[]> ExtractQuestionImagesBytes(QuestionItem q)
        {
            var result = new List<byte[]>();
            try
            {
                if (q.Images != null && q.Images.Count > 0)
                {
                    foreach (var imgRef in q.Images)
                    {
                        if (string.IsNullOrWhiteSpace(imgRef)) continue;
                        if (File.Exists(imgRef))
                        {
                            try { result.Add(File.ReadAllBytes(imgRef)); } catch { }
                        }
                        else
                        {
                            try { result.Add(Convert.FromBase64String(imgRef)); } catch { }
                        }
                    }
                }

                if (!string.IsNullOrWhiteSpace(q.Content))
                {
                    var matches = Regex.Matches(q.Content, @"\[(?:HINH_ANH|IMAGE|ANH|H[ÌI]NH(?:\s*\d+)?):\s*([^\]]+)\]", RegexOptions.IgnoreCase);
                    foreach (Match match in matches)
                    {
                        string p = match.Groups[1].Value.Trim();
                        if (File.Exists(p))
                        {
                            try { result.Add(File.ReadAllBytes(p)); } catch { }
                        }
                        else
                        {
                            string fallback = Path.Combine(ImageHelper.GetImagesDirectory(), p);
                            if (File.Exists(fallback))
                            {
                                try { result.Add(File.ReadAllBytes(fallback)); } catch { }
                            }
                        }
                    }
                }

                if (!string.IsNullOrWhiteSpace(q.TikzCode))
                {
                    var compiler = new TikzCompilerService();
                    if (compiler.Toolchain.IsPdfLatexAvailable)
                    {
                        var req = new TikzCompileRequest
                        {
                            TikzCode = q.TikzCode,
                            Format = TikzExportFormat.Png,
                            Dpi = 300,
                            TimeoutSeconds = 8
                        };
                        var task = compiler.CompileAsync(req);
                        task.Wait(8000);
                        if (task.IsCompletedSuccessfully && task.Result.Success && !string.IsNullOrEmpty(task.Result.ImagePath) && File.Exists(task.Result.ImagePath))
                        {
                            result.Add(File.ReadAllBytes(task.Result.ImagePath));
                        }
                    }
                }
            }
            catch { }
            return result;
        }

        private static Table CreateQuestionWithImageTable(
            MainDocumentPart mainPart,
            string questionText,
            Dictionary<string, string>? optionsDict,
            string questionType,
            List<byte[]> imageBytesList,
            ExamExportOptions options)
        {
            var table = new Table();
            var tblPr = new TableProperties(
                new TableBorders(
                    new TopBorder { Val = BorderValues.None },
                    new BottomBorder { Val = BorderValues.None },
                    new LeftBorder { Val = BorderValues.None },
                    new RightBorder { Val = BorderValues.None },
                    new InsideHorizontalBorder { Val = BorderValues.None },
                    new InsideVerticalBorder { Val = BorderValues.None }
                ),
                new TableWidth { Type = TableWidthUnitValues.Dxa, Width = "9640" },
                new TableJustification { Val = TableRowAlignmentValues.Center }
            );
            table.AppendChild(tblPr);

            var row = new TableRow();

            // Cột 1: Câu hỏi và các phương án (chiếm ~11.5cm = 6520 twips)
            var cellLeft = new TableCell();
            var cellLeftPr = new TableCellProperties(
                new TableCellWidth { Type = TableWidthUnitValues.Dxa, Width = "6520" },
                new TableCellVerticalAlignment { Val = TableVerticalAlignmentValues.Center }
            );
            cellLeft.AppendChild(cellLeftPr);

            var qPara = CreateFormattedParagraph(questionText, options);
            cellLeft.AppendChild(qPara);

            if (optionsDict != null && optionsDict.Count > 0)
            {
                if (questionType == "TrueFalse4")
                {
                    string[] keys = { "a", "b", "c", "d" };
                    foreach (var k in keys)
                    {
                        if (optionsDict.ContainsKey(k))
                        {
                            var itemPara = CreateFormattedParagraph($"{k}) {optionsDict[k]}", options);
                            cellLeft.AppendChild(itemPara);
                        }
                    }
                }
                else
                {
                    AppendOptionsParagraphs(cellLeft, optionsDict, options, isNarrow: true);
                }
            }
            else if (questionType == "ShortAnswer")
            {
                var ansPara = CreateFormattedParagraph("Đáp án: | | | | |", options);
                cellLeft.AppendChild(ansPara);
            }

            row.AppendChild(cellLeft);

            // Cột 2: Hình ảnh căn giữa (chiếm ~5.5cm = 3120 twips)
            var cellRight = new TableCell();
            var cellRightPr = new TableCellProperties(
                new TableCellWidth { Type = TableWidthUnitValues.Dxa, Width = "3120" },
                new TableCellVerticalAlignment { Val = TableVerticalAlignmentValues.Center }
            );
            cellRight.AppendChild(cellRightPr);

            foreach (var imgBytes in imageBytesList)
            {
                AddImageToContainer(mainPart, cellRight, imgBytes, maxEmus: 1850000L);
            }

            row.AppendChild(cellRight);
            table.AppendChild(row);
            return table;
        }

        /// <summary>
        /// Xuất nội dung đề thi chuẩn hóa ra file Word (.docx) native với bảng Table Grid và công thức toán ${...}$.
        /// </summary>
        public void ExportToDocx(string filePath, string content, WordExportOptions? options = null)
        {
            options ??= new WordExportOptions();

            using var wordDocument = WordprocessingDocument.Create(filePath, WordprocessingDocumentType.Document);
            var mainPart = wordDocument.AddMainDocumentPart();
            mainPart.Document = new Document();
            AddDocumentDefaultStyles(mainPart, options.FontFamily, options.FontSizePt);
            var body = mainPart.Document.AppendChild(new Body());

            // Thiết lập khổ giấy A4 và lề chuẩn
            ApplyA4PageSettings(body);

            // Xử lý nội dung theo từng dòng
            var lines = content.Split(new[] { "\r\n", "\r", "\n" }, StringSplitOptions.None);
            var tableBuffer = new List<string>();

            for (int i = 0; i < lines.Length; i++)
            {
                string line = lines[i];
                string trimmed = line.Trim();
                bool isTableLine = IsMarkdownTableLine(line);

                if (isTableLine && options.ConvertTablesToWordGrid)
                {
                    tableBuffer.Add(line);
                }
                else
                {
                    // Nếu đang có bảng dở dang trong buffer thì xả ra Word Table trước
                    if (tableBuffer.Count > 0)
                    {
                        var table = CreateWordTable(tableBuffer, options);
                        body.AppendChild(table);
                        tableBuffer.Clear();
                    }

                    // Nếu là dòng ngăn cách bảng (|---|---|) đứng trơ trọi, bỏ qua
                    if (IsTableSeparator(trimmed) && trimmed.StartsWith("|"))
                    {
                        continue;
                    }

                    // Nếu là phương án trắc nghiệm ở dạng markdown pipes (| A. ... | B. ... |), chuyển đổi sang tab stops
                    if (trimmed.StartsWith("|") && IsOptionLine(trimmed))
                    {
                        var cells = SplitTableCells(trimmed).Select(c => c.Trim()).Where(c => !string.IsNullOrEmpty(c)).ToList();
                        if (cells.Count > 0)
                        {
                            line = string.Join("\t", cells);
                        }
                    }
                    else if (Regex.IsMatch(trimmed, @"^[A-D]\.\s+.*?\s{2,}[B-D]\.\s+"))
                    {
                        // Chuyển dấu cách nhiều khoảng trắng giữa các phương án thành \t
                        line = Regex.Replace(trimmed, @"\s{2,}(?=[B-D]\.\s*)", "\t");
                    }

                    // Nhúng ảnh nếu dòng chứa thẻ ảnh [HINH_ANH: path] / [IMAGE: path] / [HÌNH N: path] / [ANH: path] / [HÌNH N]
                    var inlineImgMatches = Regex.Matches(line, @"\[(?:HINH_ANH|IMAGE|ANH|H[ÌI]NH(?:\s*\d+)?)(?::\s*([^\]]+))?\]", RegexOptions.IgnoreCase);
                    if (inlineImgMatches.Count > 0)
                    {
                        var foundBytesList = new List<byte[]>();
                        foreach (Match m in inlineImgMatches)
                        {
                            byte[]? imgBytes = null;
                            string p = m.Groups[1].Success ? m.Groups[1].Value.Trim() : string.Empty;

                            // 1. Kiểm tra nếu p là đường dẫn tệp thực tế
                            if (!string.IsNullOrEmpty(p) && File.Exists(p))
                            {
                                try { imgBytes = File.ReadAllBytes(p); } catch { }
                            }
                            // 2. Kiểm tra nếu p là tên file trong IMAGES_DIR
                            else if (!string.IsNullOrEmpty(p) && File.Exists(Path.Combine(ImageHelper.GetImagesDirectory(), p)))
                            {
                                try { imgBytes = File.ReadAllBytes(Path.Combine(ImageHelper.GetImagesDirectory(), p)); } catch { }
                            }
                            // 3. Kiểm tra Base64
                            else if (!string.IsNullOrEmpty(p) && (p.StartsWith("data:image", StringComparison.OrdinalIgnoreCase) || p.Length > 200))
                            {
                                try
                                {
                                    string cleanBase64 = p.Contains(",") ? p.Substring(p.IndexOf(',') + 1) : p;
                                    imgBytes = Convert.FromBase64String(cleanBase64.Trim());
                                }
                                catch { }
                            }

                            // 4. Kiểm tra chỉ số [HÌNH N] trong options.ExtractedImages nếu chưa load được
                            if (imgBytes == null && options?.ExtractedImages != null && options.ExtractedImages.Count > 0)
                            {
                                var numMatch = Regex.Match(m.Value, @"\[H[ÌI]NH\s*(\d+)", RegexOptions.IgnoreCase);
                                if (numMatch.Success && int.TryParse(numMatch.Groups[1].Value, out int imgIdx) && imgIdx >= 1 && imgIdx <= options.ExtractedImages.Count)
                                {
                                    string candidate = options.ExtractedImages[imgIdx - 1];
                                    if (File.Exists(candidate))
                                    {
                                        try { imgBytes = File.ReadAllBytes(candidate); } catch { }
                                    }
                                }
                            }

                            if (imgBytes != null && imgBytes.Length > 0)
                            {
                                foundBytesList.Add(imgBytes);
                            }
                        }

                        // Xóa sạch marker khỏi dòng văn bản để không để lại text rác trong Word
                        line = Regex.Replace(line, @"\[(?:HINH_ANH|IMAGE|ANH|H[ÌI]NH(?:\s*\d+)?)(?::\s*([^\]]+))?\]", "").Trim();

                        // Nếu dòng vẫn còn nội dung câu hỏi, thêm đoạn văn câu hỏi trước
                        if (!string.IsNullOrWhiteSpace(line))
                        {
                            var paragraph = CreateFormattedParagraph(line, options);
                            body.AppendChild(paragraph);
                            line = string.Empty;
                        }

                        // Nhúng ảnh căn giữa vào tài liệu ngay sau nội dung câu hỏi
                        foreach (var b in foundBytesList)
                        {
                            AddImageToBody(mainPart, body, b);
                        }

                        continue;
                    }

                    // Thêm đoạn văn thông thường hoặc đoạn văn có Tab Stops
                    if (!string.IsNullOrWhiteSpace(line))
                    {
                        var paragraph = CreateFormattedParagraph(line, options);
                        body.AppendChild(paragraph);
                    }
                    else
                    {
                        // Dòng trống
                        body.AppendChild(new Paragraph());
                    }
                }
            }

            // Xả bảng còn lại nếu kết thúc văn bản bằng bảng
            if (tableBuffer.Count > 0 && options.ConvertTablesToWordGrid)
            {
                var table = CreateWordTable(tableBuffer, options);
                body.AppendChild(table);
                tableBuffer.Clear();
            }

            mainPart.Document.Save();
        }

        private static bool IsMarkdownTableLine(string line)
        {
            string trimmed = line.Trim();
            if (!trimmed.StartsWith("|") || !trimmed.EndsWith("|") || trimmed.Count(c => c == '|') < 2)
                return false;

            // Tuyệt đối không coi các dòng phương án trắc nghiệm là bảng dữ liệu TableGrid
            if (IsOptionLine(trimmed))
                return false;

            return true;
        }

        private static bool IsOptionLine(string line)
        {
            if (string.IsNullOrWhiteSpace(line)) return false;
            string trimmed = line.Trim();

            // Dạng pipes: | A. ... | B. ... | hoặc | A. ... |
            if (trimmed.StartsWith("|") && (Regex.IsMatch(trimmed, @"\|\s*[A-D]\.\s*") || Regex.IsMatch(trimmed, @"\|\s*[a-d]\)\s*")))
                return true;

            // Dạng tab: A. ... \t B. ... hoặc a) ... \t b) ...
            if (trimmed.Contains('\t') && (Regex.IsMatch(trimmed, @"^[A-D]\.\s+") || Regex.IsMatch(trimmed, @"^[a-d]\)\s+")))
                return true;

            // Dạng dấu cách quãng: A. ...   B. ...
            if (Regex.IsMatch(trimmed, @"^[A-D]\.\s+.*?(?:\t|\s{2,})[B-D]\.\s+"))
                return true;

            // Dạng phương án đơn lẻ: A. ... hoặc a) ...
            if (Regex.IsMatch(trimmed, @"^[A-D]\.\s+") || Regex.IsMatch(trimmed, @"^[a-d]\)\s+"))
                return true;

            return false;
        }

        private static bool IsTableSeparator(string line)
        {
            string clean = line.Replace("|", "").Replace("-", "").Replace(":", "").Trim();
            return string.IsNullOrEmpty(clean);
        }

        public static List<string> SplitTableCells(string row)
        {
            string inner = row.Trim();
            if (inner.StartsWith("|")) inner = inner.Substring(1);
            if (inner.EndsWith("|")) inner = inner.Substring(0, inner.Length - 1);

            var cells = new List<string>();
            var cur = new System.Text.StringBuilder();
            bool inMath = false;

            for (int i = 0; i < inner.Length; i++)
            {
                char c = inner[i];
                if (c == '$') inMath = !inMath;

                if (c == '|' && !inMath)
                {
                    cells.Add(cur.ToString().Trim());
                    cur.Clear();
                }
                else
                {
                    cur.Append(c);
                }
            }
            cells.Add(cur.ToString().Trim());
            return cells;
        }

        private static Table CreateWordTable(List<string> rawLines, WordExportOptions options)
        {
            var table = new Table();

            // Định dạng thuộc tính bảng (Border, Alignment, Width)
            var tblPr = new TableProperties(
                new TableBorders(
                    new TopBorder { Val = BorderValues.Single, Size = 4, Space = 0, Color = "808080" },
                    new BottomBorder { Val = BorderValues.Single, Size = 4, Space = 0, Color = "808080" },
                    new LeftBorder { Val = BorderValues.Single, Size = 4, Space = 0, Color = "808080" },
                    new RightBorder { Val = BorderValues.Single, Size = 4, Space = 0, Color = "808080" },
                    new InsideHorizontalBorder { Val = BorderValues.Single, Size = 4, Space = 0, Color = "CCCCCC" },
                    new InsideVerticalBorder { Val = BorderValues.Single, Size = 4, Space = 0, Color = "CCCCCC" }
                ),
                new TableWidth { Type = TableWidthUnitValues.Pct, Width = "5000" }, // 100% độ rộng lề
                new TableJustification { Val = TableRowAlignmentValues.Center }
            );
            table.AppendChild(tblPr);

            bool isHeader = true;
            foreach (var line in rawLines)
            {
                if (IsTableSeparator(line))
                {
                    isHeader = false;
                    continue;
                }

                var row = new TableRow();
                var cols = SplitTableCells(line);

                foreach (var rawCol in cols)
                {
                    string colText = rawCol.Trim();
                    var cell = new TableCell();

                    var cellPr = new TableCellProperties(
                        new TableCellMargin(
                            new TopMargin { Width = "120" },
                            new BottomMargin { Width = "120" },
                            new LeftMargin { Width = "160" },
                            new RightMargin { Width = "160" }
                        ),
                        new TableCellVerticalAlignment { Val = TableVerticalAlignmentValues.Center }
                    );

                    if (isHeader)
                    {
                        cellPr.AppendChild(new Shading { Val = ShadingPatternValues.Clear, Fill = "F1F5F9" });
                    }
                    cell.AppendChild(cellPr);

                    var p = CreateFormattedParagraph(colText, options);
                    var pPr = p.GetFirstChild<ParagraphProperties>() ?? p.PrependChild(new ParagraphProperties());
                    pPr.Justification = new Justification { Val = JustificationValues.Center };

                    cell.AppendChild(p);
                    row.AppendChild(cell);
                }

                table.AppendChild(row);
                isHeader = false;
            }

            return table;
        }

        public static RunFonts CreateRunFonts(string fontName)
        {
            return new RunFonts
            {
                Ascii = fontName,
                HighAnsi = fontName,
                EastAsia = fontName,
                ComplexScript = fontName
            };
        }

        public static void AddDocumentDefaultStyles(MainDocumentPart mainPart, string fontName = "Times New Roman", string fontSizePt = "24")
        {
            var stylesPart = mainPart.StyleDefinitionsPart ?? mainPart.AddNewPart<StyleDefinitionsPart>();
            var styles = new Styles();

            // DocDefaults thiết lập font mặc định cho toàn bộ tài liệu (Times New Roman, 12pt)
            var docDefaults = new DocDefaults(
                new RunPropertiesDefault(
                    new RunPropertiesBaseStyle(
                        CreateRunFonts(fontName),
                        new FontSize { Val = fontSizePt },
                        new FontSizeComplexScript { Val = fontSizePt },
                        new Color { Val = "000000" }
                    )
                ),
                new ParagraphPropertiesDefault(
                    new ParagraphPropertiesBaseStyle(
                        new SpacingBetweenLines { Line = "276", LineRule = LineSpacingRuleValues.Auto, After = "100" }
                    )
                )
            );
            styles.AppendChild(docDefaults);

            // Style "Normal" chuẩn
            var normalStyle = new Style
            {
                Type = StyleValues.Paragraph,
                StyleId = "Normal",
                Default = true
            };
            normalStyle.AppendChild(new StyleName { Val = "Normal" });
            normalStyle.AppendChild(new PrimaryStyle());
            var normalRunPr = new StyleRunProperties(
                CreateRunFonts(fontName),
                new FontSize { Val = fontSizePt },
                new FontSizeComplexScript { Val = fontSizePt },
                new Color { Val = "000000" }
            );
            normalStyle.AppendChild(normalRunPr);
            styles.AppendChild(normalStyle);

            stylesPart.Styles = styles;
        }

        private static Paragraph CreateFormattedParagraph(string line, WordExportOptions options)
        {
            var p = new Paragraph();
            var pPr = new ParagraphProperties(
                new SpacingBetweenLines { Line = "276", LineRule = LineSpacingRuleValues.Auto, After = "100" } // 1.15 lines spacing
            );
            p.AppendChild(pPr);

            if (string.IsNullOrEmpty(line)) return p;

            // Xử lý dòng chứa Tab (các phương án trắc nghiệm A, B, C, D sử dụng Tab Stops chuẩn sư phạm)
            if (line.Contains('\t'))
            {
                var tabParts = line.Split('\t').Select(x => x.Trim()).Where(x => !string.IsNullOrEmpty(x)).ToList();
                if (tabParts.Count >= 2)
                {
                    pPr.Indentation = new Indentation { Left = "283" }; // 0.5 cm
                    if (tabParts.Count == 4)
                    {
                        // 4 phương án trên 1 dòng: Standard35 tại 3.5cm (1985), 7.0cm (3969), 10.5cm (5953) hoặc Wide45 tại 5.0cm (2835), 9.5cm (5386), 14.0cm (7937)
                        pPr.SpacingBetweenLines = new SpacingBetweenLines { Line = "276", LineRule = LineSpacingRuleValues.Auto, Before = "0", After = "160" };
                        pPr.Tabs = options.TabSpacing == TabSpacingMode.Standard35
                            ? new Tabs(
                                new TabStop { Val = TabStopValues.Left, Position = 1985 },
                                new TabStop { Val = TabStopValues.Left, Position = 3969 },
                                new TabStop { Val = TabStopValues.Left, Position = 5953 }
                            )
                            : new Tabs(
                                new TabStop { Val = TabStopValues.Left, Position = 2835 },
                                new TabStop { Val = TabStopValues.Left, Position = 5386 },
                                new TabStop { Val = TabStopValues.Left, Position = 7937 }
                            );
                    }
                    else if (tabParts.Count == 2)
                    {
                        // 2 phương án trên 1 dòng: Standard35 tại 7.0cm (3969) hoặc Wide45 tại 7.5cm (4252)
                        pPr.SpacingBetweenLines = new SpacingBetweenLines { Line = "276", LineRule = LineSpacingRuleValues.Auto, Before = "0", After = "100" };
                        int pos2 = options.TabSpacing == TabSpacingMode.Standard35 ? 3969 : 4252;
                        pPr.Tabs = new Tabs(
                            new TabStop { Val = TabStopValues.Left, Position = pos2 }
                        );
                    }
                    else
                    {
                        pPr.SpacingBetweenLines = new SpacingBetweenLines { Line = "260", LineRule = LineSpacingRuleValues.Auto, Before = "0", After = "100" };
                        var customTabs = new Tabs();
                        int colWidth = 9000 / tabParts.Count;
                        for (int t = 1; t < tabParts.Count; t++)
                        {
                            customTabs.AppendChild(new TabStop { Val = TabStopValues.Left, Position = colWidth * t });
                        }
                        pPr.Tabs = customTabs;
                    }

                    for (int i = 0; i < tabParts.Count; i++)
                    {
                        if (i > 0)
                        {
                            p.AppendChild(new Run(new TabChar()));
                        }

                        string part = tabParts[i];
                        var optMatch = Regex.Match(part, @"^([a-dA-D][\.\)])\s*(.*)$");
                        if (optMatch.Success)
                        {
                            string lbl = optMatch.Groups[1].Value + " ";
                            string val = EnsureDot(optMatch.Groups[2].Value);
                            var lblRun = new Run(
                                new RunProperties(CreateRunFonts(options.FontFamily), new Bold(), new FontSize { Val = options.FontSizePt }),
                                new Text(lbl) { Space = SpaceProcessingModeValues.Preserve });
                            p.AppendChild(lblRun);
                            AppendFormattedRuns(p, val, options);
                        }
                        else
                        {
                            AppendFormattedRuns(p, EnsureDot(part), options);
                        }
                    }

                    return p;
                }
            }

            // 1. Tách phần tiền tố nhãn cần in đậm: CHỈ in đậm đúng phần nhãn, tuyệt đối không in đậm chữ nội dung kế tiếp
            // Nhãn bao gồm: "Câu 1. ", "Lời giải: ", "Hướng dẫn giải: ", "a) Đúng. ", "b) Sai. ", "A. ", "PHẦN I. ", "Bài 1. "
            var prefixRegex = new Regex(
                @"^(%?\s*(?:Câu|Bài|CÂU|BÀI)\s*\d+[:.]?\s*|(?:Lời giải|Hướng dẫn giải|LỜI GIẢI|HƯỚNG DẪN GIẢI)[:.]?\s*|(?:[a-dA-D][\.\)]\s*(?:Đúng\.|Sai\.)?\s*)|(?:PHẦN\s+(?:[I|V|X]+|\d+)[:.]?\s*)|(?:Mệnh đề\s*\d*[:.]?\s*))",
                RegexOptions.IgnoreCase);

            string remainingText = line;
            var match = prefixRegex.Match(line);
            if (match.Success && match.Index == 0)
            {
                string labelText = match.Value;
                remainingText = line.Substring(match.Length);

                // Nếu là phương án đứng riêng 1 dòng thì thụt đầu dòng 0.5cm (283 twips)
                if (Regex.IsMatch(labelText, @"^[a-dA-D][\.\)]\s*"))
                {
                    pPr.Indentation = new Indentation { Left = "283" };
                    pPr.SpacingBetweenLines = new SpacingBetweenLines { Line = "260", LineRule = LineSpacingRuleValues.Auto, Before = "0", After = "40" };
                }

                var labelRunPr = new RunProperties(
                    CreateRunFonts(options.FontFamily),
                    new FontSize { Val = options.FontSizePt },
                    new Bold()
                );
                var labelRun = new Run(labelRunPr, new Text(labelText) { Space = SpaceProcessingModeValues.Preserve });
                p.AppendChild(labelRun);
            }

            // 2. Định dạng phần nội dung còn lại: chữ thường KHÔNG in đậm, chỉ in nghiêng công thức toán ${...}$ hoặc $...$
            if (!string.IsNullOrEmpty(remainingText))
            {
                AppendFormattedRuns(p, remainingText, options);
            }

            return p;
        }

        public static string GenerateHtmlExam(IEnumerable<QuestionItem> questions, ExamExportOptions? options = null)
        {
            options ??= new ExamExportOptions();
            var qList = questions.ToList();
            var sb = new System.Text.StringBuilder();

            string font = options.FontFamily ?? "Times New Roman";
            string subjectUpper = (options.Subject ?? "TOÁN").ToUpper();
            string schoolUpper = string.IsNullOrWhiteSpace(options.SchoolName) ? "SỞ/PHÒNG GD&ĐT" : options.SchoolName.ToUpper();
            string examTitleUpper = string.IsNullOrWhiteSpace(options.ExamTitle) ? "ĐỀ KIỂM TRA" : options.ExamTitle.ToUpper();

            sb.Append($"<div style=\"font-family:'{font}',serif; font-size:12pt; line-height:1.15; color:#000;\">");

            // 1. Header hành chính 2 cột (Border none)
            sb.Append("<table style=\"width:100%; border:none; border-collapse:collapse; margin-bottom:6px;\"><tr>");
            sb.Append($"<td style=\"width:42%; text-align:center; vertical-align:top; border:none; padding:2px;\">");
            sb.Append($"<strong>{schoolUpper}</strong><br><strong>{examTitleUpper}</strong><br>(Đề thi gồm {qList.Count:02d} câu)</td>");
            sb.Append($"<td style=\"width:58%; text-align:center; vertical-align:top; border:none; padding:2px;\">");
            sb.Append($"<strong>ĐỀ THI MÔN {subjectUpper} - LỚP {options.Grade}</strong><br><strong>Môn thi: {subjectUpper}</strong><br>");
            sb.Append($"Thời gian làm bài {options.TimeMinutes}, không kể thời gian phát đề<br>");
            sb.Append($"Lớp: {options.Grade}&nbsp;&nbsp;&nbsp;&nbsp;Năm học: {options.ExamYear}</td>");
            sb.Append("</tr></table>");

            // 2. Dòng thông tin thí sinh
            sb.Append($"<p style=\"margin:4px 0 8px 0; text-align:justify;\">Họ và tên: …………………………………………..&nbsp;&nbsp;&nbsp;&nbsp;Lớp: ………………&nbsp;&nbsp;&nbsp;&nbsp;<strong>Mã đề: {options.ExamCode}</strong></p>");

            // 3. Phân nhóm câu hỏi
            var tnQuestions = qList.Where(q => q.QuestionType == "MultipleChoice4").ToList();
            var dsQuestions = qList.Where(q => q.QuestionType == "TrueFalse4").ToList();
            var tlnQuestions = qList.Where(q => q.QuestionType == "ShortAnswer").ToList();
            var tlQuestions = qList.Where(q => q.QuestionType == "Essay" || (q.QuestionType != "MultipleChoice4" && q.QuestionType != "TrueFalse4" && q.QuestionType != "ShortAnswer")).ToList();

            int globalIndex = 1;

            // ── PHẦN I: Trắc nghiệm 4 lựa chọn ──
            if (tnQuestions.Count > 0)
            {
                sb.Append($"<p style=\"font-weight:bold; margin:10px 0 6px 0;\">PHẦN I. Thí sinh trả lời từ câu 1 đến câu {tnQuestions.Count}. Mỗi câu hỏi thí sinh chỉ chọn một phương án.</p>");

                // Bảng điền đáp án nhanh của học sinh (Table 1)
                sb.Append("<table border=\"1\" cellpadding=\"3\" cellspacing=\"0\" style=\"width:100%; border-collapse:collapse; text-align:center; margin-bottom:12px; font-size:11pt;\">");
                sb.Append("<tr><td style=\"font-weight:bold; width:60px;\">Câu</td>");
                for (int i = 1; i <= tnQuestions.Count; i++) sb.Append($"<td style=\"font-weight:bold;\">{i}</td>");
                sb.Append("</tr><tr><td style=\"font-weight:bold;\">Đáp án</td>");
                for (int i = 1; i <= tnQuestions.Count; i++) sb.Append("<td>&nbsp;</td>");
                sb.Append("</tr></table>");

                foreach (var q in tnQuestions)
                {
                    string cleanContent = CleanImageTagsFromContent(q.Content);
                    sb.Append($"<p style=\"margin:6px 0 3px 0;\"><strong>Câu {globalIndex}.</strong> {cleanContent}</p>");

                    if (q.Options.Count == 4)
                    {
                        int maxLen = q.Options.Values.Select(v => (v ?? "").Length).DefaultIfEmpty(0).Max();
                        if (maxLen <= 35)
                        {
                            // 4 cột
                            sb.Append("<table style=\"width:100%; border:none; border-collapse:collapse; margin-bottom:6px;\"><tr>");
                            foreach (var k in new[] { "A", "B", "C", "D" })
                            {
                                string v = q.Options.ContainsKey(k) ? EnsureDot(q.Options[k]) : "";
                                sb.Append($"<td style=\"width:25%; border:none; padding:2px;\"><strong>{k}.</strong> {v}</td>");
                            }
                            sb.Append("</tr></table>");
                        }
                        else if (maxLen <= 70)
                        {
                            // 2x2
                            sb.Append("<table style=\"width:100%; border:none; border-collapse:collapse; margin-bottom:6px;\">");
                            sb.Append($"<tr><td style=\"width:50%; border:none; padding:2px;\"><strong>A.</strong> {(q.Options.ContainsKey("A") ? EnsureDot(q.Options["A"]) : "")}</td><td style=\"width:50%; border:none; padding:2px;\"><strong>B.</strong> {(q.Options.ContainsKey("B") ? EnsureDot(q.Options["B"]) : "")}</td></tr>");
                            sb.Append($"<tr><td style=\"width:50%; border:none; padding:2px;\"><strong>C.</strong> {(q.Options.ContainsKey("C") ? EnsureDot(q.Options["C"]) : "")}</td><td style=\"width:50%; border:none; padding:2px;\"><strong>D.</strong> {(q.Options.ContainsKey("D") ? EnsureDot(q.Options["D"]) : "")}</td></tr>");
                            sb.Append("</table>");
                        }
                        else
                        {
                            // 1 cột
                            foreach (var k in new[] { "A", "B", "C", "D" })
                            {
                                string v = q.Options.ContainsKey(k) ? EnsureDot(q.Options[k]) : "";
                                sb.Append($"<p style=\"margin:2px 0 2px 18px;\"><strong>{k}.</strong> {v}</p>");
                            }
                        }
                    }

                    globalIndex++;
                }
            }

            // ── PHẦN II: Đúng / Sai ──
            if (dsQuestions.Count > 0)
            {
                int startIdx = globalIndex;
                int endIdx = globalIndex + dsQuestions.Count - 1;
                sb.Append($"<p style=\"font-weight:bold; margin:10px 0 6px 0;\">PHẦN II. Thí sinh trả lời từ câu {startIdx} đến câu {endIdx}. Trong mỗi ý a), b), c), d) ở mỗi câu hỏi, thí sinh chọn đúng hoặc sai.</p>");

                foreach (var q in dsQuestions)
                {
                    string cleanContent = CleanImageTagsFromContent(q.Content);
                    sb.Append($"<p style=\"margin:6px 0 3px 0;\"><strong>Câu {globalIndex}.</strong> {cleanContent}</p>");
                    foreach (var k in new[] { "a", "b", "c", "d" })
                    {
                        if (q.Options.ContainsKey(k))
                        {
                            sb.Append($"<p style=\"margin:2px 0 2px 18px;\"><strong>{k})</strong> {q.Options[k]}</p>");
                        }
                    }
                    globalIndex++;
                }
            }

            // ── PHẦN III: Trả lời ngắn ──
            if (tlnQuestions.Count > 0)
            {
                int startIdx = globalIndex;
                int endIdx = globalIndex + tlnQuestions.Count - 1;
                sb.Append($"<p style=\"font-weight:bold; margin:10px 0 6px 0;\">PHẦN III. Thí sinh trả lời từ câu {startIdx} đến câu {endIdx}.</p>");
                foreach (var q in tlnQuestions)
                {
                    string cleanContent = CleanImageTagsFromContent(q.Content);
                    sb.Append($"<p style=\"margin:6px 0 3px 0;\"><strong>Câu {globalIndex}.</strong> {cleanContent}</p>");
                    globalIndex++;
                }
            }

            // ── PHẦN IV: Tự luận ──
            if (tlQuestions.Count > 0)
            {
                int startIdx = globalIndex;
                int endIdx = globalIndex + tlQuestions.Count - 1;
                sb.Append($"<p style=\"font-weight:bold; margin:10px 0 6px 0;\">PHẦN IV. Tự luận. Thí sinh trình bày lời giải từ câu {startIdx} đến câu {endIdx}.</p>");
                foreach (var q in tlQuestions)
                {
                    string cleanContent = CleanImageTagsFromContent(q.Content);
                    sb.Append($"<p style=\"margin:6px 0 3px 0;\"><strong>Câu {globalIndex}.</strong> {cleanContent}</p>");
                    globalIndex++;
                }
            }

            sb.Append("<p style=\"text-align:center; font-weight:bold; margin:16px 0;\">---------- HẾT ----------</p>");

            if (options.IncludeSolution)
            {
                sb.Append("<p style=\"text-align:center; font-weight:bold; font-size:13pt; margin:14px 0 6px 0;\">ĐÁP ÁN THAM KHẢO</p>");
                if (tnQuestions.Count > 0)
                {
                    sb.Append("<p style=\"font-weight:bold; margin:6px 0 4px 0;\">PHẦN I.</p>");
                    sb.Append("<table border=\"1\" cellpadding=\"3\" cellspacing=\"0\" style=\"width:100%; border-collapse:collapse; text-align:center; margin-bottom:12px; font-size:11pt;\">");
                    sb.Append("<tr><td style=\"font-weight:bold; width:60px;\">Câu</td>");
                    for (int i = 1; i <= tnQuestions.Count; i++) sb.Append($"<td style=\"font-weight:bold;\">{i}</td>");
                    sb.Append("</tr><tr><td style=\"font-weight:bold;\">Đáp án</td>");
                    foreach (var q in tnQuestions) sb.Append($"<td style=\"font-weight:bold;\">{(q.CorrectAnswer ?? string.Empty)}</td>");
                    sb.Append("</tr></table>");
                }
            }

            sb.Append("</div>");
            return sb.ToString();
        }

        private static void ApplyA4PageSettings(Body body, int top = 1134, int bottom = 1134, int left = 1417, int right = 1134)
        {
            var sectionProps = new SectionProperties();

            // Khổ giấy A4: 11906 x 16838 twips (210mm x 297mm)
            var pageSize = new PageSize { Width = 11906, Height = 16838, Orient = PageOrientationValues.Portrait };

            // Lề chuẩn sư phạm (Top 2.0cm, Bottom 2.0cm, Left 2.5cm, Right 2.0cm)
            var pageMargin = new PageMargin
            {
                Top = top,
                Bottom = bottom,
                Left = (uint)left,
                Right = (uint)right,
                Header = 567U,
                Footer = 567U
            };

            sectionProps.AppendChild(pageSize);
            sectionProps.AppendChild(pageMargin);
            body.AppendChild(sectionProps);
        }
    }
}
