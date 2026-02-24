from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Credentials:
    """
    Credentails for experity portal
    """

    client_id: str
    username: str
    password: str
    auth_passphrase: Optional[str]
