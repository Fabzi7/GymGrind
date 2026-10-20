# password_utils.py
import os
import hashlib

def matrix_xor_hash(password):
    #combining a matrix and and xor operation in order to hash password (explained in nea)
    M = [[11, 8],
        [5, 10]]
    MOD = 1_000_000_007
    hash_value = 0

    for i in range(0, len(password), 2):
        v1 = ord(password[i])
        v2 = ord(password[i + 1]) if i + 1 < len(password) else 0

        v1_prime = (M[0][0] * v1 + M[0][1] * v2) % MOD
        v2_prime = (M[1][0] * v1 + M[1][1] * v2) % MOD

        combined = (v1_prime + v2_prime) % MOD
        hash_value = ((hash_value << 5) ^ (hash_value >> 2) ^ combined) % MOD

    hash_value = (hash_value ^ len(password)) % MOD
    return hex(hash_value)[2:]


def salted_matrix_xor_hash(password, salt):
    base = matrix_xor_hash(password)
    digest = hashlib.sha256(base.encode() + salt).hexdigest()
    return digest


def make_salt(nbytes = 16):
    return os.urandom(nbytes)


def verify_salted(password, salt, stored_hash):
    return salted_matrix_xor_hash(password, salt) == stored_hash


def verify_plain(password, stored_hash):
    return matrix_xor_hash(password) == stored_hash
