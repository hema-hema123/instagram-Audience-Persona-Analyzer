# Troubleshooting

## 1) `ModuleNotFoundError: No module named 'app'`
**Cause:** Running script from a subpath so the package isn’t on `PYTHONPATH`.**Fix (pick one):**
- Run as a module from repo root: `python -m scripts.demo_classify`
- Or: `export PYTHONPATH=. && python scripts/demo_classify.py`
- Ensure `app/__init__.py` exists (it does).

## 2) `uvicorn: command not found`
Install it (inside your venv): `pip install uvicorn`

## 3) Port already in use
Run on another port: `uvicorn app.main:app --reload --port 8080`

## 4) Shell script permissions (macOS/Linux)
If `permission denied`: `chmod +x scripts/*.sh`

## 5) pip/SSL issues on macOS
Upgrade wheels: `python -m pip install --upgrade pip setuptools wheel`

## 6) IG Graph 400/403
- Use **Business/Creator** IG.
- Use **long‑lived** Page token.
- App has required permissions (`instagram_basic`, `pages_read_engagement`, etc.).
- Page linked to IG Business Account.

## 7) Zero‑shot model is slow/heavy
- Keep `USE_ZEROSHOT=false`.
- Try smaller models later if needed.
