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
uint8 EMERGENCY_OFF = 9           # drives powered off, hardware finalized, only a firmware restart recovers.
                                  # never rejected because of a running switch, aborts it
uint8 STOPPED = 10                # powered, no controller: the drives stop and hold on their own PID,
                                  # without feedforward. Where the firmware ends up after a controller error

# reported only, can't be requested
uint8 FAULT = 254                 # leftovers of a controller error, cleaned up to STOPPED within 0.2 s
uint8 UNKNOWN = 255               # state not determined yet (controller manager not reachable)

uint8 mode
