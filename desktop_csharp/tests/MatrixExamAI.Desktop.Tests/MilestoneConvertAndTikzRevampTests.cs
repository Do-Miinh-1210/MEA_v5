using System;
using System.Collections.Generic;
using System.IO;
using System.Reflection;
using System.Threading;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Media;
using MatrixExamAI.Desktop.Services;
using MatrixExamAI.Desktop.Views;
using MatrixExamAI.Shared.Extensibility;
using MatrixExamAI.Shared.Tikz;
using Xunit;

namespace MatrixExamAI.Desktop.Tests
{
    public class MilestoneConvertAndTikzRevampTests
    {
        private static T GetControl<T>(FrameworkElement parent, string name) where T : class
        {
            var control = parent.FindName(name) as T;
            if (control != null) return control;

            var field = parent.GetType().GetField(name, BindingFlags.Instance | BindingFlags.NonPublic | BindingFlags.Public);
            var val = field?.GetValue(parent) as T;
            if (val != null) return val;

            throw new InvalidOperationException($"Control '{name}' of type {typeof(T).Name} could not be resolved on {parent.GetType().Name}.");
        }

        [Fact]
        public void ConvertView_FullLatexExport_GeneratesCompilableDocumentWithPreamble()
        {
            string body = @"\begin{ex}
Một vật chuyển động theo quy luật $s(t) = -t^3 + 6t^2$. Tính vận tốc lớn nhất.
\choice
{\True $12$}
{$6$}
{$18$}
{$24$}
\end{ex}";

            string fullDoc = ConvertView.GenerateFullLatexDocument(body, "KỲ THI THỬ THPT", "Toán", "12");

            Assert.Contains(@"\documentclass[12pt,a4paper]{article}", fullDoc);
            Assert.Contains(@"\usepackage[utf8]{vietnam}", fullDoc);
            Assert.Contains(@"\usepackage{amsmath,amssymb,amsfonts}", fullDoc);
            Assert.Contains(@"\usepackage{tikz}", fullDoc);
            Assert.Contains(@"\usepackage{tkz-tab}", fullDoc);
            Assert.Contains(@"\usepackage{ex_test}", fullDoc);
            Assert.Contains(@"\begin{document}", fullDoc);
            Assert.Contains(@"\end{document}", fullDoc);
            Assert.Contains(body, fullDoc);
        }

        [Fact]
        public void TikzShapeGenerators_2D_GeneratesExpectedValidLatex()
        {
            string rightTri = TikzShapeGenerators.GenerateRightTriangle(4, 3, "A", "B", "C");
            Assert.Contains(@"\begin{tikzpicture}", rightTri);
            Assert.Contains(@"(A) at (0,0)", rightTri);
            Assert.Contains(@"(B) at (4,0)", rightTri);
            Assert.Contains(@"(C) at (0,3)", rightTri);
            Assert.Contains(@"\draw (A)--(B)--(C)--cycle", rightTri);

            string equiTri = TikzShapeGenerators.GenerateEquilateralTriangle(6);
            Assert.Contains(@"\begin{tikzpicture}", equiTri);
            Assert.Contains(@"(B) at (6,0)", equiTri);

            string rect = TikzShapeGenerators.GenerateRectangle(5, 3);
            Assert.Contains(@"\coordinate[label=above right:$C$] (C) at (5,3)", rect);

            string circle = TikzShapeGenerators.GenerateCircle(0, 0, 3.5, "O");
            Assert.Contains(@"\draw (O) circle (3.5cm)", circle);

            string oxy = TikzShapeGenerators.GenerateOxyAxis(-3, 3, -2, 4);
            Assert.Contains(@"\draw[->, thick] (-3,0) -- (3,0) node[right]{$x$}", oxy);
        }

        [Fact]
        public void TikzShapeGenerators_3D_GeneratesExpectedValidLatex()
        {
            string pyramid = TikzShapeGenerators.GeneratePyramid(4, 5, "A", "B", "C", "D", "S");
            Assert.Contains(@"x={(1cm,0cm)}, y={(0.4cm,0.3cm)}, z={(0cm,1cm)}", pyramid);
            Assert.Contains(@"\coordinate[label=above:$S$]       (S) at (2,2,5)", pyramid);
            Assert.Contains(@"\draw (S)--(A) (S)--(B) (S)--(C)", pyramid);

            string tetra = TikzShapeGenerators.GenerateTetrahedron(4, 4.5);
            Assert.Contains(@"(S) at (0,0,4.5)", tetra);

            string cuboid = TikzShapeGenerators.GenerateCuboid(4, 3, 5);
            Assert.Contains(@"(A1) at (0,0,5)", cuboid);

            string cyl = TikzShapeGenerators.GenerateCylinder(2.5, 4.5);
            Assert.Contains(@"\draw (0,4.5) ellipse (2.5cm", cyl);

            string cone = TikzShapeGenerators.GenerateCone(3, 5);
            Assert.Contains(@"\coordinate[label=above:$S$] (S) at (0,5)", cone);

            string sphere = TikzShapeGenerators.GenerateSphere(4);
            Assert.Contains(@"\draw (0,0) circle (4cm)", sphere);
            Assert.Contains(@"arc (180:0:4cm", sphere);
            Assert.Contains(@"arc (180:360:4cm", sphere);

            string frustum = TikzShapeGenerators.GenerateConeFrustum(3.0, 1.5, 4.0);
            Assert.Contains(@"\begin{tikzpicture}", frustum);
            Assert.Contains(@"ellipse (1.5cm", frustum);
            Assert.Contains(@"arc (180:0:3cm", frustum);

            string planeSec = TikzShapeGenerators.GenerateSpherePlaneSection(3.0, 1.5);
            Assert.Contains(@"\begin{tikzpicture}", planeSec);
            Assert.Contains(@"circle (3cm)", planeSec);

            string cylSec = TikzShapeGenerators.GenerateCylinderSection(2.5, 4.0, 1.0);
            Assert.Contains(@"\begin{tikzpicture}", cylSec);
            Assert.Contains(@"\draw[blue, thick]", cylSec);
        }

        [Fact]
        public void TikzShapeGenerators_TkzTab_GeneratesExpectedValidTables()
        {
            string cubicTab = TikzShapeGenerators.GenerateCubicTable(1, 0, 2, 4, 0);
            Assert.Contains(@"\tkzTabInit", cubicTab);
            Assert.Contains(@"{$-\infty$, $0$, $2$, $+\infty$}", cubicTab);
            Assert.Contains(@"\tkzTabLine{, +, 0, -, 0, +, }", cubicTab);
            Assert.Contains(@"\tkzTabVar{-/ $-\infty$, +/ $4$, -/ $0$, +/ $+\infty$}", cubicTab);

            string quarticTab = TikzShapeGenerators.GenerateQuarticTable(1, -1, 0, 1, -1, 3, -1);
            Assert.Contains(@"{$-\infty$, $-1$, $0$, $1$, $+\infty$}", quarticTab);

            string rationalTab = TikzShapeGenerators.GenerateRationalTable(1, 2, true);
            Assert.Contains(@"\tkzTabLine{, +, d, +, }", rationalTab);

            string signLin = TikzShapeGenerators.GenerateSignTableLinear(2, true);
            Assert.Contains(@"\tkzTabLine{, -, 0, +, }", signLin);

            string signQuad = TikzShapeGenerators.GenerateSignTableQuadratic(-1, 3, true);
            Assert.Contains(@"\tkzTabLine{, +, 0, -, 0, +, }", signQuad);
        }

        [Fact]
        public void TikzShapeGenerators_Graphs_GeneratesExpectedValidPlots()
        {
            string parabola = TikzShapeGenerators.GenerateParabolaGraph(1, -2, -3);
            Assert.Contains(@"\begin{axis}", parabola);
            Assert.Contains(@"\addplot[blue, very thick, domain=-4:4] {1*x^2 + (-2)*x + (-3)}", parabola);

            string cubic = TikzShapeGenerators.GenerateCubicGraph(1, -3, 0, 2);
            Assert.Contains(@"\addplot[red, very thick, domain=-3:3] {1*x^3 + (-3)*x^2 + (0)*x + (2)}", cubic);
        }

        [Fact]
        public void STA_Thread_TikzShapeBuilderDialog_InitializationAndSwitching()
        {
            Exception? threadEx = null;
            var thread = new Thread(() =>
            {
                try
                {
                    var dlg = new TikzShapeBuilderDialog();
                    var cmbCat = GetControl<ComboBox>(dlg, "CmbCategory");
                    var cmbShape = GetControl<ComboBox>(dlg, "CmbShapeType");
                    var txtCode = GetControl<TextBox>(dlg, "TxtResultCode");

                    Assert.NotNull(cmbCat);
                    Assert.NotNull(cmbShape);
                    Assert.NotNull(txtCode);

                    // Switch to 3D
                    cmbCat.SelectedIndex = 1;
                    Assert.True(cmbShape.Items.Count > 0);
                    Assert.NotEmpty(txtCode.Text);

                    // Switch to TAB
                    cmbCat.SelectedIndex = 2;
                    Assert.True(cmbShape.Items.Count > 0);
                    Assert.Contains(@"\tkzTabInit", txtCode.Text);

                    // Switch to GRAPH
                    cmbCat.SelectedIndex = 3;
                    Assert.True(cmbShape.Items.Count > 0);
                    Assert.Contains(@"\begin{axis}", txtCode.Text);
                }
                catch (Exception ex)
                {
                    threadEx = ex;
                }
            });

            thread.SetApartmentState(ApartmentState.STA);
            thread.Start();
            thread.Join();

            Assert.Null(threadEx);
        }

        [Fact]
        public void STA_Thread_ConvertView_CompactLayout_Validation()
        {
            Exception? threadEx = null;
            var thread = new Thread(() =>
            {
                try
                {
                    var view = new ConvertView();
                    var btnOpen = GetControl<FrameworkElement>(view, "BtnOpenFile");
                    var btnPaste = GetControl<FrameworkElement>(view, "BtnPaste");
                    var btnConvert = GetControl<FrameworkElement>(view, "BtnConvert");
                    var btnExport = GetControl<FrameworkElement>(view, "BtnExportWord");
                    var txtStats = GetControl<TextBlock>(view, "TxtSourceStats");
                    var rbWord = GetControl<RadioButton>(view, "RbTabWordPreview");
                    var rbGrid = GetControl<RadioButton>(view, "RbTabQuestionGrid");
                    var rbRaw = GetControl<RadioButton>(view, "RbTabRawCode");

                    Assert.NotNull(btnOpen);
                    Assert.NotNull(btnPaste);
                    Assert.NotNull(btnConvert);
                    Assert.NotNull(btnExport);
                    Assert.NotNull(txtStats);
                    Assert.NotNull(rbWord);
                    Assert.NotNull(rbGrid);
                    Assert.NotNull(rbRaw);

                    // Check initial source stats
                    Assert.NotEmpty(txtStats.Text);
                    Assert.Contains("từ", txtStats.Text);
                    Assert.Contains("công thức", txtStats.Text);
                }
                catch (Exception ex)
                {
                    threadEx = ex;
                }
            });

            thread.SetApartmentState(ApartmentState.STA);
            thread.Start();
            thread.Join();

            Assert.Null(threadEx);
        }

        [Fact]
        public void STA_Thread_ConvertView_NaturalExamText_RenderQuestions()
        {
            Exception? threadEx = null;
            var thread = new Thread(() =>
            {
                try
                {
                    var view = new ConvertView();
                    var txtInput = GetControl<TextBox>(view, "TxtInput");
                    var btnConvert = GetControl<Button>(view, "BtnConvert");
                    var panelDoc = GetControl<StackPanel>(view, "PanelDocContent");

                    txtInput.Text = @"% ĐỀ THI TẠO NHANH CHUẨN BGD 2025
PHẦN I. Câu trắc nghiệm nhiều phương án lựa chọn. Thí sinh trả lời từ câu 1 đến câu 12. Mỗi câu hỏi thí sinh chỉ chọn một phương án.
Câu 1. Cho hàm số y = f(x) có đạo hàm f'(x) = x(x - 1)^2. Số điểm cực trị của hàm số là:
A. 1.
B. 2.
C. 0.
D. 3.
Lời giải:
Ta có f'(x) đổi dấu khi qua nghiệm đơn x = 0. Vậy hàm số có 1 cực trị. Chọn A.

PHẦN II. Câu trắc nghiệm đúng sai. Thí sinh trả lời từ câu 1 đến câu 4. Trong mỗi ý a), b), c), d) ở mỗi câu, thí sinh chọn đúng hoặc sai.
Câu 1. Cho hàm số y = x^3 - 3x + 2.
a) Tập xác định của hàm số là R.
b) Đạo hàm y' = 3x^2 - 3.
c) Hàm số đồng biến trên khoảng (-1; 1).
d) Giá trị cực đại của hàm số bằng 4.

PHẦN III. Câu trắc nghiệm trả lời ngắn. Thí sinh trả lời từ câu 1 đến câu 6.
Câu 1. Tìm giá trị lớn nhất của hàm số y = -x^2 + 4x + 1.
Đáp án: 5";

                    // Raise click
                    btnConvert.RaiseEvent(new RoutedEventArgs(Button.ClickEvent));

                    // Force measure and arrange
                    view.Measure(new Size(1280, 1024));
                    view.Arrange(new Rect(0, 0, 1280, 1024));

                    var borderA4 = GetControl<Border>(view, "BorderWordA4Page");
                    int count = panelDoc.Children.Count;

                    var childTypes = panelDoc.Children.OfType<UIElement>().Select(c => c.GetType().Name).ToList();
                    string details = string.Join(", ", childTypes);

                    Assert.True(count >= 5, $"Expected >= 5, but got {count}. Types: {details}");
                    Assert.True(borderA4.ActualHeight >= 500, $"BorderWordA4Page ActualHeight is {borderA4.ActualHeight}, should be >= 500");
                }
                catch (Exception ex)
                {
                    threadEx = ex;
                }
            });

            thread.SetApartmentState(ApartmentState.STA);
            thread.Start();
            thread.Join();

            Assert.Null(threadEx);
        }

        [Fact]
        public void STA_Thread_TikzView_InteractiveCanvas_Validation()
        {
            Exception? threadEx = null;
            var thread = new Thread(() =>
            {
                try
                {
                    var view = new TikzView();
                    var canvasContainer = GetControl<Grid>(view, "CanvasDiagramContainer");
                    var scaleTransform = GetControl<ScaleTransform>(view, "ImgScaleTransform");
                    var translateTransform = GetControl<TranslateTransform>(view, "ImgTranslateTransform");
                    var btnShape = GetControl<FrameworkElement>(view, "BtnShapeBuilder");
                    var cmbDpi = GetControl<ComboBox>(view, "CmbDpi");
                    var btnCopyEmf = GetControl<FrameworkElement>(view, "BtnCopyEmf");
                    var btnAutoHeal = GetControl<FrameworkElement>(view, "BtnAiAutoHeal");
                    var btnAiEdit = GetControl<FrameworkElement>(view, "BtnAiEdit");
                    var btnCompile = GetControl<FrameworkElement>(view, "BtnCompile");
                    var btnStopTikzAction = GetControl<FrameworkElement>(view, "BtnStopTikzAction");

                    Assert.NotNull(canvasContainer);
                    Assert.NotNull(scaleTransform);
                    Assert.NotNull(translateTransform);
                    Assert.NotNull(btnShape);
                    Assert.NotNull(cmbDpi);
                    Assert.NotNull(btnCopyEmf);
                    Assert.NotNull(btnAutoHeal);
                    Assert.NotNull(btnAiEdit);
                    Assert.NotNull(btnCompile);
                    Assert.NotNull(btnStopTikzAction);

                    // Verify default zoom
                    Assert.Equal(1.0, scaleTransform.ScaleX);
                    Assert.Equal(1.0, scaleTransform.ScaleY);
                }
                catch (Exception ex)
                {
                    threadEx = ex;
                }
            });

            thread.SetApartmentState(ApartmentState.STA);
            thread.Start();
            thread.Join();

            Assert.Null(threadEx);
        }

        [Fact]
        public void STA_Thread_TikzView_LayoutMode_And_CollapseExpand_Validation()
        {
            Exception? threadEx = null;
            var thread = new Thread(() =>
            {
                try
                {
                    var view = new TikzView();
                    var gridSplit = GetControl<Grid>(view, "GridSplitContainer");
                    var btnCollapse = GetControl<Button>(view, "BtnCollapseCode");
                    var btnExpand = GetControl<Button>(view, "BtnExpandCode");
                    var btnModeSplit = GetControl<Button>(view, "BtnModeSplit");
                    var btnModeImageOnly = GetControl<Button>(view, "BtnModeImageOnly");
                    var btnModeCodeOnly = GetControl<Button>(view, "BtnModeCodeOnly");

                    Assert.NotNull(gridSplit);
                    Assert.NotNull(btnCollapse);
                    Assert.NotNull(btnExpand);
                    Assert.NotNull(btnModeSplit);
                    Assert.NotNull(btnModeImageOnly);
                    Assert.NotNull(btnModeCodeOnly);

                    // Test ImageOnly layout mode (Code collapsed)
                    view.SetLayoutMode(TikzView.TikzLayoutMode.ImageOnly);
                    Assert.Equal(0, gridSplit.ColumnDefinitions[0].Width.Value);
                    Assert.Equal(Visibility.Visible, btnExpand.Visibility);

                    // Test Split layout mode (3:7 ratio restored)
                    view.SetLayoutMode(TikzView.TikzLayoutMode.Split);
                    Assert.True(gridSplit.ColumnDefinitions[0].Width.Value > 0);
                    Assert.True(gridSplit.ColumnDefinitions[2].Width.Value > 0);
                    Assert.Equal(Visibility.Collapsed, btnExpand.Visibility);

                    // Test ToggleCodePanel
                    view.ToggleCodePanel();
                    Assert.Equal(0, gridSplit.ColumnDefinitions[0].Width.Value);
                    Assert.Equal(Visibility.Visible, btnExpand.Visibility);

                    view.ToggleCodePanel();
                    Assert.True(gridSplit.ColumnDefinitions[0].Width.Value > 0);
                    Assert.Equal(Visibility.Collapsed, btnExpand.Visibility);
                }
                catch (Exception ex)
                {
                    threadEx = ex;
                }
            });

            thread.SetApartmentState(ApartmentState.STA);
            thread.Start();
            thread.Join();

            Assert.Null(threadEx);
        }

        [Fact]
        public void STA_Thread_AiDrawPromptDialog_ControlsAndProviderInfo_Validation()
        {
            Exception? threadEx = null;
            var thread = new Thread(() =>
            {
                try
                {
                    var dlg = new AiDrawPromptDialog("Vẽ đồ thị hàm bậc ba y = x^3 - 3x + 1");

                    var txtActiveProvider = GetControl<TextBlock>(dlg, "TxtActiveProvider");
                    var btnChoose = GetControl<FrameworkElement>(dlg, "BtnChooseImage");
                    var btnPaste = GetControl<FrameworkElement>(dlg, "BtnPasteImage");
                    var chkGeo = GetControl<CheckBox>(dlg, "ChkTaskGeo");
                    var chkNotes = GetControl<CheckBox>(dlg, "ChkTaskNotes");
                    var chkGraph = GetControl<CheckBox>(dlg, "ChkTaskGraph");
                    var txtInput = GetControl<TextBox>(dlg, "TxtInputPrompt");
                    var btnClose = GetControl<FrameworkElement>(dlg, "BtnClose");
                    var btnStopAi = GetControl<FrameworkElement>(dlg, "BtnStopAi");
                    var btnAutoDraw = GetControl<FrameworkElement>(dlg, "BtnAutoDraw");
                    var btnDescribe = GetControl<FrameworkElement>(dlg, "BtnDescribeOnly");

                    Assert.NotNull(txtActiveProvider);
                    Assert.NotNull(btnChoose);
                    Assert.NotNull(btnPaste);
                    Assert.NotNull(chkGeo);
                    Assert.NotNull(chkNotes);
                    Assert.NotNull(chkGraph);
                    Assert.NotNull(txtInput);
                    Assert.NotNull(btnClose);
                    Assert.NotNull(btnStopAi);
                    Assert.NotNull(btnAutoDraw);
                    Assert.NotNull(btnDescribe);

                    // Khớp layout hình 2 của bản cũ & có nút dừng
                    Assert.Contains("Provider hiện tại", txtActiveProvider.Text);
                    Assert.True(chkGeo.IsChecked);
                    Assert.True(chkNotes.IsChecked);
                    Assert.Equal("Vẽ đồ thị hàm bậc ba y = x^3 - 3x + 1", txtInput.Text);
                    Assert.Equal(Visibility.Collapsed, btnStopAi.Visibility);
                }
                catch (Exception ex)
                {
                    threadEx = ex;
                }
            });

            thread.SetApartmentState(ApartmentState.STA);
            thread.Start();
            thread.Join();

            Assert.Null(threadEx);
        }

        [Fact]
        public void TikzImagePreviewWindow_InitializesCorrectly_OnStaThread()
        {
            Exception? threadEx = null;

            var thread = new Thread(() =>
            {
                try
                {
                    var window = new TikzImagePreviewWindow(null, "dummy.png", 600, "Xem hình vẽ TikZ chi tiết (600 DPI)");
                    var txtTitle = GetControl<TextBlock>(window, "TxtTitleInfo");
                    var btnZoomIn = GetControl<FrameworkElement>(window, "BtnZoomIn");
                    var btnZoomOut = GetControl<FrameworkElement>(window, "BtnZoomOut");
                    var btnZoomFit = GetControl<FrameworkElement>(window, "BtnZoomFit");
                    var btnCopy = GetControl<FrameworkElement>(window, "BtnCopyImage");
                    var btnSave = GetControl<FrameworkElement>(window, "BtnSaveImage");
                    var btnClose = GetControl<FrameworkElement>(window, "BtnClose");
                    var img = GetControl<Image>(window, "ImgFullPreview");

                    Assert.NotNull(txtTitle);
                    Assert.NotNull(btnZoomIn);
                    Assert.NotNull(btnZoomOut);
                    Assert.NotNull(btnZoomFit);
                    Assert.NotNull(btnCopy);
                    Assert.NotNull(btnSave);
                    Assert.NotNull(btnClose);
                    Assert.NotNull(img);
                    Assert.Equal("Xem hình vẽ TikZ chi tiết (600 DPI)", txtTitle.Text);
                }
                catch (Exception ex)
                {
                    threadEx = ex;
                }
            });

            thread.SetApartmentState(ApartmentState.STA);
            thread.Start();
            thread.Join();

            Assert.Null(threadEx);
        }

        [Fact]
        public void TikzView_HasPopoutViewerAndNewImagePulseAnimation_OnStaThread()
        {
            Exception? threadEx = null;

            var thread = new Thread(() =>
            {
                try
                {
                    var view = new TikzView();
                    var btnViewer = GetControl<FrameworkElement>(view, "BtnOpenViewerWindow");
                    var borderWrapper = GetControl<Border>(view, "BorderDiagramWrapper");
                    var imgPreview = GetControl<Image>(view, "ImgDiagramPreview");
                    var txtStats = GetControl<TextBlock>(view, "TxtDiagramStats");

                    Assert.NotNull(btnViewer);
                    Assert.NotNull(borderWrapper);
                    Assert.NotNull(imgPreview);
                    Assert.NotNull(txtStats);

                    // Kiểm tra tooltip hướng dẫn công thái học
                    Assert.NotNull(borderWrapper.ToolTip);
                    Assert.Contains("Nhấp đúp chuột", borderWrapper.ToolTip.ToString());

                    // Kiểm tra phương thức PlayNewImageInsertAnimation tồn tại và an toàn khi gọi
                    var animMethod = typeof(TikzView).GetMethod("PlayNewImageInsertAnimation", BindingFlags.Instance | BindingFlags.NonPublic);
                    Assert.NotNull(animMethod);
                    animMethod.Invoke(view, null);

                    // Kiểm tra 2 nút Lưu kho và Kho hình
                    var btnSaveBank = GetControl<FrameworkElement>(view, "BtnSaveFigureBank");
                    var btnOpenBank = GetControl<FrameworkElement>(view, "BtnOpenFigureBank");
                    Assert.NotNull(btnSaveBank);
                    Assert.NotNull(btnOpenBank);
                    Assert.Contains("Ctrl+Shift+S", btnSaveBank.ToolTip.ToString());
                    Assert.Contains("Ctrl+B", btnOpenBank.ToolTip.ToString());
                }
                catch (Exception ex)
                {
                    threadEx = ex;
                }
            });

            thread.SetApartmentState(ApartmentState.STA);
            thread.Start();
            thread.Join();

            Assert.Null(threadEx);
        }

        [Fact]
        public void FigureBankService_CanSaveListAndDeleteFigures()
        {
            string tempDir = Path.Combine(Path.GetTempPath(), "MEA_FigureBank_Test_" + Guid.NewGuid().ToString("N"));
            Directory.CreateDirectory(tempDir);

            try
            {
                FigureBankService.SetCustomDirectory(tempDir);

                // 1. Lưu hình 1
                string tikz1 = @"\begin{tikzpicture}\draw (0,0) rectangle (2,2);\end{tikzpicture}";
                var fig1 = FigureBankService.SaveFigure(
                    tikzCode: tikz1,
                    title: "Hình chữ nhật 2x2",
                    description: "Hình vẽ mẫu test",
                    tags: new List<string> { "2D", "hinh_hoc" },
                    source: "manual"
                );

                Assert.NotNull(fig1);
                Assert.Equal("001", fig1.Id);
                Assert.Equal("Hình chữ nhật 2x2", fig1.Title);
                Assert.True(File.Exists(Path.Combine(tempDir, "figure_001.tex")));

                // 2. Lưu hình 2 kèm byte ảnh PNG
                string tikz2 = @"\begin{tikzpicture}\draw (0,0) circle (1cm);\end{tikzpicture}";
                byte[] mockPng = new byte[] { 0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A };
                var fig2 = FigureBankService.SaveFigure(
                    tikzCode: tikz2,
                    title: "Hình tròn R=1",
                    description: "Hình tròn cơ bản",
                    tags: new List<string> { "2D", "tron" },
                    source: "ai",
                    pngBytes: mockPng
                );

                Assert.NotNull(fig2);
                Assert.Equal("002", fig2.Id);
                Assert.True(fig2.HasPng);
                Assert.True(File.Exists(Path.Combine(tempDir, "figure_002.png")));

                // 3. Danh sách hình
                var allFigs = FigureBankService.ListFigures();
                Assert.Equal(2, allFigs.Count);

                // Tìm kiếm theo từ khóa
                var searchResult = FigureBankService.ListFigures("chữ nhật");
                Assert.Single(searchResult);
                Assert.Equal("001", searchResult[0].Id);

                // Lọc theo nguồn
                var aiFigs = FigureBankService.ListFigures("", "ai");
                Assert.Single(aiFigs);
                Assert.Equal("002", aiFigs[0].Id);

                // Đọc lại mã TikZ
                string readCode = FigureBankService.GetTikzCode(fig1);
                Assert.Equal(tikz1, readCode);

                // 4. Xóa hình
                bool deleted = FigureBankService.DeleteFigure("001");
                Assert.True(deleted);
                Assert.False(File.Exists(Path.Combine(tempDir, "figure_001.tex")));

                var remaining = FigureBankService.ListFigures();
                Assert.Single(remaining);
                Assert.Equal("002", remaining[0].Id);
            }
            finally
            {
                FigureBankService.SetCustomDirectory(null);
                if (Directory.Exists(tempDir))
                {
                    try { Directory.Delete(tempDir, true); } catch { }
                }
            }
        }

        [Fact]
        public void SaveFigureDialog_InitializesCorrectly_OnStaThread()
        {
            Exception? threadEx = null;

            var thread = new Thread(() =>
            {
                try
                {
                    var dlg = new SaveFigureDialog("Hình kiểm tra", "3D, chóp", true);
                    Assert.NotNull(dlg);
                    var txtTitle = GetControl<Wpf.Ui.Controls.TextBox>(dlg, "TxtTitle");
                    var txtTags = GetControl<Wpf.Ui.Controls.TextBox>(dlg, "TxtTags");
                    var chkPng = GetControl<CheckBox>(dlg, "ChkSavePng");

                    Assert.Equal("Hình kiểm tra", txtTitle.Text);
                    Assert.Equal("3D, chóp", txtTags.Text);
                    Assert.True(chkPng.IsChecked);
                }
                catch (Exception ex)
                {
                    threadEx = ex;
                }
            });

            thread.SetApartmentState(ApartmentState.STA);
            thread.Start();
            thread.Join();

            Assert.Null(threadEx);
        }

        [Fact]
        public void FigureBankDialog_InitializesCorrectly_OnStaThread()
        {
            Exception? threadEx = null;

            var thread = new Thread(() =>
            {
                try
                {
                    var dlg = new FigureBankDialog();
                    Assert.NotNull(dlg);
                    var grid = GetControl<DataGrid>(dlg, "GridFigures");
                    var txtSearch = GetControl<Wpf.Ui.Controls.TextBox>(dlg, "TxtSearchQuery");
                    var cmbSource = GetControl<ComboBox>(dlg, "CmbSourceFilter");
                    var btnLoad = GetControl<FrameworkElement>(dlg, "BtnLoadFigure");
                    var btnCopy = GetControl<FrameworkElement>(dlg, "BtnCopyCode");
                    var btnDelete = GetControl<FrameworkElement>(dlg, "BtnDeleteFigure");

                    Assert.NotNull(grid);
                    Assert.NotNull(txtSearch);
                    Assert.NotNull(cmbSource);
                    Assert.NotNull(btnLoad);
                    Assert.NotNull(btnCopy);
                    Assert.NotNull(btnDelete);

                    var listCards = GetControl<ListBox>(dlg, "ListCardsFigures");
                    var rbCards = GetControl<RadioButton>(dlg, "RbViewCards");
                    var rbList = GetControl<RadioButton>(dlg, "RbViewList");
                    var btnUpdate = GetControl<FrameworkElement>(dlg, "BtnUpdateCode");

                    Assert.NotNull(listCards);
                    Assert.NotNull(rbCards);
                    Assert.NotNull(rbList);
                    Assert.NotNull(btnUpdate);
                    Assert.True(rbCards.IsChecked);
                }
                catch (Exception ex)
                {
                    threadEx = ex;
                }
            });

            thread.SetApartmentState(ApartmentState.STA);
            thread.Start();
            thread.Join();

            Assert.Null(threadEx);
        }

        [Fact]
        public void FigureBankService_CanUpdateAndOverwriteFigure()
        {
            string tempDir = Path.Combine(Path.GetTempPath(), "MEA_FigureBank_UpdateTest_" + Guid.NewGuid().ToString("N"));
            Directory.CreateDirectory(tempDir);

            try
            {
                FigureBankService.SetCustomDirectory(tempDir);

                string originalTikz = @"\begin{tikzpicture}\draw (0,0) -- (1,1);\end{tikzpicture}";
                var fig = FigureBankService.SaveFigure(
                    tikzCode: originalTikz,
                    title: "Hình gốc",
                    description: "Mô tả gốc",
                    tags: new List<string> { "2D" }
                );

                Assert.Equal("001", fig.Id);
                Assert.Equal("Hình gốc", fig.Title);
                Assert.Equal(originalTikz, FigureBankService.GetTikzCode(fig));

                // Cập nhật mã và tiêu đề mới (Lưu đè)
                string updatedTikz = @"\begin{tikzpicture}\draw[thick, red] (0,0) rectangle (3,3);\end{tikzpicture}";
                byte[] mockPng = new byte[] { 0x89, 0x50, 0x4E, 0x47, 0x01, 0x02 };
                bool success = FigureBankService.UpdateFigure(
                    id: "001",
                    newCode: updatedTikz,
                    newTitle: "Hình chữ nhật đỏ (Đã cập nhật)",
                    pngBytes: mockPng
                );

                Assert.True(success);

                var allFigs = FigureBankService.ListFigures();
                Assert.Single(allFigs);
                var updatedEntry = allFigs[0];

                Assert.Equal("001", updatedEntry.Id);
                Assert.Equal("Hình chữ nhật đỏ (Đã cập nhật)", updatedEntry.Title);
                Assert.Equal(updatedTikz.Length, updatedEntry.CharCount);
                Assert.True(updatedEntry.HasPng);
                Assert.Equal(updatedTikz, FigureBankService.GetTikzCode(updatedEntry));
            }
            finally
            {
                FigureBankService.SetCustomDirectory(null);
                if (Directory.Exists(tempDir))
                {
                    try { Directory.Delete(tempDir, true); } catch { }
                }
            }
        }

        [Fact]
        public void ConvertView_WordPreviewControls_InitializeCorrectly_OnStaThread()
        {
            Exception? threadEx = null;

            var thread = new Thread(() =>
            {
                try
                {
                    var view = new ConvertView();
                    Assert.NotNull(view);

                    var btnOpenWord = GetControl<FrameworkElement>(view, "BtnOpenInWord");
                    var cmbFont = GetControl<ComboBox>(view, "CmbWordFontSize");
                    var cmbSpacing = GetControl<ComboBox>(view, "CmbWordLineSpacing");
                    var cmbChoice = GetControl<ComboBox>(view, "CmbWordChoiceLayout");
                    var chkSol = GetControl<CheckBox>(view, "ChkWordShowSolutions");
                    var chkAns = GetControl<CheckBox>(view, "ChkWordShowAnswerSheet");

                    Assert.NotNull(btnOpenWord);
                    Assert.NotNull(cmbFont);
                    Assert.NotNull(cmbSpacing);
                    Assert.NotNull(cmbChoice);
                    Assert.NotNull(chkSol);
                    Assert.NotNull(chkAns);

                    // Check default values
                    Assert.Equal(1, cmbFont.SelectedIndex); // 12 pt
                    Assert.Equal(1, cmbSpacing.SelectedIndex); // 1.15
                    Assert.Equal(0, cmbChoice.SelectedIndex); // Tự động
                    Assert.True(chkSol.IsChecked);
                    Assert.True(chkAns.IsChecked);
                }
                catch (Exception ex)
                {
                    threadEx = ex;
                }
            });

            thread.SetApartmentState(ApartmentState.STA);
            thread.Start();
            thread.Join();

            Assert.Null(threadEx);
        }

        [Fact]
        public void ConvertView_ToggleLayout_STA_Test()
        {
            Exception? threadEx = null;
            var thread = new Thread(() =>
            {
                try
                {
                    var view = new ConvertView();
                    Assert.NotNull(view);

                    var cardSource = GetControl<FrameworkElement>(view, "CardSource");
                    var cardPreview = GetControl<FrameworkElement>(view, "CardPreview");
                    var btnExpand = GetControl<FrameworkElement>(view, "BtnExpandSource");

                    // Initial state is Split
                    Assert.Equal(Visibility.Visible, cardSource.Visibility);
                    Assert.Equal(Visibility.Visible, cardPreview.Visibility);
                    Assert.Equal(Visibility.Collapsed, btnExpand.Visibility);

                    // Collapse source (PreviewOnly)
                    view.SetLayoutMode(ConvertView.ConvertLayoutMode.PreviewOnly);
                    Assert.Equal(Visibility.Collapsed, cardSource.Visibility);
                    Assert.Equal(Visibility.Visible, cardPreview.Visibility);
                    Assert.Equal(Visibility.Visible, btnExpand.Visibility);

                    // Toggle back to Split
                    view.ToggleSourcePanel();
                    Assert.Equal(Visibility.Visible, cardSource.Visibility);
                    Assert.Equal(Visibility.Visible, cardPreview.Visibility);
                    Assert.Equal(Visibility.Collapsed, btnExpand.Visibility);

                    // SourceOnly
                    view.SetLayoutMode(ConvertView.ConvertLayoutMode.SourceOnly);
                    Assert.Equal(Visibility.Visible, cardSource.Visibility);
                    Assert.Equal(Visibility.Collapsed, cardPreview.Visibility);
                }
                catch (Exception ex)
                {
                    threadEx = ex;
                }
            });

            thread.SetApartmentState(ApartmentState.STA);
            thread.Start();
            thread.Join();

            Assert.Null(threadEx);
        }

        [Fact]
        public void WordExportService_SupportsDynamicFontSizeAndSpacingOptions()
        {
            string tempDocx = Path.Combine(Path.GetTempPath(), $"test_word_export_{Guid.NewGuid():N}.docx");
            try
            {
                var service = new WordExportService();
                var questions = new List<QuestionItem>
                {
                    new QuestionItem
                    {
                        Id = 1,
                        QuestionCode = "Q1",
                        Content = "Tính giới hạn ${L = \\lim_{x \\to 0} \\frac{\\sin x}{x}}$:",
                        Options = new Dictionary<string, string>
                        {
                            { "A", "${1}$" },
                            { "B", "${0}$" },
                            { "C", "${\\infty}$" },
                            { "D", "Không tồn tại" }
                        },
                        CorrectAnswer = "A",
                        Explanation = "Theo giới hạn cơ bản, $\\lim_{x \\to 0} \\frac{\\sin x}{x} = 1$."
                    }
                };

                var options = new ExamExportOptions
                {
                    Subject = "Toán",
                    Grade = "12",
                    FontSizePt = "22", // 11pt
                    IncludeSolution = true
                };

                service.ExportExamToDocx(tempDocx, questions, options);
                Assert.True(File.Exists(tempDocx));
                var fileInfo = new FileInfo(tempDocx);
                Assert.True(fileInfo.Length > 0);
            }
            finally
            {
                if (File.Exists(tempDocx))
                {
                    try { File.Delete(tempDocx); } catch { }
                }
            }
        }

        [Fact]
        public void STA_Thread_BusinessDialogs_InitializeCorrectly()
        {
            Exception? threadEx = null;
            var thread = new Thread(() =>
            {
                try
                {
                    var quickGen = new QuickGenDialog();
                    Assert.NotNull(quickGen);
                    Assert.Equal("Toán", quickGen.Subject);
                    Assert.Equal("12", quickGen.Grade);

                    var aiMatrix = new AiMatrixDialog();
                    Assert.NotNull(aiMatrix);
                    Assert.Equal("Toán", aiMatrix.Subject);
                    Assert.Equal("12", aiMatrix.Grade);

                    var sourceMethod = new SourceMethodDialog();
                    Assert.NotNull(sourceMethod);
                    Assert.Equal("ai_only", sourceMethod.SelectedMode);

                    var quickGuide = new QuickGuideDialog();
                    Assert.NotNull(quickGuide);
                }
                catch (Exception ex)
                {
                    threadEx = ex;
                }
            });
            thread.SetApartmentState(ApartmentState.STA);
            thread.Start();
            thread.Join();

            Assert.Null(threadEx);
        }

        [Fact]
        public void PromptCatalog_WithTronXoay_ContainsRevolutionInstructions()
        {
            string prompt = MatrixExamAI.Shared.AI.PromptCatalog.GetDrawPrompt("Vẽ hình nón", MatrixExamAI.Shared.Models.DiagramType.TronXoay);
            Assert.Contains("Khối tròn xoay 3D", prompt);
            Assert.Contains("KHỐI NÓN TRÒN XOAY", prompt);
            Assert.Contains("KHỐI TRỤ TRÒN XOAY", prompt);
            Assert.Contains("KHỐI CẦU VÀ MẶT CẦU", prompt);
            Assert.Contains("KHỐI NÓN CỤT", prompt);
        }
    }
}

