# rate_limiter.py
import time
from collections import deque
from datetime import datetime, timedelta

class RateLimiter:
    """Prevent hitting email provider rate limits."""
    
    def __init__(self, max_per_minute=30, max_per_hour=500):
        self.max_per_minute = max_per_minute
        self.max_per_hour = max_per_hour
        self.minute_window = deque()
        self.hour_window = deque()
    
    def wait_if_needed(self):
        """Wait if rate limits would be exceeded."""
        now = datetime.now()
        
        # Clean old entries
        minute_ago = now - timedelta(minutes=1)
        hour_ago = now - timedelta(hours=1)
        
        while self.minute_window and self.minute_window[0] < minute_ago:
            self.minute_window.popleft()
        
        while self.hour_window and self.hour_window[0] < hour_ago:
            self.hour_window.popleft()
        
        # Check limits
        if len(self.minute_window) >= self.max_per_minute:
            sleep_time = (self.minute_window[0] + timedelta(minutes=1) - now).total_seconds()
            if sleep_time > 0:
                print(f"\n⏸️  Rate limit: waiting {sleep_time:.1f}s...")
                time.sleep(sleep_time + 1)
        
        if len(self.hour_window) >= self.max_per_hour:
            sleep_time = (self.hour_window[0] + timedelta(hours=1) - now).total_seconds()
            if sleep_time > 0:
                print(f"\n⏸️  Hourly limit: waiting {sleep_time/60:.1f} minutes...")
                time.sleep(sleep_time + 1)
        
        # Record this send
        now = datetime.now()
        self.minute_window.append(now)
        self.hour_window.append(now)


class SMTPConnectionPool:
    """Reuse SMTP connections to improve performance."""
    
    def __init__(self, smtp_server, smtp_port, sender_email, sender_password, pool_size=5):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.sender_email = sender_email
        self.sender_password = sender_password
        self.pool_size = pool_size
        self.connections = []
        self.connection_ages = []
        self.max_age = 300  # 5 minutes
    
    def get_connection(self):
        """Get a connection from pool or create new one."""
        now = time.time()
        
        # Remove old connections
        for i in reversed(range(len(self.connections))):
            if now - self.connection_ages[i] > self.max_age:
                try:
                    self.connections[i].quit()
                except:
                    pass
                del self.connections[i]
                del self.connection_ages[i]
        
        # Try to reuse existing connection
        if self.connections:
            conn = self.connections.pop(0)
            age = self.connection_ages.pop(0)
            try:
                # Test connection
                conn.noop()
                return conn, True  # Reused
            except:
                # Connection dead, create new
                pass
        
        # Create new connection
        conn = smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=30)
        conn.starttls()
        conn.login(self.sender_email, self.sender_password)
        return conn, False  # New connection
    
    def return_connection(self, conn):
        """Return connection to pool."""
        if len(self.connections) < self.pool_size:
            try:
                conn.noop()  # Test if still alive
                self.connections.append(conn)
                self.connection_ages.append(time.time())
            except:
                try:
                    conn.quit()
                except:
                    pass
        else:
            try:
                conn.quit()
            except:
                pass
    
    def close_all(self):
        """Close all connections in pool."""
        for conn in self.connections:
            try:
                conn.quit()
            except:
                pass
        self.connections.clear()
        self.connection_ages.clear()