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
        self.exchange = Okex()
        for trade in Config.okex_three_trade_list:
            self.calculation.add_three_trade(trade[0], trade[1])

    def fetch_data_from_exchange(self):
        while self.keep_running:
            self.exchange.connect();

    def disconnect_from_exchange(self):
        self.fetch_thread.keep_running = False
        self.exchange.close()

    def run(self):
        try:
            self.fetch_thread = FetchThread(self.exchange)
            self.fetch_thread.start()
            self.calculate_thread = CalculateThread(self.exchange
                                        , self.calculation)
            self.calculate_thread.start()
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
        logging.debug('main:' + str(depth_dict))

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
            logging.info('main:profit_list' + str(profit_list))
            time.sleep(1)

def sigint_handler(signum,frame):
    logging.info("main:exit")
    controller.close()
    sys.exit()

if __name__ == "__main__":
    logging.basicConfig(filename='main.log', level=logging.DEBUG)
    controller = Controller()
    signal.signal(signal.SIGINT, sigint_handler)
    controller.setOkex()
    controller.run()
    while True:
        time.sleep(10)
