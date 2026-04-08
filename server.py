"""
FastAPI server — exposes the OpenEnv HTTP interface.
Endpoints: POST /reset, POST /step, GET /state
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional

from env import PipelineRepairEnv
from models import PipelineAction, PipelineObservation

app = FastAPI(title="Pipeline Repair OpenEnv", version="1.0.0")

# One env instance per task; keyed by task_id
_envs: dict = {}


class ResetRequest(BaseModel):
    task_id: str = "task_easy"


class StepRequest(BaseModel):
    task_id: str = "task_easy"
    edited_code: str


class ResetResponse(BaseModel):
    observation: dict
    done: bool = False


class StepResponse(BaseModel):
    observation: dict
    reward: float
    done: bool
    info: dict


@app.get("/")
def root():
    return {
        "name": "Pipeline Repair OpenEnv",
        "tasks": ["task_easy", "task_medium", "task_hard"],
        "endpoints": ["/reset", "/step", "/state"],
    }


@app.post("/reset", response_model=ResetResponse)
def reset(req: ResetRequest):
    task_id = req.task_id
    if task_id not in ["task_easy", "task_medium", "task_hard"]:
        raise HTTPException(status_code=400, detail=f"Unknown task_id: {task_id}")
    env = PipelineRepairEnv(task_id=task_id)
    _envs[task_id] = env
    obs = env.reset()
    return ResetResponse(observation=obs.model_dump(), done=False)


@app.post("/step", response_model=StepResponse)
def step(req: StepRequest):
    task_id = req.task_id
    if task_id not in _envs:
        raise HTTPException(status_code=400, detail="Call /reset first.")
    env = _envs[task_id]
    action = PipelineAction(edited_code=req.edited_code)
    obs, reward, done, info = env.step(action)
    return StepResponse(
        observation=obs.model_dump(),
        reward=reward,
        done=done,
        info=info,
    )


@app.get("/state")
def state(task_id: str = "task_easy"):
    if task_id not in _envs:
        raise HTTPException(status_code=400, detail="Call /reset first.")
    return _envs[task_id].state()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7860)
