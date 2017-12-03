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
        self.__order_cond = threading.Condition()
        self.calculation = Calculation(self.__order_cond)

    def setOkex(self):
        self.exchange = Okex(Config.okex_api_key, Config.okex_secret_key, self.__order_cond)
        trade_list = Config.okex_three_trade_list
        # add depths monitor
        #self.exchange.add_coins(trade_list)
        # add coins calculations
        #for trade in trade_list:
        #    self.calculation.add_three_trade(trade[0], trade[1])

    def disconnect_from_exchange(self):
        self.fetch_thread.keep_running = False
        self.exchange.close()

    def run(self):
        try:
            self.fetch_thread = FetchThread(self.exchange)
            self.fetch_thread.start()
            self.calculate_thread = CalculateThread(self.exchange
                                        , self.calculation)
            #self.calculate_thread.start()
        except SystemExit:
            pass
    
    def close(self):
        self.calculate_thread.keep_running = False
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

class CalculateThread(threading.Thread):
    def __init__(self, exchange, calculation):
        threading.Thread.__init__(self)
        self.exchange = exchange
        self.calculation = calculation
        self.keep_running = True;

    def run(self):
        calculation = self.calculation
        time.sleep(4)
        while self.keep_running:
            profit_list = calculation.cal(self.exchange)
            logging.debug('main:profit_list' + str(profit_list))
            time.sleep(0.5)

def sigint_handler(signum,frame):
    logging.info("main:exit")
    controller.close()
    sys.exit()

if __name__ == "__main__":
    # record log
    logging.basicConfig(filename='main.log', level=logging.DEBUG)
    # The condition is made for waiting making order and receiving the result
    controller = Controller()
    signal.signal(signal.SIGINT, sigint_handler)
    controller.setOkex()
    controller.run()
    time.sleep(3)
    controller.exchange.login()
    #controller.exchange.create_spot_order('usdt', 'act', 'buy_market', price=1)
    while True:
        time.sleep(10)
