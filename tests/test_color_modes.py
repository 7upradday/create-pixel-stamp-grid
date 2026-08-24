import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skill" / "create-pixel-stamp-grid" / "scripts" / "pixelize_tile.py"


class PixelizeColorModesTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        source = Image.new("RGB", (8, 8), "#E73381")
        for x in range(4, 8):
            for y in range(8):
                source.putpixel((x, y), (35, 157, 186))
        self.source = self.root / "source.png"
        source.save(self.source)
        self.palette = self.root / "palette.json"
        self.palette.write_text(json.dumps({"shared_palette": ["#102000", "#F0F0F0"]}))

    def tearDown(self):
        self.temp.cleanup()

    def run_script(self, *args):
        subprocess.run([sys.executable, str(SCRIPT), *map(str, args)], check=True)

    @staticmethod
    def colors_in(path):
        image = Image.open(path).convert("RGB")
        return {color for _, color in image.getcolors(maxcolors=image.width * image.height)}

    def test_preserve_is_default_and_retains_source_colors(self):
        output = self.root / "preserve.png"
        self.run_script(self.source, output, "--output-size", 16)
        colors = self.colors_in(output)
        self.assertEqual(colors, {(231, 51, 129), (35, 157, 186)})

    def test_local_mode_keeps_independent_semantic_colors(self):
        output = self.root / "local.png"
        self.run_script(
            self.source,
            output,
            "--color-mode",
            "local",
            "--logical-size",
            8,
            "--output-size",
            16,
            "--local-colors",
            32,
        )
        colors = self.colors_in(output)
        self.assertIn((231, 51, 129), colors)
        self.assertIn((35, 157, 186), colors)

    def test_shared_mode_is_explicit_and_uses_only_shared_palette(self):
        output = self.root / "shared.png"
        self.run_script(
            self.source,
            output,
            "--color-mode",
            "shared",
            "--palette-json",
            self.palette,
            "--logical-size",
            8,
            "--output-size",
            16,
        )
        colors = self.colors_in(output)
        self.assertTrue(colors <= {(16, 32, 0), (240, 240, 240)})

    def test_legacy_palette_argument_still_selects_shared_mode(self):
        output = self.root / "legacy.png"
        self.run_script(
            self.source,
            output,
            "--palette-json",
            self.palette,
            "--logical-size",
            8,
            "--output-size",
            16,
        )
        colors = self.colors_in(output)
        self.assertTrue(colors <= {(16, 32, 0), (240, 240, 240)})


if __name__ == "__main__":
    unittest.main()
