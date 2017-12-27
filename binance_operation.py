import logging
import threading
import time

class BinanceOperateThread(threading.Thread):
    def __init__(self, exchange, calculation):
        threading.Thread.__init__(self)
        self.exchange = exchange
        self.calculation = calculation
        self.queue = exchange.queue
        # 0 no order; <0 error status
        self.status = 0

    def run(self):
        calculation = self.calculation
        exchange = self.exchange
        queue = self.queue
        self.status = -1
        logging.info('OperateThread starts.')
        exchange.get_available_coins()
        exchange.get_available_coins()
        while self.exchange.keep_running:
            if self.status < 0:
                logging.info('rebase all coins')
                # rebase all coins
                for k, v in exchange.spot_balance_dict.items():
                    if k == 'btc':
                        if v > 0.001:
                            response = exchange.create_spot_order('usdt', k, 'sell_market', amount=v)
                            logging.debug('rebase:' + str(response))
                    elif k == 'neo':
                        if v > 0.001:
                            response = exchange.create_spot_order('usdt', k, 'sell_market', amount=v)
                            logging.debug('rebase:' + str(response))
                    elif k == 'bnb':
                        if v > 1:
                            response = exchange.create_spot_order('usdt', k, 'sell_market', amount=v)
                            logging.debug('rebase:' + str(response))
                    elif k == 'bcc' or k == 'ltc' or k == 'eth':
                        if v > 0.001:
                            response = exchange.create_spot_order('usdt', k, 'sell_market', amount=v)
                            logging.debug('rebase:' + str(response))
                    elif k != 'usdt' and v > 0.001:
                        response = exchange.create_spot_order('usdt', k, 'sell_market', amount=v)
                        logging.debug('rebase:' + str(response))
                    else:
                        continue
                try:
                    while queue.empty() == False:
                        response = queue.get(True, 10)
                except Exception as e:
                    logging.error('rebase Error:%s' % e)
                self.status = 0
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
            max_usdt = 20
            if min_usdt > max_usdt:
                min_usdt = max_usdt
            try:
                # begin to ordering
                first_coin_before = exchange.spot_balance_dict[first_coin]
                _amount = min_usdt / first_depth_price
                response = exchange.create_spot_order('usdt', first_coin, 'buy_market', amount=_amount)
                if response.get('orderId') == None:
                    logging.error('first order created failed:' + str(response))
                    self.status = -1
                    continue
                # get coin balance
                response = queue.get(True, 10)
                if exchange.spot_balance_dict[first_coin] <= first_coin_before:
                    logging.error('first order failed:')
                    self.status = -1 
                    continue
                # second order
                second_coin_before = exchange.spot_balance_dict[second_coin]
                first_coin_before = exchange.spot_balance_dict[first_coin]
                usdt_middle = exchange.spot_balance_dict['usdt']
                if second_base_position == 1:
                    _amount = first_coin_before / second_depth_price
                    response = exchange.create_spot_order(first_coin, second_coin,
                                                'buy_market', amount=_amount)
                else:
                    response = exchange.create_spot_order(second_coin, first_coin,
                                                'sell_market', amount=first_coin_before)
                if response.get('orderId') == None:
                    logging.error('second order created failed:' + str(response))
                    self.status = -1
                    continue
                # get coin balance
                response = queue.get(True, 10)
                if exchange.spot_balance_dict[second_coin] <= second_coin_before:
                    logging.error('second order failed:')
                    self.status = -1 
                    continue
                # third order
                second_coin_before = exchange.spot_balance_dict[second_coin]
                response = exchange.create_spot_order('usdt', second_coin,
                                            'sell_market', amount=second_coin_before)
                if response.get('orderId') == None:
                    logging.error('third order created failed:' + str(response))
                    self.status = -1
                    continue
                # get coin balance
                response = queue.get(True, 10)
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
            except Exception as e:
                logging.error('Exception:' + str(e))
                self.status = -1
