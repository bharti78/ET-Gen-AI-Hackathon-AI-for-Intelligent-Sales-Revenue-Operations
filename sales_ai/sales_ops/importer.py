from __future__ import annotations

import csv
from io import StringIO

from sales_ops.models import Account, Contact, Deal, EngagementSignals


class CSVImportError(ValueError):
    pass


def _split_list(value: str) -> list[str]:
    return [item.strip() for item in value.split("|") if item.strip()]


def _normalize_key(value: str) -> str:
    return value.strip().lower().replace(" ", "_").replace("-", "_")


def _prepare_rows(content: str) -> tuple[list[str], list[dict[str, str]]]:
    rows = csv.DictReader(StringIO(content.lstrip("\ufeff")))
    fieldnames = rows.fieldnames or []
    normalized = {_normalize_key(name): name for name in fieldnames if name}
    prepared_rows: list[dict[str, str]] = []

    for row in rows:
        prepared_rows.append(
            {
                _normalize_key(key): (value or "").strip()
                for key, value in row.items()
                if key is not None
            }
        )

    return list(normalized.keys()), prepared_rows


def _tokenize(value: str) -> set[str]:
    return {token for token in _normalize_key(value).split("_") if token}


def _resolve_key(columns: list[str], aliases: list[str]) -> str | None:
    alias_set = set(aliases)

    for column in columns:
        if column in alias_set:
            return column

    alias_tokens = [_tokenize(alias) for alias in aliases]
    for column in columns:
        column_tokens = _tokenize(column)
        if any(tokens and tokens.issubset(column_tokens) for tokens in alias_tokens):
            return column

    return None


def _pick_value(row: dict[str, str], columns: list[str], aliases: list[str]) -> str:
    key = _resolve_key(columns, aliases)
    if not key:
        return ""
    return (row.get(key) or "").strip()


def _get_optional(row: dict[str, str], aliases: list[str], default: str = "") -> str:
    columns = list(row.keys())
    value = _pick_value(row, columns, aliases)
    return value if value else default


def _require_any(value: str, field_label: str) -> str:
    if value:
        return value
    raise CSVImportError(f"Missing required data for '{field_label}'.")


def _to_int(value: str, field_label: str) -> int:
    try:
        return int(float(value))
    except ValueError as exc:
        raise CSVImportError(f"Invalid number for {field_label}: {value}") from exc


def _to_float(value: str, field_label: str) -> float:
    try:
        return float(value)
    except ValueError as exc:
        raise CSVImportError(f"Invalid number for {field_label}: {value}") from exc


def _to_bool(value: str) -> bool:
    return value.strip().lower() in {"true", "yes", "1", "y"}


def parse_accounts_csv(content: str) -> list[Account]:
    columns, rows = _prepare_rows(content)
    accounts: list[Account] = []

    for row in rows:
        account_external_id = _pick_value(
            row,
            columns,
            ["account_id", "customer_id", "company_id", "crm_account_id", "record_id"],
        )
        account_name = _require_any(
            _pick_value(row, columns, ["name", "account_name", "company", "account", "customer"])
            or account_external_id,
            "name",
        )
        primary_contact_name = _pick_value(
            row,
            columns,
            ["primary_contact_name", "contact_name", "primary_name", "buyer_name", "owner_name"],
        ) or account_name
        primary_contact_role = _pick_value(
            row,
            columns,
            ["primary_contact_role", "contact_role", "title", "role", "job_title"],
        )
        primary_contact_email = _pick_value(
            row,
            columns,
            ["primary_contact_email", "contact_email", "email", "buyer_email", "owner_email"],
        )

        contacts = [
            Contact(
                name=primary_contact_name,
                role=primary_contact_role or "Primary Contact",
                email=primary_contact_email,
                influence=_get_optional(
                    row,
                    ["primary_contact_influence", "contact_influence", "influence"],
                    "champion",
                ),
            )
        ]

        secondary_name = _get_optional(row, ["secondary_contact_name", "secondary_name"])
        if secondary_name:
            contacts.append(
                Contact(
                    name=secondary_name,
                    role=_get_optional(row, ["secondary_contact_role"]),
                    email=_get_optional(row, ["secondary_contact_email"]),
                    influence=_get_optional(row, ["secondary_contact_influence"]),
                )
            )

        accounts.append(
            Account(
                name=account_name,
                industry=_get_optional(row, ["industry", "vertical"], "Unknown"),
                size=_get_optional(row, ["size", "segment", "company_size"], "Unknown"),
                region=_get_optional(row, ["region", "geo", "geography", "territory"], "Unknown"),
                annual_revenue_m=_to_int(
                    _get_optional(
                        row,
                        ["annual_revenue_m", "annual_revenue", "revenue", "arr", "acv"],
                        "0",
                    ),
                    "annual_revenue_m",
                ),
                tech_stack=_split_list(_get_optional(row, ["tech_stack", "tools", "systems"])),
                pain_points=_split_list(_get_optional(row, ["pain_points", "pain_point", "challenges"])),
                buying_signals=_split_list(
                    _get_optional(row, ["buying_signals", "signals", "intent_signals", "buying_intent"])
                ),
                contacts=contacts,
                engagement=EngagementSignals(
                    last_reply_days_ago=_to_int(
                        _get_optional(
                            row,
                            ["last_reply_days_ago", "days_since_last_reply", "last_reply_days", "days_since_reply"],
                            "0",
                        ),
                        "last_reply_days_ago",
                    ),
                    email_open_rate=_to_float(
                        _get_optional(row, ["email_open_rate", "open_rate", "email_opens"], "0"),
                        "email_open_rate",
                    ),
                    meeting_attendance_rate=_to_float(
                        _get_optional(
                            row,
                            ["meeting_attendance_rate", "attendance_rate", "meeting_rate"],
                            "0",
                        ),
                        "meeting_attendance_rate",
                    ),
                    competitor_mentions=_to_int(
                        _get_optional(row, ["competitor_mentions", "competitor_count"], "0"),
                        "competitor_mentions",
                    ),
                    champion_changed=_to_bool(_get_optional(row, ["champion_changed", "new_champion"], "false")),
                    product_usage_score=_to_float(
                        _get_optional(row, ["product_usage_score", "usage_score", "product_usage"], "0"),
                        "product_usage_score",
                    ),
                    support_tickets_open=_to_int(
                        _get_optional(row, ["support_tickets_open", "open_tickets", "ticket_count"], "0"),
                        "support_tickets_open",
                    ),
                    sentiment_score=_to_float(
                        _get_optional(row, ["sentiment_score", "sentiment", "nps_sentiment"], "0"),
                        "sentiment_score",
                    ),
                ),
                external_id=account_external_id,
            )
        )

    return accounts


def parse_deals_csv(content: str) -> list[Deal]:
    columns, rows = _prepare_rows(content)
    deals: list[Deal] = []

    for row in rows:
        account_ref = _pick_value(
            row,
            columns,
            ["account_id", "customer_id", "company_id", "crm_account_id", "record_id"],
        )
        account_name = _require_any(
            _pick_value(row, columns, ["account_name", "name", "company", "account", "customer"])
            or account_ref,
            "account_name",
        )
        deals.append(
            Deal(
                account_name=account_name,
                stage=_get_optional(row, ["stage", "deal_stage", "pipeline_stage"], "Unknown"),
                value_usd=_to_int(
                    _get_optional(row, ["value_usd", "deal_value", "amount", "value"], "0"),
                    "value_usd",
                ),
                close_probability=_to_float(
                    _get_optional(row, ["close_probability", "probability", "win_probability"], "0.5"),
                    "close_probability",
                ),
                days_in_stage=_to_int(
                    _get_optional(row, ["days_in_stage", "stage_age_days"], "0"),
                    "days_in_stage",
                ),
                next_step=_get_optional(row, ["next_step", "next_action"], "Follow up with account"),
                stakeholders=_split_list(_get_optional(row, ["stakeholders", "contacts", "buyers"])),
                account_ref=account_ref or account_name,
                notes=_split_list(_get_optional(row, ["notes", "comments", "summary"])),
            )
        )

    return deals
