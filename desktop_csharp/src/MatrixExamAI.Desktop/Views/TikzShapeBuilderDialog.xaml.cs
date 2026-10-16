using System;
using System.Globalization;
using System.Text;
using System.Windows;
using System.Windows.Controls;

namespace MatrixExamAI.Desktop.Views
{
    public partial class TikzShapeBuilderDialog : Window
    {
        public string GeneratedTikzCode { get; private set; } = string.Empty;
        private string _currentShapeTag = "tri_right";
        private bool _isInitializing = true;

        public TikzShapeBuilderDialog()
        {
            InitializeComponent();
            if (CmbCategory != null) CmbCategory.SelectedIndex = 0;
            Loaded += (s, e) =>
            {
                _isInitializing = false;
                SelectInitialShape("tri_right");
            };
        }

        private void CmbCategory_SelectionChanged(object sender, SelectionChangedEventArgs e)
        {
            if (CmbCategory == null || CmbShapeType == null || TxtResultCode == null) return;
            CmbShapeType.Items.Clear();

            switch (CmbCategory.SelectedIndex)
            {
                case 0: // 2D
                    CmbShapeType.Items.Add("Tam giác vuông");
                    CmbShapeType.Items.Add("Tam giác đều");
                    CmbShapeType.Items.Add("Hình vuông");
                    CmbShapeType.Items.Add("Đường tròn");
                    CmbShapeType.SelectedIndex = 0;
                    TxtResultCode.Text = GenerateTikzCodeForShape("tri_right", "4", "3", "", "A,B,C", true);
                    break;
                case 1: // 3D
                    CmbShapeType.Items.Add("Hình chóp S.ABCD");
                    CmbShapeType.Items.Add("Hình chóp tam giác");
                    CmbShapeType.Items.Add("Hình hộp chữ nhật");
                    CmbShapeType.SelectedIndex = 0;
                    TxtResultCode.Text = GenerateTikzCodeForShape("pyramid", "5", "4", "4", "S,A,B,C,D", true);
                    break;
                case 2: // TAB
                    CmbShapeType.Items.Add("Bảng biến thiên bậc 3");
                    CmbShapeType.Items.Add("Bảng xét dấu");
                    CmbShapeType.SelectedIndex = 0;
                    TxtResultCode.Text = @"\begin{tikzpicture}
\tkzTabInit[lgt=1.5,espcl=2.5]{$x$/1,$y'$/1,$y$/2}{$-\infty$,$1$,$3$,$+\infty$}
\tkzTabLine{,+,$0$,-,$0$,+,}
\tkzTabVar{-/$-\infty$,+/$4$,-/$-2$,+/$+\infty$}
\end{tikzpicture}";
                    break;
                case 3: // GRAPH
                    CmbShapeType.Items.Add("Đồ thị hàm bậc 2");
                    CmbShapeType.Items.Add("Đồ thị hàm bậc 3");
                    CmbShapeType.SelectedIndex = 0;
                    TxtResultCode.Text = @"\begin{tikzpicture}
\begin{axis}[
    axis lines = center,
    xlabel = $x$,
    ylabel = {$f(x)$},
    xmin=-3, xmax=3, ymin=-2, ymax=6
]
\addplot [domain=-2.5:2.5, samples=100, color=blue, thick] {x^2 - 1};
\end{axis}
\end{tikzpicture}";
                    break;
                default:
                    CmbShapeType.Items.Add("Biểu đồ cột");
                    CmbShapeType.SelectedIndex = 0;
                    TxtResultCode.Text = GenerateTikzCodeForShape("chart_bar", "3", "", "", "", false);
                    break;
            }
        }

        private void CmbShapeType_SelectionChanged(object sender, SelectionChangedEventArgs e)
        {
        }

        private void SelectInitialShape(string tag)
        {
            _currentShapeTag = tag;
            UpdateParameterLabels(tag);
            RegenerateCode();
        }

        private void TreeShapeCategories_SelectedItemChanged(object sender, RoutedPropertyChangedEventArgs<object> e)
        {
            if (_isInitializing) return;
            if (e.NewValue is TreeViewItem item && item.Tag is string tag)
            {
                _currentShapeTag = tag;
                UpdateParameterLabels(tag);
                RegenerateCode();
            }
        }

        private void UpdateParameterLabels(string shapeTag)
        {
            if (GridParam1 == null || GridParam2 == null || GridParam3 == null || GridParam4 == null) return;

            GridParam1.Visibility = Visibility.Visible;
            GridParam2.Visibility = Visibility.Visible;
            GridParam3.Visibility = Visibility.Visible;
            GridParam4.Visibility = Visibility.Visible;
            ChkOption.Visibility = Visibility.Visible;

            switch (shapeTag)
            {
                case "tri_general":
                    LblParam1.Text = "Cạnh đáy a:"; TxtParam1.Text = "5";
                    LblParam2.Text = "Cạnh bên b:"; TxtParam2.Text = "4";
                    LblParam3.Text = "Chiều cao h:"; TxtParam3.Text = "3.5";
                    LblParam4.Text = "Đỉnh (A,B,C):"; TxtParam4.Text = "A,B,C";
                    ChkOption.Content = "Hiển thị đường cao AH";
                    break;

                case "tri_right":
                    LblParam1.Text = "Cạnh góc vuông a:"; TxtParam1.Text = "4";
                    LblParam2.Text = "Cạnh góc vuông b:"; TxtParam2.Text = "3";
                    GridParam3.Visibility = Visibility.Collapsed;
                    LblParam4.Text = "Đỉnh (A,B,C):"; TxtParam4.Text = "A,B,C";
                    ChkOption.Content = "Ký hiệu góc vuông";
                    break;

                case "tri_equi":
                case "tri_iso":
                    LblParam1.Text = "Cạnh đáy a:"; TxtParam1.Text = "4";
                    LblParam2.Text = "Chiều cao h:"; TxtParam2.Text = "3.5";
                    GridParam3.Visibility = Visibility.Collapsed;
                    LblParam4.Text = "Đỉnh (A,B,C):"; TxtParam4.Text = "A,B,C";
                    ChkOption.Content = "Hiển thị đường cao";
                    break;

                case "square":
                case "rect":
                    LblParam1.Text = "Chiều dài a:"; TxtParam1.Text = "5";
                    LblParam2.Text = "Chiều rộng b:"; TxtParam2.Text = "3";
                    GridParam3.Visibility = Visibility.Collapsed;
                    LblParam4.Text = "Đỉnh (A,B,C,D):"; TxtParam4.Text = "A,B,C,D";
                    ChkOption.Content = "Hiển thị đường chéo";
                    break;

                case "parallelogram":
                    LblParam1.Text = "Chiều dài đáy a:"; TxtParam1.Text = "5";
                    LblParam2.Text = "Chiều cao h:"; TxtParam2.Text = "3";
                    LblParam3.Text = "Độ nghiêng (skew):"; TxtParam3.Text = "1.5";
                    LblParam4.Text = "Đỉnh (A,B,C,D):"; TxtParam4.Text = "A,B,C,D";
                    ChkOption.Visibility = Visibility.Collapsed;
                    break;

                case "trapezoid":
                    LblParam1.Text = "Đáy lớn a:"; TxtParam1.Text = "6";
                    LblParam2.Text = "Đáy nhỏ b:"; TxtParam2.Text = "3";
                    LblParam3.Text = "Chiều cao h:"; TxtParam3.Text = "3";
                    LblParam4.Text = "Đỉnh (A,B,C,D):"; TxtParam4.Text = "A,B,C,D";
                    ChkOption.Content = "Hình thang cân";
                    break;

                case "circle":
                    LblParam1.Text = "Bán kính R (cm):"; TxtParam1.Text = "2.5";
                    GridParam2.Visibility = Visibility.Collapsed;
                    GridParam3.Visibility = Visibility.Collapsed;
                    LblParam4.Text = "Tên tâm:"; TxtParam4.Text = "O";
                    ChkOption.Content = "Vẽ bán kính OA và tiếp tuyến";
                    break;

                case "ellipse":
                    LblParam1.Text = "Bán trục lớn a:"; TxtParam1.Text = "3";
                    LblParam2.Text = "Bán trục nhỏ b:"; TxtParam2.Text = "1.8";
                    GridParam3.Visibility = Visibility.Collapsed;
                    LblParam4.Text = "Tên tâm:"; TxtParam4.Text = "O";
                    ChkOption.Content = "Hiển thị hệ trục tọa độ";
                    break;

                case "segment":
                    LblParam1.Text = "Độ dài đoạn (cm):"; TxtParam1.Text = "5";
                    GridParam2.Visibility = Visibility.Collapsed;
                    GridParam3.Visibility = Visibility.Collapsed;
                    LblParam4.Text = "Hai đầu mút:"; TxtParam4.Text = "A,B";
                    ChkOption.Content = "Có mũi tên hướng dẫn";
                    break;

                // 3D
                case "pyramid":
                    LblParam1.Text = "Cạnh đáy a:"; TxtParam1.Text = "4";
                    LblParam2.Text = "Chiều cao SO:"; TxtParam2.Text = "4.5";
                    GridParam3.Visibility = Visibility.Collapsed;
                    LblParam4.Text = "Đỉnh chóp & Đáy:"; TxtParam4.Text = "S, A, B, C, D";
                    ChkOption.Content = "Đáy hình vuông đều";
                    break;

                case "pyramid_sa_quad":
                    LblParam1.Text = "Cạnh đáy a:"; TxtParam1.Text = "3.5";
                    LblParam2.Text = "Chiều cao SA:"; TxtParam2.Text = "3.5";
                    GridParam3.Visibility = Visibility.Collapsed;
                    LblParam4.Text = "Đỉnh chóp & Đáy:"; TxtParam4.Text = "S, A, B, C, D";
                    ChkOption.Content = "Ký hiệu vuông góc tại A";
                    break;

                case "pyramid_regular_quad":
                    LblParam1.Text = "Cạnh đáy a:"; TxtParam1.Text = "3.5";
                    LblParam2.Text = "Chiều cao SH:"; TxtParam2.Text = "4";
                    GridParam3.Visibility = Visibility.Collapsed;
                    LblParam4.Text = "Đỉnh & Tâm đáy:"; TxtParam4.Text = "S, A, B, C, D, H";
                    ChkOption.Content = "Hiển thị đường cao SH";
                    break;

                case "pyramid_tri":
                    LblParam1.Text = "Cạnh đáy a:"; TxtParam1.Text = "3.5";
                    LblParam2.Text = "Chiều cao h:"; TxtParam2.Text = "3.5";
                    GridParam3.Visibility = Visibility.Collapsed;
                    LblParam4.Text = "Đỉnh & Đáy:"; TxtParam4.Text = "S, A, B, C";
                    ChkOption.Content = "Nét đứt cạnh khuất chuẩn Cabinet";
                    break;

                case "pyramid_sa_perp":
                    LblParam1.Text = "Cạnh đáy a:"; TxtParam1.Text = "3.5";
                    LblParam2.Text = "Chiều cao SA:"; TxtParam2.Text = "3.5";
                    GridParam3.Visibility = Visibility.Collapsed;
                    LblParam4.Text = "Đỉnh & Đáy:"; TxtParam4.Text = "S, A, B, C";
                    ChkOption.Content = "Ký hiệu góc vuông SA ⟂ đáy";
                    break;

                case "pyramid_regular_tri":
                    LblParam1.Text = "Cạnh đáy a:"; TxtParam1.Text = "3.5";
                    LblParam2.Text = "Chiều cao SH:"; TxtParam2.Text = "3.5";
                    GridParam3.Visibility = Visibility.Collapsed;
                    LblParam4.Text = "Đỉnh & Trọng tâm:"; TxtParam4.Text = "S, A, B, C, H";
                    ChkOption.Content = "Đánh dấu trọng tâm H";
                    break;

                case "tetrahedron":
                    LblParam1.Text = "Cạnh tứ diện a:"; TxtParam1.Text = "3.5";
                    LblParam2.Text = "Chiều cao h:"; TxtParam2.Text = "3.5";
                    GridParam3.Visibility = Visibility.Collapsed;
                    LblParam4.Text = "Đỉnh & Đáy:"; TxtParam4.Text = "A, B, C, D";
                    ChkOption.Content = "Tứ diện đều (6 cạnh bằng)";
                    break;

                case "pyramid_frustum":
                    LblParam1.Text = "Đáy lớn a:"; TxtParam1.Text = "3.5";
                    LblParam2.Text = "Đáy nhỏ a':"; TxtParam2.Text = "1.8";
                    LblParam3.Text = "Chiều cao h:"; TxtParam3.Text = "2.8";
                    LblParam4.Text = "Hai đáy:"; TxtParam4.Text = "A,B,C,D,A',B',C',D'";
                    ChkOption.Visibility = Visibility.Collapsed;
                    break;

                case "cube":
                    LblParam1.Text = "Cạnh lập phương a:"; TxtParam1.Text = "3";
                    GridParam2.Visibility = Visibility.Collapsed;
                    GridParam3.Visibility = Visibility.Collapsed;
                    LblParam4.Text = "Đỉnh hai đáy:"; TxtParam4.Text = "A,B,C,D,A',B',C',D'";
                    ChkOption.Content = "Vẽ đường chéo AC'";
                    break;

                case "cube_diagonal":
                    LblParam1.Text = "Cạnh lập phương a:"; TxtParam1.Text = "3";
                    GridParam2.Visibility = Visibility.Collapsed;
                    GridParam3.Visibility = Visibility.Collapsed;
                    LblParam4.Text = "Đường chéo:"; TxtParam4.Text = "A, C'";
                    ChkOption.Content = "Gắn nhãn độ dài a√3";
                    break;

                case "cuboid":
                    LblParam1.Text = "Dài a:"; TxtParam1.Text = "4";
                    LblParam2.Text = "Rộng b:"; TxtParam2.Text = "3";
                    LblParam3.Text = "Cao h:"; TxtParam3.Text = "3.5";
                    LblParam4.Text = "Đỉnh đáy:"; TxtParam4.Text = "A, B, C, D";
                    ChkOption.Content = "Hiển thị kích thước a, b, c";
                    break;

                case "prism_triangular":
                    LblParam1.Text = "Cạnh đáy a:"; TxtParam1.Text = "3.5";
                    LblParam2.Text = "Chiều cao h:"; TxtParam2.Text = "3.5";
                    GridParam3.Visibility = Visibility.Collapsed;
                    LblParam4.Text = "Đỉnh hai đáy:"; TxtParam4.Text = "A,B,C,A',B',C'";
                    ChkOption.Content = "Đánh dấu cạnh bên ⟂ đáy";
                    break;

                case "cylinder":
                    LblParam1.Text = "Bán kính đáy R:"; TxtParam1.Text = "2";
                    LblParam2.Text = "Chiều cao h:"; TxtParam2.Text = "3.5";
                    GridParam3.Visibility = Visibility.Collapsed;
                    LblParam4.Text = "Hai tâm:"; TxtParam4.Text = "O, O'";
                    ChkOption.Content = "Hiển thị trục đối xứng OO'";
                    break;

                case "cylinder_section":
                    LblParam1.Text = "Bán kính đáy R:"; TxtParam1.Text = "2";
                    LblParam2.Text = "Chiều cao h:"; TxtParam2.Text = "3.5";
                    GridParam3.Visibility = Visibility.Collapsed;
                    LblParam4.Text = "Thiết diện:"; TxtParam4.Text = "A, B, C, D";
                    ChkOption.Content = "Tô màu nền thiết diện chữ nhật";
                    break;

                case "cone":
                    LblParam1.Text = "Bán kính đáy R:"; TxtParam1.Text = "2.5";
                    LblParam2.Text = "Chiều cao h:"; TxtParam2.Text = "3.5";
                    GridParam3.Visibility = Visibility.Collapsed;
                    LblParam4.Text = "Đỉnh & Tâm:"; TxtParam4.Text = "S, O";
                    ChkOption.Content = "Hiển thị đường sinh l";
                    break;

                case "cone_frustum":
                    LblParam1.Text = "Bán kính lớn R:"; TxtParam1.Text = "2.5";
                    LblParam2.Text = "Bán kính nhỏ r:"; TxtParam2.Text = "1.2";
                    LblParam3.Text = "Chiều cao h:"; TxtParam3.Text = "3";
                    LblParam4.Text = "Hai tâm:"; TxtParam4.Text = "O, O'";
                    ChkOption.Content = "Hiển thị bán kính R, r";
                    break;

                case "sphere":
                    LblParam1.Text = "Bán kính R:"; TxtParam1.Text = "2.5";
                    GridParam2.Visibility = Visibility.Collapsed;
                    GridParam3.Visibility = Visibility.Collapsed;
                    LblParam4.Text = "Tên tâm:"; TxtParam4.Text = "O";
                    ChkOption.Content = "Đổ bóng cầu 3D";
                    break;

                case "sphere_circum_cube":
                    LblParam1.Text = "Cạnh lập phương a:"; TxtParam1.Text = "2.5";
                    GridParam2.Visibility = Visibility.Collapsed;
                    GridParam3.Visibility = Visibility.Collapsed;
                    LblParam4.Text = "Tâm cầu:"; TxtParam4.Text = "I";
                    ChkOption.Content = "Bán kính R = a√3/2";
                    break;

                case "sphere_in_cube":
                    LblParam1.Text = "Cạnh lập phương a:"; TxtParam1.Text = "2.5";
                    GridParam2.Visibility = Visibility.Collapsed;
                    GridParam3.Visibility = Visibility.Collapsed;
                    LblParam4.Text = "Tâm cầu:"; TxtParam4.Text = "I";
                    ChkOption.Content = "Bán kính R = a/2";
                    break;

                case "sphere_circum_pyramid":
                    LblParam1.Text = "Cạnh đáy chóp a:"; TxtParam1.Text = "3";
                    LblParam2.Text = "Chiều cao h:"; TxtParam2.Text = "4";
                    GridParam3.Visibility = Visibility.Collapsed;
                    LblParam4.Text = "Đỉnh & Tâm:"; TxtParam4.Text = "S, I, H";
                    ChkOption.Content = "Tâm I trên đường cao SH";
                    break;

                case "octahedron":
                    LblParam1.Text = "Cạnh bát diện a:"; TxtParam1.Text = "3";
                    LblParam2.Text = "Chiều cao nửa trên h:"; TxtParam2.Text = "2.5";
                    GridParam3.Visibility = Visibility.Collapsed;
                    LblParam4.Text = "Đỉnh:"; TxtParam4.Text = "S, S', A, B, C, D";
                    ChkOption.Content = "Khối bát diện đều 8 mặt";
                    break;

                // Graph
                case "graph_quad":
                    LblParam1.Text = "Hệ số a (x²):"; TxtParam1.Text = "1";
                    LblParam2.Text = "Hệ số b (x):"; TxtParam2.Text = "-2";
                    LblParam3.Text = "Hệ số tự do c:"; TxtParam3.Text = "-1";
                    LblParam4.Text = "Miền x [min, max]:"; TxtParam4.Text = "-2, 4";
                    ChkOption.Content = "Hiển thị tọa độ đỉnh I";
                    break;

                case "graph_cubic":
                    LblParam1.Text = "Hệ số a (x³):"; TxtParam1.Text = "1";
                    LblParam2.Text = "Hệ số b (x²):"; TxtParam2.Text = "-3";
                    LblParam3.Text = "Hệ số c (x):"; TxtParam3.Text = "0";
                    LblParam4.Text = "Hệ số tự do d:"; TxtParam4.Text = "2";
                    ChkOption.Content = "Hiển thị 2 điểm cực trị";
                    break;

                case "graph_quartic":
                    LblParam1.Text = "Hệ số a (x⁴):"; TxtParam1.Text = "1";
                    LblParam2.Text = "Hệ số b (x²):"; TxtParam2.Text = "-2";
                    LblParam3.Text = "Hệ số c:"; TxtParam3.Text = "-1";
                    LblParam4.Text = "Miền x [min, max]:"; TxtParam4.Text = "-3, 3";
                    ChkOption.Visibility = Visibility.Collapsed;
                    break;

                case "graph_trig":
                    LblParam1.Text = "Biên độ A:"; TxtParam1.Text = "2";
                    LblParam2.Text = "Tần số omega:"; TxtParam2.Text = "1";
                    LblParam3.Text = "Hàm số (sin/cos):"; TxtParam3.Text = "sin";
                    LblParam4.Text = "Miền x:"; TxtParam4.Text = "-2*pi, 2*pi";
                    ChkOption.Content = "Hiển thị các mốc pi trên trục";
                    break;

                case "graph_rational":
                    LblParam1.Text = "Tử số (ax + b):"; TxtParam1.Text = "2, 1";
                    LblParam2.Text = "Mẫu số (cx + d):"; TxtParam2.Text = "1, -1";
                    GridParam3.Visibility = Visibility.Collapsed;
                    LblParam4.Text = "Miền x [min, max]:"; TxtParam4.Text = "-4, 6";
                    ChkOption.Content = "Vẽ 2 đường tiệm cận nét đứt";
                    break;

                // Charts
                case "chart_bar":
                    LblParam1.Text = "Dữ liệu (Giá trị):"; TxtParam1.Text = "25, 40, 18, 32";
                    LblParam2.Text = "Nhãn các cột:"; TxtParam2.Text = "Lớp A, Lớp B, Lớp C, Lớp D";
                    GridParam3.Visibility = Visibility.Collapsed;
                    LblParam4.Text = "Tiêu đề biểu đồ:"; TxtParam4.Text = "Số học sinh đạt điểm giỏi";
                    ChkOption.Content = "Hiển thị số liệu trên đỉnh cột";
                    break;

                case "chart_pie":
                    LblParam1.Text = "Phần trăm (%):"; TxtParam1.Text = "40, 30, 20, 10";
                    LblParam2.Text = "Nhãn thành phần:"; TxtParam2.Text = "Toán, Lý, Hóa, Sinh";
                    GridParam3.Visibility = Visibility.Collapsed;
                    LblParam4.Text = "Tiêu đề:"; TxtParam4.Text = "Cơ cấu môn thi KHTN";
                    ChkOption.Content = "Vẽ chú thích Legend bên cạnh";
                    break;

                case "chart_line":
                case "chart_area":
                    LblParam1.Text = "Dữ liệu Y:"; TxtParam1.Text = "12, 19, 28, 35, 42";
                    LblParam2.Text = "Mốc thời gian X:"; TxtParam2.Text = "2021, 2022, 2023, 2024, 2025";
                    GridParam3.Visibility = Visibility.Collapsed;
                    LblParam4.Text = "Tên chỉ tiêu:"; TxtParam4.Text = "Tỷ lệ đỗ tốt nghiệp (%)";
                    ChkOption.Content = "Đổ màu vùng dưới đường (Area)";
                    break;

                // tkz-tab
                case "tab_cubic":
                    LblParam1.Text = "Điểm cực trị x1, x2:"; TxtParam1.Text = "0, 2";
                    LblParam2.Text = "Giá trị y cực trị:"; TxtParam2.Text = "2, -2";
                    GridParam3.Visibility = Visibility.Collapsed;
                    LblParam4.Text = "Dấu f'(x) (+/-):"; TxtParam4.Text = "+, -, +";
                    ChkOption.Content = "Có dòng xét dấu đạo hàm f'(x)";
                    break;

                case "tab_quartic":
                    LblParam1.Text = "3 điểm cực trị:"; TxtParam1.Text = "-1, 0, 1";
                    LblParam2.Text = "Giá trị y cực trị:"; TxtParam2.Text = "0, 1, 0";
                    GridParam3.Visibility = Visibility.Collapsed;
                    LblParam4.Text = "Dấu đạo hàm:"; TxtParam4.Text = "-, +, -, +";
                    ChkOption.Visibility = Visibility.Collapsed;
                    break;

                case "tab_rational":
                    LblParam1.Text = "Điểm gián đoạn x0:"; TxtParam1.Text = "1";
                    LblParam2.Text = "Tiệm cận ngang y0:"; TxtParam2.Text = "2";
                    GridParam3.Visibility = Visibility.Collapsed;
                    LblParam4.Text = "Dấu đạo hàm (+/-):"; TxtParam4.Text = "-, -";
                    ChkOption.Content = "Dùng ký hiệu 2 vạch đứng (d)";
                    break;

                case "tab_sign_quad":
                    LblParam1.Text = "2 nghiệm x1, x2:"; TxtParam1.Text = "1, 3";
                    GridParam2.Visibility = Visibility.Collapsed;
                    GridParam3.Visibility = Visibility.Collapsed;
                    LblParam4.Text = "Dấu tam thức:"; TxtParam4.Text = "+, -, +";
                    ChkOption.Visibility = Visibility.Collapsed;
                    break;

                default:
                    LblParam1.Text = "Thông số 1:";
                    LblParam2.Text = "Thông số 2:";
                    LblParam3.Text = "Thông số 3:";
                    LblParam4.Text = "Tên đỉnh / Nhãn:";
                    break;
            }
        }

        private void Param_TextChanged(object sender, TextChangedEventArgs e)
        {
            if (_isInitializing) return;
            RegenerateCode();
        }

        private void ChkOption_Changed(object sender, RoutedEventArgs e)
        {
            if (_isInitializing) return;
            RegenerateCode();
        }

        private void RegenerateCode()
        {
            if (TxtResultCode == null) return;

            string p1 = TxtParam1?.Text?.Trim() ?? "4";
            string p2 = TxtParam2?.Text?.Trim() ?? "3";
            string p3 = TxtParam3?.Text?.Trim() ?? "2";
            string p4 = TxtParam4?.Text?.Trim() ?? "A,B,C,D";
            bool opt = ChkOption?.IsChecked ?? true;

            TxtResultCode.Text = GenerateTikzCodeForShape(_currentShapeTag, p1, p2, p3, p4, opt);
        }

        private static string GenerateTikzCodeForShape(string tag, string p1, string p2, string p3, string p4, bool opt)
        {
            var sb = new StringBuilder();
            double.TryParse(p1, NumberStyles.Any, CultureInfo.InvariantCulture, out double v1);
            double.TryParse(p2, NumberStyles.Any, CultureInfo.InvariantCulture, out double v2);
            double.TryParse(p3, NumberStyles.Any, CultureInfo.InvariantCulture, out double v3);
            if (v1 <= 0) v1 = 4;
            if (v2 <= 0) v2 = 3;

            switch (tag)
            {
                case "tri_general":
                    sb.AppendLine(@"\begin{tikzpicture}[scale=1, thick]");
                    sb.AppendLine($@"  \coordinate[label=below left:$A$] (A) at (0,0);");
                    sb.AppendLine($@"  \coordinate[label=below right:$B$] (B) at ({v1},0);");
                    sb.AppendLine($@"  \coordinate[label=above:$C$] (C) at ({Math.Round(v1 * 0.4, 2)},{v2});");
                    sb.AppendLine(@"  \draw (A)--(B)--(C)--cycle;");
                    if (opt)
                    {
                        sb.AppendLine($@"  \coordinate[label=below:$H$] (H) at ({Math.Round(v1 * 0.4, 2)},0);");
                        sb.AppendLine(@"  \draw[dashed] (C)--(H);");
                        sb.AppendLine(@"  \draw (H) +(0.2,0) -- +(0.2,0.2) -- +(0,0.2);");
                    }
                    sb.Append(@"\end{tikzpicture}");
                    break;

                case "tri_right":
                    sb.AppendLine(@"\begin{tikzpicture}[scale=1, thick]");
                    sb.AppendLine(@"  \coordinate[label=below left:$A$] (A) at (0,0);");
                    sb.AppendLine($@"  \coordinate[label=below right:$B$] (B) at ({v1},0);");
                    sb.AppendLine($@"  \coordinate[label=above left:$C$] (C) at (0,{v2});");
                    sb.AppendLine(@"  \draw (A)--(B)--(C)--cycle;");
                    if (opt)
                    {
                        sb.AppendLine(@"  % Góc vuông tại A");
                        sb.AppendLine(@"  \draw (A) +(0.3,0) -- +(0.3,0.3) -- +(0,0.3);");
                    }
                    sb.Append(@"\end{tikzpicture}");
                    break;

                case "tri_equi":
                    double hEqui = Math.Round(v1 * Math.Sqrt(3) / 2.0, 2);
                    sb.AppendLine(@"\begin{tikzpicture}[scale=1, thick]");
                    sb.AppendLine(@"  \coordinate[label=below left:$A$] (A) at (0,0);");
                    sb.AppendLine($@"  \coordinate[label=below right:$B$] (B) at ({v1},0);");
                    sb.AppendLine($@"  \coordinate[label=above:$C$] (C) at ({Math.Round(v1 / 2.0, 2)},{hEqui});");
                    sb.AppendLine(@"  \draw (A)--(B)--(C)--cycle;");
                    if (opt)
                    {
                        sb.AppendLine($@"  \coordinate[label=below:$H$] (H) at ({Math.Round(v1 / 2.0, 2)},0);");
                        sb.AppendLine(@"  \draw[dashed] (C)--(H);");
                    }
                    sb.Append(@"\end{tikzpicture}");
                    break;

                case "tri_iso":
                    sb.AppendLine(@"\begin{tikzpicture}[scale=1, thick]");
                    sb.AppendLine(@"  \coordinate[label=below left:$A$] (A) at (0,0);");
                    sb.AppendLine($@"  \coordinate[label=below right:$B$] (B) at ({v1},0);");
                    sb.AppendLine($@"  \coordinate[label=above:$C$] (C) at ({Math.Round(v1 / 2.0, 2)},{v2});");
                    sb.AppendLine(@"  \draw (A)--(B)--(C)--cycle;");
                    if (opt)
                    {
                        sb.AppendLine($@"  \coordinate[label=below:$H$] (H) at ({Math.Round(v1 / 2.0, 2)},0);");
                        sb.AppendLine(@"  \draw[dashed] (C)--(H);");
                    }
                    sb.Append(@"\end{tikzpicture}");
                    break;

                case "square":
                case "rect":
                    double heightRect = (tag == "square") ? v1 : v2;
                    sb.AppendLine(@"\begin{tikzpicture}[scale=1, thick]");
                    sb.AppendLine(@"  \coordinate[label=below left:$A$] (A) at (0,0);");
                    sb.AppendLine($@"  \coordinate[label=below right:$B$] (B) at ({v1},0);");
                    sb.AppendLine($@"  \coordinate[label=above right:$C$] (C) at ({v1},{heightRect});");
                    sb.AppendLine($@"  \coordinate[label=above left:$D$] (D) at (0,{heightRect});");
                    sb.AppendLine(@"  \draw (A)--(B)--(C)--(D)--cycle;");
                    if (opt)
                    {
                        sb.AppendLine(@"  \draw[dashed] (A)--(C) (B)--(D);");
                    }
                    sb.Append(@"\end{tikzpicture}");
                    break;

                case "parallelogram":
                    double skew = v3 > 0 ? v3 : 1.5;
                    sb.AppendLine(@"\begin{tikzpicture}[scale=1, thick]");
                    sb.AppendLine(@"  \coordinate[label=below left:$A$] (A) at (0,0);");
                    sb.AppendLine($@"  \coordinate[label=below right:$B$] (B) at ({v1},0);");
                    sb.AppendLine($@"  \coordinate[label=above right:$C$] (C) at ({Math.Round(v1 + skew, 2)},{v2});");
                    sb.AppendLine($@"  \coordinate[label=above left:$D$] (D) at ({skew},{v2});");
                    sb.AppendLine(@"  \draw (A)--(B)--(C)--(D)--cycle;");
                    sb.Append(@"\end{tikzpicture}");
                    break;

                case "trapezoid":
                    double offset = Math.Round((v1 - v2) / 2.0, 2);
                    double hTrap = v3 > 0 ? v3 : 3;
                    sb.AppendLine(@"\begin{tikzpicture}[scale=1, thick]");
                    sb.AppendLine(@"  \coordinate[label=below left:$A$] (A) at (0,0);");
                    sb.AppendLine($@"  \coordinate[label=below right:$B$] (B) at ({v1},0);");
                    sb.AppendLine($@"  \coordinate[label=above right:$C$] (C) at ({Math.Round(v1 - offset, 2)},{hTrap});");
                    sb.AppendLine($@"  \coordinate[label=above left:$D$] (D) at ({offset},{hTrap});");
                    sb.AppendLine(@"  \draw (A)--(B)--(C)--(D)--cycle;");
                    sb.Append(@"\end{tikzpicture}");
                    break;

                case "circle":
                    sb.AppendLine(@"\begin{tikzpicture}[scale=1, thick]");
                    sb.AppendLine(@"  \coordinate (O) at (0,0);");
                    sb.AppendLine($@"  \draw (O) circle ({v1}cm);");
                    sb.AppendLine(@"  \fill (O) circle (1.5pt) node[below]{$O$};");
                    if (opt)
                    {
                        sb.AppendLine($@"  \coordinate[label=right:$A$] (A) at ({v1},0);");
                        sb.AppendLine(@"  \draw[dashed] (O)--(A) node[midway,above]{$R$};");
                        sb.AppendLine(@"  \draw (A) +(0,-1.5) -- +(0,1.5);");
                    }
                    sb.Append(@"\end{tikzpicture}");
                    break;

                case "ellipse":
                    sb.AppendLine(@"\begin{tikzpicture}[scale=1, thick]");
                    sb.AppendLine($@"  \draw (0,0) ellipse ({v1}cm and {v2}cm);");
                    sb.AppendLine(@"  \fill (0,0) circle (1.5pt) node[below left]{$O$};");
                    if (opt)
                    {
                        sb.AppendLine($@"  \draw[->] (-{v1 + 0.8},0) -- ({v1 + 0.8},0) node[right]{{$x$}};");
                        sb.AppendLine($@"  \draw[->] (0,-{v2 + 0.6}) -- (0,{v2 + 0.6}) node[above]{{$y$}};");
                    }
                    sb.Append(@"\end{tikzpicture}");
                    break;

                case "segment":
                    sb.AppendLine(@"\begin{tikzpicture}[scale=1, thick]");
                    sb.AppendLine(@"  \coordinate[label=below left:$A$] (A) at (0,0);");
                    sb.AppendLine($@"  \coordinate[label=below right:$B$] (B) at ({v1},0);");
                    string arrowStyle = opt ? "->, thick" : "thick";
                    sb.AppendLine($@"  \draw[{arrowStyle}] (A)--(B);");
                    sb.AppendLine(@"  \fill (A) circle (1.5pt) (B) circle (1.5pt);");
                    sb.Append(@"\end{tikzpicture}");
                    break;

                // 3D
                case "pyramid":
                    double halfPyr = Math.Round(v1 / 2.0, 2);
                    sb.AppendLine(@"\begin{tikzpicture}[scale=1.2, thick,");
                    sb.AppendLine(@"    x={(1cm,0cm)}, y={(0.4cm,0.3cm)}, z={(0cm,1cm)}]");
                    sb.AppendLine(@"  \coordinate[label=below left:$A$] (A) at (0,0,0);");
                    sb.AppendLine($@"  \coordinate[label=below right:$B$] (B) at ({v1},0,0);");
                    sb.AppendLine($@"  \coordinate[label=right:$C$] (C) at ({v1},{v1},0);");
                    sb.AppendLine($@"  \coordinate[label=left:$D$] (D) at (0,{v1},0);");
                    sb.AppendLine($@"  \coordinate[label=above:$S$] (S) at ({halfPyr},{halfPyr},{v2});");
                    sb.AppendLine(@"  % Đáy");
                    sb.AppendLine(@"  \draw (A)--(B)--(C);");
                    sb.AppendLine(@"  \draw[dashed] (C)--(D)--(A);");
                    sb.AppendLine(@"  % Cạnh bên");
                    sb.AppendLine(@"  \draw (S)--(A) (S)--(B) (S)--(C);");
                    sb.AppendLine(@"  \draw[dashed] (S)--(D);");
                    sb.AppendLine(@"  \draw[dashed] (A)--(C) (B)--(D);");
                    sb.Append(@"\end{tikzpicture}");
                    break;

                case "pyramid_sa_quad":
                    sb.AppendLine(@"\begin{tikzpicture}[scale=1.2, thick,");
                    sb.AppendLine(@"    x={(1cm,0cm)}, y={(0.4cm,0.3cm)}, z={(0cm,1cm)}]");
                    sb.AppendLine(@"  \coordinate[label=below left:$A$] (A) at (0,0,0);");
                    sb.AppendLine($@"  \coordinate[label=below right:$B$] (B) at ({v1},0,0);");
                    sb.AppendLine($@"  \coordinate[label=right:$C$] (C) at ({v1},{v1},0);");
                    sb.AppendLine($@"  \coordinate[label=above left:$D$] (D) at (0,{v1},0);");
                    sb.AppendLine($@"  \coordinate[label=above:$S$] (S) at (0,0,{v2});");
                    sb.AppendLine(@"  \draw (A)--(B)--(C);");
                    sb.AppendLine(@"  \draw[dashed] (C)--(D)--(A);");
                    sb.AppendLine(@"  \draw (S)--(A) (S)--(B) (S)--(C);");
                    sb.AppendLine(@"  \draw[dashed] (S)--(D);");
                    if (opt)
                    {
                        sb.AppendLine(@"  \draw pic [draw, angle radius=3mm] {right angle = S--A--B};");
                        sb.AppendLine(@"  \draw pic [draw, angle radius=3mm] {right angle = S--A--D};");
                    }
                    sb.Append(@"\end{tikzpicture}");
                    break;

                case "pyramid_regular_quad":
                    double hCent = Math.Round(v1 / 2.0, 2);
                    sb.AppendLine(@"\begin{tikzpicture}[scale=1.2, thick,");
                    sb.AppendLine(@"    x={(1cm,0cm)}, y={(0.4cm,0.3cm)}, z={(0cm,1cm)}]");
                    sb.AppendLine(@"  \coordinate[label=below left:$A$] (A) at (0,0,0);");
                    sb.AppendLine($@"  \coordinate[label=below right:$B$] (B) at ({v1},0,0);");
                    sb.AppendLine($@"  \coordinate[label=right:$C$] (C) at ({v1},{v1},0);");
                    sb.AppendLine($@"  \coordinate[label=above left:$D$] (D) at (0,{v1},0);");
                    sb.AppendLine($@"  \coordinate (H) at ({hCent},{hCent},0);");
                    sb.AppendLine($@"  \coordinate[label=above:$S$] (S) at ({hCent},{hCent},{v2});");
                    sb.AppendLine(@"  \draw (A)--(B)--(C);");
                    sb.AppendLine(@"  \draw[dashed] (C)--(D)--(A);");
                    sb.AppendLine(@"  \draw (S)--(A) (S)--(B) (S)--(C);");
                    sb.AppendLine(@"  \draw[dashed] (S)--(D);");
                    sb.AppendLine(@"  \draw[dashed] (S)--(H);");
                    sb.AppendLine(@"  \fill (H) circle (1.2pt) node[below right] {$H$};");
                    sb.AppendLine(@"  \draw[densely dotted] (A)--(C) (B)--(D);");
                    sb.Append(@"\end{tikzpicture}");
                    break;

                case "pyramid_tri":
                    sb.AppendLine(@"\begin{tikzpicture}[scale=1.2, thick,");
                    sb.AppendLine(@"    x={(1cm,0cm)}, y={(0.4cm,0.3cm)}, z={(0cm,1cm)}]");
                    sb.AppendLine(@"  \coordinate[label=below left:$A$] (A) at (0,0,0);");
                    sb.AppendLine($@"  \coordinate[label=below right:$B$] (B) at ({v1},0,0);");
                    sb.AppendLine($@"  \coordinate[label=right:$C$] (C) at ({Math.Round(v1 * 0.5, 2)},{Math.Round(v1 * 0.8, 2)},0);");
                    sb.AppendLine($@"  \coordinate[label=above:$S$] (S) at ({Math.Round(v1 * 0.4, 2)},{Math.Round(v1 * 0.3, 2)},{v2});");
                    sb.AppendLine(@"  \draw (A)--(B)--(C);");
                    sb.AppendLine(@"  \draw[dashed] (C)--(A);");
                    sb.AppendLine(@"  \draw (S)--(A) (S)--(B) (S)--(C);");
                    sb.Append(@"\end{tikzpicture}");
                    break;

                case "pyramid_sa_perp":
                    sb.AppendLine(@"\begin{tikzpicture}[scale=1.2, thick,");
                    sb.AppendLine(@"    x={(1cm,0cm)}, y={(0.4cm,0.3cm)}, z={(0cm,1cm)}]");
                    sb.AppendLine(@"  \coordinate[label=below left:$A$] (A) at (0,0,0);");
                    sb.AppendLine($@"  \coordinate[label=below right:$B$] (B) at ({v1},0,0);");
                    sb.AppendLine($@"  \coordinate[label=right:$C$] (C) at ({Math.Round(v1 * 0.5, 2)},{Math.Round(v1 * 0.8, 2)},0);");
                    sb.AppendLine($@"  \coordinate[label=above:$S$] (S) at (0,0,{v2});");
                    sb.AppendLine(@"  \draw (A)--(B)--(C);");
                    sb.AppendLine(@"  \draw[dashed] (A)--(C);");
                    sb.AppendLine(@"  \draw (S)--(A) (S)--(B) (S)--(C);");
                    if (opt)
                    {
                        sb.AppendLine(@"  \draw pic [draw, angle radius=3mm] {right angle = S--A--B};");
                    }
                    sb.Append(@"\end{tikzpicture}");
                    break;

                case "pyramid_regular_tri":
                    sb.AppendLine(@"\begin{tikzpicture}[scale=1.2, thick,");
                    sb.AppendLine(@"    x={(1cm,0cm)}, y={(0.4cm,0.3cm)}, z={(0cm,1cm)}]");
                    sb.AppendLine(@"  \coordinate[label=below left:$A$] (A) at (0,0,0);");
                    sb.AppendLine($@"  \coordinate[label=below right:$B$] (B) at ({v1},0,0);");
                    sb.AppendLine($@"  \coordinate[label=above:$C$] (C) at ({Math.Round(v1 * 0.5, 2)},{Math.Round(v1 * 0.86, 2)},0);");
                    sb.AppendLine($@"  \coordinate (H) at ({Math.Round(v1 * 0.5, 2)},{Math.Round(v1 * 0.29, 2)},0);");
                    sb.AppendLine($@"  \coordinate[label=above:$S$] (S) at ({Math.Round(v1 * 0.5, 2)},{Math.Round(v1 * 0.29, 2)},{v2});");
                    sb.AppendLine(@"  \draw (A)--(B)--(C);");
                    sb.AppendLine(@"  \draw[dashed] (C)--(A);");
                    sb.AppendLine(@"  \draw (S)--(A) (S)--(B);");
                    sb.AppendLine(@"  \draw[dashed] (S)--(C);");
                    sb.AppendLine(@"  \draw[dashed] (S)--(H);");
                    sb.AppendLine(@"  \fill (H) circle (1.2pt) node[below right] {$H$};");
                    sb.Append(@"\end{tikzpicture}");
                    break;

                case "tetrahedron":
                    sb.AppendLine(@"\begin{tikzpicture}[scale=1.2, thick,");
                    sb.AppendLine(@"    x={(1cm,0cm)}, y={(0.4cm,0.3cm)}, z={(0cm,1cm)}]");
                    sb.AppendLine(@"  \coordinate[label=below left:$A$] (A) at (0,0,0);");
                    sb.AppendLine($@"  \coordinate[label=below right:$B$] (B) at ({v1},0,0);");
                    sb.AppendLine($@"  \coordinate[label=right:$C$] (C) at ({Math.Round(v1 * 0.5, 2)},{Math.Round(v1 * 0.86, 2)},0);");
                    sb.AppendLine($@"  \coordinate[label=above:$D$] (S) at ({Math.Round(v1 * 0.5, 2)},{Math.Round(v1 * 0.3, 2)},{v2});");
                    sb.AppendLine(@"  \draw (A)--(B)--(S)--cycle;");
                    sb.AppendLine(@"  \draw (B)--(C)--(S);");
                    sb.AppendLine(@"  \draw[dashed] (A)--(C);");
                    sb.Append(@"\end{tikzpicture}");
                    break;

                case "cube":
                    sb.AppendLine(@"\begin{tikzpicture}[scale=1.2, thick,");
                    sb.AppendLine(@"    x={(1cm,0cm)}, y={(0.4cm,0.3cm)}, z={(0cm,1cm)}]");
                    sb.AppendLine(@"  \coordinate[label=below left:$A$] (A) at (0,0,0);");
                    sb.AppendLine($@"  \coordinate[label=below right:$B$] (B) at ({v1},0,0);");
                    sb.AppendLine($@"  \coordinate[label=right:$C$] (C) at ({v1},{v1},0);");
                    sb.AppendLine($@"  \coordinate[label=above left:$D$] (D) at (0,{v1},0);");
                    sb.AppendLine($@"  \coordinate[label=above left:$A'$] (A1) at (0,0,{v1});");
                    sb.AppendLine($@"  \coordinate[label=above right:$B'$] (B1) at ({v1},0,{v1});");
                    sb.AppendLine($@"  \coordinate[label=right:$C'$] (C1) at ({v1},{v1},{v1});");
                    sb.AppendLine($@"  \coordinate[label=above:$D'$] (D1) at (0,{v1},{v1});");
                    sb.AppendLine(@"  \draw (A)--(B)--(C);");
                    sb.AppendLine(@"  \draw[dashed] (C)--(D)--(A);");
                    sb.AppendLine(@"  \draw (A)--(A1) (B)--(B1) (C)--(C1);");
                    sb.AppendLine(@"  \draw[dashed] (D)--(D1);");
                    sb.AppendLine(@"  \draw (A1)--(B1)--(C1)--(D1)--cycle;");
                    if (opt)
                    {
                        sb.AppendLine(@"  \draw[red, very thick] (A)--(C1) node[midway, below right] {$a\sqrt{3}$};");
                    }
                    sb.Append(@"\end{tikzpicture}");
                    break;

                case "cube_diagonal":
                    sb.AppendLine(@"\begin{tikzpicture}[scale=1.2, thick,");
                    sb.AppendLine(@"    x={(1cm,0cm)}, y={(0.4cm,0.3cm)}, z={(0cm,1cm)}]");
                    sb.AppendLine(@"  \coordinate[label=below left:$A$] (A) at (0,0,0);");
                    sb.AppendLine($@"  \coordinate[label=below right:$B$] (B) at ({v1},0,0);");
                    sb.AppendLine($@"  \coordinate[label=right:$C$] (C) at ({v1},{v1},0);");
                    sb.AppendLine($@"  \coordinate[label=above left:$D$] (D) at (0,{v1},0);");
                    sb.AppendLine($@"  \coordinate[label=above left:$A'$] (A1) at (0,0,{v1});");
                    sb.AppendLine($@"  \coordinate[label=above right:$B'$] (B1) at ({v1},0,{v1});");
                    sb.AppendLine($@"  \coordinate[label=right:$C'$] (C1) at ({v1},{v1},{v1});");
                    sb.AppendLine($@"  \coordinate[label=above:$D'$] (D1) at (0,{v1},{v1});");
                    sb.AppendLine(@"  \draw (A)--(B)--(C);");
                    sb.AppendLine(@"  \draw[dashed] (C)--(D)--(A);");
                    sb.AppendLine(@"  \draw (A)--(A1) (B)--(B1) (C)--(C1);");
                    sb.AppendLine(@"  \draw[dashed] (D)--(D1);");
                    sb.AppendLine(@"  \draw (A1)--(B1)--(C1)--(D1)--cycle;");
                    sb.AppendLine(@"  \draw[red, very thick] (A)--(C1) node[midway, below right] {$a\sqrt{3}$};");
                    sb.Append(@"\end{tikzpicture}");
                    break;

                case "cuboid":
                    double hCub = v3 > 0 ? v3 : 3.5;
                    sb.AppendLine(@"\begin{tikzpicture}[scale=1.1, thick,");
                    sb.AppendLine(@"    x={(1cm,0cm)}, y={(0.4cm,0.3cm)}, z={(0cm,1cm)}]");
                    sb.AppendLine(@"  \coordinate[label=below left:$A$] (A) at (0,0,0);");
                    sb.AppendLine($@"  \coordinate[label=below right:$B$] (B) at ({v1},0,0);");
                    sb.AppendLine($@"  \coordinate[label=right:$C$] (C) at ({v1},{v2},0);");
                    sb.AppendLine($@"  \coordinate[label=left:$D$] (D) at (0,{v2},0);");
                    sb.AppendLine($@"  \coordinate[label=above left:$A'$] (A1) at (0,0,{hCub});");
                    sb.AppendLine($@"  \coordinate[label=above right:$B'$] (B1) at ({v1},0,{hCub});");
                    sb.AppendLine($@"  \coordinate[label=above right:$C'$] (C1) at ({v1},{v2},{hCub});");
                    sb.AppendLine($@"  \coordinate[label=above left:$D'$] (D1) at (0,{v2},{hCub});");
                    sb.AppendLine(@"  \draw (A)--(B)--(C);");
                    sb.AppendLine(@"  \draw[dashed] (C)--(D)--(A);");
                    sb.AppendLine(@"  \draw (A1)--(B1)--(C1)--(D1)--cycle;");
                    sb.AppendLine(@"  \draw (A)--(A1) (B)--(B1) (C)--(C1);");
                    sb.AppendLine(@"  \draw[dashed] (D)--(D1);");
                    if (opt)
                    {
                        sb.AppendLine($@"  \draw[<->] (0,-0.4,0)--({v1},-0.4,0) node[midway, below] {{$a$}};");
                    }
                    sb.Append(@"\end{tikzpicture}");
                    break;

                case "prism_triangular":
                    sb.AppendLine(@"\begin{tikzpicture}[scale=1.2, thick,");
                    sb.AppendLine(@"    x={(1cm,0cm)}, y={(0.4cm,0.3cm)}, z={(0cm,1cm)}]");
                    sb.AppendLine(@"  \coordinate[label=below left:$A$] (A) at (0,0,0);");
                    sb.AppendLine($@"  \coordinate[label=below right:$B$] (B) at ({v1},0,0);");
                    sb.AppendLine($@"  \coordinate[label=right:$C$] (C) at ({Math.Round(v1 * 0.5, 2)},{Math.Round(v1 * 0.8, 2)},0);");
                    sb.AppendLine($@"  \coordinate[label=above left:$A'$] (A1) at (0,0,{v2});");
                    sb.AppendLine($@"  \coordinate[label=above right:$B'$] (B1) at ({v1},0,{v2});");
                    sb.AppendLine($@"  \coordinate[label=above:$C'$] (C1) at ({Math.Round(v1 * 0.5, 2)},{Math.Round(v1 * 0.8, 2)},{v2});");
                    sb.AppendLine(@"  \draw (A)--(B)--(C);");
                    sb.AppendLine(@"  \draw (A)--(A1) (B)--(B1) (C)--(C1);");
                    sb.AppendLine(@"  \draw (A1)--(B1)--(C1)--cycle;");
                    sb.AppendLine(@"  \draw[dashed] (C)--(A);");
                    sb.Append(@"\end{tikzpicture}");
                    break;

                case "pyramid_frustum":
                    double hFrust = v3 > 0 ? v3 : 2.8;
                    double offF = Math.Round((v1 - v2) / 2.0, 2);
                    sb.AppendLine(@"\begin{tikzpicture}[scale=1.2, thick,");
                    sb.AppendLine(@"    x={(1cm,0cm)}, y={(0.4cm,0.3cm)}, z={(0cm,1cm)}]");
                    sb.AppendLine(@"  \coordinate[label=below left:$A$] (A) at (0,0,0);");
                    sb.AppendLine($@"  \coordinate[label=below right:$B$] (B) at ({v1},0,0);");
                    sb.AppendLine($@"  \coordinate[label=right:$C$] (C) at ({v1},{v1},0);");
                    sb.AppendLine($@"  \coordinate[label=above left:$D$] (D) at (0,{v1},0);");
                    sb.AppendLine($@"  \coordinate[label=left:$A'$] (A1) at ({offF},{offF},{hFrust});");
                    sb.AppendLine($@"  \coordinate[label=right:$B'$] (B1) at ({Math.Round(offF + v2, 2)},{offF},{hFrust});");
                    sb.AppendLine($@"  \coordinate[label=right:$C'$] (C1) at ({Math.Round(offF + v2, 2)},{Math.Round(offF + v2, 2)},{hFrust});");
                    sb.AppendLine($@"  \coordinate[label=above:$D'$] (D1) at ({offF},{Math.Round(offF + v2, 2)},{hFrust});");
                    sb.AppendLine(@"  \draw (A)--(B)--(C); \draw[dashed] (C)--(D)--(A);");
                    sb.AppendLine(@"  \draw (A1)--(B1)--(C1)--(D1)--cycle;");
                    sb.AppendLine(@"  \draw (A)--(A1) (B)--(B1) (C)--(C1);");
                    sb.AppendLine(@"  \draw[dashed] (D)--(D1);");
                    sb.Append(@"\end{tikzpicture}");
                    break;

                case "cylinder":
                    double eCyl = Math.Round(v1 * 0.35, 2);
                    sb.AppendLine(@"\begin{tikzpicture}[scale=1, thick]");
                    sb.AppendLine($@"  \draw (0,0) ellipse ({v1}cm and {eCyl}cm);");
                    sb.AppendLine($@"  \draw (0,{v2}) ellipse ({v1}cm and {eCyl}cm);");
                    sb.AppendLine($@"  \draw (-{v1},0)--(-{v1},{v2});");
                    sb.AppendLine($@"  \draw ({v1},0)--({v1},{v2});");
                    sb.AppendLine($@"  \draw[dashed] (0,0)--(0,{v2});");
                    sb.AppendLine(@"  \fill (0,0) circle (1.5pt) node[below]{$O$};");
                    sb.AppendLine($@"  \fill (0,{v2}) circle (1.5pt) node[above]{{$O'$}};");
                    sb.Append(@"\end{tikzpicture}");
                    break;

                case "cylinder_section":
                    double eSec = Math.Round(v1 * 0.35, 2);
                    sb.AppendLine(@"\begin{tikzpicture}[scale=1, thick]");
                    sb.AppendLine($@"  \draw (-{v1},0) arc (180:360:{v1}cm and {eSec}cm);");
                    sb.AppendLine($@"  \draw[dashed] (-{v1},0) arc (180:0:{v1}cm and {eSec}cm);");
                    sb.AppendLine($@"  \draw (0,{v2}) ellipse ({v1}cm and {eSec}cm);");
                    sb.AppendLine($@"  \draw (-{v1},0)--(-{v1},{v2});");
                    sb.AppendLine($@"  \draw ({v1},0)--({v1},{v2});");
                    sb.AppendLine($@"  \draw[dashed] (0,0)--(0,{v2});");
                    sb.AppendLine(@"  \fill (0,0) circle (1.5pt) node[below]{$O$};");
                    sb.AppendLine($@"  \fill (0,{v2}) circle (1.5pt) node[above]{{$O'$}};");
                    sb.AppendLine($@"  \coordinate[label=below left:$A$] (A) at (-{v1},0);");
                    sb.AppendLine($@"  \coordinate[label=below right:$B$] (B) at ({v1},0);");
                    sb.AppendLine($@"  \coordinate[label=above right:$C$] (C) at ({v1},{v2});");
                    sb.AppendLine($@"  \coordinate[label=above left:$D$] (D) at (-{v1},{v2});");
                    sb.AppendLine(@"  \fill[blue!15, opacity=0.5] (A)--(B)--(C)--(D)--cycle;");
                    sb.AppendLine(@"  \draw[blue, thick] (A)--(B)--(C)--(D)--cycle;");
                    sb.Append(@"\end{tikzpicture}");
                    break;

                case "cone":
                    double eCone = Math.Round(v1 * 0.35, 2);
                    sb.AppendLine(@"\begin{tikzpicture}[scale=1, thick]");
                    sb.AppendLine($@"  \draw (0,0) ellipse ({v1}cm and {eCone}cm);");
                    sb.AppendLine($@"  \coordinate[label=above:$S$] (S) at (0,{v2});");
                    sb.AppendLine($@"  \draw (-{v1},0)--(S)--({v1},0);");
                    sb.AppendLine(@"  \draw[dashed] (0,0)--(S);");
                    sb.AppendLine(@"  \fill (0,0) circle (1.5pt) node[below right]{$O$};");
                    sb.AppendLine(@"  \fill (S) circle (1.5pt);");
                    sb.Append(@"\end{tikzpicture}");
                    break;

                case "cone_frustum":
                    double eR = Math.Round(v1 * 0.35, 2);
                    double er = Math.Round(v2 * 0.35, 2);
                    double hCf = v3 > 0 ? v3 : 3;
                    sb.AppendLine(@"\begin{tikzpicture}[scale=1, thick]");
                    sb.AppendLine($@"  \draw (-{v1},0) arc (180:360:{v1}cm and {eR}cm);");
                    sb.AppendLine($@"  \draw[dashed] (-{v1},0) arc (180:0:{v1}cm and {eR}cm);");
                    sb.AppendLine($@"  \draw (0,{hCf}) ellipse ({v2}cm and {er}cm);");
                    sb.AppendLine($@"  \draw (-{v1},0)--(-{v2},{hCf});");
                    sb.AppendLine($@"  \draw ({v1},0)--({v2},{hCf});");
                    sb.AppendLine($@"  \draw[dashed] (0,0)--(0,{hCf});");
                    sb.AppendLine(@"  \fill (0,0) circle (1.5pt) node[below]{$O$};");
                    sb.AppendLine($@"  \fill (0,{hCf}) circle (1.5pt) node[above]{{$O'$}};");
                    sb.Append(@"\end{tikzpicture}");
                    break;

                case "sphere":
                    double eSph = Math.Round(v1 * 0.35, 2);
                    sb.AppendLine(@"\begin{tikzpicture}[scale=1, thick]");
                    if (opt) sb.AppendLine($@"  \shade[ball color=blue!15!white, opacity=0.6] (0,0) circle ({v1}cm);");
                    sb.AppendLine($@"  \draw (0,0) circle ({v1}cm);");
                    sb.AppendLine($@"  \draw[dashed] (0,0) ellipse ({v1}cm and {eSph}cm);");
                    sb.AppendLine(@"  \fill (0,0) circle (1.5pt) node[below right]{$O$};");
                    sb.AppendLine($@"  \draw[<->] (0,0)--({v1},0) node[midway,above]{{$R={v1}$}};");
                    sb.Append(@"\end{tikzpicture}");
                    break;

                case "sphere_circum_cube":
                    sb.AppendLine(@"\begin{tikzpicture}[scale=1.2, thick]");
                    sb.AppendLine(@"  \begin{scope}[x={(1cm,0cm)}, y={(0.5cm,0.3cm)}, z={(0cm,1cm)}]");
                    sb.AppendLine($@"    \coordinate (A) at (0,0,0); \coordinate (B) at ({v1},0,0);");
                    sb.AppendLine($@"    \coordinate (C) at ({v1},{v1},0); \coordinate (D) at (0,{v1},0);");
                    sb.AppendLine($@"    \coordinate (A1) at (0,0,{v1}); \coordinate (B1) at ({v1},0,{v1});");
                    sb.AppendLine($@"    \coordinate (C1) at ({v1},{v1},{v1}); \coordinate (D1) at (0,{v1},{v1});");
                    sb.AppendLine(@"    \draw (A)--(B)--(C); \draw[dashed] (C)--(D)--(A);");
                    sb.AppendLine(@"    \draw (A)--(A1); \draw (B)--(B1); \draw (C)--(C1);");
                    sb.AppendLine(@"    \draw[dashed] (D)--(D1);");
                    sb.AppendLine(@"    \draw (A1)--(B1)--(C1)--(D1)--cycle;");
                    double halfC = Math.Round(v1 / 2.0, 2);
                    sb.AppendLine($@"    \coordinate (I) at ({halfC},{halfC},{halfC}); \fill (I) circle (1.2pt);");
                    sb.AppendLine(@"  \end{scope}");
                    sb.AppendLine(@"  \node[right=2pt of I] {$I$};");
                    double rCirc = Math.Round(v1 * 0.866, 2);
                    sb.AppendLine($@"  \draw[blue, thick] (I) circle ({rCirc}cm);");
                    sb.AppendLine($@"  \draw[blue] ([xshift=-{rCirc}cm] I) arc (180:360:{rCirc}cm and {Math.Round(rCirc * 0.35, 2)}cm);");
                    sb.AppendLine($@"  \draw[blue, dashed] ([xshift=-{rCirc}cm] I) arc (180:0:{rCirc}cm and {Math.Round(rCirc * 0.35, 2)}cm);");
                    sb.Append(@"\end{tikzpicture}");
                    break;

                case "sphere_in_cube":
                    sb.AppendLine(@"\begin{tikzpicture}[scale=1.2, thick]");
                    sb.AppendLine(@"  \begin{scope}[x={(1cm,0cm)}, y={(0.5cm,0.3cm)}, z={(0cm,1cm)}]");
                    sb.AppendLine($@"    \coordinate (A) at (0,0,0); \coordinate (B) at ({v1},0,0);");
                    sb.AppendLine($@"    \coordinate (C) at ({v1},{v1},0); \coordinate (D) at (0,{v1},0);");
                    sb.AppendLine($@"    \coordinate (A1) at (0,0,{v1}); \coordinate (B1) at ({v1},0,{v1});");
                    sb.AppendLine($@"    \coordinate (C1) at ({v1},{v1},{v1}); \coordinate (D1) at (0,{v1},{v1});");
                    sb.AppendLine(@"    \draw (A)--(B)--(C); \draw[dashed] (C)--(D)--(A);");
                    sb.AppendLine(@"    \draw (A)--(A1); \draw (B)--(B1); \draw (C)--(C1);");
                    sb.AppendLine(@"    \draw[dashed] (D)--(D1);");
                    sb.AppendLine(@"    \draw (A1)--(B1)--(C1)--(D1)--cycle;");
                    double halfCi = Math.Round(v1 / 2.0, 2);
                    sb.AppendLine($@"    \coordinate (I) at ({halfCi},{halfCi},{halfCi}); \fill (I) circle (1.2pt);");
                    sb.AppendLine(@"  \end{scope}");
                    sb.AppendLine(@"  \node[right=2pt of I] {$I$};");
                    double rIn = Math.Round(v1 / 2.0, 2);
                    sb.AppendLine($@"  \draw[blue, thick] (I) circle ({rIn}cm);");
                    sb.AppendLine($@"  \draw[blue] ([xshift=-{rIn}cm] I) arc (180:360:{rIn}cm and {Math.Round(rIn * 0.35, 2)}cm);");
                    sb.AppendLine($@"  \draw[blue, dashed] ([xshift=-{rIn}cm] I) arc (180:0:{rIn}cm and {Math.Round(rIn * 0.35, 2)}cm);");
                    sb.Append(@"\end{tikzpicture}");
                    break;

                case "sphere_circum_pyramid":
                    sb.AppendLine(@"\begin{tikzpicture}[scale=1.2, thick]");
                    sb.AppendLine(@"  \begin{scope}[x={(1cm,0cm)}, y={(0.5cm,0.3cm)}, z={(0cm,1cm)}]");
                    sb.AppendLine(@"    \coordinate[label=below left:$A$] (A) at (0,0,0);");
                    sb.AppendLine($@"    \coordinate[label=below right:$B$] (B) at ({v1},0,0);");
                    sb.AppendLine($@"    \coordinate[label=right:$C$] (C) at ({v1},{v1},0);");
                    sb.AppendLine($@"    \coordinate[label=above left:$D$] (D) at (0,{v1},0);");
                    double hCp = Math.Round(v1 / 2.0, 2);
                    sb.AppendLine($@"    \coordinate[label=above:$S$] (S) at ({hCp},{hCp},{v2});");
                    sb.AppendLine($@"    \coordinate (H) at ({hCp},{hCp},0);");
                    sb.AppendLine($@"    \coordinate (I) at ({hCp},{hCp},{Math.Round(v2 * 0.4, 2)});");
                    sb.AppendLine(@"    \draw (A)--(B)--(C); \draw[dashed] (C)--(D)--(A);");
                    sb.AppendLine(@"    \draw (S)--(A) (S)--(B) (S)--(C); \draw[dashed] (S)--(D) (S)--(H);");
                    sb.AppendLine(@"    \fill (H) circle (1pt) node[below right] {$H$};");
                    sb.AppendLine(@"    \fill (I) circle (1.2pt) node[right] {$I$};");
                    sb.AppendLine(@"  \end{scope}");
                    double rCp = Math.Round(v2 * 0.55, 2);
                    sb.AppendLine($@"  \draw[blue, thick] (I) circle ({rCp}cm);");
                    sb.AppendLine($@"  \draw[blue] ([xshift=-{rCp}cm] I) arc (180:360:{rCp}cm and {Math.Round(rCp * 0.35, 2)}cm);");
                    sb.AppendLine($@"  \draw[blue, dashed] ([xshift=-{rCp}cm] I) arc (180:0:{rCp}cm and {Math.Round(rCp * 0.35, 2)}cm);");
                    sb.Append(@"\end{tikzpicture}");
                    break;

                case "octahedron":
                    double hOct = v2 > 0 ? v2 : 2.5;
                    double hCentO = Math.Round(v1 / 2.0, 2);
                    sb.AppendLine(@"\begin{tikzpicture}[scale=1.2, thick,");
                    sb.AppendLine(@"    x={(1cm,0cm)}, y={(0.5cm,0.3cm)}, z={(0cm,1cm)}]");
                    sb.AppendLine(@"  \coordinate[label=below left:$A$] (A) at (0,0,0);");
                    sb.AppendLine($@"  \coordinate[label=below right:$B$] (B) at ({v1},0,0);");
                    sb.AppendLine($@"  \coordinate[label=right:$C$] (C) at ({v1},{v1},0);");
                    sb.AppendLine($@"  \coordinate[label=above left:$D$] (D) at (0,{v1},0);");
                    sb.AppendLine($@"  \coordinate[label=above:$S$] (S) at ({hCentO},{hCentO},{hOct});");
                    sb.AppendLine($@"  \coordinate[label=below:$S'$] (S1) at ({hCentO},{hCentO},-{hOct});");
                    sb.AppendLine(@"  \draw (A)--(B)--(C); \draw[dashed] (C)--(D)--(A);");
                    sb.AppendLine(@"  \draw (S)--(A) (S)--(B) (S)--(C); \draw[dashed] (S)--(D);");
                    sb.AppendLine(@"  \draw (S1)--(A) (S1)--(B) (S1)--(C); \draw[dashed] (S1)--(D);");
                    sb.Append(@"\end{tikzpicture}");
                    break;

                // Graphs
                case "graph_quad":
                    sb.AppendLine(@"\begin{tikzpicture}");
                    sb.AppendLine(@"\begin{axis}[");
                    sb.AppendLine(@"  axis lines=center, xlabel={$x$}, ylabel={$y$},");
                    sb.AppendLine(@"  xmin=-4, xmax=5, ymin=-5, ymax=6,");
                    sb.AppendLine(@"  grid=major, grid style={gray!30},");
                    sb.AppendLine(@"  width=9cm, height=7cm, samples=100,");
                    sb.AppendLine(@"]");
                    sb.AppendLine($@"  \addplot[blue, very thick, domain=-3:4] {{{p1}*x^2 + {p2}*x + ({p3})}};");
                    sb.AppendLine($@"  \addlegendentry{{$y = {p1}x^2 + ({p2})x + ({p3})$}}");
                    sb.AppendLine(@"\end{axis}");
                    sb.Append(@"\end{tikzpicture}");
                    break;

                case "graph_cubic":
                    sb.AppendLine(@"\begin{tikzpicture}");
                    sb.AppendLine(@"\begin{axis}[");
                    sb.AppendLine(@"  axis lines=center, xlabel={$x$}, ylabel={$y$},");
                    sb.AppendLine(@"  xmin=-3, xmax=4, ymin=-5, ymax=7,");
                    sb.AppendLine(@"  grid=major, grid style={gray!30},");
                    sb.AppendLine(@"  width=9.5cm, height=7cm, samples=120,");
                    sb.AppendLine(@"]");
                    sb.AppendLine($@"  \addplot[blue, very thick, domain=-2.5:3.5] {{{p1}*x^3 + ({p2})*x^2 + ({p3})*x + ({p4})}};");
                    sb.AppendLine(@"\end{axis}");
                    sb.Append(@"\end{tikzpicture}");
                    break;

                case "graph_trig":
                    sb.AppendLine(@"\begin{tikzpicture}");
                    sb.AppendLine(@"\begin{axis}[");
                    sb.AppendLine(@"  axis lines=center, xlabel={$x$}, ylabel={$y$},");
                    sb.AppendLine(@"  xtick={-6.28, -3.14, 0, 3.14, 6.28},");
                    sb.AppendLine(@"  xticklabels={$-2\pi$, $-\pi$, $0$, $\pi$, $2\pi$},");
                    sb.AppendLine(@"  xmin=-7, xmax=7, ymin=-3.5, ymax=3.5,");
                    sb.AppendLine(@"  grid=major, grid style={gray!30},");
                    sb.AppendLine(@"  width=10.5cm, height=6cm, samples=200,");
                    sb.AppendLine(@"]");
                    sb.AppendLine($@"  \addplot[blue, very thick, domain=-6.5:6.5] {{{v1}*sin(deg({v2}*x))}};");
                    sb.AppendLine($@"  \addlegendentry{{$y = {v1}\sin({v2}x)$}}");
                    sb.AppendLine(@"\end{axis}");
                    sb.Append(@"\end{tikzpicture}");
                    break;

                // Charts
                case "chart_bar":
                    sb.AppendLine(@"\begin{tikzpicture}");
                    sb.AppendLine(@"\begin{axis}[");
                    sb.AppendLine(@"  ybar, ymin=0,");
                    sb.AppendLine(@"  ylabel={Số lượng},");
                    sb.AppendLine(@"  symbolic x coords={Lớp A, Lớp B, Lớp C, Lớp D},");
                    sb.AppendLine(@"  xtick=data,");
                    sb.AppendLine(@"  nodes near coords,");
                    sb.AppendLine(@"  bar width=18pt, width=9cm, height=6.5cm,");
                    sb.AppendLine(@"]");
                    sb.AppendLine(@"  \addplot[fill=cyan!60!blue] coordinates {(Lớp A,25) (Lớp B,40) (Lớp C,18) (Lớp D,32)};");
                    sb.AppendLine(@"\end{axis}");
                    sb.Append(@"\end{tikzpicture}");
                    break;

                case "tab_cubic":
                    sb.AppendLine(@"\begin{tikzpicture}");
                    sb.AppendLine(@"\tkzTabInit[lgt=1.5,espcl=2.5]");
                    sb.AppendLine(@" {$x$ / 1, $f'(x)$ / 1, $f(x)$ / 2}");
                    sb.AppendLine(@" {$-\infty$, $0$, $2$, $+\infty$}");
                    sb.AppendLine(@"\tkzTabLine{,+,0,-,0,+,}");
                    sb.AppendLine(@"\tkzTabVar{- / $-\infty$, + / $2$, - / $-2$, + / $+\infty$}");
                    sb.Append(@"\end{tikzpicture}");
                    break;

                default:
                    sb.AppendLine(@"\begin{tikzpicture}[scale=1, thick]");
                    sb.AppendLine(@"  \draw (0,0) rectangle (4,3);");
                    sb.Append(@"\end{tikzpicture}");
                    break;
            }

            return sb.ToString();
        }

        private void BtnPreviewCode_Click(object sender, RoutedEventArgs e)
        {
            RegenerateCode();
        }

        private void BtnInsert_Click(object sender, RoutedEventArgs e)
        {
            GeneratedTikzCode = TxtResultCode.Text.Trim();
            DialogResult = true;
            Close();
        }

        private void BtnCancel_Click(object sender, RoutedEventArgs e)
        {
            DialogResult = false;
            Close();
        }
    }
}
