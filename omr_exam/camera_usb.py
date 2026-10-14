"""
omr_exam/camera_usb.py — Kết nối Camera điện thoại Android qua USB Type-C:
- Tự động nhận diện thiết bị camera USB cắm vào máy tính.
- Chuẩn UVC (USB Video Class) tích hợp sẵn trên Android 14+ khi chọn chế độ "Webcam".
- Tương thích tốt với các app chuyển camera USB (Camo, DroidCam USB, Iriun USB).
- Cung cấp luồng hình ảnh thời gian thực (Live Preview).
- Hỗ trợ chụp nhanh liên tục (Auto/Manual Trigger) và gửi trực tiếp sang OMR Grader.
"""
from __future__ import annotations
try:
    import cv2
except Exception:
    cv2 = None
import threading
import time
from typing import List, Tuple, Optional, Callable


class USBCameraManager:
    """Quản lý kết nối và luồng camera điện thoại qua USB."""
    
    def __init__(self):
        self._cap: Optional[cv2.VideoCapture] = None
        self._current_device_id: int = -1
        self._is_running: bool = False
        self._lock = threading.Lock()
        self._current_frame = None
        self._thread: Optional[threading.Thread] = None

    @staticmethod
    def get_dshow_device_names() -> List[str]:
        """Lấy danh sách tên thiết bị DirectShow video theo đúng thứ tự index."""
        import subprocess
        import re
        try:
            res = subprocess.run(['ffmpeg', '-list_devices', 'true', '-f', 'dshow', '-i', 'dummy'],
                                 capture_output=True, text=True, errors='ignore', timeout=2)
            devs = re.findall(r'"([^"]+)"\s+\(video\)', res.stderr)
            if devs:
                return devs
        except Exception:
            pass

        try:
            cmd = 'Get-PnpDevice -Class Camera -Status OK -ErrorAction SilentlyContinue | Select-Object -ExpandProperty FriendlyName'
            out = subprocess.check_output(['powershell', '-NoProfile', '-Command', cmd], text=True, errors='ignore', timeout=3)
            pnp = [l.strip() for l in out.strip().split('\n') if l.strip()]
            pnp = [n for n in pnp if 'IR ' not in n and 'Infrared' not in n]
            if pnp:
                return pnp
        except Exception:
            pass
        return []

    @staticmethod
    def list_available_cameras(max_check: int = 6) -> List[Tuple[int, str]]:
        """Quét và tìm các thiết bị Camera đang kết nối qua cổng USB / DirectShow."""
        try:
            cv2.utils.logging.setLogLevel(cv2.utils.logging.LOG_LEVEL_SILENT)
        except Exception:
            pass

        dev_names = USBCameraManager.get_dshow_device_names()

        available = []
        num_devices = max(max_check, len(dev_names))
        for dev_id in range(num_devices):
            cap = cv2.VideoCapture(dev_id, cv2.CAP_DSHOW)
            if not cap.isOpened():
                cap = cv2.VideoCapture(dev_id)
            if cap.isOpened():
                ret, _ = cap.read()
                if ret:
                    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                    raw_name = dev_names[dev_id] if dev_id < len(dev_names) else f"Camera {dev_id}"
                    
                    # Kiểm tra nếu là camera điện thoại (Iriun, DroidCam, Camo, Android, Phone, Samsung...)
                    is_phone = any(k in raw_name.lower() for k in ["iriun", "droidcam", "camo", "phone", "android", "samsung", "epoccam"])
                    if is_phone:
                        label = f"Cam {dev_id}: 📱 {raw_name} (Điện Thoại) ({w}x{h})"
                    else:
                        label = f"Cam {dev_id}: {raw_name} ({w}x{h})"
                    available.append((dev_id, label, is_phone))
                cap.release()

        # Tự động ưu tiên camera điện thoại lên đầu danh sách để giao diện tự chọn
        available.sort(key=lambda x: (0 if x[2] else 1, x[0]))
        return [(item[0], item[1]) for item in available]

    def start_camera(self, device_id: int = 1, width: int = 1920, height: int = 1080) -> bool:
        """Bật camera với độ phân giải cao để quét phiếu rõ nét (tự động dự phòng nếu thiết bị chỉ định bận)."""
        self.stop_camera()
        
        # Thử mở thiết bị được yêu cầu trước, nếu không được tự động thử các index khác (1, 0, 2)
        candidates = [device_id]
        for fallback_id in [1, 0, 2]:
            if fallback_id not in candidates:
                candidates.append(fallback_id)
                
        for dev in candidates:
            # Thử DirectShow trước
            cap = cv2.VideoCapture(dev, cv2.CAP_DSHOW)
            if not cap.isOpened():
                cap = cv2.VideoCapture(dev)
                
            if cap.isOpened():
                # Thử đọc thử 1 frame xem thiết bị có thực sự truyền dữ liệu hình ảnh không
                ret, frame = cap.read()
                if ret and frame is not None:
                    # Đặt độ phân giải Full HD (hoặc HD) để nhận diện ô tô tốt nhất
                    cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
                    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
                    cap.set(cv2.CAP_PROP_AUTOFOCUS, 1)
                    
                    self._cap = cap
                    self._current_device_id = dev
                    self._is_running = True
                    
                    self._thread = threading.Thread(target=self._read_loop, daemon=True)
                    self._thread.start()
                    return True
                else:
                    cap.release()
                    
        return False

    def _read_loop(self):
        """Vòng lặp đọc khung hình liên tục."""
        while self._is_running and self._cap and self._cap.isOpened():
            ret, frame = self._cap.read()
            if ret:
                with self._lock:
                    self._current_frame = frame
            time.sleep(0.015)  # ~60 FPS

    def get_latest_frame(self):
        """Lấy khung hình mới nhất để hiển thị giao diện hoặc chấm bài."""
        with self._lock:
            if self._current_frame is not None:
                return self._current_frame.copy()
        return None

    def capture_snapshot(self) -> Optional[any]:
        """Chụp một ảnh tĩnh chất lượng cao từ camera."""
        return self.get_latest_frame()

    def stop_camera(self):
        """Giải phóng camera."""
        self._is_running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=0.5)
            self._thread = None
        if self._cap:
            self._cap.release()
            self._cap = None
        self._current_device_id = -1
        self._current_frame = None

    @property
    def is_active(self) -> bool:
        return self._is_running and self._cap is not None and self._cap.isOpened()
