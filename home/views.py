import time

import panda_py
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from home.arm_controller.configs.config import ARM_URL
from home.arm_controller.src.controllers.camera import Camera
from home.arm_controller.src.controllers.data_recorder import DataRecorder
from home.arm_controller.src.logger.traj_logger import TrajectoryLogger
from home.arm_controller.src.replay.replay import Replay
from home.arm_controller.src.sampler.sampler import Sampler


# 全局状态，存储采集状态和数据
trajectory_state = {
    "recording": False,
    "start_time": None,
    "file_path": None,
    "file_name": None,
    # "q": None,
    # "dq": None
}

# 模块级全局变量
recorder = None
arm = panda_py.Panda(ARM_URL)
gripper = panda_py.libfranka.Gripper(ARM_URL)
camera = Camera()

def index(request):
    return render(request, 'home/index.html')  # 渲染模板文件


# 末端执行器的功能函数（获取位姿数据）
def sample_end_effector(request):
    sample = Sampler(arm, None)
    return JsonResponse({"result": sample.sample_pos()})  # 返回 JSON 数据

# 模拟轨迹采样的功能函数
def sample_trajectory(request):
    result = "轨迹点: (5, 7, 3), (6, 8, 4)"  # 这里是你实际函数返回的采样结果
    return JsonResponse({"result": result})  # 返回 JSON 数据


@csrf_exempt
def trajectory_start(request):
    """开始轨迹采集"""
    if trajectory_state["recording"]:
        return JsonResponse({"error": "Trajectory recording is already in progress."}, status=400)

    trajectory_state["recording"] = True
    trajectory_state["start_time"] = time.time()
    trajectory_state["file_path"] = request.POST.get("file_path")
    trajectory_state["file_name"] = request.POST.get("file_name")

    # 启动录制逻辑
    arm.teaching_mode(True)
    arm.enable_logging(100000)
    print("Trajectory start")
    return JsonResponse({"status": "started"})


@csrf_exempt
def trajectory_stop(request):
    """结束轨迹采集"""
    if not trajectory_state["recording"]:
        return JsonResponse({"error": "No active trajectory recording to stop."}, status=400)

    arm.teaching_mode(False)
    print("Trajectory stopped.")
    elapsed_time = time.time() - trajectory_state["start_time"]

    traj_logger = TrajectoryLogger()

    # 停止采集并获取数据
    log_data = arm.get_log()
    trajectory_state["recording"] = False
    # trajectory_state["q"] = log_data['q']
    # trajectory_state["dq"] = log_data['dq']
    data = log_data['q'], log_data['dq']
    traj_logger.write(data, trajectory_state["file_path"], trajectory_state["file_name"])
    # 返回采集结果
    return JsonResponse({
        "status": "stopped",
        "elapsed_time": elapsed_time,
        "file_path": trajectory_state["file_path"],
        "file_name": trajectory_state["file_name"]
    })

@csrf_exempt
def replay_trajectory(request):
    if request.method == 'POST':
        # 获取前端传递的路径和文件名
        file_path = request.POST.get('file_path', '')
        file_name = request.POST.get('file_name', '')

        if not file_path or not file_name:
            return JsonResponse({'error': '文件路径或文件名为空'}, status=400)

        # 合并完整路径
        full_path = f"{file_path}/{file_name}.h5"

        try:
            # 实例化 Replay 并执行重播
            replay = Replay(arm)
            replay.replay_trajectory(path=full_path)
            return JsonResponse({'message': '轨迹重播成功'}, status=200)
        except Exception as e:
            print(f"轨迹重播失败: {e}")
            return JsonResponse({'error': '轨迹重播失败，请检查文件路径和名称'}, status=500)
    else:
        return JsonResponse({'error': '仅支持 POST 请求'}, status=405)

@csrf_exempt
def start_data_collection_view(request):
    global recorder

    # 检查是否有正在运行的采集任务
    if recorder and recorder.is_alive():
        return JsonResponse({'status': 'error', 'message': 'Data collection is already running.'})

    # 从 POST 请求中获取文件路径
    save_path = request.POST.get('file_path')
    if not save_path:
        return JsonResponse({'status': 'error', 'message': 'File path is required.'})

    def on_data_saved():
        print("Data collection has been saved successfully.")

    print(save_path)
    # 初始化并启动数据采集器
    try:
        recorder = DataRecorder(arm, gripper, camera, save_path=save_path, callback=on_data_saved)
        recorder.start()  # 开始数据采集
        print("Data collection has started.")
        return JsonResponse({'status': 'success', 'message': 'Data collection started.'})
    except Exception as e:
        print(f"Failed to start data collection: {str(e)}")
        return JsonResponse({'status': 'error', 'message': f'Failed to start data collection: {str(e)}'})

@csrf_exempt
def stop_data_collection_view(request):
    global recorder

    if recorder and recorder.is_alive():
        recorder.stop_and_save()
        recorder = None
        return JsonResponse({'status': 'success', 'message': 'Recording stopped and saved.'})
    else:
        return JsonResponse({'status': 'error', 'message': 'No active recorder.'})
