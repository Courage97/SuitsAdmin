from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.backends import default_backend
import base64
import os
from django.conf import settings

# Generate a secret key (store this securely!)
SECRET_KEY = getattr(settings, "AES_SECRET_KEY", b"your-32-byte-long-secret-key")

def encrypt_data(plaintext):
    """
    Encrypts plaintext using AES-256 encryption.
    """
    iv = os.urandom(16)  # Generate a random IV (Initialization Vector)
    cipher = Cipher(algorithms.AES(SECRET_KEY), modes.CBC(iv), backend=default_backend())

    encryptor = cipher.encryptor()
    padder = padding.PKCS7(128).padder()

    padded_data = padder.update(plaintext.encode()) + padder.finalize()
    encrypted_data = encryptor.update(padded_data) + encryptor.finalize()

    return base64.b64encode(iv + encrypted_data).decode()

def decrypt_data(encrypted_text):
    """
    Decrypts AES-256 encrypted text.
    """
    encrypted_bytes = base64.b64decode(encrypted_text)
    iv = encrypted_bytes[:16]
    encrypted_data = encrypted_bytes[16:]

    cipher = Cipher(algorithms.AES(SECRET_KEY), modes.CBC(iv), backend=default_backend())

    decryptor = cipher.decryptor()
    decrypted_padded = decryptor.update(encrypted_data) + decryptor.finalize()

    unpadder = padding.PKCS7(128).unpadder()
    decrypted_data = unpadder.update(decrypted_padded) + unpadder.finalize()

    return decrypted_data.decode()
