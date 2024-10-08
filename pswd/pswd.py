from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.backends import default_backend
import json
import os
import click
import pyperclip
import yaml

def init_assets():

    to_yaml = {
        "data": os.path.join("assets", "storage.json"),
        "key": os.path.join("assets", "private_key.pem")
    }

    if not os.path.exists("assets"):
        os.mkdir("assets")
    if not os.path.exists("assets/files.yaml"):
        with open("assets/files.yaml", "w") as files:
            yaml.dump(to_yaml, files)


init_assets()


def get_file(filetype):
    if filetype not in ["data", "key"]:
        return
    with open("files.yaml", "r") as f:
        return yaml.safe_load(f)[filetype]


def set_file(filetype, filename):
    if filetype not in ["data", "key"]:
        return
    with open("files.yaml", "r+") as f:
        files = yaml.safe_load(f)
        files[filetype] = filename
        yaml.dump(files, f)


def make_key():
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend()
    )
    with open(get_file("key"), 'wb') as f:
        f.write(private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption()
        ))
    return private_key


def load_key():
    if os.path.exists(get_file("key")):
        with open(get_file("key"), 'rb') as f:
            private_key = serialization.load_pem_private_key(
                f.read(),
                password=None,
                backend=default_backend()
            )
        return private_key
    print("RSA key not found. Making a new one...")
    return make_key()


def save_passwords(passwords):
    with open(get_file("data"), 'w') as f:
        json.dump(passwords, f)


def load_passwords():
    if os.path.exists(get_file("data")):
        with open(get_file("data"), 'r') as f:
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


def get_password(service):
    private_key = load_key()
    passwords = load_passwords()

    encrypted_password_hex = passwords.get(service.lower())
    if not encrypted_password_hex:
        click.echo(f"No password found for a service.")
        return

    encrypted_password = bytes.fromhex(encrypted_password_hex)
    return decrypt_password(private_key, encrypted_password)

# CLI

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
    click.echo(get_password(service))


@cli.command()
@click.argument('service')
def copy(service):
    """Copy a password to the clipboard."""
    pyperclip.copy(get_password(service))
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
    click.echo(get_file("data"))

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

    os.system(f"move {get_file("data")} {new_path}")
    
    set_file("data", new_path)
    click.echo(f"Moved storage file {get_file("data")} to {new_path}")