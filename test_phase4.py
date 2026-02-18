import requests
import io
try:
    from pypdf import PdfWriter
except ImportError:
    print("pypdf not found, skipping PDF generation")
    PdfWriter = None

BASE = "http://localhost:8000"

def test_parse_content():
    if not PdfWriter:
        print("Skipping PDF test")
        return

    # 1. Create a dummy PDF
    buffer = io.BytesIO()
    writer = PdfWriter()
    page = writer.add_blank_page(width=200, height=200)
    # We can't easily add text without reportlab, but let's see if pypdf can read a blank page or metadata
    writer.write(buffer)
    buffer.seek(0)
    
    # 2. Upload to API
    print("Uploading PDF...")
    try:
        files = {'file': ('test.pdf', buffer, 'application/pdf')}
        r = requests.post(f"{BASE}/jobs/parse-content", files=files)
        print(f"Status: {r.status_code}")
        print(f"Response: {r.json()}")
    except Exception as e:
        print(f"Test failed: {e}")

if __name__ == "__main__":
    test_parse_content()
