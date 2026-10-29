# State of the firmware mode manager, latched on /mode_manager/state, published on change.

RobotarmMode mode             # actual mode, read from ros2_control (not the last request)
RobotarmMode[] available      # modes a set_mode request can switch to now, incl. the actual one
bool switching                # a request is being executed, other requests are rejected
                              # (except EMERGENCY_OFF)
