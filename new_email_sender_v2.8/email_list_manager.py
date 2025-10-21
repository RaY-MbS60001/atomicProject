# email_list_manager.py
import csv
import json
import os

class EmailListManager:
    """Manage email lists from various sources."""
    
    def __init__(self, script_dir):
        self.script_dir = script_dir
        self.emails_file = os.path.join(script_dir, 'email_list.txt')
        self.csv_file = os.path.join(script_dir, 'email_list.csv')
    
    def load_from_txt(self):
        """Load emails from text file (one per line)."""
        if not os.path.exists(self.emails_file):
            return []
        
        with open(self.emails_file, 'r') as f:
            return [line.strip() for line in f if line.strip()]
    
    def load_from_csv(self):
        """Load emails from CSV file."""
        if not os.path.exists(self.csv_file):
            return []
        
        emails = []
        with open(self.csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Assuming CSV has 'email' column, adjust as needed
                if 'email' in row:
                    emails.append(row['email'])
        return emails
    
    def save_to_txt(self, emails):
        """Save emails to text file."""
        with open(self.emails_file, 'w') as f:
            f.write('\n'.join(emails))
    
    def deduplicate(self, emails):
        """Remove duplicate emails while preserving order."""
        seen = set()
        deduplicated = []
        for email in emails:
            email_lower = email.lower()
            if email_lower not in seen:
                seen.add(email_lower)
                deduplicated.append(email)
        return deduplicated
    
    def load_all_sources(self):
        """Load emails from all available sources."""
        all_emails = []
        
        # Load from text file
        txt_emails = self.load_from_txt()
        if txt_emails:
            print(f"✓ Loaded {len(txt_emails)} emails from text file")
            all_emails.extend(txt_emails)
        
        # Load from CSV
        csv_emails = self.load_from_csv()
        if csv_emails:
            print(f"✓ Loaded {len(csv_emails)} emails from CSV file")
            all_emails.extend(csv_emails)
        
        # Deduplicate
        all_emails = self.deduplicate(all_emails)
        print(f"✓ Total unique emails: {len(all_emails)}")
        
        return all_emails