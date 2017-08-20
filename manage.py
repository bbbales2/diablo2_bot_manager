import sys
import os
import re
import numpy
import json
import time
import argparse
import subprocess
import shutil

parser = argparse.ArgumentParser(description='Manage a bunch of running Diablo2 bots')
parser.add_argument('Ai', type = str, help = 'Python file that runs AI script')
parser.add_argument('outputFolder', type = str, default = 1, help = 'Output folder where ')
parser.add_argument('--password', type = str, default = 'wackamole', help = 'Default password for Diablo 2 vnc server (I use wackamole)')
parser.add_argument('--input', type = str, default = '', help = 'Optional file to pass to bots')
parser.add_argument('--N', type = int, default = 1, help = 'Number of copies of bot to run')
parser.add_argument('--T', type = float, default = 1, help = 'Maximum time to run bot for')

args = parser.parse_args()

os.mkdir(args.outputFolder)

N = args.N

for i in range(0, N):
    print "Running bot {0} of {1}".format(i, N)
    subprocess.Popen('vncserver -localhost -geometry 640x480 -depth 16 -deferupdate 1 :1', shell = True).communicate()
    print "VNC server started on port localhost:1"

    time.sleep(5)
    stdout, _ = subprocess.Popen('ps -e | grep Game', shell = True, stdout = subprocess.PIPE, stderr = subprocess.PIPE).communicate()

    print stdout
    pid = stdout.strip().split()[0]
    print "Diablo2 game found at pid {0}".format(pid)

    handle = subprocess.Popen('python diablo2_vnc_viewer/vncviewer.py --bot {0} --host localhost --display 1 --fast --password {1} --botDataFile {2} --bogLog {3}/{4}'.format(args.Ai, args.password, args.input, args.outputFolder, i), shell = True)
    startTime = time.time()
    print "VNC bot started at time = {0}".format(startTime)
    
    while True:
        currentTime = time.time()
        if handle.poll() is not None:
            break
        if currentTime - startTime > args.T:
            handle.terminate()
            handle.wait()
            break
        time.sleep(0.1)
        print "Polling bot ({0})".format(currentTime)
    print "Bot finished"
        
    subprocess.Popen('vncserver -kill :1', shell = True).communicate()
    print "Killing VNC server"
