# This Python file uses the following encoding: utf-8
import math
import re
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional
from urllib.parse import parse_qs, urlparse

import pythoncom
import requests
import win32com.client
from bs4 import BeautifulSoup
from PySide6.QtCore import QThread, QTimer, Signal, Qt
from PySide6.QtWidgets import (
    QApplication,
    QAbstractItemView,
    QHeaderView,
    QMessageBox,
    QTableWidgetItem,
    QWidget,
)
from skyfield.api import EarthSatellite as SfEarthSatellite, load as sf_load, wgs84

from stellarium_panel import StellariumDialog, StellariumTarget
from ui_form import Ui_Form

EQU_TOPOCENTRIC = 1
EQU_J2000 = 2


@dataclass
class PassItem:
    sat_id: str
    name: str
    name_raw: str
    magnitude: str
    start_local: str
    end_local: str
    max_alt: str
    peak_local: str
    tle1: str
    tle2: str
    mjd: Optional[float]
    start_utc: Optional[datetime]
    end_utc: Optional[datetime]
    peak_utc: Optional[datetime]


class TodaySatelliteScraper:
    """Fetch today's pass list and per-sat TLE from Heavens-Above."""

    def __init__(self, base_url: str = "https://www.heavens-above.com"):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.7",
            }
        )

    @staticmethod
    def _extract_satid(onclick_attr: str) -> str:
        if not onclick_attr:
            return ""
        m = re.search(r"satid=(\d+)", onclick_attr)
        return m.group(1) if m else ""

    @staticmethod
    def _extract_mjd(text: str) -> Optional[float]:
        if not text:
            return None
        m = re.search(r"mjd=([0-9]+(?:\.[0-9]+)?)", text)
        if not m:
            return None
        try:
            return float(m.group(1))
        except Exception:
            return None

    @staticmethod
    def _query_param_from_href(href: str, key: str) -> str:
        if not href:
            return ""
        try:
            q = parse_qs(urlparse(href).query)
            vals = q.get(key, [])
            return vals[0] if vals else ""
        except Exception:
            return ""

    @staticmethod
    def _parse_hms(text: str) -> Optional[tuple[int, int, int]]:
        raw = (text or "").strip()
        m = re.search(r"(\d{1,2}):(\d{2})(?::(\d{2}))?", raw)
        if not m:
            return None
        hh = int(m.group(1))
        mm = int(m.group(2))
        ss = int(m.group(3) or "0")
        if hh > 23 or mm > 59 or ss > 59:
            return None
        return hh, mm, ss

    @staticmethod
    def _parse_magnitude(text: str) -> Optional[float]:
        raw = (text or "").strip()
        m = re.search(r"[-+]?\d+(?:\.\d+)?", raw)
        if not m:
            return None
        try:
            return float(m.group(0))
        except Exception:
            return None

    @staticmethod
    def _mjd_to_datetime_utc(mjd: float) -> datetime:
        # MJD -> JD
        jd = float(mjd) + 2400000.5
        unix_s = (jd - 2440587.5) * 86400.0
        return datetime.fromtimestamp(unix_s, tz=timezone.utc)

    @staticmethod
    def _tzinfo_from_source_name(tz_name: str) -> timezone:
        t = (tz_name or "").strip().lower()
        if t in {"chst", "utc+8", "cst"}:
            return timezone(timedelta(hours=8))
        return timezone.utc

    @staticmethod
    def _datetime_utc_to_mjd(dt_utc: datetime) -> float:
        if dt_utc.tzinfo is None:
            dt_utc = dt_utc.replace(tzinfo=timezone.utc)
        dt_utc = dt_utc.astimezone(timezone.utc)
        unix_s = dt_utc.timestamp()
        jd = unix_s / 86400.0 + 2440587.5
        return jd - 2400000.5

    @classmethod
    def _resolve_time_near_anchor(
        cls, anchor_utc: datetime, hms_text: str, source_tz: timezone
    ) -> Optional[datetime]:
        hms = cls._parse_hms(hms_text)
        if hms is None:
            return None
        hh, mm, ss = hms
        base_local = anchor_utc.astimezone(source_tz)
        candidates = []
        for day_shift in (-1, 0, 1):
            c_local = (base_local + timedelta(days=day_shift)).replace(
                hour=hh, minute=mm, second=ss, microsecond=0
            )
            candidates.append(c_local.astimezone(timezone.utc))
        base_utc = anchor_utc.astimezone(timezone.utc)
        return min(candidates, key=lambda x: abs((x - base_utc).total_seconds()))

    def _parse_table(self, soup: BeautifulSoup) -> list[dict]:
        table = soup.find("table", class_="standardTable")
        if not table:
            return []

        parsed: list[dict] = []
        for row in table.find_all("tr"):
            cols = row.find_all("td")
            if len(cols) < 11:
                continue

            onclick = row.get("onclick", "")
            hrefs = [a.get("href", "") for a in row.find_all("a", href=True)]

            sat_id = ""
            mjd = None
            for href in hrefs:
                sat_id = sat_id or self._query_param_from_href(href, "satid")
                mjd = mjd if isinstance(mjd, (int, float)) else self._extract_mjd(href)
                if sat_id and isinstance(mjd, (int, float)):
                    break

            sat_id = sat_id or self._extract_satid(onclick)
            mjd = mjd if isinstance(mjd, (int, float)) else self._extract_mjd(onclick)
            if not sat_id:
                continue

            raw_name = cols[0].get_text(strip=True)
            if not raw_name:
                continue

            start_local = cols[2].get_text(strip=True) if len(cols) > 2 else ""
            peak_local = cols[5].get_text(strip=True) if len(cols) > 5 else ""
            end_local = cols[8].get_text(strip=True) if len(cols) > 8 else ""

            parsed.append(
                {
                    "sat_id": sat_id,
                    "name": raw_name,
                    "name_raw": raw_name,
                    "mag": cols[1].get_text(strip=True),
                    "start_local": start_local,
                    "peak_local": peak_local,
                    "end_local": end_local,
                    "max_alt": cols[6].get_text(strip=True) if len(cols) > 6 else "",
                    "mjd": mjd,
                }
            )
        return parsed

    def fetch_tle(
        self, sat_id: str, lat: float, lon: float, loc: str, alt_m: float, tz: str
    ) -> tuple[str, str]:
        url = f"{self.base_url}/orbit.aspx"
        params = {
            "satid": sat_id,
            "lat": lat,
            "lng": lon,
            "loc": loc,
            "alt": int(round(alt_m)),
            "tz": tz,
            "cul": "zh-CHS",
        }
        try:
            r = self.session.get(url, params=params, timeout=15)
            r.raise_for_status()
            soup = BeautifulSoup(r.content, "html.parser")
            l1 = soup.find("span", id="ctl00_cph1_lblLine1")
            l2 = soup.find("span", id="ctl00_cph1_lblLine2")
            line1 = l1.get_text(strip=True) if l1 else ""
            line2 = l2.get_text(strip=True) if l2 else ""
            if line1 and line2:
                return line1, line2

            # Fallback: regex scan whole page text (some layout variants hide the span ids).
            txt = soup.get_text("\n", strip=True)
            m1 = re.search(r"^1\s+\d{5}.*$", txt, flags=re.MULTILINE)
            m2 = re.search(r"^2\s+\d{5}.*$", txt, flags=re.MULTILINE)
            return (m1.group(0).strip() if m1 else "", m2.group(0).strip() if m2 else "")
        except Exception:
            return "", ""

    def fetch_today(
        self,
        lat: float,
        lon: float,
        h_m: float,
        location_name: str,
        tz: str = "ChST",
        day_mjd: Optional[float] = None,
        prefer_dawn: bool = False,
        mag_limit: float = 4.5,
        delay_s: float = 0.1,
    ) -> list[PassItem]:
        url = f"{self.base_url}/AllSats.aspx"
        params = {
            "lat": lat,
            "lng": lon,
            "loc": location_name,
            "alt": int(round(h_m)),
            "tz": tz,
            "cul": "zh-CHS",
        }
        # 不传 mjd 时交由源站按当前时刻返回默认列表，可获得更完整数据。
        if day_mjd is not None:
            params["mjd"] = f"{float(day_mjd):.0f}"

        r = self.session.get(url, params=params, timeout=15)
        r.raise_for_status()
        raw = self._parse_table(BeautifulSoup(r.content, "html.parser"))
        source_tz = self._tzinfo_from_source_name(tz)
        filtered: list[dict] = []
        for item in raw:
            mag_val = self._parse_magnitude(item.get("mag", ""))
            if mag_val is not None and mag_val > float(mag_limit):
                continue

            # 勾选=凌晨(00:00-11:59)；未勾选=傍晚(12:00-23:59)。
            hms = self._parse_hms(item.get("start_local", ""))
            if hms is not None:
                hour = hms[0]
                if prefer_dawn and not (0 <= hour < 12):
                    continue
                if (not prefer_dawn) and not (12 <= hour <= 23):
                    continue
            filtered.append(item)
        raw = filtered

        out: list[PassItem] = []
        for i, item in enumerate(raw):
            sat_id = item.get("sat_id", "")

            tle1, tle2 = ("", "")
            if sat_id:
                tle1, tle2 = self.fetch_tle(
                    sat_id=sat_id, lat=lat, lon=lon, loc=location_name, alt_m=h_m, tz=tz
                )

            mjd = item.get("mjd", None)
            start_utc = None
            end_utc = None
            peak_utc = None
            if isinstance(mjd, (int, float)):
                try:
                    anchor_utc = self._mjd_to_datetime_utc(float(mjd))
                    start_utc = self._resolve_time_near_anchor(
                        anchor_utc, item.get("start_local", ""), source_tz
                    )
                    peak_utc = self._resolve_time_near_anchor(
                        anchor_utc, item.get("peak_local", ""), source_tz
                    )
                    end_utc = self._resolve_time_near_anchor(
                        anchor_utc, item.get("end_local", ""), source_tz
                    )
                except Exception:
                    start_utc = None
                    end_utc = None
                    peak_utc = None

            out.append(
                PassItem(
                    sat_id=sat_id,
                    name=item.get("name", ""),
                    name_raw=item.get("name_raw", ""),
                    magnitude=item.get("mag", ""),
                    start_local=item.get("start_local", ""),
                    end_local=item.get("end_local", ""),
                    max_alt=item.get("max_alt", ""),
                    peak_local=item.get("peak_local", ""),
                    tle1=tle1,
                    tle2=tle2,
                    mjd=float(mjd) if isinstance(mjd, (int, float)) else None,
                    start_utc=start_utc,
                    end_utc=end_utc,
                    peak_utc=peak_utc,
                )
            )

            if delay_s > 0 and i < len(raw) - 1:
                time.sleep(delay_s)
        return out


class FetchWorker(QThread):
    status = Signal(str)
    error = Signal(str)
    result = Signal(list)

    def __init__(
        self,
        lat: float,
        lon: float,
        h_m: float,
        location_name: str = "Observer",
        tz: str = "ChST",
        day_mjd: Optional[float] = None,
        prefer_dawn: bool = False,
        mag_limit: float = 4.5,
        parent=None,
    ):
        super().__init__(parent)
        self.lat = lat
        self.lon = lon
        self.h_m = h_m
        self.location_name = location_name
        self.tz = tz
        self.day_mjd = day_mjd
        self.prefer_dawn = prefer_dawn
        self.mag_limit = mag_limit
        self._stop = False

    def stop(self):
        self._stop = True

    def run(self):
        try:
            self.status.emit("开始抓取当天可见卫星与TLE...")
            scraper = TodaySatelliteScraper()
            data = scraper.fetch_today(
                lat=self.lat,
                lon=self.lon,
                h_m=self.h_m,
                location_name=self.location_name,
                tz=self.tz,
                day_mjd=self.day_mjd,
                prefer_dawn=self.prefer_dawn,
                mag_limit=self.mag_limit,
                delay_s=0.1,
            )
            if self._stop:
                return
            tle_ready = sum(1 for x in data if x.tle1 and x.tle2)
            self.status.emit(f"抓取完成：{len(data)} 条（可跟踪 {tle_ready} 条）")
            self.result.emit(data)
        except Exception as e:
            self.error.emit(str(e))

class NextPassWorker(QThread):
    error = Signal(str)
    result = Signal(str, list, str)  # name, track_points, status

    def __init__(
        self,
        tle1: str,
        tle2: str,
        name: str,
        lat: float,
        lon: float,
        window_start_utc: Optional[datetime] = None,
        window_end_utc: Optional[datetime] = None,
        parent=None,
    ):
        super().__init__(parent)
        self.tle1 = tle1
        self.tle2 = tle2
        self.name = name
        self.lat = lat
        self.lon = lon
        self.window_start_utc = window_start_utc
        self.window_end_utc = window_end_utc

    def run(self):
        try:
            ts = sf_load.timescale()
            sat = SfEarthSatellite(self.tle1, self.tle2, self.name, ts)
            observer = wgs84.latlon(self.lat, self.lon)
            start_dt = None
            end_dt = None
            using_row_window = False

            if self.window_start_utc is not None and self.window_end_utc is not None:
                start_dt = self.window_start_utc
                end_dt = self.window_end_utc
                if start_dt.tzinfo is None:
                    start_dt = start_dt.replace(tzinfo=timezone.utc)
                if end_dt.tzinfo is None:
                    end_dt = end_dt.replace(tzinfo=timezone.utc)
                start_dt = start_dt.astimezone(timezone.utc)
                end_dt = end_dt.astimezone(timezone.utc)
                if end_dt <= start_dt:
                    end_dt = end_dt + timedelta(days=1)
                using_row_window = True
            else:
                t0 = ts.now()
                t1 = ts.from_datetime(datetime.now(timezone.utc) + timedelta(hours=48))
                times, events = sat.find_events(observer, t0, t1, altitude_degrees=0.0)

                idx_rise = None
                idx_set = None
                for i, ev in enumerate(events):
                    if ev == 0:
                        idx_rise = i
                        for j in range(i + 1, len(events)):
                            if events[j] == 2:
                                idx_set = j
                                break
                        if idx_set is not None:
                            break

                if idx_rise is None or idx_set is None:
                    self.result.emit(self.name, [], "未来48小时未找到可见过境（Alt>0°）")
                    return

                t_rise = times[idx_rise]
                t_set = times[idx_set]
                start_dt = t_rise.utc_datetime()
                end_dt = t_set.utc_datetime()

            sample_step_s = 2

            total = max(1, int((end_dt - start_dt).total_seconds() // sample_step_s))
            sample_dts = [start_dt + timedelta(seconds=i * sample_step_s) for i in range(total + 1)]
            sample_ts = ts.from_datetimes(sample_dts)

            topo = (sat - observer).at(sample_ts)
            alt, az, _ = topo.altaz()

            track = []
            for k in range(len(sample_dts)):
                track.append(
                    {
                        "t": sample_dts[k].astimezone(timezone.utc).replace(tzinfo=timezone.utc),
                        "alt": float(alt.degrees[k]),
                        "az": float(az.degrees[k]),
                    }
                )

            dur_s = (end_dt - start_dt).total_seconds()
            if using_row_window:
                status = (
                    f"所选窗口：{start_dt.strftime('%H:%M:%S')}Z ~ {end_dt.strftime('%H:%M:%S')}Z  "
                    f"历时 {dur_s / 60:.1f} 分钟"
                )
            else:
                status = (
                    f"AOS {start_dt.strftime('%H:%M:%S')}Z  "
                    f"LOS {end_dt.strftime('%H:%M:%S')}Z  历时 {dur_s / 60:.1f} 分钟"
                )
            self.result.emit(self.name, track, status)
        except Exception as e:
            self.error.emit(str(e))


class GroundTrackWorker(QThread):
    error = Signal(str)
    result = Signal(str, list, str)  # name, track_points, status

    def __init__(
        self,
        tle1: str,
        tle2: str,
        name: str,
        minutes: int = 120,
        step_s: int = 10,
        parent=None,
    ):
        super().__init__(parent)
        self.tle1 = tle1
        self.tle2 = tle2
        self.name = name
        self.minutes = minutes
        self.step_s = step_s

    def run(self):
        try:
            ts = sf_load.timescale()
            sat = SfEarthSatellite(self.tle1, self.tle2, self.name, ts)

            total_s = self.minutes * 60
            n = max(1, total_s // self.step_s)
            start_dt = datetime.now(timezone.utc)
            dts = [start_dt + timedelta(seconds=i * self.step_s) for i in range(int(n) + 1)]
            t = ts.from_datetimes(dts)

            geoc = sat.at(t)
            sp = geoc.subpoint()
            lats = sp.latitude.degrees
            lons = sp.longitude.degrees

            track = []
            for i in range(len(dts)):
                track.append(
                    {
                        "t": dts[i],
                        "lat": float(lats[i]),
                        "lon": float(lons[i]),
                        "is_current": i == 0,
                    }
                )

            status = f"地面轨迹：当前 -> +{self.minutes} 分钟，步长 {self.step_s} 秒"
            self.result.emit(self.name, track, status)
        except Exception as e:
            self.error.emit(str(e))

class Main_menu(QWidget):
    telescope_selected = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_Form()
        self.ui.setupUi(self)
        self.setWindowTitle("主菜单")
        self._init_table()

        self.longitude: Optional[float] = None
        self.latitude: Optional[float] = None
        self.height_m = 0.0

        self._worker: Optional[FetchWorker] = None
        self._pass_worker: Optional[NextPassWorker] = None
        self._ground_worker: Optional[GroundTrackWorker] = None
        self._plot_request_id = 0
        self._visual_name = ""
        self._raw_pass_track: list[dict] = []
        self._raw_pass_status = ""
        self._raw_ground_track: list[dict] = []
        self._raw_ground_status = ""
        self._display_tz_offset_hours = 8.0
        self._display_tz = timezone(timedelta(hours=self._display_tz_offset_hours))
        # Heavens-Above 抓取按 ChST(+8) 执行；窗口文本解析回退按 +8 处理。
        self._fetch_source_tz_name = "ChST"
        self._fetch_source_tz = timezone(timedelta(hours=8))

        self.telescope = None
        self._ts = sf_load.timescale()
        self._observer = None
        self._satellite: Optional[SfEarthSatellite] = None
        self._sat_name = ""
        self._sat_id = ""
        self._tle1 = ""
        self._tle2 = ""
        self._mount_equatorial_system: Optional[int] = None

        self._tracking_active = False
        self._virtual_mode = False
        self._pretrack_mode = False
        self._waiting_pretrack_start = False
        self._slew_in_progress = False
        self._pretrack_start_utc: Optional[datetime] = None
        self._virtual_sat_start_utc: Optional[datetime] = None
        self._virtual_real_anchor_monotonic: Optional[float] = None

        self._prev_sample_time_s: Optional[float] = None
        self._prev_ra_hours: Optional[float] = None
        self._prev_dec_deg: Optional[float] = None

        self._auto_primary_rate = 0.0
        self._auto_secondary_rate = 0.0
        self._manual_primary_dir = 0
        self._manual_secondary_dir = 0
        self._last_sent_primary = 0.0
        self._last_sent_secondary = 0.0

        self._axis_ranges = {0: [], 1: []}  # abs-rate ranges per axis, e.g. [(0, 6.6), (10, 20)]
        self._manual_max_ref: Optional[float] = None
        self._offset_threshold_deg = 0.6
        self._reslew_lead_seconds = 2.0
        self._reslew_min_interval_seconds = 8.0
        self._last_reslew_monotonic = 0.0
        self._slew_settle_seconds = 8.0
        self._slew_guard_until_monotonic = 0.0

        self._tracking_timer = QTimer(self)
        self._tracking_timer.setInterval(100)
        self._tracking_timer.timeout.connect(self._tracking_tick)
        self._clock_timer = QTimer(self)
        self._clock_timer.setInterval(1000)
        self._clock_timer.timeout.connect(self._update_clock_label)
        self._stellarium_dialog: Optional[StellariumDialog] = None

        self._init_controls()
        self._bind_signals()

    @staticmethod
    def _is_parked_error(msg: str) -> bool:
        m = (msg or "").lower()
        return ("park" in m) or ("停放" in m) or ("驻车" in m)

    def _ensure_unparked(self) -> tuple[bool, str]:
        if self.telescope is None or not getattr(self.telescope, "Connected", False):
            return False, "赤道仪未连接。"
        try:
            at_park = False
            if hasattr(self.telescope, "AtPark"):
                at_park = bool(self.telescope.AtPark)
            if not at_park:
                return True, ""

            if hasattr(self.telescope, "CanUnpark") and not bool(self.telescope.CanUnpark):
                return False, "赤道仪处于驻车状态，且驱动返回 CanUnpark=False。"
            if not hasattr(self.telescope, "Unpark"):
                return False, "赤道仪处于驻车状态，且驱动不支持 Unpark()。"

            self.telescope.Unpark()

            # Give driver a short window to settle park state.
            for _ in range(20):
                if hasattr(self.telescope, "AtPark"):
                    if not bool(self.telescope.AtPark):
                        return True, ""
                else:
                    return True, ""
                time.sleep(0.1)
            return False, "已发送Unpark，但驱动仍返回 AtPark=True。"
        except Exception as e:
            return False, f"解驻车失败：{e}"

    def _init_controls(self):
        preset_lon = 121.4323
        preset_lat = 31.0276
        self.longitude = preset_lon
        self.latitude = preset_lat
        self.ui.lineEdit_longitude.setText(f"{preset_lon:.4f}")
        self.ui.lineEdit_latitude.setText(f"{preset_lat:.4f}")
        self.ui.label_longitude.setText(f"经度：{preset_lon:.4f}")
        self.ui.label_latitude.setText(f"纬度：{preset_lat:.4f}")

        self.ui.horizontalSlider.setRange(0, 100)
        self.ui.horizontalSlider.setValue(20)
        self.ui.checkBox_virtual.setChecked(False)
        self.ui.checkBox_pretrack.setChecked(False)
        if hasattr(self.ui, "checkBox_fetch_dawn"):
            self.ui.checkBox_fetch_dawn.setChecked(False)
        if hasattr(self.ui, "comboBox_mag_limit"):
            self.ui.comboBox_mag_limit.setCurrentText("4.5")
        self.ui.lineEdit_threshold.setText(f"{self._offset_threshold_deg:.2f}")
        self.ui.lineEdit_timezone.setText(self._format_utc_offset(self._display_tz_offset_hours))
        if hasattr(self.ui, "horizontalLayout"):
            # 防止 form.ui 里异常的大上边距挤压地图/天空球区域
            self.ui.horizontalLayout.setContentsMargins(-1, 0, -1, -1)
        if hasattr(self.ui, "widget_sky"):
            self.ui.widget_sky.setMinimumHeight(260)
        if hasattr(self.ui, "widget_map"):
            self.ui.widget_map.setMinimumHeight(260)
        self._update_speed_label()
        self._update_threshold_label()
        self._update_timezone_label()
        self._update_clock_label()
        self._clock_timer.start()

    def _bind_signals(self):
        self.ui.tableWidget.itemSelectionChanged.connect(self.on_table_selection_changed)
        self.ui.tableWidget.cellDoubleClicked.connect(self.on_table_row_double_clicked)

        self.ui.pushButton_stop.clicked.connect(self.on_stop_all)
        self.ui.pushButton_connect_1.clicked.connect(self.on_choose_telescope)
        self.ui.pushButton_longitude.clicked.connect(self.on_set_longitude)
        self.ui.pushButton_latitude.clicked.connect(self.on_set_latitude)
        self.ui.pushButton_threshold.clicked.connect(self.on_set_threshold)
        self.ui.pushButton_timezone.clicked.connect(self.on_set_timezone)
        self.ui.pushButton_seek.clicked.connect(self.on_seek_satellites)
        self.ui.pushButton_use_tle.clicked.connect(self.on_start_local_tle)
        self.ui.pushButton_stellarium.clicked.connect(self.on_open_stellarium_dialog)
        self.ui.horizontalSlider.valueChanged.connect(self._on_slider_changed)
        self.ui.checkBox_ot_up.toggled.connect(self._on_visual_flip_changed)
        self.ui.checkBox_ot_right.toggled.connect(self._on_visual_flip_changed)

        self.ui.pushButton_left.pressed.connect(lambda: self._set_manual_primary(-1))
        self.ui.pushButton_left.released.connect(lambda: self._release_manual_primary(-1))
        self.ui.pushButton_right.pressed.connect(lambda: self._set_manual_primary(1))
        self.ui.pushButton_right.released.connect(lambda: self._release_manual_primary(1))

        self.ui.pushButton_up.pressed.connect(lambda: self._set_manual_secondary(1))
        self.ui.pushButton_up.released.connect(lambda: self._release_manual_secondary(1))
        self.ui.pushButton_down.pressed.connect(lambda: self._set_manual_secondary(-1))
        self.ui.pushButton_down.released.connect(lambda: self._release_manual_secondary(-1))

    def _init_table(self):
        headers = ["名称", "星等", "起始时间", "结束时间", "最大高度", "ID", "TLE1", "TLE2"]
        self.ui.tableWidget.setColumnCount(len(headers))
        self.ui.tableWidget.setHorizontalHeaderLabels(headers)
        self.ui.tableWidget.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.ui.tableWidget.setWordWrap(False)
        self.ui.tableWidget.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.ui.tableWidget.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.ui.tableWidget.setSelectionMode(QAbstractItemView.SingleSelection)

    def _parse_float_from_lineedit(self, line_edit, field_name: str) -> float:
        text = line_edit.text().strip()
        if not text:
            raise ValueError(f"{field_name}不能为空。")
        text = text.replace("，", ".").replace(",", ".")
        return float(text)

    @staticmethod
    def _format_utc_offset(hours: float) -> str:
        sign = "+" if hours >= 0 else "-"
        total_minutes = int(round(abs(hours) * 60))
        hh = total_minutes // 60
        mm = total_minutes % 60
        return f"UTC{sign}{hh:02d}:{mm:02d}"

    def _to_display_dt(self, dt_utc: datetime) -> datetime:
        if dt_utc.tzinfo is None:
            dt_utc = dt_utc.replace(tzinfo=timezone.utc)
        return dt_utc.astimezone(self._display_tz)

    def _format_display_datetime(self, dt_utc: datetime) -> str:
        return self._to_display_dt(dt_utc).strftime("%Y-%m-%d %H:%M:%S")

    def _update_timezone_label(self):
        self.ui.label_timezone.setText(f"当前时区：{self._format_utc_offset(self._display_tz_offset_hours)}")

    def _update_clock_label(self):
        now_local = datetime.now(timezone.utc).astimezone(self._display_tz)
        self.ui.label_clock.setText(f"当前时间：{now_local.strftime('%Y-%m-%d %H:%M:%S')}")

    @staticmethod
    def _parse_timezone_offset_hours(text: str) -> float:
        s = (text or "").strip().upper()
        if not s:
            raise ValueError("时区不能为空。")
        s = s.replace("UTC", "").replace("GMT", "").replace(" ", "")

        m = re.fullmatch(r"([+-]?)(\d{1,2})(?::?(\d{2}))?", s)
        if m:
            sign = -1.0 if m.group(1) == "-" else 1.0
            hh = int(m.group(2))
            mm = int(m.group(3) or "0")
            if hh > 14 or mm > 59:
                raise ValueError("时区格式超出范围，请使用如 +8、+08:00、-5。")
            val = sign * (hh + mm / 60.0)
        else:
            try:
                val = float(s)
            except Exception as e:
                raise ValueError("时区格式无效，请使用如 +8、+08:00、-5。") from e

        if not (-12.0 <= val <= 14.0):
            raise ValueError("时区范围必须在 [-12, +14]。")
        return round(val * 60.0) / 60.0

    @staticmethod
    def _item_utc_from_iso(item: Optional[QTableWidgetItem]) -> Optional[datetime]:
        if item is None:
            return None
        raw = item.data(Qt.ItemDataRole.UserRole)
        if not raw:
            return None
        try:
            dt = datetime.fromisoformat(str(raw))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc)
        except Exception:
            return None

    def _parse_window_pair_to_utc(
        self, start_text: str, end_text: str, source_tz: timezone
    ) -> tuple[Optional[datetime], Optional[datetime]]:
        base_local = datetime.now(source_tz)
        s_local = self._parse_window_time(start_text, base_local)
        e_local = self._parse_window_time(end_text, base_local)
        if s_local is None or e_local is None:
            return None, None
        if e_local <= s_local:
            e_local = e_local + timedelta(days=1)
        return s_local.astimezone(timezone.utc), e_local.astimezone(timezone.utc)

    def _refresh_table_time_display(self):
        rows = self.ui.tableWidget.rowCount()
        for r in range(rows):
            s_item = self.ui.tableWidget.item(r, 2)
            e_item = self.ui.tableWidget.item(r, 3)
            s_utc = self._item_utc_from_iso(s_item)
            e_utc = self._item_utc_from_iso(e_item)
            if s_item is not None and s_utc is not None:
                s_item.setText(self._format_display_datetime(s_utc))
            if e_item is not None and e_utc is not None:
                e_item.setText(self._format_display_datetime(e_utc))
        self.ui.tableWidget.resizeColumnsToContents()

    def on_set_timezone(self):
        try:
            raw = self.ui.lineEdit_timezone.text().strip()
            off = self._parse_timezone_offset_hours(raw)
            self._display_tz_offset_hours = off
            self._display_tz = timezone(timedelta(hours=off))
            self.ui.lineEdit_timezone.setText(self._format_utc_offset(off))
            self._update_timezone_label()
            self._update_clock_label()
            self._refresh_table_time_display()
            self._refresh_visual_tracks()
        except Exception as e:
            QMessageBox.warning(self, "输入错误", str(e))

    def get_lon_lat(self):
        return self.longitude, self.latitude

    def on_set_longitude(self):
        try:
            lon = self._parse_float_from_lineedit(self.ui.lineEdit_longitude, "经度")
            if not (-180.0 <= lon <= 180.0):
                raise ValueError("经度范围必须在 [-180, 180]。")
            self.longitude = lon
            self.ui.lineEdit_longitude.setText(f"{lon:.4f}")
            self.ui.label_longitude.setText(f"经度：{lon:.4f}")
        except Exception as e:
            QMessageBox.warning(self, "输入错误", str(e))

    def on_set_latitude(self):
        try:
            lat = self._parse_float_from_lineedit(self.ui.lineEdit_latitude, "纬度")
            if not (-90.0 <= lat <= 90.0):
                raise ValueError("纬度范围必须在 [-90, 90]。")
            self.latitude = lat
            self.ui.lineEdit_latitude.setText(f"{lat:.4f}")
            self.ui.label_latitude.setText(f"纬度：{lat:.4f}")
        except Exception as e:
            QMessageBox.warning(self, "输入错误", str(e))

    def _update_threshold_label(self):
        self.ui.label_threshold.setText(f"偏差阈值：{self._offset_threshold_deg:.2f}°")

    def on_set_threshold(self):
        try:
            val = self._parse_float_from_lineedit(self.ui.lineEdit_threshold, "偏差阈值")
            if not (0.05 <= val <= 20.0):
                raise ValueError("偏差阈值范围建议在 [0.05, 20] 度。")
            self._offset_threshold_deg = float(val)
            self.ui.lineEdit_threshold.setText(f"{self._offset_threshold_deg:.2f}")
            self._update_threshold_label()
        except Exception as e:
            QMessageBox.warning(self, "输入错误", str(e))

    def on_choose_telescope(self):
        try:
            pythoncom.CoInitialize()
            chooser = win32com.client.Dispatch("ASCOM.Utilities.Chooser")
            chooser.DeviceType = "Telescope"
            prog_id = chooser.Choose(None)
            if not prog_id:
                return

            telescope = win32com.client.Dispatch(prog_id)
            telescope.Connected = True
            self.telescope = telescope
            self._mount_equatorial_system = None

            self.ui.label_connect_1.setText("已连接")
            QMessageBox.information(self, "ASCOM", f"已连接到：\n{telescope.Description}")
            self.telescope_selected.emit(prog_id)
        except Exception as e:
            QMessageBox.critical(self, "ASCOM错误", str(e))

    def _on_fetch_status(self, msg: str):
        print(msg)

    def _on_fetch_error(self, err: str):
        QMessageBox.critical(self, "抓取失败", err)
        self.ui.pushButton_seek.setEnabled(True)

    def _on_fetch_result(self, data: list):
        self.ui.tableWidget.setRowCount(len(data))
        for r, item in enumerate(data):
            start_utc = item.start_utc
            end_utc = item.end_utc
            if start_utc is None or end_utc is None:
                start_utc, end_utc = self._parse_window_pair_to_utc(
                    item.start_local, item.end_local, self._fetch_source_tz
                )
            start_text = self._format_display_datetime(start_utc) if start_utc else item.start_local
            end_text = self._format_display_datetime(end_utc) if end_utc else item.end_local

            start_item = QTableWidgetItem(start_text)
            end_item = QTableWidgetItem(end_text)
            if start_utc is not None:
                start_item.setData(Qt.ItemDataRole.UserRole, start_utc.isoformat())
            if end_utc is not None:
                end_item.setData(Qt.ItemDataRole.UserRole, end_utc.isoformat())

            name_item = QTableWidgetItem(item.name)
            if item.name_raw and item.name_raw != item.name:
                name_item.setToolTip(f"原始名称: {item.name_raw}")
            self.ui.tableWidget.setItem(r, 0, name_item)
            self.ui.tableWidget.setItem(r, 1, QTableWidgetItem(item.magnitude))
            self.ui.tableWidget.setItem(r, 2, start_item)
            self.ui.tableWidget.setItem(r, 3, end_item)
            self.ui.tableWidget.setItem(r, 4, QTableWidgetItem(item.max_alt))
            self.ui.tableWidget.setItem(r, 5, QTableWidgetItem(item.sat_id))
            self.ui.tableWidget.setItem(r, 6, QTableWidgetItem(item.tle1))
            self.ui.tableWidget.setItem(r, 7, QTableWidgetItem(item.tle2))
        self.ui.tableWidget.resizeColumnsToContents()

    def on_seek_satellites(self):
        lon, lat = self.get_lon_lat()
        if lon is None or lat is None:
            QMessageBox.warning(self, "提示", "请先设置经度和纬度。")
            return
        prefer_dawn = bool(getattr(self.ui, "checkBox_fetch_dawn", None) and self.ui.checkBox_fetch_dawn.isChecked())
        mag_limit_text = self.ui.comboBox_mag_limit.currentText().strip() if hasattr(self.ui, "comboBox_mag_limit") else "4.5"
        try:
            mag_limit = float(mag_limit_text)
        except Exception:
            QMessageBox.warning(self, "输入错误", f"最低亮度无效：{mag_limit_text}")
            return

        if self._worker and self._worker.isRunning():
            self._worker.stop()
            self._worker.wait(1000)

        # 凌晨：使用源站默认“当前时刻”列表；傍晚：锁定源站当天（UTC 对应日号）列表。
        day_mjd = None
        if not prefer_dawn:
            now_src = datetime.now(self._fetch_source_tz)
            # 按“源时区当天日期”计算日号，避免本地 00:xx 时被误判为前一天。
            src_day_utc_midnight = datetime(
                now_src.year, now_src.month, now_src.day, 0, 0, 0, tzinfo=timezone.utc
            )
            day_mjd = math.floor(TodaySatelliteScraper._datetime_utc_to_mjd(src_day_utc_midnight))

        self.ui.pushButton_seek.setEnabled(False)
        self.ui.tableWidget.setRowCount(0)

        self._worker = FetchWorker(
            lat=lat,
            lon=lon,
            h_m=self.height_m,
            location_name="Observer",
            tz=self._fetch_source_tz_name,
            day_mjd=day_mjd,
            prefer_dawn=prefer_dawn,
            mag_limit=mag_limit,
            parent=self,
        )
        self._worker.status.connect(self._on_fetch_status)
        self._worker.error.connect(self._on_fetch_error)
        self._worker.result.connect(self._on_fetch_result)
        self._worker.finished.connect(lambda: self.ui.pushButton_seek.setEnabled(True))
        self._worker.start()

    def _get_table_tle(self, row: int) -> tuple[str, str, str, str]:
        name_item = self.ui.tableWidget.item(row, 0)
        id_item = self.ui.tableWidget.item(row, 5)
        tle1_item = self.ui.tableWidget.item(row, 6)
        tle2_item = self.ui.tableWidget.item(row, 7)

        name = name_item.text().strip() if name_item else f"第{row}行"
        sat_id = id_item.text().strip() if id_item else ""
        tle1 = tle1_item.text().strip() if tle1_item else ""
        tle2 = tle2_item.text().strip() if tle2_item else ""
        return name, sat_id, tle1, tle2

    def _get_table_window_text(self, row: int) -> tuple[str, str]:
        start_item = self.ui.tableWidget.item(row, 2)
        end_item = self.ui.tableWidget.item(row, 3)
        start_text = start_item.text().strip() if start_item else ""
        end_text = end_item.text().strip() if end_item else ""
        return start_text, end_text

    def _get_table_window_utc(
        self, row: int
    ) -> tuple[Optional[datetime], Optional[datetime]]:
        start_item = self.ui.tableWidget.item(row, 2)
        end_item = self.ui.tableWidget.item(row, 3)
        start_utc = self._item_utc_from_iso(start_item)
        end_utc = self._item_utc_from_iso(end_item)
        if start_utc is not None and end_utc is not None:
            return start_utc, end_utc

        start_text, end_text = self._get_table_window_text(row)
        start_utc, end_utc = self._parse_window_pair_to_utc(
            start_text, end_text, self._fetch_source_tz
        )
        if start_item is not None and start_utc is not None:
            start_item.setData(Qt.ItemDataRole.UserRole, start_utc.isoformat())
        if end_item is not None and end_utc is not None:
            end_item.setData(Qt.ItemDataRole.UserRole, end_utc.isoformat())
        return start_utc, end_utc

    def _collect_stellarium_targets(self) -> tuple[list[StellariumTarget], int]:
        targets: list[StellariumTarget] = []
        rows = self.ui.tableWidget.rowCount()
        current_row = self.ui.tableWidget.currentRow()
        default_index = 0

        for row in range(rows):
            name, sat_id, tle1, tle2 = self._get_table_tle(row)
            start_utc, end_utc = self._get_table_window_utc(row)
            mag_item = self.ui.tableWidget.item(row, 1)
            magnitude = mag_item.text().strip() if mag_item else ""
            targets.append(
                StellariumTarget(
                    name=name,
                    sat_id=sat_id,
                    tle1=tle1,
                    tle2=tle2,
                    window_start_utc=start_utc,
                    window_end_utc=end_utc,
                    magnitude=magnitude,
                )
            )
            if row == current_row:
                default_index = len(targets) - 1

        if not targets:
            raise ValueError("当前没有已抓取卫星，请先执行搜索。")
        return targets, default_index

    def on_open_stellarium_dialog(self):
        try:
            lon, lat = self.get_lon_lat()
            if lon is None or lat is None:
                raise ValueError("请先设置经纬度。")
            targets, default_index = self._collect_stellarium_targets()
            if self._stellarium_dialog is not None:
                self._stellarium_dialog.close()
            self._stellarium_dialog = StellariumDialog(
                targets=targets,
                default_index=default_index,
                longitude=lon,
                latitude=lat,
                height_m=self.height_m,
                display_tz=self._display_tz,
                parent=self,
            )
            self._stellarium_dialog.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)
            self._stellarium_dialog.destroyed.connect(lambda *_: setattr(self, "_stellarium_dialog", None))
            self._stellarium_dialog.show()
            self._stellarium_dialog.raise_()
            self._stellarium_dialog.activateWindow()
        except Exception as e:
            QMessageBox.warning(self, "无法打开 Stellarium 联动", str(e))

    @staticmethod
    def _parse_window_time(text: str, base_date: datetime) -> Optional[datetime]:
        raw = (text or "").strip()
        if not raw:
            return None

        # Try complete datetime first
        fmts = [
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d %H:%M",
            "%Y/%m/%d %H:%M:%S",
            "%Y/%m/%d %H:%M",
            "%d %b %Y %H:%M:%S",
            "%d %b %Y %H:%M",
        ]
        for fmt in fmts:
            try:
                dt = datetime.strptime(raw, fmt)
                return dt.replace(tzinfo=base_date.tzinfo)
            except Exception:
                pass

        # Fallback: extract HH:MM[:SS] as same-day local time.
        m = re.search(r"(\d{1,2}):(\d{2})(?::(\d{2}))?", raw)
        if not m:
            return None
        hh = int(m.group(1))
        mm = int(m.group(2))
        ss = int(m.group(3)) if m.group(3) else 0
        if hh > 23 or mm > 59 or ss > 59:
            return None
        return base_date.replace(hour=hh, minute=mm, second=ss, microsecond=0)

    def _check_realtime_window(self, row: int) -> tuple[bool, str]:
        start_item = self.ui.tableWidget.item(row, 2)
        end_item = self.ui.tableWidget.item(row, 3)
        start_utc = self._item_utc_from_iso(start_item)
        end_utc = self._item_utc_from_iso(end_item)

        if start_utc is None or end_utc is None:
            start_text, end_text = self._get_table_window_text(row)
            start_utc, end_utc = self._parse_window_pair_to_utc(start_text, end_text, self._display_tz)
            if start_utc is None or end_utc is None:
                return False, f"窗口期解析失败：起始={start_text or '空'}，结束={end_text or '空'}。"
            if start_item is not None:
                start_item.setData(Qt.ItemDataRole.UserRole, start_utc.isoformat())
            if end_item is not None:
                end_item.setData(Qt.ItemDataRole.UserRole, end_utc.isoformat())

        now_utc = datetime.now(timezone.utc)
        if not (start_utc <= now_utc <= end_utc):
            return (
                False,
                "当前不在窗口期内。\n"
                f"窗口：{self._format_display_datetime(start_utc)} ~ {self._format_display_datetime(end_utc)}\n"
                f"当前：{self._format_display_datetime(now_utc)}",
            )
        return True, ""

    def on_table_selection_changed(self):
        row = self.ui.tableWidget.currentRow()
        if row < 0:
            return
        self.on_table_row_clicked(row, 0)

    def on_table_row_clicked(self, row: int, col: int):
        del col
        name, sat_id, tle1, tle2 = self._get_table_tle(row)
        if not (tle1 and tle2):
            QMessageBox.warning(self, "提示", "该行没有有效 TLE。")
            return

        self.ui.lineEdit_local_tle1.setText(tle1)
        self.ui.lineEdit_local_tle2.setText(tle2)
        start_utc, end_utc = self._get_table_window_utc(row)
        self._start_visual_tracks(name, tle1, tle2, start_utc, end_utc)

    def on_table_row_double_clicked(self, row: int, col: int):
        del col
        name, sat_id, tle1, tle2 = self._get_table_tle(row)
        if not (tle1 and tle2):
            QMessageBox.warning(self, "提示", "该行没有有效 TLE，无法开始跟踪。")
            return

        if (not self.ui.checkBox_virtual.isChecked()) and (not self.ui.checkBox_pretrack.isChecked()):
            ok_window, msg_window = self._check_realtime_window(row)
            if not ok_window:
                QMessageBox.information(self, "未到窗口期", msg_window)
                return

        ok, msg = self._start_tracking_with_tle(name=name, sat_id=sat_id, tle1=tle1, tle2=tle2)
        if not ok:
            QMessageBox.critical(self, "跟踪失败", msg)
            return

        # 双击才开始跟踪；单击仅预览地图/天空球。

    def on_start_local_tle(self):
        tle1 = self.ui.lineEdit_local_tle1.text().strip()
        tle2 = self.ui.lineEdit_local_tle2.text().strip()
        if not (tle1 and tle2):
            QMessageBox.warning(self, "提示", "请先粘贴本地TLE1和TLE2。")
            return

        sat_id = tle1[2:7].strip() if len(tle1) >= 7 else "LOCAL"
        name = f"本地-{sat_id}" if sat_id else "本地TLE"

        if (not self.ui.checkBox_virtual.isChecked()) and (not self.ui.checkBox_pretrack.isChecked()):
            row = self.ui.tableWidget.currentRow()
            if row < 0:
                QMessageBox.information(self, "未到窗口期", "非模拟模式下，请先在表格中选中一行以读取窗口期。")
                return
            ok_window, msg_window = self._check_realtime_window(row)
            if not ok_window:
                QMessageBox.information(self, "未到窗口期", msg_window)
                return

        ok, msg = self._start_tracking_with_tle(name=name, sat_id=sat_id or "LOCAL", tle1=tle1, tle2=tle2)
        if not ok:
            QMessageBox.critical(self, "跟踪失败", msg)
            return

        self._start_visual_tracks(name, tle1, tle2)
        QMessageBox.information(self, "跟踪已启动", "已使用本地TLE开始跟踪。")

    def _start_tracking_with_tle(self, name: str, sat_id: str, tle1: str, tle2: str) -> tuple[bool, str]:
        if self.telescope is None or not getattr(self.telescope, "Connected", False):
            return False, "请先连接赤道仪。"

        lon, lat = self.get_lon_lat()
        if lon is None or lat is None:
            return False, "请先设置经纬度。"

        try:
            satellite = SfEarthSatellite(tle1, tle2, name, self._ts)
            observer = wgs84.latlon(latitude_degrees=lat, longitude_degrees=lon)
        except Exception as e:
            return False, f"TLE解析失败：{e}"

        ok, msg = self._ensure_unparked()
        if not ok:
            return False, msg

        ok, msg = self._ensure_move_axis_ready()
        if not ok:
            return False, msg

        self._satellite = satellite
        self._observer = observer
        self._sat_name = name
        self._sat_id = sat_id
        self._tle1 = tle1
        self._tle2 = tle2
        self._mount_equatorial_system = None

        self._virtual_mode = self.ui.checkBox_virtual.isChecked()
        self._pretrack_mode = (not self._virtual_mode) and self.ui.checkBox_pretrack.isChecked()
        self._waiting_pretrack_start = False
        self._pretrack_start_utc = None
        self._virtual_sat_start_utc = None
        self._virtual_real_anchor_monotonic = None
        if self._virtual_mode:
            aos = self._find_next_aos_utc(satellite, observer)
            self._virtual_sat_start_utc = aos or datetime.now(timezone.utc)
            self._virtual_real_anchor_monotonic = time.monotonic()

        ok, msg = self._ensure_slew_ready()
        if not ok:
            return False, msg

        self._prev_sample_time_s = None
        self._prev_ra_hours = None
        self._prev_dec_deg = None
        self._auto_primary_rate = 0.0
        self._auto_secondary_rate = 0.0
        self._last_reslew_monotonic = 0.0
        self._slew_guard_until_monotonic = 0.0

        # 启动前先做一次 Slew 对位
        if self._pretrack_mode:
            aos = self._find_next_aos_utc(satellite, observer)
            if aos is None:
                return False, "预备跟踪模式下，未来48小时未找到可用升起点(AOS)。"
            ok, msg = self._slew_to_target_time(aos, lead_seconds=0.0)
            if not ok:
                return False, msg
            self._last_reslew_monotonic = time.monotonic()
            self._slew_guard_until_monotonic = self._last_reslew_monotonic + self._slew_settle_seconds
            self._pretrack_start_utc = aos
            self._waiting_pretrack_start = True
        else:
            ok, msg = self._slew_to_target_time(self._tracking_time_utc(), lead_seconds=0.0)
            if not ok:
                return False, msg
            self._last_reslew_monotonic = time.monotonic()
            self._slew_guard_until_monotonic = self._last_reslew_monotonic + self._slew_settle_seconds

        self._tracking_active = True

        self._set_static_labels()
        self._tracking_timer.start()
        if not self._waiting_pretrack_start:
            self._tracking_tick()
        else:
            self.ui.label_time.setText(
                f"预备中，等待AOS：{self._format_display_datetime(self._pretrack_start_utc)}"
            )
        if not self._tracking_active:
            return False, "首次MoveAxis下发失败。"
        return True, ""

    def _find_next_aos_utc(self, sat: SfEarthSatellite, observer) -> Optional[datetime]:
        try:
            t0 = self._ts.now()
            t1 = self._ts.from_datetime(datetime.now(timezone.utc) + timedelta(hours=48))
            times, events = sat.find_events(observer, t0, t1, altitude_degrees=0.0)
            for i, ev in enumerate(events):
                if ev == 0:
                    return times[i].utc_datetime().replace(tzinfo=timezone.utc)
        except Exception:
            return None
        return None

    def _ensure_slew_ready(self) -> tuple[bool, str]:
        has_async = hasattr(self.telescope, "SlewToCoordinatesAsync")
        has_sync = hasattr(self.telescope, "SlewToCoordinates")
        if not (has_async or has_sync):
            return False, "驱动不支持 SlewToCoordinates。"

        try:
            if has_async and hasattr(self.telescope, "CanSlewAsync"):
                if bool(self.telescope.CanSlewAsync):
                    return True, ""
            if has_sync and hasattr(self.telescope, "CanSlew"):
                if bool(self.telescope.CanSlew):
                    return True, ""
            # 某些驱动未实现 CanSlew*，但方法可调用；保守放行
            if has_async or has_sync:
                return True, ""
        except Exception as e:
            return False, f"Slew 能力检查失败：{e}"

        return False, "驱动不支持可用的 Slew 能力。"

    def _get_mount_equatorial_system(self) -> int:
        if self._mount_equatorial_system is not None:
            return self._mount_equatorial_system

        equ = EQU_TOPOCENTRIC
        if self.telescope is not None and hasattr(self.telescope, "EquatorialSystem"):
            try:
                equ = int(self.telescope.EquatorialSystem)
            except Exception:
                equ = EQU_TOPOCENTRIC
        self._mount_equatorial_system = equ
        return equ

    def _target_radec_at_time(self, when_utc: datetime) -> tuple[float, float]:
        if self._satellite is None or self._observer is None:
            raise RuntimeError("卫星或观测者未初始化。")
        if when_utc.tzinfo is None:
            when_utc = when_utc.replace(tzinfo=timezone.utc)
        t = self._ts.from_datetime(when_utc.astimezone(timezone.utc))
        topo = (self._satellite - self._observer).at(t)
        equ = self._get_mount_equatorial_system()
        if equ == EQU_J2000:
            ra, dec, _ = topo.radec()
        else:
            # ASCOM Scope Simulator reports equTopocentric=1, which aligns with equinox-of-date.
            ra, dec, _ = topo.radec(epoch="date")
        return float(ra.hours) % 24.0, float(dec.degrees)

    def _ensure_tracking_on_for_slew(self) -> tuple[bool, str]:
        if self.telescope is None or not getattr(self.telescope, "Connected", False):
            return False, "赤道仪未连接。"
        if not hasattr(self.telescope, "Tracking"):
            # 部分驱动未暴露 Tracking 属性，保守放行
            return True, ""

        try:
            can_set = True
            if hasattr(self.telescope, "CanSetTracking"):
                can_set = bool(self.telescope.CanSetTracking)
            if not can_set:
                try:
                    if bool(self.telescope.Tracking):
                        return True, ""
                except Exception as e:
                    return False, f"读取 Tracking 状态失败：{e}"
                return False, "驱动当前 Tracking=False 且 CanSetTracking=False，无法执行 Slew。"

            # 部分驱动要求在 Slew 前显式再次写入 Tracking=True，而不只是回读为 True。
            self.telescope.Tracking = True
            time.sleep(0.05)
            try:
                if not bool(self.telescope.Tracking):
                    return False, "设置 Tracking=True 失败，驱动仍返回 Tracking=False。"
            except Exception:
                # 若驱动不支持回读，允许继续尝试 Slew
                pass
            return True, ""
        except Exception as e:
            return False, f"设置 Tracking=True 失败：{e}"

    def _slew_to_coordinates(self, ra_hours: float, dec_deg: float, timeout_s: float = 60.0) -> tuple[bool, str]:
        if self.telescope is None or not getattr(self.telescope, "Connected", False):
            return False, "赤道仪未连接。"
        if self._slew_in_progress:
            return False, "Slew 正在执行中。"

        ok, msg = self._ensure_unparked()
        if not ok:
            return False, msg

        ok, msg = self._ensure_tracking_on_for_slew()
        if not ok:
            return False, msg

        # Slew 前先将 MoveAxis 归零，避免驱动层冲突
        self._send_axis_rates(0.0, 0.0, force=True)

        def _do_slew_once() -> tuple[bool, str]:
            can_async_local = hasattr(self.telescope, "SlewToCoordinatesAsync")
            if can_async_local and hasattr(self.telescope, "CanSlewAsync"):
                can_async_local = bool(self.telescope.CanSlewAsync)

            can_sync_local = hasattr(self.telescope, "SlewToCoordinates")
            if can_sync_local and hasattr(self.telescope, "CanSlew"):
                can_sync_local = bool(self.telescope.CanSlew)

            if can_async_local:
                if hasattr(self.telescope, "Tracking"):
                    self.telescope.Tracking = True
                self.telescope.SlewToCoordinatesAsync(float(ra_hours), float(dec_deg))
                t0 = time.monotonic()
                while time.monotonic() - t0 < timeout_s:
                    QApplication.processEvents()
                    try:
                        if hasattr(self.telescope, "Slewing") and not bool(self.telescope.Slewing):
                            return True, ""
                    except Exception:
                        # 若驱动没有稳定 Slewing 属性，给一点时间后认为完成
                        if time.monotonic() - t0 > 2.0:
                            return True, ""
                    time.sleep(0.05)
                return False, "Slew 超时。"

            if can_sync_local:
                if hasattr(self.telescope, "Tracking"):
                    self.telescope.Tracking = True
                self.telescope.SlewToCoordinates(float(ra_hours), float(dec_deg))
                return True, ""

            return False, "驱动不支持 SlewToCoordinates。"

        self._slew_in_progress = True
        try:
            return _do_slew_once()
        except Exception as e:
            msg_e = str(e)
            msg_lower = msg_e.lower()
            # 某些驱动（如 ASCOM Scope Simulator）要求 Slew 前 Tracking 必须为 True。
            if ("tracking state" in msg_lower) or ("wrong tracking state" in msg_lower):
                ok, msg2 = self._ensure_tracking_on_for_slew()
                if not ok:
                    return False, f"Slew 执行失败：{msg_e}；且自动设置 Tracking 失败：{msg2}"
                try:
                    return _do_slew_once()
                except Exception as e2:
                    return False, f"Slew 执行失败：{e2}"
            return False, f"Slew 执行失败：{e}"
        finally:
            self._slew_in_progress = False

    def _slew_to_target_time(self, base_utc: datetime, lead_seconds: float = 0.0) -> tuple[bool, str]:
        target_utc = base_utc.astimezone(timezone.utc) + timedelta(seconds=float(lead_seconds))
        try:
            ra_h, dec_d = self._target_radec_at_time(target_utc)
            return self._slew_to_coordinates(ra_h, dec_d)
        except Exception as e:
            return False, f"计算Slew目标失败：{e}"

    @staticmethod
    def _angular_sep_deg(ra1_h: float, dec1_d: float, ra2_h: float, dec2_d: float) -> float:
        r1 = math.radians(ra1_h * 15.0)
        d1 = math.radians(dec1_d)
        r2 = math.radians(ra2_h * 15.0)
        d2 = math.radians(dec2_d)
        c = math.sin(d1) * math.sin(d2) + math.cos(d1) * math.cos(d2) * math.cos(r1 - r2)
        c = min(1.0, max(-1.0, c))
        return math.degrees(math.acos(c))

    def _current_mount_error_deg(self, target_ra_h: float, target_dec_d: float) -> tuple[bool, str, float]:
        try:
            if not hasattr(self.telescope, "RightAscension") or not hasattr(self.telescope, "Declination"):
                return False, "驱动不支持读取当前 RA/Dec，无法计算偏差。", 0.0
            cur_ra = float(self.telescope.RightAscension)
            cur_dec = float(self.telescope.Declination)
            err = self._angular_sep_deg(target_ra_h, target_dec_d, cur_ra, cur_dec)
            return True, "", err
        except Exception as e:
            return False, f"读取当前 RA/Dec 失败：{e}", 0.0

    def _ensure_move_axis_ready(self) -> tuple[bool, str]:
        try:
            if not hasattr(self.telescope, "MoveAxis"):
                return False, "驱动不支持 MoveAxis。"

            can_primary = True
            can_secondary = True
            if hasattr(self.telescope, "CanMoveAxis"):
                can_primary = bool(self.telescope.CanMoveAxis(0))
                can_secondary = bool(self.telescope.CanMoveAxis(1))

            if not can_primary or not can_secondary:
                return False, "驱动返回 CanMoveAxis=False（轴0/1）。"

            ranges0 = self._query_axis_ranges(0)
            ranges1 = self._query_axis_ranges(1)
            if not ranges0:
                return False, "轴0的 AxisRates 无效。"
            if not ranges1:
                return False, "轴1的 AxisRates 无效。"

            self._axis_ranges[0] = ranges0
            self._axis_ranges[1] = ranges1

            manual0 = self._preferred_manual_max(ranges0)
            manual1 = self._preferred_manual_max(ranges1)
            if manual0 <= 0 or manual1 <= 0:
                return False, "AxisRates 未提供可用的手动速度区间。"
            self._manual_max_ref = min(manual0, manual1)
            return True, ""
        except Exception as e:
            return False, f"MoveAxis 能力检查失败：{e}"

    def _query_axis_ranges(self, axis: int) -> list[tuple[float, float]]:
        try:
            rates = self.telescope.AxisRates(axis)
            if rates is None:
                return []
            pairs = []
            if hasattr(rates, "Count") and hasattr(rates, "Item"):
                count = int(rates.Count)
                for i in range(1, count + 1):
                    item = rates.Item(i)
                    pairs.append((float(item.Minimum), float(item.Maximum)))
            else:
                for item in rates:
                    pairs.append((float(item.Minimum), float(item.Maximum)))

            cleaned = []
            for a, b in pairs:
                mn = min(abs(a), abs(b))
                mx = max(abs(a), abs(b))
                if mx > 0:
                    cleaned.append((mn, mx))
            cleaned.sort(key=lambda x: (x[0], x[1]))
            return cleaned
        except Exception:
            return []

    @staticmethod
    def _preferred_manual_max(ranges: list[tuple[float, float]]) -> float:
        # Prefer low-speed continuous range for manual guiding.
        for mn, mx in ranges:
            if mn <= 0:
                return mx
        return ranges[0][1] if ranges else 0.0

    def _tracking_time_utc(self) -> datetime:
        if self._virtual_mode and self._virtual_sat_start_utc and self._virtual_real_anchor_monotonic is not None:
            elapsed = max(0.0, time.monotonic() - self._virtual_real_anchor_monotonic)
            return self._virtual_sat_start_utc + timedelta(seconds=elapsed)
        return datetime.now(timezone.utc)

    def _tracking_tick(self):
        if not self._tracking_active:
            return
        if self._satellite is None or self._observer is None:
            return
        if self.telescope is None or not getattr(self.telescope, "Connected", False):
            self.stop_tracking(show_message=False)
            QMessageBox.warning(self, "跟踪已停止", "赤道仪连接已断开。")
            return

        try:
            if self._waiting_pretrack_start:
                now_utc = datetime.now(timezone.utc)
                if self._pretrack_start_utc and now_utc < self._pretrack_start_utc:
                    remain = (self._pretrack_start_utc - now_utc).total_seconds()
                    self._send_axis_rates(0.0, 0.0)
                    self.ui.label_time.setText(
                        f"预备中，距开始跟踪还有 {remain:.1f} 秒（AOS {self._to_display_dt(self._pretrack_start_utc).strftime('%H:%M:%S')}）"
                    )
                    return

                ok, msg = self._slew_to_target_time(now_utc, lead_seconds=0.0)
                if not ok:
                    self.stop_tracking(show_message=False)
                    QMessageBox.critical(self, "跟踪中断", f"预备模式切换跟踪失败：{msg}")
                    return
                self._waiting_pretrack_start = False
                self._prev_sample_time_s = None
                self._prev_ra_hours = None
                self._prev_dec_deg = None
                self._last_reslew_monotonic = time.monotonic()
                self._slew_guard_until_monotonic = self._last_reslew_monotonic + self._slew_settle_seconds

            track_dt = self._tracking_time_utc()
            t = self._ts.from_datetime(track_dt)

            topo = (self._satellite - self._observer).at(t)
            alt, az, _ = topo.altaz()

            ra_hours, dec_deg = self._target_radec_at_time(track_dt)
            alt_deg = float(alt.degrees)
            az_deg = float(az.degrees)

            ok_err, msg_err, err_deg = self._current_mount_error_deg(ra_hours, dec_deg)
            if not ok_err:
                self.stop_tracking(show_message=False)
                QMessageBox.critical(self, "跟踪中断", msg_err)
                return
            now_mono = time.monotonic()
            if (
                err_deg > self._offset_threshold_deg
                and (not self._slew_in_progress)
                and (now_mono >= self._slew_guard_until_monotonic)
            ):
                if (now_mono - self._last_reslew_monotonic) >= self._reslew_min_interval_seconds:
                    ok, msg = self._slew_to_target_time(track_dt, lead_seconds=self._reslew_lead_seconds)
                    self._last_reslew_monotonic = time.monotonic()
                    if not ok:
                        self.stop_tracking(show_message=False)
                        QMessageBox.critical(self, "跟踪中断", f"偏差{err_deg:.2f}°触发二次Slew失败：{msg}")
                        return
                    self._prev_sample_time_s = None
                    self._prev_ra_hours = None
                    self._prev_dec_deg = None
                    self._slew_guard_until_monotonic = self._last_reslew_monotonic + self._slew_settle_seconds
                    mode_text = "模拟" if self._virtual_mode else "实时"
                    disp_dt = self._to_display_dt(track_dt)
                    self.ui.label_time.setText(
                        f"{mode_text} {disp_dt.strftime('%Y-%m-%d %H:%M:%S')} {self._format_utc_offset(self._display_tz_offset_hours)} | 偏差{err_deg:.2f}°，已重对位"
                    )
                    return

            sample_t_s = track_dt.timestamp()
            primary_rate = 0.0
            secondary_rate = 0.0
            if (
                self._prev_sample_time_s is not None
                and self._prev_ra_hours is not None
                and self._prev_dec_deg is not None
            ):
                dt = sample_t_s - self._prev_sample_time_s
                if dt > 0:
                    ra_deg = ra_hours * 15.0
                    prev_ra_deg = self._prev_ra_hours * 15.0
                    d_ra = ((ra_deg - prev_ra_deg + 180.0) % 360.0) - 180.0
                    d_dec = dec_deg - self._prev_dec_deg
                    primary_rate = d_ra / dt
                    secondary_rate = d_dec / dt

            self._prev_sample_time_s = sample_t_s
            self._prev_ra_hours = ra_hours
            self._prev_dec_deg = dec_deg

            if self.ui.checkBox_ot_right.isChecked():
                primary_rate *= -1.0
            if self.ui.checkBox_ot_up.isChecked():
                secondary_rate *= -1.0

            self._auto_primary_rate = primary_rate
            self._auto_secondary_rate = secondary_rate

            cmd_primary, cmd_secondary = self._compose_axis_rates(include_auto=True)
            ok, msg = self._send_axis_rates(cmd_primary, cmd_secondary)
            if not ok:
                self.stop_tracking(show_message=False)
                QMessageBox.critical(self, "跟踪中断", msg)
                return

            self._update_live_labels(
                track_dt=track_dt,
                ra_hours=ra_hours,
                dec_deg=dec_deg,
                alt_deg=alt_deg,
                az_deg=az_deg,
                cmd_primary=cmd_primary,
                cmd_secondary=cmd_secondary,
            )
        except Exception as e:
            self.stop_tracking(show_message=False)
            QMessageBox.critical(self, "跟踪中断", f"跟踪周期执行失败：{e}")

    def _manual_base_rate(self) -> float:
        slider = self.ui.horizontalSlider.value() / 100.0
        ref_max = self._manual_max_ref if (self._manual_max_ref and self._manual_max_ref > 0) else 2.0
        return slider * (ref_max * 0.5)

    def _manual_rates(self) -> tuple[float, float]:
        base = self._manual_base_rate()
        primary = self._manual_primary_dir * base
        secondary = self._manual_secondary_dir * base

        if self.ui.checkBox_down.isChecked():
            primary *= -1.0
        if self.ui.checkBox_up.isChecked():
            secondary *= -1.0
        return primary, secondary

    def _compose_axis_rates(self, include_auto: bool) -> tuple[float, float]:
        auto_primary = self._auto_primary_rate if include_auto else 0.0
        auto_secondary = self._auto_secondary_rate if include_auto else 0.0
        man_primary, man_secondary = self._manual_rates()
        return auto_primary + man_primary, auto_secondary + man_secondary

    def _clamp_axis_rate(self, axis: int, rate: float) -> float:
        if abs(rate) < 1e-9:
            return 0.0
        ranges = self._axis_ranges.get(axis, [])
        if not ranges:
            return rate

        sign = 1.0 if rate >= 0 else -1.0
        mag = abs(rate)
        eps = 1e-9

        # Already in an allowed interval.
        for mn, mx in ranges:
            if (mn - eps) <= mag <= (mx + eps):
                return sign * min(max(mag, mn), mx)

        # Below the first allowed minimum: keep safe stop.
        first_mn, _first_mx = ranges[0]
        if mag < first_mn:
            return 0.0

        # Between two intervals: snap to nearest boundary.
        for i in range(len(ranges) - 1):
            _mn, mx = ranges[i]
            next_mn, _next_mx = ranges[i + 1]
            if mx < mag < next_mn:
                boundary = mx if (mag - mx) <= (next_mn - mag) else next_mn
                return sign * boundary

        # Above max interval: clamp to highest allowed.
        return sign * ranges[-1][1]

    def _send_axis_rates(self, primary_rate: float, secondary_rate: float, force: bool = False) -> tuple[bool, str]:
        primary_rate = self._clamp_axis_rate(0, float(primary_rate))
        secondary_rate = self._clamp_axis_rate(1, float(secondary_rate))
        if not force:
            if (
                abs(primary_rate - self._last_sent_primary) < 1e-7
                and abs(secondary_rate - self._last_sent_secondary) < 1e-7
            ):
                return True, ""

        try:
            self.telescope.MoveAxis(0, primary_rate)
            self.telescope.MoveAxis(1, secondary_rate)
            self._last_sent_primary = primary_rate
            self._last_sent_secondary = secondary_rate
            return True, ""
        except Exception as e:
            msg = str(e)
            if self._is_parked_error(msg):
                ok, unpark_msg = self._ensure_unparked()
                if not ok:
                    return False, f"MoveAxis失败（设备驻车）：{unpark_msg}"
                try:
                    self.telescope.MoveAxis(0, primary_rate)
                    self.telescope.MoveAxis(1, secondary_rate)
                    self._last_sent_primary = primary_rate
                    self._last_sent_secondary = secondary_rate
                    return True, ""
                except Exception as e2:
                    return False, f"MoveAxis失败（解驻车重试后）：{e2}"
            return False, f"MoveAxis失败：{e}"

    def _set_static_labels(self):
        self.ui.label_tle.setText(self._tle1 if self._tle1 else "TLE1：未知")
        self.ui.label_tle2.setText(self._tle2 if self._tle2 else "TLE2：未知")
        self.ui.label_id.setText(f"卫星ID：{self._sat_id or '未知'}")

    def _update_live_labels(
        self,
        track_dt: datetime,
        ra_hours: float,
        dec_deg: float,
        alt_deg: float,
        az_deg: float,
        cmd_primary: float,
        cmd_secondary: float,
    ):
        mode = "模拟" if self._virtual_mode else "实时"
        disp_dt = self._to_display_dt(track_dt)
        self.ui.label_time.setText(
            f"{mode} {disp_dt.strftime('%Y-%m-%d %H:%M:%S')} {self._format_utc_offset(self._display_tz_offset_hours)}"
        )
        self.ui.label_ra.setText(f"赤经：{ra_hours:.6f} h")
        self.ui.label_dec.setText(f"赤纬：{dec_deg:.6f}°")
        self.ui.label_speed_star.setText(
            f"轴速率 主:{cmd_primary:+.6f}  副:{cmd_secondary:+.6f}°/s  高度/方位 {alt_deg:.2f}/{az_deg:.2f}°"
        )

    def _update_speed_label(self):
        base = self._manual_base_rate()
        self.ui.label_speed.setText(f"手动速度：{base:.4f}°/s")

    def _on_slider_changed(self, value: int):
        del value
        self._update_speed_label()
        self._apply_manual_now()

    def _set_manual_primary(self, direction: int):
        self._manual_primary_dir = direction
        self._apply_manual_now()

    def _release_manual_primary(self, direction: int):
        if self._manual_primary_dir == direction:
            self._manual_primary_dir = 0
            self._apply_manual_now()

    def _set_manual_secondary(self, direction: int):
        self._manual_secondary_dir = direction
        self._apply_manual_now()

    def _release_manual_secondary(self, direction: int):
        if self._manual_secondary_dir == direction:
            self._manual_secondary_dir = 0
            self._apply_manual_now()

    def _apply_manual_now(self):
        if self.telescope is None or not getattr(self.telescope, "Connected", False):
            return
        # 预备等待或 Slew 期间不接受手动微调，避免与自动流程冲突。
        if self._waiting_pretrack_start or self._slew_in_progress:
            return

        include_auto = self._tracking_active and (not self._waiting_pretrack_start)
        p, s = self._compose_axis_rates(include_auto=include_auto)
        ok, msg = self._send_axis_rates(p, s)
        if not ok:
            # 手动微调属于辅助输入，失败时不应打断自动跟踪主流程。
            print(f"[Manual] MoveAxis失败（已忽略）: {msg}")
            if hasattr(self.ui, "label_time"):
                self.ui.label_time.setText("手动微调下发失败（已忽略）")

    def stop_tracking(self, show_message: bool = True):
        if self._tracking_timer.isActive():
            self._tracking_timer.stop()
        self._tracking_active = False

        if self.telescope is not None and getattr(self.telescope, "Connected", False):
            self._send_axis_rates(0.0, 0.0, force=True)

        self._satellite = None
        self._observer = None
        self._sat_name = ""
        self._sat_id = ""
        self._tle1 = ""
        self._tle2 = ""
        self._virtual_sat_start_utc = None
        self._virtual_real_anchor_monotonic = None
        self._pretrack_mode = False
        self._waiting_pretrack_start = False
        self._slew_in_progress = False
        self._pretrack_start_utc = None

        self._prev_sample_time_s = None
        self._prev_ra_hours = None
        self._prev_dec_deg = None
        self._auto_primary_rate = 0.0
        self._auto_secondary_rate = 0.0
        self._last_sent_primary = 0.0
        self._last_sent_secondary = 0.0
        self._last_reslew_monotonic = 0.0
        self._slew_guard_until_monotonic = 0.0

        if show_message:
            QMessageBox.information(self, "已停止", "卫星跟踪已停止。")

    def on_stop_draw_track(self):
        self._visual_name = ""
        self._raw_pass_track = []
        self._raw_pass_status = ""
        self._raw_ground_track = []
        self._raw_ground_status = ""
        if hasattr(self.ui, "widget_sky"):
            self.ui.widget_sky.clear()
        if hasattr(self.ui, "widget_map"):
            self.ui.widget_map.clear()

    def on_stop_all(self):
        self.stop_tracking(show_message=False)
        self.on_stop_draw_track()
        QMessageBox.information(self, "已停止", "跟踪与轨迹绘制已停止。")

    def on_sat_row_clicked_draw_track(self, row: int, col: int):
        del col
        lon, lat = self.get_lon_lat()
        if lon is None or lat is None:
            QMessageBox.warning(self, "提示", "请先设置经纬度。")
            return

        name, _sat_id, tle1, tle2 = self._get_table_tle(row)
        if not (tle1 and tle2):
            QMessageBox.warning(self, "提示", "该行没有有效TLE，无法绘制轨迹。")
            return

        start_utc, end_utc = self._get_table_window_utc(row)
        self._start_visual_tracks(name, tle1, tle2, start_utc, end_utc)

    def _start_visual_tracks(
        self,
        name: str,
        tle1: str,
        tle2: str,
        window_start_utc: Optional[datetime] = None,
        window_end_utc: Optional[datetime] = None,
    ):
        lon, lat = self.get_lon_lat()
        if lon is None or lat is None:
            QMessageBox.warning(self, "提示", "请先设置经纬度后再预览轨迹。")
            return

        self._plot_request_id += 1
        req_id = self._plot_request_id
        self._visual_name = name
        self._raw_pass_track = []
        self._raw_ground_track = []
        if window_start_utc is not None and window_end_utc is not None:
            self._raw_pass_status = "正在计算所选窗口轨迹..."
        else:
            self._raw_pass_status = "正在计算下一次过境轨迹..."
        self._raw_ground_status = "正在计算地面轨迹..."
        self._refresh_visual_tracks()

        self._pass_worker = NextPassWorker(
            tle1=tle1,
            tle2=tle2,
            name=name,
            lat=lat,
            lon=lon,
            window_start_utc=window_start_utc,
            window_end_utc=window_end_utc,
            parent=self,
        )
        self._pass_worker.error.connect(lambda msg, rid=req_id: self._on_pass_error(rid, msg))
        self._pass_worker.result.connect(
            lambda nm, track, status, rid=req_id: self._on_pass_track_ready(rid, nm, track, status)
        )
        self._pass_worker.start()

        self._ground_worker = GroundTrackWorker(
            tle1=tle1, tle2=tle2, name=name, minutes=120, step_s=10, parent=self
        )
        self._ground_worker.error.connect(lambda msg, rid=req_id: self._on_ground_error(rid, msg))
        self._ground_worker.result.connect(
            lambda nm, track, status, rid=req_id: self._on_ground_track_ready(rid, nm, track, status)
        )
        self._ground_worker.start()

    def _on_pass_error(self, req_id: int, msg: str):
        if req_id != self._plot_request_id:
            return
        QMessageBox.critical(self, "天空球轨迹失败", msg)

    def _on_ground_error(self, req_id: int, msg: str):
        if req_id != self._plot_request_id:
            return
        QMessageBox.critical(self, "地面轨迹失败", msg)

    def _on_pass_track_ready(self, req_id: int, name: str, track: list, status: str):
        if req_id != self._plot_request_id:
            return
        self._visual_name = name
        self._raw_pass_track = track or []
        self._raw_pass_status = status or ""
        self._refresh_visual_tracks()

    def _on_ground_track_ready(self, req_id: int, name: str, track: list, status: str):
        if req_id != self._plot_request_id:
            return
        self._visual_name = name
        self._raw_ground_track = track or []
        self._raw_ground_status = status or ""
        self._refresh_visual_tracks()

    def _on_visual_flip_changed(self, checked: bool):
        del checked
        self._refresh_visual_tracks()

    @staticmethod
    def _norm_lon(lon: float) -> float:
        return ((float(lon) + 180.0) % 360.0) - 180.0

    def _transform_sky_track(self, track: list) -> list:
        flip_lr = self.ui.checkBox_ot_right.isChecked()
        flip_ud = self.ui.checkBox_ot_up.isChecked()
        out = []
        for p in (track or []):
            q = dict(p)
            t = q.get("t")
            if isinstance(t, datetime):
                if t.tzinfo is None:
                    t = t.replace(tzinfo=timezone.utc)
                q["t"] = t.astimezone(self._display_tz)
            try:
                az = float(q.get("az", 0.0))
            except Exception:
                out.append(q)
                continue

            if flip_lr and flip_ud:
                az = (az + 180.0) % 360.0
            elif flip_lr:
                az = (360.0 - az) % 360.0
            elif flip_ud:
                az = (180.0 - az) % 360.0

            q["az"] = az
            out.append(q)
        return out

    def _transform_ground_track(self, track: list) -> list:
        flip_lr = self.ui.checkBox_ot_right.isChecked()
        flip_ud = self.ui.checkBox_ot_up.isChecked()
        if (not flip_lr) and (not flip_ud):
            return [dict(p) for p in (track or [])]

        out = []
        for p in (track or []):
            q = dict(p)
            try:
                lon = float(q.get("lon", 0.0))
                lat = float(q.get("lat", 0.0))
            except Exception:
                out.append(q)
                continue

            if flip_lr:
                lon = -lon
            if flip_ud:
                lat = -lat

            q["lon"] = self._norm_lon(lon)
            q["lat"] = max(-90.0, min(90.0, lat))
            out.append(q)
        return out

    def _refresh_visual_tracks(self):
        name = self._visual_name or ""
        if hasattr(self.ui, "widget_sky"):
            self.ui.widget_sky.set_track(
                name,
                self._transform_sky_track(self._raw_pass_track),
                self._raw_pass_status or "",
            )
        if hasattr(self.ui, "widget_map"):
            self.ui.widget_map.set_track(
                name,
                self._transform_ground_track(self._raw_ground_track),
                self._raw_ground_status or "",
            )


if __name__ == "__main__":
    app = QApplication(sys.argv)
    widget = Main_menu()
    widget.show()
    sys.exit(app.exec())
