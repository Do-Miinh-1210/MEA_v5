using System;
using System.Threading.Tasks;

namespace MatrixExamAI.WordAddIn.WordInterop
{
    public class TikzShapeSelectedEventArgs : EventArgs
    {
        public bool HasTikzShape { get; set; }
        public string TikzCode { get; set; } = string.Empty;
        public string ShapeTitle { get; set; } = string.Empty;
        public int ShapeId { get; set; }
    }

    public interface IWordDocumentService : IDisposable
    {
        Task<bool> InsertPictureAtSelectionAsync(string imagePath, string tikzCode);
        Task<bool> UpdateSelectedPictureAsync(string imagePath, string newTikzCode);
        Task<string> GetSelectedShapeTikzCodeAsync();
        Task<string> GetSelectionTextAsync();
        Task<bool> ReplaceSelectionTextAsync(string newText);
        Task<bool> InsertTextAfterSelectionAsync(string text);
        Task<bool> InsertOmmlAtSelectionAsync(string ommlXml);
        Task<int> ConvertAllLatexInDocumentAsync();
        Task<(bool success, int oleCount, string reportJson)> ScanMathTypeFormulasAsync(string? docxPath = null);
        Task<(bool success, int convertedCount, string outputPath, string reportJson)> ConvertMathTypeToOmmlAsync(string? docxPath = null);
        Task<bool> StandardizeDocumentFormattingAsync(string fontName = "Times New Roman", float fontSize = 12f, float lineSpacing = 1.15f, bool entireDocument = false);
        Task<bool> InsertStandardizedExamAsync(System.Collections.Generic.List<MatrixExamAI.Shared.Extensibility.QuestionItem> questions, string fontName = "Times New Roman", float fontSize = 12f, float lineSpacing = 1.15f);

        event EventHandler<TikzShapeSelectedEventArgs>? TikzShapeSelected;
    }
}
