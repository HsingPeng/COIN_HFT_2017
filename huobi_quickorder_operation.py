import logging
import threading
import time
from concurrent.futures import ThreadPoolExecutor

class HuobiQuickOrderOperateThread(threading.Thread):
    def __init__(self, exchange, calculation):
        threading.Thread.__init__(self)
        self.exchange = exchange
        self.calculation = calculation
        self.keep_running = True
        # 0 no order; <0 error status
        self.status = 0

    def run(self):
        calculation = self.calculation
        exchange = self.exchange
        self.status = -1
        logging.info('OperateThread starts.')
        executor = ThreadPoolExecutor(5)
        while self.keep_running:
            if self.status != 0:
                self.status = 0
                logging.debug('rebase all coins')
                # rebase all coins
                for k, v in exchange.spot_balance_dict.items():
                    if k == 'xrp':
                        if v > 1:
                            response = exchange.create_spot_order('usdt', k, 'sell_market', amount=v)
                            logging.debug('rebase:' + str(response))
                    elif k == 'qtum' or k == 'omg' or k == 'eos':
                        if v > 0.01:
                            response = exchange.create_spot_order('usdt', k, 'sell_market', amount=v)
                            logging.debug('rebase:' + str(response))
                    elif k == 'btc' or k == 'eth':
                        depth = exchange.get_depth('usdt', k, 'bids')
                        _amount = float(depth[0][0]) * v
                        adjust_amount = 20
                        if _amount < 90:
                            response = exchange.create_spot_order('usdt', k, 'buy_market', amount=adjust_amount)
                            logging.debug('rebase:' + str(response))
                            self.status = -1
                        elif _amount > 130:
                            response = exchange.create_spot_order('usdt', k, 'sell_market',
                                                                    amount=adjust_amount/depth[0][0])
                            logging.debug('rebase:' + str(response))
                            self.status = -1
                    elif k != 'usdt' and v > 0.001:
                        response = exchange.create_spot_order('usdt', k, 'sell_market', amount=v)
                        logging.debug('rebase:' + str(response))
                    else:
                        continue
                exchange.get_available_coins()
                exchange.get_available_coins()
                if self.status == -1:
                    continue
            profit_list = calculation.cal(self.exchange)
            if len(profit_list) == 0:
                time.sleep(0.1)
                continue
            logging.debug('main:profit_list' + str(profit_list))
            best_profit = profit_list[0]
            profit_expect = best_profit[0]
            min_usdt = best_profit[1]
            first_coin = best_profit[2]
            second_coin = best_profit[3]
            second_base_position = best_profit[4]
            first_depth_price = best_profit[5]
            second_depth_price = best_profit[6]
            third_depth_price = best_profit[7]
            usdt_before = exchange.spot_balance_dict['usdt']
            if min_usdt > usdt_before:
                min_usdt = usdt_before
            max_usdt = 50
            if min_usdt > max_usdt:
                min_usdt = max_usdt
            # begin to ordering
            # first order
            request1 = (exchange, 'usdt', first_coin, 'buy_market', min_usdt)
            first_coin_before = min_usdt / first_depth_price
            # second order
            if second_base_position == 1:
                second_coin_before = first_coin_before / second_depth_price
                request2 = (exchange, first_coin, second_coin,  'buy_market', first_coin_before)
            else:
                second_coin_before = first_coin_before * second_depth_price
                request2 = (exchange, second_coin, first_coin,  'sell_market', first_coin_before)
            # third order
            request3 = (exchange, 'usdt', second_coin, 'sell_market', second_coin_before)
            if second_base_position == 1:
                request_list = ([request1], (request2, request3))
            else:
                request_list = ((request1, request2), [request3])
            for response in executor.map(order_task, request_list):
                if response == None or response.get('status') != 'ok':
                    logging.error('order created failed:' + str(response))
                    self.status = -1
                    break
                else:
                    self.status = 0
            usdt_after = exchange.spot_balance_dict['usdt']
            usdt_profit = profit = usdt_after-usdt_before
            if usdt_profit > 0:
                color = '34m'
            else:
                color = '31m'
            logging.info('one round finished:usdt_before=' + str(usdt_before) +
                            ' usdt_after=' + str(usdt_after) +
                            ' usdt_profit=' + '\033[;;' + color + str(usdt_after-usdt_before) + '\033[0m')

def order_task(request_list):
    coin_after = 0
    for request in request_list:
        exchange = request[0]
        base_coin = request[1]
        trans_coin = request[2]
        buy_or_sell = request[3]
        _amount = request[4]
        if coin_after > 0:
            _amount = coin_after
        if buy_or_sell == 'buy_market':
            coin_target = trans_coin
        else:
            coin_target = base_coin
        coin_before = exchange.spot_balance_dict[coin_target]
        response = exchange.create_spot_order(base_coin, trans_coin, buy_or_sell, amount=_amount)
        if response.get('status') != 'ok':
            return response
        i = 0
        while i < 6:
            exchange.get_available_coins()
            coin_after = exchange.spot_balance_dict[coin_target]
            if coin_after > coin_before:
                break
            i += 1
        if i == 6:
            return None
    return response
