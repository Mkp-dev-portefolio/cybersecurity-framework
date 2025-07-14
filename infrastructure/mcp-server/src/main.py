"""
Main entry point for the MCP PKI Server
"""

import asyncio
import logging
import os
import sys
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from src.mcp_protocol import MCPServer
from src.vault_client import VaultPKIClient
from src.database import Database
from src.cache import RedisCache
from src.ca_providers import GlobalSignProvider, DigiCertProvider, EntrustProvider
from src.models import (
    CertificateRequest,
    CertificateResponse,
    CertificateInventoryResponse,
    CertificateAnalysisResponse,
    HealthCheckResponse
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/app/logs/mcp_server.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="MCP PKI Server",
    description="Model Context Protocol server for PKI certificate management",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global instances
mcp_server: Optional[MCPServer] = None
vault_client: Optional[VaultPKIClient] = None
database: Optional[Database] = None
cache: Optional[RedisCache] = None
ca_providers: dict = {}


async def initialize_services():
    """Initialize all services"""
    global mcp_server, vault_client, database, cache, ca_providers
    
    try:
        # Initialize Vault client
        vault_addr = os.getenv("VAULT_ADDR", "http://vault:8200")
        vault_token = os.getenv("VAULT_TOKEN", "root")
        vault_client = VaultPKIClient(vault_addr, vault_token)
        
        # Initialize database
        postgres_url = os.getenv("POSTGRES_URL", "postgresql://mcp_user:mcp_password@postgres:5432/mcp_pki")
        database = Database(postgres_url)
        await database.connect()
        
        # Initialize cache
        redis_url = os.getenv("REDIS_URL", "redis://redis:6379")
        cache = RedisCache(redis_url)
        await cache.connect()
        
        # Initialize CA providers
        ca_providers = {
            "globalsign": GlobalSignProvider(
                api_key=os.getenv("GLOBALSIGN_API_KEY", "demo_key"),
                api_secret=os.getenv("GLOBALSIGN_API_SECRET", "demo_secret")
            ),
            "digicert": DigiCertProvider(
                api_key=os.getenv("DIGICERT_API_KEY", "demo_key")
            ),
            "entrust": EntrustProvider(
                api_key=os.getenv("ENTRUST_API_KEY", "demo_key"),
                api_secret=os.getenv("ENTRUST_API_SECRET", "demo_secret")
            )
        }
        
        # Initialize MCP server
        mcp_server = MCPServer(
            vault_client=vault_client,
            database=database,
            cache=cache,
            ca_providers=ca_providers
        )
        
        # Register MCP tools
        await mcp_server.register_tools()
        
        logger.info("All services initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize services: {e}")
        raise


async def shutdown_services():
    """Cleanup services"""
    global database, cache
    
    try:
        if database:
            await database.disconnect()
        if cache:
            await cache.disconnect()
        logger.info("Services shut down successfully")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")


@app.on_event("startup")
async def startup_event():
    """FastAPI startup event"""
    await initialize_services()


@app.on_event("shutdown")
async def shutdown_event():
    """FastAPI shutdown event"""
    await shutdown_services()


@app.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """Health check endpoint"""
    try:
        # Check Vault connection
        vault_healthy = await vault_client.health_check() if vault_client else False
        
        # Check database connection
        db_healthy = await database.health_check() if database else False
        
        # Check cache connection
        cache_healthy = await cache.health_check() if cache else False
        
        overall_healthy = vault_healthy and db_healthy and cache_healthy
        
        return HealthCheckResponse(
            status="healthy" if overall_healthy else "unhealthy",
            timestamp=datetime.now(),
            services={
                "vault": vault_healthy,
                "database": db_healthy,
                "cache": cache_healthy
            }
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return HealthCheckResponse(
            status="unhealthy",
            timestamp=datetime.now(),
            services={"vault": False, "database": False, "cache": False}
        )


@app.post("/mcp/tools/list")
async def list_tools():
    """List available MCP tools"""
    if not mcp_server:
        raise HTTPException(status_code=503, detail="MCP server not initialized")
    
    try:
        tools = await mcp_server.list_tools()
        return {"tools": tools}
    except Exception as e:
        logger.error(f"Failed to list tools: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/mcp/tools/call")
async def call_tool(request: dict):
    """Call an MCP tool"""
    if not mcp_server:
        raise HTTPException(status_code=503, detail="MCP server not initialized")
    
    try:
        result = await mcp_server.call_tool(
            name=request.get("name"),
            arguments=request.get("arguments", {})
        )
        return result
    except Exception as e:
        logger.error(f"Failed to call tool: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/certificates/issue", response_model=CertificateResponse)
async def issue_certificate(request: CertificateRequest):
    """Issue a new certificate"""
    if not mcp_server:
        raise HTTPException(status_code=503, detail="MCP server not initialized")
    
    try:
        result = await mcp_server.call_tool(
            name="issue_certificate",
            arguments=request.dict()
        )
        return result
    except Exception as e:
        logger.error(f"Failed to issue certificate: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/certificates/revoke")
async def revoke_certificate(request: dict):
    """Revoke a certificate"""
    if not mcp_server:
        raise HTTPException(status_code=503, detail="MCP server not initialized")
    
    try:
        result = await mcp_server.call_tool(
            name="revoke_certificate",
            arguments=request
        )
        return result
    except Exception as e:
        logger.error(f"Failed to revoke certificate: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/certificates/{certificate_id}")
async def get_certificate(certificate_id: str):
    """Get certificate details"""
    if not mcp_server:
        raise HTTPException(status_code=503, detail="MCP server not initialized")
    
    try:
        result = await mcp_server.call_tool(
            name="get_certificate",
            arguments={"certificate_id": certificate_id}
        )
        return result
    except Exception as e:
        logger.error(f"Failed to get certificate: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/certificates/inventory", response_model=CertificateInventoryResponse)
async def get_certificate_inventory():
    """Get certificate inventory"""
    if not mcp_server:
        raise HTTPException(status_code=503, detail="MCP server not initialized")
    
    try:
        result = await mcp_server.call_tool(
            name="get_certificate_inventory",
            arguments={}
        )
        return result
    except Exception as e:
        logger.error(f"Failed to get certificate inventory: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/certificates/analysis", response_model=CertificateAnalysisResponse)
async def get_certificate_analysis():
    """Get certificate analysis"""
    if not mcp_server:
        raise HTTPException(status_code=503, detail="MCP server not initialized")
    
    try:
        result = await mcp_server.call_tool(
            name="analyze_certificates",
            arguments={}
        )
        return result
    except Exception as e:
        logger.error(f"Failed to analyze certificates: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    logger.error(f"Global exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


if __name__ == "__main__":
    port = int(os.getenv("MCP_SERVER_PORT", "8080"))
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=port,
        reload=False,
        log_level="info"
    )
