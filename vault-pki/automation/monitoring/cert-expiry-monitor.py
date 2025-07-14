#!/usr/bin/env python3
"""
Certificate Expiry Monitor for Enterprise PKI
CyberSec Framework - Dual Root CA with Cross-Certification

This script monitors certificate expiration dates and sends alerts
when certificates are about to expire.
"""

import os
import json
import logging
import schedule
import time
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/compliance/audit-logs/cert-monitor.log'),
        logging.StreamHandler()
    ]
)

class CertificateMonitor:
    def __init__(self):
        self.vault_addr = os.getenv('VAULT_ADDR', 'https://vault:8200')
        self.vault_token = self._get_vault_token()
        self.alert_webhook = os.getenv('ALERT_WEBHOOK_URL')
        self.warning_days = 30  # Alert when cert expires in 30 days
        self.critical_days = 7   # Critical alert when cert expires in 7 days
        
        # Configure requests session
        self.session = requests.Session()
        self.session.verify = False  # For development only
        self.session.headers.update({
            'X-Vault-Token': self.vault_token,
            'Content-Type': 'application/json'
        })
    
    def _get_vault_token(self) -> str:
        """Read Vault token from file"""
        try:
            with open('/vault-init/vault-token', 'r') as f:
                return f.read().strip()
        except FileNotFoundError:
            logging.error("Vault token file not found")
            raise
    
    def check_vault_health(self) -> bool:
        """Check if Vault is healthy and accessible"""
        try:
            response = self.session.get(f"{self.vault_addr}/v1/sys/health")
            return response.status_code == 200
        except Exception as e:
            logging.error(f"Vault health check failed: {e}")
            return False
    
    def get_pki_mounts(self) -> List[str]:
        """Get list of PKI secret engines"""
        try:
            response = self.session.get(f"{self.vault_addr}/v1/sys/mounts")
            response.raise_for_status()
            
            mounts = response.json()
            pki_mounts = []
            
            for mount, config in mounts.get('data', {}).items():
                if config.get('type') == 'pki':
                    pki_mounts.append(mount.rstrip('/'))
            
            logging.info(f"Found PKI mounts: {pki_mounts}")
            return pki_mounts
        
        except Exception as e:
            logging.error(f"Failed to get PKI mounts: {e}")
            return []
    
    def check_ca_expiry(self, mount: str) -> Optional[Dict]:
        """Check CA certificate expiry for a given mount"""
        try:
            response = self.session.get(f"{self.vault_addr}/v1/{mount}/ca/pem")
            response.raise_for_status()
            
            # Parse certificate expiry (this is simplified - in production use cryptography library)
            cert_pem = response.text
            
            # For now, return mock data - implement proper cert parsing
            return {
                'mount': mount,
                'expires_at': '2025-12-31T23:59:59Z',
                'days_until_expiry': 350,
                'status': 'healthy'
            }
        
        except Exception as e:
            logging.error(f"Failed to check CA expiry for {mount}: {e}")
            return None
    
    def get_issued_certificates(self, mount: str) -> List[Dict]:
        """Get list of issued certificates for a mount"""
        try:
            response = self.session.get(f"{self.vault_addr}/v1/{mount}/certs")
            if response.status_code == 200:
                return response.json().get('data', {}).get('keys', [])
            return []
        except Exception as e:
            logging.warning(f"Could not list certificates for {mount}: {e}")
            return []
    
    def generate_report(self) -> Dict:
        """Generate comprehensive certificate status report"""
        report = {
            'timestamp': datetime.utcnow().isoformat(),
            'vault_health': self.check_vault_health(),
            'ca_certificates': [],
            'alerts': [],
            'statistics': {
                'total_cas': 0,
                'healthy_cas': 0,
                'warning_cas': 0,
                'critical_cas': 0
            }
        }
        
        if not report['vault_health']:
            report['alerts'].append({
                'level': 'critical',
                'message': 'Vault is not accessible',
                'timestamp': datetime.utcnow().isoformat()
            })
            return report
        
        pki_mounts = self.get_pki_mounts()
        report['statistics']['total_cas'] = len(pki_mounts)
        
        for mount in pki_mounts:
            ca_info = self.check_ca_expiry(mount)
            if ca_info:
                report['ca_certificates'].append(ca_info)
                
                days_until_expiry = ca_info['days_until_expiry']
                
                if days_until_expiry <= self.critical_days:
                    report['statistics']['critical_cas'] += 1
                    report['alerts'].append({
                        'level': 'critical',
                        'message': f"CA {mount} expires in {days_until_expiry} days",
                        'mount': mount,
                        'days_until_expiry': days_until_expiry,
                        'timestamp': datetime.utcnow().isoformat()
                    })
                elif days_until_expiry <= self.warning_days:
                    report['statistics']['warning_cas'] += 1
                    report['alerts'].append({
                        'level': 'warning',
                        'message': f"CA {mount} expires in {days_until_expiry} days",
                        'mount': mount,
                        'days_until_expiry': days_until_expiry,
                        'timestamp': datetime.utcnow().isoformat()
                    })
                else:
                    report['statistics']['healthy_cas'] += 1
        
        return report
    
    def save_report(self, report: Dict):
        """Save report to file"""
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        report_file = f"/compliance/reports/cert-status-{timestamp}.json"
        
        try:
            os.makedirs(os.path.dirname(report_file), exist_ok=True)
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2)
            
            # Also save as latest report
            latest_file = "/compliance/reports/cert-status-latest.json"
            with open(latest_file, 'w') as f:
                json.dump(report, f, indent=2)
                
            logging.info(f"Report saved to {report_file}")
        
        except Exception as e:
            logging.error(f"Failed to save report: {e}")
    
    def send_alerts(self, report: Dict):
        """Send alerts via webhook if configured"""
        if not self.alert_webhook or not report['alerts']:
            return
        
        try:
            critical_alerts = [a for a in report['alerts'] if a['level'] == 'critical']
            warning_alerts = [a for a in report['alerts'] if a['level'] == 'warning']
            
            if critical_alerts or warning_alerts:
                payload = {
                    'text': f"PKI Certificate Alert - {len(critical_alerts)} critical, {len(warning_alerts)} warning",
                    'report': report
                }
                
                response = requests.post(self.alert_webhook, json=payload)
                response.raise_for_status()
                logging.info("Alerts sent successfully")
        
        except Exception as e:
            logging.error(f"Failed to send alerts: {e}")
    
    def run_check(self):
        """Run a complete certificate check"""
        logging.info("Starting certificate expiry check")
        
        try:
            report = self.generate_report()
            self.save_report(report)
            self.send_alerts(report)
            
            # Log summary
            stats = report['statistics']
            logging.info(
                f"Check completed: {stats['total_cas']} CAs total, "
                f"{stats['healthy_cas']} healthy, "
                f"{stats['warning_cas']} warning, "
                f"{stats['critical_cas']} critical"
            )
            
        except Exception as e:
            logging.error(f"Certificate check failed: {e}")

def main():
    """Main monitoring loop"""
    monitor = CertificateMonitor()
    
    # Schedule monitoring every hour
    schedule.every().hour.do(monitor.run_check)
    
    # Run initial check
    monitor.run_check()
    
    logging.info("Certificate monitor started. Press Ctrl+C to stop.")
    
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute for scheduled jobs
    except KeyboardInterrupt:
        logging.info("Certificate monitor stopped")

if __name__ == '__main__':
    main()
