"""
Update the portfolio gallery on laytojoe.github.io/Portfolio from the PowerPoint PDF export.

What it does:
  1. Renders each gallery page of the PDF to slides/slide-NN.jpeg (1456 x 840, same as before).
  2. Rewrites the gallery figures and the lightbox viewers in index.html to match.

Usage (run from the repo folder):
  pip install pymupdf
  python update_portfolio.py Joseph_Layton_Portfolio.pdf

When you add, remove, or reorder slides, edit CAPTIONS below. One entry per gallery page,
in PDF order, starting at FIRST_PAGE. Each entry is (title, tag); tag can be "".
"""
import sys, html, re
from pathlib import Path
import pymupdf

FIRST_PAGE = 3          # pages 1-2 (title, About Me) are not shown in the gallery
WIDTH, HEIGHT = 1456, 840

CAPTIONS = [
    ("Test & Flight Operations", "CMI², Pitt SOAR"),
    ("Competition Rocket Airframe — Anubis", "2026 IREC"),
    ("Boat Tail FEA / Thermal", "ANSYS"),
    ("Fin Flutter Margin — Modal Analysis", "ANSYS"),
    ("SRAD Motor Development", ""),
    ("Static-Fire Stand — Failure & Redesign", ""),
    ("Active Airbrake Control System", ""),
    ("Competition Rocket Airframe — PAX-1", "2025 IREC"),
    ("Personal TRA L1/L2 Rockets", ""),
    ("Amoeba-1 Flight Data", ""),
    ("3D-Printed 38 mm Minimum-Diameter Rocket", "PA6-GF"),
    ("CMI² Data Collection Module", 'UAS "black box"'),
    ("CFD Study — Laminar / Turbulent Flow", ""),
    ("FRA — UL9540A Battery-Safety Testing", ""),
    ("CMI² UAS Support — Dirt Days", ""),
    ("FRA — CNC Electronics & PCB", ""),
    ("FRA — 4S Test System Design", ""),
    ("FRA — Fume Hood CAD", ""),
]


def main(pdf_path):
    repo = Path(__file__).resolve().parent
    doc = pymupdf.open(pdf_path)
    pages = list(range(FIRST_PAGE, doc.page_count + 1))
    if len(pages) != len(CAPTIONS):
        sys.exit(f"PDF has {len(pages)} gallery pages (from page {FIRST_PAGE}) but CAPTIONS has "
                 f"{len(CAPTIONS)} entries. Update CAPTIONS to match the deck, then rerun.")

    # 1. Render slides
    out_dir = repo / "slides"
    out_dir.mkdir(exist_ok=True)
    for old in out_dir.glob("slide-*.jpeg"):
        if int(old.stem.split("-")[1]) >= FIRST_PAGE:
            old.unlink()                       # clear stale gallery images
    for n in pages:
        page = doc[n - 1]
        zoom = WIDTH / page.rect.width
        pix = page.get_pixmap(matrix=pymupdf.Matrix(zoom, HEIGHT / page.rect.height), alpha=False)
        pix.save(out_dir / f"slide-{n:02d}.jpeg", jpg_quality=88)
    print(f"Rendered {len(pages)} slides to {out_dir}")

    # 2. Rebuild gallery figures and lightboxes
    figs, boxes = [], []
    for i, (n, (title, tag)) in enumerate(zip(pages, CAPTIONS)):
        prev_n = pages[i - 1]                  # wraps to last slide
        next_n = pages[(i + 1) % len(pages)]   # wraps to first slide
        alt = html.escape(title, quote=True)
        cap = f"<b>{html.escape(title)}</b>" + (f" · {html.escape(tag)}" if tag else "")
        figs.append(f'      <figure class="slide"><a href="#s{n}"><img src="slides/slide-{n:02d}.jpeg" '
                    f'alt="{alt}" loading="lazy"></a><figcaption>{cap}</figcaption></figure>')
        boxes.append(f'<div class="lb" id="s{n}"><a href="#" class="close">×</a>'
                     f'<a href="#s{prev_n}" class="nav prev">‹</a><img src="slides/slide-{n:02d}.jpeg" alt="">'
                     f'<a href="#s{next_n}" class="nav next">›</a></div>')

    index = repo / "index.html"
    text = index.read_text(encoding="utf-8")
    text, k1 = re.subn(r'(<div class="gallery">\n).*?(\n    </div>\n  </div>\n</section>)',
                       lambda m: m.group(1) + "\n".join(figs) + m.group(2), text, count=1, flags=re.S)
    text, k2 = re.subn(r'(<!-- Lightboxes -->\n).*?(\n\n?</body>)',
                       lambda m: m.group(1) + "\n".join(boxes) + m.group(2), text, count=1, flags=re.S)
    if k1 != 1 or k2 != 1:
        sys.exit("Could not find the gallery or lightbox block in index.html; nothing was written.")
    index.write_text(text, encoding="utf-8")
    print("Updated index.html")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("Usage: python update_portfolio.py Joseph_Layton_Portfolio.pdf")
    main(sys.argv[1])
