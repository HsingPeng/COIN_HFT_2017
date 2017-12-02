#!/usr/bin/env python

from exchange import Exchange

class FakeExchange(Exchange):

    def __init__(self):
        Exchange.__init__(self)

    def connect(self):
        pass

    def close(self):
        pass

    def update_depth(self, base_coin, trans_coin, bids_list, asks_list):
        self._update_depth(base_coin, trans_coin, bids_list, asks_list)

if __name__ == "__main__":
    exchange = FakeExchange()
    data = {'bids': [['422.41', '4.77'], ['422.4', '26.53'], ['422.39', '0.01'], ['422.37', '0.01'], ['422.19', '0.8862']], 'asks': [['423.99', '4.511'], ['423.98', '12.458'], ['423.45', '0.97500163'], ['423.43', '4.31'], ['423.33', '0.107']], 'timestamp': 1512045796664}
    exchange.update_depth('usdt', 'eth', data['bids'], data['asks'])
    exchange.get_depth('usdt', 'eth', 'asks')
