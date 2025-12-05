"""
Streamlit Web Interface for Pennysia Backtest
Interactive UI for fetching data and running simulations
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from scripts.fetch_coingecko_data import CoinGeckoFetcher
from src.data import load_price_data, coins_cache
from src.simulation import SimulationEngine

# Page config
st.set_page_config(
    page_title="Pennysia Backtest",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        margin-bottom: 2rem;
    }
    .sub-header {
        font-size: 1.5rem;
        font-weight: bold;
        margin-top: 2rem;
        margin-bottom: 1rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'data_fetched' not in st.session_state:
    st.session_state.data_fetched = False
if 'simulation_run' not in st.session_state:
    st.session_state.simulation_run = False
if 'price_data' not in st.session_state:
    st.session_state.price_data = None
if 'results' not in st.session_state:
    st.session_state.results = None
if 'sim' not in st.session_state:
    st.session_state.sim = None
if 'last_sim_params' not in st.session_state:
    st.session_state.last_sim_params = None

# Main header
st.markdown('<div class="main-header">📊 Pennysia vs Uniswap V2 Backtest</div>', unsafe_allow_html=True)
st.markdown("---")

# Sidebar - Configuration
st.sidebar.header("⚙️ Configuration")

# API Key Section
st.sidebar.subheader("🔑 CoinGecko API Key")

api_key = st.sidebar.text_input(
    "Enter your API Key",
    value="",
    type="password",
    help="Get your free API key from https://www.coingecko.com/en/api",
    placeholder="CG-xxxxxxxxxxxxxxxxxxxx"
)

if not api_key:
    st.sidebar.error("⚠️ API key required to fetch data")
    st.sidebar.markdown("👇 Click below to learn how to get one")
else:
    st.sidebar.success("✅ API key entered")

# Show API key info - always visible
with st.sidebar.expander("ℹ️ How to get a FREE CoinGecko API key", expanded=not api_key):
    st.markdown("""
    **Get Your Free API Key (Takes 2 minutes):**
    
    1. Go to [CoinGecko API](https://www.coingecko.com/en/api)
    2. Click **"Get Your Free API Key"**
    3. Sign up with email (free account)
    4. Verify your email
    5. Copy your API key (starts with `CG-`)
    6. Paste it in the field above ☝️
    
    **Free Tier Includes:**
    - ✅ 10,000 API calls per month
    - ✅ 30 calls per minute
    - ✅ All coins & historical data
    - ✅ Perfect for backtesting!
    
    **No credit card required!** 🎉
    """)

st.sidebar.markdown("---")

# Token Configuration
st.sidebar.subheader("🪙 Token Settings")

# Token ID (CoinGecko ID) - REQUIRED
token_id = st.sidebar.text_input(
    "CoinGecko Token ID",
    value="sonic-3",
    help="CoinGecko coin ID (e.g., 'bitcoin', 'ethereum', 'sonic-3')"
).lower().strip()

# Validate and display token info
if token_id:
    try:
        coin_info = coins_cache.get_coin_by_id(token_id)
        if coin_info:
            token_name = coin_info['name']
            token_symbol = coin_info['symbol'].upper()
            st.sidebar.success(f"✅ {token_name} ({token_symbol})")
        else:
            token_name = "Unknown"
            token_symbol = "???"
            st.sidebar.error(f"❌ Token ID '{token_id}' not found in database")
            st.sidebar.info("💡 Tip: Search for tokens at coingecko.com and use the ID from the URL")
    except Exception as e:
        token_name = "Unknown"
        token_symbol = "???"
        st.sidebar.warning(f"⚠️ Could not validate token: {str(e)}")
else:
    token_name = "Unknown"
    token_symbol = "???"
    st.sidebar.warning("⚠️ Please enter a CoinGecko token ID")

st.sidebar.markdown("---")

# Time Period
st.sidebar.subheader("📅 Time Period")

days_back = st.sidebar.number_input(
    "Days of Historical Data",
    min_value=7,
    max_value=365,
    value=365,
    step=7,
    help="Number of days to fetch (last N days from today)"
)

# Calculate date range for display
end_date = datetime.now()
start_date = end_date - timedelta(days=days_back)

st.sidebar.info(f"📊 Period: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")

st.sidebar.markdown("---")

# Simulation Settings
st.sidebar.subheader("💰 Simulation Settings")

initial_capital = st.sidebar.number_input(
    "Initial Capital (USD)",
    min_value=100.0,
    max_value=1000000.0,
    value=10000.0,
    step=1000.0,
    help="Starting capital for each strategy"
)

fee_rate = st.sidebar.number_input(
    "Fee Rate (%)",
    min_value=0.01,
    max_value=5.0,
    value=0.30,
    step=0.01,
    help="Unified fee rate for both Uniswap V2 and Pennysia pools"
) / 100

pennysia_protocol_share = st.sidebar.number_input(
    "Pennysia Protocol Share (%)",
    min_value=0.0,
    max_value=20.0,
    value=20.0,
    step=1.0,
    help="Percentage of fees going to protocol (0-20%)"
) / 100

st.sidebar.markdown("---")

# Volume Simulation
st.sidebar.subheader("📊 Volume Simulation")

volume_tvl_ratio = st.sidebar.number_input(
    "Volume/TVL Ratio",
    min_value=0.0,
    max_value=50.0,
    value=3.2,
    step=0.1,
    help="Daily trading volume as multiple of pool TVL. E.g., 3.2 means volume = 3.2x TVL per day. Set to 0 to disable."
)

if volume_tvl_ratio > 0:
    st.sidebar.success(f"✅ Volume simulation enabled")
    st.sidebar.info(f"📈 Estimated daily volume: {volume_tvl_ratio:.1f}x pool TVL")
else:
    st.sidebar.warning("⚠️ Volume simulation disabled")
    st.sidebar.info("💡 Enable to simulate fee earnings")

with st.sidebar.expander("ℹ️ About Volume/TVL Ratio"):
    st.markdown("""
    **What is Volume/TVL Ratio?**
    
    This ratio determines how much trading activity occurs relative to the pool's total value locked (TVL).
    
    **Examples:**
    - **3.2** = Daily volume is 3.2x the pool TVL (typical for active pairs)
    - **10.0** = Very high activity (10x TVL per day)
    - **1.0** = Moderate activity (1x TVL per day)
    - **0.0** = No trading (only price changes, no fees)
    
    **How it works:**
    - Volume is split between buys/sells based on price direction
    - Price up → more buy volume
    - Price down → more sell volume
    - Fees are earned from this simulated trading
    
    **Typical Values:**
    - Major pairs (ETH/USDC): 5-15x
    - Mid-cap tokens: 2-5x
    - Low liquidity: 0.5-2x
    """)

# Main content
tab1, tab2, tab3 = st.tabs(["📊 Data Fetching", "🚀 Simulation", "📋 Documentation"])

# Tab 1: Data Fetching
with tab1:
    st.markdown('<div class="sub-header">Step 1: Fetch Historical Data</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([2, 2])
    
    with col1:
        st.info(f"**Token:** {token_name} ({token_symbol})")
    with col2:
        st.info(f"**Period:** Last {days_back} days ({start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')})")    
    # Check if API key and valid token ID are provided
    if not api_key:
        st.warning("⚠️ Please enter your CoinGecko API key in the sidebar to fetch data.")
        st.info("👈 Get a free API key from CoinGecko - instructions in the sidebar!")
    
    if not token_id or token_name == "Unknown":
        st.warning("⚠️ Please enter a valid CoinGecko token ID in the sidebar.")
        st.info("💡 Find token IDs at coingecko.com (e.g., 'bitcoin', 'ethereum', 'sonic-3')")
    
    fetch_disabled = not api_key or not token_id or token_name == "Unknown"
    
    if st.button("🔍 Fetch Data from CoinGecko", type="primary", use_container_width=True, disabled=fetch_disabled):
        with st.spinner(f"Fetching {token_name} data from CoinGecko..."):
            try:
                # Initialize fetcher
                fetcher = CoinGeckoFetcher(api_key)
                
                # Fetch data using token ID directly
                data = fetcher.fetch_and_save(
                    coin_identifier=token_id,
                    days=days_back,
                    output_dir="data/raw",
                    use_coin_id=True
                )
                
                if data:
                    # Convert to DataFrame
                    df = pd.DataFrame(data)
                    df['timestamp'] = pd.to_datetime(df['timestamp'])
                    
                    # Store in session state
                    st.session_state.price_data = df
                    st.session_state.data_fetched = True
                    
                    st.success(f"✅ Successfully fetched {len(df)} data points!")
                    
                    # Show saved file path
                    safe_name = token_id.replace(' ', '_').lower()
                    csv_path = f"data/raw/{safe_name}_usd_{start_date.strftime('%Y-%m-%d')}_{end_date.strftime('%Y-%m-%d')}.csv"
                    st.info(f"💾 Data saved to: `{csv_path}`")
                else:
                    st.error("❌ No data received from CoinGecko. Check your token symbol/ID and API key.")
                    
            except Exception as e:
                st.error(f"❌ Error fetching data: {str(e)}")
    
    # Display fetched data
    if st.session_state.data_fetched and st.session_state.price_data is not None:
        st.markdown("---")
        st.markdown("### 📊 Data Preview")
        
        df = st.session_state.price_data
        
        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Data Points", f"{len(df):,}")
        with col2:
            st.metric("Initial Price", f"${df['price'].iloc[0]:.4f}")
        with col3:
            st.metric("Final Price", f"${df['price'].iloc[-1]:.4f}")
        with col4:
            price_change = ((df['price'].iloc[-1] - df['price'].iloc[0]) / df['price'].iloc[0]) * 100
            st.metric("Price Change", f"{price_change:+.2f}%")
        
        # Price chart
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df['timestamp'],
            y=df['price'],
            mode='lines',
            name='Price',
            line=dict(color='#1f77b4', width=2)
        ))
        fig.update_layout(
            title=f"{token_name} Price Over Time",
            xaxis_title="Date",
            yaxis_title="Price (USD)",
            hovermode='x unified',
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Data table
        with st.expander("📋 View Raw Data"):
            st.dataframe(df, use_container_width=True)

# Tab 2: Simulation (Combined Run + Results)
with tab2:
    st.markdown('<div class="sub-header">Step 2: Run Simulation & View Results</div>', unsafe_allow_html=True)
    
    if not st.session_state.data_fetched:
        st.warning("⚠️ Please fetch data first in the 'Data Fetching' tab.")
    else:
        # Display settings at top
        col1, col2, col3 = st.columns(3)
        with col1:
            st.info(f"**Initial Capital:** ${initial_capital:,.2f}")
            st.info(f"**Fee Rate:** {fee_rate*100:.2f}%")
        with col2:
            st.info(f"**Protocol Share:** {pennysia_protocol_share*100:.0f}%")
            st.info(f"**Volume/TVL Ratio:** {volume_tvl_ratio:.1f}x")
        with col3:
            if volume_tvl_ratio > 0:
                st.success("✅ Fee simulation enabled")
            else:
                st.warning("⚠️ No fee earnings")
        
        # Check if parameters have changed
        current_params = {
            'initial_capital': initial_capital,
            'fee_rate': fee_rate,
            'pennysia_protocol_share': pennysia_protocol_share,
            'volume_tvl_ratio': volume_tvl_ratio
        }
        
        params_changed = (st.session_state.last_sim_params != current_params)
        
        if params_changed and st.session_state.simulation_run:
            st.warning("⚠️ Simulation parameters have changed. Click 'Run Simulation' to update results.")
        
        if st.button("🚀 Run Simulation", type="primary", use_container_width=True):
            with st.spinner("Running simulation..."):
                try:
                    # Prepare data
                    df = st.session_state.price_data.copy()
                    df = df.rename(columns={'price': 'price', 'volume_24h': 'volume'})
                    
                    # Initialize simulation
                    sim = SimulationEngine(
                        price_data=df,
                        initial_capital_usd=initial_capital,
                        fee_rate=fee_rate,  # Unified fee rate for both pools
                        pennysia_protocol_share=pennysia_protocol_share,
                        volume_tvl_ratio=volume_tvl_ratio
                    )
                    
                    # Run simulation
                    results = sim.run(verbose=False)
                    
                    # Store results and parameters
                    st.session_state.sim = sim
                    st.session_state.results = results
                    st.session_state.simulation_run = True
                    st.session_state.last_sim_params = current_params
                    
                    st.success("✅ Simulation completed successfully!")
                    
                    # Save results
                    os.makedirs("results", exist_ok=True)
                    results.to_csv("results/simulation_results.csv", index=False)
                    st.info("💾 Results saved to: `results/simulation_results.csv`")
                    
                except Exception as e:
                    st.error(f"❌ Error running simulation: {str(e)}")
        
        st.markdown("---")
        
        # Show results if simulation has been run
        if st.session_state.simulation_run:
            results = st.session_state.results
            sim = st.session_state.sim
            
            # Market performance
            st.markdown("### 📊 Market Performance")
            df = st.session_state.price_data
            initial_price = df['price'].iloc[0]
            final_price = df['price'].iloc[-1]
            price_change = ((final_price - initial_price) / initial_price) * 100
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Initial Price", f"${initial_price:.4f}")
            with col2:
                st.metric("Final Price", f"${final_price:.4f}")
            with col3:
                st.metric("Price Change", f"{price_change:+.2f}%")
            
            st.markdown("---")
            
            # Strategy rankings
            st.markdown("### 🏆 Strategy Rankings")
            
            # Highlight top 3 performers (if available)
            if results is not None and len(results) >= 3:
                # Determine if bull or bear market for label swapping
                is_bull_market = price_change > 0
                
                def swap_labels_if_bear(name):
                    if not is_bull_market and 'Pennysia' in name:
                        return (name.replace('100% Long', 'TEMP_LONG')
                                   .replace('100% Short', '100% Long')
                                   .replace('TEMP_LONG', '100% Short')
                                   .replace('75% Long / 25% Short', 'TEMP_75_25')
                                   .replace('25% Long / 75% Short', '75% Long / 25% Short')
                                   .replace('TEMP_75_25', '25% Long / 75% Short'))
                    return name
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.markdown("#### 🥇 1st Place")
                    top1 = results.iloc[0]
                    st.metric(
                        label=swap_labels_if_bear(top1['name']),
                        value=f"${top1['final_value']:,.2f}",
                        delta=f"{top1['return_pct']:+.2f}%"
                    )
                with col2:
                    st.markdown("#### 🥈 2nd Place")
                    top2 = results.iloc[1]
                    st.metric(
                        label=swap_labels_if_bear(top2['name']),
                        value=f"${top2['final_value']:,.2f}",
                        delta=f"{top2['return_pct']:+.2f}%"
                    )
                with col3:
                    st.markdown("#### 🥉 3rd Place")
                    top3 = results.iloc[2]
                    st.metric(
                        label=swap_labels_if_bear(top3['name']),
                        value=f"${top3['final_value']:,.2f}",
                        delta=f"{top3['return_pct']:+.2f}%"
                    )
            else:
                st.warning("⚠️ Not enough strategies to display top 3")
            
            st.markdown("---")
            
            # Rename strategies based on market direction
            # Determine if bull or bear market
            is_bull_market = price_change > 0
            
            # Create a more readable results table
            display_results = results.copy()
            
            # Swap labels for Pennysia strategies based on market direction
            if not is_bull_market:  # Bear market - swap Long/Short labels
                display_results['name'] = display_results['name'].apply(lambda x: 
                    x.replace('100% Long', 'TEMP_LONG')
                     .replace('100% Short', '100% Long')
                     .replace('TEMP_LONG', '100% Short')
                     .replace('75% Long / 25% Short', 'TEMP_75_25')
                     .replace('25% Long / 75% Short', '75% Long / 25% Short')
                     .replace('TEMP_75_25', '25% Long / 75% Short')
                    if 'Pennysia' in x else x
                )
            
            display_results['rank'] = range(1, len(display_results) + 1)
            display_results = display_results[[
                'rank', 'name', 'initial_value', 'final_value', 
                'return_pct', 'return_absolute'
            ]]
            display_results.columns = [
                'Rank', 'Strategy', 'Initial Value', 'Final Value',
                'Return (%)', 'Return ($)'
            ]
        
            # Format numbers
            display_results['Initial Value'] = display_results['Initial Value'].apply(lambda x: f"${x:,.2f}")
            display_results['Final Value'] = display_results['Final Value'].apply(lambda x: f"${x:,.2f}")
            display_results['Return (%)'] = display_results['Return (%)'].apply(lambda x: f"{x:+.2f}%")
            display_results['Return ($)'] = display_results['Return ($)'].apply(lambda x: f"${x:+,.2f}")
        
            st.dataframe(display_results, use_container_width=True, hide_index=True)
        
            st.markdown("---")
        
            # Performance chart
            st.markdown("### 📈 Performance Comparison")
        
            fig = go.Figure()
        
            for idx, row in results.iterrows():
                fig.add_trace(go.Bar(
                    name=row['name'],
                    x=[row['name']],
                    y=[row['return_pct']],
                    text=[f"{row['return_pct']:+.2f}%"],
                    textposition='outside'
                ))
            
            fig.update_layout(
                title="Return Percentage by Strategy",
                xaxis_title="Strategy",
                yaxis_title="Return (%)",
                showlegend=False,
                height=500
            )
        
            st.plotly_chart(fig, use_container_width=True)
        
            st.markdown("---")
        
            # Value over time
            st.markdown("### 📊 Portfolio Value Over Time")
        
            value_history = sim.get_value_history()
        
            fig = go.Figure()
        
            for col in value_history.columns[1:]:  # Skip timestamp
                fig.add_trace(go.Scatter(
                    x=value_history['timestamp'],
                    y=value_history[col],
                    mode='lines',
                    name=col,
                    line=dict(width=2)
                ))
            
            fig.update_layout(
                title="Portfolio Value Evolution",
                xaxis_title="Date",
                yaxis_title="Portfolio Value (USD)",
                hovermode='x unified',
                height=600,
                legend=dict(
                    orientation="v",
                    yanchor="top",
                    y=1,
                    xanchor="left",
                    x=1.02
                )
            )
        
            st.plotly_chart(fig, use_container_width=True)
        
            st.markdown("---")
        
            # Download results
            st.markdown("### 💾 Export Results")
        
            st.info("📊 Download the complete simulation data for further analysis")
        
            col1, col2, col3 = st.columns(3)
        
            with col1:
                csv = results.to_csv(index=False)
                st.download_button(
                    label="📥 Strategy Results",
                    data=csv,
                    file_name=f"{token_symbol.lower()}_backtest_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    use_container_width=True,
                    help="Download summary results for all strategies"
                )
        
            with col2:
                csv_history = value_history.to_csv(index=False)
                st.download_button(
                    label="📥 Value History",
                    data=csv_history,
                    file_name=f"{token_symbol.lower()}_value_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    use_container_width=True,
                    help="Download time-series portfolio values"
                )
        
            with col3:
                # Combine both datasets
                combined_data = f"# Backtest Results for {token_name} ({token_symbol})\n"
                combined_data += f"# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                combined_data += f"# Period: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}\n"
                combined_data += f"# Initial Capital: ${initial_capital:,.2f}\n\n"
                combined_data += "## Strategy Results\n"
                combined_data += results.to_csv(index=False)
                combined_data += "\n\n## Value History\n"
                combined_data += value_history.to_csv(index=False)
                
                st.download_button(
                    label="📥 Complete Report",
                    data=combined_data,
                    file_name=f"{token_symbol.lower()}_complete_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    use_container_width=True,
                    help="Download all data in one file"
                )

# Tab 3: Documentation
with tab3:
    st.markdown('<div class="sub-header">📚 Documentation</div>', unsafe_allow_html=True)
    
    st.markdown("""
    ## 🧮 How the Simulation Works
    
    ### Core Calculation Method
    
    **Price Tracking via xy=k Formula:**
    - Each day, we calculate the exact swap needed to move the pool price to match market price
    - Uses constant product formula: `reserve_usd × reserve_token = k`
    - Solves for new reserves that achieve target price while maintaining k
    
    **Volume Amplification:**
    - Vol/TVL ratio determines how many times we execute the directional swap
    - Example: Vol/TVL = 3.2 → execute the price-moving swap 3 times
    - More swaps = more fees generated = realistic trading activity
    
    ### Why This Makes Sense
    
    1. **Realistic Price Discovery**: Pools track market price through arbitrage swaps
    2. **Volume Matters**: Higher trading volume = more fee earnings for LPs
    3. **Directional Bias**: In Pennysia, the "winning" side (correct prediction) earns all input fees
    
    ---
    
    ## 📊 The 7 Strategies Compared
    
    **HODL (100% Token):**
    - Baseline: Just hold tokens, no LP position
    - No fees, full price exposure
    
    **Uniswap V2 LP:**
    - Traditional AMM: 50/50 USD/Token
    - Fees distributed equally to all LPs
    - Suffers impermanent loss but earns fees
    
    **Pennysia Strategies:**
    - **100% Long**: Bet on price increase, earns fees only when price rises
    - **75/25 Long/Short**: Bullish bias with some hedge
    - **50/50**: Neutral, similar to Uniswap but with directional fee split
    - **25/75 Short/Long**: Bearish bias with some upside
    - **100% Short**: Bet on price decrease, earns fees only when price falls
    
    **Key Difference**: Pennysia rewards correct predictions with ALL input fees, wrong predictions get nothing.
    
    ---
    
    ## ⚙️ Parameter Guide
    
    **Fee Rate (0.3% default):**
    - Unified for both Uniswap and Pennysia
    - Standard AMM rate, ensures fair comparison
    
    **Protocol Share (20% default):**
    - Portion of Pennysia fees going to protocol (not LPs)
    - Only affects Pennysia strategies
    
    **Volume/TVL Ratio (3.2 default):**
    - How many times the pool's TVL trades per day
    - 3.2 = realistic for active tokens
    - Higher = more fees, better differentiation between strategies
    - Set to 1.0 for minimal volume simulation
    
    **Initial Capital ($10,000 default):**
    - Same for all strategies for fair comparison
    - Uniswap pool gets 10x buffer for deep liquidity
    
    ---
    
    ## 📈 Expected Results
    
    **In a Bear Market (price down):**
    - 100% Short wins (earns all fees from selling pressure)
    - Uniswap V2 middle (earns fees but no directional advantage)
    - 100% Long loses (no fees + impermanent loss)
    
    **In a Bull Market (price up):**
    - 100% Long wins (earns all fees from buying pressure)
    - Uniswap V2 middle
    - 100% Short loses
    
    ### Bear Market (Price Down)
    - Short positions should outperform
    - 100% Short typically wins
    - HODL underperforms
    
    ### Ranging Market (Sideways)
    - Balanced positions stable
    - Fee earnings important
    - LP strategies may outperform HODL
    
    ---
    
    ## 🐛 Troubleshooting
    
    ### "No data received"
    - Check token symbol is correct
    - Verify API key is valid
    - Try with known token (BTC, ETH)
    - Check date range is valid
    
    ### "API Error"
    - Check internet connection
    - Verify API key hasn't expired
    - Try smaller date range
    - Use daily interval instead of hourly
    
    ### "Simulation Error"
    - Ensure data was fetched successfully
    - Check all settings are valid
    - Try with default settings first
    
    """)

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 2rem;">
    <p>Built with ❤️ for Pennysia Protocol Analysis</p>
    <p>Comparing Pennysia's directional liquidity model vs traditional AMMs</p>
</div>
""", unsafe_allow_html=True)
