import re
import os
from datetime import datetime
import socket
import smtplib
from time import sleep

def validate_email_syntax(email):
    """Check if email has valid syntax"""
    pattern = r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}$'
    return re.match(pattern, email) is not None

def check_domain_exists(domain):
    """Check if domain has valid DNS records"""
    try:
        socket.gethostbyname(domain)
        return True
    except socket.gaierror:
        return False

def verify_email_smtp(email):
    """
    Verify if email exists using SMTP
    Returns: True (valid), False (invalid), None (unknown)
    """
    try:
        domain = email.split('@')[1]
        
        # Check if domain exists
        if not check_domain_exists(domain):
            return False
        
        # Try to get MX records
        try:
            import dns.resolver
            mx_records = dns.resolver.resolve(domain, 'MX')
            mx_host = str(mx_records[0].exchange).rstrip('.')
        except:
            # If no MX record, try domain directly
            mx_host = domain
        
        # Connect to SMTP server
        server = smtplib.SMTP(timeout=15)
        server.set_debuglevel(0)
        
        try:
            server.connect(mx_host)
            server.helo(server.local_hostname)
            server.mail('verify@example.com')
            code, message = server.rcpt(email)
            server.quit()
            
            # Code 250 means email exists
            if code == 250:
                return True
            # Code 550 means email doesn't exist
            elif code == 550:
                return False
            else:
                return None  # Unknown
                
        except smtplib.SMTPServerDisconnected:
            return None
        except smtplib.SMTPConnectError:
            return None
        except Exception as e:
            return None
            
    except Exception as e:
        return None

def process_non_gmail_emails(input_file):
    """
    Process emails: remove duplicates, exclude Gmail, verify others
    """
    
    print("=" * 70)
    print("📧 EMAIL PROCESSOR - Non-Gmail Valid Emails Only")
    print("=" * 70)
    print(f"\n📂 Input file: {input_file}\n")
    
    # Read all emails from file
    print("📖 Reading emails from file...")
    all_emails = set()
    
    try:
        with open(input_file, 'r', encoding='utf-8', errors='ignore') as file:
            for line in file:
                line = line.strip()
                # Skip header lines and empty lines
                if line and '@' in line and not line.startswith('Total') and not line.startswith('Extraction') and not line.startswith('=') and not line.startswith('Source'):
                    if validate_email_syntax(line):
                        all_emails.add(line.lower())  # Normalize to lowercase
    except Exception as e:
        print(f"❌ Error reading file: {e}")
        return
    
    print(f"✅ Found {len(all_emails)} unique emails (after deduplication)")
    
    # Exclude Gmail addresses
    print("\n🚫 Excluding Gmail addresses...")
    non_gmail_emails = {email for email in all_emails if not email.endswith('@gmail.com')}
    gmail_count = len(all_emails) - len(non_gmail_emails)
    
    print(f"   • Gmail addresses excluded: {gmail_count}")
    print(f"   • Non-Gmail addresses to verify: {len(non_gmail_emails)}")
    
    # Show domain breakdown
    print("\n📊 Email domains found:")
    domains = {}
    for email in non_gmail_emails:
        domain = email.split('@')[1]
        domains[domain] = domains.get(domain, 0) + 1
    
    for domain, count in sorted(domains.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"   • {domain}: {count}")
    if len(domains) > 10:
        print(f"   ... and {len(domains) - 10} more domains")
    
    # Verify emails
    print("\n" + "=" * 70)
    print("🔐 STARTING EMAIL VERIFICATION")
    print("=" * 70)
    print("⏳ This may take a while... Please be patient!\n")
    
    verified_emails = []
    unknown_emails = []
    invalid_emails = []
    
    total = len(non_gmail_emails)
    
    for idx, email in enumerate(sorted(non_gmail_emails), 1):
        percentage = (idx / total) * 100
        print(f"[{idx}/{total}] ({percentage:.1f}%) Checking: {email:<50}", end='')
        
        result = verify_email_smtp(email)
        
        if result is True:
            verified_emails.append(email)
            print(" ✅ VALID")
        elif result is None:
            unknown_emails.append(email)
            print(" ❓ UNKNOWN")
        else:
            invalid_emails.append(email)
            print(" ❌ INVALID")
        
        # Rate limiting to avoid being blocked
        if idx % 5 == 0:
            sleep(2)  # Pause every 5 emails
        
        if idx % 20 == 0:
            print(f"\n⏸️  Progress check - Pausing for 5 seconds...")
            print(f"   Valid so far: {len(verified_emails)}")
            print(f"   Unknown: {len(unknown_emails)}")
            print(f"   Invalid: {len(invalid_emails)}\n")
            sleep(5)
    
    # Generate output files
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # 1. Valid emails only (what you requested)
    valid_output = f'valid_non_gmail_{timestamp}.txt'
    print(f"\n💾 Saving VALID non-Gmail emails to: {valid_output}")
    with open(valid_output, 'w', encoding='utf-8') as out_file:
        out_file.write(f"Valid Non-Gmail Email Addresses\n")
        out_file.write(f"Total Valid: {len(verified_emails)}\n")
        out_file.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        out_file.write("=" * 60 + "\n\n")
        
        for email in sorted(verified_emails):
            out_file.write(email + '\n')
    
    # 2. Full report (all categories)
    report_output = f'verification_report_{timestamp}.txt'
    print(f"💾 Saving full report to: {report_output}")
    with open(report_output, 'w', encoding='utf-8') as out_file:
        out_file.write(f"EMAIL VERIFICATION REPORT (Non-Gmail Only)\n")
        out_file.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        out_file.write("=" * 60 + "\n\n")
        
        out_file.write(f"STATISTICS:\n")
        out_file.write(f"Total emails processed: {total}\n")
        out_file.write(f"Gmail addresses excluded: {gmail_count}\n")
        out_file.write(f"Valid (Active): {len(verified_emails)} ({len(verified_emails)/total*100:.1f}%)\n")
        out_file.write(f"Unknown (Couldn't Verify): {len(unknown_emails)} ({len(unknown_emails)/total*100:.1f}%)\n")
        out_file.write(f"Invalid: {len(invalid_emails)} ({len(invalid_emails)/total*100:.1f}%)\n")
        out_file.write("\n" + "=" * 60 + "\n\n")
        
        out_file.write("VALID EMAILS (VERIFIED ACTIVE):\n")
        out_file.write("-" * 60 + "\n")
        for email in sorted(verified_emails):
            out_file.write(email + '\n')
        
        out_file.write("\n\nUNKNOWN (COULDN'T VERIFY - May still be valid):\n")
        out_file.write("-" * 60 + "\n")
        for email in sorted(unknown_emails):
            out_file.write(email + '\n')
        
        out_file.write("\n\nINVALID (Not Active/Doesn't Exist):\n")
        out_file.write("-" * 60 + "\n")
        for email in sorted(invalid_emails):
            out_file.write(email + '\n')
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 FINAL SUMMARY")
    print("=" * 70)
    print(f"Total emails processed: {total}")
    print(f"Gmail addresses excluded: {gmail_count}")
    print(f"\n✅ Valid (Active): {len(verified_emails)} ({len(verified_emails)/total*100:.1f}%)")
    print(f"❓ Unknown: {len(unknown_emails)} ({len(unknown_emails)/total*100:.1f}%)")
    print(f"❌ Invalid: {len(invalid_emails)} ({len(invalid_emails)/total*100:.1f}%)")
    print(f"\n📁 Files created:")
    print(f"   • {valid_output} ← VALID EMAILS ONLY")
    print(f"   • {report_output} ← FULL REPORT")
    print("=" * 70)

# Main execution
if __name__ == "__main__":
    INPUT_FILE = 'sample_emails.txt'
    
    print("\n📧 NON-GMAIL EMAIL VALIDATOR")
    print("=" * 70)
    
    if not os.path.exists(INPUT_FILE):
        print(f"❌ Error: File '{INPUT_FILE}' not found!")
        print(f"📁 Current directory: {os.getcwd()}")
        print("\nAvailable files:")
        for file in os.listdir('.'):
            if file.endswith('.txt'):
                print(f"   • {file}")
        
        # Let user input filename
        print("\n")
        custom_file = input("Enter the filename: ").strip()
        if os.path.exists(custom_file):
            INPUT_FILE = custom_file
        else:
            print(f"❌ File '{custom_file}' not found!")
            input("\nPress Enter to exit...")
            exit()
    
    print(f"\n✅ Found file: {INPUT_FILE}")
    print("\n⚠️  This will verify each non-Gmail email address.")
    print("⚠️  This process can take a LONG time for many emails.")
    print("⚠️  Some emails may show as 'Unknown' due to server restrictions.\n")
    
    choice = input("Continue? (y/n): ").lower().strip()
    
    if choice == 'y':
        print("\n")
        
        # Install dnspython if needed
        try:
            import dns.resolver
        except ImportError:
            print("📦 Installing required package 'dnspython'...")
            os.system('pip install dnspython')
            print()
        
        try:
            process_non_gmail_emails(INPUT_FILE)
            input("\n✨ Press Enter to exit...")
        except KeyboardInterrupt:
            print("\n\n⚠️  Process interrupted by user!")
            input("\nPress Enter to exit...")
        except Exception as e:
            print(f"\n❌ Error occurred: {e}")
            import traceback
            traceback.print_exc()
            input("\nPress Enter to exit...")
    else:
        print("\n❌ Operation cancelled.")
        input("\nPress Enter to exit...")