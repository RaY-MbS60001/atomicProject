# email_validator.py
import dns.resolver
import socket
import smtplib
import re

class EmailValidator:
    """Advanced email validation including DNS and SMTP checks."""
    
    def __init__(self):
        self.dns_cache = {}
    
    def is_valid_format(self, email):
        """Check if email format is valid."""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def get_mx_records(self, domain):
        """Get MX records for domain."""
        if domain in self.dns_cache:
            return self.dns_cache[domain]
        
        try:
            mx_records = dns.resolver.resolve(domain, 'MX')
            mx_list = [str(mx.exchange).rstrip('.') for mx in mx_records]
            self.dns_cache[domain] = mx_list
            return mx_list
        except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer, dns.resolver.Timeout):
            self.dns_cache[domain] = None
            return None
        except Exception as e:
            print(f"DNS error for {domain}: {str(e)}")
            return None
    
    def domain_exists(self, email):
        """Check if email domain has valid MX records."""
        if not self.is_valid_format(email):
            return False
        
        domain = email.split('@')[1]
        mx_records = self.get_mx_records(domain)
        return mx_records is not None and len(mx_records) > 0
    
    def verify_email_smtp(self, email, timeout=10):
        """
        Verify email exists using SMTP (may not work with all servers).
        This is intrusive and should be used sparingly.
        """
        if not self.is_valid_format(email):
            return False, "Invalid format"
        
        domain = email.split('@')[1]
        mx_records = self.get_mx_records(domain)
        
        if not mx_records:
            return False, "No MX records"
        
        try:
            # Connect to mail server
            server = smtplib.SMTP(timeout=timeout)
            server.set_debuglevel(0)
            server.connect(mx_records[0])
            server.helo(server.local_hostname)
            server.mail('verify@example.com')
            code, message = server.rcpt(email)
            server.quit()
            
            if code == 250:
                return True, "Valid"
            else:
                return False, f"SMTP code {code}"
        
        except Exception as e:
            return False, str(e)
    
    def validate_batch(self, emails, check_dns=True, check_smtp=False):
        """
        Validate a batch of emails.
        
        Args:
            emails: List of email addresses
            check_dns: Check DNS/MX records
            check_smtp: Perform SMTP verification (slow)
        
        Returns:
            dict with 'valid', 'invalid', and 'suspicious' lists
        """
        results = {
            'valid': [],
            'invalid': [],
            'suspicious': [],
            'details': {}
        }
        
        for email in emails:
            detail = {'email': email, 'checks': {}}
            
            # Format check
            if not self.is_valid_format(email):
                results['invalid'].append(email)
                detail['checks']['format'] = False
                detail['status'] = 'invalid'
                results['details'][email] = detail
                continue
            
            detail['checks']['format'] = True
            
            # DNS check
            if check_dns:
                domain_valid = self.domain_exists(email)
                detail['checks']['dns'] = domain_valid
                
                if not domain_valid:
                    results['suspicious'].append(email)
                    detail['status'] = 'suspicious'
                    results['details'][email] = detail
                    continue
            
            # SMTP check (optional, slow)
            if check_smtp:
                smtp_valid, smtp_msg = self.verify_email_smtp(email)
                detail['checks']['smtp'] = smtp_valid
                detail['checks']['smtp_message'] = smtp_msg
                
                if not smtp_valid:
                    results['suspicious'].append(email)
                    detail['status'] = 'suspicious'
                    results['details'][email] = detail
                    continue
            
            # All checks passed
            results['valid'].append(email)
            detail['status'] = 'valid'
            results['details'][email] = detail
        
        return results


def validate_email_list_interactive():
    """Interactive email validation tool."""
    print("\n" + "="*70)
    print(" "*20 + "EMAIL VALIDATOR")
    print("="*70)
    
    validator = EmailValidator()
    
    print("\n1. Validate from email_list.txt")
    print("2. Validate from email_list.csv")
    print("3. Enter emails manually")
    print("4. Exit")
    
    choice = input("\nChoice: ").strip()
    
    emails = []
    
    if choice == '1':
        from email_list_manager import EmailListManager
        manager = EmailListManager(os.path.dirname(os.path.abspath(__file__)))
        emails = manager.load_from_txt()
    elif choice == '2':
        from email_list_manager import EmailListManager
        manager = EmailListManager(os.path.dirname(os.path.abspath(__file__)))
        emails = manager.load_from_csv()
    elif choice == '3':
        print("\nEnter emails (one per line, empty line to finish):")
        while True:
            email = input().strip()
            if not email:
                break
            emails.append(email)
    else:
        return
    
    if not emails:
        print("\n❌ No emails to validate!")
        return
    
    print(f"\n🔍 Validating {len(emails)} email(s)...")
    
    check_dns = input("Check DNS/MX records? (y/n): ").lower() == 'y'
    check_smtp = False
    
    if check_dns:
        check_smtp = input("Perform SMTP verification? (slower, y/n): ").lower() == 'y'
    
    print("\nProcessing...")
    results = validator.validate_batch(emails, check_dns=check_dns, check_smtp=check_smtp)
    
    # Display results
    print("\n" + "="*70)
    print(" "*22 + "VALIDATION RESULTS")
    print("="*70)
    print(f"✓ Valid: {len(results['valid'])}")
    print(f"⚠ Suspicious: {len(results['suspicious'])}")
    print(f"✗ Invalid: {len(results['invalid'])}")
    print("="*70)
    
    if results['invalid']:
        print("\nInvalid emails:")
        for email in results['invalid'][:10]:
            print(f"  ✗ {email}")
        if len(results['invalid']) > 10:
            print(f"  ... and {len(results['invalid']) - 10} more")
    
    if results['suspicious']:
        print("\nSuspicious emails (may not exist):")
        for email in results['suspicious'][:10]:
            detail = results['details'][email]
            reason = "No DNS" if not detail['checks'].get('dns') else "SMTP failed"
            print(f"  ⚠ {email} - {reason}")
        if len(results['suspicious']) > 10:
            print(f"  ... and {len(results['suspicious']) - 10} more")
    
    # Save valid emails
    if results['valid']:
        save = input(f"\nSave {len(results['valid'])} valid email(s) to file? (y/n): ").lower()
        if save == 'y':
            filename = input("Filename (default: valid_emails.txt): ").strip() or "valid_emails.txt"
            with open(filename, 'w') as f:
                f.write('\n'.join(results['valid']))
            print(f"✓ Saved to {filename}")


if __name__ == "__main__":
    validate_email_list_interactive()