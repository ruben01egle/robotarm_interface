# robotarm_interface/msg/CartesianIncrement.msg
# Relative step of the TCP. linear in m, angular in rad (per axis, not a rotation vector).
# header.frame_id selects the frame like for twist_cmds: '' or base link → base, tcp → tool.

std_msgs/Header header
geometry_msgs/Vector3 linear
geometry_msgs/Vector3 angular
