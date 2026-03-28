import math
from datetime import datetime

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QPainter, QPen
from PySide6.QtWidgets import QWidget


class SkyTrackWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._track = []  # list[dict]: {"az": float, "alt": float, "t": datetime}
        self._name = ""
        self._status = ""

    def set_track(self, name: str, track_points: list, status: str = ""):
        self._name = name or ""
        self._track = track_points or []
        self._status = status or ""
        self.update()

    def clear(self):
        self.set_track("", [], "")

    def _azalt_to_xy(self, az_deg: float, alt_deg: float, cx: float, cy: float, radius: float):
        alt_deg = max(0.0, min(90.0, alt_deg))
        r = (90.0 - alt_deg) / 90.0 * radius
        az_rad = math.radians(az_deg)
        # 地面视角：左东右西（E 在左，W 在右）
        x = cx - r * math.sin(az_rad)
        y = cy - r * math.cos(az_rad)
        return x, y

    @staticmethod
    def _fmt_phase_time(t) -> str:
        if isinstance(t, datetime):
            return t.strftime("%H:%M:%S")
        return ""

    def paintEvent(self, event):
        del event
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        rect = self.rect()
        w, h = rect.width(), rect.height()
        cx, cy = w / 2.0, h / 2.0
        margin = min(w, h) * 0.02
        radius = min(w, h) / 2.0 - margin

        painter.fillRect(rect, Qt.white)

        painter.setPen(QPen(Qt.black, 2))
        painter.drawEllipse(int(cx - radius), int(cy - radius), int(2 * radius), int(2 * radius))

        painter.setPen(QPen(Qt.lightGray, 1))
        for alt in (60, 30):
            rr = (90.0 - alt) / 90.0 * radius
            painter.drawEllipse(int(cx - rr), int(cy - rr), int(2 * rr), int(2 * rr))
        for az in range(0, 360, 45):
            x, y = self._azalt_to_xy(az, 0, cx, cy, radius)
            painter.drawLine(int(cx), int(cy), int(x), int(y))

        painter.setPen(QPen(Qt.black, 1))
        base_font = QFont()
        base_font.setPointSize(10)
        painter.setFont(base_font)

        def draw_label(text, az, alt, dx=0, dy=0):
            x, y = self._azalt_to_xy(az, alt, cx, cy, radius)
            painter.drawText(int(x + dx), int(y + dy), text)

        draw_label("N", 0, 0, -5, -5)
        draw_label("E", 90, 0, 5, 0)
        draw_label("S", 180, 0, -5, 15)
        draw_label("W", 270, 0, -15, 0)

        if not self._track:
            return

        pts = []
        for p in self._track:
            az = float(p["az"])
            alt = float(p["alt"])
            if alt < 0:
                continue
            x, y = self._azalt_to_xy(az, alt, cx, cy, radius)
            pts.append((x, y))

        if len(pts) >= 2:
            painter.setPen(QPen(Qt.darkGray, 2))
            for i in range(len(pts) - 1):
                painter.drawLine(int(pts[i][0]), int(pts[i][1]), int(pts[i + 1][0]), int(pts[i + 1][1]))

        valid = [p for p in self._track if p["alt"] >= 0]
        if not valid:
            return

        start = valid[0]
        end = valid[-1]
        peak = max(valid, key=lambda x: x["alt"])

        def draw_dot(point, pen):
            x, y = self._azalt_to_xy(point["az"], point["alt"], cx, cy, radius)
            painter.setPen(pen)
            painter.drawEllipse(int(x - 3), int(y - 3), 6, 6)
            return x, y

        sx, sy = draw_dot(start, QPen(Qt.black, 2))
        ex, ey = draw_dot(end, QPen(Qt.black, 2))
        px, py = draw_dot(peak, QPen(Qt.black, 2))

        # 保留起点/终点时间和最高点标注
        painter.setPen(QPen(Qt.black, 1))
        painter.setFont(base_font)
        start_t = self._fmt_phase_time(start.get("t"))
        end_t = self._fmt_phase_time(end.get("t"))
        if start_t:
            painter.drawText(int(sx + 6), int(sy + 12), start_t)
        if end_t:
            painter.drawText(int(ex + 6), int(ey + 12), end_t)
        painter.drawText(int(px + 6), int(py - 6), f"最高{float(peak['alt']):.0f}°")

        # 小字体时间标记：沿轨迹约每 2 分钟标注一次，并附带小点
        painter.setPen(QPen(Qt.gray, 1))
        small_font = QFont(base_font)
        small_font.setPointSize(8)
        painter.setFont(small_font)
        last_label_t = None
        for p in valid:
            t = p.get("t")
            if not isinstance(t, datetime):
                continue
            if last_label_t is None or (t - last_label_t).total_seconds() >= 120:
                tx, ty = self._azalt_to_xy(float(p["az"]), float(p["alt"]), cx, cy, radius)
                painter.drawEllipse(int(tx - 1), int(ty - 1), 3, 3)
                painter.drawText(int(tx + 6), int(ty + 10), t.strftime("%H:%M"))
                last_label_t = t
