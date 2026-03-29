from __future__ import annotations

import csv
from io import StringIO

from sales_ops.models import Account, Contact, Deal, EngagementSignals


def _split_list(value: str) -> list[str]:
    return [item.strip() for item in value.split("|") if item.strip()]


def parse_accounts_csv(content: str) -> list[Account]:
    rows = csv.DictReader(StringIO(content))
    accounts: list[Account] = []

    for row in rows:
        contacts = [
            Contact(
                name=row["primary_contact_name"],
                role=row["primary_contact_role"],
                email=row["primary_contact_email"],
                influence=row["primary_contact_influence"],
            )
        ]

        secondary_name = row.get("secondary_contact_name", "").strip()
        if secondary_name:
            contacts.append(
                Contact(
                    name=secondary_name,
                    role=row.get("secondary_contact_role", ""),
                    email=row.get("secondary_contact_email", ""),
                    influence=row.get("secondary_contact_influence", ""),
                )
            )

        accounts.append(
            Account(
                name=row["name"],
                industry=row["industry"],
                size=row["size"],
                region=row["region"],
                annual_revenue_m=int(row["annual_revenue_m"]),
                tech_stack=_split_list(row["tech_stack"]),
                pain_points=_split_list(row["pain_points"]),
                buying_signals=_split_list(row["buying_signals"]),
                contacts=contacts,
                engagement=EngagementSignals(
                    last_reply_days_ago=int(row["last_reply_days_ago"]),
                    email_open_rate=float(row["email_open_rate"]),
                    meeting_attendance_rate=float(row["meeting_attendance_rate"]),
                    competitor_mentions=int(row["competitor_mentions"]),
                    champion_changed=row["champion_changed"].strip().lower() == "true",
                    product_usage_score=float(row.get("product_usage_score", 0) or 0),
                    support_tickets_open=int(row.get("support_tickets_open", 0) or 0),
                    sentiment_score=float(row.get("sentiment_score", 0) or 0),
                ),
            )
        )

    return accounts


def parse_deals_csv(content: str) -> list[Deal]:
    rows = csv.DictReader(StringIO(content))
    deals: list[Deal] = []

    for row in rows:
        deals.append(
            Deal(
                account_name=row["account_name"],
                stage=row["stage"],
                value_usd=int(row["value_usd"]),
                close_probability=float(row["close_probability"]),
                days_in_stage=int(row["days_in_stage"]),
                next_step=row["next_step"],
                stakeholders=_split_list(row["stakeholders"]),
                notes=_split_list(row.get("notes", "")),
            )
        )

    return deals
