# 🔐 CyberSec PKI Management Dashboard

> **A modern, modular web interface for managing PKI infrastructure with HashiCorp Vault, ACME, and OCSP services**

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Status](https://img.shields.io/badge/status-active-success.svg)
![Version](https://img.shields.io/badge/version-2.0.0-blue.svg)

## 🌟 Features

- **🔄 Real-time Service Monitoring**: Live status indicators for all PKI services
- **🤖 AI-Powered Chat Assistant**: Interactive help for PKI operations and troubleshooting
- **📱 Responsive Design**: Works seamlessly on desktop, tablet, and mobile devices
- **🎨 Modern UI**: Clean, professional interface with consistent styling
- **⚡ Modular Architecture**: Easy to extend and customize
- **🔒 Security-First**: Built for enterprise PKI management workflows

## 🚀 Quick Start

### Prerequisites
- Modern web browser (Chrome, Firefox, Safari, Edge)
- Local PKI services running (Vault, ACME, OCSP servers)
- Basic understanding of PKI concepts

### Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd cybersecurity-framework/web-ui
   ```

2. **Start a local web server**:
   ```bash
   # Using Python 3
   python3 -m http.server 8080
   
   # Using Node.js
   npx serve .
   
   # Using PHP
   php -S localhost:8080
   ```

3. **Open in browser**:
   Navigate to `http://localhost:8080`

### 🖥️ Dashboard Overview

The dashboard provides a centralized view of your PKI infrastructure:

- **Service Status Cards**: Real-time monitoring of all PKI services
- **Quick Actions**: One-click access to common operations
- **Command Center**: Ready-to-use CLI commands for certificate management
- **AI Assistant**: Interactive help and guidance

## 🏗️ Architecture

### Component Structure

```
web-ui/
├── assets/
│   ├── css/
│   │   └── main.css          # Unified styling with chat panel
│   └── js/
│       ├── components.js     # Modular UI components
│       └── main.js          # Application logic and chat functionality
├── templates/               # HTML fragment templates (alternative approach)
│   ├── header.html
│   ├── service-card.html
│   ├── service-grid.html
│   ├── commands.html
│   └── footer.html
├── index.html              # Main application entry point
└── README.md               # This documentation
```

### Core Components

#### 1. Service Management
- **`createServiceGrid()`**: Displays all PKI services with live status
- **`createServiceCard()`**: Individual service monitoring cards
- **`checkServiceStatus()`**: Real-time health checking with CORS handling

#### 2. Interactive Chat Assistant
- **`createChatPanel()`**: AI-powered help system
- **`initializeChat()`**: Chat functionality with typing indicators
- **`generateBotResponse()`**: Contextual PKI assistance

#### 3. Command Center
- **`createCommandsSection()`**: Quick-access command templates
- **Certificate operations**: ACME, OCSP, and Vault integration
- **Testing utilities**: Built-in certificate request testing

## 🔧 Usage Guide

### Service Monitoring

The dashboard automatically monitors these services:

| Service | Port | Purpose | Status Endpoint |
|---------|------|---------|----------------|
| **HashiCorp Vault** | 8200 | PKI Backend & CA | `/v1/sys/health` |
| **OCSP Server** | 8888 | Certificate Revocation | `/health` |
| **ACME Server** | 8889 | Certificate Automation | `/health` |
| **PKI Metrics** | 9100 | Prometheus Monitoring | `/` |

**Status Indicators**:
- 🟢 **Green**: Service online and responding
- 🔴 **Red**: Service offline or unreachable
- 🟡 **Yellow**: Status unknown (checking...)

### Chat Assistant

The AI assistant helps with:

- **Certificate Management**: Issuance, renewal, and revocation
- **ACME Operations**: Automated certificate workflows
- **OCSP Queries**: Certificate status checking
- **Vault Operations**: PKI backend management
- **Troubleshooting**: Common issues and solutions

**Example interactions**:
```
User: "How do I request a certificate?"
Assistant: "You can request certificates using ACME, OCSP, or Vault. Which method would you prefer?"

User: "test"
Assistant: [Runs live certificate request test]
```

### Command Center

Ready-to-use commands for common operations:

#### 1. ACME Certificate Request
```bash
curl -X POST http://localhost:8889/acme/new-order \
  -H "Content-Type: application/jose+json" \
  -d '{"identifiers": [{"type": "dns", "value": "example.com"}]}'
```

#### 2. OCSP Status Check
```bash
curl -X GET http://localhost:8888/ocsp/status/CERTIFICATE_SERIAL
```

#### 3. Vault Certificate Issuance
```bash
curl -X POST http://localhost:8200/v1/pki/issue/cybersec-role \
  -H "X-Vault-Token: cybersec-dev-token" \
  -d '{"common_name": "test.cybersec.local", "ttl": "24h"}'
```

#### 4. Agent Integration Test
```bash
python demo_agent_vault_integration.py
```

## 🎛️ Advanced Configuration

### Service Configuration

Services are defined in the `services` array in `components.js`:

```javascript
const services = [
    {
        title: 'HashiCorp Vault',
        description: 'Certificate Authority and PKI Backend',
        url: 'http://localhost:8200',
        linkText: 'Open Vault UI'
    },
    // Add more services here
];
```

**Properties**:
- `title`: Service display name
- `description`: Brief description of the service
- `url`: Service URL for links
- `linkText`: Button text for service links

### Status Monitoring URLs

Health check endpoints are configured in `main.js`:

```javascript
const urls = [
    'http://localhost:8200/v1/sys/health',  // Vault
    'http://localhost:8888/health',          // OCSP
    'http://localhost:8889/health',          // ACME
    'http://localhost:9100'                  // Metrics
];
```

### Chat Assistant Customization

Modify the AI responses in `generateBotResponse()` function:

```javascript
function generateBotResponse(userMessage) {
    const lowerMessage = userMessage.toLowerCase();
    
    if (lowerMessage.includes('certificate')) {
        return 'Your custom certificate help message';
    }
    // Add more response patterns
}
```

## 🛠️ Customization Guide

### Adding New Services

1. **Add to services array** in `components.js`:
   ```javascript
   {
       title: 'New Service',
       description: 'Service description',
       url: 'http://localhost:9000',
       linkText: 'Open Service'
   }
   ```

2. **Add health check URL** to the `urls` array in `main.js`:
   ```javascript
   'http://localhost:9000/health'
   ```

3. **Styling is applied automatically** using CSS grid

### Modifying the Layout

- **Grid layout**: Edit `.service-grid` in `main.css`
- **Component templates**: Modify functions in `components.js`
- **Colors and themes**: Update CSS variables in `main.css`

### Custom Commands

Edit the `commands` array in `createCommandsSection()`:

```javascript
const commands = [
    {
        title: '1. Your Custom Command:',
        command: 'your-custom-command --with-options'
    },
    // Add more commands
];
```

## 🔧 Alternative: HTML Fragments

For developers who prefer traditional HTML templates:

### Available Templates
- `templates/header.html` - Dashboard header
- `templates/service-card.html` - Service card with placeholders
- `templates/service-grid.html` - Complete service grid
- `templates/commands.html` - Commands section
- `templates/footer.html` - Footer

### Usage

1. **Switch to template mode** in `index.html`:
   ```html
   <script src="assets/js/template-loader.js"></script>
   <script src="assets/js/main.js"></script>
   <script>
       document.addEventListener('DOMContentLoaded', initializeAppWithFragments);
   </script>
   ```

2. **Edit templates directly** using placeholders like `{{title}}`, `{{description}}`

## 🎨 Styling & Themes

### Color Scheme

The dashboard uses a professional blue theme:

```css
:root {
    --primary-color: #2a5298;
    --secondary-color: #1e3c72;
    --accent-color: #4fc3f7;
    --success-color: #4caf50;
    --danger-color: #f44336;
    --warning-color: #ff9800;
}
```

### Responsive Design

- **Desktop**: Full grid layout with 4 columns
- **Tablet**: 2 columns with adjusted spacing
- **Mobile**: Single column with optimized touch targets

### Chat Panel Styling

The chat assistant matches the dashboard theme:

- **Header**: Gradient background with controls
- **Messages**: Bubble design with user/bot distinction
- **Input**: Rounded input with send button
- **Animations**: Smooth transitions and typing indicators

## 🚀 Deployment

### Development Server

```bash
# Python (recommended)
python3 -m http.server 8080

# Node.js
npx serve . -p 8080

# PHP
php -S localhost:8080
```

### Production Deployment

1. **Static hosting** (Netlify, Vercel, GitHub Pages):
   - Upload the entire `web-ui` directory
   - Configure build settings if needed
   - Set up custom domain

2. **Web server** (Apache, Nginx):
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;
       root /path/to/web-ui;
       index index.html;
       
       location / {
           try_files $uri $uri/ /index.html;
       }
   }
   ```

3. **Docker deployment**:
   ```dockerfile
   FROM nginx:alpine
   COPY . /usr/share/nginx/html
   EXPOSE 80
   CMD ["nginx", "-g", "daemon off;"]
   ```

## 🔍 Troubleshooting

### Common Issues

#### Services Show as Offline
- **Check if services are running** on correct ports
- **Verify CORS settings** in your PKI services
- **Check browser console** for network errors
- **Test endpoints manually** using curl

#### Chat Assistant Not Working
- **Check console for errors** in browser DevTools
- **Verify event listeners** are properly attached
- **Test with simple messages** first

#### Status Indicators Not Updating
- **Check network connectivity** to services
- **Verify health check endpoints** are correct
- **Look for CORS issues** in browser console

### Debug Mode

Enable debug logging in `main.js`:

```javascript
const DEBUG = true;

function debugLog(message) {
    if (DEBUG) {
        console.log('[DEBUG]', message);
    }
}
```

### Performance Optimization

- **Service status checking** is staggered to reduce load
- **CORS fallback** ensures compatibility
- **Lazy loading** for chat responses
- **Efficient DOM updates** using modern JavaScript

## 📊 Status Indicators

The dashboard uses a three-state indicator system:

- 🟢 **Green (Online)**: Service responding with HTTP 200-299
- 🔴 **Red (Offline)**: Service unreachable or HTTP error
- 🟡 **Yellow (Unknown)**: Initial state or checking in progress

Status checking includes:
- **Primary check**: CORS-enabled request
- **Fallback**: no-cors mode for restricted services
- **Timeout**: 5-second timeout to prevent hanging
- **Retry logic**: Automatic retry on network errors

## 📸 Screenshots

### Dashboard Overview

![Dashboard Screenshot](assets/images/dashboard-screenshot.png)

*The main dashboard showing service status cards, command center, and chat assistant*

### Key Features Shown:
- **Service Status Cards**: Real-time monitoring with color-coded indicators
- **Command Center**: Quick-access CLI commands for common operations
- **Chat Assistant**: AI-powered help floating in bottom-right corner
- **Responsive Design**: Clean, professional layout that works on all devices

### Mobile View

![Mobile Screenshot](assets/images/mobile-screenshot.png)

*The dashboard adapts seamlessly to mobile devices with optimized touch targets*

## 🧪 Testing

### Manual Testing

1. **Service Status**: Verify all service indicators show correct status
2. **Chat Assistant**: Test various PKI-related queries
3. **Command Execution**: Copy and test the provided commands
4. **Responsive Design**: Check on different screen sizes

### Integration Testing

```bash
# Test certificate request functionality
curl -X POST http://localhost:8889/acme/new-order \
  -H "Content-Type: application/jose+json" \
  -d '{"identifiers": [{"type": "dns", "value": "test.local"}]}'

# Test OCSP status check
curl -X GET http://localhost:8888/health

# Test Vault connectivity
curl -X GET http://localhost:8200/v1/sys/health
```

### Automated Testing

The dashboard includes built-in testing via the chat assistant:

1. Open the chat panel
2. Type "test" to run certificate request tests
3. Check console for detailed results

## 🤝 Contributing

### Development Setup

1. **Fork the repository**
2. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. **Make your changes**
4. **Test thoroughly**
5. **Submit a pull request**

### Code Style

- **JavaScript**: ES6+ features, consistent formatting
- **CSS**: BEM methodology, CSS variables for theming
- **HTML**: Semantic markup, accessibility considerations

### Adding New Features

1. **Components**: Add new functions to `components.js`
2. **Styling**: Update `main.css` with consistent theming
3. **Logic**: Add functionality to `main.js`
4. **Documentation**: Update this README

### Testing Guidelines

- Test on multiple browsers
- Verify mobile responsiveness
- Check accessibility with screen readers
- Test with PKI services both online and offline

## 🔗 Related Projects

- **[HashiCorp Vault](https://www.vaultproject.io/)**: PKI backend and certificate authority
- **[ACME Protocol](https://tools.ietf.org/html/rfc8555)**: Automated certificate management
- **[OCSP](https://tools.ietf.org/html/rfc6960)**: Online Certificate Status Protocol

## 📚 Resources

### PKI Documentation
- [PKI Concepts](https://en.wikipedia.org/wiki/Public_key_infrastructure)
- [Certificate Lifecycle Management](https://www.digicert.com/what-is-pki)
- [ACME Protocol Guide](https://letsencrypt.org/docs/)

### Development Resources
- [Modern JavaScript](https://javascript.info/)
- [CSS Grid Guide](https://css-tricks.com/snippets/css/complete-guide-grid/)
- [Responsive Design](https://web.dev/responsive-web-design-basics/)

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **HashiCorp Vault Team**: For the excellent PKI backend
- **ACME Protocol Contributors**: For standardizing certificate automation
- **Web Development Community**: For the tools and techniques used

---

**Built with ❤️ for the cybersecurity community**

*For questions, issues, or contributions, please open an issue or submit a pull request.*
