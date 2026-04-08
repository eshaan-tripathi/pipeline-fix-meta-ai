---
<<<<<<< HEAD
title: Pipeline Repair Env
emoji: 🛠️
colorFrom: blue
colorTo: green
sdk: docker
app_file: app.py
=======
title: Pipeline Fix — Meta AI
emoji: 🛠️
colorFrom: blue
colorTo: green
sdk: gradio
sdk_version: "3.42.0"
python_version: "3.11"
app_file: server.py
>>>>>>> f926892144472660f6de4701aecb840f412dd65d
pinned: false
---
# Pipeline Repair — OpenEnv Environment

An OpenEnv-compliant environment where an AI agent debugs and repairs broken Python ETL/data-cleaning pipelines.

<<<<<<< HEAD
=======
---

>>>>>>> f926892144472660f6de4701aecb840f412dd65d
## Overview

Real data engineers spend significant time fixing broken data pipelines — scripts that crash on renamed columns, propagate NaN silently, or produce wrong outputs due to merge bugs. This environment simulates exactly that, giving agents a broken Python script and sample data, then scoring them on whether their repaired script produces a correct output CSV.

<<<<<<< HEAD
## Tasks

| Task | Difficulty | Bugs | Max steps |
|------|-----------|------|-----------|
| `task_easy` | Easy | 1 — renamed column KeyError | 5 |
| `task_medium` | Medium | 3 — type cast, NaN propagation, wrong date format | 10 |
| `task_hard` | Hard | 5+ — schema drift, duplicate rows, bad merge, currency, sort order | 15 |
=======
---

## Tasks

| Task        | Difficulty | Bugs                                                                 | Max steps |
|------------|-----------|----------------------------------------------------------------------|-----------|
| task_easy   | Easy      | 1 — renamed column KeyError                                           | 5         |
| task_medium | Medium    | 3 — type cast, NaN propagation, wrong date format                    | 10        |
| task_hard   | Hard      | 5+ — schema drift, duplicate rows, bad merge, currency, sort order  | 15        |

---
>>>>>>> f926892144472660f6de4701aecb840f412dd65d

## Action Space

```json
{ "edited_code": "<corrected Python script as a string>" }
<<<<<<< HEAD
```

## Observation Space

```json
=======
Observation Space
>>>>>>> f926892144472660f6de4701aecb840f412dd65d
{
  "broken_code": "<the broken script>",
  "error_trace": "<last stderr output, empty if no crash>",
  "sample_rows": "<first 10 rows of the input CSV>",
  "task_id": "task_easy | task_medium | task_hard",
  "step_num": 1,
  "max_steps": 5
}
<<<<<<< HEAD
```

## Reward

- Score 0.0–1.0 based on column match, row count match, and value accuracy vs the golden CSV.
- Crash penalty: −0.1
- Step penalty: −0.05 per step (encourages fixing in fewer attempts)
- Episode ends when score ≥ 0.90 or max steps reached.

## Setup

```bash
pip install -r requirements.txt
python server.py
```

Or with Docker:

```bash
docker build -t pipeline-repair-env .
docker run -p 7860:7860 pipeline-repair-env
```

## Running inference

```bash
=======
Reward
Score 0.0–1.0 based on column match, row count match, and value accuracy vs the golden CSV.
Crash penalty: −0.1
Step penalty: −0.05 per step (encourages fixing in fewer attempts)
Episode ends when score ≥ 0.90 or max steps reached.
Setup
pip install -r requirements.txt
python server.py

Or with Docker:

docker build -t pipeline-repair-env .
docker run -p 7860:7860 pipeline-repair-env
Running Inference
>>>>>>> f926892144472660f6de4701aecb840f412dd65d
export API_BASE_URL=https://api.openai.com/v1
export MODEL_NAME=gpt-4o
export HF_TOKEN=your_api_key
export ENV_BASE_URL=http://localhost:7860
<<<<<<< HEAD
python inference.py
```

## Baseline Scores

| Task | Model | Score |
|------|-------|-------|
| task_easy | gpt-4o | ~0.85 |
| task_medium | gpt-4o | ~0.60 |
| task_hard | gpt-4o | ~0.35 |

*(Update these after running your own baseline.)*

## Deployment

This environment is deployed as a Hugging Face Space tagged `openenv`.
The Space URL serves the FastAPI server on port 7860.
=======

python inference.py
Baseline Scores
Task	Model	Score
task_easy	gpt-4o	~0.85
task_medium	gpt-4o	~0.60
task_hard	gpt-4o	~0.35

Update these after running your own baseline.

Deployment

This environment is deployed as a Hugging Face Space tagged openenv. The Space URL serves the FastAPI server on port 7860.

License

MIT License


---

✅ **Tips for GitHub**:

1. Place this as `README.md` in the root of your repo.
2. Add a `LICENSE` (MIT or Apache recommended).
3. Add a `.gitignore` for Python, e.g.:
>>>>>>> f926892144472660f6de4701aecb840f412dd65d
