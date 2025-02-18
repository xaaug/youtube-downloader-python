from flask import Flask, request, jsonify, send_file
from yt_dlp import YoutubeDL
import os

from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes


# Directory to save downloads
DOWNLOAD_DIR = "downloads"
if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)
    

@app.route("/info", methods=["POST"])
def get_video_info():
    data = request.json
    url = data.get("url")

    if not url:
        return jsonify({"error": "URL is required"}), 400

    try:
        ydl_opts = {
            'format': 'best',  # Fetch all formats
            'quiet': True,     # Suppress output
        }
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            formats = info.get('formats', [])
            resolutions = sorted(
                {f.get('format_note') for f in formats if f.get('format_note')},
                key=lambda x: int(x[:-1]) if x and x[:-1].isdigit() else 0,
                reverse=True
            )
            return jsonify({
                "title": info.get("title"),
                "thumbnail": info.get("thumbnail"),
                "resolutions": resolutions,
            })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/download", methods=["POST"])
def download_video():
    data = request.json
    url = data.get("url")
    resolution = data.get("resolution")

    print(resolution)
    if not url or not resolution:
        return jsonify({"error": "URL and resolution are required"}), 400

    try:
        ydl_opts = {
    'format': f'bestvideo[height<={resolution}]+bestaudio/best[height<={resolution}]',
           'outtmpl': f'{DOWNLOAD_DIR}/%(title)s.%(ext)s',
    'merge_output_format': 'mp4',  # Merge into MP4 format
}
    
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info).replace('.webm', '.mp3').replace('.m4a', '.mp3')
            return jsonify({
                "title": info.get("title"),
                "message": "Download successful",
                "filename": os.path.basename(filename),
            })
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    

@app.route("/stream/<filename>", methods=["GET"])
def stream_file(filename):
    file_path = os.path.join(DOWNLOAD_DIR, filename)
    if not os.path.exists(file_path):
        return jsonify({"error": "File not found"}), 404

    # Stream the file and delete it afterward
        
    return send_file(file_path, as_attachment=True)

@app.route("/delete/<filename>", methods=["DELETE"])
def delete_file(filename):
    file_path = os.path.join(DOWNLOAD_DIR, filename)

    if os.path.exists(file_path):
        try:
            os.remove(file_path)
            return jsonify({"message": f"File '{filename}' deleted successfully"}), 200
        except Exception as e:
            return jsonify({"error": f"Failed to delete file: {str(e)}"}), 500
    else:
        return jsonify({"error": "File not found"}), 404

if __name__ == "__main__":
    app.run(debug=True)