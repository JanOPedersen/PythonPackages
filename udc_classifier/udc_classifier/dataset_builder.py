import os
from tqdm import tqdm
from .pdf_extractor import extract_text_from_pdf


def collapse_code(code, depth=4):
    parts = code.split(".")
    return ".".join(parts[:depth])


def build_dataset(codes_dict):
    pdf_paths = list(codes_dict.keys())
    codes = [collapse_code(c) for c in codes_dict.values()]

    texts = []
    for path in tqdm(pdf_paths, desc="Extracting PDFs", unit="file"):
        texts.append(extract_text_from_pdf(path))

    return texts, codes
