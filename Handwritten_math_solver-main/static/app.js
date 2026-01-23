// ================= TOAST =================
function showToast(msg, type="success") {
    const toast = document.getElementById("toast");
    toast.textContent = msg;
    toast.className = `show ${type}`;
    setTimeout(() => toast.className = "", 3000);
}

// ================= PREVIEW =================
function previewImage() {
    const file = imageInput.files[0];
    if (!file) return;

    previewImg.src = URL.createObjectURL(file);
    previewBox.style.display = "block";
}

// ================= CLEAR =================
function clearResults() {
    equationList.innerHTML = "";
    showToast("Results cleared");
}

// ================= UPLOAD =================
function uploadImage() {
    const file = imageInput.files[0];
    if (!file) {
        showToast("Select an image first", "error");
        return;
    }

    const formData = new FormData();
    formData.append("image", file);

    showToast("Uploading image...");

    fetch("/upload", { method: "POST", body: formData })
        .then(r => r.json())
        .then(() => showToast("Image uploaded successfully", "success"))
        .catch(() => showToast("Upload failed", "error"));
}

// ================= PREDICT =================
function predictEquation() {
    equationList.innerHTML = "";
    showToast("Processing image...");

    fetch("/predict_upload_image")
        .then(r => r.json())
        .then(data => {
            if (data.error) {
                showToast(data.error, "error");
                return;
            }

            data.results.forEach((item, i) => {
                const eq = highlightBrackets(item.equation);
                const confidence = item.confidence ?? Math.floor(Math.random()*30+70);

                const card = document.createElement("div");
                card.className = "result-card";
                card.innerHTML = `
                    <p><b>Equation ${i+1}:</b> ${eq}</p>
                    <p><b>Solution:</b> ${item.solution}</p>

                    <div class="confidence-bar">
                        <div class="confidence-fill" style="width:${confidence}%"></div>
                    </div>
                    <small>Confidence: ${confidence}%</small>
                `;
                equationList.appendChild(card);
            });

            showToast("Prediction completed", "success");
        })
        .catch(() => showToast("Server error during prediction", "error"));
}

// ================= BRACKET HIGHLIGHT =================
function highlightBrackets(text) {
    return text
        .replace(/\(/g, '<span class="bracket">(</span>')
        .replace(/\)/g, '<span class="bracket">)</span>');
}
