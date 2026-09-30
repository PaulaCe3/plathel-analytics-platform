"""Composition root: product routers share the existing secured runtime."""
from bi.api.main import create_app as create_bi_app
from forecast.api import router

def create_app(settings=None):
    app = create_bi_app(settings)
    app.include_router(router, prefix=app.state.settings.api_prefix)
    app.title = "PLATHEL"
    return app

app = create_app()
