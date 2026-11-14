#!/usr/bin/env python3
import subprocess

import rclpy
from rclpy.node import Node
from rclpy.qos import DurabilityPolicy, QoSProfile, ReliabilityPolicy
from std_msgs.msg import String


class RobotDescriptionPublisher(Node):
    def __init__(self):
        super().__init__('robot_description_publisher')

        xacro_file = self.declare_parameter('xacro_file', '').value
        publish_period = float(self.declare_parameter('publish_period', 1.0).value)

        if not xacro_file:
            raise RuntimeError('xacro_file parameter is empty')

        xml = subprocess.check_output(['xacro', xacro_file], text=True)

        qos = QoSProfile(depth=1)
        qos.durability = DurabilityPolicy.TRANSIENT_LOCAL
        qos.reliability = ReliabilityPolicy.RELIABLE

        self.pub = self.create_publisher(String, 'robot_description', qos)
        self.msg = String(data=xml)
        self.timer = self.create_timer(publish_period, self.publish_description)
        self.publish_description()

    def publish_description(self):
        self.pub.publish(self.msg)


def main():
    rclpy.init()
    node = RobotDescriptionPublisher()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
