import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


from .routers import agents, incidents, handovers
from .db import create_db_and_tables
from .exceptions import EntityNotFoundError, StateTransitionError

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

# Startup Configuration
@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield

# FastAPI Application Instance
app = FastAPI(title="IT-Support Incident Management API",
              description="Enterprise shift handover and escalation management.",
              version="1.0.0",
              lifespan= lifespan)

# Global Exception Handlers
@app.exception_handler(EntityNotFoundError)
async def entity_not_found_handler(request: Request, exc: EntityNotFoundError):
    logging.warning(f"404 Not Found - {request.method} {request.url} - {str(exc)}")
    return JSONResponse(status_code=404, content={"detail": str(exc)})

@app.exception_handler(StateTransitionError)
async def state_transition_handler(request: Request, exc: StateTransitionError):
    logging.error(f"400 Bad Request - {request.method} {request.url} - {str(exc)}")
    return JSONResponse(status_code=400, content={"detail": str(exc)})

# Routing Assembly
app.include_router(agents.router)
app.include_router(incidents.router)
app.include_router(handovers.router)