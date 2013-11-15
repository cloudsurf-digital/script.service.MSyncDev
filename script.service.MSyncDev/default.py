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
import sys
import subprocess
import threading 
import Queue
import time
 
class UdevListener(threading.Thread): 
  """
  UDEV  [259613.929124] remove   /devices/pci0000:00/0000:00:1d.0/usb2/2-1/2-1.7/2-1.7:1.0/host7/target7:0:0/7:0:0:0/block/sdb (block)
  UDEV  [259619.580705] add      /devices/pci0000:00/0000:00:1d.0/usb2/2-1/2-1.7/2-1.7:1.0/host8/target8:0:0/8:0:0:0/block/sdb (block)
  """
  Eventq = Queue.Queue()
  def __init__(self,): 
    threading.Thread.__init__(self)
    self.command = [ "/sbin/udevadm", "monitor", "--udev", "--subsystem-match=block" ]
    self.udev_re = re.compile(r'UDEV\w+\[\d+\.\d+\]\w+(?P<action>\W+)\w+.*?/block/(?P<dev>\W+)\W+\(block\)')
 
  def run(self): 
    UdevListener.Eventq.put({'date' : time.strftime("%X"),
                             'action' : "started dev monitor",
                             'dev': None })
    proc = subprocess.Popen(self.command, stdout=subprocess.PIPE)
    
    while True:
      line = proc.stdout.readline()
      #proc.stdout.fush()
      UdevListener.Eventq.put({'date' : time.strftime("%X"),
                               'action' : "found: " + line,
                               'dev': None })
      eventmatch = re.search(self.udev_re, line)
      if eventmatch:
        event = eventmatch.groupdict()
        event['date'] = time.strftime("%X")
        UdevListener.Eventq.put(event)
      else:
        UdevListener.Eventq.put({'date' : time.strftime("%X"),
                                 'action' : line + "not matched",
                                 'dev': None })



def main():
  mylistener = UdevListener() 
  mylistener.daemon = True
  mylistener.start()
  print "Start queue listening"
  while True:
    if not UdevListener.Eventq.empty():
      event = UdevListener.Eventq.get()
      print "DEVICE event occured: Device: %s Action: %s" % (event['dev'], event['action'])
    time.sleep(1)

if __name__ == "__main__":
  main()

#settings = xbmcaddon.Addon(id='script.service.MSyncDev')
#incomingdir = settings.getSetting("incomingdir")
#song_count = settings.getSetting("song_count")
#is_activated = settings.getSetting("active")

#while (not xbmc.abortRequested):
#  xbmc.sleep(100)
