# Kỹ Năng AI Vẽ Hình TikZ — Thầy Đỗ Minh (DoMinhMath) Style

Bộ tài liệu này là **Skill hoàn chỉnh** tổng hợp từ toàn bộ hệ thống ứng dụng Code TikZ AI.

---

## Cấu trúc thư mục

```
tikz_ai_skill/
├── README.md                  ← File này — hướng dẫn tổng quan
├── SKILL.md                   ← System Prompt tổng hợp (dùng cho 1 file duy nhất)
├── 01-workflow.md             ← Quy trình 5 bước bắt buộc
├── 02-structure-and-font.md  ← Cấu trúc, khai báo biến, font chữ
├── 03-geometry.md             ← Hình học phẳng và không gian 3D
├── 04-graph.md                ← Đồ thị hàm số, hệ trục, tiệm cận
├── 05-bbt-bxd.md             ← Bảng biến thiên và bảng xét dấu
├── 06-pattern-area.md        ← Tô miền diện tích, pattern, trục số
├── 07-labels-points.md       ← Nhãn điểm, nhãn đường, tránh chồng lấn
├── 08-latex-builder.md       ← Tự động tạo preamble LaTeX
├── 09-optimization-prompt.md ← Prompt tối ưu hóa code có sẵn
└── 10-code-examples.md       ← Code mẫu chuẩn theo từng loại hình
```

---

## Cách sử dụng

### Option A: Một file duy nhất (đơn giản nhất)
Sao chép nội dung **`SKILL.md`** và dán vào:
- **ChatGPT Custom GPT**: Mục *Instructions*
- **Claude Project**: Mục *Custom Instructions*
- **Gemini**: Tham số `systemInstruction`
- **OpenAI API**: Tham số `system`

### Option B: Từng tính năng riêng lẻ
Chọn file phù hợp theo loại hình cần vẽ:
- Hình học → `03-geometry.md`
- Đồ thị → `04-graph.md`
- BBT/BXD → `05-bbt-bxd.md`
- Tô miền → `06-pattern-area.md`

### Option C: Tích hợp vào code (API)

```javascript
// Node.js + Google GenAI
import { GoogleGenAI } from "@google/genai";
import fs from "fs";

const ai = new GoogleGenAI({ apiKey: process.env.GEMINI_API_KEY });
const skillPrompt = fs.readFileSync('./tikz_ai_skill/SKILL.md', 'utf8');

const response = await ai.models.generateContentStream({
  model: "gemini-2.5-pro",
  contents: "Vẽ đồ thị hàm số y = x^3 - 3x và bảng biến thiên",
  config: {
    systemInstruction: skillPrompt,
    thinkingConfig: { thinkingBudget: -1 }  // Thinking cao nhất
  }
});
```

```python
# Python + Google GenAI
import google.generativeai as genai

with open('./tikz_ai_skill/SKILL.md', 'r', encoding='utf-8') as f:
    skill_prompt = f.read()

model = genai.GenerativeModel(
    model_name="gemini-2.5-pro",
    system_instruction=skill_prompt
)
response = model.generate_content("Vẽ hình chóp S.ABCD...")
```

---

## Các quy tắc quan trọng nhất (nhớ 10 điều này)

1. **Font**: Chỉ dùng `every node/.style={font=\normalsize}` — không có `\Large`, `\large` bất kỳ đâu.
2. **Biến**: Luôn dùng `declare function={a=5; h=4;}` — không số cứng trong tọa độ.
3. **Tọa độ cực**: `(0:a)` thay `(a,0)`, `(180:a)` thay `(-a,0)`.
4. **Line cap**: TUYỆT ĐỐI CẤM `line cap=round`.
5. **Line join**: Chỉ dùng `line join=round` cho đồ thị/đường cong, KHÔNG cho hình học.
6. **Nhãn foreach**: Dùng số đo độ (`shift={(135:9pt)}`), không dùng above/below/left/right.
7. **BBT mũi tên**: CẤM `\tkzTabVar`, phải vẽ thủ công bằng `\path + \draw[-Stealth]`.
8. **BBT dấu d**: Bỏ chữ `d` trong `\tkzTabLine`, để khoảng trắng.
9. **Tiệm cận**: Phải nằm trong scope clip, đứng TRƯỚC đồ thị.
10. **Pattern**: Góc xiên (45, 60...), `distance=4pt`, `gray!70` — KHÔNG dùng `north west lines`.

---

## Nguồn gốc

Skill được tổng hợp và tối ưu từ toàn bộ hệ thống ứng dụng **Code TikZ AI** do Thầy Đỗ Minh (DoMinhMath) phát triển, bao gồm:
- `services/geminiService.ts` — System prompt và Style Guide
- `components/AIAssistant.tsx` — Optimization prompt (TIKZ_OPTIMIZATION_PROMPT)
- `utils/latexBuilder.ts` — Logic tự động tạo preamble
- `utils/tikzOptimizer.ts` — Kiểm tra syntax, tìm kiếm, thay thế thông minh
- `constants.tsx` — Thư viện hàng trăm template TikZ mẫu chuẩn
