# AMM-Sports-Prediction-Markets
Using Kalshi API for market data, this project goal is to research and design AMM (automated market making) strategies for optimal risk/return while providing efficient liquidity across various US sports markets.

## Overview
The goal is to explore potential MM strategies that can be phased in across major and minor US sport markets - as of May 2026 intial eploration begins with the PGA. The market data pull utilizes Kalshi's API and currently saves down pre-tournament trading activity (Monday - Thursday 5AM EST). End goals look to find profitable AMM strategies that improve general market effiency through the additional liquidity provided, esuring optimal sizing across various golf markets. The idea is to use a base framework that can be automatically tuned to each market given certain characteristics.

## Current Files
### Folder:
  **_market-data_**: includes 2026 tournament market data for winner and top 10 finisher markets\
  
### Scripts: 
  **_market-data-pull-kalshi-user_**: pulls data based on date range and tournament event (winner, top 10, etc.)\
  **_pga-liquidity-strategy-analysis-may2026_**: analyzes trade data for inefficient market activity and potential bid/ask (yes/no) spreads for optimal MM implementation 

## Limitations
1. Market data pull has limit of 1000 trades per market - liquid markets or popular players will tend to exceed this limitation for pre-tournament trading, especially in the winner markets. Must pull daily trade data and aggregate to single dataset.
2. Kalshi API does not have historical orderbook data to align with trade data. Will need to join with addtional API or develop own algo.
