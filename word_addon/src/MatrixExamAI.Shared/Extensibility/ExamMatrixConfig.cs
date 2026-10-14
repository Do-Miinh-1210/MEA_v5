using System;
using System.Collections.Generic;

namespace MatrixExamAI.Shared.Extensibility
{
    /// <summary>
    /// Cấu hình khung Ma trận đề thi chuẩn Bộ Giáo dục & Đào tạo (Quyết định 764/QĐ-BGDĐT).
    /// </summary>
    public class ExamMatrixConfig
    {
        /// <summary>
        /// Tiêu đề kỳ thi hoặc mã đề (ví dụ: "Đề khảo sát chất lượng môn Toán 12 - Năm học 2025-2026").
        /// </summary>
        public string Title { get; set; } = "Đề thi khảo sát Toán học THPT";

        /// <summary>
        /// Môn học.
        /// </summary>
        public string Subject { get; set; } = "Toán";

        /// <summary>
        /// Khối lớp.
        /// </summary>
        public int Grade { get; set; } = 12;

        /// <summary>
        /// Thời gian làm bài tính bằng phút (mặc định 90 phút cho môn Toán).
        /// </summary>
        public int DurationMinutes { get; set; } = 90;

        /// <summary>
        /// Số câu Phần I: Trắc nghiệm nhiều phương án lựa chọn (Chuẩn BGD: 12 câu, 3.0 điểm).
        /// </summary>
        public int Part1Count { get; set; } = 12;

        /// <summary>
        /// Số câu Phần II: Trắc nghiệm Đúng/Sai (Chuẩn BGD: 4 câu, mỗi câu 4 ý, 4.0 điểm).
        /// </summary>
        public int Part2Count { get; set; } = 4;

        /// <summary>
        /// Số câu Phần III: Trắc nghiệm trả lời ngắn (Chuẩn BGD: 6 câu, 3.0 điểm).
        /// </summary>
        public int Part3Count { get; set; } = 6;

        /// <summary>
        /// Tổng số câu hỏi trong ma trận đề thi.
        /// </summary>
        public int TotalQuestions => Part1Count + Part2Count + Part3Count;

        /// <summary>
        /// Tỷ lệ phân bố mức độ nhận thức:
        /// "Nhận biết": 40%, "Thông hiểu": 30%, "Vận dụng": 20%, "Vận dụng cao": 10%.
        /// </summary>
        public Dictionary<string, int> CognitiveDistribution { get; set; } = new Dictionary<string, int>
        {
            { "Nhận biết", 40 },
            { "Thông hiểu", 30 },
            { "Vận dụng", 20 },
            { "Vận dụng cao", 10 }
        };

        /// <summary>
        /// Tỷ lệ phân bố câu hỏi theo từng chủ đề / chuyên đề kiến thức (%).
        /// </summary>
        public Dictionary<string, int> TopicDistribution { get; set; } = new Dictionary<string, int>();
    }

    /// <summary>
    /// Bản thảo đề thi gốc được sinh từ Ma trận câu hỏi.
    /// </summary>
    public class ExamDraftResult
    {
        public bool Success { get; set; }
        public string Title { get; set; } = string.Empty;
        public string Subject { get; set; } = "Toán";
        public int Grade { get; set; } = 12;
        public int DurationMinutes { get; set; } = 90;
        public List<QuestionItem> Part1Questions { get; set; } = new List<QuestionItem>();
        public List<QuestionItem> Part2Questions { get; set; } = new List<QuestionItem>();
        public List<QuestionItem> Part3Questions { get; set; } = new List<QuestionItem>();
        public int TotalSelectedQuestions => Part1Questions.Count + Part2Questions.Count + Part3Questions.Count;
        public string? ErrorMessage { get; set; }
    }

    /// <summary>
    /// Mã đề thi hoán vị (ví dụ: Mã đề 101, 102, 103, 104) sau khi trộn ma trận.
    /// </summary>
    public class ExamVariant
    {
        /// <summary>
        /// Mã đề thi (101, 102, 103...).
        /// </summary>
        public string ExamCode { get; set; } = "101";

        /// <summary>
        /// Danh sách câu hỏi của Phần I đã đảo thứ tự câu và thứ tự phương án A, B, C, D.
        /// </summary>
        public List<QuestionItem> Part1Questions { get; set; } = new List<QuestionItem>();

        /// <summary>
        /// Danh sách câu hỏi của Phần II đã đảo thứ tự câu và các ý a, b, c, d.
        /// </summary>
        public List<QuestionItem> Part2Questions { get; set; } = new List<QuestionItem>();

        /// <summary>
        /// Danh sách câu hỏi của Phần III đã đảo thứ tự câu.
        /// </summary>
        public List<QuestionItem> Part3Questions { get; set; } = new List<QuestionItem>();

        /// <summary>
        /// Bảng đáp án trắc nghiệm chuẩn của mã đề (Key: Số thứ tự câu, Value: Đáp án đúng).
        /// </summary>
        public Dictionary<int, string> AnswerKey { get; set; } = new Dictionary<int, string>();
    }
}
