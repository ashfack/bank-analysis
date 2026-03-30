from typing import Dict
from model.models import CategoryStats, ClusterLabel
from config import config

class Categorizer:
    """
    Responsibility: Determines the appropriate cluster for a financial category.
    
    This class uses a hierarchy of manual mappings, keyword detection, 
    directional logic (incoming vs outgoing), and statistical stability.
    """

    def __init__(self, mapping: Dict[str, str]):
        """
        Initializes the categorizer with user-defined overrides.
        
        Args:
            mapping: Dictionary mapping category names to ClusterLabels.
        """
        self.mapping = mapping

    def classify(self, 
                 name: str, 
                 stats: CategoryStats, 
                 sample_label: str, 
                 sample_amount: float) -> str:
        """
        Classifies a category into a Master Cluster.

        Args:
            name: The category name.
            stats: The CategoryStats DTO containing CV and Frequency.
            sample_label: A transaction label used for keyword matching.
            sample_amount: A transaction amount used for direction check.

        Returns:
            The string value of the assigned ClusterLabel.
        """
        # 1. Manual Mapping
        if name in self.mapping:
            return self.mapping[name]

        # 2. Key-word/Directional check
        label_clean = str(sample_label).lower()
        if 'virement' in label_clean:
            return ClusterLabel.INTERNAL.value
        
        if sample_amount > 0:
            return ClusterLabel.INCOMING.value

        # 3. Statistical Analysis
        if stats.frequency > config.RECURRING_FREQ_THRESHOLD:
            if stats.cv < config.CV_STABILITY_THRESHOLD:
                return ClusterLabel.CORE.value
            return ClusterLabel.OTHER_RECURRING.value

        if stats.frequency > config.PUNCTUAL_FREQ_THRESHOLD:
            return ClusterLabel.OTHER_PUNCTUAL.value

        return ClusterLabel.EXCEPTIONAL.value