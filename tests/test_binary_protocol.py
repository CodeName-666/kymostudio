# SPDX-License-Identifier: GPL-3.0-only OR LicenseRef-KymoStudio-Commercial
# Copyright (c) 2026 Christof Seidel
"""Golden-vector coverage for the compact embedded wire protocol."""

from __future__ import annotations

import math
import sys
import unittest
from unittest.mock import patch
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PYTHON_ROOT = PROJECT_ROOT / "python"
ECU_LIBRARY_ROOT = PROJECT_ROOT.parent / "KymoProbe" / "lib" / "KymoCore"
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


class BinaryProtocolGoldenVectorTests(unittest.TestCase):
    def test_minimal_y_frame_matches_embedded_golden_vector(self) -> None:
        frame = encode_data_point(PlotDataPoint(id=7, value=1.0))
        self.assertEqual(frame.hex(), "a55a41070000803f00")
        self.assertEqual(len(frame), 9)
        self.assertEqual(decode_data_frame(frame), PlotDataPoint(id=7, value=1.0))

    def test_xyz_timestamp_frame_matches_embedded_golden_vector(self) -> None:
        point = PlotDataPoint(id=3, x=1.25, value=-2.5, z_value=9.0, timestamp=1.234)
        frame = encode_data_point(point)
        self.assertEqual(
            frame.hex(),
            "a55a4f030000a03f000020c000001041d204000000",
        )
        self.assertEqual(len(frame), 21)
        self.assertEqual(decode_data_frame(frame), point)

    def test_crc_and_non_finite_values_are_rejected(self) -> None:
        frame = bytearray(encode_data_point(PlotDataPoint(id=1, value=2.0), crc_enabled=True))
        frame[-2] ^= 0x01
        with self.assertRaises(ProtocolError):
            decode_data_frame(bytes(frame))
        with self.assertRaises(ValueError):
            encode_data_point(PlotDataPoint(id=1, value=math.nan))

    def test_default_mode_does_not_calculate_or_check_crc(self) -> None:
        point = PlotDataPoint(id=7, value=1.0)
        with patch("Receiver.binary_protocol.crc8", side_effect=AssertionError("CRC called")), \
                patch("Receiver.binary_protocol._CRC8_TABLE", ()):
            frame = encode_data_point(point)
            self.assertEqual(frame.hex(), "a55a41070000803f00")
            # The trailer is ignored in this mode, even when changed in transit.
            changed = frame[:-1] + b"\xff"
            self.assertEqual(decode_data_frame(changed), point)
            self.assertEqual(ProtocolStreamDecoder().feed(changed), [changed])

    def test_crc_opt_in_preserves_legacy_vectors(self) -> None:
        point = PlotDataPoint(id=7, value=1.0)
        frame = encode_data_point(point, crc_enabled=True)
        self.assertEqual(frame.hex(), "a55a40070000803f54")
        self.assertEqual(decode_data_frame(frame), point)
        point = PlotDataPoint(id=3, x=1.25, value=-2.5, z_value=9.0, timestamp=1.234)
        frame = encode_data_point(point, crc_enabled=True)
        self.assertEqual(frame.hex(), "a55a4e030000a03f000020c000001041d204000089")
        self.assertEqual(decode_data_frame(frame), point)

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
        damaged = bytearray(encode_data_point(PlotDataPoint(id=1, value=1.0), crc_enabled=True))
        damaged[-1] ^= 0x80
        valid = encode_data_point(PlotDataPoint(id=2, value=2.0))
        self.assertEqual(decoder.feed(bytes(damaged) + valid), [valid])

    def test_mixed_crc_modes_across_every_fragment_size(self) -> None:
        frames = [encode_data_point(PlotDataPoint(id=i, value=float(i)), crc_enabled=bool(i % 2))
                  for i in range(8)]
        wire = b"".join(frames)
        for size in range(1, len(wire) + 1):
            decoder = ProtocolStreamDecoder()
            decoded = []
            for offset in range(0, len(wire), size):
                decoded.extend(decoder.feed(wire[offset:offset + size]))
            self.assertEqual(decoded, frames)


@unittest.skipUnless(ECU_SOURCE_ROOT.exists(), "Separate KymoProbe sources were not included in the uploaded archive")
class EmbeddedSourceContractTests(unittest.TestCase):
    def test_embedded_constants_and_golden_vectors_match_python(self) -> None:
        header = (ECU_SOURCE_ROOT / "kymo_protocol.h").read_text(encoding="utf-8")
        self.assertIn("#define KYMO_SYNC_0 0xA5u", header)
        self.assertIn("#define KYMO_SYNC_1 0x5Au", header)
        self.assertIn("#define KYMO_DESCRIPTOR_DATA 0x40u", header)
        self.assertIn("#define KYMO_FRAME_MIN_SIZE 9u", header)
        self.assertIn("#define KYMO_FRAME_MAX_SIZE 21u", header)

        protocol_doc = (ECU_LIBRARY_ROOT / "PROTOCOL.md").read_text(encoding="utf-8")
        self.assertIn("A5 5A 40 07 00 00 80 3F 54", protocol_doc)
        self.assertIn(
            "A5 5A 4E 03 00 00 A0 3F 00 00 20 C0 00 00 10 41 D2 04 00 00 89",
            protocol_doc,
        )

    def test_embedded_sender_has_no_text_formatting_or_heap_allocation(self) -> None:
        paths = sorted(ECU_SOURCE_ROOT.glob("*.cpp"))
        self.assertIn(ECU_SOURCE_ROOT / "kymo_protocol.cpp", paths)
        sources = "\n".join(path.read_text(encoding="utf-8") for path in paths)
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
