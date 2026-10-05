# Kymotrace protocol

The authoritative Kymotrace Compact Binary Protocol v6 specification now ships
with the standalone Embedded library:

`../../../KymoProbe/lib/KymoCore/PROTOCOL.md`

The Python implementation remains in `binary_protocol.py`; KymoStudio also
continues to accept the legacy JSON receive format described by that
specification.

Protocol v6.1 defaults to CRC disabled: descriptor bit 0 indicates NO_CRC,
and the last byte is retained as a zero trailer. Both decoders accept this
mode and legacy CRC-protected frames, including mixed streams. The trailer
is ignored for NO_CRC; protected frames still require a valid CRC.
Use `encode_data_point(point, crc_enabled=True)` to emit the unchanged v6.0
CRC-protected layout. MCU senders opt in with `-DKYMO_ENABLE_CRC=1` when
compiling KymoCore. Older receivers reject the new NO_CRC descriptors.
