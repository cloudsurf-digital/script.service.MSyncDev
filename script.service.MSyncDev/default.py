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
import fnmatch
import pty


def caller(command, use_pty=True):
  if use_pty:
    master, slave = pty.openpty()
    proc = subprocess.Popen(command, stdout=slave, stderr=subprocess.STDOUT, stdin=subprocess.PIPE, close_fds=True)
  else:
    return subprocess.check_output(command, stderr=subprocess.PIPE)
  return os.fdopen(master)

class MyDevice(object):
  KNOWN_FILE = ".MSyncDev"
  MUSIC_SEARCHPATTERN = "*.mp3"
  def __init__(self, event):
    self.activate_time = event['date']
    self.devname = event['dev']
    self.mountpoint = self.get_mount()
    print self.mountpoint
    self.fs_uuid = event['ID_FS_UUID']
    self.readonly = not bool(self.is_writable())
    self.vendor = event['ID_VENDOR']
    self.model = event['ID_MODEL']
    self.is_new, self.is_registered = self.register_device()
    self.files_on_device = self.music_scan()
    print self.files_on_device


  def music_scan(self):
    """os.walk """
    matches = []
    for root, dirs, filenames in os.walk(self.mountpoint):
      for filename in fnmatch.filter(filenames, MyDevice.MUSIC_SEARCHPATTERN):
        matches.append(os.path.join(root, filename))
    return matches

  def music_sync(self):
    """syncs music to xbmc library"""

  def get_mount(self):
    PROC_M = "/proc/mounts"
    for l in open(PROC_M, "r"):
      #import pdb; pdb.set_trace()
      dev = l.split(" ")[0]
      mp = l.split(" ")[1]
      if dev == "/dev/" + self.devname:
        return mp

  def is_mounted(self):
    if self.mountpoint:
      return True
    return False
  
  def is_writable(self):
    """Return true if the file is writable from the current user
    """
    return os.access(self.mountpoint, os.W_OK)

  def register_device(self):
    def write_id():
      fh = open(f, "w")
      fh.write("%s %s" % (time.strftime("%X"), self.fs_uuid))
      fh.close()
  
    f = self.mountpoint + "/" + MyDevice.KNOWN_FILE
    if os.path.isfile(f):
      for l in open(f, "r"):
        if l.split(" ")[1] == self.fs_uuid:
          return (False, True)
        else:
          write_id()
          return (False, False)
    else:
      write_id()
      return(True, False)


class UdevListener(threading.Thread): 
  Eventq = Queue.Queue()
  def __init__(self,): 
    threading.Thread.__init__(self)
    self.udev_re = re.compile(r'UDEV\s+\[\d+\.\d+\]\s+(?P<action>\S+)\s+\S+/block/(\S+/)?(?P<dev>\S+)\s+\(block\)')
 

  def dev_remove(self, event):
    """doin device stuff on remove"""
    return event

  def useable_dev(self, dev):
    """ probe if device is useable for xbmc """
    if dev['ID_BUS'] == "usb" \
      and dev['ID_USB_DRIVER'] == "usb-storage" \
      and "ID_FS_UUID" in dev \
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
    else:
      event = None

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


def main():
  mylistener = UdevListener() 
  mylistener.daemon = True
  mylistener.start()
  print "Start queue listening"
  my_devices = []
  while mylistener.isAlive():
    if not UdevListener.Eventq.empty():
      event = UdevListener.Eventq.get()
      print "%s: DEVICE event occured: Device: %s Action: %s" % (event['date'], event['dev'], event['action'])
      if event['action'] == "add":
        time.sleep(0.5)
        my_devices.append(MyDevice(event))
      elif event['action'] == "remove":
        for dev in my_devices:
          if dev.devname == event['dev']: dev.remove()

        my_devices = [ dev for dev in my_devices if dev.devname != event['dev']]
        

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
