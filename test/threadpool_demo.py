#!/usr/bin/env python3

from concurrent.futures import ThreadPoolExecutor
import time

def task(msg, m):
    time.sleep(2)
    return msg

tasks = [['ABCD', 1], ['1234', 2], ['!@#$%', 3]]

print(str(time.time()))
with ThreadPoolExecutor(max_workers=5) as executor:
    for result in executor.map(task, tasks, tasks):
        print(result)
    for result in executor.map(task, tasks, tasks):
        print(result)
print(str(time.time()))
