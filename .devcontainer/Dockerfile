FROM ros:kilted-ros-base

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    python3-pip \
    git \
    python3-colcon-common-extensions \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /robotarm_interface

RUN rosdep update

RUN echo "source /opt/ros/$ROS_DISTRO/setup.bash" >> ~/.bashrc