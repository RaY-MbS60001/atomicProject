# batch_processor.py
"""
Process large email lists in batches with pause/resume capability.
"""

import json
import os
from datetime import datetime

class BatchProcessor:
    """Handle batch processing of large email lists."""
    
    def __init__(self, batch_size=50, state_file='batch_state.json'):
        self.batch_size = batch_size
        self.state_file = state_file
        self.state = self.load_state()
    
    def load_state(self):
        """Load processing state."""
        if os.path.exists(self.state_file):
            with open(self.state_file, 'r') as f:
                return json.load(f)
        return {
            'current_batch': 0,
            'processed_emails': [],
            'last_updated': None
        }
    
    def save_state(self):
        """Save processing state."""
        self.state['last_updated'] = datetime.now().isoformat()
        with open(self.state_file, 'w') as f:
            json.dump(self.state, f, indent=2)
    
    def get_batches(self, email_list):
        """Split email list into batches."""
        batches = []
        for i in range(0, len(email_list), self.batch_size):
            batches.append(email_list[i:i + self.batch_size])
        return batches
    
    def get_next_batch(self, email_list):
        """Get the next batch to process."""
        # Filter out already processed emails
        pending = [e for e in email_list if e not in self.state['processed_emails']]
        
        if not pending:
            return None
        
        return pending[:self.batch_size]
    
    def mark_processed(self, email):
        """Mark email as processed."""
        if email not in self.state['processed_emails']:
            self.state['processed_emails'].append(email)
            self.save_state()
    
    def reset(self):
        """Reset batch processing state."""
        self.state = {
            'current_batch': 0,
            'processed_emails': [],
            'last_updated': None
        }
        self.save_state()
    
    def get_progress(self, total_emails):
        """Get processing progress."""
        processed = len(self.state['processed_emails'])
        if total_emails == 0:
            return 0.0
        return (processed / total_emails) * 100
    
    def show_status(self, total_emails):
        """Display current processing status."""
        processed = len(self.state['processed_emails'])
        remaining = total_emails - processed
        progress = self.get_progress(total_emails)
        
        print("\n" + "="*70)
        print(" "*22 + "BATCH PROCESSING STATUS")
        print("="*70)
        print(f"Total emails: {total_emails}")
        print(f"Processed: {processed}")
        print(f"Remaining: {remaining}")
        print(f"Progress: {progress:.2f}%")
        print(f"Batch size: {self.batch_size}")
        
        if self.state['last_updated']:
            print(f"Last updated: {self.state['last_updated'][:19]}")
        print("="*70)