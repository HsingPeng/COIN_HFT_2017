import requests
import logging

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s')
s = requests.Session()
i = 0
while i < 3:
    logging.info('start')
    r = s.get("https://www.baidu.com/")
    logging.info('get:')
    i += 1
