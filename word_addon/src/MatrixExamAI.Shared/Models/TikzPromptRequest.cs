namespace MatrixExamAI.Shared.Models
{
    /// <summary>
    /// Yêu cầu sinh mã hoặc tối ưu mã TikZ gửi đến AI Engine.
    /// </summary>
    public class TikzPromptRequest
    {
        /// <summary>
        /// Nội dung prompt hoặc mô tả hình vẽ toán học cần sinh.
        /// </summary>
        public string Prompt { get; set; } = string.Empty;

        /// <summary>
        /// Dữ liệu ảnh dán từ clipboard (Base64), dùng cho multimodal vision inference.
        /// </summary>
        public string? ImageBase64 { get; set; }

        /// <summary>
        /// Định dạng MIME của ảnh đính kèm (mặc định image/png).
        /// </summary>
        public string ImageMimeType { get; set; } = "image/png";

        /// <summary>
        /// Phân loại hình vẽ toán học để áp dụng các chip gợi ý và quy tắc chuyên biệt.
        /// </summary>
        public DiagramType DiagramType { get; set; } = DiagramType.Custom;

        /// <summary>
        /// Yêu cầu bổ sung của người dùng (ví dụ: đổi màu, thêm tiệm cận, ẩn hệ trục).
        /// </summary>
        public string? ExtraPrompt { get; set; }

        /// <summary>
        /// Bật/tắt chú thích tiêu đề nhóm lệnh trong mã TikZ (% ĐỒ THỊ, % HỆ TRỤC).
        /// </summary>
        public bool EnableNotes { get; set; } = true;

        /// <summary>
        /// Bỏ khung viền ngoài đối với bảng biến thiên tkz-tab (nocadre=true).
        /// </summary>
        public bool BbtNoFrame { get; set; } = false;

        /// <summary>
        /// Mã ví dụ mẫu từ thư viện tri thức để AI học phong cách.
        /// </summary>
        public string? ReferenceExamples { get; set; }

        /// <summary>
        /// Chỉ thị hệ thống ghi đè nếu muốn tùy biến sâu.
        /// </summary>
        public string? SystemInstruction { get; set; }

        /// <summary>
        /// Tên model chỉ định (mặc định gemini-3.8-flash).
        /// </summary>
        public string? ModelOverride { get; set; }

        /// <summary>
        /// Nhiệt độ lấy mẫu (mặc định 0.2 cho độ chuẩn xác cao).
        /// </summary>
        public double Temperature { get; set; } = 0.2;

        /// <summary>
        /// Giới hạn token đầu ra (mặc định 8192).
        /// </summary>
        public int MaxOutputTokens { get; set; } = 8192;
    }
}
