from flask import Flask, render_template, send_file, Response, request
import os
import subprocess

app = Flask(__name__)
ANIME_DIR = "/media/caleb/48DAF95CDAF946AA/backups/Downloads (main)/Anime"

def generate_transcoded_video(path):
    command = [
        'ffmpeg',
        '-i', path,
        '-c:v', 'libx264',
        '-preset', 'ultrafast',
        '-crf', '28',
        '-c:a', 'aac',
        '-f', 'mp4',
        '-movflags', 'frag_keyframe+empty_moov',
        '-'
    ]
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    for chunk in iter(lambda: process.stdout.read(4096), b''):
        yield chunk

@app.route('/')
def index():
    anime_list = []
    try:
        for anime in os.listdir(ANIME_DIR):
            anime_path = os.path.join(ANIME_DIR, anime)
            if os.path.isdir(anime_path):
                icon = next((f for f in os.listdir(anime_path) if f.lower().startswith('icon.')), None)
                anime_list.append({
                    'name': anime,
                    'icon': f'/anime/{anime}/{icon}' if icon else '/static/default-icon.png'
                })
    except Exception as e:
        print(f"Error reading anime directory: {e}")
    return render_template('index.html', anime_list=anime_list)

@app.route('/anime/<path:subpath>')
def serve_anime(subpath):
    try:
        full_path = os.path.join(ANIME_DIR, subpath)
        
        if os.path.isdir(full_path):
            episodes = sorted([f for f in os.listdir(full_path) 
                            if f.lower().endswith(('.mp4', '.mkv', '.avi'))])
            return render_template('player.html', 
                                episodes=episodes, 
                                anime_name=subpath.split('/')[0])
        
        # For direct MP4 files
        if full_path.lower().endswith('.mp4'):
            return send_file(full_path)
        
        # For MKV files (transcode on demand)
        if full_path.lower().endswith('.mkv'):
            return Response(
                generate_transcoded_video(full_path),
                mimetype='video/mp4',
                headers={'Content-Disposition': f'inline; filename="{os.path.basename(full_path)}.mp4"'}
            )
            
        return send_file(full_path)
    except Exception as e:
        print(f"Error serving {subpath}: {e}")
        return "File not found", 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)