#! /usr/bin/env python
# -*- coding:utf-8 -*-


import xlrd
import xlutils.copy
import csv
import pandas as pd
import numpy as np
from tempfile import NamedTemporaryFile



# file1 = open('test.csv', 'wb')
# writer = csv.writer(file1)
#
# writer.writerow([1, "IDC_IP", "CPU_Usage/%/M", "CPU_Usage/%/max", "mem_usage/G/M", "mem_usage/G/Max"])
# # writer.writerow(["IDC IP", "CPU Usage/%/M", "CPU Usage/%/max", "mem usage/G/M", "mem usage/G/Max"])
# # print(["IDC_IP", "CPU_Usage/%/M", "CPU_Usage/%/max", "mem_usage/G/M", "mem_usage/G/Max"])
# file1.close()

# book = xlrd.open_workbook("test.xls")
# wtbook = xlutils.copy.copy(book)
# wtsheet = wtbook.get_sheet(0)
# wtsheet.write(0, 0, "Ok, changed!")
# wtbook.save('test.xls')

data = [[43.5853, 43.5853, 43.5853, 43.5853],
        [43.5853, 43.5853, 43.5853, 43.5853],
        [43.5853, 43.5853, 43.5853, 43.5853],
        [43.5853, 43.5853, 43.5853, 43.5853]]
datanp = np.array(data)
# print(datanp.shape[-1])
ts = pd.Series(np.arange(datanp.shape[-1]), index=data)
ts.to_csv("ts.csv")
# out = data.to_csv("out.csv")
# print(out)
