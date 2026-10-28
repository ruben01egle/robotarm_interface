# One step of a program in the motion_server goals file.

uint8 OFFSET_BASE = 0
uint8 OFFSET_TCP = 1

string goal
string motion                 # PTP, LIN or OMPL
float64 blend                 # [m] blend radius into the next step, 0 = stop
float64 scaling               # (0, 1], 0 = the scaling of the job
float64[] offset_xyz          # [m] added to the goal's tcp position, empty = none
uint8 offset_frame            # frame of offset_xyz: OFFSET_BASE (base frame) or OFFSET_TCP (tool frame)
