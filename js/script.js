// JavaScript code will go here
console.log("Welcome to the Cybersecurity Framework website!");

const scannerForm = document.getElementById('scanner-form');
const scannerInput = document.getElementById('scanner-input');
const scannerResults = document.getElementById('scanner-results');

scannerForm.addEventListener('submit', (e) => {
    e.preventDefault();
    const target = scannerInput.value;
    if (!target) {
        return;
    }

    scannerResults.innerHTML = `<p>Scanning ${target}...</p>`;

    // Simulate a backend API call
    setTimeout(() => {
        const dummyResult = {
            host: target,
            open_ports: [80, 443],
            closed_ports: [21, 22, 23, 25, 53, 110, 143, 993, 995, 8080, 8443],
            total_scanned: 13,
            timestamp: new Date().toISOString()
        };

        scannerResults.innerHTML = `
            <h3>Scan Results for ${dummyResult.host}</h3>
            <p><strong>Open Ports:</strong> ${dummyResult.open_ports.join(', ')}</p>
            <p><strong>Closed Ports:</strong> ${dummyResult.closed_ports.length}</p>
            <p><strong>Total Scanned:</strong> ${dummyResult.total_scanned}</p>
            <p><strong>Timestamp:</strong> ${dummyResult.timestamp}</p>
        `;
    }, 2000);
});

const contactForm = document.getElementById('contact-form');

contactForm.addEventListener('submit', (e) => {
    e.preventDefault();
    const name = document.getElementById('name').value;
    const email = document.getElementById('email').value;
    const message = document.getElementById('message').value;

    if (!name || !email || !message) {
        return;
    }

    console.log('Contact form submitted:', { name, email, message });
    alert('Thank you for your message! We will get back to you soon.');
    contactForm.reset();
});
