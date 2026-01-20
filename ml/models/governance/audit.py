import json
from typing import Dict, Any, List
from datetime import datetime
from .explainability import ReasoningTrace

class AuditEvent:
    def __init__(self, event_type: str, traces: List[ReasoningTrace]):
        self.event_id = str(datetime.now().timestamp())
        self.event_type = event_type
        self.traces = traces
        self.timestamp = datetime.now()

    def to_json(self) -> str:
        data = {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "timestamp": self.timestamp.isoformat(),
            "traces": [trace.to_dict() for trace in self.traces]
        }
        return json.dumps(data, indent=2)

class AuditLogger:
    """
    Logs decision lineage to persistent storage (mocked usually).
    """
    def __init__(self):
        self.events = [] # In-memory store for now

    def log_event(self, event_type: str, traces: List[ReasoningTrace]):
        event = AuditEvent(event_type, traces)
        self.events.append(event)
        # In production, this would write to a DB or file
        # print(f"[AUDIT] {event.to_json()}") 
        return event
