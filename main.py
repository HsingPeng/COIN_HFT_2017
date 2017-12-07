#!/usr/bin/env python

import logging
import threading
import signal
import sys
import time
from okex import Okex
from calculation import Calculation
from config import Config

class Controller(object):

    def __init__(self):
        self.calculation = Calculation()

    def setOkex(self):
        self.exchange = Okex(Config.okex_api_key, Config.okex_secret_key)
        trade_list = Config.okex_three_trade_list
        # add depths monitor
        self.exchange.add_coins(trade_list)
        # add coins calculations
        for trade in trade_list:
            self.calculation.add_three_trade(trade[0], trade[1])

    def disconnect_from_exchange(self):
        self.fetch_thread.keep_running = False
        self.exchange.close()

    def run(self):
        try:
            self.fetch_thread = FetchThread(self.exchange)
            self.fetch_thread.start()
            self.operate_thread = OperateThread(self.exchange
                                        , self.calculation)
            time.sleep(3)
            self.operate_thread.start()
        except SystemExit:
            pass
    
    def close(self):
        self.operate_thread.keep_running = False
        self.disconnect_from_exchange() 

class FetchThread(threading.Thread):
    def __init__(self, exchange):
        threading.Thread.__init__(self)
        self.exchange = exchange
        self.keep_running = True;

    def run(self):
        while self.keep_running:
            self.exchange.connect();
        depth_dict = self.exchange.get_depth_dict()
        #logging.debug('main:' + str(depth_dict))

class OperateThread(threading.Thread):
    def __init__(self, exchange, calculation):
        threading.Thread.__init__(self)
        self.exchange = exchange
        self.order_cond = exchange.order_cond
        self.calculation = calculation
        self.keep_running = True

    def run(self):
        calculation = self.calculation
        exchange = self.exchange
        order_cond = self.order_cond
        while self.keep_running:
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
            # begin to ordering
            order_cond.acquire()
            exchange.create_spot_order('usdt', first_coin, 'buy_market', price=min_usdt)
            exchange.order_status = 1
            self.wait_for_respose(1)
            # whether first order created failed.
            if exchange.order_status != 10:
                logging.error('first order created failed:order_status=' + str(exchange.order_status))
                order_cond.release()
                exchange.order_status = 0
                break
            self.wait_for_respose(10)
            if exchange.order_status != 100:
                logging.error('first order failed:order_status=' + str(exchange.order_status))
                order_cond.release()
                break
            # second order
            first_coin_before = exchange.spot_balance_dict[first_coin]
            if second_base_position == 1:
                exchange.create_spot_order(first_coin, second_coin
                                            , 'buy_market', price=first_coin_before)
            else:
                exchange.create_spot_order(second_coin, first_coin
                                            , 'sell_market', amount=first_coin_before)
            exchange.order_status = 2
            self.wait_for_respose(2)
            if exchange.order_status != 20:
                logging.error('second order created failed:order_status=' + str(exchange.order_status))
                order_cond.release()
                break
            self.wait_for_respose(20)
            if exchange.order_status != 200:
                logging.error('second order failed:order_status=' + str(exchange.order_status))
                order_cond.release()
                break
            # third order
            second_coin_before = exchange.spot_balance_dict[second_coin]
            exchange.create_spot_order('usdt', second_coin
                                        , 'sell_market', amount=second_coin_before)
            exchange.order_status = 3
            self.wait_for_respose(3)
            if exchange.order_status != 30:
                logging.error('third order created failed:order_status=' + str(exchange.order_status))
                order_cond.release()
                break
            self.wait_for_respose(30)
            if exchange.order_status != 300:
                logging.error('third order failed:order_status=' + str(exchange.order_status))
                order_cond.release()
                break
            exchange.order_status = 0
            order_cond.release()
            usdt_after = exchange.spot_balance_dict['usdt']
            logging.info('one round finished:usdt_before=' + str(usdt_before)
                            + ' usdt_after=' + str(usdt_after)
                            + ' profit=' + '\033[;;33m' + str(usdt_after-usdt_before) + '\033[0m')

    def wait_for_respose(self, current_status):
        exchange = self.exchange
        while exchange.order_status > 0:
            self.order_cond.wait()
            if exchange.order_status > current_status:
                break
        return

    #controller.exchange.create_spot_order('usdt', 'act', 'buy_market', price=1)


def sigint_handler(signum,frame):
    logging.info("main:exit")
    controller.close()
    sys.exit()

if __name__ == "__main__":
    # record log
    logging.basicConfig(filename='main.log', level=logging.DEBUG
                    ,format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s')
    # The condition is made for waiting making order and receiving the result
    controller = Controller()
    signal.signal(signal.SIGINT, sigint_handler)
    controller.setOkex()
    controller.run()
    while True:
        time.sleep(10)
