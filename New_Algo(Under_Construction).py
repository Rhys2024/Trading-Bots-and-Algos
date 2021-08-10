import pandas as pd
import websocket, talib, datetime, numpy, pprint, config, json
from binance.enums import *
from binance.client import Client

closes = []
highs = []
lows = []
rsi_rocs = []
rsi_rocs_bought = []

client = Client(config.API_KEY, config.API_SECRET, tld='us')

in_position = False
is_over = False
is_under = False

RSI_PERIOD = 14
OVERSOLD_THRESHOLD = 20
OVERBOUGHT_THRESHOLD = 80
RSI_INDICATION = 50
TRADE_QUANTITY = 0.2
TRADE_SYMBOL = 'ETCUSD'
SOCKET = 'wss://stream.binance.com:9443/ws/etcusdt@kline_1m'

def roc(firstvalue, presentvalue):
    global rsi_rocs
    rsi_roc = ((presentvalue - firstvalue) / (firstvalue) ) * 100
    if in_position:
        rsi_rocs_bought.append(rsi_roc)
    rsi_rocs.append(rsi_roc)
    return rsi_roc




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
    global highs 
    global lows
    global in_position
    global is_over
    global is_under
    overboughts = []
    underboughts = []
    json_message = json.loads(message)

    candle = json_message['k']

    is_candle_closed = candle['x']
    close = candle['c']
    high = candle['h']
    low = candle['l']

    if is_candle_closed:
        print("\n\ncandle high at {}\n".format(high))
        print("\n\ncandle low at {}\n".format(low))
        print("\n\ncandle closed at {}\n".format(close))
        closes.append(float(close))
        highs.append(float(high))
        lows.append(float(low))
            

        if len(closes) > RSI_PERIOD:
            # np_closes = numpy.array(closes) <- this line was originally here instead of if-statement above
            np_highs = numpy.array(highs)
            np_lows = numpy.array(lows)
            np_closes = numpy.array(closes)
            stochk, stochd = talib.STOCHF(np_highs, np_lows, np_closes)
            print('All Stochastics values so far: ')
            print(stochk, stochd, '\n')
            last_stochk = stochk[-1]
            last_stochd = stochd[-1]
            rsi = talib.RSI(np_closes)
            print('All RSIs so far:')
            print(rsi, '\n')
            last_rsi = rsi[-1]
            print('The current Stochastics Values are {} and {}\n'.format(last_stochk, last_stochd))
            print('The current RSI is {}\n'.format(last_rsi))
            roc_rsi = roc(rsi[-1],last_rsi)
            print(roc_rsi)
            
            #if max(stochk[-3:]) > OVERBOUGHT_THRESHOLD and max(stochd[-3:]) > OVERBOUGHT_THRESHOLD:
            if last_stochd > OVERBOUGHT_THRESHOLD and last_stochk > OVERBOUGHT_THRESHOLD:
                print('\nStochastics are OVERBOUGHT\n')
                is_over = True
                is_under = False
                underboughts.clear()
                overboughts.append(last_stochd + last_stochk)
                #if last_stochd + last_stochk >= max(overboughts):
                    #newmax = last_rsi
                    #new_stochd_max = last_stochd
                    #new_stochk_max = last_stochk
            elif last_stochd < OVERSOLD_THRESHOLD and last_stochk < OVERSOLD_THRESHOLD:
                print('\nStochastics are UNDERBOUGHT\n')
                is_under = True
                is_over = False
                underboughts.append(last_stochd + last_stochk)
                overboughts.clear()
                if last_stochd + last_stochk <= min(underboughts):
                    if( last_rsi < 30):
                        new_rsi_min = last_rsi
                    new_stochd_min = last_stochd
                    new_stochk_min = last_stochk
            
            if is_under and last_rsi < 35:
                roc_rsi_when_under = roc(new_rsi_min, last_rsi)
                roc_stochd_when_under = roc(new_stochd_min, last_stochd)
                roc_stochk_when_under = roc(new_stochk_min, last_stochk)
            #elif is_over:
                #roc_rsi_when_over = roc(newmax, last_rsi)
                #roc_stochd_when_over = roc(new_stochd_max, last_stochd)
               # roc_stochk_when_over = roc(new_stochk_max, last_stochk)
            
                                                                            #Insert STOP-LOSS in parenthesis BELOW               here
            if (is_over and last_rsi < RSI_INDICATION and rsi_rocs[-2] > rsi_rocs[-1] and rsi_rocs[-3] > rsi_rocs[-1]) or ('Insert Stop-Loss'):
                #Statement above needs major wo                                            rk !!
                if in_position:
                    print('\nStochastics are Over-Bought AND RSI momentum is DOWNWARD-- SELL SELL SELL\n')
                    #Put Binance Order Logic Here
                    order_succeeded = order(SIDE_SELL, TRADE_QUANTITY, TRADE_SYMBOL)
                    if order_succeeded:
                        in_position = False
                        rsi_rocs_bought.clear()
                else:
                    print("\nStochastics are Over-Bought, but you don't own any!  Nothing to do!\n")
            else:
                print('But Market is not in a DownTrend -- WAIT TO SELL')
            
            # Following code incase if-statement doesn't work
            #b=0
            #for i in stoch[-2:]:
                #if i < OVERSOLD_THRESHOLD:
                #print('Sotchastic is OVERSOLD')
                #b+=1
                #break
            
            #if min(stochk[-3:]) < OVERSOLD_THRESHOLD and min(stochd[-3:]) < OVERSOLD_THRESHOLD:
            if is_under:
                if last_rsi < 35 and rsi_rocs[-1] > 4 and rsi_rocs[-3:-1] < 0:
                    if in_position:
                        print('\nStochastics are Over-Sold AND RSI momentum is UPWARD, but you already own it!  Nothing to do!\n')
                    else:
                        print('\nStochastics are Over-Sold AND RSI momentum is UPWARD-- BUY BUY BUY\n')
                        # Put Binance Order Logic Here
                        order_succeeded = order(SIDE_BUY, TRADE_QUANTITY, TRADE_SYMBOL)
                        if order_succeeded:
                            in_position = True
                else:
                    print('But Market is not in an UpTrend -- WAIT TO BUY')

ws = websocket.WebSocketApp(SOCKET, on_open=on_open,on_close=on_close, on_message=on_message)
ws.run_forever()











