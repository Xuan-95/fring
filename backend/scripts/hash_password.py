#!/usr/bin/env python3
"""
Helper script to generate bcrypt password hashes for manual user creation.
Usage: python scripts/hash_password.py
"""

from getpass import getpass
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def main():
    print("Password Hash Generator")
    print("=" * 50)
    print()

    while True:
        password = getpass("Enter password (or press Ctrl+C to exit): ")
        if not password:
            print("Password cannot be empty!")
            continue

        if len(password) < 8:
            print("Warning: Password is less than 8 characters")

        password_hash = pwd_context.hash(password)
        print(f"\nPassword hash:\n{password_hash}\n")
        print("=" * 50)
        print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nExiting...")
