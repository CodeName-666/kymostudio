"""Wire-format compatibility, failure isolation and finite-value guarantees."""
import json
import math
import pytest
from Core.parsing import parse_payload
from Receiver.message import PlotDataPoint
from Receiver.binary_protocol import ProtocolError, ProtocolStreamDecoder, encode_data_point, decode_data_frame

@pytest.mark.parametrize('payload, expected', [
    (b'1.5', PlotDataPoint(id=0, value=1.5)),
    (b'  +2.0\n', PlotDataPoint(id=0, value=2.0)),
    (b'{"id":7,"x":12.5,"y":-3,"timestamp":5,"z":2}', PlotDataPoint(id=7, value=-3., x=12.5, timestamp=5., z_value=2.)),
    (b'\xef\xbb\xbf{"id":0,"value":0}', PlotDataPoint(id=0, value=0.)),
    (b'{"topic":"test","payload_type":"text","payload":"2.5"}', PlotDataPoint(id=0, value=2.5)),
    (b'{"topic":"test","payload_type":"json","payload":{"id":1,"value":3}}', PlotDataPoint(id=1, value=3.)),
    (b'', None), (b' # header', None), (b'\n', None),
])
def test_supported_payloads(payload, expected):
    assert parse_payload(payload) == expected

@pytest.mark.parametrize('payload', [
    b'true', b'false', b'null', b'[]', b'{}', b'NaN', b'Infinity', b'-Infinity', b'1e999',
    b'\xff', b'{"id":true,"value":1}', b'{"id":1,"value":false}',
    b'{"id":1,"value":1,"z":NaN}', b'{"id":1,"value":1,"timestamp":-1}',
    b'{"id":1,"value":1,"x":Infinity}', b'x'*65537,
    b'['*2000 + b'0' + b']'*2000,
], ids=lambda payload: payload[:24].decode('latin-1') + ('...' if len(payload) > 24 else ''))
def test_bad_input_does_not_escape_as_a_valid_point(payload):
    with pytest.raises(ProtocolError):
        parse_payload(payload)

def test_binary_vectors_and_partial_frames():
    p = PlotDataPoint(id=7, value=1.0)
    assert encode_data_point(p).hex() == 'a55a41070000803f00'  # default: NO_CRC descriptor
    frame = encode_data_point(p, crc_enabled=True)
    assert frame.hex() == 'a55a40070000803f54'
    assert parse_payload(frame) == p
    decoder = ProtocolStreamDecoder()
    assert decoder.feed(frame[:4]) == []
    assert decoder.feed(frame[4:]) == [frame]

def test_xyz_binary_golden_vector():
    p = PlotDataPoint(id=3, x=1.25, value=-2.5, z_value=9., timestamp=1.234)
    frame = encode_data_point(p, crc_enabled=True)
    assert frame.hex() == 'a55a4e030000a03f000020c000001041d204000089'
    assert decode_data_frame(frame) == p

def test_corrupt_frame_rejected():
    frame = bytearray(encode_data_point(PlotDataPoint(id=1, value=1.), crc_enabled=True))
    frame[-1] ^= 1
    with pytest.raises(ProtocolError):
        parse_payload(bytes(frame))
