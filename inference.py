import os
import json
from typing import Any
from openai import OpenAI
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
        messages: list[Any] = [
            {
                "role": "system",
                "content": (
                    "You are a Forensic AML (Anti-Money Laundering) Investigator. "
                    "Your job is to read Suspicious Activity Reports (SAR), query bank ledgers, "
                    "read employee emails, and check company registries to find illicit funds. "
                    "Once you find the guilty accounts, freeze them. Do NOT freeze innocent accounts. "
                    "When finished, submit your report.\n\n"
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
                    messages=messages,
                    temperature=0.1, # Keep it deterministic and focused
                )
                
                llm_output = (response.choices[0].message.content or "").strip()
                messages.append({"role": "assistant", "content": llm_output})

                # Try to parse the LLM's output into our strict Pydantic model
                action_dict = json.loads(llm_output)
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