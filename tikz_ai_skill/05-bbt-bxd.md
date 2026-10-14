# 05 — BẢNG BIẾN THIÊN (BBT) VÀ BẢNG XÉT DẤU (BXD)

---

## 5.1. KHỞI TẠO BẢNG — `\tkzTabInit`

### Cú pháp chuẩn
```latex
\tkzTabInit[nocadre=false, lgt=..., espcl=..., deltacl=0.6]
  {$x$/0.7, $f'(x)$/0.7, $f(x)$/2.5}%
  {$-\infty$, $x_1$, $x_2$, $+\infty$}
```

### Bảng chọn tham số

| Tham số | Giá trị | Điều kiện |
|---|---|---|
| `nocadre` | `false` (mặc định) | Luôn có khung |
| `deltacl` | `0.6` | **Cố định, không thay đổi** |
| `lgt` | `1.2` | Khi nhãn hàm là **"y"** |
| `lgt` | `1.5` | Khi nhãn hàm là **"f(x)"** |
| `espcl` | `3.5` | Khi x có **3 giá trị** (gồm ±∞) |
| `espcl` | `2.5` | Khi x có **4 giá trị** |
| `espcl` | `2.0` | Khi x có **5 giá trị** |

### Chiều cao dòng

| Dòng | Chiều cao | Ghi chú |
|---|---|---|
| `$x$` | `0.7` | Cố định |
| `$f'(x)$` hoặc `$y'$` | `0.7` | Cố định |
| `$f(x)$` hoặc `$y$` (dòng cuối) | `2.0` nếu x có 3 giá trị | Cố định theo số giá trị |
| | `2.5` nếu x có 4 hoặc 5 giá trị | |

```latex
% Ví dụ: f(x) với 4 giá trị x:
{$x$/0.7, $f'(x)$/0.7, $f(x)$/2.5}
{$-\infty$, $0$, $2$, $+\infty$}
```

---

## 5.2. DÒNG XÉT DẤU — `\tkzTabLine`

### Quy tắc QUAN TRỌNG: Bỏ chữ `d`
Trong `\tkzTabLine`, ký tự `d` (undefined/discontinuity) **BẮT BUỘC bị bỏ**, thay bằng khoảng trống:

```latex
% SAI — có chữ d:
\tkzTabLine{, -, 0, +, d, +, 0, -, }

% ĐÚNG — bỏ chữ d, để khoảng trắng:
\tkzTabLine{, -, 0, +,  , +, 0, -, }
```

### Ký hiệu trong `\tkzTabLine`
- `+` — dương
- `-` — âm
- `0` — bằng 0
- ` ` (khoảng trắng) — không xác định (thay cho `d`)
- `,` — phân cách các vùng

---

## 5.3. MŨI TÊN BIẾN THIÊN — VẼ THỦ CÔNG (BẮT BUỘC)

> **CẤM TUYỆT ĐỐI** dùng `\tkzTabVar`. Phải vẽ thủ công bằng `\path` và `\draw[-Stealth]`.

### Hệ thống tọa độ Node của `tkz-tab`

`tkz-tab` tự động sinh ra các điểm tọa độ theo quy tắc:
- `Nij`: hàng `i`, cột `j` trong bảng biến thiên
- `j=2`: gần dòng kẻ trên (giá trị cao)
- `j=3`: gần dòng kẻ dưới (giá trị thấp)

### Quy tắc `yshift`

| Vị trí nhãn giá trị | Node dùng | yshift |
|---|---|---|
| Điểm CAO (gần mép trên) | `Ni2` | `yshift=-8pt` |
| Điểm CAO nhưng cần cách xa hơn | `Ni2` | `yshift=-16pt` |
| Điểm THẤP (gần mép dưới) | `Ni3` | `yshift=8pt` |
| Điểm THẤP cần cách xa hơn | `Ni3` | `yshift=16pt` |
| Tiệm cận đứng (dịch ngang) | `Ni2`/`Ni3` | `xshift=±16pt` |

### Cú pháp chuẩn vẽ mũi tên

```latex
% Bước 1: Đặt các node giá trị
\path
  ([yshift=8pt]N13) node (A1){$-\infty$}
  ([yshift=-8pt]N22) node (A2){$-\dfrac{22}{27}$}
  ([yshift=-8pt]N32) node (A3){$-2$}
  ([yshift=8pt]N43) node (A4){$+\infty$};

% Bước 2: Vẽ mũi tên nối các node
\foreach \i/\j in {1/2, 2/3, 3/4}{
  \draw[-Stealth] (A\i) -- (A\j);
}
```

### Ví dụ 3 cột (hàm 1 cực trị)
```latex
\path
  ([yshift=8pt]N13) node (A1){$-\infty$}
  ([yshift=-8pt]N22) node (A2){$m$}           % cực đại
  ([yshift=8pt]N33) node (A3){$+\infty$};

\foreach \i/\j in {1/2, 2/3}{\draw[-Stealth](A\i)--(A\j);}
```

### Ví dụ 4 cột (hàm 2 cực trị)
```latex
\path
  ([yshift=8pt]N13) node (A1){$-\infty$}
  ([yshift=-8pt]N22) node (A2){$M_{cd}$}      % cực đại
  ([yshift=8pt]N33) node (A3){$m_{ct}$}       % cực tiểu
  ([yshift=-8pt]N42) node (A4){$+\infty$};

\foreach \i/\j in {1/2, 2/3, 3/4}{\draw[-Stealth](A\i)--(A\j);}
```

---

## 5.4. ĐIỂM KHÔNG XÁC ĐỊNH

Khi hàm không xác định tại một điểm (tiệm cận đứng), vẽ 2 đường song song:

```latex
% Dạng chuẩn (bắt buộc):
\draw[double distance=1pt, double=white, line width=0.4pt] (N22) -- (N23);
```

---

## 5.5. PHÂN SỐ TRONG BBT

**BẮT BUỘC** dùng `\dfrac{}{}`, không dùng `\frac`:

```latex
% SAI:
node (A2) {$\frac{1}{3}$}

% ĐÚNG:
node (A2) {$\dfrac{1}{3}$}
```

---

## 5.6. VÍ DỤ BBT ĐẦY ĐỦ — HÀM BẬC BA

```latex
% code Bảng biến thiên
\begin{tikzpicture}[every node/.style={font=\normalsize}]

\tkzTabInit[nocadre=false, lgt=1.5, espcl=2.5, deltacl=0.6]
  {$x$/0.7, $f'(x)$/0.7, $f(x)$/2.5}%
  {$-\infty$, $-1$, $\dfrac{5}{3}$, $+\infty$}

\tkzTabLine{, +, 0, -,  , +, }

\path
  ([yshift=8pt]N13) node (A1){$-\infty$}
  ([yshift=-8pt]N22) node (A2){$\dfrac{4}{27}$}
  ([yshift=8pt]N33) node (A3){$-2$}
  ([yshift=-8pt]N42) node (A4){$+\infty$};

\foreach \i/\j in {1/2, 2/3, 3/4}{\draw[-Stealth](A\i)--(A\j);}

\end{tikzpicture}
```

---

## 5.7. BẢNG XÉT DẤU (BXD)

Tương tự BBT nhưng **chỉ có 2 dòng**, không có dòng mũi tên.

```latex
\begin{tikzpicture}[every node/.style={font=\normalsize}]

\tkzTabInit[nocadre=false, lgt=1.5, espcl=2.5, deltacl=0.6]
  {$x$/1, $f'(x)$/0.7}%
  {$-\infty$, $-2$, $3$, $+\infty$}

\tkzTabLine{, -, 0, +,  , +, }

\end{tikzpicture}
```

**Sự khác biệt BXD vs BBT:**

| | BBT | BXD |
|---|---|---|
| Số dòng | 3 (x, f'(x), f(x)) | 2 (x, f'(x)) |
| Chiều cao dòng 1 | `$x$/0.7` | `$x$/1` |
| Mũi tên | Có (vẽ thủ công) | Không |
| Mục đích | Biến thiên hàm số | Xét dấu biểu thức |

---

## 5.8. CHẾ ĐỘ `nocadre=true` (KHÔNG KHUNG)

Khi người dùng bật tùy chọn "BBT không khung":
- Tự động thay `nocadre=false` → `nocadre=true` trong toàn bộ code.
- Mọi quy tắc khác giữ nguyên.
