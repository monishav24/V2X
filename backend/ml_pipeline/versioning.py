"""
SmartV2X-CP Ultra — Model Version Control
============================================
Tracks model versions, metadata, and provides retrieval API.
"""

import os
import json
import time
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class ModelVersionManager:
    """
    Simple file-based model registry.

    Stores metadata about each model version including:
      • Version number
      • Training timestamp
      • Metrics (loss, accuracy)
      • File path
      • Status (active / archived)
    """

    def __init__(self, storage_dir: str = "models/"):
        self.storage_dir = storage_dir
        self._registry_path = os.path.join(storage_dir, "model_registry.json")
        os.makedirs(storage_dir, exist_ok=True)
        self._registry: List[Dict[str, Any]] = self._load_registry()

    def _load_registry(self) -> List[Dict[str, Any]]:
        if os.path.exists(self._registry_path):
            with open(self._registry_path, "r") as f:
                return json.load(f)
        return []

    def _save_registry(self):
        with open(self._registry_path, "w") as f:
            json.dump(self._registry, f, indent=2)

    def register_model(
        self,
        model_path: str,
        version: str,
        metrics: Dict[str, float],
        description: str = "",
    ) -> Dict[str, Any]:
        """Register a new model version."""
        entry = {
            "version": version,
            "model_path": model_path,
            "metrics": metrics,
            "description": description,
            "created_at": time.time(),
            "status": "active",
        }
        # Deactivate previous active versions
        for existing in self._registry:
            if existing["status"] == "active":
                existing["status"] = "archived"

        self._registry.append(entry)
        self._save_registry()
        logger.info("Model registered: v%s (%s)", version, model_path)
        return entry

    def get_active_model(self) -> Optional[Dict[str, Any]]:
        """Get the currently active model version."""
        for entry in reversed(self._registry):
            if entry["status"] == "active":
                return entry
        return None

    def list_versions(self) -> List[Dict[str, Any]]:
        """List all model versions."""
        return self._registry

    def rollback(self, version: str) -> bool:
        """Rollback to a specific model version."""
        for entry in self._registry:
            entry["status"] = "archived"
        for entry in self._registry:
            if entry["version"] == version:
                entry["status"] = "active"
                logger.info("Rolled back to model v%s", version)
                self._save_registry()
                return True
        logger.warning("Version %s not found for rollback", version)
        return False
