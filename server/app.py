import os
import sys
import argparse
import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel

# Ensure we can import from your root directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from env import AMLEnvironment
from models import Action

app = FastAPI(title="Forensic AML Investigator API")
env = AMLEnvironment()

class ResetRequest(BaseModel):
    task_name: str = "easy"

@app.get("/")
def root():
    return {"status": "ok", "message": "OpenEnv Server Running"}

@app.post("/reset")
def reset(req: ResetRequest = ResetRequest()):
    task = req.task_name
    obs = env.reset(task)
    return obs.model_dump()

@app.post("/step")
def step(action: Action):
    obs, reward, done, info = env.step(action)
    return {
        "observation": obs.model_dump(),
        "reward": float(reward),
        "done": bool(done),
        "info": info
    }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=7860)
    args, _ = parser.parse_known_args()
    uvicorn.run(app, host="0.0.0.0", port=args.port)

if __name__ == "__main__":
    main()