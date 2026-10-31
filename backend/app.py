"""Flask REST API for the Mini Business Intelligence Assistant."""
import os
from pathlib import Path
from flask import Flask, jsonify, request
from backend.database import get_connection
from backend.data_loader import import_sales_data
from backend.query_engine import interpret_question, run_analytics

ROOT_DIR = Path(__file__).resolve().parents[1]
DB_PATH = Path(os.environ.get("SALES_DB_PATH", ROOT_DIR / "backend" / "sales.db"))
CSV_PATH = Path(os.environ.get("SALES_CSV_PATH", ROOT_DIR / "data" / "sales_data.csv"))


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.update(TESTING=False)
    if test_config:
        app.config.update(test_config)

    def initialize_database():
        connection = get_connection(app.config.get("DB_PATH", DB_PATH))
        try:
            import_sales_data(connection, app.config.get("CSV_PATH", CSV_PATH))
        finally:
            connection.close()

    with app.app_context():
        initialize_database()

    @app.get("/api/health")
    def health():
        return jsonify({"status": "ok", "message": "Sales BI API is running"})

    @app.post("/api/ask")
    def ask():
        payload = request.get_json(silent=True)
        if not isinstance(payload, dict) or "question" not in payload:
            return jsonify({"error": "Request body must contain a question field."}), 400
        question = payload.get("question")
        if not isinstance(question, str) or not question.strip():
            return jsonify({"error": "Question must be a non-empty string."}), 400

        interpreted = interpret_question(question)
        if interpreted["intent"] == "unsupported":
            return jsonify({
                "question": question,
                "intent": "unsupported",
                "answer": interpreted["message"],
                "supporting_data": []
            }), 200

        connection = get_connection(app.config.get("DB_PATH", DB_PATH))
        try:
            result = run_analytics(connection, interpreted)
        finally:
            connection.close()
        result["question"] = question
        result["interpretation"] = interpreted
        return jsonify(result)

    @app.get("/api/summary")
    def summary():
        connection = get_connection(app.config.get("DB_PATH", DB_PATH))
        try:
            row = connection.execute(
                "SELECT COUNT(*) AS transactions, COALESCE(SUM(revenue),0) AS revenue FROM sales"
            ).fetchone()
            return jsonify({"transactions": row["transactions"], "revenue": row["revenue"]})
        finally:
            connection.close()

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
