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

import xbmc
import xbmcaddon
import xbmcnotify

import dbus
import threading 
import Queue
 
class UdevListener(threading.Thread): 
  Eventq = Queue.Queue()
  def __init__(self,): 
    threading.Thread.__init__(self)
    self.command = [ "/sbin/udevadm", "monitor", "--udev", "--subsystem-match=block" ]
 
  def run(self): 
    proc = subprocess.Popen(self.command, stdout=subprocess.PIPE)
    while True:
        nextline = proc.stdout.readline()
        if nextline == '' and proc.poll() != None:
            break
        UdevListener.Eventq.put(nextline)

settings = xbmcaddon.Addon(id='script.service.MSyncDev')
incomingdir = settings.getSetting("incomingdir")
song_count = settings.getSetting("song_count")

bus = dbus.SystemBus()
xbmc.log(bus.list_names())
#service = checkdevice.Service()
#while (not xbmc.abortRequested):
#  xbmc.sleep(100)
