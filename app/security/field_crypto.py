import base64
import hashlib
import hmac
import os

from flask import current_app


class FieldCrypto:
    PREFIX = "enc:v1:"
    NONCE_SIZE = 16
    MAC_SIZE = 32

    @classmethod
    def encrypt(cls, value):
        if value in (None, ""):
            return None

        text = str(value)
        if text.startswith(cls.PREFIX):
            return text

        key = cls._key()
        nonce = os.urandom(cls.NONCE_SIZE)
        plaintext = text.encode("utf-8")
        ciphertext = cls._xor(plaintext, cls._keystream(key, nonce, len(plaintext)))
        mac = hmac.new(key, nonce + ciphertext, hashlib.sha256).digest()
        payload = base64.urlsafe_b64encode(nonce + mac + ciphertext).decode("ascii")
        return cls.PREFIX + payload

    @classmethod
    def decrypt(cls, value):
        if value in (None, ""):
            return None

        text = str(value)
        if not text.startswith(cls.PREFIX):
            return text

        raw = base64.urlsafe_b64decode(text[len(cls.PREFIX):].encode("ascii"))
        nonce = raw[:cls.NONCE_SIZE]
        mac = raw[cls.NONCE_SIZE:cls.NONCE_SIZE + cls.MAC_SIZE]
        ciphertext = raw[cls.NONCE_SIZE + cls.MAC_SIZE:]
        key = cls._key()
        expected_mac = hmac.new(key, nonce + ciphertext, hashlib.sha256).digest()
        if not hmac.compare_digest(mac, expected_mac):
            raise ValueError("Campo sensivel criptografado com assinatura invalida.")

        plaintext = cls._xor(ciphertext, cls._keystream(key, nonce, len(ciphertext)))
        return plaintext.decode("utf-8")

    @classmethod
    def is_encrypted(cls, value):
        return isinstance(value, str) and value.startswith(cls.PREFIX)

    @staticmethod
    def _key():
        secret = current_app.config.get("FIELD_ENCRYPTION_KEY") if current_app else os.getenv("FIELD_ENCRYPTION_KEY")
        if not secret:
            raise RuntimeError("FIELD_ENCRYPTION_KEY nao configurada.")
        return hashlib.sha256(str(secret).encode("utf-8")).digest()

    @staticmethod
    def _keystream(key, nonce, length):
        output = bytearray()
        counter = 0
        while len(output) < length:
            counter_bytes = counter.to_bytes(8, "big")
            output.extend(hmac.new(key, nonce + counter_bytes, hashlib.sha256).digest())
            counter += 1
        return bytes(output[:length])

    @staticmethod
    def _xor(left, right):
        return bytes(a ^ b for a, b in zip(left, right))
