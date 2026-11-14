#!/usr/bin/env python3
import rclpy
from gazebo_msgs.msg import EntityState
from gazebo_msgs.srv import SetEntityState
from rclpy.node import Node


class DynamicObstacle(Node):
    def __init__(self):
        super().__init__('dynamic_obstacle')

        self.entity_name = self.declare_parameter('entity_name', 'moving_box').value
        self.service_name = self.declare_parameter('service_name', '/set_entity_state').value
        self.x = float(self.declare_parameter('x', 0.75).value)
        self.z = float(self.declare_parameter('z', 0.30).value)
        self.y_min = float(self.declare_parameter('y_min', -0.8).value)
        self.y_max = float(self.declare_parameter('y_max', 0.8).value)
        self.current_y = float(self.declare_parameter('start_y', 0.0).value)
        self.speed = float(self.declare_parameter('speed', 0.25).value)

        self.direction = 1.0
        self.last_time = self.get_clock().now()
        self.pending_future = None

        self.client = self.create_client(SetEntityState, self.service_name)

        self.get_logger().info(f'Dynamic obstacle node started for entity: {self.entity_name}')
        self.get_logger().info(f'Using service: {self.service_name}')

        # Wait properly for Gazebo service
        while not self.client.wait_for_service(timeout_sec=1.0):
            self.get_logger().warn(f'Waiting for service {self.service_name}...')

        self.get_logger().info(f'Connected to service {self.service_name}')

        self.timer = self.create_timer(0.1, self.loop)

    def loop(self):
        if self.pending_future is not None and not self.pending_future.done():
            return

        now = self.get_clock().now()
        dt = (now - self.last_time).nanoseconds / 1e9
        self.last_time = now

        self.current_y += self.direction * self.speed * dt

        if self.current_y > self.y_max:
            self.current_y = self.y_max
            self.direction = -1.0
        elif self.current_y < self.y_min:
            self.current_y = self.y_min
            self.direction = 1.0

        req = SetEntityState.Request()
        req.state = EntityState()
        req.state.name = self.entity_name
        req.state.reference_frame = 'world'

        req.state.pose.position.x = self.x
        req.state.pose.position.y = self.current_y
        req.state.pose.position.z = self.z
        req.state.pose.orientation.w = 1.0

        req.state.twist.linear.y = self.direction * self.speed

        self.pending_future = self.client.call_async(req)
        self.pending_future.add_done_callback(self.response_callback)

    def response_callback(self, future):
        try:
            result = future.result()
            if hasattr(result, 'success') and not result.success:
                self.get_logger().warn('SetEntityState returned success=False')
        except Exception as e:
            self.get_logger().error(f'Service call failed: {e}')
        finally:
            self.pending_future = None


def main():
    rclpy.init()
    node = DynamicObstacle()
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
