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
import fcntl
import pty

def caller(command, use_pty=True):
  if use_pty:
    master, slave = pty.openpty()
    proc = subprocess.Popen(command, stdout=slave, stderr=subprocess.STDOUT, stdin=subprocess.PIPE, close_fds=True)
  else:
    return subprocess.check_output(command, stderr=subprocess.PIPE)
  return os.fdopen(master)

 
class UdevListener(threading.Thread): 
  """
  UDEV  [259613.929124] remove   /devices/pci0000:00/0000:00:1d.0/usb2/2-1/2-1.7/2-1.7:1.0/host7/target7:0:0/7:0:0:0/block/sdb (block)
  UDEV  [259619.580705] add      /devices/pci0000:00/0000:00:1d.0/usb2/2-1/2-1.7/2-1.7:1.0/host8/target8:0:0/8:0:0:0/block/sdb (block)
  """
  Eventq = Queue.Queue()
  def __init__(self,): 
    threading.Thread.__init__(self)
    self.udev_re = re.compile(r'UDEV\s+\[\d+\.\d+\]\s+(?P<action>\S+)\s+\S+/block/(?P<dev>\S+)\s+\(block\)')
 

  def dev_remove(self, event):
    return event
  def dev_add(self, event):
    """
E: ID_SERIAL=JetFlash_Transcend_16GB_201651680-0:0
E: ID_SERIAL_SHORT=201651680
E: ID_TYPE=disk
E: ID_USB_DRIVER=usb-storage
E: ID_USB_INTERFACES=:080650:
E: ID_USB_INTERFACE_NUM=00
E: ID_VENDOR=JetFlash
E: ID_VENDOR_ENC=JetFlash
E: ID_VENDOR_ID=8564
E: MAJOR=8
E: MINOR=16
    """
    command = ["/sbin/udevadm", "info", "--name=%s" % (event['dev']), "--query=property" ] 
    stdout = caller(command, use_pty=False)
    print "getting info from device"
    tmp_dict = {}
    for line in stdout.splitlines():
      if not line or line == "":
        break
      k,v = line.split('=')
      tmp_dict[k] = v
    event.update(tmp_dict)
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
          else:
            event['info'] = "unknown event"
          UdevListener.Eventq.put(event)
    stdout.close()

def main():
  mylistener = UdevListener() 
  mylistener.daemon = True
  mylistener.start()
  print "Start queue listening"
  while mylistener.isAlive():
    if not UdevListener.Eventq.empty():
      event = UdevListener.Eventq.get()
      print "%s: DEVICE event occured: Device: %s Action: %s" % (event['date'], event['dev'], event['action'])
      print event
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
