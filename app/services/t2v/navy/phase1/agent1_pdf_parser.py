"""
Agent 1 — PDF Parser (Navy)
Extracts text and images from LM2500 Gas Turbine Course page by page using PyMuPDF.
Detects chapter headings, figure references, and section markers.
Also extracts embedded images (3D renders, photos, diagrams) as PNGs.
"""
import re
import fitz  # PyMuPDF
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import PDF_PATH, IMAGES_DIR


def parse_pdf() -> list[dict]:
    """Extract all text from LM2500 manual. Returns list of page dicts."""
    print(f"[Agent 1 — Navy] Opening PDF: {PDF_PATH}")
    doc = fitz.open(str(PDF_PATH))
    print(f"[Agent 1 — Navy] Total pages: {len(doc)}")

    pages = []
    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text("text")
        text = _clean_text(text)
        if not text.strip():
            continue

        chapter  = _detect_chapter(text)
        headings = _detect_headings(text)
        figures  = _detect_figures(text)

        pages.append({
            "page_number": page_num + 1,
            "page_index":  page_num,
            "text":        text,
            "section":     chapter,
            "headings":    headings,
            "figures":     figures,
            "char_count":  len(text),
        })

    doc.close()
    print(f"[Agent 1 — Navy] Parsed {len(pages)} pages with text content")
    return pages


def extract_images() -> list[dict]:
    """Extract all embedded images from the PDF as PNGs."""
    print(f"[Agent 1 — Navy] Extracting images from PDF...")
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)

    doc = fitz.open(str(PDF_PATH))
    image_records = []
    img_count = 0

    for page_num in range(len(doc)):
        page = doc[page_num]
        image_list = page.get_images(full=True)

        for img_idx, img_info in enumerate(image_list):
            xref = img_info[0]
            try:
                base_image = doc.extract_image(xref)
            except Exception:
                continue

            image_bytes = base_image["image"]
            ext = base_image.get("ext", "png")
            width = base_image.get("width", 0)
            height = base_image.get("height", 0)

            # Skip tiny images (logos, icons)
            if width < 100 or height < 100:
                continue

            filename = f"lm2500_pg{page_num + 1:03d}_img{img_idx:02d}.{ext}"
            filepath = IMAGES_DIR / filename

            with open(filepath, "wb") as f:
                f.write(image_bytes)

            page_text = page.get_text("text")
            caption = _find_caption(page_text, page_num + 1)

            image_records.append({
                "filename":    filename,
                "file_path":   str(filepath),
                "page_number": page_num + 1,
                "width":       width,
                "height":      height,
                "caption":     caption,
                "topic":       _infer_image_topic(page_text),
            })
            img_count += 1

    doc.close()
    print(f"[Agent 1 — Navy] Extracted {img_count} images to {IMAGES_DIR}")
    return image_records


def extract_page_as_image(page_numbers: list[int], zoom: float = 2.5) -> list[dict]:
    """Render specific pages as high-res PNG images."""
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    doc = fitz.open(str(PDF_PATH))
    records = []

    mat = fitz.Matrix(zoom, zoom)
    for pg in page_numbers:
        if pg < 1 or pg > len(doc):
            continue
        page = doc[pg - 1]
        pix = page.get_pixmap(matrix=mat)
        filename = f"lm2500_page_{pg:03d}.png"
        filepath = IMAGES_DIR / filename
        pix.save(str(filepath))

        page_text = page.get_text("text")
        records.append({
            "filename":    filename,
            "file_path":   str(filepath),
            "page_number": pg,
            "width":       pix.width,
            "height":      pix.height,
            "caption":     _find_caption(page_text, pg),
            "topic":       _infer_image_topic(page_text),
        })

    doc.close()
    print(f"[Agent 1 — Navy] Rendered {len(records)} page images")
    return records


def _clean_text(text: str) -> str:
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = text.replace('\x0c', '\n')
    lines = []
    for line in text.split('\n'):
        line = re.sub(r'[ \t]+', ' ', line).strip()
        lines.append(line)
    # Remove repeated header/footer
    cleaned = re.sub(
        r'LM2500 Combustion Turbine\s+Course\s+MILITARY SEALIFT COMMAND',
        '', '\n'.join(lines)
    )
    cleaned = re.sub(r'Copyright © \d{4} by Technical Training Professionals', '', cleaned)
    return cleaned


def _detect_chapter(text: str) -> int | None:
    """Detect LM2500 chapter number."""
    match = re.search(r'Ch(?:apter)?\s*(\d+)', text, re.IGNORECASE)
    if match:
        return int(match.group(1))
    # Infer from content
    t = text.lower()
    chapter_hints = [
        (1, ["overview", "enclosure"]),
        (2, ["inlet air", "filter house", "bellmouth"]),
        (3, ["accessory drive", "gearbox", "agb"]),
        (4, ["compressor section", "stator vane", "axial flow"]),
        (5, ["fuel gas system", "fuel nozzle", "combustion"]),
        (6, ["turbine section", "high-pressure turbine", "hp turbine"]),
        (7, ["lube oil", "scavenge", "bearing"]),
        (8, ["hydraulic oil", "control oil", "servo"]),
        (9, ["hydraulic start", "starter", "torque converter"]),
        (10, ["firing", "startup sequence", "zero speed"]),
        (11, ["troubleshooting", "alarm", "trip"]),
        (12, ["maintenance", "inspection", "preventive"]),
    ]
    for ch, keywords in chapter_hints:
        if any(kw in t for kw in keywords):
            return ch
    return None


def _detect_headings(text: str) -> list[str]:
    headings = []
    for line in text.split('\n'):
        line = line.strip()
        if len(line) > 3 and len(line) < 100:
            # LM2500 uses numbered headings like "1. Enclosures", "4. Compressor"
            if re.match(r'^\d+\.\s+[A-Z]', line):
                headings.append(line)
            elif line.isupper() and len(line) > 5:
                headings.append(line)
    return headings


def _detect_figures(text: str) -> list[str]:
    figs = re.findall(r'[Ff]ig(?:ure)?\s+(\d+(?:[.-]\d+)?)', text)
    return figs


def _find_caption(text: str, page_num: int) -> str:
    # LM2500 uses descriptive text near images
    match = re.search(r'(?:Below|above|following)\s+(?:is|are|shows?)\s+(.+?)(?:\.|$)', text, re.IGNORECASE)
    if match:
        return match.group(1).strip()[:120]
    # Try numbered heading
    match = re.search(r'^\d+\.\s+(.+)', text, re.MULTILINE)
    if match:
        return match.group(1).strip()[:120]
    return f"LM2500 diagram from page {page_num}"


def _infer_image_topic(text: str) -> str:
    t = text.lower()
    if "compressor" in t and ("stator" in t or "rotor" in t or "blade" in t):
        return "compressor section"
    if "combustor" in t or "combustion" in t or "fuel nozzle" in t:
        return "combustion section"
    if "turbine" in t and ("high" in t or "hp" in t):
        return "high-pressure turbine"
    if "turbine" in t and ("low" in t or "lp" in t or "power" in t):
        return "power turbine"
    if "midframe" in t:
        return "turbine midframe"
    if "inlet" in t or "bellmouth" in t or "bullet nose" in t:
        return "inlet air system"
    if "accessory" in t or "gearbox" in t or "agb" in t:
        return "accessory drive"
    if "lube" in t or "oil pump" in t or "bearing" in t:
        return "lube oil system"
    if "hydraulic" in t and "start" in t:
        return "hydraulic start system"
    if "hydraulic" in t:
        return "hydraulic oil system"
    if "fuel" in t and "gas" in t:
        return "fuel gas system"
    if "firing" in t or "startup" in t or "ignit" in t:
        return "firing sequence"
    if "troubleshoot" in t or "alarm" in t:
        return "troubleshooting"
    if "maintenance" in t or "inspection" in t:
        return "maintenance"
    if "enclosure" in t or "overview" in t or "skid" in t:
        return "overview"
    return "general gas turbine"


if __name__ == "__main__":
    pages = parse_pdf()
    for p in pages[:3]:
        print(f"\n--- Page {p['page_number']} | Chapter {p['section']} | Figs: {p['figures']} ---")
        print(p['text'][:300])

    images = extract_images()
    print(f"\nExtracted {len(images)} images")
    for img in images[:5]:
        print(f"  {img['filename']} | {img['topic']} | {img['caption'][:60]}")
