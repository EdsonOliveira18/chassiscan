import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, File, HTTPException, UploadFile, status
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from . import __service__, __version__, ocr_engine

logger = logging.getLogger(__name__)

MAX_BYTES = 10 * 1024 * 1024  # 10 MB
CHUNK_SIZE = 1024 * 1024  # 1 MB
OCR_TIMEOUT_S = 60.0
MAX_CONCURRENT_OCR = 1  # EasyOCR Reader nao e thread-safe

ALLOWED_MIME = {"image/jpeg", "image/jpg", "image/png", "image/webp", "image/bmp"}
FILE_REQUIRED = File(..., description="Imagem contendo o chassi (VIN)")

# Assinaturas binarias (magic bytes) - validacao real, nao confia no header
MAGIC_SIGNATURES = (
    b"\xff\xd8\xff",  # JPEG
    b"\x89PNG\r\n\x1a\n",  # PNG
    b"BM",  # BMP
)

_ocr_semaphore = asyncio.Semaphore(MAX_CONCURRENT_OCR)


def _looks_like_image(data: bytes) -> bool:
    if any(data.startswith(sig) for sig in MAGIC_SIGNATURES):
        return True
    # WEBP: "RIFF" .... "WEBP"
    return data[:4] == b"RIFF" and data[8:12] == b"WEBP"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Aquece o EasyOCR no startup para a 1a requisicao nao pagar o load."""
    try:
        await run_in_threadpool(ocr_engine.get_reader)
        logger.info("EasyOCR pronto")
    except Exception:  # pragma: no cover
        logger.exception("Falha ao pre-carregar o EasyOCR; sera tentado sob demanda")
    yield


app = FastAPI(
    title="ChassiScan API",
    version=__version__,
    description="Extrai e valida números de chassi (VIN) a partir de imagens.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # restrinja em producao
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str


class OCRResponse(BaseModel):
    vin: str | None = Field(None, description="VIN detectado (17 caracteres)")
    valid: bool = Field(False, description="Estrutura ISO 3780 valida")
    checksum_ok: bool = Field(False, description="Digito verificador ISO 3779 confere")
    confidence: float = Field(0.0, description="Confianca media do OCR (0-1)")
    variant: str | None = None
    rotation: int | None = None
    candidates: list[str] = Field(default_factory=list)


async def _read_capped(file: UploadFile) -> bytes:
    """Le em chunks e aborta ao exceder MAX_BYTES, sem carregar tudo em RAM."""
    buffer = bytearray()
    while chunk := await file.read(CHUNK_SIZE):
        buffer.extend(chunk)
        if len(buffer) > MAX_BYTES:
            raise HTTPException(
                status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                f"Imagem maior que {MAX_BYTES // (1024 * 1024)}MB.",
            )
    return bytes(buffer)


@app.get("/health", tags=["infra"], response_model=HealthResponse)
def health() -> dict:
    """Liveness/readiness probe."""
    return {"status": "ok", "service": __service__, "version": __version__}


@app.post("/ocr/chassi", tags=["ocr"], response_model=OCRResponse)
async def ocr_chassi(file: UploadFile = FILE_REQUIRED) -> dict:
    """Recebe uma imagem e retorna o VIN detectado com validação ISO 3779."""
    if file.content_type and file.content_type.lower() not in ALLOWED_MIME:
        raise HTTPException(
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            f"Tipo de arquivo nao suportado: {file.content_type}",
        )

    try:
        data = await _read_capped(file)
    finally:
        await file.close()

    if not data:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Arquivo vazio.")
    if not _looks_like_image(data):
        raise HTTPException(
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            "Conteudo do arquivo nao corresponde a uma imagem suportada.",
        )

    try:
        # OCR e CPU-bound e bloqueante: sai do event loop e serializa o acesso
        async with _ocr_semaphore:
            result = await asyncio.wait_for(
                run_in_threadpool(ocr_engine.read_vin_from_bytes, data),
                timeout=OCR_TIMEOUT_S,
            )
    except TimeoutError as exc:
        logger.warning("OCR excedeu %ss", OCR_TIMEOUT_S)
        raise HTTPException(
            status.HTTP_504_GATEWAY_TIMEOUT, "Tempo limite excedido no processamento."
        ) from exc
    except ValueError as exc:
        raise HTTPException(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, str(exc)) from exc
    except Exception as exc:  # pragma: no cover
        logger.exception("Falha inesperada no OCR")
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR, "Erro interno ao processar a imagem."
        ) from exc

    return result.to_dict()
