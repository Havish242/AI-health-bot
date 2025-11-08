# Minimal AI Health Assistant

This small project demonstrates a minimal, rule-based "AI" health assistant for prototyping.

Files created:
- `assistant.py` — core rule-based assistant logic
- `app.py` — Flask API exposing `/chat` (POST) that returns JSON {"reply": "..."}
- `client.py` — simple CLI client that posts to the server and falls back to a local assistant if the server is unreachable
- `requirements.txt` — minimal dependencies (Flask, requests, pytest)
- `tests/test_assistant.py` — quick unit tests for the assistant

Quick start (Windows PowerShell):

1. Create and activate a venv

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Install dependencies

```powershell
pip install -r "requirements.txt"
```

3. Run the server

```powershell
python app.py
```

4. In another terminal, run the CLI client

```powershell
python client.py
```

5. Run tests

```powershell
pytest -q
```

Notes / safety
- This is a demo, not a medical device. It provides general information and triage suggestions only.
- Do not use this code for real medical decision-making. Always consult qualified healthcare professionals for diagnosis and treatment.
