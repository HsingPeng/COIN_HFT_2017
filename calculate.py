import logging

class Calculate(object):

    def __init__(self):
        self.__three_trade_list = []

    def add_three_trade(self, first_coin, second_coin):
        self.__three_trade_list.append((first_coin, second_coin));

    def get_three_trade_list(self):
        return self.__three_trade_list

    def cal(self, exchange):
        for coins in self.__three_trade_list:
            first_coin = coins[0]
            second_coin = coins[1]
            if first_coin == 'ETH' and second_coin == 'BTC':
                second_base_coin = 'BTC'
                second_trans_coin = 'ETH'
                second_bids_or_asks = 'bids'
            elif first_coin == 'ETH':
                second_base_coin = 'ETH'
                second_trans_coin = second_coin
                second_bids_or_asks = 'asks'
            elif first_coin == 'BTC':
                second_base_coin = 'BTC'
                second_trans_coin = second_coin
                second_bids_or_asks = 'asks'
            elif second_coin == 'ETH':
                second_base_coin = 'ETH':
                second_trans_coin = first_coin
                second_bids_or_asks = 'bids'
            elif second_coin == 'BTC':
                second_base_coin = 'BTC'
                second_trans_coin = first_coin
                second_bids_or_asks = 'bids'
            else:
                logging.error('second_base_coin failed:first_coin='
                    +first_coin + ' second_coin=' + second_coin)
                continue
            # next is the calculation
            first_depth_list = exchange.get_depth('usdt', first_coin, 'asks')
            second_depth_list = exchange.get_depth(second_base_coin
                                    , second_trans_coin, second_bids_or_asks)
            third_depth_list = exchange.get_depth('usdt', second_coin, 'bids')
            first_0_depth = first_depth_list[0]
            second_0_depth = second_depth_list[0]
            third_0_depth = third_depth_list[0]
