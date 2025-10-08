import re
import os
from datetime import datetime

def validate_email_syntax(email):
    """Check if email has valid syntax"""
    pattern = r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}$'
    return re.match(pattern, email) is not None

def clean_emails(input_file):
    """
    Extract unique non-Gmail emails only
    """
    
    print(f"Processing: {input_file}")
    
    # Read and clean emails
    emails = set()
    
    with open(input_file, 'r', encoding='utf-8', errors='ignore') as file:
        for line in file:
            line = line.strip()
            
            # Only process lines that look like emails
            if '@' in line and validate_email_syntax(line):
                email = line.lower()
                # Exclude Gmail
                if not email.endswith('@gmail.com'):
                    emails.add(email)
    
    # Generate output filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f'cleaned_emails_{timestamp}.txt'
    
    # Save clean list
    with open(output_file, 'w', encoding='utf-8') as out_file:
        for email in sorted(emails):
            out_file.write(email + '\n')
    
    print(f"\n✅ Done!")
    print(f"   Total emails: {len(emails)}")
    print(f"   Saved to: {output_file}")

# Main execution
if __name__ == "__main__":
    INPUT_FILE = 'toBeCleanedListOfEmails.txt' 
    
    if os.path.exists(INPUT_FILE):
        clean_emails(INPUT_FILE)
    else:
        print(f"❌ File not found: {INPUT_FILE}")
        print("\nAvailable files:")
        for f in os.listdir('.'):
            if f.endswith('.txt'):
                print(f"   • {f}")
    
    input("\nPress Enter to exit...")