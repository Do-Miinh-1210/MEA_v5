# CHECKLIST ĐỊNH DẠNG MATRIXEXAMAI

Dùng checklist này trước khi copy output vào app.

## Câu hỏi

- [ ] Mỗi câu nằm trong `===CAU===` và `===KETCAU===`.
- [ ] KHÔNG có bất kỳ thẻ trích dẫn nào như `[cite: ...]`, `[source: ...]`, `[1]`, `[2]`.
- [ ] Có `LOAI`.
- [ ] Có `MUCDO`.
- [ ] Có `CHUONG`.
- [ ] Có `NOIDUNG`.
- [ ] Có `DAPAN` nếu là TN/DS/TLN.
- [ ] Có `LOIGIAI`.

## Loại câu

- [ ] TN có A/B/C/D.
- [ ] TN có đúng 1 đáp án A/B/C/D.
- [ ] DS có a/b/c/d.
- [ ] DS có `DAPAN: a=D,b=S,c=D,d=S`.
- [ ] TLN đáp án là số ngắn.
- [ ] TL có lời giải đầy đủ.

## Công thức

- [ ] Tất cả công thức dùng `${...}`.
- [ ] Không có `$$...$$`.
- [ ] Không có `\(...\)`.
- [ ] Không có `\[...\]`.
- [ ] Không có Unicode toán học trực tiếp.

## TikZ

- [ ] TikZ bắt đầu `\begin{tikzpicture}`.
- [ ] TikZ kết thúc `\end{tikzpicture}`.
- [ ] Bảng biến thiên dùng `\tkzTabVar` (CẤM dùng `\tkzTabVector`).
- [ ] Không có `\documentclass` nếu dùng trong app.
- [ ] Không có `\usepackage` nếu dùng trong app.
- [ ] Không có markdown fence.
- [ ] Hình đúng dữ kiện đề.

## Bảng số liệu

- [ ] Dùng bảng chuẩn Markdown (`| col | col | \n | --- | --- |`), hoặc LaTeX `\begin{tabular}`, hoặc phân cách `|`.
- [ ] Đảm bảo đủ số cột ở mọi dòng, không bị ngắt dòng dở dang.
- [ ] Bảng đặt ngay trong `NOIDUNG` hoặc `LOIGIAI`.

## Output

- [ ] Không có lời chào.
- [ ] Không có giải thích ngoài khối nếu app cần import.
- [ ] Không có markdown nếu app cần parse.
- [ ] Đáp án đã được kiểm tra lại.


