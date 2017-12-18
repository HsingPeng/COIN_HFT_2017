#!/usr/bin/env python3

import okex_pair

usdt_list = okex_pair.okex_usdt
btc_list = okex_pair.okex_btc
eth_list = okex_pair.okex_eth
bch_list = okex_pair.okex_bch

_list = []

for coin in usdt_list:
    if coin in btc_list:
        _list.append((coin, 'btc'))
        _list.append(('btc', coin))
    if coin in eth_list:
        _list.append((coin, 'eth'))
        _list.append(('eth', coin))
    if coin in bch_list:
        _list.append((coin, 'bch'))
        _list.append(('bch', coin))
# print(str(_list))
f = open('okex_list.py', 'w')
f.write('trade_list=[\n' + '("' + _list[0][0] + '","' + _list[0][1] + '"),\n')
for pair in _list[1:-1]:
    f.write('("' + pair[0] + '","' + pair[1] + '"),\n')
f.write('("' + _list[-1][0] + '","' + _list[-1][1] + '")\n')
f.write(']')
f.close()
