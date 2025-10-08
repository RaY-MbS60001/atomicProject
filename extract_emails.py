import re
from tqdm import tqdm
import os
from datetime import datetime

def extract_emails_fast(input_file):
    """
    Fast email extraction with progress bar
    """
    
    # Email regex pattern
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    
    # Get file size for progress bar
    file_size = os.path.getsize(input_file)
    
    # Generate output filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f'extracted_emails_{timestamp}.txt'
    
    print(f"📧 Starting email extraction from: {input_file}")
    print(f"📄 File size: {file_size / (1024*1024):.2f} MB\n")
    
    emails = set()
    
    # Read file in chunks for speed with progress bar
    chunk_size = 1024 * 1024  # 1MB chunks
    
    with open(input_file, 'r', encoding='utf-8', errors='ignore') as file:
        with tqdm(total=file_size, unit='B', unit_scale=True, desc="Processing") as pbar:
            while True:
                chunk = file.read(chunk_size)
                if not chunk:
                    break
                
                # Find emails in chunk
                found_emails = re.findall(email_pattern, chunk)
                emails.update(found_emails)
                
                # Update progress bar
                pbar.update(len(chunk.encode('utf-8')))
    
    # Sort emails alphabetically
    sorted_emails = sorted(emails, key=str.lower)
    
    # Write to output file
    print(f"\n💾 Saving {len(sorted_emails)} unique emails to: {output_file}")
    
    with open(output_file, 'w', encoding='utf-8') as out_file:
        out_file.write(f"Total Unique Emails Found: {len(sorted_emails)}\n")
        out_file.write(f"Extraction Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        out_file.write("=" * 60 + "\n\n")
        
        for email in sorted_emails:
            out_file.write(email + '\n')
    
    print(f"✅ Done! Found {len(sorted_emails)} unique email addresses")
    print(f"📁 Saved to: {output_file}")
    
    return sorted_emails, output_file

# Main execution
if __name__ == "__main__":
    # Replace with your txt file name
    INPUT_FILE = 'newToMergeEmailList.txt'
    
    # Check if file exists
    if not os.path.exists(INPUT_FILE):
        print(f"❌ Error: File '{INPUT_FILE}' not found!")
        print("Please make sure the file is in the same folder as this script.")
    else:
        emails, output = extract_emails_fast(INPUT_FILE)
        
        # Optional: Display first 10 emails as preview
        if emails:
            print(f"\n📋 Preview (first 10 emails):")
            for email in list(emails)[:10]:
                print(f"  • {email}")
            if len(emails) > 10:
                print(f"  ... and {len(emails) - 10} more")