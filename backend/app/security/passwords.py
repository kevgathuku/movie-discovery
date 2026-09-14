from pwdlib import PasswordHash
from pwdlib.exceptions import PwdlibError

_password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    return _password_hash.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    try:
        return _password_hash.verify(password, hashed)
    except PwdlibError:
        return False
