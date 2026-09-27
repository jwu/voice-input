import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from english_spacing import add_english_spaces


class EnglishSpacingTests(unittest.TestCase):
    def test_splits_concatenated_english(self):
        self.assertEqual(add_english_spaces("helloiamjohnny"), "hello I am johnny")

    def test_preserves_existing_word_spacing(self):
        self.assertEqual(add_english_spaces("Hello I am Johnny"), "Hello I am Johnny")

    def test_preserves_chinese_and_punctuation(self):
        self.assertEqual(
            add_english_spaces("你好helloiamjohnny!"),
            "你好hello I am johnny!",
        )


if __name__ == "__main__":
    unittest.main()
