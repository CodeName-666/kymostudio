# This Python file uses the following encoding: utf-8
import hashlib
import json
import math
import time
from collections import deque
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, List, Optional

from PySide6.QtCore import QObject, Slot, Signal, QTimer, Property
from PySide6.QtQml import QJSValue
from serial.tools import list_ports

from Receiver.registry import ReceiverRegistry, parse_interface_definitions
from Receiver.message import PlotDataPoint
from Receiver.binary_protocol import ProtocolError
from Common.converter import Converter
from Logger import logger
from Logger.logger import Logger
from Core.parsing import parse_payload
from Core.buffering import peak_envelope, FrameBuffer
from Core.configuration import atomic_json_write, local_path, validate_configuration, MAX_CONFIGURATION_BYTES
from Core.workspace import validate_workspace
from Core.paths import user_config_path
from Core.samples import Sample, SampleStore
from Backend.connection_service import ConnectionInfo, ConnectionService
from Backend.export_worker import CsvExportWorker


def _get_serial_ports() -> List[str]:
    ports = list_ports.comports()
    return [port.name for port in ports]






class Backend(QObject):
    """Single QObject-based backend used by QML."""

    __backend_instance: Optional["Backend"] = None

    _TEST_SIGNAL_TEMPLATES: List[Dict[str, Any]] = [
        {"dataId": 0, "displayName": "Sine Wave", "color": "#ff6b6b"},
        {"dataId": 1, "displayName": "Cosine Wave", "color": "#4ecdc4"},
        {"dataId": 2, "displayName": "Sine Wave (2x)", "color": "#ffe66d"},
    ]

    # Settings signals
    status_message = Signal(str, str)
    new_interface = Signal(str)
    new_settings = Signal("QJSValue")

    # Setup/connection signals
    ui_setup = Signal("QVariant")
    ui_setup_done_changed = Signal(bool)
    backend_setup_done_changed = Signal(bool)

    # Serial-port discovery
    com_port_update = Signal("QVariant")

    # Multi-connection management
    connections_changed = Signal("QVariant")  # Emitted when connection list changes
    connection_status_changed = Signal(str, str, "QVariant")  # (connection_id, status, details)

    def __init__(self, config_path: str | Path | None = None) -> None:
        super().__init__()
        if Backend.__backend_instance is not None:
            raise RuntimeError("Backend already initialized")

        # Settings state
        self.__settings = QJSValue()
        self.__interface = ""

        # Setup state
        self.ui_config: Dict[str, Any] | None = None
        self.__ui_setup_done = False
        self.__backend_setup_done = False

        # Receiver/graph bookkeeping
        self.__receiver_registry = ReceiverRegistry()
        self.__interfaces_config: Dict[str, Any] = {}
        self.__default_templates: Dict[str, Dict[str, Any]] = {}  # interface_type -> default settings (templates)
        self._backend_events: QObject | None = None
        self._ui_handle: QObject | None = None
        self._graph_state: Dict[str, Dict[str, Any]] = {}  # Key: unique_id (format: "interface_id")
        self._chart_line_overrides: Dict[str, Dict[str, str]] = {}
        self._pending_events: Dict[str, List[tuple]] = {}
        self._app_start_time: float = time.time()  # For timestamp normalization
        self._ignored_signals: set[str] = set()  # unique_id values to ignore (disabled signals)

        # Multi-connection management (primary system)
        self.__connections: Dict[str, ConnectionInfo] = {}  # connection_id -> ConnectionInfo
        self.__connection_counter: int = 0  # Counter for generating unique IDs
        self.__config_path = str(Path(config_path) if config_path else user_config_path())
        self._base_config: dict = {}
        self._sample_store = SampleStore()
        self._capture_start: float | None = None
        self._source_time_origins: dict[str, float] = {}
        self._parse_warning_times: dict[str, float] = {}
        self._received_total = self._invalid_total = self._display_dropped = 0
        self._display_reduced = self._event_dropped = self._signal_limit_dropped = 0
        self._max_pending_points = 4096
        self._display_point_limit = 10000
        self._display_paused = False
        self._export_worker = None
        self._metrics_time = time.monotonic()
        self._metrics_received = 0
        self._connection_service = ConnectionService(
            self.__receiver_registry, self._on_receiver_data, self._emit_connections_changed,
            self._emit_connection_status_changed, self._notify_status)
        self.__connections = self._connection_service.connections

        # Performance optimization: Batch updates
        self._frames_2d = FrameBuffer(self._max_pending_points)
        self._frames_3d = FrameBuffer(self._max_pending_points)
        self._point_buffer = self._frames_2d.queues
        self._point_buffer_3d = self._frames_3d.queues
        self._batch_timer = QTimer(self)
        self._batch_timer.timeout.connect(self._flush_point_buffer)
        self._batch_timer.start(33)  # Display clock, independent of acquisition rate.
        self._batch_size = 4096  # Upper bound on points per series/frame.

        # Performance optimization: Downsampling
        self._downsample_enabled = False  # Disabled by default
        self._downsample_target_hz = 50.0  # Target display rate
        self._last_emit_time: Dict[str, float] = {}  # Track last emit time per line

        # Serial port polling
        self.__com_updater_timer = QTimer(self)
        self.__com_list: List[str] = []
        self.__com_updater_timer.timeout.connect(self._update_com_ports)
        self.__com_updater_timer.start(1000)

        # Signal wiring to forward into QML event bridge
        self.backend_setup_done_changed.connect(self.on_backend_setup_done)
        self.ui_setup.connect(self._on_ui_setup_signal)
        self.com_port_update.connect(self._forward_com_port_update)

        Backend.__backend_instance = self

    @staticmethod
    def get_instance() -> "Backend":
        if Backend.__backend_instance is None:
            Backend()
        return Backend.__backend_instance  # type: ignore[return-value]

    # ------------------------------------------------------------------ #
    # Properties exposed to QML
    # ------------------------------------------------------------------ #
    @Property(str, notify=new_interface)
    def interface(self) -> str:
        return self.__interface

    @interface.setter
    def interface(self, new_interface: str) -> None:
        if self.__interface != new_interface:
            self.__interface = new_interface
            self.new_interface.emit(new_interface)
            logger.log_debug("New Interface: {}".format(new_interface))

    @Property("QJSValue", notify=new_settings)
    def settings(self) -> QJSValue:
        return self.__settings

    @settings.setter
    def settings(self, new_settings: QJSValue) -> None:
        if self.__settings != new_settings:
            self.__settings = new_settings
            logger.log_debug("New Settings")
            self.new_settings.emit(new_settings)

    @Property(bool, notify=backend_setup_done_changed)
    def backend_setup_done(self) -> bool:
        return self.__backend_setup_done

    @backend_setup_done.setter
    def backend_setup_done(self, status: bool) -> None:
        if self.__backend_setup_done != status:
            logger.log_info("Backend Setup Status: {}".format(status))
            self.__backend_setup_done = status
            self.backend_setup_done_changed.emit(status)

    @Property(bool, notify=ui_setup_done_changed)
    def ui_setup_done(self) -> bool:
        return self.__ui_setup_done

    @ui_setup_done.setter
    def ui_setup_done(self, status: bool) -> None:
        if self.__ui_setup_done != status:
            logger.log_info("UI Setup Status: {}".format(status))
            self.__ui_setup_done = status
            self.ui_setup_done_changed.emit(status)

    # ------------------------------------------------------------------ #
    # Public API used from QML/receivers
    # ------------------------------------------------------------------ #
    def config(self, config: dict) -> None:
        if not config:
            logger.log_error("Backend configuration missing")
            return

        validate_configuration(config)
        self._base_config = deepcopy(config)
        performance = config.get("performance", {})
        self.set_batch_interval(int(performance.get("frame_interval_ms", 33)))
        self._display_point_limit = max(500, min(50000, int(performance.get("display_points_per_signal", 10000))))
        self._downsample_enabled = bool(performance.get("downsample_enabled", False))
        self.set_downsample_target_hz(float(performance.get("downsample_target_hz", 1000.0)))
        self.ui_config = config.get("qml", {})
        self.__interfaces_config = parse_interface_definitions(config.get("interfaces", []))
        self._graph_state.clear()
        self._chart_line_overrides.clear()

        # Load default templates from interface config
        self.__default_templates.clear()
        for interface_type, interface_def in self.__interfaces_config.items():
            self.__default_templates[interface_type] = interface_def.defaults.copy()

        logger.log_info("Backend loaded %s interface template(s)", len(self.__default_templates))

        # Load saved connections from config
        self._load_connections_from_config()

        # Migration: If no connections exist, this is likely first run or old config
        # We don't auto-create connections anymore - user must explicitly create them
        if not self.__connections:
            logger.log_info("No saved connections found - user can create connections via UI")

        self.backend_setup_done = True

    @Slot("QString", "QJSValue", result="bool")
    def set_settings(self, interface: str, settings: QJSValue) -> bool:
        """Update default template settings for an interface type.

        This updates the default settings that will be used when creating new connections.
        To update settings for a specific connection, use update_connection_settings().

        Args:
            interface: Interface type (Serial, Telnet, MQTT, Test)
            settings: New default settings as QJSValue

        Returns:
            True if updated successfully, False otherwise
        """
        self.interface = interface
        self.settings = settings

        if interface not in self.__default_templates:
            self._notify_status("warning", f"Unknown interface type for settings: {interface}")
            return False

        py_settings = Converter.jsvalue_to_dict(settings)
        if not isinstance(py_settings, dict):
            self._notify_status("warning", f"Cannot convert settings for {interface}")
            return False

        # Update default template
        self.__default_templates[interface] = py_settings
        self._notify_status("info", f"Updated default template for {interface}")

        # Save updated templates to config
        self._save_templates_to_config()
        return True

    @Slot(result="bool")
    @Slot(str, result="bool")
    def settings_valid(self, connection_type: str = "") -> bool:
        """Check if settings for an interface type are valid.

        Note: This is a simplified check - actual validation happens when creating/updating connections.

        Args:
            connection_type: Interface type to check

        Returns:
            True if the interface type exists, False otherwise
        """
        selected_type = connection_type or self.__interface
        return bool(selected_type) and selected_type in self.__default_templates

    @Slot(str, result="QVariant")
    def get_settings(self, interface_type: str) -> Dict[str, Any]:
        """Return an isolated copy of an interface's default settings."""
        settings = self.__default_templates.get(interface_type)
        if settings is None:
            self._notify_status("warning", f"Unknown interface type: {interface_type}")
            return {}
        return deepcopy(settings)

    @Slot(QObject, QObject)
    def setup(self, ui_handle: QObject, backend_events: QObject) -> None:
        self._ui_handle = ui_handle
        self._backend_events = backend_events
        logger.log_info("Backend connected to QML events bridge")
        self._flush_pending_events()

    # Logging slots for QML use
    @Slot(str)
    def log_error(self, msg: str) -> None:
        Logger.get_instance().log_error(msg)

    @Slot(str)
    def log_warning(self, msg: str) -> None:
        Logger.get_instance().log_warning(msg)

    @Slot(str)
    def log_info(self, msg: str) -> None:
        Logger.get_instance().log_info(msg)

    @Slot(str)
    def log_debug(self, msg: str) -> None:
        Logger.get_instance().log_debug(msg)

    @Slot(str)
    def log_stack(self, stack_info: str) -> None:
        Logger.get_instance().log_qml_stack(stack_info)

    @Slot(str, result=bool)
    def remove_chart_line(self, unique_id: str) -> bool:
        """Remove a chart line from the backend.

        Args:
            unique_id: Unique identifier (format: "interface_dataId")

        Returns:
            True if removed successfully, False otherwise
        """
        # Remove from graph state
        if unique_id in self._graph_state:
            del self._graph_state[unique_id]
            logger.log_info(f"Removed chart line from state: {unique_id}")

        self._chart_line_overrides.pop(unique_id, None)

        return True

    @Slot(str, bool)
    def set_signal_ignored(self, unique_id: str, ignored: bool) -> None:
        """Enable/disable a signal source by unique_id.

        When ignored, incoming points are dropped and the line will not auto-reappear.
        """
        if ignored:
            self._ignored_signals.add(unique_id)
            # Drop any existing state/buffers so the UI can clean up.
            self.remove_chart_line(unique_id)
        else:
            self._ignored_signals.discard(unique_id)

    @Slot(str, str, str, result=bool)
    def update_chart_line(self, unique_id: str, display_name: str, color: str) -> bool:
        """Update properties of an existing chart line.

        Args:
            unique_id: Unique identifier (format: "interface_dataId")
            display_name: New display name
            color: New color (hex string)

        Returns:
            True if updated successfully, False otherwise
        """
        self._chart_line_overrides[unique_id] = {
            "display_name": display_name,
            "color": color,
        }
        if unique_id in self._graph_state:
            self._graph_state[unique_id]["display_name"] = display_name
            self._graph_state[unique_id]["color"] = color

        logger.log_info(f"Updated chart line: {unique_id} - Name: {display_name}, Color: {color}")
        return True

    # ------------------------------------------------------------------ #
    # Internal helpers
    # ------------------------------------------------------------------ #
    def _on_receiver_data(self, interface: str, payload: bytes) -> None:
        """Handle incoming data from a receiver.

        Parses the payload into a PlotDataPoint and routes it to the correct graph line.
        Uses ID-based routing where unique_id = "interface_dataId".
        """
        data_point = self._parse_data_point(interface, payload)
        if data_point is None:
            return

        self._received_total += 1
        # Create unique_id from interface and data ID
        unique_id = f"{interface}_{data_point.id}"

        # Ignore disabled signals
        if unique_id in self._ignored_signals:
            return

        # Get or create state for this unique_id
        state = self._graph_state.get(unique_id)
        if state is None:
            if len(self._graph_state) >= 256:
                self._signal_limit_dropped += 1
                return
            # New data source discovered - auto-create line
            conn_info = self.__connections.get(interface)
            interface_type = conn_info.interface_type if conn_info else interface

            # Default naming/colors
            color = self._color_from_id(data_point.id)
            display_name = f"{interface_type} #{data_point.id}"

            # Special case: Test interface provides stable, well-known signals
            if conn_info and conn_info.interface_type == "Test":
                for tpl in self._TEST_SIGNAL_TEMPLATES:
                    if int(tpl.get("dataId", -1)) == int(data_point.id):
                        display_name = str(tpl.get("displayName", display_name))
                        color = str(tpl.get("color", color))
                        break

            override = self._chart_line_overrides.get(unique_id)
            if override:
                display_name = override["display_name"]
                color = override["color"]

            state = {
                "id": data_point.id,
                "unique_id": unique_id,
                "interface": interface,
                "display_name": display_name,
                "color": color,
                "auto_index": 0,
                "first_timestamp": None,
                "first_rx_time": None,
                "announced": False
            }
            self._graph_state[unique_id] = state
            logger.log_info(f"Auto-created line: {unique_id} ({display_name})")

        # Announce graph to QML if not yet done
        if not state["announced"]:
            conn_info = self.__connections.get(interface)
            interface_type = conn_info.interface_type if conn_info else interface
            self._queue_event("newGraph", unique_id, state["display_name"], state["color"], interface_type)
            state["announced"] = True

        # ------------------------------------------------------------------
        # Time normalization
        # ------------------------------------------------------------------
        now = time.time()
        monotonic_now = time.monotonic()
        if self._capture_start is None:
            self._capture_start = monotonic_now
        # Pre-calculate time normalization even if X is present (needed for time-series views)
        t_value = None
        if data_point.timestamp is not None:
            origin = self._source_time_origins.setdefault(interface, data_point.timestamp)
            state["first_timestamp"] = origin
            t_value = float(data_point.timestamp - origin)
        else:
            if state["first_rx_time"] is None:
                state["first_rx_time"] = now
            t_value = float(monotonic_now - self._capture_start)


        # ------------------------------------------------------------------
        # Chart routing (2D + optional 3D)
        # ------------------------------------------------------------------
        # XY X-axis value:
        # - If an explicit X value is provided (XY mode), use it as-is.
        # - Else if a timestamp is provided (time mode), use normalized time.
        # - Else fall back to auto-increment.
        if getattr(data_point, "x", None) is not None:
            x_value = float(data_point.x)  # type: ignore[arg-type]
        elif t_value is not None:
            x_value = float(t_value)
        else:
            x_value = float(state["auto_index"])
            state["auto_index"] += 1

        # Time-series coordinate: prefer normalized timestamp even if X is present.
        time_value = float(t_value)

        # Retain original values before *any* display-only reduction/overflow.
        self._sample_store.append(unique_id, Sample(
            t=time_value, x=data_point.x, y=float(data_point.value), z=data_point.z_value,
            timestamp=data_point.timestamp, rx_time=now))

        # Points reach QML in frame batches on the display clock.
        self._buffer_point(
            unique_id,
            x_value,
            float(data_point.value),
            time_value,
            getattr(data_point, "x", None) is not None,
        )

        # 3D charts (XYZ): emit dedicated events when Z is present
        if getattr(data_point, "z_value", None) is not None:
            z_value = float(data_point.z_value)  # type: ignore[arg-type]
            self._buffer_point_3d(unique_id, x_value, float(data_point.value), z_value)

    def _parse_data_point(self, interface: str, payload: bytes) -> PlotDataPoint | None:
        """Parse without coupling wire validation to Qt; rate-limit error reporting."""
        try:
            return parse_payload(payload)
        except ProtocolError as exc:
            self._invalid_total += 1
            now = time.monotonic()
            if now - self._parse_warning_times.get(interface, -10.0) >= 1.0:
                self._parse_warning_times[interface] = now
                self._notify_status("warning", f"{interface}: {exc}")
            return None

    def _color_from_name(self, name: str) -> int:
        """Generate color from name hash (legacy)."""
        digest = hashlib.sha1(name.encode("utf-8")).hexdigest()
        return int(digest[:6], 16)

    def _color_from_id(self, data_id: int) -> int:
        """Generate color from data ID (0-255).

        Uses a predefined color palette for better visual distinction.
        """
        # Color palette (12 distinct colors in hex format)
        color_palette = [
            0xe74c3c, 0x3498db, 0x2ecc71, 0xf39c12,
            0x9b59b6, 0x1abc9c, 0xe67e22, 0x34495e,
            0xff6b6b, 0x4ecdc4, 0x45b7d1, 0x96ceb4
        ]
        # Use modulo to cycle through palette
        return color_palette[data_id % len(color_palette)]

    def _on_ui_setup_signal(self, settings: dict) -> None:
        self._queue_event("ui_setup", settings)

    def _forward_com_port_update(self, ports) -> None:
        self._queue_event("com_port_update", ports)

    def _queue_event(self, signal_name: str, *args) -> None:
        if self._emit_event(signal_name, *args):
            return
        events = self._pending_events.setdefault(signal_name, [])
        # Before QML is ready keep only the most recent batch for each signal.
        if signal_name.startswith("append_graph") and args:
            for index, previous in enumerate(events):
                if previous[0] == args[0]:
                    self._display_dropped += len(previous[1]) if isinstance(previous[1], list) else 1
                    events[index] = args
                    return
        if len(events) >= 256:
            events.pop(0)
            self._event_dropped += 1
        events.append(args)

    def _emit_event(self, signal_name: str, *args) -> bool:
        if self._backend_events is None:
            return False
        signal = getattr(self._backend_events, signal_name, None)
        if signal is None or not hasattr(signal, "emit"):
            return False
        signal.emit(*args)
        return True

    def _flush_pending_events(self) -> None:
        if self._backend_events is None:
            return
        for signal_name, events in list(self._pending_events.items()):
            for args in events:
                self._emit_event(signal_name, *args)
        self._pending_events.clear()

    def _notify_status(self, level: str, message: str) -> None:
        level = level.lower()
        if level == "error":
            logger.log_error(message)
        elif level == "warning":
            logger.log_warning(message)
        elif level == "debug":
            logger.log_debug(message)
        else:
            logger.log_info(message)

        self.status_message.emit(level, message)
        self._queue_event("status_message", level, message)

    # ------------------------------------------------------------------ #
    # Batch update methods for performance optimization
    # ------------------------------------------------------------------ #
    def _buffer_point(self, unique_id: str, x: float, y: float, t: float,
                      has_explicit_x: bool = True) -> None:
        """Never render from the producer; the frame timer is the only batch clock."""
        before = self._frames_2d.dropped
        self._frames_2d.append(unique_id, (x, y, t, has_explicit_x))
        self._display_dropped += self._frames_2d.dropped - before

    def _buffer_point_3d(self, unique_id: str, x: float, y: float, z: float) -> None:
        before = self._frames_3d.dropped
        self._frames_3d.append(unique_id, (x, y, z))
        self._display_dropped += self._frames_3d.dropped - before

    def _flush_point_buffer(self) -> None:
        if not self._display_paused:
            for key in list(self._point_buffer):
                self._flush_points_for_line(key)
            for key in list(self._point_buffer_3d):
                self._flush_points_for_line_3d(key)

    def _flush_points_for_line(self, unique_id: str) -> None:
        points = list(self._point_buffer.pop(unique_id, []))
        if not points:
            return
        batch, remaining = points[:self._batch_size], points[self._batch_size:]
        if remaining:
            self._point_buffer[unique_id] = deque(remaining, maxlen=self._max_pending_points)
        if self._downsample_enabled and all(not p[3] for p in batch):
            target = max(4, int(self._downsample_target_hz * self._batch_timer.interval() / 1000))
            reduced = peak_envelope(batch, target)
            self._display_reduced += len(batch) - len(reduced)
            batch = reduced
        self._queue_event("append_graph_points_batch", unique_id, [list(p) for p in batch])

    def _flush_points_for_line_3d(self, unique_id: str) -> None:
        points = list(self._point_buffer_3d.pop(unique_id, []))
        if not points:
            return
        batch, remaining = points[:self._batch_size], points[self._batch_size:]
        if remaining:
            self._point_buffer_3d[unique_id] = deque(remaining, maxlen=self._max_pending_points)
        self._queue_event("append_graph_points_batch_3d", unique_id, [list(p) for p in batch])

    @Slot(int)
    def set_batch_interval(self, interval_ms: int) -> None:
        self._batch_timer.setInterval(max(16, min(500, interval_ms)))

    @Slot(bool)
    def set_downsample_enabled(self, enabled: bool) -> None:
        """Enable or disable downsampling for high-frequency data.

        When enabled, incoming data rates above the target Hz will be reduced
        to prevent overwhelming the chart rendering.

        Args:
            enabled: True to enable downsampling, False to disable
        """
        self._downsample_enabled = enabled
        if not enabled:
            self._last_emit_time.clear()
        logger.log_info(f"Downsampling {'enabled' if enabled else 'disabled'}")

    @Slot(float)
    def set_downsample_target_hz(self, hz: float) -> None:
        if math.isfinite(hz):
            self._downsample_target_hz = max(10.0, min(100000.0, hz))

    def _should_emit_point(self, unique_id: str) -> bool:
        """Check if enough time has passed to emit a new point (rate limiting).

        Args:
            unique_id: Line identifier

        Returns:
            True if point should be emitted, False to skip
        """
        now = time.time()
        last_time = self._last_emit_time.get(unique_id, 0)
        interval = 1.0 / self._downsample_target_hz

        if now - last_time >= interval:
            self._last_emit_time[unique_id] = now
            return True
        return False

    # Setup when backend is ready
    def on_backend_setup_done(self, status: bool) -> None:
        if status:
            if not self.ui_setup_done and self.ui_config is not None:
                self.ui_setup.emit(self.ui_config)
            else:
                logger.log_info("UI already configured")
        else:
            logger.log_error("Cannot setup ui. Backend not configured")

    # Serial port polling callback
    def _update_com_ports(self) -> None:
        new_com_list = _get_serial_ports()
        if new_com_list != self.__com_list:
            logger.log_info("New Comports found {}".format(new_com_list))
            self.com_port_update.emit(new_com_list)
            self.__com_list = new_com_list

    @Slot(result="QVariant")
    def get_com_ports(self) -> List[str]:
        """Return the current list of serial ports for UI selection."""
        return _get_serial_ports()

    @Slot(str, result="QVariant")
    def get_interface_config(self, interface: str) -> Dict[str, Any]:
        """Get default template configuration for a specific interface type.

        Args:
            interface: Interface type (Serial, Telnet, MQTT, Test)

        Returns:
            Dictionary with default settings for this interface type
        """
        if interface not in self.__default_templates:
            logger.log_warning(f"No default template found for interface: {interface}")
            return {}

        default_config = self.__default_templates[interface].copy()
        logger.log_debug(f"Loaded default template for {interface}: {default_config}")
        return default_config

    @Slot(str, result="QVariant")
    def get_default_template(self, interface_type: str) -> Dict[str, Any]:
        """Get the default template for a specific interface type.

        This is used by the UI when creating new connections or editing default templates.

        Args:
            interface_type: Interface type (Serial, Telnet, MQTT, Test)

        Returns:
            Dictionary with default template settings
        """
        return self.get_interface_config(interface_type)

    @Slot(str, result=bool)
    def save_configuration_to_file(self, file_url: str) -> bool:
        """Export the complete current configuration to a user-selected file."""
        try:
            target = self._path_from_file_url(file_url)
            config = self._configuration_snapshot()
            self._write_json_atomic(target, config)
            self._notify_status("success", f"Configuration saved to {target.name}")
            logger.log_info("Configuration exported to %s", target)
            return True
        except (OSError, TypeError, ValueError, json.JSONDecodeError) as exc:
            logger.log_error("Failed to export configuration: %s", exc)
            self._notify_status("error", f"Could not save configuration: {exc}")
            return False

    @Slot(str, result=bool)
    def load_configuration_from_file(self, file_url: str) -> bool:
        """Validate first. Never replace/delete a receiver that failed to stop."""
        try:
            if self._export_worker is not None:
                raise ValueError("Finish the CSV export before changing configuration")
            source = local_path(file_url)
            if source.stat().st_size > MAX_CONFIGURATION_BYTES:
                raise ValueError("Configuration exceeds 4 MiB")
            with source.open(encoding="utf-8-sig") as stream:
                config = json.load(stream)
            validate_configuration(config)
            # Confirm all transport constructors accept their persisted values
            # before any running source or on-disk configuration is touched.
            probes = []
            try:
                for entry in config.get("saved_connections", []):
                    receiver = self.__receiver_registry.create_receiver(
                        {"type": entry["type"], "default": entry.get("settings", {})})
                    if receiver is None:
                        raise ValueError("Unsupported transport: " + entry["type"])
                    probes.append(receiver)
            finally:
                for receiver in probes:
                    receiver.deleteLater()
            if not self._connection_service.shutdown():
                raise ValueError("At least one connection could not stop; import cancelled")
            atomic_json_write(Path(self.__config_path), config)
            self._clear_runtime_state_for_configuration_reload()
            self.config(config)
            self._notify_status("success", f"Configuration loaded from {source.name}; connections remain stopped")
            return True
        except (OSError, TypeError, ValueError, OverflowError, RecursionError) as exc:
            self._notify_status("error", f"Configuration not applied: {exc}")
            return False

    @staticmethod
    def _path_from_file_url(file_url: str) -> Path:
        return local_path(file_url)

    def _configuration_snapshot(self) -> Dict[str, Any]:
        """Merge runtime state into an isolated copy of the loaded configuration."""
        snapshot = deepcopy(self._base_config)
        snapshot["interfaces"] = [
            {"type": name, "default": deepcopy(self.__default_templates.get(name, definition.defaults))}
            for name, definition in self.__interfaces_config.items()
        ]
        snapshot["saved_connections"] = [
            {"id": info.connection_id, "type": info.interface_type, "name": info.display_name,
             "settings": deepcopy(info.settings), "created_at": info.created_at}
            for info in self.__connections.values()
        ]
        snapshot["performance"] = {
            "frame_interval_ms": self._batch_timer.interval(),
            "display_points_per_signal": self._display_point_limit,
            "downsample_enabled": self._downsample_enabled,
            "downsample_target_hz": self._downsample_target_hz,
        }
        return snapshot

    @staticmethod
    def _validate_configuration(config: Any) -> None:
        validate_configuration(config)

    @staticmethod
    def _write_json_atomic(target: Path, config: Dict[str, Any]) -> None:
        atomic_json_write(target, config)

    def _clear_runtime_state_for_configuration_reload(self) -> None:
        removed_signal_ids = set(self._graph_state) | set(self._chart_line_overrides)
        for info in self.__connections.values():
            if info.receiver is not None:
                info.receiver.deleteLater()
        self.__connections.clear()
        self._connection_service._requested.clear()
        self.__connection_counter = 0
        self._graph_state.clear()
        self._last_emit_time.clear()
        self._chart_line_overrides.clear()
        self._ignored_signals.clear()
        self._pending_events.clear()
        self.clear_measurements()
        if removed_signal_ids:
            self._queue_event("signals_removed", sorted(removed_signal_ids))

    # ------------------------------------------------------------------ #
    # Multi-Connection Management API
    # ------------------------------------------------------------------ #
    @Slot(str, str, "QJSValue", result=str)
    def create_connection(self, interface_type: str, display_name: str, settings: QJSValue) -> str:
        if interface_type not in self.__interfaces_config:
            self._notify_status("error", f"Unknown interface type: {interface_type}")
            return ""
        try:
            merged = deepcopy(self.__default_templates.get(interface_type, {}))
            merged.update(self._settings_dict(settings))
        except (TypeError, ValueError) as exc:
            self._notify_status("error", str(exc))
            return ""
        name = display_name.strip() or self._generate_display_name(interface_type, merged)
        key = self._connection_service.create(interface_type, name, merged)
        if key:
            self._save_connections_to_config()
        return key

    @Slot(str, result=bool)
    def start_connection(self, connection_id: str) -> bool:
        return self._connection_service.start(connection_id)

    @Slot(str, result=bool)
    def stop_connection(self, connection_id: str) -> bool:
        return self._connection_service.stop(connection_id)

    @Slot(str, result=bool)
    def delete_connection(self, connection_id: str) -> bool:
        if connection_id not in self.__connections:
            return False
        if not self._connection_service.stop(connection_id):
            return False  # Never destroy a receiver whose worker still owns resources.
        info = self.__connections.pop(connection_id)
        if info.receiver is not None and hasattr(info.receiver, "deleteLater"):
            info.receiver.deleteLater()
        prefix = connection_id + "_"
        mappings = (self._graph_state, self._point_buffer,
                    self._point_buffer_3d, self._last_emit_time,
                    self._chart_line_overrides)
        removed = {key for state in mappings for key in state if key.startswith(prefix)}
        removed.update(key for key in self._ignored_signals if key.startswith(prefix))
        for state in mappings:
            for key in removed:
                state.pop(key, None)
        for key in removed:
            self._sample_store.remove(key)
        self._ignored_signals.difference_update(removed)
        self._source_time_origins.pop(connection_id, None)
        for event_name, events in list(self._pending_events.items()):
            self._pending_events[event_name] = [args for args in events
                if not (args and isinstance(args[0], str) and args[0] in removed)]
        if removed:
            self._queue_event("signals_removed", sorted(removed))
        self._emit_connections_changed()
        self._save_connections_to_config()
        return True

    @Slot(str, "QJSValue", result=bool)
    def update_connection_settings(self, connection_id: str, settings: QJSValue) -> bool:
        try:
            values = self._settings_dict(settings)
        except (TypeError, ValueError) as exc:
            self._notify_status("warning", str(exc))
            return False
        if not self._connection_service.update_settings(connection_id, values):
            return False
        self._save_connections_to_config()
        return True

    @Slot(str, str, result=bool)
    def rename_connection(self, connection_id: str, new_name: str) -> bool:
        if not self._connection_service.rename(connection_id, new_name):
            return False
        self._save_connections_to_config()
        return True

    @Slot(result="QVariant")
    def get_interface_types(self) -> List[Dict[str, Any]]:
        """Get list of available interface types for connection creation.

        Returns:
            List of interface type dictionaries with keys:
            - type: interface type name (Serial, MQTT, Telnet, Test)
            - defaults: default settings for this interface type
        """
        interface_types = []
        for interface_type, interface_config in self.__interfaces_config.items():
            interface_types.append({
                "type": interface_type,
                "defaults": interface_config.defaults
            })

        return interface_types

    @Slot(result="QVariant")
    def get_connections(self) -> List[Dict[str, Any]]:
        """Get list of all connections for UI display.

        Returns:
            List of connection dictionaries with keys:
            - id: connection_id
            - type: interface_type
            - name: display_name
            - status: current status (connected/disconnected/connecting)
            - settings: connection settings
        """
        connections_list = []
        for conn_id, conn_info in self.__connections.items():
            connections_list.append({
                "id": conn_id,
                "type": conn_info.interface_type,
                "name": conn_info.display_name,
                "status": conn_info.status,
                "settings": deepcopy(conn_info.settings),
                "created_at": conn_info.created_at
            })

        # Sort by creation time
        connections_list.sort(key=lambda x: x["created_at"])

        return connections_list

    @Slot(str, result="QVariant")
    def get_connection_details(self, connection_id: str) -> Dict[str, Any]:
        """Get detailed information about a specific connection.

        Args:
            connection_id: Unique ID of the connection

        Returns:
            Dictionary with connection details, or empty dict if not found
        """
        conn_info = self.__connections.get(connection_id)
        if conn_info is None:
            return {}

        return {
            "id": conn_info.connection_id,
            "type": conn_info.interface_type,
            "name": conn_info.display_name,
            "status": conn_info.status,
            "settings": deepcopy(conn_info.settings),
            "created_at": conn_info.created_at
        }

    def _emit_connections_changed(self) -> None:
        """Emit signal that connection list has changed."""
        connections_list = self.get_connections()
        self.connections_changed.emit(connections_list)

    def _emit_connection_status_changed(self, connection_id: str, status: str, details: Dict[str, Any]) -> None:
        """Emit signal that a connection's status has changed."""
        self.connection_status_changed.emit(connection_id, status, details)

    def _generate_display_name(self, interface_type: str, settings: Dict[str, Any]) -> str:
        """Generate a meaningful display name based on interface type and settings.

        Args:
            interface_type: Type of interface (Serial, Telnet, MQTT, Test)
            settings: Connection settings dictionary

        Returns:
            Generated display name
        """
        if interface_type == "Serial":
            port = settings.get("port", "")
            if port:
                return f"Serial - {port}"
            return f"Serial #{self.__connection_counter}"

        elif interface_type == "Telnet":
            host = settings.get("host", "")
            port = settings.get("port", "")
            if host and port:
                return f"Telnet - {host}:{port}"
            elif host:
                return f"Telnet - {host}"
            return f"Telnet #{self.__connection_counter}"

        elif interface_type == "MQTT":
            host = settings.get("host", "")
            if host:
                return f"MQTT - {host}"
            return f"MQTT #{self.__connection_counter}"

        elif interface_type == "Test":
            name = settings.get("name", "")
            if name:
                return f"Test - {name}"
            return f"Test #{self.__connection_counter}"

        else:
            return f"{interface_type} #{self.__connection_counter}"

    def _save_templates_to_config(self) -> bool:
        return self._persist_configuration()

    def _save_connections_to_config(self) -> bool:
        return self._persist_configuration()

    def _load_connections_from_config(self) -> None:
        """Restore the supplied configuration, never a second hidden file."""
        for entry in self._base_config.get("saved_connections", []):
            if entry.get("type") not in self.__interfaces_config:
                self._notify_status("warning", f"Unknown saved interface: {entry.get('type')}")
                continue
            self._connection_service.restore(entry)
        self._emit_connections_changed()

    @staticmethod
    def _settings_dict(value: Any) -> dict:
        if isinstance(value, QJSValue):
            value = value.toVariant()
        if value is None:
            return {}
        if not isinstance(value, dict):
            raise ValueError("Settings must be an object")
        return deepcopy(value)

    def _persist_configuration(self) -> bool:
        try:
            config = self._configuration_snapshot()
            validate_configuration(config)
            atomic_json_write(Path(self.__config_path), config)
            self._base_config = deepcopy(config)
            return True
        except (OSError, TypeError, ValueError) as exc:
            self._notify_status("error", f"Could not save configuration: {exc}")
            return False

    @Slot(bool)
    def set_display_paused(self, paused: bool) -> None:
        """Freeze rendering, not acquisition; bounded pending data resumes later."""
        self._display_paused = paused
        if not paused:
            self._flush_point_buffer()

    @Slot(int)
    def set_display_point_limit(self, limit: int) -> None:
        self._display_point_limit = max(500, min(50000, limit))

    @Slot(result="QVariant")
    def get_performance_settings(self) -> dict:
        return {"frame_interval_ms": self._batch_timer.interval(),
                "display_points_per_signal": self._display_point_limit,
                "downsample_enabled": self._downsample_enabled,
                "downsample_target_hz": self._downsample_target_hz}

    @Slot(result="QVariant")
    def get_diagnostics(self) -> dict:
        now = time.monotonic()
        elapsed = max(0.001, now - self._metrics_time)
        rate = (self._received_total - self._metrics_received) / elapsed
        self._metrics_time, self._metrics_received = now, self._received_total
        ingress_dropped = sum(getattr(info.receiver, "dropped_payloads", 0)
                              for info in self.__connections.values())
        return {"received": self._received_total, "invalid": self._invalid_total,
                "rate": rate, "signals": len(self._graph_state),
                "retained": self._sample_store.total_count, "evicted": self._sample_store.evicted,
                "displayDropped": self._display_dropped, "displayReduced": self._display_reduced,
                "ingressDropped": ingress_dropped, "eventDropped": self._event_dropped,
                "signalLimitDropped": self._signal_limit_dropped,
                "paused": self._display_paused, "exporting": self._export_worker is not None,
                "configPath": self.__config_path}

    @Slot(str, result="QVariant")
    def get_signal_statistics(self, unique_id: str) -> dict:
        return self._sample_store.statistics(unique_id)

    @Slot(str, str, result=bool)
    def export_samples(self, file_url: str, unique_id: str = "") -> bool:
        if self._export_worker is not None:
            self._notify_status("warning", "A CSV export is already running")
            return False
        try:
            path = local_path(file_url)
            rows = self._sample_store.snapshot(unique_id)
            if not rows:
                raise ValueError("No retained measurements to export")
            names = {key: value.get("display_name", key) for key, value in self._graph_state.items()}
            worker = CsvExportWorker(path, rows, names, self)
            self._export_worker = worker
            worker.completed.connect(self._export_completed)
            worker.failed.connect(self._export_failed)
            worker.finished.connect(self._export_cleanup)
            worker.start()
            return True
        except (OSError, ValueError) as exc:
            self._notify_status("error", str(exc))
            return False

    @Slot(str, int)
    def _export_completed(self, path: str, count: int) -> None:
        self._notify_status("success", f"CSV: {count} retained measurements saved to {path}")

    @Slot(str)
    def _export_failed(self, message: str) -> None:
        self._notify_status("error", f"CSV export failed: {message}")

    @Slot()
    def _export_cleanup(self) -> None:
        if self._export_worker is not None:
            self._export_worker.deleteLater()
        self._export_worker = None

    @Slot()
    def clear_measurements(self) -> None:
        self._sample_store.clear()
        self._point_buffer.clear()
        self._point_buffer_3d.clear()
        self._source_time_origins.clear()
        self._capture_start = None
        self._received_total = self._invalid_total = self._display_dropped = 0
        self._display_reduced = self._event_dropped = self._signal_limit_dropped = 0
        self._metrics_received = 0
        self._metrics_time = time.monotonic()

    @Slot(result=bool)
    def shutdown(self) -> bool:
        """Return False instead of destroying active workers or an in-flight export."""
        if self._export_worker is not None and self._export_worker.isRunning():
            self._notify_status("warning", "CSV export is still running; close again after it finishes")
            return False
        if not self._connection_service.shutdown():
            return False
        self._batch_timer.stop()
        self.__com_updater_timer.stop()
        return True

    @Slot("QJSValue", result=bool)
    def apply_performance_settings(self, settings: QJSValue) -> bool:
        try:
            values = {**self.get_performance_settings(), **self._settings_dict(settings)}
            candidate = self._configuration_snapshot()
            candidate["performance"] = values
            validate_configuration(candidate)
            # Persist before changing the active timer, so failure is unambiguous.
            atomic_json_write(Path(self.__config_path), candidate)
            self._base_config = candidate
            self.set_batch_interval(values["frame_interval_ms"])
            self.set_display_point_limit(values["display_points_per_signal"])
            self.set_downsample_enabled(values["downsample_enabled"])
            self.set_downsample_target_hz(values["downsample_target_hz"])
            self._notify_status("success", "Display settings saved")
            return True
        except (OSError, ValueError, TypeError, KeyError) as exc:
            self._notify_status("error", f"Settings not applied: {exc}")
            return False

    @Slot(result="QVariant")
    def get_workspace(self) -> dict:
        return deepcopy(self._base_config.get("workspace", {}))

    @Slot("QJSValue", result=bool)
    def save_workspace(self, workspace: QJSValue) -> bool:
        try:
            state = validate_workspace(self._settings_dict(workspace))
            candidate = self._configuration_snapshot()
            candidate["workspace"] = state
            validate_configuration(candidate)
            atomic_json_write(Path(self.__config_path), candidate)
            self._base_config = candidate
            return True
        except (OSError, ValueError, TypeError) as exc:
            self._notify_status("error", f"Layout not saved: {exc}")
            return False

    @Slot(str, result=str)
    def export_local_path(self, file_url: str) -> str:
        try:
            return str(local_path(file_url))
        except ValueError as exc:
            self._notify_status("error", str(exc))
            return ""
