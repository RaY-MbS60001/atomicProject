# progress_manager.py
import json
import os
from datetime import datetime

class ProgressManager:
    """Manage sending progress with ability to pause and resume."""
    
    def __init__(self, progress_file='sending_progress.json'):
        self.progress_file = progress_file
        self.data = self.load_progress()
    
    def load_progress(self):
        """Load progress from file."""
        if os.path.exists(self.progress_file):
            try:
                with open(self.progress_file, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                return self._create_empty_progress()
        return self._create_empty_progress()
    
    def _create_empty_progress(self):
        """Create empty progress structure."""
        return {
            'session_id': None,
            'started_at': None,
            'last_email_sent': None,
            'emails_processed': [],
            'current_index': 0,
            'paused': False,
            'paused_at': None
        }
    
    def save_progress(self):
        """Save progress to file."""
        with open(self.progress_file, 'w') as f:
            json.dump(self.data, f, indent=2)
    
    def start_session(self, session_id=None):
        """Start a new sending session."""
        self.data['session_id'] = session_id or datetime.now().strftime('%Y%m%d_%H%M%S')
        self.data['started_at'] = datetime.now().isoformat()
        self.data['paused'] = False
        self.save_progress()
    
    def mark_email_sent(self, email, index):
        """Mark email as sent in current session."""
        self.data['last_email_sent'] = email
        self.data['current_index'] = index + 1
        if email not in self.data['emails_processed']:
            self.data['emails_processed'].append(email)
        self.save_progress()
    
    def pause_session(self):
        """Pause current session."""
        self.data['paused'] = True
        self.data['paused_at'] = datetime.now().isoformat()
        self.save_progress()
        print("\n⏸️  Session paused. You can resume later.")
    
    def resume_session(self):
        """Resume paused session."""
        self.data['paused'] = False
        self.save_progress()
        print("\n▶️  Session resumed.")
    
    def can_resume(self):
        """Check if there's a session that can be resumed."""
        return self.data['session_id'] is not None and self.data['current_index'] > 0
    
    def get_resume_point(self):
        """Get the index to resume from."""
        return self.data['current_index']
    
    def clear_progress(self):
        """Clear all progress data."""
        self.data = self._create_empty_progress()
        self.save_progress()
    
    def show_status(self, total_emails):
        """Display session status."""
        if not self.data['session_id']:
            print("\n❌ No active session")
            return
        
        processed = len(self.data['emails_processed'])
        remaining = total_emails - processed
        progress = (processed / total_emails * 100) if total_emails > 0 else 0
        
        print("\n" + "="*70)
        print(" "*22 + "SESSION STATUS")
        print("="*70)
        print(f"Session ID: {self.data['session_id']}")
        print(f"Started: {self.data['started_at'][:19] if self.data['started_at'] else 'N/A'}")
        
        if self.data['paused']:
            print(f"Status: ⏸️  PAUSED (at {self.data['paused_at'][:19]})")
        else:
            print(f"Status: ▶️  ACTIVE")
        
        print(f"\nProgress: {progress:.2f}%")
        print(f"Processed: {processed}/{total_emails}")
        print(f"Remaining: {remaining}")
        
        if self.data['last_email_sent']:
            print(f"Last email: {self.data['last_email_sent']}")
        
        print("="*70)