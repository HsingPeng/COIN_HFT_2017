from bottle import get, run, template
from bottle.ext.websocket import GeventWebSocketServer
from bottle.ext.websocket import websocket
import gevent
import time

users = set()
@get('/websocket', apply=[websocket])
def chat(ws):
    users.add(ws)
    while True:
        msg = ws.receive()
        if msg is not None:
            for u in users:
                print type(u)
                u.send(msg)
                print u,msg
                time.sleep(109)
        else: break
    users.remove(ws)
run(host='0.0.0.0', port=10000, server=GeventWebSocketServer)
