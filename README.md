# Pennysia Backtest Simulator

Interactive backtesting tool for comparing Pennysia's directional AMM against Uniswap V2 using real historical price data.

## Overview

Pennysia is a directional AMM on Sonic network that allows LPs to take long/short positions. This simulator compares LP returns across different strategies and market conditions.

## Features

- **Real Historical Data**: Fetch price data from CoinGecko API
- **Multiple Strategies**: Compare HODL, Uniswap V2, and Pennysia (100% Long, 100% Short, mixed allocations)
- **Interactive UI**: Streamlit web interface with live charts
- **Directional Mechanics**: Accurate simulation of Pennysia's long/short fee distribution

## Quick Start

### 1. Install Dependencies

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Run the App

```bash
streamlit run app.py
```

Or use the provided script:
```bash
./run_app.sh
```

### 3. Get CoinGecko API Key

1. Visit [CoinGecko API](https://www.coingecko.com/en/api)
2. Sign up for free account
3. Get your API key (format: `CG-xxxxxxxxxxxxxxxxxxxx`)
4. Enter it in the sidebar when running the app

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

## License

MIT License

---

**Python**: 3.9+  
**Last Updated**: December 6, 2025
