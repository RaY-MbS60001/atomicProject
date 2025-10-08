import re
import os

def txt_to_python_list(input_file, output_file='email_list.py'):
    """
    Convert text file with emails to Python list format
    """
    
    print(f"📖 Reading emails from: {input_file}")
    
    emails = []
    
    # Read emails from file
    try:
        with open(input_file, 'r', encoding='utf-8', errors='ignore') as file:
            for line in file:
                line = line.strip()
                
                # Check if line contains an email
                if '@' in line and line:
                    # Skip header/separator lines
                    if not any(keyword in line for keyword in ['Total', 'Generated', 'Extraction', '===', '---', 'Source', 'Count']):
                        emails.append(line)
    
    except Exception as e:
        print(f"❌ Error reading file: {e}")
        return
    
    print(f"✅ Found {len(emails)} emails")
    
    # Create Python list format
    print(f"\n💾 Creating Python list in: {output_file}")
    
    with open(output_file, 'w', encoding='utf-8') as out_file:
        out_file.write("# Email list generated from: " + input_file + "\n")
        out_file.write("# Total emails: " + str(len(emails)) + "\n\n")
        out_file.write("email_list = [\n")
        
        for i, email in enumerate(emails):
            # Add comma except for last item
            if i < len(emails) - 1:
                out_file.write(f'    "{email}",\n')
            else:
                out_file.write(f'    "{email}"\n')
        
        out_file.write("]\n")
    
    print(f"✅ Python list created successfully!")
    print(f"\n📊 Summary:")
    print(f"   • Total emails: {len(emails)}")
    print(f"   • Output file: {output_file}")
    
    # Also print to console
    print(f"\n📋 Preview (first 5 emails):")
    for email in emails[:5]:
        print(f'    "{email}",')
    if len(emails) > 5:
        print(f"    ... and {len(emails) - 5} more")
    
    # Display how to use the list
    print(f"\n💡 Usage:")
    print(f"   To use this list in your Python script:")
    print(f"   1. Copy the content from '{output_file}'")
    print(f"   2. Or import it: from {output_file.replace('.py', '')} import email_list")
    
    return emails

# Main execution
if __name__ == "__main__":
    INPUT_FILE = 'cleaned_emails_20251008_132244.txt'  
    OUTPUT_FILE = 'ready_email_list.py'  
    
    print("=" * 70)
    print("📧 TXT TO PYTHON LIST CONVERTER")
    print("=" * 70)
    print()
    
    # Check if input file exists
    if not os.path.exists(INPUT_FILE):
        print(f"❌ File '{INPUT_FILE}' not found!")
        print(f"📁 Current directory: {os.getcwd()}\n")
        print("Available .txt files:")
        
        txt_files = [f for f in os.listdir('.') if f.endswith('.txt')]
        if txt_files:
            for idx, file in enumerate(txt_files, 1):
                print(f"   {idx}. {file}")
            
            choice = input("\nEnter file number or filename: ").strip()
            
            if choice.isdigit() and 1 <= int(choice) <= len(txt_files):
                INPUT_FILE = txt_files[int(choice) - 1]
            elif os.path.exists(choice):
                INPUT_FILE = choice
            else:
                print("❌ Invalid selection!")
                input("\nPress Enter to exit...")
                exit()
        else:
            print("   (No .txt files found)")
            input("\nPress Enter to exit...")
            exit()
    
    print()
    
    try:
        emails = txt_to_python_list(INPUT_FILE, OUTPUT_FILE)
        
        print("\n" + "=" * 70)
        input("\n✨ Press Enter to exit...")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        input("\nPress Enter to exit...")