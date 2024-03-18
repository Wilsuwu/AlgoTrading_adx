import datetime
import requests
import pandas as pd
import secret as secret
import sys
from alpaca.data.historical import CryptoHistoricalDataClient
from alpaca.data.requests import CryptoBarsRequest
from alpaca.data.timeframe import TimeFrame

import matplotlib.pyplot as plt

# Market Data function
def market_data (ticker,since,to,interval,feed):
    #datos=yf.download(ticker, start=since, end=to,interval=interval)

    #datetime standard Python 2022-01-08 02:36:03.198203
    #datetieme ISO RFC-3339 2022-02-06T0:00:00Z
    since_formated = since.strftime('%Y-%m-%d')
    to_formated = to.strftime("%Y-%m-%d")
    

    url = "https://data.alpaca.markets/v2/stocks/"+ticker+"/bars?feed="+feed+"&timeframe="+interval+"&start="+since_formated+"&end="+to_formated

    payload = {}
    headers = {
         "APCA-API-KEY-ID":secret.alpaca_api_key,
         "APCA-API-SECRET-KEY":secret.alpaca_secret_key       
    }

    response = requests.request("GET", url, headers=headers, data=payload)

    market_data_status = response.status_code

    # The response Code 200 establishes that the connection was OK
    # But it doesn't mean that the data we received is correct
    # Just that we could connect to the API
    status_OK = 200
    status_missing_parameters = 422
    status_too_many_requests = 429
    status_unauthorized = 403
    status_invalid_parameter = 400

    if market_data_status == status_OK:
        # JSON format
        print("MarketData Connection OK ")
        print(response)
        api_response = response.json()
        # print("Server response ", api_response)
        print(api_response)
        api_response_df = pd.json_normalize(api_response['bars'])
        
        # Formatting
        # We want the dates as the index
        api_response_df.set_index("t", inplace=True)

        # We want the column names to be like YFinance
        api_response_df.rename(
            columns={
                "o": "Open",
                "h": "High",
                "l": "Low",
                "c": "Close",
                "v": "Volume",
            },
            inplace=True
        )

        api_response_df.index.rename("Date", inplace=True)
        
    else:
        print("Error! ", response.status_code)
        # sys.exit aborts the program wherever it is
        sys.exit("No connection to Market Data - Abort")
        return

    return api_response_df, market_data_status




# Function that fetches crypto market data
# Adapted for Alpaca API
def market_crypto_data(ticker, since, to, interval):
    # Uncomment the line below if using yfinance library
    # data = yf.download(ticker, start=since, end=to, interval=interval)

    # Format the input into standard datetime to ISO RFC-3339
    # as required by the documentation
    # Each API is different
    # Yes, there are various ways to do this; this is the most direct one
    # Standard Python datetime 2022-01-08 02:36:03.198203
    # ISO RFC-3339 datetime 2022-02-06T0:00:00Z
    since = since.isoformat()[:-7] + 'Z'
    to = to.isoformat()[:-7] + 'Z'

    # Alpaca Crypto Client
    # No keys required for crypto data
    client = CryptoHistoricalDataClient()

    # Creating request object
    request_params = CryptoBarsRequest(
        symbol_or_symbols=ticker,
        timeframe=interval,
        start=since
    )

    # The response code 200 establishes that the connection was OK
    # It does not mean that the data received is correct
    # Just that we could connect without problems.
    status_OK = 200
    status_missing_parameters = 422
    status_too_many_requests = 429
    status_unauthorized = 403
    status_invalid_parameter = 400

    # Retrieve daily bars for Bitcoin in a DataFrame and printing it
    response = client.get_crypto_bars(request_params)

    # status = status_OK
    api_response_df = response.df
    return api_response_df

# Function to check the current market status
def market_open():
    # Trading API (each one is different)
    api_url_market = "https://paper-api.alpaca.markets/v2"

    # Market Clock Endpoint
    api_market_clock = "/clock"

    headers = {
        'accept': 'application/json',
        "APCA-API-KEY-ID": secret.alpaca_api_key,
        "APCA-API-SECRET-KEY": secret.alpaca_secret_key
    }

    status_OK = 200

    response = requests.get(api_url_market + api_market_clock,
                            headers=headers
                            )

    if response.status_code == status_OK:
        # Requesting data in JSON format
        print("Connection OK ")

        api_response = response.json()

        api_response_df = pd.json_normalize(api_response)

        return api_response_df

    else:
        print("Error! ", response.status_code)
        # sys.exit aborts the program wherever it is
        sys.exit("No connection to Broker - Abort")
        return False



# Function to check if we can trade:

def can_trade():
    # Trading API (each one is different)
    api_url_market = "https://paper-api.alpaca.markets/v2"

    # Account Endpoint
    api_market_account = "/account"

    headers = {
        'accept': 'application/json',
        "APCA-API-KEY-ID": secret.alpaca_api_key,
        "APCA-API-SECRET-KEY": secret.alpaca_secret_key
    }

    status_OK = 200

    response = requests.get(api_url_market + api_market_account,
                            headers=headers
                            )

    if response.status_code == status_OK:
        # Requesting data in JSON format
        print("Broker Connection OK ")

        api_response = response.json()

        api_response_df = pd.json_normalize(api_response)
        # Basic condition of an active account and buying power greater than 0
        # Remember that there are many other conditions, and checking them
        # depends on each API
        if (
                api_response_df['status'].values == "ACTIVE"
        ) and \
                \
                (
                        float(api_response_df['buying_power'].iloc[0]) > 0
                ):

            print("Active Account")
            print("Buying Power > 0 OK")
            print("Trading OK")
            return True
        else:

            print("Error in the account, check the Broker")
            print("Status:", api_response_df['status'])
            print("BuyingPower:", api_response_df['buying_power'])
            # sys.exit aborts the program wherever it is
            sys.exit("Account not enabled for Trading - Abort")

    else:
        print("Error! ", response.status_code)
        sys.exit("No connection to Broker - Abort")
        return False


def plot_chart(data_series, title="", x_axis_title="", y_axis_title=""):
    
    # Change index to datetime
    data_series.index = pd.to_datetime(data_series.index)
    
    # Plotting
    fig, ax = plt.subplots(figsize=(10, 5), constrained_layout=True)
    
    ax.plot(data_series,
            color='#030764', 
            marker='o',
            lw=1.5)
    
    # Background Format
    fig.set_facecolor('azure')
    # Other colors?
    # https://matplotlib.org/3.5.1/gallery/color/named_colors.html
    
    # Titles
    plt.title(title)
    
    # Grid ON
    plt.grid(True)
    plt.xlabel(x_axis_title)
    plt.ylabel(y_axis_title)
    
    # Rotate tick titles
    # Get current titles
    x_labels = ax.get_xticklabels()
    # Apply rotation, change x to y for the other axis
    plt.setp(x_labels, rotation=45)
    
    plt.show()



def ADX(stock_data): 
    
    high, low, close = 'High', 'Low', 'Close'
    stock_data = stock_data.reset_index()
    columns = ['Date' ,high, low, close]

    stock_data = stock_data[columns]
    
    def calc_val(df, column):
        prev_val = df.loc[i-1, column]
        curr_val = df.loc[i, column]
        return(curr_val, prev_val)

    
    def calc_dm(df, index):
        curr_high, prev_high = calc_val(df, high)
        curr_low, prev_low = calc_val(df, low)

        dm_pos = curr_high - prev_high
        dm_neg = prev_low - curr_low
        
        if dm_pos > dm_neg:
            if dm_pos < 0:
                dm_pos = 0.00
            dm_neg = 0.00
            return(dm_pos, dm_neg)

        elif dm_pos < dm_neg:
            if dm_neg < 0:
                dm_neg = 0.00
            dm_pos = 0.00
            return(dm_pos, dm_neg)
        
        else:
            if dm_pos < 0:
                dm_pos = 0.00
            dm_neg = 0.00
            return(dm_pos, dm_neg)
    
    def calc_tr(df, index):
        curr_high, prev_high = calc_val(df, high)
        curr_low, prev_low = calc_val(df, low)
        curr_close, prev_close = calc_val(df, close)
        ranges = [curr_high - curr_low, abs(curr_high - prev_close), abs(curr_low - prev_close)]
        TR = max(ranges)
        return(TR)

    def calc_first_14(df, index, column):
        result = 0
        for i in range(index-13, index+1):
            result += df.loc[i, column]
        return(result)

    def calc_subsequent_14(df, index, column):
        return(df.loc[index-1, column+'14'] - (df.loc[index-1, column+'14']/14) + df.loc[index, column])

    def calc_first_adx(df, index):
        result = 0
        for i in range(index-13, index+1):
            result += df.loc[i, 'DX']
        return(result/14)

    def calc_adx(df, index):
        return(round(((df.loc[index-1, 'ADX']*13) + df.loc[index, 'DX'])/14, 2))
    
    for i in range(1, len(stock_data)):
        dm_pos, dm_neg = calc_dm(stock_data, i)
        TR = calc_tr(stock_data, i)
        stock_data.loc[i, '+DM'] = dm_pos
        stock_data.loc[i, '-DM'] = dm_neg
        stock_data.loc[i, 'TR'] = TR

    if stock_data.TR.count() == 14:
        stock_data.loc[i, 'TR14'] = calc_first_14(stock_data, i, 'TR')
        stock_data.loc[i, '+DM14'] = calc_first_14(stock_data, i, '+DM')
        stock_data.loc[i, '-DM14'] = calc_first_14(stock_data, i, '-DM')

    elif stock_data.TR.count() >= 14:
        stock_data.loc[i, 'TR14'] = round(calc_subsequent_14(stock_data, i, 'TR'),2)
        stock_data.loc[i, '+DM14'] = round(calc_subsequent_14(stock_data, i, '+DM'), 2)
        stock_data.loc[i, '-DM14'] = round(calc_subsequent_14(stock_data, i, '-DM'), 2)
    
    if 'TR14' in stock_data.columns:
        stock_data.loc[i, '+DI'] = round((stock_data.loc[i, '+DM14'] / stock_data.loc[i, 'TR14'])*100, 2)
        stock_data.loc[i, '-DI'] = round((stock_data.loc[i, '-DM14'] / stock_data.loc[i, 'TR14'])*100, 2)

        stock_data.loc[i, 'DX'] = round((abs(stock_data.loc[i, '+DI'] - stock_data.loc[i, '-DI'])/abs(stock_data.loc[i, '+DI'] + stock_data.loc[i, '-DI']) )*100 , 2)

    if 'DX' in stock_data.columns:
        if stock_data.DX.count() == 14:
            stock_data.loc[i, 'ADX'] = calc_first_adx(stock_data, i)
        
        elif stock_data.DX.count() >= 14:
            stock_data.loc[i, 'ADX'] = calc_adx(stock_data, i)
    
    
    return stock_data

def buy_single_stock(ticker):
    # Trading API (each one is different)
    api_url_market = "https://paper-api.alpaca.markets/v2"
    api_orders = "/orders"
    
    headers = {
        'accept': 'application/json',
        "APCA-API-KEY-ID": secret.alpaca_api_key,
        "APCA-API-SECRET-KEY": secret.alpaca_secret_key
    }
    
    status_OK = 200

    # Number of contracts (shares) to buy
    contracts = 1
    buy_sell = "buy"
    order_type = "market"
    order_time_force = "gtc"
    order_class = "simple"

    params = {
        "symbol": ticker,
        "qty": contracts,
        "side": buy_sell,
        "type": order_type,
        "time_in_force": order_time_force,
        "order_class": order_class
    }

    # Make a POST request to place the order
    response = requests.post(api_url_market + api_orders,
                             json=params,
                             headers=headers
                             )

    if response.status_code == status_OK:
        # Request data in JSON format
        print("Connection OK ")
        api_response = response.json()
        
        api_response_df = pd.json_normalize(api_response)
        
        if api_response_df['status'].values == "accepted":
            print("Order accepted by the Market")
            print("Order ID:", api_response_df['id'].values)
            print("Order Time:", api_response_df['submitted_at'].values)
            print("Order Status:", api_response_df['status'].values)
            print("Order Fill Status:", api_response_df['filled_at'].values)
        else:
            print(response.status_code,"\n",'order status: ',api_response_df['status'].values)
            
        return api_response_df
    else:
        print("Error! ", response.status_code)
        sys.exit("The order could not be placed!")

    return
