from __future__ import annotations

import unittest

from src.app import _windows_colorref


class ThemeTest(unittest.TestCase):
    def test_windows_colorref_uses_windows_bgr_layout(self) -> None:
        self.assertEqual(_windows_colorref("#101318"), 0x181310)
        self.assertEqual(_windows_colorref("#f8fafc"), 0xFCFAF8)


if __name__ == "__main__":
    unittest.main()
