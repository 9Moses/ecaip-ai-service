import os
from dotenv import load_dotenv

# App core imports
from app.core.crypto import encrypt_credentials
from app.models.bi_connection import BIConnection

# Load environment variables from .env file
load_dotenv()

# 1. Prepare configuration and encrypted credentials
provider = "tableau"
token_secret = os.getenv("TABLEAU_TOKEN_SECRET")
if token_secret is None:
    raise ValueError("TABLEAU_TOKEN_SECRET environment variable is missing")
credentials_encrypted = encrypt_credentials(token_secret)

config = {
    "server_url": os.getenv("TABLEAU_SERVER"),
    "site_id": os.getenv("TABLEAU_SITE"),
    "pat_name": os.getenv("TABLEAU_TOKEN_NAME"),
    "datasource_luid": os.getenv("TABLEAU_DATASOURCE_LUID"),
}

# 2. Instantiate BIConnection model instance
connection = BIConnection(
    provider=provider, credentials_encrypted=credentials_encrypted, config=config
)

print("✅ BIConnection instance successfully created:")
print(f"Provider: {connection.provider}")
print(f"Server URL: {connection.config.get('server_url')}")

print(f"Site ID: {connection.config.get('site_id')}")
