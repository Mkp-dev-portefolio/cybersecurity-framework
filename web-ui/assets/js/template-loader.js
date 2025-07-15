// Template Loader Utility
// This provides an alternative approach using HTML fragments instead of JS template strings

class TemplateLoader {
    constructor() {
        this.cache = new Map();
    }

    // Load HTML fragment from file
    async loadFragment(path) {
        if (this.cache.has(path)) {
            return this.cache.get(path);
        }

        try {
            const response = await fetch(path);
            const html = await response.text();
            this.cache.set(path, html);
            return html;
        } catch (error) {
            console.error(`Failed to load template: ${path}`, error);
            return '';
        }
    }

    // Replace placeholders in template with data
    renderTemplate(template, data) {
        return template.replace(/\{\{(\w+)\}\}/g, (match, key) => {
            return data[key] || match;
        });
    }

    // Load and render service card with data
    async renderServiceCard(service) {
        const template = await this.loadFragment('templates/service-card.html');
        return this.renderTemplate(template, service);
    }

    // Build complete service grid
    async buildServiceGrid() {
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

        const serviceCards = await Promise.all(
            services.map(service => this.renderServiceCard(service))
        );

        return `<div class="service-grid">${serviceCards.join('')}</div>`;
    }

    // Build complete app using HTML fragments
    async buildApp() {
        const [header, serviceGrid, commands, footer] = await Promise.all([
            this.loadFragment('templates/header.html'),
            this.buildServiceGrid(),
            this.loadFragment('templates/commands.html'),
            this.loadFragment('templates/footer.html')
        ]);

        return `
            <div class="container">
                ${header}
                ${serviceGrid}
                ${commands}
                ${footer}
            </div>
        `;
    }
}

// Alternative initialization function using HTML fragments
async function initializeAppWithFragments() {
    const loader = new TemplateLoader();
    const appHTML = await loader.buildApp();
    document.body.innerHTML = appHTML;
    
    // Check service status after rendering
    checkAllServiceStatus();
}

// Export for use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { TemplateLoader, initializeAppWithFragments };
}
