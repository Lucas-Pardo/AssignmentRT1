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
----------

The task is to pair every silver token to a gold token, i.e. grab a silver token and release it near a gold token such that every gold token has exactly one silver token nearby.

### Pseudocode ###

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

### Python code ###

This section gives a brief explanation about the different parts of the python code used. 

## Parameters

We start with the different parameters used and defined in the begining of the file:

```python
a_th = 2.0
""" float: Threshold for the control of the orientation"""

d_th = 0.4
""" float: Threshold for the control of the linear distance"""

pd_th = 0.6
""" float: Distance at which we leave a token to pair to another"""

in_time = 15.0
""" float: Time in seconds of inactivity to consider all tokens paired"""
```
As done in previous exercises, `a_th` and `d_th` are used to guide the robot to the token. In the case of releasing a token we use `pd_th` instead of `d_th` so that there is no colision. The `in_time` parameter is used to finish the program (it is explained later).

## Functions

The first two functions defined and used are `drive` and `turn`. As their name imply, these are used to move the robot forward or turn the robot with a certain speed. In both cases, this is done by modifying the power of the motors for some time.

```python
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

The function `search_and_grab` is used to go to the nearest token and grab it. It takes as parameters the exclusion list of tokens `exc_list`, a time step variable `dt` to control the usage of the functions `drive` and `turn` and the token type to grab `marker_type` (silver or gold). This function uses the previous function `find_free_token` to obtain the distance and angle of the nearest appropriate token and makes the robot go to its position using the functions `drive` and `turn`. Once the robot reaches the position within some thresholds given by `a_th` and `d_th`, it uses the method `R.grab` to grab the token. This function returns -1 if no appropriate token was found otherwise it returns the code returned by the function `find_free_token`.

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
        speed = d * 20
        ang_speed = ang / 2
        if d > d_th:
            drive(speed, dt)
        if abs(ang) > a_th:
            turn(ang_speed, dt)
        if (d <= d_th) and (abs(ang) <= a_th):
            R.grab()
            return cd
```

The last function used is called `search_and_release`. It takes the exact same parameters as the previous function `search_and_grab` and works eexactly the same except that it uses `pd_th` instead of `d_th` and once the robot arrives at the given position it uses the method `R.release` to release the token that it is carrying. It returns the code of the token where the released happened or -1 if no appropriate token was found.

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
        speed = d * 20
        ang_speed = ang / 2
        if d > pd_th:
            drive(speed, dt)
        if abs(ang) > a_th:
            turn(ang_speed, dt)
        if (d <= pd_th) and (abs(ang) <= a_th):
            R.release()
            return cd
```

## Main code

The first part of the code is a set of 3 modifiable parameters: the time step used `dt` (lower values would give a smoother movement), a `speed` variable to turn the robot while looking for a suitable marker and something called the `grab_index` which is the token type that we want to grab, this is in reference to the `markers` list so 0 would be a silver token and 1 a gold token.

```python
# Modifiable parameters:
dt = 0.4
speed = 10
grab_index = 0
```

The main code is just a direct application of the pseudocode in python. It prints "Finished" after every token is paired.

```python
# Main function:
t = 0
grab_state = False
markers = [MARKER_TOKEN_SILVER, MARKER_TOKEN_GOLD]
release_index = (grab_index + 1) % 2
arranged = [[], []]
while t < in_time:
    print("working")
    if not grab_state:
        cd = search_and_grab(arranged, dt, markers[grab_index])
        if cd == -1:
            turn(speed, dt)
            t += dt
        else:
            grab_state = True
            arranged[grab_index].append(cd)
            t = 0
    else:
        cd = search_and_release(arranged, dt, markers[release_index])
        if cd == -1:
            turn(speed, dt)
        else:
            drive(-speed * 5, dt*2)
            turn(speed, dt*2)
            grab_state = False
            arranged[release_index].append(cd)
            
print("Finished.")
```

There are however some details that are not specified in the pseudocode. The first one is the exclusion list, in this case called `arranged`. Because tokens of different type can have the same code, we need a separate exclusion list for silver tokens and gold tokens. We do this using a 2 row matrix so that `arranged[0]` is the exclusion list for silver tokens and `arranged[1]` the one for gold tokens. The second detail is that functions `search_and_grab` and `search_and_release` just search for tokens directly in front of the robot (in its field of vision), so when they return -1 we need to turn the robot and try again. Finally, the way we detect the end of the process is just by an inactivity time, the parameter defined in the begining `in_time`. Every time the `search_and_grab` function fails to find an appropriate token (returns -1) we add to the time variable `t` the value of the time step `dt`. When `t` reaches the inactivity time `in_time` we consider the process finished.

### Improvements ###

