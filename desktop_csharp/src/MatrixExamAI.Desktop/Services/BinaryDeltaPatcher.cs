using System;
using System.IO;
using System.Security.Cryptography;
using System.Text;
using ICSharpCode.SharpZipLib.BZip2;

namespace MatrixExamAI.Desktop.Services;

/// <summary>
/// Trình áp dụng cập nhật vi sai nhị phân (Binary Delta Patcher) chuẩn BSDIFF 4.0.
/// Giảm dung lượng tải từ ~7MB xuống còn ~200KB-300KB cho mỗi lần phát hành cập nhật.
/// </summary>
public static class BinaryDeltaPatcher
{
    private static readonly byte[] BsdiffMagic = Encoding.ASCII.GetBytes("BSDIFF40");

    /// <summary>
    /// Áp dụng tệp patch vi sai bsdiff lên tệp gốc để tạo ra tệp đích mới.
    /// </summary>
    public static void ApplyPatch(string oldFilePath, string patchFilePath, string outputFilePath)
    {
        if (!File.Exists(oldFilePath)) throw new FileNotFoundException("Không tìm thấy tệp gốc để vá vi sai.", oldFilePath);
        if (!File.Exists(patchFilePath)) throw new FileNotFoundException("Không tìm thấy tệp patch vi sai.", patchFilePath);

        byte[] oldBuf = File.ReadAllBytes(oldFilePath);
        byte[] patchBuf = File.ReadAllBytes(patchFilePath);

        byte[] newBuf = ApplyPatchBytes(oldBuf, patchBuf);

        string? outDir = Path.GetDirectoryName(outputFilePath);
        if (!string.IsNullOrEmpty(outDir) && !Directory.Exists(outDir))
        {
            Directory.CreateDirectory(outDir);
        }

        File.WriteAllBytes(outputFilePath, newBuf);
    }

    /// <summary>
    /// Thực hiện thuật toán vá vi sai trực tiếp trong bộ nhớ.
    /// </summary>
    public static byte[] ApplyPatchBytes(byte[] oldBuf, byte[] patchBuf)
    {
        if (patchBuf.Length < 32)
        {
            throw new InvalidDataException("Tệp patch vi sai quá ngắn, không đúng chuẩn BSDIFF40.");
        }

        for (int i = 0; i < 8; i++)
        {
            if (patchBuf[i] != BsdiffMagic[i])
            {
                throw new InvalidDataException("Header tệp patch không hợp lệ (yêu cầu 'BSDIFF40').");
            }
        }

        long ctrlLen = ReadInt64(patchBuf, 8);
        long diffLen = ReadInt64(patchBuf, 16);
        long newSize = ReadInt64(patchBuf, 24);

        if (ctrlLen < 0 || diffLen < 0 || newSize < 0)
        {
            throw new InvalidDataException("Kích thước trường dữ liệu trong header BSDIFF40 không hợp lệ.");
        }

        long extraOffset = 32 + ctrlLen + diffLen;
        if (extraOffset > patchBuf.Length)
        {
            throw new InvalidDataException("Dữ liệu tệp patch bị cắt ngắn hoặc hư hỏng.");
        }

        long extraLen = patchBuf.Length - extraOffset;

        // Giải nén 3 khối bzip2 trong bộ nhớ
        byte[] ctrlData = DecompressBZip2(patchBuf, 32, (int)ctrlLen);
        byte[] diffData = DecompressBZip2(patchBuf, (int)(32 + ctrlLen), (int)diffLen);
        byte[] extraData = DecompressBZip2(patchBuf, (int)extraOffset, (int)extraLen);

        byte[] newBuf = new byte[newSize];

        int oldPos = 0;
        int newPos = 0;
        int ctrlPos = 0;
        int diffPos = 0;
        int extraPos = 0;

        while (newPos < newSize)
        {
            if (ctrlPos + 24 > ctrlData.Length)
            {
                throw new InvalidDataException("Khối điều khiển control block kết thúc sớm.");
            }

            long x = ReadInt64(ctrlData, ctrlPos);
            long y = ReadInt64(ctrlData, ctrlPos + 8);
            long z = ReadInt64(ctrlData, ctrlPos + 16);
            ctrlPos += 24;

            // 1. Thêm dữ liệu từ diff vào oldBuf
            if (newPos + x > newSize || diffPos + x > diffData.Length)
            {
                throw new InvalidDataException("Lỗi vượt biên khi đọc diff block.");
            }

            for (int i = 0; i < x; i++)
            {
                byte bOld = (oldPos + i >= 0 && oldPos + i < oldBuf.Length) ? oldBuf[oldPos + i] : (byte)0;
                newBuf[newPos + i] = (byte)(bOld + diffData[diffPos + i]);
            }

            newPos += (int)x;
            oldPos += (int)x;
            diffPos += (int)x;

            // 2. Sao chép dữ liệu từ extra block
            if (newPos + y > newSize || extraPos + y > extraData.Length)
            {
                throw new InvalidDataException("Lỗi vượt biên khi đọc extra block.");
            }

            Buffer.BlockCopy(extraData, extraPos, newBuf, newPos, (int)y);
            newPos += (int)y;
            extraPos += (int)y;
            oldPos += (int)z;
        }

        return newBuf;
    }

    /// <summary>
    /// Giải nén một đoạn buffer nén BZip2.
    /// </summary>
    private static byte[] DecompressBZip2(byte[] buffer, int offset, int count)
    {
        if (count == 0) return Array.Empty<byte>();

        using var msIn = new MemoryStream(buffer, offset, count, writable: false);
        using var bzIn = new BZip2InputStream(msIn);
        using var msOut = new MemoryStream();

        byte[] chunk = new byte[8192];
        int read;
        while ((read = bzIn.Read(chunk, 0, chunk.Length)) > 0)
        {
            msOut.Write(chunk, 0, read);
        }

        return msOut.ToArray();
    }

    /// <summary>
    /// Đọc số nguyên có dấu 64-bit theo chuẩn mã hóa sign-magnitude của BSDIFF.
    /// Bit 7 của byte thứ 8 biểu thị dấu âm.
    /// </summary>
    public static long ReadInt64(byte[] buf, int offset)
    {
        long val = (long)buf[offset] |
                   ((long)buf[offset + 1] << 8) |
                   ((long)buf[offset + 2] << 16) |
                   ((long)buf[offset + 3] << 24) |
                   ((long)buf[offset + 4] << 32) |
                   ((long)buf[offset + 5] << 40) |
                   ((long)buf[offset + 6] << 48) |
                   ((long)(buf[offset + 7] & 0x7F) << 56);

        if ((buf[offset + 7] & 0x80) != 0)
        {
            val = -val;
        }

        return val;
    }

    /// <summary>
    /// Tính chuỗi băm SHA256 dạng hex chữ thường của một tệp tin.
    /// </summary>
    public static string ComputeSha256(string filePath)
    {
        if (!File.Exists(filePath)) return string.Empty;
        using var sha = SHA256.Create();
        using var stream = File.OpenRead(filePath);
        byte[] hash = sha.ComputeHash(stream);
        return Convert.ToHexStringLower(hash);
    }
}
