from flask import (
    Flask,
    render_template,
    request,
    flash,
    redirect,
    send_from_directory
)
from werkzeug.utils import secure_filename

import os
import cv2
import uuid

from rembg import remove
from PIL import Image

# =========================
# Flask App
# =========================

app = Flask(__name__)
app.secret_key = "supersecretkey"

# =========================
# Folders
# =========================

UPLOAD_FOLDER = "uploads"
PROCESSED_FOLDER = "static/processed"

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["PROCESSED_FOLDER"] = PROCESSED_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024

# =========================
# Allowed Extensions
# =========================

ALLOWED_EXTENSIONS = {
    "png",
    "jpg",
    "jpeg",
    "webp"
}

# =========================
# Create Folders
# =========================

os.makedirs(
    UPLOAD_FOLDER,
    exist_ok=True
)

os.makedirs(
    PROCESSED_FOLDER,
    exist_ok=True
)

# =========================
# Allowed File Check
# =========================

def allowed_file(filename):

    return "." in filename and \
           filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# =========================
# Image Processing Function
# =========================

def process_image(
    filepath,
    operation,
    brightness=50,
    contrast=1,
    width=None,
    height=None,
    bgfilepath=None
):

    print("Processing image...")
    print("Operation:", operation)

    img = cv2.imread(filepath)

    if img is None:
        print("Image not loaded")
        return None

    # =========================
    # Resize (Optional)
    # =========================

    if width and height:
        try:
            width = int(width)
            height = int(height)

            if width > 0 and height > 0:
                img = cv2.resize(
                    img,
                    (width, height)
                )
        except:
            print("Resize skipped")

    # Unique output filename
    unique_name = f"{uuid.uuid4()}.png"

    output_path = os.path.join(
        PROCESSED_FOLDER,
        unique_name
    )

    try:

        # =========================
        # GrayScale
        # =========================

        if operation == "cgray":

            processed = cv2.cvtColor(
                img,
                cv2.COLOR_BGR2GRAY
            )

        # =========================
        # Brightness & Contrast
        # =========================

        elif operation == "brightness":

            processed = cv2.convertScaleAbs(
                img,
                alpha=float(contrast),
                beta=int(brightness) - 50
            )

        # =========================
        # Blur
        # =========================

        elif operation == "blur":

            processed = cv2.GaussianBlur(
                img,
                (15, 15),
                0
            )

        # =========================
        # Edge Detection
        # =========================

        elif operation == "edge":

            processed = cv2.Canny(
                img,
                100,
                200
            )

        # =========================
        # Rotate
        # =========================

        elif operation == "rotate":

            processed = cv2.rotate(
                img,
                cv2.ROTATE_90_CLOCKWISE
            )

        # =========================
        # Cartoon Filter
        # =========================

        elif operation == "cartoon":

            gray = cv2.cvtColor(
                img,
                cv2.COLOR_BGR2GRAY
            )

            gray = cv2.medianBlur(
                gray,
                5
            )

            edges = cv2.adaptiveThreshold(
                gray,
                255,
                cv2.ADAPTIVE_THRESH_MEAN_C,
                cv2.THRESH_BINARY,
                9,
                9
            )

            color = cv2.bilateralFilter(
                img,
                9,
                250,
                250
            )

            processed = cv2.bitwise_and(
                color,
                color,
                mask=edges
            )

        # =========================
        # Pencil Sketch
        # =========================

        elif operation == "sketch":

            gray = cv2.cvtColor(
                img,
                cv2.COLOR_BGR2GRAY
            )

            invert = 255 - gray

            blur = cv2.GaussianBlur(
                invert,
                (21, 21),
                0
            )

            inverted_blur = 255 - blur

            processed = cv2.divide(
                gray,
                inverted_blur,
                scale=256.0
            )

        # =========================
        # HDR Effect
        # =========================

        elif operation == "hdr":

            processed = cv2.detailEnhance(
                img,
                sigma_s=12,
                sigma_r=0.15
            )

        # =========================
        # Remove Background
        # =========================

        elif operation == "removebg":

            input_image = Image.open(filepath)

            output_image = remove(input_image)

            output_image.save(output_path)

            return output_path

        # =========================
        # Replace Background
        # =========================

        elif operation == "replacebg":

            if bgfilepath is None:
                print("Background image not provided")
                return None

            input_image = Image.open(filepath)

            removed_bg = remove(input_image)

            foreground = removed_bg.convert(
                "RGBA"
            )

            background = Image.open(
                bgfilepath
            ).convert("RGBA")

            background = background.resize(
                foreground.size
            )

            final_image = Image.alpha_composite(
                background,
                foreground
            )

            final_image.save(output_path)

            return output_path

        # =========================
        # Convert PNG
        # =========================

        elif operation == "cpng":

            processed = img

        # =========================
        # Convert JPG
        # =========================

        elif operation == "cjpg":

            output_path = output_path.replace(
                ".png",
                ".jpg"
            )

            processed = img

        # =========================
        # Convert WEBP
        # =========================

        elif operation == "cwebp":

            output_path = output_path.replace(
                ".png",
                ".webp"
            )

            processed = img

        else:

            print("Invalid operation")
            return None

        # =========================
        # Save Processed Image
        # =========================

        cv2.imwrite(
            output_path,
            processed
        )

        return output_path

    except Exception as e:

        print("PROCESS ERROR:", e)
        return None


# =========================
# Routes
# =========================

@app.route("/")
def home():

    return render_template("index.html")


@app.route("/about")
def about():

    return render_template("about.html")


@app.route("/contact")
def contact():

    return render_template("contact.html")


@app.route("/how")
def how():

    return render_template("how.html")


# =========================
# Serve Uploaded Files
# =========================

@app.route("/uploads/<path:filename>")
def uploaded_file(filename):

    return send_from_directory(
        app.config["UPLOAD_FOLDER"],
        filename
    )


# =========================
# Edit Route
# =========================

@app.route("/edit", methods=["POST"])
def edit():

    print("Edit route called")

    # Check uploaded file
    if "file" not in request.files:

        flash(
            "No file uploaded",
            "danger"
        )

        return redirect("/")

    file = request.files["file"]

    if file.filename == "":

        flash(
            "No selected file",
            "danger"
        )

        return redirect("/")

    # Validate file type
    if file and allowed_file(file.filename):

        # Save main image
        filename = secure_filename(
            file.filename
        )

        filepath = os.path.join(
            app.config["UPLOAD_FOLDER"],
            filename
        )

        file.save(filepath)

        # Read form data
        operation = request.form.get(
            "operation"
        )

        brightness = request.form.get(
            "brightness",
            50
        )

        contrast = request.form.get(
            "contrast",
            1
        )

        width = request.form.get(
            "width"
        )

        height = request.form.get(
            "height"
        )

        # Optional background image
        bgfilepath = None

        if "bgfile" in request.files:

            bgfile = request.files["bgfile"]

            if bgfile.filename != "" and allowed_file(bgfile.filename):

                bgfilename = secure_filename(
                    bgfile.filename
                )

                bgfilepath = os.path.join(
                    app.config["UPLOAD_FOLDER"],
                    bgfilename
                )

                bgfile.save(bgfilepath)

        # Process image
        processed_path = process_image(
            filepath,
            operation,
            brightness,
            contrast,
            width,
            height,
            bgfilepath
        )

        if processed_path:

            flash(
                "Image processed successfully!",
                "success"
            )

            # This path will be served by /uploads/<filename>
            original_image = "/" + filepath.replace(
                "\\",
                "/"
            )

            return render_template(
                "index.html",
                processed_image=processed_path,
                original_image=original_image
            )

        else:

            flash(
                "Something went wrong",
                "danger"
            )

            return redirect("/")

    # Invalid file type
    flash(
        "Invalid file type",
        "danger"
    )

    return redirect("/")


# =========================
# Run App
# =========================

if __name__ == "__main__":

    app.run(
        debug=True
    )