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
import select

parser = argparse.ArgumentParser(description='Manage a bunch of running Diablo2 bots')
parser.add_argument('--Ai', type = str, default = '', help = 'Python file that runs AI script')
parser.add_argument('--outputFolder', type = str, default = 'output', help = 'Output folder where result logs are stored')
parser.add_argument('-N', type = int, default = 1, help = 'Number of copies of bot to run')
parser.add_argument('-T', type = float, default = -1, help = 'Maximum time to run bot for')
parser.add_argument('--password', type = str, default = 'wackamole', help = 'Default password for Diablo 2 vnc server (I use wackamole)')
parser.add_argument('--data', type = str, default = '', help = 'Optional file to pass to bots')
parser.add_argument('--ignore', default = False, action = 'store_true', help = 'Overwrite existing output and vnc config')
parser.add_argument('--headless', default = False, action = 'store_true', help = 'Run bots in headless mode -- no pygame video output')
parser.add_argument('--suppress', default = False, action = 'store_true', help = 'Suppress messages printed from vncviewer')

args = parser.parse_args()

if os.path.exists(os.path.expanduser("~/.vnc/xstartup")):
    if not args.ignore:
        print "~/.vnc/xstartup script exists. Either run with --ignore or save your ~/.vnc/xstartup file somewhere and delete the original before running this script"
        exit(-1)

if os.path.exists(args.outputFolder):
    if not args.ignore:
        print "Output folder '{0}' exists. Either run with --ignore or move this folder before running".format(args.outputFolder)
        exit(-1)
else:
    os.mkdir(args.outputFolder)

N = args.N

def cleanupVNC():
    subprocess.Popen('vncserver -kill :1', shell = True, stdout = subprocess.PIPE, stderr = subprocess.PIPE).communicate()
    print "Killing VNC server :1"

    try:
        os.remove(os.path.expanduser("~/.vnc/xstartup"))
    except:
        pass

def cleanup(signal, frame):
    cleanupVNC()
    
    try:
        handle.kill()
    except:
        pass

    exit(-1)
    
signal.signal(signal.SIGINT, cleanup)

def is_number(string):
    try:
        int(string)
        return True
    except:
        return False

# Get pids of running games
def getRunningGames():
    stdout, _ = subprocess.Popen('ps -e | grep Game', shell = True, stdout = subprocess.PIPE, stderr = subprocess.PIPE).communicate()

    games = []
    for line in stdout.split('\n'):
        vals = line.strip().split()
        if len(vals) > 0 and is_number(vals[0]):
            games.append(vals[0])

    return set(games)

# Clean up any leftovers before we start
cleanupVNC()

for i in range(0, N):
    print "Running bot {0} of {1}".format(i, N)
    # Prepare startup script
    f = open(os.path.expanduser("~/.vnc/xstartup"), "w")
    f.write("#!/bin/sh\n")
    f.write("wine explorer /desktop=diablo{0},640x480 'C:\Program Files (x86)\Diablo II\Diablo II.exe' -ns -w\n".format(i))
    f.close()
    os.chmod(os.path.expanduser("~/.vnc/xstartup"), 0775)

    # Get currently running games
    oldGamePids = getRunningGames()
    
    # Start vnc client
    cmd = 'vncserver -localhost -geometry 640x480 -depth 16 -deferupdate 1 :1 -alwaysshared'
    print "Executing: '{0}'".format(cmd)
    handle = subprocess.Popen(cmd, shell = True, stdout = subprocess.PIPE, stderr = subprocess.PIPE)
    stdout, stderr = handle.communicate()
    if handle.returncode != 0:
        print stdout
        print stderr
        print "Failed to start vncserver for bot {0} of {1}, return code = {2}".format(handle.returncode)
        exit(-1)
    print "VNC server started on port localhost:1"

    # Wait on Diablo 2 to start and get new pid
    startTime = time.time()
    while True:
        newGames = getRunningGames() - oldGamePids
        if len(newGames) > 1:
            print "Too many new games appeared. Something is wrong"
            exit(-1)
        elif len(newGames) == 1:
            pid = newGames.pop()
            break

        if time.time() - startTime > 500.0:
            print "Diablo 2 game didn't start within 5 seconds"
            exit(-1)
    print "Diablo2 game found at pid {0}".format(pid)
    os.remove(os.path.expanduser("~/.vnc/xstartup"))

    # Start VNC client (with bot script)
    cmd = ' '.join(['python diablo2_vnc_viewer/vncviewer.py --depth=32 --host=localhost --display=1 --fast',
                    '--bot={0}'.format(args.Ai),
                    '--password={0}'.format(args.password),
                    '--botDataFile={0}'.format(args.data),
                    '--botLog={0}/{1}.log'.format(args.outputFolder, i),
                    '--gamePid={0}'.format(pid),
                    '--headless={0}'.format('1' if args.headless else '0')])
    print "Executing: '{0}'".format(cmd)
    handle = subprocess.Popen(cmd, shell = True, stdout = subprocess.PIPE, stderr = subprocess.PIPE)
    startTime = time.time()
    print "VNC bot started"

    # Wait on timeout of process
    while True:
        if handle.poll() is not None:
            break

        r, w, x = select.select([handle.stdout, handle.stderr], [], [], 0.1)
        if handle.stdout in r:
            line = handle.stdout.readline().strip()
            if not args.suppress:
                print "stdout {0}/{1}: {2}".format(i, N, line)
        if handle.stderr in r:
            line = handle.stderr.readline().strip()
            if not args.suppress:
                print "stderr {0}/{1}: {2}".format(i, N, line)

        currentTime = time.time()
        if args.T > 0 and currentTime - startTime > args.T:
            handle.terminate()
            handle.wait()
            break
    print "Bot finished"

    # Clean it up!
    subprocess.Popen('vncserver -kill :1', shell = True).communicate()
    print "Killing VNC server"
