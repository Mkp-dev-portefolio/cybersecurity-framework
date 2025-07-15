// Header Component
function createHeader() {
    return `
        <h1>🔐 CyberSec PKI Management Dashboard</h1>
    `;
}

// Service Card Component
function createServiceCard(title, description, url, linkText, statusClass = 'status-unknown') {
    return `
        <div class="service-card">
            <h3><span class="status-indicator ${statusClass}"></span>${title}</h3>
            <p>${description}</p>
            <a href="${url}" class="btn" target="_blank">${linkText}</a>
        </div>
    `;
}

// Service Grid Component
function createServiceGrid() {
    const services = [
        {
            title: 'HashiCorp Vault',
            description: 'Certificate Authority and PKI Backend',
            url: 'http://localhost:8200',
            linkText: 'Open Vault UI'
        },
        {
            title: 'OCSP Server',
            description: 'Certificate Revocation Status Protocol',
            url: 'http://localhost:8888/health',
            linkText: 'Check Health'
        },
        {
            title: 'ACME Server',
            description: 'Automated Certificate Management',
            url: 'http://localhost:8889/health',
            linkText: 'Check Health'
        },
        {
            title: 'PKI Metrics',
            description: 'Prometheus Metrics Export',
            url: 'http://localhost:9100',
            linkText: 'View Metrics'
        }
    ];

    const serviceCards = services.map(service => 
        createServiceCard(service.title, service.description, service.url, service.linkText)
    ).join('');

    return `
        <div class="service-grid">
            ${serviceCards}
        </div>
    `;
}

// Commands Section Component
function createCommandsSection() {
    const commands = [
        {
            title: '1. Request a Certificate using ACME:',
            command: `curl -X POST http://localhost:8889/acme/new-order \\
  -H "Content-Type: application/jose+json" \\
  -d '{"identifiers": [{"type": "dns", "value": "example.com"}]}'`
        },
        {
            title: '2. Check Certificate Status via OCSP:',
            command: 'curl -X GET http://localhost:8888/ocsp/status/CERTIFICATE_SERIAL'
        },
        {
            title: '3. Vault PKI Certificate Request:',
            command: `curl -X POST http://localhost:8200/v1/pki/issue/cybersec-role \\
  -H "X-Vault-Token: cybersec-dev-token" \\
  -d '{"common_name": "test.cybersec.local", "ttl": "24h"}'`
        },
        {
            title: '4. Test Agent Integration:',
            command: 'python demo_agent_vault_integration.py'
        }
    ];

    const commandItems = commands.map(cmd => `
        <h4>${cmd.title}</h4>
        <div class="command-line">${cmd.command}</div>
    `).join('');

    return `
        <div class="commands">
            <h3>🚀 Quick Start Commands</h3>
            ${commandItems}
        </div>
    `;
}

// Footer Component
function createFooter() {
    return `
        <div class="footer">
            <p>🔒 CyberSecurity Framework with PKI, OCSP, and ACME Integration</p>
            <p>Built with HashiCorp Vault, Python, and Docker</p>
        </div>
    `;
}

// Main App Component
function createApp() {
    return `
        <div class="container">
            ${createHeader()}
            ${createServiceGrid()}
            ${createCommandsSection()}
            ${createFooter()}
        </div>
        ${createChatPanel()}
    `;
}

// Chat Panel Component
function createChatPanel() {
    return `
        <div class="chat-panel" id="chatPanel">
            <div class="chat-header">
                <div class="chat-title">
                    <span class="chat-icon">💬</span>
                    <span>AI Assistant</span>
                </div>
                <div class="chat-controls">
                    <button class="chat-minimize" id="chatMinimize" title="Minimize">
                        <span class="icon-minimize">−</span>
                    </button>
                    <button class="chat-close" id="chatClose" title="Close">
                        <span class="icon-close">×</span>
                    </button>
                </div>
            </div>
            <div class="chat-messages" id="chatMessages">
                <div class="message bot-message">
                    <span class="message-icon">🤖</span>
                    <div class="message-content">
                        <p>Hello! I'm your PKI Assistant. How can I help you manage your certificates today?</p>
                    </div>
                </div>
            </div>
            <div class="chat-input-container">
                <div class="chat-input-wrapper">
                    <input type="text" id="chatInput" placeholder="Type your message..." class="chat-input">
                    <button id="chatSend" class="chat-send-btn" title="Send message">
                        <span class="send-icon">➤</span>
                    </button>
                </div>
            </div>
        </div>
        
        <div class="chat-toggle" id="chatToggle" title="Open Chat">
            <span class="toggle-icon">💬</span>
        </div>
    `;
}

// Export components for use in main.js
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        createHeader,
        createServiceCard,
        createServiceGrid,
        createCommandsSection,
        createFooter,
        createApp,
        createChatPanel
    };
}
