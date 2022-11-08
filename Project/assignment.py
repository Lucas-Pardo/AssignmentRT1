from __future__ import print_function
import time
from timeit import default_timer
from math import sqrt
from sr.robot import *


a_th = 2.0
""" float: Threshold for the control of the orientation"""

d_th = 0.4
""" float: Threshold for the control of the linear distance"""

pd_th = 0.6
""" float: Threshold for the control of the release distance"""

dt = 0.02
""" float: Time step used in all motion functions"""

grab_index = 0
""" int (0, 1): Type of token to grab. 0 for silver, 1 for gold"""

R = Robot()
""" instance of the class Robot"""

def drive(speed, seconds):
    """
    Function for setting a linear velocity
    
    Args: speed (int): the speed of the wheels
	  seconds (int): the time interval
    """
    R.motors[0].m0.power = speed
    R.motors[0].m1.power = speed
    time.sleep(seconds)
    R.motors[0].m0.power = 0
    R.motors[0].m1.power = 0


def turn(speed, seconds):
    """
    Function for setting an angular velocity
    
    Args: speed (int): the speed of the wheels
	  seconds (int): the time interval
    """
    R.motors[0].m0.power = speed
    R.motors[0].m1.power = -speed
    time.sleep(seconds)
    R.motors[0].m0.power = 0
    R.motors[0].m1.power = 0


def find_free_token(marker_type=None, exc_list=[[], []]):
    
    """
    Function to find the closest free token of marker_type

    Returns:
	dist (float): distance of the closest free token (-1 if no token is detected)
	rot_y (float): angle between the robot and the token (-1 if no token is detected)
    cd (int): code of the token. (None if no token is detected)
    """
    index = 0 if marker_type == MARKER_TOKEN_SILVER else 1
    dist = 100
    for token in R.see():
        if marker_type != None:
            if token.info.marker_type != marker_type:
                continue
        if token.info.code not in exc_list[index] and token.dist < dist:
            dist = token.dist
            cd = token.info.code
            rot_y = token.rot_y
    if dist == 100:
	    return -1, -1, None
    else:
   	    return dist, rot_y, cd


def search_and_grab(exc_list=[[], []], dt=0.4, marker_type=MARKER_TOKEN_SILVER):
    
    """
    Function to look for the nearest token of marker_type, go to it and grab it.
    
    Returns:
    cd (int): code of the token grabbed (-1 if no token is grabbed)
    """
    while True:
        d, ang, cd = find_free_token(marker_type, exc_list)
        if d < 0:
            return -1
        speed = d * (1 + round(16 / dt))
        ang_speed = min(ang / 4 / dt, 3 * ang)
        if d > d_th:
            drive(speed, dt)
        if abs(ang) > a_th:
            turn(ang_speed, dt)
        if (d <= d_th) and (abs(ang) <= a_th):
            R.grab()
            return cd
        

def search_and_release(exc_list=[[], []], dt=0.4, marker_type=MARKER_TOKEN_GOLD):
    
    """
    Function to look for the nearest token of marker_type, go to it and release the token grabbed.
    
    Returns:
    cd (int): code of the token where the release happens (-1 if no token is found)
    """
    while True:
        d, ang, cd = find_free_token(marker_type, exc_list)
        if d < 0:
            return -1
        speed = d * (1 + round(16 / dt))
        ang_speed = min(ang / 4 / dt, 3 * ang)
        if d > pd_th:
            drive(speed, dt)
        if abs(ang) > a_th:
            turn(ang_speed, dt)
        if (d <= pd_th) and (abs(ang) <= a_th):
            R.release()
            return cd
        
        
def main():
    t = 0
    in_time = 14 * sqrt(dt)
    speed = 1 + round(17 / sqrt(dt))
    grab_state = False
    markers = [MARKER_TOKEN_SILVER, MARKER_TOKEN_GOLD]
    release_index = (grab_index + 1) % 2
    arranged = [[], []]
    rot = 1
    while t < in_time:
        if not grab_state:
            cd = search_and_grab(arranged, dt, markers[grab_index])
            if cd == -1:
                turn(rot * speed, dt)
                t += dt
            else:
                grab_state = True
                arranged[grab_index].append(cd)
                t = 0
                rot *= -1
        else:
            cd = search_and_release(arranged, dt, markers[release_index])
            if cd == -1:
                turn(rot * speed, dt)
            else:
                drive(-speed, speed * dt / 6)
                grab_state = False
                arranged[release_index].append(cd)
    return in_time

# Main Code:
if __name__ == "__main__":                  #Check if the file is run as a script.
    #execfile("run.py")                      #Execute run.py
    start_time = default_timer()            #Start timer
    in_time = main()                        #Run main function
    ex_time = default_timer() - start_time  #End timer  
    print("Finished in {:.3f} seconds with {:.1f} seconds of inactivity.".format(ex_time, in_time))
    
    