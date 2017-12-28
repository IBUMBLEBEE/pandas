#! /usr/bin/env python
# -*- coding:utf-8 -*-


import numpy as np
import matplotlib


from getdata import threading_controller

cpu_30_data, memory_30_data = threading_controller

cpu_30_array = np.array(cpu_30_data)
memory_30_array = np.array(memory_30_data)



