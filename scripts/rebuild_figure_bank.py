import os, sys, json, subprocess, tempfile, shutil
import pymupdf

sys.stdout.reconfigure(encoding='utf-8')

bank_dir = os.path.expanduser(r'~/.exam_generator/figures')
os.makedirs(bank_dir, exist_ok=True)
idx_path = os.path.join(bank_dir, 'index.json')

def compile_tikz_to_png(tikz_code, dest_png_path, dpi=300):
    preamble = r'''\documentclass[tikz,border=6pt]{standalone}
\usepackage{amsmath,amssymb}
\usepackage{tikz}
\usetikzlibrary{calc,angles,quotes,intersections,patterns,arrows.meta,decorations.markings,3d}
\usepackage{tikz-3dplot}
\usepackage{tkz-tab}
\usepackage{tkz-euclide}
\usepackage{pgfplots}
\pgfplotsset{compat=1.18}
\begin{document}
'''
    postamble = r'''
\end{document}
'''
    full_tex = preamble + tikz_code + postamble
    with tempfile.TemporaryDirectory() as td:
        tex_file = os.path.join(td, 'render.tex')
        with open(tex_file, 'w', encoding='utf-8') as f:
            f.write(full_tex)
        
        proc = subprocess.run(
            ['pdflatex', '-interaction=nonstopmode', 'render.tex'],
            cwd=td,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        pdf_file = os.path.join(td, 'render.pdf')
        if os.path.exists(pdf_file):
            doc = pymupdf.open(pdf_file)
            page = doc[0]
            pix = page.get_pixmap(dpi=dpi)
            pix.save(dest_png_path)
            doc.close()
            return True
        else:
            print("Render failed. Tex snippet:")
            print(tikz_code[:200])
            return False

# 1. Load existing index
existing_entries = []
if os.path.exists(idx_path):
    with open(idx_path, 'r', encoding='utf-8-sig') as f:
        existing_entries = json.load(f)

entries_by_id = {e['id']: e for e in existing_entries}

# 2. Fix the 3 broken figures (#106, #102, #097)
fixed_figures = {
    "106": {
        "title": "Biểu đồ cột tiêu chí A (Đề QID-57F3DF636D)",
        "desc": "Biểu đồ cột biểu diễn phân bố tiêu chí đánh giá giá trị A",
        "tags": ["BieuDo", "Cot", "ThucTe"],
        "tikz": r'''\begin{tikzpicture}[x=1.2cm,y=0.035cm]
\draw[->,>=stealth,thick] (0,0) -- (5.5,0) node[below right] {Tiêu chí};
\draw[->,>=stealth,thick] (0,0) -- (0,120) node[left] {Giá trị};
\foreach \y in {20,40,60,80,100} {
    \draw (0.1,\y) -- (-0.1,\y) node[left,font=\small] {$\y$};
    \draw[dashed,gray!40] (0,\y) -- (5,\y);
}
\draw[fill=blue!50,draw=blue!80,thick] (1,0) rectangle (2,100);
\node[above,font=\bfseries,blue!80] at (1.5,100) {100};
\node[below,font=\small] at (1.5,0) {A};

\draw[fill=teal!40,draw=teal!80,thick] (3,0) rectangle (4,65);
\node[above,font=\bfseries,teal!80] at (3.5,65) {65};
\node[below,font=\small] at (3.5,0) {B};
\end{tikzpicture}'''
    },
    "102": {
        "title": "Miền nghiệm bài toán trồng ngô & đậu nành (10D2G4-0002)",
        "desc": "Miền đa giác biểu diễn hệ bất phương trình quy hoạch diện tích cây trồng",
        "tags": ["QuyHoachTuyenTinh", "Toan10", "ThucTe", "MienNghiem"],
        "tikz": r'''\begin{tikzpicture}[>=stealth,scale=0.85]
\draw[->,thick] (-0.5,0) -- (5.5,0) node[below] {$x$ (ngô)};
\draw[->,thick] (0,-0.5) -- (0,5.5) node[left] {$y$ (đậu nành)};
\node[below left] at (0,0) {$O$};
% Ranh giới 20x + 30y <= 60 => 2x + 3y <= 6 => x/3 + y/2 <= 1
\coordinate (A) at (0,3.5);
\coordinate (B) at (2.5,1.5);
\coordinate (C) at (4,0);
\fill[blue!15,opacity=0.8] (0,0) -- (0,3.5) -- (2.5,1.5) -- (4,0) -- cycle;
\draw[thick,blue!80] (0,3.5) -- (2.5,1.5) -- (4,0);
\draw[dashed,gray] (2.5,0) node[below] {$x_0$} -- (2.5,1.5) -- (0,1.5) node[left] {$y_0$};
\filldraw[blue!80] (2.5,1.5) circle (2pt) node[above right] {$M(x_0;y_0)$};
\node[above] at (1.5,1.8) {Miền nghiệm $S$};
\end{tikzpicture}'''
    },
    "097": {
        "title": "Miền nghiệm phối trộn cám X & Y (10D2G4-0003)",
        "desc": "Bài toán quy hoạch tuyến tính tìm chi phí nhỏ nhất đảm bảo dinh dưỡng cám",
        "tags": ["QuyHoachTuyenTinh", "Toan10", "ThucTe", "CamX_Y"],
        "tikz": r'''\begin{tikzpicture}[>=stealth,scale=0.85]
\draw[->,thick] (-0.5,0) -- (6,0) node[below] {$x$ (Cám X)};
\draw[->,thick] (0,-0.5) -- (0,6) node[left] {$y$ (Cám Y)};
\node[below left] at (0,0) {$O$};
\coordinate (A) at (0,4.5);
\coordinate (B) at (1.5,2);
\coordinate (C) at (4.5,0.8);
\coordinate (D) at (5.5,0);
\fill[teal!15,opacity=0.8] (A) -- (B) -- (C) -- (5.5,3) -- (5.5,5.5) -- (0,5.5) -- cycle;
\draw[thick,teal!80] (A) -- (B) -- (C);
\filldraw[red!80] (B) circle (2pt) node[above right,font=\small] {$Min(1.5; 2)$};
\draw[dashed,gray] (1.5,0) node[below,font=\small] {$1.5$} -- (B) -- (0,2) node[left,font=\small] {$2$};
\node at (3,3.5) [teal!90,font=\bfseries] {Miền khả thi};
\end{tikzpicture}'''
    }
}

for fid, data in fixed_figures.items():
    tex_path = os.path.join(bank_dir, f'figure_{fid}.tex')
    png_path = os.path.join(bank_dir, f'figure_{fid}.png')
    with open(tex_path, 'w', encoding='utf-8') as f:
        f.write(data['tikz'])
    ok = compile_tikz_to_png(data['tikz'], png_path)
    print(f"Fixed Figure #{fid} -> Render: {ok}")
    if fid in entries_by_id:
        entries_by_id[fid]['title'] = data['title']
        entries_by_id[fid]['description'] = data['desc']
        entries_by_id[fid]['tags'] = data['tags']
        entries_by_id[fid]['png_filename'] = f'figure_{fid}.png'

# 3. Import rich models from TikZStudio and real-world applied math
new_models = [
    {
        "title": "Hình chóp tam giác S.ABC có SA vuông góc đáy",
        "desc": "Mô hình hình chóp đỉnh S, tam giác đáy ABC, đường cao SA thẳng đứng",
        "tags": ["3D", "Chop", "SA_vuong_day", "HinhKhongGian"],
        "source": "template",
        "tikz": r'''\begin{tikzpicture}[declare function={goc=-45; a=5; b=0.45*a; h=5;}]
\path 
(0,0) coordinate (A)--+(0,h) coordinate (S)
(a,0) coordinate (C)
(goc:b) coordinate (B);
\draw[dashed] (A)--(C);
\draw (S)--(A)--(B)--(S)--(C)--(B);
\foreach \p/\pos in {S/above,A/left,B/below,C/right}
    \filldraw (\p) circle (1pt) node[\pos] {$\p$};
\draw (A) ++(0,0.3) -- ++(0.3,0) -- ++(0,-0.3);
\end{tikzpicture}'''
    },
    {
        "title": "Hình chóp tứ giác S.ABCD đáy hình bình hành",
        "desc": "Chóp S.ABCD đáy hình bình hành tiêu chuẩn SGK THPT",
        "tags": ["3D", "Chop", "SABCD", "BinhHanh"],
        "source": "template",
        "tikz": r'''\begin{tikzpicture}[declare function={gocx=80; goc=-150; a=5; b=a/2; h=5;}]
\path (0,0) coordinate (A)--+(gocx:h) coordinate (S)
(a,0) coordinate (B)
(goc:b) coordinate (D)
+(a,0) coordinate (C);
\draw[dashed] (S)--(A)--(B) (A)--(D);
\draw (S)--(D)--(C)--(B)--(S)--(C);
\foreach \p/\pos in {S/above,A/above left,B/right,C/below right,D/below left}
    \filldraw (\p) circle (1pt) node[\pos] {$\p$};
\end{tikzpicture}'''
    },
    {
        "title": "Hình chóp tứ giác đều S.ABCD",
        "desc": "Chóp tứ giác đều S.ABCD, SO vuông góc đáy tại tâm đối xứng O",
        "tags": ["3D", "Chop", "ChopDeu", "SO_vuong_day"],
        "source": "template",
        "tikz": r'''\begin{tikzpicture}[declare function={goc=-150; a=5; b=a/2; h=4.5;}]
\path (0,0) coordinate (A)
(a,0) coordinate (B)
(goc:b) coordinate (D)
+(a,0) coordinate (C)
($(A)!.5!(C)$) coordinate (O)--+(0,h) coordinate (S);
\draw[dashed] (S)--(A)--(B) (A)--(D) (S)--(O) (A)--(C) (B)--(D);
\draw (S)--(D)--(C)--(B)--(S)--(C);
\foreach \p/\pos in {S/above,A/above left,B/right,C/below right,D/below left,O/below}
    \filldraw (\p) circle (1pt) node[\pos] {$\p$};
\end{tikzpicture}'''
    },
    {
        "title": "Hình chóp cụt tứ giác đều",
        "desc": "Hình chóp cụt tứ giác đều ABCD.A'B'C'D' với 2 đáy song song",
        "tags": ["3D", "ChopCut", "HinhKhongGian"],
        "source": "template",
        "tikz": r'''\begin{tikzpicture}[declare function={gocx=60; goc=-150; a=5; b=a/2; h=5; k=0.5;}]
\path (0,0) coordinate (A)--+(gocx:h) coordinate (A')
(a,0) coordinate (B)
(goc:b) coordinate (D)
+(a,0) coordinate (C)
($(A')+(k*a,0)$) coordinate (B')
($(A')+(goc:k*b)$) coordinate (D')
+(k*a,0) coordinate (C');
\draw[dashed] (A')--(A)--(B) (A)--(D) (B')--(A')--(D');
\draw (B')--(C')--(D') (B)--(C)--(D) (B)--(B') (C)--(C') (D)--(D');
\foreach \p/\pos in {A/left,B/right,C/below,D/left,A'/above left,B'/above right,C'/right,D'/below left}
    \filldraw (\p) circle (1pt) node[\pos] {$\p$};
\end{tikzpicture}'''
    },
    {
        "title": "Hình lăng trụ tam giác đứng ABC.A'B'C'",
        "desc": "Lăng trụ tam giác đứng cạnh bên vuông góc với hai mặt đáy",
        "tags": ["3D", "LangTru", "LangTruDung"],
        "source": "template",
        "tikz": r'''\begin{tikzpicture}[declare function={goc=-45; a=4.5; b=0.45*a; h=5;}]
\path 
(0,0) coordinate (A)
(a,0) coordinate (C)
(goc:b) coordinate (B)
(0,h) coordinate (A')
(a,h) coordinate (C')
($(B)+(0,h)$) coordinate (B');
\draw[dashed] (A)--(C);
\draw (A)--(B)--(C) (A')--(B')--(C')--(A') (A)--(A') (B)--(B') (C)--(C');
\foreach \p/\pos in {A/left,B/below,C/right,A'/above left,B'/above,C'/above right}
    \filldraw (\p) circle (1pt) node[\pos] {$\p$};
\end{tikzpicture}'''
    },
    {
        "title": "Hình hộp chữ nhật ABCD.A'B'C'D'",
        "desc": "Hình hộp chữ nhật với ba kích thước a, b, c trực giao",
        "tags": ["3D", "HinhHop", "LapPhuong", "HinhKhongGian"],
        "source": "template",
        "tikz": r'''\begin{tikzpicture}[declare function={goc=225; a=2.5; b=5; h=4;}]
\path
(0,0) coordinate (A)
(b,0) coordinate (B)
(goc:a) coordinate (D)
($(D)+(B)-(A)$) coordinate (C)
(0,h) coordinate (A')
(b,h) coordinate (B')
($(D)+(0,h)$) coordinate (D')
($(C)+(0,h)$) coordinate (C');
\draw[dashed] (A')--(A)--(B) (A)--(D);
\draw (B)--(C)--(D) (A')--(B')--(C')--(D')--(A') (B)--(B') (C)--(C') (D)--(D');
\foreach \p/\pos in {A/above right,B/right,C/below right,D/below left,A'/above left,B'/above right,C'/above right,D'/above left}
    \filldraw (\p) circle (1pt) node[\pos] {$\p$};
\end{tikzpicture}'''
    },
    {
        "title": "Hình trụ tròn xoay",
        "desc": "Hình trụ tròn xoay bán kính đáy r, chiều cao h với hai đường sinh",
        "tags": ["3D", "MatTronXoay", "HinhTru"],
        "source": "template",
        "tikz": r'''\begin{tikzpicture}[scale=0.9]
\def\r{2.2}
\def\h{4.2}
\draw[dashed] (-\r,0) arc (180:0:\r cm and 0.65cm);
\draw (-\r,0) arc (180:360:\r cm and 0.65cm);
\draw (0,\h) ellipse (\r cm and 0.65cm);
\draw (-\r,0) -- (-\r,\h);
\draw (\r,0) -- (\r,\h);
\draw[dashed] (0,0) coordinate (O) -- (0,\h) coordinate (O');
\draw[dashed] (O) -- (\r,0) node[midway,above,font=\small] {$r$};
\draw (O') -- (\r,\h) node[midway,above,font=\small] {$r$};
\filldraw (O) circle (1pt) node[below] {$O$};
\filldraw (O') circle (1pt) node[above] {$O'$};
\node[right] at (\r,0.5*\h) {$h$};
\end{tikzpicture}'''
    },
    {
        "title": "Hình nón tròn xoay đỉnh S",
        "desc": "Hình nón đỉnh S, đáy hình tròn tâm O bán kính r, đường sinh l",
        "tags": ["3D", "MatTronXoay", "HinhNon"],
        "source": "template",
        "tikz": r'''\begin{tikzpicture}[scale=0.95]
\def\r{2.4}
\def\h{4.5}
\coordinate (S) at (0,\h);
\coordinate (O) at (0,0);
\coordinate (A) at (-\r,0);
\coordinate (B) at (\r,0);
\draw[dashed] (A) arc (180:0:\r cm and 0.7cm);
\draw (A) arc (180:360:\r cm and 0.7cm);
\draw (S) -- (A) (S) -- (B);
\draw[dashed] (S) -- (O) node[midway,left,font=\small] {$h$};
\draw[dashed] (O) -- (B) node[midway,below,font=\small] {$r$};
\filldraw (S) circle (1.2pt) node[above] {$S$};
\filldraw (O) circle (1.2pt) node[below] {$O$};
\node[right] at (0.5*\r,0.5*\h) {$l$};
\end{tikzpicture}'''
    },
    {
        "title": "Hình cầu và thiết diện đường tròn lớn",
        "desc": "Mặt cầu tâm O bán kính R với vòng xích đạo và trục thẳng đứng",
        "tags": ["3D", "MatTronXoay", "HinhCau", "MatCau"],
        "source": "template",
        "tikz": r'''\begin{tikzpicture}[scale=1.1]
\def\R{2.2}
\draw (0,0) coordinate (O) circle (\R);
\draw[dashed] (-\R,0) arc (180:0:\R cm and 0.75cm);
\draw (-\R,0) arc (180:360:\R cm and 0.75cm);
\draw[dashed] (0,-\R) -- (0,\R);
\draw[dashed] (O) -- (35:\R) node[midway,above,font=\small] {$R$};
\filldraw (O) circle (1.2pt) node[below left] {$O$};
\end{tikzpicture}'''
    },
    {
        "title": "Hình trụ nội tiếp hình nón",
        "desc": "Bài toán tối ưu thể tích khối trụ nội tiếp khối nón cho trước",
        "tags": ["3D", "ToiUu", "TruNoiTiepNon", "ThucTe"],
        "source": "template",
        "tikz": r'''\begin{tikzpicture}[scale=0.9]
\def\R{3.0} \def\H{5.0}
\def\r{1.8} \def\h{2.0}
\coordinate (S) at (0,\H);
\coordinate (O) at (0,0);
\draw[dashed] (-\R,0) arc (180:0:\R cm and 0.7cm);
\draw (-\R,0) arc (180:360:\R cm and 0.7cm);
\draw (S) -- (-\R,0) (S) -- (\R,0);
\draw[dashed] (S) -- (O);
% Trụ nội tiếp
\draw[dashed,teal] (-\r,\h) arc (180:0:\r cm and 0.45cm);
\draw[teal] (-\r,\h) arc (180:360:\r cm and 0.45cm);
\draw[dashed,teal] (-\r,0) arc (180:0:\r cm and 0.45cm);
\draw[teal] (-\r,0) arc (180:360:\r cm and 0.45cm);
\draw[teal,thick] (-\r,0) -- (-\r,\h) (\r,0) -- (\r,\h);
\filldraw (S) circle (1pt) node[above] {$S$};
\filldraw (O) circle (1pt) node[below] {$O$};
\end{tikzpicture}'''
    },
    {
        "title": "Bảng biến thiên hàm bậc 3 (2 cực trị)",
        "desc": "Bảng biến thiên chuẩn giáo khoa THPT sử dụng gói tkz-tab",
        "tags": ["BBT", "tkz-tab", "HamBac3", "KhaoSat"],
        "source": "template",
        "tikz": r'''\begin{tikzpicture}
\tkzTabInit[lgt=1.5,espcl=2.5]{$x$/1,$y'$/1,$y$/2}{$-\infty$,$1$,$3$,$+\infty$}
\tkzTabLine{,+,$0$,-,$0$,+,}
\tkzTabVar{-/$-\infty$,+/$4$,-/$-2$,+/$+\infty$}
\end{tikzpicture}'''
    },
    {
        "title": "Bảng biến thiên phân thức hữu tỉ bậc nhất / bậc nhất",
        "desc": "Bảng biến thiên hàm phân thức y = (ax+b)/(cx+d) có tiệm cận đứng",
        "tags": ["BBT", "tkz-tab", "PhanThuc", "TiemCan"],
        "source": "template",
        "tikz": r'''\begin{tikzpicture}
\tkzTabInit[lgt=1.5,espcl=2.8]{$x$/1,$y'$/1,$y$/2}{$-\infty$,$2$,$+\infty$}
\tkzTabLine{,-,d,-,}
\tkzTabVar{+/$1$,-D-/$-\infty$/$+\infty$,+/$1$}
\end{tikzpicture}'''
    },
    {
        "title": "Bài toán thực tế: Cầu treo dây văng Parabol",
        "desc": "Mô phỏng nhịp cầu treo dây văng dạng Parabol bắc qua sông",
        "tags": ["ThucTe", "Parabol", "CauTreo", "UngDung"],
        "source": "template",
        "tikz": r'''\begin{tikzpicture}[scale=0.95]
\draw[thick,brown!70!black] (-4,-0.2) rectangle (4,0);
\draw[thick,blue!60,fill=blue!10] (-4.5,-1.2) rectangle (4.5,-0.2);
\node[blue!80,font=\small] at (0,-0.7) {Mặt nước};
% Hai trụ cầu
\draw[thick,gray!80,fill=gray!20] (-3,0) rectangle (-2.6,3.5);
\draw[thick,gray!80,fill=gray!20] (2.6,0) rectangle (3,3.5);
% Dây cáp chính parabol y = a*x^2 + c
\draw[ultra thick,red!80,domain=-2.8:2.8,samples=60] plot (\x, {0.35*\x*\x + 0.6});
% Các dây văng thẳng đứng
\foreach \x in {-2.2,-1.6,-1.0,-0.4,0.4,1.0,1.6,2.2} {
    \draw[thin,gray!70] (\x,0) -- (\x,{0.35*\x*\x + 0.6});
}
\draw[<->,thick] (-2.8,3.7) -- (2.8,3.7) node[midway,above,font=\small] {$L = 120\text{ m}$};
\draw[<->,thick] (3.3,0) -- (3.3,3.5) node[midway,right,font=\small] {$h = 35\text{ m}$};
\end{tikzpicture}'''
    },
    {
        "title": "Bài toán thực tế: Ngọn hải đăng và góc quét tầm nhìn",
        "desc": "Bài toán lượng giác tính khoảng cách từ tàu thuyền đến chân ngọn hải đăng",
        "tags": ["ThucTe", "LuongGiac", "HaiDang", "TamGiacVuong"],
        "source": "template",
        "tikz": r'''\begin{tikzpicture}[scale=0.9]
% Biển
\fill[blue!10] (-0.5,-0.2) rectangle (7.5,-1.0);
\draw[thick,blue!60] (-0.5,-0.2) -- (7.5,-0.2);
% Ngọn hải đăng
\draw[thick,fill=gray!20] (0,0) -- (0.3,3.5) -- (-0.3,3.5) -- cycle;
\draw[fill=yellow!80] (-0.4,3.5) rectangle (0.4,3.8);
\node[above,font=\small] at (0,3.8) {Hải đăng $H$};
% Tàu thuyền
\coordinate (T1) at (3.5,0);
\coordinate (T2) at (6.5,0);
\draw[thick,brown!80,fill=brown!40] (3.1,0) -- (3.9,0) -- (3.7,-0.3) -- (3.3,-0.3) -- cycle;
\draw[thick,brown!80,fill=brown!40] (6.1,0) -- (6.9,0) -- (6.7,-0.3) -- (6.3,-0.3) -- cycle;
% Tia sáng
\draw[dashed,orange!80,thick] (0,3.6) -- (T1) node[midway,above,sloped,font=\footnotesize] {Tia nhìn $1$};
\draw[dashed,orange!80,thick] (0,3.6) -- (T2) node[midway,above,sloped,font=\footnotesize] {Tia nhìn $2$};
\draw (0,0) -- (0,3.6) node[midway,left,font=\small] {$h = 40\text{ m}$};
\draw (0,0) -- (T2);
\node[below,font=\small] at (3.5,-0.3) {Tàu $A$};
\node[below,font=\small] at (6.5,-0.3) {Tàu $B$};
\end{tikzpicture}'''
    },
    {
        "title": "Bài toán thực tế: Quỹ đạo ném bóng rổ Parabol",
        "desc": "Bài toán khảo sát quỹ đạo chuyển động ném xiên và xác định điểm rơi rổ",
        "tags": ["ThucTe", "VatLy", "Parabol", "BongRo"],
        "source": "template",
        "tikz": r'''\begin{tikzpicture}[>=stealth,scale=0.9]
\draw[->,thick] (-0.2,0) -- (6.5,0) node[below] {$x$ (m)};
\draw[->,thick] (0,-0.2) -- (0,4.5) node[left] {$y$ (m)};
\node[below left] at (0,0) {$O$};
% Vận động viên
\draw[thick] (0,0) -- (0,1.8) node[left] {Người ném};
\filldraw[orange!90] (0,2.0) circle (3pt) node[above left] {$M(0;2)$};
% Quỹ đạo ném: y = -0.2*(x-2.5)^2 + 3.8
\draw[thick,red!80,domain=0:5.2,samples=60] plot (\x, {-0.2*(\x-2.5)*(\x-2.5) + 3.25});
% Cột rổ
\draw[thick] (5.0,0) -- (5.0,3.05) node[right,font=\small] {Rổ ($3.05$m)};
\draw[thick,orange] (4.6,3.05) -- (5.0,3.05);
\filldraw[red!80] (4.8,3.05) circle (2.5pt);
\node[above,font=\small,red!80] at (2.5,3.3) {Đỉnh quỹ đạo};
\end{tikzpicture}'''
    },
    {
        "title": "Đường conic - Elip chính tắc và hai tiêu điểm",
        "desc": "Elip x^2/a^2 + y^2/b^2 = 1 với hai tiêu điểm F1(-c,0), F2(c,0)",
        "tags": ["Conic", "Elip", "TieuDiem", "HinhPhang"],
        "source": "template",
        "tikz": r'''\begin{tikzpicture}[>=stealth,scale=1.0]
\draw[->] (-3.8,0) -- (3.8,0) node[below] {$x$};
\draw[->] (0,-2.5) -- (0,2.5) node[left] {$y$};
\node[below left] at (0,0) {$O$};
\draw[thick,blue!80] (0,0) ellipse (3cm and 1.8cm);
\coordinate (F1) at (-2.4,0);
\coordinate (F2) at (2.4,0);
\coordinate (M) at (1.5,1.55);
\filldraw (F1) circle (1.5pt) node[below] {$F_1$};
\filldraw (F2) circle (1.5pt) node[below] {$F_2$};
\filldraw (M) circle (1.5pt) node[above right] {$M(x,y)$};
\draw[dashed,teal] (F1) -- (M) -- (F2);
\end{tikzpicture}'''
    },
    {
        "title": "Đường conic - Hypebol chính tắc và đường tiệm cận",
        "desc": "Hypebol x^2/a^2 - y^2/b^2 = 1 với hai đường tiệm cận y = ±(b/a)x",
        "tags": ["Conic", "Hypebol", "TiemCan", "HinhPhang"],
        "source": "template",
        "tikz": r'''\begin{tikzpicture}[>=stealth,scale=0.95]
\draw[->] (-4,0) -- (4,0) node[below] {$x$};
\draw[->] (0,-3) -- (0,3) node[left] {$y$};
\node[below left] at (0,0) {$O$};
% Tiệm cận y = ±0.75x
\draw[dashed,gray] (-3.5,-2.6) -- (3.5,2.6) node[right,font=\footnotesize] {$y=\frac{b}{a}x$};
\draw[dashed,gray] (-3.5,2.6) -- (3.5,-2.6);
% Nhánh phải x = 2*cosh(t), y = 1.5*sinh(t)
\draw[thick,blue!80,domain=-1.3:1.3,samples=50] plot ({2*cosh(\x)}, {1.5*sinh(\x)});
\draw[thick,blue!80,domain=-1.3:1.3,samples=50] plot ({-2*cosh(\x)}, {1.5*sinh(\x)});
\filldraw (2,0) circle (1.5pt) node[below right] {$A_2$};
\filldraw (-2,0) circle (1.5pt) node[below left] {$A_1$};
\end{tikzpicture}'''
    },
    {
        "title": "Tứ giác nội tiếp đường tròn",
        "desc": "Tứ giác ABCD nội tiếp đường tròn (O) với các góc đối bù nhau",
        "tags": ["HinhPhang", "DuongTron", "TuGiacNoiTiep"],
        "source": "template",
        "tikz": r'''\begin{tikzpicture}[scale=1.1]
\coordinate (O) at (0,0);
\def\R{2.2}
\draw[thick] (O) circle (\R);
\coordinate (A) at (130:\R);
\coordinate (B) at (40:\R);
\coordinate (C) at (-50:\R);
\coordinate (D) at (-140:\R);
\draw[thick,blue!80] (A) -- (B) -- (C) -- (D) -- cycle;
\draw[dashed,gray] (A) -- (C) (B) -- (D);
\foreach \p/\pos in {A/above left,B/above right,C/below right,D/below left,O/below}
    \filldraw (\p) circle (1pt) node[\pos] {$\p$};
\end{tikzpicture}'''
    }
]

# Next available ID
max_id = 0
for e in existing_entries:
    try:
        val = int(e['id'])
        if val > max_id:
            max_id = val
    except:
        pass

for m in new_models:
    max_id += 1
    fid = f"{max_id:03d}"
    tex_path = os.path.join(bank_dir, f'figure_{fid}.tex')
    png_path = os.path.join(bank_dir, f'figure_{fid}.png')
    
    with open(tex_path, 'w', encoding='utf-8') as f:
        f.write(m['tikz'])
    
    ok = compile_tikz_to_png(m['tikz'], png_path)
    print(f"Added Model #{fid} ({m['title']}) -> Render: {ok}")
    
    entry = {
        "id": fid,
        "title": m['title'],
        "description": m['desc'],
        "tags": m['tags'],
        "source": m.get('source', 'template'),
        "tex_filename": f'figure_{fid}.tex',
        "png_filename": f'figure_{fid}.png' if ok else '',
        "created_at": "2026-10-17T04:24:00Z",
        "char_count": len(m['tikz'])
    }
    existing_entries.insert(0, entry) # Insert at top

# Save updated index.json with utf-8-sig
with open(idx_path, 'w', encoding='utf-8-sig') as f:
    json.dump(existing_entries, f, ensure_ascii=False, indent=2)

print(f"Total entries in figure bank now: {len(existing_entries)}")
