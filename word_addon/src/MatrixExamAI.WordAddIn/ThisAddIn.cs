using System;
using System.IO;
using System.Reflection;
using System.Runtime.InteropServices;
using Microsoft.Win32;
using MatrixExamAI.WordAddIn.Ribbon;
using MatrixExamAI.WordAddIn.TaskPane;
using MatrixExamAI.WordAddIn.WordInterop;
using Extensibility;
using Office = Microsoft.Office.Core;
using Word = Microsoft.Office.Interop.Word;

namespace MatrixExamAI.WordAddIn
{
    [ComVisible(true)]
    [Guid("9B302F31-155D-4A2D-BE45-219C1D9D6C99")]
    [ProgId("MatrixExamAI.WordAddIn")]
    public class ThisAddIn : IDTExtensibility2, Office.IRibbonExtensibility, Office.ICustomTaskPaneConsumer
    {
        [DllImport("kernel32.dll", CharSet = CharSet.Auto, SetLastError = true)]
        private static extern bool SetDllDirectory(string lpPathName);

        static ThisAddIn()
        {
            try
            {
                string dir = Path.GetDirectoryName(typeof(ThisAddIn).Assembly.Location) ?? "";
                if (!string.IsNullOrEmpty(dir) && Directory.Exists(dir))
                {
                    SetDllDirectory(dir);
                }
            }
            catch { }

            AppDomain.CurrentDomain.AssemblyResolve += OnAssemblyResolve;
        }

        private static Assembly? OnAssemblyResolve(object? sender, ResolveEventArgs args)
        {
            try
            {
                var requestedName = new AssemblyName(args.Name).Name;
                string dir = Path.GetDirectoryName(typeof(ThisAddIn).Assembly.Location) ?? "";
                if (!string.IsNullOrEmpty(dir))
                {
                    string candidate = Path.Combine(dir, requestedName + ".dll");
                    if (File.Exists(candidate))
                    {
                        return Assembly.LoadFrom(candidate);
                    }
                }
            }
            catch { }
            return null;
        }

        public static ThisAddIn? Current { get; private set; }

        public Word.Application? Application { get; private set; }
        public RibbonController? Ribbon { get; private set; }
        public TaskPaneManager? TaskPaneManager { get; private set; }
        public IWordDocumentService? DocumentService { get; private set; }
        public MatrixExamAI.WordAddIn.Extensibility.WordExtensibilityManager? ExtensibilityManager { get; private set; }

        public static Office.ICTPFactory? GlobalCtpFactory { get; private set; }

        public ThisAddIn()
        {
            Current = this;
            Ribbon = new RibbonController();
        }

        #region IDTExtensibility2 Implementation

        public void OnConnection(object Application, ext_ConnectMode ConnectMode, object AddInInst, ref Array custom)
        {
            try
            {
                Current = this;
                this.Application = (Word.Application)Application;
                AddInLog.Log($"[ThisAddIn] OnConnection started. ConnectMode={ConnectMode}, Application={(this.Application != null)}");

                DocumentService = new WordDocumentService(this.Application);
                TaskPaneManager = new TaskPaneManager(this.Application);

                if (GlobalCtpFactory != null)
                {
                    AddInLog.Log("[ThisAddIn] Re-applying GlobalCtpFactory to TaskPaneManager.");
                    TaskPaneManager.SetCTPFactory(GlobalCtpFactory);
                }
                else
                {
                    AddInLog.Log("[ThisAddIn] GlobalCtpFactory is null at OnConnection.");
                }

                var sharedGeminiClient = new MatrixExamAI.Shared.AI.GeminiClient();
                ExtensibilityManager = new MatrixExamAI.WordAddIn.Extensibility.WordExtensibilityManager(
                    geminiClient: sharedGeminiClient
                );

                AddInLog.Log("[ThisAddIn] Connected to Microsoft Word successfully.");
            }
            catch (Exception ex)
            {
                AddInLog.LogError("[ThisAddIn] OnConnection error", ex);
            }
        }

        public void OnDisconnection(ext_DisconnectMode RemoveMode, ref Array custom)
        {
            try
            {
                TaskPaneManager?.Dispose();
                TaskPaneManager = null;

                DocumentService?.Dispose();
                DocumentService = null;

                ExtensibilityManager = null;

                if (Application != null)
                {
                    Marshal.ReleaseComObject(Application);
                    Application = null;
                }

                Current = null;

                // Defensive COM cleanup to ensure WINWORD.EXE exits cleanly
                GC.Collect();
                GC.WaitForPendingFinalizers();

                System.Diagnostics.Debug.WriteLine("[ThisAddIn] Disconnected and cleaned up COM objects.");
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"[ThisAddIn] OnDisconnection error: {ex.Message}");
            }
        }

        public void OnStartupComplete(ref Array custom)
        {
            System.Diagnostics.Debug.WriteLine("[ThisAddIn] Startup complete.");
        }

        public void OnBeginShutdown(ref Array custom)
        {
            System.Diagnostics.Debug.WriteLine("[ThisAddIn] Word is shutting down.");
        }

        public void OnAddInsUpdate(ref Array custom)
        {
        }

        #endregion

        #region IRibbonExtensibility Implementation

        public string GetCustomUI(string RibbonID)
        {
            if (Ribbon != null)
            {
                return Ribbon.GetCustomUI(RibbonID);
            }
            return string.Empty;
        }

        #endregion

        #region Ribbon Dispatch Callbacks

        public void OnRibbonLoad(Office.IRibbonUI ribbonUI) => Ribbon?.OnRibbonLoad(ribbonUI);

        public void OnOpenTikzSidebarClicked(Office.IRibbonControl control) => Ribbon?.OnOpenTikzSidebarClicked(control);

        public void OnEditSelectedTikZClicked(Office.IRibbonControl control) => Ribbon?.OnEditSelectedTikZClicked(control);

        public void OnToggleSidebarClicked(Office.IRibbonControl control) => Ribbon?.OnToggleSidebarClicked(control);

        public void OnAiAuthoringClicked(Office.IRibbonControl control) => Ribbon?.OnAiAuthoringClicked(control);

        public void OnAiExplainClicked(Office.IRibbonControl control) => Ribbon?.OnAiExplainClicked(control);

        public void OnConvertClicked(Office.IRibbonControl control) => Ribbon?.OnConvertClicked(control);

        public void OnQuestionBankClicked(Office.IRibbonControl control) => Ribbon?.OnQuestionBankClicked(control);

        public void OnExamMatrixClicked(Office.IRibbonControl control) => Ribbon?.OnExamMatrixClicked(control);

        public void OnStandardizeWordClicked(Office.IRibbonControl control) => Ribbon?.OnStandardizeWordClicked(control);

        public void OnEquationToMathTypeClicked(Office.IRibbonControl control) => Ribbon?.OnEquationToMathTypeClicked(control);

        public void OnConvertLatexToOmmlClicked(Office.IRibbonControl control) => Ribbon?.OnConvertLatexToOmmlClicked(control);

        public void OnShuffleExamClicked(Office.IRibbonControl control) => Ribbon?.OnShuffleExamClicked(control);

        public void OnApiSettingsClicked(Office.IRibbonControl control) => Ribbon?.OnApiSettingsClicked(control);

        public bool GetIsTikzSelected(Office.IRibbonControl control) => Ribbon?.GetIsTikzSelected(control) ?? true;

        #endregion

        #region ICustomTaskPaneConsumer Implementation

        public void CTPFactoryAvailable(Office.ICTPFactory CTPFactoryInst)
        {
            try
            {
                AddInLog.Log($"[ThisAddIn] CTPFactoryAvailable CALLED by Office! CTPFactoryInst is {(CTPFactoryInst != null ? "VALID" : "NULL")}");
                GlobalCtpFactory = CTPFactoryInst;
                TaskPaneManager?.SetCTPFactory(CTPFactoryInst);
            }
            catch (Exception ex)
            {
                AddInLog.LogError("[ThisAddIn] CTPFactoryAvailable error", ex);
            }
        }

        #endregion

        #region COM Registration Functions

        [ComRegisterFunction]
        public static void RegisterFunction(Type t)
        {
            try
            {
                string[] subKeys = new[]
                {
                    @"Software\Microsoft\Office\Word\Addins\MatrixExamAI.WordAddIn"
                };

                foreach (var subKey in subKeys)
                {
                    using var key = Registry.CurrentUser.CreateSubKey(subKey);
                    if (key != null)
                    {
                        key.SetValue("FriendlyName", "MatrixExamAI Word Add-in");
                        key.SetValue("Description", "Trợ lý Soạn thảo AI & Vẽ hình TikZ MatrixExamAI");
                        key.SetValue("LoadBehavior", 3, RegistryValueKind.DWord);
                        key.SetValue("CommandLineSafe", 0, RegistryValueKind.DWord);
                    }
                }

                // Register alias in HKCU Software\Classes for Word Addin Connect if needed
                try
                {
                    using var progKey = Registry.CurrentUser.CreateSubKey(@"Software\Classes\MatrixExamAI.WordAddIn.Connect\CLSID");
                    progKey?.SetValue("", "{9B302F31-155D-4A2D-BE45-219C1D9D6C99}");
                }
                catch { }
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"[ThisAddIn] RegisterFunction error: {ex.Message}");
            }
        }

        [ComUnregisterFunction]
        public static void UnregisterFunction(Type t)
        {
            try
            {
                string[] subKeys = new[]
                {
                    @"Software\Microsoft\Office\Word\Addins\MatrixExamAI.WordAddIn",
                    @"Software\Microsoft\Office\Word\Addins\MatrixExamAI.WordAddIn.Connect"
                };

                foreach (var subKey in subKeys)
                {
                    Registry.CurrentUser.DeleteSubKeyTree(subKey, false);
                }

                try
                {
                    Registry.CurrentUser.DeleteSubKeyTree(@"Software\Classes\MatrixExamAI.WordAddIn.Connect", false);
                }
                catch { }
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"[ThisAddIn] UnregisterFunction error: {ex.Message}");
            }
        }

        #endregion
    }

    public static class Globals
    {
        public static ThisAddIn? ThisAddIn => ThisAddIn.Current;
    }
}
