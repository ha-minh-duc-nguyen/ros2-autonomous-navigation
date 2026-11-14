from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command, LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    pkg_share = FindPackageShare('limo_car')
    gazebo_share = FindPackageShare('gazebo_ros')

    default_world = PathJoinSubstitution([pkg_share, 'worlds', 'final_world.world'])
    xacro_file = PathJoinSubstitution([pkg_share, 'urdf', 'limo_car.urdf.xacro'])

    world_arg = DeclareLaunchArgument('world', default_value=default_world)
    spawn_x_arg = DeclareLaunchArgument('spawn_x', default_value='0.0')
    spawn_y_arg = DeclareLaunchArgument('spawn_y', default_value='0.0')
    spawn_z_arg = DeclareLaunchArgument('spawn_z', default_value='0.15')

    robot_description = Command(['xacro', ' ', xacro_file])

    gzserver_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([gazebo_share, 'launch', 'gzserver.launch.py'])
        ),
        launch_arguments={
            'world': LaunchConfiguration('world'),
            'extra_gazebo_args': '-s libgazebo_ros_state.so'
        }.items(),
    )

    gzclient_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([gazebo_share, 'launch', 'gzclient.launch.py'])
        )
    )

    rsp = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        output='screen',
        parameters=[{
            'robot_description': ParameterValue(robot_description, value_type=str),
            'use_sim_time': True,
        }],
    )

    robot_desc_pub = Node(
        package='limo_car',
        executable='robot_description_publisher.py',
        output='screen',
        parameters=[{
            'xacro_file': xacro_file,
            'publish_period': 1.0,
            'use_sim_time': True,
        }],
    )

    spawner = Node(
        package='gazebo_ros',
        executable='spawn_entity.py',
        output='screen',
        arguments=[
            '-topic', 'robot_description',
            '-entity', 'limo_car',
            '-x', LaunchConfiguration('spawn_x'),
            '-y', LaunchConfiguration('spawn_y'),
            '-z', LaunchConfiguration('spawn_z'),
        ],
    )

    return LaunchDescription([
        world_arg,
        spawn_x_arg,
        spawn_y_arg,
        spawn_z_arg,
        gzserver_launch,
        gzclient_launch,
        rsp,
        robot_desc_pub,
        TimerAction(period=4.0, actions=[spawner]),
    ])
