using System;
using System.IO;
using System.Windows;
using System.Windows.Threading;

namespace MatrixExamAI.Desktop;

public partial class App : Application
{
    protected override void OnStartup(StartupEventArgs e)
    {
        DispatcherUnhandledException += App_DispatcherUnhandledException;
        AppDomain.CurrentDomain.UnhandledException += CurrentDomain_UnhandledException;
        base.OnStartup(e);
    }

    private void App_DispatcherUnhandledException(object sender, DispatcherUnhandledExceptionEventArgs e)
    {
        LogCrash(e.Exception);
        if (e.Exception is System.Runtime.InteropServices.COMException comEx && (uint)comEx.HResult == 0x800401D0)
        {
            // Clipboard is temporarily locked by another Windows process (CLIPBRD_E_CANT_OPEN)
            e.Handled = true;
            return;
        }
        MessageBox.Show($"Lỗi giao diện: {e.Exception.Message}\n\n{e.Exception.StackTrace}", "MatrixExamAI Error", MessageBoxButton.OK, MessageBoxImage.Error);
        e.Handled = true;
    }

    private void CurrentDomain_UnhandledException(object sender, UnhandledExceptionEventArgs e)
    {
        if (e.ExceptionObject is Exception ex)
        {
            LogCrash(ex);
            MessageBox.Show($"Lỗi hệ thống: {ex.Message}\n\n{ex.StackTrace}", "MatrixExamAI Fatal Error", MessageBoxButton.OK, MessageBoxImage.Error);
        }
    }

    private static void LogCrash(Exception ex)
    {
        try
        {
            string appData = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "MatrixExamAI");
            Directory.CreateDirectory(appData);
            File.AppendAllText(Path.Combine(appData, "crash.log"), $"[{DateTime.Now}] {ex}\n\n");
        }
        catch { }
    }
}

