from flask import Flask, request, jsonify
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 10*1024 * 1024

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

ALLOW_EXTENSION = {'txt', 'pdf', 'doc', 'docx'}


def is_allowed_extension(filename):
    extension = filename.split('.')[-1]
    extension = extension.lower()

    return extension in ALLOW_EXTENSION


@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"message": "No file part in the request"}), 400
    file = request.files['file']

    if file.filename == "":
        return jsonify({"message": "No file selected for uploading"}), 400

    filename = secure_filename(file.filename)
    if file and is_allowed_extension(filename):
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        return jsonify({"message": f"File '{filename}' uploaded successfully!"}), 200
    else:
        return jsonify({"message": "File type not supported"}), 400


if __name__ == '__main__':
    app.run(debug=True)
