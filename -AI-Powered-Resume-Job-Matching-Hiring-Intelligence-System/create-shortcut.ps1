$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut([System.IO.Path]::Combine([System.Environment]::GetFolderPath("Desktop"), "HRTech Platform.lnk"))
$shortcut.TargetPath = "C:\Windows\System32\cmd.exe"
$shortcut.Arguments = "/c cd /d `"c:\Users\Sumit\Downloads\mini projecttt\hrtech-platform`" && start /min python.exe flask_gateway.py"
$shortcut.WindowStyle = 7  # 7 = Minimized/Hidden
$shortcut.Save()
Write-Host "Shortcut created on Desktop!" -ForegroundColor Green
