from typing import Any
import re


class SymbolicOverride:
    """
    Responsibility: Rule Parsing with Directional Logic.
    - '+10%' -> Increase by 10% (1.1x)
    - '-10%' -> Decrease by 10% (0.9x)
    - '50%'  -> Take 50% of the value (0.5x)
    - '500'  -> Hard override to 500
    """
    @staticmethod
    def apply(rule: Any, base_val: float) -> float:
        rule_str = str(rule).strip()
        if not rule_str or rule_str.lower() == 'nan': 
            return base_val
        
        try:
            # 1. Handle Percentages
            if '%' in rule_str:
                # Extract numeric value (handles integers or decimals like 12.5)
                val_match = re.findall(r"[-+]?\d*\.?\d+", rule_str)
                if not val_match: return base_val
                
                mod = float(val_match[0]) / 100
                
                # If rule starts with + or -, it's an INCREMENTAL adjustment
                if rule_str.startswith(('+', '-')):
                    return round(base_val * (1 + mod),2)
                # If no sign, it's an ABSOLUTE RATIO (e.g., 50% of base)
                else:
                    return round(base_val * mod,2)
            
            # 2. Handle Additive Adjustments (e.g., +50 or -20)
            if rule_str.startswith(('+', '-')):
                val_match = re.findall(r"[-+]?\d*\.?\d+", rule_str)
                if not val_match: return base_val
                return round(base_val + float(val_match[0]),2)
            
            # 3. Handle Fixed Absolute Values (e.g., 850)
            return float(rule_str)
            
        except (ValueError, IndexError):
            # Fallback to base value if string is malformed (e.g., "abc%")
            return base_val