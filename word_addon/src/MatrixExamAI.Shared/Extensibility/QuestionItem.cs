using System;
using System.Collections.Generic;

namespace MatrixExamAI.Shared.Extensibility
{
    /// <summary>
    /// Thực thể câu hỏi trong Ngân hàng câu hỏi SQLite MatrixExamAI (Phase 3).
    /// </summary>
    public class QuestionItem
    {
        /// <summary>
        /// Khóa chính tự tăng trong CSDL SQLite.
        /// </summary>
        public long Id { get; set; }

        /// <summary>
        /// Mã định danh câu hỏi (ví dụ: TOAN12_H1_001, BGD2026_01).
        /// </summary>
        public string QuestionCode { get; set; } = string.Empty;

        /// <summary>
        /// Môn học (Toán, Vật lý, Hóa học...).
        /// </summary>
        public string Subject { get; set; } = "Toán";

        /// <summary>
        /// Khối lớp học (10, 11, 12).
        /// </summary>
        public int Grade { get; set; } = 12;

        /// <summary>
        /// Chủ đề / chuyên đề kiến thức (ví dụ: Khảo sát hàm số, Hình học Oxyz).
        /// </summary>
        public string Topic { get; set; } = string.Empty;

        /// <summary>
        /// Mức độ nhận thức chuẩn Bộ GD&ĐT:
        /// "Nhận biết", "Thông hiểu", "Vận dụng", "Vận dụng cao".
        /// </summary>
        public string CognitiveLevel { get; set; } = "Thông hiểu";

        /// <summary>
        /// Định dạng câu hỏi khảo thí:
        /// - MultipleChoice4: Trắc nghiệm 4 lựa chọn (Phần I chuẩn BGD)
        /// - TrueFalse4: Đúng/Sai 4 ý a,b,c,d (Phần II chuẩn BGD)
        /// - ShortAnswer: Trả lời ngắn (Phần III chuẩn BGD)
        /// - Essay: Tự luận
        /// </summary>
        public string QuestionType { get; set; } = "MultipleChoice4";

        /// <summary>
        /// Nội dung câu hỏi (chứa công thức toán LaTeX $...$).
        /// </summary>
        public string Content { get; set; } = string.Empty;

        /// <summary>
        /// Danh sách 4 phương án lựa chọn A, B, C, D (dành cho MultipleChoice4 hoặc TrueFalse4).
        /// </summary>
        public Dictionary<string, string> Options { get; set; } = new Dictionary<string, string>();

        /// <summary>
        /// Đáp án đúng (ví dụ: "A", "Đ,S,Đ,S" hoặc kết quả số "12.5").
        /// </summary>
        public string CorrectAnswer { get; set; } = string.Empty;

        /// <summary>
        /// Hướng dẫn giải chi tiết sư phạm.
        /// </summary>
        public string Explanation { get; set; } = string.Empty;

        /// <summary>
        /// Mã nguồn hình vẽ TikZ đi kèm bài toán (nếu có).
        /// </summary>
        public string TikzCode { get; set; } = string.Empty;

        /// <summary>
        /// Danh sách đường dẫn file hoặc chuỗi Base64 của các hình ảnh đính kèm bài toán (kế thừa question_image từ MEA cũ).
        /// </summary>
        public List<string> Images { get; set; } = new List<string>();

        /// <summary>
        /// Nguồn gốc câu hỏi (ví dụ: Đề thi thử Chuyên KHTN 2026, Đề minh họa BGD).
        /// </summary>
        public string Source { get; set; } = string.Empty;

        /// <summary>
        /// Dữ liệu JSON thô mở rộng để tương thích với MEA v5.0 storage.
        /// </summary>
        public string RawDataJson { get; set; } = string.Empty;

        /// <summary>
        /// Thời điểm tạo câu hỏi.
        /// </summary>
        public DateTime CreatedAt { get; set; } = DateTime.UtcNow;

        /// <summary>
        /// Thời điểm cập nhật câu hỏi gần nhất.
        /// </summary>
        public DateTime UpdatedAt { get; set; } = DateTime.UtcNow;
    }
}
