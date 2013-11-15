'''
    MSyncDev for XBMC
    
    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.
    
    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''

#import xbmc
#import xbmcaddon
#import xbmcnotify

import re
import os
import sys
import subprocess
import threading 
import Queue
import time
import pty

KNOWN_FILE = ".MSyncDev_known"

def caller(command, use_pty=True):
  if use_pty:
    master, slave = pty.openpty()
    proc = subprocess.Popen(command, stdout=slave, stderr=subprocess.STDOUT, stdin=subprocess.PIPE, close_fds=True)
  else:
    return subprocess.check_output(command, stderr=subprocess.PIPE)
  return os.fdopen(master)

class MyDevice(object):
  def __init__(self, 
 
class UdevListener(threading.Thread): 
  Eventq = Queue.Queue()
  def __init__(self,): 
    threading.Thread.__init__(self)
    self.udev_re = re.compile(r'UDEV\s+\[\d+\.\d+\]\s+(?P<action>\S+)\s+\S+/block/(?P<dev>\S+)\s+\(block\)')
 

  def dev_remove(self, event):
    """doin device stuff on remove"""
    return event

  def useable_dev(self, dev):
    """ probe if device is useable for xbmc """
    if dev['ID_BUS'] == "usb" \
      and dev['ID_USB_DRIVER'] == "usb-storage" \
      and dev['ID_TYPE'] == "disk":
      return True
    
  def dev_add(self, event):
    command = ["/sbin/udevadm", "info", "--name=%s" % (event['dev']), "--query=property" ] 
    stdout = caller(command, use_pty=False)
    print "getting info from device"
    tmp_dict = {}
    for line in stdout.splitlines():
      if not line or line == "":
        break
      k,v = line.split('=')
      tmp_dict[k] = v

    if self.useable_dev(tmp_dict):
      event.update(tmp_dict)
      useable_keys = ["DEVNAME", "ID_VENDOR", "ID_MODEL", "ID_FS_UUID" ]
      for key in useable_keys:
        event[key] = tmp_dict[key]

    return event
      

  def run(self): 
    command = [ "/sbin/udevadm", "monitor", "--udev", "--subsystem-match=block" ]
    stdout = caller(command)
    while True:
      line = stdout.readline()
      if line and not "": 
        eventmatch = re.search(self.udev_re, line)
        if eventmatch:
          event = eventmatch.groupdict()
          event['date'] = time.strftime("%X")
          if event['action'] == "add": 
            event = self.dev_add(event)
          elif event['action'] == "remove":
            event = self.dev_remove(event)
          if event:
            UdevListener.Eventq.put(event)
    stdout.close()

def get_mount(devname):
  PROC_M = "/proc/mounts"
  for l in open(PROC_M, "r"):
    mp = l.split(" ")[1]
    if mp == devname:
      return l.split(" ")[2]

def register_device(mountpoint, dev_id):
  def write_id():
    fh = open(f, "w+")
    fh.write(dev_id)
    fh.close()

  f = mountpoint + "/" + KNOWN_FILE
  if os.path.isfile(f):
    for l in open(f, "r"):
      if l == dev_id:
        return (False, True)
      else:
        write_id()
        return (False, False)
  else:
    write_id()
    return(True, False)

def is_writable(name):
  """Return true if the file is writable from the current user
  """
  return os.access(name, os.W_OK)

def new_device(dev):
  """Managing stuff for new detected device"""
  mountpoint = get_mount(dev['DEVNAME'])
  if mountpoint:
    dev['is_mounted'] = True
  else:
    dev['is_mounted'] = False
    return

  if is_writable(mountpoint):
    dev['readonly'] = False
    is_new, is_registered = register_device(mountpoint, dev['ID_FS_UUID'])
    dev['is_new'] = is_new
    dev['is_registered'] = is_registered
  else:
    dev['readonly'] = True

def main():
  mylistener = UdevListener() 
  mylistener.daemon = True
  mylistener.start()
  print "Start queue listening"
  while mylistener.isAlive():
    if not UdevListener.Eventq.empty():
      event = UdevListener.Eventq.get()
      print "%s: DEVICE event occured: Device: %s Action: %s" % (event['date'], event['dev'], event['action'])
      if event['action'] == "add":
        time.sleep(0.5)
        new_device(event)

    time.sleep(0.5)
  print "UdevListener dies"

if __name__ == "__main__":
  main()

#settings = xbmcaddon.Addon(id='script.service.MSyncDev')
#incomingdir = settings.getSetting("incomingdir")
#song_count = settings.getSetting("song_count")
#is_activated = settings.getSetting("active")

#while (not xbmc.abortRequested):
#  xbmc.sleep(100)
