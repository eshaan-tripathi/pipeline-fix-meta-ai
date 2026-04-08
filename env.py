"""
PipelineRepairEnv — OpenEnv-compliant environment.

step(action)  → (observation, reward, done, info)
reset()       → observation
state()       → current state dict
"""

import importlib
from typing import Optional, Tuple, Any

from models import PipelineObservation, PipelineAction, PipelineReward
from sandbox import run_agent_code
from graders.graders import GRADER_REGISTRY

STEP_PENALTY = 0.05
CRASH_PENALTY = 0.1
SUCCESS_THRESHOLD = 0.90


class PipelineRepairEnv:
    def __init__(self, task_id: str = "task_easy"):
        assert task_id in GRADER_REGISTRY, f"Unknown task: {task_id}"
        self.task_id = task_id
        self._task = self._load_task(task_id)
        self._step_num = 0
        self._done = False
        self._best_score = 0.0
        self._current_code = self._task.BROKEN_CODE
        self._current_error = ""

    def _load_task(self, task_id: str):
        module = importlib.import_module(f"tasks.{task_id}")
        return module

    def _get_data_files(self) -> dict:
        t = self._task
        # Each task module exposes its data as module-level constants
        files = {}
        if hasattr(t, "SAMPLE_DATA_CSV"):
            files["sales.csv"] = t.SAMPLE_DATA_CSV
        if hasattr(t, "MONTHLY_JAN_CSV"):
            files["monthly_jan.csv"] = t.MONTHLY_JAN_CSV
        if hasattr(t, "MONTHLY_FEB_CSV"):
            files["monthly_feb.csv"] = t.MONTHLY_FEB_CSV
        if hasattr(t, "FX_RATES_CSV"):
            files["fx_rates.csv"] = t.FX_RATES_CSV
        # Medium task
        if self.task_id == "task_medium" and hasattr(t, "SAMPLE_DATA_CSV"):
            files = {"transactions.csv": t.SAMPLE_DATA_CSV}
        return files

    def _make_observation(self) -> PipelineObservation:
        # Show first 10 lines of one sample file as context
        data_files = self._get_data_files()
        sample_rows = ""
        if data_files:
            first_file = next(iter(data_files.values()))
            lines = first_file.strip().split("\n")[:10]
            sample_rows = "\n".join(lines)

        return PipelineObservation(
            broken_code=self._current_code,
            error_trace=self._current_error,
            sample_rows=sample_rows,
            task_id=self.task_id,
            step_num=self._step_num,
            max_steps=self._task.MAX_STEPS,
        )

    def reset(self) -> PipelineObservation:
        self._step_num = 0
        self._done = False
        self._best_score = 0.0
        self._current_code = self._task.BROKEN_CODE
        self._current_error = ""
        return self._make_observation()

    def step(self, action: PipelineAction) -> Tuple[PipelineObservation, float, bool, dict]:
        if self._done:
            raise RuntimeError("Episode is done. Call reset() to start a new episode.")

        self._step_num += 1
        code = action.edited_code
        data_files = self._get_data_files()
        grader = GRADER_REGISTRY[self.task_id]
        golden_csv = self._task.GOLDEN_OUTPUT_CSV

        success, output_csv, error_trace = run_agent_code(code, data_files)

        if not success:
            reward_value = max(0.0, self._best_score - CRASH_PENALTY)
            self._current_error = error_trace
            breakdown = {"crash": True, "penalty": -CRASH_PENALTY}
        else:
            raw_score, breakdown = grader.score(output_csv, golden_csv)
            step_penalty = STEP_PENALTY * (self._step_num - 1)
            reward_value = round(max(0.0, raw_score - step_penalty), 4)
            self._best_score = max(self._best_score, reward_value)
            self._current_error = ""
            self._current_code = code

        done = (
            reward_value >= SUCCESS_THRESHOLD
            or self._step_num >= self._task.MAX_STEPS
        )
        self._done = done

        obs = self._make_observation()
        info = {"breakdown": breakdown, "step": self._step_num, "best_score": self._best_score}

        return obs, reward_value, done, info

    def state(self) -> dict:
        return {
            "task_id": self.task_id,
            "step_num": self._step_num,
            "done": self._done,
            "best_score": self._best_score,
            "current_code": self._current_code,
            "current_error": self._current_error,
        }
