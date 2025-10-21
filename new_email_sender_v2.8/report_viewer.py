# report_viewer.py
import json
import os
from datetime import datetime
from tabulate import tabulate  # pip install tabulate

class ReportViewer:
    """View and analyze email sending reports."""
    
    def __init__(self, report_path):
        self.report_path = report_path
        self.data = self.load_report()
    
    def load_report(self):
        """Load report from file."""
        if os.path.exists(self.report_path):
            with open(self.report_path, 'r') as f:
                return json.load(f)
        return None
    
    def show_summary(self):
        """Show summary statistics."""
        if not self.data:
            print("❌ No report found!")
            return
        
        stats = self.data.get('statistics', {})
        print("\n" + "="*70)
        print(" "*25 + "REPORT SUMMARY")
        print("="*70)
        print(f"Last Updated: {self.data.get('last_updated', 'N/A')}")
        print(f"\nTotal Successful: {stats.get('total_successful', 0)}")
        print(f"Total Failed: {stats.get('total_failed', 0)}")
        print(f"Total Attempts: {stats.get('total_attempts', 0)}")
        
        if stats.get('total_attempts', 0) > 0:
            success_rate = (stats.get('total_successful', 0) / stats.get('total_attempts', 0)) * 100
            print(f"Success Rate: {success_rate:.2f}%")
        print("="*70)
    
    def show_failed_details(self):
        """Show detailed information about failed emails."""
        if not self.data:
            print("❌ No report found!")
            return
        
        failed = self.data.get('failed', {})
        if not failed:
            print("\n✓ No failed emails!")
            return
        
        print("\n" + "="*70)
        print(" "*25 + "FAILED EMAILS")
        print("="*70)
        
        table_data = []
        for email, info in failed.items():
            attempts = info.get('attempts', 0)
            last_error = info.get('errors', [{}])[-1].get('message', 'Unknown') if info.get('errors') else 'Unknown'
            last_attempt = info.get('last_attempt', 'N/A')
            
            table_data.append([
                email[:40] + '...' if len(email) > 40 else email,
                attempts,
                last_error[:30] + '...' if len(last_error) > 30 else last_error,
                last_attempt[:19] if last_attempt != 'N/A' else 'N/A'
            ])
        
        headers = ['Email', 'Attempts', 'Last Error', 'Last Attempt']
        print(tabulate(table_data, headers=headers, tablefmt='grid'))
        print("="*70)
    
    def show_successful_details(self):
        """Show successful emails."""
        if not self.data:
            print("❌ No report found!")
            return
        
        successful = self.data.get('successful', {})
        if not successful:
            print("\n❌ No successful emails yet!")
            return
        
        print("\n" + "="*70)
        print(" "*23 + "SUCCESSFUL EMAILS")
        print("="*70)
        print(f"Total: {len(successful)}")
        
        # Show first 10 and last 10
        emails_list = list(successful.items())
        show_count = min(10, len(emails_list))
        
        print(f"\nFirst {show_count}:")
        for i, (email, info) in enumerate(emails_list[:show_count], 1):
            timestamp = info.get('timestamp', 'N/A')[:19]
            print(f"  {i}. {email} - {timestamp}")
        
        if len(emails_list) > 20:
            print(f"\n  ... ({len(emails_list) - 20} more) ...")
            
            print(f"\nLast 10:")
            for i, (email, info) in enumerate(emails_list[-10:], len(emails_list) - 9):
                timestamp = info.get('timestamp', 'N/A')[:19]
                print(f"  {i}. {email} - {timestamp}")
        elif len(emails_list) > 10:
            print(f"\nRemaining:")
            for i, (email, info) in enumerate(emails_list[10:], 11):
                timestamp = info.get('timestamp', 'N/A')[:19]
                print(f"  {i}. {email} - {timestamp}")
        
        print("="*70)
    
    def export_failed_to_file(self, output_file='failed_emails.txt'):
        """Export failed emails to a text file."""
        if not self.data:
            print("❌ No report found!")
            return
        
        failed = self.data.get('failed', {})
        if not failed:
            print("\n✓ No failed emails to export!")
            return
        
        output_path = os.path.join(os.path.dirname(self.report_path), output_file)
        with open(output_path, 'w') as f:
            for email in failed.keys():
                f.write(f"{email}\n")
        
        print(f"\n✓ Exported {len(failed)} failed emails to: {output_file}")
    
    def analyze_failure_patterns(self):
        """Analyze common failure patterns."""
        if not self.data:
            print("❌ No report found!")
            return
        
        failed = self.data.get('failed', {})
        if not failed:
            print("\n✓ No failures to analyze!")
            return
        
        print("\n" + "="*70)
        print(" "*22 + "FAILURE ANALYSIS")
        print("="*70)
        
        # Count error types
        error_types = {}
        for email, info in failed.items():
            errors = info.get('errors', [])
            if errors:
                last_error = errors[-1].get('message', 'Unknown')
                error_key = last_error[:50]  # First 50 chars
                error_types[error_key] = error_types.get(error_key, 0) + 1
        
        print("\nCommon Error Types:")
        for i, (error, count) in enumerate(sorted(error_types.items(), key=lambda x: x[1], reverse=True), 1):
            print(f"  {i}. [{count}x] {error}")
        
        # Count by attempts
        attempt_counts = {}
        for email, info in failed.items():
            attempts = info.get('attempts', 0)
            attempt_counts[attempts] = attempt_counts.get(attempts, 0) + 1
        
        print("\nAttempts Distribution:")
        for attempts in sorted(attempt_counts.keys()):
            count = attempt_counts[attempts]
            print(f"  {attempts} attempt(s): {count} email(s)")
        
        print("="*70)


def view_report_interactive():
    """Interactive report viewer."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    report_file = os.path.join(script_dir, 'email_report.json')
    
    viewer = ReportViewer(report_file)
    
    while True:
        print("\n" + "="*70)
        print(" "*22 + "REPORT VIEWER MENU")
        print("="*70)
        print("1. Show Summary")
        print("2. Show Failed Emails")
        print("3. Show Successful Emails")
        print("4. Analyze Failure Patterns")
        print("5. Export Failed Emails to File")
        print("6. Exit")
        print("="*70)
        
        choice = input("\nEnter your choice (1-6): ").strip()
        
        if choice == '1':
            viewer.show_summary()
        elif choice == '2':
            viewer.show_failed_details()
        elif choice == '3':
            viewer.show_successful_details()
        elif choice == '4':
            viewer.analyze_failure_patterns()
        elif choice == '5':
            viewer.export_failed_to_file()
        elif choice == '6':
            print("\n👋 Goodbye!")
            break
        else:
            print("\n❌ Invalid choice! Please try again.")
        
        input("\nPress Enter to continue...")


if __name__ == "__main__":
    view_report_interactive()