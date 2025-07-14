"""
HashiCorp Vault PKI Client
Handles interactions with Vault PKI secrets engine
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional
import aiohttp
import hvac
from hvac.exceptions import VaultError
import structlog

logger = structlog.get_logger(__name__)


class VaultPKIClient:
    """Async client for HashiCorp Vault PKI operations"""
    
    def __init__(self, vault_url: str, vault_token: str):
        self.vault_url = vault_url
        self.vault_token = vault_token
        self.session = None
        self.client = None
        
    async def __aenter__(self):
        """Async context manager entry"""
        await self.connect()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.disconnect()
        
    async def connect(self):
        """Initialize connection to Vault"""
        try:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30)
            )
            
            # Initialize synchronous client for some operations
            self.client = hvac.Client(
                url=self.vault_url,
                token=self.vault_token
            )
            
            # Verify connection
            if not self.client.is_authenticated():
                raise VaultError("Failed to authenticate with Vault")
                
            logger.info("Connected to Vault PKI", vault_url=self.vault_url)
            
        except Exception as e:
            logger.error("Failed to connect to Vault", error=str(e))
            raise
            
    async def disconnect(self):
        """Close connection to Vault"""
        if self.session:
            await self.session.close()
            
    async def health_check(self) -> bool:
        """Check Vault health"""
        try:
            async with self.session.get(f"{self.vault_url}/v1/sys/health") as response:
                return response.status == 200
        except Exception:
            return False
            
    async def issue_certificate(
        self, 
        common_name: str, 
        alt_names: List[str] = None,
        ttl: str = "8760h",
        role: str = "internal-role"
    ) -> Dict[str, Any]:
        """
        Issue a certificate from Vault PKI
        
        Args:
            common_name: Certificate common name
            alt_names: List of alternative names
            ttl: Certificate time-to-live
            role: Vault role to use
            
        Returns:
            Certificate data including certificate, private key, and metadata
        """
        try:
            data = {
                "common_name": common_name,
                "ttl": ttl
            }
            
            if alt_names:
                data["alt_names"] = ",".join(alt_names)
                
            headers = {
                "X-Vault-Token": self.vault_token,
                "Content-Type": "application/json"
            }
            
            async with self.session.post(
                f"{self.vault_url}/v1/pki_int/issue/{role}",
                json=data,
                headers=headers
            ) as response:
                
                if response.status != 200:
                    error_text = await response.text()
                    raise VaultError(f"Failed to issue certificate: {error_text}")
                    
                result = await response.json()
                
                if "data" not in result:
                    raise VaultError("Invalid response format from Vault")
                    
                cert_data = result["data"]
                
                # Extract certificate details
                certificate_info = {
                    "certificate": cert_data.get("certificate"),
                    "private_key": cert_data.get("private_key"),
                    "ca_chain": cert_data.get("ca_chain", []),
                    "serial_number": cert_data.get("serial_number"),
                    "common_name": common_name,
                    "alt_names": alt_names or [],
                    "ttl": ttl,
                    "issued_at": cert_data.get("lease_id"),
                    "expiration": cert_data.get("lease_duration")
                }
                
                logger.info(
                    "Certificate issued successfully",
                    common_name=common_name,
                    serial_number=cert_data.get("serial_number")
                )
                
                return certificate_info
                
        except Exception as e:
            logger.error("Failed to issue certificate", error=str(e))
            raise
            
    async def revoke_certificate(self, serial_number: str) -> Dict[str, Any]:
        """
        Revoke a certificate in Vault PKI
        
        Args:
            serial_number: Certificate serial number
            
        Returns:
            Revocation result
        """
        try:
            data = {"serial_number": serial_number}
            
            headers = {
                "X-Vault-Token": self.vault_token,
                "Content-Type": "application/json"
            }
            
            async with self.session.post(
                f"{self.vault_url}/v1/pki_int/revoke",
                json=data,
                headers=headers
            ) as response:
                
                if response.status != 200:
                    error_text = await response.text()
                    raise VaultError(f"Failed to revoke certificate: {error_text}")
                    
                result = await response.json()
                
                logger.info(
                    "Certificate revoked successfully",
                    serial_number=serial_number
                )
                
                return {
                    "serial_number": serial_number,
                    "revocation_time": result.get("data", {}).get("revocation_time"),
                    "status": "revoked"
                }
                
        except Exception as e:
            logger.error("Failed to revoke certificate", error=str(e))
            raise
            
    async def get_certificate(self, serial_number: str) -> Dict[str, Any]:
        """
        Get certificate details from Vault PKI
        
        Args:
            serial_number: Certificate serial number
            
        Returns:
            Certificate details
        """
        try:
            headers = {
                "X-Vault-Token": self.vault_token
            }
            
            async with self.session.get(
                f"{self.vault_url}/v1/pki_int/cert/{serial_number}",
                headers=headers
            ) as response:
                
                if response.status == 404:
                    raise VaultError(f"Certificate not found: {serial_number}")
                elif response.status != 200:
                    error_text = await response.text()
                    raise VaultError(f"Failed to get certificate: {error_text}")
                    
                result = await response.json()
                
                return {
                    "serial_number": serial_number,
                    "certificate": result.get("data", {}).get("certificate"),
                    "status": "active"
                }
                
        except Exception as e:
            logger.error("Failed to get certificate", error=str(e))
            raise
            
    async def list_certificates(self) -> List[Dict[str, Any]]:
        """
        List all certificates in Vault PKI
        
        Returns:
            List of certificate serial numbers
        """
        try:
            headers = {
                "X-Vault-Token": self.vault_token
            }
            
            async with self.session.get(
                f"{self.vault_url}/v1/pki_int/certs",
                headers=headers,
                params={"list": "true"}
            ) as response:
                
                if response.status != 200:
                    error_text = await response.text()
                    raise VaultError(f"Failed to list certificates: {error_text}")
                    
                result = await response.json()
                
                serial_numbers = result.get("data", {}).get("keys", [])
                
                return [{"serial_number": sn} for sn in serial_numbers]
                
        except Exception as e:
            logger.error("Failed to list certificates", error=str(e))
            raise
            
    async def get_ca_certificate(self) -> str:
        """
        Get CA certificate from Vault PKI
        
        Returns:
            CA certificate in PEM format
        """
        try:
            async with self.session.get(
                f"{self.vault_url}/v1/pki_int/ca/pem"
            ) as response:
                
                if response.status != 200:
                    error_text = await response.text()
                    raise VaultError(f"Failed to get CA certificate: {error_text}")
                    
                ca_cert = await response.text()
                
                return ca_cert
                
        except Exception as e:
            logger.error("Failed to get CA certificate", error=str(e))
            raise
            
    async def get_crl(self) -> str:
        """
        Get Certificate Revocation List from Vault PKI
        
        Returns:
            CRL in PEM format
        """
        try:
            async with self.session.get(
                f"{self.vault_url}/v1/pki_int/crl/pem"
            ) as response:
                
                if response.status != 200:
                    error_text = await response.text()
                    raise VaultError(f"Failed to get CRL: {error_text}")
                    
                crl = await response.text()
                
                return crl
                
        except Exception as e:
            logger.error("Failed to get CRL", error=str(e))
            raise
