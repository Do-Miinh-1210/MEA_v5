using System;
using System.Globalization;
using System.Text;

namespace MatrixExamAI.Shared.Tikz
{
    /// <summary>
    /// Bộ sinh mã nguồn TikZ trực quan từ các tham số hình học và giải tích,
    /// kế thừa và nâng cấp toàn diện từ ui/tikz_shape_builder.py của MEA v5.0.
    /// </summary>
    public static class TikzShapeGenerators
    {
        private static string F(double v) => Math.Round(v, 4).ToString("0.##", CultureInfo.InvariantCulture);

        // ══════════════════════════════════════════════════════════════════════════
        // 1. HÌNH HỌC PHẲNG 2D
        // ══════════════════════════════════════════════════════════════════════════

        public static string GenerateTriangle(double ax, double ay, double bx, double by, double cx, double cy,
            string na = "A", string nb = "B", string nc = "C", bool showAngle = false)
        {
            var sb = new StringBuilder();
            sb.AppendLine(@"\begin{tikzpicture}[scale=1, thick]");
            sb.AppendLine($@"  \coordinate[label=below left:${na}$]  ({na}) at ({F(ax)},{F(ay)});");
            sb.AppendLine($@"  \coordinate[label=below right:${nb}$] ({nb}) at ({F(bx)},{F(by)});");
            sb.AppendLine($@"  \coordinate[label=above:${nc}$]       ({nc}) at ({F(cx)},{F(cy)});");
            sb.AppendLine($@"  \draw ({na})--({nb})--({nc})--cycle;");
            if (showAngle)
            {
                sb.AppendLine($@"  \draw ({na}) +(0.3,0) arc (0:45:0.3);");
            }
            sb.AppendLine(@"\end{tikzpicture}");
            return sb.ToString().TrimEnd();
        }

        public static string GenerateRightTriangle(double a, double b, string na = "A", string nb = "B", string nc = "C")
        {
            var sb = new StringBuilder();
            sb.AppendLine(@"\begin{tikzpicture}[scale=1, thick]");
            sb.AppendLine($@"  \coordinate[label=below left:${na}$]  ({na}) at (0,0);");
            sb.AppendLine($@"  \coordinate[label=below right:${nb}$] ({nb}) at ({F(a)},0);");
            sb.AppendLine($@"  \coordinate[label=above left:${nc}$]  ({nc}) at (0,{F(b)});");
            sb.AppendLine($@"  \draw ({na})--({nb})--({nc})--cycle;");
            sb.AppendLine($@"  % Ký hiệu góc vuông tại {na}");
            sb.AppendLine($@"  \draw ({na}) +(0.3,0) -- +(0.3,0.3) -- +(0,0.3);");
            sb.AppendLine(@"\end{tikzpicture}");
            return sb.ToString().TrimEnd();
        }

        public static string GenerateEquilateralTriangle(double side, string na = "A", string nb = "B", string nc = "C")
        {
            double h = Math.Round(side * Math.Sqrt(3) / 2.0, 2);
            double half = Math.Round(side / 2.0, 2);
            return GenerateTriangle(0, 0, side, 0, half, h, na, nb, nc);
        }

        public static string GenerateIsoscelesTriangle(double baseWidth, double height, string na = "A", string nb = "B", string nc = "C")
        {
            double half = Math.Round(baseWidth / 2.0, 2);
            return GenerateTriangle(0, 0, baseWidth, 0, half, height, na, nb, nc);
        }

        public static string GenerateRectangle(double width, double height, string na = "A", string nb = "B", string nc = "C", string nd = "D")
        {
            var sb = new StringBuilder();
            sb.AppendLine(@"\begin{tikzpicture}[scale=1, thick]");
            sb.AppendLine($@"  \coordinate[label=below left:${na}$]  ({na}) at (0,0);");
            sb.AppendLine($@"  \coordinate[label=below right:${nb}$] ({nb}) at ({F(width)},0);");
            sb.AppendLine($@"  \coordinate[label=above right:${nc}$] ({nc}) at ({F(width)},{F(height)});");
            sb.AppendLine($@"  \coordinate[label=above left:${nd}$]  ({nd}) at (0,{F(height)});");
            sb.AppendLine($@"  \draw ({na})--({nb})--({nc})--({nd})--cycle;");
            sb.AppendLine(@"\end{tikzpicture}");
            return sb.ToString().TrimEnd();
        }

        public static string GenerateSquare(double side, string na = "A", string nb = "B", string nc = "C", string nd = "D")
        {
            return GenerateRectangle(side, side, na, nb, nc, nd);
        }

        public static string GenerateParallelogram(double width, double height, double skew,
            string na = "A", string nb = "B", string nc = "C", string nd = "D")
        {
            var sb = new StringBuilder();
            sb.AppendLine(@"\begin{tikzpicture}[scale=1, thick]");
            sb.AppendLine($@"  \coordinate[label=below left:${na}$]  ({na}) at (0,0);");
            sb.AppendLine($@"  \coordinate[label=below right:${nb}$] ({nb}) at ({F(width)},0);");
            sb.AppendLine($@"  \coordinate[label=above right:${nc}$] ({nc}) at ({F(width + skew)},{F(height)});");
            sb.AppendLine($@"  \coordinate[label=above left:${nd}$]  ({nd}) at ({F(skew)},{F(height)});");
            sb.AppendLine($@"  \draw ({na})--({nb})--({nc})--({nd})--cycle;");
            sb.AppendLine(@"\end{tikzpicture}");
            return sb.ToString().TrimEnd();
        }

        public static string GenerateTrapezoid(double bottom, double top, double height,
            string na = "A", string nb = "B", string nc = "C", string nd = "D")
        {
            double offset = Math.Round((bottom - top) / 2.0, 2);
            var sb = new StringBuilder();
            sb.AppendLine(@"\begin{tikzpicture}[scale=1, thick]");
            sb.AppendLine($@"  \coordinate[label=below left:${na}$]  ({na}) at (0,0);");
            sb.AppendLine($@"  \coordinate[label=below right:${nb}$] ({nb}) at ({F(bottom)},0);");
            sb.AppendLine($@"  \coordinate[label=above right:${nc}$] ({nc}) at ({F(bottom - offset)},{F(height)});");
            sb.AppendLine($@"  \coordinate[label=above left:${nd}$]  ({nd}) at ({F(offset)},{F(height)});");
            sb.AppendLine($@"  \draw ({na})--({nb})--({nc})--({nd})--cycle;");
            sb.AppendLine(@"\end{tikzpicture}");
            return sb.ToString().TrimEnd();
        }

        public static string GenerateCircle(double cx, double cy, double radius, string label = "O")
        {
            var sb = new StringBuilder();
            sb.AppendLine(@"\begin{tikzpicture}[scale=1, thick]");
            sb.AppendLine($@"  \coordinate ({label}) at ({F(cx)},{F(cy)});");
            sb.AppendLine($@"  \draw ({label}) circle ({F(radius)}cm);");
            sb.AppendLine($@"  \fill ({label}) circle (1.5pt) node[below left]{{${label}$}};");
            sb.AppendLine($@"  \draw[dashed] ({label}) -- +({F(radius)},0) node[midway, above]{{$R={F(radius)}$}};");
            sb.AppendLine(@"\end{tikzpicture}");
            return sb.ToString().TrimEnd();
        }

        public static string GenerateOxyAxis(double xmin = -4, double xmax = 4, double ymin = -3, double ymax = 4)
        {
            var sb = new StringBuilder();
            sb.AppendLine(@"\begin{tikzpicture}[scale=1, >=stealth]");
            sb.AppendLine($@"  \draw[->, thick] ({F(xmin)},0) -- ({F(xmax)},0) node[right]{{$x$}};");
            sb.AppendLine($@"  \draw[->, thick] (0,{F(ymin)}) -- (0,{F(ymax)}) node[above]{{$y$}};");
            sb.AppendLine(@"  \node[below left] at (0,0) {$O$};");
            sb.AppendLine($@"  \draw[thin, gray!40, dashed] ({F(xmin)},{F(ymin)}) grid ({F(xmax)},{F(ymax)});");
            sb.AppendLine(@"\end{tikzpicture}");
            return sb.ToString().TrimEnd();
        }

        // ══════════════════════════════════════════════════════════════════════════
        // 2. HÌNH HỌC KHÔNG GIAN 3D
        // ══════════════════════════════════════════════════════════════════════════

        public static string GeneratePyramid(double side, double height,
            string na = "A", string nb = "B", string nc = "C", string nd = "D", string ns = "S")
        {
            double half = Math.Round(side / 2.0, 2);
            var sb = new StringBuilder();
            sb.AppendLine(@"\begin{tikzpicture}[scale=1.2, thick,");
            sb.AppendLine(@"    x={(1cm,0cm)}, y={(0.4cm,0.3cm)}, z={(0cm,1cm)}]");
            sb.AppendLine($@"  \coordinate[label=below left:${na}$]  ({na}) at (0,0,0);");
            sb.AppendLine($@"  \coordinate[label=below right:${nb}$] ({nb}) at ({F(side)},0,0);");
            sb.AppendLine($@"  \coordinate[label=right:${nc}$]       ({nc}) at ({F(side)},{F(side)},0);");
            sb.AppendLine($@"  \coordinate[label=left:${nd}$]        ({nd}) at (0,{F(side)},0);");
            sb.AppendLine($@"  \coordinate[label=above:${ns}$]       ({ns}) at ({F(half)},{F(half)},{F(height)});");
            sb.AppendLine(@"  % Đáy");
            sb.AppendLine($@"  \draw ({na})--({nb})--({nc});");
            sb.AppendLine($@"  \draw[dashed] ({nc})--({nd})--({na});");
            sb.AppendLine(@"  % Cạnh bên");
            sb.AppendLine($@"  \draw ({ns})--({na}) ({ns})--({nb}) ({ns})--({nc});");
            sb.AppendLine($@"  \draw[dashed] ({ns})--({nd});");
            sb.AppendLine($@"  \draw[dashed] ({na})--({nc}) ({nb})--({nd});");
            sb.AppendLine(@"\end{tikzpicture}");
            return sb.ToString().TrimEnd();
        }

        public static string GenerateTetrahedron(double side, double height,
            string na = "A", string nb = "B", string nc = "C", string ns = "S")
        {
            var sb = new StringBuilder();
            sb.AppendLine(@"\begin{tikzpicture}[scale=1.2, thick,");
            sb.AppendLine(@"    x={(1cm,0cm)}, y={(0.4cm,0.3cm)}, z={(0cm,1cm)}]");
            sb.AppendLine($@"  \coordinate[label=below left:${na}$]  ({na}) at (0,0,0);");
            sb.AppendLine($@"  \coordinate[label=below right:${nb}$] ({nb}) at ({F(side)},0,0);");
            sb.AppendLine($@"  \coordinate[label=above right:${nc}$] ({nc}) at ({F(side * 0.6)},{F(side)},0);");
            sb.AppendLine($@"  \coordinate[label=above:${ns}$]       ({ns}) at (0,0,{F(height)});");
            sb.AppendLine(@"  % Đáy tam giác");
            sb.AppendLine($@"  \draw ({na})--({nb});");
            sb.AppendLine($@"  \draw[dashed] ({nb})--({nc})--({na});");
            sb.AppendLine(@"  % Các cạnh bên");
            sb.AppendLine($@"  \draw ({ns})--({na}) ({ns})--({nb});");
            sb.AppendLine($@"  \draw[dashed] ({ns})--({nc});");
            sb.AppendLine(@"\end{tikzpicture}");
            return sb.ToString().TrimEnd();
        }

        public static string GenerateCuboid(double a, double b, double h,
            string na = "A", string nb = "B", string nc = "C", string nd = "D")
        {
            var sb = new StringBuilder();
            sb.AppendLine(@"\begin{tikzpicture}[scale=1.1, thick,");
            sb.AppendLine(@"    x={(1cm,0cm)}, y={(0.4cm,0.3cm)}, z={(0cm,1cm)}]");
            sb.AppendLine($@"  \coordinate[label=below left:${na}$]   ({na}) at (0,0,0);");
            sb.AppendLine($@"  \coordinate[label=below right:${nb}$]  ({nb}) at ({F(a)},0,0);");
            sb.AppendLine($@"  \coordinate[label=right:${nc}$]        ({nc}) at ({F(a)},{F(b)},0);");
            sb.AppendLine($@"  \coordinate[label=left:${nd}$]         ({nd}) at (0,{F(b)},0);");
            sb.AppendLine($@"  \coordinate[label=above left:${na}'$]  ({na}1) at (0,0,{F(h)});");
            sb.AppendLine($@"  \coordinate[label=above right:${nb}'$] ({nb}1) at ({F(a)},0,{F(h)});");
            sb.AppendLine($@"  \coordinate[label=above right:${nc}'$] ({nc}1) at ({F(a)},{F(b)},{F(h)});");
            sb.AppendLine($@"  \coordinate[label=above left:${nd}'$]  ({nd}1) at (0,{F(b)},{F(h)});");
            sb.AppendLine(@"  % Đáy");
            sb.AppendLine($@"  \draw ({na})--({nb})--({nc});");
            sb.AppendLine($@"  \draw[dashed] ({nc})--({nd})--({na});");
            sb.AppendLine(@"  % Mặt trên");
            sb.AppendLine($@"  \draw ({na}1)--({nb}1)--({nc}1)--({nd}1)--cycle;");
            sb.AppendLine(@"  % Cạnh bên");
            sb.AppendLine($@"  \draw ({na})--({na}1) ({nb})--({nb}1) ({nc})--({nc}1);");
            sb.AppendLine($@"  \draw[dashed] ({nd})--({nd}1);");
            sb.AppendLine(@"\end{tikzpicture}");
            return sb.ToString().TrimEnd();
        }

        public static string GenerateCube(double side, string na = "A", string nb = "B", string nc = "C", string nd = "D")
        {
            return GenerateCuboid(side, side, side, na, nb, nc, nd);
        }

        public static string GenerateCylinder(double radius, double height)
        {
            double e = Math.Round(radius * 0.35, 2);
            var sb = new StringBuilder();
            sb.AppendLine(@"\begin{tikzpicture}[scale=1, thick, every node/.style={font=\normalsize}]");
            sb.AppendLine($@"  \coordinate (O) at (0,0);");
            sb.AppendLine($@"  \coordinate (O1) at (0,{F(height)});");
            sb.AppendLine($@"  % Đáy dưới: nửa sau đứt, nửa trước liền");
            sb.AppendLine($@"  \draw[dashed] (-{F(radius)},0) arc (180:0:{F(radius)}cm and {F(e)}cm);");
            sb.AppendLine($@"  \draw (-{F(radius)},0) arc (180:360:{F(radius)}cm and {F(e)}cm);");
            sb.AppendLine($@"  % Đáy trên thấy toàn phần");
            sb.AppendLine($@"  \draw (0,{F(height)}) ellipse ({F(radius)}cm and {F(e)}cm);");
            sb.AppendLine($@"  % Hai đường sinh biên");
            sb.AppendLine($@"  \draw (-{F(radius)},0)--(-{F(radius)},{F(height)});");
            sb.AppendLine($@"  \draw ({F(radius)},0)--({F(radius)},{F(height)});");
            sb.AppendLine($@"  % Trục và bán kính");
            sb.AppendLine($@"  \draw[dashed] (0,0)--(0,{F(height)});");
            sb.AppendLine($@"  \draw[dashed] (0,0)--({F(radius)},0) node[midway,below] {{$r$}};");
            sb.AppendLine($@"  \fill (0,0) circle (1.2pt) node[below] {{$O$}};");
            sb.AppendLine($@"  \fill (0,{F(height)}) circle (1.2pt) node[above] {{$O'$}};");
            sb.AppendLine($@"  \draw[<->] ({F(radius + 0.4)},0)--({F(radius + 0.4)},{F(height)}) node[midway,right] {{$h={F(height)}$}};");
            sb.AppendLine(@"\end{tikzpicture}");
            return sb.ToString().TrimEnd();
        }

        public static string GenerateCone(double radius, double height)
        {
            double e = Math.Round(radius * 0.35, 2);
            var sb = new StringBuilder();
            sb.AppendLine(@"\begin{tikzpicture}[scale=1, thick, every node/.style={font=\normalsize}]");
            sb.AppendLine($@"  \coordinate[label=above:$S$] (S) at (0,{F(height)});");
            sb.AppendLine($@"  \coordinate (O) at (0,0);");
            sb.AppendLine($@"  % Đáy elip: nửa sau đứt, nửa trước liền");
            sb.AppendLine($@"  \draw[dashed] (-{F(radius)},0) arc (180:0:{F(radius)}cm and {F(e)}cm);");
            sb.AppendLine($@"  \draw (-{F(radius)},0) arc (180:360:{F(radius)}cm and {F(e)}cm);");
            sb.AppendLine($@"  % Hai đường sinh biên");
            sb.AppendLine($@"  \draw (-{F(radius)},0)--(S)--({F(radius)},0);");
            sb.AppendLine($@"  % Trục và bán kính");
            sb.AppendLine($@"  \draw[dashed] (S)--(0,0);");
            sb.AppendLine($@"  \draw[dashed] (0,0)--({F(radius)},0) node[midway,below] {{$r$}};");
            sb.AppendLine($@"  \fill (0,0) circle (1.2pt) node[below right] {{$O$}};");
            sb.AppendLine($@"  \fill (S) circle (1.2pt);");
            sb.AppendLine($@"  \node[left] at (0,{F(height / 2.0)}) {{$h$}};");
            sb.AppendLine($@"  \node[above right] at ({F(radius / 2.0)},{F(height / 2.0)}) {{$\ell$}};");
            sb.AppendLine(@"\end{tikzpicture}");
            return sb.ToString().TrimEnd();
        }

        public static string GenerateSphere(double radius)
        {
            double e = Math.Round(radius * 0.35, 2);
            var sb = new StringBuilder();
            sb.AppendLine(@"\begin{tikzpicture}[scale=1, thick, every node/.style={font=\normalsize}]");
            sb.AppendLine($@"  \shade[ball color=cyan!15, opacity=0.35] (0,0) circle ({F(radius)}cm);");
            sb.AppendLine($@"  \draw (0,0) circle ({F(radius)}cm);");
            sb.AppendLine($@"  % Đường xích đạo: nửa sau đứt, nửa trước liền");
            sb.AppendLine($@"  \draw[dashed] (-{F(radius)},0) arc (180:0:{F(radius)}cm and {F(e)}cm);");
            sb.AppendLine($@"  \draw (-{F(radius)},0) arc (180:360:{F(radius)}cm and {F(e)}cm);");
            sb.AppendLine($@"  % Trục đứng nét đứt");
            sb.AppendLine($@"  \draw[dashed] (0,-{F(radius)})--(0,{F(radius)});");
            sb.AppendLine($@"  \draw[dashed] (0,0)--({F(radius)},0) node[midway,above] {{$R$}};");
            sb.AppendLine($@"  \fill (0,0) circle (1.2pt) node[below left] {{$O$}};");
            sb.AppendLine(@"\end{tikzpicture}");
            return sb.ToString().TrimEnd();
        }

        public static string GenerateConeFrustum(double bigR, double smallR, double height)
        {
            double e1 = Math.Round(bigR * 0.35, 2);
            double e2 = Math.Round(smallR * 0.35, 2);
            var sb = new StringBuilder();
            sb.AppendLine(@"\begin{tikzpicture}[scale=1, thick, every node/.style={font=\normalsize}]");
            sb.AppendLine($@"  \coordinate (O) at (0,0); \coordinate (O1) at (0,{F(height)});");
            sb.AppendLine($@"  % Đáy dưới");
            sb.AppendLine($@"  \draw[dashed] (-{F(bigR)},0) arc (180:0:{F(bigR)}cm and {F(e1)}cm);");
            sb.AppendLine($@"  \draw (-{F(bigR)},0) arc (180:360:{F(bigR)}cm and {F(e1)}cm);");
            sb.AppendLine($@"  % Đáy trên");
            sb.AppendLine($@"  \draw (O1) ellipse ({F(smallR)}cm and {F(e2)}cm);");
            sb.AppendLine($@"  % Đường sinh biên");
            sb.AppendLine($@"  \draw (-{F(bigR)},0)--(-{F(smallR)},{F(height)}) ({F(bigR)},0)--({F(smallR)},{F(height)});");
            sb.AppendLine($@"  % Trục và bán kính");
            sb.AppendLine($@"  \draw[dashed] (O)--(O1);");
            sb.AppendLine($@"  \draw[dashed] (O)--({F(bigR)},0) node[midway,below] {{$R$}};");
            sb.AppendLine($@"  \draw[dashed] (O1)--({F(smallR)},{F(height)}) node[midway,above] {{$r$}};");
            sb.AppendLine($@"  \fill (O) circle (1.2pt) node[below] {{$O$}};");
            sb.AppendLine($@"  \fill (O1) circle (1.2pt) node[above] {{$O'$}};");
            sb.AppendLine($@"  \draw[<->] ({F(bigR + 0.4)},0)--({F(bigR + 0.4)},{F(height)}) node[midway,right] {{$h$}};");
            sb.AppendLine(@"\end{tikzpicture}");
            return sb.ToString().TrimEnd();
        }

        public static string GenerateSpherePlaneSection(double radius, double cutDistance)
        {
            double d = Math.Min(cutDistance, radius * 0.85);
            double rSec = Math.Round(Math.Sqrt(Math.Max(0.1, radius * radius - d * d)), 2);
            double eSec = Math.Round(rSec * 0.35, 2);
            double eEq = Math.Round(radius * 0.35, 2);
            var sb = new StringBuilder();
            sb.AppendLine(@"\begin{tikzpicture}[scale=1.1, thick, every node/.style={font=\normalsize}]");
            sb.AppendLine($@"  \coordinate (O) at (0,0); \coordinate (H) at (0,{F(d)});");
            sb.AppendLine($@"  \coordinate (M) at ({F(rSec)},{F(d)});");
            sb.AppendLine($@"  \shade[ball color=cyan!15, opacity=0.3] (0,0) circle ({F(radius)}cm);");
            sb.AppendLine($@"  \draw (0,0) circle ({F(radius)}cm);");
            sb.AppendLine($@"  % Xích đạo");
            sb.AppendLine($@"  \draw[dashed, gray] (-{F(radius)},0) arc (180:0:{F(radius)}cm and {F(eEq)}cm);");
            sb.AppendLine($@"  \draw[gray] (-{F(radius)},0) arc (180:360:{F(radius)}cm and {F(eEq)}cm);");
            sb.AppendLine($@"  % Đường tròn thiết diện cắt tại H");
            sb.AppendLine($@"  \draw[dashed, blue] (-{F(rSec)},{F(d)}) arc (180:0:{F(rSec)}cm and {F(eSec)}cm);");
            sb.AppendLine($@"  \draw[blue] (-{F(rSec)},{F(d)}) arc (180:360:{F(rSec)}cm and {F(eSec)}cm);");
            sb.AppendLine($@"  % Tam giác vuông OHM");
            sb.AppendLine($@"  \draw[dashed, thick] (O)--(H) node[midway,left] {{$d$}} (H)--(M) node[midway,above] {{$r$}} (O)--(M) node[midway,below right] {{$R$}};");
            sb.AppendLine($@"  \fill (O) circle (1.2pt) node[below left] {{$O$}};");
            sb.AppendLine($@"  \fill (H) circle (1.2pt) node[above left] {{$H$}};");
            sb.AppendLine($@"  \fill (M) circle (1.2pt) node[right] {{$M$}};");
            sb.AppendLine(@"\end{tikzpicture}");
            return sb.ToString().TrimEnd();
        }

        public static string GenerateCylinderSection(double radius, double height, double chordDist = 0.8)
        {
            double d = Math.Min(chordDist, radius * 0.9);
            double halfChord = Math.Round(Math.Sqrt(Math.Max(0.1, radius * radius - d * d)), 2);
            double e = Math.Round(radius * 0.35, 2);
            var sb = new StringBuilder();
            sb.AppendLine(@"\begin{tikzpicture}[scale=1, thick, every node/.style={font=\normalsize}]");
            sb.AppendLine($@"  \coordinate (O) at (0,0); \coordinate (O1) at (0,{F(height)});");
            sb.AppendLine($@"  % Đáy dưới");
            sb.AppendLine($@"  \draw[dashed] (-{F(radius)},0) arc (180:0:{F(radius)}cm and {F(e)}cm);");
            sb.AppendLine($@"  \draw (-{F(radius)},0) arc (180:360:{F(radius)}cm and {F(e)}cm);");
            sb.AppendLine($@"  % Đáy trên");
            sb.AppendLine($@"  \draw (O1) ellipse ({F(radius)}cm and {F(e)}cm);");
            sb.AppendLine($@"  % Đường sinh biên");
            sb.AppendLine($@"  \draw (-{F(radius)},0)--(-{F(radius)},{F(height)}) ({F(radius)},0)--({F(radius)},{F(height)});");
            sb.AppendLine($@"  % Thiết diện song song trục ABB'A'");
            double yBottom = -Math.Round(e * (d / radius), 2);
            sb.AppendLine($@"  \coordinate (A) at (-{F(halfChord)},{F(yBottom)});");
            sb.AppendLine($@"  \coordinate (B) at ({F(halfChord)},{F(yBottom)});");
            sb.AppendLine($@"  \coordinate (B1) at ({F(halfChord)},{F(height + yBottom)});");
            sb.AppendLine($@"  \coordinate (A1) at (-{F(halfChord)},{F(height + yBottom)});");
            sb.AppendLine($@"  \fill[blue!15, opacity=0.5] (A)--(B)--(B1)--(A1)--cycle;");
            sb.AppendLine($@"  \draw[blue, thick] (A)--(B)--(B1)--(A1)--cycle;");
            sb.AppendLine($@"  \draw[dashed] (O)--(O1);");
            sb.AppendLine($@"  \fill (O) circle (1.2pt) node[below] {{$O$}};");
            sb.AppendLine($@"  \fill (O1) circle (1.2pt) node[above] {{$O'$}};");
            sb.AppendLine($@"  \node[below left] at (A) {{$A$}}; \node[below right] at (B) {{$B$}};");
            sb.AppendLine($@"  \node[above right] at (B1) {{$B'$}}; \node[above left] at (A1) {{$A'$}};");
            sb.AppendLine(@"\end{tikzpicture}");
            return sb.ToString().TrimEnd();
        }

        // ══════════════════════════════════════════════════════════════════════════
        // 3. BẢNG BIẾN THIÊN (tkz-tab)
        // ══════════════════════════════════════════════════════════════════════════

        public static string GenerateCubicTable(double a, double x1, double x2, double y1, double y2)
        {
            bool aPos = a > 0;
            var sb = new StringBuilder();
            sb.AppendLine(@"\begin{tikzpicture}");
            sb.AppendLine(@"  \tkzTabInit[lgt=1.5, espcl=2.5]");
            sb.AppendLine(@"    {$x$ / 0.8, $y'$ / 0.8, $y$ / 2}");
            sb.AppendLine($@"    {{$-\infty$, ${F(x1)}$, ${F(x2)}$, $+\infty$}}");
            sb.AppendLine(aPos ? @"  \tkzTabLine{, +, 0, -, 0, +, }" : @"  \tkzTabLine{, -, 0, +, 0, -, }");
            sb.AppendLine(aPos
                ? $@"  \tkzTabVar{{-/ $-\infty$, +/ ${F(y1)}$, -/ ${F(y2)}$, +/ $+\infty$}}"
                : $@"  \tkzTabVar{{+/ $+\infty$, -/ ${F(y1)}$, +/ ${F(y2)}$, -/ $-\infty$}}");
            sb.AppendLine(@"\end{tikzpicture}");
            return sb.ToString().TrimEnd();
        }

        public static string GenerateQuarticTable(double a, double x1, double x2, double x3, double y1, double y2, double y3)
        {
            bool aPos = a > 0;
            var sb = new StringBuilder();
            sb.AppendLine(@"\begin{tikzpicture}");
            sb.AppendLine(@"  \tkzTabInit[lgt=1.5, espcl=2.2]");
            sb.AppendLine(@"    {$x$ / 0.8, $y'$ / 0.8, $y$ / 2}");
            sb.AppendLine($@"    {{$-\infty$, ${F(x1)}$, ${F(x2)}$, ${F(x3)}$, $+\infty$}}");
            sb.AppendLine(aPos ? @"  \tkzTabLine{, -, 0, +, 0, -, 0, +, }" : @"  \tkzTabLine{, +, 0, -, 0, +, 0, -, }");
            sb.AppendLine(aPos
                ? $@"  \tkzTabVar{{+/ $+\infty$, -/ ${F(y1)}$, +/ ${F(y2)}$, -/ ${F(y3)}$, +/ $+\infty$}}"
                : $@"  \tkzTabVar{{-/ $-\infty$, +/ ${F(y1)}$, -/ ${F(y2)}$, +/ ${F(y3)}$, -/ $-\infty$}}");
            sb.AppendLine(@"\end{tikzpicture}");
            return sb.ToString().TrimEnd();
        }

        public static string GenerateRationalTable(double x0, double y0, bool isPositive)
        {
            var sb = new StringBuilder();
            sb.AppendLine(@"\begin{tikzpicture}");
            sb.AppendLine(@"  \tkzTabInit[lgt=1.5, espcl=3]");
            sb.AppendLine(@"    {$x$ / 0.8, $y'$ / 0.8, $y$ / 2}");
            sb.AppendLine($@"    {{$-\infty$, ${F(x0)}$, $+\infty$}}");
            sb.AppendLine(isPositive ? @"  \tkzTabLine{, +, d, +, }" : @"  \tkzTabLine{, -, d, -, }");
            sb.AppendLine(isPositive
                ? $@"  \tkzTabVar{{-/ ${F(y0)}$, +D-/ $+\infty$ / $-\infty$, +/ ${F(y0)}$}}"
                : $@"  \tkzTabVar{{+/ ${F(y0)}$, -D+/ $-\infty$ / $+\infty$, -/ ${F(y0)}$}}");
            sb.AppendLine(@"\end{tikzpicture}");
            return sb.ToString().TrimEnd();
        }

        public static string GenerateSignTableLinear(double x0, bool isPositive)
        {
            var sb = new StringBuilder();
            sb.AppendLine(@"\begin{tikzpicture}");
            sb.AppendLine(@"  \tkzTabInit[lgt=1.5, espcl=3]");
            sb.AppendLine(@"    {$x$ / 0.8, $f(x)$ / 0.8}");
            sb.AppendLine($@"    {{$-\infty$, ${F(x0)}$, $+\infty$}}");
            sb.AppendLine(isPositive ? @"  \tkzTabLine{, -, 0, +, }" : @"  \tkzTabLine{, +, 0, -, }");
            sb.AppendLine(@"\end{tikzpicture}");
            return sb.ToString().TrimEnd();
        }

        public static string GenerateSignTableQuadratic(double x1, double x2, bool isPositive)
        {
            var sb = new StringBuilder();
            sb.AppendLine(@"\begin{tikzpicture}");
            sb.AppendLine(@"  \tkzTabInit[lgt=1.5, espcl=2.5]");
            sb.AppendLine(@"    {$x$ / 0.8, $f(x)$ / 0.8}");
            sb.AppendLine($@"    {{$-\infty$, ${F(x1)}$, ${F(x2)}$, $+\infty$}}");
            sb.AppendLine(isPositive ? @"  \tkzTabLine{, +, 0, -, 0, +, }" : @"  \tkzTabLine{, -, 0, +, 0, -, }");
            sb.AppendLine(@"\end{tikzpicture}");
            return sb.ToString().TrimEnd();
        }

        // ══════════════════════════════════════════════════════════════════════════
        // 4. ĐỒ THỊ HÀM SỐ (pgfplots)
        // ══════════════════════════════════════════════════════════════════════════

        public static string GenerateParabolaGraph(double a, double b, double c, double xmin = -4, double xmax = 4)
        {
            var sb = new StringBuilder();
            sb.AppendLine(@"\begin{tikzpicture}");
            sb.AppendLine(@"  \begin{axis}[");
            sb.AppendLine(@"    axis lines=center, xlabel={$x$}, ylabel={$y$},");
            sb.AppendLine($@"    xmin={F(xmin)}, xmax={F(xmax)},");
            sb.AppendLine(@"    grid=major, grid style={gray!30},");
            sb.AppendLine(@"    width=9cm, height=7cm, samples=100");
            sb.AppendLine(@"  ]");
            sb.AppendLine($@"    \addplot[blue, very thick, domain={F(xmin)}:{F(xmax)}] {{{F(a)}*x^2 + ({F(b)})*x + ({F(c)})}};");
            sb.AppendLine(@"  \end{axis}");
            sb.AppendLine(@"\end{tikzpicture}");
            return sb.ToString().TrimEnd();
        }

        public static string GenerateCubicGraph(double a, double b, double c, double d, double xmin = -3, double xmax = 3)
        {
            var sb = new StringBuilder();
            sb.AppendLine(@"\begin{tikzpicture}");
            sb.AppendLine(@"  \begin{axis}[");
            sb.AppendLine(@"    axis lines=center, xlabel={$x$}, ylabel={$y$},");
            sb.AppendLine($@"    xmin={F(xmin)}, xmax={F(xmax)},");
            sb.AppendLine(@"    grid=major, grid style={gray!30},");
            sb.AppendLine(@"    width=9cm, height=7cm, samples=100");
            sb.AppendLine(@"  ]");
            sb.AppendLine($@"    \addplot[red, very thick, domain={F(xmin)}:{F(xmax)}] {{{F(a)}*x^3 + ({F(b)})*x^2 + ({F(c)})*x + ({F(d)})}};");
            sb.AppendLine(@"  \end{axis}");
            sb.AppendLine(@"\end{tikzpicture}");
            return sb.ToString().TrimEnd();
        }
    }
}
