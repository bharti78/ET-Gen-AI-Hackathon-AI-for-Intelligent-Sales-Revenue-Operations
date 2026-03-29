from __future__ import annotations

from statistics import mean

from sales_ops.ai_client import AIMessageGenerator
from sales_ops.data import load_accounts, load_deals
from sales_ops.importer import parse_accounts_csv, parse_deals_csv
from sales_ops.models import Account, Deal


class RevenueOpsAgent:
    def __init__(self) -> None:
        self.accounts = load_accounts()
        self.deals = load_deals()
        self.generator = AIMessageGenerator()

    def import_crm_data(self, accounts_csv: str, deals_csv: str) -> dict:
        self.accounts = parse_accounts_csv(accounts_csv)
        self.deals = parse_deals_csv(deals_csv)
        return {
            "accounts_imported": len(self.accounts),
            "deals_imported": len(self.deals),
        }

    def _fit_score(self, account: Account) -> int:
        score = 40

        if account.size in {"Mid-market", "Enterprise"}:
            score += 15
        if any(tool in account.tech_stack for tool in ["Salesforce", "HubSpot", "Outreach", "Dynamics 365"]):
            score += 15
        score += min(len(account.buying_signals) * 8, 16)
        score += min(len(account.pain_points) * 4, 12)
        score += int(account.engagement.email_open_rate * 10)

        return min(score, 100)

    def _engagement_band(self, account: Account) -> str:
        engagement_score = (
            account.engagement.email_open_rate * 0.4
            + account.engagement.meeting_attendance_rate * 0.4
            + max(0.0, 1 - account.engagement.last_reply_days_ago / 14) * 0.2
        )
        if engagement_score >= 0.75:
            return "High"
        if engagement_score >= 0.5:
            return "Medium"
        return "Low"

    def _personalized_outreach(self, account: Account) -> list[str]:
        contact = account.contacts[0]
        pain = account.pain_points[0]
        signal = account.buying_signals[0]
        return [
            f"Email 1: Mention {signal} and tie our platform to fixing {pain} for {account.industry} teams.",
            f"Email 2: Share a benchmark on cycle time reduction for {account.size.lower()} revenue teams and invite {contact.name} to a 20-minute workflow review.",
            f"LinkedIn follow-up: Reference {account.region} expansion pressure and offer a pipeline risk snapshot tailored to {account.name}.",
        ]

    def _get_account(self, account_name: str) -> Account | None:
        return next((account for account in self.accounts if account.name.lower() == account_name.lower()), None)

    def _get_deal(self, account_name: str) -> Deal | None:
        return next((deal for deal in self.deals if deal.account_name.lower() == account_name.lower()), None)

    def get_prospecting_briefs(self) -> list[dict]:
        briefs = []
        for account in self.accounts:
            briefs.append(
                {
                    "account": account.name,
                    "industry": account.industry,
                    "fit_score": self._fit_score(account),
                    "engagement": self._engagement_band(account),
                    "buying_signals": account.buying_signals,
                    "pain_points": account.pain_points,
                    "recommended_sequence": self._personalized_outreach(account),
                }
            )

        return sorted(briefs, key=lambda item: item["fit_score"], reverse=True)

    def _deal_risk_score(self, deal: Deal, account: Account) -> int:
        risk = 10
        risk += min(deal.days_in_stage, 40)
        risk += int((1 - account.engagement.email_open_rate) * 20)
        risk += int((1 - account.engagement.meeting_attendance_rate) * 20)
        risk += account.engagement.competitor_mentions * 7
        risk += 15 if account.engagement.champion_changed else 0
        risk += 8 if deal.close_probability < 0.45 else 0
        return min(risk, 100)

    def _recovery_play(self, deal: Deal, account: Account, risk_score: int) -> dict:
        contact = account.contacts[0]
        talking_points = [
            f"Reconnect the value case to {account.pain_points[0]} with quantified impact.",
            f"Use the next meeting to validate stakeholder alignment across {', '.join(deal.stakeholders[:3])}.",
        ]

        if account.engagement.competitor_mentions:
            talking_points.append("Handle competitor pressure with a side-by-side rollout and ROI comparison.")
        if account.engagement.champion_changed:
            talking_points.append("Create a fresh internal champion by onboarding the new stakeholder with a custom executive brief.")

        return {
            "priority": "Critical" if risk_score >= 70 else "Watch",
            "owner": contact.name,
            "next_best_action": deal.next_step,
            "talking_points": talking_points,
        }

    def get_deal_intelligence(self) -> list[dict]:
        results = []
        account_map = {account.name: account for account in self.accounts}

        for deal in self.deals:
            account = account_map[deal.account_name]
            risk_score = self._deal_risk_score(deal, account)
            results.append(
                {
                    "account": deal.account_name,
                    "stage": deal.stage,
                    "value_usd": deal.value_usd,
                    "risk_score": risk_score,
                    "risk_signals": [
                        f"{account.engagement.last_reply_days_ago} days since last reply",
                        f"{account.engagement.competitor_mentions} competitor mentions",
                        "champion changed" if account.engagement.champion_changed else "champion stable",
                    ],
                    "recovery_play": self._recovery_play(deal, account, risk_score),
                }
            )

        return sorted(results, key=lambda item: item["risk_score"], reverse=True)

    def _retention_risk(self, account: Account) -> int:
        risk = 15
        risk += int((1 - account.engagement.product_usage_score) * 35)
        risk += account.engagement.support_tickets_open * 4
        risk += int(max(0, -account.engagement.sentiment_score) * 30)
        risk += 10 if account.engagement.last_reply_days_ago > 10 else 0
        return min(risk, 100)

    def get_retention_watchlist(self) -> list[dict]:
        watchlist = []
        for account in self.accounts:
            if account.engagement.product_usage_score <= 0:
                continue

            risk = self._retention_risk(account)
            watchlist.append(
                {
                    "account": account.name,
                    "retention_risk": risk,
                    "health_signals": {
                        "usage_score": account.engagement.product_usage_score,
                        "open_tickets": account.engagement.support_tickets_open,
                        "sentiment": account.engagement.sentiment_score,
                    },
                    "intervention": [
                        "Trigger success-manager outreach within 24 hours.",
                        "Offer a usage recovery workshop tied to the customer team's current workflow gaps.",
                        "Escalate renewal risk to the account team if health does not improve this week.",
                    ],
                }
            )

        return sorted(watchlist, key=lambda item: item["retention_risk"], reverse=True)

    def generate_outreach(self, account_name: str) -> dict:
        account = self._get_account(account_name)
        if not account:
            return {"error": "Account not found"}

        fallback = self._personalized_outreach(account)

        system_prompt = (
            "You are an expert B2B sales development AI. Write concise, persuasive outreach for a CRM copilot. "
            "Return plain text with three labeled touches: Email 1, Email 2, and LinkedIn. "
            "Make the message specific to the company context and avoid hype."
        )
        user_prompt = (
            f"Account: {account.name}\n"
            f"Industry: {account.industry}\n"
            f"Segment: {account.size}\n"
            f"Region: {account.region}\n"
            f"Pain points: {', '.join(account.pain_points)}\n"
            f"Buying signals: {', '.join(account.buying_signals)}\n"
            f"Tech stack: {', '.join(account.tech_stack)}\n"
            f"Primary contact: {account.contacts[0].name}, {account.contacts[0].role}\n"
            "Goal: Book a discovery call."
        )
        generated = self.generator.generate(system_prompt, user_prompt)

        return {
            "account": account.name,
            "mode": self.generator.provider if generated else "fallback",
            "model": self.generator.model if generated else None,
            "content": generated if generated else "\n".join(fallback),
        }

    def generate_recovery_play(self, account_name: str) -> dict:
        account = self._get_account(account_name)
        deal = self._get_deal(account_name)
        if not account or not deal:
            return {"error": "Deal not found"}

        risk_score = self._deal_risk_score(deal, account)
        fallback = self._recovery_play(deal, account, risk_score)

        system_prompt = (
            "You are a revenue operations AI agent helping sellers recover at-risk deals. "
            "Return plain text with sections: Summary, Recovery Strategy, Talking Points, and Next Meeting Agenda. "
            "Keep it practical and tailored to the account."
        )
        user_prompt = (
            f"Account: {account.name}\n"
            f"Industry: {account.industry}\n"
            f"Deal stage: {deal.stage}\n"
            f"Deal value: ${deal.value_usd}\n"
            f"Close probability: {deal.close_probability}\n"
            f"Days in stage: {deal.days_in_stage}\n"
            f"Pain points: {', '.join(account.pain_points)}\n"
            f"Signals: last reply {account.engagement.last_reply_days_ago} days ago, "
            f"email open rate {account.engagement.email_open_rate}, "
            f"meeting attendance {account.engagement.meeting_attendance_rate}, "
            f"competitor mentions {account.engagement.competitor_mentions}, "
            f"champion changed {account.engagement.champion_changed}\n"
            f"Stakeholders: {', '.join(deal.stakeholders)}\n"
            f"Current next step: {deal.next_step}\n"
            f"Recent notes: {', '.join(deal.notes)}"
        )
        generated = self.generator.generate(system_prompt, user_prompt)

        fallback_text = "\n".join(
            [
                f"Summary: {deal.account_name} is at risk with score {risk_score}.",
                f"Recovery Strategy: {fallback['next_best_action']}",
                "Talking Points:",
                *[f"- {item}" for item in fallback["talking_points"]],
                "Next Meeting Agenda:",
                "- Reconfirm business urgency",
                "- Map stakeholder alignment",
                "- Close on a mutual action plan",
            ]
        )

        return {
            "account": account.name,
            "mode": self.generator.provider if generated else "fallback",
            "model": self.generator.model if generated else None,
            "risk_score": risk_score,
            "content": generated if generated else fallback_text,
        }

    def get_competitive_briefs(self) -> list[dict]:
        briefs = []
        for deal in self.get_deal_intelligence():
            if deal["risk_score"] < 45:
                continue

            briefs.append(
                {
                    "account": deal["account"],
                    "risk_score": deal["risk_score"],
                    "battlecard": {
                        "positioning": "Lead with revenue visibility, faster recovery actions, and lower manual CRM overhead.",
                        "proof_points": [
                            "Real-time pipeline risk scoring across engagement and stakeholder signals.",
                            "Guided next-best-action plays for sellers and account teams.",
                            "Retention alerts that connect customer health to revenue outcomes.",
                        ],
                        "landmine_to_handle": "Buyers may believe competitor dashboards are enough; stress actionability, not just reporting.",
                    },
                }
            )

        return briefs

    def build_overview(self) -> dict:
        prospects = self.get_prospecting_briefs()
        deals = self.get_deal_intelligence()
        retention = self.get_retention_watchlist()
        competitive = self.get_competitive_briefs()

        total_pipeline = sum(deal.value_usd for deal in self.deals)
        at_risk_pipeline = sum(deal["value_usd"] for deal in deals if deal["risk_score"] >= 60)

        return {
            "headline": "AI agent for prospecting, deal recovery, and revenue retention",
            "ai_generation_enabled": self.generator.enabled,
            "ai_model": self.generator.model if self.generator.enabled else None,
            "metrics": {
                "accounts_monitored": len(self.accounts),
                "active_deals": len(self.deals),
                "total_pipeline_usd": total_pipeline,
                "at_risk_pipeline_usd": at_risk_pipeline,
                "avg_fit_score": round(mean(item["fit_score"] for item in prospects), 1),
                "avg_deal_risk": round(mean(item["risk_score"] for item in deals), 1),
            },
            "top_prospects": prospects[:3],
            "deal_watchlist": deals[:2],
            "retention_watchlist": retention[:2],
            "competitive_briefs": competitive[:2],
            "automation_summary": [
                "Prospects are researched and scored from CRM-style firmographic and buying signals.",
                "Deal health is monitored for competitor pressure, stalled engagement, and stakeholder change.",
                "Retention workflows trigger before revenue is lost using usage and sentiment risk signals.",
                "Competitive battlecards are pushed into active deal contexts when pressure increases.",
            ],
        }
