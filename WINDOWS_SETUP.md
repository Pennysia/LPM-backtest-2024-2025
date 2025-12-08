# 🪟 Windows Setup Guide

> **Got import errors?** You're in the right place! This guide fixes all Windows-specific issues.

## 🚀 Quick Setup (5 Minutes)

### Step 1: Run Setup Script

**Double-click `setup_windows.bat`** - it will:
- ✓ Create virtual environment
- ✓ Install all dependencies
- ✓ Show you next steps

You should see:
```
✓ Virtual environment created
✓ Virtual environment activated
✓ Dependencies installed
```

### Step 2: Get FREE API Key

1. Go to https://www.coingecko.com/en/api
2. Click "Get Your Free API Key"
3. Sign up (free, no credit card needed)
4. Copy your API key (starts with `CG-`)

### Step 3: Build Coins Cache

Open Command Prompt in this folder and run:

```cmd
venv\Scripts\activate
python scripts\build_coins_cache.py --api-key YOUR_API_KEY_HERE
```

Replace `YOUR_API_KEY_HERE` with your actual key.

You should see:
```
✅ Received 19257 coins
✅ Module saved to: src/data/coins_cache.py
✅ SUCCESS!
```

### Step 4: Run the App

**Double-click `run_app_windows.bat`** or run:

```cmd
venv\Scripts\activate
streamlit run app.py
```

Your browser will open at `http://localhost:8501` 🎉

---

## 📝 Manual Setup (Alternative Method)

### 1. Create Virtual Environment

```cmd
python -m venv venv
```

### 2. Activate Virtual Environment (IMPORTANT!)

**On Windows Command Prompt:**
```cmd
venv\Scripts\activate
```

**On Windows PowerShell:**
```powershell
venv\Scripts\Activate.ps1
```

**Note:** If you get a PowerShell execution policy error, run:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### 3. Verify Activation

You should see `(venv)` at the start of your command prompt:
```
(venv) C:\Users\Admin\Desktop\LPM-backtest-2024-2025-main>
```

### 4. Install Dependencies

```cmd
pip install -r requirements.txt
```

### 5. Build Coins Cache (REQUIRED!)

You need a CoinGecko API key for this step:

```cmd
python scripts\build_coins_cache.py --api-key YOUR_COINGECKO_API_KEY
```

**Get a FREE API key:**
1. Go to https://www.coingecko.com/en/api
2. Sign up (free)
3. Copy your API key (starts with `CG-`)

### 6. Run the App

```cmd
streamlit run app.py
```

## Troubleshooting

### Error: "No module named 'streamlit'"

**Cause:** Virtual environment not activated or dependencies not installed

**Fix:**
1. Make sure you see `(venv)` in your prompt
2. Run `pip install -r requirements.txt` again

### Error: "cannot be loaded because running scripts is disabled"

**Cause:** PowerShell execution policy blocks scripts

**Fix:** Run PowerShell as Administrator:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Error: Import errors with coins_cache

**Cause:** Coins cache file not built

**Fix:**
1. Run: `python scripts\build_coins_cache.py --api-key YOUR_KEY`
2. Verify file exists: `src\data\coins_cache.py` (should be ~1.3 MB)
3. If file exists but errors persist, delete it and rebuild

### Error: "No such file or directory"

**Cause:** Wrong path separator

**Remember:** Windows uses backslashes (`\`), not forward slashes (`/`)
- ✅ Correct: `venv\Scripts\activate`
- ❌ Wrong: `venv/Scripts/activate`

## 📋 Pre-Flight Checklist

Before running the app, verify:

- [ ] Python 3.9+ installed: `python --version`
- [ ] Virtual environment created: `venv` folder exists
- [ ] Virtual environment activated: see `(venv)` in prompt
- [ ] Dependencies installed: `pip list` shows streamlit, pandas, etc.
- [ ] Coins cache built: `src\data\coins_cache.py` exists (~1.3 MB)
- [ ] CoinGecko API key ready

## 🔄 Starting Over

If nothing works, clean slate:

1. Delete `venv` folder
2. Delete `src\data\coins_cache.py` (if exists)
3. Double-click `setup_windows.bat`
4. Follow steps 2-4 from Quick Setup above

## 🎯 What Success Looks Like

**After setup:**
```
(venv) C:\...\LPM-backtest-2024-2025> streamlit run app.py

  You can now view your Streamlit app in your browser.

  Local URL: http://localhost:8501
```

Browser opens automatically with the Pennysia Backtest interface!

---

**That's it!** Setup takes 5 minutes, do it once. After that, just double-click `run_app_windows.bat` anytime.

## Quick Start (After Setup)

1. **Activate venv:**
   ```cmd
   venv\Scripts\activate
   ```

2. **Run app:**
   ```cmd
   streamlit run app.py
   ```

3. **Enter API key in the sidebar**

4. **Start backtesting!**

## File Paths on Windows

Note: Windows uses backslashes (`\`) instead of forward slashes (`/`):
- ✅ `venv\Scripts\activate`
- ❌ `venv/Scripts/activate`

## Need Help?

If you still have issues:
1. Make sure Python 3.9+ is installed: `python --version`
2. Make sure venv is activated (look for `(venv)` in prompt)
3. Delete `venv` folder and start over from Step 1
4. Check that `src/data/coins_cache.py` exists (created in Step 5)
