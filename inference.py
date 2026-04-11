import os
import re
import json
import time
import sys
from typing import Any, cast, Iterable
from openai import OpenAI
from openai.types.chat import ChatCompletionMessageParam
from env import AMLEnvironment
from models import Action

def main():
    api_base = os.getenv("API_BASE_URL")
    model_name = os.getenv("MODEL_NAME")
    api_key = os.getenv("HF_TOKEN")

    if not all([api_base, model_name, api_key]):
        print("Missing API credentials.", file=sys.stderr)
        return

    client = OpenAI(base_url=api_base, api_key=api_key)
    env = AMLEnvironment()
    tasks = ["easy", "medium", "hard"]
    cumulative_score = 0.0

    print("🕵️‍♂️ Starting Forensic AML Investigator Baseline Agent...\n", flush=True)

    for task in tasks:
        print(f"[START] task={task}", flush=True)
        obs = env.reset(task)
        done = False
        step_count = 0
        
        # We track history locally to detect loops
        action_history = []

        messages: list[dict[str, Any]] = [
            {
                "role": "system",
                "content": (
                    "You are a Senior AML Investigator. Your ONLY goal is to find the illicit account, FREEZE it, and SUBMIT.\n\n"
                    "INVESTIGATION PROTOCOL:\n"
                    "1. Read SAR to get the first account.\n"
                    "2. Query the ledger. If you see a transfer to a suspicious/new account, query THAT account next.\n"
                    "3. Once you reach an account that is clearly a 'wash' account (money pools there), use 'freeze_account'.\n"
                    "4. IMMEDIATELY after freezing the guilty account(s), use 'submit_report' to end the mission.\n\n"
                    "STRICT LIMITS:\n"
                    "- Never query the same target twice.\n"
                    "- Do NOT use more than 10 steps. Be efficient.\n"
                    "- Use ONLY these actions: read_sar, query_ledger, read_emails, lookup_company, freeze_account, submit_report.\n\n"
                    "JSON ONLY: {\"action_type\": \"...\", \"target\": \"...\"}"
                )
            }
        ]

        while not done and step_count < 15:
            step_count += 1
            
            # Inject a "Pressure" message if the agent is taking too long
            user_msg = f"STEP {step_count}/15. OBSERVATION:\n{obs.model_dump_json()}\n"
            if step_count > 8:
                user_msg += "CRITICAL: You are running out of time. If you have found the fraud, FREEZE and SUBMIT now."
            
            messages.append({"role": "user", "content": user_msg})

            try:
                response = client.chat.completions.create(
                    model=model_name or "",
                    messages=cast(Iterable[ChatCompletionMessageParam], messages),
                    temperature=0.1,
                )
                
                llm_output = (response.choices[0].message.content or "").strip()
                messages.append({"role": "assistant", "content": llm_output})

                # 1. Extract JSON
                match = re.search(r'(\{.*\})', llm_output, re.DOTALL)
                clean_output = match.group(1) if match else llm_output
                data = json.loads(clean_output)

                # 2. HARD-CODED REPAIR: Fix 'query_account' hallucination and 'action' key
                raw_action = data.get("action_type") or data.get("action")
                if raw_action == "query_account":
                    raw_action = "query_ledger"
                
                final_data = {
                    "action_type": raw_action,
                    "target": data.get("target")
                }

                action = Action(**final_data)
                
                # 3. LOOP DETECTION
                action_sig = f"{action.action_type}-{action.target}"
                if action_sig in action_history:
                    messages.append({"role": "user", "content": f"WARNING: You already tried {action_sig}. DO NOT REPEAT ACTIONS. Move to the next account or SUBMIT."})
                action_history.append(action_sig)

                # 4. EXECUTE
                print(f"DEBUG: {task} | Step {step_count} | {action.action_type} -> {action.target}", file=sys.stderr, flush=True)
                obs, reward, done, info = env.step(action)
                
                # Clamped Reward for Validator
                print(f"[STEP] step={step_count} reward={max(0.01, min(0.99, float(reward)))}", flush=True)

                if done:
                    safe_score = max(0.01, min(0.99, float(info.get('task_score', 0.0))))
                    cumulative_score += safe_score
                    print(f"[END] task={task} score={safe_score} steps={step_count}", flush=True)

            except Exception as e:
                print(f"⚠️ Error: {e}", file=sys.stderr)
                if step_count == 15:
                    print(f"[STEP] step={step_count} reward=0.01", flush=True)
                    print(f"[END] task={task} score=0.01 steps={step_count}", flush=True)
                    break
            
            sys.stdout.flush()

    print("\n" + "="*42)
    print(f"🏆 FINAL BASELINE SCORE: {cumulative_score:.2f} / 3")
    print("="*42)

if __name__ == "__main__":
    main()