#!/usr/bin/env python

import logging
import threading
import signal
import sys
import time
from okex import Okex

class Controller(object):

    def __init__(self):
        pass

    def setOkex(self):
        self.exchange = Okex()

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
        except SystemExit:
            pass
    
    def close(self):
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
        logging.debug(depth_dict)
        

def sigint_handler(signum,frame):
    logging.info("main exit")
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
