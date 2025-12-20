import os

from cryptography.hazmat.primitives.serialization import load_pem_public_key
from cryptography.hazmat.primitives.hashes import Hash, SHA256
from cryptography.exceptions import InvalidSignature


class Challenge:
    CHALLENGE_SIZE = 32

    def __init__(self, public_key_file: str):
        self.public_key = self.load_public_key(public_key_file)
        self.hash = Hash(SHA256())
        self.challenge = bytes()
        self.gen_new_challenge()

    def load_public_key(self, public_key_file: str):
        with open(public_key_file, "rb") as f:
            pem_public_key = f.read()
        return load_pem_public_key(pem_public_key)

    def gen_new_challenge(self):
        self.hash = Hash(SHA256())
        self.challenge = os.urandom(self.CHALLENGE_SIZE)

    def get_challenge(self) -> bytes:
        return self.challenge

    def check_response(self, response: bytes) -> bool:
        self.hash.update(self.challenge)
        try:
            self.public_key.verify(response, self.hash.finalize())
            result = True
        except InvalidSignature:
            result = False
        self.gen_new_challenge()
        return result
