Set objWshShell = CreateObject("WScript.Shell")
objWshShell.CurrentDirectory = "c:\Users\Sumit\Downloads\mini projecttt\hrtech-platform"
objWshShell.Run "python.exe flask_gateway.py", 0, False
