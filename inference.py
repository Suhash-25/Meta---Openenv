import os
import re
import json
import time
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
        # --- MANDATORY: START TAG ---
        print(f"[START] task={task}", flush=True) 

        obs = env.reset(task)
        done = False
        step_count = 0
        
        # History of the conversation for the LLM
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
                    "1. For `query_ledger` and `freeze_account`, use exact Account IDs.\n"
                    "2. For `read_emails`, use exact Employee Names.\n"
                    "3. For `lookup_company`, use exact Company Names.\n"
                    "4. TRACING RULE: Do NOT submit early! Follow the money to the end.\n"
                    "5. Output ONLY raw JSON starting with { and ending with }.\n\n"
                    "Schema:\n"
                    "{\n"
                    '  "action_type": "read_sar" | "query_ledger" | "read_emails" | "lookup_company" | "freeze_account" | "submit_report",\n'
                    '  "target": "string or null"\n'
                    "}\n"
                )
            }
        ]

        # 5. The Agent Loop (max 15 steps per task)
        while not done and step_count < 15:
            step_count += 1 

            # Force a submission if we are at the limit
            if step_count == 15:
                messages.append({"role": "user", "content": "CRITICAL: Final step. You MUST call submit_report now."})

            messages.append({
                "role": "user",
                "content": f"CURRENT OBSERVATION:\n{obs.model_dump_json(indent=2)}\n\nWhat is your next action (JSON only)?"
            })

            time.sleep(4) # Rate limit safety

            try:
                response = client.chat.completions.create(
                    model=model_name or "",
                    messages=cast(Iterable[ChatCompletionMessageParam], messages),
                    temperature=0.1, 
                )
                
                llm_output = (response.choices[0].message.content or "").strip()
                messages.append({"role": "assistant", "content": llm_output})

                # --- IMPROVED REGEX PARSER ---
                # Extracts only the JSON object, ignoring any extra chatter or markdown
                match = re.search(r'(\{.*\})', llm_output, re.DOTALL)
                clean_output = match.group(1) if match else llm_output
                
                action_dict = json.loads(clean_output)
                action = Action(**action_dict)
                
                print(f"🤖 Agent Action: {action.action_type} | Target: {action.target}")

                # Step the environment forward
                obs, reward, done, info = env.step(action)
                
                # --- MANDATORY: STEP TAG ---
                print(f"[STEP] step={step_count} reward={reward}", flush=True)
                
                if done:
                    task_score = info.get('task_score', 0.0)
                    # --- MANDATORY: END TAG ---
                    print(f"[END] task={task} score={task_score} steps={step_count}", flush=True)
                    total_score += task_score

            except Exception as e:
                print(f"⚠️ Agent Error / Rate Limit: {e}")
                obs_error = f"System Error: {str(e)}. Please output strictly valid JSON."
                messages.append({"role": "user", "content": obs_error})
                
                # Recover from potential 429 rate limits
                print("⏳ Sleeping for 20 seconds...")
                time.sleep(20)
                
                if len(messages) > 40:
                    print(f"❌ Task '{task}' aborted due to excessive errors.")
                    break

    # 6. Final Evaluation Output
    max_possible = len(tasks)
    print("==========================================")
    print(f"🏆 FINAL BASELINE SCORE: {total_score} / {max_possible}")
    print("==========================================")

if __name__ == "__main__":
    main()