import os
from pypdf import PdfReader, PdfWriter
from pypdf.generic import Destination

def sanitize_filename(name: str) -> str:
    """Remove invalid characters from filename"""
    return "".join(c for c in name if c.isalnum() or c in (' ', '_', '-')).rstrip()

def flatten_outlines(outlines):
    """Đệ quy duyệt outlines, trả về list Destination"""
    flat = []
    for o in outlines:
        if isinstance(o, list):  # Outline con
            flat.extend(flatten_outlines(o))
        elif isinstance(o, Destination):
            flat.append(o)
    return flat

def split_pdf_by_outline(input_file: str, output_folder: str):
    """Split PDF with outline"""
    file_name = os.path.basename(input_file)
    print(f"\nProcessing file: {file_name}")

    reader = PdfReader(input_file)

    try:
        outlines = reader.outline
    except Exception:
        outlines = []

    if not outlines:
        print("PDF is not setup outline/bookmark.")
        return

    flat_outlines = flatten_outlines(outlines)

    # Filter out outlines without pages
    valid_outlines = []
    for o in flat_outlines:
        try:
            page_num = reader.get_destination_page_number(o)
            if page_num is not None:
                valid_outlines.append(o)
        except Exception:
            continue

    if not valid_outlines:
        print("No valid outlines found for splitting.")
        return

    print(f" Found {len(valid_outlines)} valid outlines:")
    for i, outline in enumerate(valid_outlines, 1):
        print(f"   {i}. {outline.title}")

    # Create subfolder for this file
    base_name = os.path.splitext(file_name)[0]
    file_output_dir = os.path.join(output_folder, base_name)
    os.makedirs(file_output_dir, exist_ok=True)

    # Split file by outline
    for i, outline in enumerate(valid_outlines, 1):
        title = sanitize_filename(outline.title)
        start_page = reader.get_destination_page_number(outline)

        if i < len(valid_outlines):
            end_page = reader.get_destination_page_number(valid_outlines[i])
        else:
            end_page = len(reader.pages)

        if end_page is None or start_page is None or end_page <= start_page:
            continue

        writer = PdfWriter()
        for p in range(start_page, end_page):
            writer.add_page(reader.pages[p])

        output_path = os.path.join(file_output_dir, f"{i:02d}_{title}.pdf")
        with open(output_path, "wb") as f:
            writer.write(f)

        print(f"Exported: {output_path}")

if __name__ == "__main__":
    input_file = r"troubleshoot-windows-server.pdf"
    output_folder = "newdata_server"
    os.makedirs(output_folder, exist_ok=True)

    split_pdf_by_outline(input_file, output_folder)
