from pydantic import BaseModel, Field
from typing import List, Dict

class Finding(BaseModel):
    title: str = Field(..., description="A short descriptive title of the diagnostic finding.")
    category: str = Field(..., description="Subsystem category (e.g. CPU, Memory, Storage, Network, Services, Startup, Logs).")
    severity: str = Field("INFO", description="Severity level: HEALTHY, INFO, WARNING, ATTENTION, CRITICAL.")
    evidence: str = Field(..., description="Measurable system metrics or evidence backing this finding.")
    possible_causes: List[str] = Field(default_factory=list, description="A list of possible system root causes for this finding.")
    confidence: str = Field("HIGH", description="Confidence level: LOW, MEDIUM, HIGH.")
    recommendation: str = Field(..., description="Suggested actionable recommendation for resolving this finding.")
    requires_action: bool = Field(False, description="Whether this finding requires a system-modifying repair action.")

class DiagnosticReport(BaseModel):
    findings: List[Finding] = Field(default_factory=list, description="List of structured findings identified during diagnostics.")
    overall_health_score: int = Field(100, description="The overall system health score from 0 to 100.")
    categories_scores: Dict[str, int] = Field(default_factory=dict, description="Individually calculated category scores.")
    summary: str = Field("", description="A short natural language summary explaining the general health and top issues.")
