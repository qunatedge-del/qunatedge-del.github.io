import unittest
from ktherm_proto import checksum, make_frame, parse_line, make_log_end


class T(unittest.TestCase):
    def test_roundtrip(self):
        f = make_frame("T", 12, 1760000000, [23.44, -200.0, "OPEN", 1372.0], 24.567, 5)
        self.assertTrue(f.startswith("$T,12,1760000000,23.4,-200.0,OPEN,1372.0,24.57,5*"))
        p = parse_line(f)
        self.assertEqual(p["type"], "sample")
        self.assertEqual(p["ch"], [23.4, -200.0, "OPEN", 1372.0])
        self.assertEqual((p["seq"], p["t"], p["cjc"], p["flags"]), (12, 1760000000, 24.57, 5))

    def test_known_checksum(self):
        # 0x41 ^ 0x42 ^ 0x43 = 0x40  (worked out by hand, independent of the implementation)
        self.assertEqual(checksum("ABC"), "40")
        self.assertEqual(checksum(""), "00")

    def test_bad(self):
        f = make_frame("T", 1, 1, [1, 2, 3, 4], 20, 0)
        self.assertEqual(parse_line(f[:-2] + "00")["type"], "bad")
        self.assertEqual(parse_line("$T,1,2*00")["type"], "bad")
        self.assertEqual(parse_line("$T,1,1,x,2,3,4,20.00,0*" + checksum("T,1,1,x,2,3,4,20.00,0"))["reason"], "field")

    def test_misc(self):
        self.assertEqual(parse_line("# KTHERM 4CH FW1.0")["type"], "info")
        self.assertEqual(parse_line("OK")["type"], "resp")
        self.assertIsNone(parse_line("  \r\n"))
        e = parse_line(make_log_end(42))
        self.assertEqual((e["type"], e["count"]), ("logend", 42))
        l = parse_line(make_frame("L", 3, 5, [1, 2, 3, 4], 20, 4))
        self.assertEqual(l["type"], "logrec")


if __name__ == "__main__":
    unittest.main()
