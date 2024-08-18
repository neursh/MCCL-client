import os
import json

class ConfigLoader:
    def __init__(self):
        self.config = dict()
    
    def get(self):
        if os.path.exists("config.json") and os.path.isfile("config.json"):
            with open("config.json", "r") as rawConfig:
                self.config: dict = json.load(rawConfig)
            return True
        
        return False