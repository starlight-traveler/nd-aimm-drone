# config.py
import yaml
import os

class Config:
    def __init__(self, config_file='/start/config.yaml'):
        if not os.path.exists(config_file):
            raise FileNotFoundError(f"Configuration file '{config_file}' not found.")
        with open(config_file, 'r') as f:
            self.settings = yaml.safe_load(f)
    
    def get(self, section, key, default=None):
        return self.settings.get(section, {}).get(key, default)
    
    def get_section(self, section):
        return self.settings.get(section, {})
