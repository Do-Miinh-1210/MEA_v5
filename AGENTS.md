# QUY TẮC PHÁT HÀNH BẢN CẬP NHẬT MATRIXEXAMAI PRO (.NET 10)

> **QUY TẮC CỨNG (BẮT BUỘC):**  
> Mỗi khi hoàn tất một tính năng, sửa lỗi giao diện, hoặc khi người dùng yêu cầu cập nhật, **TUYỆT ĐỐI KHÔNG CHỈ COMMIT/PUSH CODE LÊN GIT**.  
> **BẮT BUỘC PHẢI THỰC HIỆN ĐỦ 5 BƯỚC PHÁT HÀNH (RELEASE)** để toàn bộ máy người dùng (Client) mở app lên hoặc bấm "Kiểm tra bản cập nhật" đều tự động tải và cập nhật được ngay.

---

## 5 BƯỚC BẮT BUỘC MỖI KHI CẬP NHẬT:

### 1. Nâng số phiên bản (Version Bump)
Tăng số phiên bản đồng bộ tại 4 vị trí:
- `desktop_csharp/src/MatrixExamAI.Desktop/Services/GitHubUpdateService.cs` (`CurrentVersion` & `DisplayVersion`)
- `desktop_csharp/src/MatrixExamAI.Desktop/MatrixExamAI.Desktop.csproj` (`<Version>`, `<AssemblyVersion>`, `<FileVersion>`)
- `desktop_csharp/src/MatrixExamAI.Desktop/Views/SettingsView.xaml` (TextBlock tiêu đề phiên bản)
- `installer_pro.iss` (`#define MyAppVersion`)

### 2. Biên dịch gói Release
```powershell
dotnet publish desktop_csharp\src\MatrixExamAI.Desktop\MatrixExamAI.Desktop.csproj -c Release -r win-x64 --self-contained false -o desktop_csharp\publish
```

### 3. Xuất bản GitHub Release & Upload Assets
Cập nhật `TAG`, `TITLE`, `BODY` trong tệp `scripts/publish_release.py` rồi chạy:
```powershell
& "C:\Users\domin\AppData\Local\Python\bin\python.exe" scripts\publish_release.py
```
*Script tự động đóng gói `MatrixExamAI_Patch.zip`, tạo GitHub Release và upload `MatrixExamAI_Patch.zip` + `MatrixExamAI_Pro_Setup.exe`.*

### 4. Đồng bộ toàn bộ Git Remotes & Tags
```powershell
git add -A
git commit -m "chore(release): bump version to <vTag> and publish update"
git push origin source-main
git push origin source-main:main
git tag -a <vTag> -m "Release <vTag>"
git push origin <vTag>
```

### 5. Kiểm tra xác nhận Client nhận diện được bản mới
```powershell
curl.exe -s -o NUL -w "%{url_effective}\n" -L https://github.com/Do-Miinh-1210/MEA_v5/releases/latest
```
*Đảm bảo URL chuyển hướng trả về chính xác tag phiên bản vừa phát hành.*
