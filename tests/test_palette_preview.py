import importlib.util
import tempfile
import unittest
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skill" / "create-pixel-stamp-grid" / "scripts" / "extract_palette.py"
SPEC = importlib.util.spec_from_file_location("extract_palette", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class PalettePreviewTest(unittest.TestCase):
    def test_preview_expands_for_twenty_four_shared_colors(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "preview.png"
            per_image = [[(index * 20, 80, 120) for index in range(8)]] * 4
            shared = [(index * 10, 100, 180) for index in range(24)]
            dominant = [
                {
                    "role": "primary",
                    "base_color": "#EEF9F1",
                    "accent_color": "#BFE8D0",
                    "family": "mint-green",
                    "source_color": "#8DAB9A",
                },
                {
                    "role": "secondary",
                    "base_color": "#FFF3B2",
                    "accent_color": "#FFE371",
                    "family": "yellow-warm",
                    "source_color": "#A39065",
                },
            ]
            MODULE.draw_preview(per_image, shared, dominant, output)
            with Image.open(output) as preview:
                self.assertGreaterEqual(preview.width, 180 + 24 * 72)


if __name__ == "__main__":
    unittest.main()
