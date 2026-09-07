from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ariadne.api.routes import analyze, cti, graph, health, query
from ariadne.config import settings


def create_app() -> FastAPI:
    app = FastAPI(title="Ariadne", version="0.1.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router)
    app.include_router(graph.router)
    app.include_router(cti.router)
    app.include_router(query.router)
    app.include_router(analyze.router)

    return app


app = create_app()
