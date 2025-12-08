# Pennysia Backtest Simulator

Interactive backtesting tool for comparing Pennysia's directional AMM against Uniswap V2 using real historical price data.

> **🪟 Windows Users:** See [WINDOWS_SETUP.md](./WINDOWS_SETUP.md) for complete setup instructions!

## Overview

Pennysia is a directional AMM on Sonic network that allows LPs to take long/short positions. This simulator compares LP returns across different strategies and market conditions.

## Features

- **Real Historical Data**: Fetch price data from CoinGecko API
- **Multiple Strategies**: Compare HODL, Uniswap V2, and Pennysia (100% Long, 100% Short, mixed allocations)
- **Interactive UI**: Streamlit web interface with live charts
- **Directional Mechanics**: Accurate simulation of Pennysia's long/short fee distribution

## Quick Start

> **Windows Users:** See [WINDOWS_SETUP.md](./WINDOWS_SETUP.md) for detailed Windows-specific instructions!

### 1. Install Dependencies

**On macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**On Windows:**
```cmd
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Build Coins Cache (REQUIRED!)

Get a free CoinGecko API key first:
1. Visit [CoinGecko API](https://www.coingecko.com/en/api)
2. Sign up for free account
3. Copy your API key (format: `CG-xxxxxxxxxxxxxxxxxxxx`)

Then build the cache:

**On macOS/Linux:**
```bash
python scripts/build_coins_cache.py --api-key YOUR_API_KEY
```

**On Windows:**
```cmd
python scripts\build_coins_cache.py --api-key YOUR_API_KEY
```

This creates `src/data/coins_cache.py` with 19,000+ token IDs for validation.

### 3. Run the App

**On macOS/Linux:**
```bash
streamlit run app.py
# Or use: ./run_app.sh
```

**On Windows:**
```cmd
streamlit run app.py
```

### 4. Use the App

1. Enter your CoinGecko API key in the sidebar
2. Enter a token ID (e.g., `bitcoin`, `ethereum`, `sonic-3`)
3. Fetch data and run simulations!

## Usage

1. **Enter API Key**: Paste your CoinGecko API key in the sidebar
2. **Select Token**: Choose from popular tokens or enter custom CoinGecko ID
3. **Set Parameters**: Configure time period and volume/TVL ratio
4. **Fetch Data**: Click to download historical price data
5. **Run Simulation**: Compare strategies across different market conditions
6. **Analyze Results**: View rankings, charts, and export data

## Strategies Compared

- **HODL**: Hold 100% tokens
- **Uniswap V2 LP**: Traditional 50/50 liquidity provision
- **Pennysia 100% Long**: Bullish position (wins in bull markets)
- **Pennysia 100% Short**: Bearish position (wins in bear markets)
- **Pennysia Mixed**: Various long/short allocations (75/25, 50/50, 25/75)

## Key Insights

- **Bull Markets**: Long positions outperform due to directional fee rewards
- **Bear Markets**: Short positions outperform for the same reason
- **Uniswap V2**: Neutral performance, good baseline comparison
- **Fee Distribution**: Pennysia's directional mechanics create asymmetric returns

## Project Structure

```
├── app.py                 # Streamlit web interface
├── src/
│   ├── pools/            # Pool implementations (Uniswap V2, Pennysia)
│   ├── simulation/       # Simulation engine and strategies
│   ├── data/             # Data loading and coin cache
│   └── utils/            # Math utilities
├── scripts/              # Data fetching scripts
├── config/               # Configuration files
└── data/raw/             # Historical price data (gitignored)
```

## Troubleshooting

### Import Errors (ModuleNotFoundError)

**Problem:** `ModuleNotFoundError: No module named 'streamlit'` or similar

**Solution:**
1. Make sure virtual environment is activated (you should see `(venv)` in your prompt)
2. Run `pip install -r requirements.txt` again
3. On Windows, use `venv\Scripts\activate` not `source venv/bin/activate`

### Coins Cache Errors

**Problem:** `"get_coin_by_id" is not a known attribute` or token validation fails

**Solution:**
1. Build the coins cache: `python scripts/build_coins_cache.py --api-key YOUR_KEY`
2. Verify `src/data/coins_cache.py` exists and is ~1.3MB
3. If it exists but errors persist, delete it and rebuild

### Windows PowerShell Errors

**Problem:** `cannot be loaded because running scripts is disabled`

**Solution:**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Still Having Issues?

1. Check Python version: `python --version` (need 3.9+)
2. Delete `venv` folder and start over
3. See [WINDOWS_SETUP.md](./WINDOWS_SETUP.md) for Windows-specific help

## License

MIT License

---

**Python**: 3.9+  
**Last Updated**: December 8, 2025
