using System;
using System.IO;
using System.Text;
using MatrixExamAI.Desktop.Services;
using Xunit;

namespace MatrixExamAI.Desktop.Tests;

public class BinaryDeltaPatcherTests
{
    [Fact]
    public void ReadInt64_PositiveAndNegative_DecodesAccurately()
    {
        // 100: 64 00 00 00 00 00 00 00
        byte[] posBuf = Convert.FromHexString("6400000000000000");
        long posVal = BinaryDeltaPatcher.ReadInt64(posBuf, 0);
        Assert.Equal(100, posVal);

        // -100: 64 00 00 00 00 00 00 80 (sign-magnitude in BSDIFF40)
        byte[] negBuf = Convert.FromHexString("6400000000000080");
        long negVal = BinaryDeltaPatcher.ReadInt64(negBuf, 0);
        Assert.Equal(-100, negVal);

        // 0: 00 00 00 00 00 00 00 00
        byte[] zeroBuf = new byte[8];
        long zeroVal = BinaryDeltaPatcher.ReadInt64(zeroBuf, 0);
        Assert.Equal(0, zeroVal);
    }

    [Fact]
    public void ApplyPatchBytes_ValidBsDiff_ReconstructsTargetAccurately()
    {
        byte[] oldBytes = Encoding.UTF8.GetBytes("MatrixExamAI Version 5.3.0.12 Base Assembly Data Content");
        string expectedNewStr = "MatrixExamAI Version 5.3.0.13 Updated Assembly Data Content with Delta Patching!";
        byte[] expectedNewBytes = Encoding.UTF8.GetBytes(expectedNewStr);

        string patchHex = "4253444946463430360000000000000027000000000000005000000000000000425a6839314159265359aa3f244300001170405920030440004000200021284c8fd48400c1c5f3d0210d9df8bb9229c2848551f92218425a6839314159265359783ee1f8000000500040000001200021008283177245385090783ee1f8425a6839314159265359fff32ff60000029f8060000800040042002ee544802000314d323131310a343269ea34f481b0e156a5f29c280a47658999a5e3e2ee48a70a121ffe65fec0";
        byte[] patchBytes = Convert.FromHexString(patchHex);

        byte[] actualNewBytes = BinaryDeltaPatcher.ApplyPatchBytes(oldBytes, patchBytes);

        Assert.Equal(expectedNewBytes.Length, actualNewBytes.Length);
        Assert.Equal(expectedNewStr, Encoding.UTF8.GetString(actualNewBytes));
    }

    [Fact]
    public void ApplyPatchBytes_CorruptHeader_ThrowsInvalidDataException()
    {
        byte[] oldBytes = Encoding.UTF8.GetBytes("Some old data");
        byte[] corruptPatch = Encoding.UTF8.GetBytes("NOT_A_BSDIFF_HEADER_HERE_TOO_SHORT");

        Assert.Throws<InvalidDataException>(() => BinaryDeltaPatcher.ApplyPatchBytes(oldBytes, corruptPatch));
    }

    [Fact]
    public void ComputeSha256_ValidFile_ReturnsCorrectHash()
    {
        string tempFile = Path.Combine(Path.GetTempPath(), $"sha_test_{Guid.NewGuid():N}.txt");
        try
        {
            File.WriteAllText(tempFile, "Hello SHA256 Test");
            string hash = BinaryDeltaPatcher.ComputeSha256(tempFile);
            Assert.False(string.IsNullOrEmpty(hash));
            Assert.Equal(64, hash.Length);
        }
        finally
        {
            if (File.Exists(tempFile)) File.Delete(tempFile);
        }
    }
}
