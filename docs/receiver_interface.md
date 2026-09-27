# Receiver Interface Contract

Every transport adapter inherits from `Receiver` in
`python/Receiver/receiver.py`. The interface keeps lifecycle and payload
handling identical for Serial, Telnet, MQTT, CAN, and synthetic test data.

## Signal contract

`new_data: Signal(bytes)` emits exactly one complete message:

- one Plotter Compact Binary Protocol v6 frame, or
- one complete legacy JSON/plain-number message.

Byte-stream adapters must pass received chunks through
`ProtocolStreamDecoder` before emitting. Individual serial or socket reads are
not message boundaries.

## Lifecycle

- `start()` validates settings, opens the transport, and starts its worker.
- `stop()` signals the worker, waits for termination, and closes resources.
- `open_connection() -> bool`, `close_connection()`, and
  `settings_valid() -> bool` are implemented by concrete receivers.
- Connection state is changed only through `_set_connected()`.
- `config(dict)` stores settings and invokes `_on_config_updated()`.

## Threads

Workers derive from `ReceiverThread`. A receiver calls `attach_thread()` once
the worker exists; the base class forwards worker messages to `new_data`.

`send_response(bytes)` forwards raw bytes when a transport supports sending.
Protocol v6.0 defines telemetry input only, so this method does not imply an
application-level command format.

## Adapter checklist

1. Validate all required transport settings.
2. Open and close resources without blocking the GUI thread.
3. For Serial/TCP-like streams, feed chunks into `ProtocolStreamDecoder` and
   emit only its complete messages.
4. Pass binary v6 frames unchanged.
5. Transport-native formats such as Classic CAN may normalize values into an
   accepted Plotter payload.
6. Stop promptly when `stop_event` is emitted and keep connection state in
   sync.

The canonical wire contract is
`../../PlotterEcu/lib/PlotterLib/PROTOCOL.md`.
