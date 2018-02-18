import logging
import threading
import time
from multiprocessing import Queue

class OperateThread(threading.Thread):
    def __init__(self, exchange, calculation):
        threading.Thread.__init__(self)
        self.exchange = exchange
        self.queue = exchange.queue
        self.calculation = calculation
        self.keep_running = True
        # 0 no order; <0 error status
        self.status = 0

    def run(self):
        calculation = self.calculation
        exchange = self.exchange
        queue = self.queue
        self.status = -1
        logging.info('OperateThread starts.')
        while self.keep_running:
            if self.status < 0:
                exchange.add_channel_userinfo()
                time.sleep(0.2)
                logging.info('rebase all coins')
                # rebase all coins
                try:
                    for k in exchange.spot_balance_dict.keys():
                        v = exchange.spot_balance_dict[k]
                        if k == 'btc' and v > 0.001:
                            exchange.create_spot_order('usdt', k, 'sell_market', amount=v)
                        elif k != 'usdt' and v > 0.01:
                            exchange.create_spot_order('usdt', k, 'sell_market', amount=v)
                        else:
                            continue
                            response = queue.get(True, 3)
                            _type = response['type']
                            if _type == 'error':
                                logging.error('rebase order created failed:' + str(response))
                                continue
                except Exception as e:
                    logging.error('rebase Error:%s' % e)
                self.status = 0
            profit_list = calculation.cal(self.exchange)
            if len(profit_list) == 0:
                time.sleep(0.05)
                continue
            while queue.empty() == False:
                    response = queue.get(True, 3)
            logging.debug('main:profit_list' + str(profit_list))
            best_profit = profit_list[0]
            profit_expect = best_profit[0]
            min_usdt = best_profit[1]
            first_coin = best_profit[2]
            second_coin = best_profit[3]
            second_base_position = best_profit[4]
            usdt_before = exchange.spot_balance_dict['usdt']
            if min_usdt > usdt_before:
                min_usdt = usdt_before
            max_usdt = 30
            if min_usdt > max_usdt:
                min_usdt = max_usdt
            try:
                # begin to ordering
                i = 0
                while i <= 3:
                    i += 1
                    exchange.create_spot_order('usdt', first_coin, 'buy_market', price=min_usdt)
                    response = queue.get(True, 3)
                    _type = response['type']
                    # whether first order created failed.
                    if _type == 'error':
                        logging.error('first order created failed:' + str(response))
                        self.status = response['code']
                        continue
                    elif _type == 'order':
                        filled_size = response.get('filledSize')
                        available = filled_size * 0.999
                        self.status = 0
                        break
                    else:
                        self.status = -2
                        logging.error('first order created failed:' + str(response))
                        break
                if self.status < 0:
                    time.sleep(0.5)
                    continue
                # second order
                #first_coin_before = exchange.spot_balance_dict[first_coin]
                first_coin_before = available
                i = 0
                while i<=10:
                    i += 1
                    if second_base_position == 1:
                        exchange.create_spot_order(first_coin, second_coin,
                                                    'buy_market', price=first_coin_before)
                    else:
                        exchange.create_spot_order(second_coin, first_coin,
                                                    'sell_market', amount=first_coin_before)
                    response = queue.get(True, 3)
                    _type = response['type']
                    if _type == 'error':
                        logging.debug('second order created failed:' + str(response))
                        self.status = response['code']
                        continue
                    elif _type == 'order':
                        if second_base_position == 1:
                            filled_size = response.get('filledSize')
                            available = filled_size * 0.999
                        else:
                            executed_value = response.get('executedValue')
                            available = executed_value * 0.999
                        self.status = 0
                        break
                    else:
                        logging.error('second order created failed:' + str(response))
                        self.status = -2
                        break
                if self.status < 0:
                    time.sleep(0.5)
                    continue
                # third order
                #second_coin_before = exchange.spot_balance_dict[second_coin]
                second_coin_before = available
                i = 0
                while i<=10:
                    i += 1
                    exchange.create_spot_order('usdt', second_coin,
                                                'sell_market', amount=second_coin_before)
                    response = queue.get(True, 3)
                    _type = response['type']
                    if _type == 'error':
                        logging.debug('third order created failed:' + str(response))
                        self.status = response['code']
                        continue
                    elif _type == 'order':
                        executed_value = response.get('executedValue')
                        available = executed_value * 0.999
                        self.status = 0
                        break
                    else:
                        self.status = -2
                        logging.error('third order created failed:' + str(response))
                        break
                if self.status < 0:
                    time.sleep(2)
                    continue
                usdt_after = available + usdt_before - min_usdt
                usdt_profit = usdt_after - usdt_before
                if usdt_profit > 0:
                    color = '34m'
                else:
                    color = '31m'
                logging.info('one round finished:usdt_before=' + str(usdt_before) +
                                ' usdt_after=' + str(usdt_after) +
                                ' usdt_profit=' + '\033[;;' + color + str(usdt_after-usdt_before) + '\033[0m')
            except Exception as e:
                logging.error('Exception:%s' % e)
                self.status = -1
