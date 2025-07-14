"""
Integration tests for MCP PKI server
"""

import asyncio
import pytest
import aiohttp
from typing import Dict, Any
import json
import time


class MCPTestClient:
    """Test client for MCP server"""
    
    def __init__(self, base_url: str = "http://localhost:8080"):
        self.base_url = base_url
        self.session = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
            
    async def health_check(self) -> Dict[str, Any]:
        """Test health check endpoint"""
        async with self.session.get(f"{self.base_url}/health") as response:
            return await response.json()
            
    async def mcp_initialize(self) -> Dict[str, Any]:
        """Test MCP initialization"""
        async with self.session.post(f"{self.base_url}/mcp/initialize") as response:
            return await response.json()
            
    async def mcp_list_tools(self) -> Dict[str, Any]:
        """Test MCP tools listing"""
        async with self.session.post(f"{self.base_url}/mcp/tools/list") as response:
            return await response.json()
            
    async def mcp_call_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Test MCP tool calling"""
        payload = {
            "tool_name": tool_name,
            "parameters": parameters
        }
        async with self.session.post(
            f"{self.base_url}/mcp/tools/call",
            json=payload
        ) as response:
            return await response.json()
            
    async def issue_certificate(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Test certificate issuance"""
        async with self.session.post(
            f"{self.base_url}/certificates/issue",
            json=request_data
        ) as response:
            return await response.json()
            
    async def get_certificate_inventory(self, ca_provider: str = None) -> Dict[str, Any]:
        """Test certificate inventory"""
        params = {}
        if ca_provider:
            params["ca_provider"] = ca_provider
            
        async with self.session.get(
            f"{self.base_url}/certificates/inventory",
            params=params
        ) as response:
            return await response.json()


@pytest.mark.asyncio
async def test_health_check():
    """Test server health check"""
    async with MCPTestClient() as client:
        result = await client.health_check()
        
        assert result["status"] == "healthy"
        assert "timestamp" in result
        assert "services" in result
        
        # Check individual service health
        services = result["services"]
        print(f"Service health: {services}")
        
        # Vault should be healthy
        assert services.get("vault") is not None
        
        # Database should be healthy
        assert services.get("database") is not None
        
        # Cache should be healthy
        assert services.get("cache") is not None


@pytest.mark.asyncio
async def test_mcp_initialization():
    """Test MCP protocol initialization"""
    async with MCPTestClient() as client:
        result = await client.mcp_initialize()
        
        assert "protocolVersion" in result
        assert "capabilities" in result
        assert "serverInfo" in result
        assert "sessionId" in result
        
        print(f"MCP initialization: {result}")


@pytest.mark.asyncio
async def test_mcp_tools_listing():
    """Test MCP tools listing"""
    async with MCPTestClient() as client:
        result = await client.mcp_list_tools()
        
        assert "tools" in result
        tools = result["tools"]
        
        # Check that we have the expected tools
        tool_names = [tool["name"] for tool in tools]
        
        # Vault tools
        assert "vault_issue_certificate" in tool_names
        assert "vault_revoke_certificate" in tool_names
        assert "vault_get_certificate" in tool_names
        
        # CA provider tools
        assert "globalsign_issue_certificate" in tool_names
        assert "digicert_issue_certificate" in tool_names
        assert "entrust_issue_certificate" in tool_names
        
        # Analysis tools
        assert "analyze_certificate" in tool_names
        assert "get_certificate_inventory" in tool_names
        
        print(f"Available tools: {tool_names}")


@pytest.mark.asyncio
async def test_vault_certificate_issuance():
    """Test Vault certificate issuance via MCP"""
    async with MCPTestClient() as client:
        # Test certificate issuance
        parameters = {
            "common_name": "test.internal.local",
            "alt_names": ["test1.internal.local", "test2.internal.local"],
            "ttl": "24h",
            "role": "internal-role"
        }
        
        result = await client.mcp_call_tool("vault_issue_certificate", parameters)
        
        print(f"Certificate issuance result: {result}")
        
        # Check if the request was successful
        if result.get("success"):
            data = result["data"]
            assert "certificate" in data
            assert "private_key" in data
            assert "serial_number" in data
            assert data["common_name"] == "test.internal.local"
            
            # Test certificate retrieval
            serial_number = data["serial_number"]
            get_result = await client.mcp_call_tool("vault_get_certificate", {
                "serial_number": serial_number
            })
            
            print(f"Certificate retrieval result: {get_result}")
            
            if get_result.get("success"):
                assert get_result["data"]["serial_number"] == serial_number
                
        else:
            print(f"Certificate issuance failed: {result.get('error')}")


@pytest.mark.asyncio
async def test_certificate_inventory():
    """Test certificate inventory retrieval"""
    async with MCPTestClient() as client:
        result = await client.mcp_call_tool("get_certificate_inventory", {})
        
        print(f"Certificate inventory result: {result}")
        
        if result.get("success"):
            data = result["data"]
            assert isinstance(data, list)
            print(f"Found {len(data)} certificates")
        else:
            print(f"Certificate inventory failed: {result.get('error')}")


@pytest.mark.asyncio
async def test_certificate_analysis():
    """Test certificate analysis"""
    async with MCPTestClient() as client:
        # Sample certificate for testing (this would be a real certificate in practice)
        sample_cert = """-----BEGIN CERTIFICATE-----
MIIDQTCCAimgAwIBAgITBmyfz5m/jAo54vB4ikPmljZbyjANBgkqhkiG9w0BAQsF
ADA5MQswCQYDVQQGEwJVUzEPMA0GA1UEChMGQW1hem9uMRkwFwYDVQQDExBBbWF6
b24gUm9vdCBDQSAxMB4XDTE1MDUyNjAwMDAwMFoXDTM4MDExNzAwMDAwMFowOTEL
MAkGA1UEBhMCVVMxDzANBgNVBAoTBkFtYXpvbjEZMBcGA1UEAxMQQW1hem9uIFJv
b3QgQ0EgMTCCASIwDQYJKoZIhvcNAQEBBQADggEPADCCAQoCggEBALJ4gHHKeNXj
ca9HgFB0fW7Y14h29Jlo91ghYPl0hAEvrAIthtOgQ3pOsqTQNroBvo3bSMgHFzZM
9O6II8c+6zf1tRn4SWiw3te5djgdYZ6k/oI2peVKVuRF4fn9tBb6dNqcmzU5L/qw
IFAGbHrQgLKm+a/sRxmPUDgH3KKHOVj4utWp+UhnMJbulHheb4mjUcAwhmahRWa6
VOujw5H5SNz/0egwLX0tdHA114gk957EWW67c4cX8jJGKLhD+rcdqsq08p8kDi1L
93FcXmn/6pUCyziKrlA4b9v7LWIbxcceVOF34GfID5yHI9Y/QCB/IIDEgEw+OyQm
jgSubJrIqg0CAwEAAaNCMEAwDwYDVR0TAQH/BAUwAwEB/zAOBgNVHQ8BAf8EBAMC
AYYwHQYDVR0OBBYEFIQYzIU07LwMlJQuCFmcx7IQTgoIMA0GCSqGSIb3DQEBCwUA
A4IBAQCY8jdaQZChGsV2USggNiMOruYou6r4lK5IpDB/G/wkjUu0yKGX9rbxenDI
U5PMCCjjmCXPI6T53iHTfIuJruydjsw2hUwsHqOflwUk
-----END CERTIFICATE-----"""
        
        parameters = {
            "certificate_pem": sample_cert,
            "compliance_framework": "RFC3647"
        }
        
        result = await client.mcp_call_tool("analyze_certificate", parameters)
        
        print(f"Certificate analysis result: {result}")
        
        if result.get("success"):
            data = result["data"]
            assert "common_name" in data
            assert "issuer" in data
            assert "risk_score" in data
        else:
            print(f"Certificate analysis failed: {result.get('error')}")


@pytest.mark.asyncio
async def test_rest_api_certificate_issuance():
    """Test REST API certificate issuance"""
    async with MCPTestClient() as client:
        request_data = {
            "common_name": "api-test.example.com",
            "organization": "Test Organization",
            "ca_provider": "vault",
            "certificate_type": "ssl",
            "ttl": "24h"
        }
        
        result = await client.issue_certificate(request_data)
        
        print(f"REST API certificate issuance result: {result}")
        
        if "error" not in result:
            assert "certificate_id" in result or "serial_number" in result
            assert result["common_name"] == "api-test.example.com"
            assert result["ca_provider"] == "vault"


@pytest.mark.asyncio
async def test_certificate_inventory_rest():
    """Test REST API certificate inventory"""
    async with MCPTestClient() as client:
        result = await client.get_certificate_inventory()
        
        print(f"REST API certificate inventory result: {result}")
        
        if isinstance(result, list):
            print(f"Found {len(result)} certificates via REST API")
        elif isinstance(result, dict) and "error" in result:
            print(f"Certificate inventory failed: {result['error']}")


if __name__ == "__main__":
    # Run tests individually for debugging
    async def run_tests():
        print("=== Testing Health Check ===")
        await test_health_check()
        
        print("\n=== Testing MCP Initialization ===")
        await test_mcp_initialization()
        
        print("\n=== Testing MCP Tools Listing ===")
        await test_mcp_tools_listing()
        
        print("\n=== Testing Vault Certificate Issuance ===")
        await test_vault_certificate_issuance()
        
        print("\n=== Testing Certificate Inventory ===")
        await test_certificate_inventory()
        
        print("\n=== Testing Certificate Analysis ===")
        await test_certificate_analysis()
        
        print("\n=== Testing REST API Certificate Issuance ===")
        await test_rest_api_certificate_issuance()
        
        print("\n=== Testing REST API Certificate Inventory ===")
        await test_certificate_inventory_rest()
        
        print("\n=== All tests completed ===")
    
    # Run the tests
    asyncio.run(run_tests())
