# robotarm_interface/msg/CartesianStiffness.msg
# Cartesian spring stiffness, linear in N/m, angular in Nm/rad (diagonal in the selected frame).
# header.frame_id selects the frame like for twist_cmds: '' or base link → base, tcp → tool.

std_msgs/Header header
geometry_msgs/Vector3 linear
geometry_msgs/Vector3 angular