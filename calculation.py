import logging
import bisect

class Calculation(object):

    def __init__(self):
        self.__three_trade_list = []

    def add_three_trade(self, first_coin, second_coin):
        self.__three_trade_list.append((first_coin, second_coin));

    def get_three_trade_list(self):
        return self.__three_trade_list

    def cal(self, exchange):
        profit_list = []
        for coins in self.__three_trade_list:
            first_coin = coins[0]
            second_coin = coins[1]
            if first_coin == 'eth' and second_coin == 'btc':
                second_base_coin = 'btc'
                second_trans_coin = 'eth'
                second_bids_or_asks = 'bids'
                second_base_position = 2
            elif first_coin == 'eth':
                second_base_coin = 'eth'
                second_trans_coin = second_coin
                second_bids_or_asks = 'asks'
                second_base_position = 1
            elif first_coin == 'btc':
                second_base_coin = 'btc'
                second_trans_coin = second_coin
                second_bids_or_asks = 'asks'
                second_base_position = 1
            elif second_coin == 'eth':
                second_base_coin = 'eth'
                second_trans_coin = first_coin
                second_bids_or_asks = 'bids'
                second_base_position = 2
            elif second_coin == 'btc':
                second_base_coin = 'btc'
                second_trans_coin = first_coin
                second_bids_or_asks = 'bids'
                second_base_position = 2
            else:
                logging.error('calculation:second_base_coin failed:first_coin='
                    +first_coin + ' second_coin=' + second_coin)
                continue
            # next get the depth
            first_depth_list = exchange.get_depth('usdt', first_coin, 'asks')
            second_depth_list = exchange.get_depth(second_base_coin
                                    , second_trans_coin, second_bids_or_asks)
            third_depth_list = exchange.get_depth('usdt', second_coin, 'bids')
            first_depth = first_depth_list[0]
            second_depth = second_depth_list[0]
            third_depth = third_depth_list[0]
            first_depth_price = float(first_depth[0])
            first_depth_amount = float(first_depth[1])
            second_depth_price = float(second_depth[0])
            second_depth_amount = float(second_depth[1])
            third_depth_price = float(third_depth[0])
            third_depth_amount = float(third_depth[1])
            # assume initial fund is 100 usdt
            initial_usdt = 100.0
            after_first_coin_amount = initial_usdt / first_depth_price
            if second_base_position == 1:
                after_second_coin_amount = after_first_coin_amount / second_depth_price
            else:
                after_second_coin_amount = after_first_coin_amount * second_depth_price
            after_third_coin_amount = after_second_coin_amount * third_depth_price
            profit = after_third_coin_amount - initial_usdt
            # calculate whether the depth amount is enough
            first_depth_usdt = first_depth_price * first_depth_amount
            if second_base_position == 1:
                second_depth_usdt = second_depth_price * second_depth_amount * first_depth_price
            else:
                second_depth_usdt = second_depth_price * second_depth_amount * third_depth_price
            third_depth_usdt = third_depth_price * third_depth_amount
            if first_depth_usdt > second_depth_usdt:
                min_usdt = second_depth_usdt
            else:
                min_usdt = first_depth_usdt
            if min_usdt > third_depth_usdt:
                min_usdt = third_depth_usdt
            # finish the calculation
            '''logging.debug('calculation:first_coin=' + first_coin
                            + '\tsecond_coin=' + second_coin
                            + '\tmin_usdt=' + str(min_usdt)
                            + '\tprofit=' + str(profit))'''
            if profit > 1 and min_usdt >= 20:
                logging.info('calculation:first_coin=' + first_coin
                            + '\tsecond_coin=' + second_coin
                            + '\tmin_usdt=' + str(min_usdt)
                            + '\tprofit=' + str(profit) + ' '
                            + str(first_depth_price) + ' '
                            + str(second_depth_price) + ' '
                            + str(third_depth_price))
                bisect.insort(profit_list, (profit, min_usdt,
                                            first_coin, second_coin, second_base_position,
                                            first_depth_price,
                                            second_depth_price,
                                            third_depth_price))
        profit_list.reverse()
        return profit_list
