Set objWshShell = CreateObject("WScript.Shell")
objWshShell.CurrentDirectory = "c:\Users\Sumit\Downloads\mini projecttt\hrtech-platform"
Dim fso
Set fso = CreateObject("Scripting.FileSystemObject")

Dim venvPythonw
venvPythonw = "c:\Users\Sumit\Downloads\mini projecttt\.venv\Scripts\pythonw.exe"

If fso.FileExists(venvPythonw) Then
	objWshShell.Run """" & venvPythonw & """ flask_gateway.py", 0, False
Else
	objWshShell.Run "pythonw.exe flask_gateway.py", 0, False
End If
