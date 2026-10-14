# 08 — TỰ ĐỘNG TẠO PREAMBLE LATEX (LaTeX Builder)

Khi cần xuất file `.tex` hoàn chỉnh (có `\documentclass`), hệ thống tự động quét code TikZ thuần và thêm đúng packages + libraries cần thiết. Logic này được implement trong `latexBuilder.ts`.

---

## 8.1. CẤU TRÚC PREAMBLE CHUẨN

```latex
\documentclass[tikz,border=10mm]{standalone}
% --- PACKAGES MẶC ĐỊNH (luôn có) ---
\usepackage[utf8]{vietnam}
\usepackage{amsmath,amssymb,amsfonts,mathtools,bm}
% --- PACKAGES TÙY CHỌN (tự động phát hiện) ---
% ...
\usetikzlibrary{...}
% --- CONFIG ---
% ...
\begin{document}
% --- CODE TIKZ THUẦN ---
\end{document}
```

---

## 8.2. PHÁT HIỆN PACKAGES TỰ ĐỘNG

Hệ thống quét code bằng regex để thêm đúng packages:

| Phát hiện trong code | Package thêm vào |
|---|---|
| `\qty`, `\SI`, `\norm`, `\abs`, `\dd`, `\dv`... | `physics`, `siunitx` + config `\sisetup{per-mode=symbol}` |
| `\ce`, `\ch`, `\chemfig` | `mhchem[version=4]`, `chemfig` |
| `circuitikz` hoặc `to[` + từ `american` | `circuitikz[american, scale=1.2]` |
| `circuitikz` hoặc `to[` (không có `american`) | `circuitikz[european, scale=1.2]` |
| `\includegraphics` | `graphicx` |
| `pgfplots`, `axis`, `addplot` | `pgfplots` + `\pgfplotsset{compat=1.18}` + `\usepgfplotslibrary{fillbetween,statistics}` |
| `\tkz` (nhưng không `\tkzTab`) | `tkz-euclide` |
| `tdplot` | `tikz-3dplot` |
| `lstlisting`, `\lst` | `listings` |
| `\tkzTab` | `tkz-tab`, `tabvar` |
| `tabular`, `table`, `figure`, `multirow`, `\toprule` | `float,caption,subcaption,booktabs,multirow,array` |

---

## 8.3. PHÁT HIỆN THƯVIỆN TIKZ TỰ ĐỘNG

| Phát hiện trong code | Library thêm vào |
|---|---|
| **(Luôn có)** | `arrows.meta` |
| `$` (dollar sign) hoặc `calc` | `calc` |
| `intersection` | `intersections` |
| `above=`, `below=`, `left=`, `right=`, `positioning` | `positioning` |
| `ellipse`, `polygon`, `star`, `shapes.geometric` | `shapes.geometric` |
| `pattern` | `patterns.meta` |
| `decorat` | `decorations.markings`, `decorations.pathmorphing` |
| `pic`, `angle`, `right angle` | `angles`, `quotes` + `\tikzset{right angle/.style={angle}}` |
| `circle through` | `through` |
| `background` | `backgrounds` |
| `fit=` | `fit` |
| `mark=` | `plotmarks` |
| `chain` | `chains` |
| `matrix` | `matrix` |
| `perspective` | `perspective` |
| `canvas is` | `3d` |

---

## 8.4. TRÍCH XUẤT CODE TIKZ TỪ FULL LATEX

Khi nhận code từ AI có thể kèm preamble đầy đủ, hệ thống tự rút trích phần TikZ thuần:

### Ưu tiên trích xuất (theo thứ tự)

1. **Có `\begin{document}` và `\end{document}`:**  
   Lấy phần nằm **giữa** hai môi trường này.

2. **Có `\documentclass` + `\begin{tikzpicture}` + `\end{tikzpicture}`:**  
   Lấy toàn bộ môi trường `tikzpicture`.

3. **Có `\documentclass` + `\begin{circuitikz}` + `\end{circuitikz}`:**  
   Lấy toàn bộ môi trường `circuitikz`.

4. **Không có cái nào trên:**  
   Giữ nguyên code gốc.

### Ví dụ
```latex
% INPUT (AI trả về có đủ preamble):
\documentclass[tikz]{standalone}
\usepackage{tikz}
\begin{document}
\begin{tikzpicture}[...]
  \draw (0,0) -- (1,1);
\end{tikzpicture}
\end{document}

% OUTPUT (sau khi trích xuất — chỉ còn TikZ thuần):
\begin{tikzpicture}[...]
  \draw (0,0) -- (1,1);
\end{tikzpicture}
```

---

## 8.5. HƯỚNG DẪN CHO AI

Khi người dùng yêu cầu xuất full document (`.tex`):

1. **Luôn có** `\usepackage[utf8]{vietnam}` trong preamble.
2. Quét code để phát hiện và thêm đúng packages (theo bảng 8.2 và 8.3).
3. Dùng `\documentclass[tikz,border=10mm]{standalone}` làm document class.
4. Không thêm packages không cần thiết (gây compile chậm, conflict).

```latex
% Template đầy đủ tối thiểu khi xuất file .tex:
\documentclass[tikz,border=10mm]{standalone}
\usepackage[utf8]{vietnam}
\usepackage{amsmath,amssymb,amsfonts,mathtools,bm}
\usetikzlibrary{arrows.meta,calc}
% (thêm các packages/libraries khác theo nhu cầu)
\begin{document}

\begin{tikzpicture}[...code của bạn...]
  ...
\end{tikzpicture}

\end{document}
```
