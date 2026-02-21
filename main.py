from __future__ import annotations

import csv
import os
import re
from typing import List, Optional

from PIL import Image, ImageDraw, ImageFont, ImageOps


# ==========================
# CONFIG
# ==========================
CSV_FILE = "id_data.csv"
TEMPLATE_PATH = "id_template.png"
PHOTO_FOLDER = "photos"
OUTPUT_FOLDER = "output"

# Photo box (top-left corner where the photo will be pasted)
PHOTO_POSITION = (520, 200)
PHOTO_SIZE = (180, 180)

# Text block starts below the photo and flows downward.
TEXT_START_X = 520
TEXT_START_Y = PHOTO_POSITION[1] + PHOTO_SIZE[1] + 16

# Wrap area width for all text blocks
WRAP_MAX_WIDTH = 260
SECTION_GAP = 10

# Colors (hex supported by Pillow)
COLOR_BLACK = "#000000"
COLOR_RED   = "#FF0000"

# Fonts
# Option A (recommended): Put your font files inside ./fonts and set paths here.
# Example:
# FONT_NAME_PATH = os.path.join("fonts", "Brigends Expanded.otf")
# If you don't have custom fonts, keep None and it will fall back to arial.
FONT_NAME_PATH: Optional[str] = None
FONT_ID_PATH: Optional[str] = None
FONT_ROLE_PATH: Optional[str] = None
FONT_SMALL_PATH: Optional[str] = None

FONT_NAME_SIZE = 56
FONT_ID_SIZE = 34
FONT_ROLE_SIZE = 52
FONT_SMALL_SIZE = 22


# ==========================
# HELPERS
# ==========================
def safe_filename(text: str) -> str:
    text = text.strip().replace(" ", "_")
    text = re.sub(r"[^A-Za-z0-9_\\-]+", "", text)
    return text or "unknown"


def load_font(font_path: Optional[str], size: int) -> ImageFont.FreeTypeFont:
    # Use custom font if supplied and exists, otherwise try Arial, otherwise default
    if font_path and os.path.exists(font_path):
        return ImageFont.truetype(font_path, size)

    try:
        return ImageFont.truetype("arial.ttf", size)
    except Exception:
        return ImageFont.load_default()


def text_width(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont) -> int:
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0]


def text_height(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont) -> int:
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[3] - bbox[1]


def wrap_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont, max_width: int) -> List[str]:
    # Word-wrap by measuring width
    words = text.split()
    if not words:
        return [""]

    lines: List[str] = []
    line: List[str] = []

    for w in words:
        test = " ".join(line + [w])
        if text_width(draw, test, font) <= max_width:
            line.append(w)
        else:
            if line:
                lines.append(" ".join(line))
                line = [w]
            else:
                # Single word longer than max_width: hard-cut
                lines.append(w)
                line = []

    if line:
        lines.append(" ".join(line))

    return lines


def fit_font_size(
    draw: ImageDraw.ImageDraw,
    text: str,
    font_path: Optional[str],
    start_size: int,
    max_width: int,
    min_size: int = 14,
) -> ImageFont.ImageFont:
    size = start_size
    while size >= min_size:
        font = load_font(font_path, size)
        if text_width(draw, text, font) <= max_width:
            return font
        size -= 1
    return load_font(font_path, min_size)


def open_photo_correct_orientation(path: str) -> Image.Image:
    # Fix EXIF rotation AND convert to RGBA to avoid paste issues
    img = Image.open(path)
    img = ImageOps.exif_transpose(img)
    return img.convert("RGBA")


# ==========================
# CORE
# ==========================
def create_id_card(
    firstname: str,
    lastname: str,
    role: str,
    school: str,
    district: str,
    photo_filename: str,
    template_path: str,
    photo_folder: str,
    output_folder: str,
):
    full_name = f"{firstname} {lastname}".strip()

    template = Image.open(template_path).convert("RGBA")
    draw = ImageDraw.Draw(template)

    font_name = fit_font_size(
        draw=draw,
        text=full_name.upper(),
        font_path=FONT_NAME_PATH,
        start_size=FONT_NAME_SIZE,
        max_width=WRAP_MAX_WIDTH,
        min_size=28,
    )
    font_id = load_font(FONT_ID_PATH, FONT_ID_SIZE)
    font_role = fit_font_size(
        draw=draw,
        text=str(role).upper(),
        font_path=FONT_ROLE_PATH,
        start_size=FONT_ROLE_SIZE,
        max_width=WRAP_MAX_WIDTH,
        min_size=20,
    )
    font_small = load_font(FONT_SMALL_PATH, FONT_SMALL_SIZE)

    y = TEXT_START_Y

    name_lines = wrap_text(draw, full_name.upper(), font_name, max_width=WRAP_MAX_WIDTH)
    for ln in name_lines[:2]:
        draw.text((TEXT_START_X, y), ln, fill=COLOR_BLACK, font=font_name)
        y += text_height(draw, ln, font_name) + 2
    y += SECTION_GAP

    generated_id = safe_filename(f"{lastname}_{firstname}").upper()
    id_line = f"ID: {generated_id}"
    draw.text((TEXT_START_X, y), id_line, fill=COLOR_BLACK, font=font_id)
    y += text_height(draw, id_line, font_id) + SECTION_GAP

    role_line = str(role).upper()
    draw.text((TEXT_START_X, y), role_line, fill=COLOR_RED, font=font_role)
    y += text_height(draw, role_line, font_role) + SECTION_GAP

    school_text = f"SCHOOL: {school}".upper().strip()
    school_lines = wrap_text(draw, school_text, font_small, WRAP_MAX_WIDTH)
    for ln in school_lines[:3]:
        draw.text((TEXT_START_X, y), ln, fill=COLOR_BLACK, font=font_small)
        y += text_height(draw, ln, font_small) + 2
    y += 4

    district_text = f"DISTRICT: {district}".upper().strip()
    district_lines = wrap_text(draw, district_text, font_small, WRAP_MAX_WIDTH)
    for ln in district_lines[:3]:
        draw.text((TEXT_START_X, y), ln, fill=COLOR_BLACK, font=font_small)
        y += text_height(draw, ln, font_small) + 2

    # Photo
    photo_path = os.path.join(photo_folder, photo_filename) if photo_filename else ""
    if photo_path and os.path.exists(photo_path):
        try:
            photo = open_photo_correct_orientation(photo_path)

            # If still rotated weird (no EXIF / wrong EXIF), optional heuristic:
            # If it's very tall vs wide, keep; if it's sideways and looks wrong, you can rotate:
            # if photo.width > photo.height:
            #     photo = photo.rotate(90, expand=True)

            photo = photo.resize(PHOTO_SIZE)
            template.paste(photo, PHOTO_POSITION, mask=photo)
        except Exception as e:
            print(f"[WARN] Photo error for '{photo_path}': {e}")
    else:
        if photo_filename:
            print(f"[WARN] Photo not found: {photo_path}")

    # Save output
    os.makedirs(output_folder, exist_ok=True)
    out_name = safe_filename(f"{firstname}_{lastname}").upper() + ".png"
    out_path = os.path.join(output_folder, out_name)
    template.convert("RGB").save(out_path)
    print(f"Saved: {out_path}")


def batch_generate_id_cards(csv_file: str):
    if not os.path.exists(TEMPLATE_PATH):
        raise FileNotFoundError(f"Missing template: {TEMPLATE_PATH} (put id_template.png in the project root)")

    # IMPORTANT: utf-8-sig removes BOM (\\ufeff) from 'firstname'
    with open(csv_file, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        print(f"Detected headers: {reader.fieldnames}")

        for i, row in enumerate(reader, start=1):
            try:
                firstname = (row.get("firstname") or "").strip()
                lastname  = (row.get("lastname") or "").strip()
                role      = (row.get("Role") or "").strip()
                photo     = (row.get("Photo") or "").strip()
                district  = (row.get("District") or "").strip()
                school    = (row.get("School") or "").strip()

                if not firstname and not lastname:
                    print(f"[WARN] Row {i}: missing firstname/lastname - skipping")
                    continue

                create_id_card(
                    firstname=firstname,
                    lastname=lastname,
                    role=role,
                    school=school,
                    district=district,
                    photo_filename=photo,
                    template_path=TEMPLATE_PATH,
                    photo_folder=PHOTO_FOLDER,
                    output_folder=OUTPUT_FOLDER,
                )

            except Exception as e:
                print(f"[ERROR] Row {i} failed: {e}")


if __name__ == "__main__":
    batch_generate_id_cards(CSV_FILE)
