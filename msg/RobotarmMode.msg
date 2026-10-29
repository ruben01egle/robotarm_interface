# Operating mode of the arm, as set and reported by the firmware mode manager.
# Which controllers make up a mode is internal to the firmware.

uint8 LIMP = 0                    # drives unpowered, the arm is limp
uint8 ARMED = 1                   # position hold with feedforward
uint8 JOINT_STREAM = 2            # position controlled, streamed joint targets
uint8 CARTESIAN_JOG = 3           # position controlled, cartesian twists / increments
uint8 TRAJECTORY = 4              # position controlled, FollowJointTrajectory action
uint8 GRAVITY_COMP = 5            # floats, hand guiding
uint8 IMPEDANCE = 6               # compliant hold of the activation pose
uint8 IMPEDANCE_JOINT_STREAM = 7  # compliant, streamed joint targets
uint8 IMPEDANCE_JOG = 8           # compliant, cartesian twists / increments

# reported only, can't be requested
uint8 FAULT = 254                 # drives hold position without feedforward after an error, request ARMED or LIMP
uint8 UNKNOWN = 255               # state not determined yet (controller manager not reachable)

uint8 mode
