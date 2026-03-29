from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request

from sales_ops.engine import RevenueOpsAgent
from sales_ops.importer import CSVImportError


def create_app() -> Flask:
    load_dotenv()
    app = Flask(__name__, static_folder="public", static_url_path="")
    agent = RevenueOpsAgent()

    @app.route("/")
    def index():
        return render_template("dashboard.html", overview=agent.build_overview())

    @app.route("/api/overview")
    def overview():
        return jsonify(agent.build_overview())

    @app.route("/api/prospects")
    def prospects():
        return jsonify(agent.get_prospecting_briefs())

    @app.route("/api/deals")
    def deals():
        return jsonify(agent.get_deal_intelligence())

    @app.route("/api/retention")
    def retention():
        return jsonify(agent.get_retention_watchlist())

    @app.route("/api/competitive")
    def competitive():
        return jsonify(agent.get_competitive_briefs())

    @app.route("/api/generate/outreach/<account_name>", methods=["POST"])
    def generate_outreach(account_name: str):
        return jsonify(agent.generate_outreach(account_name))

    @app.route("/api/generate/recovery/<account_name>", methods=["POST"])
    def generate_recovery(account_name: str):
        return jsonify(agent.generate_recovery_play(account_name))

    @app.route("/api/import/crm", methods=["POST"])
    def import_crm():
        accounts_file = request.files.get("accounts_csv")
        deals_file = request.files.get("deals_csv")

        if not accounts_file or not deals_file:
            return jsonify({"error": "Both accounts_csv and deals_csv are required"}), 400

        try:
            result = agent.import_crm_data(
                accounts_file.read().decode("utf-8-sig"),
                deals_file.read().decode("utf-8-sig"),
            )
        except CSVImportError as exc:
            return jsonify({"error": str(exc)}), 400

        return jsonify(
            {
                "message": "CRM data imported successfully",
                **result,
                "overview": agent.build_overview(),
            }
        )

    return app


app = create_app()
