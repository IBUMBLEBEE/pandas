#! /usr/bin/env python
# -*- coding:utf-8 -*-

import calendar
import datetime
import multiprocessing
from pyzabbix import ZabbixAPI
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
        self.iplist = []
        self.itemidslist = []
        self.zapi = ZabbixAPI(self.url)
        self.zapi.login(self.user, self.password)

    def get_host_id(self):
        dellhost = re.compile(r'(?<![\.\d])(?:\d{1,3}\.){3}\d{1,3}(?![\.\d])')
        for h in self.zapi.host.get(output="extend"):
            for ip in dellhost.findall(h["name"]):
                if "10.10.249" in ip:
                    # print(ip)
                    self.iplist.append(h["hostid"])
        return self.iplist

    def get_itemid_from_item(self, hostid, key):
        for h in hostid:
            object_itemids = self.zapi.do_request("item.get", {"output": "itemids", "hostids": "%s" % h,
                                                               "search": {"key_": "%s" % key}})
            self.itemidslist.append(object_itemids["result"][0]["itemid"])
        return self.itemidslist


def cpu_usage_history_data(hid, itemid, time_from, time_till):
    datalist = []
    zapi = ZabbixAPI(url)
    zapi.login(user, password)
    history = zapi.do_request("history.get", {"itemids": ["%s" % itemid], "output": "extend", "hostids": "%s" % hid,
                                              "time_from": "%s" % time_from, "time_till": "%s" % time_till, "id": 1})
    for sub in history['result']:
        datalist.append(sub['value'])
    return datalist


def memory_usage_history_data(hid, itemid, time_from, time_till):
    datalist = []
    zapi = ZabbixAPI(url)
    zapi.login(user, password)
    history = zapi.do_request("history.get", {"itemids": ["%s" % itemid], "output": "extend", "hostids": "%s" % hid,
                                              "time_from": "%s" % time_from, "time_till": "%s" % time_till, "id": 1})
    for sub in history['result']:
        datalist.append(sub['value'])
    return datalist


def threading_controller():
    cpu_month_data = []
    memory_month_data = []
    zbx = ZabbixInfoEsxi()
    hostids = zbx.get_host_id()

    cpu_usage_itemids = zbx.get_itemid_from_item(hostids, "vmware.hv.cpu.usage[{$URL},{HOST.HOST}]")
    memory_useage_itemids = zbx.get_itemid_from_item(hostids, "vmware.hv.memory.used[{$URL},{HOST.HOST}]")

    for oneday in handler_datetime():
        time_from, time_till = oneday
        for number in xrange(0, len(hostids)):
            print "from: %s to: %s hostid: %s cpu: %s memory: %s" % (time_from, time_till, hostids[number],
                                                                     cpu_usage_itemids[number], memory_useage_itemids[number])
            cpu_day_data = cpu_usage_history_data(hid=hostids[number], itemid=cpu_usage_itemids[number],
                                                  time_from=time_from, time_till=time_till)
            cpu_month_data.append(cpu_day_data)
            memory_day_data = memory_usage_history_data(hid=hostids[number], itemid=memory_useage_itemids[number],
                                                        time_from=time_from, time_till=time_till)
            memory_month_data.append(memory_day_data)
    print cpu_month_data, memory_month_data
    return cpu_month_data, memory_month_data


def handler_datetime():
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
    threading_controller()
    # zbx = ZabbixInfoEsxi()
    # hostids = zbx.get_host_id()
    # pprint.pprint(hostids)
    #
    # cpu_usage_itemids = zbx.get_itemid_from_item(hostids, "vmware.hv.cpu.usage[{$URL},{HOST.HOST}]")
    # memory_useage_itemids = zbx.get_itemid_from_item(hostids, "vmware.hv.memory.used[{$URL},{HOST.HOST}]")
    # # hard_free_itemids = zbx.get_itemid_from_item(hostids,
    # #                                              "vmware.hv.datastore.size[{$URL},{HOST.HOST},datastore1,pfree]")
    # pprint.pprint(cpu_usage_itemids)