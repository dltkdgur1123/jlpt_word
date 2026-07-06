Set shell = CreateObject("WScript.Shell")
shell.CurrentDirectory = "D:\backup\jlpt_word"
shell.Run """D:\backup\jlpt_word\venv\Scripts\pythonw.exe"" ""D:\backup\jlpt_word\streamlit_tray.py""", 0, False
