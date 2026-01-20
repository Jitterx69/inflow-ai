from typing import List, Dict, Any
from datetime import datetime

class ReasoningTrace:
    """
    Captures the decision-making process for explainability.
    """
    def __init__(self, step: str):
        self.step = step
        self.timestamp = datetime.now()
        self.inputs = {}
        self.outputs = {}
        self.reasoning = []

    def log_input(self, key: str, value: Any):
        self.inputs[key] = str(value)

    def log_output(self, key: str, value: Any):
        self.outputs[key] = str(value)

    def add_reason(self, reason: str):
        self.reasoning.append(reason)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "step": self.step,
            "timestamp": self.timestamp.isoformat(),
            "inputs": self.inputs,
            "outputs": self.outputs,
            "reasoning": self.reasoning
        }
