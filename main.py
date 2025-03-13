from flask import Flask, render_template, request, flash, redirect
from werkzeug.utils import secure_filename
import os
import cv2


UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'webp', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}

app = Flask(__name__)
app.secret_key = 'super secret key'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def processImage(filename,operation):
    print(f"the operation is{operation} and filename is{filename}")
    img =cv2.imread(f"uploads/{filename}")
    match operation:
        case "cgray":
            imgprocessed =cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            newFilename= f"static/{filename}"
            cv2.imwrite(newFilename, imgprocessed)
            return newFilename
        
        case "cjpg":
            newFilename= f"static/{filename.rsplit('.',1)[0]}.jpg"
            cv2.imwrite(newFilename, img)
            return newFilename
        case "cpng":
            newFilename= f"static/{filename.rsplit('.',1)[0]}.png"
            cv2.imwrite(newFilename, img)
            return newFilename
        case "cwebp":
            newFilename= f"static/{filename.rsplit('.',1)[0]}.webp"
            cv2.imwrite(newFilename, img)
            return newFilename


@app.route("/")
def hello_world():
    return render_template("index.html")  # Ensure this file exists inside the "templates" folder
@app.route("/about")
def hello():
    return render_template("about.html")  # Ensure this file exists inside the "templates" folder

@app.route("/edit", methods=["Get","POST"])
def Edite():
    if request.method=="POST":
        operation = request.form.get("operation") # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # If the user does not select a file, the browser submits an
        # empty file without a filename.
        if file.filename == '':
            flash('No selected file')
            return "error no selected file"
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            new = processImage(filename,operation)
            flash(f"your image has been processed and is available <a href='/{new}' target='_blank'>here</a>")
            return render_template("index.html")  
    return render_template("index.html")  


if __name__ == "__main__":  # Best practice to run the app
    app.run(debug=True)
