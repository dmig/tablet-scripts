#!/usr/bin/env python2
import time
import os
import subprocess
import sys


def read_file(path): #self.filename
    myDatei = open(path, "r")
    myList = []
    #Liste aus Datei erstellen
    for Line in myDatei:
        Line = Line.rstrip()
        #Line = Line.decode('utf8')
        myList.append(Line)
    myDatei.close()
    return(myList)


def write_file(path, myList): #self.filename
    myDatei = open(path, "w")
    #Liste aus Datei erstelle
    myDatei.writelines(myList)
    myDatei.close()


def disable_touch():
    command = 'xinput disable "{0}"'.format(touchscreen)
    os.system(command)


def enable_touch():
    command = 'xinput enable "{0}"'.format(touchscreen)
    os.system(command)


def refresh_touch():
    disable_touch()
    enable_touch()


def check_displays():
    check_displays = "xrandr | grep -w 'connected'"
    str_displays = str(subprocess.check_output(check_displays, shell=True).lower().rstrip())
    list_displays = str_displays.splitlines()
    int_displays = len(list_displays)

    return int_displays


def find_accelerometer():
    count = 0
    partial_iio_path = '/sys/bus/iio/devices/iio:device'
    accelerometer_file_proof = 'in_accel_scale'

    while count <= 9:
        iio_path = partial_iio_path + str(count)
        proof_path = iio_path + '/' + accelerometer_file_proof

        if os.path.exists(proof_path) == True:
            return iio_path, proof_path # directory of accelerometer device (iio), and accelerometer file
            break

        count = count + 1


def rotate_screen(orientation):
    rotate_screen_commands = "xrandr -o {0}; xinput set-prop '{1}' 'Coordinate Transformation Matrix' {3}; xinput set-prop '{2}' 'Coordinate Transformation Matrix' {3};"
       
    if orientation == 'inverted':
        matrix = '-1 0 1 0 -1 1 0 0 1'

    elif orientation == 'right':
        matrix = '0 1 0 -1 0 1 0 0 1'

    elif orientation == 'left':
        matrix = '0 -1 1 1 0 0 0 0 1'

    elif orientation == 'normal':
        matrix = '1 0 0 0 1 0 0 0 1'

    rotate_screen_commands = rotate_screen_commands.format(orientation, touchscreen, pen, matrix)
    os.system(rotate_screen_commands)

    refresh_touch()

# Globals
touchscreen = 'NTRG0001:01 1B96:1B05'
pen = "{0} Pen".format(touchscreen)
state_dict = {0: "normal", 1: "inverted", 2: "right", 3: "left"}
device_path, accelerometer_path = find_accelerometer()


# Config
debug = False
path = os.path.abspath(os.path.dirname(os.path.abspath(__file__)))
freq = 1 # Checks per second


# Initialization
current_state = 0
previous_tstate = "on"
previousStylusProximityStatus = "out"
firstrun = True


# Accelerometer
with open(accelerometer_path) as f:
    scale = float(f.readline())


while True:
    multimonitor = False
    int_displays = check_displays()

    if int_displays > 1:
        multimonitor = True

    time.sleep(1.0/freq)
    previous_state = current_state
    status = read_file(os.path.join(path, 'status.txt'))

    has_keyboard_dock_command = 'xinput --list | grep "Microsoft Surface Type Cover Keyboard" | wc -l'
    has_keyboard_dock = int(subprocess.check_output(has_keyboard_dock_command, shell=True))

    if str(status[0]) == "on" and multimonitor == False and has_keyboard_dock < 1:
        with open(device_path + '/' + 'in_accel_x_raw', 'r') as fx:
            with open(device_path + '/' + 'in_accel_y_raw', 'r') as fy:
                with open(device_path + '/' + 'in_accel_z_raw', 'r') as fz:
                    thex = float(fx.readline())
                    they = float(fy.readline())
                    thez = float(fz.readline())

                    if check_displays() == 1:
                        if (thex >= 65000 or thex <= 650):
                            if (they <= 65000 and they >= 64000):
                                current_state = 0
                            if (they >= 650 and they <= 1100):
                                current_state = 1
                        if (thex <= 64999 and thex >= 650):
                            if (thex >= 64500 and thex <=64700):
                                current_state = 2
                            if (thex >= 800 and thex <= 1000):
                                current_state = 3

                        #cmd = 'sudo chvt 8'
                        #cmd_result = subprocess.check_output(cmd, shell=True)

        if debug:
            os.system('clear')

            print("ExtDi: " + str(multimonitor))
            print("A-ROT: " + status[0])
            print("    x: " + str(thex))
            print("    y: " + str(they))
            print("    z: " + str(thez))
            print("  POS: " + state_dict[current_state])
    
    else:
        #cmd = 'sudo chvt 7'
        #cmd_result = subprocess.check_output(cmd, shell=True)
        pass
    
    if (status[0] == "off" or multimonitor == True) and debug:
        os.system('clear')

        print("ExtDi: " + str(multimonitor))
        print("A-ROT: " + status[0])
        print("    x: " + status[0])
        print("    y: " + status[0])
        print("    z: " + status[0])
        print("  POS: " + state_dict[previous_state])

    if current_state != previous_state:
        rotate_screen(state_dict[current_state])

        if debug:
            print "Touchscreen refreshed"

    if debug:
        print("##########################")


    #SCREEN
    stylusProximityCommand = 'xinput query-state "{0}" | grep Proximity | cut -d " " -f3 | cut -d "=" -f2'.format(pen)
    stylusProximityStatus = str(subprocess.check_output(stylusProximityCommand, shell=True).lower().rstrip())
    tstatus = read_file(os.path.join(path, 'touch.txt'))


    #TOUCHSCREEN
    if str(tstatus[0]) == "on" and stylusProximityStatus == "out":
        enable_touch()
        print("TOUCH: " + tstatus[0])

    elif str(tstatus[0]) == "off" and stylusProximityStatus == "out":
        disable_touch()
        print("TOUCH: " + tstatus[0])


    previous_tstate = str(tstatus[0])


    #PEN
    if str(tstatus[0]) == "off" and stylusProximityStatus == "in":
        if debug:
            print("TOUCH: " + tstatus[0])
            print("  PEN: " + stylusProximityStatus)

    elif str(tstatus[0]) == "on" and stylusProximityStatus == "in" and firstrun == False:
        disable_touch() 

        if debug:
            print("TOUCH: " + "off")
            print("  PEN: " + stylusProximityStatus)

    elif stylusProximityStatus == "out":
        firstrun == False

        if debug:
            print("  PEN: " + stylusProximityStatus)
