"""Behavior checks for the portable image converter; synthetic inputs only."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from PIL import Image, ImageCms
import images


class ImagesTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="image-check-", dir=Path.cwd())
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def source(self, mode="RGB", size=(200, 100), color="red", **save):
        path = self.root / ("source.jpg" if mode == "CMYK" else "source.png")
        Image.new(mode, size, color).save(path, **save)
        return path

    def test_focal_crop_selects_subject_without_stretch(self):
        im = Image.new("RGB", (200, 100), "red")
        im.paste("blue", (100, 0, 200, 100))
        src = self.root / "wide.png"
        im.save(src)
        out = self.root / "square.webp"
        result = images.convert(src, out, (64, 64), focal=(1, .5), lossless=True)
        with Image.open(out) as converted:
            self.assertEqual(converted.size, (64, 64))
            self.assertEqual(converted.getpixel((32, 32)), (0, 0, 255))
        self.assertEqual(result["crop_box"], [100, 0, 200, 100])

    def test_exif_rotation_precedes_crop_and_metadata_is_removed(self):
        src = self.root / "rotated.jpg"
        exif = Image.Exif()
        exif[274] = 6
        exif[270] = "private original description"
        Image.new("RGB", (80, 40), "red").save(src, exif=exif)
        out = self.root / "rotated.webp"
        result = images.convert(src, out, (40, 80), lossless=True)
        self.assertEqual(result["oriented_size"], (40, 80))
        with Image.open(out) as im:
            self.assertEqual(im.size, (40, 80))
            self.assertFalse(im.getexif())
            self.assertNotIn("exif", im.info)

    def test_contain_keeps_alpha_and_optional_background(self):
        src = self.source("RGBA", (100, 40), (255, 0, 0, 128))
        out = self.root / "alpha.webp"
        images.convert(src, out, (100, 100), fit="contain", lossless=True)
        with Image.open(out) as im:
            self.assertEqual(im.getpixel((0, 0))[3], 0)
            self.assertEqual(im.getpixel((50, 50))[3], 128)
        out = self.root / "flattened.webp"
        images.convert(src, out, (100, 100), fit="contain", background="white", lossless=True)
        with Image.open(out) as im:
            self.assertEqual(im.mode, "RGB")
            self.assertEqual(im.getpixel((0, 0)), (255, 255, 255))

    def test_budget_failure_preserves_source_and_existing_derivative(self):
        src = self.source()
        before = hashlib.sha256(src.read_bytes()).digest()
        out = self.root / "kept.webp"
        out.write_bytes(b"existing derivative")
        with self.assertRaises(ValueError):
            images.convert(src, out, (64, 64), max_bytes=1, overwrite=True)
        self.assertEqual(out.read_bytes(), b"existing derivative")
        self.assertEqual(hashlib.sha256(src.read_bytes()).digest(), before)
        self.assertEqual(sorted(p.name for p in self.root.iterdir()), ["kept.webp", "source.png"])

    def test_valid_budget_and_no_implicit_enlargement(self):
        src = self.source()
        out = self.root / "valid.webp"
        result = images.convert(src, out, (64, 64), max_bytes=3000)
        self.assertLessEqual(result["bytes"], 3000)
        with self.assertRaises(ValueError):
            images.convert(src, self.root / "too-large.webp", (640, 640))
        self.assertFalse((self.root / "too-large.webp").exists())

    def test_invalid_crop_and_source_overwrite_are_rejected(self):
        src = self.source()
        with self.assertRaises(ValueError):
            images.convert(src, self.root / "invalid.webp", (64, 64), crop=(150, 0, 100, 100))
        with self.assertRaises(ValueError):
            images.convert(src, src, (64, 64), overwrite=True)

    def test_embedded_profile_and_cmyk_are_normalized(self):
        profile = ImageCms.ImageCmsProfile(ImageCms.createProfile("sRGB")).tobytes()
        src = self.source(icc_profile=profile)
        out = self.root / "srgb.webp"
        images.convert(src, out, (64, 64), lossless=True)
        with Image.open(out) as im:
            self.assertEqual(im.getpixel((32, 32)), (255, 0, 0))
        src = self.source("CMYK", (200, 100), (0, 255, 255, 0))
        images.convert(src, self.root / "cmyk.webp", (64, 64))
        with Image.open(self.root / "cmyk.webp") as im:
            self.assertEqual(im.mode, "RGB")

    def test_cli_runs_from_an_independent_project_directory(self):
        src = self.source()
        command = [sys.executable, str(Path(images.__file__).resolve()), "convert",
                   src.name, "portable.webp", "--size", "64x64"]
        result = subprocess.run(command, cwd=self.root, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((self.root / "portable.webp").is_file())

    def test_named_cli_output_matches_actual_geometry_and_preserves_previous_file(self):
        src = self.source(size=(200, 160))
        command = [sys.executable, str(Path(images.__file__).resolve()), "convert",
                   src.name, "assets", "--size", "80x100", "--name", "alaksiej-michalevic",
                   "--role", "portrait"]
        result = subprocess.run(command, cwd=self.root, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        output = self.root / json.loads(result.stdout)["output"]
        self.assertEqual(output.name, "alaksiej-michalevic-portrait-4x5-80w.webp")
        with Image.open(output) as image:
            self.assertEqual(image.size, (80, 100))
        original = output.read_bytes()
        repeated = subprocess.run(command, cwd=self.root, capture_output=True, text=True)
        self.assertNotEqual(repeated.returncode, 0)
        self.assertEqual(output.read_bytes(), original)

    def test_named_outputs_reject_missing_identity_and_path_fragments(self):
        src = self.source()
        for options in ({"name": "oleg-bresky"}, {"role": "portrait"},
                        {"name": "../oleg-bresky", "role": "portrait"},
                        {"name": "oleg-bresky", "role": "portrait/card"}):
            with self.assertRaises(ValueError):
                images.convert(src, self.root / "assets", (64, 64), **options)
        self.assertFalse((self.root / "assets").exists())

    def test_named_outputs_support_non_person_images(self):
        src = self.source(size=(200, 100))
        result = images.convert(src, self.root / "assets", (160, 90),
                                name="courtroom", role="hero")
        self.assertEqual(Path(result["output"]).name, "courtroom-hero-16x9-160w.webp")
        with Image.open(result["output"]) as image:
            self.assertEqual(image.size, (160, 90))


if __name__ == "__main__":
    unittest.main()

