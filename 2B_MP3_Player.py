#!/usr/bin/env python3
import glob
import subprocess
import os, signal, sys
import time
import random
from random import shuffle
from mutagen.mp3 import MP3
from gpiozero import Button
from gpiozero import LED

#version 0.03

# if using BLUETOOTH speaker set use_BT = 1
use_BT = 0
# to set default SHUFFLE set shuffled = 1
shuffled = 0
# to play at startup set Con_Play = 1
Con_Play = 0

# define GPIOs used
# BUTTONS
PLAY = 19 # PLAY     (whilst stopped) / STOP    (whilst playing) / SHUTDOWN (hold down for 5 seconds)
PREV = 26 # PREVIOUS (whilst playing) / SHUFFLE (whilst stopped) / REBOOT   (hold down for 5 seconds)
# LEDS
LED1 = 13 # READY LED / Flashes during startup checking for USB stick
LED2 = 5  # PLAYING LED
LED3 = 6  # SHUFFLED LED / LOADING MP3s (Flashes if no MP3s found)

# setup GPIO
button_play = Button(PLAY)
button_prev = Button(PREV)
led_1 = LED(LED1)
led_2 = LED(LED2)
led_3 = LED(LED3)
led_1.off()
led_2.off()

# find user
h_user = "/home/" + os.getlogin( )
m_user = "/media/" + os.getlogin( )

# check if USB mounted
start = time.monotonic()
usb = glob.glob(m_user + "/*")
if len(usb) < 1:
    while time.monotonic() - start < 20 and len(usb) == 0:
        usb = glob.glob(m_user + "/*")
        led_1.off()
        time.sleep(.25)
        led_1.on()
        time.sleep(.25)
led_1.off()

# find MP3 tracks
tracks  = []
tracks2 = []
while len(tracks) == 0:
    led_3.off()
    time.sleep(.25)
    led_3.on()
    time.sleep(.25)
    tracks  = glob.glob(h_user + "/Music/*.mp3")
    tracks2 = glob.glob(m_user + "/*/*/*/*.mp3")
    for x in range(0,len(tracks2)):
        tracks.append(tracks2[x])
    tracks.sort()
led_1.on()
if shuffled == 0:
    led_3.off()
    tracks.sort()
else:
    led_3.on()
    shuffle(tracks)

# set starting variables
skip = 0
Z = 0

while True:
    while not button_play.is_pressed and Con_Play == 0:
        time.sleep(0.1)
        # check for shuffle key
        if button_prev.is_pressed:                     
            time.sleep(0.5)
            if shuffled == 0:
                print ("Shuffled")
                shuffle(tracks)
                shuffled = 1
                led_3.on()
            else:
                print ("unShuffled")
                tracks.sort()
                shuffled = 0
                led_3.off()
            timer1 = time.monotonic()
            while button_prev.is_pressed:
                # reboot if pressed > 5 seconds
                if time.monotonic() - timer1 > 5:                  
                    led_2.off()
                    led_1.off()
                    led_3.off()
                    print ("Restart")
                    os.system("reboot")
    timer1 = time.monotonic()
    while button_play.is_pressed:
        # shutdown if pressed > 5 seconds
        if time.monotonic() - timer1 > 5:                  
            led_2.off()
            led_1.off()
            led_3.off()
            print ("Goodbye!")
            os.system("sudo shutdown -h now")
    Con_Play = 1
    led_2.on()                      
    
    while Con_Play == 1 :
        rpistr = "mplayer " + " -quiet " +  '"' + tracks[Z] + '"'
        print ("Playing..." + tracks[Z])
        audio = MP3(tracks[Z])
        track_len = audio.info.length
        p = subprocess.Popen(rpistr, shell=True, preexec_fn=os.setsid)
        poll = p.poll()
        start = time.monotonic()
        while poll == None:                        
            time.sleep(0.1)
            # stop track if near end of track, required for Bluetooth operation
            if time.monotonic() - start > track_len - 2 and use_BT == 1:
                print ("Track stopped for BT")
                os.killpg(p.pid, signal.SIGTERM)
                time.sleep(1)
            # check for stop/shutdown
            if button_play.is_pressed:                    
                timer1 = time.monotonic()
                print ("Track stopped")
                os.killpg(p.pid, signal.SIGTERM)
                Con_Play = 0
                led_2.off()
                while button_play.is_pressed:
                    # shutdown if pressed > 5 seconds
                    if time.monotonic() - timer1 > 5:       
                        led_2.off()
                        led_1.off()
                        led_3.off()  
                        print ("Goodbye!")
                        os.killpg(p.pid, signal.SIGTERM)
                        os.system("sudo shutdown -h now")
            # check for previous key 
            elif button_prev.is_pressed:                   
                print ("Previous Track...")
                time.sleep(0.5)
                os.killpg(p.pid, signal.SIGTERM)
                Z -= 2
                timer1 = time.monotonic()
                while button_prev.is_pressed:
                    # reboot if pressed > 5 seconds
                    if time.monotonic() - timer1 > 5:                  
                        led_2.off()
                        led_1.off()
                        led_3.off()
                        print ("Restart")
                        os.system("reboot")
            poll = p.poll()
        Z += 1
        if Z < 0:
            Z = len(tracks) + Z
        if Z > len(tracks) - 1:
            Z = Z - len(tracks) 





            
