from pydantic import BaseModel, Field
from typing import List, Optional, Literal

class Action(BaseModel):
    action_type: Literal[
        "read_sar",           # Read the Suspicious Activity Report (starting point)
        "query_ledger",       # Check bank transactions for an account ID
        "read_emails",        # Check emails for an employee name
        "lookup_company",     # Check business registry for a company name
        "freeze_account",     # Freeze a bank account
        "submit_report"       # End the task and submit findings
    ] = Field(..., description="The specific action the agent wants to take.")
    
    target: Optional[str] = Field(
        default=None, 
        description="The ID, name, or account number to target. Leave null if reading the initial SAR."
    )
class Observation(BaseModel):
    step_count: int = Field(description="How many actions the agent has taken so far.")
    last_action: str = Field(description="A summary of the action just attempted.")
    result: str = Field(description="The data returned from the action (e.g., transaction list, email text, or error).")
    currently_frozen_accounts: List[str] = Field(description="List of accounts the agent has frozen so far.")

class State(BaseModel):
    current_task: str = Field(description="The difficulty level: easy, medium, or hard.")
    step_count: int = Field(default=0)
    frozen_accounts: List[str] = Field(default_factory=list)
    is_done: bool = Field(default=False)
    
    target_guilty_accounts: List[str] = Field(default_factory=list)
    innocent_accounts: List[str] = Field(default_factory=list)