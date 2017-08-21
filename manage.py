import sys
import os
import re
import numpy
import json
import time
import argparse
import subprocess
import shutil
import signal
import sys

parser = argparse.ArgumentParser(description='Manage a bunch of running Diablo2 bots')
parser.add_argument('Ai', type = str, help = 'Python file that runs AI script')
parser.add_argument('outputFolder', type = str, default = 1, help = 'Output folder where ')
parser.add_argument('-N', type = int, default = 1, help = 'Number of copies of bot to run')
parser.add_argument('-T', type = float, default = -1, help = 'Maximum time to run bot for')
parser.add_argument('--password', type = str, default = 'wackamole', help = 'Default password for Diablo 2 vnc server (I use wackamole)')
parser.add_argument('--data', type = str, default = '', help = 'Optional file to pass to bots')

if os.path.exists(os.path.expanduser("~/.vnc/xstartup")):
    print "Save your ~/.vnc/xstartup file somewhere and delete the original before running this script"
    exit(-1)

args = parser.parse_args()

os.mkdir(args.outputFolder)

N = args.N

def cleanup(signal, frame):
    subprocess.Popen('vncserver -kill :1', shell = True).communicate()
    print "Killing VNC server"

    try:
        os.remove(os.path.expanduser("~/.vnc/xstartup"))
    except:
        pass

    try:
        handle.kill()
    except:
        pass

    exit(-1)
    
signal.signal(signal.SIGINT, cleanup)

subprocess.Popen('vncserver -kill :1', shell = True).communicate()
print "Killing existing VNC server if it exists"
for i in range(0, N):
    print "Running bot {0} of {1}".format(i, N)
    f = open(os.path.expanduser("~/.vnc/xstartup"), "w")
    f.write("#!/bin/sh\n")
    f.write("wine ~/.wine/drive_c/Program\ Files\ \(x86\)/Diablo\ II/Diablo\ II.exe -w -ns\n")
    f.close()
    os.chmod(os.path.expanduser("~/.vnc/xstartup"), 0775)
    cmd = 'vncserver -localhost -geometry 640x480 -depth 16 -deferupdate 1 :1'
    print "Executing: '{0}'".format(cmd)
    subprocess.Popen(cmd, shell = True).communicate()
    print "VNC server started on port localhost:1"

    startTime = time.time()
    while True:
        stdout, _ = subprocess.Popen('ps -e | grep Game', shell = True, stdout = subprocess.PIPE, stderr = subprocess.PIPE).communicate()

        try:
            pid = stdout.strip().split()[0]
            break
        except:
            pass

        if time.time() - startTime > 5.0:
            print "Diablo 2 game didn't start within 5 seconds"
            exit(-1)
    print "Diablo2 game found at pid {0}".format(pid)
    os.remove(os.path.expanduser("~/.vnc/xstartup"))
    
    cmd = 'python diablo2_vnc_viewer/vncviewer.py --depth=32 --bot={0} --host=localhost --display=1 --fast --password={1} --botDataFile={2} --botLog={3}/{4}.log --gamePid={5}'.format(args.Ai, args.password, args.data, args.outputFolder, i, pid)
    print "Executing: '{0}'".format(cmd)
    handle = subprocess.Popen(cmd, shell = True)
    startTime = time.time()
    print "VNC bot started at time = {0}".format(startTime)
    
    while True:
        currentTime = time.time()
        if handle.poll() is not None:
            break
        if args.T > 0 and currentTime - startTime > args.T:
            handle.terminate()
            handle.wait()
            break
        time.sleep(0.1)
    print "Bot finished"

    subprocess.Popen('vncserver -kill :1', shell = True).communicate()
    print "Killing VNC server"
