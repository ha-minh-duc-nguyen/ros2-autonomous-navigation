from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    pkg_share = FindPackageShare('limo_car')
    nav2_launch = PathJoinSubstitution([pkg_share, 'launch', 'limo_car_nav2.launch.py'])
    params_file = PathJoinSubstitution([pkg_share, 'config', 'nav2_params_smac_rpp.yaml'])

    return LaunchDescription([
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(nav2_launch),
            launch_arguments={'nav2_params_file': params_file}.items(),
        )
    ])
