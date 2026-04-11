# 🕵️‍♂️ Forensic AML Investigator OpenEnv
**An AML Reasoning Benchmark for Multi-Step Financial Investigation**

🛡️ **Category:** Financial Intelligence / RegTech  
🚀 **Difficulty:** Easy | Medium | Hard  
📦 **SDK:** Docker Compatible | FastAPI | Pydantic  

---

## 📌 Problem Motivation
Financial crimes like money laundering are rarely identified in a single answer. An analyst must follow a "money trail" through layers of shell companies, offshore accounts, and corporate emails to find the ultimate source of illicit funds. 

**Forensic AML Investigator OpenEnv** was built to evaluate whether an agent can reason like a practical Financial Intelligence Unit (FIU) analyst. It moves beyond simple classification to test if an agent can navigate bank ledgers and corporate registries while staying fast, reproducible, and hackathon-friendly.

---

## ⚙️ Environment Design
CyberOps OpenEnv provides three realistic financial investigation workflows:
* **Easy:** Individual "rogue employee" fraud using corporate cards and personal accounts.
* **Medium:** Corporate embezzlement involving shell companies and vendor fraud.
* **Hard:** Multi-layered offshore laundering networks designed to "wash" funds through complex wire transfers.

**The environment tracks:**
* **Money Trail Progress:** How many layers of the laundering chain have been uncovered.
* **Freeze Accuracy:** Distinguishing between "wash" accounts and legitimate business vendors (e.g., AWS, Payroll).
* **Action History:** Ensuring the agent doesn't repeat queries or waste resources.

---

## 🛠️ Action and Observation Spaces

### Action Space
The action space is a typed Pydantic model:
```python
class Action(BaseModel):
    action_type: str  # read_sar, query_ledger, read_emails, lookup_company, freeze_account, submit_report
    target: str       # Account ID, Employee Name, or Company Name
Observation SpaceThe observation space returns structured financial and investigative context:Pythonclass Observation(BaseModel):
    account_details: Optional[dict]
    transaction_history: Optional[list]
    email_content: Optional[str]
    company_registry: Optional[dict]
    system_message: str
🧠 Multi-Step ReasoningInstead of one-shot answers, scenarios are broken into sequential investigative stages:Detect: Extract initial identifiers from a Suspicious Activity Report (SAR).Trace: Use query_ledger and read_emails to follow transfers to downstream accounts.Contain: Use freeze_account on confirmed shell/illicit accounts.Report: Use submit_report to finalize the investigation and stop the money laundering.💰 Reward DesignRewards are shaped at every step and clamped to [0, 1]:Partial Correctness (+0.1): Identifying a new layer in the laundering chain.Operational Completeness (+0.5 - 0.75): Awarded for correctly freezing the "wash" account before reporting.Penalties (-0.05): Querying legitimate vendors (Payroll/AWS) or re-querying the same account.Safety Guardrails: Zero reward for freezing origin corporate accounts to avoid disrupting legitimate business operations.📊 Benchmark Results (Baseline)The environment is designed to remain lightweight while surfacing rich reasoning behavior.TaskStepsScoreNotesEasy120.50Successfully identifies and freezes personal account.Medium150.00Exposes weaknesses in handling complex ID tracing loops.Hard90.75Expertly traces through shell networks to the final wash.🏆 FINAL BASELINE SCORE: 1.25 / 3.0🚀 Setup and UsageLocal SetupBashpip install -r requirements.txt
Run the AgentBashpython inference.py
Required Environment VariablesEnsure the following are set in your environment:API_BASE_URL: LLM provider endpoint.MODEL_NAME: Model version (e.g., Llama-3).HF_TOKEN: HuggingFace/API key.🌟 Why This Stands OutForensic AML Investigator OpenEnv is not just a toy environment with themed strings. It behaves like a compact SOC simulation for finance. It forces agents to build a response over time, justify severity, and remember prior decisions. This makes it judge-friendly, realistic, and aligned with real-world AI-for-Financial-Security evaluation.
