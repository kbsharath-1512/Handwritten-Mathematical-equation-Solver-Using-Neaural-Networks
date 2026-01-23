from flask import Flask, render_template, request, jsonify, redirect, url_for
import base64
import io
import os
import cv2
from PIL import Image
from pix2tex.cli import LatexOCR

from equation_calculator import equation_solver_function
from solve_equation_file import solve_equation

app = Flask(__name__)
app.config['SECRET_KEY'] = 'abcdef'
app.config['UPLOAD_FOLDER'] = 'static'

# =========================================================
# Initialize pix2tex ONCE (FIX 1)
# =========================================================
try:
    latex_ocr = LatexOCR()
except Exception as e:
    latex_ocr = None
    print("pix2tex init failed:", e)


# =========================================================
# Normalize OCR output (BRACKETS FIX)
# =========================================================
def normalize_equation(eq):
    if not eq:
        return eq

    eq = eq.replace('[', '(').replace(']', ')')
    eq = eq.replace('{', '(').replace('}', ')')

    if eq.count('|') == 2:
        eq = eq.replace('|', '(', 1).replace('|', ')', 1)
    elif eq.count('|') == 1:
        eq = eq.replace('|', '(')

    return eq.replace(" ", "")


def is_balanced(eq):
    stack = []
    for ch in eq:
        if ch == '(':
            stack.append(ch)
        elif ch == ')':
            if not stack:
                return False
            stack.pop()
    return len(stack) == 0
def latex_to_python(expr):
    if not expr:
        return None

    expr = expr.replace(r"\times", "*")
    expr = expr.replace(r"\cdot", "*")
    expr = expr.replace(r"\div", "/")
    expr = expr.replace(r"\%", "%")
    expr = expr.replace("{", "(").replace("}", ")")
    expr = expr.replace(" ", "")

    return expr


def hybrid_recognize_equation(image_path):
    """
    Returns:
        final_eq (str)
        source ('cnn' or 'pix2tex')
    """

    # 1️⃣ CNN OCR (always)
    cnn_eq = equation_solver_function(image_path)
    cnn_eq = normalize_equation(cnn_eq)

    # 2️⃣ pix2tex OCR (safe, optional)
    pix_eq = None
    if latex_ocr is not None:
        try:
            latex = latex_ocr(image_path)
            pix_eq = latex_to_python(latex)
        except Exception as e:
            print("pix2tex OCR failed:", e)

    # 3️⃣ Selection logic
    if pix_eq and ("(" in pix_eq or ")" in pix_eq):
        return pix_eq, "pix2tex"

    return cnn_eq, "cnn"


# =========================================================
# pix2tex bracket detection (FIX 2)
# =========================================================
def image_has_brackets_pix2tex(image_path):
    if latex_ocr is None:
        return False

    try:
        latex = latex_ocr(image_path)
        print("pix2tex LaTeX:", latex)
        return "(" in latex or ")" in latex
    except Exception as e:
        print("pix2tex error:", e)
        return False


# =========================================================
# Split image into equation lines
# =========================================================
def split_equation_lines(image_path):
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        return [], None

    thresh = cv2.adaptiveThreshold(
        img, 255,
        cv2.ADAPTIVE_THRESH_MEAN_C,
        cv2.THRESH_BINARY_INV,
        15, 5
    )

    projection = thresh.sum(axis=1)
    lines, start = [], None

    for i, val in enumerate(projection):
        if val > 0 and start is None:
            start = i
        elif val == 0 and start is not None:
            if i - start > 10:
                lines.append((start, i))
            start = None

    if start is not None and len(projection) - start > 10:
        lines.append((start, len(projection)))

    return lines, img


# =========================================================
# Extract & solve equations (ONE BY ONE)
# =========================================================
def extract_and_solve_equations(image_path):
    lines, img = split_equation_lines(image_path)
    results = []

    if not lines:
        eq, source = hybrid_recognize_equation(temp_path)


        if not eq:
            return results

        if not is_balanced(eq):
            solution = "Unbalanced brackets"
        else:
            solution = solve_equation(eq.replace("^", "**"))

        return [{"equation": eq, "solution": str(solution)}]

    for idx, (start, end) in enumerate(lines):
        line_img = img[start:end, :]
        if line_img is None or line_img.size == 0:
            continue

        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
        line_img = cv2.dilate(line_img, kernel, iterations=1)

        temp_path = os.path.join(app.config['UPLOAD_FOLDER'], f"temp_eq_{idx}.png")
        cv2.imwrite(temp_path, line_img)

        eq = equation_solver_function(temp_path)
        eq = normalize_equation(eq)
        os.remove(temp_path)

        if not eq:
            continue

        if not is_balanced(eq):
            solution = "Unbalanced brackets"
        else:
            try:
                solution = solve_equation(eq.replace("^", "**"))
            except Exception:
                solution = "Invalid equation"

        results.append({"equation": eq, "solution": str(solution)})

    return results


# =========================================================
# Routes
# =========================================================
@app.route('/')
def index():
    return redirect(url_for('upload_page'))


@app.route('/upload_page')
def upload_page():
    image_path = os.path.join(app.config['UPLOAD_FOLDER'], 'equation.png')
    if os.path.exists(image_path):
        os.remove(image_path)
    return render_template('uploadimage.html')


@app.route('/upload', methods=['POST'])
def upload_file():
    if 'image' not in request.files:
        return jsonify("No image uploaded")

    image_file = request.files['image']
    if image_file.filename == '':
        return jsonify("Empty file")

    save_path = os.path.join(app.config['UPLOAD_FOLDER'], 'equation.png')
    image_file.save(save_path)

    return jsonify("Image uploaded successfully")


@app.route('/canvas_image')
def canvas_image():
    return render_template('canvasimage.html')


@app.route('/save', methods=['POST'])
def save_canvas():
    img_data = request.values.get('canvas_data')
    if not img_data:
        return jsonify("No canvas data")

    img = Image.open(io.BytesIO(base64.b64decode(img_data.split(",")[1])))
    img.convert("RGB").save(os.path.join(app.config['UPLOAD_FOLDER'], 'equation.png'))
    return jsonify("Image saved successfully")


@app.route('/predict_upload_image', methods=['GET', 'POST'])
def predict_upload_image():
    image_path = os.path.join(app.config['UPLOAD_FOLDER'], 'equation.png')

    if not os.path.exists(image_path):
        return jsonify({"error": "No image found"})

    # 🔍 Check brackets using pix2tex (soft check, NOT a blocker)
    brackets_present = image_has_brackets_pix2tex(image_path)

    # Always run extraction
    results = extract_and_solve_equations(image_path)

    if not results:
        return jsonify({"error": "No equations detected"})

    # Add info flag for UI (optional)
    for r in results:
        r["brackets_detected"] = brackets_present

    return jsonify({"results": results})


if __name__ == '__main__':
    app.run(debug=True)
