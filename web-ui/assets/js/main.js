// Enhanced service status check with better CORS handling
async function checkServiceStatus(url, indicator) {
    try {
        // First try with CORS enabled to get actual response
        const response = await fetch(url, {
            method: 'GET',
            mode: 'cors',
            headers: {
                'Accept': 'application/json, */*'
            },
            // Add timeout to prevent hanging
            signal: AbortSignal.timeout(5000)
        });
        
        // Check if response is OK (200-299 status codes)
        if (response.ok) {
            indicator.className = 'status-indicator status-online';
            indicator.title = `Service online (${response.status})`;
        } else {
            indicator.className = 'status-indicator status-offline';
            indicator.title = `Service offline (${response.status})`;
        }
    } catch (error) {
        // If CORS fails, try a fallback approach
        if (error.name === 'TypeError' && error.message.includes('CORS')) {
            // CORS error - try alternative approach
            await checkServiceStatusFallback(url, indicator);
        } else {
            // Network error or timeout
            indicator.className = 'status-indicator status-offline';
            indicator.title = `Service unavailable (${error.message})`;
        }
    }
}

// Fallback method for CORS-restricted services
async function checkServiceStatusFallback(url, indicator) {
    try {
        // Use no-cors mode as fallback, but with better error handling
        const response = await fetch(url, {
            method: 'GET',
            mode: 'no-cors',
            signal: AbortSignal.timeout(5000)
        });
        
        // With no-cors, we can't read the response, but if we get here without error,
        // it means the request was sent successfully
        indicator.className = 'status-indicator status-online';
        indicator.title = 'Service appears online (CORS restricted)';
    } catch (error) {
        indicator.className = 'status-indicator status-offline';
        indicator.title = `Service unavailable (${error.name})`;
    }
}

// Alternative: Use a lightweight proxy approach for better status checking
async function checkServiceStatusViaProxy(url, indicator) {
    try {
        // If we had a proxy endpoint, we could use it like this:
        // const proxyUrl = `/api/proxy/health-check?url=${encodeURIComponent(url)}`;
        // const response = await fetch(proxyUrl);
        
        // For now, we'll use the direct approach
        await checkServiceStatus(url, indicator);
    } catch (error) {
        indicator.className = 'status-indicator status-offline';
        indicator.title = `Proxy check failed: ${error.message}`;
    }
}

// Initialize the application
function initializeApp() {
    // Render the entire app using components
    document.body.innerHTML = createApp();
    
    // Check service status after rendering
    checkAllServiceStatus();
    
    // Initialize chat functionality
    initializeChat();
}

// Check all service status
function checkAllServiceStatus() {
    const indicators = document.querySelectorAll('.status-indicator');
    const urls = [
        'http://localhost:8200/v1/sys/health',
        'http://localhost:8888/health',
        'http://localhost:8889/health',
        'http://localhost:9100'
    ];
    
    indicators.forEach((indicator, index) => {
        setTimeout(() => {
            checkServiceStatus(urls[index], indicator);
        }, index * 500);
    });
}

// Chat functionality
function initializeChat() {
    const chatPanel = document.getElementById('chatPanel');
    const chatToggle = document.getElementById('chatToggle');
    const chatClose = document.getElementById('chatClose');
    const chatMinimize = document.getElementById('chatMinimize');
    const chatSend = document.getElementById('chatSend');
    const chatInput = document.getElementById('chatInput');
    const chatMessages = document.getElementById('chatMessages');
    
    // Initially hide chat panel
    chatPanel.style.display = 'none';
    
    // Toggle chat panel
    chatToggle.addEventListener('click', () => {
        chatPanel.style.display = chatPanel.style.display === 'none' ? 'flex' : 'none';
        if (chatPanel.style.display === 'flex') {
            chatInput.focus();
        }
    });
    
    // Close chat panel
    chatClose.addEventListener('click', () => {
        chatPanel.style.display = 'none';
    });
    
    // Minimize chat panel
    chatMinimize.addEventListener('click', () => {
        chatPanel.classList.toggle('minimized');
    });
    
    // Render bubble for messages
    function appendMessage(author, text) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${author.toLowerCase() === 'you' ? 'user' : 'bot'}-message`;
        
        const icon = author.toLowerCase() === 'you' ? '👤' : '🤖';
        messageDiv.innerHTML = `
            <span class="message-icon">${icon}</span>
            <div class="message-content">
                <p>${text}</p>
            </div>
        `;
        
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
    
    // Send message
    async function sendMessage() {
        const userText = chatInput.value.trim();
        if (userText) {
            appendMessage('You', userText);
            chatInput.value = '';
            
            // Show typing indicator
            addTypingIndicator();
            
            try {
                const res = await fetch('/agent/chat', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ text: userText })
                });
                
                if (res.ok) {
                    const { reply } = await res.json();
                    removeTypingIndicator();
                    appendMessage('Agent', reply);
                } else {
                    // Use fallback response
                    removeTypingIndicator();
                    setTimeout(() => {
                        const botResponse = generateBotResponse(userText);
                        appendMessage('Agent', botResponse);
                    }, 1000);
                }
            } catch (error) {
                console.error('Error sending message:', error);
                // Use fallback response
                removeTypingIndicator();
                setTimeout(() => {
                    const botResponse = generateBotResponse(userText);
                    appendMessage('Agent', botResponse);
                }, 1000);
            }
        }
    }
    
    // Add message to chat
    function addMessage(message, sender) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}-message`;
        
        const icon = sender === 'user' ? '👤' : '🤖';
        messageDiv.innerHTML = `
            <span class="message-icon">${icon}</span>
            <div class="message-content">
                <p>${message}</p>
            </div>
        `;
        
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
    
    // Generate bot response
    function generateBotResponse(userMessage) {
        const lowerMessage = userMessage.toLowerCase();
        
        if (lowerMessage.includes('certificate') || lowerMessage.includes('cert')) {
            return 'I can help you with certificate management! You can request certificates using ACME, check their status via OCSP, or manage them through HashiCorp Vault. What specific task would you like to accomplish?';
        } else if (lowerMessage.includes('vault')) {
            return 'HashiCorp Vault is our PKI backend. You can access it at http://localhost:8200. Use the cybersec-dev-token for authentication. Would you like help with a specific Vault operation?';
        } else if (lowerMessage.includes('ocsp')) {
            return 'OCSP (Online Certificate Status Protocol) helps check certificate revocation status. The OCSP server is running on port 8888. You can check a certificate status using the /ocsp/status endpoint.';
        } else if (lowerMessage.includes('acme')) {
            return 'ACME (Automated Certificate Management Environment) automates certificate issuance and renewal. The ACME server is running on port 8889. You can create new orders at the /acme/new-order endpoint.';
        } else if (lowerMessage.includes('test') || lowerMessage.includes('demo')) {
            testCertificateRequest();
            return 'Running certificate request test... Check the console for results!';
        } else if (lowerMessage.includes('help') || lowerMessage.includes('commands')) {
            return 'Here are some things I can help you with:\n• Certificate management and issuance\n• ACME protocol operations\n• OCSP status checking\n• HashiCorp Vault PKI operations\n• Troubleshooting PKI services\n• Type "test" to run a certificate request demo\n\nWhat would you like to know more about?';
        } else {
            return 'I\'m here to help with PKI and certificate management tasks. You can ask me about certificates, ACME, OCSP, or Vault operations. How can I assist you today?';
        }
    }
    
    // Test certificate request functionality
    async function testCertificateRequest() {
        console.log('Testing certificate request functionality...');
        
        // Test Vault PKI endpoint
        try {
            const vaultResponse = await fetch('http://localhost:8200/v1/pki/issue/cybersec-role', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Vault-Token': 'cybersec-dev-token'
                },
                body: JSON.stringify({
                    common_name: 'test.cybersec.local',
                    ttl: '24h'
                })
            });
            
            if (vaultResponse.ok) {
                const vaultData = await vaultResponse.json();
                console.log('✅ Vault certificate request successful:', vaultData);
                appendMessage('Agent', '✅ Vault certificate request successful! Check console for details.');
            } else {
                console.log('❌ Vault certificate request failed:', vaultResponse.status);
                appendMessage('Agent', '❌ Vault certificate request failed. Make sure Vault is running and configured.');
            }
        } catch (error) {
            console.log('❌ Vault connection error:', error);
            appendMessage('Agent', '❌ Could not connect to Vault. Make sure it\'s running on port 8200.');
        }
        
        // Test ACME endpoint
        try {
            const acmeResponse = await fetch('http://localhost:8889/acme/new-order', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/jose+json'
                },
                body: JSON.stringify({
                    identifiers: [{
                        type: 'dns',
                        value: 'example.com'
                    }]
                })
            });
            
            if (acmeResponse.ok) {
                const acmeData = await acmeResponse.json();
                console.log('✅ ACME certificate request successful:', acmeData);
                appendMessage('Agent', '✅ ACME certificate request successful! Check console for details.');
            } else {
                console.log('❌ ACME certificate request failed:', acmeResponse.status);
                appendMessage('Agent', '❌ ACME certificate request failed. Make sure ACME server is running.');
            }
        } catch (error) {
            console.log('❌ ACME connection error:', error);
            appendMessage('Agent', '❌ Could not connect to ACME server. Make sure it\'s running on port 8889.');
        }
    }
    
    // Add typing indicator
    function addTypingIndicator() {
        const typingDiv = document.createElement('div');
        typingDiv.className = 'message bot-message typing-indicator';
        typingDiv.id = 'typingIndicator';
        
        typingDiv.innerHTML = `
            <span class="message-icon">🤖</span>
            <div class="message-content">
                <div class="typing-dots">
                    <span></span>
                    <span></span>
                    <span></span>
                </div>
            </div>
        `;
        
        chatMessages.appendChild(typingDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
    
    // Remove typing indicator
    function removeTypingIndicator() {
        const typingIndicator = document.getElementById('typingIndicator');
        if (typingIndicator) {
            typingIndicator.remove();
        }
    }
    
    // Event listeners
    chatSend.addEventListener('click', sendMessage);
    chatInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });
}

// Initialize app on page load
document.addEventListener('DOMContentLoaded', initializeApp);
