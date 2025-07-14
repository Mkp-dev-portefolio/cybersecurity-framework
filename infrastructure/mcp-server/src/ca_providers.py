"""
Commercial CA Providers
Integrations with GlobalSign, DigiCert, and Entrust APIs
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional
from abc import ABC, abstractmethod
import aiohttp
from datetime import datetime, timedelta
import structlog

logger = structlog.get_logger(__name__)


class CAProvider(ABC):
    """Abstract base class for CA providers"""
    
    def __init__(self, name: str):
        self.name = name
        self.session = None
        
    async def __aenter__(self):
        """Async context manager entry"""
        await self.connect()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.disconnect()
        
    async def connect(self):
        """Initialize connection"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=60)
        )
        
    async def disconnect(self):
        """Close connection"""
        if self.session:
            await self.session.close()
            
    @abstractmethod
    async def issue_certificate(self, **kwargs) -> Dict[str, Any]:
        """Issue a certificate"""
        pass
        
    @abstractmethod
    async def revoke_certificate(self, **kwargs) -> Dict[str, Any]:
        """Revoke a certificate"""
        pass
        
    @abstractmethod
    async def get_certificate(self, **kwargs) -> Dict[str, Any]:
        """Get certificate details"""
        pass


class GlobalSignProvider(CAProvider):
    """GlobalSign CA provider"""
    
    def __init__(self, api_key: str, api_secret: str):
        super().__init__("GlobalSign")
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = "https://emea.api.globalsign.com"
        
    async def issue_certificate(
        self,
        common_name: str,
        certificate_type: str = "SSL",
        validity_period: int = 12,
        organization: str = None,
        organizational_unit: str = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Issue certificate from GlobalSign
        
        Args:
            common_name: Certificate common name
            certificate_type: Type of certificate (SSL, OV, EV)
            validity_period: Validity period in months
            organization: Organization name
            organizational_unit: Organizational unit
            
        Returns:
            Certificate data
        """
        try:
            # Generate CSR (simplified for demo)
            csr = await self._generate_csr(common_name, organization, organizational_unit)
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "certificate_type": certificate_type,
                "common_name": common_name,
                "validity_period": validity_period,
                "csr": csr,
                "organization": organization,
                "organizational_unit": organizational_unit
            }
            
            async with self.session.post(
                f"{self.base_url}/v2/certificates",
                json=data,
                headers=headers
            ) as response:
                
                if response.status != 201:
                    error_text = await response.text()
                    raise Exception(f"GlobalSign API error: {error_text}")
                    
                result = await response.json()
                
                certificate_info = {
                    "certificate_id": result.get("id"),
                    "certificate": result.get("certificate"),
                    "common_name": common_name,
                    "organization": organization,
                    "validity_period": validity_period,
                    "status": "issued",
                    "ca_provider": "globalsign",
                    "issued_at": datetime.utcnow().isoformat(),
                    "expires_at": (datetime.utcnow() + timedelta(days=validity_period * 30)).isoformat()
                }
                
                logger.info(
                    "Certificate issued from GlobalSign",
                    common_name=common_name,
                    certificate_id=result.get("id")
                )
                
                return certificate_info
                
        except Exception as e:
            logger.error("Failed to issue certificate from GlobalSign", error=str(e))
            raise
            
    async def revoke_certificate(
        self,
        certificate_id: str,
        reason: str = "unspecified",
        **kwargs
    ) -> Dict[str, Any]:
        """
        Revoke certificate from GlobalSign
        
        Args:
            certificate_id: Certificate ID
            reason: Revocation reason
            
        Returns:
            Revocation result
        """
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "reason": reason
            }
            
            async with self.session.post(
                f"{self.base_url}/v2/certificates/{certificate_id}/revoke",
                json=data,
                headers=headers
            ) as response:
                
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"GlobalSign API error: {error_text}")
                    
                result = await response.json()
                
                logger.info(
                    "Certificate revoked from GlobalSign",
                    certificate_id=certificate_id
                )
                
                return {
                    "certificate_id": certificate_id,
                    "status": "revoked",
                    "reason": reason,
                    "revoked_at": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error("Failed to revoke certificate from GlobalSign", error=str(e))
            raise
            
    async def get_certificate(
        self,
        certificate_id: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Get certificate details from GlobalSign
        
        Args:
            certificate_id: Certificate ID
            
        Returns:
            Certificate details
        """
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}"
            }
            
            async with self.session.get(
                f"{self.base_url}/v2/certificates/{certificate_id}",
                headers=headers
            ) as response:
                
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"GlobalSign API error: {error_text}")
                    
                result = await response.json()
                
                return {
                    "certificate_id": certificate_id,
                    "certificate": result.get("certificate"),
                    "status": result.get("status"),
                    "common_name": result.get("common_name"),
                    "organization": result.get("organization"),
                    "ca_provider": "globalsign"
                }
                
        except Exception as e:
            logger.error("Failed to get certificate from GlobalSign", error=str(e))
            raise
            
    async def _generate_csr(self, common_name: str, organization: str, organizational_unit: str) -> str:
        """Generate CSR for certificate request (simplified)"""
        # In a real implementation, this would generate a proper CSR
        # For demo purposes, returning a mock CSR
        return f"""-----BEGIN CERTIFICATE REQUEST-----
MIICvjCCAaYCAQAweTELMAkGA1UEBhMCVVMxCzAJBgNVBAgMAkNBMRYwFAYDVQQH
DA1TYW4gRnJhbmNpc2NvMRkwFwYDVQQKDBB{organization or 'Example'}1EzARBgNVBAsM
Cg{organizational_unit or 'IT'}xGTAXBgNVBAMMEG{common_name}1BDBOBgkqhkiG9w0BAQEF
AAOCAg8AMIICCgKCAgEAuKsOVe0L6eOZPCbkpGPWfxO6+8QvGBaJHPxFWPKMlQ5z
-----END CERTIFICATE REQUEST-----"""


class DigiCertProvider(CAProvider):
    """DigiCert CA provider"""
    
    def __init__(self, api_key: str):
        super().__init__("DigiCert")
        self.api_key = api_key
        self.base_url = "https://www.digicert.com/services/v2"
        
    async def issue_certificate(
        self,
        common_name: str,
        certificate_type: str = "ssl_plus",
        validity_years: int = 1,
        organization: str = None,
        csr: str = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Issue certificate from DigiCert
        
        Args:
            common_name: Certificate common name
            certificate_type: Type of certificate
            validity_years: Validity period in years
            organization: Organization name
            csr: Certificate signing request
            
        Returns:
            Certificate data
        """
        try:
            if not csr:
                csr = await self._generate_csr(common_name, organization)
                
            headers = {
                "X-DC-DEVKEY": self.api_key,
                "Content-Type": "application/json"
            }
            
            data = {
                "certificate": {
                    "common_name": common_name,
                    "csr": csr,
                    "signature_hash": "sha256"
                },
                "organization": {
                    "name": organization or "Example Organization"
                },
                "validity_years": validity_years,
                "product": {
                    "name_id": certificate_type
                }
            }
            
            async with self.session.post(
                f"{self.base_url}/order/certificate/{certificate_type}",
                json=data,
                headers=headers
            ) as response:
                
                if response.status != 201:
                    error_text = await response.text()
                    raise Exception(f"DigiCert API error: {error_text}")
                    
                result = await response.json()
                
                certificate_info = {
                    "certificate_id": result.get("id"),
                    "order_id": result.get("id"),
                    "certificate": result.get("certificate"),
                    "common_name": common_name,
                    "organization": organization,
                    "validity_years": validity_years,
                    "status": "pending",
                    "ca_provider": "digicert",
                    "issued_at": datetime.utcnow().isoformat()
                }
                
                logger.info(
                    "Certificate order placed with DigiCert",
                    common_name=common_name,
                    order_id=result.get("id")
                )
                
                return certificate_info
                
        except Exception as e:
            logger.error("Failed to issue certificate from DigiCert", error=str(e))
            raise
            
    async def revoke_certificate(
        self,
        certificate_id: str,
        reason: str = "unspecified",
        **kwargs
    ) -> Dict[str, Any]:
        """
        Revoke certificate from DigiCert
        
        Args:
            certificate_id: Certificate ID
            reason: Revocation reason
            
        Returns:
            Revocation result
        """
        try:
            headers = {
                "X-DC-DEVKEY": self.api_key,
                "Content-Type": "application/json"
            }
            
            data = {
                "reason": reason
            }
            
            async with self.session.put(
                f"{self.base_url}/certificate/{certificate_id}/revoke",
                json=data,
                headers=headers
            ) as response:
                
                if response.status != 204:
                    error_text = await response.text()
                    raise Exception(f"DigiCert API error: {error_text}")
                    
                logger.info(
                    "Certificate revoked from DigiCert",
                    certificate_id=certificate_id
                )
                
                return {
                    "certificate_id": certificate_id,
                    "status": "revoked",
                    "reason": reason,
                    "revoked_at": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error("Failed to revoke certificate from DigiCert", error=str(e))
            raise
            
    async def get_certificate(
        self,
        certificate_id: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Get certificate details from DigiCert
        
        Args:
            certificate_id: Certificate ID
            
        Returns:
            Certificate details
        """
        try:
            headers = {
                "X-DC-DEVKEY": self.api_key
            }
            
            async with self.session.get(
                f"{self.base_url}/certificate/{certificate_id}",
                headers=headers
            ) as response:
                
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"DigiCert API error: {error_text}")
                    
                result = await response.json()
                
                return {
                    "certificate_id": certificate_id,
                    "certificate": result.get("certificate"),
                    "status": result.get("status"),
                    "common_name": result.get("common_name"),
                    "organization": result.get("organization", {}).get("name"),
                    "ca_provider": "digicert"
                }
                
        except Exception as e:
            logger.error("Failed to get certificate from DigiCert", error=str(e))
            raise
            
    async def _generate_csr(self, common_name: str, organization: str) -> str:
        """Generate CSR for certificate request (simplified)"""
        # In a real implementation, this would generate a proper CSR
        return f"""-----BEGIN CERTIFICATE REQUEST-----
MIICvjCCAaYCAQAweTELMAkGA1UEBhMCVVMxCzAJBgNVBAgMAkNBMRYwFAYDVQQH
DA1TYW4gRnJhbmNpc2NvMRkwFwYDVQQKDBB{organization or 'Example'}1EzARBgNVBAsM
Cg{common_name}1BDBOBgkqhkiG9w0BAQEF
-----END CERTIFICATE REQUEST-----"""


class EntrustProvider(CAProvider):
    """Entrust CA provider"""
    
    def __init__(self, api_key: str, api_secret: str):
        super().__init__("Entrust")
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = "https://cloud.entrust.net/EntrustCertificateServices"
        
    async def issue_certificate(
        self,
        common_name: str,
        certificate_type: str = "STANDARD_SSL",
        validity_period: int = 12,
        organization: str = None,
        csr: str = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Issue certificate from Entrust
        
        Args:
            common_name: Certificate common name
            certificate_type: Type of certificate
            validity_period: Validity period in months
            organization: Organization name
            csr: Certificate signing request
            
        Returns:
            Certificate data
        """
        try:
            if not csr:
                csr = await self._generate_csr(common_name, organization)
                
            headers = {
                "X-API-Key": self.api_key,
                "Content-Type": "application/json"
            }
            
            data = {
                "certificateType": certificate_type,
                "csr": csr,
                "validityPeriod": validity_period,
                "organization": organization or "Example Organization",
                "commonName": common_name
            }
            
            async with self.session.post(
                f"{self.base_url}/api/client/v2/certificates",
                json=data,
                headers=headers
            ) as response:
                
                if response.status != 201:
                    error_text = await response.text()
                    raise Exception(f"Entrust API error: {error_text}")
                    
                result = await response.json()
                
                certificate_info = {
                    "certificate_id": result.get("trackingId"),
                    "certificate": result.get("certificate"),
                    "common_name": common_name,
                    "organization": organization,
                    "validity_period": validity_period,
                    "status": "pending",
                    "ca_provider": "entrust",
                    "issued_at": datetime.utcnow().isoformat()
                }
                
                logger.info(
                    "Certificate request submitted to Entrust",
                    common_name=common_name,
                    tracking_id=result.get("trackingId")
                )
                
                return certificate_info
                
        except Exception as e:
            logger.error("Failed to issue certificate from Entrust", error=str(e))
            raise
            
    async def revoke_certificate(
        self,
        certificate_id: str,
        reason: str = "unspecified",
        **kwargs
    ) -> Dict[str, Any]:
        """
        Revoke certificate from Entrust
        
        Args:
            certificate_id: Certificate ID
            reason: Revocation reason
            
        Returns:
            Revocation result
        """
        try:
            headers = {
                "X-API-Key": self.api_key,
                "Content-Type": "application/json"
            }
            
            data = {
                "reason": reason
            }
            
            async with self.session.post(
                f"{self.base_url}/api/client/v2/certificates/{certificate_id}/revoke",
                json=data,
                headers=headers
            ) as response:
                
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"Entrust API error: {error_text}")
                    
                logger.info(
                    "Certificate revoked from Entrust",
                    certificate_id=certificate_id
                )
                
                return {
                    "certificate_id": certificate_id,
                    "status": "revoked",
                    "reason": reason,
                    "revoked_at": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error("Failed to revoke certificate from Entrust", error=str(e))
            raise
            
    async def get_certificate(
        self,
        certificate_id: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Get certificate details from Entrust
        
        Args:
            certificate_id: Certificate ID
            
        Returns:
            Certificate details
        """
        try:
            headers = {
                "X-API-Key": self.api_key
            }
            
            async with self.session.get(
                f"{self.base_url}/api/client/v2/certificates/{certificate_id}",
                headers=headers
            ) as response:
                
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"Entrust API error: {error_text}")
                    
                result = await response.json()
                
                return {
                    "certificate_id": certificate_id,
                    "certificate": result.get("certificate"),
                    "status": result.get("status"),
                    "common_name": result.get("commonName"),
                    "organization": result.get("organization"),
                    "ca_provider": "entrust"
                }
                
        except Exception as e:
            logger.error("Failed to get certificate from Entrust", error=str(e))
            raise
            
    async def _generate_csr(self, common_name: str, organization: str) -> str:
        """Generate CSR for certificate request (simplified)"""
        # In a real implementation, this would generate a proper CSR
        return f"""-----BEGIN CERTIFICATE REQUEST-----
MIICvjCCAaYCAQAweTELMAkGA1UEBhMCVVMxCzAJBgNVBAgMAkNBMRYwFAYDVQQH
DA1TYW4gRnJhbmNpc2NvMRkwFwYDVQQKDBB{organization or 'Example'}1EzARBgNVBAsM
Cg{common_name}1BDBOBgkqhkiG9w0BAQEF
-----END CERTIFICATE REQUEST-----"""
