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
    }
}
