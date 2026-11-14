from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, RegisterEventHandler, TimerAction
from launch.event_handlers import OnProcessExit
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    pkg_share = FindPackageShare('limo_car')

    nav2_launch = PathJoinSubstitution([
        pkg_share, 'launch', 'limo_car_nav2.launch.py'
    ])

    box_model = PathJoinSubstitution([
        pkg_share, 'models', 'moving_box', 'model.sdf'
    ])

    spawn_box = Node(
        package='gazebo_ros',
        executable='spawn_entity.py',
        name='spawn_moving_box',
        output='screen',
        arguments=[
            '-entity', 'moving_box',
            '-file', box_model,
            '-x', '2.20',
            '-y', '-1.10',
            '-z', '0.30'
        ]
    )

    move_box = Node(
        package='limo_car',
        executable='dynamic_obstacle.py',
        name='dynamic_obstacle',
        output='screen',
        parameters=[{
            'entity_name': 'moving_box',
            'service_name': '/set_entity_state',
            'x': 2.20,
            'z': 0.30,
            'start_y': -1.10,
            'y_min': -1.10,
            'y_max': 0.10,
            'speed': 0.18
        }]
    )

    start_move_box = RegisterEventHandler(
        OnProcessExit(
            target_action=spawn_box,
            on_exit=[
                TimerAction(
                    period=2.0,
                    actions=[move_box]
                )
            ]
        )
    )

    return LaunchDescription([
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(nav2_launch)
        ),

        TimerAction(
            period=8.0,
            actions=[spawn_box]
        ),

        start_move_box,
    ])
