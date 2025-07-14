# Cybersecurity Framework

A comprehensive cybersecurity framework built with AI agents, PKI infrastructure, and Model Context Protocol (MCP) integration.

## Features

- **AI-Powered Security Agents**: Intelligent agents for PKI management, vulnerability assessment, and security analysis
- **PKI Infrastructure**: Complete Public Key Infrastructure with certificate lifecycle management
- **MCP Integration**: Model Context Protocol server for seamless AI tool integration
- **Docker Deployment**: Containerized deployment with Docker Compose
- **Comprehensive Testing**: Integration tests for all components
- **Scalable Architecture**: Modular design supporting multiple security domains

## Architecture

The framework consists of several key components:

### Core Components

1. **AI Agents** (`agents/`)
   - Base agent framework with memory and tool registry
   - PKI-specific agent for certificate management
   - Extensible architecture for additional security domains

2. **Infrastructure** (`infrastructure/`)
   - MCP server for AI tool integration
   - PostgreSQL database for data persistence
   - Docker Compose orchestration
   - Vault integration for secrets management

3. **Compose for Agents** (`compose-for-agents/`)
   - Collection of pre-built agent frameworks
   - Support for multiple AI frameworks (LangGraph, CrewAI, etc.)
   - Ready-to-use agent templates

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.11+ (for development)
- Git

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/cybersecurity-framework.git
cd cybersecurity-framework
```

2. Set up the environment:
```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

3. Start the services:
```bash
# Start all services
docker-compose -f infrastructure/docker-compose.yml up -d

# Check service status
docker-compose -f infrastructure/docker-compose.yml ps
```

4. Run tests:
```bash
# Run integration tests
pytest tests/test_mcp_integration.py -v
```

## Usage

### PKI Agent

The PKI agent provides comprehensive certificate management capabilities:

```python
from agents.pki.pki_agent import PKIAgent

# Initialize the agent
agent = PKIAgent()

# Issue a certificate
cert_request = {
    "common_name": "example.com",
    "organization": "My Organization",
    "country": "US"
}

certificate = agent.issue_certificate(cert_request)
print(f"Certificate issued: {certificate['serial_number']}")
```

### MCP Server

The MCP server provides AI tools for security operations:

```bash
# Start the MCP server
cd infrastructure/mcp-server
python src/main.py

# The server will be available at http://localhost:8080
```

### Docker Deployment

Deploy the entire framework using Docker Compose:

```bash
# Deploy all services
docker-compose -f infrastructure/docker-compose.yml up -d

# Scale specific services
docker-compose -f infrastructure/docker-compose.yml up -d --scale mcp-server=3

# View logs
docker-compose -f infrastructure/docker-compose.yml logs -f mcp-server
```

## Development

### Project Structure

```
cybersecurity-framework/
├── agents/                 # AI agents
│   ├── base/              # Base agent framework
│   └── pki/               # PKI-specific agent
├── infrastructure/        # Core infrastructure
│   ├── docker-compose.yml # Service orchestration
│   ├── mcp-server/        # MCP server implementation
│   └── postgres/          # Database configuration
├── compose-for-agents/    # Agent frameworks collection
├── tests/                 # Integration tests
├── framework-structure.md # Architecture documentation
└── README.md             # This file
```

### Adding New Agents

1. Create a new agent directory under `agents/`
2. Implement the agent class inheriting from `BaseAgent`
3. Add tools and capabilities specific to your domain
4. Update the tool registry
5. Add tests for the new agent

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_mcp_integration.py -v

# Run with coverage
pytest tests/ --cov=agents --cov=infrastructure
```

## Configuration

### Environment Variables

Create a `.env` file in the root directory:

```env
# Database
POSTGRES_DB=cybersecurity_db
POSTGRES_USER=cyber_user
POSTGRES_PASSWORD=secure_password

# MCP Server
MCP_SERVER_PORT=8080
MCP_SERVER_HOST=0.0.0.0

# Vault (if using)
VAULT_ADDR=http://localhost:8200
VAULT_TOKEN=your_vault_token
```

### Service Configuration

Each service can be configured through environment variables or configuration files:

- **MCP Server**: `infrastructure/mcp-server/src/config.py`
- **Database**: `infrastructure/postgres/init.sql`
- **Agents**: Individual agent configuration files

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines

- Follow PEP 8 style guidelines
- Add tests for new features
- Update documentation for API changes
- Use type hints where appropriate
- Add docstrings for all functions and classes

## Security Considerations

- All sensitive data is encrypted at rest
- Certificate private keys are stored securely
- API endpoints are protected with authentication
- Regular security audits are performed
- Secrets are managed through environment variables

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For support and questions:

- Open an issue on GitHub
- Check the documentation in `framework-structure.md`
- Review the test cases for usage examples

## Roadmap

- [ ] Additional AI agent types (vulnerability scanning, compliance checking)
- [ ] Web UI for agent management
- [ ] Advanced analytics and reporting
- [ ] Integration with external security tools
- [ ] Multi-tenant support
- [ ] Enhanced monitoring and alerting

## Acknowledgments

- Built with Model Context Protocol (MCP)
- Uses Docker for containerization
- Leverages modern AI frameworks
- Incorporates security best practices
