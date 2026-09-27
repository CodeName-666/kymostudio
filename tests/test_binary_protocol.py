"""Golden-vector coverage for the compact embedded wire protocol."""

from __future__ import annotations

import math
import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PYTHON_ROOT = PROJECT_ROOT / "python"
ECU_LIBRARY_ROOT = PROJECT_ROOT.parent / "PlotterEcu" / "lib" / "PlotterLib"
ECU_SOURCE_ROOT = ECU_LIBRARY_ROOT / "src"
if str(PYTHON_ROOT) not in sys.path:
    sys.path.insert(0, str(PYTHON_ROOT))

from Receiver.binary_protocol import (  # noqa: E402
    ProtocolError,
    ProtocolStreamDecoder,
    decode_data_frame,
    encode_data_point,
)
from Receiver.message import PlotDataPoint  # noqa: E402
from Backend.backend import Backend  # noqa: E402
from Receiver.mqtt_receiver import _extract_plotter_payload_lines  # noqa: E402
from Receiver.serial_receiver import SerialReceiver  # noqa: E402
from Receiver.can_receiver import can_message_to_plotter_payload  # noqa: E402
import can  # noqa: E402


class BinaryProtocolGoldenVectorTests(unittest.TestCase):
    def test_minimal_y_frame_matches_embedded_golden_vector(self) -> None:
        frame = encode_data_point(PlotDataPoint(id=7, value=1.0))
        self.assertEqual(frame.hex(), "a55a40070000803f54")
        self.assertEqual(len(frame), 9)
        self.assertEqual(decode_data_frame(frame), PlotDataPoint(id=7, value=1.0))

    def test_xyz_timestamp_frame_matches_embedded_golden_vector(self) -> None:
        point = PlotDataPoint(id=3, x=1.25, value=-2.5, z_value=9.0, timestamp=1.234)
        frame = encode_data_point(point)
        self.assertEqual(
            frame.hex(),
            "a55a4e030000a03f000020c000001041d204000089",
        )
        self.assertEqual(len(frame), 21)
        self.assertEqual(decode_data_frame(frame), point)

    def test_crc_and_non_finite_values_are_rejected(self) -> None:
        frame = bytearray(encode_data_point(PlotDataPoint(id=1, value=2.0)))
        frame[-2] ^= 0x01
        with self.assertRaises(ProtocolError):
            decode_data_frame(bytes(frame))
        with self.assertRaises(ValueError):
            encode_data_point(PlotDataPoint(id=1, value=math.nan))

    def test_binary_frame_is_smaller_than_equivalent_json(self) -> None:
        point = PlotDataPoint(id=3, value=-2.5, timestamp=1.234)
        binary = encode_data_point(point)
        json_payload = b'{"id":3,"value":-2.5,"timestamp":1.234}\n'
        self.assertLessEqual(len(binary), len(json_payload) // 3)


class ProtocolStreamDecoderTests(unittest.TestCase):
    def test_fragmented_and_concatenated_frames_are_reassembled(self) -> None:
        decoder = ProtocolStreamDecoder()
        first = encode_data_point(PlotDataPoint(id=1, value=1.5))
        second = encode_data_point(PlotDataPoint(id=2, x=3.0, value=4.0))

        self.assertEqual(decoder.feed(first[:4]), [])
        self.assertEqual(decoder.feed(first[4:] + second), [first, second])

    def test_binary_and_legacy_json_can_share_a_stream(self) -> None:
        decoder = ProtocolStreamDecoder()
        binary = encode_data_point(PlotDataPoint(id=4, value=5.0))
        json_line = b'{"id":5,"value":6.0}'
        frames = decoder.feed(json_line + b"\n" + binary)
        self.assertEqual(frames, [json_line, binary])

    def test_decoder_resynchronizes_after_a_corrupt_frame(self) -> None:
        decoder = ProtocolStreamDecoder()
        damaged = bytearray(encode_data_point(PlotDataPoint(id=1, value=1.0)))
        damaged[-1] ^= 0x80
        valid = encode_data_point(PlotDataPoint(id=2, value=2.0))
        self.assertEqual(decoder.feed(bytes(damaged) + valid), [valid])


class TransportIntegrationTests(unittest.TestCase):
    def test_backend_parser_accepts_binary_without_json_conversion(self) -> None:
        point = PlotDataPoint(id=12, x=2.0, value=3.0, timestamp=4.0)
        parsed = Backend._parse_data_point(object(), "Serial", encode_data_point(point))
        self.assertEqual(parsed, point)

    def test_mqtt_message_can_contain_concatenated_binary_frames(self) -> None:
        first = encode_data_point(PlotDataPoint(id=1, value=1.0))
        second = encode_data_point(PlotDataPoint(id=2, value=2.0))
        self.assertEqual(_extract_plotter_payload_lines(first + second), [first, second])

    def test_serial_receiver_never_strips_binary_crc_bytes(self) -> None:
        frame = encode_data_point(PlotDataPoint(id=10, value=-8.0))
        self.assertEqual(SerialReceiver._parse_payload(object(), frame), frame)

    def test_can_fd_forwards_the_same_binary_frame(self) -> None:
        frame = encode_data_point(PlotDataPoint(id=9, x=1.0, value=2.0))
        message = can.Message(arbitration_id=0x123, data=frame, is_fd=True)
        self.assertEqual(can_message_to_plotter_payload(message), frame)

    def test_legacy_json_rejects_non_finite_values_like_binary(self) -> None:
        class ParserContext:
            def _notify_status(self, *_args) -> None:
                pass

        self.assertIsNone(
            Backend._parse_data_point(
                ParserContext(), "Serial", b'{"id":1,"value":NaN}'
            )
        )


class EmbeddedSourceContractTests(unittest.TestCase):
    def test_embedded_constants_and_golden_vectors_match_python(self) -> None:
        header = (ECU_SOURCE_ROOT / "plotter_protocol.h").read_text(encoding="utf-8")
        self.assertIn("#define PLOTTER_SYNC_0 0xA5u", header)
        self.assertIn("#define PLOTTER_SYNC_1 0x5Au", header)
        self.assertIn("#define PLOTTER_DESCRIPTOR_DATA 0x40u", header)
        self.assertIn("#define PLOTTER_FRAME_MIN_SIZE 9u", header)
        self.assertIn("#define PLOTTER_FRAME_MAX_SIZE 21u", header)

        protocol_doc = (ECU_LIBRARY_ROOT / "PROTOCOL.md").read_text(encoding="utf-8")
        self.assertIn("A5 5A 40 07 00 00 80 3F 54", protocol_doc)
        self.assertIn(
            "A5 5A 4E 03 00 00 A0 3F 00 00 20 C0 00 00 10 41 D2 04 00 00 89",
            protocol_doc,
        )

    def test_embedded_sender_has_no_text_formatting_or_heap_allocation(self) -> None:
        sources = "\n".join(
            path.read_text(encoding="utf-8")
            for path in (
                ECU_SOURCE_ROOT / "plotter.cpp",
                ECU_SOURCE_ROOT / "plotter_protocol.c",
            )
        )
        self.assertNotIn("snprintf", sources)
        self.assertNotIn("new PrintStream", sources)
        self.assertNotIn("malloc", sources)

    def test_embedded_code_lives_in_the_standalone_library(self) -> None:
        self.assertFalse((PROJECT_ROOT / "embedded").exists())
        self.assertTrue((ECU_LIBRARY_ROOT / "library.json").is_file())
        self.assertTrue((ECU_LIBRARY_ROOT / "library.properties").is_file())
        self.assertTrue((ECU_LIBRARY_ROOT / "test" / "protocol_golden_test.cpp").is_file())


if __name__ == "__main__":
    unittest.main()
