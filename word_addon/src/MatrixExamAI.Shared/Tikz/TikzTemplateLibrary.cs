using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.RegularExpressions;

namespace MatrixExamAI.Shared.Tikz
{
    /// <summary>
    /// Thư viện mẫu hình vẽ và bảng toán học TikZ phong phú, kế thừa từ kho tri thức THPT.
    /// Cung cấp hơn 40 mẫu hình học phẳng, không gian, đồ thị, bảng biến thiên tkz-tab và biểu đồ.
    /// </summary>
    public static class TikzTemplateLibrary
    {
        private static readonly List<TikzTemplateCategory> _categories = new List<TikzTemplateCategory>();
        private static readonly Dictionary<string, TikzTemplate> _idLookup = new Dictionary<string, TikzTemplate>(StringComparer.OrdinalIgnoreCase);
        private static readonly Dictionary<string, TikzTemplate> _titleLookup = new Dictionary<string, TikzTemplate>(StringComparer.OrdinalIgnoreCase);

        static TikzTemplateLibrary()
        {
            InitializeCategories();
        }

        /// <summary>
        /// Danh sách tất cả các chuyên đề mẫu TikZ.
        /// </summary>
        public static IReadOnlyList<TikzTemplateCategory> Categories => _categories;

        /// <summary>
        /// Danh sách toàn bộ các mẫu hình vẽ TikZ trong thư viện.
        /// </summary>
        public static IReadOnlyList<TikzTemplate> AllTemplates => _idLookup.Values.ToList();

        /// <summary>
        /// Tra cứu mẫu theo Id.
        /// </summary>
        public static TikzTemplate? FindById(string id)
        {
            if (string.IsNullOrWhiteSpace(id)) return null;
            return _idLookup.TryGetValue(id, out var tpl) ? tpl : null;
        }

        /// <summary>
        /// Tra cứu mẫu theo Tiêu đề.
        /// </summary>
        public static TikzTemplate? FindByTitle(string title)
        {
            if (string.IsNullOrWhiteSpace(title)) return null;
            return _titleLookup.TryGetValue(title, out var tpl) ? tpl : null;
        }

        /// <summary>
        /// Tìm kiếm mẫu theo từ khóa (tiêu đề, mô tả, thẻ).
        /// </summary>
        public static IReadOnlyList<TikzTemplate> Search(string query)
        {
            if (string.IsNullOrWhiteSpace(query)) return AllTemplates;
            string q = query.Trim().ToLowerInvariant();
            return _idLookup.Values
                .Where(t => t.Title.ToLowerInvariant().Contains(q)
                         || t.Description.ToLowerInvariant().Contains(q)
                         || t.Tags.Any(tag => tag.ToLowerInvariant().Contains(q)))
                .ToList();
        }

        private static void InitializeCategories()
        {
            _categories.Clear();
            _idLookup.Clear();
            _titleLookup.Clear();

            // =========================================================================
            // 1. HÌNH HỌC PHẲNG 2D (Plane Geometry)
            // =========================================================================
            var cat2d = new TikzTemplateCategory
            {
                Id = "plane_2d",
                Name = "Hình học phẳng 2D",
                Icon = "Shapes24"
            };

            cat2d.Templates.Add(new TikzTemplate
            {
                Id = "tri_right",
                Title = "Tam giác vuông ABC tại A",
                CategoryId = cat2d.Id,
                CategoryName = cat2d.Name,
                Tags = new[] { "2D", "tam giác", "tam giác vuông", "hình phẳng" },
                Description = "Tam giác vuông tại đỉnh A với ký hiệu pic right angle và nhãn độ dài cạnh",
                Code = @"\begin{tikzpicture}[scale=1.5, thick]
  \coordinate[label=below left:$A$]  (A) at (0,0);
  \coordinate[label=below right:$B$] (B) at (3,0);
  \coordinate[label=above left:$C$]  (C) at (0,2);
  \draw (A)--(B)--(C)--cycle;
  \draw pic [draw, angle radius=4mm, ""$\cdot$"" anchor=north east, """" pos=0.5]
    {right angle = B--A--C};
  \node at (1.5,0)   [below]  {$c$};
  \node at (0,1)     [left]   {$b$};
  \node at (1.55,1)  [above right] {$a$};
\end{tikzpicture}"
            });

            cat2d.Templates.Add(new TikzTemplate
            {
                Id = "tri_equilateral",
                Title = "Tam giác đều ABC",
                CategoryId = cat2d.Id,
                CategoryName = cat2d.Name,
                Tags = new[] { "2D", "tam giác", "tam giác đều", "đều" },
                Description = "Tam giác đều 3 cạnh bằng nhau, 3 góc 60 độ có cung đánh dấu",
                Code = @"\begin{tikzpicture}[scale=1.5, thick]
  \coordinate[label=above:$A$]      (A) at (2,3.464);
  \coordinate[label=below left:$B$] (B) at (0,0);
  \coordinate[label=below right:$C$](C) at (4,0);
  \draw (A)--(B)--(C)--cycle;
  \pic[draw, angle radius=6mm, ""$60^\circ$""] {angle=B--A--C};
  \pic[draw, angle radius=6mm, ""$60^\circ$""] {angle=C--B--A};
  \pic[draw, angle radius=6mm, ""$60^\circ$""] {angle=A--C--B};
\end{tikzpicture}"
            });

            cat2d.Templates.Add(new TikzTemplate
            {
                Id = "tri_isosceles",
                Title = "Tam giác cân ABC tại A",
                CategoryId = cat2d.Id,
                CategoryName = cat2d.Name,
                Tags = new[] { "2D", "tam giác", "tam giác cân", "đường cao" },
                Description = "Tam giác cân tại A kèm đường cao AH vuông góc cạnh đáy BC",
                Code = @"\begin{tikzpicture}[scale=1.5, thick]
  \coordinate[label=above:$A$]      (A) at (2,3);
  \coordinate[label=below left:$B$] (B) at (0,0);
  \coordinate[label=below right:$C$](C) at (4,0);
  \coordinate[label=below:$H$]      (H) at (2,0);
  \draw (A)--(B)--(C)--cycle;
  \draw[dashed] (A)--(H);
  \draw pic [draw, angle radius=3mm] {right angle = A--H--C};
\end{tikzpicture}"
            });

            cat2d.Templates.Add(new TikzTemplate
            {
                Id = "tri_centroid",
                Title = "Tam giác có trọng tâm G",
                CategoryId = cat2d.Id,
                CategoryName = cat2d.Name,
                Tags = new[] { "2D", "tam giác", "trọng tâm", "trung tuyến" },
                Description = "Tam giác ABC cùng 3 đường trung tuyến cắt nhau tại trọng tâm G",
                Code = @"\begin{tikzpicture}[scale=1.2, thick]
  \coordinate[label=above:$A$]       (A) at (0, 3.464);
  \coordinate[label=below left:$B$]  (B) at (-2, 0);
  \coordinate[label=below right:$C$] (C) at (2, 0);
  \coordinate[label=below:$M$]       (M) at (0, 0);
  \coordinate[label=above right:$N$] (N) at (1, 1.732);
  \coordinate[label=above left:$P$]  (P) at (-1, 1.732);
  \coordinate (G) at (0, 1.155);
  \draw (A)--(B)--(C)--cycle;
  \draw[dashed] (A)--(M);
  \draw[dashed] (B)--(N);
  \draw[dashed] (C)--(P);
  \fill (G) circle (1.5pt) node[above right=1pt] {$G$};
\end{tikzpicture}"
            });

            cat2d.Templates.Add(new TikzTemplate
            {
                Id = "tri_orthocenter",
                Title = "Tam giác có trực tâm H",
                CategoryId = cat2d.Id,
                CategoryName = cat2d.Name,
                Tags = new[] { "2D", "tam giác", "trực tâm", "đường cao" },
                Description = "Tam giác ABC với đường cao hạ từ các đỉnh cắt nhau tại trực tâm H",
                Code = @"\begin{tikzpicture}[scale=1.2, thick]
  \coordinate[label=above:$A$]       (A) at (1, 3);
  \coordinate[label=below left:$B$]  (B) at (-1, 0);
  \coordinate[label=below right:$C$] (C) at (3, 0);
  \coordinate[label=below:$A'$]      (Ap) at (1, 0);
  \draw (A)--(B)--(C)--cycle;
  \draw[dashed] (A)--(Ap);
  \coordinate[label=right:$H$] (H) at (1, 0.67);
  \fill (H) circle (1.5pt);
  \draw pic [draw, angle radius=3mm] {right angle = A--Ap--C};
\end{tikzpicture}"
            });

            cat2d.Templates.Add(new TikzTemplate
            {
                Id = "circle_circumscribed",
                Title = "Đường tròn ngoại tiếp tam giác",
                CategoryId = cat2d.Id,
                CategoryName = cat2d.Name,
                Tags = new[] { "2D", "đường tròn", "ngoại tiếp", "tam giác" },
                Description = "Đường tròn tâm O đi qua ba đỉnh của tam giác ABC",
                Code = @"\begin{tikzpicture}[scale=1.4, thick]
  \coordinate (A) at (0,0);
  \coordinate (B) at (4,0);
  \coordinate (C) at (1,3);
  \draw (A)--(B)--(C)--cycle;
  \coordinate (O) at (2,0.8);
  \draw[densely dashed] (O) circle (2.2cm);
  \fill (O) circle (1.5pt) node[below right] {$O$};
  \fill (A) circle (1.2pt) node[below left] {$A$};
  \fill (B) circle (1.2pt) node[below right] {$B$};
  \fill (C) circle (1.2pt) node[above] {$C$};
\end{tikzpicture}"
            });

            cat2d.Templates.Add(new TikzTemplate
            {
                Id = "circle_inscribed",
                Title = "Đường tròn nội tiếp tam giác",
                CategoryId = cat2d.Id,
                CategoryName = cat2d.Name,
                Tags = new[] { "2D", "đường tròn", "nội tiếp", "tam giác" },
                Description = "Đường tròn tâm I tiếp xúc ba cạnh của tam giác ABC",
                Code = @"\begin{tikzpicture}[scale=1.4, thick]
  \coordinate[label=below left:$A$]  (A) at (0,0);
  \coordinate[label=below right:$B$] (B) at (4,0);
  \coordinate[label=above:$C$]       (C) at (1.5,3);
  \draw (A)--(B)--(C)--cycle;
  \coordinate[label=below right:$I$] (I) at (1.7,1.0);
  \draw[blue, thick] (I) circle (1cm);
  \fill (I) circle (1.5pt);
\end{tikzpicture}"
            });

            cat2d.Templates.Add(new TikzTemplate
            {
                Id = "quad_cyclic",
                Title = "Tứ giác nội tiếp đường tròn ABCD",
                CategoryId = cat2d.Id,
                CategoryName = cat2d.Name,
                Tags = new[] { "2D", "tứ giác", "tứ giác nội tiếp", "đường tròn" },
                Description = "Bốn đỉnh A, B, C, D nằm trên đường tròn tâm O",
                Code = @"\begin{tikzpicture}[scale=1.4, thick]
  \coordinate (O) at (0,0);
  \draw[densely dashed] (O) circle (2cm);
  \coordinate[label=left:$A$]        (A) at (160:2);
  \coordinate[label=below left:$B$]  (B) at (220:2);
  \coordinate[label=below right:$C$] (C) at (-30:2);
  \coordinate[label=above:$D$]       (D) at (60:2);
  \draw (A)--(B)--(C)--(D)--cycle;
  \fill (A) circle (1.2pt); \fill (B) circle (1.2pt);
  \fill (C) circle (1.2pt); \fill (D) circle (1.2pt);
  \fill (O) circle (1.2pt) node[below right] {$O$};
\end{tikzpicture}"
            });

            cat2d.Templates.Add(new TikzTemplate
            {
                Id = "trapezoid_isosceles",
                Title = "Hình thang cân ABCD",
                CategoryId = cat2d.Id,
                CategoryName = cat2d.Name,
                Tags = new[] { "2D", "hình thang", "hình thang cân", "tứ giác" },
                Description = "Hình thang cân hai cạnh bên bằng nhau và hai đường chéo bằng nhau",
                Code = @"\begin{tikzpicture}[scale=1.2, thick]
  \coordinate[label=below left:$A$]  (A) at (0,0);
  \coordinate[label=below right:$B$] (B) at (5,0);
  \coordinate[label=above right:$C$] (C) at (4,2.5);
  \coordinate[label=above left:$D$]  (D) at (1,2.5);
  \draw (A)--(B)--(C)--(D)--cycle;
  \draw[dashed, blue] (A)--(C);
  \draw[dashed, blue] (B)--(D);
\end{tikzpicture}"
            });

            cat2d.Templates.Add(new TikzTemplate
            {
                Id = "trapezoid_right",
                Title = "Hình thang vuông ABCD",
                CategoryId = cat2d.Id,
                CategoryName = cat2d.Name,
                Tags = new[] { "2D", "hình thang", "hình thang vuông", "tứ giác" },
                Description = "Hình thang vuông tại hai đỉnh kề một cạnh bên AD",
                Code = @"\begin{tikzpicture}[scale=1.2, thick]
  \coordinate[label=below left:$A$]  (A) at (0,0);
  \coordinate[label=below right:$B$] (B) at (4,0);
  \coordinate[label=above right:$C$] (C) at (2.5,2.5);
  \coordinate[label=above left:$D$]  (D) at (0,2.5);
  \draw (A)--(B)--(C)--(D)--cycle;
  \draw pic [draw, angle radius=3mm] {right angle = B--A--D};
  \draw pic [draw, angle radius=3mm] {right angle = A--D--C};
\end{tikzpicture}"
            });

            cat2d.Templates.Add(new TikzTemplate
            {
                Id = "parallelogram",
                Title = "Hình bình hành ABCD",
                CategoryId = cat2d.Id,
                CategoryName = cat2d.Name,
                Tags = new[] { "2D", "hình bình hành", "tứ giác", "đường chéo" },
                Description = "Hình bình hành hai đường chéo cắt nhau tại trung điểm O",
                Code = @"\begin{tikzpicture}[scale=1.2, thick]
  \coordinate[label=below left:$A$] (A) at (0,0);
  \coordinate[label=below right:$B$] (B) at (4,0);
  \coordinate[label=above right:$C$] (C) at (5,2);
  \coordinate[label=above left:$D$] (D) at (1,2);
  \draw (A)--(B)--(C)--(D)--cycle;
  \draw[dashed] (A)--(C) (B)--(D);
  \node at (2.5,1) [above] {$O$};
\end{tikzpicture}"
            });

            cat2d.Templates.Add(new TikzTemplate
            {
                Id = "rhombus",
                Title = "Hình thoi ABCD",
                CategoryId = cat2d.Id,
                CategoryName = cat2d.Name,
                Tags = new[] { "2D", "hình thoi", "tứ giác", "vuông góc" },
                Description = "Hình thoi có bốn cạnh bằng nhau, hai đường chéo vuông góc",
                Code = @"\begin{tikzpicture}[scale=1.2, thick]
  \coordinate[label=below:$A$] (A) at (0,0);
  \coordinate[label=right:$B$] (B) at (2,1.5);
  \coordinate[label=above:$C$] (C) at (0,3);
  \coordinate[label=left:$D$] (D) at (-2,1.5);
  \draw (A)--(B)--(C)--(D)--cycle;
  \draw[dashed] (A)--(C) (B)--(D);
  \node at (0,1.5) [below right] {$O$};
\end{tikzpicture}"
            });

            cat2d.Templates.Add(new TikzTemplate
            {
                Id = "circle_tangents",
                Title = "Hai tiếp tuyến từ điểm M",
                CategoryId = cat2d.Id,
                CategoryName = cat2d.Name,
                Tags = new[] { "2D", "đường tròn", "tiếp tuyến", "góc vuông" },
                Description = "Hai tiếp tuyến MA, MB kẻ từ điểm M bên ngoài đường tròn tâm O",
                Code = @"\begin{tikzpicture}[scale=1.1, thick]
  \coordinate (O) at (0,0);
  \draw (O) circle (1.5cm);
  \fill (O) circle (1.5pt) node[below left] {$O$};
  \coordinate[label=right:$M$] (M) at (4,0);
  \fill (M) circle (1.5pt);
  \coordinate[label=above right:$A$] (A) at ({1.5*cos(67.98)}, {1.5*sin(67.98)});
  \coordinate[label=below right:$B$] (B) at ({1.5*cos(-67.98)}, {1.5*sin(-67.98)});
  \fill (A) circle (1.2pt);
  \fill (B) circle (1.2pt);
  \draw (M)--(A);
  \draw (M)--(B);
  \draw[dashed] (O)--(A);
  \draw[dashed] (O)--(B);
  \draw[dashed] (O)--(M);
  \draw pic [draw, angle radius=2.5mm] {right angle = O--A--M};
  \draw pic [draw, angle radius=2.5mm] {right angle = O--B--M};
\end{tikzpicture}"
            });

            _categories.Add(cat2d);

            // =========================================================================
            // 2. HÌNH HỌC KHÔNG GIAN 3D (Solid Geometry - Cabinet Projection)
            // =========================================================================
            var cat3d = new TikzTemplateCategory
            {
                Id = "solid_3d",
                Name = "Hình học không gian 3D",
                Icon = "Cube24"
            };

            cat3d.Templates.Add(new TikzTemplate
            {
                Id = "pyramid_triangular",
                Title = "Hình chóp tam giác S.ABC",
                CategoryId = cat3d.Id,
                CategoryName = cat3d.Name,
                Tags = new[] { "3D", "hình chóp", "S.ABC", "không gian" },
                Description = "Hình chóp tam giác S.ABC với nét đứt cạnh khuất chuẩn Cabinet",
                Code = @"\begin{tikzpicture}[scale=1.2, thick,
    x={(1cm,0cm)}, y={(0.5cm,0.3cm)}, z={(0cm,1cm)}]
  \coordinate[label=below left:$A$]  (A) at (0,0,0);
  \coordinate[label=below right:$B$] (B) at (3,0,0);
  \coordinate[label=right:$C$]       (C) at (1.5,2.5,0);
  \coordinate[label=above:$S$]       (S) at (1.2,1,3.5);
  \draw (A)--(B)--(C);
  \draw[dashed] (C)--(A);
  \draw (S)--(A) (S)--(B) (S)--(C);
\end{tikzpicture}"
            });

            cat3d.Templates.Add(new TikzTemplate
            {
                Id = "pyramid_sa_perp",
                Title = "Hình chóp S.ABC có SA vuông góc đáy",
                CategoryId = cat3d.Id,
                CategoryName = cat3d.Name,
                Tags = new[] { "3D", "hình chóp", "SA vuông góc", "đường cao" },
                Description = "Hình chóp tam giác có cạnh bên SA vuông góc với mặt phẳng đáy (ABC)",
                Code = @"\begin{tikzpicture}[scale=1.2, thick,
    x={(1cm,0cm)}, y={(0.5cm,0.3cm)}, z={(0cm,1cm)}]
  \coordinate[label=below left:$A$]  (A) at (0,0,0);
  \coordinate[label=below right:$B$] (B) at (3.5,0,0);
  \coordinate[label=right:$C$]       (C) at (1.5,2.5,0);
  \coordinate[label=above:$S$]       (S) at (0,0,3.5);
  \draw (A)--(B)--(C);
  \draw[dashed] (A)--(C);
  \draw (S)--(A) (S)--(B) (S)--(C);
  \draw pic [draw, angle radius=3mm] {right angle = S--A--B};
\end{tikzpicture}"
            });

            cat3d.Templates.Add(new TikzTemplate
            {
                Id = "pyramid_quadrilateral",
                Title = "Hình chóp tứ giác S.ABCD",
                CategoryId = cat3d.Id,
                CategoryName = cat3d.Name,
                Tags = new[] { "3D", "hình chóp", "S.ABCD", "đáy tứ giác" },
                Description = "Hình chóp tứ giác S.ABCD có đáy là hình bình hành",
                Code = @"\begin{tikzpicture}[scale=1.3, thick,
    x={(1cm,0cm)}, y={(0.5cm,0.3cm)}, z={(0cm,1cm)}]
  \coordinate[label=below left:$A$]  (A) at (0,0,0);
  \coordinate[label=below right:$B$] (B) at (3,0,0);
  \coordinate[label=right:$C$]       (C) at (3,3,0);
  \coordinate[label=above left:$D$]  (D) at (0,3,0);
  \coordinate[label=above:$S$]       (S) at (1.5,1.5,4);
  \draw (A)--(B)--(C);
  \draw[dashed] (C)--(D)--(A);
  \draw (S)--(A) (S)--(B) (S)--(C);
  \draw[dashed] (S)--(D);
\end{tikzpicture}"
            });

            cat3d.Templates.Add(new TikzTemplate
            {
                Id = "pyramid_regular_quad",
                Title = "Hình chóp tứ giác đều S.ABCD",
                CategoryId = cat3d.Id,
                CategoryName = cat3d.Name,
                Tags = new[] { "3D", "chóp đều", "tứ giác đều", "đường cao SH" },
                Description = "Hình chóp tứ giác đều S.ABCD với đường cao SH vuông góc tâm đáy",
                Code = @"\begin{tikzpicture}[scale=1.3, thick,
    x={(1cm,0cm)}, y={(0.5cm,0.3cm)}, z={(0cm,1cm)}]
  \coordinate[label=below left:$A$]  (A) at (0,0,0);
  \coordinate[label=below right:$B$] (B) at (3,0,0);
  \coordinate[label=right:$C$]       (C) at (3,3,0);
  \coordinate[label=above left:$D$]  (D) at (0,3,0);
  \coordinate[label=above:$S$]       (S) at (1.5,1.5,4);
  \coordinate (H) at (1.5,1.5,0);
  \draw (A)--(B)--(C);
  \draw[dashed] (C)--(D)--(A);
  \draw (S)--(A) (S)--(B) (S)--(C);
  \draw[dashed] (S)--(D);
  \draw[dashed] (S)--(H);
  \fill (H) circle (1.2pt) node[below right] {$H$};
  \draw[densely dotted] (A)--(C);
  \draw[densely dotted] (B)--(D);
\end{tikzpicture}"
            });

            cat3d.Templates.Add(new TikzTemplate
            {
                Id = "prism_triangular",
                Title = "Hình lăng trụ tam giác ABC.A'B'C'",
                CategoryId = cat3d.Id,
                CategoryName = cat3d.Name,
                Tags = new[] { "3D", "lăng trụ", "lăng trụ tam giác" },
                Description = "Hình lăng trụ tam giác xiên hoặc đứng ABC.A'B'C'",
                Code = @"\begin{tikzpicture}[scale=1.2, thick,
    x={(1cm,0cm)}, y={(0.5cm,0.3cm)}, z={(0cm,1cm)}]
  \coordinate[label=below left:$A$]  (A) at (0,0,0);
  \coordinate[label=below right:$B$] (B) at (3,0,0);
  \coordinate[label=right:$C$]       (C) at (1.7,2.5,0);
  \coordinate[label=above left:$A'$]  (A1) at (0,0,3);
  \coordinate[label=above right:$B'$] (B1) at (3,0,3);
  \coordinate[label=above:$C'$]       (C1) at (1.7,2.5,3);
  \draw (A)--(B)--(C);
  \draw (A)--(A1) (B)--(B1) (C)--(C1);
  \draw (A1)--(B1)--(C1)--cycle;
  \draw[dashed] (C)--(A);
\end{tikzpicture}"
            });

            cat3d.Templates.Add(new TikzTemplate
            {
                Id = "prism_right_quad",
                Title = "Hình lăng trụ đứng ABCD.A'B'C'D'",
                CategoryId = cat3d.Id,
                CategoryName = cat3d.Name,
                Tags = new[] { "3D", "lăng trụ đứng", "tứ giác", "hộp" },
                Description = "Hình lăng trụ đứng tứ giác có các cạnh bên vuông góc với mặt đáy",
                Code = @"\begin{tikzpicture}[scale=1.1, thick,
    x={(1cm,0cm)}, y={(0.5cm,0.3cm)}, z={(0cm,1cm)}]
  \coordinate[label=below left:$A$]  (A) at (0,0,0);
  \coordinate[label=below right:$B$] (B) at (3,0,0);
  \coordinate[label=right:$C$]       (C) at (3,2.5,0);
  \coordinate[label=above left:$D$]  (D) at (0,2.5,0);
  \coordinate[label=above left:$A'$]  (A1) at (0,0,3);
  \coordinate[label=above right:$B'$] (B1) at (3,0,3);
  \coordinate[label=right:$C'$]       (C1) at (3,2.5,3);
  \coordinate[label=above:$D'$]       (D1) at (0,2.5,3);
  \draw (A)--(B)--(C);
  \draw[dashed] (C)--(D)--(A);
  \draw (A)--(A1) (B)--(B1) (C)--(C1);
  \draw[dashed] (D)--(D1);
  \draw (A1)--(B1)--(C1)--(D1)--cycle;
\end{tikzpicture}"
            });

            cat3d.Templates.Add(new TikzTemplate
            {
                Id = "cube",
                Title = "Hình lập phương ABCD.A'B'C'D'",
                CategoryId = cat3d.Id,
                CategoryName = cat3d.Name,
                Tags = new[] { "3D", "lập phương", "khối đa diện đều" },
                Description = "Khối lập phương 6 mặt hình vuông với phép chiếu Cabinet chuẩn",
                Code = @"\begin{tikzpicture}[scale=1.1, thick,
    x={(1cm,0cm)}, y={(0.5cm,0.3cm)}, z={(0cm,1cm)}]
  \coordinate[label=below left:$A$]  (A) at (0,0,0);
  \coordinate[label=below right:$B$] (B) at (2.5,0,0);
  \coordinate[label=right:$C$]       (C) at (2.5,2.5,0);
  \coordinate[label=above left:$D$]  (D) at (0,2.5,0);
  \coordinate[label=above left:$A'$]  (A1) at (0,0,2.5);
  \coordinate[label=above right:$B'$] (B1) at (2.5,0,2.5);
  \coordinate[label=right:$C'$]       (C1) at (2.5,2.5,2.5);
  \coordinate[label=above:$D'$]       (D1) at (0,2.5,2.5);
  \draw (A)--(B)--(C);
  \draw[dashed] (C)--(D)--(A);
  \draw (A)--(A1) (B)--(B1) (C)--(C1);
  \draw[dashed] (D)--(D1);
  \draw (A1)--(B1)--(C1)--(D1)--cycle;
\end{tikzpicture}"
            });

            cat3d.Templates.Add(new TikzTemplate
            {
                Id = "cone",
                Title = "Hình nón tròn xoay",
                CategoryId = cat3d.Id,
                CategoryName = cat3d.Name,
                Tags = new[] { "3D", "hình nón", "nón tròn xoay", "khối tròn xoay" },
                Description = "Hình nón tròn xoay có bán kính đáy r, chiều cao h và đường sinh l",
                Code = @"\begin{tikzpicture}[scale=1.1, thick]
  \draw         (-2,0) arc (180:360:2cm and 0.6cm);
  \draw[dashed] (-2,0) arc (180:0  :2cm and 0.6cm);
  \coordinate[label=above:$S$] (S) at (0,3);
  \draw (-2,0) -- (S);
  \draw ( 2,0) -- (S);
  \fill (0,0) circle (1.5pt) node[below] {$O$};
  \draw[dashed] (S)--(0,0);
  \draw[<->] (0.1,0)--(2,0) node[midway, below] {$r$};
  \draw[<->] (-0.3,0)--(-0.3,3) node[midway, left] {$h$};
  \node[blue] at (1.3, 1.6) {$\ell$};
\end{tikzpicture}"
            });

            cat3d.Templates.Add(new TikzTemplate
            {
                Id = "cylinder",
                Title = "Hình trụ tròn xoay",
                CategoryId = cat3d.Id,
                CategoryName = cat3d.Name,
                Tags = new[] { "3D", "hình trụ", "trụ tròn xoay", "khối tròn xoay" },
                Description = "Hình trụ tròn xoay có trục OO', bán kính r và chiều cao h",
                Code = @"\begin{tikzpicture}[scale=1.1, thick]
  \draw         (-1.5,0) arc (180:360:1.5cm and 0.5cm);
  \draw[dashed] (-1.5,0) arc (180:0  :1.5cm and 0.5cm);
  \draw (0,3) ellipse (1.5cm and 0.5cm);
  \draw (-1.5,0) -- (-1.5,3);
  \draw ( 1.5,0) -- ( 1.5,3);
  \draw[dashed] (0,0)--(0,3);
  \fill (0,0) circle (1.5pt) node[below] {$O$};
  \fill (0,3) circle (1.5pt) node[above] {$O'$};
  \draw[<->] (0,0)--(1.5,0) node[midway, below] {$r$};
  \draw[<->] (1.8,0)--(1.8,3) node[midway, right] {$h$};
\end{tikzpicture}"
            });

            cat3d.Templates.Add(new TikzTemplate
            {
                Id = "sphere",
                Title = "Mặt cầu tâm O bán kính R",
                CategoryId = cat3d.Id,
                CategoryName = cat3d.Name,
                Tags = new[] { "3D", "mặt cầu", "hình cầu", "bán kính R" },
                Description = "Mặt cầu tròn xoay tâm O kèm đường tròn xích đạo elip và bán kính R",
                Code = @"\begin{tikzpicture}[scale=1.1, thick]
  \draw (0,0) circle (2cm);
  \draw         (-2,0) arc (180:360:2cm and 0.6cm);
  \draw[dashed] (-2,0) arc (180:0  :2cm and 0.6cm);
  \fill (0,0) circle (1.5pt) node[below right] {$O$};
  \draw[->, thick, blue] (0,0)--(50:2) node[midway, above left] {$R$};
\end{tikzpicture}"
            });

            cat3d.Templates.Add(new TikzTemplate
            {
                Id = "pyramid_regular_tri",
                Title = "Hình chóp tam giác đều S.ABC",
                CategoryId = cat3d.Id,
                CategoryName = cat3d.Name,
                Tags = new[] { "3D", "hình chóp", "chóp tam giác đều", "đáy đều", "trọng tâm H" },
                Description = "Hình chóp tam giác đều có đáy là tam giác đều và chân đường cao SH trùng với trọng tâm H",
                Code = @"\begin{tikzpicture}[scale=1.3, thick,
    x={(1cm,0cm)}, y={(0.5cm,0.3cm)}, z={(0cm,1cm)}]
  \coordinate[label=below left:$A$]  (A) at (0,0,0);
  \coordinate[label=below right:$B$] (B) at (3,0,0);
  \coordinate[label=above:$C$]       (C) at (1.5,2.6,0);
  \coordinate (H) at (1.5,0.87,0);
  \coordinate[label=above:$S$]       (S) at (1.5,0.87,3.5);
  \draw (A)--(B)--(C);
  \draw[dashed] (C)--(A);
  \draw (S)--(A) (S)--(B);
  \draw[dashed] (S)--(C);
  \draw[dashed] (S)--(H);
  \fill (H) circle (1.2pt) node[below right] {$H$};
\end{tikzpicture}"
            });

            cat3d.Templates.Add(new TikzTemplate
            {
                Id = "pyramid_sa_quad",
                Title = "Hình chóp S.ABCD có SA vuông góc đáy",
                CategoryId = cat3d.Id,
                CategoryName = cat3d.Name,
                Tags = new[] { "3D", "hình chóp", "S.ABCD", "SA vuông góc đáy" },
                Description = "Hình chóp tứ giác có cạnh bên SA vuông góc với mặt phẳng đáy (ABCD)",
                Code = @"\begin{tikzpicture}[scale=1.3, thick,
    x={(1cm,0cm)}, y={(0.5cm,0.3cm)}, z={(0cm,1cm)}]
  \coordinate[label=below left:$A$]  (A) at (0,0,0);
  \coordinate[label=below right:$B$] (B) at (3,0,0);
  \coordinate[label=right:$C$]       (C) at (3,3,0);
  \coordinate[label=above left:$D$]  (D) at (0,3,0);
  \coordinate[label=above:$S$]       (S) at (0,0,3.5);
  \draw (A)--(B)--(C);
  \draw[dashed] (C)--(D)--(A);
  \draw (S)--(A) (S)--(B) (S)--(C);
  \draw[dashed] (S)--(D);
  \draw pic [draw, angle radius=3mm] {right angle = S--A--B};
  \draw pic [draw, angle radius=3mm] {right angle = S--A--D};
\end{tikzpicture}"
            });

            cat3d.Templates.Add(new TikzTemplate
            {
                Id = "tetrahedron_regular",
                Title = "Tứ diện đều ABCD",
                CategoryId = cat3d.Id,
                CategoryName = cat3d.Name,
                Tags = new[] { "3D", "tứ diện đều", "khối đa diện", "4 mặt đều" },
                Description = "Tứ diện đều có 4 mặt là các tam giác đều và 6 cạnh bằng nhau",
                Code = @"\begin{tikzpicture}[scale=1.4, thick,
    x={(1cm,0cm)}, y={(0.5cm,0.3cm)}, z={(0cm,1cm)}]
  \coordinate[label=below left:$A$]  (A) at (0,0,0);
  \coordinate[label=below right:$B$] (B) at (3,0,0);
  \coordinate[label=right:$C$]       (C) at (1.5,2.6,0);
  \coordinate[label=above:$D$]       (D) at (1.5,0.87,2.5);
  \draw (A)--(B)--(C);
  \draw[dashed] (C)--(A);
  \draw (D)--(A) (D)--(B);
  \draw[dashed] (D)--(C);
\end{tikzpicture}"
            });

            cat3d.Templates.Add(new TikzTemplate
            {
                Id = "pyramid_frustum",
                Title = "Hình chóp cụt tứ giác đều ABCD.A'B'C'D'",
                CategoryId = cat3d.Id,
                CategoryName = cat3d.Name,
                Tags = new[] { "3D", "chóp cụt", "tứ giác đều", "frustum" },
                Description = "Hình chóp cụt tứ giác đều với 2 đáy là hai hình vuông đồng tâm song song",
                Code = @"\begin{tikzpicture}[scale=1.2, thick,
    x={(1cm,0cm)}, y={(0.5cm,0.3cm)}, z={(0cm,1cm)}]
  \coordinate[label=below left:$A$]  (A) at (0,0,0);
  \coordinate[label=below right:$B$] (B) at (3,0,0);
  \coordinate[label=right:$C$]       (C) at (3,3,0);
  \coordinate[label=above left:$D$]  (D) at (0,3,0);
  \coordinate[label=left:$A'$]       (A1) at (0.75,0.75,2.5);
  \coordinate[label=right:$B'$]      (B1) at (2.25,0.75,2.5);
  \coordinate[label=right:$C'$]      (C1) at (2.25,2.25,2.5);
  \coordinate[label=above:$D'$]      (D1) at (0.75,2.25,2.5);
  \draw (A)--(B)--(C);
  \draw[dashed] (C)--(D)--(A);
  \draw (A1)--(B1)--(C1)--(D1)--cycle;
  \draw (A)--(A1) (B)--(B1) (C)--(C1);
  \draw[dashed] (D)--(D1);
\end{tikzpicture}"
            });

            cat3d.Templates.Add(new TikzTemplate
            {
                Id = "cube_diagonal",
                Title = "Hình lập phương với đường chéo AC'",
                CategoryId = cat3d.Id,
                CategoryName = cat3d.Name,
                Tags = new[] { "3D", "lập phương", "đường chéo", "AC'" },
                Description = "Hình lập phương ABCD.A'B'C'D' vẽ nổi bật đường chéo không gian AC' = a√3",
                Code = @"\begin{tikzpicture}[scale=1.3, thick,
    x={(1cm,0cm)}, y={(0.5cm,0.3cm)}, z={(0cm,1cm)}]
  \coordinate[label=below left:$A$]  (A) at (0,0,0);
  \coordinate[label=below right:$B$] (B) at (2.5,0,0);
  \coordinate[label=right:$C$]       (C) at (2.5,2.5,0);
  \coordinate[label=above left:$D$]  (D) at (0,2.5,0);
  \coordinate[label=above left:$A'$]  (A1) at (0,0,2.5);
  \coordinate[label=above right:$B'$] (B1) at (2.5,0,2.5);
  \coordinate[label=right:$C'$]       (C1) at (2.5,2.5,2.5);
  \coordinate[label=above:$D'$]       (D1) at (0,2.5,2.5);
  \draw (A)--(B)--(C);
  \draw[dashed] (C)--(D)--(A);
  \draw (A)--(A1) (B)--(B1) (C)--(C1);
  \draw[dashed] (D)--(D1);
  \draw (A1)--(B1)--(C1)--(D1)--cycle;
  \draw[red, very thick] (A)--(C1) node[midway, below right] {$a\sqrt{3}$};
\end{tikzpicture}"
            });

            cat3d.Templates.Add(new TikzTemplate
            {
                Id = "cuboid",
                Title = "Hình hộp chữ nhật ABCD.A'B'C'D'",
                CategoryId = cat3d.Id,
                CategoryName = cat3d.Name,
                Tags = new[] { "3D", "hình hộp", "hộp chữ nhật", "kích thước a b c" },
                Description = "Hình hộp chữ nhật với 3 kích thước dài a, rộng b, cao c",
                Code = @"\begin{tikzpicture}[scale=1.1, thick,
    x={(1cm,0cm)}, y={(0.5cm,0.3cm)}, z={(0cm,1cm)}]
  \coordinate[label=below left:$A$]  (A) at (0,0,0);
  \coordinate[label=below right:$B$] (B) at (3.5,0,0);
  \coordinate[label=right:$C$]       (C) at (3.5,2.2,0);
  \coordinate[label=above left:$D$]  (D) at (0,2.2,0);
  \coordinate[label=above left:$A'$]  (A1) at (0,0,2.5);
  \coordinate[label=above right:$B'$] (B1) at (3.5,0,2.5);
  \coordinate[label=right:$C'$]       (C1) at (3.5,2.2,2.5);
  \coordinate[label=above:$D'$]       (D1) at (0,2.2,2.5);
  \draw (A)--(B)--(C);
  \draw[dashed] (C)--(D)--(A);
  \draw (A)--(A1) (B)--(B1) (C)--(C1);
  \draw[dashed] (D)--(D1);
  \draw (A1)--(B1)--(C1)--(D1)--cycle;
  \draw[<->] (0,-0.4,0)--(3.5,-0.4,0) node[midway, below] {$a$};
  \draw[<->] (3.9,0,0)--(3.9,2.2,0) node[midway, below right] {$b$};
  \draw[<->] (3.9,0,0)--(3.9,0,2.5) node[midway, right] {$c$};
\end{tikzpicture}"
            });

            cat3d.Templates.Add(new TikzTemplate
            {
                Id = "cylinder_section",
                Title = "Hình trụ có thiết diện qua trục",
                CategoryId = cat3d.Id,
                CategoryName = cat3d.Name,
                Tags = new[] { "3D", "hình trụ", "thiết diện qua trục", "hình chữ nhật" },
                Description = "Hình trụ tròn xoay với thiết diện qua trục là hình chữ nhật ABCD",
                Code = @"\begin{tikzpicture}[scale=1.1, thick]
  \draw         (-1.5,0) arc (180:360:1.5cm and 0.5cm);
  \draw[dashed] (-1.5,0) arc (180:0  :1.5cm and 0.5cm);
  \draw (0,3) ellipse (1.5cm and 0.5cm);
  \draw (-1.5,0) -- (-1.5,3);
  \draw ( 1.5,0) -- ( 1.5,3);
  \draw[dashed] (0,0)--(0,3);
  \fill (0,0) circle (1.5pt) node[below] {$O$};
  \fill (0,3) circle (1.5pt) node[above] {$O'$};
  \coordinate[label=below left:$A$]  (A) at (-1.5,0);
  \coordinate[label=below right:$B$] (B) at ( 1.5,0);
  \coordinate[label=above right:$C$] (C) at ( 1.5,3);
  \coordinate[label=above left:$D$]  (D) at (-1.5,3);
  \fill[blue!15, opacity=0.5] (A)--(B)--(C)--(D)--cycle;
  \draw[blue, thick] (A)--(B)--(C)--(D)--cycle;
\end{tikzpicture}"
            });

            cat3d.Templates.Add(new TikzTemplate
            {
                Id = "cone_frustum",
                Title = "Hình nón cụt tròn xoay",
                CategoryId = cat3d.Id,
                CategoryName = cat3d.Name,
                Tags = new[] { "3D", "hình nón", "nón cụt", "R r h" },
                Description = "Hình nón cụt tròn xoay với bán kính đáy lớn R, đáy nhỏ r và chiều cao h",
                Code = @"\begin{tikzpicture}[scale=1.1, thick]
  \draw         (-2,0) arc (180:360:2cm and 0.6cm);
  \draw[dashed] (-2,0) arc (180:0  :2cm and 0.6cm);
  \draw (0,3) ellipse (1cm and 0.3cm);
  \draw (-2,0) -- (-1,3);
  \draw ( 2,0) -- ( 1,3);
  \draw[dashed] (0,0)--(0,3);
  \fill (0,0) circle (1.5pt) node[below] {$O$};
  \fill (0,3) circle (1.5pt) node[above] {$O'$};
  \draw[<->] (0.1,0)--(2,0) node[midway, below] {$R$};
  \draw[<->] (0.1,3)--(1,3) node[midway, above] {$r$};
  \draw[<->] (2.3,0)--(2.3,3) node[midway, right] {$h$};
\end{tikzpicture}"
            });

            cat3d.Templates.Add(new TikzTemplate
            {
                Id = "sphere_circum_cube",
                Title = "Mặt cầu ngoại tiếp hình lập phương",
                CategoryId = cat3d.Id,
                CategoryName = cat3d.Name,
                Tags = new[] { "3D", "mặt cầu ngoại tiếp", "hình lập phương", "R = a√3/2" },
                Description = "Mặt cầu ngoại tiếp hình lập phương có tâm I là tâm khối lập phương và bán kính R = a√3/2",
                Code = @"\begin{tikzpicture}[scale=1.2, thick]
  \begin{scope}[x={(1cm,0cm)}, y={(0.5cm,0.3cm)}, z={(0cm,1cm)}]
    \coordinate (A) at (0,0,0); \coordinate (B) at (2,0,0);
    \coordinate (C) at (2,2,0); \coordinate (D) at (0,2,0);
    \coordinate (A1) at (0,0,2); \coordinate (B1) at (2,0,2);
    \coordinate (C1) at (2,2,2); \coordinate (D1) at (0,2,2);
    \draw (A)--(B)--(C); \draw[dashed] (C)--(D)--(A);
    \draw (A)--(A1); \draw (B)--(B1); \draw (C)--(C1);
    \draw[dashed] (D)--(D1);
    \draw (A1)--(B1)--(C1)--(D1)--cycle;
    \coordinate (I) at (1,1,1);
    \fill (I) circle (1.2pt);
  \end{scope}
  \node[right=2pt of I] {$I$};
  \draw[blue, thick] (I) circle (1.732cm);
  \draw[blue]         ([xshift=-1.732cm] I) arc (180:360:1.732cm and 0.55cm);
  \draw[blue, dashed] ([xshift=-1.732cm] I) arc (180:0  :1.732cm and 0.55cm);
\end{tikzpicture}"
            });

            cat3d.Templates.Add(new TikzTemplate
            {
                Id = "sphere_circum_pyramid",
                Title = "Mặt cầu ngoại tiếp chóp tứ giác đều",
                CategoryId = cat3d.Id,
                CategoryName = cat3d.Name,
                Tags = new[] { "3D", "mặt cầu ngoại tiếp", "chóp tứ giác đều", "tâm I" },
                Description = "Mặt cầu ngoại tiếp hình chóp tứ giác đều có tâm I nằm trên đường cao SH",
                Code = @"\begin{tikzpicture}[scale=1.2, thick]
  \begin{scope}[x={(1cm,0cm)}, y={(0.5cm,0.3cm)}, z={(0cm,1cm)}]
    \coordinate[label=below left:$A$]  (A) at (0,0,0);
    \coordinate[label=below right:$B$] (B) at (3,0,0);
    \coordinate[label=right:$C$]       (C) at (3,3,0);
    \coordinate[label=above left:$D$]  (D) at (0,3,0);
    \coordinate[label=above:$S$]       (S) at (1.5,1.5,4);
    \coordinate (H) at (1.5,1.5,0);
    \coordinate (I) at (1.5,1.5,1.5);
    \draw (A)--(B)--(C);
    \draw[dashed] (C)--(D)--(A);
    \draw (S)--(A) (S)--(B) (S)--(C);
    \draw[dashed] (S)--(D);
    \draw[dashed] (S)--(H);
    \fill (H) circle (1pt) node[below right] {$H$};
    \fill (I) circle (1.2pt) node[right] {$I$};
  \end{scope}
  \draw[blue, thick] (I) circle (2.2cm);
  \draw[blue]         ([xshift=-2.2cm] I) arc (180:360:2.2cm and 0.7cm);
  \draw[blue, dashed] ([xshift=-2.2cm] I) arc (180:0  :2.2cm and 0.7cm);
\end{tikzpicture}"
            });

            cat3d.Templates.Add(new TikzTemplate
            {
                Id = "octahedron_regular",
                Title = "Khối bát diện đều (8 mặt đều)",
                CategoryId = cat3d.Id,
                CategoryName = cat3d.Name,
                Tags = new[] { "3D", "bát diện đều", "khối đa diện đều", "octahedron" },
                Description = "Khối bát diện đều gồm hai hình chóp tứ giác đều ghép đáy ABCD đối xứng qua tâm",
                Code = @"\begin{tikzpicture}[scale=1.3, thick,
    x={(1cm,0cm)}, y={(0.5cm,0.3cm)}, z={(0cm,1cm)}]
  \coordinate[label=below left:$A$]  (A) at (0,0,0);
  \coordinate[label=below right:$B$] (B) at (3,0,0);
  \coordinate[label=right:$C$]       (C) at (3,3,0);
  \coordinate[label=above left:$D$]  (D) at (0,3,0);
  \coordinate[label=above:$S$]       (S) at (1.5,1.5,2.5);
  \coordinate[label=below:$S'$]      (S1) at (1.5,1.5,-2.5);
  \draw (A)--(B)--(C);
  \draw[dashed] (C)--(D)--(A);
  \draw (S)--(A) (S)--(B) (S)--(C);
  \draw[dashed] (S)--(D);
  \draw (S1)--(A) (S1)--(B) (S1)--(C);
  \draw[dashed] (S1)--(D);
\end{tikzpicture}"
            });

            cat3d.Templates.Add(new TikzTemplate
            {
                Id = "coord_3d_oxyz",
                Title = "Hệ trục tọa độ không gian Oxyz",
                CategoryId = cat3d.Id,
                CategoryName = cat3d.Name,
                Tags = new[] { "3D", "tọa độ", "Oxyz", "vector chỉ phương" },
                Description = "Hệ trục tọa độ Descartes ba chiều Oxyz với các vector đơn vị i, j, k",
                Code = @"\begin{tikzpicture}[scale=1.3, thick,
    x={(1cm,0cm)}, y={(0.5cm,0.3cm)}, z={(0cm,1cm)}]
  \coordinate (O) at (0,0,0);
  \draw[->] (O) -- (4,0,0) node[below] {$x$};
  \draw[->] (O) -- (0,4,0) node[right] {$y$};
  \draw[->] (O) -- (0,0,3.5) node[above] {$z$};
  \node[below left] at (O) {$O$};
  \draw[->, red, very thick] (O) -- (1,0,0) node[midway, below] {$\vec{i}$};
  \draw[->, green!60!black, very thick] (O) -- (0,1,0) node[midway, below right] {$\vec{j}$};
  \draw[->, blue, very thick] (O) -- (0,0,1) node[midway, left] {$\vec{k}$};
\end{tikzpicture}"
            });

            _categories.Add(cat3d);

            // =========================================================================
            // 3. ĐỒ THỊ HÀM SỐ (Function Graphs - pgfplots)
            // =========================================================================
            var catGraph = new TikzTemplateCategory
            {
                Id = "graphs",
                Name = "Đồ thị hàm số",
                Icon = "DataTrending24"
            };

            catGraph.Templates.Add(new TikzTemplate
            {
                Id = "graph_linear",
                Title = "Đồ thị hàm bậc nhất y = ax + b",
                CategoryId = catGraph.Id,
                CategoryName = catGraph.Name,
                Tags = new[] { "đồ thị", "hàm bậc 1", "đường thẳng", "pgfplots" },
                Description = "Đường thẳng y = 2x - 1 với các điểm cắt trục tọa độ",
                Code = @"\begin{tikzpicture}
\begin{axis}[
  axis lines=middle, xlabel=$x$, ylabel=$y$,
  xmin=-3, xmax=4, ymin=-2, ymax=5,
  width=9cm, height=7cm,
  grid=major, grid style={dashed, gray!30},
]
  \addplot[blue, very thick, domain=-2.5:3.5] {2*x - 1};
  \addlegendentry{$y = 2x - 1$}
  \addplot[only marks, mark=*, red] coordinates {(0,-1) (0.5,0) (2,3)};
\end{axis}
\end{tikzpicture}"
            });

            catGraph.Templates.Add(new TikzTemplate
            {
                Id = "graph_quadratic",
                Title = "Parabol bậc hai y = ax^2 + bx + c",
                CategoryId = catGraph.Id,
                CategoryName = catGraph.Name,
                Tags = new[] { "đồ thị", "parabol", "hàm bậc 2", "đỉnh I" },
                Description = "Parabol y = x^2 - 1 có đỉnh I(0; -1) và trục đối xứng Oy",
                Code = @"\begin{tikzpicture}
\begin{axis}[
  axis lines=middle, xlabel=$x$, ylabel=$y$,
  xmin=-3, xmax=3, ymin=-2, ymax=6,
  width=9cm, height=7cm, samples=150,
  grid=major, grid style={dashed, gray!30},
]
  \addplot[blue, very thick, domain=-2.5:2.5] {x^2 - 1};
  \addlegendentry{$y = x^2 - 1$}
  \addplot[only marks, mark=*, red] coordinates {(0,-1)};
  \node[red, below] at (axis cs:0,-1) {$I(0;-1)$};
\end{axis}
\end{tikzpicture}"
            });

            catGraph.Templates.Add(new TikzTemplate
            {
                Id = "graph_cubic",
                Title = "Hàm bậc ba có 2 cực trị",
                CategoryId = catGraph.Id,
                CategoryName = catGraph.Name,
                Tags = new[] { "đồ thị", "hàm bậc 3", "cực đại", "cực tiểu", "điểm uốn" },
                Description = "Đồ thị hàm số bậc 3 y = x^3 - 3x có điểm cực đại, cực tiểu và tâm uốn",
                Code = @"\begin{tikzpicture}
\begin{axis}[
  axis lines=middle, xlabel=$x$, ylabel=$y$,
  xmin=-3, xmax=3, ymin=-4, ymax=4,
  width=10cm, height=8cm, samples=150,
  grid=major, grid style={dashed, gray!30},
]
  \addplot[blue, very thick, domain=-2.2:2.2] {x^3 - 3*x};
  \addlegendentry{$y = x^3 - 3x$}
  \addplot[only marks, mark=*, red, mark size=2.5pt]
    coordinates {(-1, 2) (1, -2)};
  \node[red, above left]  at (axis cs:-1, 2)  {CĐ};
  \node[red, below right] at (axis cs: 1,-2)  {CT};
  \addplot[only marks, mark=*, green!60!black] coordinates {(0,0)};
  \node[green!60!black, above right] at (axis cs:0,0) {$U$};
\end{axis}
\end{tikzpicture}"
            });

            catGraph.Templates.Add(new TikzTemplate
            {
                Id = "graph_quartic",
                Title = "Hàm bậc bốn trùng phương (chữ W)",
                CategoryId = catGraph.Id,
                CategoryName = catGraph.Name,
                Tags = new[] { "đồ thị", "trùng phương", "hàm bậc 4", "3 cực trị" },
                Description = "Đồ thị hàm trùng phương y = x^4 - 2x^2 dạng chữ W với 3 điểm cực trị",
                Code = @"\begin{tikzpicture}
\begin{axis}[
  axis lines=middle, xlabel=$x$, ylabel=$y$,
  xmin=-2.5, xmax=2.5, ymin=-2, ymax=4,
  width=10cm, height=8cm, samples=200,
  grid=major, grid style={dashed, gray!30},
]
  \addplot[blue, very thick, domain=-1.8:1.8] {x^4 - 2*x^2};
  \addlegendentry{$y = x^4 - 2x^2$}
  \addplot[only marks, mark=*, red, mark size=2.5pt]
    coordinates {(0,0) (-1,-1) (1,-1)};
  \node[red, above]      at (axis cs: 0, 0) {CĐ};
  \node[red, below left] at (axis cs:-1,-1) {CT};
  \node[red, below right]at (axis cs: 1,-1) {CT};
\end{axis}
\end{tikzpicture}"
            });

            catGraph.Templates.Add(new TikzTemplate
            {
                Id = "graph_rational_1_1",
                Title = "Phân thức bậc 1/1 y = (ax+b)/(cx+d)",
                CategoryId = catGraph.Id,
                CategoryName = catGraph.Name,
                Tags = new[] { "đồ thị", "phân thức", "tiệm cận đứng", "tiệm cận ngang" },
                Description = "Đồ thị hàm nhất biến có tiệm cận đứng x = 1 và tiệm cận ngang y = 1",
                Code = @"\begin{tikzpicture}
\begin{axis}[
  axis lines=middle, xlabel=$x$, ylabel=$y$,
  xmin=-4, xmax=5, ymin=-4, ymax=5,
  width=10cm, height=8cm, samples=200,
  grid=major, grid style={dashed, gray!30},
]
  \addplot[blue, very thick, domain=-3.5:0.85] {(x+1)/(x-1)};
  \addplot[blue, very thick, domain=1.15:4.5] {(x+1)/(x-1)};
  \addplot[red, dashed, thick] coordinates {(1,-4) (1,5)};
  \node[red, above] at (axis cs:1,4.5) {$x=1$};
  \addplot[red, dashed, thick] coordinates {(-4,1) (5,1)};
  \node[red, right] at (axis cs:4.5,1) {$y=1$};
\end{axis}
\end{tikzpicture}"
            });

            catGraph.Templates.Add(new TikzTemplate
            {
                Id = "graph_rational_2_1",
                Title = "Phân thức bậc 2/1 có tiệm cận xiên",
                CategoryId = catGraph.Id,
                CategoryName = catGraph.Name,
                Tags = new[] { "đồ thị", "phân thức bậc 2/1", "tiệm cận xiên" },
                Description = "Hàm số phân thức bậc hai trên bậc nhất với tiệm cận đứng và tiệm cận xiên",
                Code = @"\begin{tikzpicture}
\begin{axis}[
  axis lines=middle, xlabel=$x$, ylabel=$y$,
  xmin=-5, xmax=5, ymin=-6, ymax=6,
  width=10cm, height=8cm, samples=150,
  grid=major, grid style={dashed, gray!30},
]
  \addplot[blue, very thick, domain=-4.5:0.85] {(x^2 - x + 1)/(x - 1)};
  \addplot[blue, very thick, domain=1.15:4.5] {(x^2 - x + 1)/(x - 1)};
  \addplot[red, dashed, thick] coordinates {(1,-6) (1,6)};
  \addplot[purple, dashed, thick, domain=-4.5:4.5] {x};
\end{axis}
\end{tikzpicture}"
            });

            catGraph.Templates.Add(new TikzTemplate
            {
                Id = "graph_trig",
                Title = "Đồ thị lượng giác y = sin x & cos x",
                CategoryId = catGraph.Id,
                CategoryName = catGraph.Name,
                Tags = new[] { "đồ thị", "lượng giác", "sin", "cos", "chu kỳ" },
                Description = "Đồ thị hàm tuần hoàn sóng sin và cos trên đoạn [-2pi; 2pi]",
                Code = @"\begin{tikzpicture}
\begin{axis}[
  axis lines=middle, xlabel={$x$}, ylabel={$y$},
  xmin=-7, xmax=7, ymin=-1.5, ymax=1.5,
  xtick={-6.28, -3.14, 0, 3.14, 6.28},
  xticklabels={$-2\pi$, $-\pi$, $0$, $\pi$, $2\pi$},
  grid=major, grid style={dashed, gray!30},
  width=11cm, height=6cm, samples=200, legend pos=north east,
]
  \addplot[blue, very thick, domain=-6.5:6.5] {sin(deg(x))};
  \addlegendentry{$y = \sin x$}
  \addplot[red, thick, dashed, domain=-6.5:6.5] {cos(deg(x))};
  \addlegendentry{$y = \cos x$}
\end{axis}
\end{tikzpicture}"
            });

            catGraph.Templates.Add(new TikzTemplate
            {
                Id = "graph_exp_log",
                Title = "Hàm mũ y = e^x và logarit y = ln x",
                CategoryId = catGraph.Id,
                CategoryName = catGraph.Name,
                Tags = new[] { "đồ thị", "hàm mũ", "logarit", "đối xứng" },
                Description = "Cặp đồ thị y = e^x và y = ln x đối xứng nhau qua phân giác y = x",
                Code = @"\begin{tikzpicture}
\begin{axis}[
  axis lines=middle, xlabel=$x$, ylabel=$y$,
  xmin=-3, xmax=4, ymin=-3, ymax=4,
  width=9cm, height=9cm, samples=150,
  grid=major, grid style={dashed, gray!30},
  legend pos=north west,
]
  \addplot[blue, thick, domain=-2.5:1.3] {exp(x)};
  \addlegendentry{$y = e^x$}
  \addplot[red, thick, dashed, domain=0.05:4] {ln(x)};
  \addlegendentry{$y = \ln x$}
  \addplot[gray, dotted, domain=-3:4] {x};
  \addlegendentry{$y = x$}
\end{axis}
\end{tikzpicture}"
            });

            _categories.Add(catGraph);

            // =========================================================================
            // 4. BẢNG BIẾN THIÊN & XÉT DẤU (tkz-tab)
            // =========================================================================
            var catTable = new TikzTemplateCategory
            {
                Id = "tables",
                Name = "Bảng biến thiên & Xét dấu (tkz-tab)",
                Icon = "Table24"
            };

            catTable.Templates.Add(new TikzTemplate
            {
                Id = "bbt_cubic_pos",
                Title = "BBT hàm bậc 3 (a > 0, có CĐ và CT)",
                CategoryId = catTable.Id,
                CategoryName = catTable.Name,
                Tags = new[] { "bbt", "bậc 3", "tkz-tab", "cực trị" },
                Description = "Bảng biến thiên hàm bậc 3 có 2 điểm cực trị và a > 0",
                Code = @"\begin{tikzpicture}
  \tkzTabInit[lgt=2, espcl=3]
    {$x$/1, $y'$/1, $y$/2}{$-\infty$, $x_1$, $x_2$, $+\infty$}
  \tkzTabLine{, +, 0, -, 0, +, }
  \tkzTabVar{-/$-\infty$, +/$y_{C\!D}$, -/$y_{CT}$, +/$+\infty$}
\end{tikzpicture}"
            });

            catTable.Templates.Add(new TikzTemplate
            {
                Id = "bbt_cubic_neg",
                Title = "BBT hàm bậc 3 (a < 0, có CT và CĐ)",
                CategoryId = catTable.Id,
                CategoryName = catTable.Name,
                Tags = new[] { "bbt", "bậc 3", "a < 0", "tkz-tab" },
                Description = "Bảng biến thiên hàm bậc 3 có 2 điểm cực trị và hệ số a < 0",
                Code = @"\begin{tikzpicture}
  \tkzTabInit[lgt=2, espcl=3]
    {$x$/1, $y'$/1, $y$/2}{$-\infty$, $x_1$, $x_2$, $+\infty$}
  \tkzTabLine{, -, 0, +, 0, -, }
  \tkzTabVar{+/$+\infty$, -/$y_{CT}$, +/$y_{C\!D}$, -/$-\infty$}
\end{tikzpicture}"
            });

            catTable.Templates.Add(new TikzTemplate
            {
                Id = "bbt_rational_inc",
                Title = "BBT phân thức bậc 1/1 (đồng biến)",
                CategoryId = catTable.Id,
                CategoryName = catTable.Name,
                Tags = new[] { "bbt", "phân thức", "đồng biến", "tkz-tab" },
                Description = "Bảng biến thiên hàm phân thức đồng biến trên từng khoảng xác định",
                Code = @"\begin{tikzpicture}
  \tkzTabInit[lgt=2.5, espcl=3]
    {$x$/1, $y'$/1, $y$/2.5}
    {$-\infty$, $-\frac{d}{c}$, $+\infty$}
  \tkzTabLine{, +, d, +, }
  \tkzTabVar{-/$\frac{a}{c}$, +D+/$+\infty$/$-\infty$, -/$\frac{a}{c}$}
\end{tikzpicture}"
            });

            catTable.Templates.Add(new TikzTemplate
            {
                Id = "bbt_rational_dec",
                Title = "BBT phân thức bậc 1/1 (nghịch biến)",
                CategoryId = catTable.Id,
                CategoryName = catTable.Name,
                Tags = new[] { "bbt", "phân thức", "nghịch biến", "tkz-tab" },
                Description = "Bảng biến thiên hàm phân thức nghịch biến trên từng khoảng xác định",
                Code = @"\begin{tikzpicture}
  \tkzTabInit[lgt=2.5, espcl=3]
    {$x$/1, $y'$/1, $y$/2.5}
    {$-\infty$, $-\frac{d}{c}$, $+\infty$}
  \tkzTabLine{, -, d, -, }
  \tkzTabVar{+/$\frac{a}{c}$, -D-/$-\infty$/$+\infty$, +/$\frac{a}{c}$}
\end{tikzpicture}"
            });

            catTable.Templates.Add(new TikzTemplate
            {
                Id = "bbt_quartic",
                Title = "BBT hàm trùng phương (3 cực trị)",
                CategoryId = catTable.Id,
                CategoryName = catTable.Name,
                Tags = new[] { "bbt", "trùng phương", "bậc 4", "tkz-tab" },
                Description = "Bảng biến thiên hàm trùng phương a > 0, b < 0 có 3 điểm cực trị",
                Code = @"\begin{tikzpicture}
  \tkzTabInit[lgt=2, espcl=2.5]
    {$x$/1, $y'$/1, $y$/2.5}{$-\infty$, $-x_0$, $0$, $x_0$, $+\infty$}
  \tkzTabLine{, -, 0, +, 0, -, 0, +, }
  \tkzTabVar{+/$+\infty$, -/$y_{CT}$, +/$y_{C\!D}$, -/$y_{CT}$, +/$+\infty$}
\end{tikzpicture}"
            });

            catTable.Templates.Add(new TikzTemplate
            {
                Id = "bbt_parabola",
                Title = "BBT Parabol (a > 0, cực tiểu)",
                CategoryId = catTable.Id,
                CategoryName = catTable.Name,
                Tags = new[] { "bbt", "parabol", "bậc 2", "tkz-tab" },
                Description = "Bảng biến thiên hàm bậc 2 bề lõm quay lên, cực tiểu tại đỉnh",
                Code = @"\begin{tikzpicture}
  \tkzTabInit[lgt=2, espcl=3]
    {$x$/1, $y'$/1, $y$/2}{$-\infty$, $-\frac{b}{2a}$, $+\infty$}
  \tkzTabLine{, -, 0, +, }
  \tkzTabVar{+/$+\infty$, -/$-\frac{\Delta}{4a}$, +/$+\infty$}
\end{tikzpicture}"
            });

            catTable.Templates.Add(new TikzTemplate
            {
                Id = "bxd_linear",
                Title = "Bảng xét dấu nhị thức bậc 1",
                CategoryId = catTable.Id,
                CategoryName = catTable.Name,
                Tags = new[] { "bxd", "xét dấu", "nhị thức", "tkz-tab" },
                Description = "Bảng xét dấu f(x) = ax + b theo quy tắc trái khác phải cùng",
                Code = @"\begin{tikzpicture}
  \tkzTabInit[lgt=3, espcl=3]
    {$x$/1, $f(x)=ax+b$/1}{$-\infty$, $-\frac{b}{a}$, $+\infty$}
  \tkzTabLine{, -, 0, +, }
\end{tikzpicture}"
            });

            catTable.Templates.Add(new TikzTemplate
            {
                Id = "bxd_quadratic",
                Title = "Bảng xét dấu tam thức bậc 2 (Delta > 0)",
                CategoryId = catTable.Id,
                CategoryName = catTable.Name,
                Tags = new[] { "bxd", "xét dấu", "tam thức", "tkz-tab" },
                Description = "Bảng xét dấu f(x) = ax^2 + bx + c theo quy tắc trong trái ngoài cùng",
                Code = @"\begin{tikzpicture}
  \tkzTabInit[lgt=3, espcl=2.5]
    {$x$/1, $f(x)=ax^2+bx+c$/1}{$-\infty$, $x_1$, $x_2$, $+\infty$}
  \tkzTabLine{, +, 0, -, 0, +, }
\end{tikzpicture}"
            });

            _categories.Add(catTable);

            // =========================================================================
            // 5. BIỂU ĐỒ & TRỤC SỐ (Charts & Miscellaneous)
            // =========================================================================
            var catMisc = new TikzTemplateCategory
            {
                Id = "misc",
                Name = "Biểu đồ & Trục số",
                Icon = "ChartMultiple24"
            };

            catMisc.Templates.Add(new TikzTemplate
            {
                Id = "chart_bar",
                Title = "Biểu đồ cột đơn giản",
                CategoryId = catMisc.Id,
                CategoryName = catMisc.Name,
                Tags = new[] { "biểu đồ", "cột", "thống kê", "pgfplots" },
                Description = "Biểu đồ cột thể hiện điểm số các môn học có nhãn giá trị",
                Code = @"\begin{tikzpicture}
\begin{axis}[
  ybar,
  symbolic x coords={Toán, Lý, Hóa, Sinh},
  xtick=data, ylabel={Điểm}, title={Kết quả học tập},
  width=9cm, height=6.5cm, nodes near coords,
  ymin=0, ymax=10,
]
  \addplot[fill=blue!50] coordinates {(Toán,8) (Lý,7) (Hóa,9) (Sinh,6)};
\end{axis}
\end{tikzpicture}"
            });

            catMisc.Templates.Add(new TikzTemplate
            {
                Id = "chart_line",
                Title = "Biểu đồ đường",
                CategoryId = catMisc.Id,
                CategoryName = catMisc.Name,
                Tags = new[] { "biểu đồ", "đường", "tăng trưởng", "thống kê" },
                Description = "Biểu đồ đường gấp khúc thể hiện tăng trưởng theo mốc thời gian",
                Code = @"\begin{tikzpicture}
\begin{axis}[
  axis lines=left, xlabel={Tháng}, ylabel={Doanh số},
  title={Tăng trưởng định kỳ}, width=9cm, height=6cm,
  grid=major, ymin=0, ymax=30,
]
  \addplot[blue, mark=*, thick] coordinates {(1,10) (2,15) (3,12) (4,20) (5,25)};
  \addlegendentry{Năm 2026}
\end{axis}
\end{tikzpicture}"
            });

            catMisc.Templates.Add(new TikzTemplate
            {
                Id = "numline_int",
                Title = "Trục số nguyên",
                CategoryId = catMisc.Id,
                CategoryName = catMisc.Name,
                Tags = new[] { "trục số", "tập hợp", "số học" },
                Description = "Trục số biểu diễn các giá trị nguyên từ -5 đến 5",
                Code = @"\begin{tikzpicture}[scale=1]
  \draw[->, thick] (-5.5,0)--(5.5,0) node[right] {$x$};
  \foreach \x in {-5,-4,-3,-2,-1,0,1,2,3,4,5} {
    \draw (\x,0.1)--(\x,-0.1);
    \node[below] at (\x,-0.1) {$\x$};
  }
\end{tikzpicture}"
            });

            catMisc.Templates.Add(new TikzTemplate
            {
                Id = "numline_closed",
                Title = "Khoảng nghiệm đoạn đóng [a, b]",
                CategoryId = catMisc.Id,
                CategoryName = catMisc.Name,
                Tags = new[] { "trục số", "đoạn đóng", "tập nghiệm", "bất phương trình" },
                Description = "Trục số tô đậm khoảng nghiệm đóng [-1; 3] với hai đầu mút đặc",
                Code = @"\begin{tikzpicture}[scale=1]
  \draw[->, thick] (-3,0)--(5,0) node[right] {$x$};
  \foreach \x in {-2,-1,0,1,2,3,4} {
    \draw (\x,0.08)--(\x,-0.08);
    \node[below] at (\x,-0.1) {$\x$};
  }
  \draw[blue, very thick] (-1,0.2)--(3,0.2);
  \fill[blue] (-1,0.2) circle (3pt);
  \fill[blue] ( 3,0.2) circle (3pt);
  \node[blue, above] at (1, 0.4) {$x \in [-1; 3]$};
\end{tikzpicture}"
            });

            catMisc.Templates.Add(new TikzTemplate
            {
                Id = "numline_open",
                Title = "Khoảng nghiệm khoảng mở (a, b)",
                CategoryId = catMisc.Id,
                CategoryName = catMisc.Name,
                Tags = new[] { "trục số", "khoảng mở", "tập nghiệm", "bất phương trình" },
                Description = "Trục số tô đậm khoảng mở (-1; 3) với hai đầu mút tròn rỗng",
                Code = @"\begin{tikzpicture}[scale=1]
  \draw[->, thick] (-3,0)--(5,0) node[right] {$x$};
  \foreach \x in {-2,-1,0,1,2,3,4} {
    \draw (\x,0.08)--(\x,-0.08);
    \node[below] at (\x,-0.1) {$\x$};
  }
  \draw[blue, very thick] (-1,0.2)--(3,0.2);
  \draw[blue, fill=white, thick] (-1,0.2) circle (3pt);
  \draw[blue, fill=white, thick] ( 3,0.2) circle (3pt);
  \node[blue, above] at (1, 0.4) {$x \in (-1; 3)$};
\end{tikzpicture}"
            });

            catMisc.Templates.Add(new TikzTemplate
            {
                Id = "venn_intersection",
                Title = "Sơ đồ Venn giao hai tập hợp",
                CategoryId = catMisc.Id,
                CategoryName = catMisc.Name,
                Tags = new[] { "sơ đồ Venn", "tập hợp", "phép giao" },
                Description = "Sơ đồ Venn biểu diễn phần giao giữa hai tập hợp A và B",
                Code = @"\begin{tikzpicture}[scale=1.1]
  \def\firstcircle{(0,0) circle (1.5cm)}
  \def\secondcircle{(1.8,0) circle (1.5cm)}
  \begin{scope}
    \clip \firstcircle;
    \fill[blue!30] \secondcircle;
  \end{scope}
  \draw[thick] \firstcircle node[left=1.6cm] {$A$};
  \draw[thick] \secondcircle node[right=1.6cm] {$B$};
  \node at (0.9,0) {$A \cap B$};
\end{tikzpicture}"
            });

            _categories.Add(catMisc);

            // Đăng ký toàn bộ template vào lookup index
            foreach (var cat in _categories)
            {
                foreach (var tpl in cat.Templates)
                {
                    _idLookup[tpl.Id] = tpl;
                    _titleLookup[tpl.Title] = tpl;
                }
            }
        }

        /// <summary>
        /// Tự động quét và nạp toàn bộ template từ thư mục data/tikz_kb (nếu có).
        /// </summary>
        public static void AutoScanAndLoad()
        {
            try
            {
                var candidatePaths = new List<string>
                {
                    Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "data", "tikz_kb"),
                    Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "..", "..", "..", "..", "data", "tikz_kb"),
                    Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "..", "..", "..", "data", "tikz_kb"),
                    Path.Combine(Environment.CurrentDirectory, "data", "tikz_kb"),
                    @"M:\IT\Phần mềm biên soạn tài liệu\MEA_v5.0\data\tikz_kb"
                };

                foreach (var path in candidatePaths)
                {
                    try
                    {
                        string fullPath = Path.GetFullPath(path);
                        if (Directory.Exists(fullPath))
                        {
                            LoadFromDirectory(fullPath);
                            break;
                        }
                    }
                    catch { }
                }
            }
            catch { }
        }

        /// <summary>
        /// Nạp các mẫu TikZ từ cây thư mục .txt (chuẩn data/tikz_kb).
        /// </summary>
        public static void LoadFromDirectory(string dirPath)
        {
            if (string.IsNullOrWhiteSpace(dirPath) || !Directory.Exists(dirPath)) return;

            try
            {
                var files = Directory.GetFiles(dirPath, "*.txt", SearchOption.AllDirectories);
                foreach (var file in files)
                {
                    ParseAndMergeFile(file);
                }
            }
            catch { }
        }

        private static void ParseAndMergeFile(string filePath)
        {
            try
            {
                string text = File.ReadAllText(filePath);
                var headerRegex = new Regex(@"^=+\s*TEMPLATE\s*:\s*(.+?)\s*=+\s*$", RegexOptions.Multiline | RegexOptions.IgnoreCase);
                var matches = headerRegex.Matches(text);
                if (matches.Count == 0) return;

                // Xác định categoryId mặc định theo tên thư mục
                string dirName = Path.GetFileName(Path.GetDirectoryName(filePath) ?? "") ?? "";
                string defaultCatId = "misc";
                if (dirName.Contains("01_plane") || dirName.Contains("plane")) defaultCatId = "plane_2d";
                else if (dirName.Contains("02_solid") || dirName.Contains("solid")) defaultCatId = "solid_3d";
                else if (dirName.Contains("03_graph") || dirName.Contains("graph")) defaultCatId = "graphs";
                else if (dirName.Contains("04_table") || dirName.Contains("table")) defaultCatId = "tables";
                else if (dirName.Contains("05_chart") || dirName.Contains("chart")) defaultCatId = "charts";

                for (int i = 0; i < matches.Count; i++)
                {
                    int start = matches[i].Index + matches[i].Length;
                    int end = (i + 1 < matches.Count) ? matches[i + 1].Index : text.Length;
                    string block = text.Substring(start, end - start);
                    string title = matches[i].Groups[1].Value.Trim();

                    // Tìm code tikz
                    int beginIdx = block.IndexOf("\\begin{tikzpicture}", StringComparison.Ordinal);
                    int endIdx = block.IndexOf("\\end{tikzpicture}", StringComparison.Ordinal);
                    if (beginIdx < 0 || endIdx < 0 || endIdx <= beginIdx) continue;

                    string code = block.Substring(beginIdx, (endIdx + "\\end{tikzpicture}".Length) - beginIdx).Trim();
                    string meta = block.Substring(0, beginIdx);

                    var tags = new List<string>();
                    string desc = "";

                    foreach (var line in meta.Split(new[] { '\r', '\n' }, StringSplitOptions.RemoveEmptyEntries))
                    {
                        string trimmed = line.Trim();
                        if (trimmed.StartsWith("TAGS:", StringComparison.OrdinalIgnoreCase))
                        {
                            var parts = trimmed.Substring(5).Split(new[] { ',' }, StringSplitOptions.RemoveEmptyEntries);
                            foreach (var p in parts) tags.Add(p.Trim());
                        }
                        else if (trimmed.StartsWith("NOTES:", StringComparison.OrdinalIgnoreCase))
                        {
                            desc = trimmed.Substring(6).Trim();
                        }
                    }

                    int openCurly = code.Count(c => c == '{');
                    int closeCurly = code.Count(c => c == '}');
                    int openSquare = code.Count(c => c == '[');
                    int closeSquare = code.Count(c => c == ']');
                    if (openCurly != closeCurly || openSquare != closeSquare) continue;

                    string catId = defaultCatId;
                    if (tags.Any(t => t.IndexOf("3D", StringComparison.OrdinalIgnoreCase) >= 0 || t.IndexOf("không gian", StringComparison.OrdinalIgnoreCase) >= 0))
                        catId = "solid_3d";
                    else if (tags.Any(t => t.IndexOf("graph", StringComparison.OrdinalIgnoreCase) >= 0 || t.IndexOf("đồ thị", StringComparison.OrdinalIgnoreCase) >= 0))
                        catId = "graphs";
                    else if (tags.Any(t => t.IndexOf("bbt", StringComparison.OrdinalIgnoreCase) >= 0 || t.IndexOf("bảng", StringComparison.OrdinalIgnoreCase) >= 0))
                        catId = "tables";

                    var category = _categories.FirstOrDefault(c => c.Id == catId);
                    if (category == null)
                    {
                        category = _categories.FirstOrDefault(c => c.Id == "misc");
                        if (category == null) continue;
                    }

                    if (_titleLookup.ContainsKey(title)) continue;

                    string id = Regex.Replace(title.ToLowerInvariant(), @"[^a-z0-9_]+", "_").Trim('_');
                    if (string.IsNullOrEmpty(id) || _idLookup.ContainsKey(id))
                    {
                        id = "kb_" + Guid.NewGuid().ToString("N").Substring(0, 8);
                    }

                    string finalDesc = string.IsNullOrWhiteSpace(desc) ? title : desc;

                    var tpl = new TikzTemplate
                    {
                        Id = id,
                        Title = title,
                        CategoryId = category.Id,
                        CategoryName = category.Name,
                        Description = finalDesc,
                        Tags = tags.ToArray(),
                        Code = code
                    };

                    RegisterTemplate(tpl);
                }
            }
            catch { }
        }

        /// <summary>
        /// Đăng ký hoặc cập nhật một mẫu TikZ vào thư viện.
        /// </summary>
        public static void RegisterTemplate(TikzTemplate tpl)
        {
            if (tpl == null || string.IsNullOrWhiteSpace(tpl.Title) || string.IsNullOrWhiteSpace(tpl.Code)) return;

            var cat = _categories.FirstOrDefault(c => c.Id == tpl.CategoryId);
            if (cat == null)
            {
                cat = _categories.FirstOrDefault(c => c.Id == "misc") ?? _categories.FirstOrDefault();
                if (cat == null) return;
                tpl.CategoryId = cat.Id;
                tpl.CategoryName = cat.Name;
            }

            if (_idLookup.ContainsKey(tpl.Id) || _titleLookup.ContainsKey(tpl.Title)) return;

            cat.Templates.Add(tpl);
            _idLookup[tpl.Id] = tpl;
            _titleLookup[tpl.Title] = tpl;
        }

        private static readonly TikzTemplateCategory _userFiguresCategory = new TikzTemplateCategory
        {
            Id = "figure_bank",
            Name = "Kho hình cá nhân",
            Icon = "Folder24"
        };

        /// <summary>
        /// Chuyên đề kho hình cá nhân của người dùng (tải từ FigureBank).
        /// </summary>
        public static TikzTemplateCategory UserFiguresCategory => _userFiguresCategory;

        /// <summary>
        /// Nạp toàn bộ danh mục hình vẽ người dùng (FigureBank) vào chuyên đề riêng trong thư viện.
        /// </summary>
        public static void LoadUserFigures(IEnumerable<(string Id, string Title, string Description, IEnumerable<string> Tags, string Code)> figures)
        {
            if (figures == null) return;
            _userFiguresCategory.Templates.Clear();

            foreach (var fig in figures)
            {
                if (string.IsNullOrWhiteSpace(fig.Code)) continue;
                var tpl = new TikzTemplate
                {
                    Id = $"fig_{fig.Id}",
                    Title = string.IsNullOrWhiteSpace(fig.Title) ? $"Hình #{fig.Id}" : fig.Title,
                    CategoryId = _userFiguresCategory.Id,
                    CategoryName = _userFiguresCategory.Name,
                    Description = string.IsNullOrWhiteSpace(fig.Description) ? $"Hình #{fig.Id}" : fig.Description,
                    Tags = fig.Tags?.ToArray() ?? new[] { "kho hình", "cá nhân" },
                    Code = fig.Code
                };

                _userFiguresCategory.Templates.Add(tpl);
            }

            _userFiguresCategory.Name = $"Kho hình cá nhân ({_userFiguresCategory.Templates.Count} hình)";
        }
    }
}
