# A goal of the motion_server goals file (robotarm_motion), or a named state of the SRDF.

uint8 TYPE_JOINT = 1
uint8 TYPE_CARTESIAN = 2

uint8 SOURCE_FILE = 1
uint8 SOURCE_SRDF = 2

string name
uint8 type
uint8 source
float64[] joints              # TYPE_JOINT: [rad] in axis order (axis1..axis6)
geometry_msgs/Pose pose       # TYPE_CARTESIAN: tcp pose in the base frame
float64[] seed                # TYPE_CARTESIAN: optional IK seed [rad] in axis order, empty = none
