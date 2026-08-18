from fastapi import FastAPI, HTTPException
from sqlalchemy import text

from src.database import engine, dwh_engine, datalake_engine
from src.config import settings
from src.routers.research_project import router as research_project_router
from src.routers.research_question import router as research_question_router
from src.routers.hypothesis import router as hypothesis_router
from src.routers.prediction import router as prediction_router
from src.routers.dataset_version import router as dataset_version_router
from src.routers.analysis_plan import router as analysis_plan_router
from src.routers.analysis_run import router as analysis_run_router
from src.routers.experiment import router as experiment_router
from src.routers.experiment_run import router as experiment_run_router
from src.routers.brainstorming_session import router as brainstorming_session_router
from src.routers.research_plan import router as research_plan_router
from src.routers.data_intelligence import router as data_intelligence_router
from src.routers.research_agenda import router as research_agenda_router
from src.routers.domain_intelligence import router as domain_intelligence_router
from src.routers.orchestrator import router as orchestrator_router
from src.routers.llm_gateway import router as llm_gateway_router
from src.routers.scientific_capability import router as scientific_capability_router
from src.routers.scientific_context import router as scientific_context_router
from src.routers.investigation_step import router as investigation_step_router
from src.routers.demo_seeder import router as demo_seeder_router
from src.routers.config_manager import router as config_manager_router
from src.routers.project_export import router as project_export_router

from src.routers.llm_gateway import gateway_status_payload





app = FastAPI(
    title="Biodiversity AI Scientist",
    version="0.1.0",
)


app.include_router(
    research_project_router,
)

app.include_router(
    research_question_router,
)

app.include_router(
    hypothesis_router,
)

app.include_router(
    prediction_router,
)

app.include_router(
    dataset_version_router,
)

app.include_router(
    experiment_router,
)

app.include_router(
    experiment_run_router,
)

app.include_router(
    analysis_plan_router,
)

app.include_router(
    analysis_run_router,
)

app.include_router(
    brainstorming_session_router,
)

app.include_router(
    research_plan_router,
)

app.include_router(
    data_intelligence_router,
)

app.include_router(
    research_agenda_router,
)

app.include_router(
    domain_intelligence_router,
)

app.include_router(
    orchestrator_router,
)

app.include_router(llm_gateway_router)
app.include_router(scientific_capability_router)
app.include_router(scientific_context_router)
app.include_router(investigation_step_router)
app.include_router(demo_seeder_router)
app.include_router(config_manager_router)
app.include_router(project_export_router)








@app.get("/")
def root():
    return {
        "service": "Biodiversity AI Scientist",
        "status": "running",
    }


@app.get("/health")
def health():
    return {
        "status": "ok",
    }

@app.get("/health/llm-gateway")
def llm_gateway_health():
    return gateway_status_payload()


@app.get("/health/database")
def database_health():
    try:
        with engine.connect() as connection:
            version = connection.execute(
                text("SELECT VERSION()")
            ).scalar_one()

            database = connection.execute(
                text("SELECT DATABASE()")
            ).scalar_one()

        return {
            "status": "ok",
            "database": database,
            "mysql_version": version,
        }

    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail=f"Database connection failed: {exc}",
        )


@app.get("/health/dwh")
def dwh_health():
    try:
        with dwh_engine.connect() as connection:
            database = connection.execute(
                text("SELECT DATABASE()")
            ).scalar_one()
            version = connection.execute(
                text("SELECT VERSION()")
            ).scalar_one()

        return {
            "status": "ok",
            "database": database,
            "server": settings.dwh_db_host,
            "mysql_version": version,
        }
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail=f"DWH database connection failed: {exc}",
        )
