#!/usr/bin/env python3
import rclpy
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from rclpy.node import Node
from sensor_msgs.msg import LaserScan
from std_srvs.srv import Empty
class AutoLocalize(Node):
    def __init__(self):
        super().__init__('auto_localize')
        self.cmd_topic=self.declare_parameter('cmd_topic','/cmd_vel').value
        self.odom_topic=self.declare_parameter('odom_topic','/odom').value
        self.scan_topic=self.declare_parameter('scan_topic','/scan').value
        self.service_name=self.declare_parameter('service_name','/reinitialize_global_localization').value
        self.startup_delay=float(self.declare_parameter('startup_delay',6.0).value)
        self.spin_time=float(self.declare_parameter('spin_time',10.0).value)
        self.angular_speed=float(self.declare_parameter('angular_speed',0.30).value)
        self.cmd_pub=self.create_publisher(Twist,self.cmd_topic,10)
        self.client=self.create_client(Empty,self.service_name)
        self.create_subscription(Odometry,self.odom_topic,self.odom_cb,10)
        self.create_subscription(LaserScan,self.scan_topic,self.scan_cb,10)
        self.start_time=self.get_clock().now(); self.last_odom_time=None; self.last_scan_time=None; self.started=False; self.spinning=False; self.spin_started_time=None; self.zero_sent=False; self.last_status_log_time=self.get_clock().now(); self.timer=self.create_timer(0.05,self.loop)
    def odom_cb(self,_): self.last_odom_time=self.get_clock().now()
    def scan_cb(self,_): self.last_scan_time=self.get_clock().now()
    def seconds_since(self,t0): return (self.get_clock().now()-t0).nanoseconds/1e9
    def maybe_log_waiting(self,msg):
        if self.seconds_since(self.last_status_log_time)>2.0: self.get_logger().info(msg); self.last_status_log_time=self.get_clock().now()
    def ready_topics(self):
        odom_ok=self.last_odom_time is not None and self.seconds_since(self.last_odom_time)<1.0
        scan_ok=self.last_scan_time is not None and self.seconds_since(self.last_scan_time)<1.0
        return odom_ok, scan_ok
    def loop(self):
        if not self.started:
            if self.seconds_since(self.start_time)<self.startup_delay: return
            odom_ok,scan_ok=self.ready_topics()
            if not odom_ok or not scan_ok: self.maybe_log_waiting(f'Waiting for topics... odom_ok={odom_ok}, scan_ok={scan_ok}'); return
            if not self.client.wait_for_service(timeout_sec=0.2): self.maybe_log_waiting(f'Waiting for {self.service_name} ...'); return
            self.get_logger().info('Calling global relocalization service ...'); self.client.call_async(Empty.Request()); self.started=True; self.spinning=True; self.spin_started_time=self.get_clock().now(); return
        if self.spinning:
            if self.seconds_since(self.spin_started_time)<=self.spin_time:
                msg=Twist(); msg.angular.z=self.angular_speed; self.cmd_pub.publish(msg); return
            self.spinning=False
        if not self.zero_sent: self.cmd_pub.publish(Twist()); self.zero_sent=True; self.get_logger().info('Auto localization spin complete.')
def main():
    rclpy.init(); node=AutoLocalize()
    try: rclpy.spin(node)
    except KeyboardInterrupt: pass
    finally:
        node.cmd_pub.publish(Twist()); node.destroy_node();
        if rclpy.ok(): rclpy.shutdown()
if __name__=='__main__': main()
