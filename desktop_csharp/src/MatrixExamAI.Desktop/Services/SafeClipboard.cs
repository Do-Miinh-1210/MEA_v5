using System;
using System.Runtime.InteropServices;
using System.Threading;
using System.Windows;
using System.Windows.Media.Imaging;

namespace MatrixExamAI.Desktop.Services
{
    /// <summary>
    /// Tiện ích clipboard an toàn cho Windows/WPF, tự động thử lại (Retry với exponential backoff) khi Clipboard bị các ứng dụng khác khóa (0x800401D0 CLIPBRD_E_CANT_OPEN).
    /// </summary>
    public static class SafeClipboard
    {
        private const int MaxRetries = 10;
        private const int DelayMs = 50;

        public static bool SetText(string text)
        {
            if (text == null) return false;
            for (int i = 0; i < MaxRetries; i++)
            {
                try
                {
                    Clipboard.SetDataObject(text, true);
                    return true;
                }
                catch (COMException) when (i < MaxRetries - 1)
                {
                    Thread.Sleep(DelayMs);
                }
                catch (Exception) when (i < MaxRetries - 1)
                {
                    Thread.Sleep(DelayMs);
                }
                catch
                {
                    // Fallback on final attempt
                }
            }
            return false;
        }

        public static bool SetHtmlAndText(string html, string plainText)
        {
            if (html == null && plainText == null) return false;
            for (int i = 0; i < MaxRetries; i++)
            {
                try
                {
                    var dataObject = new DataObject();
                    if (!string.IsNullOrEmpty(plainText))
                    {
                        dataObject.SetData(DataFormats.UnicodeText, plainText);
                        dataObject.SetData(DataFormats.Text, plainText);
                    }
                    if (!string.IsNullOrEmpty(html))
                    {
                        string cfHtml = GenerateCfHtml(html);
                        dataObject.SetData(DataFormats.Html, cfHtml);
                    }
                    Clipboard.SetDataObject(dataObject, true);
                    return true;
                }
                catch (COMException) when (i < MaxRetries - 1)
                {
                    Thread.Sleep(DelayMs);
                }
                catch (Exception) when (i < MaxRetries - 1)
                {
                    Thread.Sleep(DelayMs);
                }
                catch
                {
                    try
                    {
                        Clipboard.SetDataObject(plainText ?? string.Empty, true);
                        return true;
                    }
                    catch { }
                }
            }
            return false;
        }

        private static string GenerateCfHtml(string htmlSnippet)
        {
            const string headerFormat =
                "Version:0.9\r\n" +
                "StartHTML:{0:D8}\r\n" +
                "EndHTML:{1:D8}\r\n" +
                "StartFragment:{2:D8}\r\n" +
                "EndFragment:{3:D8}\r\n";

            string prefix = "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0 Transitional//EN\"><html><head><meta http-equiv=\"Content-Type\" content=\"text/html; charset=utf-8\"><style>body{font-family:'Times New Roman',serif;font-size:12pt;line-height:1.15;}</style></head><body><!--StartFragment-->";
            string suffix = "<!--EndFragment--></body></html>";

            int dummyHeaderLen = string.Format(headerFormat, 0, 0, 0, 0).Length;
            int startHtml = dummyHeaderLen;
            int startFragment = startHtml + System.Text.Encoding.UTF8.GetByteCount(prefix);
            int endFragment = startFragment + System.Text.Encoding.UTF8.GetByteCount(htmlSnippet);
            int endHtml = endFragment + System.Text.Encoding.UTF8.GetByteCount(suffix);

            string header = string.Format(headerFormat, startHtml, endHtml, startFragment, endFragment);
            return header + prefix + htmlSnippet + suffix;
        }

        public static string GetText()
        {
            for (int i = 0; i < MaxRetries; i++)
            {
                try
                {
                    return Clipboard.GetText();
                }
                catch (COMException) when (i < MaxRetries - 1)
                {
                    Thread.Sleep(DelayMs);
                }
                catch (Exception) when (i < MaxRetries - 1)
                {
                    Thread.Sleep(DelayMs);
                }
                catch
                {
                    break;
                }
            }
            return string.Empty;
        }

        public static bool ContainsText()
        {
            for (int i = 0; i < MaxRetries; i++)
            {
                try
                {
                    return Clipboard.ContainsText();
                }
                catch (COMException) when (i < MaxRetries - 1)
                {
                    Thread.Sleep(DelayMs);
                }
                catch (Exception) when (i < MaxRetries - 1)
                {
                    Thread.Sleep(DelayMs);
                }
                catch
                {
                    break;
                }
            }
            return false;
        }

        public static bool ContainsImage()
        {
            for (int i = 0; i < MaxRetries; i++)
            {
                try
                {
                    return Clipboard.ContainsImage();
                }
                catch (COMException) when (i < MaxRetries - 1)
                {
                    Thread.Sleep(DelayMs);
                }
                catch (Exception) when (i < MaxRetries - 1)
                {
                    Thread.Sleep(DelayMs);
                }
                catch
                {
                    break;
                }
            }
            return false;
        }

        public static BitmapSource? GetImage()
        {
            for (int i = 0; i < MaxRetries; i++)
            {
                try
                {
                    return Clipboard.GetImage();
                }
                catch (COMException) when (i < MaxRetries - 1)
                {
                    Thread.Sleep(DelayMs);
                }
                catch (Exception) when (i < MaxRetries - 1)
                {
                    Thread.Sleep(DelayMs);
                }
                catch
                {
                    break;
                }
            }
            return null;
        }

        public static bool SetImage(BitmapSource image)
        {
            if (image == null) return false;
            for (int i = 0; i < MaxRetries; i++)
            {
                try
                {
                    Clipboard.SetImage(image);
                    return true;
                }
                catch (COMException) when (i < MaxRetries - 1)
                {
                    Thread.Sleep(DelayMs);
                }
                catch (Exception) when (i < MaxRetries - 1)
                {
                    Thread.Sleep(DelayMs);
                }
                catch
                {
                    // Fallback on final attempt
                }
            }
            return false;
        }
    }
}
