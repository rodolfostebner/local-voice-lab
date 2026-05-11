import os
import json
from pathlib import Path
from typing import Dict, Any, List

class PersonaManager:
    """
    Registry for discovering and managing personas declaratively.
    """
    def __init__(self, config_dir: str = "config/personas"):
        self.config_dir = Path(config_dir)
        self.personas: Dict[str, dict] = {}
        self._load_personas()
        
    def _load_personas(self):
        """Discover and load all JSON persona configs."""
        if not self.config_dir.exists():
            print(f"Warning: Persona directory {self.config_dir} not found.")
            return
            
        for file_path in self.config_dir.glob("*.json"):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if "id" in data:
                        self.personas[data["id"]] = data
            except Exception as e:
                print(f"Error loading persona {file_path}: {e}")
                
    def get_persona(self, persona_id: str) -> dict:
        """Return persona by ID, or fallback to default atlas."""
        return self.personas.get(persona_id, self.personas.get("atlas", {}))
        
    def list_personas(self) -> List[dict]:
        """Return a list of all available personas for the frontend."""
        return [{"id": p["id"], "display_name": p.get("display_name", p["id"]), "greeting": p.get("greeting", "")} 
                for p in self.personas.values()]
