from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, TimerAction
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    pkg_share = FindPackageShare('limo_car')
    nav2_share = FindPackageShare('nav2_bringup')

    default_map = PathJoinSubstitution([pkg_share, 'maps', 'week5_map.yaml'])
    default_nav2_params = PathJoinSubstitution([pkg_share, 'config', 'nav2_params.yaml'])
    sim_launch = PathJoinSubstitution([pkg_share, 'launch', 'limo_car_sim.launch.py'])
    nav2_launch = PathJoinSubstitution([nav2_share, 'launch', 'bringup_launch.py'])
    rviz_config = PathJoinSubstitution([pkg_share, 'rviz', 'nav2_config.rviz'])

    map_arg = DeclareLaunchArgument('map', default_value=default_map)
    nav2_params_arg = DeclareLaunchArgument('nav2_params_file', default_value=default_nav2_params)
    rviz_arg = DeclareLaunchArgument('rviz', default_value='true')
    set_initial_pose_arg = DeclareLaunchArgument('set_initial_pose', default_value='true')
    auto_localize_arg = DeclareLaunchArgument('auto_localize', default_value='false')
    init_x_arg = DeclareLaunchArgument('initial_pose_x', default_value='0.27')
    init_y_arg = DeclareLaunchArgument('initial_pose_y', default_value='-0.73')
    init_yaw_arg = DeclareLaunchArgument('initial_pose_yaw', default_value='0.0')

    rviz = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        output='screen',
        arguments=['-d', rviz_config],
        parameters=[{'use_sim_time': True}],
        condition=IfCondition(LaunchConfiguration('rviz'))
    )

    initial_pose = Node(
        package='limo_car',
        executable='set_initial_pose.py',
        name='set_initial_pose',
        output='screen',
        parameters=[{
            'startup_delay': 0.5,
            'repeat_count': 2,
            'publish_period': 0.3,
            'frame_id': 'map',
            'x': LaunchConfiguration('initial_pose_x'),
            'y': LaunchConfiguration('initial_pose_y'),
            'yaw': LaunchConfiguration('initial_pose_yaw'),
            'use_sim_time': True
        }],
        condition=IfCondition(LaunchConfiguration('set_initial_pose'))
    )

    auto_localize = Node(
        package='limo_car',
        executable='auto_localize.py',
        name='auto_localize',
        output='screen',
        parameters=[{
            'cmd_topic': '/cmd_vel',
            'service_name': '/reinitialize_global_localization',
            'startup_delay': 0.0,
            'spin_time': 10.0,
            'angular_speed': 0.30,
            'use_sim_time': True
        }],
        condition=IfCondition(LaunchConfiguration('auto_localize'))
    )

    delayed_nav2 = TimerAction(
        period=10.0,
        actions=[
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(nav2_launch),
                launch_arguments={
                    'slam': 'False',
                    'map': LaunchConfiguration('map'),
                    'use_sim_time': 'True',
                    'params_file': LaunchConfiguration('nav2_params_file'),
                    'autostart': 'True',
                    'use_composition': 'False',
                }.items()
            )
        ]
    )

    delayed_initial_pose = TimerAction(
        period=13.0,
        actions=[initial_pose]
    )

    delayed_auto_localize = TimerAction(
        period=15.0,
        actions=[auto_localize]
    )

    delayed_rviz = TimerAction(
        period=15.0,
        actions=[rviz]
    )

    return LaunchDescription([
        map_arg,
        nav2_params_arg,
        rviz_arg,
        set_initial_pose_arg,
        auto_localize_arg,
        init_x_arg,
        init_y_arg,
        init_yaw_arg,
        IncludeLaunchDescription(PythonLaunchDescriptionSource(sim_launch)),
        delayed_nav2,
        delayed_initial_pose,
        delayed_auto_localize,
        delayed_rviz,
    ])
