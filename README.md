# Branching Stories

**Branching Stories** is a Python project for building and experimenting with *branching narratives* (choose-your-own-adventure style).

---

## What’s in this repo

This repository centers around a main Python app plus a few “prototype snapshots” that capture earlier approaches while iterating on branching logic (including multiple branches and merging branches). :contentReference[oaicite:2]{index=2}

- `app.py` — current main application entrypoint :contentReference[oaicite:3]{index=3}  
- `app_backup1_(one_shot).py` — earlier “one shot” prototype :contentReference[oaicite:4]{index=4}  
- `app_backup2_(add_multiple_branches).py` — prototype focused on adding multiple branches :contentReference[oaicite:5]{index=5}  
- `app_backup3_(merging branches).py` — prototype focused on merging branches :contentReference[oaicite:6]{index=6}  
- `requirements.txt` — Python dependencies :contentReference[oaicite:7]{index=7}  
- `.devcontainer/` — dev container setup for a consistent dev environment :contentReference[oaicite:8]{index=8}  

---

## Quick start (local)

### 1) Clone
```bash
git clone https://github.com/Leoendithas/branchingstories.git
cd branchingstories
````

### 2) Create & activate a virtual environment

```bash
python -m venv .venv
# macOS / Linux
source .venv/bin/activate
# Windows (PowerShell)
.venv\Scripts\Activate.ps1
```

### 3) Install dependencies

```bash
pip install -r requirements.txt
```

### 4) Run the app

```bash
python app.py
```

If `app.py` supports CLI flags, configuration files, or environment variables, document them here once finalized.

---

## Using the prototypes

The backup apps are kept as reference points for different approaches to story branching:

* **One-shot flow:** `app_backup1_(one_shot).py`
* **Multiple branches:** `app_backup2_(add_multiple_branches).py`
* **Merging branches:** `app_backup3_(merging branches).py`

Run any prototype the same way:

```bash
python "app_backup2_(add_multiple_branches).py"
```

---

## Development (Dev Container)

If you use VS Code, this repo includes a `.devcontainer/` directory so you can open the project in a preconfigured container environment:

1. Install **Docker** + **VS Code** + the **Dev Containers** extension
2. Open the repo folder in VS Code
3. Choose **“Reopen in Container”**

This helps keep Python/tooling consistent across machines. ([GitHub][1])

---

## Roadmap ideas (optional)

If you want a clearer direction for the project, consider tracking items like:

* Story graph data model (nodes, choices, outcomes)
* Import/export formats (JSON/YAML/Markdown)
* Validation (dead ends, unreachable nodes, loops)
* Visualizer (graph view) and/or editor UI
* Test suite for branching & merge logic

---

## Contributing

Contributions are welcome—especially around:

* clearer story format + examples
* refactoring prototypes into reusable modules
* tests and documentation

Suggested workflow:

1. Fork the repo
2. Create a feature branch
3. Open a PR with a short description + screenshots/logs if relevant

---

## License

Licensed under the **Apache License 2.0**. See the `LICENSE` file for details.


