#!/usr/bin/env python

import sys
import signal
import logging
import zlib
import websocket
import json
import time
from exchange import Exchange

class Okex(Exchange):
    def __init__(self):
            Exchange.__init__(self)
        
    def fresh_ticker(self, deJson):
        _channel = deJson[0]['channel']
        data = deJson[0]['data']
        _buy = data['buy']
        _sell = data['sell']
        logging.debug('channel:%s\tbuy:%-10s\tsell:%-10s' % (_channel, _buy, _sell))

    def fresh_depth(self, deJson, base_coin, trans_coin):
        _channel = deJson[0]['channel']
        data = deJson[0]['data']
        self._update_depth(base_coin, trans_coin, data['bids'], data['asks'])
        #logging.debug(data)

    def on_message(self, ws, msg):
        decompress = zlib.decompressobj(
                -zlib.MAX_WBITS
        )
        inflated = decompress.decompress(msg)
        inflated += decompress.flush()
        deJson = json.loads(inflated.decode('utf-8'))
        channel = deJson[0]['channel'];
        if channel == 'ok_sub_spot_eth_usdt_ticker':
            self.fresh_ticker(deJson)
        elif channel == 'ok_sub_spot_eth_usdt_depth_5':
            self.fresh_depth(deJson, 'usdt', 'eth')
        elif channel == 'ok_sub_spot_eth_btc_depth_5':
            self.fresh_depth(deJson, 'btc', 'eth')
        elif channel == 'ok_sub_spot_btc_usdt_depth_5':
            self.fresh_depth(deJson, 'usdt', 'btc')

    def on_error(self, ws, error):
        logging.error(error)

    def on_close(self, ws):
        logging.debug("okex:#### closed ###")

    def on_open(self, ws):
        logging.debug('okex:### opening ###')
        #ws.send("{'event':'addChannel','channel':'ok_sub_spot_eth_usdt_ticker','binary':'1'}")
        ws.send("{'event':'addChannel','channel':'ok_sub_spot_eth_usdt_depth_5','binary':'1'}")
        ws.send("{'event':'addChannel','channel':'ok_sub_spot_eth_btc_depth_5','binary':'1'}")
        ws.send("{'event':'addChannel','channel':'ok_sub_spot_btc_usdt_depth_5','binary':'1'}")

    def connect(self):
        websocket.enableTrace(False)
        self.ws = websocket.WebSocketApp("wss://real.okex.com:10441/websocket",
                                    on_message = self.on_message,
                                    on_error = self.on_error,
                                    on_close = self.on_close)
        self.ws.on_open = self.on_open
        self.ws.run_forever()

    def close(self):
        self.ws.close()


def sigint_handler(signum,frame):
    logging.debug("okex:exit")
    sys.exit()


if __name__ == "__main__":
    signal.signal(signal.SIGINT, sigint_handler)
    logging.basicConfig()
    okex = Okex()
    okex.connect()
