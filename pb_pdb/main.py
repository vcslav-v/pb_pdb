from fastapi import FastAPI
from pb_pdb.api.routes import routes

app = FastAPI(debug=True)

app.include_router(routes)
