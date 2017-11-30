#!/usr/bin/env python3

import sys
import signal
import zlib
import websocket
import json
import time

class OKEX:
    def freshTicker(self, deJson):
        _channel = deJson[0]['channel']
        data = deJson[0]['data']
        _buy = data['buy']
        _sell = data['sell']
        print('channel:%s\tbuy:%-10s\tsell:%-10s' % (_channel, _buy, _sell))
        #print(data)
        # _high = data['high']
        # _last = data['last']
        # _low = data['low']
        # _open = data['open']
        # _close = data['close']
        # sys.stdout.write('\033[1A\033[K')
        # print('ETH:high=%-7s low=%-7s last=\033[;;34m%-7s\033[0m open=%-7s close=%-7s'
               # % (_high, _low, _last, _open, _close))

    def freshDepth(self, deJson):
        _channel = deJson[0]['channel']
        data = deJson[0]['data']
        print(data)

    def on_message(self, ws, msg):
        decompress = zlib.decompressobj(
                -zlib.MAX_WBITS  # see above
        )
        inflated = decompress.decompress(msg)
        inflated += decompress.flush()
        deJson = json.loads(inflated.decode('utf-8'))
        channel = deJson[0]['channel'];
        if channel == 'ok_sub_spot_eth_usdt_ticker':
            self.freshTicker(deJson)
        elif channel == 'ok_sub_spot_eth_usdt_depth_5':
            self.freshDepth(deJson)

    def on_error(self, ws, error):
        print(error)

    def on_close(self, ws):
        print("#### closed ###")

    def on_open(self, ws):
        ws.send("{'event':'addChannel','channel':'ok_sub_spot_eth_usdt_ticker','binary':'1'}")
        ws.send("{'event':'addChannel','channel':'ok_sub_spot_eth_usdt_depth_5','binary':'1'}")
        #ws.send("{'event':'addChannel','channel':'ok_sub_spot_eth_btc_ticker'}")
        #ws.send("{'event':'addChannel','channel':'ok_sub_spot_btc_usdt_ticker'}")
        print('### opening ###')

    def connect(self):
        websocket.enableTrace(False)
        self.ws = websocket.WebSocketApp("wss://real.okex.com:10441/websocket",
                                    on_message = self.on_message,
                                    on_error = self.on_error,
                                    on_close = self.on_close)
        self.ws.on_open = self.on_open
        self.ws.run_forever()


def sigint_handler(signum,frame):
    print("exit")
    sys.exit()


if __name__ == "__main__":
    signal.signal(signal.SIGINT, sigint_handler)
    okex = OKEX()
    okex.connect()
