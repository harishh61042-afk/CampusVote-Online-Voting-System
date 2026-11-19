# CampusVote — Quick Start (Windows + VS Code)

```powershell
# In the extracted CampusVote folder:
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m flask --app run.py create-admin
python scripts/seed_demo.py   # optional fictitious sample elections
python run.py
```

Open http://127.0.0.1:5000.

Sign in with the admin ID and password you created. To demo student voting, use student `STU001` and the **random demo voter password printed by the seed command**.

Run tests (after installation): `python -m pytest tests -q` and `python scripts/offline_verify.py`. Stop the server with `Ctrl+C`.

For PowerShell activation issues, use `cmd.exe` with `.venv\Scripts\activate.bat`, or run `.\.venv\Scripts\python.exe run.py` directly.

No payment or API key is required.
