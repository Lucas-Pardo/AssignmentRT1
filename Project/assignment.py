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

dt = 0.05
""" float: Time step used in all motion functions"""

grab_index = 0
""" int (0, 1): Type of token to grab. 0 for silver, 1 for gold"""

rot = 1
""" int (1, -1): Direction of rotation. 1 for clockwise, -1 for anticlockwise."""

alternatingRot = (True, False)
""" boolean tuple: Whether to alternate rotation direction after (grabbing, releasing) or not."""

R = Robot()
""" instance of the class Robot"""

sqdt = sqrt(dt)

def stop():
    """
    Function to stop the motion of the robot
    """
    R.motors[0].m0.power = 0
    R.motors[0].m1.power = 0


def drive(speed):
    """
    Function for setting a linear velocity
    
    Args: speed (int): the speed of the wheels
    """
    R.motors[0].m0.power = speed
    R.motors[0].m1.power = speed


def turn(speed):
    """
    Function for setting an angular velocity
    
    Args: speed (int): the speed of the wheels
    """
    R.motors[0].m0.power += speed
    R.motors[0].m1.power -= speed


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
        speed = d * (1 + round(24 / sqdt, 1))
        ang_speed = ang * (0.3 + 0.05 / dt)
        if d > d_th:
            drive(speed)
        if abs(ang) > a_th:
            turn(ang_speed)
        time.sleep(dt)
        if (d <= d_th) and (abs(ang) <= a_th):
            stop()
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
        speed = d * (1 + round(24 / sqdt, 1))
        ang_speed = ang * (0.3 + 0.05 / dt)
        if d > pd_th:
            drive(speed)
        if abs(ang) > a_th:
            turn(ang_speed)
        time.sleep(dt)
        if (d <= pd_th) and (abs(ang) <= a_th):
            stop()
            R.release()
            return cd
        
        
def main():
    global rot
    t = 0
    in_time = round(0.5 + 8 * sqdt, 1)
    speed = 1 + round(9 / dt, 1)
    grab_state = False
    markers = [MARKER_TOKEN_SILVER, MARKER_TOKEN_GOLD]
    release_index = (grab_index + 1) % 2
    arranged = [[], []]
    while t < in_time:
        if not grab_state:
            cd = search_and_grab(arranged, dt, markers[grab_index])
            if cd == -1:
                turn(rot*speed)
                time.sleep(dt)
                turn(-0.95*rot*speed)
                t += dt
            else:
                grab_state = True
                arranged[grab_index].append(cd)
                t = 0
                rot = -rot if alternatingRot[0] else rot
        else:
            cd = search_and_release(arranged, dt, markers[release_index])
            if cd == -1:
                turn(rot*speed)
                time.sleep(dt)
                turn(-0.95*rot*speed)
            else:
                drive(-speed)
                time.sleep(3 * sqdt)
                grab_state = False
                arranged[release_index].append(cd)
                rot = -rot if alternatingRot[1] else rot
    stop()
    return in_time


# Main Code:
start_time = default_timer()            #Start timer
in_time = main()                        #Run main function
ex_time = default_timer() - start_time  #End timer  
print("Finished in {:.3f} seconds with {:.1f} seconds of inactivity.".format(ex_time, in_time))
    
    