from flask import Flask, request, jsonify
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024

# create path if not exist
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

ALLOW_EXTENSION = {'txt', 'pdf', 'doc', 'docx', 'pptx'}

# check if the file type is allowed
def is_allowed_extension(filename):
    extension = filename.split('.')[-1]
    extension = extension.lower()

    return extension in ALLOW_EXTENSION

# upload file
@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"message": "No file part in the request"}), 400
    file = request.files['file']

    if file.filename == "":
        return jsonify({"message": "No file selected for uploading"}), 400

    # use secure filename
    if file and is_allowed_extension(file.filename):
        file.filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filepath)
        return jsonify({"message": f"File '{file.filename}' uploaded successfully!"}), 200
    else:
        return jsonify({"message": "File type not supported"}), 400


if __name__ == '__main__':
    app.run(debug=True)
