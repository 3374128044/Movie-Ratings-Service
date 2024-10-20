from flask import Flask, request, jsonify
import os

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

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
    
    if not is_allowed_extension(file.filename):
        return jsonify({"message":"File type not supported"}),400

    if file and is_allowed_extension(file.filename):
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        return jsonify({"message": f"File '{file.filename}' uploaded successfully!"}), 200


if __name__ == '__main__':
    app.run(debug=True)
