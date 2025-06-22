import secrets
import string
import os

def generate_secure_password(length=16):
    """Generate a secure password with a mix of letters, digits, and punctuation."""
    alphabet = string.ascii_letters + string.digits + string.punctuation
    password = ''.join(secrets.choice(alphabet) for i in range(length))
    # Ensure the password doesn't contain characters that might break .env files or shell commands
    password = password.replace('"', '_').replace("'", '_').replace('`', '_').replace('$', '_')
    return password

def generate_secure_username(length=8):
    """Generate a secure, simple username."""
    alphabet = string.ascii_lowercase + string.digits
    return ''.join(secrets.choice(alphabet) for i in range(length))

def create_env_file():
    """Create a .env file with all necessary environment variables."""
    db_user = generate_secure_username()
    db_password = generate_secure_password()
    db_name = "sunwind_scada_db"
    db_host = "db"
    db_port = "5432"
    django_secret_key = generate_secure_password(50)

    env_content = f"""# PostgreSQL Database Configuration
DB_NAME={db_name}
DB_USER={db_user}
DB_PASSWORD={db_password}
DB_HOST={db_host}
DB_PORT={db_port}

# Django Configuration
DJANGO_SECRET_KEY={django_secret_key}
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1,django

# Security Settings for Production (defaults are for development)
CSRF_TRUSTED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000,http://localhost:8000,http://127.0.0.1:8000
SECURE_SSL_REDIRECT=False
SESSION_COOKIE_SECURE=False
CSRF_COOKIE_SECURE=False
SECURE_HSTS_SECONDS=0
SECURE_HSTS_INCLUDE_SUBDOMAINS=False
SECURE_HSTS_PRELOAD=False
"""

    with open(".env", "w") as f:
        f.write(env_content)

    print("Successfully created .env file with new credentials.")
    print(f"Database User: {db_user}")

if __name__ == "__main__":
    create_env_file()
