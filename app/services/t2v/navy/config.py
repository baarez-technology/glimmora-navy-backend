"""
Configuration for Navy T2V Pipeline
Source: LM2500 Gas Turbine Course (Military Sealift Command)
"""
from pathlib import Path

# ── Paths ─────────────────────────────────────────────────────
BASE_DIR    = Path(__file__).parent
PROJECT_ROOT = BASE_DIR.parent.parent.parent  # app/services/t2v -> app/services -> app -> root
T2V_DATA_ROOT = BASE_DIR.parent / "data"
PDF_PATH    = T2V_DATA_ROOT / "pdfs" / "MSC01A_1211_B5_LM2500-Gas-Turbine_-r5b_rg.pdf"
IMAGES_DIR  = BASE_DIR / "data" / "ref_images"
CHROMA_DIR  = BASE_DIR / "data" / "chroma_db"
OUTPUT_DIR  = BASE_DIR / "data" / "output"

# ── ChromaDB Collections ──────────────────────────────────────
TEXT_COLLECTION  = "lm2500_text"
IMAGE_COLLECTION = "lm2500_images"

# ── Chunking ──────────────────────────────────────────────────
CHUNK_SIZE    = 1500
CHUNK_OVERLAP = 150

# ── Models ────────────────────────────────────────────────────
# Embeddings use Google Gemini (must match the model used to index ChromaDB).
EMBEDDING_MODEL = "gemini-embedding-001"

# LLM models — use the globally configured model for the active provider.
# Agents that need "strong" vs "fast" reasoning both get the same model;
# the distinction is kept for future per-task tuning.
from app.config import settings as _settings
_LLM_DEFAULT = _settings.LLM_MODEL
LLM_FAST   = _LLM_DEFAULT
LLM_STRONG = _LLM_DEFAULT

# ── Domain ────────────────────────────────────────────────────
DOMAIN       = "navy"
PLATFORM     = "LM2500 Gas Turbine"
SOURCE_DOC   = "MSC LM2500 Combustion Turbine Course, Military Sealift Command"

# ── LM2500 Chapter Map ────────────────────────────────────────
SECTION_MAP = {
    1:  "Overview",
    2:  "Inlet Air System",
    3:  "Accessory Drive",
    4:  "Compressor Section",
    5:  "Fuel Gas System",
    6:  "Turbine Section",
    7:  "Lube Oil System",
    8:  "Hydraulic Oil Systems",
    9:  "Hydraulic Start System",
    10: "Firing",
    11: "Turbine Troubleshooting",
    12: "Combustion Turbine Maintenance",
}

# ── LM2500 Domain Keywords ────────────────────────────────────
KEYWORD_PATTERNS = [
    # Compressor
    r'\bcompressor\b', r'\bstator\b', r'\brotor\b', r'\bblade\b',
    r'\bvane\b', r'\bIGV\b', r'\bvariable geometry\b', r'\bstage\b',
    r'\baxial flow\b', r'\bcompressor stall\b', r'\bsurge\b',
    # Combustion
    r'\bcombust\b', r'\bcombustor\b', r'\bannular\b', r'\bliner\b',
    r'\bfuel nozzle\b', r'\bigniter\b', r'\bflame\b', r'\bdome\b',
    r'\bskirt\b', r'\bcowl\b', r'\bSAC\b', r'\bDLE\b',
    # Turbine
    r'\bturbine\b', r'\bhigh.pressure\b', r'\blow.pressure\b',
    r'\bpower turbine\b', r'\bHP\b', r'\bLP\b', r'\bnozzle\b',
    r'\bmidframe\b', r'\bexhaust\b', r'\bdiffuser\b',
    # Fuel System
    r'\bfuel\b', r'\bfuel gas\b', r'\bgas control valve\b',
    r'\bflow divider\b', r'\bpilot valve\b', r'\bmanifold\b',
    # Lube Oil
    r'\blube oil\b', r'\boil pump\b', r'\bscavenge\b', r'\bsump\b',
    r'\bfilter\b', r'\bcooler\b', r'\bbearing\b', r'\bseal\b',
    # Hydraulic
    r'\bhydraulic\b', r'\bcontrol oil\b', r'\bservo\b',
    r'\bwater injection\b', r'\bflow control\b',
    # Start System
    r'\bstart\b', r'\bstarter\b', r'\bhydraulic start\b',
    r'\btorque converter\b', r'\bSSS clutch\b',
    # Inlet
    r'\binlet\b', r'\bfilter house\b', r'\bbellmouth\b', r'\bbullet nose\b',
    r'\btrash screen\b', r'\bevaporative\b',
    # Accessory Drive
    r'\baccessory\b', r'\bgearbox\b', r'\bAGB\b', r'\bshaft\b',
    r'\bcoupling\b',
    # General
    r'\benclosure\b', r'\bskid\b', r'\bgenerator\b', r'\bload\b',
    r'\btrip\b', r'\balarm\b', r'\bmaintenance\b', r'\binspection\b',
]

# ── Image Metadata (populated after extraction) ───────────────
IMAGE_METADATA = {}
