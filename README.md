# Biodiversity AI Scientist

[![Release](https://img.shields.io/badge/release-v0.1.0--alpha-blue.svg)](https://github.com/Biodiversity-AI-Scientist/biodiversity-ai-scientist)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Status: Alpha](https://img.shields.io/badge/Status-Early%20Alpha-orange.svg)]()

The **Biodiversity AI Scientist (BAIS)** is an open-source scientific software platform designed to assist and accelerate biodiversity research through structured scientific reasoning, automated literature and taxonomy grounding, modular capability orchestration, and reproducible experiment execution.

> **Project Status**: Early Alpha (`v0.1.0-alpha`). Core architectures, scientific data models, and provider boundaries are established and under active development. Installation and operational documentation will evolve as interfaces stabilize.

---

## 🔬 Core Architecture & Scientific Capabilities

BAIS organizes scientific inquiry into a disciplined, auditable, multi-stage lifecycle:

```mermaid
flowchart LR
    RQ["1. Research Questions & Hypotheses"] --> IP["2. Investigation Planning"]
    IP --> SC["3. Scientific Capability Selection"]
    SC --> EXP["4. Experiment Planning & Runs"]
    EXP --> EV["5. Evidence & Provenance Governance"]
```

### 1. Research Questions & Structured Hypotheses
Formalizes taxonomic, morphological, phylogenetic, and biogeographic inquiries with structured variables, assumptions, background knowledge grounding, and explicit falsification criteria.

### 2. Multi-Stage Investigation Planning
Decomposes complex biodiversity studies into directional investigation DAGs, tracking dependencies, preconditions, execution checkpoints, and intermediate artifact contracts.

### 3. Scientific Capabilities & Implementations (B01 Model)
Enforces a clean separation between generic scientific methods and their concrete computational execution:
- **`ScientificCapability`**: Represents the abstract biological/computational method (e.g. `extract_image_embeddings`, `infer_phylogeny`, `calculate_extent_of_occurrence`).
- **`CapabilityImplementation`**: Represents the specific software runtime, container, or adapter executing the capability (e.g. BioCLIP, IQ-TREE, custom vision models).
- **Taxonomy Governance**: 4-tier scope classification (`generic_core`, `official_extension`, `external_tool`, `deployment_specific`).

### 4. Reproducible Experiment & Run Execution
Experiments are versioned specifications paired with immutable runtime records (`ExperimentRun` / `AnalysisRun`), capturing full configuration parameters, resource metrics, logs, and cryptographic output hashes.

### 5. Evidence & Provenance Governance
All produced dataset versions, embeddings, classification matrices, and scientific tables are recorded in an auditable artifact store with SHA-256 integrity verification.

---

## 🧩 Modular System Boundaries & Extensibility

BAIS core provides standard abstract contracts and local default providers:
- **`ExecutionBackend`**: Local process execution, job scheduling, container workers, and remote dispatch.
- **`ArtifactStore`**: Content-addressable storage, checksum verification, and URI resolution.
- **`DatasetStore`**: Specimen manifest resolution and versioning.
- **`CapabilityAdapter`**: Generic interface connecting scientific algorithms to modular execution engines.

### Deployment Separation
The generic BAIS core contains **zero hardcoded dependencies on private infrastructure**. 
External hardware accelerators, institutional storage clusters, or private laboratory adapters register dynamically with the generic `ProviderRegistry` from the deployment side.

---

## 🚀 Installation & Quick Start

### 1. Clone the Repository
```bash
git clone https://github.com/Biodiversity-AI-Scientist/biodiversity-ai-scientist.git
cd biodiversity-ai-scientist
```

### 2. Run Preflight Check (Optional)
```bash
python3 install/preflight.py --port 8000
```

### 3. Run Canonical Public Installer
```bash
python3 install/install.py --port 8000
```
*The installer automatically validates prerequisites, provisions an isolated virtual environment (`.venv`), installs required dependencies, generates initial runtime configuration, and initializes the database schema.*

### 4. Start the Application
```bash
source .venv/bin/activate
uvicorn src.main:app --host 0.0.0.0 --port 8000
```

### 5. Verify Health & Core Registry
```bash
curl http://127.0.0.1:8000/health
# Response: {"status": "ok"}
```

### Running Tests
```bash
pytest
```

---

## 📖 Citation

If you use or reference the Biodiversity AI Scientist platform in academic work, please cite it using the metadata in [CITATION.cff](CITATION.cff).

---

## 📜 License

This project is licensed under the Apache License 2.0. See [LICENSE](LICENSE) for the full license text.
