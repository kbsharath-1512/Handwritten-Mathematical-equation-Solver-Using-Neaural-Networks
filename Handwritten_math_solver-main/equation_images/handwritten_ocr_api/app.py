
API_KEY = "K83521503888957"
from flask import Flask, render_template, request
import requests
import re
import os
import sympy as sp

app = Flask(__name__)

# 🔑 PUT YOUR OCR.SPACE API KEY HERE



# ---------- CLEAN OCR TEXT ----------
def clean_expression(text):
    text = text.replace(" ", "")
    text = text.replace("÷", "/").replace("×", "*")
    text = text.replace("²", "**2").replace("³", "**3")

    # 🔥 FIX: replace y' with p
    text = text.replace("y'", "p")

    return text


def normalize_multiplication(expr):
    # 2p -> 2*p
    expr = re.sub(r'(\d)([a-zA-Z])', r'\1*\2', expr)
    return expr


def fix_quadratic(expr):
    """
    Fix:
    p+2*p+1=0 -> p**2+2*p+1=0
    """
    if "=0" in expr and "**" not in expr:
        if expr.count("p") >= 2:
            expr = re.sub(r'^p(?=[+\-])', 'p**2', expr)
    return expr



# ---------- SOLVER ----------
def solve_expression(expr):
    p = sp.symbols("p")

    if "=" in expr:
        left, right = expr.split("=")
        equation = sp.Eq(sp.sympify(left), sp.sympify(right))
        return sp.solve(equation, p)

    return eval(expr)


# ---------- ROUTE ----------
@app.route("/", methods=["GET", "POST"])
def index():
    ocr_text = ""
    cleaned_expr = ""
    result = ""
    error = ""
    file_status = ""

    if request.method == "POST":
        if "image" not in request.files:
            error = "No file uploaded"
            return render_template("index.html", error=error)

        image = request.files["image"]

        if image.filename == "":
            error = "No file selected"
            return render_template("index.html", error=error)

        file_status = f"File received: {image.filename}"

        # Detect file type
        ext = os.path.splitext(image.filename)[1].replace(".", "").lower()
        if ext not in ["jpg", "jpeg", "png", "bmp", "tiff"]:
            error = "Unsupported image format"
            return render_template("index.html", error=error)

        # OCR request
        url = "https://api.ocr.space/parse/image"
        payload = {
            "apikey": API_KEY,
            "language": "eng",
            "ocrengine": 2,
            "scale": True,
            "filetype": ext
        }

        response = requests.post(
            url,
            files={"file": image},
            data=payload
        )

        data = response.json()

        if data.get("IsErroredOnProcessing"):
            error = data.get("ErrorMessage")
        else:
            parsed = data.get("ParsedResults")
            if not parsed:
                error = "No text detected"
            else:
                ocr_text = parsed[0].get("ParsedText", "")

                cleaned_expr = clean_expression(ocr_text)
                cleaned_expr = normalize_multiplication(cleaned_expr)
                cleaned_expr = fix_quadratic(cleaned_expr)  

                try:
                    result = solve_expression(cleaned_expr)
                except Exception:
                    result = "Invalid Equation"

    return render_template(
        "index.html",
        ocr_text=ocr_text,
        cleaned_expr=cleaned_expr,
        result=result,
        error=error,
        file_status=file_status
    )


if __name__ == "__main__":
    app.run(debug=True)
