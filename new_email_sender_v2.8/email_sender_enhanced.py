# email_sender_enhanced.py
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import os
import time
import random
import logging
import re
import json
from datetime import datetime
from tqdm import tqdm

# Import our custom modules
from email_list_manager import EmailListManager
from rate_limiter import RateLimiter, SMTPConnectionPool
from report_viewer import ReportViewer

# Logging setup
script_dir = os.path.dirname(os.path.abspath(__file__))
log_file = os.path.join(script_dir, 'email_sender.log')
report_file = os.path.join(script_dir, 'email_report.json')

logging.basicConfig(
    filename=log_file,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Email Configuration
SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587
SENDER_EMAIL = "sfisomabaso12242001@gmail.com"
SENDER_PASSWORD = "swwf uqok tqeo ####"

# Email Content
SUBJECT = "Learnership/Internship Application"
BODY = """
Good day. My name is Sbongakonke Sfiso Mabaso, and I am currently seeking a learning opportunity in the form of a learnership or internship to further grow my skills and contribute meaningfully within a dynamic and forward-thinking technology team.

I am passionate about the IT field and eager to apply the knowledge I have gained through my academic journey in a practical environment, while continuously learning and adding value.

Please find my CV attached for your consideration. I would be truly grateful for an opportunity to be part of your organization and contribute wherever possible.

Kind regards,
Sbongakonke Sfiso Mabaso
📞 076 017 8522
📧 sfisomabaso12242001@gmail.com
"""

ATTACHMENT_FILE = os.path.join(script_dir, "ilovepdf_merged (1).pdf")


class EmailReport:
    """Handles reading and writing email sending reports."""
    
    def __init__(self, report_path):
        self.report_path = report_path
        self.data = self.load_report()
    
    def load_report(self):
        """Load existing report or create new one."""
        if os.path.exists(self.report_path):
            try:
                with open(self.report_path, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                logging.warning("Corrupted report file, creating new one")
                return self._create_empty_report()
        return self._create_empty_report()
    
    def _create_empty_report(self):
        """Create empty report structure."""
        return {
            "last_updated": None,
            "successful": {},
            "failed": {},
            "statistics": {
                "total_successful": 0,
                "total_failed": 0,
                "total_attempts": 0
            }
        }
    
    def save_report(self):
        """Save report to file."""
        self.data["last_updated"] = datetime.now().isoformat()
        with open(self.report_path, 'w') as f:
            json.dump(self.data, f, indent=2)
    
    def mark_successful(self, email):
        """Mark email as successfully sent."""
        timestamp = datetime.now().isoformat()
        self.data["successful"][email] = {
            "timestamp": timestamp,
            "attempts": self.data["failed"].get(email, {}).get("attempts", 0) + 1
        }
        if email in self.data["failed"]:
            del self.data["failed"][email]
        self.data["statistics"]["total_successful"] += 1
        self.save_report()
    
    def mark_failed(self, email, error_message):
        """Mark email as failed."""
        timestamp = datetime.now().isoformat()
        if email not in self.data["failed"]:
            self.data["failed"][email] = {
                "first_attempt": timestamp,
                "attempts": 0,
                "errors": []
            }
        
        self.data["failed"][email]["last_attempt"] = timestamp
        self.data["failed"][email]["attempts"] += 1
        self.data["failed"][email]["errors"].append({
            "timestamp": timestamp,
            "message": error_message
        })
        self.data["statistics"]["total_failed"] += 1
        self.save_report()
    
    def is_already_sent(self, email):
        """Check if email was already successfully sent."""
        return email in self.data["successful"]
    
    def get_failed_emails(self):
        """Get list of failed emails."""
        return list(self.data["failed"].keys())
    
    def get_statistics(self):
        """Get current statistics."""
        return self.data["statistics"]


def is_valid_email(email):
    """Validate email format."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def create_email_message(to_email):
    """Create the email message with attachment."""
    msg = MIMEMultipart()
    msg['From'] = SENDER_EMAIL
    msg['To'] = to_email
    msg['Subject'] = SUBJECT
    
    msg.attach(MIMEText(BODY, 'plain'))
    
    if os.path.exists(ATTACHMENT_FILE):
        with open(ATTACHMENT_FILE, "rb") as attachment:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(attachment.read())
            encoders.encode_base64(part)
            part.add_header(
                'Content-Disposition',
                f'attachment; filename={os.path.basename(ATTACHMENT_FILE)}'
            )
            msg.attach(part)
    
    return msg


def send_email_with_pool(to_email, report, connection_pool, rate_limiter):
    """Send email using connection pool and rate limiting."""
    try:
        if not is_valid_email(to_email):
            raise ValueError("Invalid email format")

        # Wait if rate limit would be exceeded
        rate_limiter.wait_if_needed()

        msg = create_email_message(to_email)
        
        # Get connection from pool
        conn, reused = connection_pool.get_connection()
        
        try:
            conn.send_message(msg)
            # Return connection to pool
            connection_pool.return_connection(conn)
        except Exception as e:
            # Connection failed, don't return to pool
            try:
                conn.quit()
            except:
                pass
            raise e
            
        logging.info(f"Successfully sent email to {to_email}")
        report.mark_successful(to_email)
        return True, "Success"
        
    except FileNotFoundError:
        error_msg = "CV file not found"
        logging.error(f"{error_msg}: {ATTACHMENT_FILE}")
        report.mark_failed(to_email, error_msg)
        return False, error_msg
    except smtplib.SMTPAuthenticationError:
        error_msg = "SMTP Authentication failed"
        logging.error(error_msg)
        report.mark_failed(to_email, error_msg)
        return False, error_msg
    except Exception as e:
        error_msg = str(e)
        logging.error(f"Error sending to {to_email}: {error_msg}")
        report.mark_failed(to_email, error_msg)
        return False, error_msg


def setup_check():
    """Perform initial setup checks."""
    print("\n" + "="*70)
    print(" "*20 + "S Y S T E M   C H E C K")
    print("="*70)
    
    if not os.path.exists(ATTACHMENT_FILE):
        print(f"❌ CV file not found at: {ATTACHMENT_FILE}")
        return False
    print(f"✓ CV file found: {os.path.basename(ATTACHMENT_FILE)}")
    
    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=10) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            print("✓ Email authentication successful")
            return True
    except Exception as e:
        print(f"❌ Email connection failed: {str(e)}")
        return False


def send_emails_batch(email_list, report, desc="Sending emails", use_pool=True):
    """Send emails with progress tracking."""
    successful = 0
    failed = 0
    
    # Initialize rate limiter and connection pool
    rate_limiter = RateLimiter(max_per_minute=30, max_per_hour=500)
    connection_pool = None
    
    if use_pool:
        connection_pool = SMTPConnectionPool(
            SMTP_SERVER, SMTP_PORT, SENDER_EMAIL, SENDER_PASSWORD, pool_size=3
        )
    
    try:
        # Use tqdm with custom bar format
        with tqdm(total=len(email_list), desc=desc, unit="email", 
                  bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]') as pbar:
            
            for email in email_list:
                if use_pool:
                    success, message = send_email_with_pool(email, report, connection_pool, rate_limiter)
                else:
                    success, message = send_email_basic(email, report)
                
                if success:
                    successful += 1
                else:
                    failed += 1
                
                # Update progress bar with current stats
                pbar.set_postfix({
                    'Success': successful,
                    'Failed': failed
                }, refresh=True)
                pbar.update(1)
                
                # Random delay between 30-60 seconds (only if not using rate limiter)
                if not use_pool and email != email_list[-1]:
                    time.sleep(random.uniform(30, 60))
    
    finally:
        # Clean up connection pool
        if connection_pool:
            connection_pool.close_all()
    
    return successful, failed


def send_email_basic(to_email, report):
    """Basic email sending without connection pool (fallback)."""
    try:
        if not is_valid_email(to_email):
            raise ValueError("Invalid email format")

        msg = create_email_message(to_email)
        
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=30) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.send_message(msg)
            
        logging.info(f"Successfully sent email to {to_email}")
        report.mark_successful(to_email)
        return True, "Success"
        
    except Exception as e:
        error_msg = str(e)
        logging.error(f"Error sending to {to_email}: {error_msg}")
        report.mark_failed(to_email, error_msg)
        return False, error_msg


def print_summary(report, successful, failed, total):
    """Print sending summary."""
    print("\n" + "="*70)
    print(" "*20 + "E M A I L   S U M M A R Y")
    print("="*70)
    print(f"Total emails processed: {total}")
    print(f"✓ Successful sends: {successful}")
    print(f"✗ Failed sends: {failed}")
    
    if total > 0:
        success_rate = (successful / total) * 100
        print(f"Success rate: {success_rate:.2f}%")
    
    stats = report.get_statistics()
    print(f"\nOverall Statistics:")
    print(f"  Total successful (all time): {stats['total_successful']}")
    print(f"  Total failed (all time): {stats['total_failed']}")
    print("="*70)


def show_main_menu():
    """Display main menu."""
    print("\n" + "="*70)
    print(" "*15 + "EMAIL SENDER - MAIN MENU")
    print("="*70)
    print("1. Send Emails (from code)")
    print("2. Send Emails (from email_list.txt)")
    print("3. Send Emails (from email_list.csv)")
    print("4. Retry Failed Emails")
    print("5. View Reports")
    print("6. Export Failed Emails")
    print("7. Clear All Reports (Reset)")
    print("8. Exit")
    print("="*70)


def load_emails_from_code():
    """Load emails from the hardcoded list in the script."""
    emails = [
        "1-cv@infopersonnel.co.za",
        "10-recruitment@reagetswemininggroup.co.za",
        "11-rudith@newrak.co.za",
        "12-kim@pereirassteelworks.co.za",
        "2-kroondal.hr@glencore.co.za",
        "23.lebogangm@dynaniclabour.co.za",
        "3-recruitment@bafokengplatinum.co.za",
        "4-recruitment@bosha.co.za",
    ]
    return emails


def process_emails(email_list, report):
    """Process a list of emails."""
    # Validate and filter emails
    valid_emails = [email for email in email_list if is_valid_email(email)]
    
    if not valid_emails:
        print("\n❌ No valid emails found to process!")
        return
    
    print(f"\n✓ Found {len(valid_emails)} valid emails")
    
    # Filter out already sent emails
    pending_emails = [email for email in valid_emails if not report.is_already_sent(email)]
    already_sent_count = len(valid_emails) - len(pending_emails)
    
    if already_sent_count > 0:
        print(f"ℹ️  {already_sent_count} email(s) already sent successfully (skipping)")
    
    if not pending_emails:
        print("\n✓ All emails have been sent successfully!")
        return
    
    print(f"\n📧 {len(pending_emails)} new email(s) to process")
    confirm = input("Continue with sending emails? (y/n): ").lower()
    if confirm != 'y':
        print("\n❌ Operation cancelled by user")
        return
    
    # Ask about using connection pool
    use_pool = input("Use connection pool for better performance? (y/n): ").lower() == 'y'
    
    # Send emails
    print(f"\n🚀 Starting to send {len(pending_emails)} email(s)...\n")
    successful, failed = send_emails_batch(pending_emails, report, use_pool=use_pool)
    
    # Print summary
    print_summary(report, successful, failed, len(pending_emails))


def retry_failed_emails(report):
    """Retry sending failed emails."""
    failed_emails = report.get_failed_emails()
    
    if not failed_emails:
        print("\n✓ No failed emails to retry!")
        return
    
    print(f"\n🔄 Found {len(failed_emails)} failed email(s)")
    
    # Show failure details
    print("\nFailed emails:")
    for i, email in enumerate(failed_emails[:10], 1):
        print(f"  {i}. {email}")
    
    if len(failed_emails) > 10:
        print(f"  ... and {len(failed_emails) - 10} more")
    
    confirm = input(f"\nRetry sending to {len(failed_emails)} failed email(s)? (y/n): ").lower()
    if confirm != 'y':
        print("\n❌ Operation cancelled")
        return
    
    # Ask about using connection pool
    use_pool = input("Use connection pool for better performance? (y/n): ").lower() == 'y'
    
    print(f"\n🔄 Retrying {len(failed_emails)} failed email(s)...\n")
    successful, failed = send_emails_batch(failed_emails, report, "Retrying failed emails", use_pool=use_pool)
    
    print_summary(report, successful, failed, len(failed_emails))


def clear_reports(report):
    """Clear all reports and start fresh."""
    print("\n⚠️  WARNING: This will delete all sending history!")
    confirm = input("Are you sure you want to continue? (yes/no): ").lower()
    
    if confirm == 'yes':
        report.data = report._create_empty_report()
        report.save_report()
        print("\n✓ All reports cleared successfully!")
    else:
        print("\n❌ Operation cancelled")


def main():
    """Main function with menu system."""
    print("\n" + "="*70)
    print(" "*15 + "EMAIL SENDER - APPLICATION BOT")
    print("="*70)
    
    # Initialize report
    report = EmailReport(report_file)
    email_manager = EmailListManager(script_dir)
    
    # Perform setup checks
    if not setup_check():
        print("\n❌ Setup check failed. Please fix the errors and try again.")
        input("\nPress Enter to exit...")
        return
    
    while True:
        show_main_menu()
        choice = input("\nEnter your choice (1-8): ").strip()
        
        if choice == '1':
            # Send from hardcoded list
            emails = load_emails_from_code()
            process_emails(emails, report)
        
        elif choice == '2':
            # Send from text file
            emails = email_manager.load_from_txt()
            if not emails:
                print("\n❌ No emails found in email_list.txt")
                print(f"Create a file at: {email_manager.emails_file}")
            else:
                process_emails(emails, report)
        
        elif choice == '3':
            # Send from CSV
            emails = email_manager.load_from_csv()
            if not emails:
                print("\n❌ No emails found in email_list.csv")
                print(f"Create a CSV file at: {email_manager.csv_file}")
            else:
                process_emails(emails, report)
        
        elif choice == '4':
            # Retry failed emails
            retry_failed_emails(report)
        
        elif choice == '5':
            # View reports
            viewer = ReportViewer(report_file)
            print("\n1. Summary")
            print("2. Failed Details")
            print("3. Successful Details")
            print("4. Failure Analysis")
            sub_choice = input("\nChoice: ").strip()
            
            if sub_choice == '1':
                viewer.show_summary()
            elif sub_choice == '2':
                viewer.show_failed_details()
            elif sub_choice == '3':
                viewer.show_successful_details()
            elif sub_choice == '4':
                viewer.analyze_failure_patterns()
        
        elif choice == '6':
            # Export failed emails
            viewer = ReportViewer(report_file)
            viewer.export_failed_to_file()
        
        elif choice == '7':
            # Clear reports
            clear_reports(report)
        
        elif choice == '8':
            # Exit
            print("\n👋 Thank you for using Email Sender!")
            print("Goodbye!")
            break
        
        else:
            print("\n❌ Invalid choice! Please try again.")
        
        if choice != '8':
            input("\nPress Enter to continue...")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Process interrupted by user")
        logging.warning("Process interrupted by user")
    except Exception as e:
        print(f"\n\n❌ An unexpected error occurred: {str(e)}")
        logging.error(f"Unexpected error: {str(e)}")
    
    print("\nPress Enter to exit...")
    input()