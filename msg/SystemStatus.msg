# State of the control_center, published at 10 Hz on /system_status.

uint8 IDLE = 0
uint8 CONNECTED = 1
uint8 ARMED = 2
uint8 MISSION = 3
uint8 CONFIG = 4
uint8 STOP = 5
uint8 ERROR = 6
uint8 EMERGENCY = 7

uint8 state
bool connected
bool armed
bool stopped
string active_node              # node that owns the running mission, empty = none
string[] active_controllers     # controller set of the running mission
