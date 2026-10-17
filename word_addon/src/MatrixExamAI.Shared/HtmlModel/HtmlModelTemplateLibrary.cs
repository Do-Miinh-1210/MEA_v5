using System;
using System.Collections.Generic;

namespace MatrixExamAI.Shared.HtmlModel
{
    public class HtmlModelTemplateItem
    {
        public string Id { get; set; } = string.Empty;
        public string Title { get; set; } = string.Empty;
        public string Category { get; set; } = string.Empty;
        public string Description { get; set; } = string.Empty;
        public string HtmlCode { get; set; } = string.Empty;
    }

    /// <summary>
    /// Thư viện mẫu mô hình mô phỏng Toán học & Khoa học tương tác 3D HTML / Three.js / KaTeX.
    /// </summary>
    public static class HtmlModelTemplateLibrary
    {
        public static readonly List<string> Categories = new List<string>
        {
            "Toán 11: Cấp số nhân & Phân dạng Sierpinski",
            "Toán 12: Khối tròn xoay & Tích phân",
            "Toán học: Hình không gian & Thiết diện 3D",
            "Toán học: Tọa độ không gian Oxyz",
            "Toán học: Đồ thị hàm số & Mặt cong 3D",
            "Vật lý: Dao động điều hòa & Sóng cơ",
            "Hóa học: Cấu trúc phân tử 3D",
            "Sinh học: Cấu trúc ADN & Tế bào",
            "Ứng dụng thực tế & Kỹ thuật"
        };

        public static List<HtmlModelTemplateItem> GetAllTemplates()
        {
            return new List<HtmlModelTemplateItem>
            {
                GetTemplateSierpinski232(),
                GetTemplateSolidOfRevolution(),
                GetTemplateSphereSection(),
                GetTemplatePyramidSection(),
                GetTemplateOxyzVectors(),
                GetTemplateSurfaceCalculus(),
                GetTemplatePhysicsPendulum(),
                GetTemplateChemistryMolecule(),
                GetTemplateBiologyDna()
            };
        }

        public static HtmlModelTemplateItem GetTemplateSolidOfRevolution()
        {
            return new HtmlModelTemplateItem
            {
                Id = "solid_rev_cau6",
                Title = "Khối tròn xoay: Miền (R) xoay quanh trục AB (Câu 6 THPT)",
                Category = "Toán 12: Khối tròn xoay & Tích phân",
                Description = "Mô phỏng song song 2D và 3D khối tròn xoay tạo bởi 2 cung phần tư đường tròn trong hình vuông xoay quanh cạnh AB, quét thiết diện R(y), thanh trượt góc xoay và 4 bước giải chi tiết KaTeX.",
                HtmlCode = @"<!DOCTYPE html>
<html lang=""vi"">
<head>
    <meta charset=""UTF-8"">
    <meta name=""viewport"" content=""width=device-width, initial-scale=1.0"">
    <title>Mô Phỏng & Giải Chi Tiết: Thể Tích Khối Tròn Xoay (Câu 6)</title>
    <!-- Tailwind CSS -->
    <script src=""https://cdn.tailwindcss.com""></script>
    <!-- Google Fonts -->
    <link href=""https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap"" rel=""stylesheet"">
    <!-- KaTeX CSS & JS -->
    <link rel=""stylesheet"" href=""https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.css"">
    <script src=""https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.js""></script>
    <script src=""https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/contrib/auto-render.min.js""></script>
    <!-- Three.js -->
    <script src=""https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js""></script>

    <style>
        body {
            font-family: 'Inter', sans-serif;
            background-color: #f8fafc;
            color: #0f172a;
        }
        ::-webkit-scrollbar {
            width: 6px;
            height: 6px;
        }
        ::-webkit-scrollbar-track {
            background: #f1f5f9;
            border-radius: 4px;
        }
        ::-webkit-scrollbar-thumb {
            background: #cbd5e1;
            border-radius: 4px;
        }
        ::-webkit-scrollbar-thumb:hover {
            background: #94a3b8;
        }
        input[type=""range""] {
            accent-color: #0d9488;
        }
        .katex-display {
            margin: 0.65em 0 !important;
            overflow-x: auto;
            overflow-y: hidden;
            padding: 0.25rem 0;
        }
        .step-card {
            transition: all 0.25s ease;
        }
        .step-card.active-step {
            border-color: #0d9488;
            box-shadow: 0 4px 14px -2px rgba(13, 148, 136, 0.15);
            background-color: #f0fdfa;
        }
    </style>
</head>

<body class=""min-h-screen flex flex-col"">
    <!-- Top Header -->
    <header class=""bg-white border-b border-slate-200 sticky top-0 z-20 shadow-sm"">
        <div class=""max-w-7xl mx-auto px-4 py-3 flex flex-wrap items-center justify-between gap-3"">
            <div class=""flex items-center gap-3"">
                <span class=""inline-flex items-center justify-center w-9 h-9 rounded-xl bg-teal-600 text-white font-bold text-lg shadow-sm"">
                    6
                </span>
                <div>
                    <h1 class=""text-base sm:text-lg font-bold text-slate-800 leading-tight"">
                        Ứng Dụng Tích Phân: Thể Tích Khối Tròn Xoay
                    </h1>
                    <p class=""text-xs text-slate-500"">
                        Mô phỏng trực quan 2D & 3D đúng tính chất hình học • Không che lấp vùng biểu diễn
                    </p>
                </div>
            </div>

            <!-- Answer Verification & Quick Result -->
            <div class=""flex items-center gap-2 sm:gap-3"">
                <div class=""flex items-center bg-slate-100 border border-slate-300 rounded-lg px-2.5 py-1.5 gap-2"">
                    <span class=""text-xs font-semibold text-slate-700"">KQ:</span>
                    <input id=""ansInput"" type=""text"" value=""10,5"" aria-label=""Kết quả""
                        class=""w-16 text-center font-bold text-teal-800 bg-white border border-slate-300 rounded px-1.5 py-0.5 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500"">
                    <button id=""checkAnsBtn"" class=""text-xs bg-teal-600 hover:bg-teal-700 text-white font-medium px-2.5 py-1 rounded transition"">
                        Kiểm tra
                    </button>
                </div>
                <span id=""ansFeedback"" class=""hidden text-xs font-semibold px-2.5 py-1 rounded-full bg-emerald-100 text-emerald-800"">
                    ✓ Chính xác ($10{,}5\text{ cm}^3$)
                </span>
            </div>
        </div>
    </header>

    <main class=""flex-1 max-w-7xl w-full mx-auto px-4 py-4 flex flex-col gap-4"">
        <!-- Problem Statement Box -->
        <section class=""bg-[#f4fbf9] border-2 border-teal-700/70 rounded-xl p-3.5 sm:p-4 shadow-sm"">
            <div class=""flex items-start justify-between gap-4"">
                <div class=""text-sm sm:text-base text-slate-800 leading-relaxed"">
                    <span class=""font-bold text-teal-800 inline-flex items-center gap-1 mr-1"">
                        ❖ Câu 6.
                    </span>
                    Một vật trang trí có dạng một khối tròn xoay được tạo thành khi xoay miền $(R)$ (phần gạch chéo trong hình vẽ) quanh trục $AB$. Miền $(R)$ được giới hạn bởi các cạnh $AB, AD$ của hình vuông $ABCD$ và các cung phần tư của các đường tròn bán kính bằng $1\text{ cm}$ với tâm lần lượt là trung điểm của các cạnh $BC, AD$. Tính thể tích của vật trang trí đó (đơn vị $\text{cm}^3$), làm tròn kết quả đến hàng phần mười.
                </div>
                <button id=""toggleProblemBtn"" class=""shrink-0 text-xs font-medium text-teal-700 hover:text-teal-900 bg-teal-100/80 hover:bg-teal-200/70 px-2.5 py-1 rounded-lg transition"">
                    Thu gọn đề
                </button>
            </div>
        </section>

        <!-- Main Workspace Grid -->
        <div class=""grid grid-cols-1 lg:grid-cols-12 gap-4 items-start"">
            <!-- LEFT COLUMN: VISUAL SIMULATION -->
            <div class=""lg:col-span-7 bg-white border border-slate-200 rounded-2xl shadow-sm flex flex-col overflow-hidden"">
                <!-- Simulation Top Toolbar -->
                <div class=""bg-slate-50 border-b border-slate-200 p-3 flex flex-wrap items-center justify-between gap-2"">
                    <!-- View Mode Tabs -->
                    <div class=""inline-flex rounded-lg bg-slate-200/80 p-1 text-xs font-semibold"">
                        <button data-view=""split"" class=""view-tab px-3 py-1.5 rounded-md bg-white text-teal-700 shadow-sm transition"">
                            Song song (2D + 3D)
                        </button>
                        <button data-view=""2d"" class=""view-tab px-3 py-1.5 rounded-md text-slate-600 hover:text-slate-900 transition"">
                            Hình phẳng 2D
                        </button>
                        <button data-view=""3d"" class=""view-tab px-3 py-1.5 rounded-md text-slate-600 hover:text-slate-900 transition"">
                            Khối tròn xoay 3D
                        </button>
                    </div>

                    <!-- Checkboxes for Geometry Overlays -->
                    <div class=""flex flex-wrap items-center gap-3 text-xs font-medium text-slate-700"">
                        <label class=""inline-flex items-center gap-1.5 cursor-pointer select-none"">
                            <input type=""checkbox"" id=""chkAxes"" checked class=""rounded text-teal-600 focus:ring-teal-500"">
                            <span>Hệ trục tọa độ</span>
                        </label>
                        <label class=""inline-flex items-center gap-1.5 cursor-pointer select-none"">
                            <input type=""checkbox"" id=""chkConstruction"" checked class=""rounded text-teal-600 focus:ring-teal-500"">
                            <span>Tâm $M, N$ & đường phụ</span>
                        </label>
                        <label class=""inline-flex items-center gap-1.5 cursor-pointer select-none"">
                            <input type=""checkbox"" id=""chkSplitVol"" checked class=""rounded text-teal-600 focus:ring-teal-500"">
                            <span>Tách màu $V_1, V_2$</span>
                        </label>
                    </div>
                </div>

                <!-- Canvas Stage -->
                <div id=""canvasGrid"" class=""grid grid-cols-1 md:grid-cols-2 divide-y md:divide-y-0 md:divide-x divide-slate-200 bg-white"">
                    <!-- 2D Figure Panel -->
                    <div id=""panel2D"" class=""flex flex-col"">
                        <div class=""px-3 py-1.5 bg-slate-50/70 border-b border-slate-100 flex items-center justify-between text-xs text-slate-600"">
                            <span class=""font-semibold text-slate-700"">Mặt phẳng hình vuông $ABCD$ & miền $(R)$</span>
                            <span class=""text-[11px] text-teal-700 font-medium"">Trục quay: $AB$</span>
                        </div>
                        <div class=""relative w-full h-[340px] sm:h-[380px] bg-white flex items-center justify-center"">
                            <canvas id=""canvas2D"" class=""w-full h-full block""></canvas>
                        </div>
                    </div>

                    <!-- 3D Solid of Revolution Panel -->
                    <div id=""panel3D"" class=""flex flex-col"">
                        <div class=""px-3 py-1.5 bg-slate-50/70 border-b border-slate-100 flex items-center justify-between text-xs text-slate-600"">
                            <span class=""font-semibold text-slate-700"">Mô hình 3D xoay quanh trục $AB$</span>
                            <button id=""resetCamBtn"" class=""text-[11px] text-teal-700 hover:underline font-medium"">
                                Đặt lại góc nhìn 3D
                            </button>
                        </div>
                        <div id=""container3D"" class=""relative w-full h-[340px] sm:h-[380px] bg-slate-900 flex items-center justify-center cursor-grab active:cursor-grabbing"">
                        </div>
                    </div>
                </div>

                <!-- Interactive Sliders & Controls -->
                <div class=""bg-slate-50 border-t border-slate-200 p-3.5 flex flex-col gap-3"">
                    <div class=""grid grid-cols-1 sm:grid-cols-2 gap-4"">
                        <!-- Rotation Angle Control -->
                        <div class=""bg-white border border-slate-200 rounded-xl p-2.5 flex flex-col gap-1.5"">
                            <div class=""flex items-center justify-between text-xs"">
                                <span class=""font-semibold text-slate-700"">Góc xoay quanh trục $AB$: <strong id=""lblAngle"" class=""text-teal-700"">360°</strong></span>
                                <button id=""btnPlayRotate"" class=""px-2.5 py-0.5 rounded bg-teal-600 hover:bg-teal-700 text-white font-medium text-xs transition"">
                                    ⟳ Mô phỏng xoay
                                </button>
                            </div>
                            <input id=""sliderAngle"" type=""range"" min=""0"" max=""360"" step=""1"" value=""360"" class=""w-full h-2 bg-slate-200 rounded-lg cursor-pointer"">
                        </div>

                        <!-- Cross-section Slice Height Control -->
                        <div class=""bg-white border border-slate-200 rounded-xl p-2.5 flex flex-col gap-1.5"">
                            <div class=""flex items-center justify-between text-xs"">
                                <span class=""font-semibold text-slate-700"">Mặt cắt ngang tại độ cao $y$: <strong id=""lblSliceY"" class=""text-rose-600"">1.35 cm</strong></span>
                                <button id=""btnPlaySlice"" class=""px-2.5 py-0.5 rounded bg-rose-600 hover:bg-rose-700 text-white font-medium text-xs transition"">
                                    ↕ Quét thiết diện
                                </button>
                            </div>
                            <input id=""sliderSliceY"" type=""range"" min=""0"" max=""2"" step=""0.01"" value=""1.35"" class=""w-full h-2 bg-slate-200 rounded-lg cursor-pointer"">
                        </div>
                    </div>

                    <!-- Live Mathematical Telemetry Bar -->
                    <div class=""grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs"">
                        <div class=""bg-white border border-slate-200 rounded-lg px-2.5 py-1.5"">
                            <div class=""text-slate-400 text-[11px]"">Miền chứa thiết diện</div>
                            <div id=""statZone"" class=""font-semibold text-slate-800"">Phần trên $y \in [1; 2]$</div>
                        </div>
                        <div class=""bg-white border border-slate-200 rounded-lg px-2.5 py-1.5"">
                            <div class=""text-slate-400 text-[11px]"">Bán kính quay $R(y)$</div>
                            <div id=""statRadius"" class=""font-semibold text-rose-600"">1.76 cm</div>
                        </div>
                        <div class=""bg-white border border-slate-200 rounded-lg px-2.5 py-1.5"">
                            <div class=""text-slate-400 text-[11px]"">Diện tích mặt cắt $S(y)=\pi R^2$</div>
                            <div id=""statArea"" class=""font-semibold text-indigo-700"">9.73 cm²</div>
                        </div>
                        <div class=""bg-teal-50 border border-teal-200 rounded-lg px-2.5 py-1.5"">
                            <div class=""text-teal-700 text-[11px] font-medium"">Tổng thể tích $V = V_1 + V_2$</div>
                            <div class=""font-bold text-teal-900"">$\frac{10\pi}{3} \approx 10{,}5\text{ cm}^3$</div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- RIGHT COLUMN: STEP-BY-STEP SOLUTIONS -->
            <div class=""lg:col-span-5 bg-white border border-slate-200 rounded-2xl shadow-sm flex flex-col overflow-hidden"">
                <!-- Step Navigation Header -->
                <div class=""bg-slate-50 border-b border-slate-200 p-3 flex flex-col gap-2.5"">
                    <div class=""flex items-center justify-between"">
                        <h2 class=""text-sm font-bold text-slate-800 flex items-center gap-2"">
                            <span class=""w-2.5 h-2.5 rounded-full bg-teal-600""></span>
                            Các Bước Giải Chi Tiết (Đồng bộ hình vẽ)
                        </h2>
                        <div class=""flex items-center gap-1"">
                            <button id=""prevStepBtn"" class=""px-2.5 py-1 rounded border border-slate-300 bg-white hover:bg-slate-100 text-xs font-medium text-slate-700 transition"">
                                ← Trước
                            </button>
                            <button id=""nextStepBtn"" class=""px-2.5 py-1 rounded bg-teal-600 hover:bg-teal-700 text-xs font-medium text-white transition"">
                                Tiếp theo →
                            </button>
                        </div>
                    </div>

                    <!-- Step Pills -->
                    <div class=""grid grid-cols-4 gap-1.5 text-xs font-semibold"">
                        <button data-step=""1"" class=""step-pill py-1.5 rounded-lg bg-teal-600 text-white shadow-sm transition"">
                            Bước 1
                        </button>
                        <button data-step=""2"" class=""step-pill py-1.5 rounded-lg bg-white border border-slate-200 text-slate-600 hover:bg-slate-100 transition"">
                            Bước 2
                        </button>
                        <button data-step=""3"" class=""step-pill py-1.5 rounded-lg bg-white border border-slate-200 text-slate-600 hover:bg-slate-100 transition"">
                            Bước 3
                        </button>
                        <button data-step=""4"" class=""step-pill py-1.5 rounded-lg bg-white border border-slate-200 text-slate-600 hover:bg-slate-100 transition"">
                            Bước 4
                        </button>
                    </div>
                </div>

                <!-- Step Content Cards Container -->
                <div id=""stepsContainer"" class=""p-3.5 space-y-3 max-h-[600px] overflow-y-auto"">
                    <!-- STEP 1 -->
                    <article data-step-card=""1"" class=""step-card active-step border-2 rounded-xl p-3.5 cursor-pointer"">
                        <div class=""flex items-center justify-between mb-1.5"">
                            <span class=""text-xs font-bold uppercase tracking-wider text-teal-700 bg-teal-100 px-2 py-0.5 rounded"">
                                Bước 1 • Phân tích tính chất hình vẽ
                            </span>
                            <span class=""text-xs text-slate-400"">Nhấn để minh họa</span>
                        </div>
                        <h3 class=""font-bold text-slate-800 text-sm mb-2"">
                            Xác định kích thước hình vuông $ABCD$ và các cung phần tư
                        </h3>
                        <div class=""text-xs sm:text-sm text-slate-700 space-y-2 leading-relaxed"">
                            <p>
                                Gọi $M, N$ lần lượt là trung điểm của các cạnh $BC, AD$ và $O$ là tâm của hình vuông $ABCD$ (cũng là trung điểm của $MN$).
                            </p>
                            <ul class=""list-disc pl-5 space-y-1"">
                                <li>
                                    Cung phần tư thứ nhất có tâm $M$, bán kính $R = 1\text{ cm}$ nối từ đỉnh $B$ đến tâm $O$, nên:
                                    $$MB = MO = 1\text{ cm} \implies BC = 2MB = 2\text{ cm}$$
                                </li>
                                <li>
                                    Cung phần tư thứ hai có tâm $N$, bán kính $R = 1\text{ cm}$ nối từ tâm $O$ đến đỉnh $D$, nên:
                                    $$NO = ND = 1\text{ cm} \implies AD = 2ND = 2\text{ cm}$$
                                </li>
                            </ul>
                            <p class=""bg-white/90 border border-teal-200 rounded-lg p-2 text-teal-900 font-medium"">
                                Vậy $ABCD$ là hình vuông cạnh bằng $2\text{ cm}$. Hai cung tròn $\overset{\frown}{BO}$ và $\overset{\frown}{OD}$ tiếp xúc với nhau tại tâm $O$.
                            </p>
                        </div>
                    </article>

                    <!-- STEP 2 -->
                    <article data-step-card=""2"" class=""step-card border-2 border-slate-200 rounded-xl p-3.5 cursor-pointer"">
                        <div class=""flex items-center justify-between mb-1.5"">
                            <span class=""text-xs font-bold uppercase tracking-wider text-indigo-700 bg-indigo-100 px-2 py-0.5 rounded"">
                                Bước 2 • Thiết lập hệ trục tọa độ
                            </span>
                            <span class=""text-xs text-slate-400"">Nhấn để minh họa</span>
                        </div>
                        <h3 class=""font-bold text-slate-800 text-sm mb-2"">
                            Viết phương trình các cung tròn giới hạn miền $(R)$
                        </h3>
                        <div class=""text-xs sm:text-sm text-slate-700 space-y-2 leading-relaxed"">
                            <p>
                                Chọn hệ trục tọa độ $Bxy$ sao cho gốc tọa độ tại $B(0;0)$, tia $Bx$ trùng với tia $BC$, tia $By$ trùng với tia $BA$ (trục quay $AB$ là trục $By$ với $y \in [0; 2]$).
                            </p>
                            <p>
                                Khi đó tọa độ: $B(0;0)$, $A(0;2)$, $M(1;0)$, $N(1;2)$, $O(1;1)$ và trung điểm $E(0;1)$ của $AB$.
                            </p>
                            <div class=""bg-slate-50 border border-slate-200 rounded-lg p-2.5 space-y-1.5"">
                                <p class=""font-semibold text-amber-800"">
                                    1. Trên đoạn $y \in [0; 1]$ (cung $\overset{\frown}{BO}$ tâm $M(1;0)$, $R=1$):
                                </p>
                                $$(x - 1)^2 + y^2 = 1 \implies x = g_1(y) = 1 - \sqrt{1 - y^2}$$
                                <p class=""font-semibold text-teal-800 pt-1"">
                                    2. Trên đoạn $y \in [1; 2]$ (cung $\overset{\frown}{OD}$ tâm $N(1;2)$, $R=1$):
                                </p>
                                $$(x - 1)^2 + (y - 2)^2 = 1 \implies x = g_2(y) = 1 + \sqrt{1 - (y - 2)^2}$$
                            </div>
                        </div>
                    </article>

                    <!-- STEP 3 -->
                    <article data-step-card=""3"" class=""step-card border-2 border-slate-200 rounded-xl p-3.5 cursor-pointer"">
                        <div class=""flex items-center justify-between mb-1.5"">
                            <span class=""text-xs font-bold uppercase tracking-wider text-rose-700 bg-rose-100 px-2 py-0.5 rounded"">
                                Bước 3 • Công thức thể tích khối tròn xoay
                            </span>
                            <span class=""text-xs text-slate-400"">Nhấn để minh họa</span>
                        </div>
                        <h3 class=""font-bold text-slate-800 text-sm mb-2"">
                            Thiết lập tích phân thể tích khi quay quanh trục $AB$
                        </h3>
                        <div class=""text-xs sm:text-sm text-slate-700 space-y-2 leading-relaxed"">
                            <p>
                                Thiết diện vuông góc trục $AB$ tại tung độ $y$ là hình tròn bán kính $R(y) = x$, diện tích $S(y) = \pi R^2(y)$.
                            </p>
                            $$V = V_1 + V_2 = \pi \int_{0}^{1} [g_1(y)]^2\,dy + \pi \int_{1}^{2} [g_2(y)]^2\,dy$$
                        </div>
                    </article>

                    <!-- STEP 4 -->
                    <article data-step-card=""4"" class=""step-card border-2 border-slate-200 rounded-xl p-3.5 cursor-pointer"">
                        <div class=""flex items-center justify-between mb-1.5"">
                            <span class=""text-xs font-bold uppercase tracking-wider text-emerald-700 bg-emerald-100 px-2 py-0.5 rounded"">
                                Bước 4 • Tính tích phân & Kết luận
                            </span>
                            <span class=""text-xs text-slate-400"">Nhấn để minh họa</span>
                        </div>
                        <h3 class=""font-bold text-slate-800 text-sm mb-2"">
                            Rút gọn đối xứng và làm tròn đến hàng phần mười
                        </h3>
                        <div class=""text-xs sm:text-sm text-slate-700 space-y-2 leading-relaxed"">
                            <p>
                                <strong>Rút gọn đối xứng:</strong> Ở $V_2$, đặt $t = 2 - y$. Lượng căn thức tự triệt tiêu:
                            </p>
                            $$V = 2\pi \int_{0}^{1} (2 - y^2)\,dy = 2\pi \left(2 - \frac{1}{3}\right) = \frac{10\pi}{3} \approx 10{,}47\text{ (cm}^3\text{)}$$
                            <div class=""bg-emerald-50 border border-emerald-300 rounded-lg p-2.5 text-emerald-950 font-bold text-center"">
                                Làm tròn đến hàng phần mười: $V \approx 10{,}5\text{ cm}^3$
                            </div>
                        </div>
                    </article>
                </div>
            </div>
        </div>
    </main>

    <script>
        const state = {
            currentStep: 1,
            viewMode: 'split',
            angleDeg: 360,
            sliceY: 1.35,
            showAxes: true,
            showConstruction: true,
            showSplitVol: true,
            isRotatingAnim: false,
            isSlicingAnim: false,
            sliceDirection: 1
        };

        function getRadiusAtY(y) {
            const clampedY = Math.max(0, Math.min(2, y));
            if (clampedY <= 1) {
                const inside = Math.max(0, 1 - clampedY * clampedY);
                return 1 - Math.sqrt(inside);
            } else {
                const dy = clampedY - 2;
                const inside = Math.max(0, 1 - dy * dy);
                return 1 + Math.sqrt(inside);
            }
        }

        function updateTelemetry() {
            const y = state.sliceY;
            const r = getRadiusAtY(y);
            const area = Math.PI * r * r;

            document.getElementById('lblAngle').textContent = `${Math.round(state.angleDeg)}°`;
            document.getElementById('lblSliceY').textContent = `${y.toFixed(2)} cm`;
            document.getElementById('statZone').textContent = y <= 1.0 ? 'Phần dưới V₁: y ∈ [0; 1]' : 'Phần trên V₂: y ∈ [1; 2]';
            document.getElementById('statRadius').textContent = `${r.toFixed(3)} cm`;
            document.getElementById('statArea').textContent = `${area.toFixed(3)} cm²`;
        }

        const canvas2D = document.getElementById('canvas2D');
        const ctx2D = canvas2D.getContext('2d');

        function draw2DFigure() {
            const rect = canvas2D.parentElement.getBoundingClientRect();
            if (rect.width === 0 || rect.height === 0) return;

            const dpr = window.devicePixelRatio || 1;
            canvas2D.width = Math.floor(rect.width * dpr);
            canvas2D.height = Math.floor(rect.height * dpr);

            ctx2D.save();
            ctx2D.scale(dpr, dpr);
            const W = rect.width;
            const H = rect.height;

            ctx2D.fillStyle = '#ffffff';
            ctx2D.fillRect(0, 0, W, H);

            const margin = 50;
            const availSize = Math.min(W - margin * 2, H - margin * 2);
            const unitPx = availSize / 2;
            const originX = (W - availSize) / 2;
            const originY = H - (H - availSize) / 2;

            const toPx = (x) => originX + x * unitPx;
            const toPy = (y) => originY - y * unitPx;

            function traceRegionPath() {
                ctx2D.beginPath();
                ctx2D.moveTo(toPx(0), toPy(0));
                ctx2D.lineTo(toPx(0), toPy(2));
                ctx2D.lineTo(toPx(2), toPy(2));
                ctx2D.arc(toPx(1), toPy(2), unitPx, 0, Math.PI / 2, false);
                ctx2D.arc(toPx(1), toPy(0), unitPx, -Math.PI / 2, -Math.PI, true);
                ctx2D.closePath();
            }

            if (state.showSplitVol) {
                ctx2D.save();
                traceRegionPath();
                ctx2D.clip();
                ctx2D.fillStyle = 'rgba(245, 158, 11, 0.15)';
                ctx2D.fillRect(toPx(0), toPy(1), unitPx * 2, unitPx);
                ctx2D.fillStyle = 'rgba(13, 148, 136, 0.15)';
                ctx2D.fillRect(toPx(0), toPy(2), unitPx * 2, unitPx);
                ctx2D.restore();
            }

            ctx2D.save();
            traceRegionPath();
            ctx2D.clip();
            ctx2D.strokeStyle = '#334155';
            ctx2D.lineWidth = 1.2;
            for (let d = -availSize; d <= availSize * 2; d += 8) {
                ctx2D.beginPath();
                ctx2D.moveTo(originX + d, originY);
                ctx2D.lineTo(originX + d + availSize, originY - availSize);
                ctx2D.stroke();
            }
            ctx2D.restore();

            ctx2D.strokeStyle = '#0f172a';
            ctx2D.lineWidth = 1.8;
            ctx2D.strokeRect(toPx(0), toPy(2), availSize, availSize);

            ctx2D.beginPath();
            ctx2D.arc(toPx(1), toPy(0), unitPx, -Math.PI, -Math.PI / 2, false);
            ctx2D.strokeStyle = state.showSplitVol ? '#d97706' : '#0f172a';
            ctx2D.lineWidth = 2.5;
            ctx2D.stroke();

            ctx2D.beginPath();
            ctx2D.arc(toPx(1), toPy(2), unitPx, 0, Math.PI / 2, false);
            ctx2D.strokeStyle = state.showSplitVol ? '#0d9488' : '#0f172a';
            ctx2D.lineWidth = 2.5;
            ctx2D.stroke();

            // Slice line
            const sy = state.sliceY;
            const sr = getRadiusAtY(sy);
            ctx2D.strokeStyle = '#e11d48';
            ctx2D.lineWidth = 2.8;
            ctx2D.beginPath();
            ctx2D.moveTo(toPx(0), toPy(sy));
            ctx2D.lineTo(toPx(sr), toPy(sy));
            ctx2D.stroke();

            // Labels
            ctx2D.font = 'italic bold 15px Georgia, serif';
            ctx2D.fillStyle = '#0f172a';
            ctx2D.fillText('A', toPx(0) - 20, toPy(2) - 6);
            ctx2D.fillText('D', toPx(2) + 6, toPy(2) - 6);
            ctx2D.fillText('B', toPx(0) - 20, toPy(0) + 16);
            ctx2D.fillText('C', toPx(2) + 6, toPy(0) + 16);

            ctx2D.restore();
        }

        // Three.js 3D Setup
        const container3D = document.getElementById('container3D');
        const scene = new THREE.Scene();
        scene.background = new THREE.Color(0x0f172a);

        const camera = new THREE.PerspectiveCamera(42, 1, 0.1, 100);
        const camSpherical = { radius: 5.4, theta: 0.65, phi: 1.18, target: new THREE.Vector3(0.25, 1.0, 0) };

        function updateCameraPosition() {
            const sinPhi = Math.sin(camSpherical.phi);
            camera.position.x = camSpherical.target.x + camSpherical.radius * sinPhi * Math.sin(camSpherical.theta);
            camera.position.y = camSpherical.target.y + camSpherical.radius * Math.cos(camSpherical.phi);
            camera.position.z = camSpherical.target.z + camSpherical.radius * sinPhi * Math.cos(camSpherical.theta);
            camera.lookAt(camSpherical.target);
        }
        updateCameraPosition();

        const renderer = new THREE.WebGLRenderer({ antialias: true });
        renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
        container3D.appendChild(renderer.domElement);

        scene.add(new THREE.AmbientLight(0xffffff, 0.7));
        const dirLight = new THREE.DirectionalLight(0xffffff, 0.8);
        dirLight.position.set(5, 8, 6);
        scene.add(dirLight);

        const gridHelper = new THREE.GridHelper(5, 10, 0x334155, 0x1e293b);
        scene.add(gridHelper);

        const axisMesh = new THREE.Mesh(new THREE.CylinderGeometry(0.02, 0.02, 2.9, 16), new THREE.MeshBasicMaterial({ color: 0x38bdf8 }));
        axisMesh.position.set(0, 1.05, 0);
        scene.add(axisMesh);

        const solidGroup = new THREE.Group();
        scene.add(solidGroup);

        function rebuild3DSolid() {
            while (solidGroup.children.length > 0) solidGroup.remove(solidGroup.children[0]);

            const angleRad = THREE.MathUtils.degToRad(state.angleDeg);
            const radialSegments = Math.max(8, Math.floor((state.angleDeg / 360) * 64));

            if (angleRad > 0.01) {
                const ptsV1 = [];
                for (let i = 0; i <= 30; i++) {
                    const y = (i / 30) * 1.0;
                    ptsV1.push(new THREE.Vector2(getRadiusAtY(y), y));
                }
                ptsV1.push(new THREE.Vector2(0, 1.0));
                const latheV1 = new THREE.Mesh(
                    new THREE.LatheGeometry(ptsV1, radialSegments, 0, angleRad),
                    new THREE.MeshStandardMaterial({ color: state.showSplitVol ? 0xf59e0b : 0x14b8a6, transparent: true, opacity: 0.85, side: THREE.DoubleSide })
                );
                solidGroup.add(latheV1);

                const ptsV2 = [new THREE.Vector2(0, 1.0)];
                for (let i = 0; i <= 30; i++) {
                    const y = 1.0 + (i / 30) * 1.0;
                    ptsV2.push(new THREE.Vector2(getRadiusAtY(y), y));
                }
                ptsV2.push(new THREE.Vector2(0, 2.0));
                const latheV2 = new THREE.Mesh(
                    new THREE.LatheGeometry(ptsV2, radialSegments, 0, angleRad),
                    new THREE.MeshStandardMaterial({ color: 0x0d9488, transparent: true, opacity: 0.85, side: THREE.DoubleSide })
                );
                solidGroup.add(latheV2);
            }

            const sy = state.sliceY;
            const sr = Math.max(0.01, getRadiusAtY(sy));
            const disk = new THREE.Mesh(
                new THREE.CylinderGeometry(sr, sr, 0.025, 40),
                new THREE.MeshBasicMaterial({ color: 0xf43f5e, transparent: true, opacity: 0.8 })
            );
            disk.position.set(0, sy, 0);
            solidGroup.add(disk);
        }

        // Camera Orbit Controls Drag
        let isDragging3D = false;
        let prevPointer = { x: 0, y: 0 };
        container3D.addEventListener('mousedown', (e) => { isDragging3D = true; prevPointer = { x: e.clientX, y: e.clientY }; });
        window.addEventListener('mouseup', () => { isDragging3D = false; });
        window.addEventListener('mousemove', (e) => {
            if (!isDragging3D) return;
            camSpherical.theta -= (e.clientX - prevPointer.x) * 0.008;
            camSpherical.phi = Math.max(0.2, Math.min(Math.PI - 0.2, camSpherical.phi - (e.clientY - prevPointer.y) * 0.008));
            prevPointer = { x: e.clientX, y: e.clientY };
            updateCameraPosition();
        });
        container3D.addEventListener('wheel', (e) => {
            e.preventDefault();
            camSpherical.radius = Math.max(2.5, Math.min(10, camSpherical.radius + e.deltaY * 0.003));
            updateCameraPosition();
        }, { passive: false });

        document.getElementById('resetCamBtn').addEventListener('click', () => {
            camSpherical.radius = 5.4; camSpherical.theta = 0.65; camSpherical.phi = 1.18; updateCameraPosition();
        });

        function resizeAll() {
            draw2DFigure();
            const rect = container3D.getBoundingClientRect();
            if (rect.width > 0 && rect.height > 0) {
                camera.aspect = rect.width / rect.height;
                camera.updateProjectionMatrix();
                renderer.setSize(rect.width, rect.height);
            }
        }
        window.addEventListener('resize', resizeAll);

        // View Mode Switcher
        document.querySelectorAll('.view-tab').forEach(btn => {
            btn.addEventListener('click', () => {
                const view = btn.getAttribute('data-view');
                document.querySelectorAll('.view-tab').forEach(b => b.className = 'view-tab px-3 py-1.5 rounded-md text-slate-600 hover:text-slate-900 transition');
                btn.className = 'view-tab px-3 py-1.5 rounded-md bg-white text-teal-700 shadow-sm transition';
                const p2 = document.getElementById('panel2D');
                const p3 = document.getElementById('panel3D');
                const g = document.getElementById('canvasGrid');
                if (view === 'split') {
                    g.className = 'grid grid-cols-1 md:grid-cols-2 divide-y md:divide-y-0 md:divide-x divide-slate-200 bg-white';
                    p2.classList.remove('hidden'); p3.classList.remove('hidden');
                } else if (view === '2d') {
                    g.className = 'grid grid-cols-1 bg-white';
                    p2.classList.remove('hidden'); p3.classList.add('hidden');
                } else {
                    g.className = 'grid grid-cols-1 bg-white';
                    p2.classList.add('hidden'); p3.classList.remove('hidden');
                }
                setTimeout(resizeAll, 30);
            });
        });

        // Sliders
        const sliderAngle = document.getElementById('sliderAngle');
        const sliderSliceY = document.getElementById('sliderSliceY');

        sliderAngle.addEventListener('input', (e) => {
            state.angleDeg = parseFloat(e.target.value);
            updateTelemetry();
            rebuild3DSolid();
        });
        sliderSliceY.addEventListener('input', (e) => {
            state.sliceY = parseFloat(e.target.value);
            updateTelemetry();
            draw2DFigure();
            rebuild3DSolid();
        });

        document.getElementById('btnPlayRotate').addEventListener('click', (e) => {
            state.isRotatingAnim = !state.isRotatingAnim;
            if (state.isRotatingAnim && state.angleDeg >= 360) state.angleDeg = 0;
            e.target.textContent = state.isRotatingAnim ? '⏸ Dừng xoay' : '⟳ Mô phỏng xoay';
        });

        document.getElementById('btnPlaySlice').addEventListener('click', (e) => {
            state.isSlicingAnim = !state.isSlicingAnim;
            e.target.textContent = state.isSlicingAnim ? '⏸ Dừng quét' : '↕ Quét thiết diện';
        });

        document.getElementById('chkAxes').addEventListener('change', (e) => { state.showAxes = e.target.checked; draw2DFigure(); });
        document.getElementById('chkConstruction').addEventListener('change', (e) => { state.showConstruction = e.target.checked; draw2DFigure(); });
        document.getElementById('chkSplitVol').addEventListener('change', (e) => { state.showSplitVol = e.target.checked; draw2DFigure(); rebuild3DSolid(); });

        // Step cards
        function setActiveStep(n) {
            state.currentStep = n;
            document.querySelectorAll('.step-pill').forEach(p => {
                p.className = (parseInt(p.getAttribute('data-step')) === n)
                    ? 'step-pill py-1.5 rounded-lg bg-teal-600 text-white shadow-sm transition'
                    : 'step-pill py-1.5 rounded-lg bg-white border border-slate-200 text-slate-600 hover:bg-slate-100 transition';
            });
            document.querySelectorAll('[data-step-card]').forEach(c => {
                c.classList.toggle('active-step', parseInt(c.getAttribute('data-step-card')) === n);
                c.classList.toggle('border-slate-200', parseInt(c.getAttribute('data-step-card')) !== n);
            });
        }
        document.querySelectorAll('.step-pill').forEach(p => p.addEventListener('click', () => setActiveStep(parseInt(p.getAttribute('data-step')))));
        document.querySelectorAll('[data-step-card]').forEach(c => c.addEventListener('click', () => setActiveStep(parseInt(c.getAttribute('data-step-card')))));

        function loop() {
            requestAnimationFrame(loop);
            let rebuild = false;
            if (state.isRotatingAnim) {
                state.angleDeg += 2.5;
                if (state.angleDeg >= 360) { state.angleDeg = 360; state.isRotatingAnim = false; }
                sliderAngle.value = state.angleDeg;
                rebuild = true;
            }
            if (state.isSlicingAnim) {
                state.sliceY += 0.012 * state.sliceDirection;
                if (state.sliceY >= 2.0) { state.sliceY = 2.0; state.sliceDirection = -1; }
                else if (state.sliceY <= 0.0) { state.sliceY = 0.0; state.sliceDirection = 1; }
                sliderSliceY.value = state.sliceY;
                draw2DFigure();
                rebuild = true;
            }
            if (rebuild) { updateTelemetry(); rebuild3DSolid(); }
            renderer.render(scene, camera);
        }

        window.onload = function() {
            if (typeof renderMathInElement === 'function') {
                renderMathInElement(document.body, {
                    delimiters: [{ left: '$$', right: '$$', display: true }, { left: '$', right: '$', display: false }],
                    throwOnError: false
                });
            }
            updateTelemetry();
            rebuild3DSolid();
            resizeAll();
            loop();
        };
    </script>
</body>
</html>"
            };
        }

        public static HtmlModelTemplateItem GetTemplateSphereSection()
        {
            return new HtmlModelTemplateItem
            {
                Id = "sphere_section_3d",
                Title = "Mặt cầu 3D & Mặt phẳng cắt thiết diện tròn (Tam giác vuông OHM)",
                Category = "Toán 12: Khối tròn xoay & Tích phân",
                Description = "Mặt cầu bán kính R, mặt phẳng cắt cách tâm khoảng cách d, thiết diện đường tròn bán kính r với hệ thức Pythagoras r² = R² - d².",
                HtmlCode = @"<!DOCTYPE html>
<html lang=""vi"">
<head>
    <meta charset=""UTF-8"">
    <meta name=""viewport"" content=""width=device-width, initial-scale=1.0"">
    <title>Mặt Cầu & Thiết Diện Phẳng 3D</title>
    <script src=""https://cdn.tailwindcss.com""></script>
    <link rel=""stylesheet"" href=""https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.css"">
    <script src=""https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.js""></script>
    <script src=""https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/contrib/auto-render.min.js""></script>
    <script src=""https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js""></script>
    <style>
        body { font-family: 'Inter', system-ui, sans-serif; background: #0f172a; color: #f8fafc; }
        input[type=""range""] { accent-color: #0284c7; }
    </style>
</head>
<body class=""min-h-screen flex flex-col p-4"">
    <header class=""flex items-center justify-between pb-3 border-b border-slate-700"">
        <div>
            <h1 class=""text-lg font-bold text-sky-400"">Mô Hình 3D: Mặt Cầu &amp; Thiết Diện Phẳng Cắt</h1>
            <p class=""text-xs text-slate-400"">Quan sát trực quan tương giao mặt phẳng $(\alpha)$ với mặt cầu $S(O; R)$</p>
        </div>
        <div class=""text-xs bg-slate-800 border border-slate-700 px-3 py-1.5 rounded-lg text-emerald-400 font-semibold"">
            Tam giác vuông $OHM: R^2 = d^2 + r^2$
        </div>
    </header>

    <div class=""flex-1 grid grid-cols-1 lg:grid-cols-12 gap-4 mt-3"">
        <div class=""lg:col-span-8 flex flex-col bg-slate-900 border border-slate-800 rounded-xl overflow-hidden"">
            <div id=""canvasContainer"" class=""relative flex-1 h-[420px] cursor-grab active:cursor-grabbing""></div>
            <div class=""p-3 bg-slate-800/80 border-t border-slate-700 flex flex-wrap items-center justify-between gap-3 text-xs"">
                <div class=""flex items-center gap-2"">
                    <span>Khoảng cách $d = OH$:</span>
                    <input id=""sliderD"" type=""range"" min=""0"" max=""2.45"" step=""0.05"" value=""1.2"" class=""w-36"">
                    <span id=""lblD"" class=""font-bold text-sky-400"">1.20</span>
                </div>
                <div class=""flex items-center gap-2"">
                    <span>Bán kính cầu $R = OM$:</span>
                    <input id=""sliderR"" type=""range"" min=""1.5"" max=""3.0"" step=""0.1"" value=""2.5"" class=""w-36"">
                    <span id=""lblR"" class=""font-bold text-indigo-400"">2.50</span>
                </div>
                <div class=""text-amber-400 font-bold"">
                    $r = \sqrt{R^2 - d^2} = $ <span id=""lblRadius"">2.19</span>
                </div>
            </div>
        </div>

        <div class=""lg:col-span-4 bg-slate-900 border border-slate-800 rounded-xl p-4 flex flex-col gap-3 text-xs text-slate-300"">
            <h2 class=""text-sm font-bold text-slate-100 flex items-center gap-2"">
                <span class=""w-2 h-2 rounded-full bg-sky-500""></span>
                Lý Thuyết &amp; Công Thức Hình Học
            </h2>
            <div class=""space-y-2 bg-slate-800/60 p-3 rounded-lg border border-slate-700/60 leading-relaxed"">
                <p>Mặt cầu $(S)$ tâm $O$, bán kính $R$. Khoảng cách $d = d(O, (\alpha))$:</p>
                <ul class=""list-disc pl-4 space-y-1 text-slate-300"">
                    <li>$d < R$: Mặt phẳng cắt mặt cầu theo đường tròn thiết diện tâm $H$, bán kính $r = \sqrt{R^2 - d^2}$.</li>
                    <li>$d = R$: Mặt phẳng tiếp xúc mặt cầu tại tiếp điểm $H$ ($r = 0$).</li>
                    <li>$d > R$: Mặt phẳng không cắt mặt cầu.</li>
                </ul>
            </div>
            <div class=""bg-slate-800/60 p-3 rounded-lg border border-slate-700/60 space-y-1.5"">
                <div class=""font-semibold text-sky-300"">Diện tích thiết diện:</div>
                <div id=""mathArea"" class=""font-mono text-emerald-400 text-sm"">$$S = \pi r^2 = \pi (R^2 - d^2)$$</div>
                <div class=""font-semibold text-amber-300 pt-1"">Chu vi đường tròn giao tuyến:</div>
                <div class=""font-mono text-amber-400 text-sm"">$$C = 2\pi r = 2\pi \sqrt{R^2 - d^2}$$</div>
            </div>
            <div class=""mt-auto bg-sky-950/60 border border-sky-800 p-2.5 rounded-lg text-sky-200"">
                💡 <em>Gợi ý thao tác:</em> Kéo chuột trái để xoay 360°, cuộn bánh xe để zoom phóng to/thu nhỏ, kéo slider để thay đổi khoảng cách mặt cắt.
            </div>
        </div>
    </div>

    <script>
        const container = document.getElementById('canvasContainer');
        const scene = new THREE.Scene();
        const camera = new THREE.PerspectiveCamera(45, container.clientWidth / container.clientHeight, 0.1, 100);
        camera.position.set(4, 3, 5);

        const renderer = new THREE.WebGLRenderer({ antialias: true });
        renderer.setSize(container.clientWidth, container.clientHeight);
        renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
        container.appendChild(renderer.domElement);

        scene.add(new THREE.AmbientLight(0xffffff, 0.6));
        const light = new THREE.DirectionalLight(0xffffff, 0.8);
        light.position.set(5, 10, 7);
        scene.add(light);

        let sphereMesh, planeMesh, diskMesh, triangleMesh;
        const group = new THREE.Group();
        scene.add(group);

        function updateScene() {
            while (group.children.length > 0) group.remove(group.children[0]);

            const R = parseFloat(document.getElementById('sliderR').value);
            const d = parseFloat(document.getElementById('sliderD').value);
            const r = (d <= R) ? Math.sqrt(R * R - d * d) : 0;

            document.getElementById('lblR').textContent = R.toFixed(2);
            document.getElementById('lblD').textContent = d.toFixed(2);
            document.getElementById('lblRadius').textContent = r.toFixed(2);

            // 1. Mặt cầu bán trong suốt
            const sphereGeo = new THREE.SphereGeometry(R, 36, 24);
            const sphereMat = new THREE.MeshStandardMaterial({
                color: 0x38bdf8,
                transparent: true,
                opacity: 0.35,
                roughness: 0.2,
                metalness: 0.1
            });
            sphereMesh = new THREE.Mesh(sphereGeo, sphereMat);
            group.add(sphereMesh);

            // Wireframe mặt cầu
            const wireMat = new THREE.MeshBasicMaterial({ color: 0x0284c7, wireframe: true, transparent: true, opacity: 0.15 });
            group.add(new THREE.Mesh(sphereGeo, wireMat));

            // 2. Mặt phẳng cắt (alpha)
            const planeGeo = new THREE.PlaneGeometry(R * 2.6, R * 2.6);
            const planeMat = new THREE.MeshStandardMaterial({ color: 0x64748b, transparent: true, opacity: 0.35, side: THREE.DoubleSide });
            planeMesh = new THREE.Mesh(planeGeo, planeMat);
            planeMesh.rotation.x = Math.PI / 2;
            planeMesh.position.y = d;
            group.add(planeMesh);

            // 3. Đĩa tròn thiết diện r
            if (r > 0.05) {
                const diskGeo = new THREE.CircleGeometry(r, 48);
                const diskMat = new THREE.MeshBasicMaterial({ color: 0xf59e0b, transparent: true, opacity: 0.75, side: THREE.DoubleSide });
                diskMesh = new THREE.Mesh(diskGeo, diskMat);
                diskMesh.rotation.x = Math.PI / 2;
                diskMesh.position.y = d;
                group.add(diskMesh);
            }

            // 4. Đoạn OH và OM
            const ptsOH = [new THREE.Vector3(0, 0, 0), new THREE.Vector3(0, d, 0)];
            group.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints(ptsOH), new THREE.LineBasicMaterial({ color: 0x38bdf8, linewidth: 2 })));

            const ptsOM = [new THREE.Vector3(0, 0, 0), new THREE.Vector3(r, d, 0)];
            group.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints(ptsOM), new THREE.LineBasicMaterial({ color: 0x818cf8, linewidth: 2 })));

            const ptsHM = [new THREE.Vector3(0, d, 0), new THREE.Vector3(r, d, 0)];
            group.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints(ptsHM), new THREE.LineBasicMaterial({ color: 0xf59e0b, linewidth: 2 })));
        }

        let isDown = false, px = 0, py = 0, theta = 0.6, phi = 1.0, rad = 7.0;
        function updateCam() {
            camera.position.x = rad * Math.sin(phi) * Math.sin(theta);
            camera.position.y = rad * Math.cos(phi);
            camera.position.z = rad * Math.sin(phi) * Math.cos(theta);
            camera.lookAt(0, 0.5, 0);
        }
        container.addEventListener('mousedown', (e) => { isDown = true; px = e.clientX; py = e.clientY; });
        window.addEventListener('mouseup', () => { isDown = false; });
        window.addEventListener('mousemove', (e) => {
            if (!isDown) return;
            theta -= (e.clientX - px) * 0.01;
            phi = Math.max(0.2, Math.min(Math.PI - 0.2, phi - (e.clientY - py) * 0.01));
            px = e.clientX; py = e.clientY;
            updateCam();
        });
        container.addEventListener('wheel', (e) => {
            e.preventDefault();
            rad = Math.max(3.5, Math.min(12, rad + e.deltaY * 0.005));
            updateCam();
        });

        document.getElementById('sliderD').addEventListener('input', updateScene);
        document.getElementById('sliderR').addEventListener('input', updateScene);

        window.addEventListener('resize', () => {
            camera.aspect = container.clientWidth / container.clientHeight;
            camera.updateProjectionMatrix();
            renderer.setSize(container.clientWidth, container.clientHeight);
        });

        function animate() {
            requestAnimationFrame(animate);
            renderer.render(scene, camera);
        }

        updateCam();
        updateScene();
        animate();
        renderMathInElement(document.body);
    </script>
</body>
</html>"
            };
        }

        public static HtmlModelTemplateItem GetTemplatePyramidSection()
        {
            return new HtmlModelTemplateItem
            {
                Id = "pyramid_section_3d",
                Title = "Hình chóp S.ABCD & Thiết diện mặt phẳng cắt tương tác",
                Category = "Toán học: Hình không gian & Thiết diện 3D",
                Description = "Mô phỏng hình chóp tứ giác đều S.ABCD bị cắt bởi mặt phẳng song song hoặc nghiêng, hiển thị đa giác thiết diện và thể tích phần bị cắt.",
                HtmlCode = @"<!DOCTYPE html>
<html lang=""vi"">
<head>
    <meta charset=""UTF-8"">
    <title>Hình Chóp S.ABCD & Thiết Diện Cắt 3D</title>
    <script src=""https://cdn.tailwindcss.com""></script>
    <script src=""https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js""></script>
    <style>body { margin: 0; background: #0f172a; color: white; font-family: sans-serif; }</style>
</head>
<body class=""flex flex-col h-screen"">
    <div class=""p-3 bg-slate-800 border-b border-slate-700 flex justify-between items-center"">
        <h1 class=""font-bold text-teal-400"">Hình Chóp Tứ Giác S.ABCD &amp; Thiết Diện Mặt Phẳng</h1>
        <div class=""text-xs text-slate-300"">Xoay 3D bằng chuột | Kéo slider để nâng hạ mặt phẳng cắt</div>
    </div>
    <div id=""canvas3D"" class=""flex-1""></div>
    <div class=""p-3 bg-slate-800/90 border-t border-slate-700 flex gap-4 text-xs items-center justify-center"">
        <span>Độ cao mặt phẳng cắt $z$:</span>
        <input id=""sliderZ"" type=""range"" min=""0.2"" max=""2.8"" step=""0.05"" value=""1.5"" class=""w-48 accent-teal-500"">
        <span id=""valZ"" class=""font-bold text-teal-400"">1.50</span>
    </div>
    <script>
        const container = document.getElementById('canvas3D');
        const scene = new THREE.Scene();
        const camera = new THREE.PerspectiveCamera(45, container.clientWidth / container.clientHeight, 0.1, 100);
        camera.position.set(5, 4, 6);
        camera.lookAt(0, 1.2, 0);

        const renderer = new THREE.WebGLRenderer({ antialias: true });
        renderer.setSize(container.clientWidth, container.clientHeight);
        container.appendChild(renderer.domElement);

        scene.add(new THREE.AmbientLight(0xffffff, 0.6));
        const dirLight = new THREE.DirectionalLight(0xffffff, 0.8);
        dirLight.position.set(6, 10, 8);
        scene.add(dirLight);

        const group = new THREE.Group();
        scene.add(group);

        // Đỉnh S(0, 3, 0), Đáy A(-1.5, 0, -1.5), B(1.5, 0, -1.5), C(1.5, 0, 1.5), D(-1.5, 0, 1.5)
        function renderScene() {
            while (group.children.length > 0) group.remove(group.children[0]);

            const zCut = parseFloat(document.getElementById('sliderZ').value);
            document.getElementById('valZ').textContent = zCut.toFixed(2);

            // Dựng khung hình chóp
            const S = new THREE.Vector3(0, 3, 0);
            const A = new THREE.Vector3(-1.5, 0, -1.5);
            const B = new THREE.Vector3(1.5, 0, -1.5);
            const C = new THREE.Vector3(1.5, 0, 1.5);
            const D = new THREE.Vector3(-1.5, 0, 1.5);

            const edges = [
                [A, B], [B, C], [C, D], [D, A],
                [S, A], [S, B], [S, C], [S, D]
            ];
            edges.forEach(e => {
                const geo = new THREE.BufferGeometry().setFromPoints(e);
                group.add(new THREE.Line(geo, new THREE.LineBasicMaterial({ color: 0x38bdf8, linewidth: 2 })));
            });

            // Mặt phẳng cắt tại cao độ zCut (tỉ số k = 1 - zCut/3)
            const k = (3 - zCut) / 3;
            if (k > 0.05 && k < 0.98) {
                const A1 = new THREE.Vector3(A.x * k, zCut, A.z * k);
                const B1 = new THREE.Vector3(B.x * k, zCut, B.z * k);
                const C1 = new THREE.Vector3(C.x * k, zCut, C.z * k);
                const D1 = new THREE.Vector3(D.x * k, zCut, D.z * k);

                const shape = new THREE.Shape();
                shape.moveTo(A1.x, A1.z);
                shape.lineTo(B1.x, B1.z);
                shape.lineTo(C1.x, C1.z);
                shape.lineTo(D1.x, D1.z);
                shape.closePath();

                const polyGeo = new THREE.ShapeGeometry(shape);
                const polyMat = new THREE.MeshBasicMaterial({ color: 0xf59e0b, transparent: true, opacity: 0.75, side: THREE.DoubleSide });
                const polyMesh = new THREE.Mesh(polyGeo, polyMat);
                polyMesh.rotation.x = Math.PI / 2;
                polyMesh.position.y = zCut;
                group.add(polyMesh);

                // Đường viền thiết diện
                const borderPts = [A1, B1, C1, D1, A1];
                group.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints(borderPts), new THREE.LineBasicMaterial({ color: 0xffffff, linewidth: 3 })));
            }
        }

        document.getElementById('sliderZ').addEventListener('input', renderScene);
        renderScene();

        // Xoay chuột
        let isDown = false, px = 0, py = 0, rotY = 0.5, rotX = 0.4;
        container.addEventListener('mousedown', e => { isDown = true; px = e.clientX; py = e.clientY; });
        window.addEventListener('mouseup', () => isDown = false);
        window.addEventListener('mousemove', e => {
            if (!isDown) return;
            rotY += (e.clientX - px) * 0.01;
            rotX = Math.max(0.1, Math.min(1.4, rotX + (e.clientY - py) * 0.01));
            px = e.clientX; py = e.clientY;
            camera.position.x = 8 * Math.sin(rotY) * Math.cos(rotX);
            camera.position.z = 8 * Math.cos(rotY) * Math.cos(rotX);
            camera.position.y = 8 * Math.sin(rotX);
            camera.lookAt(0, 1.2, 0);
        });

        function animate() {
            requestAnimationFrame(animate);
            renderer.render(scene, camera);
        }
        animate();
    </script>
</body>
</html>"
            };
        }

        public static HtmlModelTemplateItem GetTemplateOxyzVectors()
        {
            return new HtmlModelTemplateItem
            {
                Id = "cartesian_oxyz_3d",
                Title = "Hệ tọa độ Oxyz 3D - Điểm, Vector & Mặt phẳng",
                Category = "Toán học: Tọa độ không gian Oxyz",
                Description = "Trực quan hóa hệ trục Oxyz trong không gian 3 chiều, biểu diễn vector, tích có hướng của 2 vector và phương trình mặt phẳng Ax + By + Cz + D = 0.",
                HtmlCode = @"<!DOCTYPE html>
<html lang=""vi"">
<head>
    <meta charset=""UTF-8"">
    <title>Hệ Trục Tọa Độ Oxyz 3D</title>
    <script src=""https://cdn.tailwindcss.com""></script>
    <script src=""https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js""></script>
    <style>body { margin: 0; background: #0f172a; color: white; }</style>
</head>
<body class=""flex flex-col h-screen"">
    <div class=""p-3 bg-slate-900 border-b border-slate-800 flex justify-between items-center text-xs"">
        <h1 class=""font-bold text-sky-400 text-sm"">Hệ Tọa Độ Không Gian Oxyz 3D</h1>
        <div class=""flex gap-4 font-mono"">
            <span class=""text-rose-400"">Trục Ox (Đỏ)</span>
            <span class=""text-emerald-400"">Trục Oy (Xanh lá)</span>
            <span class=""text-sky-400"">Trục Oz (Xanh dương)</span>
        </div>
    </div>
    <div id=""canvasOxyz"" class=""flex-1""></div>
    <script>
        const c = document.getElementById('canvasOxyz');
        const scene = new THREE.Scene();
        const camera = new THREE.PerspectiveCamera(45, c.clientWidth / c.clientHeight, 0.1, 100);
        camera.position.set(6, 5, 8);
        camera.lookAt(0, 0, 0);

        const renderer = new THREE.WebGLRenderer({ antialias: true });
        renderer.setSize(c.clientWidth, c.clientHeight);
        c.appendChild(renderer.domElement);

        scene.add(new THREE.GridHelper(10, 10, 0x334155, 0x1e293b));
        scene.add(new THREE.AxesHelper(4)); // X: red, Y: green, Z: blue

        // Vector u(2, 3, 2)
        const dir = new THREE.Vector3(2, 3, 2).normalize();
        const origin = new THREE.Vector3(0, 0, 0);
        const arrow = new THREE.ArrowHelper(dir, origin, Math.sqrt(17), 0xf59e0b, 0.4, 0.2);
        scene.add(arrow);

        function animate() {
            requestAnimationFrame(animate);
            renderer.render(scene, camera);
        }
        animate();
    </script>
</body>
</html>"
            };
        }

        public static HtmlModelTemplateItem GetTemplateSurfaceCalculus()
        {
            return new HtmlModelTemplateItem
            {
                Id = "surface_calc_3d",
                Title = "Khảo sát hàm 2 biến & Mặt cong Paraboloid 3D (z = x² + y²)",
                Category = "Toán học: Đồ thị hàm số & Mặt cong 3D",
                Description = "Đồ thị 3 chiều của mặt cong bậc hai Paraboloid eliptic, tô màu theo độ cao z, hỗ trợ khảo sát cực trị và mặt phẳng tiếp diện.",
                HtmlCode = @"<!DOCTYPE html>
<html lang=""vi"">
<head>
    <meta charset=""UTF-8"">
    <title>Mặt Cong Paraboloid 3D: z = x² + y²</title>
    <script src=""https://cdn.tailwindcss.com""></script>
    <script src=""https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js""></script>
</head>
<body class=""bg-slate-900 text-white flex flex-col h-screen"">
    <div class=""p-3 bg-slate-800 border-b border-slate-700 flex justify-between items-center text-xs"">
        <h1 class=""font-bold text-teal-400 text-sm"">Mặt Cong Paraboloid: $z = x^2 + y^2$</h1>
        <div class=""text-slate-400"">Cực tiểu toàn cục tại gốc tọa độ $(0, 0, 0)$</div>
    </div>
    <div id=""canvasSurface"" class=""flex-1""></div>
    <script>
        const container = document.getElementById('canvasSurface');
        const scene = new THREE.Scene();
        const camera = new THREE.PerspectiveCamera(45, container.clientWidth / container.clientHeight, 0.1, 100);
        camera.position.set(4, 5, 6);
        camera.lookAt(0, 1.5, 0);

        const renderer = new THREE.WebGLRenderer({ antialias: true });
        renderer.setSize(container.clientWidth, container.clientHeight);
        container.appendChild(renderer.domElement);

        scene.add(new THREE.AmbientLight(0xffffff, 0.6));
        const light = new THREE.DirectionalLight(0xffffff, 0.8);
        light.position.set(5, 8, 5);
        scene.add(light);

        // Tạo lưới mặt cong Paraboloid
        const size = 30, range = 2;
        const geo = new THREE.PlaneGeometry(range * 2, range * 2, size, size);
        const pos = geo.attributes.position;
        for (let i = 0; i < pos.count; i++) {
            const x = pos.getX(i);
            const y = pos.getY(i);
            pos.setZ(i, (x * x + y * y) * 0.7);
        }
        geo.computeVertexNormals();

        const mat = new THREE.MeshStandardMaterial({ color: 0x06b6d4, wireframe: false, side: THREE.DoubleSide });
        const mesh = new THREE.Mesh(geo, mat);
        mesh.rotation.x = -Math.PI / 2;
        scene.add(mesh);

        const wire = new THREE.Mesh(geo, new THREE.MeshBasicMaterial({ color: 0xffffff, wireframe: true, transparent: true, opacity: 0.15 }));
        wire.rotation.x = -Math.PI / 2;
        scene.add(wire);

        function animate() {
            requestAnimationFrame(animate);
            mesh.rotation.z += 0.005;
            wire.rotation.z += 0.005;
            renderer.render(scene, camera);
        }
        animate();
    </script>
</body>
</html>"
            };
        }

        public static HtmlModelTemplateItem GetTemplatePhysicsPendulum()
        {
            return new HtmlModelTemplateItem
            {
                Id = "physics_pendulum_3d",
                Title = "Vật lý 12: Con lắc đơn & Dao động điều hòa 3D",
                Category = "Vật lý: Dao động điều hòa & Sóng cơ",
                Description = "Mô phỏng 3D con lắc đơn dao động điều hòa tự do, đồ thị li độ - thời gian song song thời gian thực, tính chu kỳ T = 2π√(l/g).",
                HtmlCode = @"<!DOCTYPE html>
<html lang=""vi"">
<head>
    <meta charset=""UTF-8"">
    <title>Mô Phỏng Vật Lý: Con Lắc Đơn Dao Động Điều Hòa 3D</title>
    <script src=""https://cdn.tailwindcss.com""></script>
    <script src=""https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js""></script>
</head>
<body class=""bg-slate-950 text-white flex flex-col h-screen"">
    <div class=""p-3 bg-slate-900 border-b border-slate-800 flex justify-between items-center text-xs"">
        <h1 class=""font-bold text-amber-400 text-sm"">Vật Lý 12: Con Lắc Đơn Dao Động Điều Hòa 3D</h1>
        <div class=""font-mono text-emerald-400"">Chu kỳ $T = 2\pi\sqrt{\frac{l}{g}} \approx 2{,}00\text{ s}$</div>
    </div>
    <div id=""canvasPendulum"" class=""flex-1""></div>
    <script>
        const c = document.getElementById('canvasPendulum');
        const scene = new THREE.Scene();
        const camera = new THREE.PerspectiveCamera(45, c.clientWidth / c.clientHeight, 0.1, 100);
        camera.position.set(0, 0, 5);

        const renderer = new THREE.WebGLRenderer({ antialias: true });
        renderer.setSize(c.clientWidth, c.clientHeight);
        c.appendChild(renderer.domElement);

        scene.add(new THREE.AmbientLight(0xffffff, 0.8));

        // Thanh treo
        const pivot = new THREE.Group();
        pivot.position.set(0, 1.8, 0);
        scene.add(pivot);

        // Dây treo
        const lineGeo = new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(0, 0, 0), new THREE.Vector3(0, -2.5, 0)]);
        const line = new THREE.Line(lineGeo, new THREE.LineBasicMaterial({ color: 0x94a3b8, linewidth: 2 }));
        pivot.add(line);

        // Quả nặng
        const bob = new THREE.Mesh(new THREE.SphereGeometry(0.22, 32, 32), new THREE.MeshStandardMaterial({ color: 0xf59e0b, metalness: 0.8, roughness: 0.2 }));
        bob.position.set(0, -2.5, 0);
        pivot.add(bob);

        let t = 0;
        const maxAngle = 0.35; // rad (~20 độ)
        function animate() {
            requestAnimationFrame(animate);
            t += 0.035;
            pivot.rotation.z = maxAngle * Math.cos(t * Math.PI);
            renderer.render(scene, camera);
        }
        animate();
    </script>
</body>
</html>"
            };
        }

        public static HtmlModelTemplateItem GetTemplateChemistryMolecule()
        {
            return new HtmlModelTemplateItem
            {
                Id = "chemistry_molecule_3d",
                Title = "Hóa học: Cấu trúc phân tử 3D (Methane CH₄ / Nước H₂O)",
                Category = "Hóa học: Cấu trúc phân tử 3D",
                Description = "Mô hình quả cầu que nối 3D (Ball-and-stick) cấu trúc phân tử Metan CH4 dạng tứ diện đều góc 109.5°, xoay 3D 360 độ tự do.",
                HtmlCode = @"<!DOCTYPE html>
<html lang=""vi"">
<head>
    <meta charset=""UTF-8"">
    <title>Cấu Trúc Phân Tử 3D: Methane (CH₄)</title>
    <script src=""https://cdn.tailwindcss.com""></script>
    <script src=""https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js""></script>
</head>
<body class=""bg-slate-900 text-white flex flex-col h-screen"">
    <div class=""p-3 bg-slate-800 border-b border-slate-700 flex justify-between items-center text-xs"">
        <h1 class=""font-bold text-sky-400 text-sm"">Hóa Học: Cấu Trúc Phân Tử Methane ($CH_4$) Dạng Tứ Diện Đều</h1>
        <div class=""text-slate-400"">Góc liên kết H-C-H = 109.5° | Carbon (Xám), Hydro (Trắng)</div>
    </div>
    <div id=""canvasMol"" class=""flex-1""></div>
    <script>
        const c = document.getElementById('canvasMol');
        const scene = new THREE.Scene();
        const camera = new THREE.PerspectiveCamera(45, c.clientWidth / c.clientHeight, 0.1, 100);
        camera.position.set(0, 0, 6);

        const renderer = new THREE.WebGLRenderer({ antialias: true });
        renderer.setSize(c.clientWidth, c.clientHeight);
        c.appendChild(renderer.domElement);

        scene.add(new THREE.AmbientLight(0xffffff, 0.7));
        const light = new THREE.DirectionalLight(0xffffff, 0.8);
        light.position.set(5, 5, 5);
        scene.add(light);

        const molGroup = new THREE.Group();
        scene.add(molGroup);

        // Nguyên tử Carbon trung tâm (đen/xám)
        const cAtom = new THREE.Mesh(new THREE.SphereGeometry(0.45, 32, 32), new THREE.MeshStandardMaterial({ color: 0x334155, roughness: 0.3 }));
        molGroup.add(cAtom);

        // 4 Nguyên tử Hydrogen tại 4 đỉnh tứ diện đều
        const hCoords = [
            new THREE.Vector3(1, 1, 1).normalize().multiplyScalar(1.5),
            new THREE.Vector3(-1, -1, 1).normalize().multiplyScalar(1.5),
            new THREE.Vector3(-1, 1, -1).normalize().multiplyScalar(1.5),
            new THREE.Vector3(1, -1, -1).normalize().multiplyScalar(1.5)
        ];

        hCoords.forEach(pos => {
            const hAtom = new THREE.Mesh(new THREE.SphereGeometry(0.25, 24, 24), new THREE.MeshStandardMaterial({ color: 0xf8fafc, roughness: 0.3 }));
            hAtom.position.copy(pos);
            molGroup.add(hAtom);

            // Liên kết C-H (Cylinder)
            const bondGeo = new THREE.CylinderGeometry(0.06, 0.06, pos.length(), 16);
            const bondMat = new THREE.MeshStandardMaterial({ color: 0x94a3b8 });
            const bond = new THREE.Mesh(bondGeo, bondMat);
            bond.position.copy(pos.clone().multiplyScalar(0.5));
            bond.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), pos.clone().normalize());
            molGroup.add(bond);
        });

        function animate() {
            requestAnimationFrame(animate);
            molGroup.rotation.y += 0.008;
            molGroup.rotation.x += 0.004;
            renderer.render(scene, camera);
        }
        animate();
    </script>
</body>
</html>"
            };
        }

        public static HtmlModelTemplateItem GetTemplateBiologyDna()
        {
            return new HtmlModelTemplateItem
            {
                Id = "biology_dna_helix_3d",
                Title = "Sinh học: Cấu trúc Xoắn kép ADN 3D tương tác",
                Category = "Sinh học: Cấu trúc ADN & Tế bào",
                Description = "Mô hình xoắn kép phân tử ADN trong không gian 3D, các cặp bazơ nitơ bổ sung Adenin - Timin và Guanin - Xitôzin kết nối bằng liên kết hydro.",
                HtmlCode = @"<!DOCTYPE html>
<html lang=""vi"">
<head>
    <meta charset=""UTF-8"">
    <title>Cấu Trúc Xoắn Kép ADN 3D</title>
    <script src=""https://cdn.tailwindcss.com""></script>
    <script src=""https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js""></script>
</head>
<body class=""bg-slate-950 text-white flex flex-col h-screen"">
    <div class=""p-3 bg-slate-900 border-b border-slate-800 flex justify-between items-center text-xs"">
        <h1 class=""font-bold text-teal-400 text-sm"">Sinh Học: Cấu Trúc Xoắn Kép Phân Tử ADN 3D</h1>
        <div class=""text-slate-400"">Cặp bazơ nitơ bổ sung: A - T (Đỏ - Vàng), G - X (Xanh lục - Xanh dương)</div>
    </div>
    <div id=""canvasDna"" class=""flex-1""></div>
    <script>
        const c = document.getElementById('canvasDna');
        const scene = new THREE.Scene();
        const camera = new THREE.PerspectiveCamera(45, c.clientWidth / c.clientHeight, 0.1, 100);
        camera.position.set(0, 0, 8);

        const renderer = new THREE.WebGLRenderer({ antialias: true });
        renderer.setSize(c.clientWidth, c.clientHeight);
        c.appendChild(renderer.domElement);

        scene.add(new THREE.AmbientLight(0xffffff, 0.7));
        const light = new THREE.DirectionalLight(0xffffff, 0.8);
        light.position.set(5, 5, 5);
        scene.add(light);

        const dnaGroup = new THREE.Group();
        scene.add(dnaGroup);

        const steps = 30, radius = 1.2, height = 5.0;
        const colors = [0xef4444, 0xf59e0b, 0x10b981, 0x06b6d4];

        for (let i = 0; i < steps; i++) {
            const angle = (i / 10) * Math.PI * 2;
            const y = (i / steps) * height - height / 2;

            const p1 = new THREE.Vector3(Math.cos(angle) * radius, y, Math.sin(angle) * radius);
            const p2 = new THREE.Vector3(-Math.cos(angle) * radius, y, -Math.sin(angle) * radius);

            // 2 hạt đường - photphat
            const s1 = new THREE.Mesh(new THREE.SphereGeometry(0.12, 16, 16), new THREE.MeshStandardMaterial({ color: 0x38bdf8 }));
            s1.position.copy(p1);
            dnaGroup.add(s1);

            const s2 = new THREE.Mesh(new THREE.SphereGeometry(0.12, 16, 16), new THREE.MeshStandardMaterial({ color: 0x38bdf8 }));
            s2.position.copy(p2);
            dnaGroup.add(s2);

            // Bậc thang bazơ nitơ
            const color = colors[i % colors.length];
            const bondGeo = new THREE.CylinderGeometry(0.04, 0.04, radius * 2, 8);
            const bond = new THREE.Mesh(bondGeo, new THREE.MeshStandardMaterial({ color: color }));
            bond.position.set(0, y, 0);
            bond.rotation.z = Math.PI / 2;
            bond.rotation.y = -angle;
            dnaGroup.add(bond);
        }

        function animate() {
            requestAnimationFrame(animate);
            dnaGroup.rotation.y += 0.01;
            renderer.render(scene, camera);
        }
        animate();
    </script>
</body>
</html>"
            };
        }

        public static HtmlModelTemplateItem GetTemplateSierpinski232()
        {
            return new HtmlModelTemplateItem
            {
                Id = "sierpinski_sgk11_232",
                Title = "Toán 11: Phân dạng Sierpinski & Cấp số nhân (Bài 2.32 SGK)",
                Category = "Toán 11: Cấp số nhân & Phân dạng Sierpinski",
                Description = "Mô phỏng đệ quy Canvas 2D thảm Sierpinski phân rã cấp số nhân u_n và tổng S_n, hiệu ứng KaTeX hover zoom 2x, nút ẩn/hiện đáp số ??? kích thích học sinh tự tính và chế độ trình chiếu toàn màn hình.",
                HtmlCode = @"<!DOCTYPE html>

<html lang=""vi"">

<head>

    <meta charset=""UTF-8"">

    <meta name=""viewport"" content=""width=device-width, initial-scale=1.0"">

    <title>Mô Phỏng & Hướng Dẫn Từng Bước - Bài Toán 2.32 (SGK Toán 11)</title>



    <!-- Tailwind CSS -->

    <script src=""https://cdn.tailwindcss.com""></script>

    <script>

        tailwind.config = {

            theme: {

                extend: {

                    colors: {

                        tbYellow: '#fed7aa',

                        tbYellowDark: '#f59e0b',

                        tbBlue: '#0ea5e9',

                        tbBlueDark: '#0284c7'

                    }

                }

            }

        };

    </script>



    <!-- KaTeX -->

    <link rel=""stylesheet"" href=""https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.css"">

    <script src=""https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.js""></script>

    <script src=""https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/contrib/auto-render.min.js""></script>



    <!-- Font Awesome -->

    <link rel=""stylesheet"" href=""https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css"">

    <!-- Three.js -->

    <script src=""https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js""></script>



    <!-- Fonts -->

    <link rel=""preconnect"" href=""https://fonts.googleapis.com"">

    <link rel=""preconnect"" href=""https://fonts.gstatic.com"">

    <link href=""https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Fira+Code:wght@500;600;700&display=swap"" rel=""stylesheet"">



    <style>

        body {

            font-family: 'Inter', system-ui, -apple-system, sans-serif;

        }

        /* Hiệu ứng rê chuột phóng to công thức KaTeX cực đại (~3x) */

        .katex {

            font-size: 1.05em;

            line-height: 1.2;

            transition: transform 0.16s cubic-bezier(0.16, 1, 0.3, 1), box-shadow 0.16s ease, background-color 0.16s ease;

            transform-origin: center center;

            cursor: zoom-in;

        }

        .katex:hover {

            display: inline-block;

            transform: scale(2.0);

            position: relative;

            z-index: 100;

            background: #ffffff;

            padding: 3px 8px;

            border-radius: 8px;

            border: 1.5px solid #38bdf8;

            box-shadow: 0 16px 36px -4px rgba(14, 165, 233, 0.45), 0 6px 16px -2px rgba(0, 0, 0, 0.2);

        }

        .katex-display {

            transition: transform 0.2s cubic-bezier(0.16, 1, 0.3, 1);

            transform-origin: center center;

            cursor: zoom-in;

        }

        .katex-display:hover {

            transform: scale(1.8);

            position: relative;

            z-index: 100;

            background: #ffffff;

            padding: 10px 16px;

            border-radius: 12px;

            border: 2px solid #38bdf8;

            box-shadow: 0 20px 45px -6px rgba(14, 165, 233, 0.5), 0 8px 20px -3px rgba(0, 0, 0, 0.25);

        }

        .table-math .katex {

            font-size: 1.15em;

        }

        .table-math .katex:hover {

            transform: scale(2.0);

            background: #ffffff;

            border: 1.5px solid #38bdf8;

            box-shadow: 0 16px 36px -4px rgba(14, 165, 233, 0.45);

        }

        .custom-scroll::-webkit-scrollbar {

            width: 6px;

            height: 6px;

        }

        .custom-scroll::-webkit-scrollbar-track {

            background: #f1f5f9;

            border-radius: 4px;

        }

        .custom-scroll::-webkit-scrollbar-thumb {

            background: #cbd5e1;

            border-radius: 4px;

        }

        .custom-scroll::-webkit-scrollbar-thumb:hover {

            background: #94a3b8;

        }

    </style>

</head>

<body class=""h-screen flex flex-col bg-slate-100 text-slate-800 antialiased text-sm overflow-hidden select-none"">



    <!-- 1. HEADER CHÍNH -->

    <header class=""bg-white border-b border-slate-200 px-3 sm:px-4 py-2 shrink-0 z-20 flex items-center justify-between shadow-xs"">

        <div class=""flex items-center gap-2.5"">

            <div class=""w-8 h-8 rounded-lg bg-sky-600 text-white flex items-center justify-center font-bold text-sm shadow-xs"">

                <i class=""fa-solid fa-shapes""></i>

            </div>

            <div>

                <h1 class=""text-sm sm:text-base font-bold text-slate-900 leading-tight"">

                    Mô Phỏng Phân Dạng Sierpinski & Cấp Số Nhân

                </h1>

                <p class=""text-[11px] text-slate-500 hidden sm:block"">

                    Toán 11 • Bài 2.32 (SGK Kết nối tri thức) • Hướng dẫn giải gợi mở từng bước

                </p>

            </div>

        </div>



        <div class=""flex items-center gap-2"">

            <!-- Nút bật/tắt thanh đề bài tinh gọn -->

            <button onclick=""toggleProblemBanner()"" id=""btnToggleProblem"" class=""px-2.5 py-1.5 rounded-lg border border-sky-300 bg-sky-50 hover:bg-sky-100 text-sky-800 text-xs font-bold flex items-center gap-1.5 transition shadow-2xs"">

                <i class=""fa-solid fa-book-open text-sky-600""></i>

                <span id=""textToggleProblem"">Thu gọn đề bài</span>

            </button>



            <!-- Nút Trình chiếu toàn màn hình chuyên dụng (chỉ xem hình & nút chuyển đổi) -->

            <button onclick=""openPresentationMode()"" class=""px-3 py-1.5 rounded-lg bg-gradient-to-r from-sky-600 to-indigo-600 hover:from-sky-700 hover:to-indigo-700 text-white font-bold text-xs flex items-center gap-1.5 transition shadow-xs"">

                <i class=""fa-solid fa-expand text-xs""></i>

                <span class=""hidden sm:inline"">Trình chiếu</span> toàn màn hình

            </button>



            <!-- Gợi ý phím tắt -->

            <div class=""hidden lg:flex items-center gap-1 text-[11px] text-slate-500 bg-slate-100 px-2 py-1 rounded-md border border-slate-200 font-mono"">

                <span>Phím:</span>

                <kbd class=""px-1 py-0.5 bg-white rounded border border-slate-300 font-bold"">←</kbd>

                <kbd class=""px-1 py-0.5 bg-white rounded border border-slate-300 font-bold"">→</kbd>

            </div>

        </div>

    </header>



    <!-- 2. THANH ĐỀ BÀI THIẾT KẾ MỚI: RÕ RÀNG, ĐẸP MẮT, KHÔNG CHE KHUẤT (CÓ THỂ THU GỌN) -->

    <section id=""problemBannerSection"" class=""bg-gradient-to-r from-amber-50/90 via-sky-50/50 to-slate-50 border-b border-slate-200 px-3 sm:px-4 py-2.5 shrink-0 transition-all duration-300 shadow-2xs"">

        <div class=""max-w-7xl mx-auto space-y-1.5"">

            <div class=""flex items-center gap-2 flex-wrap"">

                    <span class=""px-2 py-0.5 rounded-md bg-amber-500 text-white font-bold text-xs shadow-2xs"">

                        Đề bài 2.32 SGK

                    </span>

                    <span class=""text-xs font-bold text-slate-800"">Toán 11 • Kết nối tri thức với cuộc sống (Hình 2.1)</span>

                </div>

                <p class=""text-xs sm:text-[13px] text-slate-800 leading-relaxed"">

                    ""Một hình vuông màu vàng có cạnh <strong class=""px-1.5 py-0.2 rounded bg-amber-200 text-amber-950 font-bold"">1 đơn vị dài</strong> được chia thành <strong class=""px-1.5 py-0.2 rounded bg-sky-200 text-sky-950 font-bold"">9 hình vuông nhỏ hơn</strong> và hình vuông ở chính giữa được <strong class=""px-1.5 py-0.2 rounded bg-sky-600 text-white font-bold"">tô màu xanh</strong> (Hình 2.1). Mỗi hình vuông màu vàng nhỏ hơn lại được chia thành 9 hình vuông con, và mỗi hình vuông con ở chính giữa lại được tô màu xanh. Nếu quá trình này được tiếp tục <strong class=""px-1.5 py-0.2 rounded bg-purple-200 text-purple-950 font-bold"">lặp lại năm lần</strong> thì <strong class=""px-1.5 py-0.2 rounded bg-rose-200 text-rose-950 font-bold underline decoration-rose-400"">tổng diện tích các hình vuông được tô màu xanh là bao nhiêu?</strong> (Làm tròn đến chữ số thập phân thứ hai)""

                </p>

        </div>

    </section>



    <!-- 3. LAYOUT CHÍNH: 2 CỘT CÂN ĐỐI VỪA KHÍT 1 MÀN HÌNH -->

    <main class=""flex-1 grid grid-cols-1 lg:grid-cols-12 gap-3 p-2 sm:p-3 overflow-hidden"">



        <!-- CỘT TRÁI (5/12): CANVAS KHÔNG BỊ CHE KHUẤT + NÚT MŨI TÊN + BỘ ĐIỀU KHIỂN PHÓNG TO THU NHỎ -->

        <section class=""lg:col-span-5 flex flex-col gap-2 h-full overflow-hidden bg-white rounded-xl border border-slate-200 p-2.5 shadow-xs"">

            

            <!-- THANH ĐIỀU HƯỚNG MŨI TÊN & TỰ ĐỘNG CHẠY -->

            <div class=""flex items-center justify-between gap-1.5 p-1.5 bg-slate-50 rounded-xl border border-slate-200 shrink-0"">

                <!-- Nút Mũi Tên Lùi -->

                <button onclick=""stepIteration(-1)"" id=""btnPrev"" class=""px-2.5 py-1.5 rounded-lg bg-white border border-slate-200 hover:bg-sky-50 hover:text-sky-700 text-slate-700 font-bold text-xs flex items-center gap-1 transition shadow-2xs disabled:opacity-40 disabled:cursor-not-allowed"">

                    <i class=""fa-solid fa-chevron-left text-xs""></i>

                    <span>Lùi</span>

                </button>



                <!-- Bộ đo Lần Lặp Trung Tâm -->

                <div class=""flex items-center gap-1"">

                    <span class=""text-xs font-semibold text-slate-500 hidden sm:inline"">Mức:</span>

                    <div class=""flex items-center gap-1"" id=""dotsContainer""></div>

                </div>



                <!-- Nút Tự Động / Tạm Dừng -->

                <button onclick=""toggleAutoPlay()"" id=""btnAutoPlay"" class=""px-2.5 py-1.5 rounded-lg bg-sky-600 hover:bg-sky-700 text-white font-semibold text-xs flex items-center gap-1 transition shadow-2xs"">

                    <i class=""fa-solid fa-play text-[10px]"" id=""iconPlay""></i>

                    <span id=""textPlay"">Tự động</span>

                </button>



                <!-- Nút Mũi Tên Tiến -->

                <button onclick=""stepIteration(1)"" id=""btnNext"" class=""px-2.5 py-1.5 rounded-lg bg-white border border-slate-200 hover:bg-sky-50 hover:text-sky-700 text-slate-700 font-bold text-xs flex items-center gap-1 transition shadow-2xs disabled:opacity-40 disabled:cursor-not-allowed"">

                    <span>Tiến</span>

                    <i class=""fa-solid fa-chevron-right text-xs""></i>

                </button>

            </div>



            <!-- THANH TRẠNG THÁI & CÔNG CỤ TIỆN ÍCH -->

            <div class=""flex items-center justify-between px-2 py-1.5 bg-slate-50 border border-slate-200 rounded-lg text-xs shrink-0 flex-wrap gap-1"">

                <div class=""flex items-center gap-1.5"">

                    <span id=""badgeCurrentN"" class=""px-2 py-0.5 rounded-md bg-sky-600 text-white font-mono font-bold text-xs shadow-2xs"">

                        Lần n = 1

                    </span>

                    <span id=""labelSubTitle"" class=""font-semibold text-slate-800 text-xs truncate max-w-[120px] sm:max-w-none""></span>

                </div>



                <!-- Nhóm nút tiện ích: Đường lưới + Ẩn/Hiện Diện tích + Zoom + Nút xem riêng hình -->

                <div class=""flex items-center gap-1"">

                    <!-- Nút bật/tắt đường lưới -->

                    <button onclick=""toggleGridLines()"" id=""btnToggleGrid"" class=""px-2 py-0.5 rounded border border-sky-300 bg-sky-50 text-sky-800 font-semibold text-[11px] flex items-center gap-1 hover:bg-sky-100 transition shadow-2xs"" title=""Bật/Tắt đường kẻ chia ô"">

                        <i class=""fa-solid fa-border-all text-[10px]""></i>

                        <span id=""textToggleGrid"">Lưới: Bật</span>

                    </button>



                    <!-- Nút Ẩn / Hiện Đáp số Diện tích để học sinh tự tính -->

                    <button onclick=""toggleAreaResults()"" id=""btnToggleArea"" class=""px-2 py-0.5 rounded border border-amber-300 bg-amber-50 text-amber-900 font-semibold text-[11px] flex items-center gap-1 hover:bg-amber-100 transition shadow-2xs"" title=""Ẩn/Hiện kết quả diện tích để HS tự giải"">

                        <i class=""fa-solid fa-eye-slash text-[10px]"" id=""iconToggleArea""></i>

                        <span id=""textToggleArea"">Đang ẩn diện tích</span>

                    </button>



                    <!-- Bộ điều khiển Thu/Phóng -->

                    <div class=""flex items-center gap-0.5 bg-white px-1.5 py-0.5 rounded-md border border-slate-200 shadow-2xs"">

                        <button onclick=""changeZoom(-0.15)"" class=""w-5 h-5 rounded hover:bg-slate-100 flex items-center justify-center font-bold text-slate-700"" title=""Thu nhỏ (-15%)"">

                            <i class=""fa-solid fa-minus text-[9px]""></i>

                        </button>

                        <span id=""zoomPercentLabel"" class=""text-[11px] font-mono font-bold min-w-[34px] text-center text-sky-700"">100%</span>

                        <button onclick=""changeZoom(0.15)"" class=""w-5 h-5 rounded hover:bg-slate-100 flex items-center justify-center font-bold text-slate-700"" title=""Phóng to (+15%)"">

                            <i class=""fa-solid fa-plus text-[9px]""></i>

                        </button>

                        <button onclick=""resetZoom()"" class=""text-[10px] text-slate-500 hover:text-sky-600 ml-0.5 underline"" title=""Đặt lại cỡ chuẩn 100%"">100%</button>

                    </div>



                    <!-- Nút mở chế độ chỉ chiếu ảnh -->

                    <button onclick=""openPresentationMode()"" class=""w-6 h-6 rounded bg-sky-600 hover:bg-sky-700 text-white flex items-center justify-center shadow-2xs"" title=""Phóng to toàn màn hình chỉ xem ảnh"">

                        <i class=""fa-solid fa-maximize text-[10px]""></i>

                    </button>

                </div>

            </div>



            <!-- VIEWPORT CANVAS TRỐNG THOÁNG -->

            <div id=""canvasViewportArea"" class=""flex-1 w-full bg-slate-50/70 rounded-xl border border-slate-200/80 p-2 flex items-center justify-center overflow-auto custom-scroll relative"">

                <div id=""canvasContainerBox"" class=""relative rounded-lg shadow-sm border border-slate-300 bg-white transition-all duration-150 shrink-0"" style=""width: 320px; height: 320px;"">

                    <canvas id=""carpetCanvas"" class=""w-full h-full block rounded-lg cursor-crosshair""></canvas>

                </div>

            </div>



            <!-- CHÚ THÍCH & TỌA ĐỘ KHI SOI CHUỘT -->

            <div class=""w-full flex items-center justify-between text-[11px] text-slate-600 px-1 font-mono shrink-0"">

                <div class=""flex items-center gap-2"">

                    <span class=""inline-flex items-center gap-1"">

                        <span class=""w-2.5 h-2.5 rounded-xs bg-tbYellow border border-amber-400""></span> Vàng còn

                    </span>

                    <span class=""inline-flex items-center gap-1"">

                        <span class=""w-2.5 h-2.5 rounded-xs bg-tbBlue""></span> Xanh đã tô

                    </span>

                </div>

                <div id=""hoverInspector"" class=""truncate text-right"">Rê chuột lên hình để soi ô con</div>

            </div>



            <!-- BỐN THẺ THÔNG SỐ TOÁN HỌC -->

            <div class=""grid grid-cols-2 sm:grid-cols-4 gap-1.5 shrink-0 text-xs"">

                <!-- Cạnh ô con -->

                <div class=""p-1.5 rounded-lg bg-slate-50 border border-slate-200 text-center"">

                    <div class=""text-[10px] text-slate-500 font-semibold"" id=""labelCardSide"">Cạnh ô con (<span class=""math-expr"" data-expr=""a_n"">a_n</span>)</div>

                    <div id=""metricSide"" class=""font-bold text-slate-900 mt-0.5""></div>

                </div>

                <!-- Số ô xanh thêm -->

                <div class=""p-1.5 rounded-lg bg-sky-50 border border-sky-200 text-center"">

                    <div class=""text-[10px] text-sky-800 font-semibold"">Số ô xanh thêm</div>

                    <div id=""metricNewSquares"" class=""font-bold text-sky-950 mt-0.5""></div>

                </div>

                <!-- Diện tích thêm (Hỗ trợ ẩn khi HS tự tính) -->

                <div class=""p-1.5 rounded-lg bg-emerald-50 border border-emerald-200 text-center relative cursor-pointer"" onclick=""toggleAreaResults()"" title=""Bấm để ẩn/hiện diện tích"">

                    <div class=""text-[10px] text-emerald-800 font-semibold"" id=""labelCardAdded"">Diện tích thêm (<span class=""math-expr"" data-expr=""u_n"">u_n</span>)</div>

                    <div id=""metricAddedArea"" class=""font-bold text-emerald-950 mt-0.5""></div>

                </div>

                <!-- Tổng diện tích (Hỗ trợ ẩn khi HS tự tính) -->

                <div class=""p-1.5 rounded-lg bg-amber-50 border border-amber-200 text-center relative cursor-pointer"" onclick=""toggleAreaResults()"" title=""Bấm để ẩn/hiện tổng diện tích"">

                    <div class=""text-[10px] text-amber-800 font-semibold"" id=""labelCardTotal"">Tổng diện tích (<span class=""math-expr"" data-expr=""S_n"">S_n</span>)</div>

                    <div id=""metricTotalArea"" class=""font-bold text-amber-950 mt-0.5""></div>

                </div>

            </div>



            <!-- THANH TỈ LỆ DIỆN TÍCH TỔNG HỢP (ẨN KHI ĐANG HỎI ĐÁP HS) -->

            <div id=""areaProgressContainer"" class=""p-2 rounded-xl bg-slate-50 border border-slate-200 shrink-0 space-y-1"">

                <div class=""flex justify-between items-center text-xs font-semibold"">

                    <span class=""text-sky-700"" id=""barTextBlue""></span>

                    <span class=""text-amber-700"" id=""barTextYellow""></span>

                </div>

                <div class=""w-full h-2.5 rounded-full bg-tbYellow overflow-hidden border border-slate-300 flex"">

                    <div id=""areaProgressBar"" class=""h-full bg-tbBlue transition-all duration-300"" style=""width: 11.11%""></div>

                </div>

            </div>



        </section>



        <!-- CỘT PHẢI (7/12): HƯỚNG DẪN TỪNG BƯỚC GỢI MỞ & HỎI ĐÁP HS -->

        <section class=""lg:col-span-7 flex flex-col h-full overflow-hidden bg-white rounded-xl border border-slate-200 shadow-xs"">

            

            <!-- HEADER CÁC TAB -->

            <div class=""p-2 bg-slate-50 border-b border-slate-200 flex items-center justify-between gap-1 shrink-0"">

                <div class=""grid grid-cols-3 gap-1 flex-1 text-xs font-semibold"">

                    <button onclick=""selectTab('guide')"" id=""navBtn-guide"" class=""py-1.5 px-2 rounded-lg text-center transition flex items-center justify-center gap-1.5 bg-white shadow-2xs text-sky-800 font-bold border border-slate-200"">

                        <i class=""fa-solid fa-lightbulb text-amber-500""></i>

                        <span>Gợi ý 5 bước cho HS</span>

                    </button>

                    <button onclick=""selectTab('solution')"" id=""navBtn-solution"" class=""py-1.5 px-2 rounded-lg text-center transition flex items-center justify-center gap-1.5 text-slate-600 hover:text-slate-900"">

                        <i class=""fa-solid fa-graduation-cap text-sky-600""></i>

                        <span>Lời giải 2 cách</span>

                    </button>

                    <button onclick=""selectTab('table')"" id=""navBtn-table"" class=""py-1.5 px-2 rounded-lg text-center transition flex items-center justify-center gap-1.5 text-slate-600 hover:text-slate-900"">

                        <i class=""fa-solid fa-table-list text-emerald-600""></i>

                        <span>Bảng số liệu lớn (n=0..5)</span>

                    </button>

                </div>

            </div>



            <!-- NỘI DUNG TAB 1: GỢI Ý & PHÂN TÍCH TỪNG BƯỚC (HỎI ĐÁP SƯ PHẠM) -->

            <div id=""tabContent-guide"" class=""flex-1 overflow-y-auto custom-scroll p-3 sm:p-4 space-y-3"">

                

                <!-- Thanh công cụ hỗ trợ giáo viên điều khiển hiển thị câu hỏi -->

                <div class=""flex items-center justify-between bg-sky-50/70 p-2.5 rounded-xl border border-sky-100 text-xs"">

                    <div class=""font-medium text-sky-950 flex items-center gap-1.5"">

                        <i class=""fa-solid fa-chalkboard-user text-sky-600""></i>

                        <span>Phương pháp: Đặt câu hỏi gợi mở cho học sinh trước khi xem đáp án</span>

                    </div>

                    <div class=""flex items-center gap-1.5"">

                        <button onclick=""toggleAllAccordions(true)"" class=""px-2 py-1 rounded bg-white border border-sky-200 text-sky-700 hover:bg-sky-100 font-semibold text-[11px] transition"">

                            Mở hết

                        </button>

                        <button onclick=""toggleAllAccordions(false)"" class=""px-2 py-1 rounded bg-white border border-slate-200 text-slate-600 hover:bg-slate-100 font-semibold text-[11px] transition"">

                            Ẩn hết

                        </button>

                    </div>

                </div>



                <!-- BƯỚC 1: QUAN SÁT LẦN 1 -->

                <div class=""rounded-xl border border-slate-200 overflow-hidden bg-white shadow-2xs transition hover:border-sky-300"" id=""stepCard-1"">

                    <div class=""p-3 bg-slate-50 border-b border-slate-200 flex items-center justify-between cursor-pointer"" onclick=""toggleAccordion('step1')"">

                        <div class=""flex items-center gap-2"">

                            <span class=""w-6 h-6 rounded-full bg-sky-600 text-white font-bold text-xs flex items-center justify-center"">1</span>

                            <div>

                                <h3 class=""text-xs sm:text-sm font-bold text-slate-900"">

                                    Bước 1: Quan sát Lần 1 (<span class=""math-expr"" data-expr=""n = 1"">n = 1</span>) & Thiết lập đơn vị cơ bản

                                </h3>

                                <span class=""text-[11px] text-slate-500"">Khám phá kích thước và tỉ lệ diện tích hình vuông đầu tiên</span>

                            </div>

                        </div>

                        <div class=""flex items-center gap-2"">

                            <button onclick=""event.stopPropagation(); jumpToN(1)"" class=""px-2 py-1 rounded bg-sky-100 hover:bg-sky-200 text-sky-800 text-[11px] font-bold transition"">

                                Xem hình n=1

                            </button>

                            <i class=""fa-solid fa-chevron-down text-xs text-slate-400 transition-transform duration-200"" id=""accIcon-step1""></i>

                        </div>

                    </div>



                    <div id=""accBody-step1"" class=""p-3.5 space-y-3 text-xs leading-relaxed text-slate-700"">

                        <div class=""p-2.5 rounded-lg bg-amber-50/80 border border-amber-200 space-y-1.5"">

                            <div class=""font-bold text-amber-950 flex items-center gap-1.5 text-xs"">

                                <i class=""fa-solid fa-circle-question text-amber-600""></i>

                                <span>Câu hỏi dẫn dắt giáo viên đặt cho học sinh:</span>

                            </div>

                            <ol class=""list-decimal list-inside space-y-1 text-slate-800"">

                                <li>Hình vuông ban đầu có diện tích bằng bao nhiêu? Khi chia cạnh làm 3 phần thì hình vuông được chia thành bao nhiêu ô vuông nhỏ hơn?</li>

                                <li>Mỗi ô vuông nhỏ có cạnh bằng bao nhiêu và diện tích bằng bao nhiêu so với hình ban đầu?</li>

                                <li>Có bao nhiêu ô vuông được tô màu xanh ở Lần 1? Diện tích màu xanh <span class=""math-expr"" data-expr=""u_1"">u_1</span> bằng bao nhiêu? Còn lại bao nhiêu ô vàng?</li>

                            </ol>

                        </div>



                        <div class=""flex items-center gap-2"">

                            <button onclick=""toggleBox('hint-1')"" class=""px-2.5 py-1 rounded-md bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold text-xs flex items-center gap-1 transition"">

                                <i class=""fa-regular fa-eye text-sky-600""></i>

                                <span id=""hintBtnText-1"">Hiện gợi ý trả lời</span>

                            </button>

                            <button onclick=""toggleBox('ans-1')"" class=""px-2.5 py-1 rounded-md bg-sky-50 hover:bg-sky-100 text-sky-800 font-semibold text-xs flex items-center gap-1 border border-sky-200 transition"">

                                <i class=""fa-solid fa-check text-emerald-600""></i>

                                <span id=""ansBtnText-1"">Hiện kết luận & công thức</span>

                            </button>

                        </div>



                        <div id=""box-hint-1"" class=""hidden p-2.5 rounded-lg bg-sky-50/60 border border-sky-100 space-y-1"">

                            <p class=""font-semibold text-sky-900"">💡 Gợi ý định hướng:</p>

                            <p>• Hình vuông cạnh $1 \implies S_0 = 1^2 = 1$.</p>

                            <p>• Chia mỗi cạnh làm 3 phần bằng nhau $\implies$ tạo ra $3 \times 3 = 9$ ô vuông con bằng nhau, mỗi ô có cạnh $a_1 = \frac{1}{3}$.</p>

                            <p>• Chỉ có đúng $1$ ô chính giữa được tô xanh $\implies$ còn lại $8$ ô màu vàng.</p>

                        </div>



                        <div id=""box-ans-1"" class=""hidden p-3 rounded-lg bg-emerald-50/70 border border-emerald-200 space-y-1.5 font-medium text-emerald-950"">

                            <p class=""font-bold text-emerald-900"">✅ Kết luận chuẩn bước 1:</p>

                            <p>• Cạnh mỗi ô vuông con: $a_1 = \frac{1}{3}$.</p>

                            <p>• Diện tích $1$ ô vuông xanh: $s_1 = \left(\frac{1}{3}\right)^2 = \frac{1}{9}$.</p>

                            <p>• Số ô xanh tô mới: $1$ ô $\implies$ Diện tích xanh Lần 1 là $u_1 = \frac{1}{9}$.</p>

                            <p>• Diện tích màu vàng còn lại: $V_1 = 1 - \frac{1}{9} = \frac{8}{9}$ (gồm $8$ ô vàng, mỗi ô diện tích $\frac{1}{9}$).</p>

                        </div>

                    </div>

                </div>



                <!-- BƯỚC 2: QUAN SÁT LẦN 2 -->

                <div class=""rounded-xl border border-slate-200 overflow-hidden bg-white shadow-2xs transition hover:border-sky-300"" id=""stepCard-2"">

                    <div class=""p-3 bg-slate-50 border-b border-slate-200 flex items-center justify-between cursor-pointer"" onclick=""toggleAccordion('step2')"">

                        <div class=""flex items-center gap-2"">

                            <span class=""w-6 h-6 rounded-full bg-sky-600 text-white font-bold text-xs flex items-center justify-center"">2</span>

                            <div>

                                <h3 class=""text-xs sm:text-sm font-bold text-slate-900"">

                                    Bước 2: Quan sát Lần 2 (<span class=""math-expr"" data-expr=""n = 2"">n = 2</span>) & Phát hiện độ tăng

                                </h3>

                                <span class=""text-[11px] text-slate-500"">Mỗi ô vàng lại sinh ra bao nhiêu ô xanh và tăng thêm bao nhiêu diện tích?</span>

                            </div>

                        </div>

                        <div class=""flex items-center gap-2"">

                            <button onclick=""event.stopPropagation(); jumpToN(2)"" class=""px-2 py-1 rounded bg-sky-100 hover:bg-sky-200 text-sky-800 text-[11px] font-bold transition"">

                                Xem hình n=2

                            </button>

                            <i class=""fa-solid fa-chevron-down text-xs text-slate-400 transition-transform duration-200"" id=""accIcon-step2""></i>

                        </div>

                    </div>



                    <div id=""accBody-step2"" class=""p-3.5 space-y-3 text-xs leading-relaxed text-slate-700"">

                        <div class=""p-2.5 rounded-lg bg-amber-50/80 border border-amber-200 space-y-1.5"">

                            <div class=""font-bold text-amber-950 flex items-center gap-1.5 text-xs"">

                                <i class=""fa-solid fa-circle-question text-amber-600""></i>

                                <span>Câu hỏi dẫn dắt giáo viên đặt cho học sinh:</span>

                            </div>

                            <ol class=""list-decimal list-inside space-y-1 text-slate-800"">

                                <li>Ở lần 2, quá trình chia 9 ô được lặp lại trên những ô vuông nào (ô xanh hay ô vàng)?</li>

                                <li>Có bao nhiêu ô màu vàng từ lần 1 được tiếp tục chia nhỏ?</li>

                                <li>Mỗi ô màu vàng đó lại sinh ra mấy ô vuông xanh ở giữa? Vậy ở lần 2 ta <strong>tăng thêm bao nhiêu ô vuông xanh</strong>?</li>

                                <li>Cạnh của mỗi ô vuông xanh mới bằng bao nhiêu? Diện tích của mỗi ô đó là bao nhiêu?</li>

                                <li>Tổng diện tích màu xanh <strong>tăng thêm ở lần 2 (<span class=""math-expr"" data-expr=""u_2"">u_2</span>)</strong> là bao nhiêu? So với <span class=""math-expr"" data-expr=""u_1"">u_1</span> thì gấp bao nhiêu lần?</li>

                            </ol>

                        </div>



                        <div class=""flex items-center gap-2"">

                            <button onclick=""toggleBox('hint-2')"" class=""px-2.5 py-1 rounded-md bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold text-xs flex items-center gap-1 transition"">

                                <i class=""fa-regular fa-eye text-sky-600""></i>

                                <span id=""hintBtnText-2"">Hiện gợi ý trả lời</span>

                            </button>

                            <button onclick=""toggleBox('ans-2')"" class=""px-2.5 py-1 rounded-md bg-sky-50 hover:bg-sky-100 text-sky-800 font-semibold text-xs flex items-center gap-1 border border-sky-200 transition"">

                                <i class=""fa-solid fa-check text-emerald-600""></i>

                                <span id=""ansBtnText-2"">Hiện kết luận & công thức</span>

                            </button>

                        </div>



                        <div id=""box-hint-2"" class=""hidden p-2.5 rounded-lg bg-sky-50/60 border border-sky-100 space-y-1"">

                            <p class=""font-semibold text-sky-900"">💡 Gợi ý định hướng:</p>

                            <p>• Ô xanh đã tô thì giữ nguyên. Chỉ có $8$ ô vàng của Lần 1 mới bị chia nhỏ tiếp.</p>

                            <p>• Mỗi ô vàng sinh ra $1$ ô xanh con $\implies$ Số ô xanh mới tô thêm đúng bằng $8 \times 1 = 8$ ô.</p>

                            <p>• Cạnh mỗi ô con mới: lấy cạnh $\frac{1}{3}$ chia 3 $\implies a_2 = \frac{1}{3^2} = \frac{1}{9}$.</p>

                        </div>



                        <div id=""box-ans-2"" class=""hidden p-3 rounded-lg bg-emerald-50/70 border border-emerald-200 space-y-1.5 font-medium text-emerald-950"">

                            <p class=""font-bold text-emerald-900"">✅ Kết luận chuẩn bước 2:</p>

                            <p>• Cạnh ô xanh mới: $a_2 = \frac{1}{9}$. Diện tích $1$ ô xanh mới: $s_2 = \left(\frac{1}{9}\right)^2 = \frac{1}{81}$.</p>

                            <p>• Số lượng ô xanh mới tăng thêm: $8$ ô.</p>

                            <p>• Diện tích màu xanh tăng thêm ở lần 2: $$u_2 = 8 \cdot \frac{1}{81} = \frac{8}{81}$$</p>

                            <p>• Nhận xét tỉ số: $$\frac{u_2}{u_1} = \frac{8/81}{1/9} = \frac{8}{9}$$</p>

                        </div>

                    </div>

                </div>



                <!-- BƯỚC 3: QUY NẠP TỔNG QUÁT CẤP SỐ NHÂN -->

                <div class=""rounded-xl border border-slate-200 overflow-hidden bg-white shadow-2xs transition hover:border-sky-300"" id=""stepCard-3"">

                    <div class=""p-3 bg-slate-50 border-b border-slate-200 flex items-center justify-between cursor-pointer"" onclick=""toggleAccordion('step3')"">

                        <div class=""flex items-center gap-2"">

                            <span class=""w-6 h-6 rounded-full bg-sky-600 text-white font-bold text-xs flex items-center justify-center"">3</span>

                            <div>

                                <h3 class=""text-xs sm:text-sm font-bold text-slate-900"">

                                    Bước 3: Tổng quát hóa lần thứ <span class=""math-expr"" data-expr=""k"">k</span> & Nhận dạng Cấp Số Nhân

                                </h3>

                                <span class=""text-[11px] text-slate-500"">Thiết lập công thức tổng quát cho diện tích tăng thêm <span class=""math-expr"" data-expr=""u_k"">u_k</span></span>

                            </div>

                        </div>

                        <div class=""flex items-center gap-2"">

                            <button onclick=""event.stopPropagation(); jumpToN(3)"" class=""px-2 py-1 rounded bg-sky-100 hover:bg-sky-200 text-sky-800 text-[11px] font-bold transition"">

                                Xem hình n=3

                            </button>

                            <i class=""fa-solid fa-chevron-down text-xs text-slate-400 transition-transform duration-200"" id=""accIcon-step3""></i>

                        </div>

                    </div>



                    <div id=""accBody-step3"" class=""p-3.5 space-y-3 text-xs leading-relaxed text-slate-700"">

                        <div class=""p-2.5 rounded-lg bg-amber-50/80 border border-amber-200 space-y-1.5"">

                            <div class=""font-bold text-amber-950 flex items-center gap-1.5 text-xs"">

                                <i class=""fa-solid fa-circle-question text-amber-600""></i>

                                <span>Câu hỏi dẫn dắt giáo viên đặt cho học sinh:</span>

                            </div>

                            <ol class=""list-decimal list-inside space-y-1 text-slate-800"">

                                <li>Số ô xanh thêm mới qua các lần $n=1, 2, 3,\dots$ là $1, 8, 64,\dots$ Đây là dãy số có quy luật lũy thừa như thế nào?</li>

                                <li>Diện tích của $1$ ô xanh con qua các lần $n=1, 2, 3,\dots$ là $\frac{1}{9}, \frac{1}{9^2}, \frac{1}{9^3},\dots$ biến đổi ra sao?</li>

                                <li>Từ đó hãy nhân (Số ô) $\times$ (Diện tích 1 ô) để tìm diện tích $u_k$ tăng thêm ở lần lặp thứ $k$?</li>

                                <li>Dãy số $(u_n)$ có phải là một <strong>Cấp số nhân</strong> không? Hãy chỉ ra số hạng đầu $u_1$ và công bội $q$?</li>

                            </ol>

                        </div>



                        <div class=""flex items-center gap-2"">

                            <button onclick=""toggleBox('hint-3')"" class=""px-2.5 py-1 rounded-md bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold text-xs flex items-center gap-1 transition"">

                                <i class=""fa-regular fa-eye text-sky-600""></i>

                                <span id=""hintBtnText-3"">Hiện gợi ý trả lời</span>

                            </button>

                            <button onclick=""toggleBox('ans-3')"" class=""px-2.5 py-1 rounded-md bg-sky-50 hover:bg-sky-100 text-sky-800 font-semibold text-xs flex items-center gap-1 border border-sky-200 transition"">

                                <i class=""fa-solid fa-check text-emerald-600""></i>

                                <span id=""ansBtnText-3"">Hiện kết luận & công thức</span>

                            </button>

                        </div>



                        <div id=""box-hint-3"" class=""hidden p-2.5 rounded-lg bg-sky-50/60 border border-sky-100 space-y-1"">

                            <p class=""font-semibold text-sky-900"">💡 Gợi ý định hướng:</p>

                            <p>• Ở lần thứ $k$: số ô vuông xanh mới thêm vào là $8^{k-1}$.</p>

                            <p>• Cạnh mỗi ô con là $a_k = \frac{1}{3^k} \implies$ diện tích mỗi ô là $s_k = \left(\frac{1}{3^k}\right)^2 = \frac{1}{9^k}$.</p>

                            <p>• Lập tỉ số $\frac{u_{k+1}}{u_k}$ để kiểm tra xem có phải là hằng số $q$ không.</p>

                        </div>



                        <div id=""box-ans-3"" class=""hidden p-3 rounded-lg bg-emerald-50/70 border border-emerald-200 space-y-1.5 font-medium text-emerald-950"">

                            <p class=""font-bold text-emerald-900"">✅ Kết luận chuẩn bước 3:</p>

                            <p>• Diện tích màu xanh tăng thêm ở lần lặp thứ $k$ là: $$u_k = 8^{k-1} \cdot \frac{1}{9^k} = \frac{1}{9} \cdot \left(\frac{8}{9}\right)^{k-1}$$</p>

                            <p>• Dãy số $(u_k)$ là một <strong>cấp số nhân</strong> với:</p>

                            <ul class=""list-disc list-inside ml-2"">

                                <li>Số hạng đầu: $u_1 = \frac{1}{9}$</li>

                                <li>Công bội: $q = \frac{8}{9} < 1$</li>

                            </ul>

                        </div>

                    </div>

                </div>



                <!-- BƯỚC 4: THIẾT LẬP TỔNG S5 -->

                <div class=""rounded-xl border border-slate-200 overflow-hidden bg-white shadow-2xs transition hover:border-sky-300"" id=""stepCard-4"">

                    <div class=""p-3 bg-slate-50 border-b border-slate-200 flex items-center justify-between cursor-pointer"" onclick=""toggleAccordion('step4')"">

                        <div class=""flex items-center gap-2"">

                            <span class=""w-6 h-6 rounded-full bg-sky-600 text-white font-bold text-xs flex items-center justify-center"">4</span>

                            <div>

                                <h3 class=""text-xs sm:text-sm font-bold text-slate-900"">

                                    Bước 4: Thiết lập biểu thức tính Tổng diện tích sau 5 lần (<span class=""math-expr"" data-expr=""S_5"">S_5</span>)

                                </h3>

                                <span class=""text-[11px] text-slate-500"">So sánh 2 hướng tiếp cận: Tổng cấp số nhân vs Phần bù diện tích màu vàng</span>

                            </div>

                        </div>

                        <div class=""flex items-center gap-2"">

                            <button onclick=""event.stopPropagation(); jumpToN(5)"" class=""px-2 py-1 rounded bg-sky-100 hover:bg-sky-200 text-sky-800 text-[11px] font-bold transition"">

                                Xem hình n=5

                            </button>

                            <i class=""fa-solid fa-chevron-down text-xs text-slate-400 transition-transform duration-200"" id=""accIcon-step4""></i>

                        </div>

                    </div>



                    <div id=""accBody-step4"" class=""p-3.5 space-y-3 text-xs leading-relaxed text-slate-700"">

                        <div class=""p-2.5 rounded-lg bg-amber-50/80 border border-amber-200 space-y-1.5"">

                            <div class=""font-bold text-amber-950 flex items-center gap-1.5 text-xs"">

                                <i class=""fa-solid fa-circle-question text-amber-600""></i>

                                <span>Câu hỏi dẫn dắt giáo viên đặt cho học sinh:</span>

                            </div>

                            <ol class=""list-decimal list-inside space-y-1 text-slate-800"">

                                <li>Muốn tính tổng diện tích các hình vuông màu xanh sau 5 lần lặp, ta cần tính tổng của biểu thức nào? Áp dụng công thức tổng $n$ số hạng đầu $S_n = u_1 \frac{1 - q^n}{1 - q}$ ra sao?</li>

                                <li><strong>Cách tư duy thông minh (Phần bù):</strong> Sau mỗi lần lặp, diện tích màu vàng còn lại bằng bao nhiêu phần diện tích màu vàng trước đó? Vậy sau 5 lần lặp, diện tích vàng còn lại $V_5$ là bao nhiêu? Từ đó suy ra $S_5$ bằng cách nào?</li>

                            </ol>

                        </div>



                        <div class=""flex items-center gap-2"">

                            <button onclick=""toggleBox('hint-4')"" class=""px-2.5 py-1 rounded-md bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold text-xs flex items-center gap-1 transition"">

                                <i class=""fa-regular fa-eye text-sky-600""></i>

                                <span id=""hintBtnText-4"">Hiện gợi ý trả lời</span>

                            </button>

                            <button onclick=""toggleBox('ans-4')"" class=""px-2.5 py-1 rounded-md bg-sky-50 hover:bg-sky-100 text-sky-800 font-semibold text-xs flex items-center gap-1 border border-sky-200 transition"">

                                <i class=""fa-solid fa-check text-emerald-600""></i>

                                <span id=""ansBtnText-4"">Hiện kết luận & công thức</span>

                            </button>

                        </div>



                        <div id=""box-hint-4"" class=""hidden p-2.5 rounded-lg bg-sky-50/60 border border-sky-100 space-y-1"">

                            <p class=""font-semibold text-sky-900"">💡 Gợi ý định hướng:</p>

                            <p>• Cách 1: Thay $u_1 = \frac{1}{9}$, $q = \frac{8}{9}$, $n = 5$ vào công thức $S_5 = u_1 \cdot \frac{1 - q^5}{1 - q}$. Chú ý mẫu số $1 - \frac{8}{9} = \frac{1}{9}$ sẽ triệt tiêu gọn gàng với $u_1$!</p>

                            <p>• Cách 2: Toàn bộ diện tích ban đầu là $1$. Phần vàng còn lại sau mỗi bước bị nhân với $\frac{8}{9} \implies V_5 = \left(\frac{8}{9}\right)^5$. Do đó $S_5 = 1 - V_5 = 1 - \left(\frac{8}{9}\right)^5$.</p>

                        </div>



                        <div id=""box-ans-4"" class=""hidden p-3 rounded-lg bg-emerald-50/70 border border-emerald-200 space-y-1.5 font-medium text-emerald-950"">

                            <p class=""font-bold text-emerald-900"">✅ Kết luận chuẩn bước 4:</p>

                            <p>Cả hai cách đều dẫn đến một biểu thức rút gọn duy nhất cực kỳ đẹp mắt:</p>

                            <div class=""p-2 bg-white rounded border border-emerald-200 text-center font-bold text-emerald-900"">

                                $$S_5 = 1 - \left(\frac{8}{9}\right)^5$$

                            </div>

                        </div>

                    </div>

                </div>



                <!-- BƯỚC 5: TÍNH TOÁN & LÀM TRÒN -->

                <div class=""rounded-xl border border-slate-200 overflow-hidden bg-white shadow-2xs transition hover:border-sky-300"" id=""stepCard-5"">

                    <div class=""p-3 bg-slate-50 border-b border-slate-200 flex items-center justify-between cursor-pointer"" onclick=""toggleAccordion('step5')"">

                        <div class=""flex items-center gap-2"">

                            <span class=""w-6 h-6 rounded-full bg-emerald-600 text-white font-bold text-xs flex items-center justify-center"">5</span>

                            <div>

                                <h3 class=""text-xs sm:text-sm font-bold text-slate-900"">

                                    Bước 5: Tính kết quả phân số & Làm tròn thập phân theo yêu cầu

                                </h3>

                                <span class=""text-[11px] text-slate-500"">Hoàn thành bài toán với độ chính xác theo đề bài</span>

                            </div>

                        </div>

                        <div class=""flex items-center gap-2"">

                            <span class=""px-2 py-0.5 rounded bg-emerald-100 text-emerald-800 text-[10px] font-bold"">Đáp số cuối</span>

                            <i class=""fa-solid fa-chevron-down text-xs text-slate-400 transition-transform duration-200"" id=""accIcon-step5""></i>

                        </div>

                    </div>



                    <div id=""accBody-step5"" class=""p-3.5 space-y-3 text-xs leading-relaxed text-slate-700"">

                        <div class=""p-2.5 rounded-lg bg-amber-50/80 border border-amber-200 space-y-1.5"">

                            <div class=""font-bold text-amber-950 flex items-center gap-1.5 text-xs"">

                                <i class=""fa-solid fa-circle-question text-amber-600""></i>

                                <span>Câu hỏi dẫn dắt giáo viên đặt cho học sinh:</span>

                            </div>

                            <ol class=""list-decimal list-inside space-y-1 text-slate-800"">

                                <li>Tính giá trị lũy thừa $8^5$ và $9^5$?</li>

                                <li>Phân số chính xác của $S_5$ là bao nhiêu?</li>

                                <li>Đổi ra số thập phân và làm tròn đến <strong>chữ số thập phân thứ hai</strong> như đề bài yêu cầu thì ta được bao nhiêu?</li>

                            </ol>

                        </div>



                        <div class=""flex items-center gap-2"">

                            <button onclick=""toggleBox('ans-5')"" class=""px-3 py-1.5 rounded-md bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs flex items-center gap-1.5 shadow-2xs transition"">

                                <i class=""fa-solid fa-trophy""></i>

                                <span id=""ansBtnText-5"">Xem đáp số chính xác & làm tròn</span>

                            </button>

                        </div>



                        <div id=""box-ans-5"" class=""hidden p-3 rounded-lg bg-emerald-50 border border-emerald-300 space-y-2 text-emerald-950"">

                            <p class=""font-bold text-emerald-900 text-sm"">🏆 Lời giải kết luận chuẩn:</p>

                            <p>Ta có:</p>

                            <div class=""p-2 bg-white rounded border border-emerald-200 text-center font-mono text-xs"">

                                $$8^5 = 32768, \quad 9^5 = 59049$$

                            </div>

                            <p>Tổng diện tích các hình vuông được tô màu xanh sau 5 lần lặp là:</p>

                            <div class=""p-2.5 bg-white rounded-lg border border-emerald-200 text-center text-xs sm:text-sm font-bold text-emerald-900"">

                                $$S_5 = 1 - \frac{32768}{59049} = \frac{26281}{59049} \approx 0.445071...$$

                            </div>

                            <div class=""p-2.5 bg-emerald-600 text-white rounded-lg text-center font-bold text-sm shadow-xs"">

                                Làm tròn đến chữ số thập phân thứ hai: <span class=""text-amber-200 text-base font-extrabold underline underline-offset-4"">0,45</span> (hoặc 45%)

                            </div>

                        </div>

                    </div>

                </div>



            </div>



            <!-- NỘI DUNG TAB 2: LỜI GIẢI CHI TIẾT 2 PHƯƠNG PHÁP -->

            <div id=""tabContent-solution"" class=""hidden flex-1 overflow-y-auto custom-scroll p-3 sm:p-4 space-y-3 text-xs leading-relaxed"">

                <!-- Cách 1 -->

                <div class=""p-3.5 rounded-xl bg-slate-50 border border-slate-200 space-y-2"">

                    <div class=""font-bold text-sky-900 flex items-center gap-2 text-xs sm:text-sm"">

                        <span class=""w-5 h-5 rounded-full bg-sky-600 text-white flex items-center justify-center text-[10px]"">1</span>

                        <span>Cách 1: Tính trực tiếp theo Tổng Cấp Số Nhân</span>

                    </div>

                    <div class=""space-y-1.5 text-slate-700"">

                        <p>• <strong>Lần 1 ($n=1$):</strong> Có $1$ hình vuông xanh cạnh $\frac{1}{3}$. Diện tích là $u_1 = \left(\frac{1}{3}\right)^2 = \frac{1}{9}$.</p>

                        <p>• <strong>Lần 2 ($n=2$):</strong> Có $8$ ô vuông vàng từ bước trước, mỗi ô sinh ra $1$ ô vuông xanh mới cạnh $\frac{1}{9}$. Số ô xanh thêm là $8$, diện tích: $u_2 = 8 \cdot \left(\frac{1}{9}\right)^2 = \frac{8}{81}$.</p>

                        <p>• <strong>Lần thứ $k$:</strong> Số ô vuông xanh được tô thêm là $8^{k-1}$, mỗi ô có diện tích $\left(\frac{1}{3^k}\right)^2 = \frac{1}{9^k}$. Do đó diện tích tăng thêm là:</p>

                        <div class=""p-2 bg-white rounded border border-slate-200 text-center font-mono"">

                            $$u_k = 8^{k-1} \cdot \frac{1}{9^k} = \frac{1}{9}\left(\frac{8}{9}\right)^{k-1}$$

                        </div>

                        <p>Dãy số $(u_k)$ là một cấp số nhân có số hạng đầu $u_1 = \frac{1}{9}$ và công bội $q = \frac{8}{9}$.</p>

                        <p>Tổng diện tích màu xanh sau 5 lần lặp là tổng 5 số hạng đầu của cấp số nhân:</p>

                        <div class=""p-2 bg-white rounded border border-slate-200 text-center font-mono"">

                            $$S_5 = u_1 \cdot \frac{1 - q^5}{1 - q} = \frac{1}{9} \cdot \frac{1 - (8/9)^5}{1 - 8/9} = 1 - \left(\frac{8}{9}\right)^5 = \frac{26281}{59049} \approx 0.4451$$

                        </div>

                        <p class=""font-bold text-sky-950"">Làm tròn đến 2 chữ số thập phân: <span class=""bg-sky-200 px-1.5 py-0.5 rounded text-sky-900"">0,45</span></p>

                    </div>

                </div>



                <!-- Cách 2 -->

                <div class=""p-3.5 rounded-xl bg-slate-50 border border-slate-200 space-y-2"">

                    <div class=""font-bold text-amber-900 flex items-center gap-2 text-xs sm:text-sm"">

                        <span class=""w-5 h-5 rounded-full bg-amber-600 text-white flex items-center justify-center text-[10px]"">2</span>

                        <span>Cách 2: Phương pháp phần bù diện tích màu vàng (Cực nhanh)</span>

                    </div>

                    <div class=""space-y-1.5 text-slate-700"">

                        <p>• Hình vuông ban đầu có diện tích $S_{\text{tổng}} = 1^2 = 1$.</p>

                        <p>• Ở mỗi bước, mỗi ô vuông màu vàng được chia làm $9$ phần bằng nhau và bỏ đi $1$ phần ở giữa để tô màu xanh. Do đó, diện tích màu vàng còn lại luôn bằng $\frac{8}{9}$ diện tích màu vàng của bước trước đó.</p>

                        <p>• Sau 5 lần lặp, diện tích màu vàng còn lại là:</p>

                        <div class=""p-2 bg-white rounded border border-slate-200 text-center font-mono"">

                            $$V_5 = 1 \cdot \left(\frac{8}{9}\right)^5 = \frac{32768}{59049}$$

                        </div>

                        <p>• Tổng diện tích màu xanh đã tô là phần bù:</p>

                        <div class=""p-2 bg-amber-50 rounded border border-amber-300 text-center font-mono font-bold text-amber-950"">

                            $$S_5 = S_{\text{tổng}} - V_5 = 1 - \left(\frac{8}{9}\right)^5 = \frac{26281}{59049} \approx 0.45$$

                        </div>

                    </div>

                </div>

            </div>



            <!-- NỘI DUNG TAB 3: BẢNG SỐ LIỆU ĐỐI SOÁT (CHỮ VÀ SỐ TO RÕ RÀNG) -->

            <div id=""tabContent-table"" class=""hidden flex-1 overflow-y-auto custom-scroll p-3 sm:p-4 space-y-3"">

                <div class=""flex items-center justify-between pb-1 text-sm border-b border-slate-100"">

                    <span class=""font-bold text-slate-900 text-sm sm:text-base"">Bảng giá trị biến thiên chi tiết qua 5 lần lặp:</span>

                    <span class=""text-slate-500 text-xs"">Bấm dòng để xem hình vẽ tương ứng</span>

                </div>

                <div class=""overflow-x-auto rounded-xl border border-slate-200 shadow-2xs"">

                    <table class=""w-full text-sm sm:text-base text-left border-collapse table-math"">

                        <thead class=""bg-slate-100 text-slate-800 font-bold border-b border-slate-200"">

                            <tr>

                                <th class=""p-3 text-center"">Lần <span class=""math-expr"" data-expr=""n"">n</span></th>

                                <th class=""p-3 text-center"">Cạnh ô con (<span class=""math-expr"" data-expr=""a_n"">a_n</span>)</th>

                                <th class=""p-3 text-center"">Số ô xanh mới</th>

                                <th class=""p-3 text-center"">Diện tích thêm (<span class=""math-expr"" data-expr=""u_n"">u_n</span>)</th>

                                <th class=""p-3 text-center"">Tổng diện tích (<span class=""math-expr"" data-expr=""S_n"">S_n</span>)</th>

                                <th class=""p-3 text-right"">% Xanh</th>

                            </tr>

                        </thead>

                        <tbody id=""tableBodyProgression"" class=""divide-y divide-slate-200 font-mono"">

                            <!-- Render bằng JS với font to và phân số lớn -->

                        </tbody>

                    </table>

                </div>

            </div>



        </section>



    </main>



    <!-- ================= 4. CHẾ ĐỘ TRÌNH CHIẾU TOÀN MÀN HÌNH CHUYÊN DỤNG (CHỈ CHIẾU HÌNH & NÚT MŨI TÊN CHUYỂN ĐỔI) ================= -->

    <div id=""presentationOverlay"" class=""fixed inset-0 z-50 bg-slate-950/95 backdrop-blur-sm flex flex-col items-center justify-between p-3 sm:p-5 select-none text-white hidden"">

        

        <!-- THANH ĐIỀU KHIỂN NỔI PHÍA TRÊN CỦA CHẾ ĐỘ TRÌNH CHIẾU -->

        <header class=""w-full max-w-6xl flex items-center justify-between gap-2 flex-wrap shrink-0 pb-2 border-b border-slate-800"">

            <!-- Thông tin bước lặp -->

            <div class=""flex items-center gap-2"">

                <span id=""presBadgeN"" class=""px-3 py-1 rounded-lg bg-sky-600 text-white font-mono font-extrabold text-sm sm:text-base shadow-md"">

                    Lần n = 1

                </span>

                <span id=""presTitle"" class=""text-xs sm:text-sm font-semibold text-slate-200 truncate max-w-[220px] sm:max-w-none"">

                    Lần lặp thứ 1

                </span>

            </div>



            <!-- BỘ ĐIỀU KHIỂN MŨI TÊN QUA LẠI TRUNG TÂM -->

            <div class=""flex items-center gap-2 bg-slate-900/90 px-3 py-1.5 rounded-2xl border border-slate-700/80 shadow-xl"">

                <!-- Nút Lùi -->

                <button onclick=""stepIteration(-1)"" id=""presBtnPrev"" class=""px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-sky-600 text-white font-bold text-xs sm:text-sm flex items-center gap-1.5 transition shadow-sm disabled:opacity-30 disabled:cursor-not-allowed"">

                    <i class=""fa-solid fa-chevron-left""></i>

                    <span>Lùi</span>

                </button>



                <!-- Bộ đo n = 0..5 -->

                <div class=""flex items-center gap-1 sm:gap-1.5"" id=""presDotsContainer""></div>



                <!-- Tự động chạy -->

                <button onclick=""toggleAutoPlay()"" id=""presBtnAuto"" class=""px-3 py-1.5 rounded-xl bg-sky-600 hover:bg-sky-500 text-white font-bold text-xs sm:text-sm flex items-center gap-1.5 transition shadow-sm"">

                    <i class=""fa-solid fa-play text-xs"" id=""presIconPlay""></i>

                    <span id=""presTextPlay"">Tự động</span>

                </button>



                <!-- Nút Tiến -->

                <button onclick=""stepIteration(1)"" id=""presBtnNext"" class=""px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-sky-600 text-white font-bold text-xs sm:text-sm flex items-center gap-1.5 transition shadow-sm disabled:opacity-30 disabled:cursor-not-allowed"">

                    <span>Tiến</span>

                    <i class=""fa-solid fa-chevron-right""></i>

                </button>

            </div>



            <!-- Tiện ích bên phải: Lưới & Thoát trình chiếu -->

            <div class=""flex items-center gap-2"">

                <button onclick=""toggleGridLines()"" id=""presBtnGrid"" class=""px-2.5 py-1.5 rounded-xl bg-slate-800 border border-slate-700 text-slate-300 hover:text-white text-xs font-semibold flex items-center gap-1 transition"">

                    <i class=""fa-solid fa-border-all text-xs""></i>

                    <span id=""presTextGrid"">Lưới: Bật</span>

                </button>

                <button onclick=""closePresentationMode()"" class=""px-3 py-1.5 rounded-xl bg-rose-600 hover:bg-rose-500 text-white font-bold text-xs sm:text-sm flex items-center gap-1.5 transition shadow-md"" title=""Thoát chế độ trình chiếu (Phím Esc)"">

                    <i class=""fa-solid fa-compress""></i>

                    <span>Thoát (Esc)</span>

                </button>

            </div>

        </header>



        <!-- KHUNG CANVAS TOÀN MÀN HÌNH KHÔNG BỊ BẤT KỲ GÌ CHE KHUẤT -->

        <div class=""flex-1 flex items-center justify-center w-full my-3 overflow-hidden"">

            <div id=""presCanvasContainer"" class=""relative rounded-2xl shadow-2xl border-2 border-sky-500/70 bg-white aspect-square overflow-hidden"" style=""height: min(74vh, 680px); width: min(74vh, 680px);"">

                <canvas id=""presentationCanvas"" class=""w-full h-full block cursor-crosshair""></canvas>

            </div>

        </div>



        <!-- THANH FOOTER TRÌNH CHIẾU: THÔNG SỐ VÀ PHÍM TẮT -->

        <footer class=""w-full max-w-4xl flex items-center justify-between text-xs text-slate-400 shrink-0 pt-2 border-t border-slate-800 flex-wrap gap-2"">

            <div class=""flex items-center gap-3"">

                <span class=""inline-flex items-center gap-1.5 text-amber-300 font-semibold"">

                    <span class=""w-3 h-3 rounded-xs bg-tbYellow border border-amber-400""></span>

                    <span id=""presYellowText"">Vàng còn lại</span>

                </span>

                <span class=""inline-flex items-center gap-1.5 text-sky-300 font-semibold"">

                    <span class=""w-3 h-3 rounded-xs bg-tbBlue""></span>

                    <span id=""presBlueText"">Xanh đã tô</span>

                </span>

            </div>



            <div class=""flex items-center gap-2 font-mono text-[11px] text-slate-400"">

                <span>Dùng phím:</span>

                <kbd class=""px-1.5 py-0.5 bg-slate-800 rounded border border-slate-700 text-white font-bold"">←</kbd>

                <kbd class=""px-1.5 py-0.5 bg-slate-800 rounded border border-slate-700 text-white font-bold"">→</kbd>

                <span>chuyển lần lặp,</span>

                <kbd class=""px-1.5 py-0.5 bg-slate-800 rounded border border-slate-700 text-white font-bold"">Esc</kbd>

                <span>thoát</span>

            </div>

        </footer>



    </div>



    <!-- JAVASCRIPT LOGIC & CÔNG THỨC TOÁN HỌC CHUẨN XÁC -->

    <script>

        const DATA = [

            { n: 0, title: ""Hình vuông ban đầu (n = 0)"", side: ""1"", newBlue: 0, totalBlue: 0, added: ""0"", sum: ""0"", sumDec: 0, remYellow: ""1"", yellowCells: 1 },

            { n: 1, title: ""Lần lặp thứ 1 (n = 1)"", side: ""\\frac{1}{3}"", newBlue: 1, totalBlue: 1, added: ""\\frac{1}{9}"", sum: ""\\frac{1}{9}"", sumDec: 1/9, remYellow: ""\\frac{8}{9}"", yellowCells: 8 },

            { n: 2, title: ""Lần lặp thứ 2 (n = 2)"", side: ""\\frac{1}{9}"", newBlue: 8, totalBlue: 9, added: ""\\frac{8}{81}"", sum: ""\\frac{17}{81}"", sumDec: 17/81, remYellow: ""\\frac{64}{81}"", yellowCells: 64 },

            { n: 3, title: ""Lần lặp thứ 3 (n = 3)"", side: ""\\frac{1}{27}"", newBlue: 64, totalBlue: 73, added: ""\\frac{64}{729}"", sum: ""\\frac{217}{729}"", sumDec: 217/729, remYellow: ""\\frac{512}{729}"", yellowCells: 512 },

            { n: 4, title: ""Lần lặp thứ 4 (n = 4)"", side: ""\\frac{1}{81}"", newBlue: 512, totalBlue: 585, added: ""\\frac{512}{6561}"", sum: ""\\frac{2233}{6561}"", sumDec: 2233/6561, remYellow: ""\\frac{4096}{6561}"", yellowCells: 4096 },

            { n: 5, title: ""Lần lặp thứ 5 (Yêu cầu đề)"", side: ""\\frac{1}{243}"", newBlue: 4096, totalBlue: 4681, added: ""\\frac{4096}{59049}"", sum: ""\\frac{26281}{59049}"", sumDec: 26281/59049, remYellow: ""\\frac{32768}{59049}"", yellowCells: 32768 }

        ];



        let state = {

            n: 1,

            zoomLevel: 1.0,

            autoPlayTimer: null,

            activeTab: 'guide',

            showGrid: true,             // Bật/tắt đường line chia ô

            showAreaResults: false,      // Ẩn diện tích & tổng diện tích theo yêu cầu

            problemBannerOpen: true,     // Trạng thái thanh đề bài

            isPresentationMode: false    // Trạng thái trình chiếu toàn màn hình

        };



        // Hàm render KaTeX trực tiếp

        function k(tex, display = false) {

            if (window.katex && window.katex.renderToString) {

                try {

                    return window.katex.renderToString(tex, { displayMode: display, throwOnError: false });

                } catch(e) {

                    return tex;

                }

            }

            return tex;

        }



        // Render toàn bộ math tĩnh

        function renderAllStaticMath() {

            document.querySelectorAll('.math-expr').forEach(el => {

                const expr = el.getAttribute('data-expr');

                if (expr) {

                    el.innerHTML = k(expr, false);

                }

            });



            if (window.renderMathInElement) {

                try {

                    window.renderMathInElement(document.body, {

                        delimiters: [

                            { left: '$$', right: '$$', display: true },

                            { left: '$', right: '$', display: false },

                            { left: '\\(', right: '\\)', display: false },

                            { left: '\\[', right: '\\]', display: true }

                        ],

                        ignoredTags: [""script"", ""noscript"", ""style"", ""textarea""],

                        throwOnError: false

                    });

                } catch(e) {}

            }

        }



        // Vẽ thảm Sierpinski Carpet lên bất kỳ canvas nào (chuẩn sắc nét theo kích thước thực)

        function drawSierpinski(canvas, n) {

            if (!canvas) return;

            const dpr = window.devicePixelRatio || 1;

            const rect = canvas.getBoundingClientRect();

            const size = rect.width > 0 ? rect.width : (canvas.width || 320);

            canvas.width = size * dpr;

            canvas.height = size * dpr;



            const ctx = canvas.getContext('2d');

            ctx.resetTransform();

            ctx.scale(dpr, dpr);



            // 1. Nền vàng

            ctx.fillStyle = '#fed7aa';

            ctx.fillRect(0, 0, size, size);



            // 2. Đệ quy vẽ ô vuông xanh chính giữa

            if (n >= 1) {

                function drawCell(x, y, cellSize, depth) {

                    if (depth > n) return;

                    const third = cellSize / 3;



                    // Ô giữa tô màu xanh

                    ctx.fillStyle = '#0ea5e9';

                    ctx.fillRect(x + third, y + third, third, third);



                    // Phân rã tiếp 8 ô vàng xung quanh

                    if (depth < n) {

                        for (let r = 0; r < 3; r++) {

                            for (let c = 0; c < 3; c++) {

                                if (r === 1 && c === 1) continue;

                                drawCell(x + c * third, y + r * third, third, depth + 1);

                            }

                        }

                    }

                }

                drawCell(0, 0, size, 1);

            }



            // 3. ĐƯỜNG LINE CHIA Ô VUÔNG (CẢ KHI n=0 ĐỂ THỂ HIỆN BƯỚC CHIA 9)

            if (state.showGrid) {

                ctx.save();

                const gridDivisions = Math.max(3, Math.pow(3, n));

                

                if (gridDivisions <= 81) {

                    const step = size / gridDivisions;

                    ctx.beginPath();

                    

                    if (n === 0) {

                        ctx.strokeStyle = '#d97706';

                        ctx.lineWidth = 1.3;

                        ctx.setLineDash([5, 4]); // Nét đứt rõ ràng biểu thị chia 9 ở bước đầu

                    } else {

                        ctx.strokeStyle = 'rgba(2, 132, 199, 0.6)';

                        ctx.lineWidth = gridDivisions <= 9 ? 1.1 : 0.65;

                        ctx.setLineDash([]);

                    }



                    for (let i = 1; i < gridDivisions; i++) {

                        const pos = Math.round(i * step);

                        // Kẻ dọc

                        ctx.moveTo(pos, 0);

                        ctx.lineTo(pos, size);

                        // Kẻ ngang

                        ctx.moveTo(0, pos);

                        ctx.lineTo(size, pos);

                    }

                    ctx.stroke();

                }

                ctx.restore();

            }



            // Viền ngoài sắc nét

            ctx.strokeStyle = '#0284c7';

            ctx.lineWidth = 2.0;

            ctx.strokeRect(0, 0, size, size);

        }



        // Bật/tắt thanh đề bài

        function toggleProblemBanner() {

            state.problemBannerOpen = !state.problemBannerOpen;

            const banner = document.getElementById('problemBannerSection');

            const txt = document.getElementById('textToggleProblem');

            if (state.problemBannerOpen) {

                banner.classList.remove('hidden');

                txt.textContent = ""Thu gọn đề bài"";

            } else {

                banner.classList.add('hidden');

                txt.textContent = ""Mở đề bài SGK"";

            }

        }



        // Bật/tắt đường line chia ô

        function toggleGridLines() {

            state.showGrid = !state.showGrid;

            

            // Cập nhật nút ở giao diện thường

            const btn = document.getElementById('btnToggleGrid');

            const txt = document.getElementById('textToggleGrid');

            if (state.showGrid) {

                btn.className = ""px-2 py-0.5 rounded border border-sky-300 bg-sky-50 text-sky-800 font-semibold text-[11px] flex items-center gap-1 hover:bg-sky-100 transition shadow-2xs"";

                txt.textContent = ""Lưới: Bật"";

            } else {

                btn.className = ""px-2 py-0.5 rounded border border-slate-300 bg-slate-100 text-slate-600 font-semibold text-[11px] flex items-center gap-1 hover:bg-slate-200 transition shadow-2xs"";

                txt.textContent = ""Lưới: Tắt"";

            }



            // Cập nhật nút ở chế độ trình chiếu

            const presGridTxt = document.getElementById('presTextGrid');

            if (presGridTxt) {

                presGridTxt.textContent = state.showGrid ? ""Lưới: Bật"" : ""Lưới: Tắt"";

            }



            renderAllCanvases();

        }



        // Bật/tắt ẩn hiện diện tích (u_n, S_n)

        function toggleAreaResults() {

            state.showAreaResults = !state.showAreaResults;

            const btn = document.getElementById('btnToggleArea');

            const txt = document.getElementById('textToggleArea');

            const icon = document.getElementById('iconToggleArea');

            

            if (state.showAreaResults) {

                btn.className = ""px-2 py-0.5 rounded border border-emerald-300 bg-emerald-50 text-emerald-900 font-semibold text-[11px] flex items-center gap-1 hover:bg-emerald-100 transition shadow-2xs"";

                txt.textContent = ""Đang hiện diện tích"";

                icon.className = ""fa-solid fa-eye text-[10px]"";

            } else {

                btn.className = ""px-2 py-0.5 rounded border border-amber-300 bg-amber-50 text-amber-900 font-semibold text-[11px] flex items-center gap-1 hover:bg-amber-100 transition shadow-2xs"";

                txt.textContent = ""Đang ẩn diện tích"";

                icon.className = ""fa-solid fa-eye-slash text-[10px]"";

            }

            updateUI();

        }



        // Điều khiển Zoom tự do

        function changeZoom(delta) {

            state.zoomLevel = Math.max(0.5, Math.min(2.5, Math.round((state.zoomLevel + delta) * 100) / 100));

            applyZoom();

        }



        function resetZoom() {

            state.zoomLevel = 1.0;

            applyZoom();

        }



        function applyZoom() {

            const baseSize = 320;

            const currentSize = Math.round(baseSize * state.zoomLevel);

            const box = document.getElementById('canvasContainerBox');

            box.style.width = currentSize + 'px';

            box.style.height = currentSize + 'px';

            document.getElementById('zoomPercentLabel').textContent = Math.round(state.zoomLevel * 100) + '%';

            

            renderAllCanvases();

        }



        // Vẽ lại cả 2 canvas (thường và trình chiếu)

        function renderAllCanvases() {

            const canvasMain = document.getElementById('carpetCanvas');

            drawSierpinski(canvasMain, state.n);



            if (state.isPresentationMode) {

                const canvasPres = document.getElementById('presentationCanvas');

                drawSierpinski(canvasPres, state.n);

            }

        }



        // Mở chế độ trình chiếu toàn màn hình

        function openPresentationMode() {

            state.isPresentationMode = true;

            const overlay = document.getElementById('presentationOverlay');

            overlay.classList.remove('hidden');



            // Cố gắng mở full màn hình trình duyệt

            if (document.documentElement.requestFullscreen && !document.fullscreenElement) {

                document.documentElement.requestFullscreen().catch(() => {});

            }



            updatePresentationUI();

            setTimeout(renderAllCanvases, 60);

        }



        // Thoát chế độ trình chiếu

        function closePresentationMode() {

            state.isPresentationMode = false;

            const overlay = document.getElementById('presentationOverlay');

            overlay.classList.add('hidden');



            if (document.fullscreenElement && document.exitFullscreen) {

                document.exitFullscreen().catch(() => {});

            }



            renderAllCanvases();

        }



        // Cập nhật giao diện Trình chiếu

        function updatePresentationUI() {

            const n = state.n;

            const d = DATA[n];



            // Tiêu đề & badge

            document.getElementById('presBadgeN').textContent = `Lần n = ${n}`;

            document.getElementById('presTitle').textContent = d.title;



            // Nút lùi/tiến trong trình chiếu

            document.getElementById('presBtnPrev').disabled = (n === 0);

            document.getElementById('presBtnNext').disabled = (n === 5);



            // Chấm chọn nhanh n = 0..5 trong trình chiếu

            const container = document.getElementById('presDotsContainer');

            container.innerHTML = '';

            for (let i = 0; i <= 5; i++) {

                const b = document.createElement('button');

                const isActive = (n === i);

                b.className = `w-7 h-7 sm:w-8 sm:h-8 rounded-lg font-mono font-extrabold text-xs sm:text-sm flex items-center justify-center transition ${

                    isActive ? 'bg-sky-500 text-white shadow-lg scale-110' : 'bg-slate-800 text-slate-300 hover:bg-slate-700'

                }`;

                b.textContent = i;

                b.onclick = () => jumpToN(i);

                container.appendChild(b);

            }



            // Footer info

            document.getElementById('presYellowText').textContent = `Vàng còn: ${d.yellowCells.toLocaleString('vi-VN')} ô`;

            document.getElementById('presBlueText').textContent = `Xanh đã tô: ${d.totalBlue.toLocaleString('vi-VN')} ô`;



            // Nút tự động

            const autoBtn = document.getElementById('presBtnAuto');

            const autoIcon = document.getElementById('presIconPlay');

            const autoTxt = document.getElementById('presTextPlay');

            if (state.autoPlayTimer) {

                autoBtn.className = ""px-3 py-1.5 rounded-xl bg-amber-600 hover:bg-amber-500 text-white font-bold text-xs sm:text-sm flex items-center gap-1.5 transition shadow-sm"";

                autoIcon.className = ""fa-solid fa-pause text-xs"";

                autoTxt.textContent = ""Tạm dừng"";

            } else {

                autoBtn.className = ""px-3 py-1.5 rounded-xl bg-sky-600 hover:bg-sky-500 text-white font-bold text-xs sm:text-sm flex items-center gap-1.5 transition shadow-sm"";

                autoIcon.className = ""fa-solid fa-play text-xs"";

                autoTxt.textContent = ""Tự động"";

            }

        }



        // Cập nhật giao diện toàn diện

        function updateUI() {

            const n = state.n;

            const d = DATA[n];



            // 1. Nút lùi/tiến

            document.getElementById('btnPrev').disabled = (n === 0);

            document.getElementById('btnNext').disabled = (n === 5);



            // 2. Chấm hiển thị n

            renderDots();



            // 3. Tiêu đề ngoài hình

            document.getElementById('badgeCurrentN').textContent = `Lần n = ${n}`;

            document.getElementById('labelSubTitle').textContent = d.title;



            // 4. Bốn thẻ số đo (RENDER CHUẨN KATEX + HỖ TRỢ ẨN HIỆN)

            document.getElementById('metricSide').innerHTML = k(`a_${n} = ${d.side}`, false);

            document.getElementById('metricNewSquares').textContent = d.newBlue.toLocaleString('vi-VN') + ' ô';



            const elAdded = document.getElementById('metricAddedArea');

            const elTotal = document.getElementById('metricTotalArea');

            const elBarBlue = document.getElementById('barTextBlue');

            const elBarYellow = document.getElementById('barTextYellow');

            const progressBar = document.getElementById('areaProgressBar');



            if (state.showAreaResults) {

                elAdded.innerHTML = k(`u_${n} = ${d.added}`, false);

                elTotal.innerHTML = k(`S_${n} = ${d.sum}`, false);



                const bluePct = (d.sumDec * 100).toFixed(2);

                const yellowPct = ((1 - d.sumDec) * 100).toFixed(2);

                elBarBlue.innerHTML = `Xanh: ${bluePct}% (${k(d.sum, false)})`;

                elBarYellow.innerHTML = `Vàng: ${yellowPct}% (${k(d.remYellow, false)})`;

                progressBar.style.width = `${bluePct}%`;

            } else {

                elAdded.innerHTML = `<span class=""inline-block px-2 py-0.5 rounded bg-emerald-100 text-emerald-800 text-[11px] font-bold"">??? (Bấm hiện)</span>`;

                elTotal.innerHTML = `<span class=""inline-block px-2 py-0.5 rounded bg-amber-100 text-amber-800 text-[11px] font-bold"">??? (Bấm hiện)</span>`;

                elBarBlue.innerHTML = `<span class=""text-slate-500 italic"">Đang ẩn kết quả diện tích để HS tự giải</span>`;

                elBarYellow.innerHTML = `<button onclick=""toggleAreaResults()"" class=""text-amber-800 font-bold underline hover:text-amber-900 text-xs"">Hiện kết quả</button>`;

                progressBar.style.width = `0%`;

            }



            // 5. Highlight dòng bảng

            highlightTableRow(n);



            // 6. Mở accordion tương ứng ở Tab Gợi Ý

            if (n >= 1 && n <= 5) {

                highlightStepCard(n);

            }



            // 7. Đồng bộ sang giao diện Trình chiếu (nếu đang mở)

            if (state.isPresentationMode) {

                updatePresentationUI();

            }



            // 8. Vẽ Canvas

            renderAllCanvases();

        }



        function renderDots() {

            const container = document.getElementById('dotsContainer');

            container.innerHTML = '';

            for (let i = 0; i <= 5; i++) {

                const btn = document.createElement('button');

                const isActive = (state.n === i);

                btn.className = `w-5 h-5 sm:w-6 sm:h-6 rounded-md font-mono font-bold text-xs flex items-center justify-center transition ${

                    isActive ? 'bg-sky-600 text-white shadow-xs' : 'bg-white border border-slate-200 text-slate-600 hover:bg-slate-100'

                }`;

                btn.textContent = i;

                btn.title = `Xem lần lặp n = ${i}`;

                btn.onclick = () => jumpToN(i);

                container.appendChild(btn);

            }

        }



        function stepIteration(delta) {

            const next = state.n + delta;

            if (next >= 0 && next <= 5) {

                state.n = next;

                updateUI();

            }

        }



        function jumpToN(targetN) {

            state.n = targetN;

            updateUI();

        }



        function toggleAutoPlay() {

            if (state.autoPlayTimer) {

                clearInterval(state.autoPlayTimer);

                state.autoPlayTimer = null;

                document.getElementById('textPlay').textContent = 'Tự động';

                document.getElementById('iconPlay').className = 'fa-solid fa-play text-[10px]';

                document.getElementById('btnAutoPlay').className = 'px-2.5 py-1.5 rounded-lg bg-sky-600 hover:bg-sky-700 text-white font-semibold text-xs flex items-center gap-1 transition shadow-2xs';

            } else {

                if (state.n >= 5) state.n = 0;

                updateUI();

                document.getElementById('textPlay').textContent = 'Tạm dừng';

                document.getElementById('iconPlay').className = 'fa-solid fa-pause text-[10px]';

                document.getElementById('btnAutoPlay').className = 'px-2.5 py-1.5 rounded-lg bg-amber-600 hover:bg-amber-700 text-white font-semibold text-xs flex items-center gap-1 transition shadow-2xs';



                state.autoPlayTimer = setInterval(() => {

                    if (state.n < 5) {

                        state.n++;

                        updateUI();

                    } else {

                        toggleAutoPlay();

                    }

                }, 2200);

            }

            if (state.isPresentationMode) updatePresentationUI();

        }



        function toggleAccordion(id) {

            const body = document.getElementById(`accBody-${id}`);

            const icon = document.getElementById(`accIcon-${id}`);

            if (body.classList.contains('hidden')) {

                body.classList.remove('hidden');

                icon.style.transform = 'rotate(180deg)';

                renderAllStaticMath();

            } else {

                body.classList.add('hidden');

                icon.style.transform = 'rotate(0deg)';

            }

        }



        function toggleAllAccordions(open) {

            for (let i = 1; i <= 5; i++) {

                const body = document.getElementById(`accBody-step${i}`);

                const icon = document.getElementById(`accIcon-step${i}`);

                if (body && icon) {

                    if (open) {

                        body.classList.remove('hidden');

                        icon.style.transform = 'rotate(180deg)';

                    } else {

                        body.classList.add('hidden');

                        icon.style.transform = 'rotate(0deg)';

                    }

                }

            }

            if (open) renderAllStaticMath();

        }



        function toggleBox(boxId) {

            const box = document.getElementById(`box-${boxId}`);

            if (!box) return;



            const isHint = boxId.startsWith('hint');

            const stepNum = boxId.split('-')[1];

            const btnText = document.getElementById(isHint ? `hintBtnText-${stepNum}` : `ansBtnText-${stepNum}`);



            if (box.classList.contains('hidden')) {

                box.classList.remove('hidden');

                renderAllStaticMath();

                if (btnText) btnText.textContent = isHint ? 'Ẩn gợi ý' : 'Ẩn công thức';

            } else {

                box.classList.add('hidden');

                if (btnText) btnText.textContent = isHint ? 'Hiện gợi ý trả lời' : 'Hiện kết luận & công thức';

            }

        }



        function highlightStepCard(n) {

            for (let i = 1; i <= 5; i++) {

                const card = document.getElementById(`stepCard-${i}`);

                if (card) {

                    if (i === n) {

                        card.classList.add('border-sky-500', 'ring-2', 'ring-sky-200');

                        const body = document.getElementById(`accBody-step${i}`);

                        const icon = document.getElementById(`accIcon-step${i}`);

                        if (body && body.classList.contains('hidden')) {

                            body.classList.remove('hidden');

                            if (icon) icon.style.transform = 'rotate(180deg)';

                            renderAllStaticMath();

                        }

                    } else {

                        card.classList.remove('border-sky-500', 'ring-2', 'ring-sky-200');

                    }

                }

            }

        }



        function selectTab(tabKey) {

            state.activeTab = tabKey;

            ['guide', 'solution', 'table'].forEach(key => {

                const nav = document.getElementById(`navBtn-${key}`);

                const content = document.getElementById(`tabContent-${key}`);

                if (key === tabKey) {

                    nav.className = ""py-1.5 px-2 rounded-lg text-center transition flex items-center justify-center gap-1.5 bg-white shadow-2xs text-sky-800 font-bold border border-slate-200"";

                    content.classList.remove('hidden');

                    renderAllStaticMath();

                } else {

                    nav.className = ""py-1.5 px-2 rounded-lg text-center transition flex items-center justify-center gap-1.5 text-slate-600 hover:text-slate-900"";

                    content.classList.add('hidden');

                }

            });

        }



        function populateTable() {

            const tbody = document.getElementById('tableBodyProgression');

            tbody.innerHTML = '';

            

            const tableFractions = [

                { side: ""1"", added: ""0"", sum: ""0"" },

                { side: ""\\dfrac{1}{3}"", added: ""\\dfrac{1}{9}"", sum: ""\\dfrac{1}{9}"" },

                { side: ""\\dfrac{1}{9}"", added: ""\\dfrac{8}{81}"", sum: ""\\dfrac{17}{81}"" },

                { side: ""\\dfrac{1}{27}"", added: ""\\dfrac{64}{729}"", sum: ""\\dfrac{217}{729}"" },

                { side: ""\\dfrac{1}{81}"", added: ""\\dfrac{512}{6561}"", sum: ""\\dfrac{2233}{6561}"" },

                { side: ""\\dfrac{1}{243}"", added: ""\\dfrac{4096}{59049}"", sum: ""\\dfrac{26281}{59049}"" }

            ];



            DATA.forEach(d => {

                const tf = tableFractions[d.n];

                const tr = document.createElement('tr');

                tr.id = `row-n-${d.n}`;

                tr.className = ""cursor-pointer hover:bg-sky-50 transition border-b border-slate-100"";

                tr.onclick = () => jumpToN(d.n);

                

                tr.innerHTML = `

                    <td class=""p-3 sm:p-3.5 text-center font-bold text-slate-900 text-sm sm:text-base"">n = ${d.n}</td>

                    <td class=""p-3 sm:p-3.5 text-center text-sm sm:text-base font-semibold text-slate-800"">${k(tf.side, false)}</td>

                    <td class=""p-3 sm:p-3.5 text-center text-sky-700 font-extrabold text-sm sm:text-base"">${d.newBlue.toLocaleString('vi-VN')}</td>

                    <td class=""p-3 sm:p-3.5 text-center text-emerald-800 font-bold text-sm sm:text-base"">${k(tf.added, false)}</td>

                    <td class=""p-3 sm:p-3.5 text-center font-extrabold text-slate-950 text-sm sm:text-base"">${k(tf.sum, false)}</td>

                    <td class=""p-3 sm:p-3.5 text-right text-slate-900 font-extrabold text-sm sm:text-base"">${(d.sumDec * 100).toFixed(2)}%</td>

                `;

                tbody.appendChild(tr);

            });

        }



        function highlightTableRow(n) {

            for (let i = 0; i <= 5; i++) {

                const row = document.getElementById(`row-n-${i}`);

                if (row) {

                    if (i === n) {

                        row.className = ""cursor-pointer bg-sky-100/90 font-bold border-l-4 border-l-sky-600 shadow-2xs"";

                    } else {

                        row.className = ""cursor-pointer hover:bg-sky-50 transition border-b border-slate-100"";

                    }

                }

            }

        }



        function setupHoverInspector() {

            const canvas = document.getElementById('carpetCanvas');

            const info = document.getElementById('hoverInspector');



            canvas.addEventListener('mousemove', (e) => {

                const rect = canvas.getBoundingClientRect();

                const u = Math.max(0, Math.min(0.99999, (e.clientX - rect.left) / rect.width));

                const v = Math.max(0, Math.min(0.99999, (e.clientY - rect.top) / rect.height));



                let blueAt = 0;

                let cu = u, cv = v;

                for (let step = 1; step <= state.n; step++) {

                    const col = Math.floor(cu * 3);

                    const row = Math.floor(cv * 3);

                    if (col === 1 && row === 1) {

                        blueAt = step;

                        break;

                    }

                    cu = (cu * 3) % 1;

                    cv = (cv * 3) % 1;

                }



                if (blueAt > 0) {

                    info.innerHTML = `Ô <strong class=""text-sky-700"">XANH</strong> tô tại lần <strong>${blueAt}</strong> (Cạnh 1/${Math.pow(3, blueAt)})`;

                } else {

                    info.innerHTML = `Vùng <strong class=""text-amber-700"">VÀNG</strong> còn lại (Sẽ chia tiếp ở lần sau)`;

                }

            });



            canvas.addEventListener('mouseleave', () => {

                info.innerHTML = `Rê chuột lên hình để soi ô con`;

            });

        }



        // Hỗ trợ cuộn chuột kèm phím Ctrl để zoom

        document.getElementById('canvasViewportArea').addEventListener('wheel', (e) => {

            if (e.ctrlKey) {

                e.preventDefault();

                changeZoom(e.deltaY < 0 ? 0.15 : -0.15);

            }

        }, { passive: false });



        // Phím tắt bàn phím

        window.addEventListener('keydown', (e) => {

            if (e.key === 'ArrowRight') stepIteration(1);

            if (e.key === 'ArrowLeft') stepIteration(-1);

            if (e.key === 'Escape' && state.isPresentationMode) closePresentationMode();

            if (e.key === ' ' && state.isPresentationMode) {

                e.preventDefault();

                toggleAutoPlay();

            }

        });



        // Khởi động khi tải trang

        function initApp() {

            renderAllStaticMath();

            populateTable();

            updateUI();

            setupHoverInspector();

            

            const acc1 = document.getElementById('accBody-step1');

            const icon1 = document.getElementById('accIcon-step1');

            if (acc1) acc1.classList.remove('hidden');

            if (icon1) icon1.style.transform = 'rotate(180deg)';



            setTimeout(renderAllStaticMath, 250);

            setTimeout(populateTable, 250);

        }



        window.onload = initApp;



        window.addEventListener('resize', () => {

            renderAllCanvases();

        });

    </script>

</body>

</html>"
            };
        }
    }
}
