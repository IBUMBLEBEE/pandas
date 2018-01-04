#! /usr/bin/env python
# -*- coding:utf-8 -*-

import calendar
import datetime
import multiprocessing
import numpy as np
from pyzabbix import ZabbixAPI
import pandas as pd
import re
import time


url = "http://10.10.255.253:8080"
user = "Admin"
password = "zabbix!253."


class ZabbixInfoEsxi(object):
    def __init__(self):
        self.url = url
        self.user = user
        self.password = password
        self.hostidlist = []
        self.itemidslist = []
        self.hostipslist = []
        self.zapi = ZabbixAPI(self.url)
        self.zapi.login(self.user, self.password)

    def get_host_id(self):
        """
        先获取主机IP，通过ip获取hostid。通过IP的 sorted 排序
        :return: hostid is list, host ip is list
        """
        dellhost = re.compile(r'(?<![\.\d])(?:\d{1,3}\.){3}\d{1,3}(?![\.\d])')
        for h in self.zapi.host.get(output="extend"):
            for ip in dellhost.findall(h["name"]):
                if "10.10.249" in ip:
                    # print(h["name"], h["hostid"])
                    self.hostipslist.append(h["name"])
        ip = self.zapi.do_request("host.get", {"filter": {"name": sorted(self.hostipslist)}})
        for tmp in ip["result"]:
            self.hostidlist.append(tmp["hostid"])
        return self.hostidlist, sorted(self.hostipslist)

    def get_itemid_from_item(self, hostid, key):
        """

        :param hostid: list
        :param key: string
        :return: itemids is list
        """
        for h in hostid:
            object_itemids = self.zapi.do_request("item.get", {"output": "extend", "hostids": "%s" % h,
                                                               "search": {"key_": "%s" % key}})
            self.itemidslist.append(object_itemids["result"][0]["itemid"])
        return self.itemidslist


def cpu_usage_history_data(hid, itemid, time_from, time_till):
    """
    Get cpu history data
    :param hid: string
    :param itemid: string
    :param time_from: start timestamp
    :param time_till: end timestamp
    :return: a day data, list
    """
    datalist = []
    zapi = ZabbixAPI(url)
    zapi.login(user, password)
    history = zapi.do_request("history.get", {"itemids": ["%s" % itemid], "output": "extend", "hostids": "%s" % hid,
                                              "time_from": "%s" % time_from, "time_till": "%s" % time_till, "id": 1})
    # 单位换算：1000*1000*1000 = 1000000000 Hz=>GHz
    for sub in history['result']:
        datalist.append((float(sub['value'])/1000000000))
    return datalist


def memory_usage_history_data(hid, itemid, time_from, time_till):
    """
    Get memory history data
    :param hid: string
    :param itemid: string
    :param time_from: start timestamp
    :param time_till: end timestamp
    :return: a day data, list
    """
    datalist = []
    zapi = ZabbixAPI(url)
    zapi.login(user, password)
    history = zapi.do_request("history.get", {"itemids": ["%s" % itemid], "output": "extend", "hostids": "%s" % hid,
                                              "time_from": "%s" % time_from, "time_till": "%s" % time_till, "id": 1})
    # 单位换算：1024*1024*1024 = 1073741824 B=>GB
    for sub in history['result']:
        datalist.append(float(sub['value'])/1073741824)
    return datalist


def disk_free_history_data(hid, disk_item):
    """

    :param hid: list
    :param disk_item: string
    :return: Free space on datastore (percentage)(last value)
    """
    itemidslist = []
    zapi = ZabbixAPI(url)
    zapi.login(user, password)
    for h in hid:
        last_value = zapi.do_request("item.get", {"output": "extend", "hostids": "%s" % h,
                                                  "search": {"key_": "%s" % disk_item}})
        itemidslist.append(last_value["result"][0]["lastvalue"])
    return itemidslist


def memory_total_data(hid):
    memory_total = "vmware.hv.hw.memory[{$URL},{HOST.HOST}]"
    memory_usage = "vmware.hv.memory.used[{$URL},{HOST.HOST}]"
    zapi = ZabbixAPI(url)
    zapi.login(user, password)

    total_last_value = zapi.do_request("item.get", {"output": "extend", "hostids": "%s" % hid,
                                       "search": {"key_": "%s" % memory_total}})
    memory_total_last_value = total_last_value["result"][0]["lastvalue"]

    usage_last_value = zapi.do_request("item.get", {"output": "extend", "hostids": "%s" % hid,
                                                    "search": {"key_": "%s" % memory_usage}})
    memory_usage_last_value = usage_last_value["result"][0]["lastvalue"]
    print float(memory_total_last_value)/1073741824, memory_usage_last_value
    memory_pfree_last_value = (float(memory_total_last_value)-float(memory_usage_last_value))\
                              /float(memory_total_last_value)
    memory_free_last_value = float(memory_pfree_last_value)*float(memory_total_last_value)/1073741824
    return memory_pfree_last_value*100, memory_free_last_value


# 控制中心
def controller():
    cpu_month_data = []
    memory_month_data = []
    multidimensional_array = []
    zbx = ZabbixInfoEsxi()
    hostids, hostips = zbx.get_host_id()
    # print(hostids)
    # print(hostips)

    cpu_usage_itemids = zbx.get_itemid_from_item(hostids, "vmware.hv.cpu.usage[{$URL},{HOST.HOST}]")
    memory_useage_itemids = zbx.get_itemid_from_item(hostids, "vmware.hv.memory.used[{$URL},{HOST.HOST}]")

    # for oneday in handler_datetime():
    first_line = ["IDC-IP", "CPU-avg/GHz/month", "CPU-max/GHz/month", "MEM-avg/G/month", "MEM-max/G/month"]
    multidimensional_array.append(first_line)

    # Disk
    disk_last_data = disk_free_history_data(hid=hostids, disk_item="pfree")

    for number in xrange(0, len(hostids)):

        # 计算所有主机Disk数据
        mem_pfree_final_data, mem_free_final_data = memory_total_data(hostids[number])

        for oneday in handler_datetime():
            time_from, time_till = oneday

            # 打印测试数据
            print "from: %s to: %s hostid: %s cpu: %s pfree_memory: %s%s free_memroy: %s Disk: %s%s" % \
                  (time_from, time_till, hostips[number], cpu_usage_itemids[number],
                   mem_pfree_final_data, "%", mem_free_final_data, disk_last_data[number], '%')

            # CPU
            cpu_day_data = cpu_usage_history_data(hid=hostids[number], itemid=cpu_usage_itemids[number],
                                                  time_from=time_from, time_till=time_till)
            cpu_day_data = data_repair(cpu_day_data)
            cpu_month_data.append(cpu_day_data)

            # memory
            # memory_day_data = memory_usage_history_data(hid=hostids[number], itemid=memory_useage_itemids[number],
            #                                             time_from=time_from, time_till=time_till)
            # memory_day_data = data_repair(memory_day_data)
            # memory_month_data.append(memory_day_data)

        # 计算CPU一个月均值
        cpu_avg_final_data, cpu_max_final_data = calculation_unit(cpu_month_data)
        # mem_avg_final_data, mem_max_final_data = calculation_unit(memory_month_data)

        # 计算所有主机Disk数据
        # mem_pfree_final_data, mem_free_final_data = memory_total_data(hostids[number])

        # 构建一维数组
        one_dimensional_array = [hostips[number], cpu_avg_final_data, cpu_max_final_data,
                                 mem_pfree_final_data, mem_free_final_data, disk_last_data[number]]

        # 构建numpy多维数组
        multidimensional_array.append(one_dimensional_array)

    write_to_scv(multidimensional_array)
    # return multidimensional_array


# 数据修复部分
def data_repair(org_data):
    """
    当数据大于1440一天数据量时，使用修复保持矩阵维度相等
    :param org_data: List
    :return: list
    """
    print(org_data)
    if len(org_data) < 1440:
        last_data = org_data[-1]
        length_repair_data = 1440 - len(org_data)
        new_list = [[last_data]*length_repair_data]
        complete_data = org_data.extend(new_list)
        return complete_data
    elif len(org_data) > 1440:
        length_repair_data = 1440-len(org_data)
        complete_data = org_data[:length_repair_data]
        return complete_data
    else:
        pass


# 月数据计算单元，计算CPU和MEMORY
def calculation_unit(list_data):
    """
    使用numpy模块的多维数组属性进行计算
    :param list_data: list
    :return: Maximum and average value
    """
    # print(list_data)
    list_array = np.array(list_data, dtype=np.float64)
    agv_data = list_array.sum()/list_array.size
    # agv_data = list_array.sum
    max_data = list_array.max()
    return agv_data, max_data


# 写入SCV文件
def write_to_scv(data):
    """
    使用numpy模块属性写入文件csv
    :param data: numpy的多维数组写入文件
    :return: None
    """
    tmp_data = np.array(data)
    ts = pd.Series(np.arange(tmp_data.shape[-1]), index=tmp_data)
    ts.to_csv("IDC.csv")


# 时间处理，间隔为一个月
def handler_datetime():
    """
    获取上月每天的时间开始和结束时间戳
    :return: list
    """
    last_month = (datetime.date.today().replace(day=1) - datetime.timedelta(1)).replace(day=1)
    last_days = calendar.monthrange(last_month.year, last_month.month)[-1]
    last_month_timestamp = []
    for day_number in xrange(1, (int(last_days)+1)):
        start_time = '%s-%s-%s 00:00:00' % (last_month.year, last_month.month, day_number)
        end_time = '%s-%s-%s 23:59:59' % (last_month.year, last_month.month, day_number)
        start = str(time.mktime(time.strptime(start_time, '%Y-%m-%d %H:%M:%S'))).split('.')[0]
        end = str(time.mktime(time.strptime(end_time, '%Y-%m-%d %H:%M:%S'))).split('.')[0]
        last_month_timestamp.append((start, end))
    return last_month_timestamp


if __name__ == '__main__':
    controller()

