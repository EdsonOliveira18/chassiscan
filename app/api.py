from fastapi import FastAPI, File, HTTPException, UploadFile

from . import __service__, __version__, ocr_engine

app = FastAPI(title="ChassiScan API", version=__version__)

MAX_BYTES = 10 * 1024 * 1024
FILE_REQUIRED = File(...)


@app.get("/health")
def health():
    return {"status": "ok", "service": __service__, "version": __version__}


@app.post("/ocr/chassi")
async def ocr_chassi(file: UploadFile = FILE_REQUIRED):
    data = await file.read()
    if not data:
        raise HTTPException(400, "Arquivo vazio.")
    if len(data) > MAX_BYTES:
        raise HTTPException(413, "Imagem maior que 10MB.")
    try:
        result = ocr_engine.read_vin_from_bytes(data)
    except ValueError as exc:
        raise HTTPException(415, str(exc)) from exc
    return result.to_dict()
