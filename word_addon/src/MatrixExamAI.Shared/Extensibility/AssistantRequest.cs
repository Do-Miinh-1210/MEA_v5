using System;
using System.Collections.Generic;

namespace MatrixExamAI.Shared.Extensibility
{
    /// <summary>
    /// Các chế độ xử lý tác vụ của Trợ lý AI Soạn thảo văn bản.
    /// </summary>
    public enum AssistantTaskType
    {
        /// <summary>
        /// Phân tích và sinh lời giải chi tiết từng bước cho câu hỏi toán học.
        /// </summary>
        ExplainQuestion,

        /// <summary>
        /// Viết lại/phát triển câu hỏi tương đương, thay đổi số liệu nhưng giữ nguyên cấu trúc.
        /// </summary>
        RewriteMathProblem,

        /// <summary>
        /// Tự động giải chi tiết và trình bày đáp án chuẩn mực Bộ GD&ĐT.
        /// </summary>
        GenerateSolution,

        /// <summary>
        /// Trợ lý soạn thảo tự do: gợi ý viết tiếp, tối ưu hóa diễn đạt và sửa lỗi chính tả.
        /// </summary>
        FreeformAuthoring,

        /// <summary>
        /// Chuẩn hóa ngôn ngữ đề thi và phát hiện các bẫy logic / phương án nhiễu.
        /// </summary>
        StandardizeLanguage
    }

    /// <summary>
    /// Yêu cầu gửi tới Trợ lý AI Soạn thảo văn bản Microsoft Word (Gemini 3.8 Flash).
    /// </summary>
    public class AssistantRequest
    {
        /// <summary>
        /// Loại tác vụ yêu cầu AI thực hiện.
        /// </summary>
        public AssistantTaskType TaskType { get; set; } = AssistantTaskType.ExplainQuestion;

        /// <summary>
        /// Đoạn văn bản hoặc câu hỏi đang được bôi đen/chọn trong tài liệu Word.
        /// </summary>
        public string SelectedText { get; set; } = string.Empty;

        /// <summary>
        /// Hướng dẫn hoặc prompt bổ sung từ người dùng (tùy chọn).
        /// </summary>
        public string Prompt { get; set; } = string.Empty;

        /// <summary>
        /// Bối cảnh văn bản xung quanh (các đoạn văn trước/sau) để AI nắm bắt ngữ cảnh.
        /// </summary>
        public string Context { get; set; } = string.Empty;

        /// <summary>
        /// Môn học (Toán, Vật lý, Hóa học, Sinh học...). Mặc định là "Toán".
        /// </summary>
        public string Subject { get; set; } = "Toán";

        /// <summary>
        /// Khối lớp học (10, 11, 12).
        /// </summary>
        public int? TargetGrade { get; set; } = 12;

        /// <summary>
        /// Có yêu cầu AI gợi ý sinh kèm mã TikZ minh họa hay không.
        /// </summary>
        public bool IncludeTikzSuggestion { get; set; } = true;

        /// <summary>
        /// Mô hình AI mục tiêu (ví dụ: gemini-3.8-flash).
        /// </summary>
        public string Model { get; set; } = "gemini-3.8-flash";
    }
}
