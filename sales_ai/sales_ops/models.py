from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


@dataclass
class Contact:
    name: str
    role: str
    email: str
    influence: str


@dataclass
class EngagementSignals:
    last_reply_days_ago: int
    email_open_rate: float
    meeting_attendance_rate: float
    competitor_mentions: int
    champion_changed: bool
    product_usage_score: float = 0.0
    support_tickets_open: int = 0
    sentiment_score: float = 0.0


@dataclass
class Account:
    name: str
    industry: str
    size: str
    region: str
    annual_revenue_m: int
    tech_stack: List[str]
    pain_points: List[str]
    buying_signals: List[str]
    contacts: List[Contact]
    engagement: EngagementSignals
    external_id: str = ""


@dataclass
class Deal:
    account_name: str
    stage: str
    value_usd: int
    close_probability: float
    days_in_stage: int
    next_step: str
    stakeholders: List[str]
    account_ref: str = ""
    notes: List[str] = field(default_factory=list)
