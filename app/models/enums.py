from enum import Enum

class IngestStatus(str, Enum):
    INGESTED = "INGESTED"
    FAILED = "FAILED"

class EventType(str, Enum):
    FILE_UPLOADED = "INGESTED"
    AI_PROCESSED = "AI_COMPLETE"

class PairingStatus(str, Enum):
    WAITING = "WAITING"
    CLAIMED = "CLAIMED"
    EXPIRED = "EXPIRED"
