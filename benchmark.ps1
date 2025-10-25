$python = ".\.vemv\Scripts\python.exe"

$process = Start-Process -FilePath $python -ArgumentList "tests\benchmark_test.py" -NoNewWindow -PassThru
$process | Wait-Process