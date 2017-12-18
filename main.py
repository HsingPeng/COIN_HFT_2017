#!/usr/bin/env python3

import logging
import threading
import signal
import sys
import time
from okex import Okex
from calculation import Calculation
from config import Config
from operation import OperateThread

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
        self.heartbeat_thread.keep_running = False
        self.exchange.close()

    def run(self):
        try:
            self.fetch_thread = FetchThread(self.exchange)
            self.fetch_thread.start()
            self.heartbeat_thread = HeartbeatThread(self.exchange)
            self.heartbeat_thread.start()
            self.operate_thread = OperateThread(self.exchange
                                        , self.calculation)
            time.sleep(5)
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
        self.keep_running = True

    def run(self):
        while self.keep_running:
            self.exchange.connect()
        depth_dict = self.exchange.get_depth_dict()
        #logging.debug('main:' + str(depth_dict))

class HeartbeatThread(threading.Thread):
    def __init__(self, exchange):
        threading.Thread.__init__(self)
        self.exchange = exchange
        self.keep_running = True

    def run(self):
        time.sleep(28)
        while self.keep_running:
            self.exchange.heartbeat()
            time.sleep(28)

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
