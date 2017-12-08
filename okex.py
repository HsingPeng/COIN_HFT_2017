#!/usr/bin/env python

import sys
import signal
import logging
import zlib
import websocket
import json
import time
import hashlib
import threading
from exchange import Exchange

class Okex(Exchange):
    def __init__(self, api_key, secret_key):
        Exchange.__init__(self)
        self.__api_key = api_key
        self.__secret_key = secret_key
        self.__channels_dict = {}
        self.spot_balance_dict = {}
        self.order_cond = threading.Condition()
        # 0    no order;
        # 1    first order sent;
        # 10   first order created;
        # 100  first order finished;
        # 2    second order sent;
        # 20   second order created;
        # 200  second order finished;
        # 3    third order sent;
        # 30   third order created;
        # 300  third order finished;
        # -1   error status
        self.order_status = 0
        
    def __fresh_ticker(self, one_msg):
        _channel = one_msg['channel']
        data = one_msg['data']
        _buy = data['buy']
        _sell = data['sell']
        logging.debug('channel:%s\tbuy:%-10s\tsell:%-10s' % (_channel, _buy, _sell))

    def __fresh_depth(self, one_msg, base_coin, trans_coin):
        _channel = one_msg['channel']
        data = one_msg['data']
        self._update_depth(base_coin, trans_coin, data['bids'], data['asks'])
        #logging.debug(data)

    def __fresh_spot_balance(self, one_msg):
        logging.debug('__fresh_spot_balance:' + str(one_msg))
        channel = one_msg['channel']
        data = one_msg['data']
        free = data.get('info').get('funds').get('free')
        for k,v in free.items():
            self.spot_balance_dict[k] = float(v)

    def __handle_order(self, one_msg):
        logging.debug('__handle_order:' + str(one_msg))
        order_cond = self.order_cond
        order_cond.acquire()
        channel = one_msg.get('channel')
        _type = one_msg.get('type')
        if channel == 'ok_spot_order':
            if one_msg.get('data').get('result') == True:
                if self.order_status > 0 and self.order_status < 10:
                    self.order_status *= 10
                    order_cond.notifyAll()
            else:
                self.order_status = -one_msg.get('data').get('error_code')
                order_cond.notifyAll()
        elif _type == 'balance':
            quote = one_msg.get('quote')
            base = one_msg.get('base')
            currency_id = one_msg.get('data').get('currencyId')
            available = float(one_msg.get('data').get('available'))
            if quote == 'usdt':
                base_id = 7
            elif quote == 'btc':
                base_id = 0
            elif quote == 'eth':
                base_id = 2
            else:
                logging.error('base=' + str(base) + ':' + str(one_msg))
                return
            if base_id == currency_id:
                self.spot_balance_dict[quote] = available
            else:
                self.spot_balance_dict[base] = available
            if self.order_status >= 100 and self.order_status % 10 == 0:
                self.order_status += 1
            elif self.order_status >= 100:
                self.order_status = self.order_status / 10 * 10
                order_cond.notifyAll()
            logging.debug('currency_id=' + str(currency_id) + ' order_status=' + str(self.order_status))
        elif _type == 'order':
            status = one_msg.get('data').get('status')
            if self.order_status <= 0:
                return
            elif status == 0 and self.order_status < 10:
                self.order_status *= 10
                order_cond.notifyAll()
            elif status == 2 and self.order_status < 100: 
                self.order_status *= 10
            logging.debug('status=' + str(status))
        order_cond.release()
        time.sleep(0)

    def __on_message(self, ws, msg):
        # decode the msg
        decode_error = False
        try:
            decompress = zlib.decompressobj(-zlib.MAX_WBITS)
            inflated = decompress.decompress(msg)
            inflated += decompress.flush()
            deJson = json.loads(inflated.decode('utf-8'))
        except Exception, e:
            decode_error = True
        if decode_error == True:
            try:
                deJson = json.loads(msg)
                decode_error = False
            except Exception, e:
                pass
        if decode_error == True:
            logging.error('okex:__on_message:decode meg failed:' + str(msg))
            return
        # read the msg
        #logging.info('msg:' + str(deJson))
        if isinstance(deJson, dict):
            result = deJson['result']
            logging.error('okex:__on_message:last sent meg error:' + str(msg))
            return
        for one_msg in deJson:
            # handle channel
            channel = one_msg.get('channel')
            if channel != None:
                channel_list = self.__channels_dict.get(channel)
                if channel_list != None:
                    self.__fresh_depth(one_msg, channel_list[0], channel_list[1])
                elif channel == 'ok_sub_spot_eth_usdt_ticker':
                    self.__fresh_ticker(one_msg)
                elif channel == 'ok_spot_userinfo':
                    self.__fresh_spot_balance(one_msg)
                elif channel == 'ok_spot_order':
                    self.__handle_order(one_msg)
                else:
                    logging.debug('okex:__on_message:unhandle channel:' + str(one_msg))
                return
            # handle type
            _type = one_msg.get('type')
            if _type != None:
                if _type == 'balance':
                    self.__handle_order(one_msg)
                elif _type == 'order':
                    self.__handle_order(one_msg)
                return
        logging.debug('okex:__on_message:unhandle:' + str(deJson))

    def __on_error(self, ws, error):
        logging.error(error)

    def __on_close(self, ws):
        logging.debug("okex:#### closed ###")

    def __on_open(self, ws):
        logging.debug('okex:### opening ###')
        self.login()
        self.add_channel_userinfo()
        self.add_channel_userinfo()
        for channel,values in self.__channels_dict.items():
            add_one_channel = "{'event':'addChannel','channel':'" + channel + "','binary':'1'}"
            self.__send(add_one_channel)
            logging.debug("okex:add_one_channel:" + add_one_channel)
        #self.__send("{'event':'addChannel','channel':'ok_sub_spot_btc_usdt_depth_5','binary':'1'}")

    def __send(self, msg):
        self.ws.send(msg)
        logging.debug('okex:__send:msg:' + str(msg))

    def connect(self):
        websocket.enableTrace(False)
        self.ws = websocket.WebSocketApp("wss://real.okex.com:10441/websocket",
                                    on_message = self.__on_message,
                                    on_error = self.__on_error,
                                    on_close = self.__on_close)
        self.ws.on_open = self.__on_open
        self.ws.run_forever()

    def close(self):
        self.ws.close()

    def add_coins(self, coins_list):
        self.__channels_dict['ok_sub_spot_eth_usdt_depth_5'] = ('usdt', 'eth')
        self.__channels_dict['ok_sub_spot_btc_usdt_depth_5'] = ('usdt', 'btc')
        for coins in coins_list:
            if coins[0] == 'eth' and coins[1] == 'btc':
                self.__channels_dict['ok_sub_spot_eth_btc_depth_5'] = ('btc', 'eth')
            elif coins[0] == 'eth':
                self.__channels_dict['ok_sub_spot_'+coins[1]+'_eth'+'_depth_5'] = ('eth', coins[1])
                self.__channels_dict['ok_sub_spot_'+coins[1]+'_usdt'+'_depth_5'] = ('usdt', coins[1])
            elif coins[0] == 'btc':
                self.__channels_dict['ok_sub_spot_'+coins[1]+'_btc'+'_depth_5'] = ('btc', coins[1])
                self.__channels_dict['ok_sub_spot_'+coins[1]+'_usdt'+'_depth_5'] = ('usdt', coins[1])

    def login(self):
        api_key = self.__api_key
        params={'api_key':api_key}
        sign = self.__build_my_sign(params)
        finalStr = '{"event":"login","parameters":{"api_key":"' + api_key\
                        + '","sign":"' + sign + '"},"binary":"1"}'
        self.__send(finalStr) 

    def add_channel_userinfo(self):
        api_key = self.__api_key
        params={'api_key':api_key}
        sign = self.__build_my_sign(params)
        finalStr = '{"event":"addChannel","channel":"ok_spot_userinfo","parameters":{"api_key":"'\
                        + api_key + '","sign":"' + sign + '"},"binary":"1"}'
        self.__send(finalStr) 

    def create_spot_order(self, base_coin, trans_coin, buy_or_sell, price='', amount=''):
        api_key = self.__api_key
        symbol = trans_coin+'_'+base_coin
        params={
            'api_key':api_key,
            'symbol':symbol,
            'type':buy_or_sell
         }
        if price:
            params['price'] = price
        if amount:
            params['amount'] = amount
        sign = self.__build_my_sign(params)
        finalStr = "{'event':'addChannel','channel':'ok_spot_order','parameters':{'api_key':'"+api_key\
                        +"','sign':'"+sign+"','symbol':'"+symbol+"','type':'"+buy_or_sell+"'"
        if price:
            finalStr += ",'price':'"+str(price)+"'"
        if amount:
            finalStr += ",'amount':'"+str(amount)+"'"
        finalStr+="},'binary':'1'}"
        self.__send(finalStr)

    def __build_my_sign(self, params):
        secretKey = self.__secret_key
        sign = ''
        for key in sorted(params.keys()):
            sign += key + '=' + str(params[key]) +'&'
        return  hashlib.md5((sign+'secret_key='+secretKey).encode("utf-8")).hexdigest().upper()

def okex_sigint_handler(signum,frame):
    logging.info("okex:exit")
    sys.exit()


if __name__ == "__main__":
    signal.signal(signal.SIGINT, okex_sigint_handler)
    logging.basicConfig()
    okex = Okex()
    okex.connect()
