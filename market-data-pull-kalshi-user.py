# %%
from os import path
import pandas as pd
import requests
import datetime
import base64
import os
from urllib.parse import urlparse
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import padding

# Configuration
API_KEY_ID = 'Insert API key ID here'  # e.g. 'abc123def456ghi789'
PRIVATE_KEY_PATH = 'Insert private key file path here'  # e.g. 'private_key.pem'
BASE_URL = 'https://external-api.kalshi.com/trade-api/v2'

# DIAGNOSTIC CHECKS
print("=== DIAGNOSTICS ===")
print(f"1. Private key file exists: {os.path.exists(PRIVATE_KEY_PATH)}")
print(f"2. API Key ID: {API_KEY_ID}")
print(f"3. Using endpoint: {BASE_URL}")
print()

def load_private_key(key_path):
    with open(key_path, "rb") as f:
        return serialization.load_pem_private_key(f.read(), password=None, backend=default_backend())

def create_signature(private_key, timestamp, method, path):
    """Create the request signature."""
    # Strip query parameters before signing
    path_without_query = path.split('?')[0]
    message = f"{timestamp}{method}{path_without_query}".encode('utf-8')
    signature = private_key.sign(
        message,
        padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.DIGEST_LENGTH),
        hashes.SHA256()
    )
    return base64.b64encode(signature).decode('utf-8')

def get(private_key, api_key_id, path, base_url=BASE_URL):
    """Make an authenticated GET request to the Kalshi API."""
    timestamp = str(int(datetime.datetime.now().timestamp() * 1000))
    # Signing requires the full URL path from root (e.g. /trade-api/v2/portfolio/balance)
    sign_path = urlparse(base_url + path).path
    signature = create_signature(private_key, timestamp, "GET", sign_path)

    headers = {
        'KALSHI-ACCESS-KEY': api_key_id,
        'KALSHI-ACCESS-SIGNATURE': signature,
        'KALSHI-ACCESS-TIMESTAMP': timestamp
    }

    return requests.get(base_url + path, headers=headers)

# Load private key
private_key = load_private_key(PRIVATE_KEY_PATH)

# %%
# Get historical market data for all markets in a single event
series_prefix = 'KXPGATOP10-TRC26'  # Series prefix from event
start_date_str = '2026-05-04-00:00:01Z'
end_date_str = '2026-05-07-05:00:00Z'

# Clear dataframe if it exists
try:
    del df
except NameError:
    pass

# Convert ISO format date strings to Unix timestamps (milliseconds)
# Format: '2026-05-11-00:00:00Z' -> Unix timestamp in milliseconds (int64)
def date_to_unix_timestamp_ms(date_str):
    # Parse ISO format date - handle the format with hyphens
    # Replace the format from '2026-05-11-00:00:00Z' to standard ISO format
    dt_str = date_str.replace('Z', '+00:00')
    try:
        # Try parsing as standard ISO format
        parsed_dt = datetime.datetime.fromisoformat(dt_str)
    except:
        # If that fails, try replacing middle dash with T
        dt_str = date_str[:10] + 'T' + date_str[11:-1] + '+00:00'
        parsed_dt = datetime.datetime.fromisoformat(dt_str)
    
    # Convert to Unix timestamp in seconds
    unix_ts_s = int(parsed_dt.timestamp())
    return unix_ts_s

start_date = date_to_unix_timestamp_ms(start_date_str)
end_date = date_to_unix_timestamp_ms(end_date_str)

print(f"=== FETCHING MARKETS FOR SERIES: {series_prefix} ===\n")

# Step 1: Get all markets matching the series prefix
response = get(private_key, API_KEY_ID, f'/markets?event_ticker={series_prefix}')

if response.status_code == 200:
    data = response.json()
    markets = data.get('markets', [])
    print(f"Found {len(markets)} markets for series {series_prefix}\n")
    
    # Display market info
    print("Markets in this series:")
    for market in markets:
        ticker = market.get('ticker', 'N/A')
        title = market.get('title', 'N/A')
        print(f"  - {ticker}: {title}")

        print("FETCHING TRADES FOR MARKET:", ticker)
        # Step 2: Fetch historical trades for this market
        hist_response = get(private_key, API_KEY_ID, f'/markets/trades?ticker={ticker}&limit=1000&min_ts={start_date}&max_ts={end_date}')
        if hist_response.status_code == 200:
            trades_list = hist_response.json().get('trades', [])
            # Add title to each trade record
            for trade in trades_list:
                trade['title'] = title
            try:
                df
                df = pd.concat([df, pd.DataFrame(trades_list)], ignore_index=True)
            except NameError:
                df = pd.DataFrame(trades_list)
            print(f"  -> Found {len(trades_list)} trades for market {ticker} in the specified date range\n")
        else:
            print(f"  -> Failed to fetch trades for market {ticker}. Status code: {hist_response.status_code}\n")
else:
    print(f"Failed to fetch markets for series {series_prefix}. Status code: {response.status_code}")

print("=== DATA FETCH COMPLETE ===")

# %%
print(df.to_string(index=False))

# Sort df by creared_time
df = df.sort_values(by='created_time', ascending=True)

# Send to csv for backup
df.to_csv('kalshi_golf_trades_' + series_prefix + '_' + start_date_str[:10] + '_' + end_date_str[:10] + '.csv', index=False)


