from passlib.context import CryptContext

# Create a password context
pwd_context = CryptContext(schemes=["sha256_crypt"], deprecated="auto")


# Helper functions for password hashing
def get_password_hash(password):
    return pwd_context.hash(password)


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)
