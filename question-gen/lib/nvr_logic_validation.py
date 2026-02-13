from collections import Counter
from typing import Any, Callable, Dict, List, Optional

def check_derived_parameters(
    options: List[Dict[str, Any]], 
    extractors: Dict[str, Callable[[Dict[str, Any]], Any]]
) -> List[Dict[str, Any]]:
    """
    Validates that only ONE property (primary differentiator) has an (N-1):1 split.
    Identifies 'Derived' conflicts by aggregating local properties.
    
    Args:
        options: List of option dictionaries.
        extractors: Dictionary mapping property names to functions that extract values from an option.
                   e.g. {"Total Circles": lambda opt: ...}
                   
    Returns:
        List of conflicts (unintended splits).
        Each conflict is specific to a property that has a 4:1 (or N-1:1) split.
        Note: The Caller is responsible for ignoring the *intended* split.
    """
    n = len(options)
    split_target_count = n - 1 # We look for value with freq 1 (meaning the rest are N-1)
    
    conflicts = []
    
    for name, func in extractors.items():
        try:
            values = [func(opt) for opt in options]
        except Exception:
            # If extraction fails (e.g. key error), skip or handle
            continue
            
        counts = Counter(values)
        
        # Check if any value appears exactly 1 time
        # This implies the other values sum to N-1.
        # But wait, what if we have 1:1:1:1:1? No conflict.
        # What if we have 2:3? No conflict.
        # Conflict is ONLY when one value is unique (freq=1) AND the rest are NOT unique?
        # Actually, "Odd One Out" means there is a "Common Rule" satisfied by N-1 options.
        # So we look for a value that appears N-1 times (Defining the rule) 
        # OR we look for a value that appears 1 time (The exception).
        # Equivalently: Is there a value with frequency N-1?
        # If so, the REMAINING option (freq=1) is the Odd One Out.
        
        # Example: [A, A, A, A, B] -> A freq=4. Valid split.
        # Example: [A, B, C, D, E] -> All freq=1. No common rule.
        # Example: [A, A, B, B, C] -> No common rule (2:2:1).
        
        has_common_rule = any(c == split_target_count for c in counts.values())
        
        if has_common_rule:
            # Identify the odd one out
            # The odd one is the one with the value that has frequency 1 (since N-1 + 1 = N).
            # (Assuming N=5. If N=3, split is 2:1).
            
            # Find the value with freq 1
            odd_val = next((v for v, c in counts.items() if c == 1), None)
            
            if odd_val is not None:
                odd_indices = [i for i, v in enumerate(values) if v == odd_val]
                # Should be exactly 1 index
                for unique_idx in odd_indices:
                     conflicts.append({
                        "property": name,
                        "answer_index": unique_idx, # 0-based
                        "value": odd_val,
                        "common_value": next(v for v, c in counts.items() if c == split_target_count)
                    })
                    
    return conflicts
