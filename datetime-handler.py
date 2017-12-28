#! /usr/bin/env python
# -*- coding:utf-8 -*-

import datetime
import calendar
import time


last_month = (datetime.date.today().replace(day=1) - datetime.timedelta(1)).replace(day=1)
last_days = calendar.monthrange(last_month.year, last_month.month)[-1]
last_month_timestamp = []
for day_number in xrange(1, (int(last_days)+1)):
    start_time = '%s-%s-%s 00:00:00' % (last_month.year, last_month.month, day_number)
    end_time = '%s-%s-%s 23:59:59' % (last_month.year, last_month.month, day_number)
    start = str(time.mktime(time.strptime(start_time, '%Y-%m-%d %H:%M:%S'))).split('.')[0]
    end = str(time.mktime(time.strptime(end_time, '%Y-%m-%d %H:%M:%S'))).split('.')[0]
    last_month_timestamp.append((start, end))
print(last_month_timestamp)
