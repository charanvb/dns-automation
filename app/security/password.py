from passlib.context import CryptContext

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# bcrypt silently truncates at 72 bytes; enforce it explicitly so hash and verify are consistent
_MAX_BYTES = 72


def _prep(plain: str) -> str:
    encoded = plain.encode("utf-8")
    return encoded[:_MAX_BYTES].decode("utf-8", errors="ignore") if len(encoded) > _MAX_BYTES else plain


def hash_password(plain_password: str) -> str:
    return _pwd_context.hash(_prep(plain_password))


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return _pwd_context.verify(_prep(plain_password), hashed_password)
