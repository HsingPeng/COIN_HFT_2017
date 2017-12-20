import logging
import threading
import time

class HuobiOperateThread(threading.Thread):
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
        while self.keep_running:
            if self.status < 0:
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
                    elif k != 'usdt' and v > 0.001:
                        response = exchange.create_spot_order('usdt', k, 'sell_market', amount=v)
                        logging.debug('rebase:' + str(response))
                    else:
                        continue
                self.status = 0
                exchange.get_available_coins()
                exchange.get_available_coins()
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
            usdt_before = exchange.spot_balance_dict['usdt']
            if min_usdt > usdt_before:
                min_usdt = usdt_before
            max_usdt = 100
            if min_usdt > max_usdt:
                min_usdt = max_usdt
            try:
                # begin to ordering
                first_coin_before = exchange.spot_balance_dict[first_coin]
                response = exchange.create_spot_order('usdt', first_coin, 'buy_market', amount=min_usdt)
                if response.get('status') != 'ok':
                    logging.error('first order created failed:' + str(response))
                    self.status = -1
                    continue
                # get coin balance
                i = 0
                while (i < 5):
                    exchange.get_available_coins()
                    if exchange.spot_balance_dict[first_coin] > first_coin_before:
                        break
                if exchange.spot_balance_dict[first_coin] <= first_coin_before:
                    logging.error('first order failed:')
                    self.status = -1 
                    continue
                # second order
                second_coin_before = exchange.spot_balance_dict[second_coin]
                first_coin_before = exchange.spot_balance_dict[first_coin]
                usdt_middle = exchange.spot_balance_dict['usdt']
                if second_base_position == 1:
                    response = exchange.create_spot_order(first_coin, second_coin,
                                                'buy_market', amount=first_coin_before)
                else:
                    response = exchange.create_spot_order(second_coin, first_coin,
                                                'sell_market', amount=first_coin_before)
                if response.get('status') != 'ok':
                    logging.error('second order created failed:' + str(response))
                    self.status = -1
                    continue
                i = 0
                while (i < 5):
                    exchange.get_available_coins()
                    if exchange.spot_balance_dict[second_coin] > second_coin_before:
                        break
                if exchange.spot_balance_dict[second_coin] <= second_coin_before:
                    logging.error('second order failed:')
                    self.status = -1 
                    continue
                # third order
                second_coin_before = exchange.spot_balance_dict[second_coin]
                response = exchange.create_spot_order('usdt', second_coin,
                                            'sell_market', amount=second_coin_before)
                if response.get('status') != 'ok':
                    logging.error('third order created failed:' + str(response))
                    self.status = -1
                    continue
                i = 0
                while (i < 5):
                    exchange.get_available_coins()
                    if exchange.spot_balance_dict['usdt'] > usdt_middle:
                        break
                    exchange.get_available_coins()
                if exchange.spot_balance_dict['usdt'] <= usdt_middle:
                    logging.error('third order failed:')
                    self.status = -1 
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
            except OSError as e:
                logging.error('Exception:' + str(e))
                self.status = -1
