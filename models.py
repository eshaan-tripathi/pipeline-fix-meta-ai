from pydantic import BaseModel
from typing import Optional


class PipelineObservation(BaseModel):
    broken_code: str
    error_trace: str
    sample_rows: str
    task_id: str
    step_num: int
    max_steps: int


class PipelineAction(BaseModel):
    edited_code: str


class PipelineReward(BaseModel):
    value: float
    breakdown: dict
