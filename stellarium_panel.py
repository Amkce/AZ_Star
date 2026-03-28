# This Python file uses the following encoding: utf-8
import json
import subprocess
import winreg
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import requests
from PySide6.QtCore import QTimer, Qt
from PySide6.QtWidgets import QAbstractItemView, QDialog, QMessageBox, QTableWidgetItem

from stellarium_panel_ui import Ui_StellariumDialog


@dataclass
class StellariumTarget:
    name: str
    sat_id: str
    tle1: str
    tle2: str
    window_start_utc: Optional[datetime]
    window_end_utc: Optional[datetime]
    magnitude: str = ""


class StellariumClient:
    def __init__(self, base_url: str = "http://localhost:8090", timeout_s: float = 5.0):
        self.base_url = base_url.rstrip("/")
        self.timeout_s = timeout_s
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "AZ-Star-New/Stellarium"})

    @staticmethod
    def _datetime_utc_to_jd(dt_utc: datetime) -> float:
        if dt_utc.tzinfo is None:
            dt_utc = dt_utc.replace(tzinfo=timezone.utc)
        dt_utc = dt_utc.astimezone(timezone.utc)
        unix_s = dt_utc.timestamp()
        return unix_s / 86400.0 + 2440587.5

    def _request(self, method: str, path: str, **kwargs):
        resp = self.session.request(
            method=method,
            url=f"{self.base_url}{path}",
            timeout=self.timeout_s,
            **kwargs,
        )
        resp.raise_for_status()
        return resp

    def get_status(self) -> dict:
        return self._request("GET", "/api/main/status").json()

    def get_plugins(self) -> dict:
        return self._request("GET", "/api/main/plugins").json()

    def get_actions(self) -> dict:
        return self._request("GET", "/api/stelaction/list").json()

    def is_online(self) -> bool:
        try:
            self.get_status()
            return True
        except Exception:
            return False

    def set_location(self, lat: float, lon: float, altitude_m: float = 0.0, name: str = "Observer"):
        self._request(
            "POST",
            "/api/location/setlocationfields",
            data={
                "latitude": f"{lat:.6f}",
                "longitude": f"{lon:.6f}",
                "altitude": str(int(round(altitude_m))),
                "name": name,
                "planet": "Earth",
            },
        )

    def set_time(self, dt_utc: datetime):
        if dt_utc.tzinfo is None:
            dt_utc = dt_utc.replace(tzinfo=timezone.utc)
        jd = self._datetime_utc_to_jd(dt_utc.astimezone(timezone.utc))
        self._request("POST", "/api/main/time", data={"time": f"{jd:.8f}"})

    def set_time_multiplier(self, multiplier: float):
        rate_jd_per_second = float(multiplier) / 86400.0
        self._request("POST", "/api/main/time", data={"timerate": f"{rate_jd_per_second:.12f}"})

    def find_objects(self, query: str) -> list[str]:
        q = (query or "").strip()
        if not q:
            return []
        resp = self._request("GET", "/api/objects/find", params={"str": q})
        data = resp.json()
        return data if isinstance(data, list) else []

    def focus_object(self, target: str, mode: str = "center"):
        self._request("POST", "/api/main/focus", data={"target": target, "mode": mode})

    def do_action(self, action_id: str):
        self._request("POST", "/api/stelaction/do", data={"id": action_id})

    def go_realtime(self):
        self.do_action("actionReturn_To_Current_Time")
        self.do_action("actionSet_Real_Time_Speed")

    def pause_time(self):
        self.do_action("actionSet_Time_Rate_Zero")

    def _find_action_entry(self, action_tree: dict, action_id: str) -> Optional[dict]:
        for entries in action_tree.values():
            if not isinstance(entries, list):
                continue
            for entry in entries:
                if isinstance(entry, dict) and entry.get("id") == action_id:
                    return entry
        return None

    def set_action_checked(self, action_id: str, desired: bool):
        try:
            actions = self.get_actions()
            entry = self._find_action_entry(actions, action_id)
            if entry is None:
                return
            if bool(entry.get("isCheckable")) and bool(entry.get("isChecked")) != bool(desired):
                self.do_action(action_id)
        except Exception:
            pass


def get_stellarium_satellites_path() -> Path:
    appdata = Path.home() / "AppData" / "Roaming" / "Stellarium" / "modules" / "Satellites"
    return appdata / "satellites.json"


def load_stellarium_satellites(path: Optional[Path] = None) -> dict:
    sat_path = path or get_stellarium_satellites_path()
    if not sat_path.exists():
        return {"creator": "AZ Star New", "hintColor": [0.4, 0.4, 0.4], "satellites": {}}
    with sat_path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if "satellites" not in data or not isinstance(data["satellites"], dict):
        data["satellites"] = {}
    return data


def resolve_stellarium_satellite_name(target: StellariumTarget, path: Optional[Path] = None) -> str:
    try:
        data = load_stellarium_satellites(path)
    except Exception:
        return target.name
    entry = data.get("satellites", {}).get(target.sat_id, {})
    name = str(entry.get("name", "")).strip()
    return name or target.name


def upsert_stellarium_satellite(target: StellariumTarget, path: Optional[Path] = None) -> tuple[Path, str, bool]:
    sat_path = path or get_stellarium_satellites_path()
    sat_path.parent.mkdir(parents=True, exist_ok=True)
    data = load_stellarium_satellites(sat_path)
    satellites = data.setdefault("satellites", {})
    key = target.sat_id or (target.tle1[2:7].strip() if len(target.tle1) >= 7 else "") or target.name
    existed = key in satellites
    entry = dict(satellites.get(key, {}))
    current_name = str(entry.get("name", "")).strip() or target.name

    groups = list(entry.get("groups", [])) if isinstance(entry.get("groups"), list) else []
    if "az_star_new" not in groups:
        groups.append("az_star_new")

    entry.update(
        {
            "name": current_name,
            "tle1": target.tle1,
            "tle2": target.tle2,
            "visible": True,
            "orbitVisible": True,
            "groups": groups,
            "lastUpdated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
    )
    entry.setdefault("comms", [])
    entry.setdefault("hintColor", [0.2, 0.8, 1.0])
    entry.setdefault("infoColor", [0.2, 0.8, 1.0])
    satellites[key] = entry

    tmp_path = sat_path.with_suffix(".json.tmp")
    with tmp_path.open("w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    tmp_path.replace(sat_path)
    return sat_path, current_name, existed


def find_stellarium_executable() -> Optional[Path]:
    candidates = [
        Path(r"C:\Program Files\Stellarium\stellarium.exe"),
        Path(r"C:\Program Files (x86)\Stellarium\stellarium.exe"),
        Path.home() / "AppData" / "Local" / "Programs" / "Stellarium" / "stellarium.exe",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate

    uninstall_roots = [
        (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Uninstall"),
        (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\Uninstall"),
        (winreg.HKEY_LOCAL_MACHINE, r"Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
    ]
    for hive, root in uninstall_roots:
        try:
            with winreg.OpenKey(hive, root) as root_key:
                for i in range(winreg.QueryInfoKey(root_key)[0]):
                    try:
                        sub_name = winreg.EnumKey(root_key, i)
                        with winreg.OpenKey(root_key, sub_name) as sub_key:
                            display_name = str(winreg.QueryValueEx(sub_key, "DisplayName")[0])
                            if "Stellarium" not in display_name:
                                continue
                            install_location = str(winreg.QueryValueEx(sub_key, "InstallLocation")[0]).strip()
                            if install_location:
                                exe = Path(install_location) / "stellarium.exe"
                                if exe.exists():
                                    return exe
                    except Exception:
                        continue
        except Exception:
            continue
    return None


class StellariumDialog(QDialog):
    def __init__(
        self,
        targets: list[StellariumTarget],
        default_index: int,
        longitude: float,
        latitude: float,
        height_m: float,
        display_tz: timezone,
        parent=None,
    ):
        super().__init__(parent)
        self.ui = Ui_StellariumDialog()
        self.ui.setupUi(self)

        self.targets = list(targets)
        self.longitude = longitude
        self.latitude = latitude
        self.height_m = height_m
        self.display_tz = display_tz
        self.client = StellariumClient()
        self.satellites_path = get_stellarium_satellites_path()
        self._default_index = max(0, min(default_index, len(self.targets) - 1)) if self.targets else -1
        self._stellarium_name = ""

        self.ui.splitter_main.setSizes([460, 600])
        self.ui.combo_rate.setCurrentText("30x")
        self.ui.table_targets.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.ui.table_targets.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.ui.table_targets.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.ui.table_targets.setWordWrap(False)

        self._bind_signals()
        self._load_targets()
        self.on_check_connection(show_success=False)

    def _bind_signals(self):
        self.ui.button_launch.clicked.connect(self.on_launch_stellarium)
        self.ui.button_check.clicked.connect(self.on_check_connection)
        self.ui.button_one_click.clicked.connect(self.on_one_click)
        self.ui.button_write_sat.clicked.connect(self.on_write_satellite)
        self.ui.button_sync_location.clicked.connect(self.on_sync_location)
        self.ui.button_sync_start.clicked.connect(self.on_sync_start_time)
        self.ui.button_focus.clicked.connect(self.on_focus_satellite)
        self.ui.button_play.clicked.connect(self.on_start_simulation)
        self.ui.button_pause.clicked.connect(self.on_pause_simulation)
        self.ui.button_realtime.clicked.connect(self.on_realtime)
        self.ui.table_targets.itemSelectionChanged.connect(self.on_target_selection_changed)

    def _append_log(self, text: str):
        stamp = datetime.now().strftime("%H:%M:%S")
        self.ui.text_log.appendPlainText(f"[{stamp}] {text}")

    def _format_display_dt(self, dt_utc: Optional[datetime]) -> str:
        if dt_utc is None:
            return "未知"
        if dt_utc.tzinfo is None:
            dt_utc = dt_utc.replace(tzinfo=timezone.utc)
        return dt_utc.astimezone(self.display_tz).strftime("%Y-%m-%d %H:%M:%S")

    def _display_window_text(self, target: StellariumTarget) -> tuple[str, str]:
        return self._format_display_dt(target.window_start_utc), self._format_display_dt(target.window_end_utc)

    def _load_targets(self):
        self.ui.table_targets.setRowCount(len(self.targets))
        for row, target in enumerate(self.targets):
            start_text, end_text = self._display_window_text(target)
            self.ui.table_targets.setItem(row, 0, QTableWidgetItem(target.name or "未知"))
            self.ui.table_targets.setItem(row, 1, QTableWidgetItem(target.magnitude or ""))
            self.ui.table_targets.setItem(row, 2, QTableWidgetItem(start_text))
            self.ui.table_targets.setItem(row, 3, QTableWidgetItem(end_text))
        self.ui.table_targets.resizeColumnsToContents()
        self.ui.label_location.setText(
            f"经度 {self.longitude:.4f}，纬度 {self.latitude:.4f}，海拔 {self.height_m:.0f} m"
        )
        if self.targets:
            self.ui.table_targets.selectRow(self._default_index if self._default_index >= 0 else 0)
        else:
            self._refresh_summary(None)

    def current_index(self) -> int:
        return self.ui.table_targets.currentRow()

    def current_target(self) -> StellariumTarget:
        idx = self.current_index()
        if idx < 0 or idx >= len(self.targets):
            raise ValueError("当前没有可用卫星。")
        return self.targets[idx]

    def _refresh_summary(self, target: Optional[StellariumTarget]):
        if target is None:
            self.ui.label_name.setText("未选择")
            self.ui.label_stellarium_name.setText("未选择")
            self.ui.label_sat_id.setText("未选择")
            self.ui.label_mag.setText("未选择")
            self.ui.label_window.setText("未选择")
            self.ui.text_tle.setPlainText("")
            self._stellarium_name = ""
            return

        self._stellarium_name = resolve_stellarium_satellite_name(target, self.satellites_path)
        self.ui.label_name.setText(target.name or "未知")
        self.ui.label_stellarium_name.setText(self._stellarium_name or "未知")
        self.ui.label_sat_id.setText(target.sat_id or "未知")
        self.ui.label_mag.setText(target.magnitude or "未知")
        if target.window_start_utc and target.window_end_utc:
            self.ui.label_window.setText(
                f"{self._format_display_dt(target.window_start_utc)} ~ "
                f"{self._format_display_dt(target.window_end_utc)}"
            )
        else:
            self.ui.label_window.setText("未绑定窗口，将按当前时间模拟。")
        self.ui.text_tle.setPlainText(f"{target.tle1}\n{target.tle2}".strip())

    def _preferred_start_time(self) -> datetime:
        target = self.current_target()
        dt = target.window_start_utc or datetime.now(timezone.utc)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)

    def _playback_multiplier(self) -> float:
        text = self.ui.combo_rate.currentText().strip().lower().replace("x", "")
        try:
            return float(text)
        except Exception:
            return 30.0

    def _ensure_online(self):
        if not self.client.is_online():
            raise RuntimeError("Stellarium 远程控制未连接，请先启动 Stellarium 并确认 Remote Control 可用。")

    def _ensure_target_has_tle(self) -> StellariumTarget:
        target = self.current_target()
        if not (target.tle1 and target.tle2):
            raise RuntimeError("当前卫星没有有效 TLE，无法同步到 Stellarium。")
        return target

    def _try_find_target_name(self, target: StellariumTarget) -> Optional[str]:
        candidates = []
        for name in [self._stellarium_name, target.name, target.sat_id]:
            clean = (name or "").strip()
            if clean and clean not in candidates:
                candidates.append(clean)
        for query in candidates:
            try:
                matches = self.client.find_objects(query)
            except Exception:
                matches = []
            for match in matches:
                if match == query:
                    return match
            if matches:
                return matches[0]
        return None

    def on_target_selection_changed(self):
        row = self.current_index()
        target = self.targets[row] if 0 <= row < len(self.targets) else None
        self._refresh_summary(target)

    def on_launch_stellarium(self):
        exe = find_stellarium_executable()
        if exe is None:
            QMessageBox.warning(self, "未找到程序", "未找到 stellarium.exe，请确认软件已安装。")
            return
        try:
            subprocess.Popen([str(exe)], cwd=str(exe.parent))
            self._append_log(f"已启动 Stellarium：{exe}")
            QTimer.singleShot(2500, lambda: self.on_check_connection(show_success=False))
        except Exception as e:
            QMessageBox.critical(self, "启动失败", f"启动 Stellarium 失败：{e}")

    def on_check_connection(self, show_success: bool = True):
        try:
            status = self.client.get_status()
            plugins = self.client.get_plugins()
            sat_loaded = bool(plugins.get("Satellites", {}).get("loaded"))
            remote_loaded = bool(plugins.get("RemoteControl", {}).get("loaded"))
            self.ui.label_status.setText(
                f"已连接（Remote Control={'是' if remote_loaded else '否'}，Satellites={'是' if sat_loaded else '否'}）"
            )
            loc = status.get("location", {}) if isinstance(status, dict) else {}
            loc_name = loc.get("name") or "未知地点"
            self._append_log(f"连接成功，当前地点：{loc_name}")
            if show_success:
                QMessageBox.information(self, "连接正常", "已连接到本机 Stellarium。")
        except Exception as e:
            self.ui.label_status.setText("未连接")
            if show_success:
                QMessageBox.warning(self, "连接失败", f"无法连接 Stellarium：{e}")

    def on_write_satellite(self, show_success: bool = True):
        try:
            target = self._ensure_target_has_tle()
            sat_path, sat_name, existed = upsert_stellarium_satellite(target, self.satellites_path)
            self._stellarium_name = sat_name
            self._refresh_summary(target)
            action = "更新" if existed else "写入"
            msg = f"已{action}卫星配置：{sat_name}\n文件：{sat_path}"
            self._append_log(msg)
            self._append_log("若当前 Stellarium 搜索不到新目标，通常重启 Stellarium 后即可加载新条目。")
            if show_success:
                QMessageBox.information(self, "卫星已同步", msg)
        except Exception as e:
            if show_success:
                QMessageBox.critical(self, "写入失败", str(e))
            else:
                raise

    def on_sync_location(self, show_success: bool = True):
        try:
            self._ensure_online()
            self.client.set_location(self.latitude, self.longitude, self.height_m, name="Observer")
            self._append_log(
                f"已同步观测地：经度 {self.longitude:.4f}，纬度 {self.latitude:.4f}，海拔 {self.height_m:.0f} m"
            )
            if show_success:
                QMessageBox.information(self, "已同步", "观测地已同步到 Stellarium。")
        except Exception as e:
            if show_success:
                QMessageBox.warning(self, "同步失败", str(e))
            else:
                raise

    def on_sync_start_time(self, show_success: bool = True):
        try:
            self._ensure_online()
            start_utc = self._preferred_start_time()
            self.client.set_time(start_utc)
            self._append_log(f"已跳到起始时刻：{self._format_display_dt(start_utc)}")
            if show_success:
                QMessageBox.information(self, "已同步", "时间已同步到起始时刻。")
        except Exception as e:
            if show_success:
                QMessageBox.warning(self, "同步失败", str(e))
            else:
                raise

    def on_focus_satellite(self, show_success: bool = True):
        try:
            self._ensure_online()
            target = self._ensure_target_has_tle()
            target_name = self._try_find_target_name(target)
            if not target_name:
                self.on_write_satellite(show_success=False)
                target_name = self._try_find_target_name(target)
            if not target_name:
                raise RuntimeError(
                    "当前 Stellarium 中没有找到该卫星。\n"
                    "已尝试写入 satellites.json。若仍搜索不到，通常需要重启 Stellarium 以加载新条目。"
                )
            self.client.focus_object(target_name, mode="center")
            self.client.set_action_checked("actionShow_Satellite_Hints", True)
            self.client.set_action_checked("actionShow_Satellite_Labels", True)
            self.client.set_action_checked("actionSet_Tracking", True)
            self._append_log(f"已定位到卫星：{target_name}")
            if show_success:
                QMessageBox.information(self, "定位成功", f"已定位到卫星：{target_name}")
        except Exception as e:
            if show_success:
                QMessageBox.warning(self, "定位失败", str(e))
            else:
                raise

    def on_start_simulation(self):
        try:
            self._ensure_online()
            self._ensure_target_has_tle()
            self.on_sync_location(show_success=False)
            self.on_sync_start_time(show_success=False)
            self.on_focus_satellite(show_success=False)
            multiplier = self._playback_multiplier()
            self.client.set_time_multiplier(multiplier)
            self._append_log(f"已开始模拟回放，倍率 {multiplier:.0f}x")
            QMessageBox.information(self, "模拟已开始", f"已在 Stellarium 中开始 {multiplier:.0f}x 回放。")
        except Exception as e:
            QMessageBox.warning(self, "模拟失败", str(e))

    def on_pause_simulation(self):
        try:
            self._ensure_online()
            self.client.pause_time()
            self._append_log("已暂停 Stellarium 时间流逝。")
            QMessageBox.information(self, "已暂停", "模拟已暂停。")
        except Exception as e:
            QMessageBox.warning(self, "暂停失败", str(e))

    def on_realtime(self):
        try:
            self._ensure_online()
            self.client.go_realtime()
            self._append_log("已恢复到实时。")
            QMessageBox.information(self, "已恢复", "Stellarium 已恢复实时。")
        except Exception as e:
            QMessageBox.warning(self, "恢复失败", str(e))

    def on_one_click(self):
        try:
            self._ensure_online()
            self._ensure_target_has_tle()
            self.on_write_satellite(show_success=False)
            self.on_sync_location(show_success=False)
            self.on_sync_start_time(show_success=False)
            self.on_focus_satellite(show_success=False)
            self._append_log("一键联动完成。")
            QMessageBox.information(self, "联动完成", "时间、地点、卫星已同步到 Stellarium。")
        except Exception as e:
            QMessageBox.warning(self, "联动失败", str(e))
