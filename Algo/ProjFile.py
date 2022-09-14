import MetaTrader5 as mt5
from datetime import datetime

#Account Info
account = 5006389422

#Initialize the connection and login to MT5
mt5.initialize()
authorized = mt5.login(account, password = "mbkzkta5", server = "MetaQuotes-Demo")

if authorized:
    print("Connected: Connecting to MT5 Client")
else:
    print(f"Failed to connect at {account}, error code: {mt5.last_error()}")

#------------------------------------------------------------------------------------
#Move here only after you are authorized!!!

#Sample timeblock
utc_start = datetime(2021, 1, 1)
utc_end = datetime(2021, 1, 10)

#Pull data
rates = mt5.copy_rates_range("EURUSD", mt5.TIMEFRAME_H4, utc_start, utc_end)

#Observe the data
for rate in rates:
    print(rate)

