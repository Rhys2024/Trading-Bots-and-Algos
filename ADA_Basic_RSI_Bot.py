import pandas as pd
import websocket, talib, datetime, numpy, pprint, config, json
from binance.enums import *
from binance.client import Client

closes = []

client = Client(config.API_KEY, config.API_SECRET, tld='us')

in_position = False

RSI_PERIOD = 14
OVERSOLD_THRESHOLD = 30
OVERBOUGHT_THRESHOLD = 70
TRADE_QUANTITY = 8
TRADE_SYMBOL = 'ADAUSD'
SOCKET = 'wss://stream.binance.com:9443/ws/adausdt@kline_1m'

def order(side, quantity, symbol, order_type=ORDER_TYPE_MARKET):
    try:
        print('\nsending order....\n')
        order = client.create_order(symbol=symbol, side = side, type = order_type, quantity = quantity)
        print(order)
    except Exception as e:
        return False
    return True

def on_open(ws):
    print('\nopened connection')

def on_close(ws):
    # CTRL+C to close the connection
    print('\nclosed connection')

def on_message(ws, message):
    print("Message Received...")
    global closes
    global in_position
    json_message = json.loads(message)

    candle = json_message['k']

    is_candle_closed = candle['x']
    close = candle['c']

    if is_candle_closed:
        print("\n\ncandle closed at {}\n".format(close))
        closes.append(float(close))

        if len(closes) > RSI_PERIOD:
            np_closes = numpy.array(closes)
            rsi = talib.RSI(np_closes, RSI_PERIOD)
            
            print('All RSIs so far:')
            print(rsi, '\n')
            last_rsi = rsi[-1]
            print('The current RSI is {}'.format(last_rsi))

            if last_rsi > OVERBOUGHT_THRESHOLD:
                if in_position:
                    print('\nOver-Bought -- SELL SELL SELL\n')
                    #Put Binance Order Logic Here
                    order_succeeded = order(SIDE_SELL, TRADE_QUANTITY, TRADE_SYMBOL)
                    if order_succeeded:
                        in_position = False
                else:
                    print("\nIt is Over-Bought, but you don't own any!  Nothing to do!\n")
            
            if last_rsi < OVERSOLD_THRESHOLD:
                if in_position:
                    print('\nIt is Over-Sold, but you already own it!  Nothing to do!\n')
                else:
                    print('\nIt is Over-Sold -- BUY BUY BUY\n')
                    # Put Binance Order Logic Here
                    order_succeeded = order(SIDE_BUY, TRADE_QUANTITY, TRADE_SYMBOL)
                    if order_succeeded:
                        in_position = True

ws = websocket.WebSocketApp(SOCKET, on_open=on_open,on_close=on_close, on_message=on_message)
ws.run_forever()











