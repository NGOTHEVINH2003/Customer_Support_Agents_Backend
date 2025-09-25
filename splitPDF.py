import os
import re
import fitz 

def split_pdf_by_heading(input_pdf, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    doc = fitz.open(input_pdf)

    headings = []

    for page_num, page in enumerate(doc):
        blocks = page.get_text("dict")["blocks"]

        for b in blocks:
            if "lines" not in b:
                continue
            for l in b["lines"]:
                for s in l["spans"]:
                    text = s["text"].strip()
                    size = s["size"]

                    if len(text.split()) > 3 and size >= 13:
                        next_text = page.get_text("text").split("\n")
                        idx = next((i for i, t in enumerate(next_text) if text in t), -1)
                        if idx >= 0 and any(
                            re.search(r"\d{2}/\d{2}/\d{4}", t) for t in next_text[idx:idx+4]
                        ):
                            headings.append((page_num, text))

    if not headings:
        print("Không tìm thấy heading nào. Thử chỉnh lại font size threshold.")
        return

    # Tách PDF
    for i, (start_page, heading) in enumerate(headings):
        end_page = headings[i+1][0] if i+1 < len(headings) else len(doc)

        new_doc = fitz.open()
        new_doc.insert_pdf(doc, from_page=start_page, to_page=end_page-1)

        safe_heading = re.sub(r"[^a-zA-Z0-9_-]", "_", heading)[:60]
        filename = os.path.join(output_dir, f"{i+1:03d}_{safe_heading}.pdf")
        new_doc.save(filename)
        new_doc.close()
        print(f"Saved: {filename}")

    doc.close()
    print("Done!!!!!!")

if __name__ == "__main__":
    input_pdf = "troubleshoot-windows-client.pdf"  
    output_dir = "troubleshoot-windows-client" 
    split_pdf_by_heading(input_pdf, output_dir)
