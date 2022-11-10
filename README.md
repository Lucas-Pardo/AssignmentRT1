Python Robotics Simulator
================================

This is a simple, portable robot simulator developed by [Student Robotics](https://studentrobotics.org).
Some of the arenas and the exercises have been modified for the Research Track I course

Installing and running
----------------------

The simulator requires a Python 2.7 installation, the [pygame](http://pygame.org/) library, [PyPyBox2D](https://pypi.python.org/pypi/pypybox2d/2.1-r331), and [PyYAML](https://pypi.python.org/pypi/PyYAML/).

Pygame, unfortunately, can be tricky (though [not impossible](http://askubuntu.com/q/312767)) to install in virtual environments. If you are using `pip`, you might try `pip install hg+https://bitbucket.org/pygame/pygame`, or you could use your operating system's package manager. Windows users could use [Portable Python](http://portablepython.com/). PyPyBox2D and PyYAML are more forgiving, and should install just fine using `pip` or `easy_install`.

## Troubleshooting

When running `python run.py <file>`, you may be presented with an error: `ImportError: No module named 'robot'`. This may be due to a conflict between sr.tools and sr.robot. To resolve, symlink simulator/sr/robot to the location of sr.tools.

On Ubuntu, this can be accomplished by:
* Find the location of srtools: `pip show sr.tools`
* Get the location. In my case this was `/usr/local/lib/python2.7/dist-packages`
* Create symlink: `ln -s path/to/simulator/sr/robot /usr/local/lib/python2.7/dist-packages/sr/`

Robot API
---------

The API for controlling a simulated robot is designed to be as similar as possible to the [SR API][sr-api].

### Motors ###

The simulated robot has two motors configured for skid steering, connected to a two-output [Motor Board](https://studentrobotics.org/docs/kit/motor_board). The left motor is connected to output `0` and the right motor to output `1`.

The Motor Board API is identical to [that of the SR API](https://studentrobotics.org/docs/programming/sr/motors/), except that motor boards cannot be addressed by serial number. So, to turn on the spot at one quarter of full power, one might write the following:

```python
R.motors[0].m0.power = 25
R.motors[0].m1.power = -25
```

### The Grabber ###

The robot is equipped with a grabber, capable of picking up a token which is in front of the robot and within 0.4 metres of the robot's centre. To pick up a token, call the `R.grab` method:

```python
success = R.grab()
```

The `R.grab` function returns `True` if a token was successfully picked up, or `False` otherwise. If the robot is already holding a token, it will throw an `AlreadyHoldingSomethingException`.

To drop the token, call the `R.release` method.

Cable-tie flails are not implemented.

### Vision ###

To help the robot find tokens and navigate, each token has markers stuck to it, as does each wall. The `R.see` method returns a list of all the markers the robot can see, as `Marker` objects. The robot can only see markers which it is facing towards.

Each `Marker` object has the following attributes:

* `info`: a `MarkerInfo` object describing the marker itself. Has the following attributes:
  * `code`: the numeric code of the marker.
  * `marker_type`: the type of object the marker is attached to (either `MARKER_TOKEN_GOLD`, `MARKER_TOKEN_SILVER` or `MARKER_ARENA`).
  * `offset`: offset of the numeric code of the marker from the lowest numbered marker of its type. For example, token number 3 has the code 43, but offset 3.
  * `size`: the size that the marker would be in the real game, for compatibility with the SR API.
* `centre`: the location of the marker in polar coordinates, as a `PolarCoord` object. Has the following attributes:
  * `length`: the distance from the centre of the robot to the object (in metres).
  * `rot_y`: rotation about the Y axis in degrees.
* `dist`: an alias for `centre.length`
* `res`: the value of the `res` parameter of `R.see`, for compatibility with the SR API.
* `rot_y`: an alias for `centre.rot_y`
* `timestamp`: the time at which the marker was seen (when `R.see` was called).

For example, the following code lists all of the markers the robot can see:

```python
markers = R.see()
print "I can see", len(markers), "markers:"

for m in markers:
    if m.info.marker_type in (MARKER_TOKEN_GOLD, MARKER_TOKEN_SILVER):
        print " - Token {0} is {1} metres away".format( m.info.offset, m.dist )
    elif m.info.marker_type == MARKER_ARENA:
        print " - Arena marker {0} is {1} metres away".format( m.info.offset, m.dist )
```

[sr-api]: https://studentrobotics.org/docs/programming/sr/


Assignment
==========

The task is to pair every silver token to a gold token, i.e. grab a silver token and release it near a gold token such that every gold token has exactly one silver token nearby.

## Pseudocode

A general pseudocode for this task could be the following:

```
Initialize an empty exclusion list of markers
Initialize the grab_state to false

Do until every token is paired:
  if grab_state is false:
    search the nearest silver token that is not in exclusion list
    go to token and grab it
    set grab_state to true
    add token code to exclusion list
  else:
    search nearest gold token that is not in exclusion list
    go to token and release the silver token near it
    set grab_state to false
    add gold token code to exclusion list

```

## Python code 

This section gives a brief explanation about the different parts of the python code used: `assignment.py`. To run the program write in the terminal:

```bash
$ python2 run.py assignment.py
```

### Parameters ###

We start with the different parameters used and defined in the begining of the file:

```python
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

rot = -1
""" int (1, -1): Direction of rotation. 1 for clockwise, -1 for anticlockwise."""

alternatingRot = (True, False)
""" boolean tuple: Whether to alternate rotation direction after (grabbing, releasing) or not."""
```
* As done in previous exercises, `a_th` and `d_th` are used to guide the robot to the token. In the case of releasing a token we use `pd_th` instead of `d_th` so that there is no colision. 
* The `dt` parameter is the time step used between motion commands. 
* The `grab_index` parameter is the token that we want to seek and pair to the opposite token type. It can take the value 0 for silver tokens and 1 for gold tokens. 
* The `rot` parameter is the direction of rotation of the robot while it searches for a suitable token. It can take the value 1 for a clockwise rotation and -1 for an anticlockwise rotation. 

Finally, we have decided to include an interesting parameter called `AlternatingRot`, which is a boolean tuple (`boolean`, `boolean`). It indicates whether to alternate the rotation direction after performing the corresponding action (`grab`, `release`), e.g. `(False, True)` means that the rotation will be alternated after every release but not after grabbing. This parameter is interesting because it can actually improve the performance (time taken) of the robot without decreasing the time step `dt`. After some testing the configurations `(True, True)` and `(True, False)` seem to work best for the current arena configuration.

### Functions ###

The first three functions defined and used are `stop`, `drive` and `turn`. As their name imply, these are used to stop the robot, move the robot forward or turn the robot with a certain speed. In both cases, this is done by modifying the power of the motors. There is an important difference with respect to the usual `drive` and `turn` functions and that is that the `turn` function does not set the speed it just adds speed to the motors. This way we can obtain a smoother path to the tokens.

```python

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
```

The next function and most important one is called `find_free_token`. It takes as parameters a `marker_type` (silver or gold) and the exclusion list of markers. This function uses the `R.see` method to obtain the list of markers and then it looks through it to return the distance, angle and code of the nearest token of type `marker_type` that is not in `exc_list`.

```python
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
```

The function `search_and_grab` is used to go to the nearest token and grab it. It takes as parameters the exclusion list of tokens `exc_list`, a time step variable `dt` to control the usage of the functions `drive` and `turn` and the token type to grab `marker_type` (silver or gold). This function uses the previous function `find_free_token` to obtain the distance and angle of the nearest appropriate token and makes the robot go to its position using the functions `drive` and `turn`. The speed and angular speed used is calculated using the relative distances (`d`, `ang`) and the time step `dt` to obtain a good trajectory regardless of the time step used. Once the robot reaches the position within some thresholds given by `a_th` and `d_th`, it uses the method `R.grab` to grab the token. This function returns -1 if no appropriate token was found otherwise it returns the code returned by the function `find_free_token`.

* Note: sqdt = sqrt(dt), it is defined as a paramater because it is used in multiple places inside loops.

```python
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
        speed = d * (1 + 24 / sqdt)
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
```

The last function used is called `search_and_release`. It takes the exact same parameters as the previous function `search_and_grab` and works exactly the same except that it uses `pd_th` instead of `d_th` and once the robot arrives at the given position it uses the method `R.release` to release the token that it is carrying. It returns the code of the token where the release happened (gold token) or -1 if no appropriate token was found.

```python
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
        speed = d * (1 + 24 / sqdt)
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
```

### Main code ###

The main code is defined as the function `main` which is a direct application of the pseudocode in python using the functions defined.

* Note: The `rot` paramater is the only one that must be declared global since it "becomes" a variable (we assign values to it) if any element of `AlternatingRot` is `True`. 

```python
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
```

There are however some details that are not specified in the pseudocode:

* The first one is the exclusion list, in this case called `arranged`. Because tokens of different type can have the same code, we need a separate exclusion list for silver tokens and gold tokens. We do this using a 2 row matrix so that `arranged[0]` is the exclusion list for silver tokens and `arranged[1]` the one for gold tokens. 

* The second detail is that functions `search_and_grab` and `search_and_release` just search for tokens directly in front of the robot (in its field of vision), so when they return -1 we need to turn the robot and try again. We do this by calling the `turn` function, but since this function adds speed, the speed would keep increasing without any control. After calling `time.sleep` we would need to call the function `stop` or, as we have done, turn the opposite direction. As we can see, we have decided not to stop it completely and just reduce the speed by 95%. This means that there is still a slight acceleration, i.e. the speed keeps increasing slightly as the robot turns to find an appropriate token. The speed for iteration n > 0 is v(n) = (1.05)^n * v(0).

* Finally, the way we detect the end of the process is just by an inactivity time, the variable computed in the begining, `in_time`. Every time the `search_and_grab` function fails to find an appropriate token (returns -1) we add to the time variable `t` the value of the time step `dt`. When `t` reaches the inactivity time `in_time` we consider the process finished (no more tokens to pair). This parameter is computed using the time step `dt` such that there is enough time to perform at least a whole turn given the speed used (also computed using `dt`).

```python
# Main Code:
start_time = default_timer()            #Start timer
in_time = main()                        #Run main function
ex_time = default_timer() - start_time  #End timer  
print("Finished in {:.3f} seconds with {:.1f} seconds of inactivity.".format(ex_time, in_time))
```

The actual main block of code executed is just a call to the `main` function surrounded by some calls to the `timeit.default_timer` function to time the process and a print with the time taken and how much time of inactivity.


## Improvements

### Better pathing ###

The code works pretty well for the given arena and configuration of tokens. However, if we perform the opposite operation for instance, pair gold tokens to silver tokens, we find that the process becomes sluggish and even impossible. This is because the robot does not consider other tokens blocking its path to the desired token. This means that most of the times the robot drags around some tokens for some time and even forever, preventing it from reaching the desired token within the given threshold. To solve this problem and obtain a more general algorithm for this task, we need to implement some function to detect tokens in its path and some kind of movement algorithm to avoid it.

### Better movement control ###

Right now the functions `search_and_grab` and `search_and_release` use a very simple form of variable speed to approach the token. This works quite well for small values of `dt`, however, for large values the pathing becomes quite rough. Given that larger values of `dt` would improve the performance, it could be useful to implement a more complex movement controller (in discrete time) if performance becomes a problem.

### Cleaner code ###

There are some improvements that can be made in the code. For instance, we could easily merge `search_and_grab` and `search_and_release` into a single function using the `grab_state` variable. This would also reduce and simplify a little the main function. We have decided not to do it in favour of readability of the main code and to maintain some semblance of the pseudocode.