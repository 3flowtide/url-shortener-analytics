import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest

from app.services.short_code_generator import ShortCodeGenerator


def test_generate_returns_correct_length():
    generator = ShortCodeGenerator(length=10)
    assert len(generator.generate()) == 10


def test_generate_returns_unique_codes():
    generator = ShortCodeGenerator(length=8)
    codes = {generator.generate() for _ in range(200)}
    assert len(codes) == 200


def test_length_below_minimum_raises():
    with pytest.raises(ValueError):
        ShortCodeGenerator(length=2)
