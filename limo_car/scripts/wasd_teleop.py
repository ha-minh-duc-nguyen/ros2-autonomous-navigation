#!/usr/bin/env python3
import select, sys, termios, time, tty
import rclpy
from geometry_msgs.msg import Twist
from rclpy.node import Node

def clamp(x, lo, hi): return max(lo, min(hi, x))
class WasdTeleop(Node):
    def __init__(self):
        super().__init__('wasd_teleop')
        self.cmd_topic=self.declare_parameter('cmd_topic','/cmd_vel').value
        self.base_linear=float(self.declare_parameter('base_linear',0.10).value)
        self.base_angular=float(self.declare_parameter('base_angular',0.55).value)
        self.publish_rate=float(self.declare_parameter('publish_rate',40.0).value)
        self.hold_timeout=float(self.declare_parameter('hold_timeout',0.20).value)
        self.pub=self.create_publisher(Twist,self.cmd_topic,10)
        self.overall_scale=self.linear_scale=self.angular_scale=1.0
        self.current_key=None; self.last_key_time=0.0
        self.settings=termios.tcgetattr(sys.stdin); tty.setcbreak(sys.stdin.fileno())
        self.timer=self.create_timer(1.0/self.publish_rate,self.loop)
        self.get_logger().info('\nWASD teleop started\nW/S = forward/backward, A/D = left/right\n1 = all +10%, 2 = all -10%\n3 = linear +10%, 4 = linear -10%\n5 = angular +10%, 6 = angular -10%\n7 = print speeds, 8 = safe preset, 9 = fast preset\n0 = reset normal, X = stop, Q = quit\n')
    def get_key_nonblocking(self):
        dr,_,_=select.select([sys.stdin],[],[],0); return sys.stdin.read(1) if dr else None
    def report_scales(self): self.get_logger().info(f'overall={self.overall_scale:.2f}, linear={self.linear_scale:.2f}, angular={self.angular_scale:.2f}')
    def loop(self):
        now=time.monotonic(); key=self.get_key_nonblocking()
        if key is not None:
            key=key.lower()
            if key in ['w','a','s','d']: self.current_key=key; self.last_key_time=now
            elif key=='1': self.overall_scale=clamp(self.overall_scale*1.1,0.3,2.0); self.report_scales()
            elif key=='2': self.overall_scale=clamp(self.overall_scale*0.9,0.3,2.0); self.report_scales()
            elif key=='3': self.linear_scale=clamp(self.linear_scale*1.1,0.3,2.0); self.report_scales()
            elif key=='4': self.linear_scale=clamp(self.linear_scale*0.9,0.3,2.0); self.report_scales()
            elif key=='5': self.angular_scale=clamp(self.angular_scale*1.1,0.3,2.0); self.report_scales()
            elif key=='6': self.angular_scale=clamp(self.angular_scale*0.9,0.3,2.0); self.report_scales()
            elif key=='7': self.report_scales()
            elif key=='8': self.overall_scale=self.linear_scale=self.angular_scale=0.8; self.report_scales()
            elif key=='9': self.overall_scale=1.2; self.linear_scale=self.angular_scale=1.1; self.report_scales()
            elif key=='0': self.overall_scale=self.linear_scale=self.angular_scale=1.0; self.report_scales()
            elif key=='x': self.current_key=None; self.publish_stop()
            elif key=='q': raise KeyboardInterrupt
        lin=self.base_linear*self.overall_scale*self.linear_scale; ang=self.base_angular*self.overall_scale*self.angular_scale
        msg=Twist()
        if self.current_key and (now-self.last_key_time)<=self.hold_timeout:
            if self.current_key=='w': msg.linear.x=lin
            elif self.current_key=='s': msg.linear.x=-lin
            elif self.current_key=='a': msg.angular.z=ang
            elif self.current_key=='d': msg.angular.z=-ang
        else: self.current_key=None
        self.pub.publish(msg)
    def publish_stop(self): self.pub.publish(Twist())
    def destroy_node(self):
        try: termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.settings)
        except Exception: pass
        self.publish_stop(); super().destroy_node()
def main():
    rclpy.init(); node=WasdTeleop()
    try: rclpy.spin(node)
    except KeyboardInterrupt: pass
    finally: node.destroy_node(); rclpy.shutdown()
if __name__=='__main__': main()
