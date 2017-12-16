#!/usr/bin/env python3

import socket
import ssl
import logging

logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s')

sock = ssl.wrap_socket(socket.socket())
logging.debug('start')
sock.connect(('api.huobi.pro', 443))
logging.debug('connected')
data = "GET /market/depth?symbol=ethusdt&type=step1 HTTP/1.1\r\nHost: api.huobi.pro\r\nConnection: close\r\nUser-Agent: Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.71 Safari/537.36\r\nContent-type: application/x-www-form-urlencoded\r\n\r\n"
sock.sendall(data.encode())
logging.debug('send all')
#sock.connect(('github.com', 443))
#sock.sendall("GET / HTTP/1.1\r\nHost: github.com\r\nConnection: close\r\n\r\n".encode())
response = ''
temp = sock.recv(64)
logging.debug('response:')
response += temp.decode()
while temp:
    temp = sock.recv(4096)
    response += temp.decode()
logging.debug('response:' + response)
