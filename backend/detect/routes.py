"""
视频检测接口

接口:
    POST /api/video/upload         - 上传视频文件
    WebSocket /ws/video/<video_id> - 实时返回处理进度和检测结果
"""
import os
import time
import uuid
import asyncio
import base64
import struct
from quart import Blueprint, jsonify, request, websocket
import cv2
import numpy as np
from core import FallDetector
from .risk_engine import risk_engine, RISK_COLORS_BGR, RISK_REASON_LABELS

detect_bp = Blueprint('detect', __name__)

# 视频存储目录
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'videos')
os.makedirs(UPLOAD_DIR, exist_ok=True)

# 全局检测器实例
_detector = None

# 视频处理状态存储
video_status = {}  # video_id -> {status, progress, results, total_frames}


def get_detector() -> FallDetector:
    """获取全局检测器实例"""
    global _detector
    if _detector is None:
        _detector = FallDetector(model_path="core/models/fall_detection_v1.onnx")
    return _detector


@detect_bp.route('/api/video/upload', methods=['POST'])
async def upload_video():
    """
    上传视频文件

    Returns:
        {"video_id": "xxx", "filename": "xxx.mp4"}
    """
    files = await request.files
    if 'video' not in files:
        return jsonify({'error': '未找到视频文件'}), 400

    video_file = files['video']
    if not video_file.filename:
        return jsonify({'error': '文件名为空'}), 400

    # 生成唯一ID
    video_id = str(uuid.uuid4())[:8]

    # 保存文件
    ext = os.path.splitext(video_file.filename)[1] or '.mp4'
    filename = f"{video_id}{ext}"
    filepath = os.path.join(UPLOAD_DIR, filename)

    await video_file.save(filepath)

    # 初始化状态
    video_status[video_id] = {
        'status': 'uploaded',
        'progress': 0,
        'total_frames': 0,
        'results': []
    }

    return jsonify({
        'video_id': video_id,
        'filename': video_file.filename
    })


@detect_bp.websocket('/ws/video/<video_id>')
async def process_video_ws(video_id: str):
    """
    WebSocket 视频处理

    发送格式:
    {
        "type": "progress" | "frame" | "complete" | "error",
        "progress": 0-100,        // 进度时
        "frame_id": 1.5,          // 帧结果时
        "persons": [...],         // 帧结果时，每人含 risk_level/risk_reason/box
        "total_frames": 100,      // 完成时
        "results": [...]          // 完成时
    }
    """
    # 查找视频文件
    video_path = None
    for ext in ['.mp4', '.avi', '.mov', '.mkv', '.webm']:
        candidate = os.path.join(UPLOAD_DIR, f"{video_id}{ext}")
        if os.path.exists(candidate):
            video_path = candidate
            break

    if not video_path:
        await websocket.send_json({'type': 'error', 'message': '视频文件不存在'})
        await websocket.close()
        return

    detector = get_detector()
    session_id = detector.create_session()
    risk_engine.create_session(session_id, is_live=False)

    try:
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            await websocket.send_json({'type': 'error', 'message': '无法打开视频文件'})
            await websocket.close()
            return

        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS) or 25
        frame_interval = 1

        await websocket.send_json({
            'type': 'info',
            'total_frames': total_frames,
            'fps': fps,
            'frame_interval': frame_interval
        })

        frame_count = 0
        processed_count = 0
        all_results = []

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            frame_count += 1

            if frame_count % frame_interval == 0:
                frame_time = frame_count / fps
                resized = cv2.resize(frame, (640, 480))

                # 检测
                result = await detector.process_frame_async(session_id, resized)
                now = time.time()

                # 风险判定
                risk_results = risk_engine.process(
                    session_id, result.frame_result.persons, now
                )

                # 在帧上绘制风险框
                for risk in risk_results:
                    x1, y1, x2, y2 = [int(x) for x in risk.box]
                    color = RISK_COLORS_BGR.get(risk.risk_level, (0, 255, 0))
                    cv2.rectangle(resized, (x1, y1), (x2, y2), color, 2)
                    cv2.putText(resized, risk.risk_level, (x1, y1 - 8),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

                # 编码帧图像
                _, buffer = cv2.imencode('.jpg', resized, [cv2.IMWRITE_JPEG_QUALITY, 80])
                frame_hex = buffer.tobytes().hex()

                frame_result = {
                    'type': 'frame',
                    'frame_id': round(frame_time, 2),
                    'frame_number': frame_count,
                    'image': frame_hex,
                    'persons': [
                        {
                            'person_id': r.person_id,
                            'box': [round(x, 1) for x in r.box],
                            'risk_level': r.risk_level,
                            'risk_reason': r.risk_reason,
                        }
                        for r in risk_results
                    ],
                }

                all_results.append(frame_result)
                processed_count += 1

                await websocket.send_json(frame_result)

                progress = int((frame_count / total_frames) * 100)
                await websocket.send_json({
                    'type': 'progress',
                    'progress': progress,
                    'processed': processed_count
                })

        cap.release()
        detector.close_session(session_id)
        risk_engine.close_session(session_id)

        await websocket.send_json({
            'type': 'complete',
            'total_frames': frame_count,
            'processed_frames': processed_count,
            'results': all_results
        })

    except Exception as e:
        await websocket.send_json({'type': 'error', 'message': str(e)})
    finally:
        await websocket.close(1000)  # 1000 = 正常关闭


# ── 实时帧检测接口（供摄像头使用） ──────────────────────────

@detect_bp.route('/api/session/create', methods=['POST'])
async def create_session():
    """创建实时检测会话"""
    detector = get_detector()
    video_id = detector.create_session()
    risk_engine.create_session(video_id, is_live=True)
    return jsonify({'video_id': video_id})


@detect_bp.route('/api/session/close/<video_id>', methods=['POST'])
async def close_session(video_id: str):
    """关闭实时检测会话"""
    detector = get_detector()
    success = detector.close_session(video_id)
    risk_engine.close_session(video_id)
    return jsonify({'success': success})


@detect_bp.websocket('/ws/detect/<video_id>')
async def detect_ws(video_id: str):
    """WebSocket 实时帧检测（摄像头）"""
    detector = get_detector()

    if detector.session_manager.get_session(video_id) is None:
        await websocket.send_json({'error': 'Invalid video_id'})
        await websocket.close()
        return

    while True:
        try:
            data = await websocket.receive()

            if isinstance(data, bytes):
                frame = decode_jpeg(data)
            elif isinstance(data, str):
                frame_bytes = base64.b64decode(data)
                frame = decode_jpeg(frame_bytes)
            else:
                continue

            if frame is None:
                await websocket.send_json({'error': 'Invalid frame data'})
                continue

            result = await detector.process_frame_async(video_id, frame)
            now = time.time()
            risk_results = risk_engine.process(video_id, result.frame_result.persons, now)
            response = build_response(result.frame_result.detected, risk_results)
            await websocket.send_json(response)

        except Exception as e:
            print(f"WebSocket error: {e}")
            break


def decode_jpeg(data: bytes) -> np.ndarray:
    """解码 JPEG 字节流为 BGR 图像"""
    try:
        arr = np.frombuffer(data, dtype=np.uint8)
        frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        return frame
    except Exception:
        return None


def build_response(detected: bool, risk_results) -> dict:
    """构建给前端的 JSON 响应"""
    return {
        'detected': detected,
        'persons': [
            {
                'person_id': r.person_id,
                'box': [round(x, 1) for x in r.box],
                'risk_level': r.risk_level,
                'risk_reason': r.risk_reason,
            }
            for r in risk_results
        ],
    }
