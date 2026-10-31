# Simple explanation of the project

## 30-second introduction

"I built a Mini AI Business Intelligence Assistant. It allows a user to ask questions about sales data in normal language. The CSV data is cleaned with Pandas and stored in SQLite. A Flask API receives the question, maps it to a supported analytics intent, runs a predefined SQL query, and returns the answer with supporting figures. Streamlit provides the user interface."

## Explain the flow

1. The user types a question in Streamlit.
2. Streamlit sends the question to Flask using an HTTP POST request.
3. The question interpreter identifies the intended analytics operation.
4. The backend runs a predefined SQL SELECT query against SQLite.
5. Flask returns JSON containing the answer and supporting data.
6. Streamlit displays the answer and table/chart.

## Important honesty point about AI

"This version does not call an external LLM because I did not have an API key. It uses a rule-based natural-language intent interpreter as a no-key fallback. It is not a generative AI model. I designed the interpreter so an LLM can later be added to map questions to the same limited set of allowed intents."

## Common questions

**Why SQLite?**
It is lightweight, file-based, requires no separate database server, and is suitable for this small assignment.

**Why Pandas?**
It makes reading the CSV, converting dates/numbers, detecting missing values, and cleaning records straightforward.

**How is revenue calculated?**
For each valid completed transaction: quantity multiplied by unit price, minus discount amount.

**How do you handle returned transactions?**
They are excluded from revenue calculations because they do not represent completed sales under the cleaning policy.

**How do you prevent destructive SQL?**
The application never executes SQL generated from the user's text. It selects from predefined read-only SELECT queries.

**What happens if the user asks an unsupported question?**
The API returns a helpful message listing the types of questions it supports.

**What would you improve?**
I would integrate an LLM with structured output and strict intent validation, add richer date filtering, improve the interface, and deploy the app securely.

## Before the interview

Run the project yourself, ask all five sample questions, run the tests, and make sure you can explain each step in your own words. Do not memorize an explanation for code you have not run or understood.
