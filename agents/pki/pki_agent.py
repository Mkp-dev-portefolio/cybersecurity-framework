"""
PKI Agent with smolagents and MCP integration
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

from smolagents.tools import Tool
from ..base.agent import CybersecurityAgent, AgentConfig


class PKITool(Tool):
    """Base PKI tool"""
    
    def __init__(self, name: str, description: str, vault_client=None):
        super().__init__(name=name, description=description)
        self.vault_client = vault_client
        self.logger = logging.getLogger(__name__)


class CertificateIssueTool(PKITool):
    """Tool for issuing certificates"""
    
    def __init__(self, vault_client=None):
        super().__init__(
            name="issue_certificate",
            description="Issue a new certificate from PKI",
            vault_client=vault_client
        )
    
    async def forward(self, common_name: str, alt_names: Optional[List[str]] = None, ttl: str = "8760h") -> Dict[str, Any]:
        """Issue a certificate"""
        try:
            if self.vault_client:
                result = await self.vault_client.issue_certificate(
                    common_name=common_name,
                    alt_names=alt_names or [],
                    ttl=ttl
                )
                return {
                    "success": True,
                    "certificate": result.get("certificate"),
                    "serial_number": result.get("serial_number"),
                    "common_name": common_name,
                    "expires_at": result.get("expiration")
                }
            else:
                # Fallback to mock data for testing
                return {
                    "success": True,
                    "certificate": "-----BEGIN CERTIFICATE-----\nMOCK_CERT_DATA\n-----END CERTIFICATE-----",
                    "serial_number": "12345678",
                    "common_name": common_name,
                    "expires_at": "2025-01-01T00:00:00Z"
                }
        except Exception as e:
            self.logger.error(f"Certificate issuance failed: {str(e)}")
            return {"success": False, "error": str(e)}


class CertificateRevokeTool(PKITool):
    """Tool for revoking certificates"""
    
    def __init__(self, vault_client=None):
        super().__init__(
            name="revoke_certificate",
            description="Revoke a certificate",
            vault_client=vault_client
        )
    
    async def forward(self, serial_number: str, reason: str = "unspecified") -> Dict[str, Any]:
        """Revoke a certificate"""
        try:
            if self.vault_client:
                result = await self.vault_client.revoke_certificate(serial_number)
                return {
                    "success": True,
                    "serial_number": serial_number,
                    "revoked_at": datetime.now().isoformat(),
                    "reason": reason
                }
            else:
                # Fallback to mock data
                return {
                    "success": True,
                    "serial_number": serial_number,
                    "revoked_at": datetime.now().isoformat(),
                    "reason": reason
                }
        except Exception as e:
            self.logger.error(f"Certificate revocation failed: {str(e)}")
            return {"success": False, "error": str(e)}


class CertificateListTool(PKITool):
    """Tool for listing certificates"""
    
    def __init__(self, vault_client=None):
        super().__init__(
            name="list_certificates",
            description="List all certificates",
            vault_client=vault_client
        )
    
    async def forward(self, limit: int = 100) -> Dict[str, Any]:
        """List certificates"""
        try:
            # Mock data for now
            certificates = [
                {
                    "serial_number": "12345678",
                    "common_name": "example.com",
                    "status": "active",
                    "expires_at": "2025-01-01T00:00:00Z"
                },
                {
                    "serial_number": "87654321",
                    "common_name": "test.internal.local",
                    "status": "active",
                    "expires_at": "2025-06-01T00:00:00Z"
                }
            ]
            
            return {
                "success": True,
                "certificates": certificates[:limit],
                "count": len(certificates)
            }
        except Exception as e:
            self.logger.error(f"Certificate listing failed: {str(e)}")
            return {"success": False, "error": str(e)}


class PKIComplianceCheckTool(PKITool):
    """Tool for PKI compliance checking"""
    
    def __init__(self, vault_client=None):
        super().__init__(
            name="check_pki_compliance",
            description="Check PKI compliance status",
            vault_client=vault_client
        )
    
    async def forward(self, framework: str = "RFC3647") -> Dict[str, Any]:
        """Check PKI compliance"""
        try:
            # Mock compliance check
            compliance_results = {
                "framework": framework,
                "overall_score": 85,
                "checks": [
                    {"name": "Certificate Policy", "status": "pass", "score": 90},
                    {"name": "Key Management", "status": "pass", "score": 88},
                    {"name": "Certificate Lifecycle", "status": "warning", "score": 75},
                    {"name": "Audit Logging", "status": "pass", "score": 95}
                ],
                "recommendations": [
                    "Implement automated certificate renewal",
                    "Enhance key rotation procedures"
                ]
            }
            
            return {
                "success": True,
                "compliance": compliance_results,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            self.logger.error(f"PKI compliance check failed: {str(e)}")
            return {"success": False, "error": str(e)}


class PKIAgent(CybersecurityAgent):
    """PKI specialized agent"""
    
    def __init__(self, config: AgentConfig, vault_client=None):
        self.vault_client = vault_client
        super().__init__(config)
        self.logger = logging.getLogger(__name__)
    
    async def _get_domain_tools(self) -> List[Tool]:
        """Get PKI-specific tools"""
        return [
            CertificateIssueTool(self.vault_client),
            CertificateRevokeTool(self.vault_client),
            CertificateListTool(self.vault_client),
            PKIComplianceCheckTool(self.vault_client)
        ]
    
    async def issue_certificate(self, common_name: str, alt_names: Optional[List[str]] = None, ttl: str = "8760h") -> Dict[str, Any]:
        """Issue a certificate using the agent"""
        task = f"Issue a certificate for {common_name}"
        if alt_names:
            task += f" with alternative names: {', '.join(alt_names)}"
        
        context = {
            "common_name": common_name,
            "alt_names": alt_names,
            "ttl": ttl,
            "operation": "certificate_issue"
        }
        
        return await self.run_task(task, context)
    
    async def revoke_certificate(self, serial_number: str, reason: str = "unspecified") -> Dict[str, Any]:
        """Revoke a certificate using the agent"""
        task = f"Revoke certificate with serial number {serial_number} for reason: {reason}"
        
        context = {
            "serial_number": serial_number,
            "reason": reason,
            "operation": "certificate_revoke"
        }
        
        return await self.run_task(task, context)
    
    async def check_compliance(self, framework: str = "RFC3647") -> Dict[str, Any]:
        """Check PKI compliance using the agent"""
        task = f"Check PKI compliance against {framework} framework"
        
        context = {
            "framework": framework,
            "operation": "compliance_check"
        }
        
        return await self.run_task(task, context)
    
    async def get_certificate_inventory(self) -> Dict[str, Any]:
        """Get certificate inventory using the agent"""
        task = "Get comprehensive certificate inventory and status"
        
        context = {
            "operation": "certificate_inventory"
        }
        
        return await self.run_task(task, context)
    
    async def analyze_certificate_health(self) -> Dict[str, Any]:
        """Analyze certificate health using the agent"""
        task = "Analyze certificate health including expiration dates, revocation status, and compliance"
        
        context = {
            "operation": "certificate_health_analysis"
        }
        
        return await self.run_task(task, context)
