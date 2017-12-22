import logging
import threading
import time
from multiprocessing import Queue

class OkexWaveOperateThread(threading.Thread):
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
        fix_line_low = 100
        fix_line_high = 130
        float_line_low = 97
        float_line_high = 103
        float_range = 3
        min_btc_usdt = 20
        while self.keep_running:
            try:
                usdt_before = exchange.spot_balance_dict['usdt']
                btc_amount = exchange.spot_balance_dict['btc']
                btc_price = exchange.get_depth('usdt', 'btc', 'asks')
                btc_value = btc_amount * float(btc_price[0][0])
                if btc_value < fix_line_low:
                    _price = fix_line_low + min_btc_usdt - btc_value
                    exchange.create_spot_order('usdt', 'btc', 'buy_market', price=_price)
                elif btc_value > fix_line_high:
                    _amount = (btc_value - fix_line_high - min_btc_usdt) / btc_price
                    exchange.create_spot_order('usdt', 'btc', 'sell_market', amount=_amount)
                elif btc_value <= float_line_low:
                    exchange.create_spot_order('usdt', 'btc', 'buy_market', price=min_btc_usdt)
                elif btc_value >= float_line_high:
                    _amount = (btc_value - min_btc_usdt) / btc_price
                    exchange.create_spot_order('usdt', 'btc', 'sell_market', amount=_amount)
                else:
                    time.sleep(0.2)
                    continue
                response = queue.get(True, 10)
                _type = response['type']
                if _type == 'error':
                    logging.error('rebase btc order created failed:' + str(response))
                    continue
                response = queue.get(True, 10)
                response = queue.get(True, 10)
                btc_amount = exchange.spot_balance_dict['btc']
                btc_price = exchange.get_depth('usdt', 'btc', 'asks')
                btc_value = btc_amount * float(btc_price[0][0])
                float_line_low = btc_value - float_range
                float_line_high = btc_value + float_range
                # record
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
                logging.error('Exception:%s' % e)
                self.status = -1
