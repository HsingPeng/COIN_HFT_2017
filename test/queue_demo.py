import Queue
import threading
import time

class MyThread(threading.Thread):
    def __init__(self, q):
        threading.Thread.__init__(self)
        self.q = q
    def run(self):
        try:
            self.q.get(True, 2)
        except Queue.Empty:
            print('except Empty')
        print('thread exit.')

queue = Queue.Queue()
thread = MyThread(queue)
thread.start()

time.sleep(10)
