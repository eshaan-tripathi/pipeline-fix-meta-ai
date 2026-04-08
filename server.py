"""
FastAPI server — exposes the OpenEnv HTTP interface.

Endpoints:
  POST /reset           — body optional, task_id defaults to "task_easy"
  POST /step            — body required with edited_code
  GET  /state           — query param task_id
  GET  /health          — liveness probe
"""

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional

from env import PipelineRepairEnv
from models import PipelineAction

app = FastAPI(title="Pipeline Repair OpenEnv", version="1.0.0")

_envs: dict = {}
VALID_TASKS = ["task_easy", "task_medium", "task_hard"]


class ResetResponse(BaseModel):
    observation: dict
    done: bool = False
    reward: float = 0.0


class StepResponse(BaseModel):
    observation: dict
    reward: float
    done: bool
    info: dict


@app.get("/")
def root():
    return {
        "name": "Pipeline Repair OpenEnv",
        "tasks": VALID_TASKS,
        "endpoints": ["/reset", "/step", "/state", "/health"],
    }


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/reset")
async def reset(
    request: Request,
    task_id: Optional[str] = Query(default=None),
):
    """
    Reset the environment. Accepts task_id from JSON body, query param, or defaults to task_easy.
    Handles empty body, missing Content-Type, and bare pings from the pre-validator.
    """
    body_task_id = None
    try:
        content_type = request.headers.get("content-type", "")
        if "application/json" in content_type:
            body = await request.json()
            body_task_id = body.get("task_id") if isinstance(body, dict) else None
    except Exception:
        pass

    resolved_task_id = body_task_id or task_id or "task_easy"

    if resolved_task_id not in VALID_TASKS:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown task_id '{resolved_task_id}'. Valid: {VALID_TASKS}",
        )

    env = PipelineRepairEnv(task_id=resolved_task_id)
    _envs[resolved_task_id] = env
    obs = env.reset()

    return JSONResponse(content={
        "observation": obs.model_dump(),
        "done": False,
        "reward": 0.0,
    })


@app.post("/step")
async def step(request: Request):
    """
    Take one step. Body: {"task_id": "task_easy", "edited_code": "<python code>"}
    """
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=422, detail="Request body must be valid JSON.")

    task_id = body.get("task_id", "task_easy")
    edited_code = body.get("edited_code", "")

    if not edited_code:
        raise HTTPException(status_code=422, detail="'edited_code' field is required.")

    if task_id not in _envs:
        raise HTTPException(
            status_code=400,
            detail=f"No active episode for '{task_id}'. Call POST /reset first.",
        )

    env = _envs[task_id]
    action = PipelineAction(edited_code=edited_code)
    obs, reward, done, info = env.step(action)

    return JSONResponse(content={
        "observation": obs.model_dump(),
        "reward": reward,
        "done": done,
        "info": info,
    })


@app.get("/state")
def state(task_id: str = Query(default="task_easy")):
    if task_id not in _envs:
        raise HTTPException(
            status_code=400,
            detail=f"No active episode for '{task_id}'. Call POST /reset first.",
        )
    return _envs[task_id].state()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7860)
