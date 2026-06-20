"""FastAPI 应用入口。

启动：
    cd backend && uvicorn main:app --reload --port 8000

路由树：
    main -> api.router (prefix=/api)
                 -> /api/health
                 -> /api/sample
                 -> /api/schedule
                 -> /api/simulate
            -> engine (scheduler / simulator / risk / geometry / models)
"""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import router

app = FastAPI(
    title="外卖骑手动态调度模拟引擎",
    description="基于 NumPy/Pandas 的离散调度与轨迹模拟服务",
    version="1.0.0",
)

# 允许前端开发服务器跨域访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"service": "rider-dispatch-sim", "docs": "/docs"}


app.include_router(router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
