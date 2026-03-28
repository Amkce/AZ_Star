from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter, QPen, QPixmap
from PySide6.QtWidgets import QWidget


class MapTrackWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._track = []  # list[dict]: {"lon": float, "lat": float, "t": datetime}
        self._name = ""
        self._status = ""
        self._bg = None

    def set_background(self, pixmap: QPixmap):
        self._bg = pixmap
        self.update()

    def set_track(self, name: str, track_points: list, status: str = ""):
        self._name = name or ""
        self._track = track_points or []
        self._status = status or ""
        self.update()

    def clear(self):
        self.set_track("", [], "")

    def _lonlat_to_xy(self, lon: float, lat: float, rect):
        x = (lon + 180.0) / 360.0 * rect.width() + rect.left()
        y = (90.0 - lat) / 180.0 * rect.height() + rect.top()
        return x, y

    def paintEvent(self, event):
        del event
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = self.rect()

        if self._bg and not self._bg.isNull():
            painter.drawPixmap(rect, self._bg)
        else:
            painter.fillRect(rect, Qt.black)

        if not self._track:
            return

        painter.setPen(QPen(Qt.gray, 1))
        for lon in (-120, -60, 0, 60, 120):
            x1, y1 = self._lonlat_to_xy(lon, 90, rect)
            x2, y2 = self._lonlat_to_xy(lon, -90, rect)
            painter.drawLine(int(x1), int(y1), int(x2), int(y2))
        for lat in (-60, -30, 0, 30, 60):
            x1, y1 = self._lonlat_to_xy(-180, lat, rect)
            x2, y2 = self._lonlat_to_xy(180, lat, rect)
            painter.drawLine(int(x1), int(y1), int(x2), int(y2))

        painter.setPen(QPen(Qt.white, 2))
        prev = None
        for p in self._track:
            lon = ((float(p["lon"]) + 180.0) % 360.0) - 180.0
            lat = float(p["lat"])
            if prev is not None:
                lon_prev, lat_prev = prev
                if abs(lon - lon_prev) <= 180.0:
                    x1, y1 = self._lonlat_to_xy(lon_prev, lat_prev, rect)
                    x2, y2 = self._lonlat_to_xy(lon, lat, rect)
                    painter.drawLine(int(x1), int(y1), int(x2), int(y2))
            prev = (lon, lat)

        cur = self._track[0]
        cur_lon = ((float(cur["lon"]) + 180.0) % 360.0) - 180.0
        cur_lat = float(cur["lat"])
        cx, cy = self._lonlat_to_xy(cur_lon, cur_lat, rect)
        painter.setPen(QPen(Qt.yellow, 2))
        painter.drawEllipse(int(cx - 4), int(cy - 4), 8, 8)

        end = self._track[-1]
        end_lon = ((float(end["lon"]) + 180.0) % 360.0) - 180.0
        end_lat = float(end["lat"])
        ex, ey = self._lonlat_to_xy(end_lon, end_lat, rect)
        painter.setPen(QPen(Qt.white, 2))
        painter.drawEllipse(int(ex - 2), int(ey - 2), 4, 4)
