
Markdown
# Method for Choosing Answer Parameters for Odd-One-Out NVR Problems

## 1. Outline of Issue
When an question generator (human, agent, or procedural) is tasked with creating certain types of odd-one-out Non-Verbal Reasoning (NVR) questions, a recurring computational problem occurs: the generation of unintended "secondary" rules. This happens when the combination of independent parameters creates a visual pattern—a **derived parameter**—that provides a valid, alternative reason for a different answer to be the "odd one out".

### 1.1 Objective
The generator must produce $N-1$ incorrect answers and 1 correct answer, with the following requirements:
* **The Primary Split**: The $N-1$ incorrect answers must share a property in common, determined by a specific parameter (e.g., `fill="black"`), that is not shared by the correct answer.
* **No Unintended Splits**: The $N$ answers must not have an $N-1:1$ split for any other property.
* **Distinctness**: All $N-1$ incorrect answers should be different from each other to ensure the set is visually diverse.

---

## 2. Mathematical Notation
To formalize the generation process, we use:
* $A_1 \dots A_n$: Denotes the set of answers, where $A_1$ is typically the intended correct answer.
* $P_1 \dots P_m$: Denotes the parameterized properties that vary between the answers.

In simple questions featuring a single element, uniqueness is straightforward. By choosing a distribution other than $N-1:1$ (e.g., $2:3$ or $1:1:1:1:1$) for all non-target parameters, the generator can guarantee that only the intended target parameter creates a valid solution.

---

## 3. The Challenge: Derived Parameters
The problem becomes complex when answers feature repeated or multiple elements (e.g., two shapes side-by-side). In these cases, **Derived Parameters** emerge from the relationship between the sub-elements.

### 3.1 Local vs. Global Properties
1. **Local Parameters ($P_{local}$)**: Properties tied to a specific sub-element (e.g., "the shape on the left is a circle").
2. **Derived (Global) Parameters ($P_{derived}$)**: Properties that emerge from the frame as a whole (e.g., the total count of a specific color or shape across both elements).

### 3.2 Failure Case Example
Consider an intended odd-one-out question where the rule is "The shape on the left is a Circle".

| Answer | Left Shape ($P_1$) | Left Color ($P_2$) | Right Shape ($P_3$) | Right Color ($P_4$) |
| :--- | :--- | :--- | :--- | :--- |
| **A1** | **Circle** | Black | Square | White |
| **A2** | Square | White | Circle | Black |
| **A3** | Square | White | Square | Black |
| **A4** | Square | Black | Circle | White |
| **A5** | Square | Black | Circle | Black |

**The Resulting Conflict:**
* **Intended Logic**: $A_1$ is the only answer with a circle on the left.
* **Derived Logic (Count)**: In $A_3$, the total number of squares is 2, whereas all other answers have a 1:1 mix. $A_3$ becomes a valid odd-one-out.
* **Derived Logic (Color)**: In $A_5$, the total number of black shapes is 2, whereas others have a 1:1 mix. $A_5$ becomes a valid odd-one-out.

---

## 4. Visual Saliency
A critical factor in abstract reasoning is **Saliency**—how "obvious" a rule is to the human eye. Derived parameters like "total count" or "symmetry" are often more salient than local parameters like "positional shape." If a generator accidentally creates an $N-1:1$ split on a highly salient derived parameter, the intended answer ($A_1$) will likely be ignored by the student in favor of the more "obvious" emergent rule.

---

## 5. Validation Requirements
To ensure an unambiguous question, the procedural generator must implement the following checks:
* **Local Invariant Check**: Ensure no unintended $N-1:1$ splits exist in the primary parameters $P_1 \dots P_m$.
* **Derived Aggregate Check**: Calculate total counts for every value across the frame (e.g., total circles, total black fills). No aggregate value can have an $N-1:1$ split.
* **Relational Check**: Check for boolean properties such as "Are shapes identical?" or "Is one shape inside another?" These must be distributed in a way that does not create a secondary odd-one-out.
* **Collision Check**: Ensure no two answers $A_i$ and $A_j$ result in identical rendered diagrams.

## Suggested py code for parameter checks

To implement a Derived Parameter Check, we need a validation function that aggregates all "local" properties into a "global" state. This script checks for any property that results in a $4:1$ split (or $(N-1):1$), which would create an unintended second solution.Pythonfrom collections import Counter

def check_derived_parameters(answers, n_size=5):
    """
    Validates that only ONE property has a (N-1):1 split.
    Identifies 'Derived' conflicts by aggregating local properties.
    """
    # 1. Map all properties (Local and Derived)
    # Each 'frame' contains multiple sub-elements (e.g., Left/Right shapes)
    global_property_logs = []

    for idx, ans in enumerate(answers):
        # Local properties (directly from your parameters)
        properties = {
            "left_shape": ans['L']['shape'],
            "left_fill": ans['L']['fill'],
            "right_shape": ans['R']['shape'],
            "right_fill": ans['R']['fill']
        }
        
        # Derived/Aggregate properties (the "Human Perception" layer)
        properties.update({
            "total_circles": (1 if ans['L']['shape'] == 'circle' else 0) + 
                             (1 if ans['R']['shape'] == 'circle' else 0),
            "total_squares": (1 if ans['L']['shape'] == 'square' else 0) + 
                             (1 if ans['R']['shape'] == 'square' else 0),
            "total_black":   (1 if ans['L']['fill'] == 'black' else 0) + 
                             (1 if ans['R']['fill'] == 'black' else 0),
            "is_identical":  ans['L']['shape'] == ans['R']['shape'] and 
                             ans['L']['fill'] == ans['R']['fill']
        })
        global_property_logs.append(properties)

    # 2. Analyze Splits for every property
    keys = global_property_logs[0].keys()
    unintended_solutions = []

    for key in keys:
        values = [frame[key] for frame in global_property_logs]
        counts = Counter(values)
        
        # Check if any value appears exactly 1 time or exactly (N-1) times
        # This indicates an Odd-One-Out split
        for val, freq in counts.items():
            if freq == 1:
                odd_index = values.index(val)
                unintended_solutions.append({
                    "property": key,
                    "answer_index": odd_index + 1,
                    "value": val
                })

    return unintended_solutions

# Example Failure Case from your .md
test_answers = [
    {"L": {"shape": "circle", "fill": "black"}, "R": {"shape": "square", "fill": "white"}}, # A1 (Intended)
    {"L": {"shape": "square", "fill": "white"}, "R": {"shape": "circle", "fill": "black"}}, # A2
    {"L": {"shape": "square", "fill": "white"}, "R": {"shape": "square", "fill": "black"}}, # A3 (Conflict: 2 squares)
    {"L": {"shape": "square", "fill": "black"}, "R": {"shape": "circle", "fill": "white"}}, # A4
    {"L": {"shape": "square", "fill": "black"}, "R": {"shape": "circle", "fill": "black"}}, # A5 (Conflict: 2 black)
]

conflicts = check_derived_parameters(test_answers)
for c in conflicts:
    print(f"Found {c['property']} split: Answer {c['answer_index']} is an odd-one-out

# Possible solution - Constraint-Based Parameter Selection Algorithm

To eliminate the need for repeated "re-rolling," this algorithm uses a **Pre-Allocation Matrix**. Instead of assigning values answer-by-answer, it distributes values across the entire set to mathematically guarantee that no derived $N-1:1$ split can occur.

---

## 1. The Core Strategy: "The Anti-Split Parity Rule"
The primary reason derived parameters fail is that a unique "Local" value (e.g., a circle on the left) often results in a unique "Global" count (e.g., only one circle in total). To prevent this, the algorithm ensures that any value used in a unique position is "hidden" by placing that same value in a non-unique position elsewhere in the set.

---

## 2. The Algorithm Steps

### Step 1: Initialize the Target Split
* **Assign the Target**: Choose a parameter (e.g., $P_1$ / "Left Shape") and assign the $N-1:1$ split.
* **Identify the Unique Value**: Let $V_{target}$ be the value that makes $A_1$ the odd-one-out (e.g., "Circle").

### Step 2: Seed the Global "Anchor"
* To ensure the count of $V_{target}$ is not unique to $A_1$, force $V_{target}$ into a *different* parameter slot (e.g., $P_3$ / "Right Shape") of a *different* answer (e.g., $A_2$).
* This ensures that both $A_1$ and $A_2$ now contain exactly one "Circle," breaking the $4:1$ derived split for the "Total Circle Count".

### Step 3: Noise Distribution via Safe Permutation
* For all remaining empty slots, use **Safe Splits** (e.g., $2:3$ or $2:2:1$ for $N=5$).
* **The Derangement Constraint**: For any $P_{noise}$, ensure that if a value creates a "1" in a $2:2:1$ split, that "1" does not align with the answer index of any other property's "1".

---

## 3. Visualization: The Parameter Matrix
By planning the grid horizontally (answers) and vertically (parameters) simultaneously, we can see the conflicts before they are rendered.

| Answer | Slot 1 (Left Shape) | Slot 2 (Right Shape) | Global Count (Derived) | Result |
| :--- | :--- | :--- | :--- | :--- |
| **A1** | **Circle** (Target) | Square | 1 Circle, 1 Square | **Target Odd-One-Out** |
| **A2** | Square | **Circle** (Anchor) | 1 Circle, 1 Square | Safe (Count = 1) |
| **A3** | Square | Triangle | 1 Square, 1 Triangle | Safe (Count = 0) |
| **A4** | Square | Triangle | 1 Square, 1 Triangle | Safe (Count = 0) |
| **A5** | Square | Square | 2 Squares | Safe (Count = 0) |



---

## 4. Pseudocode Implementation

```python
def generate_safe_parameters(n=5):
    # 1. Define Primary Split (Left Shape)
    # A1 = Circle, A2-A5 = Square
    slots = initialize_matrix(rows=n, cols=2) 
    slots[0][0] = "Circle" 
    for i in range(1, n): slots[i][0] = "Square"

    # 2. Apply Anchor Rule to break Derived Count
    # Place a Circle in the Right slot of A2
    slots[1][1] = "Circle"

    # 3. Distribute Noise (Right Shape)
    # Remaining slots for Right Shape: A1, A3, A4, A5
    # Use a Safe Split (e.g., two Squares, two Triangles)
    noise_values = ["Square", "Triangle", "Triangle", "Square"]
    random.shuffle(noise_values)
    
    fill_remaining_slots(slots, col=1, values=noise_values)

    # 4. Final Distinctness Check
    # Ensure no two rows are identical
    if not has_duplicates(slots):
        return slots
```


# 5. Benefits of this Approach
Computational Efficiency: It eliminates the "Generate -> Fail -> Reroll" loop by being "Correct by Construction".Saliency Control: You can prioritize anchoring high-saliency properties (like color) first, as these are the derived parameters humans notice most easily.Mathematical Certainty: By tracking the "Global Budget" of shapes and colors, you guarantee that no unintended $N-1:1$ total count exists.        


Here is the complete logic, explanation, and code for the Constraint-Based Selection Algorithm provided in raw Markdown format.

Markdown
# Constraint-Based NVR Parameter Selection Logic

To move beyond a "generate-and-validate" approach, this logic uses a **Constraint-Based Distribution** algorithm. This method mathematically guarantees that no derived $N-1:1$ split can exist by pre-allocating values that cancel out emergent patterns.

## 1. The "Global Balance" Selection Algorithm

### Step 1: Define the Global Budget
Instead of picking values for $A_1$, then $A_2$, etc., you decide on the **Global Distribution** of every visual value first.
* **Target Parameter ($P_{target}$)**: Explicitly set to an $N-1:1$ split (e.g., 4 squares, 1 circle).
* **Noise Parameters ($P_{noise}$)**: For every other property, select a distribution that is "Split-Safe" (e.g., $2:3$, $2:2:1$, or $1:1:1:1:1$).

### Step 2: The Anchor (Parity) Rule
To prevent derived "Total Count" failures (like "Total Circles"), you must treat the frame as a single entity during assignment.
* If $A_1$ (the odd-one-out) is assigned a "Circle" in the left slot, you must force a "Circle" into a different slot (e.g., the right slot) of a different answer (e.g., $A_2$).
* This ensures that both $A_1$ and $A_2$ now contain exactly one "Circle," breaking the $4:1$ derived split for the "Total Circle Count".



---

## 2. Python Implementation

This script implements the **Anchoring** technique to ensure local oddities do not create unintended global (derived) splits.

```python
import random
from collections import Counter

class NVRGenerator:
    def __init__(self):
        self.shapes = ["circle", "square", "triangle", "star"]
        self.fills = ["black", "white", "striped", "dotted"]

    def generate_balanced_question(self):
        """
        Generates 5 answers where A1 is the only one with a specific 
        shape on the left, but global counts are balanced to avoid 
        derived parameter splits.
        """
        # 1. Define the Primary Target (Local Split)
        # Goal: A1 has 'circle' on left, A2-A5 have 'square' on left
        target_val = "circle"
        common_val = "square"
        
        answers = [
            {"L": {"shape": target_val, "fill": None}, "R": {"shape": None, "fill": None}}
            for _ in range(5)
        ]
        for i in range(1, 5):
            answers[i]["L"]["shape"] = common_val

        # 2. Seed the Global Anchor (Break the Derived Count)
        # To prevent 'Total Circles == 1' from being an odd-one-out rule for A1,
        # we give A2 a circle on the Right.
        answers[1]["R"]["shape"] = target_val # A2 now also has a circle

        # 3. Fill remaining Shape slots with "Safe Splits"
        # We need shapes for: A1-Right, A3-Right, A4-Right, A5-Right
        # We use 'triangle' and 'star' in a 2:2 split to avoid any 4:1 splits.
        noise_shapes = ["triangle", "triangle", "star", "star"]
        random.shuffle(noise_shapes)
        
        # Assign to remaining empty Right slots
        remaining_indices = [0, 2, 3, 4]
        for i, shape in zip(remaining_indices, noise_shapes):
            answers[i]["R"]["shape"] = shape

        # 4. Assign Fills (Colors) using "Safe Splits"
        # We will use a 3:2 split for Left Fills and a 2:3 split for Right Fills
        # but carefully align them so no answer has a unique "Total Black" count.
        
        # Left Fills: 3 Black, 2 White
        l_fills = ["black", "black", "black", "white", "white"]
        random.shuffle(l_fills)
        
        # Right Fills: 2 Black, 3 White
        r_fills = ["black", "black", "white", "white", "white"]
        random.shuffle(r_fills)

        for i in range(5):
            answers[i]["L"]["fill"] = l_fills[i]
            answers[i]["R"]["fill"] = r_fills[i]

        return answers

    def validate(self, answers):
        """
        Checks every property (Local and Derived) for 4:1 splits.
        """
        results = []
        # Define the properties to check (simulating human perception)
        checks = {
            "Left Shape": lambda a: a["L"]["shape"],
            "Right Shape": lambda a: a["R"]["shape"],
            "Total Circles": lambda a: (1 if a["L"]["shape"] == "circle" else 0) + 
                                       (1 if a["R"]["shape"] == "circle" else 0),
            "Total Black": lambda a: (1 if a["L"]["fill"] == "black" else 0) + 
                                     (1 if a["R"]["fill"] == "black" else 0),
            "Are Identical": lambda a: a["L"] == a["R"]
        }

        for name, func in checks.items():
            values = [func(a) for a in answers]
            counts = Counter(values)
            for val, count in counts.items():
                if count == 1:
                    odd_idx = values.index(val)
                    results.append(f"SPLIT FOUND: {name} (Ans {odd_idx+1} is unique with value {val})")
        
        return results

# Execution
gen = NVRGenerator()
question = gen.generate_balanced_question()
conflicts = gen.validate(question)

print("--- Generated Answer Set ---")
for i, ans in enumerate(question):
    print(f"A{i+1}: L={ans['L']}, R={ans['R']}")

print("\n--- Validation Results ---")
if not conflicts:
    print("No unintentional odd-one-out rules found.")
else:
    for c in conflicts:
        print(c)

```
# 3. Benefits of this Approach
Computational Efficiency: It eliminates the "Generate -> Fail -> Reroll" loop by being "Correct by Construction".Saliency Control: You can prioritize anchoring high-saliency properties (like color) first, as these are the derived parameters humans notice most easily.Mathematical Certainty: By tracking the "Global Budget" of shapes and colors, you guarantee that no unintended $N-1:1$ total count exists.