#!/usr/bin/env python3
import RPi.GPIO as GPIO
import glob
import subprocess
import os, signal, sys
import time
import random
from random import shuffle
from mutagen.mp3 import MP3

#version 25102020_1

# define physical GPIO pins used
# BUTTONS
PLAY = 18 # PLAY / STOP / SHUTDOWN (hold down for 5 seconds)
PREV = 16 # PREVIOUS (whilst playing) / SHUFFLE (whilst stopped) / REBOOT (hold down for 5 seconds)
# LEDS
LED1 = 11 # ON LED
LED2 = 13 # PLAYING LED
LED3 = 7  # SHUFFLED LED

# setup GPIO
GPIO.setmode(GPIO.BOARD)
GPIO.setwarnings(False)
GPIO.setup(PLAY,GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(PREV,GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(LED1,GPIO.OUT)
GPIO.setup(LED2,GPIO.OUT)
GPIO.setup(LED3,GPIO.OUT)
GPIO.output(LED1,GPIO.LOW) # turn LED1 OFF
GPIO.output(LED2,GPIO.LOW) # turn LED2 OFF
GPIO.output(LED3,GPIO.LOW) # turn LED3 OFF

# delay to ensure USB mounted, flash LED1
start = time.time()
while time.time() - start < 10:
    GPIO.output(LED1,GPIO.LOW)
    time.sleep(.25)
    GPIO.output(LED1,GPIO.HIGH)
    time.sleep(.25)
GPIO.output(LED1,GPIO.HIGH)

# find tracks
tracks = []
tracks2 = []
while len(tracks) == 0:
    # light LED3 whilst checking for mp3 tracks
    GPIO.output(LED3,GPIO.HIGH)
    tracks = glob.glob("/home/pi/Music/*.mp3")
    tracks2 = glob.glob("/media/pi/*/*/*/*.mp3")
    for x in range(0,len(tracks2)):
        tracks.append(tracks2[x])
    tracks.sort()
GPIO.output(LED3,GPIO.LOW)

# set starting variables
Con_Play = 1
skip = 0
Z = 0
shuffled = 0

while True:
    while GPIO.input(PLAY) == 1:
        time.sleep(0.1)
        # check for shuffle key
        if  GPIO.input(PREV) == 0:                     
            time.sleep(0.5)
            if shuffled == 0:
                print ("Shuffled")
                shuffle(tracks)
                shuffled = 1
                GPIO.output(LED3,GPIO.HIGH)
            else:
                print ("unShuffled")
                tracks.sort()
                shuffled = 0
                GPIO.output(LED3,GPIO.LOW)
            timer1 = time.time()
            while GPIO.input(PREV) == 0:
                # reboot if pressed > 5 seconds
                if time.time() - timer1 > 5:                  
                    GPIO.output(LED2,GPIO.LOW)
                    GPIO.output(LED1,GPIO.LOW)
                    GPIO.output(LED3,GPIO.LOW)
                    print ("Restart")
                    os.system("reboot")
    timer1 = time.time()
    while GPIO.input(PLAY) == 0:
        # shutdown if pressed > 5 seconds
        if time.time() - timer1 > 5:                  
            GPIO.output(LED2,GPIO.LOW)
            GPIO.output(LED1,GPIO.LOW)
            GPIO.output(LED3,GPIO.LOW)
            print ("Goodbye!")
            os.system("sudo shutdown -h now")
    Con_Play = 1
    GPIO.output(LED2,GPIO.HIGH)                      
    
    while Con_Play == 1 :
        rpistr = "mplayer " + '"' + tracks[Z] + '"'
        print ("Playing..." + tracks[Z])
        audio = MP3(tracks[Z])
        track_len = audio.info.length
        start = time.time()
        p = subprocess.Popen(rpistr, shell=True, preexec_fn=os.setsid)
        poll = p.poll()
        while poll == None:                        
            time.sleep(0.1)
            # check if near end of track, required for Bluetooth operation
            if time.time() - start > track_len - 1:
                print ("Track stopped for BT")
                os.killpg(p.pid, signal.SIGTERM)
                GPIO.output(LED2,GPIO.LOW)
            # check for stop/shutdown
            if  GPIO.input(PLAY) == 0:                     
                timer1 = time.time()
                print ("Track stopped")
                os.killpg(p.pid, signal.SIGTERM)
                Con_Play = 0
                GPIO.output(LED2,GPIO.LOW)
                while GPIO.input(PLAY) == 0:
                    # shutdown if pressed > 5 seconds
                    if time.time() - timer1 > 5:       
                        GPIO.output(LED2,GPIO.LOW)
                        GPIO.output(LED1,GPIO.LOW)
                        GPIO.output(LED3,GPIO.LOW)  
                        print ("Goodbye!")
                        os.killpg(p.pid, signal.SIGTERM)
                        os.system("sudo shutdown -h now")
            # check for previous key 
            elif  GPIO.input(PREV) == 0:                   
                print ("Previous Track...")
                time.sleep(0.5)
                os.killpg(p.pid, signal.SIGTERM)
                Z -= 2
                timer1 = time.time()
                while GPIO.input(PREV) == 0:
                    # reboot if pressed > 5 seconds
                    if time.time() - timer1 > 5:                  
                        GPIO.output(LED2,GPIO.LOW)
                        GPIO.output(LED1,GPIO.LOW)
                        GPIO.output(LED3,GPIO.LOW)
                        print ("Restart")
                        os.system("reboot")
            poll = p.poll()
        Z += 1
        if Z < 0:
            Z = len(tracks) + Z
        if Z > len(tracks) - 1:
            Z = Z - len(tracks) 





            
