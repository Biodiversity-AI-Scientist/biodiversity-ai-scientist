# Biodiversity AI Scientist (BAIS)

[![Release](https://img.shields.io/badge/release-v0.1.0--alpha-blue.svg)](https://github.com/Biodiversity-AI-Scientist/biodiversity-ai-scientist)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Python: >=3.10](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12-brightgreen.svg)]()
[![Status: Alpha](https://img.shields.io/badge/Status-Early%20Alpha-orange.svg)]()

The **Biodiversity AI Scientist (BAIS)** is an open-source scientific software platform designed to assist and accelerate biodiversity research through structured scientific reasoning, automated literature and taxonomy grounding, modular capability orchestration, and reproducible experiment execution.

---

## 🔬 Core Architecture & Scientific Lifecycle

BAIS organizes scientific inquiry into an auditable, multi-stage lifecycle:

```mermaid
flowchart LR
    RQ["1. Research Questions & Hypotheses"] --> IP["2. Investigation Planning"]
    IP --> SC["3. Scientific Capability Selection"]
    SC --> EXP["4. Experiment Planning & Runs"]
    EXP --> EV["5. Evidence & Provenance Governance"]
```

1. **Research Questions & Structured Hypotheses**: Formalizes taxonomic, morphological, phylogenetic, and biogeographic inquiries with structured variables, background grounding, and falsification criteria.
2. **Multi-Stage Investigation Planning**: Decomposes complex studies into directional investigation DAGs, tracking dependencies, preconditions, execution checkpoints, and intermediate artifact contracts.
3. **Scientific Capabilities & Implementations (B01 Model)**: Enforces clean separation between abstract biological methods and runtime execution engines (`BioCLIP`, `IQ-TREE`, `MaxEnt`, custom models).
4. **Reproducible Experiment Execution**: Versioned experiment specifications paired with immutable runtime records (`AnalysisRun` / `ExperimentRun`) capturing parameters, metrics, logs, and cryptographic output hashes.
5. **Evidence & Provenance Governance**: Auditable artifact store with SHA-256 integrity verification.

---

## ⚡ Quick Start (One-Command Launcher)

If you have Python 3.10+ installed, you can clone and launch BAIS with a single command:

```bash
git clone https://github.com/Biodiversity-AI-Scientist/biodiversity-ai-scientist.git
cd biodiversity-ai-scientist
./run.sh
```

*(On Windows or platforms without bash, run `python3 run.py`)*

The launcher will automatically detect whether the virtual environment is provisioned, run the installer if needed, bind the server port, and open:
- **Web Interface**: `http://localhost:8000/ai-scientist/`
- **Release Manager**: `http://localhost:8000/bais_prm/`
- **Interactive API Docs**: `http://localhost:8000/docs`

---

## 🛠️ Step-by-Step Installation

### Prerequisites
- **Operating System**: Linux, macOS, or Windows (WSL recommended)
- **Python**: Version `3.10`, `3.11`, or `3.12`
- **Git**: Installed and available in PATH
- **Disk Space**: At least 500 MB free space

---

### Step 1: Clone the Repository
```bash
git clone https://github.com/Biodiversity-AI-Scientist/biodiversity-ai-scientist.git
cd biodiversity-ai-scientist
```

---

### Step 2: Validate Prerequisites (Preflight)
Run the built-in preflight validator to verify host compatibility and port availability:
```bash
python3 install/preflight.py --port 8000
```
*Outputs structured check results for OS, Python version, `venv` module, disk space, and port availability.*

---

### Step 3: Run the Canonical Public Installer
```bash
python3 install/install.py --port 8000
```

The installer performs the following automated steps:
1. Validates host preflight checks.
2. Provisions a self-contained Python virtual environment at `.venv/`.
3. Installs all required core dependencies from `requirements.txt`.
4. Creates a local `.env` runtime configuration.
5. Initializes the isolated SQLite database schema at `data/bais_database.db`.
6. Executes a FastAPI smoke test to verify application loading.

> **Using External MySQL instead of SQLite?**  
> Pass your database connection string directly:
> ```bash
> python3 install/install.py --db-url "mysql+pymysql://your_username:your_password_here@localhost:3306/bais_db"
> ```

---

### Step 4: Start the Application Daemon
```bash
source .venv/bin/activate
uvicorn src.main:app --host 0.0.0.0 --port 8000
```
Or simply use:
```bash
./run.sh
```

---

### Step 5: Verify Live System Health
```bash
curl http://127.0.0.1:8000/health
# Expected output: {"status": "ok"}
```

You can also run the comprehensive **BAIS Doctor** diagnostic tool:
```bash
python3 install/doctor.py
```
*Diagnoses Python environment, database table schema, active records, LLM connectivity, and disk storage.*

---

## 🔑 LLM Gateway Configuration

The public release ships with zero private credentials. You can explore projects, register scientific capabilities, and review datasets without an LLM key.

To enable **automated AI brainstorming, hypothesis generation, and investigation planning**:

### Option A: Via the Web Interface (Recommended)
1. Open the web interface at `http://localhost:8000/ai-scientist/configuration.php`.
2. Select your provider preset:
   - **OpenAI**: `gpt-4o`, `gpt-4o-mini`
   - **DeepSeek**: `deepseek-chat`, `deepseek-reasoner`
   - **Local Ollama (Offline / Free)**: `llama3.1`, `qwen2.5`, `mistral` (Runs 100% locally with zero token cost!)
3. Enter your API key (if required) and click **"Save & Test Connection"**.

### Option B: Via `.env` Configuration File
Edit `.env` in the repository root:
```ini
# OpenAI Configuration
LLM_GATEWAY_ENABLED=true
LLM_PROVIDER=openai_responses
LLM_BASE_URL=https://api.openai.com/v1
LLM_API_KEY=sk-your-api-key-here
LLM_DEFAULT_MODEL=gpt-4o
LLM_ALLOWED_MODELS=gpt-4o,gpt-4o-mini

# Or Local Ollama Configuration (100% Offline & Free)
# LLM_GATEWAY_ENABLED=true
# LLM_PROVIDER=ollama
# LLM_BASE_URL=http://localhost:11434/v1
# LLM_DEFAULT_MODEL=llama3.1
# LLM_ALLOWED_MODELS=llama3.1,qwen2.5,mistral
```

---

## 🌟 First-Time Usage & Demo Project

1. **Load Example Biodiversity Study**:
   - When you first open the **[Projects](http://localhost:8000/ai-scientist/projects.php)** page, click **"Load Example Biodiversity Project"**.
   - This automatically provisions a complete demonstration study (*"Alpine Flora Phenological Shifts & Elevational Climate Grounding"*) with research questions, formal hypotheses, DAG investigation steps, and registered capabilities.
2. **Export Academic Reproducibility Bundles**:
   - Inside any research project overview, click **"Export Project (JSON)"** to download an immutable, self-contained JSON archive of the study's questions, hypotheses, investigation steps, and analysis logs.

---

## 🧪 Running Automated Tests

Run the full core test suite using pytest:
```bash
source .venv/bin/activate
pytest
```

---

## 📖 Citation

If you use or reference the Biodiversity AI Scientist platform in academic research or software publications, please cite it using the metadata in [CITATION.cff](CITATION.cff).

---

## 📜 License

This project is licensed under the Apache License 2.0. See [LICENSE](LICENSE) for the full license text.
