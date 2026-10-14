using System;
using System.IO;

namespace MatrixExamAI.WordAddIn
{
    public static class AddInLog
    {
        private static readonly object _lock = new object();
        private static readonly string _logPath;

        static AddInLog()
        {
            try
            {
                string dir = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "MatrixExamAI");
                Directory.CreateDirectory(dir);
                _logPath = Path.Combine(dir, "addin.log");
            }
            catch
            {
                _logPath = Path.Combine(Path.GetTempPath(), "matrixexamai_addin.log");
            }
        }

        public static void Log(string message)
        {
            try
            {
                lock (_lock)
                {
                    File.AppendAllText(_logPath, $"[{DateTime.Now:yyyy-MM-dd HH:mm:ss.fff}] {message}\r\n");
                }
                System.Diagnostics.Debug.WriteLine(message);
            }
            catch { }
        }

        public static void LogError(string context, Exception ex)
        {
            Log($"[ERROR] {context}: {ex.GetType().Name} - {ex.Message}\r\n{ex.StackTrace}");
        }
    }
}
