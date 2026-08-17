import secrets
import string

ALPHABET = string.ascii_letters + string.digits


class ShortCodeGenerator:
    def __init__(self, length=7):
        if length < 4:
            raise ValueError("length must be at least 4 to keep collisions unlikely")
        self._length = length

    def generate(self):
        code = ""
        for _ in range(self._length):
            code += secrets.choice(ALPHABET)
        return code
