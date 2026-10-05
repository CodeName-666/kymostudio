# SPDX-License-Identifier: GPL-3.0-only OR LicenseRef-KymoStudio-Commercial
# Copyright (c) 2026 Christof Seidel
"""Receiver registry and factory helpers.

The registry is responsible for mapping interface identifiers from the project
configuration to concrete :class:`Receiver` instances. This centralizes the
creation logic so the backend can simply work with the resulting
``receiver_list`` without worrying about the transport specific constructor
details.

All built-in transports are registered here. Additional transports can hook
into the registry by registering their factory via ``register_factory``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, Iterable, Optional

from Logger import logger

from .receiver import Receiver
from .serial_receiver import SerialReceiver
from .telnet_receiver import TelnetClientReceiver
from .mqtt_receiver import MqttReceiver
from .test_receiver import TestReceiver
from .can_receiver import CanReceiver


ReceiverFactory = Callable[[Dict[str, Any]], Optional[Receiver]]


@dataclass
class InterfaceDefinition:
    """Simplified interface definition parsed from the JSON configuration."""

    type: str
    defaults: Dict[str, Any]


class PlaceholderReceiver(Receiver):
    """Fallback receiver that keeps track of config but has no transport yet."""

    def __init__(self, interface_type: str, defaults: Dict[str, Any]):
        super().__init__(receiver_thread=None)
        self._interface_type = interface_type
        self._defaults = defaults or {}

    def open_connection(self) -> bool:
        logger.log_warning(
            f"Receiver '{self._interface_type}' has no transport implementation yet"
        )
        return False

    def close_connection(self) -> None:
        logger.log_info(f"Receiver '{self._interface_type}' closed")

    def settings_valid(self) -> bool:
        # For now assume placeholder receivers are always valid so the backend
        # logic can proceed. Real receivers should override this with concrete
        # validation rules.
        return True


class ReceiverRegistry:
    """Keeps a mapping of interface identifiers to factory functions."""

    def __init__(self) -> None:
        self._factories: Dict[str, ReceiverFactory] = {}
        self._register_builtin_factories()

    def register_factory(self, interface_type: str, factory: ReceiverFactory) -> None:
        """Register or override the factory for a specific interface type."""

        self._factories[interface_type] = factory
        logger.log_debug(f"Registered receiver factory for '{interface_type}'")

    def create_receiver(self, interface_config: Dict[str, Any]) -> Optional[Receiver]:
        """Create a single receiver instance from an interface configuration.

        Args:
            interface_config: Dictionary with 'type' and 'default' keys

        Returns:
            Receiver instance or None if creation fails
        """
        interface_type = interface_config.get("type")
        if not interface_type:
            logger.log_error("Interface config missing 'type' field")
            return None

        factory = self._factories.get(interface_type)
        if factory is None:
            logger.log_warning(
                f"No receiver factory registered for '{interface_type}'"
            )
            return None

        defaults = interface_config.get("default", {})
        receiver = factory({"type": interface_type, "default": defaults})
        if receiver is None:
            logger.log_warning(
                f"Factory for '{interface_type}' returned no receiver instance"
            )
            return None

        receiver.config(defaults)
        logger.log_info(f"Created receiver for interface '{interface_type}'")
        return receiver

    def create_receivers(
        self, interface_definitions: Iterable[InterfaceDefinition]
    ) -> Dict[str, Receiver]:
        receivers: Dict[str, Receiver] = {}

        for definition in interface_definitions:
            factory = self._factories.get(definition.type)
            if factory is None:
                logger.log_warning(
                    f"No receiver factory registered for '{definition.type}'"
                )
                continue

            receiver = factory({"type": definition.type, "default": definition.defaults})
            if receiver is None:
                logger.log_warning(
                    f"Factory for '{definition.type}' returned no receiver instance"
                )
                continue

            receiver.config(definition.defaults)
            receivers[definition.type] = receiver
            logger.log_info(f"Created receiver for interface '{definition.type}'")

        return receivers

    def _register_builtin_factories(self) -> None:
        self.register_factory(
            "Serial", lambda cfg: SerialReceiver(cfg.get("default", {}))
        )
        self.register_factory(
            "Telnet", lambda cfg: TelnetClientReceiver(cfg.get("default", {}))
        )
        self.register_factory(
            "MQTT", lambda cfg: MqttReceiver(cfg.get("default", {}))
        )
        self.register_factory(
            "CAN", lambda cfg: CanReceiver(cfg.get("default", {}))
        )
        self.register_factory(
            "Test", lambda cfg: TestReceiver(cfg.get("default", {}))
        )


def parse_interface_definitions(raw_interfaces: Iterable[Dict[str, Any]]) -> Dict[str, InterfaceDefinition]:
    """Normalize the raw JSON interfaces list.

    The JSON config simply contains dictionaries with keys ``type`` and
    ``default``. Normalizing them once keeps the backend config handling tidy.
    """

    definitions: Dict[str, InterfaceDefinition] = {}

    if not raw_interfaces:
        return definitions

    for item in raw_interfaces:
        interface_type = item.get("type")
        if not interface_type:
            logger.log_warning("Encountered interface entry without 'type'")
            continue

        defaults = item.get("default", {}) or {}
        definitions[interface_type] = InterfaceDefinition(interface_type, defaults)

    return definitions


__all__ = ["InterfaceDefinition", "PlaceholderReceiver", "ReceiverRegistry", "parse_interface_definitions"]
