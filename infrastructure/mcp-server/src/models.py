"""
Data models for PKI MCP server
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class CAProvider(str, Enum):
    """CA Provider types"""
    VAULT = "vault"
    GLOBALSIGN = "globalsign"
    DIGICERT = "digicert"
    ENTRUST = "entrust"


class CertificateType(str, Enum):
    """Certificate types"""
    SSL = "ssl"
    CODE_SIGNING = "code_signing"
    EMAIL = "email"
    USER_AUTH = "user_auth"
    DEVICE = "device"


class CertificateStatus(str, Enum):
    """Certificate status"""
    PENDING = "pending"
    ISSUED = "issued"
    ACTIVE = "active"
    REVOKED = "revoked"
    EXPIRED = "expired"
    SUSPENDED = "suspended"


class CertificateRequest(BaseModel):
    """Certificate request model"""
    common_name: str = Field(..., description="Certificate common name")
    organization: Optional[str] = Field(None, description="Organization name")
    organizational_unit: Optional[str] = Field(None, description="Organizational unit")
    country: Optional[str] = Field(None, description="Country code")
    state: Optional[str] = Field(None, description="State or province")
    locality: Optional[str] = Field(None, description="Locality or city")
    
    alt_names: List[str] = Field(default_factory=list, description="Alternative names")
    ca_provider: CAProvider = Field(..., description="CA provider")
    certificate_type: CertificateType = Field(CertificateType.SSL, description="Certificate type")
    
    # Vault-specific fields
    ttl: Optional[str] = Field("8760h", description="TTL for Vault certificates")
    role: Optional[str] = Field("internal-role", description="Vault role")
    
    # Commercial CA fields
    validity_period: Optional[int] = Field(12, description="Validity period in months")
    validity_years: Optional[int] = Field(1, description="Validity period in years")
    csr: Optional[str] = Field(None, description="Certificate signing request")
    
    # Additional metadata
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class CertificateResponse(BaseModel):
    """Certificate response model"""
    certificate_id: Optional[str] = Field(None, description="Certificate ID")
    serial_number: Optional[str] = Field(None, description="Certificate serial number")
    common_name: str = Field(..., description="Certificate common name")
    organization: Optional[str] = Field(None, description="Organization name")
    
    certificate: Optional[str] = Field(None, description="Certificate in PEM format")
    private_key: Optional[str] = Field(None, description="Private key in PEM format")
    ca_chain: List[str] = Field(default_factory=list, description="CA certificate chain")
    
    ca_provider: CAProvider = Field(..., description="CA provider")
    certificate_type: CertificateType = Field(..., description="Certificate type")
    status: CertificateStatus = Field(..., description="Certificate status")
    
    issued_at: Optional[datetime] = Field(None, description="Issuance timestamp")
    expires_at: Optional[datetime] = Field(None, description="Expiration timestamp")
    revoked_at: Optional[datetime] = Field(None, description="Revocation timestamp")
    revocation_reason: Optional[str] = Field(None, description="Revocation reason")
    
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class RevocationRequest(BaseModel):
    """Certificate revocation request"""
    certificate_id: Optional[str] = Field(None, description="Certificate ID")
    serial_number: Optional[str] = Field(None, description="Certificate serial number")
    reason: str = Field("unspecified", description="Revocation reason")
    ca_provider: CAProvider = Field(..., description="CA provider")


class CertificateInventoryQuery(BaseModel):
    """Certificate inventory query parameters"""
    ca_provider: Optional[CAProvider] = Field(None, description="Filter by CA provider")
    status: Optional[CertificateStatus] = Field(None, description="Filter by status")
    organization: Optional[str] = Field(None, description="Filter by organization")
    common_name: Optional[str] = Field(None, description="Filter by common name")
    limit: int = Field(100, ge=1, le=1000, description="Number of records to return")
    offset: int = Field(0, ge=0, description="Number of records to skip")


class CertificateInventoryResponse(BaseModel):
    """Certificate inventory response"""
    certificates: List[CertificateResponse] = Field(..., description="List of certificates")
    total_count: int = Field(..., description="Total number of certificates")
    limit: int = Field(..., description="Limit used in query")
    offset: int = Field(..., description="Offset used in query")


class HealthCheckResponse(BaseModel):
    """Health check response"""
    status: str = Field(..., description="Overall health status")
    timestamp: datetime = Field(..., description="Health check timestamp")
    services: Dict[str, bool] = Field(..., description="Individual service health")
    version: str = Field("1.0.0", description="Server version")


class ErrorResponse(BaseModel):
    """Error response model"""
    error: str = Field(..., description="Error message")
    error_code: str = Field(..., description="Error code")
    timestamp: datetime = Field(..., description="Error timestamp")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")


class MCPToolInfo(BaseModel):
    """MCP tool information"""
    name: str = Field(..., description="Tool name")
    description: str = Field(..., description="Tool description")
    parameters: Dict[str, Any] = Field(..., description="Tool parameters")
    ca_provider: Optional[CAProvider] = Field(None, description="Associated CA provider")


class MCPToolsResponse(BaseModel):
    """MCP tools list response"""
    tools: List[MCPToolInfo] = Field(..., description="Available tools")
    total_count: int = Field(..., description="Total number of tools")
    server_info: Dict[str, Any] = Field(..., description="Server information")


class CertificateAnalysisRequest(BaseModel):
    """Certificate analysis request"""
    certificate_pem: str = Field(..., description="Certificate in PEM format")
    compliance_framework: str = Field("RFC3647", description="Compliance framework")
    check_revocation: bool = Field(True, description="Check revocation status")
    check_transparency: bool = Field(True, description="Check certificate transparency")


class CertificateAnalysisResponse(BaseModel):
    """Certificate analysis response"""
    certificate_id: Optional[str] = Field(None, description="Certificate identifier")
    common_name: str = Field(..., description="Certificate common name")
    issuer: str = Field(..., description="Certificate issuer")
    
    # Validity information
    valid_from: datetime = Field(..., description="Valid from timestamp")
    valid_to: datetime = Field(..., description="Valid to timestamp")
    is_expired: bool = Field(..., description="Whether certificate is expired")
    days_to_expiry: int = Field(..., description="Days until expiry")
    
    # Cryptographic information
    signature_algorithm: str = Field(..., description="Signature algorithm")
    public_key_algorithm: str = Field(..., description="Public key algorithm")
    key_size: int = Field(..., description="Key size in bits")
    
    # Extensions
    key_usage: List[str] = Field(default_factory=list, description="Key usage extensions")
    extended_key_usage: List[str] = Field(default_factory=list, description="Extended key usage")
    subject_alt_names: List[str] = Field(default_factory=list, description="Subject alternative names")
    
    # Compliance and security
    compliance_status: Dict[str, bool] = Field(default_factory=dict, description="Compliance check results")
    security_issues: List[str] = Field(default_factory=list, description="Security issues found")
    recommendations: List[str] = Field(default_factory=list, description="Security recommendations")
    
    # Revocation and transparency
    revocation_status: Optional[str] = Field(None, description="Revocation status")
    transparency_logs: List[str] = Field(default_factory=list, description="Certificate transparency logs")
    
    # Overall assessment
    risk_score: int = Field(..., ge=0, le=100, description="Risk score (0-100)")
    overall_status: str = Field(..., description="Overall certificate status")


class CAProviderConfig(BaseModel):
    """CA provider configuration"""
    provider_name: CAProvider = Field(..., description="CA provider name")
    is_active: bool = Field(True, description="Whether provider is active")
    api_endpoint: Optional[str] = Field(None, description="API endpoint URL")
    api_key: Optional[str] = Field(None, description="API key")
    api_secret: Optional[str] = Field(None, description="API secret")
    configuration: Dict[str, Any] = Field(default_factory=dict, description="Provider-specific configuration")
    created_at: datetime = Field(..., description="Configuration creation timestamp")
    updated_at: datetime = Field(..., description="Configuration update timestamp")


class CertificateOperation(BaseModel):
    """Certificate operation log entry"""
    id: int = Field(..., description="Operation ID")
    certificate_id: str = Field(..., description="Certificate ID")
    operation_type: str = Field(..., description="Operation type")
    operation_data: Dict[str, Any] = Field(..., description="Operation data")
    result: Dict[str, Any] = Field(..., description="Operation result")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    performed_at: datetime = Field(..., description="Operation timestamp")
    performed_by: str = Field(..., description="User who performed operation")


class CertificateOperationsResponse(BaseModel):
    """Certificate operations response"""
    operations: List[CertificateOperation] = Field(..., description="List of operations")
    certificate_id: str = Field(..., description="Certificate ID")
    total_count: int = Field(..., description="Total number of operations")
    limit: int = Field(..., description="Limit used in query")
    offset: int = Field(..., description="Offset used in query")
