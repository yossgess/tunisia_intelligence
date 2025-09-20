"""
Secure secret management for Tunisia Intelligence RSS scraper.

This module provides secure handling of sensitive configuration data like API keys,
database credentials, and other secrets. It supports multiple backends including
environment variables, Azure Key Vault, AWS Secrets Manager, and encrypted files.
"""
import os
import json
import base64
from typing import Optional, Dict, Any, Union
from pathlib import Path
import logging
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

logger = logging.getLogger(__name__)


class SecretManager:
    """Manages secrets with multiple backend support."""
    
    def __init__(self, backend: str = "env", **kwargs):
        """
        Initialize the secret manager.
        
        Args:
            backend: Secret backend to use ('env', 'file', 'azure_kv', 'aws_sm')
            **kwargs: Backend-specific configuration
        """
        self.backend = backend.lower()
        self.config = kwargs
        self._secrets_cache: Dict[str, Any] = {}
        
        if self.backend == "file":
            self._init_file_backend()
        elif self.backend == "azure_kv":
            self._init_azure_backend()
        elif self.backend == "aws_sm":
            self._init_aws_backend()
        elif self.backend != "env":
            raise ValueError(f"Unsupported secret backend: {backend}")
    
    def _init_file_backend(self):
        """Initialize encrypted file backend."""
        self.secrets_file = Path(self.config.get("secrets_file", "secrets.enc"))
        self.key_file = Path(self.config.get("key_file", "secret.key"))
        
        # Generate or load encryption key
        if not self.key_file.exists():
            self._generate_encryption_key()
        
        self.cipher = Fernet(self._load_encryption_key())
    
    def _init_azure_backend(self):
        """Initialize Azure Key Vault backend."""
        try:
            from azure.keyvault.secrets import SecretClient
            from azure.identity import DefaultAzureCredential
            
            vault_url = self.config.get("vault_url")
            if not vault_url:
                raise ValueError("vault_url is required for Azure Key Vault backend")
            
            credential = DefaultAzureCredential()
            self.azure_client = SecretClient(vault_url=vault_url, credential=credential)
            logger.info("Azure Key Vault backend initialized")
            
        except ImportError:
            raise ImportError("azure-keyvault-secrets and azure-identity packages required for Azure backend")
    
    def _init_aws_backend(self):
        """Initialize AWS Secrets Manager backend."""
        try:
            import boto3
            
            region = self.config.get("region", "us-east-1")
            self.aws_client = boto3.client("secretsmanager", region_name=region)
            logger.info("AWS Secrets Manager backend initialized")
            
        except ImportError:
            raise ImportError("boto3 package required for AWS backend")
    
    def _generate_encryption_key(self):
        """Generate a new encryption key for file backend."""
        password = os.environ.get("SECRETS_PASSWORD", "default-password").encode()
        salt = os.urandom(16)
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password))
        
        # Save key and salt
        key_data = {
            "key": key.decode(),
            "salt": base64.b64encode(salt).decode()
        }
        
        with open(self.key_file, "w") as f:
            json.dump(key_data, f)
        
        # Set restrictive permissions
        os.chmod(self.key_file, 0o600)
        logger.info(f"Generated new encryption key: {self.key_file}")
    
    def _load_encryption_key(self) -> bytes:
        """Load encryption key for file backend."""
        with open(self.key_file, "r") as f:
            key_data = json.load(f)
        
        return key_data["key"].encode()
    
    def get_secret(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """
        Get a secret value by key.
        
        Args:
            key: Secret key name
            default: Default value if secret not found
            
        Returns:
            Secret value or default
        """
        # Check cache first
        if key in self._secrets_cache:
            return self._secrets_cache[key]
        
        try:
            if self.backend == "env":
                value = os.environ.get(key, default)
            elif self.backend == "file":
                value = self._get_secret_from_file(key, default)
            elif self.backend == "azure_kv":
                value = self._get_secret_from_azure(key, default)
            elif self.backend == "aws_sm":
                value = self._get_secret_from_aws(key, default)
            else:
                value = default
            
            # Cache the value
            if value is not None:
                self._secrets_cache[key] = value
            
            return value
            
        except Exception as e:
            logger.error(f"Error retrieving secret '{key}': {e}")
            return default
    
    def _get_secret_from_file(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Get secret from encrypted file."""
        if not self.secrets_file.exists():
            return default
        
        try:
            with open(self.secrets_file, "rb") as f:
                encrypted_data = f.read()
            
            decrypted_data = self.cipher.decrypt(encrypted_data)
            secrets = json.loads(decrypted_data.decode())
            
            return secrets.get(key, default)
            
        except Exception as e:
            logger.error(f"Error reading encrypted secrets file: {e}")
            return default
    
    def _get_secret_from_azure(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Get secret from Azure Key Vault."""
        try:
            secret = self.azure_client.get_secret(key)
            return secret.value
        except Exception as e:
            logger.error(f"Error retrieving secret from Azure Key Vault: {e}")
            return default
    
    def _get_secret_from_aws(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Get secret from AWS Secrets Manager."""
        try:
            response = self.aws_client.get_secret_value(SecretId=key)
            return response["SecretString"]
        except Exception as e:
            logger.error(f"Error retrieving secret from AWS Secrets Manager: {e}")
            return default
    
    def set_secret(self, key: str, value: str) -> bool:
        """
        Set a secret value.
        
        Args:
            key: Secret key name
            value: Secret value
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if self.backend == "env":
                os.environ[key] = value
                logger.warning("Setting environment variable - this is not persistent!")
            elif self.backend == "file":
                return self._set_secret_in_file(key, value)
            elif self.backend == "azure_kv":
                return self._set_secret_in_azure(key, value)
            elif self.backend == "aws_sm":
                return self._set_secret_in_aws(key, value)
            
            # Update cache
            self._secrets_cache[key] = value
            return True
            
        except Exception as e:
            logger.error(f"Error setting secret '{key}': {e}")
            return False
    
    def _set_secret_in_file(self, key: str, value: str) -> bool:
        """Set secret in encrypted file."""
        try:
            # Load existing secrets
            secrets = {}
            if self.secrets_file.exists():
                with open(self.secrets_file, "rb") as f:
                    encrypted_data = f.read()
                decrypted_data = self.cipher.decrypt(encrypted_data)
                secrets = json.loads(decrypted_data.decode())
            
            # Update secret
            secrets[key] = value
            
            # Encrypt and save
            encrypted_data = self.cipher.encrypt(json.dumps(secrets).encode())
            with open(self.secrets_file, "wb") as f:
                f.write(encrypted_data)
            
            # Set restrictive permissions
            os.chmod(self.secrets_file, 0o600)
            return True
            
        except Exception as e:
            logger.error(f"Error writing encrypted secrets file: {e}")
            return False
    
    def _set_secret_in_azure(self, key: str, value: str) -> bool:
        """Set secret in Azure Key Vault."""
        try:
            self.azure_client.set_secret(key, value)
            return True
        except Exception as e:
            logger.error(f"Error setting secret in Azure Key Vault: {e}")
            return False
    
    def _set_secret_in_aws(self, key: str, value: str) -> bool:
        """Set secret in AWS Secrets Manager."""
        try:
            self.aws_client.create_secret(Name=key, SecretString=value)
            return True
        except self.aws_client.exceptions.ResourceExistsException:
            # Update existing secret
            self.aws_client.update_secret(SecretId=key, SecretString=value)
            return True
        except Exception as e:
            logger.error(f"Error setting secret in AWS Secrets Manager: {e}")
            return False
    
    def delete_secret(self, key: str) -> bool:
        """
        Delete a secret.
        
        Args:
            key: Secret key name
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if self.backend == "env":
                os.environ.pop(key, None)
            elif self.backend == "file":
                return self._delete_secret_from_file(key)
            elif self.backend == "azure_kv":
                return self._delete_secret_from_azure(key)
            elif self.backend == "aws_sm":
                return self._delete_secret_from_aws(key)
            
            # Remove from cache
            self._secrets_cache.pop(key, None)
            return True
            
        except Exception as e:
            logger.error(f"Error deleting secret '{key}': {e}")
            return False
    
    def _delete_secret_from_file(self, key: str) -> bool:
        """Delete secret from encrypted file."""
        try:
            if not self.secrets_file.exists():
                return True
            
            # Load existing secrets
            with open(self.secrets_file, "rb") as f:
                encrypted_data = f.read()
            decrypted_data = self.cipher.decrypt(encrypted_data)
            secrets = json.loads(decrypted_data.decode())
            
            # Remove secret
            secrets.pop(key, None)
            
            # Encrypt and save
            encrypted_data = self.cipher.encrypt(json.dumps(secrets).encode())
            with open(self.secrets_file, "wb") as f:
                f.write(encrypted_data)
            
            return True
            
        except Exception as e:
            logger.error(f"Error deleting secret from file: {e}")
            return False
    
    def _delete_secret_from_azure(self, key: str) -> bool:
        """Delete secret from Azure Key Vault."""
        try:
            self.azure_client.begin_delete_secret(key)
            return True
        except Exception as e:
            logger.error(f"Error deleting secret from Azure Key Vault: {e}")
            return False
    
    def _delete_secret_from_aws(self, key: str) -> bool:
        """Delete secret from AWS Secrets Manager."""
        try:
            self.aws_client.delete_secret(SecretId=key, ForceDeleteWithoutRecovery=True)
            return True
        except Exception as e:
            logger.error(f"Error deleting secret from AWS Secrets Manager: {e}")
            return False
    
    def list_secrets(self) -> list:
        """List all available secret keys."""
        try:
            if self.backend == "env":
                return list(os.environ.keys())
            elif self.backend == "file":
                return self._list_secrets_from_file()
            elif self.backend == "azure_kv":
                return self._list_secrets_from_azure()
            elif self.backend == "aws_sm":
                return self._list_secrets_from_aws()
            
            return []
            
        except Exception as e:
            logger.error(f"Error listing secrets: {e}")
            return []
    
    def _list_secrets_from_file(self) -> list:
        """List secrets from encrypted file."""
        try:
            if not self.secrets_file.exists():
                return []
            
            with open(self.secrets_file, "rb") as f:
                encrypted_data = f.read()
            decrypted_data = self.cipher.decrypt(encrypted_data)
            secrets = json.loads(decrypted_data.decode())
            
            return list(secrets.keys())
            
        except Exception as e:
            logger.error(f"Error listing secrets from file: {e}")
            return []
    
    def _list_secrets_from_azure(self) -> list:
        """List secrets from Azure Key Vault."""
        try:
            secrets = self.azure_client.list_properties_of_secrets()
            return [secret.name for secret in secrets]
        except Exception as e:
            logger.error(f"Error listing secrets from Azure Key Vault: {e}")
            return []
    
    def _list_secrets_from_aws(self) -> list:
        """List secrets from AWS Secrets Manager."""
        try:
            response = self.aws_client.list_secrets()
            return [secret["Name"] for secret in response["SecretList"]]
        except Exception as e:
            logger.error(f"Error listing secrets from AWS Secrets Manager: {e}")
            return []


# Global secret manager instance
_secret_manager: Optional[SecretManager] = None


def get_secret_manager() -> SecretManager:
    """Get the global secret manager instance."""
    global _secret_manager
    if _secret_manager is None:
        # Determine backend from environment
        backend = os.environ.get("SECRETS_BACKEND", "env").lower()
        
        # Backend-specific configuration
        config = {}
        if backend == "file":
            config = {
                "secrets_file": os.environ.get("SECRETS_FILE", "secrets.enc"),
                "key_file": os.environ.get("SECRETS_KEY_FILE", "secret.key")
            }
        elif backend == "azure_kv":
            config = {
                "vault_url": os.environ.get("AZURE_KEY_VAULT_URL")
            }
        elif backend == "aws_sm":
            config = {
                "region": os.environ.get("AWS_REGION", "us-east-1")
            }
        
        _secret_manager = SecretManager(backend=backend, **config)
    
    return _secret_manager


def get_secret(key: str, default: Optional[str] = None) -> Optional[str]:
    """Convenience function to get a secret."""
    return get_secret_manager().get_secret(key, default)


def set_secret(key: str, value: str) -> bool:
    """Convenience function to set a secret."""
    return get_secret_manager().set_secret(key, value)
