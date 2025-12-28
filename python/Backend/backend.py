# This Python file uses the following encoding: utf-8
import hashlib
import json
import time
from dataclasses import dataclass, field
from functools import partial
from typing import Any, Dict, List, Optional, Tuple

from PySide6 import QtCharts
from PySide6.QtCore import QObject, Slot, Signal, QTimer, QJsonValue, Property, QRectF
from PySide6.QtQml import QJSValue
from serial.tools import list_ports

from Receiver.receiver import Receiver
from Receiver.registry import ReceiverRegistry, parse_interface_definitions
from Receiver.message import PlotDataPoint
from Common.converter import Converter
from Logger import logger
from Logger.logger import Logger


def _get_serial_ports() -> List[str]:
    ports = list_ports.comports()
    return [port.name for port in ports]


@dataclass
class _GraphBuffer:
    series: Optional[QtCharts.QLineSeries] = None
    pending_points: List[Tuple[float, float]] = field(default_factory=list)


@dataclass
class ConnectionInfo:
    """Information about a single connection instance."""
    connection_id: str  # Unique ID (e.g., "Serial_COM3_1234567890")
    interface_type: str  # Interface type (Serial, Telnet, MQTT, Test)
    display_name: str  # User-friendly name
    status: str  # "disconnected", "connecting", "connected"
    settings: Dict[str, Any] = field(default_factory=dict)
    receiver: Optional[Receiver] = None
    created_at: float = field(default_factory=time.time)


class Backend(QObject):
    """Single QObject-based backend used by QML."""

    __backend_instance: Optional["Backend"] = None

    _TEST_SIGNAL_TEMPLATES: List[Dict[str, Any]] = [
        {"dataId": 0, "displayName": "Sine Wave", "color": "#ff6b6b"},
        {"dataId": 1, "displayName": "Cosine Wave", "color": "#4ecdc4"},
        {"dataId": 2, "displayName": "Sine Wave (2x)", "color": "#ffe66d"},
    ]

    # Settings signals
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

    def __init__(self) -> None:
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
        self._pending_events: Dict[str, List[tuple]] = {}
        self._app_start_time: float = time.time()  # For timestamp normalization
        self._ignored_signals: set[str] = set()  # unique_id values to ignore (disabled signals)

        # Multi-connection management (primary system)
        self.__connections: Dict[str, ConnectionInfo] = {}  # connection_id -> ConnectionInfo
        self.__connection_counter: int = 0  # Counter for generating unique IDs
        self.__config_path: str = "config/config.json"

        # Chart helpers
        self.__graph_list: Dict[str, _GraphBuffer] = {}
        self.__plot_area = QRectF()
        self.__chart: Optional[QtCharts.QChart] = None
        self.__xAxis: Optional[QtCharts.QValueAxis] = None
        self.__yAxis: Optional[QtCharts.QValueAxis] = None
        self.__xPoint = 0.0
        self.__scroll_step = 5

        # Performance optimization: Batch updates
        self._point_buffer: Dict[str, List[Tuple[float, float, float]]] = {}
        self._point_buffer_3d: Dict[str, List[Tuple[float, float, float]]] = {}
        self._batch_timer = QTimer(self)
        self._batch_timer.timeout.connect(self._flush_point_buffer)
        self._batch_timer.start(50)  # Flush every 50ms (20 Hz batch rate)
        self._batch_size = 10  # Max points per batch before immediate flush
        self._batch_enabled = True  # Enable batching by default

        # Message registry (UI table) - throttle updates to the same batch timer
        self._message_state: Dict[str, Dict[str, Any]] = {}
        self._dirty_messages: set[str] = set()

        # Performance optimization: Downsampling
        self._downsample_enabled = False  # Disabled by default
        self._downsample_target_hz = 50.0  # Target display rate
        self._last_emit_time: Dict[str, float] = {}  # Track last emit time per line

        # Serial port polling
        self.__com_updater_timer = QTimer(self)
        self.__com_list: List[str] = []
        self.__com_updater_timer.timeout.connect(self._update_com_ports)
        self.__com_updater_timer.start(1000)

        # Auto-scroll timer for charts
        self.__scroll_timer = QTimer(self)
        self.__scroll_timer.timeout.connect(self._on_scroll_timer)
        self.__auto_scroll_enabled = False  # Disabled by default for better performance
        # Don't start timer by default - will be started when enabled

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

    @Property(QRectF)
    def plot_area(self) -> QRectF:
        return self.__plot_area

    @plot_area.setter
    def plot_area(self, area: QRectF) -> None:
        self.__plot_area = area

    @Property(QObject)
    def xAxis(self) -> QtCharts.QValueAxis:
        """Expose the X axis as QObject to keep the meta type valid."""
        return self.__xAxis if self.__xAxis else QtCharts.QValueAxis()

    @xAxis.setter
    def xAxis(self, new_x_axis: QObject) -> None:
        self.__xAxis = new_x_axis if isinstance(new_x_axis, QtCharts.QValueAxis) else None

    @Property(QObject)
    def yAxis(self) -> QtCharts.QValueAxis:
        """Expose the Y axis as QObject to keep the meta type valid."""
        return self.__yAxis if self.__yAxis else QtCharts.QValueAxis()

    @yAxis.setter
    def yAxis(self, new_y_axis: QObject) -> None:
        self.__yAxis = new_y_axis if isinstance(new_y_axis, QtCharts.QValueAxis) else None

    # ------------------------------------------------------------------ #
    # Public API used from QML/receivers
    # ------------------------------------------------------------------ #
    def connect_signals(self) -> None:
        """Kept for backward compatibility."""
        self.backend_setup_done_changed.connect(self.on_backend_setup_done)

    @Slot(str, result="bool")
    def connectTo(self, connection_type: str) -> bool:
        """Legacy method - now forwards to connection-based system.

        This method is deprecated and kept for backward compatibility.
        Use start_connection() with a specific connection_id instead.
        """
        # Find first connection of this type
        for conn_id, conn_info in self.__connections.items():
            if conn_info.interface_type == connection_type:
                return self.start_connection(conn_id)

        self._notify_status("error", f"No connection found for type: {connection_type}")
        return False

    def config(self, config: dict) -> None:
        if not config:
            logger.log_error("Backend configuration missing")
            return

        self.ui_config = config.get("qml", {})
        self.__interfaces_config = parse_interface_definitions(config.get("interfaces", []))
        self.__scroll_step = config.get("scroll_step", self.__scroll_step)
        self._graph_state.clear()

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

    @Slot(str, result="bool")
    def settings_valid(self, connection_type: str) -> bool:
        """Check if settings for an interface type are valid.

        Note: This is a simplified check - actual validation happens when creating/updating connections.

        Args:
            connection_type: Interface type to check

        Returns:
            True if the interface type exists, False otherwise
        """
        return connection_type in self.__default_templates

    @Slot(result="QVariant")
    def get_ui_config(self):
        try:
            return self.ui_config
        except AttributeError:
            return {}

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

    # Chart helpers used from QML
    @Slot(str, QObject, result=bool)
    def add_graph(self, name: str, graph: QtCharts.QLineSeries) -> bool:
        buffer = self.__graph_list.setdefault(name, _GraphBuffer())
        buffer.series = graph
        if buffer.pending_points:
            for x_val, y_val in buffer.pending_points:
                buffer.series.append(x_val, y_val)
            buffer.pending_points.clear()
        return True

    @Slot(QObject)
    def set_chart(self, chart: QtCharts.QChart) -> None:
        self.__chart = chart

    @Slot(QRectF)
    def set_plot_area(self, area: QRectF) -> None:
        self.plot_area = area

    @Slot(QObject, QObject)
    def set_axis(self, x_axis: QObject, y_axis: QObject) -> None:
        self.xAxis = x_axis
        self.yAxis = y_axis

    @Slot(str, QObject, result=bool)
    def append_graph_point(self, graph_name: str, point: Tuple) -> bool:
        if not point:
            return False
        buffer = self.__graph_list.get(graph_name)
        if buffer is None or buffer.series is None:
            return False
        try:
            x_val, y_val = point
        except (ValueError, TypeError):
            return False
        buffer.series.append(x_val, y_val)
        return True

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

        # Remove from graph list (series buffer)
        if unique_id in self.__graph_list:
            del self.__graph_list[unique_id]
            logger.log_info(f"Removed chart line series: {unique_id}")

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

    @Slot(result="QVariant")
    def get_ignored_signals(self) -> List[str]:
        """Return ignored signal unique_ids."""
        return sorted(self._ignored_signals)

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
        if unique_id not in self._graph_state:
            logger.log_warning(f"Cannot update - chart line not found: {unique_id}")
            return False

        # Update state
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

        # Create unique_id from interface and data ID
        unique_id = f"{interface}_{data_point.id}"

        # Ignore disabled signals
        if unique_id in self._ignored_signals:
            return

        # Get or create state for this unique_id
        state = self._graph_state.get(unique_id)
        if state is None:
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
        # Message registry (for UI inspection)
        # ------------------------------------------------------------------
        now = time.time()
        conn_info = self.__connections.get(interface)
        interface_type = conn_info.interface_type if conn_info else interface

        prev = self._message_state.get(unique_id)
        prev_rx = prev.get("rxTime") if prev else None
        cycle_time = (now - float(prev_rx)) if prev_rx is not None else None
        rx_count = (int(prev.get("rxCount", 0)) + 1) if prev else 1

        # Pre-calculate time normalization even if X is present (needed for time-series views)
        t_value = None
        if data_point.timestamp is not None:
            if state["first_timestamp"] is None:
                state["first_timestamp"] = data_point.timestamp
            t_value = float(data_point.timestamp - state["first_timestamp"])
        else:
            if state["first_rx_time"] is None:
                state["first_rx_time"] = now
            t_value = float(now - state["first_rx_time"])

        self._message_state[unique_id] = {
            "uniqueId": unique_id,
            "displayName": state["display_name"],
            "interface": interface,
            "interfaceType": interface_type,
            "dataId": int(data_point.id),
            "x": float(data_point.x) if getattr(data_point, "x", None) is not None else None,
            "y": float(data_point.value),
            "z": float(data_point.z_value) if getattr(data_point, "z_value", None) is not None else None,
            "timestamp": float(data_point.timestamp) if data_point.timestamp is not None else None,
            "t": t_value,
            "rxTime": float(now),
            "cycleTime": float(cycle_time) if cycle_time is not None else None,
            "rxCount": rx_count,
        }
        self._dirty_messages.add(unique_id)

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

        # Apply downsampling if enabled
        if self._downsample_enabled and not self._should_emit_point(unique_id):
            return

        # Send point to QML - use batching for better performance
        if self._batch_enabled:
            self._buffer_point(unique_id, x_value, float(data_point.value), time_value)
        else:
            # Legacy: direct send (slower)
            point = {
                "x": x_value,
                "y": float(data_point.value),
                "t": time_value,
                "timestamp": float(data_point.timestamp) if data_point.timestamp is not None else None,
                "z": float(data_point.z_value) if getattr(data_point, "z_value", None) is not None else None,
            }
            self._queue_event("append_graph_point", unique_id, point)

        # 3D charts (XYZ): emit dedicated events when Z is present
        if getattr(data_point, "z_value", None) is not None:
            z_value = float(data_point.z_value)  # type: ignore[arg-type]
            if self._batch_enabled:
                self._buffer_point_3d(unique_id, x_value, float(data_point.value), z_value)
            else:
                self._queue_event(
                    "append_graph_point_3d",
                    unique_id,
                    {"x": x_value, "y": float(data_point.value), "z": z_value},
                )

    @Slot(result="QVariant")
    def get_test_signal_templates(self) -> List[Dict[str, Any]]:
        """Return the well-known Test interface signal templates (2D).

        Each item contains:
          - dataId: int
          - displayName: str
          - color: str
        """
        return [tpl.copy() for tpl in self._TEST_SIGNAL_TEMPLATES]

    def _parse_data_point(self, interface: str, payload: bytes) -> PlotDataPoint | None:
        """Parse received payload into a PlotDataPoint.

        Expected formats:
        1. JSON (time): {"id": 0-255, "value": float, "timestamp": float (optional), "z": float (optional)}
        2. JSON (XY): {"id": 0-255, "x": float, "y": float} (or "value" instead of "y")
        3. JSON: {"id": 0-255, "value": float, "z": float (optional)}
        4. Plain number: float (fallback: id=0, auto-timestamp)

        Args:
            interface: Name of the interface (for logging)
            payload: Raw bytes received

        Returns:
            PlotDataPoint or None if parsing failed
        """
        if not payload:
            return None

        try:
            text = payload.decode("utf-8").strip()
        except UnicodeDecodeError:
            self._notify_status("warning", f"{interface}: received non-text payload")
            return None

        if not text:
            return None
        if text.startswith("#"):
            # Allow embedded examples to print comment/header lines.
            return None

        # Try to parse as JSON first
        try:
            decoded = json.loads(text)
        except json.JSONDecodeError:
            # Fallback: Try as plain number
            try:
                value = float(text)
                # Fallback: id=0, no timestamp (will use auto-increment)
                return PlotDataPoint(id=0, value=value, timestamp=None)
            except ValueError:
                self._notify_status("warning", f"{interface}: cannot parse payload '{text[:40]}...'")
                return None

        # Handle optional MQTT wrapper: {"topic": "...", "payload_type": "...", "payload": ...}
        if isinstance(decoded, dict) and "payload" in decoded and "payload_type" in decoded and "topic" in decoded:
            payload_type = decoded.get("payload_type")
            inner = decoded.get("payload")
            if payload_type == "json" and isinstance(inner, dict):
                decoded = inner
            elif payload_type == "text" and isinstance(inner, str):
                inner_text = inner.strip()
                if inner_text.startswith("#") or not inner_text:
                    return None
                try:
                    decoded = json.loads(inner_text)
                except json.JSONDecodeError:
                    try:
                        value = float(inner_text)
                        return PlotDataPoint(id=0, value=value, timestamp=None)
                    except ValueError:
                        return None

        # Handle JSON object
        if isinstance(decoded, dict):
            # Extract required fields
            data_id = decoded.get("id")
            value = decoded.get("value")
            if value is None:
                value = decoded.get("y")
            x_value = decoded.get("x")
            timestamp = decoded.get("timestamp")
            z_value = decoded.get("z")

            # Validate ID
            if data_id is None:
                self._notify_status("warning", f"{interface}: missing 'id' field in JSON")
                return None
            if not isinstance(data_id, int) or not 0 <= data_id <= 255:
                self._notify_status("warning", f"{interface}: 'id' must be integer 0-255, got {data_id}")
                return None

            # Validate value
            if value is None:
                self._notify_status("warning", f"{interface}: missing 'value'/'y' field in JSON")
                return None
            if not isinstance(value, (int, float)):
                self._notify_status("warning", f"{interface}: 'value' must be numeric, got {type(value)}")
                return None

            # Validate X (optional)
            if x_value is not None and not isinstance(x_value, (int, float)):
                self._notify_status("warning", f"{interface}: 'x' must be numeric or omitted, got {type(x_value)}")
                return None

            # Validate timestamp (optional)
            if timestamp is not None and not isinstance(timestamp, (int, float)):
                self._notify_status("warning", f"{interface}: 'timestamp' must be numeric or omitted, got {type(timestamp)}")
                return None

            # Validate z_value (optional)
            if z_value is not None and not isinstance(z_value, (int, float)):
                self._notify_status("warning", f"{interface}: 'z' must be numeric or omitted, got {type(z_value)}")
                return None

            try:
                return PlotDataPoint(
                    id=data_id,
                    value=float(value),
                    x=float(x_value) if x_value is not None else None,
                    timestamp=float(timestamp) if timestamp is not None else None,
                    z_value=float(z_value) if z_value is not None else None
                )
            except ValueError as e:
                self._notify_status("warning", f"{interface}: invalid data point: {e}")
                return None

        # Handle plain number in JSON
        if isinstance(decoded, (int, float)):
            return PlotDataPoint(id=0, value=float(decoded), timestamp=None)

        self._notify_status("warning", f"{interface}: unexpected JSON format")
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

    def _on_scroll_timer(self) -> None:
        if not self.__auto_scroll_enabled or self._backend_events is None:
            return
        self.__xPoint += self.__scroll_step
        self._queue_event("scrollRight", self.__scroll_step)

    def _queue_event(self, signal_name: str, *args) -> None:
        if self._emit_event(signal_name, *args):
            return
        self._pending_events.setdefault(signal_name, []).append(args)

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

        self._queue_event("status_message", level, message)

    # ------------------------------------------------------------------ #
    # Batch update methods for performance optimization
    # ------------------------------------------------------------------ #
    def _buffer_point(self, unique_id: str, x: float, y: float, t: float) -> None:
        """Buffer a point for batch sending to QML.

        Points are collected and sent in batches to reduce QML/JavaScript overhead.
        If buffer reaches batch_size, it's flushed immediately.
        Otherwise, the batch timer will flush it periodically.
        """
        if unique_id not in self._point_buffer:
            self._point_buffer[unique_id] = []

        # Store as [x, y, t] so different chart types can pick the right coordinate.
        self._point_buffer[unique_id].append((x, y, t))

        # Flush immediately if buffer is full
        if len(self._point_buffer[unique_id]) >= self._batch_size:
            self._flush_points_for_line(unique_id)

    def _buffer_point_3d(self, unique_id: str, x: float, y: float, z: float) -> None:
        """Buffer a 3D point for batch sending to QML."""
        if unique_id not in self._point_buffer_3d:
            self._point_buffer_3d[unique_id] = []

        self._point_buffer_3d[unique_id].append((x, y, z))

        if len(self._point_buffer_3d[unique_id]) >= self._batch_size:
            self._flush_points_for_line_3d(unique_id)

    def _flush_point_buffer(self) -> None:
        """Timer callback to flush all buffered points + message state."""
        for unique_id in list(self._point_buffer.keys()):
            self._flush_points_for_line(unique_id)
        for unique_id in list(self._point_buffer_3d.keys()):
            self._flush_points_for_line_3d(unique_id)

        self._flush_message_updates()

    def _flush_points_for_line(self, unique_id: str) -> None:
        """Flush buffered points for a single line to QML."""
        if unique_id not in self._point_buffer:
            return

        points = self._point_buffer[unique_id]
        if not points:
            return

        # Send batch to QML
        self._queue_event("append_graph_points_batch", unique_id, points)

        # Clear buffer
        self._point_buffer[unique_id] = []

    def _flush_points_for_line_3d(self, unique_id: str) -> None:
        if unique_id not in self._point_buffer_3d:
            return

        points = self._point_buffer_3d[unique_id]
        if not points:
            return

        self._queue_event("append_graph_points_batch_3d", unique_id, points)
        self._point_buffer_3d[unique_id] = []

    def _flush_message_updates(self) -> None:
        if not self._dirty_messages:
            return

        # Emit latest state per message (throttled to batch timer)
        for unique_id in list(self._dirty_messages):
            msg = self._message_state.get(unique_id)
            if not msg:
                continue
            self._queue_event("message_received", msg)

        self._dirty_messages.clear()

    @Slot(bool)
    def set_batch_enabled(self, enabled: bool) -> None:
        """Enable or disable batch updates.

        Args:
            enabled: True to enable batching (better performance), False for immediate updates
        """
        self._batch_enabled = enabled
        logger.log_info(f"Batch updates {'enabled' if enabled else 'disabled'}")

        # If disabling, flush remaining buffers
        if not enabled:
            self._flush_point_buffer()

    @Slot(int)
    def set_batch_size(self, size: int) -> None:
        """Set maximum batch size before immediate flush.

        Args:
            size: Number of points to buffer before flushing (default: 10)
        """
        if size < 1:
            size = 1
        self._batch_size = size
        logger.log_info(f"Batch size set to {size}")

    @Slot(int)
    def set_batch_interval(self, interval_ms: int) -> None:
        """Set batch flush interval in milliseconds.

        Args:
            interval_ms: Milliseconds between batch flushes (default: 50ms = 20 Hz)
        """
        if interval_ms < 10:
            interval_ms = 10
        self._batch_timer.setInterval(interval_ms)
        logger.log_info(f"Batch interval set to {interval_ms}ms")

    @Slot(bool)
    def set_auto_scroll_enabled(self, enabled: bool) -> None:
        """Enable or disable automatic chart scrolling.

        Args:
            enabled: True to enable auto-scroll, False to disable
        """
        self.__auto_scroll_enabled = enabled
        if enabled:
            if not self.__scroll_timer.isActive():
                self.__scroll_timer.start(1000)
            logger.log_info("Auto-scroll enabled")
        else:
            self.__scroll_timer.stop()
            logger.log_info("Auto-scroll disabled")

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
        """Set target display rate for downsampling.

        Args:
            hz: Target frequency in Hz (default: 50 Hz)
        """
        if hz < 1:
            hz = 1
        if hz > 1000:
            hz = 1000
        self._downsample_target_hz = hz
        logger.log_info(f"Downsample target set to {hz} Hz")

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

    @Slot(result="QVariant")
    def get_available_interface_types(self) -> List[str]:
        """Get list of all available interface types.

        Returns:
            List of interface type names (e.g., ["Serial", "Telnet", "MQTT", "Test"])
        """
        return list(self.__default_templates.keys())

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

    @Slot()
    def save_settings_to_config(self) -> bool:
        """Save current default templates to config.json.

        This saves the default templates that will be used when creating new connections.
        Individual connection settings are saved separately via _save_connections_to_config().

        Returns:
            True if saved successfully, False otherwise
        """
        return self._save_templates_to_config()

    @Slot(str, "QVariant", result="bool")
    def save_preset(self, file_url: str, preset: Dict[str, Any]) -> bool:
        """Save settings preset to a JSON file."""
        try:
            import json
            from urllib.parse import urlparse

            # Convert file URL to path
            parsed = urlparse(file_url)
            file_path = parsed.path
            if file_path.startswith('/') and len(file_path) > 2 and file_path[2] == ':':
                file_path = file_path[1:]

            with open(file_path, 'w') as f:
                json.dump(preset, f, indent=2)

            logger.log_info(f"Preset saved to {file_path}")
            return True

        except Exception as e:
            logger.log_error(f"Failed to save preset: {e}")
            return False

    @Slot(str, result="QVariant")
    def load_preset(self, file_url: str) -> Dict[str, Any]:
        """Load settings preset from a JSON file."""
        try:
            import json
            from urllib.parse import urlparse

            # Convert file URL to path
            parsed = urlparse(file_url)
            file_path = parsed.path
            if file_path.startswith('/') and len(file_path) > 2 and file_path[2] == ':':
                file_path = file_path[1:]

            with open(file_path, 'r') as f:
                preset = json.load(f)

            logger.log_info(f"Preset loaded from {file_path}")
            return preset

        except Exception as e:
            logger.log_error(f"Failed to load preset: {e}")
            return {}

    # ------------------------------------------------------------------ #
    # Multi-Connection Management API
    # ------------------------------------------------------------------ #
    @Slot(str, str, "QJSValue", result=str)
    def create_connection(self, interface_type: str, display_name: str, settings: QJSValue) -> str:
        """Create a new connection instance.

        Args:
            interface_type: Type of interface (Serial, Telnet, MQTT, Test)
            display_name: User-friendly name for the connection
            settings: Initial settings as QJSValue

        Returns:
            connection_id: Unique ID for the created connection, or empty string on error
        """
        # Validate interface type
        if interface_type not in self.__interfaces_config:
            self._notify_status("error", f"Unknown interface type: {interface_type}")
            return ""

        # Generate unique connection ID
        self.__connection_counter += 1
        timestamp = int(time.time() * 1000)
        connection_id = f"{interface_type}_{timestamp}_{self.__connection_counter}"

        # Convert settings first to generate better display name
        py_settings = Converter.jsvalue_to_dict(settings) if settings.isObject() else {}

        # Auto-generate display name if empty
        if not display_name or display_name.strip() == "":
            display_name = self._generate_display_name(interface_type, py_settings)

        # Create receiver instance
        interface_config = self.__interfaces_config[interface_type]
        receiver = self.__receiver_registry.create_receiver({
            "type": interface_config.type,
            "default": interface_config.defaults
        })
        if receiver is None:
            self._notify_status("error", f"Failed to create receiver for {interface_type}")
            return ""

        # Configure receiver with settings or defaults
        if py_settings:
            receiver.config(py_settings)
        else:
            # Use default settings from config
            default_settings = interface_config.defaults
            if default_settings:
                receiver.config(default_settings)

        # Connect receiver signals
        receiver.new_data.connect(partial(self._on_receiver_data, connection_id))

        # Create connection info
        conn_info = ConnectionInfo(
            connection_id=connection_id,
            interface_type=interface_type,
            display_name=display_name,
            status="disconnected",
            settings=py_settings if py_settings else interface_config.defaults,
            receiver=receiver
        )

        self.__connections[connection_id] = conn_info
        logger.log_info(f"Created connection: {connection_id} ({display_name})")

        # Emit signal and save
        self._emit_connections_changed()
        self._save_connections_to_config()

        return connection_id

    @Slot(str, result=bool)
    def start_connection(self, connection_id: str) -> bool:
        """Start a specific connection.

        Args:
            connection_id: Unique ID of the connection to start

        Returns:
            True if started successfully, False otherwise
        """
        conn_info = self.__connections.get(connection_id)
        if conn_info is None:
            self._notify_status("error", f"Connection not found: {connection_id}")
            return False

        if conn_info.status == "connected":
            self._notify_status("warning", f"Connection already active: {connection_id}")
            return True

        # Update status to connecting
        conn_info.status = "connecting"
        self._emit_connection_status_changed(connection_id, "connecting", {})

        try:
            conn_info.receiver.start()
            conn_info.status = "connected"
            self._notify_status("info", f"Connection started: {conn_info.display_name}")
            self._emit_connection_status_changed(connection_id, "connected", {})
            self._emit_connections_changed()
            return True

        except ValueError as exc:
            conn_info.status = "disconnected"
            error_msg = f"Invalid settings for {conn_info.display_name}: {exc}"
            self._notify_status("warning", error_msg)
            self._emit_connection_status_changed(connection_id, "disconnected", {"error": str(exc)})
            self._emit_connections_changed()
            return False

        except ConnectionError as exc:
            conn_info.status = "disconnected"
            error_msg = f"Failed to connect {conn_info.display_name}: {exc}"
            self._notify_status("error", error_msg)
            self._emit_connection_status_changed(connection_id, "disconnected", {"error": str(exc)})
            self._emit_connections_changed()
            return False

    @Slot(str, result=bool)
    def stop_connection(self, connection_id: str) -> bool:
        """Stop a specific connection.

        Args:
            connection_id: Unique ID of the connection to stop

        Returns:
            True if stopped successfully, False otherwise
        """
        conn_info = self.__connections.get(connection_id)
        if conn_info is None:
            self._notify_status("error", f"Connection not found: {connection_id}")
            return False

        if conn_info.status == "disconnected":
            self._notify_status("warning", f"Connection already stopped: {connection_id}")
            return True

        try:
            conn_info.receiver.stop()
            conn_info.status = "disconnected"
            self._notify_status("info", f"Connection stopped: {conn_info.display_name}")
            self._emit_connection_status_changed(connection_id, "disconnected", {})
            self._emit_connections_changed()
            return True

        except Exception as exc:
            error_msg = f"Error stopping {conn_info.display_name}: {exc}"
            self._notify_status("error", error_msg)
            return False

    @Slot(str, result=bool)
    def delete_connection(self, connection_id: str) -> bool:
        """Delete a connection (only if disconnected).

        Args:
            connection_id: Unique ID of the connection to delete

        Returns:
            True if deleted successfully, False otherwise
        """
        conn_info = self.__connections.get(connection_id)
        if conn_info is None:
            self._notify_status("error", f"Connection not found: {connection_id}")
            return False

        if conn_info.status != "disconnected":
            self._notify_status("error", f"Cannot delete active connection: {conn_info.display_name}")
            return False

        # Clean up discovered signal state for this connection
        prefix = f"{connection_id}_"
        for unique_id in list(self._graph_state.keys()):
            if unique_id.startswith(prefix):
                self._graph_state.pop(unique_id, None)
                self.__graph_list.pop(unique_id, None)
                self._point_buffer.pop(unique_id, None)
                self._last_emit_time.pop(unique_id, None)

        # Remove connection
        del self.__connections[connection_id]
        logger.log_info(f"Deleted connection: {connection_id} ({conn_info.display_name})")

        # Emit signal and save
        self._emit_connections_changed()
        self._save_connections_to_config()

        return True

    @Slot(str, "QJSValue", result=bool)
    def update_connection_settings(self, connection_id: str, settings: QJSValue) -> bool:
        """Update settings for a specific connection.

        Args:
            connection_id: Unique ID of the connection
            settings: New settings as QJSValue

        Returns:
            True if updated successfully, False otherwise
        """
        conn_info = self.__connections.get(connection_id)
        if conn_info is None:
            self._notify_status("error", f"Connection not found: {connection_id}")
            return False

        py_settings = Converter.jsvalue_to_dict(settings)
        if not isinstance(py_settings, dict):
            self._notify_status("warning", f"Invalid settings format for {connection_id}")
            return False

        # Update settings
        conn_info.settings = py_settings
        conn_info.receiver.config(py_settings)

        logger.log_info(f"Updated settings for connection: {connection_id}")
        self._notify_status("info", f"Settings updated for {conn_info.display_name}")

        # Save to config
        self._save_connections_to_config()

        return True

    @Slot(str, str, result=bool)
    def rename_connection(self, connection_id: str, new_name: str) -> bool:
        """Rename a connection.

        Args:
            connection_id: Unique ID of the connection
            new_name: New display name

        Returns:
            True if renamed successfully, False otherwise
        """
        conn_info = self.__connections.get(connection_id)
        if conn_info is None:
            self._notify_status("error", f"Connection not found: {connection_id}")
            return False

        if not new_name or new_name.strip() == "":
            self._notify_status("warning", "Connection name cannot be empty")
            return False

        old_name = conn_info.display_name
        conn_info.display_name = new_name.strip()
        logger.log_info(f"Renamed connection {connection_id}: '{old_name}' -> '{new_name}'")

        self._emit_connections_changed()
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
                "settings": conn_info.settings,
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
            "settings": conn_info.settings,
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
        """Save default templates to config.json.

        Returns:
            True if saved successfully, False otherwise
        """
        try:
            # Read current config
            with open(self.__config_path, 'r') as f:
                config = json.load(f)

            # Update interface defaults with current templates
            for iface_conf in config.get("interfaces", []):
                interface_type = iface_conf.get("type")
                if interface_type in self.__default_templates:
                    iface_conf["default"] = self.__default_templates[interface_type]
                    logger.log_debug(f"Updated default template for {interface_type}")

            # Write back to file
            with open(self.__config_path, 'w') as f:
                json.dump(config, f, indent=2)

            logger.log_info("Default templates saved to config.json")
            return True

        except Exception as e:
            logger.log_error(f"Failed to save templates to config: {e}")
            return False

    def _save_connections_to_config(self) -> bool:
        """Save all connections to config.json for persistence.

        Returns:
            True if saved successfully, False otherwise
        """
        try:
            # Read current config
            with open(self.__config_path, 'r') as f:
                config = json.load(f)

            # Serialize connections (only save disconnected ones to avoid auto-connecting on startup)
            saved_connections = []
            for conn_id, conn_info in self.__connections.items():
                saved_connections.append({
                    "id": conn_id,
                    "type": conn_info.interface_type,
                    "name": conn_info.display_name,
                    "settings": conn_info.settings,
                    "created_at": conn_info.created_at
                })

            # Update config
            config["saved_connections"] = saved_connections

            # Write back to file
            with open(self.__config_path, 'w') as f:
                json.dump(config, f, indent=2)

            logger.log_debug(f"Saved {len(saved_connections)} connections to config")
            return True

        except Exception as e:
            logger.log_error(f"Failed to save connections to config: {e}")
            return False

    def _load_connections_from_config(self) -> None:
        """Load saved connections from config.json on startup."""
        try:
            with open(self.__config_path, 'r') as f:
                config = json.load(f)

            saved_connections = config.get("saved_connections", [])
            if not saved_connections:
                logger.log_info("No saved connections found in config")
                return

            logger.log_info(f"Loading {len(saved_connections)} saved connections...")

            for conn_data in saved_connections:
                try:
                    # Extract connection data
                    conn_id = conn_data.get("id")
                    interface_type = conn_data.get("type")
                    display_name = conn_data.get("name")
                    settings = conn_data.get("settings", {})
                    created_at = conn_data.get("created_at", time.time())

                    # Validate
                    if not conn_id or not interface_type or not display_name:
                        logger.log_warning(f"Skipping invalid connection entry: {conn_data}")
                        continue

                    if interface_type not in self.__interfaces_config:
                        logger.log_warning(f"Skipping connection with unknown interface: {interface_type}")
                        continue

                    # Create receiver
                    interface_config = self.__interfaces_config[interface_type]
                    receiver = self.__receiver_registry.create_receiver({
                        "type": interface_config.type,
                        "default": interface_config.defaults
                    })
                    if receiver is None:
                        logger.log_warning(f"Failed to create receiver for saved connection: {conn_id}")
                        continue

                    # Configure receiver
                    if settings:
                        receiver.config(settings)
                    else:
                        default_settings = interface_config.defaults
                        if default_settings:
                            receiver.config(default_settings)

                    # Connect receiver signals
                    receiver.new_data.connect(partial(self._on_receiver_data, conn_id))

                    # Create connection info
                    conn_info = ConnectionInfo(
                        connection_id=conn_id,
                        interface_type=interface_type,
                        display_name=display_name,
                        status="disconnected",
                        settings=settings,
                        receiver=receiver,
                        created_at=created_at
                    )

                    self.__connections[conn_id] = conn_info
                    logger.log_info(f"Restored connection: {conn_id} ({display_name})")

                    # Update connection counter to avoid ID collisions
                    if "_" in conn_id:
                        try:
                            parts = conn_id.split("_")
                            if len(parts) >= 3:
                                counter = int(parts[-1])
                                self.__connection_counter = max(self.__connection_counter, counter)
                        except (ValueError, IndexError):
                            pass

                except Exception as e:
                    logger.log_error(f"Error loading connection {conn_data.get('id', 'unknown')}: {e}")
                    continue

            logger.log_info(f"Successfully loaded {len(self.__connections)} connections from config")

            # Emit signal to update UI
            self._emit_connections_changed()

        except FileNotFoundError:
            logger.log_info(f"Config file not found: {self.__config_path}")
        except Exception as e:
            logger.log_error(f"Failed to load connections from config: {e}")
