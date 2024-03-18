import pandas as pd
import numpy as np
from alpaca_functions import *
import datetime
import requests
import pandas_ta
import mplfinance as mpf


today=datetime.datetime.today()
past=today+datetime.timedelta(days=-260)


# Main ticket where we want to make the backtesting
ticker=str(input(f"Enter a ticker symbol: "))
# Benchmark to compare to
benchmark = "SPY"




# Market Data
data, status = market_data(
                            ticker=ticker,
                            since=past,
                            to=today,
                            interval ='1Day',
                            feed='iex'
                            )


benchmark_data, benchmark_status = market_data(
                                                ticker=benchmark,
                                                since= past,
                                                to=today,
                                                interval='1Day',
                                                feed='iex'
                                                )

# Initial amount of money to evaluate the performance
Equity=10000

Start=10000

# Calculate ADX
adx = pandas_ta.adx(data['High'],
                    data['Low'],
                    data['Close']
                    )


# Put all in a Dataframe
col_df1 = ['Open','High','Low','Close','Volume']
col_df2 = ['ADX_14','DMP_14','DMN_14']

data_adx = pd.concat(
                    [
                    data[col_df1],
                    adx[col_df2]
                    ],
                    axis=1
)




# calculate SMA_20, which is important to our strategy
data_adx['SMA_20'] = pandas_ta.sma(
                                    data_adx['Close'],
                                    length=20
                                    )






date_since= data_adx.index.min()
date_to= data_adx.index.max()

#Inicialmente llenar con el Equity del principio
data_adx['Equity']= Equity

#Calcular retornos para buy and hold
data_adx['Return%'] = data_adx['Close'].pct_change()
benchmark_data['BenchmarkReturn%'] = benchmark_data['Close'].pct_change()

data_adx['ticker_return'] = data_adx['Return%'].add(1).cumprod().sub(1)
benchmark_data['benchmark_return'] = benchmark_data['BenchmarkReturn%'].add(1).cumprod().sub(1)

data_adx['Hold'] = (data_adx['ticker_return'] + 1) * Equity
benchmark_data['Hold'] = (benchmark_data['benchmark_return'] + 1) * Equity


#Backtest Event Driven Manual
#Recorrer los precios barra por barra
#Ver si hay senal,comprar y vender de acuerdo
#a lo que corresponda,actualizar equity

# Buy is going to be the trigger of the purchase signal
data_adx['Buy_signal']=(
                data_adx['DMP_14']>=data_adx['DMN_14']) \
                    & (data_adx['ADX_14'] <= 20)
#& (data_adx['SMA_20'] <= data_adx['Close'].shift(1))

# "Buy_Stop" is gonna be the  stop loss for the buy order
data_adx['Buy_Filter'] = (data_adx['Close'] <= data_adx['SMA_20'])


# Necessary DataFrames to log the Signals:
signals = pd.DataFrame(columns=["Signal"])
close_signals = pd.DataFrame(columns=['Close_signal'])


# Variables to take some stats:
gains = 0
ng = 0
losses = 0
nl = 0
cum_returns = 1


results = pd.DataFrame()
percentagechange = []

#comienzo sin posicion
position = 0
Position_Status = 'Close'
price = 0
print("Antes del bucle: Position =", position, "Equity =", Equity)


signals = pd.DataFrame(columns=["Signal"])
close_signals = pd.DataFrame(columns=['Close_signal'])

returns = []

max_returns = []
min_returns = [] 


#loop 
for index, row in data_adx.iterrows():
    #Check if there is an active position:
    if position == 0:
    
        # There is Signal BLIATZ?
        if  (row['Buy_signal'] and not row['Buy_Filter']):
            position = 1
            data_adx.loc[index, 'Equity'] = (row['Return%']+1) * Equity
            Equity = data_adx.loc[index, 'Equity']
            
            # way 2 to calculate returns
            price = data_adx.iloc[data_adx.index.get_loc(index) + 1]['Open']
            
            
            # Graphic porpouses
            signals.loc[index, 'Signal'] = 1
            signals.loc[index, 'Price'] =  price
            close_signals.loc[index, 'Close_signal'] = np.nan
            print("  ---  Buy Filled  ---  |  at price: ", data_adx.loc[index, 'Close'])
            print(Equity)
        else:
            data_adx.loc[index, 'Equity'] = Equity
            signals.loc[index, 'Signal'] = np.nan
            close_signals.loc[index, 'Close_signal'] = np.nan
    
    
    elif not row['Buy_Filter']:

        
        # Position Open
        # Calculate Returns
        data_adx.loc[index, 'Equity'] = (row['Return%']+1) * Equity
        Equity = data_adx.loc[index, 'Equity']
        position = 1
        
        # Graphic porpouses
        signals.loc[index, 'Signal'] = np.nan
        close_signals.loc[index, 'Close_signal'] = np.nan
        
        print(" POSITIONS STILL OPENED  |" , )
        print("Equity : ", Equity)

    elif (position == 1 & row['Buy_Filter']):
        
        #  Close the position
        data_adx.loc[index, 'Equity'] = Equity
        #Position_Status = 'Close'
        close = data_adx.loc[index, 'Close']
        Equity = data_adx.loc[index, 'Equity']
        position = 0
        
        position_return = (close - price)/price
        returns.append(position_return)
        
        #   Graphic Porpouse
        close_signals.loc[index,'Close_signal'] = 1 
        close_signals.loc[index, 'Price'] = close
        close_signals.loc[index, 'Close_marker'] = (close*1.01)
        signals.loc[index, 'Signal'] = np.nan
        
        print("  --- CLOSE POSITION ---  | at price: ",data_adx.loc[index, 'Close'])
        print("Equity : ", Equity)
        
    else:
        
        # If I have no Position, equity remains equal
        data_adx.loc[index, 'Equity'] = Equity
        signals.loc[index, 'Signal'] = np.nan
        close_signals.loc[index, 'Close_signal'] = np.nan


for i in returns:
    if (i > 0):
        gains+=i
        ng+=1
    else:
        losses+=i
        nl+=1
    cum_returns *= (1 + i)
# Total Returns
total_r = round((cum_returns-1)*100,2)
print(total_r)

if(ng>0):
    avgGain=gains/ng
    maxR=str(max(returns))+ ' %'
else:
    avgGain=0
    maxR='Undifined'

if(nl>0):
    avgLoss=losses/ng
    maxL=str(min(returns))+' %'
    ratio=str(-avgGain/avgLoss)
else:
    avgLoss=0
    maxL = 'Undifined'

if (ng>0 or nl>0):
    battingAvg=ng/(ng+nl)
else:
    battingAvg=0


print()
print("Results for "+ ticker +" going back to "+str(data_adx.index[0])+", Sample size: "+str(ng+nl)+" trades")
print("Batting Avg: "+ str(battingAvg))
print("Gain/loss ratio: "+ ratio)
print("Average Gain: "+ str(avgGain))
print("Average Loss: "+ str(avgLoss))
print("Max Return: "+ maxR)
print("Max Loss: "+ maxL)
print("Total return over "+str(ng+nl)+ " trades: "+ str(total_r)+" %" )
#print("Example return Simulating "+str(n)+ " trades: "+ str(nReturn)+"%" )
print()


since_date = data_adx.index.min()
to_date = data_adx.index.max()

plot_chart(data_adx['Equity'].sub(Start),
                ticker+" ADX sin BIAS " +since_date+" a "+to_date)
#Hold
plot_chart(data_adx['Hold'].sub(Start),
                ticker+" HODL " +since_date+" a "+to_date)
plot_chart(benchmark_data['Hold'].sub(Start),
                benchmark+" HODL "+since_date+" a "+to_date)



data_adx.index = pd.to_datetime(data_adx.index)
since_date = data_adx.index.min()
to_date = data_adx.index.max()
tdf = data_adx.loc[since_date:to_date,]  # Take a smaller data set so it's easier to see the scatter points

adx_columns = ['ADX_14', 'DMP_14','DMN_14']
adx = tdf[adx_columns]
#adx.index = pd.to_datetime(adx.index)
#apd_adx = adx.loc['2024-02-21T11:30:00Z':'2024-02-23T17:30:00Z',]
signals.index = pd.to_datetime(signals.index)

signals_colums = ['Price']
apd_signals = signals[signals_colums]
apd_signals['Marker'] = (signals[signals_colums])*0.95
apd_signals = apd_signals.loc[since_date:to_date,]
apd_signals.index = pd.to_datetime(apd_signals.index)

# Close signals:
close_signals.index = pd.to_datetime(close_signals.index)
apd_close_signals = close_signals[signals_colums]
apd_close_signals['Marker'] = (close_signals[signals_colums])*1.05

apd_close_signals = apd_close_signals.loc[since_date:to_date,]


apds = [mpf.make_addplot((adx),panel = 1),
        mpf.make_addplot(apd_signals['Price'],type='scatter',markersize=2,color = 'b'),
        mpf.make_addplot(apd_signals['Marker'],type='scatter',markersize=50,marker='^'),
        mpf.make_addplot(apd_close_signals['Marker'], type = 'scatter',markersize=50,marker='v', color='r'),
        mpf.make_addplot(apd_close_signals['Price'], type = 'scatter',markersize=2, color='r')
]


mpf.plot(tdf,
         addplot=apds,
         type = "candle",   
         mav=20)


# If you want the plot to be saved, used this code instead:
'''
mpf.plot(tdf,
         addplot=apds,
         type = "candle",   
         mav=20,
         savefig=dict(fname=f'Path\\{ticker}performance_100.jpg',dpi=100,pad_inches=0.25))
'''
