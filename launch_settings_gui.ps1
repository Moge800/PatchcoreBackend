$python=".\.vemv\Scripts\python.exe"

$process = Start-Process -FilePath $python "src/ui/main_gui_launcher.py" -NoNewWindow -PassThru

$process | Wait-Process