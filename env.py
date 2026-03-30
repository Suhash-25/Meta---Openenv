import json
from typing import Tuple, Dict, Any
from models import Action, Observation, State

class AMLEnvironment:
    def __init__(self):
        self._state = State(current_task="easy")
        self.db = self._load_database()

    def _load_database(self):
        """The hidden truth. This simulates our bank ledgers, emails, and company registries."""
        return {
            "easy": {
                "sar": "ALERT: Employee 'Alice_Smith' flagged for unusually high corporate card expenses.",
                "ledger": {
                    "ACC-ALICE-CORP": ["-$5000 Gucci Store", "-$2000 Bahamas Resort", "-$15 Starbucks"],
                    "ACC-ALICE-PERSONAL": ["+$7000 from ACC-ALICE-CORP (Wire)"]
                },
                "emails": {"Alice_Smith": ["Hey team, just expense the luxury bags as 'client gifts' lol. Transferring cash now."]},
                "registry": {},
                "targets": ["ACC-ALICE-CORP", "ACC-ALICE-PERSONAL"]
            },
            "medium": {
                "sar": "ALERT: High volume of sudden payments to new vendor 'TechSolutions_LLC'.",
                "ledger": {
                    "ACC-CORP-MAIN": ["-$50000 to ACC-TECHSOLUTIONS"],
                    "ACC-TECHSOLUTIONS": ["+$50000 from ACC-CORP-MAIN", "-$49000 to ACC-BOB-PERSONAL"],
                    "ACC-BOB-PERSONAL": ["+$49000 from ACC-TECHSOLUTIONS"]
                },
                "emails": {"Bob_Jones": ["Let's approve the TechSolutions invoice immediately. No review needed."]},
                "registry": {"TechSolutions_LLC": "Registered Agent: Bob Jones. Status: Active."},
                "targets": ["ACC-TECHSOLUTIONS", "ACC-BOB-PERSONAL"]
            },
            "hard": {
                "sar": "ALERT: Suspicious wire pattern detected from user 'Charlie_Corp'. Possible layering.",
                "ledger": {
                    "ACC-CHARLIE": ["-$100000 to ACC-SHELL-A"],
                    "ACC-SHELL-A": ["+$100000 from ACC-CHARLIE", "-$50000 to ACC-OFFSHORE-B", "-$50000 to ACC-OFFSHORE-C"],
                    "ACC-OFFSHORE-B": ["+$50000 from ACC-SHELL-A", "-$50000 to ACC-CLEAN-WASH"],
                    "ACC-OFFSHORE-C": ["+$50000 from ACC-SHELL-A", "-$50000 to ACC-CLEAN-WASH"],
                    "ACC-CLEAN-WASH": ["+$100000 total from mixed offshore."]
                },
                "emails": {}, # Hard task requires relying strictly on ledgers
                "registry": {
                    "Shell_A": "Registered Agent: Anonymous Proxy. Jurisdiction: Cayman Islands.",
                    "CleanWash_Inc": "Registered Agent: Charlie. Jurisdiction: Panama."
                },
                "targets": ["ACC-SHELL-A", "ACC-OFFSHORE-B", "ACC-OFFSHORE-C", "ACC-CLEAN-WASH"]
            }
        }

    def reset(self, task_name: str = "easy") -> Observation:
        """Resets the environment for a specific task level."""
        if task_name not in self.db:
            raise ValueError(f"Task {task_name} not found. Choose easy, medium, or hard.")
        
        self._state = State(
            current_task=task_name,
            target_guilty_accounts=self.db[task_name]["targets"],
            frozen_accounts=[],
            step_count=0,
            is_done=False
        )
        
        return Observation(
            step_count=0,
            last_action="system_reset",
            result=f"Environment reset to '{task_name}' mode. Awaiting 'read_sar' action.",
            currently_frozen_accounts=[]
        )

    def state(self) -> State:
        """Returns the internal state (required by OpenEnv spec)."""
        return self._state

    def step(self, action: Action) -> Tuple[Observation, float, bool, Dict[str, Any]]:
        """Executes the agent's action and returns the Observation, Reward, Done flag, and Info dict."""
        if self._state.is_done:
            return self._build_obs("Error: Task already completed.", action.action_type), 0.0, True, {}

        self._state.step_count += 1
        reward = 0.0
        done = False
        result_text = ""
        db_context = self.db[self._state.current_task]

        # --- ACTION ROUTING ---
        if action.action_type == "read_sar":
            result_text = db_context["sar"]
            reward = 0.05  # Good job starting

        elif action.action_type == "query_ledger":
            if action.target in db_context["ledger"]:
                result_text = json.dumps(db_context["ledger"][action.target])
                reward = 0.1  # Found useful financial data
            else:
                result_text = f"No ledger found for {action.target}."
                reward = -0.05  # Wasting time

        elif action.action_type == "read_emails":
            if action.target in db_context["emails"]:
                result_text = json.dumps(db_context["emails"][action.target])
                reward = 0.1
            else:
                result_text = f"No emails found for {action.target}."
                reward = -0.05

        elif action.action_type == "lookup_company":
            if action.target in db_context["registry"]:
                result_text = db_context["registry"][action.target]
                reward = 0.1
            else:
                result_text = f"No company registry found for {action.target}."
                reward = -0.05

        elif action.action_type == "freeze_account":
            if not action.target:
                result_text = "Error: No account target specified."
                reward = -0.1
            elif action.target in self._state.frozen_accounts:
                result_text = f"Account {action.target} is already frozen."
                reward = -0.05
            else:
                self._state.frozen_accounts.append(action.target)
                result_text = f"SUCCESS: Account {action.target} frozen."
                # Don't reward immediately for freezing, evaluate at the end to prevent spamming.

        elif action.action_type == "submit_report":
            done = True
            self._state.is_done = True
            
            # --- THE GRADER (0.0 to 1.0) ---
            targets = set(self._state.target_guilty_accounts)
            frozen = set(self._state.frozen_accounts)
            
            correct_freezes = len(frozen.intersection(targets))
            false_positives = len(frozen - targets)
            
            # Calculate score: 1.0 for perfect accuracy. Penalize for innocent accounts frozen.
            base_score = correct_freezes / len(targets) if targets else 0.0
            penalty = false_positives * 0.5
            
            final_score = max(0.0, min(1.0, base_score - penalty))
            reward = final_score
            
            result_text = f"Report submitted. Correct: {correct_freezes}/{len(targets)}. False Positives: {false_positives}. Final Task Score: {final_score}"

        else:
            result_text = "Error: Invalid action type."
            reward = -0.1

        # Max step limit to prevent infinite loops
        if self._state.step_count >= 15 and not done:
            done = True
            self._state.is_done = True
            result_text = "Maximum steps reached. Investigation forcibly closed."
            reward = 0.0

        obs = self._build_obs(result_text, action.action_type)
        return obs, reward, done, {"task_score": reward if done else 0.0}

    def _build_obs(self, result: str, last_action: str) -> Observation:
        return Observation(
            step_count=self._state.step_count,
            last_action=last_action,
            result=result,
            currently_frozen_accounts=self._state.frozen_accounts
        )