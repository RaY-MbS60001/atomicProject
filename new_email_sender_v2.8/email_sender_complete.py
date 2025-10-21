# email_sender_complete.py
"""
Complete email sender with all features integrated.
"""

import os
import sys
import signal
from email_sender_enhanced import *
from progress_manager import ProgressManager
from batch_processor import BatchProcessor
from email_validator import EmailValidator
from template_manager import TemplateManager

# Global progress manager for signal handling
progress_mgr = None

def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully."""
    print("\n\n⚠️  Interrupt received!")
    if progress_mgr:
        progress_mgr.pause_session()
    print("Progress saved. You can resume later.")
    sys.exit(0)

# Register signal handler
signal.signal(signal.SIGINT, signal_handler)


def advanced_send_with_resume(email_list, report, progress_manager):
    """Send emails with pause/resume capability."""
    global progress_mgr
    progress_mgr = progress_manager  # ✅ Fixed: assign parameter to global

    # Check if we can resume
    start_index = 0
    if progress_mgr.can_resume():
        resume = input("\n📋 Previous session found. Resume? (y/n): ").lower()
        if resume == 'y':
            start_index = progress_mgr.get_resume_point()
            print(f"✓ Resuming from email #{start_index + 1}")
            progress_mgr.resume_session()
        else:
            progress_mgr.clear_progress()

    # Start new session if not resuming
    if start_index == 0:
        progress_mgr.start_session()

    # Filter emails
    emails_to_send = email_list[start_index:]

    # Initialize components
    rate_limiter = RateLimiter(max_per_minute=30, max_per_hour=500)
    connection_pool = SMTPConnectionPool(
        SMTP_SERVER, SMTP_PORT, SENDER_EMAIL, SENDER_PASSWORD, pool_size=3
    )

    successful = 0
    failed = 0

    try:
        with tqdm(total=len(emails_to_send), desc="Sending emails", unit="email",
                  initial=0, bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]') as pbar:

            for idx, email in enumerate(emails_to_send, start=start_index):
                success, message = send_email_with_pool(email, report, connection_pool, rate_limiter)

                if success:
                    successful += 1
                else:
                    failed += 1

                # Update progress
                progress_mgr.mark_email_sent(email, idx)

                pbar.set_postfix({'Success': successful, 'Failed': failed}, refresh=True)
                pbar.update(1)

    finally:
        connection_pool.close_all()

    return successful, failed


def main_menu_enhanced():
    """Enhanced main menu with all features."""
    report = EmailReport(report_file)
    progress_manager = ProgressManager()  # ✅ Changed variable name here too
    batch_processor = BatchProcessor(batch_size=50)
    validator = EmailValidator()
    
    while True:
        print("\n" + "="*70)
        print(" "*12 + "EMAIL SENDER - COMPLETE EDITION")
        print("="*70)
        print("📧 SENDING")
        print("  1. Send Emails (with resume)")
        print("  2. Send in Batches")
        print("  3. Retry Failed Emails")
        print("\n📊 REPORTS & ANALYSIS")
        print("  4. View Reports")
        print("  5. View Session Status")
        print("  6. Export Failed Emails")
        print("\n🔧 TOOLS")
        print("  7. Validate Email List")
        print("  8. Clear All Data")
        print("\n⚙️  SETTINGS")
        print("  9. View/Edit Configuration")
        print(" 10. Test Email Connection")
        print("\n 11. Exit")
        print("="*70)
        
        choice = input("\nEnter your choice (1-11): ").strip()
        
        try:
            if choice == '1':
                # Send with resume capability
                print("\nSelect email source:")
                print("1. From code")
                print("2. From email_list.txt")
                print("3. From email_list.csv")
                source = input("Choice: ").strip()
                
                emails = []
                if source == '1':
                    emails = load_emails_from_code()
                elif source == '2':
                    manager = EmailListManager(script_dir)
                    emails = manager.load_from_txt()
                elif source == '3':
                    manager = EmailListManager(script_dir)
                    emails = manager.load_from_csv()
                else:
                    print("❌ Invalid choice")
                    continue
                
                if not emails:
                    print("❌ No emails loaded")
                    continue
                
                # Validate emails
                valid_emails = [e for e in emails if is_valid_email(e)]
                pending_emails = [e for e in valid_emails if not report.is_already_sent(e)]
                
                print(f"\n✓ Loaded: {len(emails)}")
                print(f"✓ Valid: {len(valid_emails)}")
                print(f"✓ Pending: {len(pending_emails)}")
                
                if not pending_emails:
                    print("\n✓ All emails already sent!")
                    continue
                
                confirm = input(f"\nSend to {len(pending_emails)} emails? (y/n): ").lower()
                if confirm != 'y':
                    print("❌ Cancelled")
                    continue
                
                print("\n🚀 Starting email sending (Press Ctrl+C to pause)...\n")
                successful, failed = advanced_send_with_resume(pending_emails, report, progress_manager)  # ✅ Fixed
                print_summary(report, successful, failed, len(pending_emails))
                
                # Clear progress after successful completion
                if successful + failed == len(pending_emails):
                    progress_manager.clear_progress()
            
            elif choice == '2':
                # Batch processing
                print("\nSelect email source:")
                print("1. From email_list.txt")
                print("2. From email_list.csv")
                source = input("Choice: ").strip()
                
                manager = EmailListManager(script_dir)
                emails = []
                
                if source == '1':
                    emails = manager.load_from_txt()
                elif source == '2':
                    emails = manager.load_from_csv()
                else:
                    print("❌ Invalid choice")
                    continue
                
                if not emails:
                    print("❌ No emails loaded")
                    continue
                
                valid_emails = [e for e in emails if is_valid_email(e)]
                pending_emails = [e for e in valid_emails if not report.is_already_sent(e)]
                
                if not pending_emails:
                    print("\n✓ All emails already sent!")
                    continue
                
                # Show batch status
                batch_processor.show_status(len(pending_emails))
                
                batch_size = input(f"\nBatch size (default 50): ").strip()
                if batch_size.isdigit():
                    batch_processor.batch_size = int(batch_size)
                
                batches = batch_processor.get_batches(pending_emails)
                print(f"\n📦 Will process {len(batches)} batch(es)")
                
                confirm = input("Start batch processing? (y/n): ").lower()
                if confirm != 'y':
                    print("❌ Cancelled")
                    continue
                
                total_successful = 0
                total_failed = 0
                
                for batch_num, batch in enumerate(batches, 1):
                    print(f"\n{'='*70}")
                    print(f"BATCH {batch_num}/{len(batches)} - {len(batch)} emails")
                    print('='*70)
                    
                    successful, failed = send_emails_batch(batch, report, 
                                                          f"Batch {batch_num}/{len(batches)}")
                    
                    total_successful += successful
                    total_failed += failed
                    
                    # Mark batch as processed
                    for email in batch:
                        batch_processor.mark_processed(email)
                    
                    if batch_num < len(batches):
                        cont = input(f"\nContinue to batch {batch_num + 1}? (y/n): ").lower()
                        if cont != 'y':
                            print("⏸️  Batch processing paused")
                            break
                
                print(f"\n{'='*70}")
                print("BATCH PROCESSING SUMMARY")
                print('='*70)
                print(f"Batches completed: {batch_num}/{len(batches)}")
                print(f"Total successful: {total_successful}")
                print(f"Total failed: {total_failed}")
                print('='*70)
            
            elif choice == '3':
                # Retry failed emails
                retry_failed_emails(report)
            
            elif choice == '4':
                # View reports
                viewer = ReportViewer(report_file)
                
                print("\n1. Summary")
                print("2. Failed Details")
                print("3. Successful Details")
                print("4. Failure Analysis")
                print("5. Back")
                
                sub_choice = input("\nChoice: ").strip()
                
                if sub_choice == '1':
                    viewer.show_summary()
                elif sub_choice == '2':
                    viewer.show_failed_details()
                elif sub_choice == '3':
                    viewer.show_successful_details()
                elif sub_choice == '4':
                    viewer.analyze_failure_patterns()
            
            elif choice == '5':
                # View session status
                manager = EmailListManager(script_dir)
                all_emails = manager.load_all_sources()
                progress_manager.show_status(len(all_emails))  # ✅ Fixed
            
            elif choice == '6':
                # Export failed emails
                viewer = ReportViewer(report_file)
                viewer.export_failed_to_file()
            
            elif choice == '7':
                # Validate email list
                print("\nSelect validation source:")
                print("1. From email_list.txt")
                print("2. From email_list.csv")
                print("3. Enter manually")
                
                val_choice = input("Choice: ").strip()
                
                emails = []
                manager = EmailListManager(script_dir)
                
                if val_choice == '1':
                    emails = manager.load_from_txt()
                elif val_choice == '2':
                    emails = manager.load_from_csv()
                elif val_choice == '3':
                    print("\nEnter emails (one per line, empty line to finish):")
                    while True:
                        email = input().strip()
                        if not email:
                            break
                        emails.append(email)
                else:
                    print("❌ Invalid choice")
                    continue
                
                if not emails:
                    print("❌ No emails to validate")
                    continue
                
                print(f"\n🔍 Validating {len(emails)} email(s)...")
                
                check_dns = input("Check DNS/MX records? (y/n): ").lower() == 'y'
                
                print("\nValidating...")
                results = validator.validate_batch(emails, check_dns=check_dns, check_smtp=False)
                
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
                    print("\nSuspicious emails:")
                    for email in results['suspicious'][:10]:
                        print(f"  ⚠ {email}")
                    if len(results['suspicious']) > 10:
                        print(f"  ... and {len(results['suspicious']) - 10} more")
                
                # Save valid emails
                if results['valid']:
                    save = input(f"\nSave {len(results['valid'])} valid emails? (y/n): ").lower()
                    if save == 'y':
                        filename = input("Filename (default: valid_emails.txt): ").strip()
                        filename = filename or "valid_emails.txt"
                        with open(os.path.join(script_dir, filename), 'w') as f:
                            f.write('\n'.join(results['valid']))
                        print(f"✓ Saved to {filename}")
            
            elif choice == '8':
                # Clear all data
                print("\n⚠️  WARNING: This will delete:")
                print("  - Email sending reports")
                print("  - Session progress")
                print("  - Batch processing state")
                print("  - Log files")
                
                confirm = input("\nType 'DELETE' to confirm: ").strip()
                
                if confirm == 'DELETE':
                    # Clear report
                    report.data = report._create_empty_report()
                    report.save_report()
                    
                    # Clear progress
                    progress_manager.clear_progress()  # ✅ Fixed
                    
                    # Clear batch state
                    batch_processor.reset()
                    
                    # Clear logs (optional)
                    clear_logs = input("Also clear log files? (y/n): ").lower()
                    if clear_logs == 'y':
                        if os.path.exists(log_file):
                            os.remove(log_file)
                    
                    print("\n✓ All data cleared successfully!")
                else:
                    print("❌ Cancelled")
            
            elif choice == '9':
                # View/Edit configuration
                print("\n" + "="*70)
                print(" "*22 + "CONFIGURATION")
                print("="*70)
                print("\nCurrent Settings:")
                print(f"  SMTP Server: {SMTP_SERVER}")
                print(f"  SMTP Port: {SMTP_PORT}")
                print(f"  Sender Email: {SENDER_EMAIL}")
                print(f"  Delay Range: 30-60 seconds")
                print(f"  Rate Limit: 30/minute, 500/hour")
                print("\nNote: Edit config.json to change settings")
                print("="*70)
            
            elif choice == '10':
                # Test email connection
                print("\n🔌 Testing email connection...")
                if setup_check():
                    print("✓ Connection test successful!")
                    
                    # Optional: send test email
                    test = input("\nSend test email to yourself? (y/n): ").lower()
                    if test == 'y':
                        test_report = EmailReport(':memory:')  # Temporary report
                        success, msg = send_email_basic(SENDER_EMAIL, test_report)
                        if success:
                            print(f"✓ Test email sent to {SENDER_EMAIL}")
                        else:
                            print(f"❌ Test failed: {msg}")
                else:
                    print("❌ Connection test failed")
            
            elif choice == '11':
                # Exit
                print("\n" + "="*70)
                print(" "*18 + "THANK YOU FOR USING")
                print(" "*15 + "EMAIL SENDER COMPLETE EDITION")
                print("="*70)
                print("\n👋 Goodbye!")
                break
            
            else:
                print("\n❌ Invalid choice! Please enter 1-11.")
        
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")
            logging.error(f"Menu error: {str(e)}")
        
        if choice != '11':
            input("\n⏎ Press Enter to continue...")


if __name__ == "__main__":
    try:
        print("\n" + "="*70)
        print(" "*10 + "EMAIL SENDER - COMPLETE EDITION v2.0")
        print(" "*15 + "Advanced Bulk Email Application System")
        print("="*70)
        print("\nFeatures:")
        print("  ✓ Persistent tracking (no duplicate sends)")
        print("  ✓ Pause & resume capability")
        print("  ✓ Batch processing")
        print("  ✓ Email validation")
        print("  ✓ Rate limiting")
        print("  ✓ Connection pooling")
        print("  ✓ Detailed reports & analytics")
        print("="*70)
        
        input("\nPress Enter to start...")
        
        main_menu_enhanced()
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Process interrupted by user")
        logging.warning("Process interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {str(e)}")
        logging.error(f"Unexpected error: {str(e)}", exc_info=True)
    finally:
        print("\nPress Enter to exit...")
        input()# email_sender_complete.py
"""
Complete email sender with all features integrated.
"""

import os
import sys
import signal
from email_sender_enhanced import *
from progress_manager import ProgressManager
from batch_processor import BatchProcessor
from email_validator import EmailValidator
from template_manager import TemplateManager

# Global progress manager for signal handling
progress_mgr = None

def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully."""
    print("\n\n⚠️  Interrupt received!")
    if progress_mgr:
        progress_mgr.pause_session()
    print("Progress saved. You can resume later.")
    sys.exit(0)

# Register signal handler
signal.signal(signal.SIGINT, signal_handler)


def advanced_send_with_resume(email_list, report, progress_manager):
    """Send emails with pause/resume capability."""
    global progress_mgr
    progress_mgr = progress_manager  # ✅ Fixed: assign parameter to global

    # Check if we can resume
    start_index = 0
    if progress_mgr.can_resume():
        resume = input("\n📋 Previous session found. Resume? (y/n): ").lower()
        if resume == 'y':
            start_index = progress_mgr.get_resume_point()
            print(f"✓ Resuming from email #{start_index + 1}")
            progress_mgr.resume_session()
        else:
            progress_mgr.clear_progress()

    # Start new session if not resuming
    if start_index == 0:
        progress_mgr.start_session()

    # Filter emails
    emails_to_send = email_list[start_index:]

    # Initialize components
    rate_limiter = RateLimiter(max_per_minute=30, max_per_hour=500)
    connection_pool = SMTPConnectionPool(
        SMTP_SERVER, SMTP_PORT, SENDER_EMAIL, SENDER_PASSWORD, pool_size=3
    )

    successful = 0
    failed = 0

    try:
        with tqdm(total=len(emails_to_send), desc="Sending emails", unit="email",
                  initial=0, bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]') as pbar:

            for idx, email in enumerate(emails_to_send, start=start_index):
                success, message = send_email_with_pool(email, report, connection_pool, rate_limiter)

                if success:
                    successful += 1
                else:
                    failed += 1

                # Update progress
                progress_mgr.mark_email_sent(email, idx)

                pbar.set_postfix({'Success': successful, 'Failed': failed}, refresh=True)
                pbar.update(1)

    finally:
        connection_pool.close_all()

    return successful, failed


def main_menu_enhanced():
    """Enhanced main menu with all features."""
    report = EmailReport(report_file)
    progress_manager = ProgressManager()  # ✅ Changed variable name here too
    batch_processor = BatchProcessor(batch_size=50)
    validator = EmailValidator()
    
    while True:
        print("\n" + "="*70)
        print(" "*12 + "EMAIL SENDER - COMPLETE EDITION")
        print("="*70)
        print("📧 SENDING")
        print("  1. Send Emails (with resume)")
        print("  2. Send in Batches")
        print("  3. Retry Failed Emails")
        print("\n📊 REPORTS & ANALYSIS")
        print("  4. View Reports")
        print("  5. View Session Status")
        print("  6. Export Failed Emails")
        print("\n🔧 TOOLS")
        print("  7. Validate Email List")
        print("  8. Clear All Data")
        print("\n⚙️  SETTINGS")
        print("  9. View/Edit Configuration")
        print(" 10. Test Email Connection")
        print("\n 11. Exit")
        print("="*70)
        
        choice = input("\nEnter your choice (1-11): ").strip()
        
        try:
            if choice == '1':
                # Send with resume capability
                print("\nSelect email source:")
                print("1. From code")
                print("2. From email_list.txt")
                print("3. From email_list.csv")
                source = input("Choice: ").strip()
                
                emails = []
                if source == '1':
                    emails = load_emails_from_code()
                elif source == '2':
                    manager = EmailListManager(script_dir)
                    emails = manager.load_from_txt()
                elif source == '3':
                    manager = EmailListManager(script_dir)
                    emails = manager.load_from_csv()
                else:
                    print("❌ Invalid choice")
                    continue
                
                if not emails:
                    print("❌ No emails loaded")
                    continue
                
                # Validate emails
                valid_emails = [e for e in emails if is_valid_email(e)]
                pending_emails = [e for e in valid_emails if not report.is_already_sent(e)]
                
                print(f"\n✓ Loaded: {len(emails)}")
                print(f"✓ Valid: {len(valid_emails)}")
                print(f"✓ Pending: {len(pending_emails)}")
                
                if not pending_emails:
                    print("\n✓ All emails already sent!")
                    continue
                
                confirm = input(f"\nSend to {len(pending_emails)} emails? (y/n): ").lower()
                if confirm != 'y':
                    print("❌ Cancelled")
                    continue
                
                print("\n🚀 Starting email sending (Press Ctrl+C to pause)...\n")
                successful, failed = advanced_send_with_resume(pending_emails, report, progress_manager)  # ✅ Fixed
                print_summary(report, successful, failed, len(pending_emails))
                
                # Clear progress after successful completion
                if successful + failed == len(pending_emails):
                    progress_manager.clear_progress()
            
            elif choice == '2':
                # Batch processing
                print("\nSelect email source:")
                print("1. From email_list.txt")
                print("2. From email_list.csv")
                source = input("Choice: ").strip()
                
                manager = EmailListManager(script_dir)
                emails = []
                
                if source == '1':
                    emails = manager.load_from_txt()
                elif source == '2':
                    emails = manager.load_from_csv()
                else:
                    print("❌ Invalid choice")
                    continue
                
                if not emails:
                    print("❌ No emails loaded")
                    continue
                
                valid_emails = [e for e in emails if is_valid_email(e)]
                pending_emails = [e for e in valid_emails if not report.is_already_sent(e)]
                
                if not pending_emails:
                    print("\n✓ All emails already sent!")
                    continue
                
                # Show batch status
                batch_processor.show_status(len(pending_emails))
                
                batch_size = input(f"\nBatch size (default 50): ").strip()
                if batch_size.isdigit():
                    batch_processor.batch_size = int(batch_size)
                
                batches = batch_processor.get_batches(pending_emails)
                print(f"\n📦 Will process {len(batches)} batch(es)")
                
                confirm = input("Start batch processing? (y/n): ").lower()
                if confirm != 'y':
                    print("❌ Cancelled")
                    continue
                
                total_successful = 0
                total_failed = 0
                
                for batch_num, batch in enumerate(batches, 1):
                    print(f"\n{'='*70}")
                    print(f"BATCH {batch_num}/{len(batches)} - {len(batch)} emails")
                    print('='*70)
                    
                    successful, failed = send_emails_batch(batch, report, 
                                                          f"Batch {batch_num}/{len(batches)}")
                    
                    total_successful += successful
                    total_failed += failed
                    
                    # Mark batch as processed
                    for email in batch:
                        batch_processor.mark_processed(email)
                    
                    if batch_num < len(batches):
                        cont = input(f"\nContinue to batch {batch_num + 1}? (y/n): ").lower()
                        if cont != 'y':
                            print("⏸️  Batch processing paused")
                            break
                
                print(f"\n{'='*70}")
                print("BATCH PROCESSING SUMMARY")
                print('='*70)
                print(f"Batches completed: {batch_num}/{len(batches)}")
                print(f"Total successful: {total_successful}")
                print(f"Total failed: {total_failed}")
                print('='*70)
            
            elif choice == '3':
                # Retry failed emails
                retry_failed_emails(report)
            
            elif choice == '4':
                # View reports
                viewer = ReportViewer(report_file)
                
                print("\n1. Summary")
                print("2. Failed Details")
                print("3. Successful Details")
                print("4. Failure Analysis")
                print("5. Back")
                
                sub_choice = input("\nChoice: ").strip()
                
                if sub_choice == '1':
                    viewer.show_summary()
                elif sub_choice == '2':
                    viewer.show_failed_details()
                elif sub_choice == '3':
                    viewer.show_successful_details()
                elif sub_choice == '4':
                    viewer.analyze_failure_patterns()
            
            elif choice == '5':
                # View session status
                manager = EmailListManager(script_dir)
                all_emails = manager.load_all_sources()
                progress_manager.show_status(len(all_emails))  # ✅ Fixed
            
            elif choice == '6':
                # Export failed emails
                viewer = ReportViewer(report_file)
                viewer.export_failed_to_file()
            
            elif choice == '7':
                # Validate email list
                print("\nSelect validation source:")
                print("1. From email_list.txt")
                print("2. From email_list.csv")
                print("3. Enter manually")
                
                val_choice = input("Choice: ").strip()
                
                emails = []
                manager = EmailListManager(script_dir)
                
                if val_choice == '1':
                    emails = manager.load_from_txt()
                elif val_choice == '2':
                    emails = manager.load_from_csv()
                elif val_choice == '3':
                    print("\nEnter emails (one per line, empty line to finish):")
                    while True:
                        email = input().strip()
                        if not email:
                            break
                        emails.append(email)
                else:
                    print("❌ Invalid choice")
                    continue
                
                if not emails:
                    print("❌ No emails to validate")
                    continue
                
                print(f"\n🔍 Validating {len(emails)} email(s)...")
                
                check_dns = input("Check DNS/MX records? (y/n): ").lower() == 'y'
                
                print("\nValidating...")
                results = validator.validate_batch(emails, check_dns=check_dns, check_smtp=False)
                
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
                    print("\nSuspicious emails:")
                    for email in results['suspicious'][:10]:
                        print(f"  ⚠ {email}")
                    if len(results['suspicious']) > 10:
                        print(f"  ... and {len(results['suspicious']) - 10} more")
                
                # Save valid emails
                if results['valid']:
                    save = input(f"\nSave {len(results['valid'])} valid emails? (y/n): ").lower()
                    if save == 'y':
                        filename = input("Filename (default: valid_emails.txt): ").strip()
                        filename = filename or "valid_emails.txt"
                        with open(os.path.join(script_dir, filename), 'w') as f:
                            f.write('\n'.join(results['valid']))
                        print(f"✓ Saved to {filename}")
            
            elif choice == '8':
                # Clear all data
                print("\n⚠️  WARNING: This will delete:")
                print("  - Email sending reports")
                print("  - Session progress")
                print("  - Batch processing state")
                print("  - Log files")
                
                confirm = input("\nType 'DELETE' to confirm: ").strip()
                
                if confirm == 'DELETE':
                    # Clear report
                    report.data = report._create_empty_report()
                    report.save_report()
                    
                    # Clear progress
                    progress_manager.clear_progress()  # ✅ Fixed
                    
                    # Clear batch state
                    batch_processor.reset()
                    
                    # Clear logs (optional)
                    clear_logs = input("Also clear log files? (y/n): ").lower()
                    if clear_logs == 'y':
                        if os.path.exists(log_file):
                            os.remove(log_file)
                    
                    print("\n✓ All data cleared successfully!")
                else:
                    print("❌ Cancelled")
            
            elif choice == '9':
                # View/Edit configuration
                print("\n" + "="*70)
                print(" "*22 + "CONFIGURATION")
                print("="*70)
                print("\nCurrent Settings:")
                print(f"  SMTP Server: {SMTP_SERVER}")
                print(f"  SMTP Port: {SMTP_PORT}")
                print(f"  Sender Email: {SENDER_EMAIL}")
                print(f"  Delay Range: 30-60 seconds")
                print(f"  Rate Limit: 30/minute, 500/hour")
                print("\nNote: Edit config.json to change settings")
                print("="*70)
            
            elif choice == '10':
                # Test email connection
                print("\n🔌 Testing email connection...")
                if setup_check():
                    print("✓ Connection test successful!")
                    
                    # Optional: send test email
                    test = input("\nSend test email to yourself? (y/n): ").lower()
                    if test == 'y':
                        test_report = EmailReport(':memory:')  # Temporary report
                        success, msg = send_email_basic(SENDER_EMAIL, test_report)
                        if success:
                            print(f"✓ Test email sent to {SENDER_EMAIL}")
                        else:
                            print(f"❌ Test failed: {msg}")
                else:
                    print("❌ Connection test failed")
            
            elif choice == '11':
                # Exit
                print("\n" + "="*70)
                print(" "*18 + "THANK YOU FOR USING")
                print(" "*15 + "EMAIL SENDER COMPLETE EDITION")
                print("="*70)
                print("\n👋 Goodbye!")
                break
            
            else:
                print("\n❌ Invalid choice! Please enter 1-11.")
        
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")
            logging.error(f"Menu error: {str(e)}")
        
        if choice != '11':
            input("\n⏎ Press Enter to continue...")


if __name__ == "__main__":
    try:
        print("\n" + "="*70)
        print(" "*10 + "EMAIL SENDER - COMPLETE EDITION v2.0")
        print(" "*15 + "Advanced Bulk Email Application System")
        print("="*70)
        print("\nFeatures:")
        print("  ✓ Persistent tracking (no duplicate sends)")
        print("  ✓ Pause & resume capability")
        print("  ✓ Batch processing")
        print("  ✓ Email validation")
        print("  ✓ Rate limiting")
        print("  ✓ Connection pooling")
        print("  ✓ Detailed reports & analytics")
        print("="*70)
        
        input("\nPress Enter to start...")
        
        main_menu_enhanced()
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Process interrupted by user")
        logging.warning("Process interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {str(e)}")
        logging.error(f"Unexpected error: {str(e)}", exc_info=True)
    finally:
        print("\nPress Enter to exit...")
        input()