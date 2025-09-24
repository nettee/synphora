import uvicorn


def dev():
    """Starts the development server."""
    uvicorn.run(
        "synphora.server:app",
        reload=True,
        host="0.0.0.0",
        port=8000,
    )


def server():
    """Starts the server."""
    uvicorn.run("synphora.server:app", reload=True)
