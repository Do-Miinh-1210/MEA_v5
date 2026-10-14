namespace MatrixExamAI.Shared.Validation
{
    /// <summary>
    /// Bản ghi phát hiện lỗi hoặc cảnh báo cú pháp mã TikZ.
    /// </summary>
    public class ValidationIssue
    {
        public IssueSeverity Severity { get; set; }
        public int Line { get; set; }
        public string Message { get; set; } = string.Empty;
        public string Rule { get; set; } = string.Empty;
        public bool Fixable { get; set; }

        public ValidationIssue() { }

        public ValidationIssue(IssueSeverity severity, int line, string message, string rule, bool fixable = false)
        {
            Severity = severity;
            Line = line;
            Message = message;
            Rule = rule;
            Fixable = fixable;
        }

        public override string ToString()
        {
            string loc = Line > 0 ? $"[Dòng {Line}]" : "[Toàn cục]";
            return $"{loc} [{Severity}] {Message} ({Rule})";
        }
    }
}
