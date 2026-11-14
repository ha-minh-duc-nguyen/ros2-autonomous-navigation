from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    ExecuteProcess,
    IncludeLaunchDescription,
    RegisterEventHandler,
    TimerAction,
)
from launch.conditions import IfCondition
from launch.event_handlers import OnProcessStart
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    pkg_share = FindPackageShare('limo_car')

    sim_launch = PathJoinSubstitution([
        pkg_share,
        'launch',
        'limo_car_sim.launch.py'
    ])

    slam_params = PathJoinSubstitution([
        pkg_share,
        'config',
        'slam_toolbox.yaml'
    ])

    rviz_config = PathJoinSubstitution([
        pkg_share,
        'rviz',
        'slam_config.rviz'
    ])

    rviz_arg = DeclareLaunchArgument('rviz', default_value='true')
    teleop_arg = DeclareLaunchArgument('teleop', default_value='false')

    rviz = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        output='screen',
        arguments=['-d', rviz_config],
        parameters=[{'use_sim_time': True}],
        condition=IfCondition(LaunchConfiguration('rviz'))
    )

    teleop = ExecuteProcess(
        cmd=[
            'gnome-terminal',
            '--',
            'bash',
            '-lc',
            'source /opt/ros/humble/setup.bash && '
            'source ~/limo_ws/install/setup.bash && '
            'ros2 run limo_car wasd_teleop.py; exec bash'
        ],
        output='screen',
        condition=IfCondition(LaunchConfiguration('teleop'))
    )

    delayed_teleop_after_rviz = RegisterEventHandler(
        OnProcessStart(
            target_action=rviz,
            on_start=[
                TimerAction(
                    period=10.0,
                    actions=[teleop]
                )
            ]
        )
    )

    return LaunchDescription([
        rviz_arg,
        teleop_arg,
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(sim_launch)
        ),
        Node(
            package='slam_toolbox',
            executable='async_slam_toolbox_node',
            name='slam_toolbox',
            output='screen',
            parameters=[slam_params]
        ),
        rviz,
        delayed_teleop_after_rviz,
    ])
