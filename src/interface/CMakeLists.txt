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
  "msg/StopCommand.msg"
  "msg/MotorParameter.msg"
  "msg/SystemState.msg"
  "msg/HardwareActions.msg"
  "msg/HardwareCommand.msg"
  "msg/HardwareFeedback.msg"
  "msg/HeartbeatQuery.msg"
  "msg/Heartbeat.msg"
  "msg/AxisData.msg"
  "msg/JointAngles.msg"
  "msg/TelemetryFrame.msg"
  "msg/TelemetryBatch.msg"
  "msg/TrajectoryFrame.msg"
  "msg/TrajectoryBatch.msg"
  "msg/TrajectoryFeedback.msg"
  "srv/CANFDTunnel.srv"
  "srv/RequestAction.srv"
  "action/ConfigMotor.action"
  "action/ReadMotorConfigs.action"
  "action/Mission.action"
  "action/PlanJointSpace.action"
  "action/PlanCSV.action"
  DEPENDENCIES builtin_interfaces std_msgs
)

set(PYTHON_SCRIPT "${CMAKE_CURRENT_SOURCE_DIR}/../../build_cpp.py")

add_custom_target(run_custom_build_script ALL
    COMMAND python3 ${PYTHON_SCRIPT}
    WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}/../..
    COMMENT "Run build_cpp.py..."
)

add_library(protocol_headers INTERFACE)
add_dependencies(protocol_headers run_custom_build_script)

target_include_directories(protocol_headers INTERFACE
  $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
  $<INSTALL_INTERFACE:include>
)

install(DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}/../../include/ 
        DESTINATION include)
install(TARGETS protocol_headers
  EXPORT export_protocol_headers
  ARCHIVE DESTINATION lib
  LIBRARY DESTINATION lib
  RUNTIME DESTINATION bin
)

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  set(ament_cmake_copyright_FOUND TRUE)
  set(ament_cmake_cpplint_FOUND TRUE)
  ament_lint_auto_find_test_dependencies()
endif()

ament_export_targets(export_protocol_headers HAS_LIBRARY_TARGET)
ament_export_dependencies(rosidl_default_runtime)
ament_export_dependencies(rosidl_default_generators)

ament_package()