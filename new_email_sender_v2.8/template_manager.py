# template_manager.py
import os
from string import Template

class TemplateManager:
    """Manage email templates with variable substitution."""
    
    def __init__(self, template_file='email_template.txt'):
        self.template_file = template_file
        self.template = self.load_template()
    
    def load_template(self):
        """Load email template from file."""
        if not os.path.exists(self.template_file):
            raise FileNotFoundError(f"Template file not found: {self.template_file}")
        
        with open(self.template_file, 'r', encoding='utf-8') as f:
            return Template(f.read())
    
    def render(self, **kwargs):
        """Render template with provided variables."""
        try:
            return self.template.substitute(**kwargs)
        except KeyError as e:
            raise ValueError(f"Missing template variable: {e}")
    
    def get_required_variables(self):
        """Extract required variables from template."""
        import re
        pattern = r'\{(\w+)\}'
        with open(self.template_file, 'r', encoding='utf-8') as f:
            content = f.read()
        return set(re.findall(pattern, content))