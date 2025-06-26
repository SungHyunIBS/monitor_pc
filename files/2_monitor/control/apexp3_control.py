#!/opt/monitor/venv/bin/python
import sys
import time
import logging
from pathlib import Path
import json
import serial
import os

import datetime
from datetime import datetime
from pyModbusTCP.client import ModbusClient

def read_device_status(client):
    regs1 = client.read_holding_registers( 2, 1)
    dataset1 = {}
    for i in range(0,16):
        data = regs1[0] & 0x1
        dataset1[i] = data
        regs1[0] = regs1[0] >> 1

    regs2 = client.read_holding_registers(55, 1) 
    dataset2 = {}
    for i in range(0,16):
        data = regs2[0] & 0x1
        dataset2[i] = data
        regs2[0] = regs2[0] >> 1

    print("Running               ", dataset1[0])
    print("Sampling              ", dataset1[1])
    print("New Data              ", dataset1[2])
    print("Device Error          ", dataset1[3])
    print("Laser Status          ", dataset1[11])
    print("Flow Status           ", dataset1[12])
    print("Service Status        ", dataset1[13])
    print("Threshold H           ", dataset1[14])
    print("Threshold L           ", dataset1[15])
    print("Laser Power           ", dataset2[0])
    print("Laser Current         ", dataset2[1])
    print("Laser Supply          ", dataset2[2])
    print("Laser Life            ", dataset2[3])
    print("No Flow Status        ", dataset2[4])
    print("Photoamp Supply Status", dataset2[5])
    print("Background Status     ", dataset2[6])
    print("Photodiode Status     ", dataset2[7])
    print("Calibration Due Date  ", dataset2[8])
    
def read_serial(client):
    regs = client.read_holding_registers(4, 2)
    serial = (regs[0] << 16) + regs[1]
    print(regs[0], regs[1], serial)

def read_prod(client):
    regs = client.read_holding_registers(6, 8)
    for i in range(len(regs)):
        for j in range (2):
            if(j == 0):
                data = (regs[i] >> 8) & 0xFF
            else:
                data = regs[i] & 0xFF

            print(i, j, chr(data))

def read_model(client):
    regs = client.read_holding_registers(14, 8)
    for i in range(len(regs)):
        for j in range (2):
            if(j == 0):
                data = (regs[i] >> 8) & 0xFF
            else:
                data = regs[i] & 0xFF

            print(i, j, chr(data))

def read_record_count(client):
    # need to study
    regs = client.read_holding_registers(23, 3)
    print(regs)

def read_time(client):

    regs  = client.read_holding_registers(26, 2)
    utime = (regs[0] << 16) + regs[1]
    stime = datetime.utcfromtimestamp(utime)
    ttime = stime.strftime("%s")

    print(stime, ttime)

def read_flowunit(client):

    regs = client.read_holding_registers(40, 2)
    print(regs)
    # data = (regs[0] << 16) + regs[1]
    # for i in range(0, 4):
    #     out = (data >> (24 - i * 8)) & 0xFF
    #     print(chr(out), end="")
    # print()

def read_setting(client):

    regs   = client.read_holding_registers(28,2)
    delay  = (regs[0] << 16) + regs[1]
    regs   = client.read_holding_registers(30,2)
    hold   = (regs[0] << 16) + regs[1]
    regs   = client.read_holding_registers(32,2)
    sample = (regs[0] << 16) + regs[1]
    print("delay  : ", delay)
    print("hold   : ", hold)
    print("sample : ", sample)

def write_setting(client, delay, hold, sample):

    client.write_single_register(29, delay)
    client.write_single_register(31, hold)
    client.write_single_register(33, sample)
    
def run_start(client):
    client.write_single_register(1, 11)
            
def run_stop(client):
    client.write_single_register(1, 12)

def save_config(client):
    client.write_single_register(1, 1)

def clear_buffer(client):
    client.write_single_register(1, 3)

def cmd_1(client, val):
    client.write_single_register(1, val)

def read_all_4xx(client):

    data = {}
    for i in range(0, 999):
        flag = 0
        reg  = client.read_holding_registers(i*10, 10)
        for j in range(0, 10):
            if(reg[j] == 0):
                flag = flag | 0
            else:
                flag = flag | 1

        if(flag == 1):
            flag = 0
            for j in range(0,10):
                data[j] = hex(reg[j])
            print(i*10+40001, data)
            
def read_all_3xx(client):

    data = {}
    for i in range(0, 999):
        flag = 0
        reg  = client.read_input_registers(i*10, 10)
        for j in range(0, 10):
            if(reg[j] == 0):
                flag = flag | 0
            else:
                flag = flag | 1

        if(flag == 1):
            flag = 0
            for j in range(0,10):
                data[j] = hex(reg[j])
            print(i*10+30001, data)
            
def read_dust(client):

    data = {}
    reg  = client.read_input_registers(1008, 8)
    d0d3  = reg[0] * 65536 + reg[1]
    d0d5  = reg[2] * 65536 + reg[3]
    d5d0  = reg[4] * 65536 + reg[5]
    d10d0 = reg[6] * 65536 + reg[7]
    print(d0d3, d0d5, d5d0, d10d0)
            
def main():

    c = ModbusClient(host = "172.16.1.71", port =  502)
    #read_dust(c)
    #read_all_4xx(c)
    #write_setting(c, 0, 0, 60)
    run_stop(c)
    #read_device_status(c)
    #print()
    #read_serial(c)
    
if __name__ == '__main__':
    main()
