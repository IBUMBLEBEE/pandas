#! /usr/bin/env python
# -*- coding:utf-8 -*-

import calendar
import datetime
import multiprocessing
import mysql.connector
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


def cpu_usage_history_data(hid, time_from, time_till):
    """
    Get cpu history data
    :param hid: string
    :param time_from: start timestamp
    :param time_till: end timestamp
    :return: a day data, list
    """
    cpu_usage_item = "vmware.hv.cpu.usage[{$URL},{HOST.HOST}]"
    datalist = []
    zapi = ZabbixAPI(url)
    zapi.login(user, password)
    itemid_obj = zapi.do_request("item.get", {"output": "extend", "hostids": "%s" % hid,
                                                    "search": {"key_": "%s" % cpu_usage_item}})
    itemid = itemid_obj["result"][0]["itemid"]
    cnx = mysql.connector.connect(host="10.10.255.253", user="root", password="n%KAuOa847ga", database="zabbix")
    cursor = cnx.cursor(buffered=True)
    query = ('''SELECT `value` FROM zabbix.history_uint WHERE itemid = %s AND clock >= %s AND clock <= %s''')
    cursor.execute(query, (itemid, time_from, time_till))
    for value in cursor:
        datalist.append(value[0])
    cursor.close()
    cnx.close()
    cpu_agv_data, cpu_max_data = calculation_unit(datalist)
    return cpu_agv_data, cpu_max_data


def disk_free_history_data(hid, disk_item):
    """
    Get memory last data
    :param hid: list
    :param disk_item: string
    :return: Free space on datastore (percentage)(last value), list
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
    """
    Get memory last data
    :param hid:
    :return:
    """
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
    # print float(memory_total_last_value)/1073741824, memory_usage_last_value
    memory_pfree_last_value = (float(memory_total_last_value)-float(memory_usage_last_value))\
                              /float(memory_total_last_value)
    memory_free_last_value = float(memory_pfree_last_value)*float(memory_total_last_value)/1073741824
    return memory_pfree_last_value*100, memory_free_last_value


# 控制中心
def controller():
    multidimensional_array = []
    zbx = ZabbixInfoEsxi()
    hostids, hostips = zbx.get_host_id()

    # 时间处理
    time_from, time_till = handler_datetime()

    first_line = ["IDC-IP", "CPU-avg/GHz/month", "CPU-max/GHz/month", "MEM-pfree/%/last",
                  "MEM-free/GB/last", "Disk-free/GB/last"]
    multidimensional_array.append(first_line)

    # Disk
    disk_last_data = disk_free_history_data(hid=hostids, disk_item="pfree")

    for number in xrange(0, len(hostids)):

        # Memory
        mem_pfree_final_data, mem_free_final_data = memory_total_data(hostids[number])

        # CPU
        cpu_avg_final_data, cpu_max_final_data = cpu_usage_history_data(hid=hostids[number], time_from=time_from,
                                                                        time_till=time_till)

        print "from: ".format(time_from), " to: ".format(time_till), " hostip: ".format(),\
              " cpu-avg: ".format(cpu_avg_final_data), " cpu-max: ".format(cpu_max_final_data),\
              " memory-pfree: ".format(mem_pfree_final_data), " memory-free: ".format(mem_free_final_data),\
              " Disk: %".format(disk_last_data[number])

        # 构建一维数组
        one_dimensional_array = [hostips[number], cpu_avg_final_data, cpu_max_final_data,
                                 mem_pfree_final_data, mem_free_final_data, disk_last_data[number]]

        # 构建numpy多维数组
        multidimensional_array.append(one_dimensional_array)

    write_to_scv(multidimensional_array)
    # return multidimensional_array


# 月数据计算单元，计算CPU和MEMORY
def calculation_unit(list_data):
    """
    使用numpy模块的多维数组属性进行计算
    :param list_data: list
    :return: Maximum and average value
    """
    # print(list_data)
    list_array = np.array(list_data, dtype=np.float64)
    # print(list_array.sum(), list_array.size)
    agv_data = (list_array.sum()/list_array.size)/(1000*1000*1000)
    # agv_data = list_array.sum
    max_data = list_array.max()/(1000*1000*1000)
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
    first_day = '%s-%s-%s 00:00:00' % (last_month.year, last_month.month, last_month.day)
    last_day = '%s-%s-%s 23:59:59' % (last_month.year, last_month.month, last_days)
    start = str(time.mktime(time.strptime(first_day, '%Y-%m-%d %H:%M:%S'))).split('.')[0]
    end = str(time.mktime(time.strptime(last_day, '%Y-%m-%d %H:%M:%S'))).split('.')[0]
    return start, end


if __name__ == '__main__':
    controller()
    # print(handler_datetime())

