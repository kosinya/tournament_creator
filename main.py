import uvicorn
from fastapi import FastAPI
from  fastapi.middleware.cors import CORSMiddleware
from database import Base, engine
from routers import tournament, player, department, league, match, group, playoff


app = FastAPI()

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(tournament.router, prefix='/tournaments')
app.include_router(player.router, prefix='/players')
app.include_router(league.router, prefix='/leagues')
app.include_router(department.router, prefix='/departments')
app.include_router(match.router, prefix='/matches')
app.include_router(playoff.router, prefix='/playoff')
app.include_router(group.router, prefix='/groups')
Base.metadata.create_all(bind=engine)


if __name__ == "__main__":
    uvicorn.run('main:app', host='127.0.0.1', port=8000, reload=True, workers=4)

