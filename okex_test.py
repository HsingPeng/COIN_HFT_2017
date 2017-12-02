#!/usr/bin/env python

from okex import Okex
from config import Config

if __name__ == "__main__":
    okex = Okex()
    trade_list = Config.okex_three_trade_list
    okex.add_coins(trade_list)
