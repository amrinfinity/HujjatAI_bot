from datetime import datetime
from pathlib import Path

import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from act_pdf import create_act_pdf, safe_filename as act_safe_filename
from config import Config
from individual_legal_pdf import create_individual_legal_pdf, safe_filename as jy_safe_filename
from legal_legal_pdf import create_legal_legal_pdf, safe_filename as yy_safe_filename
from mobile_app_pdf import create_mobile_app_pdf, safe_filename
from rental_pdf import create_rental_pdf, safe_filename as rental_safe_filename
from schemas import (
    ActData,
    IndividualLegalContractData,
    LegalLegalContractData,
    MobileAppContractData,
    RentalContractData,
)

BASE_DIR = Path(__file__).resolve().parent.parent
DOCUMENTS_DIR = BASE_DIR / "documents"
DOCUMENTS_DIR.mkdir(exist_ok=True)

app = FastAPI(title="Hujjat AI", version="2.6.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=Config.cors_origins(),
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _unique_filepath(filename: str) -> tuple[str, Path]:
    filepath = DOCUMENTS_DIR / filename
    if filepath.exists():
        stem = filepath.stem
        filename = f"{stem}_{datetime.now().strftime('%H%M%S')}.pdf"
        filepath = DOCUMENTS_DIR / filename
    return filename, filepath


def _download_url(request: Request, filename: str) -> str:
    base = str(request.base_url).rstrip("/")
    return f"{base}/download/{filename}"


def _success_response(request: Request, filename: str) -> dict:
    return {
        "success": True,
        "filename": filename,
        "download_url": _download_url(request, filename),
    }


@app.get("/")
def root():
    return {"message": "Hujjat AI Backend ishlayapti!"}


@app.post("/generate-mobile-app")
def generate_mobile_app_contract(data: MobileAppContractData, request: Request):
    filename, filepath = _unique_filepath(safe_filename(data.project_name, data.contract_date))
    try:
        create_mobile_app_pdf(data, filepath)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"PDF yaratishda xatolik: {exc}") from exc
    return _success_response(request, filename)


@app.post("/generate-individual-legal")
def generate_individual_legal_contract(data: IndividualLegalContractData, request: Request):
    filename, filepath = _unique_filepath(jy_safe_filename(data.legal_entity.org_name, data.contract_date))
    try:
        create_individual_legal_pdf(data, filepath)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"PDF yaratishda xatolik: {exc}") from exc
    return _success_response(request, filename)


@app.post("/generate-legal-legal")
def generate_legal_legal_contract(data: LegalLegalContractData, request: Request):
    filename, filepath = _unique_filepath(
        yy_safe_filename(data.party_first.org_name, data.party_second.org_name, data.contract_date)
    )
    try:
        create_legal_legal_pdf(data, filepath)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"PDF yaratishda xatolik: {exc}") from exc
    return _success_response(request, filename)


@app.post("/generate-rental")
def generate_rental_contract(data: RentalContractData, request: Request):
    filename, filepath = _unique_filepath(rental_safe_filename(data.tenant.full_name, data.contract_date))
    try:
        create_rental_pdf(data, filepath)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"PDF yaratishda xatolik: {exc}") from exc
    return _success_response(request, filename)


@app.post("/generate-act")
def generate_act(data: ActData, request: Request):
    filename, filepath = _unique_filepath(act_safe_filename(data.customer_name, data.date))
    try:
        create_act_pdf(data, filepath)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"PDF yaratishda xatolik: {exc}") from exc
    return _success_response(request, filename)


@app.get("/download/{filename}")
def download_pdf(filename: str):
    if ".." in filename or "/" in filename or "\\" in filename:
        raise HTTPException(status_code=400, detail="Noto'g'ri fayl nomi")
    filepath = DOCUMENTS_DIR / filename
    if not filepath.exists():
        raise HTTPException(status_code=404, detail="Fayl topilmadi")
    return FileResponse(path=filepath, media_type="application/pdf", filename=filename)


if __name__ == "__main__":
    uvicorn.run("main:app", host=Config.HOST, port=Config.PORT, reload=True)
