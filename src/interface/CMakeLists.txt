cmake_minimum_required(VERSION 3.8)
project(interface)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

find_package(ament_cmake REQUIRED)
find_package(std_msgs REQUIRED)
find_package(rosidl_default_generators REQUIRED)
find_package(builtin_interfaces REQUIRED)

rosidl_generate_interfaces(${PROJECT_NAME}
  "msg/MotorParameter.msg"
  "msg/SystemState.msg"
  "msg/TrajectoryStatus.msg"
  "msg/HeartbeatQuery.msg"
  "msg/Heartbeat.msg"
  "msg/AxisData.msg"
  "msg/TelemetryFrame.msg"
  "msg/TelemetryBatch.msg"
  "msg/TrajectoryFrame.msg"
  "msg/TrajectoryBatch.msg"
  "msg/TrajectoryQuery.msg"
  "srv/CANFDTunnel.srv"
  "srv/RequestAction.srv"
  "action/ConfigMotor.action"
  "action/Mission.action"
  DEPENDENCIES builtin_interfaces std_msgs
)

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  set(ament_cmake_copyright_FOUND TRUE)
  set(ament_cmake_cpplint_FOUND TRUE)
  ament_lint_auto_find_test_dependencies()
endif()

ament_package()