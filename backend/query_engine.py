"""Safe question interpretation and deterministic SQL analytics.

This starter uses a transparent rule-based intent interpreter because no
external LLM API key is configured. It never executes SQL supplied by a user.
"""
import re
from datetime import datetime

INTENTS = {
    "total_revenue": ("total revenue", "revenue", "sales revenue", "how much", "overall sales"),
    "top_product": ("highest revenue product", "top product", "best selling product",
                    "product generated", "which product", "most revenue product"),
    "monthly_trend": ("monthly revenue", "revenue trend", "month wise", "monthly trend",
                      "revenue by month", "trend"),
    "top_region": ("highest sales region", "top region", "best region",
                   "which region", "region generated", "sales by region"),
    "compare_months": ("compare", "between", "change between", "difference between",
                       "revenue change", "compared to"),
}


def interpret_question(question):
    """Map a supported natural-language question to a known analytics intent."""
    if not isinstance(question, str) or not question.strip():
        return {"intent": "unsupported", "message": "Please enter a question."}

    normalized = re.sub(r"[^a-z0-9 ]", " ", question.lower())
    normalized = re.sub(r"\s+", " ", normalized).strip()

    # Month comparison is checked before general monthly trend.
    month_names = (
        "january", "february", "march", "april", "may", "june",
        "july", "august", "september", "october", "november", "december"
    )
    mentioned_months = [m for m in month_names if re.search(rf"\b{m}\b", normalized)]
    if len(mentioned_months) >= 2 and any(
        word in normalized for word in ("between", "compare", "compared", "change", "difference")
    ):
        return {"intent": "compare_months", "months": mentioned_months[:2]}

    if any(term in normalized for term in INTENTS["top_product"]):
        return {"intent": "top_product"}
    if any(term in normalized for term in INTENTS["top_region"]):
        return {"intent": "top_region"}
    if any(term in normalized for term in INTENTS["monthly_trend"]):
        return {"intent": "monthly_trend"}
    if any(term in normalized for term in INTENTS["compare_months"]):
        if len(mentioned_months) >= 2:
            return {"intent": "compare_months", "months": mentioned_months[:2]}
        return {"intent": "unsupported", "message": "Please mention two months, such as January and February."}
    if any(term in normalized for term in INTENTS["total_revenue"]):
        return {"intent": "total_revenue"}

    return {
        "intent": "unsupported",
        "message": "I can answer questions about total revenue, top product, monthly trend, top region, or comparison between two months."
    }


def run_analytics(connection, interpreted):
    """Execute only predefined read-only SELECT queries."""
    intent = interpreted["intent"]

    if intent == "total_revenue":
        row = connection.execute(
            "SELECT COALESCE(SUM(revenue), 0) AS revenue, COUNT(*) AS transactions FROM sales"
        ).fetchone()
        amount = float(row["revenue"])
        return {
            "intent": intent,
            "answer": f"Total revenue is ₹{amount:,.2f} from {row['transactions']} valid completed transactions.",
            "supporting_data": [{"metric": "Total revenue", "value": amount},
                                {"metric": "Valid transactions", "value": row["transactions"]}]
        }

    if intent == "top_product":
        rows = connection.execute("""
            SELECT product, SUM(revenue) AS revenue
            FROM sales GROUP BY product ORDER BY revenue DESC
        """).fetchall()
        if not rows:
            return {"intent": intent, "answer": "No valid sales data is available.", "supporting_data": []}
        top = rows[0]
        return {
            "intent": intent,
            "answer": f"{top['product']} generated the highest revenue: ₹{top['revenue']:,.2f}.",
            "supporting_data": [{"product": r["product"], "revenue": float(r["revenue"])} for r in rows]
        }

    if intent == "monthly_trend":
        rows = connection.execute("""
            SELECT strftime('%Y-%m', order_date) AS month,
                   SUM(revenue) AS revenue
            FROM sales GROUP BY month ORDER BY month
        """).fetchall()
        data = [{"month": r["month"], "revenue": float(r["revenue"])} for r in rows]
        return {
            "intent": intent,
            "answer": "Here is the monthly revenue trend for the available completed transactions.",
            "supporting_data": data
        }

    if intent == "top_region":
        rows = connection.execute("""
            SELECT region, SUM(revenue) AS revenue
            FROM sales GROUP BY region ORDER BY revenue DESC
        """).fetchall()
        if not rows:
            return {"intent": intent, "answer": "No valid sales data is available.", "supporting_data": []}
        top = rows[0]
        return {
            "intent": intent,
            "answer": f"{top['region']} generated the highest sales revenue: ₹{top['revenue']:,.2f}.",
            "supporting_data": [{"region": r["region"], "revenue": float(r["revenue"])} for r in rows]
        }

    if intent == "compare_months":
        months = interpreted.get("months", [])
        if len(months) != 2:
            return {"intent": intent, "answer": "Please provide two months to compare.", "supporting_data": []}
        month_map = {datetime.strptime(m, "%B").strftime("%m"): m.title() for m in months}
        results = []
        for month_number, month_name in month_map.items():
            row = connection.execute("""
                SELECT COALESCE(SUM(revenue), 0) AS revenue
                FROM sales WHERE strftime('%m', order_date) = ?
            """, (month_number,)).fetchone()
            results.append({"month": month_name, "revenue": float(row["revenue"])})
        difference = results[1]["revenue"] - results[0]["revenue"]
        direction = "increased" if difference > 0 else "decreased" if difference < 0 else "did not change"
        return {
            "intent": intent,
            "answer": (
                f"Revenue {direction} by ₹{abs(difference):,.2f} from "
                f"{results[0]['month']} to {results[1]['month']}."
            ),
            "supporting_data": results,
            "difference": difference
        }

    return {"intent": "unsupported", "answer": interpreted.get("message", "Unsupported question."),
            "supporting_data": []}
