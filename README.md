# 🕵️‍♂️💸 Forensic AML Investigator (OpenEnv)

An interactive, real-world OpenEnv environment where an AI agent acts as a financial forensic investigator. The agent must navigate messy data across bank ledgers, corporate emails, and business registries to trace money laundering and freeze illicit accounts.

## 🌍 Real-World Utility & Motivation
Financial institutions and governments spend billions of dollars annually on human analysts trying to trace illicit funds. Criminals use "layering"—moving money through shell companies, offshore accounts, and fake vendors—to hide its origin. 

This environment moves beyond standard coding or web-scraping tasks to test an LLM's **multi-hop reasoning**, **entity resolution**, and **high-stakes decision-making**. It models a genuine enterprise workflow where an agent must aggregate data from distinct APIs (ledgers, emails, registries) to build a case.

## 🧩 Spaces (Strictly Typed via Pydantic)

### Observation Space
After every action, the agent receives a strict `Observation` containing:
* `step_count` (int): Actions taken so far (max 15 steps per task).
* `last_action` (str): Summary of the attempted action.
* `result` (str): The returned data (e.g., a JSON list of transactions, an email body, or an error message).
* `currently_frozen_accounts` (List[str]): Accounts the agent has frozen during the episode.

### Action Space
The agent outputs a strict `Action` JSON with `action_type` and an optional `target`:
* `read_sar`: Reads the initial Suspicious Activity Report (SAR) to start the investigation.
* `query_ledger`: Checks bank transactions for a specific account ID.
* `read_emails`: Reads internal corporate emails for a specific employee.
* `lookup_company`: Checks the business registry for a company name.
* `freeze_account`: Freezes a target account based on gathered evidence.
* `submit_report`: Ends the episode and triggers the programmatic grader.

## 📈 Tasks & Difficulty Progression
1. **Easy:** A rogue employee is using a corporate card for personal luxury purchases. 
   * *Challenge:* Linking basic ledger entries to email confessions.
2. **Medium:** "Invoice Fraud." An employee set up a fake vendor company. 
   * *Challenge:* Connecting the vendor's registered agent to the employee to prove a conflict of interest.
3. **Hard:** Complex Money Laundering/Layering. Funds are split into multiple offshore shell companies. 
   * *Challenge:* Tracing a multi-hop financial graph entirely through ledger queries, identifying the flow of funds while actively ignoring innocent accounts.

## ⚖️ Meaningful Reward Function & Grader
The environment features a deterministic, programmatic grader that produces a score from `0.0` to `1.0`.

* **Partial Progress:** The agent receives small, immediate rewards (`+0.05` to `+0.1`) for successfully querying relevant databases, and penalties (`-0.05`) for querying non-existent data, providing a rich signal over the trajectory.
* **Final Score:** Upon calling `submit_report`, the environment calculates the percentage of correctly frozen guilty accounts. 
* **Penalties:** The agent is heavily penalized (`-0.5` per account) for freezing innocent accounts (false positives). Freezing the wrong account in real life carries massive compliance and legal risks, and the environment reflects this.

## 🚀 Setup & Usage

### 1. Local Installation
Clone the repository and install the dependencies:
```bash
python -m venv venv
source venv/bin/activate        # Linux/macOS
venv\Scripts\activate           # Windows
pip install -r requirements.txt
```

### 2. Configure Environment Variables
Create a `.env` file or export the following before running:
```bash
export API_BASE_URL="https://<your-openai-compatible-endpoint>/v1"
export MODEL_NAME="<your-model-name>"
export HF_TOKEN="<your-api-key>"
```

### 3. Run the Agent
```bash
python inference.py
```

## 📁 Project Structure
```
forensic-aml-env/
├── env.py            # AML environment: database, action routing, grader
├── models.py         # Pydantic models: Action, Observation, State
├── inference.py      # Baseline agent loop using an OpenAI-compatible LLM
├── requirements.txt  # Python dependencies
└── README.md
```