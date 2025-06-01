# main.py

from fastapi import FastAPI
from app.routes import router

app = FastAPI(title="Pluss-Botss API")

# Inclui as rotas da aplicação
app.include_router(router)

if __name__ == "__main__":
    import uvicorn

    host = "0.0.0.0"
    port = 8000
    print(f"🚀 Servidor rodando em: http://localhost:{port}/docs")
    uvicorn.run("main:app", host=host, port=port, reload=True)
