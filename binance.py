#!/usr/bin/env python3

import sys
import signal
import logging
import websocket
import json
import time
import hashlib
import threading
import ssl
import hmac
import hashlib
import requests
from multiprocessing import Queue
from exchange import Exchange
from urllib.parse import urlencode
from config import Config

class Binance(Exchange):

    __ENDPOINT = "https://www.binance.com"

    __BUY = "BUY"
    __SELL = "SELL"

    __LIMIT = "LIMIT"
    __MARKET = "MARKET"

    __GTC = "GTC"
    __IOC = "IOC"

    def __init__(self, api_key, secret_key):
        Exchange.__init__(self)
        self.__api_key = api_key
        self.__secret_key = secret_key
        self.__channels_dict = {}
        self.spot_balance_dict = {}
        self.queue = Queue()
        
    def __fresh_depth(self, data, coins):
        if coins.endswith('usdt'):
            base_coin = 'usdt'
            trans_coin = coins[0:len(coins) - 4]
        elif coins.endswith('btc'):
            base_coin = 'btc'
            trans_coin = coins[0:len(coins) - 3]
        elif coins.endswith('eth'):
            base_coin = 'eth'
            trans_coin = coins[0:len(coins) - 3]
        elif coins.endswith('bnb'):
            base_coin = 'bnb'
            trans_coin = coins[0:len(coins) - 3]
        else:
            return
        self._update_depth(base_coin, trans_coin, data['bids'], data['asks'])
        #logging.debug(str(self.get_depth_dict()))

    def __on_message(self, ws, msg):
        queue = self.queue
        # read the msg
        deJson = json.loads(msg)
        #logging.debug('msg:' + str(deJson))
        stream = deJson.get('stream')
        e = deJson.get('e')
        if stream != None and stream.endswith('depth5'):
            self.__fresh_depth(deJson.get('data'), stream.split('@')[0])
            return
        elif e != None and e == 'outboundAccountInfo':
            msg = {'type': 'balance'}
            queue.put(msg)
            B = deJson.get('B')
            for balance in B:
                self.spot_balance_dict[balance['a'].lower()] = float(balance['f'])
            return
        elif e != None and e == 'executionReport':
            logging.debug('binance:__on_message:executionReport')
            return
        logging.debug('binance:__on_message:unhandle:' + str(deJson))

    def __on_error(self, ws, error):
        logging.error(error)
        msg = {'type': 'error', 'msg': str(error), 'code': -101}

    def __on_close(self, ws):
        logging.debug("binance:#### closed ###")

    def __on_open(self, ws):
        logging.debug('binance:### opening ###')

    def __send(self, msg):
        self.ws.send(msg)
        logging.debug('binance:__send:msg:' + str(msg))

    def connect(self):
        websocket.enableTrace(False)
        websocket.setdefaulttimeout=1
        url = 'wss://stream.binance.com:9443/stream?streams='
        for (channel, values) in self.__channels_dict.items():
            url = url + channel + '/'
        url = url[:-1]
        self.ws = websocket.WebSocketApp(url,
                                    on_message = self.__on_message,
                                    on_error = self.__on_error,
                                    on_close = self.__on_close,
                                    on_open = self.__on_open)
        self.ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})

    def connect_userdata(self):
        response = self.__create_a_listenkey()
        listen_key = response.get('listenKey')
        if listen_key == None:
            logging.debug('binance:__create_a_listenkey error:%s' % str(response))
            return
        self.__listen_key = listen_key
        websocket.enableTrace(False)
        url = 'wss://stream.binance.com:9443/ws/' + listen_key
        self.ws_userdata = websocket.WebSocketApp(url,
                                    on_message = self.__on_message,
                                    on_error = self.__on_error,
                                    on_close = self.__on_close)
        self.ws_userdata.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})

    def close(self):
        self.ws.close()
        self.ws_userdata.close()

    def add_coins(self, coins_list):
        if coins_list == None:
            return
        self.__channels_dict['ethusdt@depth5'] = ('usdt', 'eth')
        self.__channels_dict['btcusdt@depth5'] = ('usdt', 'btc')
        self.__channels_dict['bchusdt@depth5'] = ('usdt', 'bch')
        self.__channels_dict['bnbusdt@depth5'] = ('usdt', 'bnb')
        for coins in coins_list:
            if coins[0] == 'btc':
                self.__channels_dict[coins[1]+'btc'+'@depth5'] = ('btc', coins[1])
                self.__channels_dict[coins[1]+'usdt'+'@depth5'] = ('usdt', coins[1])
            elif coins[0] == 'eth':
                self.__channels_dict[coins[1]+'eth'+'@depth5'] = ('eth', coins[1])
                self.__channels_dict[coins[1]+'usdt'+'@depth5'] = ('usdt', coins[1])
            elif coins[0] == 'bch':
                self.__channels_dict[coins[1]+'bch'+'@depth5'] = ('bch', coins[1])
                self.__channels_dict[coins[1]+'usdt'+'@depth5'] = ('usdt', coins[1])
            elif coins[0] == 'bnb':
                self.__channels_dict[coins[1]+'bnb'+'@depth5'] = ('bnb', coins[1])
                self.__channels_dict[coins[1]+'usdt'+'@depth5'] = ('usdt', coins[1])

    def get_available_coins(self):
        return self.__balances()

    def create_spot_order(self, base_coin, trans_coin, buy_or_sell, price='', amount=''):
        symbol = trans_coin + base_coin
        if buy_or_sell == 'sell_market':
            side = self.__SELL
            orderType = self.__MARKET
            quantity = amount
        elif buy_or_sell == 'buy_market':
            side = self.__BUY
            orderType = self.__MARKET
            quantity = amount
        else:
            return
        if base_coin == 'btc':
            if trans_coin == 'eth':
                quantity = int(quantity * 1000) / 1000
            elif trans_coin == 'neo':
                quantity = int(quantity * 100) / 100
            elif trans_coin == 'bnb':
                quantity = int(quantity * 1) / 1
            elif trans_coin == 'ltc':
                quantity = int(quantity * 100) / 100
            elif trans_coin == 'bcc':
                quantity = int(quantity * 1000) / 1000
            else:
                quantity = int(quantity * 1000) / 1000
        elif base_coin == 'eth':
            if trans_coin == 'neo':
                quantity = int(quantity * 100) / 100
            elif trans_coin == 'bnb':
                quantity = int(quantity * 1) / 1
            elif trans_coin == 'bcc':
                quantity = int(quantity * 1000) / 1000
            elif trans_coin == 'ltc':
                quantity = int(quantity * 1000) / 1000
        elif trans_coin == 'btc':
            quantity = int(quantity * 1000) / 1000
        elif trans_coin == 'neo':
            quantity = int(quantity * 1000) / 1000
        elif trans_coin == 'bnb':
            quantity = int(quantity * 1) / 1
        elif trans_coin == 'bcc' or trans_coin == 'ltc' or trans_coin == 'eth':
            quantity = int(quantity * 1000) / 1000
        else:
            quantity = int(quantity * 1000) / 1000
        return self.__order(symbol.upper(), side, quantity, orderType=orderType)

    def heartbeat(self):
        self.__request('PUT', '/api/v1/userDataStream', {'listenKey':self.__listen_key})

    def __balances(self):
        """Get current balances for all symbols."""
        data = self.__signedRequest("GET", "/api/v3/account", {})
        if data.get('balances') == None:
            logging.error('Binance:get balances error:%s' % str(data))
            return
        for d in data['balances']:
            self.spot_balance_dict[d['asset'].lower()] = float(d['free'])

    def __order(self, symbol, side, quantity, price=0, orderType=__LIMIT, timeInForce=__GTC,
              test=False, **kwargs):
        """Send in a new order.
        Args:
            symbol (str)
            side (str): BUY or SELL.
            quantity (float, str or decimal)
            price (float, str or decimal)
            orderType (str, optional): LIMIT or MARKET.
            timeInForce (str, optional): GTC or IOC.
            test (bool, optional): Creates and validates a new order but does not
                send it into the matching engine. Returns an empty dict if
                successful.
            newClientOrderId (str, optional): A unique id for the order.
                Automatically generated if not sent.
            stopPrice (float, str or decimal, optional): Used with stop orders.
            icebergQty (float, str or decimal, optional): Used with iceberg orders.
        """
        params = {
            "symbol": symbol,
            "side": self.__formatNumber(side),
            "type": orderType,
            #"timeInForce": timeInForce,
            "quantity": quantity,
            #"price": self.__formatNumber(price),
        }
        params.update(kwargs)
        path = "/api/v3/order/test" if test else "/api/v3/order"
        data = self.__signedRequest("POST", path, params)
        return data

    def __create_a_listenkey(self):
        return self.__request('POST', '/api/v1/userDataStream')

    def __request(self, method, path, params=None):
        resp = requests.request(method, self.__ENDPOINT + path, params=params,
                                    headers={"X-MBX-APIKEY": self.__api_key})
        return resp.json()

    def __signedRequest(self, method, path, params):
        query = urlencode(sorted(params.items()))
        query += "&timestamp={}".format(int(time.time() * 1000))
        secret = bytes(self.__secret_key.encode("utf-8"))
        signature = hmac.new(secret, query.encode("utf-8"),
                             hashlib.sha256).hexdigest()
        query += "&signature={}".format(signature)
        resp = requests.request(method,
                                self.__ENDPOINT + path + "?" + query,
                                headers={"X-MBX-APIKEY": self.__api_key})
        data = resp.json()
        if "msg" in data:
            logging.error(data['msg'])
            return None
        return data

    def __formatNumber(self, x):
        if isinstance(x, float):
            return "{:.8f}".format(x)
        else:
            return str(x)

def binance_sigint_handler(signum,frame):
    logging.info("binance:exit")
    sys.exit()

if __name__ == "__main__":
    signal.signal(signal.SIGINT, binance_sigint_handler)
    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s')
    __ACCESS_KEY = Config.binance_api_key
    __SECRET_KEY = Config.binance_secret_key
    binance = Binance(__ACCESS_KEY, __SECRET_KEY)
    binance.add_coins([('eth', 'btc'), ('btc', 'eth')])
    #binance.connect()
    logging.debug('start')
    #binance.get_available_coins()
    #print(str(binance.spot_balance_dict))
    #data = binance.create_spot_order('usdt', 'bnb', 'buy_market', price=1)
    #logging.debug(str(data))
    #print(str(binance.create_a_listenkey()))
    binance.connect_userdata()
