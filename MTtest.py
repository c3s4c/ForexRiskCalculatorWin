import MetaTrader5 as mt5

symbol = "XAUUSD"
if not mt5.initialize():
    print("MT5 init failed")
else:
    info = mt5.symbol_info(symbol)
    if info:
        print("Contract size:", info.trade_contract_size)
        print("Point:", info.point)
        print("Digits:", info.digits)
        print("Tick value:", info.trade_tick_value)
        print("Description:", info.description)
    else:
        print("Symbol not found.")
    mt5.shutdown()
