using System;
using System.Windows;
using System.Windows.Controls;
using MatrixExamAI.Desktop.Services;
using MatrixExamAI.Shared.Tikz;

namespace MatrixExamAI.Desktop.Views
{
    public partial class TikzShapeBuilderDialog : Window
    {
        public string GeneratedTikzCode { get; private set; } = string.Empty;

        public TikzShapeBuilderDialog()
        {
            InitializeComponent();
            PopulateShapesForCategory("2D");
        }

        private void CmbCategory_SelectionChanged(object sender, SelectionChangedEventArgs e)
        {
            if (CmbCategory?.SelectedItem is ComboBoxItem item && item.Tag is string tag)
            {
                PopulateShapesForCategory(tag);
            }
        }

        private void PopulateShapesForCategory(string category)
        {
            if (CmbShapeType == null) return;

            CmbShapeType.Items.Clear();

            switch (category)
            {
                case "2D":
                    CmbShapeType.Items.Add(new ComboBoxItem { Content = "Tam giác vuông", Tag = "tri_right" });
                    CmbShapeType.Items.Add(new ComboBoxItem { Content = "Tam giác đều", Tag = "tri_equi" });
                    CmbShapeType.Items.Add(new ComboBoxItem { Content = "Tam giác cân", Tag = "tri_iso" });
                    CmbShapeType.Items.Add(new ComboBoxItem { Content = "Hình chữ nhật", Tag = "rect" });
                    CmbShapeType.Items.Add(new ComboBoxItem { Content = "Hình vuông", Tag = "square" });
                    CmbShapeType.Items.Add(new ComboBoxItem { Content = "Hình bình hành", Tag = "parallelogram" });
                    CmbShapeType.Items.Add(new ComboBoxItem { Content = "Hình thang cân", Tag = "trapezoid" });
                    CmbShapeType.Items.Add(new ComboBoxItem { Content = "Đường tròn (O, R)", Tag = "circle" });
                    CmbShapeType.Items.Add(new ComboBoxItem { Content = "Hệ trục tọa độ Oxy", Tag = "oxy" });
                    break;

                case "3D":
                    CmbShapeType.Items.Add(new ComboBoxItem { Content = "Hình chóp tứ giác S.ABCD", Tag = "pyramid" });
                    CmbShapeType.Items.Add(new ComboBoxItem { Content = "Hình chóp tam giác S.ABC", Tag = "tetrahedron" });
                    CmbShapeType.Items.Add(new ComboBoxItem { Content = "Hình hộp chữ nhật", Tag = "cuboid" });
                    CmbShapeType.Items.Add(new ComboBoxItem { Content = "Hình lập phương", Tag = "cube" });
                    CmbShapeType.Items.Add(new ComboBoxItem { Content = "Hình trụ tròn xoay", Tag = "cylinder" });
                    CmbShapeType.Items.Add(new ComboBoxItem { Content = "Hình nón tròn xoay", Tag = "cone" });
                    CmbShapeType.Items.Add(new ComboBoxItem { Content = "Hình cầu khối", Tag = "sphere" });
                    break;

                case "TAB":
                    CmbShapeType.Items.Add(new ComboBoxItem { Content = "Bảng biến thiên bậc 3 (2 cực trị)", Tag = "tab_cubic" });
                    CmbShapeType.Items.Add(new ComboBoxItem { Content = "Bảng biến thiên bậc 4 trùng phương", Tag = "tab_quartic" });
                    CmbShapeType.Items.Add(new ComboBoxItem { Content = "Bảng biến thiên phân thức (ax+b)/(cx+d)", Tag = "tab_rational" });
                    CmbShapeType.Items.Add(new ComboBoxItem { Content = "Bảng xét dấu nhị thức bậc nhất", Tag = "tab_sign_lin" });
                    CmbShapeType.Items.Add(new ComboBoxItem { Content = "Bảng xét dấu tam thức bậc hai", Tag = "tab_sign_quad" });
                    break;

                case "GRAPH":
                    CmbShapeType.Items.Add(new ComboBoxItem { Content = "Đồ thị Parabol y = ax² + bx + c", Tag = "graph_quad" });
                    CmbShapeType.Items.Add(new ComboBoxItem { Content = "Đồ thị bậc 3 y = ax³ + bx² + cx + d", Tag = "graph_cubic" });
                    break;
            }

            if (CmbShapeType.Items.Count > 0)
            {
                CmbShapeType.SelectedIndex = 0;
            }
        }

        private void CmbShapeType_SelectionChanged(object sender, SelectionChangedEventArgs e)
        {
            if (CmbShapeType?.SelectedItem is ComboBoxItem item && item.Tag is string tag)
            {
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
                case "tri_right":
                    LblParam1.Text = "Cạnh góc vuông a:"; TxtParam1.Text = "4";
                    LblParam2.Text = "Cạnh góc vuông b:"; TxtParam2.Text = "3";
                    GridParam3.Visibility = Visibility.Collapsed;
                    LblParam4.Text = "Đỉnh (A,B,C):"; TxtParam4.Text = "A,B,C";
                    ChkOption.Content = "Ký hiệu góc vuông";
                    break;

                case "tri_equi":
                case "tri_iso":
                    LblParam1.Text = "Cạnh đáy / Cạnh a:"; TxtParam1.Text = "4";
                    LblParam2.Text = "Chiều cao h:"; TxtParam2.Text = "3.5";
                    GridParam3.Visibility = Visibility.Collapsed;
                    LblParam4.Text = "Đỉnh (A,B,C):"; TxtParam4.Text = "A,B,C";
                    ChkOption.Visibility = Visibility.Collapsed;
                    break;

                case "rect":
                case "square":
                    LblParam1.Text = "Chiều dài a:"; TxtParam1.Text = "5";
                    LblParam2.Text = "Chiều rộng b:"; TxtParam2.Text = "3";
                    GridParam3.Visibility = Visibility.Collapsed;
                    LblParam4.Text = "Đỉnh (A,B,C,D):"; TxtParam4.Text = "A,B,C,D";
                    ChkOption.Visibility = Visibility.Collapsed;
                    break;

                case "parallelogram":
                    LblParam1.Text = "Cạnh đáy a:"; TxtParam1.Text = "5";
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
                    ChkOption.Visibility = Visibility.Collapsed;
                    break;

                case "circle":
                    LblParam1.Text = "Bán kính R:"; TxtParam1.Text = "3";
                    LblParam2.Text = "Tọa độ tâm (x,y):"; TxtParam2.Text = "0";
                    GridParam3.Visibility = Visibility.Collapsed;
                    LblParam4.Text = "Tên tâm:"; TxtParam4.Text = "O";
                    ChkOption.Content = "Hiển thị nét đứt bán kính R";
                    break;

                case "oxy":
                    LblParam1.Text = "Khoảng x (min,max):"; TxtParam1.Text = "-4, 4";
                    LblParam2.Text = "Khoảng y (min,max):"; TxtParam2.Text = "-3, 4";
                    GridParam3.Visibility = Visibility.Collapsed;
                    GridParam4.Visibility = Visibility.Collapsed;
                    ChkOption.Content = "Hiển thị lưới tọa độ (grid)";
                    break;

                case "pyramid":
                case "tetrahedron":
                    LblParam1.Text = "Cạnh đáy a:"; TxtParam1.Text = "4";
                    LblParam2.Text = "Chiều cao h:"; TxtParam2.Text = "4.5";
                    GridParam3.Visibility = Visibility.Collapsed;
                    LblParam4.Text = "Đỉnh (S,A,B,C,D):"; TxtParam4.Text = "S,A,B,C,D";
                    ChkOption.Visibility = Visibility.Collapsed;
                    break;

                case "cuboid":
                case "cube":
                    LblParam1.Text = "Chiều dài a:"; TxtParam1.Text = "4";
                    LblParam2.Text = "Chiều rộng b:"; TxtParam2.Text = "3";
                    LblParam3.Text = "Chiều cao h:"; TxtParam3.Text = "3.5";
                    LblParam4.Text = "Tên đáy:"; TxtParam4.Text = "A,B,C,D";
                    ChkOption.Visibility = Visibility.Collapsed;
                    break;

                case "cylinder":
                case "cone":
                    LblParam1.Text = "Bán kính r:"; TxtParam1.Text = "2.5";
                    LblParam2.Text = "Chiều cao h:"; TxtParam2.Text = "4.5";
                    GridParam3.Visibility = Visibility.Collapsed;
                    GridParam4.Visibility = Visibility.Collapsed;
                    ChkOption.Visibility = Visibility.Collapsed;
                    break;

                case "sphere":
                    LblParam1.Text = "Bán kính R:"; TxtParam1.Text = "3";
                    GridParam2.Visibility = Visibility.Collapsed;
                    GridParam3.Visibility = Visibility.Collapsed;
                    GridParam4.Visibility = Visibility.Collapsed;
                    ChkOption.Visibility = Visibility.Collapsed;
                    break;

                case "tab_cubic":
                    LblParam1.Text = "Hệ số a (>0 hay <0):"; TxtParam1.Text = "1";
                    LblParam2.Text = "2 điểm cực trị x1, x2:"; TxtParam2.Text = "0, 2";
                    LblParam3.Text = "2 giá trị y1, y2:"; TxtParam3.Text = "4, 0";
                    GridParam4.Visibility = Visibility.Collapsed;
                    ChkOption.Visibility = Visibility.Collapsed;
                    break;

                case "tab_quartic":
                    LblParam1.Text = "Hệ số a (>0 hay <0):"; TxtParam1.Text = "1";
                    LblParam2.Text = "3 cực trị x1,x2,x3:"; TxtParam2.Text = "-1, 0, 1";
                    LblParam3.Text = "3 giá trị y1,y2,y3:"; TxtParam3.Text = "-1, 3, -1";
                    GridParam4.Visibility = Visibility.Collapsed;
                    ChkOption.Visibility = Visibility.Collapsed;
                    break;

                case "tab_rational":
                    LblParam1.Text = "Tiệm cận đứng x0:"; TxtParam1.Text = "1";
                    LblParam2.Text = "Tiệm cận ngang y0:"; TxtParam2.Text = "2";
                    GridParam3.Visibility = Visibility.Collapsed;
                    GridParam4.Visibility = Visibility.Collapsed;
                    ChkOption.Content = "Đồng biến (y' > 0)";
                    ChkOption.IsChecked = true;
                    break;

                case "tab_sign_lin":
                    LblParam1.Text = "Nghiệm x0:"; TxtParam1.Text = "2";
                    GridParam2.Visibility = Visibility.Collapsed;
                    GridParam3.Visibility = Visibility.Collapsed;
                    GridParam4.Visibility = Visibility.Collapsed;
                    ChkOption.Content = "Hệ số a > 0";
                    ChkOption.IsChecked = true;
                    break;

                case "tab_sign_quad":
                    LblParam1.Text = "2 Nghiệm x1, x2:"; TxtParam1.Text = "-1, 3";
                    GridParam2.Visibility = Visibility.Collapsed;
                    GridParam3.Visibility = Visibility.Collapsed;
                    GridParam4.Visibility = Visibility.Collapsed;
                    ChkOption.Content = "Hệ số a > 0 (Trong trái ngoài cùng)";
                    ChkOption.IsChecked = true;
                    break;

                case "graph_quad":
                    LblParam1.Text = "Hệ số a, b, c:"; TxtParam1.Text = "1, -2, -1";
                    LblParam2.Text = "Khoảng vẽ [xmin, xmax]:"; TxtParam2.Text = "-2, 4";
                    GridParam3.Visibility = Visibility.Collapsed;
                    GridParam4.Visibility = Visibility.Collapsed;
                    ChkOption.Visibility = Visibility.Collapsed;
                    break;

                case "graph_cubic":
                    LblParam1.Text = "Hệ số a, b, c, d:"; TxtParam1.Text = "1, -3, 0, 1";
                    LblParam2.Text = "Khoảng vẽ [xmin, xmax]:"; TxtParam2.Text = "-2, 3";
                    GridParam3.Visibility = Visibility.Collapsed;
                    GridParam4.Visibility = Visibility.Collapsed;
                    ChkOption.Visibility = Visibility.Collapsed;
                    break;
            }
        }

        private void RegenerateCode()
        {
            if (TxtResultCode == null || CmbShapeType?.SelectedItem is not ComboBoxItem item || item.Tag is not string tag)
                return;

            try
            {
                string code = tag switch
                {
                    "tri_right" => TikzShapeGenerators.GenerateRightTriangle(
                        ParseDouble(TxtParam1.Text, 4), ParseDouble(TxtParam2.Text, 3)),
                    "tri_equi" => TikzShapeGenerators.GenerateEquilateralTriangle(
                        ParseDouble(TxtParam1.Text, 4)),
                    "tri_iso" => TikzShapeGenerators.GenerateIsoscelesTriangle(
                        ParseDouble(TxtParam1.Text, 4), ParseDouble(TxtParam2.Text, 3.5)),
                    "rect" => TikzShapeGenerators.GenerateRectangle(
                        ParseDouble(TxtParam1.Text, 5), ParseDouble(TxtParam2.Text, 3)),
                    "square" => TikzShapeGenerators.GenerateSquare(
                        ParseDouble(TxtParam1.Text, 4)),
                    "parallelogram" => TikzShapeGenerators.GenerateParallelogram(
                        ParseDouble(TxtParam1.Text, 5), ParseDouble(TxtParam2.Text, 3), ParseDouble(TxtParam3.Text, 1.5)),
                    "trapezoid" => TikzShapeGenerators.GenerateTrapezoid(
                        ParseDouble(TxtParam1.Text, 6), ParseDouble(TxtParam2.Text, 3), ParseDouble(TxtParam3.Text, 3)),
                    "circle" => TikzShapeGenerators.GenerateCircle(
                        0, 0, ParseDouble(TxtParam1.Text, 3), TxtParam4.Text.Trim()),
                    "oxy" => TikzShapeGenerators.GenerateOxyAxis(-4, 4, -3, 4),
                    "pyramid" => TikzShapeGenerators.GeneratePyramid(
                        ParseDouble(TxtParam1.Text, 4), ParseDouble(TxtParam2.Text, 4.5)),
                    "tetrahedron" => TikzShapeGenerators.GenerateTetrahedron(
                        ParseDouble(TxtParam1.Text, 4), ParseDouble(TxtParam2.Text, 4.5)),
                    "cuboid" => TikzShapeGenerators.GenerateCuboid(
                        ParseDouble(TxtParam1.Text, 4), ParseDouble(TxtParam2.Text, 3), ParseDouble(TxtParam3.Text, 3.5)),
                    "cube" => TikzShapeGenerators.GenerateCube(
                        ParseDouble(TxtParam1.Text, 3.5)),
                    "cylinder" => TikzShapeGenerators.GenerateCylinder(
                        ParseDouble(TxtParam1.Text, 2.5), ParseDouble(TxtParam2.Text, 4.5)),
                    "cone" => TikzShapeGenerators.GenerateCone(
                        ParseDouble(TxtParam1.Text, 2.5), ParseDouble(TxtParam2.Text, 4.5)),
                    "sphere" => TikzShapeGenerators.GenerateSphere(
                        ParseDouble(TxtParam1.Text, 3)),
                    "tab_cubic" => TikzShapeGenerators.GenerateCubicTable(
                        ParseDouble(TxtParam1.Text, 1), 0, 2, 4, 0),
                    "tab_quartic" => TikzShapeGenerators.GenerateQuarticTable(
                        ParseDouble(TxtParam1.Text, 1), -1, 0, 1, -1, 3, -1),
                    "tab_rational" => TikzShapeGenerators.GenerateRationalTable(
                        ParseDouble(TxtParam1.Text, 1), ParseDouble(TxtParam2.Text, 2), ChkOption.IsChecked == true),
                    "tab_sign_lin" => TikzShapeGenerators.GenerateSignTableLinear(
                        ParseDouble(TxtParam1.Text, 2), ChkOption.IsChecked == true),
                    "tab_sign_quad" => TikzShapeGenerators.GenerateSignTableQuadratic(
                        -1, 3, ChkOption.IsChecked == true),
                    "graph_quad" => TikzShapeGenerators.GenerateParabolaGraph(1, -2, -1),
                    "graph_cubic" => TikzShapeGenerators.GenerateCubicGraph(1, -3, 0, 1),
                    _ => "% Chưa có mã cho loại hình này"
                };

                TxtResultCode.Text = code;
            }
            catch (Exception ex)
            {
                TxtResultCode.Text = $"% Lỗi sinh mã: {ex.Message}";
            }
        }

        private static double ParseDouble(string input, double defaultValue)
        {
            if (double.TryParse(input?.Trim(), System.Globalization.NumberStyles.Any, System.Globalization.CultureInfo.InvariantCulture, out double val))
            {
                return val;
            }
            if (double.TryParse(input?.Trim(), out double valLocal))
            {
                return valLocal;
            }
            return defaultValue;
        }

        private void Param_TextChanged(object sender, TextChangedEventArgs e)
        {
            RegenerateCode();
        }

        private void ChkOption_Changed(object sender, RoutedEventArgs e)
        {
            RegenerateCode();
        }

        private void BtnInsert_Click(object sender, RoutedEventArgs e)
        {
            GeneratedTikzCode = TxtResultCode.Text;
            DialogResult = true;
            Close();
        }

        private void BtnCopyCode_Click(object sender, RoutedEventArgs e)
        {
            SafeClipboard.SetText(TxtResultCode.Text);
            MessageBox.Show("Đã sao chép mã TikZ vào Clipboard!", "Thành công", MessageBoxButton.OK, MessageBoxImage.Information);
        }

        private void BtnCancel_Click(object sender, RoutedEventArgs e)
        {
            DialogResult = false;
            Close();
        }
    }
}
