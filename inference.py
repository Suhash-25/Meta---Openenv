import os
import json
from typing import Any, cast, Iterable
from openai import OpenAI
from openai.types.chat import ChatCompletionMessageParam
from env import AMLEnvironment
from models import Action

def main():
    # 1. Load required environment variables (Strict OpenEnv Rule)
    api_base = os.getenv("API_BASE_URL")
    model_name = os.getenv("MODEL_NAME")
    api_key = os.getenv("HF_TOKEN")

    if not all([api_base, model_name, api_key]):
        raise ValueError("Missing required environment variables: API_BASE_URL, MODEL_NAME, or HF_TOKEN")

    # 2. Initialize the OpenAI-compatible client
    client = OpenAI(
        base_url=api_base,
        api_key=api_key
    )

    # 3. Initialize our Environment
    env = AMLEnvironment()
    tasks = ["easy", "medium", "hard"]
    total_score = 0.0

    print("🕵️‍♂️ Starting Forensic AML Investigator Baseline Agent...\n")

    # 4. Loop through each difficulty level
    for task in tasks:
        print(f"--- Starting Task: {task.upper()} ---")
        obs = env.reset(task)
        done = False
        
        # We keep a history of the conversation for the LLM
        messages: list[dict[str, Any]] = [
            {
                "role": "system",
                "content": (
                    "You are a Forensic AML (Anti-Money Laundering) Investigator. "
                    "Your job is to read Suspicious Activity Reports (SAR), query bank ledgers, "
                    "read employee emails, and check company registries to find illicit funds. "
                    "Once you find the guilty accounts, freeze them. Do NOT freeze innocent accounts. "
                    "When finished, use submit_report.\n\n"
                    "CRITICAL RULES:\n"
                    "1. For `query_ledger` and `freeze_account`, use the exact Account ID (e.g., 'ACC-ALICE-CORP', 'ACC-TECHSOLUTIONS').\n"
                    "2. For `read_emails`, use exact Employee Names (e.g., 'Alice_Smith').\n"
                    "3. For `lookup_company`, use exact Company Names (e.g., 'TechSolutions_LLC').\n"
                    "4. TRACING RULE: Do NOT submit your report early! You must use `query_ledger` on EVERY suspicious account you discover to follow the money. If Account A sends money to B and C, you must query B and C to see if they send money to D.\n"
                    "5. FREEZING RULES:\n"
                    "   - Freeze ALL accounts involved in the fraud.\n"
                    "   - If a rogue employee is committing fraud on their specific individual corporate card (e.g., ACC-ALICE-CORP), freeze it AND their personal account.\n"
                    "   - If money is being layered out of a company's MAIN wire account (e.g., ACC-CHARLIE) into shell companies, do NOT freeze the main company account. ONLY freeze the downstream shell and offshore accounts.\n\n"
                    "You must ONLY respond with valid JSON matching this schema:\n"
                    "{\n"
                    '  "action_type": "read_sar" | "query_ledger" | "read_emails" | "lookup_company" | "freeze_account" | "submit_report",\n'
                    '  "target": "string or null"\n'
                    "}\n"
                    "Do not include markdown blocks like ```json, just output the raw JSON."
                )
            }
        ]

        # 5. The Agent Loop (max 15 steps per task)
        while not done:
            # Tell the LLM what it currently sees
            messages.append({
                "role": "user",
                "content": f"CURRENT OBSERVATION:\n{obs.model_dump_json(indent=2)}\n\nWhat is your next action (JSON only)?"
            })

            try:
                # Call the LLM
                response = client.chat.completions.create(
                    model=model_name or "",
                    messages=cast(Iterable[ChatCompletionMessageParam], messages),
                    temperature=0.1, # Keep it deterministic and focused
                )
                
                llm_output = (response.choices[0].message.content or "").strip()
                messages.append({"role": "assistant", "content": llm_output})

                # --- BULLETPROOF JSON PARSER ---
                # Strip markdown blocks in case the LLM hallucinates them
                clean_output = llm_output
                if clean_output.startswith("```json"):
                    clean_output = clean_output.split("```json", 1)[1]
                elif clean_output.startswith("```"):
                    clean_output = clean_output.split("```", 1)[1]
                if clean_output.endswith("```"):
                    clean_output = clean_output.rsplit("```", 1)[0]
                clean_output = clean_output.strip()
                
                # Parse output to Pydantic model
                action_dict = json.loads(clean_output)
                action = Action(**action_dict)
                
                print(f"🤖 Agent Action: {action.action_type} | Target: {action.target}")

                # Step the environment forward
                obs, reward, done, info = env.step(action)
                
                if done:
                    print(f"✅ Task '{task}' Complete! Score: {info['task_score']}\n")
                    total_score += info['task_score']

            except Exception as e:
                print(f"⚠️ Agent Error / Bad JSON: {e}")
                # If the LLM messes up, tell it so it can fix it on the next loop
                obs_error = f"System Error: {str(e)}. Please ensure you output strictly valid JSON matching the schema."
                messages.append({"role": "user", "content": obs_error})
                
                # Failsafe to prevent infinite error loops
                if len(messages) > 30:
                    print(f"❌ Task '{task}' failed due to too many errors.")
                    break

    # 6. Final Evaluation Output
    max_possible = len(tasks)
    print("==========================================")
    print(f"🏆 FINAL BASELINE SCORE: {total_score} / {max_possible}")
    print("==========================================")

if __name__ == "__main__":
    main()