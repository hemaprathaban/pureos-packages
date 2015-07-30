#!/usr/bin/env python
'''
Based on code by Tony "Fragadelic" Brijeski

 Copyright 2015  Casey Parker <casey.parker@puri.sm>

This version is for PureOS 1.0 Arcturus - it may work with other distros.
'''

from os import geteuid, path, waitpid
from shutil import copyfile
from sys import exit
from subprocess import *
import datetime

''' definitions '''
def configSetup():
  '''set some values and make some dirs'''
  now = datetime.datetime.now()
  ISODATE = now.strftime("%Y%m%d")
  LIVEUSER = ("pureos")
  BASEWORKDIR = ("/home/pureos-iso")
  global WORKDIR
  WORKDIR = ("/home/pureos-iso/work")
  LIVECDLABEL = ("PureOS GNU Linux")
  CDBOOTTYPE = ("ISOLINUX")
  LIVECDURL = ("http://www.puri.sm")
  SQUASHFSOPTS = ("-no-recovery -always-use-fragments -b 1M -no-duplicates")
  CUSTOMISO = ("PureOS-{0}.iso".format(ISODATE))
  if path.isdir(WORKDIR) == True:
    call(["rm","-rf",WORKDIR])
  call(["mkdir","-p",WORKDIR])
  global LOGFILE
  LOGFILE = ("%s/make-pureos-iso.log" % WORKDIR)
  if path.exists(LOGFILE) == True:
    call(["rm","-f",LOGFILE])
  call(["touch",LOGFILE])

def writeLog(MESSAGE):
  with open(LOGFILE,"a") as log:
    print>>log,MESSAGE
    print(MESSAGE)
    return(0)
  return("Log file missing?")

def writeFirstBoot():
  '''create make-pureos-iso-firstboot script'''
  data = ("#! /bin/sh","### BEGIN INIT INFO","# Provides:          make-pureos-iso-firstboot",
	  "# Required-Start:    \$remote_fs \$syslog \$all",
	  "# Required-Stop:","# Default-Start:     2 3 4 5",
	  "# Default-Stop:      0 1 6",
	  "# Short-Description: Run firstboot items for pureos after install",
	  "### END INIT INFO","",
	  "PATH=/sbin:/usr/sbin:/bin:/usr/bin:/usr/local/bin:/usr/local/sbin",
	  "",". /lib/init/vars.sh",". /lib/lsb/init-functions","",
	  "do_start() {","        #REM302",
	  """        if [ "\`cat /proc/cmdline | grep casper\`" = "" ]; then""",
	  '            [ "\$VERBOSE" != no ] && log_begin_msg "Running make-pureos-iso-firstboot"',
	  "            (sleep 60 && update-rc.d -f make-pureos-iso-firstboot remove) &",
	  "            sed -i -e 's/root:x:/root:!:/g' /etc/shadow",
	  "            rm -rf /home/*/Desktop/ubiquity*.desktop",
	  "            #Place your custom commands below this line",
	  "","            #Place your custom commands above this line",
	  "ES=\$?","""[ "\$VERBOSE" != no ] && log_end_msg \$ES""",
	  "return \$ES","        fi","}","",'case "\$1" in',"    start)",
	  "        do_start","        ;;","    restart|reload|force-reload)",
	  '''        echo "Error: argument '\$1' not supported" >&2''',
	  "        exit 3","        ;;","    stop)","        ;;",
	  "    *)",'        echo "Usage: \$0 start|stop" >&2',
	  "        exit 3","        ;;","esac")
  call(["touch","/etc/init.d/make-pureos-iso-firstboot"])
  writeLog("Writing make-pureos-iso-firstboot...")
  with open("/etc/init.d/make-pureos-iso-firstboot","w") as firstBoot:
    for line in data:
      print>>firstBoot,line
    writeLog("OK")
    return(0)
  exit("Something went wrong in writeFirstBoot()")

def buildCDFS():
  ''' create cdfs filesystem '''
  call(["chmod","755","/etc/init.d/make-pureos-iso-firstboot"])
  call(["update-rc.d","make-pureos-iso-firstboot","defaults"])
  
  writeLog("Checking filesystem type of the Working Folder")
  
  ''' popularity-contest causes a problem when installing with ubiquity '''
  writeLog("Making sure popularity contest is not installed")
  call(["apt-get","remove","-y","-q","popularity-contest"])
  
  ''' load the ubiquity frontend '''
  writeLog("Installing the Ubiquity GTK frontend")
  call(["apt-get","install","-y","-q","ubiquity-frontend-gtk","ubiquity-slideshow-pureos"])
  
  ''' create lightdm.conf if it doesn't already exist '''
  if not path.exists("/etc/lightdm/lightdm.conf") == True:
    call(["touch","/etc/lightdm/lightdm.conf"])
  
  ''' prevent the installer from changing the apt sources.list '''
  if not path.exists("/usr/share/ubiquity/apt-setup.saved") == True:
    copyfile("/usr/share/ubiquity/apt-setup","/usr/share/ubiquity/apt-setup.saved")
  
  ''' Create the CD tree in $WORKDIR/ISOTMP '''
  writeLog("checking for {0}".format(WORKDIR))
  if path.isdir("{0}/dummysys".format(WORKDIR)):
    removeList = ["/dummysys/var/*",
		  "/dummysys/run/*",
		  "/ISOTMP/isolinux",
		  "/ISOTMP/grub",
		  "/ISOTMP/.disk"]
    for removeMe in removeList:
      call(["rm","-rf","{0}{2}".format(WORKDIR,removeMe)])
  else:
    writeLog("Creating {0} folder tree".format(WORKDIR))
    createList = ["/ISOTMP/casper",
		  "/ISOTMP/preseed",
		  "/ISOTMP/isolinux",
		  "/ISOTMP/install",
		  "/ISOTMP/.disk",
		  "/dummysys/dev",
		  "/dummysys/etc",
		  "/dummysys/proc",
		  "/dummysys/tmp",
		  "/dummysys/sys",
		  "/dummysys/mnt",
		  "/dummysys/media"
		  "/dummysys/cdrom",
		  "/dummysys/var"]
    for makeMe in createList:
      call(["mkdir","-p","{0}{1}".format(WORKDIR,makeMe)])
    if path.isdir("/run") == True:
      call(["mkdir","-p","{0}/dummysys/run".format(WORKDIR)])
      call(["chmod","ug+rwx,o+rwt","{0}/dummysys/tmp".format(WORKDIR)])
  
  writeLog("Copying /var and /etc ...")
  call(["rsync",
	"--exclude='*.log.*'",
	"--exclude='*.pid'",
	"--exclude='*.bak'",
	"--exclude='*.[0-9].gz'",
	"--exclude='*.deb'",
	"--exclude='kdecache*'"
	"/var/.","{0}/dummysys/var/.".format(WORKDIR)])
  call(["rsync","/etc/.","{0}/dummysys/etc/.".format(WORKDIR)])

  writeLog("Cleaning up after myself...")
  removeList = ["/etc/X11/xorg.conf*",
	      "/etc/hosts",
	      "/etc/hostname",
	      "/etc/timezone",
	      "/etc/mtab*",
	      "/etc/fstab",
	      "/etc/udev/rules.d/70-persistent*",
	      "/etc/cups/ssl/server.crt",
	      "/etc/cups/ssl/server.key",
	      "/etc/ssh/ssh_host_rsa_key",
	      "/etc/ssh/ssh_host_rsa_key.pub",
	      "/etc/ssh/ssh_host_dsa_key",
	      "/etc/ssh/ssh_host_dsa_key.pub",
	      "/var/lib/dbus/machine-id",
	      "/etc/group",
	      "/etc/passwd",
	      "/etc/shadow",
	      "/etc/shadow-",
	      "/etc/gshadow",
	      "/etc/gshadow-",
	      "/etc/wicd/wired-settings.conf",
	      "/etc/wicd/wireless-settings.conf",
	      "/etc/NetworkManager/system-connections/*",
	      "/etc/printcap",
	      "/etc/cups/printers.conf",
	      "/var/cache/gdm/*",
	      "/var/lib/sudo/*",
	      "/var/lib/AccountsService/users/*",
	      "/var/lib/kdm/*",
	      "/var/run/console/*",
	      "/etc/gdm/gdm.conf-custom",
	      "/etc/gdm/custom.conf"]
  for removeMe in removeList:
    call(["rm","-rf","{0}/dummysys/{1}".format(WORKDIR,removeMe)])
  
  call(["touch","{0}/dummysys/etc/printcap".format(WORKDIR)])
  
  p = Popen("echo" + " ''> {0}/dummysys/etc/cups/printers.conf".format(WORKDIR), shell=True)
  p = Popen("grep" + " '^[^:]*:[^:]*:[0-9]:' /etc/passwd > {0}/dummysys/etc/passwd".format(WORKDIR), shell=True)
  sts = waitpid(p.pid, 0)[1]
'''
grep '^[^:]*:[^:]*:[0-9]:' /etc/passwd > $WORKDIR/dummysys/etc/passwd
grep '^[^:]*:[^:]*:[0-9][0-9]:' /etc/passwd >> $WORKDIR/dummysys/etc/passwd
grep '^[^:]*:[^:]*:[0-9][0-9][0-9]:' /etc/passwd >> $WORKDIR/dummysys/etc/passwd
grep '^[^:]*:[^:]*:[3-9][0-9][0-9][0-9][0-9]:' /etc/passwd >> $WORKDIR/dummysys/etc/passwd
grep '^[^:]*:[^:]*:[0-9]:' /etc/group > $WORKDIR/dummysys/etc/group
grep '^[^:]*:[^:]*:[0-9][0-9]:' /etc/group >> $WORKDIR/dummysys/etc/group
grep '^[^:]*:[^:]*:[0-9][0-9][0-9]:' /etc/group >> $WORKDIR/dummysys/etc/group
grep '^[^:]*:[^:]*:[3-9][0-9][0-9][0-9][0-9]:' /etc/group >> $WORKDIR/dummysys/etc/group

grep '^[^:]*:[^:]*:[5-9][0-9][0-9]:' /etc/passwd | awk -F ":" '{print $1}'> $WORKDIR/tmpusers1
grep '^[^:]*:[^:]*:[1-9][0-9][0-9][0-9]:' /etc/passwd | awk -F ":" '{print $1}'> $WORKDIR/tmpusers2
grep '^[^:]*:[^:]*:[1-2][0-9][0-9][0-9][0-9]:' /etc/passwd | awk -F ":" '{print $1}'> $WORKDIR/tmpusers3
'''
''' end of definitions '''

call(["clear"])
print("\nPureOS ISO Mastering Utility")
print("= = = = = = = = = = = = = = = = = = =\n")
'''check that we're running as root before we do anything'''
if geteuid() != 0:
  print("You must run with sudo.\n")
  exit(1)

configSetup()

writeFirstBoot()

buildCDFS()

print("= = = = = = = = = = = = = = = = = = =\nFinished.\n")
exit(0)

