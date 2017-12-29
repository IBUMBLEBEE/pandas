#! /usr/bin/env python
# -*- coding:utf-8 -*-


import numpy as np
import matplotlib


from getdata import threading_controller

# cpu_30_data, memory_30_data = threading_controller

cpu_30_data = [[43.5853, 43.5853, 43.5853, 43.5853],
               [43.5853, 43.5853, 43.5853, 43.5853],
               [43.5853, 43.5853, 43.5853, 43.5853],
               [43.5853, 43.5853, 43.5853, 43.5853],
               [43.5853, 43.5853, 43.5853, 43.5853],
               [43.5853, 43.5853, 43.5853, 43.5853],
               [43.5853, 43.5853, 43.5853, 43.5853],
               [43.5853, 43.5853, 43.5853, 43.5853],
               [43.5853, 43.5853, 43.5853, 43.5853],
               [43.5853, 43.5853, 43.5853, 43.5853],
               [43.5853, 43.5853, 43.5853, 43.6853]]

cpu_30_array = np.array(cpu_30_data)
print("cpu usage avg: %s, cpu usage max: %s" % (cpu_30_array.sum()/cpu_30_array.size, cpu_30_array.max()))
# memory_30_array = np.array(memory_30_data)



