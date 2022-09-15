import MetaTrader5 as mt5
from datetime import datetime
import pandas as pd
import time
import schedule
import pytz

'''
This file is meant to ---
'''

#Functionalize components

#Connect to MT5
def connect(account = 5006389422):
    mt5.initialize()
    authorized = mt5.login(account, password = "mbkzkta5", server = "MetaQuotes-Demo")

    if authorized:
        print("Connected: Connecting to MT5 Client")
    else:
        print(f"Failed to connect at {account}, error code: {mt5.last_error()}")

#Open position for the trade
def openPosition(pair, order_type, size, tp_distance = None, stop_distance = None):
    symbol_info = mt5.symbol_info(pair)
    if symbol_info is None:
        print(f"{pair} not found")
        return
    
    if not symbol_info.visible:
        print(f"{pair} is not visible, trying to switch it on")
        if not mt5.symbol_select(pair, True):
            print(f"symbol_select({pair}) failed, exit now")
            return
    
    print(f"{pair} found!")

    #Executing the order
    point = symbol_info.point

    #If we ask to BUY
    if order_type == "BUY":
        order = mt5.ORDER_TYPE_BUY
        price = mt5.symbol_info_tick(pair).ask
        if stop_distance:
            sl = price - (stop_distance * point)
        if tp_distance:
            tp = price + (tp_distance * point)
    
    #If we ask to SELL
    if order_type == "SELL":
        order = mt5.ORDER_TYPE_SELL
        price = mt5.symbol_info_tick(pair).bid
        if stop_distance:
            sl = price + (stop_distance * point)
        if tp_distance:
            tp = price - (tp_distance * point)
    
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": pair,
        "volume": float(size),
        "type": order,
        "price": price,
        "sl": sl,
        "tp": tp,
        "magic": 234000,
        "comment": "",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }

    result = mt5.order_send(request)

    print(result.comment)

    if result.retcode != mt5.TRADE_RETCODE_DONE:
        print("Failed to send order :(")
    else:
        print("Order successfully placed!")

#Information on the trade (important for closing!)
def positionsGet(symbol = None):
    if symbol is None:
        res = mt5.positions_get()
    else:
        res = mt5.positions_get(symbol = symbol)
    

    if res is not None and res != ():
        df = pd.DataFrame(list(res), columns = res[0]._asdict().keys())
        df['time'] = pd.to_datetime(df['time'], unit = 's')
        return df
    
    return pd.DataFrame()

def closePosition(deal_id):
    open_positions = positionsGet()
    open_positions = open_positions[open_positions['ticket'] == deal_id]

    order_type = open_positions['type'][0]
    symbol = open_positions['symbol'][0]
    volume = open_positions['volume'][0]
    
    #Redefining the order type
    if order_type == mt5.ORDER_TYPE_BUY:
        order_type = mt5.ORDER_TYPE_SELL
        price = mt5.symbol_info_tick(symbol).bid
    else:
        order_type = mt5.ORDER_TYPE_SELL
        price = mt5.symbol_info_tick(symbol).ask
    
    #Creating a request
    close_request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": float(volume),
        "type": order_type,
        "position": deal_id,
        "price": price,
        "magic": 234000,
        "comment": "close the trade",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }

    #Submit the order request
    result = mt5.order_send(close_request)

    if result.retcode != mt5.TRADE_RETCODE_DONE:
        print("Failed to close order :(")
    else:
        print("Order successfully closed!")

#Close all trades referring to a symbol
def close_positions_by_symbol(symbol):
    open_positions = positionsGet(symbol)
    open_positions['ticket'].apply(lambda x: closePosition(x))

#Connecting to MT5 to get the data
def run_trader(time_frame):
    connect()
    get_data(time_frame)

#Get data from MT5
def get_data(time_frame):
    pairs = ['EURUSD', 'USDCAD']
    pair_data = {}

    for pair in pairs:
        utc_start = datetime(2021, 1, 1)
        date_end = datetime.now().astimezone(pytz.timezone('Europe/Athens'))
        date_end = datetime(date_end.year, date_end.month, date_end.day, hour = date_end.hour, minute = date_end.minute)
        rates = mt5.copy_rates_range(pair, time_frame, utc_start, date_end)
        rates_frame = pd.DataFrame(rates)
        rates_frame['time'] = pd.to_datetime(rates_frame['time'], unit = 's')
        rates_frame.drop(rates_frame.tail(1).index, inplace = True)
        pair_data[pair] = rates_frame
        print(pair_data[pair])
            
    return pair_data

#Live trading
def live_trading():
    schedule.every().hour.at(":00").do(run_trader, mt5.TIMEFRAME_M15)
    schedule.every().hour.at(":15").do(run_trader, mt5.TIMEFRAME_M15)
    schedule.every().hour.at(":30").do(run_trader, mt5.TIMEFRAME_M15)
    schedule.every().hour.at(":45").do(run_trader, mt5.TIMEFRAME_M15)

    while True:
        schedule.run_pending()
        time.sleep(1)




if __name__ == '__main__':
    live_trading()

connect()
openPosition("EURUSD", "BUY", 1, 300, 100)
openPosition("EURUSD", "BUY", 5, 200, 50)
close_positions_by_symbol("EURUSD")