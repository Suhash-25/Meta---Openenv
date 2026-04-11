# 🕵️‍♂️ Forensic AML Investigator OpenEnv

**An AML Reasoning Benchmark for Multi-Step Financial Investigation**

🛡️ **Category:** Financial Intelligence / RegTech  
🚀 **Difficulty:** Easy | Medium | Hard  
📦 **SDK:** Docker Compatible | FastAPI | Pydantic

---

## 📌 Problem Motivation

Financial crimes like money laundering are rarely identified in a single step. An investigator must follow a "money trail" through layers of shell companies, offshore accounts, and corporate emails to find the ultimate source or destination of illicit funds.

Most benchmarks evaluate simple classification (Is this transaction fraud: Yes/No?). **Forensic AML Investigator OpenEnv** evaluates whether an agent can reason like a practical Financial Intelligence Unit (FIU) analyst—navigating bank ledgers and corporate registries while staying fast, reproducible, and validator-friendly.

---

## ⚙️ Environment Design

The environment provides three realistic financial investigation workflows:

- **Easy:** Individual "rogue employee" fraud using corporate cards and personal accounts.
- **Medium:** Corporate embezzlement involving shell companies and vendor fraud.
- **Hard:** Multi-layered offshore laundering networks designed to "wash" funds through complex wire transfers.

**The environment tracks:**
- **Money Trail Progress:** How many layers of the laundering chain have been uncovered.
- **Freeze Accuracy:** Distinguishing between "wash" accounts and legitimate business vendors (e.g., AWS, Payroll).
- **Action History:** Ensuring the agent doesn't repeat queries and wastes resources.

---

## 🛠️ Action and Observation Spaces

### Action Space

The action space is a typed Pydantic model:

```python
class Action(BaseModel):
    action_type: str  # read_sar, query_ledger, read_emails, lookup_company, freeze_account, submit_report
    target: str       # Account ID, Employee Name, or Company Name
```

### Observation Space

The observation space returns structured financial and investigative context:

```python
class Observation(BaseModel):
    account_details: Optional[dict]
    transaction_history: Optional[list]
    email_content: Optional[str]
    company_registry: Optional[dict]
    system_message: str
```

---

## 🧠 Multi-Step Reasoning

Instead of one-shot answers, the agent must execute a sequence of investigative steps:

1. **Detect:** Extract initial IDs from a Suspicious Activity Report (SAR).
2. **Trace:** Use `query_ledger` and `read_emails` to follow transfers to downstream accounts.
3. **Contain:** Use `freeze_account` on confirmed shell/illicit accounts.
4. **Report:** Use `submit_report` to finalize the investigation.

---

## 💰 Reward Design

Rewards are shaped at every step and clamped to [0, 1]:

- **Positive Reward (+0.1):** Successfully identifying a new "layer" in the money trail.
- **Accuracy Bonus (+0.5 - 0.75):** Awarded upon `submit_report` for correctly freezing the "wash" account.
- **Penalties (-0.05):** Querying legitimate vendors (Payroll/AWS) or re-querying the same account.
- **Zero Reward:** Freezing the main origin corporate account (to avoid disrupting business operations).

---

## 🏗️ Architecture

The benchmark is split into reusable layers:

- **env/:** Stateful AML environment logic.
- **models.py:** Pydantic definitions for Actions and Observations.
- **inference.py:** The main agent runner with Recursive JSON Parsing and LLM reasoning.
- **requirements.txt:** Minimal dependencies for hackathon-speed execution.

---

## 🤖 Agent Design

The included `inference.py` uses a **Resilient Reasoning Strategy:**

- **Recursive JSON Parser:** Automatically extracts valid actions even if the LLM adds conversational "chatter" or nests the JSON incorrectly.
- **Environment-Aware Prompting:** Explicitly instructs the agent on "Freezing Rules" to ensure business continuity while stopping fraud.
- **Deterministic Step Tracking:** Strictly adheres to the `[START]`, `[STEP]`, and `[END]` logging format required for Scaler validation.

---

## 🏆 Benchmark Results

The environment is optimized for high-fidelity reasoning with low compute overhead.

| Task | Steps | Score | Notes |
|------|-------|-------|-------|
| Easy | 12 | 0.50 | Successfully identifies and freezes personal account. |
| Medium | 15 | 0.00 | Currently fails due to high-complexity ID tracing loops. |
| Hard | 9 | 0.75 | Expertly traces through Shell-A and Offshore-B to the final wash. |

**🏆 FINAL BASELINE SCORE:** 1.25 / 3.0

---

## 🔗 Interface Compatibility

This project preserves all hackathon requirements:

- ✅ 3 core tasks (Easy/Medium/Hard).
- ✅ Typed Pydantic observations and actions.
- ✅ Mandatory logging format: `[START]`, `[STEP]`, `[END]`.
- ✅ Docker-compatible and FastAPI ready.

---

## 🚀 Setup and Usage

### Local Run

```bash
# Install dependencies
pip install -r requirements.txt

# Run the investigator agent
python inference.py
```

### Environment Variables Required

Ensure the following are set in your environment:

- **API_BASE_URL:** Your LLM provider endpoint.
- **MODEL_NAME:** The model version (e.g., Llama-3).
- **HF_TOKEN:** Your HuggingFace/API key.

---

**Built with ❤️ for Financial Intelligence & RegTech Excellence**