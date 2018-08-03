#!/usr/bin/python3

import os
import re
import shlex
import subprocess
import sys

def get_devices_byid(devDict):
  devdir = '/dev'
  diskiddir = "%s/disk/by-id" % devdir
  mylist = []
  diskidDevMapDic = {}

  if os.path.exists(diskiddir):
    mylist= os.listdir(diskiddir)

  for item in mylist:
    if item in devDict:
      itemPath = "%s/%s" % (diskiddir, item)
      devLetter = os.path.realpath(itemPath)
      diskidDevMapDic[item] = devLetter

  return diskidDevMapDic

def get_all_devices_byid():
  devdir = '/dev'
  diskiddir = "%s/disk/by-id" % devdir
  mylist = []
  diskidDevMapDic = {}

  if os.path.exists(diskiddir):
    mylist= os.listdir(diskiddir)

  for item in mylist:
    rxdev = re.search('^ata.+', item, re.I)
    if rxdev:
      rxpart = re.search('.+-part.+', item, re.I)
      if rxpart:
        continue
      else:
        itemPath = "%s/%s" % (diskiddir, item)
        devLetter = os.path.realpath(itemPath)
        diskidDevMapDic[devLetter] = item
  return diskidDevMapDic

def get_hdd_temp(device):
  cmd = "/usr/sbin/hddtemp"
  args = "%s" % device
  cmdArgs = "%s %s" % (cmd, args)
  proc = subprocess.Popen(shlex.split(cmdArgs) ,stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
  output, error = proc.communicate()
  output = output.decode('utf-8')
  output = output.split(':')
  hddtemp = output[-1]
  hddtemp = hddtemp.replace('\n', '')
  return hddtemp

def get_zpools():
  poolList = []
  cmd = '/sbin/zpool'
  args = 'status'
  cmdArgs = "%s %s" % (cmd, args)
  proc = subprocess.Popen(shlex.split(cmdArgs) ,stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
  output, error = proc.communicate()
  output = output.decode('utf-8')

  output = output.split('\n')

  for line in output:
    rxpool = re.match('.+pool:\s+(.+)$', line, re.I)
    if rxpool:
      pool = rxpool.group(1)
      poolList.append(pool)

  return poolList
      
#-------------- MAIN --------------#

poolList = get_zpools()

for pool in poolList:
  cmd='/sbin/zpool'
  args = "status %s " % pool
  cmdArgs = "%s %s" % (cmd, args)

  proc = subprocess.Popen(shlex.split(cmdArgs) ,stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
  output, error = proc.communicate()
  output = output.decode('utf-8')

  output = output.split('\n')
  devList = []
  devDict = {}
  allDevDict = {}

  for entry in output:
    rx = re.match('^\s+(ata-\w+-\w+|\d+)\s+(\w+)\s+\d+\s+\d+.+', entry, re.I)
    if rx:
      name = rx.group(1)
      status = rx.group(2)
      devDict[name] = status

  devByIdDict = get_devices_byid(devDict)

  print("                    ZPOOL %s      " % pool)
  print("------------------------------------------------------------------------------")
  print("   Device by ID                                               Device Name")
  print("------------------------------------------------------------------------------")
  for devid, devname in devByIdDict.items():
    print("{:60} {:25}".format(devid, devname))
  print("------------------------------------------------------------------------------")

allDevDict = get_all_devices_byid()
allDevList = []

for key in allDevDict.keys():
  allDevList.append(key)

allDevList.sort()
print("")
print("All devices to dev names")
print("   Device by ID                            Device Name          Temp")
print("------------------------------------------------------------------------------")
for key in allDevList:
  devname = key
  if key in allDevDict:
    devid = allDevDict[key]
    hddtemp = get_hdd_temp(devname)
    if devname == '/dev/sr0':
      print("{:43} {:18}".format(devid, devname))
    else:
      print("{:43} {:18} {:4}".format(devid, devname, hddtemp))
print("------------------------------------------------------------------------------")



