"""
Database operations for certificate management
PostgreSQL async operations using asyncpg
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime
import asyncpg
import structlog

logger = structlog.get_logger(__name__)


class Database:
    """Database operations for PKI MCP server"""
    
    def __init__(self, postgres_url: str):
        self.postgres_url = postgres_url
        self.pool = None
        
    async def connect(self):
        """Initialize database connection pool"""
        try:
            self.pool = await asyncpg.create_pool(
                self.postgres_url,
                min_size=5,
                max_size=20,
                command_timeout=30
            )
            
            # Create tables if they don't exist
            await self._create_tables()
            
            logger.info("Database connected successfully")
            
        except Exception as e:
            logger.error("Failed to connect to database", error=str(e))
            raise
            
    async def disconnect(self):
        """Close database connection pool"""
        if self.pool:
            await self.pool.close()
            
    async def health_check(self) -> bool:
        """Check database health"""
        try:
            async with self.pool.acquire() as conn:
                await conn.execute("SELECT 1")
                return True
        except Exception:
            return False
            
    async def _create_tables(self):
        """Create database tables"""
        async with self.pool.acquire() as conn:
            # Certificates table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS certificates (
                    id SERIAL PRIMARY KEY,
                    certificate_id VARCHAR(255) UNIQUE,
                    serial_number VARCHAR(255),
                    common_name VARCHAR(255) NOT NULL,
                    organization VARCHAR(255),
                    organizational_unit VARCHAR(255),
                    ca_provider VARCHAR(50) NOT NULL,
                    certificate_type VARCHAR(50),
                    status VARCHAR(50) DEFAULT 'pending',
                    certificate_pem TEXT,
                    private_key_pem TEXT,
                    ca_chain TEXT[],
                    alt_names TEXT[],
                    validity_period INTEGER,
                    issued_at TIMESTAMP WITH TIME ZONE,
                    expires_at TIMESTAMP WITH TIME ZONE,
                    revoked_at TIMESTAMP WITH TIME ZONE,
                    revocation_reason VARCHAR(100),
                    metadata JSONB,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                );
            """)
            
            # Create indexes
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_certificates_serial_number 
                ON certificates(serial_number);
            """)
            
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_certificates_common_name 
                ON certificates(common_name);
            """)
            
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_certificates_ca_provider 
                ON certificates(ca_provider);
            """)
            
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_certificates_status 
                ON certificates(status);
            """)
            
            # Certificate operations log table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS certificate_operations (
                    id SERIAL PRIMARY KEY,
                    certificate_id VARCHAR(255),
                    operation_type VARCHAR(50) NOT NULL,
                    operation_data JSONB,
                    result JSONB,
                    error_message TEXT,
                    performed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    performed_by VARCHAR(255),
                    FOREIGN KEY (certificate_id) REFERENCES certificates(certificate_id)
                );
            """)
            
            # CA providers configuration table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS ca_providers (
                    id SERIAL PRIMARY KEY,
                    provider_name VARCHAR(50) UNIQUE NOT NULL,
                    provider_config JSONB,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                );
            """)
            
    async def store_certificate(
        self,
        provider: str,
        certificate_data: Dict[str, Any],
        metadata: Dict[str, Any] = None
    ) -> int:
        """
        Store certificate in database
        
        Args:
            provider: CA provider name
            certificate_data: Certificate data from CA
            metadata: Additional metadata
            
        Returns:
            Certificate database ID
        """
        try:
            async with self.pool.acquire() as conn:
                result = await conn.fetchrow("""
                    INSERT INTO certificates (
                        certificate_id, serial_number, common_name, organization,
                        organizational_unit, ca_provider, certificate_type, status,
                        certificate_pem, private_key_pem, ca_chain, alt_names,
                        validity_period, issued_at, expires_at, metadata
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16)
                    RETURNING id
                """, 
                    certificate_data.get("certificate_id"),
                    certificate_data.get("serial_number"),
                    certificate_data.get("common_name"),
                    certificate_data.get("organization"),
                    certificate_data.get("organizational_unit"),
                    provider,
                    certificate_data.get("certificate_type"),
                    certificate_data.get("status", "issued"),
                    certificate_data.get("certificate"),
                    certificate_data.get("private_key"),
                    certificate_data.get("ca_chain", []),
                    certificate_data.get("alt_names", []),
                    certificate_data.get("validity_period"),
                    self._parse_timestamp(certificate_data.get("issued_at")),
                    self._parse_timestamp(certificate_data.get("expires_at")),
                    json.dumps(metadata) if metadata else None
                )
                
                cert_id = result['id']
                
                # Log the operation
                await self._log_operation(
                    conn,
                    certificate_data.get("certificate_id"),
                    "issue",
                    certificate_data,
                    {"success": True}
                )
                
                logger.info(
                    "Certificate stored in database",
                    cert_id=cert_id,
                    provider=provider,
                    common_name=certificate_data.get("common_name")
                )
                
                return cert_id
                
        except Exception as e:
            logger.error("Failed to store certificate", error=str(e))
            raise
            
    async def update_certificate_status(
        self,
        certificate_id: str = None,
        serial_number: str = None,
        status: str = None,
        revocation_reason: str = None
    ) -> bool:
        """
        Update certificate status
        
        Args:
            certificate_id: Certificate ID
            serial_number: Certificate serial number
            status: New status
            revocation_reason: Revocation reason if applicable
            
        Returns:
            True if updated successfully
        """
        try:
            async with self.pool.acquire() as conn:
                if certificate_id:
                    where_clause = "certificate_id = $1"
                    where_value = certificate_id
                elif serial_number:
                    where_clause = "serial_number = $1"
                    where_value = serial_number
                else:
                    raise ValueError("Either certificate_id or serial_number must be provided")
                
                update_fields = ["status = $2", "updated_at = NOW()"]
                params = [where_value, status]
                
                if status == "revoked":
                    update_fields.append("revoked_at = NOW()")
                    if revocation_reason:
                        update_fields.append(f"revocation_reason = ${len(params) + 1}")
                        params.append(revocation_reason)
                
                query = f"""
                    UPDATE certificates 
                    SET {', '.join(update_fields)}
                    WHERE {where_clause}
                    RETURNING certificate_id
                """
                
                result = await conn.fetchrow(query, *params)
                
                if result:
                    # Log the operation
                    await self._log_operation(
                        conn,
                        result['certificate_id'],
                        "status_update",
                        {"status": status, "reason": revocation_reason},
                        {"success": True}
                    )
                    
                    logger.info(
                        "Certificate status updated",
                        certificate_id=result['certificate_id'],
                        status=status
                    )
                    
                    return True
                
                return False
                
        except Exception as e:
            logger.error("Failed to update certificate status", error=str(e))
            raise
            
    async def get_certificate_inventory(
        self,
        ca_provider: str = None,
        status: str = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get certificate inventory
        
        Args:
            ca_provider: Filter by CA provider
            status: Filter by status
            limit: Number of records to return
            offset: Number of records to skip
            
        Returns:
            List of certificate records
        """
        try:
            async with self.pool.acquire() as conn:
                where_conditions = []
                params = []
                
                if ca_provider:
                    where_conditions.append(f"ca_provider = ${len(params) + 1}")
                    params.append(ca_provider)
                    
                if status:
                    where_conditions.append(f"status = ${len(params) + 1}")
                    params.append(status)
                
                where_clause = ""
                if where_conditions:
                    where_clause = f"WHERE {' AND '.join(where_conditions)}"
                
                params.extend([limit, offset])
                
                query = f"""
                    SELECT 
                        certificate_id, serial_number, common_name, organization,
                        ca_provider, certificate_type, status, issued_at, expires_at,
                        revoked_at, revocation_reason, created_at, updated_at
                    FROM certificates
                    {where_clause}
                    ORDER BY created_at DESC
                    LIMIT ${len(params) - 1} OFFSET ${len(params)}
                """
                
                rows = await conn.fetch(query, *params)
                
                inventory = []
                for row in rows:
                    inventory.append({
                        "certificate_id": row['certificate_id'],
                        "serial_number": row['serial_number'],
                        "common_name": row['common_name'],
                        "organization": row['organization'],
                        "ca_provider": row['ca_provider'],
                        "certificate_type": row['certificate_type'],
                        "status": row['status'],
                        "issued_at": row['issued_at'].isoformat() if row['issued_at'] else None,
                        "expires_at": row['expires_at'].isoformat() if row['expires_at'] else None,
                        "revoked_at": row['revoked_at'].isoformat() if row['revoked_at'] else None,
                        "revocation_reason": row['revocation_reason'],
                        "created_at": row['created_at'].isoformat(),
                        "updated_at": row['updated_at'].isoformat()
                    })
                
                return inventory
                
        except Exception as e:
            logger.error("Failed to get certificate inventory", error=str(e))
            raise
            
    async def get_certificate_by_id(self, certificate_id: str) -> Optional[Dict[str, Any]]:
        """
        Get certificate by ID
        
        Args:
            certificate_id: Certificate ID
            
        Returns:
            Certificate record or None
        """
        try:
            async with self.pool.acquire() as conn:
                row = await conn.fetchrow("""
                    SELECT * FROM certificates WHERE certificate_id = $1
                """, certificate_id)
                
                if row:
                    return dict(row)
                
                return None
                
        except Exception as e:
            logger.error("Failed to get certificate by ID", error=str(e))
            raise
            
    async def get_certificate_operations(
        self,
        certificate_id: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get certificate operations log
        
        Args:
            certificate_id: Certificate ID
            limit: Number of records to return
            
        Returns:
            List of operation records
        """
        try:
            async with self.pool.acquire() as conn:
                rows = await conn.fetch("""
                    SELECT * FROM certificate_operations
                    WHERE certificate_id = $1
                    ORDER BY performed_at DESC
                    LIMIT $2
                """, certificate_id, limit)
                
                operations = []
                for row in rows:
                    operations.append({
                        "id": row['id'],
                        "operation_type": row['operation_type'],
                        "operation_data": row['operation_data'],
                        "result": row['result'],
                        "error_message": row['error_message'],
                        "performed_at": row['performed_at'].isoformat(),
                        "performed_by": row['performed_by']
                    })
                
                return operations
                
        except Exception as e:
            logger.error("Failed to get certificate operations", error=str(e))
            raise
            
    async def _log_operation(
        self,
        conn: asyncpg.Connection,
        certificate_id: str,
        operation_type: str,
        operation_data: Dict[str, Any],
        result: Dict[str, Any],
        error_message: str = None,
        performed_by: str = "system"
    ):
        """Log certificate operation"""
        try:
            await conn.execute("""
                INSERT INTO certificate_operations 
                (certificate_id, operation_type, operation_data, result, error_message, performed_by)
                VALUES ($1, $2, $3, $4, $5, $6)
            """, 
                certificate_id,
                operation_type,
                json.dumps(operation_data),
                json.dumps(result),
                error_message,
                performed_by
            )
            
        except Exception as e:
            logger.error("Failed to log operation", error=str(e))
            # Don't raise here as it's a logging operation
            
    def _parse_timestamp(self, timestamp_str: str) -> Optional[datetime]:
        """Parse timestamp string to datetime"""
        if not timestamp_str:
            return None
            
        try:
            # Try ISO format first
            return datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        except ValueError:
            try:
                # Try other common formats
                return datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
            except ValueError:
                logger.warning(f"Failed to parse timestamp: {timestamp_str}")
                return None
