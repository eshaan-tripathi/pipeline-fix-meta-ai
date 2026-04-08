"""
inference.py — Baseline inference script for Pipeline Repair OpenEnv.
Reads API credentials from environment variables.
Emits structured [START] / [STEP] / [END] logs as required by the hackathon spec.

Usage:
    export API_BASE_URL=https://api.openai.com/v1
    export MODEL_NAME=gpt-4o
    export HF_TOKEN=your_hf_or_openai_key
    python inference.py
"""

import json
import os
import time
from typing import List

import requests
from openai import OpenAI

# ── Config ──────────────────────────────────────────────────────────────────
API_BASE_URL = os.environ.get("API_BASE_URL", "https://api.openai.com/v1")
MODEL_NAME = os.environ.get("MODEL_NAME", "gpt-4o")
API_KEY = os.environ.get("HF_TOKEN", "")

# The running HF Space URL — update after deployment
ENV_BASE_URL = os.environ.get("ENV_BASE_URL", "http://localhost:7860")

TASKS = ["task_easy", "task_medium", "task_hard"]
MAX_STEPS = {"task_easy": 5, "task_medium": 10, "task_hard": 15}
MAX_TOTAL_REWARD = {"task_easy": 5.0, "task_medium": 10.0, "task_hard": 15.0}
SUCCESS_SCORE_THRESHOLD = 0.8
TEMPERATURE = 0.2
MAX_TOKENS = 2048

SYSTEM_PROMPT = """\
You are an expert Python data engineer. You will be given a broken Python ETL/data pipeline script and sample data.
Your job is to return ONLY the corrected Python script — no explanation, no markdown, no backticks.
The script must:
  1. Run without errors.
  2. Write its final result to output.csv using df.to_csv('output.csv', index=False).
  3. Fix all bugs in the original code.
Output raw Python only.
"""

# ── Logging helpers (exact format required by hackathon) ─────────────────────
def log_start(task: str, env: str, model: str):
    print(json.dumps({"type": "START", "task": task, "env": env, "model": model}), flush=True)

def log_step(step: int, action: str, reward: float, done: bool, error):
    print(json.dumps({
        "type": "STEP",
        "step": step,
        "action": action[:200],  # truncate for log readability
        "reward": reward,
        "done": done,
        "error": error,
    }), flush=True)

def log_end(success: bool, steps: int, score: float, rewards: List[float]):
    print(json.dumps({
        "type": "END",
        "success": success,
        "steps": steps,
        "score": score,
        "rewards": rewards,
    }), flush=True)

# ── Environment client (HTTP) ────────────────────────────────────────────────
def env_reset(task_id: str) -> dict:
    r = requests.post(f"{ENV_BASE_URL}/reset", json={"task_id": task_id}, timeout=30)
    r.raise_for_status()
    return r.json()

def env_step(task_id: str, edited_code: str) -> dict:
    r = requests.post(f"{ENV_BASE_URL}/step", json={"task_id": task_id, "edited_code": edited_code}, timeout=60)
    r.raise_for_status()
    return r.json()

# ── Model call ───────────────────────────────────────────────────────────────
def get_model_code(client: OpenAI, obs: dict, history: List[str]) -> str:
    history_text = "\n".join(history[-4:]) if history else "No previous attempts."
    user_prompt = f"""\
Task: {obs['task_id']} | Step {obs['step_num']} / {obs['max_steps']}

=== BROKEN CODE ===
{obs['broken_code']}

=== LAST ERROR (empty = no crash) ===
{obs['error_trace'] or 'None'}

=== SAMPLE DATA (first rows) ===
{obs['sample_rows']}

=== RECENT HISTORY ===
{history_text}

Return ONLY the corrected Python script.
"""
    try:
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS,
            stream=False,
        )
        code = (completion.choices[0].message.content or "").strip()
        # Strip markdown fences if model adds them despite instructions
        if code.startswith("```"):
            lines = code.split("\n")
            code = "\n".join(lines[1:-1]) if lines[-1].strip() == "```" else "\n".join(lines[1:])
        return code if code else "print('error')"
    except Exception as exc:
        print(f"[DEBUG] Model call failed: {exc}", flush=True)
        return "print('error')"

# ── Run one task ─────────────────────────────────────────────────────────────
def run_task(client: OpenAI, task_id: str) -> float:
    log_start(task=task_id, env="pipeline-repair-env", model=MODEL_NAME)

    history: List[str] = []
    rewards: List[float] = []
    steps_taken = 0
    score = 0.0
    success = False

    try:
        result = env_reset(task_id)
        obs = result["observation"]

        for step in range(1, MAX_STEPS[task_id] + 1):
            if result.get("done", False):
                break

            code = get_model_code(client, obs, history)
            result = env_step(task_id, code)
            obs = result["observation"]
            reward = result.get("reward", 0.0)
            done = result.get("done", False)

            rewards.append(reward)
            steps_taken = step

            log_step(step=step, action=code, reward=reward, done=done, error=None)
            history.append(f"Step {step}: reward={reward:.3f} error={obs.get('error_trace','')[:80]}")

            if done:
                break

        max_r = MAX_TOTAL_REWARD[task_id]
        score = round(min(max(sum(rewards) / max_r, 0.0), 1.0), 4)
        success = score >= SUCCESS_SCORE_THRESHOLD

    except Exception as e:
        print(f"[DEBUG] Task {task_id} failed: {e}", flush=True)
    finally:
        log_end(success=success, steps=steps_taken, score=score, rewards=rewards)

    return score

# ── Main ─────────────────────────────────────────────────────────────────────
def main():
    client = OpenAI(base_url=API_BASE_URL, api_key=API_KEY)
    all_scores = {}

    for task_id in TASKS:
        print(f"\n{'='*60}", flush=True)
        print(f"Running task: {task_id}", flush=True)
        print(f"{'='*60}", flush=True)
        score = run_task(client, task_id)
        all_scores[task_id] = score
        print(f"[RESULT] {task_id}: {score:.4f}", flush=True)
        time.sleep(2)

    print("\n[FINAL SCORES]", flush=True)
    for tid, sc in all_scores.items():
        print(f"  {tid}: {sc:.4f}", flush=True)
    avg = sum(all_scores.values()) / len(all_scores)
    print(f"  average: {avg:.4f}", flush=True)

if __name__ == "__main__":
    main()