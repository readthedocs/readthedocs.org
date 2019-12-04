import os
import time
import requests

wait_sleep = 3
max_loops = 15

loops = 1
if 'SEARCH' in os.environ:
    while loops < max_loops:
        try:
            print('Waiting for search service...')
            response = requests.get('http://search:9200/_cluster/health')
            if response.status_code == 200:
                print('Search is ready!')
                break
            loops += 1
        except:
            pass
        time.sleep(wait_sleep)
