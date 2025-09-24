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

def split_pdf_by_outline(input_file: str, output_root: str = "data_split"):
    file_name = os.path.basename(input_file)
    base_name = os.path.splitext(file_name)[0]

    # Nếu không truyền output_root thì folder output = cùng cấp với file gốc
    if output_root is None:
        output_root = os.path.dirname(input_file)

    # Folder xuất ra = <output_root>/<tên file pdf>
    file_output_dir = os.path.join(output_root, base_name)
    os.makedirs(file_output_dir, exist_ok=True)

    print(f"\nProcessing file: {file_name}")
    reader = PdfReader(input_file)

    try:
        outlines = reader.outline
    except Exception:
        outlines = []

    if not outlines:
        print("This file has no outline/bookmark.")
        return

    flat_outlines = flatten_outlines(outlines)

    # Lọc những outline có page hợp lệ
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

    print(f"Found {len(valid_outlines)} valid outlines:")
    for i, outline in enumerate(valid_outlines, 1):
        print(f"      {i}. {outline.title}")
    output_files = []
    # Tách file theo outline
    for i, outline in enumerate(valid_outlines, 1):
        title = sanitize_filename(outline.title)
        start_page = reader.get_destination_page_number(outline)

        if i < len(valid_outlines):
            end_page = reader.get_destination_page_number(valid_outlines[i])
        else:
            end_page = len(reader.pages)

        # Bảo vệ khi end_page < start_page
        if end_page is None or start_page is None or end_page <= start_page:
            continue

        writer = PdfWriter()
        for p in range(start_page, end_page):
            writer.add_page(reader.pages[p])

        output_path = os.path.join(file_output_dir, f"{i:02d}_{title}.pdf")
        with open(output_path, "wb") as f:
            writer.write(f)
        output_files.append(output_path)
        print(f"Exported: {output_path}")

    return output_files if output_files else [input_file]

# -------------------- RUN --------------------
if __name__ == "__main__":
    input_file = r"troubleshoot-windows-server.pdf"
    split_pdf_by_outline(input_file)
    
