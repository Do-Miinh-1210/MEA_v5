using System;
using System.Globalization;
using System.Text;
using System.Text.RegularExpressions;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Media;

namespace MatrixExamAI.Desktop.Views
{
    public partial class TikzShapeBuilderDialog : Window
    {
        public string GeneratedTikzCode { get; private set; } = string.Empty;
        public bool AutoCompileRequested { get; private set; }
        private string _currentShapeTag = "tri_right";
        private bool _isInitializing = true;
        private string _selectedColor = "blue";
        private bool _enableFill = false;

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
                    TxtResultCode.Text = GenerateTikzCodeForShape("tri_right", "4", "3", "", "A,B,C", true, _selectedColor, _enableFill);
                    break;
                case 1: // 3D
                    CmbShapeType.Items.Add("Hình chóp S.ABCD");
                    CmbShapeType.Items.Add("Hình chóp tam giác");
                    CmbShapeType.Items.Add("Hình hộp chữ nhật");
                    CmbShapeType.SelectedIndex = 0;
                    TxtResultCode.Text = GenerateTikzCodeForShape("pyramid", "5", "4", "4", "S,A,B,C,D", true, _selectedColor, _enableFill);
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
                    TxtResultCode.Text = GenerateTikzCodeForShape("chart_bar", "3", "", "", "", false, _selectedColor, _enableFill);
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

        private void Color_MouseDown(object sender, System.Windows.Input.MouseButtonEventArgs e)
        {
            if (sender is Border b && b.Tag is string color)
            {
                _selectedColor = color;
                if (ColorBlue != null) ColorBlue.BorderBrush = color == "blue" ? Brushes.White : Brushes.Transparent;
                if (ColorRed != null) ColorRed.BorderBrush = color == "red" ? Brushes.White : Brushes.Transparent;
                if (ColorGreen != null) ColorGreen.BorderBrush = color == "teal" ? Brushes.White : Brushes.Transparent;
                if (ColorOrange != null) ColorOrange.BorderBrush = color == "orange" ? Brushes.White : Brushes.Transparent;
                if (ColorPurple != null) ColorPurple.BorderBrush = color == "purple" ? Brushes.White : Brushes.Transparent;
                if (ColorBlack != null) ColorBlack.BorderBrush = color == "black" ? (Brush)new BrushConverter().ConvertFrom("#94A3B8")! : Brushes.Transparent;
                RegenerateCode();
            }
        }

        private void ChkOption_Changed(object sender, RoutedEventArgs e)
        {
            if (_isInitializing) return;
            RegenerateCode();
        }

        private void ChkFillOption_Changed(object sender, RoutedEventArgs e)
        {
            if (_isInitializing) return;
            _enableFill = ChkFillOption?.IsChecked == true;
            RegenerateCode();
        }

        private void Param_TextChanged(object sender, TextChangedEventArgs e)
        {
            if (_isInitializing) return;
            RegenerateCode();
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
                // ================= 1. HÌNH HỌC PHẲNG 2D =================
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
                    ChkOption.Content = "Ký hiệu góc vuông tại A";
                    break;

                case "tri_equi":
                case "tri_iso":
                    LblParam1.Text = "Cạnh đáy a:"; TxtParam1.Text = "4";
                    LblParam2.Text = "Chiều cao h:"; TxtParam2.Text = "3.5";
                    GridParam3.Visibility = Visibility.Collapsed;
                    LblParam4.Text = "Đỉnh (A,B,C):"; TxtParam4.Text = "A,B,C";
                    ChkOption.Content = "Hiển thị đường cao";
                    break;

                case "tri_right_iso":
                    LblParam1.Text = "Cạnh góc vuông a:"; TxtParam1.Text = "4";
                    GridParam2.Visibility = Visibility.Collapsed;
                    GridParam3.Visibility = Visibility.Collapsed;
                    LblParam4.Text = "Đỉnh (A,B,C):"; TxtParam4.Text = "A,B,C";
                    ChkOption.Content = "Ký hiệu góc vuông và góc 45°";
                    break;

                case "tri_incircle":
                case "tri_circumcircle":
                    LblParam1.Text = "Cạnh đáy a:"; TxtParam1.Text = "5";
                    LblParam2.Text = "Chiều cao h:"; TxtParam2.Text = "4";
                    GridParam3.Visibility = Visibility.Collapsed;
                    LblParam4.Text = "Đỉnh & Tâm:"; TxtParam4.Text = "A,B,C,O";
                    ChkOption.Content = "Hiển thị tâm và bán kính đường tròn";
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
                case "trapezoid_iso":
                case "trapezoid_right":
                    LblParam1.Text = "Đáy lớn a:"; TxtParam1.Text = "6";
                    LblParam2.Text = "Đáy nhỏ b:"; TxtParam2.Text = "3";
                    LblParam3.Text = "Chiều cao h:"; TxtParam3.Text = "3.5";
                    LblParam4.Text = "Đỉnh (A,B,C,D):"; TxtParam4.Text = "A,B,C,D";
                    ChkOption.Content = "Hiển thị đường cao";
                    break;

                case "rhombus":
                    LblParam1.Text = "Đường chéo d1:"; TxtParam1.Text = "6";
                    LblParam2.Text = "Đường chéo d2:"; TxtParam2.Text = "4";
                    GridParam3.Visibility = Visibility.Collapsed;
                    LblParam4.Text = "Đỉnh (A,B,C,D):"; TxtParam4.Text = "A,B,C,D";
                    ChkOption.Content = "Ký hiệu hai đường chéo vuông góc";
                    break;

                case "pentagon_regular":
                case "hexagon_regular":
                    LblParam1.Text = "Bán kính ngoại R:"; TxtParam1.Text = "3";
                    GridParam2.Visibility = Visibility.Collapsed;
                    GridParam3.Visibility = Visibility.Collapsed;
                    LblParam4.Text = "Đỉnh:"; TxtParam4.Text = "A,B,C,D,E";
                    ChkOption.Content = "Hiển thị tâm O và các đường chéo";
                    break;

                case "star_5":
                    LblParam1.Text = "Bán kính ngoài R:"; TxtParam1.Text = "3";
                    LblParam2.Text = "Bán kính trong r:"; TxtParam2.Text = "1.2";
                    GridParam3.Visibility = Visibility.Collapsed;
                    LblParam4.Text = "Tâm:"; TxtParam4.Text = "O";
                    ChkOption.Content = "Vẽ cánh sao đối xứng";
                    break;

                case "segment":
                    LblParam1.Text = "Độ dài đoạn (cm):"; TxtParam1.Text = "5";
                    GridParam2.Visibility = Visibility.Collapsed;
                    GridParam3.Visibility = Visibility.Collapsed;
                    LblParam4.Text = "Hai đầu mút:"; TxtParam4.Text = "A,B";
                    ChkOption.Content = "Có mũi tên hướng dẫn";
                    break;

                // ================= 2. HÌNH KHÔNG GIAN 3D =================
                case "pyramid_sa_perp":
                    LblParam1.Text = "Cạnh đáy a:"; TxtParam1.Text = "5";
                    LblParam2.Text = "Chiều cao SA:"; TxtParam2.Text = "5";
                    GridParam3.Visibility = Visibility.Collapsed;
                    LblParam4.Text = "Đỉnh & Đáy:"; TxtParam4.Text = "S, A, B, C";
                    ChkOption.Content = "Ký hiệu SA ⟂ đáy";
                    break;

                case "pyramid_sab_perp":
                    LblParam1.Text = "Cạnh đáy a:"; TxtParam1.Text = "5";
                    LblParam2.Text = "Chiều cao SH:"; TxtParam2.Text = "5";
                    GridParam3.Visibility = Visibility.Collapsed;
                    LblParam4.Text = "Đỉnh, Chân cao & Đáy:"; TxtParam4.Text = "S, H, A, B, C";
                    ChkOption.Content = "Ký hiệu SH ⟂ AB";
                    break;

                case "pyramid_regular_tri":
                case "tetrahedron":
                    LblParam1.Text = "Cạnh đáy a:"; TxtParam1.Text = "4";
                    LblParam2.Text = "Chiều cao h:"; TxtParam2.Text = "4.5";
                    GridParam3.Visibility = Visibility.Collapsed;
                    LblParam4.Text = "Đỉnh & Đáy:"; TxtParam4.Text = "S, A, B, C";
                    ChkOption.Content = "Hiển thị tâm đáy và trục SO";
                    break;

                case "pyramid":
                case "pyramid_regular_quad":
                    LblParam1.Text = "Cạnh đáy a:"; TxtParam1.Text = "4.5";
                    LblParam2.Text = "Chiều cao h:"; TxtParam2.Text = "4.5";
                    GridParam3.Visibility = Visibility.Collapsed;
                    LblParam4.Text = "Đỉnh & Đáy:"; TxtParam4.Text = "S, A, B, C, D";
                    ChkOption.Content = "Hiển thị tâm O và chiều cao SO";
                    break;

                case "pyramid_sa_quad":
                case "pyramid_trapezoid":
                case "pyramid_sad_perp":
                    LblParam1.Text = "Cạnh đáy a:"; TxtParam1.Text = "4.5";
                    LblParam2.Text = "Chiều cao SA/SH:"; TxtParam2.Text = "4.5";
                    GridParam3.Visibility = Visibility.Collapsed;
                    LblParam4.Text = "Đỉnh & Đáy:"; TxtParam4.Text = "S, A, B, C, D";
                    ChkOption.Content = "Ký hiệu đường cao ⟂ đáy";
                    break;

                case "pyramid_regular_penta":
                case "pyramid_regular_hexa":
                    LblParam1.Text = "Bán kính đáy R:"; TxtParam1.Text = "3";
                    LblParam2.Text = "Chiều cao h:"; TxtParam2.Text = "4.5";
                    GridParam3.Visibility = Visibility.Collapsed;
                    LblParam4.Text = "Đỉnh & Tâm:"; TxtParam4.Text = "S, O";
                    ChkOption.Content = "Hiển thị trục SO";
                    break;

                case "pyramid_frustum":
                case "pyramid_tri_frustum":
                    LblParam1.Text = "Đáy lớn a:"; TxtParam1.Text = "4";
                    LblParam2.Text = "Đáy nhỏ a':"; TxtParam2.Text = "2";
                    LblParam3.Text = "Chiều cao h:"; TxtParam3.Text = "3.5";
                    LblParam4.Text = "Đỉnh hai đáy:"; TxtParam4.Text = "A,B,C,D,A',B',C',D'";
                    ChkOption.Visibility = Visibility.Collapsed;
                    break;

                case "prism_triangular":
                case "prism_tri_oblique":
                    LblParam1.Text = "Cạnh đáy a:"; TxtParam1.Text = "3.5";
                    LblParam2.Text = "Chiều cao h:"; TxtParam2.Text = "4";
                    GridParam3.Visibility = Visibility.Collapsed;
                    LblParam4.Text = "Đỉnh hai đáy:"; TxtParam4.Text = "A,B,C,A',B',C'";
                    ChkOption.Content = "Hiển thị cạnh bên song song";
                    break;

                case "prism_quad":
                case "prism_quad_oblique":
                case "cuboid":
                case "cube":
                    LblParam1.Text = "Kích thước a:"; TxtParam1.Text = "4";
                    LblParam2.Text = "Kích thước b:"; TxtParam2.Text = "3";
                    LblParam3.Text = "Chiều cao h:"; TxtParam3.Text = "3.5";
                    LblParam4.Text = "Đỉnh hai đáy:"; TxtParam4.Text = "A,B,C,D,A',B',C',D'";
                    ChkOption.Content = "Hiển thị đường chéo";
                    break;

                case "prism_penta":
                case "prism_hexa":
                case "octahedron":
                    LblParam1.Text = "Cạnh đáy a:"; TxtParam1.Text = "3";
                    LblParam2.Text = "Chiều cao h:"; TxtParam2.Text = "4.5";
                    GridParam3.Visibility = Visibility.Collapsed;
                    LblParam4.Text = "Nhãn đỉnh:"; TxtParam4.Text = "A, B, C, D, E";
                    ChkOption.Content = "Hiển thị trục thẳng đứng";
                    break;

                // ================= 3. MẶT TRÒN XOAY =================
                case "cylinder":
                case "cylinder_section":
                    LblParam1.Text = "Bán kính đáy R:"; TxtParam1.Text = "2.2";
                    LblParam2.Text = "Chiều cao h:"; TxtParam2.Text = "4";
                    GridParam3.Visibility = Visibility.Collapsed;
                    LblParam4.Text = "Hai tâm:"; TxtParam4.Text = "O, O'";
                    ChkOption.Content = "Hiển thị trục OO' và bán kính r";
                    break;

                case "cone":
                case "cone_down":
                    LblParam1.Text = "Bán kính đáy R:"; TxtParam1.Text = "2.4";
                    LblParam2.Text = "Chiều cao h:"; TxtParam2.Text = "4.2";
                    GridParam3.Visibility = Visibility.Collapsed;
                    LblParam4.Text = "Đỉnh & Tâm:"; TxtParam4.Text = "S, O";
                    ChkOption.Content = "Hiển thị đường sinh l";
                    break;

                case "cone_frustum":
                    LblParam1.Text = "Bán kính lớn R:"; TxtParam1.Text = "2.5";
                    LblParam2.Text = "Bán kính nhỏ r:"; TxtParam2.Text = "1.2";
                    LblParam3.Text = "Chiều cao h:"; TxtParam3.Text = "3";
                    LblParam4.Text = "Hai tâm:"; TxtParam4.Text = "O, O'";
                    ChkOption.Content = "Hiển thị trục OO'";
                    break;

                case "sphere":
                case "sphere_circle_section":
                    LblParam1.Text = "Bán kính cầu R:"; TxtParam1.Text = "2.5";
                    LblParam2.Text = "Khoảng cách cắt d:"; TxtParam2.Text = "1.5";
                    GridParam3.Visibility = Visibility.Collapsed;
                    LblParam4.Text = "Tâm cầu:"; TxtParam4.Text = "O";
                    ChkOption.Content = "Hiển thị đường tròn lớn xích đạo";
                    break;

                case "cylinder_in_cone":
                case "cylinder_in_sphere":
                case "cone_in_sphere":
                    LblParam1.Text = "Bán kính ngoài R:"; TxtParam1.Text = "3";
                    LblParam2.Text = "Chiều cao ngoài H:"; TxtParam2.Text = "4.5";
                    LblParam3.Text = "Bán kính/chiều cao trong:"; TxtParam3.Text = "1.8";
                    LblParam4.Text = "Đỉnh & Tâm:"; TxtParam4.Text = "S, O";
                    ChkOption.Content = "Tô màu làm nổi bật khối nội tiếp";
                    break;

                case "solid_rev_ox":
                case "solid_rev_oz":
                    LblParam1.Text = "Bán kính đầu r1:"; TxtParam1.Text = "1.5";
                    LblParam2.Text = "Bán kính đuôi r2:"; TxtParam2.Text = "2.8";
                    LblParam3.Text = "Chiều dài trục L:"; TxtParam3.Text = "4";
                    LblParam4.Text = "Trục tọa độ:"; TxtParam4.Text = "x, y, z";
                    ChkOption.Content = "Hiển thị trục quay và mũi tên xoay";
                    break;

                // ================= 4. ĐƯỜNG TRÒN & CONIC =================
                case "circle":
                case "circle_diameter":
                case "circle_two_tangents":
                case "circle_inscribed_quad":
                case "circle_tangent_ext":
                    LblParam1.Text = "Bán kính R:"; TxtParam1.Text = "2.5";
                    GridParam2.Visibility = Visibility.Collapsed;
                    GridParam3.Visibility = Visibility.Collapsed;
                    LblParam4.Text = "Tâm & Tiếp điểm:"; TxtParam4.Text = "O, A, B";
                    ChkOption.Content = "Hiển thị tiếp tuyến và bán kính";
                    break;

                case "ellipse":
                case "ellipse_foci":
                    LblParam1.Text = "Bán trục lớn a:"; TxtParam1.Text = "3";
                    LblParam2.Text = "Bán trục nhỏ b:"; TxtParam2.Text = "1.8";
                    GridParam3.Visibility = Visibility.Collapsed;
                    LblParam4.Text = "Tâm & Tiêu điểm:"; TxtParam4.Text = "O, F1, F2";
                    ChkOption.Content = "Hiển thị hai tiêu điểm F1, F2";
                    break;

                case "hyperbola":
                    LblParam1.Text = "Bán trục thực a:"; TxtParam1.Text = "2";
                    LblParam2.Text = "Bán trục ảo b:"; TxtParam2.Text = "1.5";
                    GridParam3.Visibility = Visibility.Collapsed;
                    LblParam4.Text = "Tâm:"; TxtParam4.Text = "O";
                    ChkOption.Content = "Hiển thị 2 đường tiệm cận y = ±(b/a)x";
                    break;

                case "parabola_vert":
                case "parabola_horiz":
                    LblParam1.Text = "Hệ số a (y = ax²):"; TxtParam1.Text = "0.5";
                    GridParam2.Visibility = Visibility.Collapsed;
                    GridParam3.Visibility = Visibility.Collapsed;
                    LblParam4.Text = "Đỉnh & Trục:"; TxtParam4.Text = "O, x, y";
                    ChkOption.Content = "Hiển thị tiêu điểm F và đường chuẩn Δ";
                    break;

                // ================= 5. ĐỒ THỊ & BBT =================
                case "graph_quad":
                    LblParam1.Text = "Hệ số a, b, c:"; TxtParam1.Text = "1, -2, -1";
                    GridParam2.Visibility = Visibility.Collapsed;
                    GridParam3.Visibility = Visibility.Collapsed;
                    LblParam4.Text = "Đỉnh I:"; TxtParam4.Text = "I(1;-2)";
                    ChkOption.Content = "Hiển thị trục đối xứng và đỉnh I";
                    break;

                case "graph_cubic":
                    LblParam1.Text = "Hệ số a, b, c, d:"; TxtParam1.Text = "1, 0, -3, 1";
                    GridParam2.Visibility = Visibility.Collapsed;
                    GridParam3.Visibility = Visibility.Collapsed;
                    LblParam4.Text = "Điểm uốn:"; TxtParam4.Text = "U(0;1)";
                    ChkOption.Content = "Hiển thị 2 điểm cực trị và điểm uốn";
                    break;

                case "graph_quartic":
                    LblParam1.Text = "Hệ số a, b, c:"; TxtParam1.Text = "1, -2, -1";
                    GridParam2.Visibility = Visibility.Collapsed;
                    GridParam3.Visibility = Visibility.Collapsed;
                    LblParam4.Text = "Tên hàm:"; TxtParam4.Text = "y = x^4 - 2x^2 - 1";
                    ChkOption.Content = "Hiển thị 3 điểm cực trị";
                    break;

                case "graph_rational":
                case "graph_rational_21":
                    LblParam1.Text = "Tử số a,b:"; TxtParam1.Text = "2, 1";
                    LblParam2.Text = "Mẫu số c,d:"; TxtParam2.Text = "1, -1";
                    GridParam3.Visibility = Visibility.Collapsed;
                    LblParam4.Text = "Tâm đối xứng I:"; TxtParam4.Text = "I(1;2)";
                    ChkOption.Content = "Hiển thị tiệm cận đứng và tiệm cận ngang";
                    break;

                case "graph_trig":
                    LblParam1.Text = "Biên độ A:"; TxtParam1.Text = "2";
                    LblParam2.Text = "Tần số góc ω:"; TxtParam2.Text = "1";
                    GridParam3.Visibility = Visibility.Collapsed;
                    LblParam4.Text = "Tên hàm:"; TxtParam4.Text = "y = 2*sin(x)";
                    ChkOption.Content = "Chu kỳ T = 2π";
                    break;

                case "graph_log_exp":
                    LblParam1.Text = "Cơ số a:"; TxtParam1.Text = "2";
                    GridParam2.Visibility = Visibility.Collapsed;
                    GridParam3.Visibility = Visibility.Collapsed;
                    LblParam4.Text = "Tên hàm:"; TxtParam4.Text = "y = 2^x";
                    ChkOption.Content = "Vẽ cả đường y = x đối xứng";
                    break;

                case "graph_area_integral":
                    LblParam1.Text = "Cận dưới a:"; TxtParam1.Text = "0";
                    LblParam2.Text = "Cận trên b:"; TxtParam2.Text = "2";
                    GridParam3.Visibility = Visibility.Collapsed;
                    LblParam4.Text = "Hàm số f(x):"; TxtParam4.Text = "-x^2 + 2*x";
                    ChkOption.Content = "Tô màu miền diện tích S tích phân";
                    break;

                case "tab_cubic":
                case "tab_quartic":
                case "tab_rational":
                case "tab_rational_21":
                case "tab_sign_quad":
                    LblParam1.Text = "Điểm cực trị / nghiệm:"; TxtParam1.Text = "1, 3";
                    LblParam2.Text = "Giá trị cực trị:"; TxtParam2.Text = "4, -2";
                    GridParam3.Visibility = Visibility.Collapsed;
                    LblParam4.Text = "Tên hàm:"; TxtParam4.Text = "y";
                    ChkOption.Content = "Định dạng tkz-tab chuẩn THPT";
                    break;

                // ================= 6. BÀI TOÁN THỰC TẾ =================
                case "real_bridge_parabola":
                    LblParam1.Text = "Chiều dài nhịp L (m):"; TxtParam1.Text = "120";
                    LblParam2.Text = "Chiều cao tháp h (m):"; TxtParam2.Text = "35";
                    GridParam3.Visibility = Visibility.Collapsed;
                    LblParam4.Text = "Tên cầu:"; TxtParam4.Text = "Cầu treo Parabol";
                    ChkOption.Content = "Hiển thị mặt nước và hệ dây văng";
                    break;

                case "real_lighthouse":
                    LblParam1.Text = "Chiều cao hải đăng h:"; TxtParam1.Text = "40";
                    LblParam2.Text = "Khoảng cách tàu d:"; TxtParam2.Text = "120";
                    GridParam3.Visibility = Visibility.Collapsed;
                    LblParam4.Text = "Hải đăng & Tàu:"; TxtParam4.Text = "H, A, B";
                    ChkOption.Content = "Hiển thị tia nhìn và góc nâng";
                    break;

                case "real_basketball":
                    LblParam1.Text = "Khoảng cách ném d:"; TxtParam1.Text = "5";
                    LblParam2.Text = "Chiều cao rổ h:"; TxtParam2.Text = "3.05";
                    GridParam3.Visibility = Visibility.Collapsed;
                    LblParam4.Text = "Vận động viên & Rổ:"; TxtParam4.Text = "M, R";
                    ChkOption.Content = "Hiển thị quỹ đạo ném Parabol";
                    break;

                case "real_tent_pyramid":
                    LblParam1.Text = "Cạnh đáy lều a:"; TxtParam1.Text = "3";
                    LblParam2.Text = "Chiều cao chóp h:"; TxtParam2.Text = "2.5";
                    GridParam3.Visibility = Visibility.Collapsed;
                    LblParam4.Text = "Đỉnh & Cọc:"; TxtParam4.Text = "S, A, B, C";
                    ChkOption.Content = "Lều trại du lịch hình chóp";
                    break;

                case "real_hourglass":
                    LblParam1.Text = "Bán kính nón R:"; TxtParam1.Text = "2.5";
                    LblParam2.Text = "Chiều cao mỗi nón h:"; TxtParam2.Text = "3.5";
                    GridParam3.Visibility = Visibility.Collapsed;
                    LblParam4.Text = "Tâm đối xứng:"; TxtParam4.Text = "O";
                    ChkOption.Content = "Hai khối nón đối đỉnh đối xứng";
                    break;

                default:
                    LblParam1.Text = "Kích thước 1:"; TxtParam1.Text = "4";
                    LblParam2.Text = "Kích thước 2:"; TxtParam2.Text = "3";
                    GridParam3.Visibility = Visibility.Collapsed;
                    LblParam4.Text = "Tên đỉnh:"; TxtParam4.Text = "A, B, C";
                    ChkOption.Content = "Hiển thị phụ";
                    break;
            }
        }

        private void RegenerateCode()
        {
            if (TxtResultCode == null) return;

            string p1 = TxtParam1?.Text?.Trim() ?? "4";
            string p2 = TxtParam2?.Text?.Trim() ?? "3";
            string p3 = TxtParam3?.Text?.Trim() ?? "2";
            string p4 = TxtParam4?.Text?.Trim() ?? "A,B,C,D";
            bool opt = ChkOption?.IsChecked ?? true;

            TxtResultCode.Text = GenerateTikzCodeForShape(_currentShapeTag, p1, p2, p3, p4, opt, _selectedColor, _enableFill);
        }

        public static string GenerateTikzCodeForShape(string tag, string p1, string p2, string p3, string p4, bool opt)
        {
            return GenerateTikzCodeForShape(tag, p1, p2, p3, p4, opt, "blue", false);
        }

        public static string GenerateTikzCodeForShape(string tag, string p1, string p2, string p3, string p4, bool opt, string color, bool fill)
        {
            var prevCulture = Thread.CurrentThread.CurrentCulture;
            var prevUiCulture = Thread.CurrentThread.CurrentUICulture;
            try
            {
                Thread.CurrentThread.CurrentCulture = CultureInfo.InvariantCulture;
                Thread.CurrentThread.CurrentUICulture = CultureInfo.InvariantCulture;
                CultureInfo.CurrentCulture = CultureInfo.InvariantCulture;
                CultureInfo.CurrentUICulture = CultureInfo.InvariantCulture;

                var sb = new StringBuilder();
                double.TryParse(p1?.Trim().Replace(',', '.'), NumberStyles.Any, CultureInfo.InvariantCulture, out double v1);
                double.TryParse(p2?.Trim().Replace(',', '.'), NumberStyles.Any, CultureInfo.InvariantCulture, out double v2);
                double.TryParse(p3?.Trim().Replace(',', '.'), NumberStyles.Any, CultureInfo.InvariantCulture, out double v3);
                if (v1 <= 0) v1 = 4;
                if (v2 <= 0) v2 = 3;

                string drawOpt = color switch
                {
                    "red" => fill ? "thick, red, fill=red!15" : "thick, red",
                    "teal" => fill ? "thick, teal, fill=teal!15" : "thick, teal",
                    "orange" => fill ? "thick, orange, fill=orange!15" : "thick, orange",
                    "purple" => fill ? "thick, purple, fill=purple!15" : "thick, purple",
                    "black" => fill ? "thick, black, fill=gray!15" : "thick, black",
                    _ => fill ? "thick, blue, fill=blue!15" : "thick, blue"
                };

            switch (tag)
            {
                // ================= 1. HÌNH HỌC PHẲNG 2D =================
                case "tri_general":
                    sb.AppendLine($@"\begin{{tikzpicture}}[scale=1, {drawOpt}]");
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
                    sb.AppendLine($@"\begin{{tikzpicture}}[scale=1, {drawOpt}]");
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
                    sb.AppendLine($@"\begin{{tikzpicture}}[scale=1, {drawOpt}]");
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
                case "tri_right_iso":
                    double hIso = tag == "tri_right_iso" ? Math.Round(v1 / 2.0, 2) : v2;
                    sb.AppendLine($@"\begin{{tikzpicture}}[scale=1, {drawOpt}]");
                    sb.AppendLine(@"  \coordinate[label=below left:$A$] (A) at (0,0);");
                    sb.AppendLine($@"  \coordinate[label=below right:$B$] (B) at ({v1},0);");
                    sb.AppendLine($@"  \coordinate[label=above:$C$] (C) at ({Math.Round(v1 / 2.0, 2)},{hIso});");
                    sb.AppendLine(@"  \draw (A)--(B)--(C)--cycle;");
                    if (opt)
                    {
                        sb.AppendLine($@"  \coordinate[label=below:$H$] (H) at ({Math.Round(v1 / 2.0, 2)},0);");
                        sb.AppendLine(@"  \draw[dashed] (C)--(H);");
                    }
                    sb.Append(@"\end{tikzpicture}");
                    break;

                case "tri_incircle":
                    sb.AppendLine($@"\begin{{tikzpicture}}[scale=1, {drawOpt}]");
                    sb.AppendLine(@"  \coordinate[label=below left:$A$] (A) at (0,0);");
                    sb.AppendLine($@"  \coordinate[label=below right:$B$] (B) at ({v1},0);");
                    sb.AppendLine($@"  \coordinate[label=above:$C$] (C) at ({Math.Round(v1 * 0.45, 2)},{v2});");
                    sb.AppendLine(@"  \draw (A)--(B)--(C)--cycle;");
                    sb.AppendLine($@"  \draw ({Math.Round(v1 * 0.45, 2)},{Math.Round(v2 * 0.35, 2)}) circle ({Math.Round(v2 * 0.32, 2)});");
                    sb.AppendLine($@"  \filldraw ({Math.Round(v1 * 0.45, 2)},{Math.Round(v2 * 0.35, 2)}) circle (1.5pt) node[right] {{$I$}};");
                    sb.Append(@"\end{tikzpicture}");
                    break;

                case "tri_circumcircle":
                    sb.AppendLine($@"\begin{{tikzpicture}}[scale=1, {drawOpt}]");
                    sb.AppendLine(@"  \coordinate[label=below left:$A$] (A) at (0,0);");
                    sb.AppendLine($@"  \coordinate[label=below right:$B$] (B) at ({v1},0);");
                    sb.AppendLine($@"  \coordinate[label=above:$C$] (C) at ({Math.Round(v1 * 0.5, 2)},{v2});");
                    sb.AppendLine(@"  \draw (A)--(B)--(C)--cycle;");
                    sb.AppendLine($@"  \draw ({Math.Round(v1 * 0.5, 2)},{Math.Round(v2 * 0.4, 2)}) circle ({Math.Round(v1 * 0.55, 2)});");
                    sb.AppendLine($@"  \filldraw ({Math.Round(v1 * 0.5, 2)},{Math.Round(v2 * 0.4, 2)}) circle (1.5pt) node[below] {{$O$}};");
                    sb.Append(@"\end{tikzpicture}");
                    break;

                case "square":
                case "rect":
                    double hR = tag == "square" ? v1 : v2;
                    sb.AppendLine($@"\begin{{tikzpicture}}[scale=1, {drawOpt}]");
                    sb.AppendLine(@"  \coordinate[label=below left:$A$] (A) at (0,0);");
                    sb.AppendLine($@"  \coordinate[label=below right:$B$] (B) at ({v1},0);");
                    sb.AppendLine($@"  \coordinate[label=above right:$C$] (C) at ({v1},{hR});");
                    sb.AppendLine($@"  \coordinate[label=above left:$D$] (D) at (0,{hR});");
                    sb.AppendLine(@"  \draw (A)--(B)--(C)--(D)--cycle;");
                    if (opt)
                    {
                        sb.AppendLine(@"  \draw[dashed] (A)--(C) (B)--(D);");
                    }
                    sb.Append(@"\end{tikzpicture}");
                    break;

                case "parallelogram":
                    double skew = v3 > 0 ? v3 : 1.5;
                    sb.AppendLine($@"\begin{{tikzpicture}}[scale=1, {drawOpt}]");
                    sb.AppendLine(@"  \coordinate[label=below left:$A$] (A) at (0,0);");
                    sb.AppendLine($@"  \coordinate[label=below right:$B$] (B) at ({v1},0);");
                    sb.AppendLine($@"  \coordinate[label=above right:$C$] (C) at ({Math.Round(v1 + skew, 2)},{v2});");
                    sb.AppendLine($@"  \coordinate[label=above left:$D$] (D) at ({skew},{v2});");
                    sb.AppendLine(@"  \draw (A)--(B)--(C)--(D)--cycle;");
                    sb.Append(@"\end{tikzpicture}");
                    break;

                case "trapezoid":
                case "trapezoid_iso":
                case "trapezoid_right":
                    double off = tag == "trapezoid_right" ? 0 : Math.Round((v1 - v2) / 2.0, 2);
                    double hTr = v3 > 0 ? v3 : 3.5;
                    sb.AppendLine($@"\begin{{tikzpicture}}[scale=1, {drawOpt}]");
                    sb.AppendLine(@"  \coordinate[label=below left:$A$] (A) at (0,0);");
                    sb.AppendLine($@"  \coordinate[label=below right:$B$] (B) at ({v1},0);");
                    sb.AppendLine($@"  \coordinate[label=above right:$C$] (C) at ({Math.Round(v1 - off, 2)},{hTr});");
                    sb.AppendLine($@"  \coordinate[label=above left:$D$] (D) at ({off},{hTr});");
                    sb.AppendLine(@"  \draw (A)--(B)--(C)--(D)--cycle;");
                    if (opt && tag == "trapezoid_right")
                    {
                        sb.AppendLine(@"  \draw (A) +(0.3,0) -- +(0.3,0.3) -- +(0,0.3);");
                        sb.AppendLine(@"  \draw (D) +(0.3,0) -- +(0.3,-0.3) -- +(0,-0.3);");
                    }
                    sb.Append(@"\end{tikzpicture}");
                    break;

                case "rhombus":
                    double rx = v1 / 2.0;
                    double ry = v2 / 2.0;
                    sb.AppendLine($@"\begin{{tikzpicture}}[scale=1, {drawOpt}]");
                    sb.AppendLine($@"  \coordinate[label=left:$A$] (A) at ({-rx},0);");
                    sb.AppendLine($@"  \coordinate[label=below:$B$] (B) at (0,{-ry});");
                    sb.AppendLine($@"  \coordinate[label=right:$C$] (C) at ({rx},0);");
                    sb.AppendLine($@"  \coordinate[label=above:$D$] (D) at (0,{ry});");
                    sb.AppendLine(@"  \draw (A)--(B)--(C)--(D)--cycle;");
                    if (opt)
                    {
                        sb.AppendLine(@"  \draw[dashed] (A)--(C) (B)--(D);");
                        sb.AppendLine(@"  \draw (0,0) +(0.2,0) -- +(0.2,0.2) -- +(0,0.2);");
                    }
                    sb.Append(@"\end{tikzpicture}");
                    break;

                case "pentagon_regular":
                    sb.AppendLine($@"\begin{{tikzpicture}}[scale=1, {drawOpt}]");
                    sb.AppendLine($@"  \foreach \i/\lab in {{1/A, 2/B, 3/C, 4/D, 5/E}} {{");
                    sb.AppendLine($@"    \coordinate (P\i) at ({{\i*72+18}}:{v1});");
                    sb.AppendLine($@"    \filldraw (P\i) circle (1.2pt) node[shift={{({{\i*72+18}}:9pt)}}] {{$\lab$}};");
                    sb.AppendLine(@"  }");
                    sb.AppendLine(@"  \draw (P1)--(P2)--(P3)--(P4)--(P5)--cycle;");
                    sb.Append(@"\end{tikzpicture}");
                    break;

                case "hexagon_regular":
                    sb.AppendLine($@"\begin{{tikzpicture}}[scale=1, {drawOpt}]");
                    sb.AppendLine($@"  \foreach \i/\lab in {{1/A, 2/B, 3/C, 4/D, 5/E, 6/F}} {{");
                    sb.AppendLine($@"    \coordinate (P\i) at ({{\i*60}}:{v1});");
                    sb.AppendLine($@"    \filldraw (P\i) circle (1.2pt) node[shift={{({{\i*60}}:9pt)}}] {{$\lab$}};");
                    sb.AppendLine(@"  }");
                    sb.AppendLine(@"  \draw (P1)--(P2)--(P3)--(P4)--(P5)--(P6)--cycle;");
                    if (opt)
                    {
                        sb.AppendLine(@"  \draw[dashed] (P1)--(P4) (P2)--(P5) (P3)--(P6);");
                    }
                    sb.Append(@"\end{tikzpicture}");
                    break;

                case "star_5":
                    sb.AppendLine($@"\begin{{tikzpicture}}[scale=1, {drawOpt}]");
                    sb.AppendLine($@"  \draw (90:{v1}) -- (234:{v1}) -- (18:{v1}) -- (162:{v1}) -- (306:{v1}) -- cycle;");
                    sb.Append(@"\end{tikzpicture}");
                    break;

                case "segment":
                    sb.AppendLine(@"\begin{tikzpicture}[scale=1, thick]");
                    sb.AppendLine(@"  \coordinate[label=below left:$A$] (A) at (0,0);");
                    sb.AppendLine($@"  \coordinate[label=below right:$B$] (B) at ({v1},0);");
                    sb.AppendLine(@"  \draw[fill=blue] (A) circle (1.5pt) (B) circle (1.5pt);");
                    sb.AppendLine(opt ? @"  \draw[->,>=stealth,very thick] (A)--(B);" : @"  \draw[very thick] (A)--(B);");
                    sb.Append(@"\end{tikzpicture}");
                    break;

                // ================= 2. HÌNH KHÔNG GIAN 3D =================
                case "pyramid_sa_perp":
                    sb.AppendLine($@"\begin{{tikzpicture}}[declare function={{goc=-45; a={v1}; b=0.45*a; h={v2};}}, {drawOpt}]");
                    sb.AppendLine(@"  \path (0,0) coordinate (A)--+(0,h) coordinate (S)");
                    sb.AppendLine(@"  (a,0) coordinate (C) (goc:b) coordinate (B);");
                    sb.AppendLine(@"  \draw[dashed] (A)--(C);");
                    sb.AppendLine(@"  \draw (S)--(A)--(B)--(S)--(C)--(B);");
                    sb.AppendLine(@"  \foreach \p/\pos in {S/above,A/left,B/below,C/right}");
                    sb.AppendLine(@"    \filldraw (\p) circle (1.2pt) node[\pos] {$\p$};");
                    if (opt)
                    {
                        sb.AppendLine(@"  \draw (A) ++(0,0.3) -- ++(0.3,0) -- ++(0,-0.3);");
                    }
                    sb.Append(@"\end{tikzpicture}");
                    break;

                case "pyramid_sab_perp":
                    sb.AppendLine($@"\begin{{tikzpicture}}[declare function={{goc=-45; a={v1}; b=0.45*a; h={v2};}}, {drawOpt}]");
                    sb.AppendLine(@"  \path (0,0) coordinate (A) (a,0) coordinate (C) (goc:b) coordinate (B)");
                    sb.AppendLine(@"  ($(A)!.4!(B)$) coordinate (H)--+(0,h) coordinate (S);");
                    sb.AppendLine(@"  \draw[dashed] (A)--(C) (S)--(H);");
                    sb.AppendLine(@"  \draw (S)--(A)--(B)--(S)--(C)--(B);");
                    sb.AppendLine(@"  \foreach \p/\pos in {S/above,A/left,B/below,C/right,H/below left}");
                    sb.AppendLine(@"    \filldraw (\p) circle (1.2pt) node[\pos] {$\p$};");
                    sb.Append(@"\end{tikzpicture}");
                    break;

                case "pyramid_regular_tri":
                case "tetrahedron":
                    sb.AppendLine($@"\begin{{tikzpicture}}[declare function={{goc=-40; a={v1}; b=0.45*a; h={v2};}}, {drawOpt}]");
                    sb.AppendLine(@"  \path (0,0) coordinate (A) (a,0) coordinate (C) (goc:b) coordinate (B)");
                    sb.AppendLine(@"  ($(A)!0.33!(C)!0.5!(B)$) coordinate (O)--+(0,h) coordinate (S);");
                    sb.AppendLine(@"  \draw[dashed] (A)--(C) (S)--(O);");
                    sb.AppendLine(@"  \draw (S)--(A)--(B)--(S)--(C)--(B);");
                    sb.AppendLine(@"  \foreach \p/\pos in {S/above,A/left,B/below,C/right,O/below}");
                    sb.AppendLine(@"    \filldraw (\p) circle (1.2pt) node[\pos] {$\p$};");
                    sb.Append(@"\end{tikzpicture}");
                    break;

                case "pyramid":
                case "pyramid_sa_quad":
                    sb.AppendLine($@"\begin{{tikzpicture}}[declare function={{gocx=80; goc=-150; a={v1}; b=a/2; h={v2};}}, {drawOpt}]");
                    sb.AppendLine(@"  \path (0,0) coordinate (A)--+(gocx:h) coordinate (S)");
                    sb.AppendLine(@"  (a,0) coordinate (B) (goc:b) coordinate (D) +(a,0) coordinate (C);");
                    sb.AppendLine(@"  \draw[dashed] (S)--(A)--(B) (A)--(D);");
                    sb.AppendLine(@"  \draw (S)--(D)--(C)--(B)--(S)--(C);");
                    sb.AppendLine(@"  \foreach \p/\pos in {S/above,A/above left,B/right,C/below right,D/below left}");
                    sb.AppendLine(@"    \filldraw (\p) circle (1.2pt) node[\pos] {$\p$};");
                    sb.Append(@"\end{tikzpicture}");
                    break;

                case "pyramid_regular_quad":
                    sb.AppendLine($@"\begin{{tikzpicture}}[declare function={{goc=-150; a={v1}; b=a/2; h={v2};}}, {drawOpt}]");
                    sb.AppendLine(@"  \path (0,0) coordinate (A) (a,0) coordinate (B) (goc:b) coordinate (D) +(a,0) coordinate (C)");
                    sb.AppendLine(@"  ($(A)!.5!(C)$) coordinate (O)--+(0,h) coordinate (S);");
                    sb.AppendLine(@"  \draw[dashed] (S)--(A)--(B) (A)--(D) (S)--(O) (A)--(C) (B)--(D);");
                    sb.AppendLine(@"  \draw (S)--(D)--(C)--(B)--(S)--(C);");
                    sb.AppendLine(@"  \foreach \p/\pos in {S/above,A/above left,B/right,C/below right,D/below left,O/below}");
                    sb.AppendLine(@"    \filldraw (\p) circle (1.2pt) node[\pos] {$\p$};");
                    sb.Append(@"\end{tikzpicture}");
                    break;

                case "pyramid_trapezoid":
                case "pyramid_sad_perp":
                    sb.AppendLine($@"\begin{{tikzpicture}}[declare function={{goc=-60; gocx=90; a={v1}; b=0.4*a; c=0.4*a; h={v2};}}, {drawOpt}]");
                    sb.AppendLine(@"  \path (0,0) coordinate (A) (a,0) coordinate (B) (goc:b) coordinate (D)");
                    sb.AppendLine(@"  +(c,0) coordinate (C) (gocx:h) coordinate (S);");
                    sb.AppendLine(@"  \draw[dashed] (S)--(A)--(B) (A)--(D);");
                    sb.AppendLine(@"  \draw (S)--(D)--(C)--(B)--(S)--(C);");
                    sb.AppendLine(@"  \foreach \p/\pos in {S/above,A/above left,B/right,C/below right,D/below left}");
                    sb.AppendLine(@"    \filldraw (\p) circle (1.2pt) node[\pos] {$\p$};");
                    sb.Append(@"\end{tikzpicture}");
                    break;

                case "pyramid_regular_penta":
                    sb.AppendLine($@"\begin{{tikzpicture}}[declare function={{gocx=75; goc=-40; a={v1}; d=0.4*a; b=0.25*a; c=0.7*a; h={v2};}}, {drawOpt}]");
                    sb.AppendLine(@"  \path (0,0) coordinate (A) (-goc:d) coordinate (E) (a,0) coordinate (B) (goc:b) coordinate (D) (0.5*goc:c) coordinate (C)");
                    sb.AppendLine(@"  ($(A)!.4!(C)$) coordinate (O)--+(0,h) coordinate (S);");
                    sb.AppendLine(@"  \draw[dashed] (E)--(A)--(B) (S)--(A) (S)--(E) (S)--(O);");
                    sb.AppendLine(@"  \draw (E)--(D)--(C)--(B) (S)--(D) (S)--(C) (S)--(B);");
                    sb.AppendLine(@"  \foreach \p/\pos in {S/above,A/above,B/right,C/below right,D/below left,E/left,O/below}");
                    sb.AppendLine(@"    \filldraw (\p) circle (1.2pt) node[\pos] {$\p$};");
                    sb.Append(@"\end{tikzpicture}");
                    break;

                case "pyramid_regular_hexa":
                    sb.AppendLine($@"\begin{{tikzpicture}}[declare function={{gocx=75; goc=-50; a={v1}; d=0.4*a; b=0.3*a; h={v2};}}, {drawOpt}]");
                    sb.AppendLine(@"  \path (0,0) coordinate (A) (a,0) coordinate (B) (goc:b) coordinate (D) ($(D)+(d,0)$) coordinate (C) ($(A)+(B)-(C)$) coordinate (E) (-goc:d) coordinate (F)");
                    sb.AppendLine(@"  ($(A)!.5!(D)$) coordinate (O)--+(0,h) coordinate (S);");
                    sb.AppendLine(@"  \draw[dashed] (F)--(A)--(B) (S)--(A) (S)--(F) (S)--(O);");
                    sb.AppendLine(@"  \draw (F)--(E)--(D)--(C)--(B) (S)--(B) (S)--(C) (S)--(D) (S)--(E);");
                    sb.AppendLine(@"  \foreach \p/\pos in {S/above,A/above,B/right,C/below right,D/below,E/below left,F/left,O/below}");
                    sb.AppendLine(@"    \filldraw (\p) circle (1.2pt) node[\pos] {$\p$};");
                    sb.Append(@"\end{tikzpicture}");
                    break;

                case "pyramid_frustum":
                    sb.AppendLine($@"\begin{{tikzpicture}}[declare function={{gocx=60; goc=-150; a={v1}; b=a/2; h={v2}; k=0.5;}}, {drawOpt}]");
                    sb.AppendLine(@"  \path (0,0) coordinate (A)--+(gocx:h) coordinate (A')");
                    sb.AppendLine(@"  (a,0) coordinate (B) (goc:b) coordinate (D) +(a,0) coordinate (C)");
                    sb.AppendLine(@"  ($(A')+(k*a,0)$) coordinate (B') ($(A')+(goc:k*b)$) coordinate (D') +(k*a,0) coordinate (C');");
                    sb.AppendLine(@"  \draw[dashed] (A')--(A)--(B) (A)--(D) (B')--(A')--(D');");
                    sb.AppendLine(@"  \draw (B')--(C')--(D') (B)--(C)--(D) (B)--(B') (C)--(C') (D)--(D');");
                    sb.AppendLine(@"  \foreach \p/\pos in {A/left,B/right,C/below,D/left,A'/above left,B'/above right,C'/right,D'/below left}");
                    sb.AppendLine(@"    \filldraw (\p) circle (1.2pt) node[\pos] {$\p$};");
                    sb.Append(@"\end{tikzpicture}");
                    break;

                case "pyramid_tri_frustum":
                    sb.AppendLine($@"\begin{{tikzpicture}}[declare function={{goc=-45; a={v1}; b=0.45*a; h={v2}; k=0.5;}}, {drawOpt}]");
                    sb.AppendLine(@"  \path (0,0) coordinate (A) (a,0) coordinate (C) (goc:b) coordinate (B)");
                    sb.AppendLine(@"  ($(A)+(0.2*a,h)$) coordinate (A') ($(C)+(k*a-a,h)$) coordinate (C') ($(B)+(k*a-a,h)$) coordinate (B');");
                    sb.AppendLine(@"  \draw[dashed] (A)--(C) (A')--(C');");
                    sb.AppendLine(@"  \draw (A)--(B)--(C) (A')--(B')--(C') (A)--(A') (B)--(B') (C)--(C');");
                    sb.AppendLine(@"  \foreach \p/\pos in {A/left,B/below,C/right,A'/above left,B'/above,C'/above right}");
                    sb.AppendLine(@"    \filldraw (\p) circle (1.2pt) node[\pos] {$\p$};");
                    sb.Append(@"\end{tikzpicture}");
                    break;

                case "prism_triangular":
                    sb.AppendLine($@"\begin{{tikzpicture}}[declare function={{goc=-45; a={v1}; b=0.45*a; h={v2};}}, {drawOpt}]");
                    sb.AppendLine(@"  \path (0,0) coordinate (A) (a,0) coordinate (C) (goc:b) coordinate (B)");
                    sb.AppendLine(@"  (0,h) coordinate (A') (a,h) coordinate (C') ($(B)+(0,h)$) coordinate (B');");
                    sb.AppendLine(@"  \draw[dashed] (A)--(C);");
                    sb.AppendLine(@"  \draw (A)--(B)--(C) (A')--(B')--(C')--(A') (A)--(A') (B)--(B') (C)--(C');");
                    sb.AppendLine(@"  \foreach \p/\pos in {A/left,B/below,C/right,A'/above left,B'/above,C'/above right}");
                    sb.AppendLine(@"    \filldraw (\p) circle (1.2pt) node[\pos] {$\p$};");
                    sb.Append(@"\end{tikzpicture}");
                    break;

                case "prism_tri_oblique":
                    sb.AppendLine($@"\begin{{tikzpicture}}[declare function={{goc=-45; gocx=75; a={v1}; b=0.45*a; h={v2};}}, {drawOpt}]");
                    sb.AppendLine(@"  \path (0,0) coordinate (A) (a,0) coordinate (C) (goc:b) coordinate (B)");
                    sb.AppendLine(@"  (gocx:h) coordinate (A') ($(gocx:h)+(C)$) coordinate (C') ($(gocx:h)+(B)$) coordinate (B');");
                    sb.AppendLine(@"  \draw[dashed] (A)--(C);");
                    sb.AppendLine(@"  \draw (A)--(B)--(C) (A')--(B')--(C')--(A') (A)--(A') (B)--(B') (C)--(C');");
                    sb.AppendLine(@"  \foreach \p/\pos in {A/left,B/below,C/right,A'/above left,B'/above,C'/above right}");
                    sb.AppendLine(@"    \filldraw (\p) circle (1.2pt) node[\pos] {$\p$};");
                    sb.Append(@"\end{tikzpicture}");
                    break;

                case "cuboid":
                case "cube":
                case "prism_quad":
                    double hCuboid = tag == "cube" ? v1 : (v3 > 0 ? v3 : v2);
                    sb.AppendLine($@"\begin{{tikzpicture}}[declare function={{goc=225; a={Math.Round(v1 * 0.5, 2)}; b={v1}; h={hCuboid};}}, {drawOpt}]");
                    sb.AppendLine(@"  \path (0,0) coordinate (A) (b,0) coordinate (B) (goc:a) coordinate (D) ($(D)+(B)-(A)$) coordinate (C)");
                    sb.AppendLine(@"  (0,h) coordinate (A') (b,h) coordinate (B') ($(D)+(0,h)$) coordinate (D') ($(C)+(0,h)$) coordinate (C');");
                    sb.AppendLine(@"  \draw[dashed] (A')--(A)--(B) (A)--(D);");
                    sb.AppendLine(@"  \draw (B)--(C)--(D) (A')--(B')--(C')--(D')--(A') (B)--(B') (C)--(C') (D)--(D');");
                    sb.AppendLine(@"  \foreach \p/\pos in {A/above right,B/right,C/below right,D/below left,A'/above left,B'/above right,C'/above right,D'/above left}");
                    sb.AppendLine(@"    \filldraw (\p) circle (1.2pt) node[\pos] {$\p$};");
                    sb.Append(@"\end{tikzpicture}");
                    break;

                case "prism_quad_oblique":
                    sb.AppendLine($@"\begin{{tikzpicture}}[declare function={{goc=225; gocx=75; a={Math.Round(v1 * 0.5, 2)}; b={v1}; h={v2};}}, {drawOpt}]");
                    sb.AppendLine(@"  \path (0,0) coordinate (A) (b,0) coordinate (B) (goc:a) coordinate (D) ($(D)+(B)-(A)$) coordinate (C)");
                    sb.AppendLine(@"  (gocx:h) coordinate (A') ($(gocx:h)+(B)$) coordinate (B') ($(gocx:h)+(D)$) coordinate (D') ($(gocx:h)+(C)$) coordinate (C');");
                    sb.AppendLine(@"  \draw[dashed] (A')--(A)--(B) (A)--(D);");
                    sb.AppendLine(@"  \draw (B)--(C)--(D) (A')--(B')--(C')--(D')--(A') (B)--(B') (C)--(C') (D)--(D');");
                    sb.AppendLine(@"  \foreach \p/\pos in {A/above right,B/right,C/below right,D/below left,A'/above left,B'/above right,C'/above right,D'/above left}");
                    sb.AppendLine(@"    \filldraw (\p) circle (1.2pt) node[\pos] {$\p$};");
                    sb.Append(@"\end{tikzpicture}");
                    break;

                // ================= 3. MẶT TRÒN XOAY =================
                case "cylinder":
                case "cylinder_section":
                    sb.AppendLine($@"\begin{{tikzpicture}}[scale=0.95, {drawOpt}]");
                    sb.AppendLine($@"  \def\r{{{v1 / 2.0}}} \def\h{{{v2}}}");
                    sb.AppendLine(@"  \draw[dashed] (-\r,0) arc (180:0:\r cm and 0.65cm);");
                    sb.AppendLine(@"  \draw (-\r,0) arc (180:360:\r cm and 0.65cm);");
                    sb.AppendLine(@"  \draw (0,\h) ellipse (\r cm and 0.65cm);");
                    sb.AppendLine(@"  \draw (-\r,0) -- (-\r,\h) (\r,0) -- (\r,\h);");
                    sb.AppendLine(@"  \draw[dashed] (0,0) coordinate (O) -- (0,\h) coordinate (O');");
                    sb.AppendLine(@"  \draw[dashed] (O) -- (\r,0) node[midway,above,font=\small] {$r$};");
                    sb.AppendLine(@"  \filldraw (O) circle (1pt) node[below] {$O$};");
                    sb.AppendLine(@"  \filldraw (O') circle (1pt) node[above] {$O'$};");
                    sb.Append(@"\end{tikzpicture}");
                    break;

                case "cone":
                case "cone_down":
                    sb.AppendLine($@"\begin{{tikzpicture}}[scale=0.95, {drawOpt}]");
                    sb.AppendLine($@"  \def\r{{{v1 / 2.0}}} \def\h{{{v2}}}");
                    sb.AppendLine(@"  \coordinate (S) at (0,\h); \coordinate (O) at (0,0);");
                    sb.AppendLine(@"  \draw[dashed] (-\r,0) arc (180:0:\r cm and 0.7cm);");
                    sb.AppendLine(@"  \draw (-\r,0) arc (180:360:\r cm and 0.7cm);");
                    sb.AppendLine(@"  \draw (S) -- (-\r,0) (S) -- (\r,0);");
                    sb.AppendLine(@"  \draw[dashed] (S) -- (O) node[midway,left,font=\small] {$h$};");
                    sb.AppendLine(@"  \draw[dashed] (O) -- (\r,0) node[midway,below,font=\small] {$r$};");
                    sb.AppendLine(@"  \filldraw (S) circle (1.2pt) node[above] {$S$};");
                    sb.AppendLine(@"  \filldraw (O) circle (1.2pt) node[below] {$O$};");
                    sb.Append(@"\end{tikzpicture}");
                    break;

                case "cone_frustum":
                    sb.AppendLine($@"\begin{{tikzpicture}}[scale=0.95, {drawOpt}]");
                    sb.AppendLine($@"  \def\R{{{v1 / 2.0}}} \def\r{{{v2 / 2.0}}} \def\h{{{(v3 > 0 ? v3 : 3.5)}}}");
                    sb.AppendLine(@"  \draw[dashed] (-\R,0) arc (180:0:\R cm and 0.7cm);");
                    sb.AppendLine(@"  \draw (-\R,0) arc (180:360:\R cm and 0.7cm);");
                    sb.AppendLine(@"  \draw (0,\h) ellipse (\r cm and 0.45cm);");
                    sb.AppendLine(@"  \draw (-\R,0) -- (-\r,\h) (\R,0) -- (\r,\h);");
                    sb.AppendLine(@"  \draw[dashed] (0,0) coordinate (O) -- (0,\h) coordinate (O');");
                    sb.Append(@"\end{tikzpicture}");
                    break;

                case "sphere":
                case "sphere_circle_section":
                    sb.AppendLine($@"\begin{{tikzpicture}}[scale=1.1, {drawOpt}]");
                    sb.AppendLine($@"  \def\R{{{v1 / 2.0}}}");
                    sb.AppendLine(@"  \draw (0,0) coordinate (O) circle (\R);");
                    sb.AppendLine(@"  \draw[dashed] (-\R,0) arc (180:0:\R cm and 0.75cm);");
                    sb.AppendLine(@"  \draw (-\R,0) arc (180:360:\R cm and 0.75cm);");
                    sb.AppendLine(@"  \draw[dashed] (0,-\R) -- (0,\R);");
                    sb.AppendLine(@"  \draw[dashed] (O) -- (35:\R) node[midway,above,font=\small] {$R$};");
                    sb.AppendLine(@"  \filldraw (O) circle (1.2pt) node[below left] {$O$};");
                    sb.Append(@"\end{tikzpicture}");
                    break;

                case "cylinder_in_cone":
                    sb.AppendLine($@"\begin{{tikzpicture}}[scale=0.9, {drawOpt}]");
                    sb.AppendLine($@"  \def\R{{{v1 / 2.0}}} \def\H{{{v2}}} \def\r{{{v1 * 0.3}}} \def\h{{{v2 * 0.4}}}");
                    sb.AppendLine(@"  \coordinate (S) at (0,\H); \coordinate (O) at (0,0);");
                    sb.AppendLine(@"  \draw[dashed] (-\R,0) arc (180:0:\R cm and 0.7cm);");
                    sb.AppendLine(@"  \draw (-\R,0) arc (180:360:\R cm and 0.7cm);");
                    sb.AppendLine(@"  \draw (S) -- (-\R,0) (S) -- (\R,0);");
                    sb.AppendLine(@"  \draw[dashed] (S) -- (O);");
                    sb.AppendLine(@"  \draw[dashed,teal] (-\r,\h) arc (180:0:\r cm and 0.45cm);");
                    sb.AppendLine(@"  \draw[teal] (-\r,\h) arc (180:360:\r cm and 0.45cm);");
                    sb.AppendLine(@"  \draw[dashed,teal] (-\r,0) arc (180:0:\r cm and 0.45cm);");
                    sb.AppendLine(@"  \draw[teal] (-\r,0) arc (180:360:\r cm and 0.45cm);");
                    sb.AppendLine(@"  \draw[teal,thick] (-\r,0) -- (-\r,\h) (\r,0) -- (\r,\h);");
                    sb.AppendLine(@"  \filldraw (S) circle (1pt) node[above] {$S$};");
                    sb.AppendLine(@"  \filldraw (O) circle (1pt) node[below] {$O$};");
                    sb.Append(@"\end{tikzpicture}");
                    break;

                // ================= 4. ĐƯỜNG TRÒN & CONIC =================
                case "circle":
                case "circle_diameter":
                case "circle_two_tangents":
                case "circle_inscribed_quad":
                case "circle_tangent_ext":
                    sb.AppendLine($@"\begin{{tikzpicture}}[scale=1, {drawOpt}]");
                    sb.AppendLine($@"  \coordinate (O) at (0,0);");
                    sb.AppendLine($@"  \draw (O) circle ({v1 / 2.0});");
                    sb.AppendLine($@"  \filldraw (O) circle (1.5pt) node[below] {{$O$}};");
                    if (opt)
                    {
                        sb.AppendLine($@"  \draw (O) -- (40:{v1 / 2.0}) node[midway,above] {{$R$}};");
                        sb.AppendLine($@"  \draw (40:{v1 / 2.0}) circle (1.5pt) node[above right] {{$M$}};");
                    }
                    sb.Append(@"\end{tikzpicture}");
                    break;

                case "ellipse":
                case "ellipse_foci":
                    double cFoci = Math.Sqrt(Math.Max(0.1, v1 * v1 / 4.0 - v2 * v2 / 4.0));
                    sb.AppendLine($@"\begin{{tikzpicture}}[>=stealth,scale=1, {drawOpt}]");
                    sb.AppendLine($@"  \draw[->] ({-v1/2.0 - 1},0) -- ({v1/2.0 + 1},0) node[below] {{$x$}};");
                    sb.AppendLine($@"  \draw[->] (0,{-v2/2.0 - 0.8}) -- (0,{v2/2.0 + 0.8}) node[left] {{$y$}};");
                    sb.AppendLine(@"  \node[below left] at (0,0) {$O$};");
                    sb.AppendLine($@"  \draw (0,0) ellipse ({v1/2.0}cm and {v2/2.0}cm);");
                    if (opt)
                    {
                        sb.AppendLine($@"  \coordinate (F1) at ({-cFoci:F2},0);");
                        sb.AppendLine($@"  \coordinate (F2) at ({cFoci:F2},0);");
                        sb.AppendLine(@"  \filldraw (F1) circle (1.5pt) node[below] {$F_1$};");
                        sb.AppendLine(@"  \filldraw (F2) circle (1.5pt) node[below] {$F_2$};");
                    }
                    sb.Append(@"\end{tikzpicture}");
                    break;

                case "hyperbola":
                    sb.AppendLine($@"\begin{{tikzpicture}}[>=stealth,scale=1, {drawOpt}]");
                    sb.AppendLine(@"  \draw[->] (-4,0) -- (4,0) node[below] {$x$};");
                    sb.AppendLine(@"  \draw[->] (0,-3) -- (0,3) node[left] {$y$};");
                    sb.AppendLine(@"  \node[below left] at (0,0) {$O$};");
                    sb.AppendLine(@"  \draw[dashed,gray] (-3.5,-2.6) -- (3.5,2.6) node[right,font=\footnotesize] {$y=\frac{b}{a}x$};");
                    sb.AppendLine(@"  \draw[dashed,gray] (-3.5,2.6) -- (3.5,-2.6);");
                    sb.AppendLine(@"  \draw[thick,domain=-1.3:1.3,samples=50] plot ({2*cosh(\x)}, {1.5*sinh(\x)});");
                    sb.AppendLine(@"  \draw[thick,domain=-1.3:1.3,samples=50] plot ({-2*cosh(\x)}, {1.5*sinh(\x)});");
                    sb.Append(@"\end{tikzpicture}");
                    break;

                case "parabola_vert":
                case "parabola_horiz":
                    sb.AppendLine($@"\begin{{tikzpicture}}[>=stealth,scale=1, {drawOpt}]");
                    sb.AppendLine(@"  \draw[->] (-3,0) -- (3,0) node[below] {$x$};");
                    sb.AppendLine(@"  \draw[->] (0,-1) -- (0,4) node[left] {$y$};");
                    sb.AppendLine(@"  \node[below left] at (0,0) {$O$};");
                    sb.AppendLine(@"  \draw[thick,domain=-2.4:2.4,samples=60] plot (\x, {0.6*\x*\x});");
                    sb.Append(@"\end{tikzpicture}");
                    break;

                // ================= 5. ĐỒ THỊ & BBT =================
                case "graph_quad":
                    sb.AppendLine(@"\begin{tikzpicture}");
                    sb.AppendLine(@"\begin{axis}[");
                    sb.AppendLine(@"  axis lines=center, xlabel=$x$, ylabel={$f(x)$},");
                    sb.AppendLine(@"  xmin=-3, xmax=3, ymin=-2, ymax=6,");
                    sb.AppendLine(@"  width=9.5cm, height=6.5cm");
                    sb.AppendLine(@"]");
                    sb.AppendLine(@"  \addplot [domain=-2.5:2.5, samples=100, color=blue, thick] {x^2 - 1};");
                    sb.AppendLine(@"\end{axis}");
                    sb.Append(@"\end{tikzpicture}");
                    break;

                case "graph_cubic":
                    sb.AppendLine(@"\begin{tikzpicture}");
                    sb.AppendLine(@"\begin{axis}[");
                    sb.AppendLine(@"  axis lines=center, xlabel=$x$, ylabel={$f(x)$},");
                    sb.AppendLine(@"  xmin=-3, xmax=3, ymin=-3, ymax=3,");
                    sb.AppendLine(@"  width=9.5cm, height=6.5cm");
                    sb.AppendLine(@"]");
                    sb.AppendLine(@"  \addplot [domain=-2.2:2.2, samples=100, color=blue, thick] {x^3 - 3*x};");
                    sb.AppendLine(@"\end{axis}");
                    sb.Append(@"\end{tikzpicture}");
                    break;

                case "graph_quartic":
                    sb.AppendLine(@"\begin{tikzpicture}");
                    sb.AppendLine(@"\begin{axis}[");
                    sb.AppendLine(@"  axis lines=center, xlabel=$x$, ylabel={$f(x)$},");
                    sb.AppendLine(@"  xmin=-3, xmax=3, ymin=-3, ymax=4,");
                    sb.AppendLine(@"  width=9.5cm, height=6.5cm");
                    sb.AppendLine(@"]");
                    sb.AppendLine(@"  \addplot [domain=-2.2:2.2, samples=100, color=blue, thick] {x^4 - 2*x^2 - 1};");
                    sb.AppendLine(@"\end{axis}");
                    sb.Append(@"\end{tikzpicture}");
                    break;

                case "graph_rational":
                case "graph_rational_21":
                    sb.AppendLine(@"\begin{tikzpicture}");
                    sb.AppendLine(@"\begin{axis}[");
                    sb.AppendLine(@"  axis lines=center, xlabel=$x$, ylabel={$f(x)$},");
                    sb.AppendLine(@"  xmin=-4, xmax=6, ymin=-3, ymax=7,");
                    sb.AppendLine(@"  width=9.5cm, height=6.5cm");
                    sb.AppendLine(@"]");
                    sb.AppendLine(@"  \addplot [domain=-3.5:0.8, samples=80, color=blue, thick] {(2*x+1)/(x-1)};");
                    sb.AppendLine(@"  \addplot [domain=1.2:5.5, samples=80, color=blue, thick] {(2*x+1)/(x-1)};");
                    sb.AppendLine(@"  \draw[dashed, red] (1,-3) -- (1,7);");
                    sb.AppendLine(@"  \draw[dashed, red] (-4,2) -- (6,2);");
                    sb.AppendLine(@"\end{axis}");
                    sb.Append(@"\end{tikzpicture}");
                    break;

                case "graph_trig":
                    sb.AppendLine(@"\begin{tikzpicture}");
                    sb.AppendLine(@"\begin{axis}[");
                    sb.AppendLine(@"  axis lines=center, xlabel=$x$, ylabel={$y$},");
                    sb.AppendLine(@"  xmin=-7, xmax=7, ymin=-3.5, ymax=3.5,");
                    sb.AppendLine(@"  grid=major, grid style={gray!30},");
                    sb.AppendLine(@"  width=10.5cm, height=6cm, samples=200");
                    sb.AppendLine(@"]");
                    sb.AppendLine($@"  \addplot[blue, very thick, domain=-6.5:6.5] {{{v1}*sin(deg({v2}*x))}};");
                    sb.AppendLine(@"\end{axis}");
                    sb.Append(@"\end{tikzpicture}");
                    break;

                case "graph_area_integral":
                    sb.AppendLine(@"\begin{tikzpicture}");
                    sb.AppendLine(@"\begin{axis}[");
                    sb.AppendLine(@"  axis lines=center, xlabel=$x$, ylabel={$y$},");
                    sb.AppendLine(@"  xmin=-1, xmax=3, ymin=-1, ymax=3,");
                    sb.AppendLine(@"  width=9cm, height=6.5cm");
                    sb.AppendLine(@"]");
                    sb.AppendLine(@"  \addplot [domain=0:2, samples=60, fill=blue!20] {-x^2 + 2*x} \closedcycle;");
                    sb.AppendLine(@"  \addplot [domain=-0.5:2.5, samples=80, blue, thick] {-x^2 + 2*x};");
                    sb.AppendLine(@"\end{axis}");
                    sb.Append(@"\end{tikzpicture}");
                    break;

                case "tab_cubic":
                    sb.AppendLine(@"\begin{tikzpicture}");
                    sb.AppendLine(@"\tkzTabInit[lgt=1.5,espcl=2.5]");
                    sb.AppendLine(@" {$x$ / 1, $f'(x)$ / 1, $f(x)$ / 2}");
                    sb.AppendLine(@" {$-\infty$, $1$, $3$, $+\infty$}");
                    sb.AppendLine(@"\tkzTabLine{,+,0,-,0,+,}");
                    sb.AppendLine(@"\tkzTabVar{- / $-\infty$, + / $4$, - / $-2$, + / $+\infty$}");
                    sb.Append(@"\end{tikzpicture}");
                    break;

                case "tab_quartic":
                    sb.AppendLine(@"\begin{tikzpicture}");
                    sb.AppendLine(@"\tkzTabInit[lgt=1.5,espcl=2.2]");
                    sb.AppendLine(@" {$x$ / 1, $f'(x)$ / 1, $f(x)$ / 2}");
                    sb.AppendLine(@" {$-\infty$, $-1$, $0$, $1$, $+\infty$}");
                    sb.AppendLine(@"\tkzTabLine{,-,0,+,0,-,0,+,}");
                    sb.AppendLine(@"\tkzTabVar{+ / $+\infty$, - / $-2$, + / $-1$, - / $-2$, + / $+\infty$}");
                    sb.Append(@"\end{tikzpicture}");
                    break;

                case "tab_rational":
                case "tab_rational_21":
                    sb.AppendLine(@"\begin{tikzpicture}");
                    sb.AppendLine(@"\tkzTabInit[lgt=1.5,espcl=2.8]");
                    sb.AppendLine(@" {$x$ / 1, $y'$ / 1, $y$ / 2}");
                    sb.AppendLine(@" {$-\infty$, $2$, $+\infty$}");
                    sb.AppendLine(@"\tkzTabLine{,-,d,-,}");
                    sb.AppendLine(@"\tkzTabVar{+ / $1$, -D- / $-\infty$ / $+\infty$, + / $1$}");
                    sb.Append(@"\end{tikzpicture}");
                    break;

                case "tab_sign_quad":
                    sb.AppendLine(@"\begin{tikzpicture}");
                    sb.AppendLine(@"\tkzTabInit[lgt=1.5,espcl=2.5]");
                    sb.AppendLine(@" {$x$ / 1, $f(x)$ / 1}");
                    sb.AppendLine(@" {$-\infty$, $1$, $2$, $+\infty$}");
                    sb.AppendLine(@"\tkzTabLine{,+,0,-,0,+,}");
                    sb.Append(@"\end{tikzpicture}");
                    break;

                // ================= 6. BÀI TOÁN THỰC TẾ =================
                case "real_bridge_parabola":
                    sb.AppendLine($@"\begin{{tikzpicture}}[scale=0.95, {drawOpt}]");
                    sb.AppendLine(@"  \draw[thick,brown!70!black] (-4,-0.2) rectangle (4,0);");
                    sb.AppendLine(@"  \draw[thick,blue!60,fill=blue!10] (-4.5,-1.2) rectangle (4.5,-0.2);");
                    sb.AppendLine(@"  \node[blue!80,font=\small] at (0,-0.7) {Mặt nước};");
                    sb.AppendLine(@"  \draw[thick,gray!80,fill=gray!20] (-3,0) rectangle (-2.6,3.5);");
                    sb.AppendLine(@"  \draw[thick,gray!80,fill=gray!20] (2.6,0) rectangle (3,3.5);");
                    sb.AppendLine(@"  \draw[ultra thick,red!80,domain=-2.8:2.8,samples=60] plot (\x, {0.35*\x*\x + 0.6});");
                    sb.AppendLine(@"  \foreach \x in {-2.2,-1.6,-1.0,-0.4,0.4,1.0,1.6,2.2} {");
                    sb.AppendLine(@"      \draw[thin,gray!70] (\x,0) -- (\x,{0.35*\x*\x + 0.6});");
                    sb.AppendLine(@"  }");
                    sb.AppendLine(@"  \draw[<->,thick] (-2.8,3.7) -- (2.8,3.7) node[midway,above,font=\small] {$L = 120\text{ m}$};");
                    sb.AppendLine(@"  \draw[<->,thick] (3.3,0) -- (3.3,3.5) node[midway,right,font=\small] {$h = 35\text{ m}$};");
                    sb.Append(@"\end{tikzpicture}");
                    break;

                case "real_lighthouse":
                    sb.AppendLine($@"\begin{{tikzpicture}}[scale=0.9, {drawOpt}]");
                    sb.AppendLine(@"  \fill[blue!10] (-0.5,-0.2) rectangle (7.5,-1.0);");
                    sb.AppendLine(@"  \draw[thick,blue!60] (-0.5,-0.2) -- (7.5,-0.2);");
                    sb.AppendLine(@"  \draw[thick,fill=gray!20] (0,0) -- (0.3,3.5) -- (-0.3,3.5) -- cycle;");
                    sb.AppendLine(@"  \draw[fill=yellow!80] (-0.4,3.5) rectangle (0.4,3.8);");
                    sb.AppendLine(@"  \node[above,font=\small] at (0,3.8) {Hải đăng $H$};");
                    sb.AppendLine(@"  \coordinate (T1) at (3.5,0); \coordinate (T2) at (6.5,0);");
                    sb.AppendLine(@"  \draw[thick,brown!80,fill=brown!40] (3.1,0) -- (3.9,0) -- (3.7,-0.3) -- (3.3,-0.3) -- cycle;");
                    sb.AppendLine(@"  \draw[thick,brown!80,fill=brown!40] (6.1,0) -- (6.9,0) -- (6.7,-0.3) -- (6.3,-0.3) -- cycle;");
                    sb.AppendLine(@"  \draw[dashed,orange!80,thick] (0,3.6) -- (T1) node[midway,above,sloped,font=\footnotesize] {Tia nhìn $1$};");
                    sb.AppendLine(@"  \draw[dashed,orange!80,thick] (0,3.6) -- (T2) node[midway,above,sloped,font=\footnotesize] {Tia nhìn $2$};");
                    sb.AppendLine(@"  \draw (0,0) -- (0,3.6) node[midway,left,font=\small] {$h = 40\text{ m}$};");
                    sb.AppendLine(@"  \draw (0,0) -- (T2);");
                    sb.AppendLine(@"  \node[below,font=\small] at (3.5,-0.3) {Tàu $A$};");
                    sb.AppendLine(@"  \node[below,font=\small] at (6.5,-0.3) {Tàu $B$};");
                    sb.Append(@"\end{tikzpicture}");
                    break;

                case "real_basketball":
                    sb.AppendLine($@"\begin{{tikzpicture}}[>=stealth,scale=0.9, {drawOpt}]");
                    sb.AppendLine(@"  \draw[->,thick] (-0.2,0) -- (6.5,0) node[below] {$x$ (m)};");
                    sb.AppendLine(@"  \draw[->,thick] (0,-0.2) -- (0,4.5) node[left] {$y$ (m)};");
                    sb.AppendLine(@"  \node[below left] at (0,0) {$O$};");
                    sb.AppendLine(@"  \draw[thick] (0,0) -- (0,1.8) node[left] {Người ném};");
                    sb.AppendLine(@"  \filldraw[orange!90] (0,2.0) circle (3pt) node[above left] {$M(0;2)$};");
                    sb.AppendLine(@"  \draw[thick,red!80,domain=0:5.2,samples=60] plot (\x, {-0.2*(\x-2.5)*(\x-2.5) + 3.25});");
                    sb.AppendLine(@"  \draw[thick] (5.0,0) -- (5.0,3.05) node[right,font=\small] {Rổ ($3.05$m)};");
                    sb.AppendLine(@"  \draw[thick,orange] (4.6,3.05) -- (5.0,3.05);");
                    sb.AppendLine(@"  \filldraw[red!80] (4.8,3.05) circle (2.5pt);");
                    sb.AppendLine(@"  \node[above,font=\small,red!80] at (2.5,3.3) {Đỉnh quỹ đạo};");
                    sb.Append(@"\end{tikzpicture}");
                    break;

                case "real_tent_pyramid":
                    sb.AppendLine($@"\begin{{tikzpicture}}[declare function={{goc=-45; a={v1}; b=0.45*a; h={v2};}}, {drawOpt}]");
                    sb.AppendLine(@"  \path (0,0) coordinate (A) (a,0) coordinate (C) (goc:b) coordinate (B)");
                    sb.AppendLine(@"  ($(A)!0.33!(C)!0.5!(B)$) coordinate (O)--+(0,h) coordinate (S);");
                    sb.AppendLine(@"  \draw[dashed] (A)--(C);");
                    sb.AppendLine(@"  \draw (S)--(A)--(B)--(S)--(C)--(B);");
                    sb.AppendLine(@"  \node[above,font=\bfseries] at (S) {Đỉnh lều $S$};");
                    sb.Append(@"\end{tikzpicture}");
                    break;

                case "real_hourglass":
                    sb.AppendLine($@"\begin{{tikzpicture}}[scale=0.9, {drawOpt}]");
                    sb.AppendLine($@"  \def\r{{{v1 / 2.0}}} \def\h{{{v2}}}");
                    sb.AppendLine(@"  \draw (0,\h) ellipse (\r cm and 0.5cm);");
                    sb.AppendLine(@"  \draw (0,-\h) ellipse (\r cm and 0.5cm);");
                    sb.AppendLine(@"  \draw (-\r,\h) -- (\r,-\h) (\r,\h) -- (-\r,-\h);");
                    sb.AppendLine(@"  \filldraw (0,0) circle (1.5pt) node[right] {$O$};");
                    sb.Append(@"\end{tikzpicture}");
                    break;

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

                default:
                    sb.AppendLine($@"\begin{{tikzpicture}}[scale=1, {drawOpt}]");
                    sb.AppendLine(@"  \draw (0,0) rectangle (4,3);");
                    sb.Append(@"\end{tikzpicture}");
                    break;
            }

                string raw = sb.ToString();
                raw = Regex.Replace(raw, @"\\\\([a-zA-Z]+|\{|\})", @"\$1");

                // Đảm bảo không bao giờ tồn tại dấu phẩy thập phân kiểu vi-VN (1,25 -> 1.25)
                raw = Regex.Replace(raw, @"(?<=\\def\\[a-zA-Z]+\{)(\d+),(\d+)(?=\})", "$1.$2");
                raw = Regex.Replace(raw, @"(\d+),(\d+)\s*(cm|mm|pt|in|ex|em)", "$1.$2$3");
                raw = Regex.Replace(raw, @"(?<=\b[a-zA-Z_]+\s*=\s*)(\d+),(\d+)(?=[,;\}\]])", "$1.$2");
                raw = Regex.Replace(raw, @"circle\s*\(\s*(\d+),(\d+)\s*\)", "circle ($1.$2)");

                return raw;
            }
            finally
            {
                Thread.CurrentThread.CurrentCulture = prevCulture;
                Thread.CurrentThread.CurrentUICulture = prevUiCulture;
                CultureInfo.CurrentCulture = prevCulture;
                CultureInfo.CurrentUICulture = prevUiCulture;
            }
        }

        private void BtnPreviewCode_Click(object sender, RoutedEventArgs e)
        {
            RegenerateCode();
        }

        private void BtnInsert_Click(object sender, RoutedEventArgs e)
        {
            AutoCompileRequested = false;
            GeneratedTikzCode = TxtResultCode.Text.Trim();
            DialogResult = true;
            Close();
        }

        private void BtnInsertAndCompile_Click(object sender, RoutedEventArgs e)
        {
            AutoCompileRequested = true;
            GeneratedTikzCode = TxtResultCode.Text.Trim();
            DialogResult = true;
            Close();
        }

        private void BtnCancel_Click(object sender, RoutedEventArgs e)
        {
            AutoCompileRequested = false;
            DialogResult = false;
            Close();
        }
    }
}
