using System;
using System.Collections.Generic;
using System.Runtime.InteropServices;
using System.Threading.Tasks;
using Office = Microsoft.Office.Core;
using Word = Microsoft.Office.Interop.Word;

namespace MatrixExamAI.WordAddIn.TaskPane
{
    public class TaskPaneManager : IDisposable
    {
        private const string PaneTitle = "MatrixExamAI — Vẽ hình TikZ & Soạn thảo AI";
        private const string ControlProgId = "MatrixExamAI.WordAddIn.SidebarUserControl";
        private const int DefaultWidth = 460;

        private readonly Word.Application _wordApp;
        private Office.ICTPFactory? _ctpFactory;
        private readonly Dictionary<int, Office.CustomTaskPane> _panesMap;
        private readonly Dictionary<int, SidebarUserControl> _controlsMap;
        private bool _isDisposed;

        public TaskPaneManager(Word.Application wordApp)
        {
            _wordApp = wordApp ?? throw new ArgumentNullException(nameof(wordApp));
            _panesMap = new Dictionary<int, Office.CustomTaskPane>();
            _controlsMap = new Dictionary<int, SidebarUserControl>();

            // Chỉ đăng ký DocumentBeforeClose để giải phóng bộ nhớ khi đóng cửa sổ.
            // KHÔNG đăng ký WindowActivate để tạo CTP sớm vì khi Word khởi động,
            // WindowActivate chạy trước khi Office cấp CTPFactoryAvailable.
            _wordApp.DocumentBeforeClose += OnDocumentBeforeClose;
        }

        public void SetCTPFactory(Office.ICTPFactory factory)
        {
            AddInLog.Log($"[TaskPaneManager] SetCTPFactory called: factory is {(factory != null ? "VALID" : "NULL")}");
            _ctpFactory = factory;
        }

        #region Multi-Window SDI Tracking

        public Office.CustomTaskPane? GetOrCreatePane(Word.Window? window)
        {
            if (window == null)
            {
                try
                {
                    if (_wordApp.Documents.Count == 0)
                    {
                        AddInLog.Log("[TaskPaneManager] Documents count is 0. Creating a blank document.");
                        _wordApp.Documents.Add();
                    }
                    window = _wordApp.ActiveWindow;
                }
                catch (Exception ex)
                {
                    AddInLog.LogError("[TaskPaneManager] Error acquiring ActiveWindow", ex);
                    return null;
                }
            }

            if (window == null)
            {
                AddInLog.Log("[TaskPaneManager] GetOrCreatePane: window is null.");
                return null;
            }

            int hwnd = 0;
            try
            {
                hwnd = window.Hwnd;
            }
            catch (COMException ex)
            {
                AddInLog.LogError("[TaskPaneManager] Window.Hwnd error", ex);
                return null;
            }

            if (_panesMap.TryGetValue(hwnd, out var existingPane))
            {
                return existingPane;
            }

            if (_ctpFactory == null && ThisAddIn.GlobalCtpFactory != null)
            {
                AddInLog.Log("[TaskPaneManager] Restored _ctpFactory from ThisAddIn.GlobalCtpFactory.");
                _ctpFactory = ThisAddIn.GlobalCtpFactory;
            }

            if (_ctpFactory == null)
            {
                // Cho Office tối đa 1.5 giây nếu người dùng click ribbon ngay khoảnh khắc Word vừa mở
                for (int i = 0; i < 15 && _ctpFactory == null; i++)
                {
                    System.Threading.Thread.Sleep(100);
                    System.Windows.Forms.Application.DoEvents();
                    if (ThisAddIn.GlobalCtpFactory != null)
                    {
                        _ctpFactory = ThisAddIn.GlobalCtpFactory;
                        break;
                    }
                }
            }

            if (_ctpFactory == null)
            {
                AddInLog.Log("[TaskPaneManager] WARNING: _ctpFactory is NULL. Office has not supplied ICTPFactory yet.");
                System.Windows.Forms.MessageBox.Show(
                    "Word đang hoàn tất khởi động thanh tác vụ. Vui lòng bấm lại sau giây lát.",
                    "MatrixExamAI",
                    System.Windows.Forms.MessageBoxButtons.OK,
                    System.Windows.Forms.MessageBoxIcon.Information);
                return null;
            }

            try
            {
                AddInLog.Log($"[TaskPaneManager] Calling _ctpFactory.CreateCTP('{ControlProgId}', '{PaneTitle}')...");
                Office.CustomTaskPane pane = _ctpFactory.CreateCTP(ControlProgId, PaneTitle, window);
                pane.DockPosition = Office.MsoCTPDockPosition.msoCTPDockPositionRight;
                pane.Width = DefaultWidth;
                pane.VisibleStateChange += OnPaneVisibleStateChange;

                _panesMap[hwnd] = pane;

                AddInLog.Log($"[TaskPaneManager] CreateCTP succeeded! ContentControl is {pane.ContentControl?.GetType().FullName}");

                if (pane.ContentControl is SidebarUserControl userControl)
                {
                    _controlsMap[hwnd] = userControl;
                }

                return pane;
            }
            catch (Exception ex)
            {
                AddInLog.LogError($"[TaskPaneManager] Failed to create CTP with ProgId '{ControlProgId}'", ex);
                System.Windows.Forms.MessageBox.Show(
                    $"Không thể tạo thanh tác vụ Sidebar MatrixExamAI.\n\nLỗi: {ex.Message}\n\nProgId: {ControlProgId}",
                    "MatrixExamAI",
                    System.Windows.Forms.MessageBoxButtons.OK,
                    System.Windows.Forms.MessageBoxIcon.Error);
                return null;
            }
        }

        private void OnPaneVisibleStateChange(Office.CustomTaskPane customTaskPaneInst)
        {
            // Future ribbon sync callback if toggle button state is added
        }


        private void OnDocumentBeforeClose(Word.Document doc, ref bool cancel)
        {
            try
            {
                if (doc.Windows != null && doc.Windows.Count > 0)
                {
                    foreach (Word.Window win in doc.Windows)
                    {
                        try
                        {
                            int hwnd = win.Hwnd;
                            RemovePaneByHwnd(hwnd);
                        }
                        catch
                        {
                            // Ignore window disposal COM errors
                        }
                    }
                }
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"[TaskPaneManager] DocumentBeforeClose error: {ex.Message}");
            }
        }

        private void RemovePaneByHwnd(int hwnd)
        {
            if (_panesMap.TryGetValue(hwnd, out var pane))
            {
                try
                {
                    pane.VisibleStateChange -= OnPaneVisibleStateChange;
                    pane.Delete();
                    Marshal.ReleaseComObject(pane);
                }
                catch
                {
                    // Ignore deletion COM errors
                }
                _panesMap.Remove(hwnd);
            }

            if (_controlsMap.TryGetValue(hwnd, out var control))
            {
                try
                {
                    control.Dispose();
                }
                catch
                {
                    // Ignore control dispose errors
                }
                _controlsMap.Remove(hwnd);
            }
        }

        #endregion

        #region Public Actions

        public void ShowTikzSidebar()
        {
            ShowTab("tikz");
        }

        public void ToggleSidebar()
        {
            try
            {
                AddInLog.Log("[TaskPaneManager] ToggleSidebar called.");
                var pane = GetOrCreatePane(_wordApp.ActiveWindow);
                if (pane != null)
                {
                    pane.Visible = !pane.Visible;
                    AddInLog.Log($"[TaskPaneManager] Sidebar visible set to {pane.Visible}.");
                }
            }
            catch (Exception ex)
            {
                AddInLog.LogError("[TaskPaneManager] ToggleSidebar error", ex);
            }
        }

        public void ShowTab(string tabName)
        {
            try
            {
                AddInLog.Log($"[TaskPaneManager] ShowTab('{tabName}') called.");
                var pane = GetOrCreatePane(_wordApp.ActiveWindow);
                if (pane != null)
                {
                    pane.Visible = true;
                    AddInLog.Log($"[TaskPaneManager] Set pane.Visible = true for tab '{tabName}'.");
                    if (_controlsMap.TryGetValue(_wordApp.ActiveWindow.Hwnd, out var control))
                    {
                        control.NavigateToTab(tabName);
                    }
                }
            }
            catch (Exception ex)
            {
                AddInLog.LogError($"[TaskPaneManager] ShowTab('{tabName}') error", ex);
            }
        }

        public async void TriggerEditSelectedTikzAsync()
        {
            try
            {
                var docService = ThisAddIn.Current?.DocumentService;
                if (docService == null) return;

                string tikzCode = await docService.GetSelectedShapeTikzCodeAsync();
                ShowTikzSidebar();

                if (!string.IsNullOrWhiteSpace(tikzCode))
                {
                    BroadcastEvent("word/selectionChanged", new
                    {
                        hasSelectedShape = true,
                        isTikZ = true,
                        tikzCode = tikzCode,
                        shapeTitle = "MatrixExamAI:TikZ"
                    });
                }
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"[TaskPaneManager] TriggerEditSelectedTikzAsync error: {ex.Message}");
            }
        }

        public void BroadcastEvent(string eventName, object? data)
        {
            foreach (var control in _controlsMap.Values)
            {
                try
                {
                    control.Bridge?.SendPushEvent(eventName, data);
                }
                catch (Exception ex)
                {
                    System.Diagnostics.Debug.WriteLine($"[TaskPaneManager] BroadcastEvent error: {ex.Message}");
                }
            }
        }

        #endregion

        #region IDisposable

        public void Dispose()
        {
            if (_isDisposed) return;
            _isDisposed = true;

            try
            {
                _wordApp.DocumentBeforeClose -= OnDocumentBeforeClose;
            }
            catch
            {
                // Word COM connection might already be down
            }

            foreach (var kvp in _panesMap)
            {
                try
                {
                    kvp.Value.VisibleStateChange -= OnPaneVisibleStateChange;
                    kvp.Value.Delete();
                    Marshal.ReleaseComObject(kvp.Value);
                }
                catch
                {
                    // Ignore pane deletion errors on shutdown
                }
            }
            _panesMap.Clear();

            foreach (var kvp in _controlsMap)
            {
                try
                {
                    kvp.Value.Dispose();
                }
                catch
                {
                    // Ignore control dispose errors
                }
            }
            _controlsMap.Clear();
        }

        #endregion
    }
}
