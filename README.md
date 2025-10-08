# Email Extractor

A small Python utility to extract unique email addresses from large text files.

Features
- Streaming read (1MB chunks by default) to handle large files without loading everything into memory
- Progress bar using `tqdm`
- Outputs a timestamped text file containing unique, sorted email addresses

Requirements
- Python 3.7+
- tqdm (for progress bar)

Installation
1. (Optional) Create and activate a virtual environment.
2. Install dependencies:

```powershell
pip install -r requirements.txt
```

Usage

```powershell
python extract_emails.py path\to\input.txt
```

Options
- --chunk-size: Read chunk size in bytes (default 1048576)
- --no-preview: Do not print the first 10 emails as a preview

Output
- Produces a file named `extracted_emails_YYYYmmdd_HHMMSS.txt` in the current working directory.
- The output file starts with a header that includes the total unique emails found and the extraction date.

Example

```powershell
python extract_emails.py "extract1 (2).txt"
```

Notes and limitations
- The included email regex is practical for most use cases but not a full RFC-5322 compliant validator. It may miss or include some edge-case addresses.
- The script reads files using UTF-8 with errors ignored; non-UTF-8 bytes will be skipped rather than failing.

License
- Public domain / use as you wish
