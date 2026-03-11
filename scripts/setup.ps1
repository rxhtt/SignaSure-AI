param(
  [string]$Python = "C:\Users\Lenovo\AppData\Local\Programs\Python\Python312\python.exe",
  [string]$Dataset = "divyanshrai/handwritten-signatures"
)

& $Python -m venv .venv

.\.venv\Scripts\python.exe -m pip install -r requirements.txt

.\.venv\Scripts\python.exe scripts\fetch_data.py --source kaggle --dataset $Dataset
.\.venv\Scripts\python.exe scripts\prepare_data.py
.\.venv\Scripts\python.exe scripts\train.py

Write-Host "Training complete. Run: .\\.venv\\Scripts\\python.exe -m uvicorn app.main:app --reload" -ForegroundColor Green
