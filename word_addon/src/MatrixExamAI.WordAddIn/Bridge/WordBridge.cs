using System;
using System.Collections.Generic;
using System.Collections.Concurrent;
using System.IO;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using System.Windows.Forms;
using Microsoft.Web.WebView2.Core;
using Microsoft.Web.WebView2.WinForms;
using MatrixExamAI.WordAddIn.WordInterop;
using MatrixExamAI.Shared.AI;
using MatrixExamAI.Shared.Extensibility;
using MatrixExamAI.Shared.Tikz;
using MatrixExamAI.Shared.Validation;
using MatrixExamAI.WordAddIn;
using SharedModels = MatrixExamAI.Shared.Models;

namespace MatrixExamAI.WordAddIn.Bridge
{
    public class JsonRpcRequest
    {
        public string Id { get; set; } = string.Empty;
        public string Action { get; set; } = string.Empty;
        public JsonElement? Payload { get; set; }
    }

    public class JsonRpcResponse
    {
        public string Id { get; set; } = string.Empty;
        public string Status { get; set; } = "success";
        public object? Data { get; set; }
        public JsonRpcError? Error { get; set; }
    }

    public class JsonRpcError
    {
        public string Code { get; set; } = string.Empty;
        public string Message { get; set; } = string.Empty;
        public string? Details { get; set; }
    }

    public class JsonRpcPushEvent
    {
        public string Event { get; set; } = string.Empty;
        public object? Data { get; set; }
    }

    public class WordBridge : IDisposable
    {
        private readonly WebView2 _webView;
        private readonly Control _ownerControl;
        private readonly IWordDocumentService? _documentService;
        private readonly SynchronizationContext _syncContext;
        private readonly ConcurrentDictionary<string, Func<JsonElement?, Task<object?>>> _handlers;
        private readonly IGeminiClient _geminiClient;
        private readonly ITikzCompiler _tikzCompiler;
        private readonly ITikzAutoHealer _autoHealer;
        private bool _isDisposed;

        public IGeminiClient GeminiClient => _geminiClient;
        public ITikzCompiler TikzCompiler => _tikzCompiler;
        public ITikzAutoHealer AutoHealer => _autoHealer;
        private Extensibility.WordExtensibilityManager? _extensibilityManager;
        public Extensibility.WordExtensibilityManager ExtensibilityManager => _extensibilityManager ??= new Extensibility.WordExtensibilityManager(
            aiAssistantService: new AiAssistantService(_geminiClient),
            convertService: new ConvertService(_geminiClient),
            geminiClient: _geminiClient
        );

        public WordBridge(
            WebView2 webView, 
            Control ownerControl, 
            IWordDocumentService? documentService = null,
            IGeminiClient? geminiClient = null,
            ITikzCompiler? tikzCompiler = null,
            ITikzAutoHealer? autoHealer = null)
        {
            _webView = webView ?? throw new ArgumentNullException(nameof(webView));
            _ownerControl = ownerControl ?? throw new ArgumentNullException(nameof(ownerControl));
            _documentService = documentService;
            _syncContext = SynchronizationContext.Current ?? new WindowsFormsSynchronizationContext();
            _handlers = new ConcurrentDictionary<string, Func<JsonElement?, Task<object?>>>(StringComparer.OrdinalIgnoreCase);

            _geminiClient = geminiClient ?? new GeminiClient();
            _tikzCompiler = tikzCompiler ?? new TikzCompilerService();
            _autoHealer = autoHealer ?? new AutoHealingService(_geminiClient, _tikzCompiler);

            if (_autoHealer is AutoHealingService healingService)
            {
                healingService.ProgressChanged += (s, e) =>
                {
                    SendPushEvent("ai/healingProgress", new
                    {
                        attempt = e.Attempt,
                        maxAttempts = e.MaxAttempts,
                        errorSnippet = e.ErrorSnippet,
                        isSuccess = e.IsSuccess
                    });
                };
            }

            LoadSavedConfiguration();
            RegisterDefaultHandlers();

            if (_documentService != null)
            {
                _documentService.TikzShapeSelected += OnTikzShapeSelected;
            }
        }

        public void Initialize()
        {
            if (_webView.CoreWebView2 != null)
            {
                _webView.CoreWebView2.WebMessageReceived += OnWebMessageReceived;
            }
        }

        #region Handler Registration

        public void RegisterHandler(string action, Func<JsonElement?, Task<object?>> handler)
        {
            _handlers[action] = handler ?? throw new ArgumentNullException(nameof(handler));
        }

        public bool HasHandler(string action) => _handlers.ContainsKey(action);

        public Task<object?> DispatchActionAsync(string action, JsonElement? payload = null)
        {
            if (_handlers.TryGetValue(action, out var handler))
            {
                return handler(payload);
            }
            throw new InvalidOperationException($"No handler registered for action '{action}'.");
        }

        private void RegisterDefaultHandlers()
        {
            // Diagnostics
            RegisterHandler("app/ping", payload => Task.FromResult<object?>(new
            {
                pong = true,
                timestamp = DateTime.UtcNow
            }));

            // Word Selection & Picture Insertion
            RegisterHandler("word/insertPicture", HandleInsertPictureAsync);
            RegisterHandler("word/insertTikz", HandleInsertPictureAsync);
            RegisterHandler("word/updateTikz", HandleUpdatePictureAsync);
            RegisterHandler("word/getSelectedTikz", HandleGetSelectedTikzAsync);
            RegisterHandler("word/getSelectionText", HandleGetSelectionTextAsync);
            RegisterHandler("word/replaceSelectionText", HandleReplaceSelectionTextAsync);
            RegisterHandler("word/insertTextAfterSelection", HandleInsertTextAfterSelectionAsync);

            // TikZ engine wiring
            RegisterHandler("tikz/generate", HandleTikzGenerateAsync);
            RegisterHandler("tikz/compile", HandleTikzCompileAsync);

            // Configuration
            RegisterHandler("system/getConfig", HandleGetConfigAsync);
            RegisterHandler("system/saveConfig", HandleSaveConfigAsync);

            // Extensibility: Phase 2 AI Assistant
            RegisterHandler("ai/assistant", HandleAiAssistantAsync);

            // Extensibility: Phase 3 Question Bank & Matrix
            RegisterHandler("questionBank/search", HandleQuestionBankSearchAsync);
            RegisterHandler("questionBank/insert", HandleQuestionBankInsertAsync);
            RegisterHandler("questionBank/delete", HandleQuestionBankDeleteAsync);
            RegisterHandler("examMatrix/generate", HandleExamMatrixGenerateAsync);

            // Extensibility: Phase 4 & Phase 5 LaTeX to OMML, MathType & Formatting
            RegisterHandler("latex/convertOmml", HandleConvertLatexOmmlAsync);
            RegisterHandler("latex/convertSelection", HandleConvertSelectionLatexAsync);
            RegisterHandler("latex/convertAllInDoc", HandleConvertAllLatexInDocAsync);
            RegisterHandler("word/insertOmml", HandleInsertOmmlAsync);
            RegisterHandler("word/standardizeDocument", HandleStandardizeDocumentAsync);
            RegisterHandler("mathtype/scan", HandleMathTypeScanAsync);
            RegisterHandler("mathtype/convert", HandleMathTypeConvertAsync);

            // Extensibility: Convert AI Vision & Text/LaTeX (Ảnh / Text / Clipboard -> Đề thi Word)
            RegisterHandler("convert/extract", HandleConvertExtractAsync);
            RegisterHandler("convert/saveToBank", HandleConvertSaveToBankAsync);
            RegisterHandler("convert/parseText", HandleConvertParseTextAsync);
            RegisterHandler("convert/getPromptTemplate", HandleConvertGetPromptTemplateAsync);

            // Native Windows Clipboard
            RegisterHandler("clipboard/getImage", HandleClipboardGetImageAsync);
        }

        #endregion

        #region Message Handling

        private async void OnWebMessageReceived(object? sender, CoreWebView2WebMessageReceivedEventArgs e)
        {
            string? rawMessage = null;
            try
            {
                try
                {
                    rawMessage = e.TryGetWebMessageAsString();
                }
                catch
                {
                    // If message is not a string, TryGetWebMessageAsString throws E_INVALIDARG (0x80070057)
                }

                if (string.IsNullOrWhiteSpace(rawMessage))
                {
                    try
                    {
                        rawMessage = e.WebMessageAsJson;
                    }
                    catch { }
                }

                if (string.IsNullOrWhiteSpace(rawMessage))
                {
                    AddInLog.Log("[WordBridge] Received empty message from WebView2.");
                    return;
                }

                string previewSnippet = rawMessage.Length > 100 ? rawMessage.Substring(0, 100) + "..." : rawMessage;
                AddInLog.Log($"[WordBridge] OnWebMessageReceived: {previewSnippet}");

                var request = JsonSerializer.Deserialize<JsonRpcRequest>(rawMessage, new JsonSerializerOptions
                {
                    PropertyNameCaseInsensitive = true
                });

                if (request == null || string.IsNullOrWhiteSpace(request.Action))
                {
                    AddInLog.Log("[WordBridge] Could not parse valid JsonRpcRequest or action is empty.");
                    return;
                }

                AddInLog.Log($"[WordBridge] Dispatching action '{request.Action}', Id='{request.Id}'");
                await DispatchRequestAsync(request);
            }
            catch (Exception ex)
            {
                AddInLog.LogError("[WordBridge] Error in OnWebMessageReceived", ex);
            }
        }

        private async Task DispatchRequestAsync(JsonRpcRequest request)
        {
            string reqId = request.Id;
            try
            {
                if (_handlers.TryGetValue(request.Action, out var handler))
                {
                    object? result = await handler(request.Payload);
                    AddInLog.Log($"[WordBridge] Handler for '{request.Action}' succeeded. Sending success response.");
                    SendResponse(new JsonRpcResponse
                    {
                        Id = reqId,
                        Status = "success",
                        Data = result
                    });
                }
                else
                {
                    AddInLog.Log($"[WordBridge] Handler for '{request.Action}' NOT FOUND.");
                    SendResponse(new JsonRpcResponse
                    {
                        Id = reqId,
                        Status = "error",
                        Error = new JsonRpcError
                        {
                            Code = "METHOD_NOT_FOUND",
                            Message = $"No handler registered for action '{request.Action}'."
                        }
                    });
                }
            }
            catch (Exception ex)
            {
                AddInLog.LogError($"[WordBridge] Exception in handler '{request.Action}'", ex);
                SendResponse(new JsonRpcResponse
                {
                    Id = reqId,
                    Status = "error",
                    Error = new JsonRpcError
                    {
                        Code = "INTERNAL_ERROR",
                        Message = ex.Message,
                        Details = ex.StackTrace
                    }
                });
            }
        }

        #endregion

        #region Default Handler Implementations

        private async Task<object?> HandleInsertPictureAsync(JsonElement? payload)
        {
            if (_documentService == null)
            {
                throw new InvalidOperationException("Word document service is not connected.");
            }

            string imagePath = string.Empty;
            string tikzCode = string.Empty;

            if (payload.HasValue)
            {
                if (payload.Value.TryGetProperty("imagePath", out var pPath))
                    imagePath = pPath.GetString() ?? string.Empty;
                else if (payload.Value.TryGetProperty("imageBase64", out var pBase64))
                    imagePath = pBase64.GetString() ?? string.Empty;

                if (payload.Value.TryGetProperty("tikzCode", out var pTikz))
                    tikzCode = pTikz.GetString() ?? string.Empty;
            }

            // Auto-compile if imagePath is empty but tikzCode is present
            if (string.IsNullOrWhiteSpace(imagePath) && !string.IsNullOrWhiteSpace(tikzCode))
            {
                var compRes = await _tikzCompiler.CompileAsync(new SharedModels.TikzCompileRequest
                {
                    TikzCode = tikzCode,
                    Format = SharedModels.TikzExportFormat.Png
                });

                if (compRes.Success && !string.IsNullOrWhiteSpace(compRes.ImagePath))
                {
                    imagePath = compRes.ImagePath!;
                }
                else
                {
                    throw new InvalidOperationException($"Không thể biên dịch hình ảnh trước khi chèn vào Word: {compRes.ErrorMessage}");
                }
            }

            if (string.IsNullOrWhiteSpace(imagePath))
            {
                throw new ArgumentException("Missing imagePath or tikzCode in payload.");
            }

            bool success = await InvokeOnStaThreadAsync(async () =>
            {
                return await _documentService.InsertPictureAtSelectionAsync(imagePath, tikzCode);
            });

            return new { success, shapeTitle = "MatrixExamAI:TikZ", imagePath };
        }

        private async Task<object?> HandleUpdatePictureAsync(JsonElement? payload)
        {
            if (_documentService == null)
            {
                throw new InvalidOperationException("Word document service is not connected.");
            }

            string imagePath = string.Empty;
            string tikzCode = string.Empty;

            if (payload.HasValue)
            {
                if (payload.Value.TryGetProperty("imagePath", out var pPath))
                    imagePath = pPath.GetString() ?? string.Empty;
                else if (payload.Value.TryGetProperty("imageBase64", out var pBase64))
                    imagePath = pBase64.GetString() ?? string.Empty;

                if (payload.Value.TryGetProperty("tikzCode", out var pTikz))
                    tikzCode = pTikz.GetString() ?? string.Empty;
            }

            bool success = await InvokeOnStaThreadAsync(async () =>
            {
                return await _documentService.UpdateSelectedPictureAsync(imagePath, tikzCode);
            });

            return new { success, isUpdated = success };
        }

        private async Task<object?> HandleGetSelectedTikzAsync(JsonElement? payload)
        {
            if (_documentService == null)
            {
                return new { hasTikz = false, tikzCode = string.Empty };
            }

            string tikzCode = await InvokeOnStaThreadAsync(async () =>
            {
                return await _documentService.GetSelectedShapeTikzCodeAsync();
            });

            bool hasTikz = !string.IsNullOrWhiteSpace(tikzCode);
            return new { hasTikz, tikzCode };
        }

        private async Task<object?> HandleGetSelectionTextAsync(JsonElement? payload)
        {
            if (_documentService == null)
            {
                return new { text = string.Empty };
            }

            string text = await InvokeOnStaThreadAsync(async () =>
            {
                return await _documentService.GetSelectionTextAsync();
            });

            return new { text };
        }

        private async Task<object?> HandleReplaceSelectionTextAsync(JsonElement? payload)
        {
            if (_documentService == null)
            {
                return new { success = false };
            }

            string newText = string.Empty;
            if (payload.HasValue)
            {
                if (payload.Value.TryGetProperty("newText", out var pNew))
                {
                    newText = pNew.GetString() ?? string.Empty;
                }
                else if (payload.Value.TryGetProperty("text", out var pTxt))
                {
                    newText = pTxt.GetString() ?? string.Empty;
                }
            }

            bool success = await InvokeOnStaThreadAsync(async () =>
            {
                return await _documentService.ReplaceSelectionTextAsync(newText);
            });

            return new { success };
        }

        private async Task<object?> HandleInsertTextAfterSelectionAsync(JsonElement? payload)
        {
            if (_documentService == null)
            {
                return new { success = false };
            }

            string text = string.Empty;
            List<QuestionItem>? questions = null;

            if (payload.HasValue)
            {
                var root = payload.Value;
                if (root.TryGetProperty("questions", out var pQs) && pQs.ValueKind == JsonValueKind.Array)
                {
                    try
                    {
                        var json = pQs.GetRawText();
                        questions = JsonSerializer.Deserialize<List<QuestionItem>>(json, new JsonSerializerOptions { PropertyNameCaseInsensitive = true });
                    }
                    catch { }
                }

                if (root.TryGetProperty("text", out var pTxt))
                {
                    text = pTxt.GetString() ?? string.Empty;
                }
                else if (root.TryGetProperty("newText", out var pNew))
                {
                    text = pNew.GetString() ?? string.Empty;
                }
            }

            if ((questions == null || questions.Count == 0) && !string.IsNullOrWhiteSpace(text))
            {
                bool hasExamQuestions = System.Text.RegularExpressions.Regex.IsMatch(text, @"(?m)^(?:%?\s*(?:Câu|Bài|CÂU|BÀI)\s*\d+[:.]|===CAU===|\\begin\{(?:ex|bt)\})");
                if (hasExamQuestions)
                {
                    if (ExtensibilityManager.ConvertService != null)
                    {
                        var cRes = ExtensibilityManager.ConvertService.ParseTextDirectly(text);
                        if (cRes?.Questions != null && cRes.Questions.Count > 0)
                        {
                            questions = cRes.Questions;
                        }
                    }
                    if (questions == null || questions.Count == 0)
                    {
                        var parseRes = QuestionParserEngine.ParseQuestions(text);
                        if (parseRes?.Questions != null && parseRes.Questions.Count > 0)
                        {
                            questions = parseRes.Questions;
                        }
                    }
                }
            }

            bool success = await InvokeOnStaThreadAsync(async () =>
            {
                if (questions != null && questions.Count > 0)
                {
                    return await _documentService.InsertStandardizedExamAsync(questions);
                }
                return await _documentService.InsertTextAfterSelectionAsync(text);
            });

            return new { success };
        }

        private async Task<object?> HandleTikzGenerateAsync(JsonElement? payload)
        {
            string prompt = string.Empty;
            string? imageBase64 = null;
            string imageMimeType = "image/png";
            SharedModels.DiagramType diagramType = SharedModels.DiagramType.Custom;
            string? extraPrompt = null;
            bool enableNotes = true;
            bool bbtNoFrame = false;
            string? modelOverride = null;

            if (payload.HasValue)
            {
                var root = payload.Value;
                if (root.TryGetProperty("prompt", out var pPrompt))
                    prompt = pPrompt.GetString() ?? string.Empty;

                if (root.TryGetProperty("imageBase64", out var pImage))
                    imageBase64 = pImage.GetString();

                if (root.TryGetProperty("imageMimeType", out var pMime))
                    imageMimeType = pMime.GetString() ?? "image/png";

                if (root.TryGetProperty("diagramType", out var pType))
                {
                    string typeStr = pType.GetString() ?? string.Empty;
                    if (string.Equals(typeStr, "BBT", StringComparison.OrdinalIgnoreCase) || typeStr.IndexOf("bbt", StringComparison.OrdinalIgnoreCase) >= 0)
                        diagramType = SharedModels.DiagramType.BBT;
                    else if (string.Equals(typeStr, "BXD", StringComparison.OrdinalIgnoreCase) || typeStr.IndexOf("bxd", StringComparison.OrdinalIgnoreCase) >= 0)
                        diagramType = SharedModels.DiagramType.BXD;
                    else if (string.Equals(typeStr, "DoThi", StringComparison.OrdinalIgnoreCase) || typeStr.IndexOf("dothi", StringComparison.OrdinalIgnoreCase) >= 0)
                        diagramType = SharedModels.DiagramType.DoThi;
                    else if (string.Equals(typeStr, "HinhKhongGian", StringComparison.OrdinalIgnoreCase) || typeStr.IndexOf("khonggian", StringComparison.OrdinalIgnoreCase) >= 0 || typeStr.IndexOf("3d", StringComparison.OrdinalIgnoreCase) >= 0)
                        diagramType = SharedModels.DiagramType.HinhKhongGian;
                }

                if (root.TryGetProperty("extraPrompt", out var pExtra))
                    extraPrompt = pExtra.GetString();

                if (root.TryGetProperty("enableNotes", out var pNotes) && pNotes.ValueKind == JsonValueKind.False)
                    enableNotes = false;

                if (root.TryGetProperty("bbtNoFrame", out var pNoFrame) && pNoFrame.ValueKind == JsonValueKind.True)
                    bbtNoFrame = true;

                if (root.TryGetProperty("modelOverride", out var pModel))
                    modelOverride = pModel.GetString();
            }

            var request = new SharedModels.TikzPromptRequest
            {
                Prompt = prompt,
                ImageBase64 = imageBase64,
                ImageMimeType = imageMimeType,
                DiagramType = diagramType,
                ExtraPrompt = extraPrompt,
                EnableNotes = enableNotes,
                BbtNoFrame = bbtNoFrame,
                ModelOverride = modelOverride
            };

            AddInLog.Log($"[TikzGenerate] Starting TikZ generation. Prompt='{prompt}', DiagramType={diagramType}, HasImage={!string.IsNullOrEmpty(imageBase64)}");
            var genResult = await _geminiClient.GenerateTikzAsync(request);
            AddInLog.Log($"[TikzGenerate] Finished. Success={genResult.Success}, Model={genResult.ModelUsed}, Provider={genResult.ProviderUsed}, Elapsed={genResult.ExecutionTimeMs}ms, Error={genResult.ErrorMessage}");

            return new
            {
                success = genResult.Success,
                tikzCode = genResult.TikzCode,
                model = genResult.ModelUsed,
                provider = genResult.ProviderUsed,
                executionTimeMs = genResult.ExecutionTimeMs,
                errorMessage = genResult.ErrorMessage
            };
        }

        private async Task<object?> HandleTikzCompileAsync(JsonElement? payload)
        {
            string tikzCode = string.Empty;
            SharedModels.TikzExportFormat format = SharedModels.TikzExportFormat.Png;
            string border = "2pt";
            bool autoHeal = true;

            if (payload.HasValue)
            {
                var root = payload.Value;
                if (root.TryGetProperty("tikzCode", out var pCode))
                    tikzCode = pCode.GetString() ?? string.Empty;

                if (root.TryGetProperty("format", out var pFormat))
                {
                    string fmtStr = pFormat.GetString() ?? "png";
                    if (string.Equals(fmtStr, "svg", StringComparison.OrdinalIgnoreCase))
                        format = SharedModels.TikzExportFormat.Svg;
                    else if (string.Equals(fmtStr, "emf", StringComparison.OrdinalIgnoreCase))
                        format = SharedModels.TikzExportFormat.Emf;
                }

                if (root.TryGetProperty("border", out var pBorder))
                    border = pBorder.GetString() ?? "2pt";

                if (root.TryGetProperty("autoHeal", out var pHeal) && pHeal.ValueKind == JsonValueKind.False)
                    autoHeal = false;
            }

            AddInLog.Log($"[TikzCompile] Starting compilation. Format={format}, Border='{border}', CodeLength={tikzCode.Length}");

            var compileReq = new SharedModels.TikzCompileRequest
            {
                TikzCode = tikzCode,
                Format = format,
                Border = border
            };

            var compileResult = await _tikzCompiler.CompileAsync(compileReq).ConfigureAwait(false);

            // Auto-healing fallback if compilation failed and auto-healing is enabled
            if (!compileResult.Success && autoHeal && _autoHealer != null && _geminiClient.KeyPool.TotalKeys > 0)
            {
                AddInLog.Log($"[TikzCompile] Initial compile failed ({compileResult.ErrorMessage}), triggering auto-healing...");
                SendPushEvent("ai/healingProgress", new
                {
                    attempt = 1,
                    errorSnippet = compileResult.ErrorMessage
                });

                var healResult = await _autoHealer.AutoHealAsync(
                    tikzCode,
                    compileResult.RawLatexLog ?? string.Empty,
                    new SharedModels.TikzPromptRequest { Prompt = "Sửa lỗi cú pháp TikZ" }).ConfigureAwait(false);

                if (healResult.Success && !string.IsNullOrWhiteSpace(healResult.TikzCode))
                {
                    tikzCode = healResult.TikzCode;
                    compileReq.TikzCode = tikzCode;
                    compileResult = await _tikzCompiler.CompileAsync(compileReq).ConfigureAwait(false);
                    AddInLog.Log($"[TikzCompile] After auto-heal compile. Success={compileResult.Success}");
                }
            }

            AddInLog.Log($"[TikzCompile] Finished. Success={compileResult.Success}, ImagePath='{compileResult.ImagePath}', PreviewLength={compileResult.PreviewDataUrl?.Length ?? 0}, Elapsed={compileResult.CompilationTimeMs}ms, Error={compileResult.ErrorMessage}");

            return new
            {
                success = compileResult.Success,
                imagePath = compileResult.ImagePath ?? string.Empty,
                previewDataUrl = compileResult.PreviewDataUrl ?? string.Empty,
                format = compileResult.Format.ToString().ToLowerInvariant(),
                errorMessage = compileResult.ErrorMessage,
                compilationTimeMs = compileResult.CompilationTimeMs,
                parsedError = compileResult.ParsedError?.ToString(),
                rawLog = compileResult.RawLatexLog
            };
        }

        private Task<object?> HandleGetConfigAsync(JsonElement? payload)
        {
            string appData = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "MatrixExamAI");
            string configFile = Path.Combine(appData, "config.json");
            if (File.Exists(configFile))
            {
                string json = File.ReadAllText(configFile);
                var doc = JsonDocument.Parse(json);
                return Task.FromResult<object?>(doc.RootElement);
            }

            return Task.FromResult<object?>(new
            {
                provider = "gemini",
                model = _geminiClient.DefaultModel,
                hasApiKey = _geminiClient.KeyPool.TotalKeys > 0
            });
        }

        private Task<object?> HandleSaveConfigAsync(JsonElement? payload)
        {
            if (payload.HasValue)
            {
                string appData = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "MatrixExamAI");
                Directory.CreateDirectory(appData);
                string configFile = Path.Combine(appData, "config.json");
                File.WriteAllText(configFile, payload.Value.GetRawText());

                ApplyConfigElement(payload.Value);
            }

            return Task.FromResult<object?>(new { saved = true });
        }

        private void LoadSavedConfiguration()
        {
            try
            {
                string appData = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "MatrixExamAI");
                string configFile = Path.Combine(appData, "config.json");
                if (File.Exists(configFile))
                {
                    string json = File.ReadAllText(configFile);
                    using var doc = JsonDocument.Parse(json);
                    ApplyConfigElement(doc.RootElement);
                }

                if (_geminiClient.KeyPool.TotalKeys == 0)
                {
                    string? envKey = Environment.GetEnvironmentVariable("GEMINI_API_KEY") 
                                  ?? Environment.GetEnvironmentVariable("GOOGLE_API_KEY");
                    if (!string.IsNullOrWhiteSpace(envKey))
                    {
                        _geminiClient.KeyPool.AddKey(envKey!.Trim());
                    }
                }
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"[WordBridge] LoadSavedConfiguration error: {ex.Message}");
            }
        }

        private void ApplyConfigElement(JsonElement root)
        {
            if (root.TryGetProperty("apiKey", out var pKey) && !string.IsNullOrWhiteSpace(pKey.GetString()))
            {
                _geminiClient.KeyPool.SetKeys(new[] { pKey.GetString()! });
            }
            if (root.TryGetProperty("model", out var pModel) && !string.IsNullOrWhiteSpace(pModel.GetString()))
            {
                _geminiClient.DefaultModel = pModel.GetString()!;
            }
            if (root.TryGetProperty("nineRouterApiKey", out var p9R) && !string.IsNullOrWhiteSpace(p9R.GetString()))
            {
                _geminiClient.Fallback.NineRouterApiKey = p9R.GetString();
            }
            if (root.TryGetProperty("openAiApiKey", out var pOai) && !string.IsNullOrWhiteSpace(pOai.GetString()))
            {
                _geminiClient.Fallback.OpenAiApiKey = pOai.GetString();
            }
        }

        #endregion

        #region Push Events and Response Dispatch

        public void SendResponse(JsonRpcResponse response)
        {
            if (_isDisposed || _webView.CoreWebView2 == null) return;

            string json = JsonSerializer.Serialize(response, new JsonSerializerOptions
            {
                PropertyNamingPolicy = JsonNamingPolicy.CamelCase
            });

            PostToWebView(json);
        }

        public void SendPushEvent(string eventName, object? data)
        {
            if (_isDisposed || _webView.CoreWebView2 == null) return;

            var pushEvent = new JsonRpcPushEvent
            {
                Event = eventName,
                Data = data
            };

            string json = JsonSerializer.Serialize(pushEvent, new JsonSerializerOptions
            {
                PropertyNamingPolicy = JsonNamingPolicy.CamelCase
            });

            PostToWebView(json);
        }

        private void PostToWebView(string json)
        {
            if (_ownerControl.InvokeRequired)
            {
                _ownerControl.BeginInvoke(new Action(() =>
                {
                    try
                    {
                        _webView.CoreWebView2?.PostWebMessageAsJson(json);
                        AddInLog.Log("[WordBridge] PostWebMessageAsJson dispatched via BeginInvoke.");
                    }
                    catch (Exception ex)
                    {
                        AddInLog.LogError("[WordBridge] PostToWebView (BeginInvoke) error", ex);
                    }
                }));
            }
            else
            {
                try
                {
                    _webView.CoreWebView2?.PostWebMessageAsJson(json);
                    AddInLog.Log("[WordBridge] PostWebMessageAsJson dispatched synchronously.");
                }
                catch (Exception ex)
                {
                    AddInLog.LogError("[WordBridge] PostToWebView (Sync) error", ex);
                }
            }
        }

        private void OnTikzShapeSelected(object? sender, TikzShapeSelectedEventArgs e)
        {
            SendPushEvent("word/selectionChanged", new
            {
                hasTikzShape = e.HasTikzShape,
                hasSelectedShape = e.HasTikzShape,
                isTikZ = e.HasTikzShape,
                tikzCode = e.TikzCode,
                shapeTitle = e.ShapeTitle,
                shapeId = e.ShapeId
            });
        }

        #endregion

        #region STA Thread Marshaling

        public async Task<T> InvokeOnStaThreadAsync<T>(Func<Task<T>> asyncFunc)
        {
            if (_ownerControl.InvokeRequired)
            {
                var tcs = new TaskCompletionSource<T>();
                _ownerControl.BeginInvoke(new Action(async () =>
                {
                    try
                    {
                        var res = await asyncFunc();
                        tcs.SetResult(res);
                    }
                    catch (Exception ex)
                    {
                        tcs.SetException(ex);
                    }
                }));
                return await tcs.Task;
            }

            return await asyncFunc();
        }

        public Task<T> InvokeOnStaThreadAsync<T>(Func<T> syncFunc)
        {
            if (_ownerControl.InvokeRequired)
            {
                var tcs = new TaskCompletionSource<T>();
                _ownerControl.BeginInvoke(new Action(() =>
                {
                    try
                    {
                        var res = syncFunc();
                        tcs.SetResult(res);
                    }
                    catch (Exception ex)
                    {
                        tcs.SetException(ex);
                    }
                }));
                return tcs.Task;
            }

            return Task.FromResult(syncFunc());
        }

        #endregion

        #region Extensibility Handlers

        private async Task<object?> HandleAiAssistantAsync(JsonElement? payload)
        {
            string prompt = string.Empty;
            string selectedText = string.Empty;
            string taskTypeStr = "explain";

            if (payload.HasValue)
            {
                var root = payload.Value;
                if (root.TryGetProperty("prompt", out var pPrompt)) prompt = pPrompt.GetString() ?? string.Empty;
                if (root.TryGetProperty("selectedText", out var pText)) selectedText = pText.GetString() ?? string.Empty;
                if (root.TryGetProperty("taskType", out var pType)) taskTypeStr = pType.GetString() ?? "explain";
            }

            if (string.IsNullOrWhiteSpace(selectedText) && _documentService != null)
            {
                selectedText = await _documentService.GetSelectionTextAsync().ConfigureAwait(false);
            }

            var taskType = Shared.Extensibility.AssistantTaskType.ExplainQuestion;
            if (string.Equals(taskTypeStr, "rewrite", StringComparison.OrdinalIgnoreCase))
                taskType = Shared.Extensibility.AssistantTaskType.RewriteMathProblem;
            else if (string.Equals(taskTypeStr, "solve", StringComparison.OrdinalIgnoreCase))
                taskType = Shared.Extensibility.AssistantTaskType.GenerateSolution;
            else if (string.Equals(taskTypeStr, "authoring", StringComparison.OrdinalIgnoreCase))
                taskType = Shared.Extensibility.AssistantTaskType.FreeformAuthoring;

            var response = await ExtensibilityManager.AiAssistantService.ProcessAsync(new Shared.Extensibility.AssistantRequest
            {
                TaskType = taskType,
                SelectedText = selectedText,
                Prompt = prompt
            }).ConfigureAwait(false);

            return new
            {
                success = response.Success,
                resultText = response.ResultText,
                tikzCode = response.TikzCode,
                suggestions = response.Suggestions,
                model = response.ModelUsed,
                latencyMs = response.LatencyMs,
                errorMessage = response.ErrorMessage
            };
        }

        private async Task<object?> HandleQuestionBankSearchAsync(JsonElement? payload)
        {
            string? keyword = null;
            string? subject = null;
            int? grade = null;
            string? topic = null;
            string? level = null;
            string? qtype = null;
            int limit = 50;

            if (payload.HasValue)
            {
                var root = payload.Value;
                if (root.TryGetProperty("keyword", out var pKw) && pKw.ValueKind == JsonValueKind.String) keyword = pKw.GetString();
                if (root.TryGetProperty("subject", out var pSubj) && pSubj.ValueKind == JsonValueKind.String) subject = pSubj.GetString();
                if (root.TryGetProperty("grade", out var pGr) && pGr.ValueKind == JsonValueKind.Number && pGr.TryGetInt32(out int gVal)) grade = gVal;
                if (root.TryGetProperty("topic", out var pTop) && pTop.ValueKind == JsonValueKind.String) topic = pTop.GetString();
                if (root.TryGetProperty("level", out var pLev) && pLev.ValueKind == JsonValueKind.String) level = pLev.GetString();
                if (root.TryGetProperty("questionType", out var pQt) && pQt.ValueKind == JsonValueKind.String) qtype = pQt.GetString();
                if (root.TryGetProperty("limit", out var pLim) && pLim.ValueKind == JsonValueKind.Number && pLim.TryGetInt32(out int lVal)) limit = lVal;
            }

            // Tự động nạp ngân hàng mẫu chuẩn BGD nếu CSDL đang trống
            if (await ExtensibilityManager.QuestionBankService.GetQuestionCountAsync().ConfigureAwait(false) == 0)
            {
                if (ExtensibilityManager.QuestionBankService is MatrixExamAI.Shared.Extensibility.QuestionBankService qbs)
                {
                    await qbs.SeedDefaultQuestionsAsync().ConfigureAwait(false);
                }
            }

            var list = await ExtensibilityManager.QuestionBankService.SearchQuestionsAsync(
                keyword, subject, grade, topic, level, qtype, limit).ConfigureAwait(false);

            return new
            {
                success = true,
                count = list.Count,
                questions = list
            };
        }

        private async Task<object?> HandleQuestionBankInsertAsync(JsonElement? payload)
        {
            if (!payload.HasValue) return new { success = false, message = "Payload rỗng." };

            var root = payload.Value;
            var item = new Shared.Extensibility.QuestionItem();

            if (root.TryGetProperty("questionCode", out var pCode)) item.QuestionCode = pCode.GetString() ?? string.Empty;
            if (root.TryGetProperty("subject", out var pSubj)) item.Subject = pSubj.GetString() ?? "Toán";
            if (root.TryGetProperty("grade", out var pGr) && pGr.TryGetInt32(out int gVal)) item.Grade = gVal;
            if (root.TryGetProperty("topic", out var pTop)) item.Topic = pTop.GetString() ?? string.Empty;
            if (root.TryGetProperty("cognitiveLevel", out var pLev)) item.CognitiveLevel = pLev.GetString() ?? "Thông hiểu";
            if (root.TryGetProperty("questionType", out var pQt)) item.QuestionType = pQt.GetString() ?? "MultipleChoice4";
            if (root.TryGetProperty("content", out var pCont)) item.Content = pCont.GetString() ?? string.Empty;
            if (root.TryGetProperty("correctAnswer", out var pAns)) item.CorrectAnswer = pAns.GetString() ?? string.Empty;
            if (root.TryGetProperty("explanation", out var pExp)) item.Explanation = pExp.GetString() ?? string.Empty;
            if (root.TryGetProperty("tikzCode", out var pTikz)) item.TikzCode = pTikz.GetString() ?? string.Empty;

            long id = await ExtensibilityManager.QuestionBankService.InsertQuestionAsync(item).ConfigureAwait(false);
            return new { success = true, id = id };
        }

        private async Task<object?> HandleQuestionBankDeleteAsync(JsonElement? payload)
        {
            if (!payload.HasValue) return new { success = false, message = "Payload rỗng." };
            long id = 0;
            if (payload.Value.TryGetProperty("id", out var pId) && pId.TryGetInt64(out long idVal))
            {
                id = idVal;
            }
            if (id <= 0) return new { success = false, message = "ID không hợp lệ." };

            bool ok = await ExtensibilityManager.QuestionBankService.DeleteQuestionAsync(id).ConfigureAwait(false);
            return new { success = ok };
        }

        private async Task<object?> HandleExamMatrixGenerateAsync(JsonElement? payload)
        {
            var config = new Shared.Extensibility.ExamMatrixConfig();

            if (payload.HasValue)
            {
                var root = payload.Value;
                if (root.TryGetProperty("title", out var pTitle)) config.Title = pTitle.GetString() ?? config.Title;
                if (root.TryGetProperty("subject", out var pSubj)) config.Subject = pSubj.GetString() ?? config.Subject;
                if (root.TryGetProperty("grade", out var pGr) && pGr.TryGetInt32(out int gVal)) config.Grade = gVal;
                if (root.TryGetProperty("part1Count", out var pP1) && pP1.TryGetInt32(out int p1Val)) config.Part1Count = p1Val;
                if (root.TryGetProperty("part2Count", out var pP2) && pP2.TryGetInt32(out int p2Val)) config.Part2Count = p2Val;
                if (root.TryGetProperty("part3Count", out var pP3) && pP3.TryGetInt32(out int p3Val)) config.Part3Count = p3Val;
            }

            var draft = await ExtensibilityManager.ExamMatrixService.GenerateExamFromMatrixAsync(
                config, ExtensibilityManager.QuestionBankService).ConfigureAwait(false);

            return new
            {
                success = draft.Success,
                title = draft.Title,
                totalQuestions = draft.TotalSelectedQuestions,
                part1 = draft.Part1Questions,
                part2 = draft.Part2Questions,
                part3 = draft.Part3Questions,
                errorMessage = draft.ErrorMessage
            };
        }

        private async Task<object?> HandleConvertLatexOmmlAsync(JsonElement? payload)
        {
            string latex = string.Empty;
            bool isDisplayMode = false;

            if (payload.HasValue)
            {
                var root = payload.Value;
                if (root.TryGetProperty("latex", out var pLatex)) latex = pLatex.GetString() ?? string.Empty;
                if (root.TryGetProperty("isDisplayMode", out var pDisp) && pDisp.ValueKind == JsonValueKind.True) isDisplayMode = true;
            }

            if (string.IsNullOrWhiteSpace(latex) && _documentService != null)
            {
                latex = await _documentService.GetSelectionTextAsync().ConfigureAwait(false);
            }

            var result = await ExtensibilityManager.LatexToOmmlService.ConvertLatexToOmmlAsync(latex, isDisplayMode).ConfigureAwait(false);
            return new
            {
                success = result.Success,
                originalLatex = result.OriginalLatex,
                ommlXml = result.OmmlXml,
                latencyMs = result.LatencyMs,
                errorMessage = result.ErrorMessage
            };
        }

        private async Task<object?> HandleInsertOmmlAsync(JsonElement? payload)
        {
            string ommlXml = string.Empty;
            string latex = string.Empty;

            if (payload.HasValue)
            {
                var root = payload.Value;
                if (root.TryGetProperty("ommlXml", out var pXml)) ommlXml = pXml.GetString() ?? string.Empty;
                if (root.TryGetProperty("latex", out var pLatex)) latex = pLatex.GetString() ?? string.Empty;
            }

            if (string.IsNullOrWhiteSpace(ommlXml) && !string.IsNullOrWhiteSpace(latex))
            {
                var res = await ExtensibilityManager.LatexToOmmlService.ConvertLatexToOmmlAsync(latex);
                if (res.Success) ommlXml = res.OmmlXml;
            }

            if (string.IsNullOrWhiteSpace(ommlXml))
            {
                return new { success = false, message = "OMML XML rỗng." };
            }

            if (_documentService == null)
            {
                return new { success = false, message = "Word document service chưa sẵn sàng." };
            }

            bool ok = await _documentService.InsertOmmlAtSelectionAsync(ommlXml);
            return new { success = ok };
        }

        private async Task<object?> HandleStandardizeDocumentAsync(JsonElement? payload)
        {
            if (_documentService == null)
            {
                return new { success = false, message = "Word document service chưa sẵn sàng." };
            }

            string fontName = "Times New Roman";
            float fontSize = 12f;
            float lineSpacing = 1.15f;
            bool entireDoc = false;

            if (payload.HasValue)
            {
                var root = payload.Value;
                if (root.TryGetProperty("fontName", out var pFont) && !string.IsNullOrWhiteSpace(pFont.GetString()))
                    fontName = pFont.GetString()!;
                if (root.TryGetProperty("fontSize", out var pSize) && pSize.TryGetSingle(out float sVal))
                    fontSize = sVal;
                if (root.TryGetProperty("lineSpacing", out var pSpacing) && pSpacing.TryGetSingle(out float spVal))
                    lineSpacing = spVal;
                if (root.TryGetProperty("entireDocument", out var pEntire) && pEntire.ValueKind == JsonValueKind.True)
                    entireDoc = true;
            }

            bool ok = await _documentService.StandardizeDocumentFormattingAsync(fontName, fontSize, lineSpacing, entireDoc).ConfigureAwait(false);
            return new { success = ok };
        }

        private async Task<object?> HandleConvertSelectionLatexAsync(JsonElement? payload)
        {
            if (_documentService == null)
            {
                return new { success = false, message = "Word document service chưa sẵn sàng." };
            }

            string latex = await _documentService.GetSelectionTextAsync().ConfigureAwait(false);
            if (string.IsNullOrWhiteSpace(latex))
            {
                return new { success = false, message = "Vui lòng bôi đen công thức LaTeX trong Word trước khi bấm chuyển đổi." };
            }

            var result = await ExtensibilityManager.LatexToOmmlService.ConvertLatexToOmmlAsync(latex, isDisplayMode: false).ConfigureAwait(false);
            if (!result.Success || string.IsNullOrWhiteSpace(result.OmmlXml))
            {
                return new { success = false, message = result.ErrorMessage ?? "Không thể phân tích cú pháp LaTeX sang OMML." };
            }

            bool ok = await _documentService.InsertOmmlAtSelectionAsync(result.OmmlXml).ConfigureAwait(false);
            return new
            {
                success = ok,
                originalLatex = latex,
                ommlXml = result.OmmlXml,
                latencyMs = result.LatencyMs
            };
        }

        private async Task<object?> HandleConvertAllLatexInDocAsync(JsonElement? payload)
        {
            if (_documentService == null)
            {
                return new { success = false, message = "Word document service chưa sẵn sàng." };
            }

            int count = await _documentService.ConvertAllLatexInDocumentAsync().ConfigureAwait(false);
            return new
            {
                success = true,
                count = count,
                message = count > 0 
                    ? $"Đã chuyển đổi thành công {count} công thức LaTeX sang Word Native OMML!" 
                    : "Không tìm thấy công thức LaTeX ($...$) nào trong tài liệu."
            };
        }

        private async Task<object?> HandleMathTypeScanAsync(JsonElement? payload)
        {
            if (_documentService == null)
            {
                return new { success = false, message = "Word document service chưa sẵn sàng." };
            }

            string? docxPath = null;
            if (payload.HasValue && payload.Value.TryGetProperty("docxPath", out var pPath))
            {
                docxPath = pPath.GetString();
            }

            var (success, count, report) = await _documentService.ScanMathTypeFormulasAsync(docxPath).ConfigureAwait(false);
            return new
            {
                success = success,
                oleCount = count,
                report = report
            };
        }

        private async Task<object?> HandleMathTypeConvertAsync(JsonElement? payload)
        {
            if (_documentService == null)
            {
                return new { success = false, message = "Word document service chưa sẵn sàng." };
            }

            string? docxPath = null;
            if (payload.HasValue && payload.Value.TryGetProperty("docxPath", out var pPath))
            {
                docxPath = pPath.GetString();
            }

            var (success, count, outPath, report) = await _documentService.ConvertMathTypeToOmmlAsync(docxPath).ConfigureAwait(false);
            return new
            {
                success = success,
                convertedCount = count,
                outputPath = outPath,
                report = report
            };
        }

        private async Task<object?> HandleConvertExtractAsync(JsonElement? payload)
        {
            var req = new ConvertRequest();
            if (payload.HasValue)
            {
                var root = payload.Value;
                if (root.TryGetProperty("imageBase64", out var pImg))
                    req.ImageBase64 = pImg.GetString();
                if (root.TryGetProperty("imageMimeType", out var pMime))
                    req.ImageMimeType = pMime.GetString() ?? "image/png";
                if (root.TryGetProperty("rawInputText", out var pRaw))
                    req.RawInputText = pRaw.GetString();
                if (root.TryGetProperty("qtypeFilter", out var pFilter))
                    req.QtypeFilter = pFilter.GetString() ?? "auto";
                if (root.TryGetProperty("includeSolution", out var pSol))
                    req.IncludeSolution = pSol.GetBoolean();
                if (root.TryGetProperty("model", out var pMod))
                    req.ModelOverride = pMod.GetString();
            }

            var result = await ExtensibilityManager.ConvertService.ConvertContentAsync(req).ConfigureAwait(false);
            return new
            {
                success = result.Success,
                errorMessage = result.ErrorMessage,
                subject = result.Subject,
                grade = result.Grade,
                topic = result.Topic,
                questions = result.Questions,
                formattedDocText = result.FormattedDocText,
                rawAiResponse = result.RawAiResponse,
                modelUsed = result.ModelUsed,
                latencyMs = result.LatencyMs
            };
        }

        private async Task<object?> HandleConvertSaveToBankAsync(JsonElement? payload)
        {
            if (!payload.HasValue || !payload.Value.TryGetProperty("questions", out var pList) || pList.ValueKind != JsonValueKind.Array)
            {
                return new { success = false, message = "Danh sách câu hỏi không hợp lệ." };
            }

            int savedCount = 0;
            foreach (var qEl in pList.EnumerateArray())
            {
                try
                {
                    var item = new QuestionItem();
                    if (qEl.TryGetProperty("subject", out var pSub)) item.Subject = pSub.GetString() ?? "Toán";
                    if (qEl.TryGetProperty("grade", out var pGr)) item.Grade = pGr.GetInt32();
                    if (qEl.TryGetProperty("topic", out var pTop)) item.Topic = pTop.GetString() ?? "";
                    if (qEl.TryGetProperty("cognitiveLevel", out var pLevel)) item.CognitiveLevel = pLevel.GetString() ?? "Thông hiểu";
                    if (qEl.TryGetProperty("questionType", out var pType)) item.QuestionType = pType.GetString() ?? "MultipleChoice4";
                    if (qEl.TryGetProperty("content", out var pCont)) item.Content = pCont.GetString() ?? "";
                    if (qEl.TryGetProperty("correctAnswer", out var pAns)) item.CorrectAnswer = pAns.GetString() ?? "";
                    if (qEl.TryGetProperty("explanation", out var pExp)) item.Explanation = pExp.GetString() ?? "";
                    else if (qEl.TryGetProperty("solution", out var pSol)) item.Explanation = pSol.GetString() ?? "";

                    if (qEl.TryGetProperty("options", out var pOpts) && pOpts.ValueKind == JsonValueKind.Object)
                    {
                        foreach (var prop in pOpts.EnumerateObject())
                        {
                            item.Options[prop.Name] = prop.Value.GetString() ?? "";
                        }
                    }

                    if (!string.IsNullOrWhiteSpace(item.Content))
                    {
                        long id = await ExtensibilityManager.QuestionBankService.InsertQuestionAsync(item).ConfigureAwait(false);
                        if (id > 0) savedCount++;
                    }
                }
                catch (Exception ex)
                {
                    AddInLog.Log($"[ConvertSaveToBank] Lỗi lưu câu hỏi: {ex.Message}");
                }
            }

            return new
            {
                success = true,
                savedCount = savedCount,
                message = $"Đã lưu thành công {savedCount} câu hỏi vào Ngân hàng CSDL SQLite!"
            };
        }

        private Task<object?> HandleConvertParseTextAsync(JsonElement? payload)
        {
            return Task.Run<object?>(() =>
            {
                if (ExtensibilityManager?.ConvertService == null)
                {
                    return new { success = false, message = "Convert service chưa sẵn sàng." };
                }

                string rawText = "";
                string subject = "Toán";
                int grade = 12;

                if (payload.HasValue)
                {
                    var root = payload.Value;
                    if (root.TryGetProperty("rawText", out var pText)) rawText = pText.GetString() ?? "";
                    if (root.TryGetProperty("subject", out var pSub)) subject = pSub.GetString() ?? "Toán";
                    if (root.TryGetProperty("grade", out var pG))
                    {
                        if (pG.ValueKind == JsonValueKind.Number && pG.TryGetInt32(out int gVal)) grade = gVal;
                        else if (pG.ValueKind == JsonValueKind.String && int.TryParse(pG.GetString(), out int gsVal)) grade = gsVal;
                    }
                }

                var res = ExtensibilityManager.ConvertService.ParseTextDirectly(rawText, subject, grade);
                return new
                {
                    success = res.Success,
                    errorMessage = res.ErrorMessage,
                    questions = res.Questions,
                    formattedDocText = res.FormattedDocText,
                    subject = res.Subject,
                    grade = res.Grade,
                    topic = res.Topic,
                    modelUsed = res.ModelUsed,
                    count = res.Questions != null ? res.Questions.Count : 0
                };
            });
        }

        private Task<object?> HandleConvertGetPromptTemplateAsync(JsonElement? payload)
        {
            return Task.Run<object?>(() =>
            {
                if (ExtensibilityManager?.ConvertService == null)
                {
                    return new { success = false, message = "Convert service chưa sẵn sàng." };
                }

                string subject = "Toán";
                int grade = 12;
                string topic = "";

                if (payload.HasValue)
                {
                    var root = payload.Value;
                    if (root.TryGetProperty("subject", out var pSub)) subject = pSub.GetString() ?? "Toán";
                    if (root.TryGetProperty("grade", out var pG))
                    {
                        if (pG.ValueKind == JsonValueKind.Number && pG.TryGetInt32(out int gVal)) grade = gVal;
                        else if (pG.ValueKind == JsonValueKind.String && int.TryParse(pG.GetString(), out int gsVal)) grade = gsVal;
                    }
                    if (root.TryGetProperty("topic", out var pTop)) topic = pTop.GetString() ?? "";
                }

                string prompt = ExtensibilityManager.ConvertService.GetChatbotPromptTemplate(subject, grade, topic);
                return new
                {
                    success = true,
                    prompt = prompt
                };
            });
        }

        private Task<object?> HandleClipboardGetImageAsync(JsonElement? payload)
        {
            return Task.Run<object?>(() =>
            {
                try
                {
                    bool hasImage = false;
                    string? base64 = null;
                    string mimeType = "image/png";
                    long sizeKb = 0;
                    bool hasText = false;
                    string? text = null;

                    var thread = new System.Threading.Thread(() =>
                    {
                        try
                        {
                            if (System.Windows.Forms.Clipboard.ContainsImage())
                            {
                                using (var img = System.Windows.Forms.Clipboard.GetImage())
                                {
                                    if (img != null)
                                    {
                                        using (var ms = new System.IO.MemoryStream())
                                        {
                                            img.Save(ms, System.Drawing.Imaging.ImageFormat.Png);
                                            byte[] bytes = ms.ToArray();
                                            base64 = Convert.ToBase64String(bytes);
                                            mimeType = "image/png";
                                            sizeKb = bytes.Length / 1024;
                                            hasImage = true;
                                        }
                                    }
                                }
                            }
                            else if (System.Windows.Forms.Clipboard.ContainsFileDropList())
                            {
                                var files = System.Windows.Forms.Clipboard.GetFileDropList();
                                if (files != null && files.Count > 0)
                                {
                                    string file = files[0];
                                    string ext = System.IO.Path.GetExtension(file).ToLowerInvariant();
                                    if (ext == ".png" || ext == ".jpg" || ext == ".jpeg" || ext == ".bmp" || ext == ".gif")
                                    {
                                        byte[] bytes = System.IO.File.ReadAllBytes(file);
                                        base64 = Convert.ToBase64String(bytes);
                                        mimeType = (ext == ".png") ? "image/png" : "image/jpeg";
                                        sizeKb = bytes.Length / 1024;
                                        hasImage = true;
                                    }
                                }
                            }

                            if (System.Windows.Forms.Clipboard.ContainsText())
                            {
                                text = System.Windows.Forms.Clipboard.GetText();
                                hasText = !string.IsNullOrWhiteSpace(text);
                            }
                        }
                        catch (Exception ex)
                        {
                            AddInLog.Log($"[Clipboard] Error: {ex.Message}");
                        }
                    });

                    thread.SetApartmentState(System.Threading.ApartmentState.STA);
                    thread.Start();
                    thread.Join(2500);

                    if (hasImage && !string.IsNullOrEmpty(base64))
                    {
                        return new
                        {
                            success = true,
                            hasImage = true,
                            imageBase64 = base64,
                            mimeType = mimeType,
                            sizeKb = sizeKb,
                            hasText = hasText,
                            text = text
                        };
                    }
                    else if (hasText)
                    {
                        return new
                        {
                            success = true,
                            hasImage = false,
                            hasText = true,
                            text = text,
                            message = "Clipboard hiện tại chứa văn bản thay vì hình ảnh."
                        };
                    }

                    return new
                    {
                        success = false,
                        hasImage = false,
                        hasText = false,
                        message = "Clipboard hiện không chứa hình ảnh. Vui lòng chụp màn hình (Windows+Shift+S) rồi bấm nút Dán ảnh đề thi lại."
                    };
                }
                catch (Exception ex)
                {
                    return new
                    {
                        success = false,
                        hasImage = false,
                        message = ex.Message
                    };
                }
            });
        }

        #endregion

        #region IDisposable

        public void Dispose()
        {
            if (_isDisposed) return;
            _isDisposed = true;

            if (_documentService != null)
            {
                _documentService.TikzShapeSelected -= OnTikzShapeSelected;
            }

            if (_webView.CoreWebView2 != null)
            {
                _webView.CoreWebView2.WebMessageReceived -= OnWebMessageReceived;
            }
        }

        #endregion
    }
}
