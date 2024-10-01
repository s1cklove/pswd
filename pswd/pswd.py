from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.backends import default_backend
import json
import os

if not os.path.exists("assets"):
    os.mkdir("assets")

DATA_FILE = os.path.join("assets", "storage.json")
KEY_FILE = os.path.join("assets", "private_key.pem")

def reset_data_file(new_data_file: str):

    global DATA_FILE
    DATA_FILE = new_data_file


def load_key():
    if os.path.exists(KEY_FILE):
        with open(KEY_FILE, 'rb') as key_file:
            private_key = serialization.load_pem_private_key(
                key_file.read(),
                password=None,
                backend=default_backend()
            )
        return private_key
    else:
        print("RSA key not found. Making a new one...")
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )
        with open(KEY_FILE, 'wb') as key_file:
            key_file.write(private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption()
            ))
        return private_key


def save_passwords(passwords):
    with open(DATA_FILE, 'w') as f:
        json.dump(passwords, f)


def load_passwords():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    return {}


def encrypt_password(public_key, password):
    encrypted_password = public_key.encrypt(
        password.encode(),
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    return encrypted_password


def decrypt_password(private_key, encrypted_password):
    decrypted_password = private_key.decrypt(
        encrypted_password,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    return decrypted_password.decode()

# CLI

from rsa import *
from store import DATA_FILE, reset_data_file
import click
import pyperclip

@click.group()
def cli():
    pass


@cli.command()
@click.argument('service')
@click.argument('password')
def new(service, password):
    """Add new password for a service. Makes it lowercase.
    """
    private_key = load_key()
    public_key = private_key.public_key()
    passwords = load_passwords()

    if service in passwords:
        click.echo(f"Password already exists. Consider using \"edit\".")
        return

    encrypted_password = encrypt_password(public_key, password)
    passwords[service.lower()] = encrypted_password.hex()
    save_passwords(passwords)
    click.echo(f"Password added.")


@cli.command()
@click.argument('service')
def get(service):
    """Get a password for a service."""
    private_key = load_key()
    passwords = load_passwords()

    encrypted_password_hex = passwords.get(service.lower())
    if not encrypted_password_hex:
        click.echo(f"No password found for a service.")
        return

    encrypted_password = bytes.fromhex(encrypted_password_hex)
    decrypted_password = decrypt_password(private_key, encrypted_password)
    click.echo(decrypted_password)


@cli.command()
@click.argument('service')
def copy(service):
    """Copy a password to the clipboard."""
    private_key = load_key()
    passwords = load_passwords()

    encrypted_password_hex = passwords.get(service.lower())
    if not encrypted_password_hex:
        click.echo(f"No password found for a service.")
        return

    encrypted_password = bytes.fromhex(encrypted_password_hex)
    decrypted_password = decrypt_password(private_key, encrypted_password)
    pyperclip.copy(decrypted_password)
    click.echo(f"Copied to clipboard.")


@cli.command()
@click.argument('service')
@click.argument('new_password')
def edit(service, new_password):
    """Change existing password."""
    private_key = load_key()
    public_key = private_key.public_key()
    passwords = load_passwords()

    if service.lower() not in passwords:
        click.echo(f"No password found for a service.")
        return

    encrypted_password = encrypt_password(public_key, new_password)
    passwords[service.lower()] = encrypted_password.hex()
    save_passwords(passwords)
    click.echo(f"Updated one.")


@cli.command()
def view_keys():
    """Look up for all services you saved something for."""
    passwords = load_passwords()
    for service in passwords.keys():
        click.echo(service.lower())


@cli.command()
def view_passwords():
    """Look up for all passwords you have."""
    private_key = load_key()
    passwords = load_passwords()

    for service, encrypted_password_hex in passwords.items():
        encrypted_password = bytes.fromhex(encrypted_password_hex)
        decrypted_password = decrypt_password(private_key, encrypted_password)
        click.echo(f"{service.lower():15} {decrypted_password}")


@cli.command()
@click.argument('service')
def delete(service):
    """Remove password for a service."""
    passwords = load_passwords()

    if service.lower() in passwords:
        del passwords[service.lower()]
        save_passwords(passwords)
        click.echo(f"Password removed.")
    else:
        click.echo(f"No password found for a service.")

@cli.command()
def get_storage():
    """Get storage file path."""
    click.echo(DATA_FILE)

@cli.command()
@click.argument('new_path')
def reset_storage(new_path: str):
    """Change storage file path. Equivalent to
    move $OLD_PATH$ $NEW_PATH$, but safe (using move
    will completely break everything)

    Both absolute and relative paths are supported.

    Example: pswd new_path '../assets/MyStorage.json'
    """

    new_path = os.path.abspath(new_path)

    os.system(f"move {DATA_FILE} {new_path}")

    reset_data_file(new_path)
    click.echo(f"Moved storage file {DATA_FILE} to {new_path}")