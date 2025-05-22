from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),  # 将根路径映射到 index 视图
    path('sample/end_effector/', views.sample_end_effector, name="sample_end_effector"),

    path('sample/gripper/', views.sample_gripper_state, name="sample_gripper"),
    path('sample/trajectory/', views.sample_trajectory, name="sample_trajectory"),
    path('sample/trajectory/start/', views.trajectory_start, name='trajectory_start'),
    path('sample/trajectory/stop/', views.trajectory_stop, name='trajectory_stop'),

    path('replay/trajectory/', views.replay_trajectory, name='replay_trajectory'),

    path('start_data_collection/', views.start_data_collection_view, name='start_data_collection'),

    path('stop_data_collection/', views.stop_data_collection_view, name='stop_data_collection'),

    # 保存位姿接口
    path('save/pose/', views.save_pose, name='save_pose'),

    # 获取已保存位姿接口
    path('get/saved_poses/', views.get_saved_poses, name='get_saved_poses'),

    # 保存采轨信息接口
    path('save/trajectory/', views.save_trajectory, name='save_trajectory'),

    # 查看已保存轨迹接口
    path('get/saved_trajectories/', views.get_saved_trajectories, name='get_saved_trajectories'),

    path('save/gripper_state/', views.save_gripper_state, name='save_gripper_state'),
    path('get/saved_gripper_states/', views.get_saved_gripper_states, name='get_saved_gripper_states'),

    path('move/gripper/', views.move_gripper, name='move_gripper'),

    path('grip/gripper/', views.grip_gripper, name='grip_gripper'),


]
