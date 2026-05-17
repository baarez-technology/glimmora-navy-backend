"""
Agent 2 — Chunker (Navy)
Splits LM2500 Gas Turbine text into retrievable chunks with rich metadata.
"""
import re
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import CHUNK_SIZE, CHUNK_OVERLAP, KEYWORD_PATTERNS, SECTION_MAP


def chunk_pages(pages: list[dict]) -> list[dict]:
    """Split parsed pages into chunks with metadata."""
    print(f"[Agent 2 — Navy] Chunking {len(pages)} pages...")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""],
        length_function=len,
    )

    current_section = None
    chunks = []
    chunk_id = 0

    for page in pages:
        if page["section"]:
            current_section = page["section"]

        text = page["text"].strip()
        if not text:
            continue

        raw_chunks = splitter.split_text(text)

        for raw in raw_chunks:
            raw = raw.strip()
            if len(raw) < 50:
                continue

            figures  = re.findall(r'[Ff]ig(?:ure)?\s+(\d+(?:[.-]\d+)?)', raw)
            keywords = _extract_keywords(raw)
            topic    = _infer_topic(raw, current_section)

            chunk = {
                "chunk_id":    f"navy_chunk_{chunk_id:04d}",
                "section":     current_section,
                "page_number": page["page_number"],
                "topic":       topic,
                "keywords":    keywords,
                "figure_refs": figures,
                "headings":    page["headings"],
                "text":        raw,
                "char_count":  len(raw),
            }
            chunks.append(chunk)
            chunk_id += 1

    print(f"[Agent 2 — Navy] Created {len(chunks)} chunks")
    return chunks


def _extract_keywords(text: str) -> list[str]:
    found = set()
    text_lower = text.lower()
    for pattern in KEYWORD_PATTERNS:
        if re.search(pattern, text_lower, re.IGNORECASE):
            kw = re.sub(r'\\b|\\', '', pattern).replace('.', ' ').strip()
            found.add(kw)
    return sorted(found)


def _infer_topic(text: str, chapter: int | None) -> str:
    base = SECTION_MAP.get(chapter, "general") if chapter else "general"
    t = text.lower()

    if "compressor" in t and ("stall" in t or "surge" in t):
        return "compressor stall and surge"
    if "igv" in t or "variable geometry" in t or "variable stator" in t:
        return "IGV and variable stator vanes"
    if "compressor" in t and ("rotor" in t or "blade" in t):
        return "compressor rotor and blades"
    if "bellmouth" in t or "bullet nose" in t:
        return "inlet bellmouth and bullet nose"
    if "filter house" in t or "trash screen" in t:
        return "inlet filter house"
    if "combustor" in t or "combustion chamber" in t:
        return "annular combustion chamber"
    if "fuel nozzle" in t and "igniter" in t:
        return "fuel nozzles and igniters"
    if "fuel nozzle" in t:
        return "fuel nozzles"
    if "high" in t and "pressure" in t and "turbine" in t:
        return "high-pressure turbine section"
    if "power turbine" in t or ("low" in t and "pressure" in t and "turbine" in t):
        return "low-pressure power turbine"
    if "midframe" in t:
        return "turbine midframe"
    if "exhaust" in t or "diffuser" in t:
        return "exhaust diffuser"
    if "lube oil" in t and ("pump" in t or "scavenge" in t):
        return "lube oil pumps and scavenge"
    if "lube oil" in t and "cooler" in t:
        return "lube oil cooler"
    if "bearing" in t and ("seal" in t or "oil" in t):
        return "bearing and seal system"
    if "gas control valve" in t:
        return "gas control valve"
    if "flow divider" in t:
        return "fuel flow divider"
    if "hydraulic start" in t or "starter" in t:
        return "hydraulic start system"
    if "torque converter" in t:
        return "torque converter"
    if "sss clutch" in t:
        return "SSS clutch"
    if "firing" in t or "startup sequence" in t:
        return "firing and startup sequence"
    if "accessory" in t and "gearbox" in t:
        return "accessory gearbox — AGB"
    if "control oil" in t:
        return "control oil system"
    if "water injection" in t:
        return "water injection system"
    if "troubleshoot" in t or "trip" in t or "alarm" in t:
        return "troubleshooting"
    if "maintenance" in t or "inspection" in t:
        return "preventive maintenance"
    if "enclosure" in t or "skid" in t:
        return "turbine enclosure and skid"
    if "generator" in t and ("coupling" in t or "load" in t):
        return "generator and coupling"

    return base


if __name__ == "__main__":
    from agent1_pdf_parser import parse_pdf
    pages  = parse_pdf()
    chunks = chunk_pages(pages)

    print(f"\nSample chunks:")
    for c in chunks[5:9]:
        print(f"\n[{c['chunk_id']}] p{c['page_number']} | {c['topic']}")
        print(f"  Keywords: {c['keywords'][:5]}")
        print(f"  Text:     {c['text'][:200]}...")
