using System;
using System.IO;
using System.Reflection;
using System.Runtime.InteropServices;
using System.Windows.Forms;
using Office = Microsoft.Office.Core;

namespace MatrixExamAI.WordAddIn.Ribbon
{
    [ComVisible(true)]
    [Guid("43A7C8E2-2C99-4A94-BFD1-85E951E91C61")]
    public class RibbonController : Office.IRibbonExtensibility
    {
        private Office.IRibbonUI? _ribbon;
        private bool _isTikzSelected;

        public static RibbonController? Instance { get; private set; }

        public RibbonController()
        {
            Instance = this;
        }

        #region IRibbonExtensibility

        public string GetCustomUI(string ribbonID)
        {
            try
            {
                var assembly = Assembly.GetExecutingAssembly();
                using var stream = assembly.GetManifestResourceStream("MatrixExamAI.WordAddIn.Ribbon.Ribbon.xml");
                if (stream != null)
                {
                    using var reader = new StreamReader(stream);
                    return reader.ReadToEnd();
                }

                // Fallback to loading from disk if running in development without embedded resource
                string localPath = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "Ribbon", "Ribbon.xml");
                if (File.Exists(localPath))
                {
                    return File.ReadAllText(localPath);
                }
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"[RibbonController] Error loading Ribbon.xml: {ex.Message}");
            }

            return GetFallbackRibbonXml();
        }

        #endregion

        #region Ribbon Lifecycle Callbacks

        public void OnRibbonLoad(Office.IRibbonUI ribbonUI)
        {
            _ribbon = ribbonUI;
        }

        #endregion

        #region Button Action Callbacks

        public void OnOpenTikzSidebarClicked(Office.IRibbonControl control)
        {
            AddInLog.Log("Ribbon: OnOpenTikzSidebarClicked");
            ThisAddIn.Current?.TaskPaneManager?.ShowTikzSidebar();
        }

        public void OnEditSelectedTikZClicked(Office.IRibbonControl control)
        {
            AddInLog.Log("Ribbon: OnEditSelectedTikZClicked");
            ThisAddIn.Current?.TaskPaneManager?.TriggerEditSelectedTikzAsync();
        }

        public void OnToggleSidebarClicked(Office.IRibbonControl control)
        {
            AddInLog.Log("Ribbon: OnToggleSidebarClicked");
            ThisAddIn.Current?.TaskPaneManager?.ToggleSidebar();
        }

        public async void OnAiAuthoringClicked(Office.IRibbonControl control)
        {
            AddInLog.Log("Ribbon: OnAiAuthoringClicked");
            if (ThisAddIn.Current?.ExtensibilityManager != null)
            {
                await ThisAddIn.Current.ExtensibilityManager.HandleAiAuthoringAsync();
            }
            else
            {
                ThisAddIn.Current?.TaskPaneManager?.ShowTab("ai-authoring");
            }
        }

        public async void OnAiExplainClicked(Office.IRibbonControl control)
        {
            AddInLog.Log("Ribbon: OnAiExplainClicked");
            if (ThisAddIn.Current?.ExtensibilityManager != null)
            {
                await ThisAddIn.Current.ExtensibilityManager.HandleAiExplainAsync();
            }
            else
            {
                ThisAddIn.Current?.TaskPaneManager?.ShowTab("ai-explain");
            }
        }

        public void OnQuestionBankClicked(Office.IRibbonControl control)
        {
            AddInLog.Log("Ribbon: OnQuestionBankClicked");
            if (ThisAddIn.Current?.ExtensibilityManager != null)
            {
                ThisAddIn.Current.ExtensibilityManager.HandleQuestionBank();
            }
            else
            {
                ThisAddIn.Current?.TaskPaneManager?.ShowTab("question-bank");
            }
        }

        public void OnExamMatrixClicked(Office.IRibbonControl control)
        {
            AddInLog.Log("Ribbon: OnExamMatrixClicked");
            if (ThisAddIn.Current?.ExtensibilityManager != null)
            {
                ThisAddIn.Current.ExtensibilityManager.HandleExamMatrix();
            }
            else
            {
                ThisAddIn.Current?.TaskPaneManager?.ShowTab("exam-matrix");
            }
        }

        public void OnConvertClicked(Office.IRibbonControl control)
        {
            AddInLog.Log("Ribbon: OnConvertClicked");
            if (ThisAddIn.Current?.ExtensibilityManager != null)
            {
                ThisAddIn.Current.ExtensibilityManager.HandleConvert();
            }
            else
            {
                ThisAddIn.Current?.TaskPaneManager?.ShowTab("convert");
            }
        }

        public void OnStandardizeWordClicked(Office.IRibbonControl control)
        {
            AddInLog.Log("Ribbon: OnStandardizeWordClicked");
            ThisAddIn.Current?.TaskPaneManager?.ShowTab("standardize");
        }

        public async void OnEquationToMathTypeClicked(Office.IRibbonControl control)
        {
            AddInLog.Log("Ribbon: OnEquationToMathTypeClicked");
            try
            {
                if (ThisAddIn.Current?.DocumentService != null)
                {
                    var res = await ThisAddIn.Current.DocumentService.ConvertAllEquationsToMathTypeAsync();
                    MessageBox.Show(
                        res.message,
                        "MatrixExamAI — Chuyển đổi Equation sang MathType",
                        MessageBoxButtons.OK,
                        res.success ? MessageBoxIcon.Information : MessageBoxIcon.Warning);
                }
            }
            catch (Exception ex)
            {
                AddInLog.LogError("Ribbon: OnEquationToMathTypeClicked error", ex);
                MessageBox.Show(
                    "Lỗi chuyển đổi: " + ex.Message,
                    "MatrixExamAI — Lỗi",
                    MessageBoxButtons.OK,
                    MessageBoxIcon.Error);
            }
        }

        public void OnConvertLatexToOmmlClicked(Office.IRibbonControl control)
        {
            AddInLog.Log("Ribbon: OnConvertLatexToOmmlClicked (redirected to normalize)");
            ThisAddIn.Current?.TaskPaneManager?.ShowTab("normalize");
        }

        public void OnConvertMathTypeToOmmlClicked(Office.IRibbonControl control)
        {
            AddInLog.Log("Ribbon: OnConvertMathTypeToOmmlClicked (redirected to normalize)");
            ThisAddIn.Current?.TaskPaneManager?.ShowTab("normalize");
        }

        public void OnApiSettingsClicked(Office.IRibbonControl control)
        {
            AddInLog.Log("Ribbon: OnApiSettingsClicked");
            ThisAddIn.Current?.TaskPaneManager?.ShowTab("settings");
        }

        public void OnShuffleExamClicked(Office.IRibbonControl control)
        {
            AddInLog.Log("Ribbon: OnShuffleExamClicked");
            if (ThisAddIn.Current?.ExtensibilityManager != null)
            {
                ThisAddIn.Current.ExtensibilityManager.HandleShuffle();
            }
            else
            {
                ThisAddIn.Current?.TaskPaneManager?.ShowTab("shuffle");
            }
        }

        public bool GetIsTikzSelected(Office.IRibbonControl control)
        {
            return _isTikzSelected;
        }

        #endregion

        #region Invalidation and State Management

        public void SetTikZSelectionState(bool isSelected)
        {
            if (_isTikzSelected != isSelected)
            {
                _isTikzSelected = isSelected;
                try
                {
                    _ribbon?.InvalidateControl("btnEditSelectedTikZ");
                }
                catch (COMException)
                {
                    // Word might be in modal state or busy, ignore safely
                }
            }
        }

        public void InvalidateControl(string controlId)
        {
            try
            {
                _ribbon?.InvalidateControl(controlId);
            }
            catch (COMException)
            {
                // Word busy state handling
            }
        }

        public void Invalidate()
        {
            try
            {
                _ribbon?.Invalidate();
            }
            catch (COMException)
            {
                // Word busy state handling
            }
        }

        #endregion

        #region Fallback Ribbon XML

        private static string GetFallbackRibbonXml()
        {
            return @"<?xml version=""1.0"" encoding=""utf-8""?>
<customUI xmlns=""http://schemas.microsoft.com/office/2009/07/customui"" onLoad=""OnRibbonLoad"">
  <ribbon>
    <tabs>
      <tab id=""tabMatrixExamAI"" label=""MatrixExamAI"" keytip=""M"">
        <group id=""grpTikz"" label=""Vẽ hình TikZ"">
          <button id=""btnOpenTikzSidebar"" label=""Vẽ hình TikZ"" size=""large"" imageMso=""EquationInsertGallery"" onAction=""OnOpenTikzSidebarClicked"" />
          <separator id=""sepTikz1"" />
          <button id=""btnEditSelectedTikZ"" label=""Sửa hình TikZ"" size=""normal"" imageMso=""PictureRecolorGallery"" onAction=""OnEditSelectedTikZClicked"" getEnabled=""GetIsTikzSelected"" />
          <button id=""btnToggleSidebar"" label=""Bật/Tắt Sidebar"" size=""normal"" imageMso=""ViewTaskPane"" onAction=""OnToggleSidebarClicked"" />
        </group>
        <group id=""grpAI"" label=""Soạn thảo AI"">
          <button id=""btnAiAuthoring"" label=""Soạn thảo AI"" size=""large"" imageMso=""SmartArtInsert"" onAction=""OnAiAuthoringClicked"" />
        </group>
        <group id=""grpConvert"" label=""Convert Đề thi"">
          <button id=""btnOpenConvert"" label=""Convert Đề thi"" size=""large"" imageMso=""FileSaveAsWordDocx"" onAction=""OnConvertClicked"" />
        </group>
        <group id=""grpQuestions"" label=""Kho câu hỏi"">
          <button id=""btnQuestionBank"" label=""Kho câu hỏi"" size=""large"" imageMso=""DatabaseInsertGallery"" onAction=""OnQuestionBankClicked"" />
        </group>
        <group id=""grpMatrix"" label=""Ma trận đề"">
          <button id=""btnExamMatrix"" label=""Ma trận đề"" size=""large"" imageMso=""TableDesign"" onAction=""OnExamMatrixClicked"" />
        </group>
        <group id=""grpNormalize"" label=""Chuẩn hóa Word"">
          <button id=""btnStandardizeWord"" label=""Chuẩn hóa Word"" size=""large"" imageMso=""FileDocumentInspect"" onAction=""OnStandardizeWordClicked"" />
          <separator id=""sepNorm1"" />
          <button id=""btnEquationToMathType"" label=""Equation sang MathType"" size=""large"" imageMso=""EquationInsertGallery"" onAction=""OnEquationToMathTypeClicked"" />
        </group>
        <group id=""grpShuffle"" label=""Trộn đề thi"">
          <button id=""btnShuffleExam"" label=""Trộn đề thi"" size=""large"" imageMso=""AdpPrimaryKey"" onAction=""OnShuffleExamClicked"" />
        </group>
        <group id=""grpSettings"" label=""Cài đặt API"">
          <button id=""btnApiSettings"" label=""Cài đặt API"" size=""large"" imageMso=""ServerProperties"" onAction=""OnApiSettingsClicked"" />
        </group>
      </tab>
    </tabs>
  </ribbon>
</customUI>";
        }

        #endregion
    }
}
