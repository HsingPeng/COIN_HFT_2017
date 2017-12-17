import logging
import threading
import time
from concurrent.futures import ThreadPoolExecutor

def order_task(data):
    exchange = data[0]
    base_coin = data[1]
    trans_coin = data[2]
    buy_or_sell = data[3]
    amount = data[4]
    response = exchange.create_spot_order(base_coin, trans_coin, buy_or_sell, amount=_amount)
    return response

class HuobiHedgeOperateThread(threading.Thread):
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
                break
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
            # begin to ordering
            # first order
            request_list = []
            request_list.append((exchange, 'usdt', first_coin, 'buy_market', min_usdt))
            first_coin_before = min_usdt / first_depth_price
            # second order
            if second_base_position == 1:
                second_coin_before = first_coin_before / second_depth_price
                request_list.append((first_coin, second_coin,  'buy_market', first_coin_before))
            else:
                second_coin_before = first_coin_before * second_depth_price
                request_list.append((second_coin, first_coin,  'sell_market', first_coin_before))
            # third order
            request_list.append(('usdt', second_coin, 'sell_market', second_coin_before))
            with ThreadPoolExecutor(max_workers=5) as executor:
                i = 0
                for response in executor.map(task, tasks):
                    if response.get('status') != 'ok':
                        logging.error(str(i) + ' order created failed:' + str(response))
                        self.status = -1
                        continue 
                    i += 1
            exchange.get_available_coins()
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
