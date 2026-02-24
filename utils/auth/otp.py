"""
.. module:: totp_generator
   :platform: Python
   :synopsis: A utility module to generate temporary OTP similar to google authenticator.

:Date: 2025-12-29
:Author(s): Sinku Kumar

Module `totp_generator` provides the `TOTP` class for generating passphrase, OTP, and temporary OTP verifcation.
Additionally it provides a uri generator that can be used to generate QR Code for adding additional authenticators.
"""

from abc import ABC, abstractmethod

import base64
import hashlib
import hmac
import os
import struct
import time
from typing import Optional, Literal


class OTPProvider(ABC):
    """
    Abstract OTP interface based on RFC6238-style TOTP systems.

    This supports:
    - Real-time OTP generation
    - Time-based OTP
    - Verification with drift window
    - Provisioning (QR / URI)
    """

    @abstractmethod
    def generate_otp(self, for_time: Optional[int] = None) -> str:
        """
        Generate OTP for current time or a specific timestamp.
        """
        raise NotImplementedError

    @abstractmethod
    def verify(self, otp: str, window: int = 1) -> bool:
        """
        Verify an OTP with allowed time drift window.
        """
        raise NotImplementedError

    @abstractmethod
    def provisioning_uri(self, account_name: str, issuer: str) -> str:
        """
        Generate otpauth:// provisioning URI for QR code generation.
        """
        raise NotImplementedError


class TOTPProvider(OTPProvider):
    """
    Google Authenticator compatible TOTP generator.
    """

    def __init__(
        self,
        secret: str,
        interval: int = 30,
        digits: int = 6,
        algorithm: Literal["SHA1", "SHA256", "SHA512"] = "SHA1",
    ):
        """
        Google Authenticator compatible TOTP implementation.

        :param secret: Base32 encoded secret
        :param interval: Time step in seconds (default: 30)
        :param digits: Number of digits in OTP (default: 6)
        :param algorithm: Hash algorithm (SHA1, SHA256, SHA512)
        """
        self.secret = secret
        self.interval = interval
        self.digits = digits
        self.algorithm = algorithm.upper()

    @staticmethod
    def generate_secret(length: int = 20) -> str:
        """
        Generate a Base32 secret suitable for Google Authenticator.
        """
        random_bytes = os.urandom(length)
        return base64.b32encode(random_bytes).decode("utf-8").replace("=", "")

    def _get_hmac(self, counter: int) -> bytes:
        key = base64.b32decode(self.secret + "=" * ((8 - len(self.secret) % 8) % 8))
        msg = struct.pack(">Q", counter)

        if self.algorithm == "SHA1":
            digest = hashlib.sha1
        elif self.algorithm == "SHA256":
            digest = hashlib.sha256
        elif self.algorithm == "SHA512":
            digest = hashlib.sha512
        else:
            raise ValueError("Unsupported algorithm")

        return hmac.new(key, msg, digest).digest()

    def generate_otp(self, for_time: Optional[int] = None) -> str:
        """
        Generate TOTP for the current time (or a specific timestamp).
        """
        if for_time is None:
            for_time = int(time.time())

        counter = for_time // self.interval
        hmac_digest = self._get_hmac(counter)

        offset = hmac_digest[-1] & 0x0F
        binary = struct.unpack(">I", hmac_digest[offset : offset + 4])[0]
        binary &= 0x7FFFFFFF

        otp = binary % (10**self.digits)
        return str(otp).zfill(self.digits)

    def verify(self, otp: str, window: int = 1) -> bool:
        """
        Verify an OTP allowing time drift.

        :param otp: User-provided OTP
        :param window: Number of intervals before/after to allow
        """
        current_time = int(time.time())

        for offset in range(-window, window + 1):
            test_time = current_time + (offset * self.interval)
            if self.generate_otp(test_time) == otp:
                return True

        return False

    def provisioning_uri(self, account_name: str, issuer: str) -> str:
        """
        Generate otpauth:// URI for QR code generation.
        """
        return f"otpauth://totp/{issuer}:{account_name}" f"?secret={self.secret}&issuer={issuer}" f"&algorithm={self.algorithm}&digits={self.digits}&period={self.interval}"


if __name__ == "__main__":
    # Generate secret (store this securely)
    secret = TOTPProvider.generate_secret()

    totp = TOTPProvider("FH2MMUESLNQUHIH2")

    # Generate OTP
    code = totp.generate_otp()
    print("Current OTP:", code)

    # Verify OTP (user input)
    is_valid = totp.verify(code)
    print("Valid:", is_valid)

    # Optional: generate QR-compatible URI
    uri = totp.provisioning_uri("user@example.com", "MyApp")
    print(uri)
