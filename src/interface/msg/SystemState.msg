# msg/SystemMode.msg
uint32 IDLE = 1
uint32 CONNECTED = 2
uint32 ARMED = 3
uint32 MOTION = 4
uint32 CONFIG = 5
uint32 ERROR = 1638             # 0x666
uint32 EMERGENCY_HALT = 65535   # 0xFFFF

uint32 state