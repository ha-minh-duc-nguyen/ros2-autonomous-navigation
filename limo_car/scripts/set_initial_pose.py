#!/usr/bin/env python3
import math

import rclpy
from geometry_msgs.msg import PoseWithCovarianceStamped
from rclpy.node import Node
from rclpy.time import Time


class SetInitialPose(Node):
    def __init__(self):
        super().__init__('set_initial_pose')

        self.frame_id = self.declare_parameter('frame_id', 'map').value
        self.x = float(self.declare_parameter('x', 0.01).value)
        self.y = float(self.declare_parameter('y', 0.00).value)
        self.yaw = float(self.declare_parameter('yaw', -0.01).value)
        self.startup_delay = float(self.declare_parameter('startup_delay', 0.5).value)
        self.repeat_count = int(self.declare_parameter('repeat_count', 2).value)
        self.publish_period = float(self.declare_parameter('publish_period', 0.3).value)

        self.pub = self.create_publisher(PoseWithCovarianceStamped, '/initialpose', 10)
        self.start_time = self.get_clock().now()
        self.sent = 0
        self.finish_timer = None
        self.timer = self.create_timer(self.publish_period, self.loop)

    def loop(self):
        elapsed = (self.get_clock().now() - self.start_time).nanoseconds / 1e9
        if elapsed < self.startup_delay:
            return

        msg = PoseWithCovarianceStamped()

        # Use time 0 so TF uses the latest available transform.
        msg.header.stamp = Time(seconds=0).to_msg()
        msg.header.frame_id = self.frame_id

        msg.pose.pose.position.x = self.x
        msg.pose.pose.position.y = self.y
        msg.pose.pose.orientation.z = math.sin(self.yaw / 2.0)
        msg.pose.pose.orientation.w = math.cos(self.yaw / 2.0)

        msg.pose.covariance[0] = 0.25
        msg.pose.covariance[7] = 0.25
        msg.pose.covariance[35] = 0.10

        self.pub.publish(msg)
        self.sent += 1

        if self.sent >= self.repeat_count:
            self.get_logger().info('Initial pose published.')
            self.timer.cancel()
            self.finish_timer = self.create_timer(0.2, self.finish)

    def finish(self):
        if self.finish_timer is not None:
            self.finish_timer.cancel()
        if rclpy.ok():
            rclpy.shutdown()


def main():
    rclpy.init()
    node = SetInitialPose()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        if node is not None:
            node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
