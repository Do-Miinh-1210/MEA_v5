using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Runtime.InteropServices;
using System.Text.Json;
using System.Text.RegularExpressions;
using System.Threading.Tasks;
using System.Windows.Forms;
using MatrixExamAI.WordAddIn.Ribbon;
using Word = Microsoft.Office.Interop.Word;

namespace MatrixExamAI.WordAddIn.WordInterop
{
    public class WordDocumentService : IWordDocumentService
    {
        private const string TagPrefix = "<!-- MatrixExamAI:TikZ:v5.0 -->";
        private const string TagSuffix = "<!-- END:TikZ -->";
        private const string DefaultTitle = "MatrixExamAI:TikZ";

        private readonly Word.Application _wordApp;
        private readonly Timer _debounceTimer;

        public event EventHandler<TikzShapeSelectedEventArgs>? TikzShapeSelected;

        public WordDocumentService(Word.Application wordApp)
        {
            _wordApp = wordApp ?? throw new ArgumentNullException(nameof(wordApp));

            _debounceTimer = new Timer
            {
                Interval = 150
            };
            _debounceTimer.Tick += OnDebounceTimerTick;

            _wordApp.WindowSelectionChange += OnWindowSelectionChange;
        }

        #region Selection Detection & Debounce

        private void OnWindowSelectionChange(Word.Selection sel)
        {
            // Reset debounce timer
            _debounceTimer.Stop();
            _debounceTimer.Start();
        }

        private void OnDebounceTimerTick(object? sender, EventArgs e)
        {
            _debounceTimer.Stop();
            InspectCurrentSelection();
        }

        public void InspectCurrentSelection()
        {
            Word.Selection? sel = null;
            try
            {
                sel = _wordApp.Selection;
                if (sel == null) return;

                // 1. Check InlineShapes
                if (sel.Type == Word.WdSelectionType.wdSelectionInlineShape && sel.InlineShapes.Count > 0)
                {
                    Word.InlineShape inlineShape = sel.InlineShapes[1];
                    try
                    {
                        string title = inlineShape.Title ?? string.Empty;
                        string altText = inlineShape.AlternativeText ?? string.Empty;

                        if (IsMatrixExamAiShape(title, altText))
                        {
                            string tikzCode = ExtractTikzCode(altText);
                            NotifySelection(true, tikzCode, title, 1);
                            return;
                        }
                    }
                    finally
                    {
                        Marshal.ReleaseComObject(inlineShape);
                    }
                }
                // 2. Check Floating Shapes (ShapeRange)
                else if (sel.ShapeRange != null && sel.ShapeRange.Count > 0)
                {
                    Word.Shape shape = sel.ShapeRange[1];
                    try
                    {
                        string title = shape.Title ?? string.Empty;
                        string altText = shape.AlternativeText ?? string.Empty;

                        if (IsMatrixExamAiShape(title, altText))
                        {
                            string tikzCode = ExtractTikzCode(altText);
                            NotifySelection(true, tikzCode, title, 1);
                            return;
                        }
                    }
                    finally
                    {
                        Marshal.ReleaseComObject(shape);
                    }
                }

                // Deselected
                NotifySelection(false, string.Empty, string.Empty, 0);
            }
            catch (COMException ex)
            {
                // Word may be busy with a modal dialog or print preview
                System.Diagnostics.Debug.WriteLine($"[WordDocumentService] COM Exception in InspectSelection: {ex.Message}");
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"[WordDocumentService] Unexpected error: {ex.Message}");
            }
            finally
            {
                if (sel != null)
                {
                    Marshal.ReleaseComObject(sel);
                }
            }
        }

        private void NotifySelection(bool hasTikz, string tikzCode, string title, int shapeId)
        {
            RibbonController.Instance?.SetTikZSelectionState(hasTikz);
            TikzShapeSelected?.Invoke(this, new TikzShapeSelectedEventArgs
            {
                HasTikzShape = hasTikz,
                TikzCode = tikzCode,
                ShapeTitle = title,
                ShapeId = shapeId
            });
        }

        #endregion

        #region Picture Insertion & Update

        public Task<bool> InsertPictureAtSelectionAsync(string imagePath, string tikzCode)
        {
            return Task.Run(() =>
            {
                Word.Selection? sel = null;
                Word.InlineShapes? inlineShapes = null;
                Word.InlineShape? newShape = null;

                try
                {
                    string resolvedImagePath = ResolveImagePath(imagePath);
                    if (!File.Exists(resolvedImagePath))
                    {
                        throw new FileNotFoundException("Image file not found for insertion into Word.", resolvedImagePath);
                    }

                    sel = _wordApp.Selection;
                    if (sel == null) return false;

                    object linkToFile = false;
                    object saveWithDocument = true;
                    object range = sel.Range;

                    inlineShapes = sel.InlineShapes;
                    newShape = inlineShapes.AddPicture(
                        resolvedImagePath,
                        ref linkToFile,
                        ref saveWithDocument,
                        ref range
                    );

                    newShape.Title = DefaultTitle;
                    newShape.AlternativeText = FormatTikzMetadata(tikzCode);

                    // Select the newly inserted shape
                    newShape.Select();

                    // Notify ribbon and listeners
                    NotifySelection(true, tikzCode, DefaultTitle, 1);

                    return true;
                }
                finally
                {
                    if (newShape != null) Marshal.ReleaseComObject(newShape);
                    if (inlineShapes != null) Marshal.ReleaseComObject(inlineShapes);
                    if (sel != null) Marshal.ReleaseComObject(sel);
                }
            });
        }

        public Task<bool> UpdateSelectedPictureAsync(string imagePath, string newTikzCode)
        {
            return Task.Run(() =>
            {
                Word.Selection? sel = null;
                Word.Range? targetRange = null;
                Word.InlineShape? newShape = null;

                try
                {
                    string resolvedImagePath = ResolveImagePath(imagePath);
                    if (!File.Exists(resolvedImagePath))
                    {
                        throw new FileNotFoundException("Updated image file not found.", resolvedImagePath);
                    }

                    sel = _wordApp.Selection;
                    if (sel == null) return false;

                    // Update InlineShape
                    if (sel.Type == Word.WdSelectionType.wdSelectionInlineShape && sel.InlineShapes.Count > 0)
                    {
                        Word.InlineShape oldShape = sel.InlineShapes[1];
                        targetRange = oldShape.Range;
                        oldShape.Delete();
                        Marshal.ReleaseComObject(oldShape);

                        object linkToFile = false;
                        object saveWithDocument = true;
                        object rangeObj = targetRange;

                        newShape = targetRange.InlineShapes.AddPicture(
                            resolvedImagePath,
                            ref linkToFile,
                            ref saveWithDocument,
                            ref rangeObj
                        );

                        newShape.Title = DefaultTitle;
                        newShape.AlternativeText = FormatTikzMetadata(newTikzCode);
                        newShape.Select();

                        NotifySelection(true, newTikzCode, DefaultTitle, 1);
                        return true;
                    }
                    // Update ShapeRange
                    else if (sel.ShapeRange != null && sel.ShapeRange.Count > 0)
                    {
                        Word.Shape oldShape = sel.ShapeRange[1];
                        targetRange = oldShape.Anchor;
                        oldShape.Delete();
                        Marshal.ReleaseComObject(oldShape);

                        object linkToFile = false;
                        object saveWithDocument = true;
                        object rangeObj = targetRange;

                        newShape = targetRange.InlineShapes.AddPicture(
                            resolvedImagePath,
                            ref linkToFile,
                            ref saveWithDocument,
                            ref rangeObj
                        );

                        newShape.Title = DefaultTitle;
                        newShape.AlternativeText = FormatTikzMetadata(newTikzCode);
                        newShape.Select();

                        NotifySelection(true, newTikzCode, DefaultTitle, 1);
                        return true;
                    }

                    return false;
                }
                finally
                {
                    if (newShape != null) Marshal.ReleaseComObject(newShape);
                    if (targetRange != null) Marshal.ReleaseComObject(targetRange);
                    if (sel != null) Marshal.ReleaseComObject(sel);
                }
            });
        }

        public Task<string> GetSelectedShapeTikzCodeAsync()
        {
            return Task.Run(() =>
            {
                Word.Selection? sel = null;
                try
                {
                    sel = _wordApp.Selection;
                    if (sel == null) return string.Empty;

                    if (sel.Type == Word.WdSelectionType.wdSelectionInlineShape && sel.InlineShapes.Count > 0)
                    {
                        Word.InlineShape shape = sel.InlineShapes[1];
                        try
                        {
                            return ExtractTikzCode(shape.AlternativeText ?? string.Empty);
                        }
                        finally
                        {
                            Marshal.ReleaseComObject(shape);
                        }
                    }
                    else if (sel.ShapeRange != null && sel.ShapeRange.Count > 0)
                    {
                        Word.Shape shape = sel.ShapeRange[1];
                        try
                        {
                            return ExtractTikzCode(shape.AlternativeText ?? string.Empty);
                        }
                        finally
                        {
                            Marshal.ReleaseComObject(shape);
                        }
                    }

                    return string.Empty;
                }
                finally
                {
                    if (sel != null) Marshal.ReleaseComObject(sel);
                }
            });
        }

        #endregion

        #region Text Operations

        public Task<string> GetSelectionTextAsync()
        {
            return Task.Run(() =>
            {
                Word.Selection? sel = null;
                try
                {
                    sel = _wordApp.Selection;
                    return sel?.Text ?? string.Empty;
                }
                finally
                {
                    if (sel != null) Marshal.ReleaseComObject(sel);
                }
            });
        }

        public Task<bool> ReplaceSelectionTextAsync(string newText)
        {
            return Task.Run(() =>
            {
                Word.Selection? sel = null;
                try
                {
                    sel = _wordApp.Selection;
                    if (sel == null) return false;
                    sel.Text = newText ?? string.Empty;
                    return true;
                }
                finally
                {
                    if (sel != null) Marshal.ReleaseComObject(sel);
                }
            });
        }

        public Task<bool> InsertTextAfterSelectionAsync(string text)
        {
            return Task.Run(() =>
            {
                if (string.IsNullOrWhiteSpace(text)) return false;

                // Nếu văn bản có cấu trúc đề thi, tự động chuyển hướng sang chuẩn hóa đề thi
                bool hasExamQuestions = Regex.IsMatch(text, @"(?m)^(?:%?\s*(?:Câu|Bài|CÂU|BÀI)\s*\d+[:.]|===CAU===|\\begin\{(?:ex|bt)\})");
                if (hasExamQuestions)
                {
                    var parseRes = MatrixExamAI.Shared.Extensibility.QuestionParserEngine.ParseQuestions(text);
                    if (parseRes?.Questions != null && parseRes.Questions.Count > 0)
                    {
                        Word.Document? activeDoc = null;
                        try { activeDoc = _wordApp.ActiveDocument; } catch { }
                        if (activeDoc == null)
                        {
                            try { activeDoc = _wordApp.Documents.Add(); } catch { }
                        }
                        if (activeDoc != null)
                        {
                            return StandardizeActiveDocumentExam(activeDoc, parseRes.Questions, "Times New Roman", 12f, 1.15f);
                        }
                    }
                }

                Word.Selection? sel = null;
                try
                {
                    sel = _wordApp.Selection;
                    if (sel == null) return false;
                    sel.Collapse(Word.WdCollapseDirection.wdCollapseEnd);
                    sel.TypeParagraph();
                    sel.TypeText(text ?? string.Empty);
                    return true;
                }
                finally
                {
                    if (sel != null) Marshal.ReleaseComObject(sel);
                }
            });
        }

        public Task<bool> InsertStandardizedExamAsync(List<MatrixExamAI.Shared.Extensibility.QuestionItem> questions, string fontName = "Times New Roman", float fontSize = 12f, float lineSpacing = 1.15f)
        {
            return Task.Run(() =>
            {
                if (questions == null || questions.Count == 0) return false;

                Word.Document? doc = null;
                try
                {
                    doc = _wordApp.ActiveDocument;
                }
                catch
                {
                    try { doc = _wordApp.Documents.Add(); } catch { }
                }

                if (doc == null)
                {
                    try { doc = _wordApp.Documents.Add(); } catch { return false; }
                }

                return StandardizeActiveDocumentExam(doc, questions, fontName, fontSize, lineSpacing);
            });
        }

        private static string WrapInWordprocessingML(string ommlXml)
        {
            if (string.IsNullOrWhiteSpace(ommlXml)) return string.Empty;
            if (ommlXml.Contains("<pkg:package")) return ommlXml;

            string innerMath = ommlXml.Trim();

            return $@"<?xml version=""1.0"" encoding=""UTF-8"" standalone=""yes""?>
<pkg:package xmlns:pkg=""http://schemas.microsoft.com/office/2006/xmlPackage"">
  <pkg:part pkg:name=""/_rels/.rels"" pkg:contentType=""application/vnd.openxmlformats-package.relationships+xml"">
    <pkg:xmlData>
      <Relationships xmlns=""http://schemas.openxmlformats.org/package/2006/relationships"">
        <Relationship Id=""rId1"" Type=""http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument"" Target=""word/document.xml""/>
      </Relationships>
    </pkg:xmlData>
  </pkg:part>
  <pkg:part pkg:name=""/word/document.xml"" pkg:contentType=""application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"">
    <pkg:xmlData>
      <w:document xmlns:w=""http://schemas.openxmlformats.org/wordprocessingml/2006/main""
                  xmlns:m=""http://schemas.openxmlformats.org/officeDocument/2006/math"">
        <w:body>
          <w:p>
            {innerMath}
          </w:p>
        </w:body>
      </w:document>
    </pkg:xmlData>
  </pkg:part>
</pkg:package>";
        }

        public Task<bool> InsertOmmlAtSelectionAsync(string ommlXml)
        {
            return Task.Run(() =>
            {
                Word.Selection? sel = null;
                Word.Range? range = null;
                try
                {
                    sel = _wordApp.Selection;
                    if (sel == null) return false;
                    range = sel.Range;
                    if (range == null) return false;

                    string pkgXml = WrapInWordprocessingML(ommlXml);
                    try
                    {
                        range.InsertXML(pkgXml);
                        return true;
                    }
                    catch (Exception exPkg)
                    {
                        AddInLog.Log($"[WordDocumentService] InsertXML with pkg:package failed: {exPkg.Message}. Fallback to direct XML.");
                        try
                        {
                            range.InsertXML(ommlXml);
                            return true;
                        }
                        catch
                        {
                            range.Text = ommlXml;
                            return true;
                        }
                    }
                }
                catch (Exception ex)
                {
                    AddInLog.LogError("[WordDocumentService] InsertOmmlAtSelectionAsync error", ex);
                    return false;
                }
                finally
                {
                    if (range != null) Marshal.ReleaseComObject(range);
                    if (sel != null) Marshal.ReleaseComObject(sel);
                }
            });
        }

        public Task<int> ConvertAllLatexInDocumentAsync()
        {
            return Task.Run(async () =>
            {
                int convertedCount = 0;
                Word.Document? doc = null;
                try
                {
                    doc = _wordApp.ActiveDocument;
                    if (doc == null) return 0;

                    var latexService = new MatrixExamAI.Shared.Extensibility.LatexToOmmlService();

                    foreach (Word.Range storyRange in doc.StoryRanges)
                    {
                        try
                        {
                            string text = storyRange.Text;
                            if (string.IsNullOrEmpty(text)) continue;

                            var displayMatches = Regex.Matches(text, @"\$\$([\s\S]+?)\$\$");
                            var inlineMatches = Regex.Matches(text, @"\$([^\$\r\n]+?)\$");

                            var allMatches = new List<(int Index, int Length, string Latex, bool IsDisplay)>();
                            foreach (Match m in displayMatches)
                            {
                                allMatches.Add((m.Index, m.Length, m.Groups[1].Value, true));
                            }
                            foreach (Match m in inlineMatches)
                            {
                                allMatches.Add((m.Index, m.Length, m.Groups[1].Value, false));
                            }

                            var sortedMatches = allMatches.OrderByDescending(m => m.Index).ToList();

                            foreach (var item in sortedMatches)
                            {
                                try
                                {
                                    var ommlResult = await latexService.ConvertLatexToOmmlAsync(item.Latex, item.IsDisplay).ConfigureAwait(false);
                                    if (ommlResult.Success && !string.IsNullOrWhiteSpace(ommlResult.OmmlXml))
                                    {
                                        int charStart = storyRange.Start + item.Index;
                                        int charEnd = charStart + item.Length;
                                        Word.Range targetRange = doc.Range(charStart, charEnd);
                                        try
                                        {
                                            string pkg = WrapInWordprocessingML(ommlResult.OmmlXml);
                                            targetRange.InsertXML(pkg);
                                            convertedCount++;
                                        }
                                        catch
                                        {
                                            targetRange.Text = ommlResult.OmmlXml;
                                            convertedCount++;
                                        }
                                        finally
                                        {
                                            Marshal.ReleaseComObject(targetRange);
                                        }
                                    }
                                }
                                catch (Exception exMatch)
                                {
                                    AddInLog.Log($"[ConvertAllLatex] Error converting formula '{item.Latex}': {exMatch.Message}");
                                }
                            }
                        }
                        finally
                        {
                            Marshal.ReleaseComObject(storyRange);
                        }
                    }

                    AddInLog.Log($"[WordDocumentService] ConvertAllLatexInDocumentAsync completed: {convertedCount} formulas converted.");
                    return convertedCount;
                }
                catch (Exception ex)
                {
                    AddInLog.LogError("[WordDocumentService] ConvertAllLatexInDocumentAsync error", ex);
                    return convertedCount;
                }
                finally
                {
                    if (doc != null) Marshal.ReleaseComObject(doc);
                }
            });
        }

        private static string ResolvePythonPath()
        {
            string candidate = @"C:\Users\domin\AppData\Local\Python\bin\python.exe";
            if (File.Exists(candidate)) return candidate;
            string cand314 = @"C:\Users\domin\AppData\Local\Python\bin\python3.14.exe";
            if (File.Exists(cand314)) return cand314;
            string py = @"C:\Users\domin\AppData\Local\Microsoft\WindowsApps\python3.exe";
            if (File.Exists(py)) return py;
            return "python";
        }

        public Task<(bool success, int oleCount, string reportJson)> ScanMathTypeFormulasAsync(string? docxPath = null)
        {
            return Task.Run(() =>
            {
                try
                {
                    string targetFile = docxPath ?? string.Empty;
                    if (string.IsNullOrWhiteSpace(targetFile))
                    {
                        if (_wordApp.ActiveDocument == null) return (false, 0, "Không có tài liệu nào đang mở.");
                        targetFile = _wordApp.ActiveDocument.FullName;
                        if (!File.Exists(targetFile))
                        {
                            string tempFile = Path.Combine(Path.GetTempPath(), $"MEA_Scan_{Guid.NewGuid():N}.docx");
                            _wordApp.ActiveDocument.SaveAs2(tempFile);
                            targetFile = tempFile;
                        }
                    }

                    string pythonExe = ResolvePythonPath();
                    string scriptPath = @"C:\Users\domin\.gemini\config\skills\docx-math-engine\scripts\docx_math.py";

                    if (!File.Exists(scriptPath))
                    {
                        return (false, 0, "Không tìm thấy script docx_math.py trên hệ thống.");
                    }

                    string tempReport = Path.Combine(Path.GetTempPath(), $"MEA_ScanReport_{Guid.NewGuid():N}.json");

                    var psi = new ProcessStartInfo
                    {
                        FileName = pythonExe,
                        Arguments = $"\"{scriptPath}\" scan \"{targetFile}\" --format json -o \"{tempReport}\"",
                        UseShellExecute = false,
                        CreateNoWindow = true,
                        RedirectStandardOutput = true,
                        RedirectStandardError = true
                    };

                    using (var proc = Process.Start(psi))
                    {
                        proc?.WaitForExit(30000);
                    }

                    if (File.Exists(tempReport))
                    {
                        string json = File.ReadAllText(tempReport);
                        try { File.Delete(tempReport); } catch { }
                        using (var jdoc = JsonDocument.Parse(json))
                        {
                            int count = 0;
                            if (jdoc.RootElement.TryGetProperty("total_formulas", out var pTotal)) count = pTotal.GetInt32();
                            else if (jdoc.RootElement.TryGetProperty("formulas_found", out var pF)) count = pF.GetInt32();
                            return (true, count, json);
                        }
                    }

                    return (false, 0, "Không nhận được kết quả quét từ docx-math-engine.");
                }
                catch (Exception ex)
                {
                    AddInLog.LogError("[WordDocumentService] ScanMathTypeFormulasAsync error", ex);
                    return (false, 0, ex.Message);
                }
            });
        }

        public Task<(bool success, int convertedCount, string outputPath, string reportJson)> ConvertMathTypeToOmmlAsync(string? docxPath = null)
        {
            return Task.Run(() =>
            {
                try
                {
                    string targetFile = docxPath ?? string.Empty;
                    if (string.IsNullOrWhiteSpace(targetFile))
                    {
                        if (_wordApp.ActiveDocument == null) return (false, 0, string.Empty, "Không có tài liệu nào đang mở.");
                        targetFile = _wordApp.ActiveDocument.FullName;
                        if (!File.Exists(targetFile))
                        {
                            string tempFile = Path.Combine(Path.GetTempPath(), $"MEA_Doc_{Guid.NewGuid():N}.docx");
                            _wordApp.ActiveDocument.SaveAs2(tempFile);
                            targetFile = tempFile;
                        }
                        else
                        {
                            _wordApp.ActiveDocument.Save();
                        }
                    }

                    string dir = Path.GetDirectoryName(targetFile) ?? Path.GetTempPath();
                    string baseName = Path.GetFileNameWithoutExtension(targetFile);
                    string outputFile = Path.Combine(dir, $"{baseName}_OMML.docx");
                    string reportFile = Path.Combine(Path.GetTempPath(), $"MEA_ConvertReport_{Guid.NewGuid():N}.json");

                    string pythonExe = ResolvePythonPath();
                    string scriptPath = @"C:\Users\domin\.gemini\config\skills\docx-math-engine\scripts\docx_math.py";

                    var psi = new ProcessStartInfo
                    {
                        FileName = pythonExe,
                        Arguments = $"\"{scriptPath}\" convert \"{targetFile}\" -o \"{outputFile}\" --report \"{reportFile}\"",
                        UseShellExecute = false,
                        CreateNoWindow = true,
                        RedirectStandardOutput = true,
                        RedirectStandardError = true
                    };

                    using (var proc = Process.Start(psi))
                    {
                        proc?.WaitForExit(60000);
                    }

                    if (File.Exists(outputFile))
                    {
                        string reportJson = File.Exists(reportFile) ? File.ReadAllText(reportFile) : "{}";
                        try { if (File.Exists(reportFile)) File.Delete(reportFile); } catch { }

                        int converted = 0;
                        try
                        {
                            using (var doc = JsonDocument.Parse(reportJson))
                            {
                                if (doc.RootElement.TryGetProperty("converted", out var pConv)) converted = pConv.GetInt32();
                                else if (doc.RootElement.TryGetProperty("total_converted", out var pTot)) converted = pTot.GetInt32();
                            }
                        }
                        catch { }

                        try
                        {
                            _wordApp.Documents.Open(outputFile);
                        }
                        catch (Exception exOpen)
                        {
                            AddInLog.Log($"[ConvertMathType] Could not auto-open converted file in Word: {exOpen.Message}");
                        }

                        return (true, converted, outputFile, reportJson);
                    }

                    return (false, 0, string.Empty, "Chuyển đổi thất bại, không tạo được tệp OMML mới.");
                }
                catch (Exception ex)
                {
                    AddInLog.LogError("[WordDocumentService] ConvertMathTypeToOmmlAsync error", ex);
                    return (false, 0, string.Empty, ex.Message);
                }
            });
        }

        public Task<(bool success, int convertedCount, string message)> ConvertAllEquationsToMathTypeAsync()
        {
            Word.Document? doc = null;
            try
            {
                doc = _wordApp.ActiveDocument;
                if (doc == null) return Task.FromResult((false, 0, "Không có tài liệu Word nào đang mở."));

                int omathCount = doc.OMaths.Count;
                if (omathCount == 0) return Task.FromResult((true, 0, "Không tìm thấy công thức Word Equation (OMML) nào trong tài liệu."));

                var ommlService = new MatrixExamAI.Shared.Extensibility.OmmlToLatexService();
                int count = 0;

                AddInLog.Log($"[WordDocumentService] Bắt đầu chuyển đổi {omathCount} công thức Equation sang MathType...");

                bool prevUpdating = _wordApp.ScreenUpdating;
                _wordApp.ScreenUpdating = false;

                try
                {
                    // 1. Duyệt ngược từ cuối lên đầu để không làm sai lệch Range
                    for (int i = omathCount; i >= 1; i--)
                    {
                        try
                        {
                            var omath = doc.OMaths[i];
                            var range = omath.Range;
                            string xml = range.WordOpenXML;

                            string latex = ommlService.ConvertOmmlXmlToLatex(xml);
                            if (string.IsNullOrWhiteSpace(latex))
                            {
                                latex = range.Text?.Trim() ?? string.Empty;
                            }

                            if (!string.IsNullOrWhiteSpace(latex))
                            {
                                range.Text = $"${latex}$";
                                count++;
                            }
                        }
                        catch (Exception ex)
                        {
                            AddInLog.LogError($"[WordDocumentService] Lỗi chuyển đổi OMath[{i}]", ex);
                        }
                    }
                }
                finally
                {
                    _wordApp.ScreenUpdating = prevUpdating;
                }

                // 2. Kích hoạt lệnh ToggleTeX của MathType trên toàn bộ tài liệu
                try
                {
                    doc.Content.Select();
                    ExecuteMathTypeToggleTeX();
                }
                catch (Exception ex)
                {
                    AddInLog.LogError("[WordDocumentService] Lỗi kích hoạt MathType ToggleTeX", ex);
                }

                string msg = $"Đã chuyển đổi thành công {count}/{omathCount} công thức Equation sang MathType qua ToggleTeX.";
                AddInLog.Log($"[WordDocumentService] {msg}");
                return Task.FromResult((true, count, msg));
            }
            catch (Exception ex)
            {
                AddInLog.LogError("[WordDocumentService] ConvertAllEquationsToMathTypeAsync error", ex);
                return Task.FromResult((false, 0, ex.Message));
            }
        }

        private void ExecuteMathTypeToggleTeX()
        {
            string[] macroCandidates = new[]
            {
                "MTCommand_TeXToggle",
                "'MathType Commands 2016.dotm'!MTCommand_TeXToggle",
                "MTCommand_OnTexToggle",
                "'MathType Commands 2016.dotm'!MTCommand_OnTexToggle",
                "MathTypeCommands.MTCommand_TeXToggle",
                "ToggleTeX",
                "TeXToggle"
            };

            foreach (var macro in macroCandidates)
            {
                try
                {
                    _wordApp.Run(macro);
                    AddInLog.Log($"[WordDocumentService] MathType macro '{macro}' executed successfully.");
                    return;
                }
                catch (Exception ex)
                {
                    AddInLog.Log($"[WordDocumentService] Thử macro '{macro}' không thành công: {ex.Message}");
                }
            }

            // Fallback gửi phím tắt Alt + \ của MathType
            try
            {
                _wordApp.Activate();
                System.Windows.Forms.SendKeys.SendWait("%\\");
                AddInLog.Log("[WordDocumentService] MathType shortcut Alt+\\ sent.");
            }
            catch (Exception ex)
            {
                AddInLog.LogError("[WordDocumentService] Không thể kích hoạt ToggleTeX", ex);
            }
        }


        public Task<bool> StandardizeDocumentFormattingAsync(string fontName = "Times New Roman", float fontSize = 12f, float lineSpacing = 1.15f, bool entireDocument = false)
        {
            return Task.Run(() =>
            {
                Word.Selection? sel = null;
                Word.Range? range = null;
                try
                {
                    sel = _wordApp.Selection;
                    if (sel == null) return false;

                    Word.Document? doc = _wordApp.ActiveDocument;
                    if (doc == null) return false;

                    if (entireDocument || sel.Start == sel.End)
                    {
                        range = doc.Content;
                    }
                    else
                    {
                        range = sel.Range;
                    }

                    if (range == null) return false;

                    string text = range.Text ?? string.Empty;

                    // Kiểm tra xem vùng chọn hoặc tài liệu có chứa câu hỏi đề thi không
                    bool hasExamQuestions = Regex.IsMatch(text, @"(?m)^(?:%?\s*(?:Câu|Bài|CÂU|BÀI)\s*\d+[:.]|===CAU===|\\begin\{(?:ex|bt)\})");
                    if (hasExamQuestions)
                    {
                        var parseRes = MatrixExamAI.Shared.Extensibility.QuestionParserEngine.ParseQuestions(text);
                        var questions = parseRes?.Questions;
                        if (questions != null && questions.Count > 0)
                        {
                            if (entireDocument || sel.Start == sel.End)
                            {
                                return StandardizeActiveDocumentExam(doc, questions, fontName, fontSize, lineSpacing);
                            }
                            else
                            {
                                return StandardizeSelectionExam(doc, sel, questions, fontName, fontSize, lineSpacing);
                            }
                        }
                    }

                    // Fallback chuẩn hóa định dạng chung nếu không phải đề thi
                    range.Font.Name = string.IsNullOrWhiteSpace(fontName) ? "Times New Roman" : fontName;
                    range.Font.Size = fontSize > 0 ? fontSize : 12f;
                    range.ParagraphFormat.LineSpacingRule = Word.WdLineSpacing.wdLineSpaceMultiple;
                    range.ParagraphFormat.LineSpacing = _wordApp.LinesToPoints(lineSpacing > 0 ? lineSpacing : 1.15f);
                    range.ParagraphFormat.SpaceBefore = 0;
                    range.ParagraphFormat.SpaceAfter = 3;

                    return true;
                }
                catch (Exception ex)
                {
                    System.Diagnostics.Debug.WriteLine($"[WordDocumentService] StandardizeDocumentFormattingAsync error: {ex.Message}");
                    return false;
                }
                finally
                {
                    if (range != null) Marshal.ReleaseComObject(range);
                    if (sel != null) Marshal.ReleaseComObject(sel);
                }
            });
        }

        private bool StandardizeActiveDocumentExam(Word.Document doc, List<MatrixExamAI.Shared.Extensibility.QuestionItem> questions, string fontName, float fontSize, float lineSpacing)
        {
            fontName = string.IsNullOrWhiteSpace(fontName) ? "Times New Roman" : fontName;
            if (fontSize <= 0) fontSize = 12f;
            if (lineSpacing <= 0) lineSpacing = 1.15f;

            // 1. Ưu tiên gọi trực tiếp engine xuất Word chuẩn của MEA (export/word_exporter.py) qua CLI bridge
            if (TryExportWithPythonCli(questions, out string tempDocxPath))
            {
                try
                {
                    doc.Content.Delete();
                    doc.Content.InsertFile(tempDocxPath);
                    try
                    {
                        doc.PageSetup.PaperSize = Word.WdPaperSize.wdPaperA4;
                        doc.PageSetup.TopMargin = _wordApp.CentimetersToPoints(1.0f);
                        doc.PageSetup.BottomMargin = _wordApp.CentimetersToPoints(1.0f);
                        doc.PageSetup.LeftMargin = _wordApp.CentimetersToPoints(1.5f);
                        doc.PageSetup.RightMargin = _wordApp.CentimetersToPoints(1.5f);
                    }
                    catch { }
                    return true;
                }
                catch (Exception ex)
                {
                    System.Diagnostics.Debug.WriteLine($"[WordDocumentService] InsertFile error: {ex.Message}");
                }
                finally
                {
                    try { if (File.Exists(tempDocxPath)) File.Delete(tempDocxPath); } catch { }
                }
            }

            // 2. Fallback COM: Tái hiện 100% cấu trúc của word_exporter.py
            try
            {
                // Cài đặt khổ giấy A4 và lề chuẩn: 1.0cm trên/dưới, 1.5cm trái/phải
                try
                {
                    doc.PageSetup.PaperSize = Word.WdPaperSize.wdPaperA4;
                    doc.PageSetup.TopMargin = _wordApp.CentimetersToPoints(1.0f);
                    doc.PageSetup.BottomMargin = _wordApp.CentimetersToPoints(1.0f);
                    doc.PageSetup.LeftMargin = _wordApp.CentimetersToPoints(1.5f);
                    doc.PageSetup.RightMargin = _wordApp.CentimetersToPoints(1.5f);
                }
                catch { }

                doc.Content.Delete();

                // Khung tiêu đề 2 cột phẳng (Table 0: 7.25cm và 11.25cm)
                var pHeader = doc.Paragraphs.Add();
                Word.Table headerTable = doc.Tables.Add(pHeader.Range, 1, 2);
                headerTable.Borders.Enable = 0;
                headerTable.Columns[1].Width = _wordApp.CentimetersToPoints(7.25f);
                headerTable.Columns[2].Width = _wordApp.CentimetersToPoints(11.25f);

                string subject = questions.FirstOrDefault(q => !string.IsNullOrWhiteSpace(q.Subject))?.Subject ?? "TOÁN";
                int grade = questions.FirstOrDefault(q => q.Grade > 0)?.Grade ?? 12;

                Word.Cell cellLeft = headerTable.Cell(1, 1);
                cellLeft.Range.Text = $"SỞ GIÁO DỤC VÀ ĐÀO TẠO\rTRƯỜNG THPT .........................\r(Đề thi gồm {questions.Count:D2} câu)";
                cellLeft.Range.ParagraphFormat.Alignment = Word.WdParagraphAlignment.wdAlignParagraphCenter;
                cellLeft.Range.Font.Name = fontName;
                cellLeft.Range.Font.Size = fontSize;
                try
                {
                    if (cellLeft.Range.Paragraphs.Count >= 3)
                    {
                        cellLeft.Range.Paragraphs[1].Range.Font.Bold = 1;
                        cellLeft.Range.Paragraphs[2].Range.Font.Bold = 1;
                        cellLeft.Range.Paragraphs[3].Range.Font.Bold = 0;
                    }
                    else
                    {
                        cellLeft.Range.Font.Bold = 1;
                    }
                }
                catch { cellLeft.Range.Font.Bold = 1; }

                Word.Cell cellRight = headerTable.Cell(1, 2);
                cellRight.Range.Text = $"ĐỀ KIỂM TRA CHÍNH THỨC\rMôn: {subject.ToUpperInvariant()} - Khối {grade}\rThời gian làm bài: 90 phút (không kể phát đề)";
                cellRight.Range.ParagraphFormat.Alignment = Word.WdParagraphAlignment.wdAlignParagraphCenter;
                cellRight.Range.Font.Name = fontName;
                cellRight.Range.Font.Size = fontSize;
                try
                {
                    if (cellRight.Range.Paragraphs.Count >= 3)
                    {
                        cellRight.Range.Paragraphs[1].Range.Font.Bold = 1;
                        cellRight.Range.Paragraphs[2].Range.Font.Bold = 1;
                        cellRight.Range.Paragraphs[3].Range.Font.Bold = 0;
                    }
                }
                catch { }

                // Dòng thông tin thí sinh phẳng với tab stops
                Word.Paragraph candPara = doc.Paragraphs.Add();
                candPara.Range.Text = "Họ và tên thí sinh: ....................................................   Số báo danh: ..............   Mã đề 101\r";
                candPara.Range.Font.Name = fontName;
                candPara.Range.Font.Size = fontSize;
                candPara.Range.Font.Bold = 0;
                candPara.Range.ParagraphFormat.TabStops.ClearAll();
                candPara.Range.ParagraphFormat.TabStops.Add(_wordApp.CentimetersToPoints(0.5f), Word.WdTabAlignment.wdAlignTabLeft);
                candPara.Range.ParagraphFormat.TabStops.Add(_wordApp.CentimetersToPoints(5.0f), Word.WdTabAlignment.wdAlignTabLeft);
                candPara.Range.ParagraphFormat.TabStops.Add(_wordApp.CentimetersToPoints(9.5f), Word.WdTabAlignment.wdAlignTabLeft);
                candPara.Range.ParagraphFormat.TabStops.Add(_wordApp.CentimetersToPoints(14.0f), Word.WdTabAlignment.wdAlignTabLeft);
                candPara.Range.ParagraphFormat.SpaceAfter = 2;
                int maDeIdx = candPara.Range.Text.IndexOf("Mã đề");
                if (maDeIdx >= 0)
                {
                    try
                    {
                        Word.Range rMaDe = doc.Range(candPara.Range.Start + maDeIdx, candPara.Range.End - 1);
                        rMaDe.Font.Bold = 1;
                    }
                    catch { }
                }

                // Đường kẻ phân cách _add_hrule
                Word.Paragraph hrulePara = doc.Paragraphs.Add();
                hrulePara.Range.Text = "\r";
                try
                {
                    hrulePara.Range.ParagraphFormat.Borders[Word.WdBorderType.wdBorderBottom].LineStyle = Word.WdLineStyle.wdLineStyleSingle;
                    hrulePara.Range.ParagraphFormat.Borders[Word.WdBorderType.wdBorderBottom].LineWidth = Word.WdLineWidth.wdLineWidth075pt;
                }
                catch { }
                hrulePara.Range.ParagraphFormat.SpaceAfter = 6;

                // Phân nhóm câu hỏi
                var tnQuestions = questions.Where(q => q.QuestionType == "MultipleChoice4").ToList();
                var dsQuestions = questions.Where(q => q.QuestionType == "TrueFalse4").ToList();
                var tlnQuestions = questions.Where(q => q.QuestionType == "ShortAnswer").ToList();
                var tlQuestions = questions.Where(q => q.QuestionType == "Essay" || (q.QuestionType != "MultipleChoice4" && q.QuestionType != "TrueFalse4" && q.QuestionType != "ShortAnswer")).ToList();

                int globalIndex = 1;

                // ── PHẦN I: Trắc nghiệm 4 lựa chọn ──
                if (tnQuestions.Count > 0)
                {
                    Word.Paragraph pSec1 = doc.Paragraphs.Add();
                    pSec1.Range.Text = $"PHẦN I. Thí sinh trả lời từ câu 1 đến câu {tnQuestions.Count}. Mỗi câu hỏi thí sinh chỉ chọn một phương án.\r";
                    pSec1.Range.Font.Name = fontName;
                    pSec1.Range.Font.Size = fontSize;
                    pSec1.Range.Font.Bold = 1;
                    pSec1.Range.ParagraphFormat.SpaceBefore = 4;
                    pSec1.Range.ParagraphFormat.SpaceAfter = 4;

                    foreach (var q in tnQuestions)
                    {
                        Word.Paragraph pQ = doc.Paragraphs.Add();
                        string cleanContent = Regex.Replace(q.Content ?? "", @"^(?:Câu|Bài|CÂU|BÀI)\s*\d+[\.:\)]\s*", "").Trim();
                        pQ.Range.Text = $"Câu {globalIndex}. {cleanContent}\r";
                        pQ.Range.Font.Name = fontName;
                        pQ.Range.Font.Size = fontSize;
                        pQ.Range.ParagraphFormat.SpaceAfter = 2;
                        Word.Range rBold = doc.Range(pQ.Range.Start, pQ.Range.Start + $"Câu {globalIndex}.".Length);
                        rBold.Font.Bold = 1;

                        InsertQuestionImagesCom(doc, q);

                        if (q.Options.Count > 0)
                        {
                            AppendOptionsToWordDoc(doc, q.Options, fontName, fontSize);
                        }

                        globalIndex++;
                    }
                }

                // ── PHẦN II: Đúng / Sai 4 ý ──
                if (dsQuestions.Count > 0)
                {
                    int startIdx = globalIndex;
                    int endIdx = globalIndex + dsQuestions.Count - 1;
                    Word.Paragraph pSec2 = doc.Paragraphs.Add();
                    pSec2.Range.Text = $"PHẦN II. Thí sinh trả lời từ câu {startIdx} đến câu {endIdx}. Trong mỗi ý a), b), c), d) ở mỗi câu hỏi, thí sinh chọn đúng hoặc sai.\r";
                    pSec2.Range.Font.Name = fontName;
                    pSec2.Range.Font.Size = fontSize;
                    pSec2.Range.Font.Bold = 1;
                    pSec2.Range.ParagraphFormat.SpaceBefore = 4;
                    pSec2.Range.ParagraphFormat.SpaceAfter = 4;

                    foreach (var q in dsQuestions)
                    {
                        Word.Paragraph pQ = doc.Paragraphs.Add();
                        string cleanContent = Regex.Replace(q.Content ?? "", @"^(?:Câu|Bài|CÂU|BÀI)\s*\d+[\.:\)]\s*", "").Trim();
                        pQ.Range.Text = $"Câu {globalIndex}. {cleanContent}\r";
                        pQ.Range.Font.Name = fontName;
                        pQ.Range.Font.Size = fontSize;
                        pQ.Range.ParagraphFormat.SpaceAfter = 2;
                        Word.Range rBold = doc.Range(pQ.Range.Start, pQ.Range.Start + $"Câu {globalIndex}.".Length);
                        rBold.Font.Bold = 1;

                        InsertQuestionImagesCom(doc, q);

                        foreach (var k in new[] { "a", "b", "c", "d" })
                        {
                            if (q.Options.ContainsKey(k))
                            {
                                Word.Paragraph pOpt = doc.Paragraphs.Add();
                                string val = q.Options[k].Trim();
                                if (!val.EndsWith(".") && !val.EndsWith(";") && !val.EndsWith("!")) val += ".";
                                pOpt.Range.Text = $"{k}) {val}\r";
                                pOpt.Range.Font.Name = fontName;
                                pOpt.Range.Font.Size = fontSize;
                                Word.Range rLetter = doc.Range(pOpt.Range.Start, pOpt.Range.Start + 2);
                                rLetter.Font.Bold = 1;
                                pOpt.Range.ParagraphFormat.LeftIndent = _wordApp.CentimetersToPoints(0.5f);
                                pOpt.Range.ParagraphFormat.SpaceAfter = 2;
                            }
                        }
                        globalIndex++;
                    }
                }

                // ── PHẦN III: Trả lời ngắn ──
                if (tlnQuestions.Count > 0)
                {
                    int startIdx = globalIndex;
                    int endIdx = globalIndex + tlnQuestions.Count - 1;
                    Word.Paragraph pSec3 = doc.Paragraphs.Add();
                    pSec3.Range.Text = $"PHẦN III. Thí sinh trả lời từ câu {startIdx} đến câu {endIdx}.\r";
                    pSec3.Range.Font.Name = fontName;
                    pSec3.Range.Font.Size = fontSize;
                    pSec3.Range.Font.Bold = 1;
                    pSec3.Range.ParagraphFormat.SpaceBefore = 4;
                    pSec3.Range.ParagraphFormat.SpaceAfter = 4;

                    foreach (var q in tlnQuestions)
                    {
                        Word.Paragraph pQ = doc.Paragraphs.Add();
                        string cleanContent = Regex.Replace(q.Content ?? "", @"^(?:Câu|Bài|CÂU|BÀI)\s*\d+[\.:\)]\s*", "").Trim();
                        pQ.Range.Text = $"Câu {globalIndex}. {cleanContent}\r";
                        pQ.Range.Font.Name = fontName;
                        pQ.Range.Font.Size = fontSize;
                        pQ.Range.ParagraphFormat.SpaceAfter = 4;
                        Word.Range rBold = doc.Range(pQ.Range.Start, pQ.Range.Start + $"Câu {globalIndex}.".Length);
                        rBold.Font.Bold = 1;

                        InsertQuestionImagesCom(doc, q);

                        globalIndex++;
                    }
                }

                // ── PHẦN IV: Tự luận ──
                if (tlQuestions.Count > 0)
                {
                    int startIdx = globalIndex;
                    int endIdx = globalIndex + tlQuestions.Count - 1;
                    Word.Paragraph pSec4 = doc.Paragraphs.Add();
                    pSec4.Range.Text = $"PHẦN IV. Tự luận. Thí sinh trình bày lời giải từ câu {startIdx} đến câu {endIdx}.\r";
                    pSec4.Range.Font.Name = fontName;
                    pSec4.Range.Font.Size = fontSize;
                    pSec4.Range.Font.Bold = 1;
                    pSec4.Range.ParagraphFormat.SpaceBefore = 4;
                    pSec4.Range.ParagraphFormat.SpaceAfter = 4;

                    foreach (var q in tlQuestions)
                    {
                        Word.Paragraph pQ = doc.Paragraphs.Add();
                        string cleanContent = Regex.Replace(q.Content ?? "", @"^(?:Câu|Bài|CÂU|BÀI)\s*\d+[\.:\)]\s*", "").Trim();
                        pQ.Range.Text = $"Câu {globalIndex}. {cleanContent}\r";
                        pQ.Range.Font.Name = fontName;
                        pQ.Range.Font.Size = fontSize;
                        pQ.Range.ParagraphFormat.SpaceAfter = 4;
                        Word.Range rBold = doc.Range(pQ.Range.Start, pQ.Range.Start + $"Câu {globalIndex}.".Length);
                        rBold.Font.Bold = 1;

                        InsertQuestionImagesCom(doc, q);

                        globalIndex++;
                    }
                }

                // 6. HẾT
                Word.Paragraph pEnd = doc.Paragraphs.Add();
                pEnd.Range.Text = "HẾT\r";
                pEnd.Range.Font.Name = fontName;
                pEnd.Range.Font.Size = fontSize;
                pEnd.Range.Font.Bold = 1;
                pEnd.Range.ParagraphFormat.Alignment = Word.WdParagraphAlignment.wdAlignParagraphCenter;
                pEnd.Range.ParagraphFormat.SpaceBefore = 6;
                pEnd.Range.ParagraphFormat.SpaceAfter = 2;

                // 7. BẢNG ĐÁP ÁN THAM KHẢO
                bool hasAnyAnswer = questions.Any(q => !string.IsNullOrWhiteSpace(q.CorrectAnswer));
                if (hasAnyAnswer)
                {
                    Word.Paragraph pAnsHead = doc.Paragraphs.Add();
                    pAnsHead.Range.Text = "ĐÁP ÁN THAM KHẢO\r";
                    pAnsHead.Range.Font.Name = fontName;
                    pAnsHead.Range.Font.Size = fontSize;
                    pAnsHead.Range.Font.Bold = 1;
                    pAnsHead.Range.ParagraphFormat.Alignment = Word.WdParagraphAlignment.wdAlignParagraphCenter;
                    pAnsHead.Range.ParagraphFormat.SpaceBefore = 4;
                    pAnsHead.Range.ParagraphFormat.SpaceAfter = 2;

                    if (tnQuestions.Count > 0)
                    {
                        Word.Paragraph pLbl1 = doc.Paragraphs.Add();
                        pLbl1.Range.Text = "PHẦN I.\r";
                        pLbl1.Range.Font.Bold = 1;

                        Word.Table tblKey = doc.Tables.Add(doc.Paragraphs.Add().Range, 2, tnQuestions.Count + 1);
                        tblKey.Borders.Enable = 1;
                        tblKey.Rows.Alignment = Word.WdRowAlignment.wdAlignRowCenter;
                        tblKey.Cell(1, 1).Range.Text = "Câu";
                        tblKey.Cell(1, 1).Range.Font.Bold = 1;
                        tblKey.Cell(2, 1).Range.Text = "Đáp án";
                        tblKey.Cell(2, 1).Range.Font.Bold = 1;

                        for (int i = 0; i < tnQuestions.Count; i++)
                        {
                            tblKey.Cell(1, i + 2).Range.Text = (i + 1).ToString();
                            tblKey.Cell(1, i + 2).Range.Font.Bold = 1;
                            tblKey.Cell(2, i + 2).Range.Text = tnQuestions[i].CorrectAnswer ?? "";
                            tblKey.Cell(2, i + 2).Range.Font.Bold = 0;
                        }
                        tblKey.Range.Font.Name = fontName;
                        tblKey.Range.Font.Size = fontSize - 1f;
                    }
                }

                // 8. LỜI GIẢI THAM KHẢO
                bool hasAnySol = questions.Any(q => !string.IsNullOrWhiteSpace(q.Explanation));
                if (hasAnySol)
                {
                    Word.Paragraph pSolHead = doc.Paragraphs.Add();
                    pSolHead.Range.Text = "LỜI GIẢI THAM KHẢO\r";
                    pSolHead.Range.Font.Name = fontName;
                    pSolHead.Range.Font.Size = fontSize;
                    pSolHead.Range.Font.Bold = 1;
                    pSolHead.Range.ParagraphFormat.Alignment = Word.WdParagraphAlignment.wdAlignParagraphCenter;
                    pSolHead.Range.ParagraphFormat.SpaceBefore = 6;
                    pSolHead.Range.ParagraphFormat.SpaceAfter = 2;

                    for (int i = 0; i < questions.Count; i++)
                    {
                        var q = questions[i];
                        if (!string.IsNullOrWhiteSpace(q.Explanation))
                        {
                            Word.Paragraph pSol = doc.Paragraphs.Add();
                            string ansNotice = !string.IsNullOrWhiteSpace(q.CorrectAnswer) ? $" Chọn {q.CorrectAnswer}." : "";
                            pSol.Range.Text = $"Câu {i + 1}.{ansNotice}\r{q.Explanation}\r";
                            pSol.Range.Font.Name = fontName;
                            pSol.Range.Font.Size = fontSize;
                            Word.Range rSolPrefix = doc.Range(pSol.Range.Start, pSol.Range.Start + $"Câu {i + 1}.".Length);
                            rSolPrefix.Font.Bold = 1;
                            pSol.Range.ParagraphFormat.SpaceAfter = 4;
                        }
                    }
                }

                return true;
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"[WordDocumentService] StandardizeActiveDocumentExam error: {ex.Message}");
                return false;
            }
        }

        private bool TryExportWithPythonCli(List<MatrixExamAI.Shared.Extensibility.QuestionItem> questions, out string tempDocxPath)
        {
            tempDocxPath = Path.Combine(Path.GetTempPath(), $"mea_exam_{Guid.NewGuid():N}.docx");
            string tempJsonPath = Path.Combine(Path.GetTempPath(), $"mea_exam_{Guid.NewGuid():N}.json");

            try
            {
                string? rootDir = FindMeaRootDirectory();
                if (string.IsNullOrEmpty(rootDir)) return false;

                string scriptPath = Path.Combine(rootDir, "export", "export_cli.py");
                if (!File.Exists(scriptPath)) return false;

                var jsonOptions = new JsonSerializerOptions { WriteIndented = true };
                string json = JsonSerializer.Serialize(questions, jsonOptions);
                File.WriteAllText(tempJsonPath, json, System.Text.Encoding.UTF8);

                string pythonExe = ResolvePythonPath();
                string[] pythonRunners = new[] { pythonExe, @"C:\Users\domin\AppData\Local\Python\bin\python.exe", @"C:\Users\domin\AppData\Local\Python\bin\python3.14.exe", "py", "python" };
                foreach (var pyRunner in pythonRunners)
                {
                    try
                    {
                        var psi = new ProcessStartInfo
                        {
                            FileName = pyRunner,
                            Arguments = $"-m export.export_cli --json-file \"{tempJsonPath}\" -o \"{tempDocxPath}\"",
                            WorkingDirectory = rootDir,
                            UseShellExecute = false,
                            CreateNoWindow = true,
                            RedirectStandardOutput = true,
                            RedirectStandardError = true
                        };

                        using var proc = Process.Start(psi);
                        if (proc == null) continue;

                        proc.WaitForExit(10000);
                        if (proc.ExitCode == 0 && File.Exists(tempDocxPath) && new FileInfo(tempDocxPath).Length > 1000)
                        {
                            return true;
                        }
                    }
                    catch
                    {
                        // Try next runner
                    }
                }
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"[WordDocumentService] TryExportWithPythonCli failed: {ex.Message}");
            }
            finally
            {
                try { if (File.Exists(tempJsonPath)) File.Delete(tempJsonPath); } catch { }
            }

            return false;
        }

        private string? FindMeaRootDirectory()
        {
            string fixedPath = @"M:\IT\Phần mềm biên soạn tài liệu\MEA_v5.0";
            if (Directory.Exists(fixedPath) && File.Exists(Path.Combine(fixedPath, "export", "export_cli.py")))
            {
                return fixedPath;
            }

            string current = AppDomain.CurrentDomain.BaseDirectory;
            for (int i = 0; i < 6; i++)
            {
                if (File.Exists(Path.Combine(current, "export", "export_cli.py")))
                {
                    return current;
                }
                var parent = Directory.GetParent(current);
                if (parent == null) break;
                current = parent.FullName;
            }

            return null;
        }

        private bool StandardizeSelectionExam(Word.Document doc, Word.Selection sel, List<MatrixExamAI.Shared.Extensibility.QuestionItem> questions, string fontName, float fontSize, float lineSpacing)
        {
            try
            {
                Word.Range selRange = sel.Range;
                selRange.Text = string.Empty;

                for (int i = 0; i < questions.Count; i++)
                {
                    var q = questions[i];
                    Word.Paragraph pQ = doc.Paragraphs.Add(selRange);
                    pQ.Range.Text = $"Câu {i + 1}. {q.Content}\r";
                    pQ.Range.Font.Name = fontName;
                    pQ.Range.Font.Size = fontSize;
                    Word.Range rBold = doc.Range(pQ.Range.Start, pQ.Range.Start + $"Câu {i + 1}.".Length);
                    rBold.Font.Bold = 1;

                    if (q.Options.Count > 0)
                    {
                        AppendOptionsToWordDoc(doc, q.Options, fontName, fontSize);
                    }
                }

                selRange.Font.Name = fontName;
                selRange.Font.Size = fontSize;
                selRange.ParagraphFormat.LineSpacingRule = Word.WdLineSpacing.wdLineSpaceMultiple;
                selRange.ParagraphFormat.LineSpacing = _wordApp.LinesToPoints(lineSpacing);
                return true;
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"[WordDocumentService] StandardizeSelectionExam error: {ex.Message}");
                return false;
            }
        }

        private void AppendOptionsToWordDoc(Word.Document doc, Dictionary<string, string> options, string fontName, float fontSize)
        {
            int maxLen = options.Values.Select(v => (v ?? "").Length).DefaultIfEmpty(0).Max();
            int totalLen = options.Values.Sum(v => (v ?? "").Length);

            if (maxLen <= 32 && totalLen <= 120 && options.Count == 4)
            {
                Word.Paragraph p = doc.Paragraphs.Add();
                p.Format.LeftIndent = _wordApp.CentimetersToPoints(0.5f);
                p.Format.TabStops.ClearAll();
                p.Format.TabStops.Add(_wordApp.CentimetersToPoints(5.0f), Word.WdTabAlignment.wdAlignTabLeft);
                p.Format.TabStops.Add(_wordApp.CentimetersToPoints(9.5f), Word.WdTabAlignment.wdAlignTabLeft);
                p.Format.TabStops.Add(_wordApp.CentimetersToPoints(14.0f), Word.WdTabAlignment.wdAlignTabLeft);
                p.Format.SpaceAfter = 8;

                string optA = options.ContainsKey("A") ? options["A"] : "";
                string optB = options.ContainsKey("B") ? options["B"] : "";
                string optC = options.ContainsKey("C") ? options["C"] : "";
                string optD = options.ContainsKey("D") ? options["D"] : "";

                p.Range.Text = $"A. {optA}\tB. {optB}\tC. {optC}\tD. {optD}\r";
                p.Range.Font.Name = fontName;
                p.Range.Font.Size = fontSize;
                BoldOptionLetter(doc, p, "A.");
                BoldOptionLetter(doc, p, "B.");
                BoldOptionLetter(doc, p, "C.");
                BoldOptionLetter(doc, p, "D.");
            }
            else if (maxLen <= 64 && totalLen <= 220 && options.Count == 4)
            {
                Word.Paragraph p1 = doc.Paragraphs.Add();
                p1.Format.LeftIndent = _wordApp.CentimetersToPoints(0.5f);
                p1.Format.TabStops.ClearAll();
                p1.Format.TabStops.Add(_wordApp.CentimetersToPoints(7.5f), Word.WdTabAlignment.wdAlignTabLeft);
                p1.Format.SpaceAfter = 2;
                string optA = options.ContainsKey("A") ? options["A"] : "";
                string optB = options.ContainsKey("B") ? options["B"] : "";
                p1.Range.Text = $"A. {optA}\tB. {optB}\r";
                p1.Range.Font.Name = fontName;
                p1.Range.Font.Size = fontSize;
                BoldOptionLetter(doc, p1, "A.");
                BoldOptionLetter(doc, p1, "B.");

                Word.Paragraph p2 = doc.Paragraphs.Add();
                p2.Format.LeftIndent = _wordApp.CentimetersToPoints(0.5f);
                p2.Format.TabStops.ClearAll();
                p2.Format.TabStops.Add(_wordApp.CentimetersToPoints(7.5f), Word.WdTabAlignment.wdAlignTabLeft);
                p2.Format.SpaceAfter = 8;
                string optC = options.ContainsKey("C") ? options["C"] : "";
                string optD = options.ContainsKey("D") ? options["D"] : "";
                p2.Range.Text = $"C. {optC}\tD. {optD}\r";
                p2.Range.Font.Name = fontName;
                p2.Range.Font.Size = fontSize;
                BoldOptionLetter(doc, p2, "C.");
                BoldOptionLetter(doc, p2, "D.");
            }
            else
            {
                foreach (var k in new[] { "A", "B", "C", "D" })
                {
                    if (options.ContainsKey(k))
                    {
                        Word.Paragraph p = doc.Paragraphs.Add();
                        p.Range.Text = $"{k}. {options[k]}\r";
                        p.Range.Font.Name = fontName;
                        p.Range.Font.Size = fontSize;
                        p.Format.LeftIndent = _wordApp.CentimetersToPoints(0.5f);
                        p.Format.SpaceAfter = (k != "D") ? 2 : 8;
                        Word.Range rL = doc.Range(p.Range.Start, p.Range.Start + 2);
                        rL.Font.Bold = 1;
                    }
                }
            }
        }

        private static void BoldOptionLetter(Word.Document doc, Word.Paragraph p, string optLabel)
        {
            try
            {
                string text = p.Range.Text ?? string.Empty;
                int idx = text.IndexOf(optLabel, StringComparison.Ordinal);
                if (idx >= 0)
                {
                    Word.Range r = doc.Range(p.Range.Start + idx, p.Range.Start + idx + optLabel.Length);
                    r.Font.Bold = 1;
                }
            }
            catch { }
        }

        private void InsertQuestionImagesCom(Word.Document doc, MatrixExamAI.Shared.Extensibility.QuestionItem q)
        {
            var imgPaths = new List<string>();

            // 1. Danh sách ảnh q.Images (đường dẫn hoặc Base64)
            if (q.Images != null && q.Images.Count > 0)
            {
                foreach (var imgRef in q.Images)
                {
                    if (string.IsNullOrWhiteSpace(imgRef)) continue;
                    if (File.Exists(imgRef))
                    {
                        imgPaths.Add(imgRef);
                    }
                    else if (imgRef.StartsWith("data:image") || (imgRef.Length > 200 && !imgRef.Contains(Path.DirectorySeparatorChar.ToString())))
                    {
                        try
                        {
                            string b64 = imgRef;
                            if (b64.Contains(",")) b64 = b64.Split(',')[1];
                            byte[] bytes = Convert.FromBase64String(b64);
                            string resolvedPath = Path.Combine(Path.GetTempPath(), $"mea_qimg_{Guid.NewGuid():N}.png");
                            File.WriteAllBytes(resolvedPath, bytes);
                            imgPaths.Add(resolvedPath);
                        }
                        catch { }
                    }
                }
            }

            // 2. Thẻ [HINH_ANH: ...] hoặc [IMAGE: ...] trong q.Content
            if (!string.IsNullOrWhiteSpace(q.Content))
            {
                var matches = Regex.Matches(q.Content, @"\[(?:HINH_ANH|IMAGE|ANH|H[ÌI]NH(?:\s*\d+)?):\s*([^\]]+)\]", RegexOptions.IgnoreCase);
                foreach (Match m in matches)
                {
                    string p = m.Groups[1].Value.Trim();
                    if (File.Exists(p) && !imgPaths.Contains(p))
                    {
                        imgPaths.Add(p);
                    }
                }
            }

            // 3. Mã TikZ của câu hỏi (biên dịch sang PNG nếu có TikzCompilerService)
            if (!string.IsNullOrWhiteSpace(q.TikzCode))
            {
                try
                {
                    var compiler = new MatrixExamAI.Shared.Tikz.TikzCompilerService();
                    if (compiler.Toolchain.IsPdfLatexAvailable)
                    {
                        var req = new MatrixExamAI.Shared.Models.TikzCompileRequest
                        {
                            TikzCode = q.TikzCode,
                            Format = MatrixExamAI.Shared.Models.TikzExportFormat.Png,
                            Dpi = 300,
                            TimeoutSeconds = 8
                        };
                        var compileTask = compiler.CompileAsync(req);
                        compileTask.Wait(8000);
                        if (compileTask.Status == TaskStatus.RanToCompletion && compileTask.Result.Success && !string.IsNullOrEmpty(compileTask.Result.ImagePath) && File.Exists(compileTask.Result.ImagePath))
                        {
                            imgPaths.Add(compileTask.Result.ImagePath);
                        }
                    }
                }
                catch { }
            }

            // Chèn từng hình ảnh căn giữa vào tài liệu
            foreach (var resolvedPath in imgPaths)
            {
                try
                {
                    Word.Paragraph pImg = doc.Paragraphs.Add();
                    pImg.Range.ParagraphFormat.Alignment = Word.WdParagraphAlignment.wdAlignParagraphCenter;
                    pImg.Range.ParagraphFormat.SpaceBefore = 2;
                    pImg.Range.ParagraphFormat.SpaceAfter = 4;
                    object linkToFile = false;
                    object saveWithDoc = true;
                    object rangeObj = pImg.Range;
                    var shape = doc.InlineShapes.AddPicture(resolvedPath, ref linkToFile, ref saveWithDoc, ref rangeObj);
                    if (shape != null)
                    {
                        if (shape.Width > 396)
                        {
                            float ratio = 396f / shape.Width;
                            shape.Width = 396;
                            shape.Height = shape.Height * ratio;
                        }
                        Marshal.ReleaseComObject(shape);
                    }
                }
                catch (Exception ex)
                {
                    System.Diagnostics.Debug.WriteLine($"[InsertQuestionImagesCom] Error: {ex.Message}");
                }
            }
        }

        #endregion

        #region Metadata Helpers

        public static string FormatTikzMetadata(string rawCode)
        {
            return $"{TagPrefix}\n{rawCode?.Trim() ?? string.Empty}\n{TagSuffix}";
        }

        public static string ExtractTikzCode(string altText)
        {
            if (string.IsNullOrWhiteSpace(altText)) return string.Empty;

            int startIdx = altText.IndexOf(TagPrefix, StringComparison.OrdinalIgnoreCase);
            if (startIdx >= 0)
            {
                startIdx += TagPrefix.Length;
                int endIdx = altText.IndexOf(TagSuffix, startIdx, StringComparison.OrdinalIgnoreCase);
                if (endIdx > startIdx)
                {
                    return altText.Substring(startIdx, endIdx - startIdx).Trim();
                }
                return altText.Substring(startIdx).Trim();
            }

            // Fallback: check if the text contains a raw tikzpicture environment
            if (altText.Contains("\\begin{tikzpicture}"))
            {
                return altText.Trim();
            }

            return altText.Trim();
        }

        public static bool IsMatrixExamAiShape(string title, string altText)
        {
            if (!string.IsNullOrEmpty(title) && title.IndexOf("MatrixExamAI", StringComparison.OrdinalIgnoreCase) >= 0)
            {
                return true;
            }

            if (!string.IsNullOrEmpty(altText) &&
                (altText.IndexOf("MatrixExamAI:TikZ", StringComparison.OrdinalIgnoreCase) >= 0 ||
                 altText.IndexOf("\\begin{tikzpicture}", StringComparison.OrdinalIgnoreCase) >= 0))
            {
                return true;
            }

            return false;
        }

        private static string ResolveImagePath(string pathOrBase64)
        {
            if (string.IsNullOrWhiteSpace(pathOrBase64))
            {
                throw new ArgumentException("Image path or base64 data must not be empty.", nameof(pathOrBase64));
            }

            // Check if it's already an existing file
            if (File.Exists(pathOrBase64))
            {
                return pathOrBase64;
            }

            // If it's Base64 data (e.g. data:image/png;base64,... or pure base64)
            string base64Data = pathOrBase64;
            if (base64Data.StartsWith("data:", StringComparison.OrdinalIgnoreCase))
            {
                int commaIdx = base64Data.IndexOf(',');
                if (commaIdx >= 0)
                {
                    base64Data = base64Data.Substring(commaIdx + 1);
                }
            }

            try
            {
                byte[] bytes = Convert.FromBase64String(base64Data);
                string tempDir = Path.Combine(Path.GetTempPath(), "MatrixExamAI_TikZ");
                Directory.CreateDirectory(tempDir);
                string tempFile = Path.Combine(tempDir, $"tikz_{Guid.NewGuid():N}.png");
                File.WriteAllBytes(tempFile, bytes);
                return tempFile;
            }
            catch (FormatException)
            {
                // Not valid base64 and file doesn't exist
                return pathOrBase64;
            }
        }

        public Task<(bool success, string? imageBase64, int sizeKb, string? errorMessage)> GetSelectedImageBase64Async()
        {
            return Task.Run<(bool success, string? imageBase64, int sizeKb, string? errorMessage)>(() =>
            {
                try
                {
                    try
                    {
                        var sel = _wordApp.Selection;
                        if (sel != null)
                        {
                            if (sel.InlineShapes != null && sel.InlineShapes.Count > 0)
                            {
                                sel.InlineShapes[1].Select();
                                _wordApp.Selection.Copy();
                            }
                            else if (sel.ShapeRange != null && sel.ShapeRange.Count > 0)
                            {
                                sel.ShapeRange[1].Select();
                                _wordApp.Selection.Copy();
                            }
                        }
                    }
                    catch (Exception ex)
                    {
                        Debug.WriteLine($"[WordDocumentService] Copy shape failed: {ex.Message}");
                    }

                    string? base64 = null;
                    int sizeKb = 0;
                    bool hasImg = false;

                    var staThread = new System.Threading.Thread(() =>
                    {
                        try
                        {
                            if (System.Windows.Forms.Clipboard.ContainsImage())
                            {
                                using (var img = System.Windows.Forms.Clipboard.GetImage())
                                {
                                    if (img != null)
                                    {
                                        using (var ms = new MemoryStream())
                                        {
                                            img.Save(ms, System.Drawing.Imaging.ImageFormat.Png);
                                            byte[] bytes = ms.ToArray();
                                            base64 = Convert.ToBase64String(bytes);
                                            sizeKb = (int)(bytes.Length / 1024);
                                            hasImg = true;
                                        }
                                    }
                                }
                            }
                        }
                        catch { }
                    });
                    staThread.SetApartmentState(System.Threading.ApartmentState.STA);
                    staThread.Start();
                    staThread.Join(2000);

                    if (hasImg && !string.IsNullOrEmpty(base64))
                    {
                        return (true, base64, sizeKb, null);
                    }

                    return (false, null, 0, "Không tìm thấy hình ảnh nào đang được chọn trong Word hoặc trong Clipboard.");
                }
                catch (Exception ex)
                {
                    return (false, null, 0, ex.Message);
                }
            });
        }

        #endregion

        #region IDisposable

        public void Dispose()
        {
            try
            {
                _wordApp.WindowSelectionChange -= OnWindowSelectionChange;
            }
            catch
            {
                // Ignore COM cleanup exceptions
            }

            _debounceTimer.Stop();
            _debounceTimer.Tick -= OnDebounceTimerTick;
            _debounceTimer.Dispose();
        }

        #endregion
    }
}
