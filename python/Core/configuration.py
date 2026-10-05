"""Atomic JSON persistence, structural validation and local-file URL handling."""
from __future__ import annotations

import json
import os
import tempfile
from copy import deepcopy
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlsplit

from Core.workspace import validate_workspace

MAX_CONFIGURATION_BYTES = 4 * 1024 * 1024


def local_path(value: str | Path) -> Path:
    """Accept paths or file: URLs, never arbitrary remote URL schemes.

    Plain paths are deliberately *not* URL-decoded: a literal '%20' is a legal
    filename. file://localhost is local; other file hosts are UNC paths.
    """
    if isinstance(value, Path):
        return value
    text = str(value).strip()
    if not text or '\x00' in text:
        raise ValueError("No valid file was selected")
    if len(text) > 2 and text[1] == ':' and text[2] in '/\\':
        return Path(text)
    parsed = urlsplit(text)
    if not parsed.scheme:
        return Path(text)
    if parsed.scheme != 'file' or parsed.query or parsed.fragment:
        raise ValueError("Only local file URLs without query or fragment are supported")
    path = unquote(parsed.path)
    if parsed.netloc and parsed.netloc.lower() != 'localhost':
        path = '//' + parsed.netloc + path
    elif os.name == 'nt' and len(path) > 2 and path[0] == '/' and path[2] == ':':
        path = path[1:]
    if not path:
        raise ValueError("The file URL has no path")
    return Path(path)


def validate_configuration(config: Any) -> None:
    """Validate structure before any running connections or files are changed."""
    if not isinstance(config, dict):
        raise ValueError("Configuration root must be an object")
    try:
        encoded = json.dumps(config, allow_nan=False)
    except (TypeError, ValueError, OverflowError, RecursionError) as exc:
        raise ValueError("Configuration must contain finite JSON values") from exc
    if len(encoded.encode('utf-8')) > MAX_CONFIGURATION_BYTES:
        raise ValueError("Configuration exceeds the 4 MiB limit")
    interfaces = config.get('interfaces')
    if not isinstance(interfaces, list) or not interfaces or len(interfaces) > 64:
        raise ValueError("Configuration needs 1–64 interfaces")
    types: set[str] = set()
    for item in interfaces:
        if not isinstance(item, dict):
            raise ValueError("Every interface must be an object")
        name = item.get('type')
        if not isinstance(name, str) or not name.strip() or name in types:
            raise ValueError("Interface types must be nonempty and unique")
        if not isinstance(item.get('default', {}), dict):
            raise ValueError(f"Defaults for {name} must be an object")
        types.add(name)
    connections = config.get('saved_connections', [])
    if not isinstance(connections, list) or len(connections) > 128:
        raise ValueError("saved_connections must be an array with at most 128 entries")
    ids: set[str] = set()
    for entry in connections:
        if not isinstance(entry, dict):
            raise ValueError("Every connection must be an object")
        if not all(isinstance(entry.get(k), str) and entry[k].strip() for k in ('id', 'name', 'type')):
            raise ValueError("Connections require id, name and type")
        if entry['id'] in ids or entry['type'] not in types:
            raise ValueError("Duplicate connection ID or unknown interface type")
        if not isinstance(entry.get('settings', {}), dict):
            raise ValueError("Connection settings must be an object")
        if 'created_at' in entry and type(entry['created_at']) not in (int, float):
            raise ValueError("Connection created_at must be numeric")
        ids.add(entry['id'])
    for key in ('qml', 'logging', 'performance', 'workspace'):
        if key in config and not isinstance(config[key], dict):
            raise ValueError(f"{key} must be an object")

    performance = config.get('performance', {})
    for field, lower, upper in (('frame_interval_ms', 16, 500), ('display_points_per_signal', 500, 50000)):
        if field in performance:
            v = performance[field]
            if type(v) is not int or not lower <= v <= upper:
                raise ValueError(f"{field} must be an integer from {lower} to {upper}")
    if 'downsample_enabled' in performance and type(performance['downsample_enabled']) is not bool:
        raise ValueError('downsample_enabled must be boolean')
    if 'downsample_target_hz' in performance:
        v = performance['downsample_target_hz']
        if type(v) not in (int, float) or not 10 <= v <= 100000:
            raise ValueError('downsample_target_hz must be 10–100000')
    if config.get('workspace'):
        validate_workspace(config['workspace'])


def atomic_json_write(target: Path, data: Any) -> None:
    """Replace only after serialization and fsync succeed; retain the old file on error."""
    serialized = json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False) + '\n'
    target = Path(target).expanduser().resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary: str | None = None
    try:
        with tempfile.NamedTemporaryFile('w', encoding='utf-8', dir=target.parent,
                                         prefix='.' + target.name + '.', suffix='.tmp', delete=False) as stream:
            temporary = stream.name
            stream.write(serialized)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, target)
        temporary = None
    finally:
        if temporary:
            Path(temporary).unlink(missing_ok=True)


class ConfigurationRepository:
    """Explicit path ownership and copy isolation for user configuration."""

    def __init__(self, path: Path, defaults: dict) -> None:
        self.path = Path(path)
        self._defaults = deepcopy(defaults)

    def load(self) -> dict:
        if not self.path.exists():
            data = deepcopy(self._defaults)
        else:
            if self.path.stat().st_size > MAX_CONFIGURATION_BYTES:
                raise ValueError("Configuration file exceeds 4 MiB")
            with self.path.open(encoding='utf-8-sig') as stream:
                data = json.load(stream)
        validate_configuration(data)
        return data

    def save(self, data: dict) -> None:
        validate_configuration(data)
        atomic_json_write(self.path, data)
