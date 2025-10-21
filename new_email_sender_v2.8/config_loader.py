# config_loader.py
import json
import os

class Config:
    """Configuration loader."""
    
    def __init__(self, config_path='config.json'):
        self.config_path = config_path
        self.data = self.load_config()
    
    def load_config(self):
        """Load configuration from JSON file."""
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"Config file not found: {self.config_path}")
        
        with open(self.config_path, 'r') as f:
            return json.load(f)
    
    def get(self, key_path, default=None):
        """Get config value using dot notation (e.g., 'smtp.server')."""
        keys = key_path.split('.')
        value = self.data
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
    
    @property
    def smtp_server(self):
        return self.get('smtp.server')
    
    @property
    def smtp_port(self):
        return self.get('smtp.port')
    
    @property
    def sender_email(self):
        return self.get('smtp.sender_email')
    
    @property
    def sender_password(self):
        return self.get('smtp.sender_password')
    
    @property
    def email_subject(self):
        return self.get('email.subject')
    
    @property
    def delay_range(self):
        return (self.get('settings.delay_min'), self.get('settings.delay_max'))
    
    @property
    def rate_limits(self):
        return {
            'per_minute': self.get('settings.rate_limit_per_minute'),
            'per_hour': self.get('settings.rate_limit_per_hour')
        }