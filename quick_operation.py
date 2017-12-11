import logging
import threading
import time

class QuickOperateThread(threading.Thread):
    def __init__(self, exchange, calculation):
        threading.Thread.__init__(self)
        self.exchange = exchange
        self.queue = exchange.queue
        self.calculation = calculation
        self.keep_running = True
        # 0    no order; <0   error status
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
                logging.debug('rebase all coins')
                # rebase all coins
                for k, v in exchange.spot_balance_dict.items():
                    if k == 'btc' and v > 0.001:
                        exchange.create_spot_order('usdt', k, 'sell_market', amount=v)
                    elif k != 'usdt' and v > 0.01:
                        exchange.create_spot_order('usdt', k, 'sell_market', amount=v)
                    else:
                        continue
                    response = queue.get()
                    _type = response['type']
                    if _type == 'error':
                        logging.error('rebase order created failed:' + str(response))
                        continue
                    response = queue.get()
                    response = queue.get()
                self.status = 0
            profit_list = calculation.cal(self.exchange)
            if len(profit_list) == 0:
                time.sleep(0.1)
                continue
            while queue.empty() == False:
                    response = queue.get()
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
            if min_usdt > 120:
                min_usdt = 120
            # begin to ordering
            exchange.create_spot_order('usdt', first_coin, 'buy_market', price=min_usdt)
            response = queue.get()
            _type = response['type']
            # whether first order created failed.
            if _type == 'error':
                logging.error('first order created failed:' + str(response))
                self.status = response['code']
                continue
            # get basecoin balance
            response = queue.get()
            _type = response['type']
            if _type == 'error':
                logging.error('first order failed:' + str(response))
                self.status = response['code']
                continue
            # get targetcoin balance
            response = queue.get()
            _type = response['type']
            if _type == 'error':
                logging.error('first order failed:' + str(response))
                self.status = response['code']
                continue
            # second order
            first_coin_before = exchange.spot_balance_dict[first_coin]
            if second_base_position == 1:
                exchange.create_spot_order(first_coin, second_coin,
                                            'buy_market', price=first_coin_before)
            else:
                exchange.create_spot_order(second_coin, first_coin,
                                            'sell_market', amount=first_coin_before)
            response = queue.get()
            _type = response['type']
            if _type == 'error':
                logging.error('second order created failed:' + str(response))
                self.status = response['code']
                continue
            response = queue.get()
            _type = response['type']
            if _type == 'error':
                logging.error('second order failed:' + str(response))
                self.status = response['code']
                continue
            response = queue.get()
            _type = response['type']
            if _type == 'error':
                logging.error('second order failed:' + str(response))
                self.status = response['code']
                continue
            # third order
            second_coin_before = exchange.spot_balance_dict[second_coin]
            exchange.create_spot_order('usdt', second_coin,
                                        'sell_market', amount=second_coin_before)
            response = queue.get()
            _type = response['type']
            if _type == 'error':
                logging.error('third order created failed:' + str(response))
                self.status = response['code']
                continue
            response = queue.get()
            _type = response['type']
            if _type == 'error':
                logging.error('third order failed:' + str(response))
                self.status = response['code']
                continue
            response = queue.get()
            _type = response['type']
            if _type == 'error':
                logging.error('third order failed:' + str(response))
                self.status = response['code']
                continue
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

