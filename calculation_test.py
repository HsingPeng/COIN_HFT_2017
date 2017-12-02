#!/usr/bin/env python

from exchange import Exchange
from calculation import Calculation

class FakeExchange(Exchange):

    def __init__(self):
        Exchange.__init__(self)

    def connect(self):
        pass

    def close(self):
        pass

    def update_depth(self, base_coin, trans_coin, bids_list, asks_list):
        self._update_depth(base_coin, trans_coin, bids_list, asks_list);

if __name__ == "__main__":
    exchange = FakeExchange()
    data = {'bids': [[u'429.76', u'7.871'], [u'429.36', u'0.914'], [u'429.27', u'0.0232954'], [u'429.1', u'0.15998'], [u'429.07', u'0.12']], 'asks': [[u'430.14', u'9.05598791'], [u'430', u'1.4985'], [u'429.99', u'5.6'], [u'429.8', u'7.557'], [u'429.77', u'5.149']]}
    exchange.update_depth('usdt', 'eth', data['bids'], data['asks'])
    data = {'bids': [[u'9901.23', u'0.00002804'], [u'9881.99', u'0.73'], [u'9881.96', u'0.97'], [u'9871.97', u'0.57'], [u'9849.99', u'0.00131326']], 'asks': [[u'9903.86', u'0.01'], [u'9903.24', u'0.002'], [u'9901.48', u'0.00264327'], [u'9901.25', u'0.68'], [u'9901.24', u'1.61']]}
    exchange.update_depth('usdt', 'btc', data['bids'], data['asks'])
    data = {'bids': [[u'0.04355987', u'35.4606005'], [u'0.04355985', u'78.295'], [u'0.04355982', u'0.3'], [u'0.04354018', u'0.6'], [u'0.04353952', u'2.6']], 'asks': [[u'0.04358887', u'0.3'], [u'0.04358873', u'0.3'], [u'0.04358836', u'0.3'], [u'0.04355993', u'0.029955'], [u'0.04355988', u'10.52']]}
    exchange.update_depth('btc', 'eth', data['bids'], data['asks'])
    #print(exchange.get_depth_dict())
    cal = Calculation()
    cal.add_three_trade('btc', 'eth')
    profit_list = cal.cal(exchange)
    print(profit_list)
