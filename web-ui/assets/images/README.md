# Dashboard Screenshots

## Placeholder Files

The README.md references the following screenshot files:
- `dashboard-screenshot.png` - Main dashboard overview
- `mobile-screenshot.png` - Mobile responsive view

## How to Generate Screenshots

1. **Start the application**:
   ```bash
   python3 -m http.server 8080
   ```

2. **Open in browser**: Navigate to `http://localhost:8080`

3. **Take screenshots**:
   - Full desktop view for `dashboard-screenshot.png`
   - Mobile view (using browser dev tools) for `mobile-screenshot.png`

4. **Save to this directory** with the correct filenames

## Screenshot Guidelines

- **Resolution**: 1920x1080 for desktop, 375x667 for mobile
- **Format**: PNG with transparency if needed
- **Content**: Show service status cards, command center, and chat assistant
- **Quality**: High resolution for documentation purposes

## Alternative: Generate Screenshots Programmatically

You can use tools like:
- **Puppeteer** (Node.js)
- **Playwright** (Multiple languages)
- **Selenium** (Multiple languages)

Example with Puppeteer:
```javascript
const puppeteer = require('puppeteer');

(async () => {
  const browser = await puppeteer.launch();
  const page = await browser.newPage();
  await page.goto('http://localhost:8080');
  await page.setViewport({width: 1920, height: 1080});
  await page.screenshot({path: 'dashboard-screenshot.png'});
  await browser.close();
})();
```
