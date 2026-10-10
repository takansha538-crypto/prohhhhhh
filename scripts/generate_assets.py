"""Generate local SVG logo, avatars, and portfolio covers."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "static" / "images"
(ROOT / "avatars").mkdir(parents=True, exist_ok=True)
(ROOT / "portfolio").mkdir(parents=True, exist_ok=True)

LOGO = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" fill="none">
  <rect width="64" height="64" rx="16" fill="#1C2C44"/>
  <circle cx="22" cy="32" r="8" stroke="#F3EFE8" stroke-width="2.2"/>
  <circle cx="42" cy="24" r="6" stroke="#B5522A" stroke-width="2.2"/>
  <circle cx="44" cy="42" r="5" stroke="#C9A15B" stroke-width="2"/>
  <path d="M29 29.5 L37 25.5 M28.5 36 L40 40" stroke="#F3EFE8" stroke-width="1.8"/>
  <path d="M42 18 L43.2 21.2 L46.5 22 L43.2 22.8 L42 26 L40.8 22.8 L37.5 22 L40.8 21.2 Z" fill="#C9A15B"/>
</svg>
"""

AVATARS = {
    "aria": ("AC", "#1C2C44", "#E8C9B0"),
    "marcus": ("MV", "#3D4A3A", "#D8C4A8"),
    "priya": ("PR", "#5C2E2A", "#F0D2C0"),
    "jonah": ("JO", "#2A3B4A", "#C9B48A"),
    "elena": ("ER", "#4A2C3B", "#EAD3C4"),
    "kenji": ("KN", "#2C3340", "#D9C7B0"),
    "sofia": ("SA", "#3A4A32", "#E4CDB8"),
    "theo": ("TB", "#242424", "#D6C2A6"),
    "amara": ("AD", "#3B2F28", "#E2C3A8"),
    "liam": ("LW", "#2F3F38", "#DCC8A8"),
    "hana": ("HK", "#4A3140", "#F0D5C8"),
    "rafael": ("RC", "#3A3228", "#E0C29A"),
    "isabelle": ("IM", "#2E3644", "#E6D3C2"),
    "dev": ("DS", "#3B332C", "#E8D2B8"),
    "nina": ("NP", "#2C3A38", "#D5C8B4"),
    "maya": ("ME", "#1C2C44", "#C9B48A"),
    "claire": ("CH", "#4A3030", "#EAD3C4"),
    "oskar": ("OL", "#2C3A44", "#D8C4A8"),
    "pmenon": ("PM", "#3D3228", "#E8D2B8"),
    "jreed": ("JR", "#33402C", "#DCC8A8"),
    "leila": ("LH", "#3A2C38", "#E4CDB8"),
    "default": ("CH", "#6B645C", "#F3EFE8"),
}


def avatar(initials, bg, skin):
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 160 160">
  <rect width="160" height="160" fill="{bg}"/>
  <circle cx="80" cy="62" r="28" fill="{skin}"/>
  <ellipse cx="80" cy="148" rx="48" ry="40" fill="{skin}"/>
  <text x="80" y="28" text-anchor="middle" font-family="Georgia, serif" font-size="14" fill="#F3EFE8">{initials}</text>
</svg>
"""


COVERS = {
    "helix-night": ("#1A1420", "#B5522A", "Helix Night Atelier"),
    "lumina-drift": ("#1C2C44", "#C9A15B", "Lumina Drift"),
    "orbit-pulse": ("#241C18", "#8D6A32", "Orbit Pulse"),
    "atlas-quiet": ("#E8E2D6", "#1C2C44", "Atlas Quiet Geometry"),
    "verdant-seed": ("#2F4A32", "#E4CDB8", "Verdant Seed"),
    "helix-silk": ("#3B2A28", "#E8C9B0", "Helix Silk Loop"),
    "lumina-cabin": ("#2A3038", "#A8B4C0", "Lumina Cabin"),
    "verdant-table": ("#F3EFE8", "#1F4D3A", "Verdant Table Light"),
    "orbit-bible": ("#16130F", "#C9A15B", "Orbit World Bible"),
    "atlas-inheritance": ("#2C2824", "#D8C4A8", "Atlas Inheritance"),
    "orbit-ceramic": ("#E6DDD0", "#6B4A3A", "Orbit Ceramic"),
    "helix-hardware": ("#1A1814", "#B8A078", "Helix Hardware"),
    "atlas-type": ("#F4F0EA", "#1C2C44", "Atlas Kinetic"),
    "verdant-field": ("#3A4630", "#DCC8A8", "Verdant Field Notes"),
    "lumina-dawn": ("#C45C2C", "#1C2C44", "Lumina Dawn"),
    "default": ("#1C2C44", "#B5522A", "CreatorsHub Project"),
}


def cover(bg, accent, title):
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 500">
  <rect width="800" height="500" fill="{bg}"/>
  <circle cx="620" cy="120" r="160" fill="{accent}" fill-opacity="0.35"/>
  <rect x="80" y="320" width="280" height="8" fill="{accent}"/>
  <text x="80" y="300" font-family="Georgia, serif" font-size="36" fill="#F3EFE8">{title}</text>
  <text x="80" y="360" font-family="system-ui, sans-serif" font-size="16" fill="#F3EFE8" fill-opacity="0.7">CreatorsHub portfolio · demo visual</text>
</svg>
"""


def main():
    (ROOT / "logo.svg").write_text(LOGO, encoding="utf-8")
    for name, (ini, bg, skin) in AVATARS.items():
        (ROOT / "avatars" / f"{name}.svg").write_text(avatar(ini, bg, skin), encoding="utf-8")
    for name, (bg, ac, title) in COVERS.items():
        (ROOT / "portfolio" / f"{name}.svg").write_text(cover(bg, ac, title), encoding="utf-8")
    print("assets written")


if __name__ == "__main__":
    main()
