from datetime import datetime
from time import time


time_now = time()
print(datetime.fromtimestamp(time_now))
now = datetime.fromtimestamp(time_now + 3600 )
print(now)
