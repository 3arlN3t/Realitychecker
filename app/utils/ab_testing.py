
from typing import Dict, Any, Optional
import hashlib
import random

class ABTesting:
    def __init__(self, experiments: Dict[str, Any]):
        self.experiments = experiments

    def get_variant(self, user_id: str, experiment_name: str) -> Optional[str]:
        if experiment_name not in self.experiments:
            return None

        experiment = self.experiments[experiment_name]
        user_hash = int(hashlib.sha256(user_id.encode()).hexdigest(), 16)
        
        total_weight = sum(experiment['variants'].values())
        assignment = user_hash % total_weight
        
        cumulative_weight = 0
        for variant, weight in experiment['variants'].items():
            cumulative_weight += weight
            if assignment < cumulative_weight:
                return variant
        
        return None
