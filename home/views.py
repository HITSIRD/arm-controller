import json
import os
import time

import panda_py
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from home.arm_controller.configs.config import ARM_URL, SAVE_FILE_PATH, TRAJECTORY_FILE_PATH, GRIPPER_STATE_FILE_PATH
from home.arm_controller.src.controllers.arm_controller import ArmController
from home.arm_controller.src.controllers.camera import Camera, CameraThread
from home.arm_controller.src.controllers.data_recorder import DataRecorder
from home.arm_controller.src.controllers.hand_controller import HandController
from home.arm_controller.src.logger.traj_logger import TrajectoryLogger
from home.arm_controller.src.replay.replay import Replay
from home.arm_controller.src.sampler.sampler import Sampler
from home.arm_controller.src.scripts.sub_operation import process_suboperation_data, process_skill_data

# 全局状态，存储采集状态和数据
trajectory_state = {
    "recording": False,
    "start_time": None,
    "file_path": None,
    "file_name": None,
    # "q": None,
    # "dq": None
}

# Define a global variable for the camera thread

# 模块级全局变量
recorder = None
arm = panda_py.Panda(ARM_URL)
gripper = panda_py.libfranka.Gripper(ARM_URL)
camera = Camera()
frame = None
current_skill = None
skill_label = None
hand_controller = HandController(gripper)
#arm_controller = ArmController(arm)
def index(request):
    return render(request, 'home/index.html')  # 渲染模板文件


# 末端执行器的功能函数（获取位姿数据）
def sample_end_effector(request):
    sample = Sampler(arm, None)
    return JsonResponse({"result": sample.sample_pos()})  # 返回 JSON 数据

# 夹爪的功能函数（获取夹爪宽度数据）
def sample_gripper_state(request):
    #sample = Sampler(arm, None)
    hand_controller = HandController(gripper)
    return JsonResponse({"result": hand_controller.read_width()})  # 返回 JSON 数据


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
    print("Teaching mode on")
    arm.enable_logging(100000)
    print("Enabling logging")
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

@csrf_exempt
def save_pose(request):
    if request.method == 'POST':
        # 解析用户提交的 JSON 数据
        try:
            data = json.loads(request.body.decode('utf-8'))
            pose = data.get('pose')
            description = data.get('description')
            timestamp = data.get('timestamp')
        except (json.JSONDecodeError, KeyError):
            return JsonResponse({'status': 'error', 'message': 'Invalid input data'}, status=400)

        # 尝试读取现有的 JSON 文件，如果文件不存在或损坏，初始化为空列表
        saved_poses = []
        if os.path.exists(SAVE_FILE_PATH):  # 检查文件是否存在
            try:
                with open(SAVE_FILE_PATH, 'r') as f:
                    saved_poses = json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):  # 文件为空或损坏
                saved_poses = []

        # 添加新的数据到列表
        saved_poses.append({
            'pose': pose,
            'description': description,
            'timestamp': timestamp,
        })

        # 将数据写回 JSON 文件
        with open(SAVE_FILE_PATH, 'w') as f:
            json.dump(saved_poses, f, ensure_ascii=False, indent=4)

        return JsonResponse({'status': 'success'}, status=200)

    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)

@csrf_exempt
def get_saved_poses(request):
    try:
        with open(SAVE_FILE_PATH, 'r') as f:
            saved_poses = json.load(f)
        return JsonResponse({'poses': saved_poses})
    except FileNotFoundError:
        return JsonResponse({'poses': []})

@csrf_exempt
def save_trajectory(request):
    if request.method == 'POST':
        # 解析用户提交的 JSON 数据
        try:
            data = json.loads(request.body.decode('utf-8'))
            path = data.get('path')  # 文件路径
            file_name = data.get('file_name')  # 文件名
            description = data.get('description')  # 描述
            timestamp = data.get('timestamp')  # 时间戳
        except (json.JSONDecodeError, KeyError):
            return JsonResponse({'status': 'error', 'message': 'Invalid input data'}, status=400)

        # 初始化保存文件数据
        saved_trajectories = []
        if os.path.exists(TRAJECTORY_FILE_PATH):  # 检查是否存在轨迹文件
            try:
                with open(TRAJECTORY_FILE_PATH, 'r') as file:
                    saved_trajectories = json.load(file)
            except (json.JSONDecodeError, FileNotFoundError):  # 文件为空或损坏
                saved_trajectories = []

        # 添加新的轨迹条目到保存列表
        saved_trajectories.append({
            'path': path,
            'file_name': file_name,
            'description': description,
            'timestamp': timestamp,
        })

        # 保存文件
        with open(TRAJECTORY_FILE_PATH, 'w') as file:
            json.dump(saved_trajectories, file, ensure_ascii=False, indent=4)

        return JsonResponse({'status': 'success'}, status=200)

    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)

@csrf_exempt
def get_saved_trajectories(request):
    if request.method == 'GET':
        # 初始化轨迹列表
        saved_trajectories = []
        if os.path.exists(TRAJECTORY_FILE_PATH):  # 检查轨迹文件是否存在
            try:
                with open(TRAJECTORY_FILE_PATH, 'r') as file:
                    saved_trajectories = json.load(file)
            except (json.JSONDecodeError, FileNotFoundError):  # 文件为空或损坏
                saved_trajectories = []

        return JsonResponse({'status': 'success', 'trajectories': saved_trajectories}, status=200)

    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)


@csrf_exempt
def save_gripper_state(request):
    if request.method == 'POST':
        try:
            # 从 POST 请求的请求体中解析 JSON 数据
            data = json.loads(request.body.decode('utf-8'))
            state = data.get('state')  # 夹爪状态
            description = data.get('description')  # 夹爪状态描述
            timestamp = data.get('timestamp')  # 时间戳
        except (json.JSONDecodeError, KeyError):
            return JsonResponse({'status': 'error', 'message': 'Invalid input data'}, status=400)

        # 尝试读取现有的 JSON 文件，如果文件不存在或损坏，初始化为空列表
        saved_states = []
        if os.path.exists(GRIPPER_STATE_FILE_PATH):
            try:
                with open(GRIPPER_STATE_FILE_PATH, 'r') as f:
                    saved_states = json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):  # 文件为空或损坏
                saved_states = []

        # 添加新的夹爪状态到列表
        saved_states.append({
            'state': state,  # 夹爪状态
            'description': description,  # 描述
            'timestamp': timestamp,  # 时间戳
        })

        # 将数据写回到 JSON 文件
        with open(GRIPPER_STATE_FILE_PATH, 'w') as f:
            json.dump(saved_states, f, ensure_ascii=False, indent=4)

        return JsonResponse({'status': 'success'}, status=200)

    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)


@csrf_exempt
def get_saved_gripper_states(request):
    try:
        # 尝试从文件中读取保存的夹爪状态
        with open(GRIPPER_STATE_FILE_PATH, 'r') as f:
            saved_states = json.load(f)  # 读取 JSON 数据
        return JsonResponse({'states': saved_states})
    except FileNotFoundError:
        # 如果文件不存在，则返回空列表
        return JsonResponse({'states': []})

@csrf_exempt
def move_gripper(request):
    """
    移动夹爪接口
    POST 参数: { "width": float, "speed": float }
    """
    if request.method == 'POST':
        try:
            # 解析请求体的 JSON 数据
            data = json.loads(request.body.decode('utf-8'))
            width = float(data.get('width'))  # 夹爪宽度
            speed = float(data.get('speed'))  # 移动速度
        except (json.JSONDecodeError, ValueError, KeyError):
            return JsonResponse({'status': 'error', 'message': 'Invalid input data'}, status=400)

        try:
            # 调用 HandController 的 move_gripper 方法
            success = hand_controller.move_gripper(width, speed)
            print(success)
            if success:
                return JsonResponse({'status': 'success', 'message': 'Gripper moved successfully.'})
            else:
                return JsonResponse({'status': 'error', 'message': 'Failed to move gripper.'}, status=500)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)


@csrf_exempt
def grip_gripper(request):
    """
    执行夹取操作接口
    POST 参数: { "width": float, "speed": float, "force": float (可选) }
    """
    if request.method == 'POST':
        try:
            # 解析请求体的 JSON 数据
            data = json.loads(request.body.decode('utf-8'))
            width = float(data.get('width'))  # 夹爪宽度
            speed = float(data.get('speed'))  # 夹取速度
            force = float(data.get('force', 10.0))  # 夹取力度，默认为 10.0
        except (json.JSONDecodeError, ValueError, KeyError):
            return JsonResponse({'status': 'error', 'message': 'Invalid input data'}, status=400)

        try:
            # 调用 HandController 的 grasp 方法
            success = hand_controller.grasp(width, speed, force)
            if success:
                return JsonResponse({'status': 'success', 'message': 'Gripper gripped successfully.'})
            else:
                return JsonResponse({'status': 'error', 'message': 'Failed to grip.'}, status=500)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)

@csrf_exempt
def execute_skill(request):
    if request.method == "POST":
        try:
            # 解析请求的 JSON 数据
            body_unicode = request.body.decode('utf-8')
            body_data = json.loads(body_unicode)

            # 获取类型和数据
            skill_type = body_data.get('type')  # "skill" 或 "suboperation"
            current_skill = body_data.get('data')  # 包含完整的技能或子操作数据
            if skill_type == 'skill':
                # 如果是技能，解析技能数据（包括其子操作）
                processed_skill = process_skill_data(current_skill, arm, hand_controller)
                return JsonResponse({
                    'status': 'success',
                    'message': '技能执行成功！',
                    'processed_data': processed_skill  # 返回解析后的技能数据
                })

            elif skill_type == 'suboperation':
                # 如果是子操作，只处理自身
                processed_suboperation = process_suboperation_data(current_skill, arm, hand_controller)
                return JsonResponse({
                    'status': 'success',
                    'message': '子操作执行成功！',
                    'processed_data': processed_suboperation  # 返回解析后的子操作数据
                })
            else:
                return JsonResponse({
                    'status': 'error',
                    'message': '未知类型，请检查数据！'
                })

        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': f'数据解析失败：{str(e)}'
            })

    else:
        return JsonResponse({
            'status': 'error',
            'message': '仅支持 POST 请求！'
        })

