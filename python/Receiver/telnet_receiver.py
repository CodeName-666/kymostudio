"""Telnet client/server receivers with automatic reconnect handling."""

from __future__ import annotations

import socket
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from Logger import logger

from .receiver import Receiver
from .receiver_thread import ReceiverThread
from .binary_protocol import ProtocolStreamDecoder


class TelnetClientThread(ReceiverThread):
    def __init__(self, host: str, port: int, reconnect_delay: float = 2.0) -> None:
        super().__init__()
        self._host = host
        self._port = port
        self._socket: Optional[socket.socket] = None
        self._reconnect_delay = max(1.0, reconnect_delay)
        self._read_size = 4096
        self._protocol_decoder = ProtocolStreamDecoder()

    def run(self) -> None:
        logger.log_info(
            "Telnet client thread started for %s:%s", self._host, self._port
        )
        while not self.stopped():
            if self._socket is None:
                if not self._connect():
                    self.interruptible_wait(self._reconnect_delay)
                    continue

            try:
                chunk = self._socket.recv(self._read_size)
            except socket.timeout:
                continue
            except (OSError, AttributeError) as exc:
                logger.log_error(f"Telnet client recv failed: {exc}")
                self._close_socket()
                self.interruptible_wait(self._reconnect_delay)
                continue

            if chunk:
                self._emit_messages(chunk)
            else:
                logger.log_info("Telnet client remote closed connection")
                self._close_socket()

        self._close_socket()
        logger.log_info("Telnet client thread stopped")

    def send_response(self, response: bytes) -> None:
        if not self._socket:
            logger.log_warning("Telnet client send requested without connection")
            return
        try:
            self._socket.sendall(response)
        except (OSError, AttributeError) as exc:
            logger.log_error(f"Telnet client send failed: {exc}")
            self._close_socket()

    def stop(self) -> None:
        super().stop()
        self._close_socket()

    def _connect(self) -> bool:
        try:
            sock = socket.create_connection((self._host, self._port), timeout=1.0)
        except (OSError, AttributeError) as exc:
            logger.log_warning(f"Telnet client connect failed: {exc}")
            return False

        sock.settimeout(1.0)
        if self.stopped():
            sock.close()
            return False
        self._socket = sock
        self.connection_state.emit(True)
        logger.log_info("Telnet client connected to %s:%s", self._host, self._port)
        return True

    def _close_socket(self) -> None:
        if self._socket:
            try:
                self._socket.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            try:
                self._socket.close()
            except OSError:
                pass
            self._socket = None
            self.connection_state.emit(False)
        self._protocol_decoder.reset()

    def _emit_messages(self, chunk: bytes) -> None:
        for message in self._protocol_decoder.feed(chunk):
            self.new_data.emit(message)


class TelnetServerThread(ReceiverThread):
    def __init__(self, host: str, port: int, reconnect_delay: float = 2.0) -> None:
        super().__init__()
        self._host = host
        self._port = port
        self._listener: Optional[socket.socket] = None
        self._client: Optional[socket.socket] = None
        self._reconnect_delay = max(1.0, reconnect_delay)
        self._read_size = 4096
        self._protocol_decoder = ProtocolStreamDecoder()

    def run(self) -> None:
        logger.log_info("Telnet server thread listening on %s:%s", self._host, self._port)
        while not self.stopped():
            if self._listener is None and not self._setup_listener():
                self.interruptible_wait(self._reconnect_delay)
                continue

            if self._client is None and not self._accept_client():
                continue

            if self._client is None:
                continue

            try:
                chunk = self._client.recv(self._read_size)
            except socket.timeout:
                continue
            except (OSError, AttributeError) as exc:
                logger.log_error(f"Telnet server recv failed: {exc}")
                self._close_client()
                continue

            if chunk:
                self._emit_messages(chunk)
            else:
                logger.log_info("Telnet server client disconnected")
                self._close_client()

        self._close_client()
        self._close_listener()
        logger.log_info("Telnet server thread stopped")

    def send_response(self, response: bytes) -> None:
        if not self._client:
            logger.log_warning("Telnet server send requested without client")
            return
        try:
            self._client.sendall(response)
        except (OSError, AttributeError) as exc:
            logger.log_error(f"Telnet server send failed: {exc}")
            self._close_client()

    def stop(self) -> None:
        super().stop()
        self._close_client()
        self._close_listener()

    def _setup_listener(self) -> bool:
        try:
            listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            listener.bind((self._host, self._port))
            listener.listen(1)
            listener.settimeout(1.0)
            self._listener = listener
            logger.log_info("Telnet server listening on %s:%s", self._host, self._port)
            return True
        except (OSError, AttributeError) as exc:
            logger.log_error(f"Telnet server listen failed: {exc}")
            self._close_listener()
            return False

    def _accept_client(self) -> bool:
        if self._listener is None:
            return False
        try:
            client, addr = self._listener.accept()
        except socket.timeout:
            return False
        except (OSError, AttributeError) as exc:
            logger.log_error(f"Telnet server accept failed: {exc}")
            self._close_listener()
            return False

        client.settimeout(1.0)
        self._client = client
        self.connection_state.emit(True)
        logger.log_info("Telnet server accepted connection from %s", addr)
        return True

    def _close_client(self) -> None:
        if self._client:
            try:
                self._client.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            try:
                self._client.close()
            except OSError:
                pass
            self._client = None
            self.connection_state.emit(False)
        self._protocol_decoder.reset()

    def _close_listener(self) -> None:
        if self._listener:
            try:
                self._listener.close()
            except OSError:
                pass
            self._listener = None

    def _emit_messages(self, chunk: bytes) -> None:
        for message in self._protocol_decoder.feed(chunk):
            self.new_data.emit(message)


class TelnetBaseReceiver(Receiver, ABC):
    def __init__(self, defaults: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(receiver_thread=None)
        self._settings: Dict[str, Any] = defaults.copy() if defaults else {}
        self._worker: Optional[ReceiverThread] = None
        if self._settings:
            super().config(self._settings)

    def config(self, config: Dict[str, Any]) -> None:
        self._settings.update(config or {})
        super().config(self._settings)

    def open_connection(self) -> bool:
        if self._worker is None:
            self._worker = self._create_worker()
            self.attach_thread(self._worker)
        # Actual connection state is reported by the worker after handshake.
        return True

    def close_connection(self) -> None:
        self._stop_worker()
        self._worker = None
        self.detach_thread()
        self._set_connected(False)

    @abstractmethod
    def _create_worker(self) -> ReceiverThread:
        raise NotImplementedError


class TelnetClientReceiver(TelnetBaseReceiver):
    def settings_valid(self) -> bool:
        host = self._settings.get("host")
        if not host:
            logger.log_warning("TelnetClientReceiver: Missing host")
            return False

        port = self._port_value()
        if port is None:
            logger.log_warning("TelnetClientReceiver: Invalid port setting")
            return False

        return True

    def _create_worker(self) -> ReceiverThread:
        port = self._port_value()
        reconnect = self._positive_float(self._settings.get("reconnect_delay", 2))
        return TelnetClientThread(self._settings.get("host"), port, reconnect)

    def _port_value(self) -> Optional[int]:
        try:
            port = int(self._settings.get("port"))
        except (TypeError, ValueError):
            return None
        if not (0 < port < 65536):
            return None
        return port

    def _positive_float(self, value: Any, default: float = 2.0) -> float:
        try:
            candidate = float(value)
            if candidate <= 0:
                raise ValueError
            return candidate
        except (TypeError, ValueError):
            return default


class TelnetServerReceiver(TelnetBaseReceiver):
    def settings_valid(self) -> bool:
        port = self._port_value()
        if port is None:
            logger.log_warning("TelnetServerReceiver: Invalid port setting")
            return False
        return True

    def _create_worker(self) -> ReceiverThread:
        port = self._port_value()
        host = self._settings.get("host") or ""
        reconnect = self._positive_float(self._settings.get("reconnect_delay", 2))
        return TelnetServerThread(host, port, reconnect)

    def _port_value(self) -> Optional[int]:
        try:
            port = int(self._settings.get("port"))
        except (TypeError, ValueError):
            return None
        if not (0 < port < 65536):
            return None
        return port

    def _positive_float(self, value: Any, default: float = 2.0) -> float:
        try:
            candidate = float(value)
            if candidate <= 0:
                raise ValueError
            return candidate
        except (TypeError, ValueError):
            return default


__all__ = [
    "TelnetBaseReceiver",
    "TelnetClientReceiver",
    "TelnetClientThread",
    "TelnetServerReceiver",
    "TelnetServerThread",
]
