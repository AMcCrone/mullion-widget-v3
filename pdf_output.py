import io

def get_pdf_bytes(fig):
    buffer = io.BytesIO()
    fig.write_image(buffer, format="pdf")
    buffer.seek(0)
    return buffer.getvalue()
