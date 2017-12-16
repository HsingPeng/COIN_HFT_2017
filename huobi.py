#!/usr/bin/env python3
# encoding: utf-8
import websocket
import signal
import sys
import logging
import json
import gzip
import base64
import datetime
import hashlib
import hmac
import json
import urllib
import urllib.parse
import urllib.request
import requests
from io import BytesIO
from exchange import Exchange

class Huobi(Exchange):
    __TRADE_URL = 'https://api.huobi.pro'
    
    def __init__(self, api_key, secret_key):
        Exchange.__init__(self)
        self.__access_key = api_key
        self.__secret_key = secret_key
        self.__channels_dict = { }
        self.spot_balance_dict = { }
    
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
        else:
            return
        self._update_depth(base_coin, trans_coin, data['tick']['bids'], data['tick']['asks'])

    def __on_message(self, ws, event):
        buf = BytesIO(event)
        f = gzip.GzipFile(fileobj = buf)
        data = f.read().decode('utf8')
        data = json.loads(data)
        if 'ping' in data:
            pong = {
                'pong': data['ping'] }
            pong = json.dumps(pong)
            logging.debug(pong)
            ws.send(pong)
            return
        if data.get('status') != None and data.get('status') != 'ok':
            logging.debug('__on_message error:' + str(data))
            return
        ch = data.get('ch')
        if ch != None:
            channel = ch.split('.')
            if channel[2] == 'depth':
                self.__fresh_depth(data, channel[1])
            else:
                logging.debug('__unhandle_message:' + str(data))
        else:
            logging.debug('__unhandle_message:' + str(data))

    def __on_error(self, ws, error):
        logging.error(error)

    def __on_close(self, ws):
        logging.debug('huobi:### closed ###')

    def __on_open(self, ws):
        logging.debug('huobi:### opening ###')
        self.get_accounts()
        self.get_available_coins()
        for (channel, values) in self.__channels_dict.items():
            add_one_channel = '{"sub": "' + channel + '", "id": "' + channel + '"}'
            ws.send(add_one_channel)
            logging.debug('huobi:add_one_channel:' + add_one_channel)

    def connect(self):
        websocket.enableTrace(False)
        self.ws = websocket.WebSocketApp('wss://api.huobi.pro/ws',
                                            on_message = self.__on_message,
                                            on_error = self.__on_error,
                                            on_close = self.__on_close,
                                            on_open = self.__on_open)
        self.ws.run_forever()

    def send(self, msg):
        self.ws.send(msg)

    def close(self):
        self.ws.close()

    def add_coins(self, coins_list):
        self.__channels_dict['market.ethusdt.depth.step1'] = ('usdt', 'eth')
        self.__channels_dict['market.btcusdt.depth.step1'] = ('usdt', 'btc')
        for coins in coins_list:
            if coins[0] == 'eth' and coins[1] == 'btc':
                self.__channels_dict['market.ethbtc.depth.step1'] = ('btc', 'eth')
                continue
            if coins[0] == 'eth':
                self.__channels_dict['market.' + coins[1] + 'eth' + '.depth.step1'] = ('eth', coins[1])
                self.__channels_dict['market.' + coins[1] + 'usdt' + '.depth.step1'] = ('usdt', coins[1])
                continue
            if coins[0] == 'btc':
                self.__channels_dict['market.' + coins[1] + 'btc' + '.depth.step1'] = ('btc', coins[1])
                self.__channels_dict['market.' + coins[1] + 'usdt' + '.depth.step1'] = ('usdt', coins[1])
                continue

    def create_spot_order(self, base_coin, trans_coin, buy_or_sell, price = '', amount = ''):
        symbol = trans_coin + base_coin
        source = 'api'
        if buy_or_sell == 'buy_market':
            _type = 'buy-market'
        elif buy_or_sell == 'sell_market':
            _type = 'sell-market'
            if trans_coin == 'xrp':
                amount = int(amount)
            elif trans_coin == 'eos' or trans_coin == 'omg' or trans_coin == 'qtum':
                amount = int(amount * 100) / 100
        else:
            return None
        amount = int(amount * 10000) / 10000
        return self.__orders(str(amount), source, symbol, _type)

    def heartbeat(self):
        pass

    def get_available_coins(self):
        self.__get_balance()

    def __http_get_request(self, url, params, add_to_headers = None):
        headers = {
            'Content-type': 'application/x-www-form-urlencoded',
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.71 Safari/537.36' }
        if add_to_headers:
            headers.update(add_to_headers)
        postdata = urllib.parse.urlencode(params)
        logging.debug('request get')
        logging.debug(url + postdata)
        try:
            response = requests.get(url, postdata, headers = headers, timeout = 5)
            logging.debug('response get')
            logging.debug(response)
            if response.status_code == 200:
                return response.json()
            return None
        except Exception:
            if 'response' in dir():
                logging.debug('httpGet failed, detail is:%s' % response.text)
            else:
                logging.debug('httpGet failed, detail is:%s' % e)
            return None

    def __http_post_request(self, url, params, add_to_headers = None):
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json' }
        if add_to_headers:
            headers.update(add_to_headers)
        postdata = json.dumps(params)
        logging.debug('request post')
        logging.debug(url + postdata) 
        try:
            response = requests.post(url, postdata, headers = headers, timeout = 10)
            if response.status_code == 200:
                return response.json()
            return None
        except:
            logging.debug('httpPost failed, detail is:%s' % response.text)
            return None

    def __api_key_get(self, params, request_path):
        method = 'GET'
        timestamp = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S')
        params.update({'AccessKeyId': self.__access_key,
                       'SignatureMethod': 'HmacSHA256',
                       'SignatureVersion': '2',
                       'Timestamp': timestamp})
        host_url = self.__TRADE_URL
        host_name = urllib.parse.urlparse(host_url).hostname
        host_name = host_name.lower()
        params['Signature'] = self.__createSign(params, method, host_name, request_path, self.__secret_key)
        logging.debug('sign\n' + params['Signature'])
        url = host_url + request_path
        return self.__http_get_request(url, params)

    def __api_key_post(self, params, request_path):
        method = 'POST'
        timestamp = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S')
        params_to_sign = {
            'AccessKeyId': self.__access_key,
            'SignatureMethod': 'HmacSHA256',
            'SignatureVersion': '2',
            'Timestamp': timestamp }
        host_url = self.__TRADE_URL
        host_name = urllib.parse.urlparse(host_url).hostname
        host_name = host_name.lower()
        params_to_sign['Signature'] = self.__createSign(params_to_sign, method, host_name, request_path, self.__secret_key)
        logging.debug('sign post\n' + params_to_sign['Signature'])
        url = host_url + request_path + '?' + urllib.parse.urlencode(params_to_sign)
        return self.__http_post_request(url, params)

    def __createSign(self, pParams, method, host_url, request_path, __secret_key):
        sorted_params = sorted(pParams.items(), key = (lambda d: d[0]), reverse = False)
        encode_params = urllib.parse.urlencode(sorted_params)
        payload = [
            method,
            host_url,
            request_path,
            encode_params]
        payload = '\n'.join(payload)
        payload = payload.encode(encoding = 'UTF8')
        __secret_key = __secret_key.encode(encoding = 'UTF8')
        logging.debug('createsign')
        logging.debug(payload)
        digest = hmac.new(__secret_key, payload, digestmod = hashlib.sha256).digest()
        signature = base64.b64encode(digest)
        signature = signature.decode()
        return signature

    def __get_balance(self):
        url = '/v1/account/accounts/{0}/balance'.format(self.__acct_id)
        params = {
            'account-id': self.__acct_id }
        data = self.__api_key_get(params, url)
        if data.get('status') != 'ok':
            logging.error('__get_balance error:' + str(data))
            return None
        balance_list = data.get('data').get('list')
        for balance in balance_list:
            if balance['type'] == 'trade':
                currency = balance['currency']
                available = balance['balance']
                self.spot_balance_dict[currency] = float(available)
                continue

    def __orders(self, amount, source, symbol, _type, price = 0):
        '''
        :param amount: 
        :param source: 
        :param symbol: 
        :param _type: 可选值 {buy-market：市价买, sell-market：市价卖, buy-limit：限价买, sell-limit：限价卖}
        :param price: 
        :return: 
        '''
        params = {
            'account-id': self.__acct_id,
            'amount': amount,
            'symbol': symbol,
            'type': _type,
            'source': source }
        if price:
            params['price'] = price
        url = '/v1/order/orders/place'
        return self.__api_key_post(params, url)

    def get_accounts(self):
        path = '/v1/account/accounts'
        params = { }
        data = self.__api_key_get(params, path)
        acct_id = data.get('data')[0]['id']
        self.__acct_id = str(acct_id)
        return self.__acct_id

def huobi_sigint_handler(signum, frame):
    logging.info('huobi:exit')
    sys.exit()

if __name__ == '__main__':
    signal.signal(signal.SIGINT, huobi_sigint_handler)
    logging.basicConfig(level = logging.DEBUG)
    __ACCESS_KEY = None
    __SECRET_KEY = None
    huobi = Huobi(__ACCESS_KEY, __SECRET_KEY)
    huobi.add_coins([('eth', 'btc'), ('btc', 'eth')])
    huobi.connect()
