from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),  # 将根路径映射到 index 视图
    path('sample/end_effector/', views.sample_end_effector, name="sample_end_effector"),
    path('sample/trajectory/', views.sample_trajectory, name="sample_trajectory"),
    path('sample/trajectory/start/', views.trajectory_start, name='trajectory_start'),
    path('sample/trajectory/stop/', views.trajectory_stop, name='trajectory_stop'),

    path('replay/trajectory/', views.replay_trajectory, name='replay_trajectory'),

    path('start_data_collection/', views.start_data_collection_view, name='start_data_collection'),

    path('stop_data_collection/', views.stop_data_collection_view, name='stop_data_collection'),
]
