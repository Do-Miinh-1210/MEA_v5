using System;
using System.Threading.Tasks;
using System.Windows.Forms;
using MatrixExamAI.Shared.AI;
using MatrixExamAI.Shared.Extensibility;

namespace MatrixExamAI.WordAddIn.Extensibility
{
    /// <summary>
    /// Điều phối viên tích hợp các phân hệ mở rộng (Phase 2, Phase 3, Phase 4) trong Microsoft Word Add-in.
    /// Liên kết thanh công cụ Ribbon, Custom Task Pane WebView2 và dịch vụ Word COM.
    /// </summary>
    public class WordExtensibilityManager
    {
        public IAIAssistantService AiAssistantService { get; }
        public IQuestionBankService QuestionBankService { get; }
        public IExamMatrixService ExamMatrixService { get; }
        public ILatexToOmmlService LatexToOmmlService { get; }
        public IConvertService ConvertService { get; }

        public WordExtensibilityManager(
            IAIAssistantService? aiAssistantService = null,
            IQuestionBankService? questionBankService = null,
            IExamMatrixService? examMatrixService = null,
            ILatexToOmmlService? latexToOmmlService = null,
            IConvertService? convertService = null,
            MatrixExamAI.Shared.AI.IGeminiClient? geminiClient = null)
        {
            var client = geminiClient ?? new GeminiClient();
            AiAssistantService = aiAssistantService ?? new AiAssistantService(client);

            var qb = questionBankService as QuestionBankService ?? new QuestionBankService();
            QuestionBankService = qb;
            ExamMatrixService = examMatrixService ?? qb;

            LatexToOmmlService = latexToOmmlService ?? new LatexToOmmlService();
            ConvertService = convertService ?? new ConvertService(client);
        }

        /// <summary>
        /// Xử lý nút Ribbon 'Soạn thảo AI' (btnAiAuthoring).
        /// </summary>
        public async Task HandleAiAuthoringAsync()
        {
            try
            {
                var docService = ThisAddIn.Current?.DocumentService;
                string selectedText = docService != null ? await docService.GetSelectionTextAsync() : string.Empty;

                if (!string.IsNullOrWhiteSpace(selectedText))
                {
                    // Chuyển sang Sidebar và gửi lệnh xử lý
                    ThisAddIn.Current?.TaskPaneManager?.ShowTab("ai-authoring");

                    var response = await AiAssistantService.ProcessAsync(new AssistantRequest
                    {
                        TaskType = AssistantTaskType.FreeformAuthoring,
                        SelectedText = selectedText,
                        Prompt = "Tối ưu hóa câu từ, bổ sung dữ kiện thiếu và sửa lỗi định dạng cho đoạn văn bản."
                    });

                    ThisAddIn.Current?.TaskPaneManager?.BroadcastEvent("ai/authoringResult", new
                    {
                        success = response.Success,
                        selectedText = selectedText,
                        resultText = response.ResultText,
                        model = response.ModelUsed,
                        suggestions = response.Suggestions
                    });
                }
                else
                {
                    ThisAddIn.Current?.TaskPaneManager?.ShowTab("ai-authoring");
                }
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"[WordExtensibilityManager] HandleAiAuthoringAsync error: {ex.Message}");
            }
        }

        /// <summary>
        /// Xử lý nút Ribbon 'Giải chi tiết' (btnAiExplain).
        /// </summary>
        public async Task HandleAiExplainAsync()
        {
            try
            {
                var docService = ThisAddIn.Current?.DocumentService;
                string selectedText = docService != null ? await docService.GetSelectionTextAsync() : string.Empty;

                if (!string.IsNullOrWhiteSpace(selectedText))
                {
                    ThisAddIn.Current?.TaskPaneManager?.ShowTab("ai-explain");

                    var response = await AiAssistantService.ExplainQuestionAsync(selectedText);

                    ThisAddIn.Current?.TaskPaneManager?.BroadcastEvent("ai/explainResult", new
                    {
                        success = response.Success,
                        selectedText = selectedText,
                        resultText = response.ResultText,
                        model = response.ModelUsed,
                        suggestions = response.Suggestions,
                        tikzCode = response.TikzCode
                    });
                }
                else
                {
                    ThisAddIn.Current?.TaskPaneManager?.ShowTab("ai-explain");
                }
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"[WordExtensibilityManager] HandleAiExplainAsync error: {ex.Message}");
            }
        }

        /// <summary>
        /// Xử lý nút Ribbon 'Kho câu hỏi' (btnQuestionBank).
        /// </summary>
        public void HandleQuestionBank()
        {
            ThisAddIn.Current?.TaskPaneManager?.ShowTab("question-bank");
        }

        /// <summary>
        /// Xử lý nút Ribbon 'Ma trận đề' (btnExamMatrix).
        /// </summary>
        public void HandleExamMatrix()
        {
            ThisAddIn.Current?.TaskPaneManager?.ShowTab("exam-matrix");
        }

        /// <summary>
        /// Xử lý nút Ribbon 'LaTeX -> OMML' (btnConvertLatexToOmml).
        /// </summary>
        public async Task HandleConvertLatexToOmmlAsync()
        {
            try
            {
                var docService = ThisAddIn.Current?.DocumentService;
                string selectedText = docService != null ? await docService.GetSelectionTextAsync() : string.Empty;

                if (!string.IsNullOrWhiteSpace(selectedText) &&
                    (selectedText.Contains("$") || selectedText.Contains("\\") || selectedText.Contains("^") || selectedText.Contains("_")))
                {
                    var result = await LatexToOmmlService.ConvertLatexToOmmlAsync(selectedText, isDisplayMode: false);
                    if (result.Success && docService != null)
                    {
                        await docService.InsertOmmlAtSelectionAsync(result.OmmlXml);
                    }
                    else
                    {
                        ThisAddIn.Current?.TaskPaneManager?.ShowTab("latex-omml");
                    }
                }
                else
                {
                    ThisAddIn.Current?.TaskPaneManager?.ShowTab("latex-omml");
                }
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"[WordExtensibilityManager] HandleConvertLatexToOmmlAsync error: {ex.Message}");
            }
        }

        /// <summary>
        /// Xử lý nút Ribbon 'Convert Đề thi' (btnOpenConvert).
        /// </summary>
        public void HandleConvert()
        {
            ThisAddIn.Current?.TaskPaneManager?.ShowTab("convert");
        }
    }
}
