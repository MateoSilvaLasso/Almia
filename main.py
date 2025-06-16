from fastapi import FastAPI, UploadFile, File
import shutil
from agent import PerfilAnalyzer
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional



app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class PerfilRequest(BaseModel):
    linkedin: str
    name: str

@app.post("/analizar-perfil/")
async def analizar_perfil(request: PerfilRequest):
    print("llego")
    analizador = PerfilAnalyzer(linkedin_url=request.linkedin, name=request.name)
    resultado = await analizador.analizar()
    return resultado
