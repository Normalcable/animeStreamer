# --- START OF FILE app.py ---

# Make sure to run: pip install Flask
from flask import Flask, render_template, send_file, Response, request, jsonify, redirect, url_for
import os
import subprocess
import json             # <-- Import json
from datetime import datetime # <-- Import datetime
import re               # <-- Import re for sanitizing filenames

app = Flask(__name__)

# --- Configuration ---
# IMPORTANT: Make sure this path is correct for YOUR system
ANIME_DIR = "/media/caleb/48DAF95CDAF946AA/backups/Downloads (main)/Anime"
# Creates a 'comments' directory next to your app.py file
COMMENTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'comments')

# --- Ensure comments directory exists ---
if not os.path.exists(COMMENTS_DIR):
    try:
        os.makedirs(COMMENTS_DIR)
        print(f"Created comments directory: {COMMENTS_DIR}")
    except OSError as e:
        print(f"Error creating comments directory {COMMENTS_DIR}: {e}")

# --- Helper function to sanitize anime name for filename ---
def sanitize_filename(name):
    name = name.replace(" ", "_")
    name = re.sub(r'[^\w\-\.]+', '', name)
    if name in ['.', '..']:
        return '_'
    return name[:100]

# --- Helper function to get comment file path ---
def get_comment_file_path(anime_name):
    safe_name = sanitize_filename(anime_name)
    if not safe_name:
        safe_name = "unknown_anime"
    return os.path.join(COMMENTS_DIR, f"{safe_name}.json")

# --- Helper function to load comments ---
def load_comments(anime_name):
    filepath = get_comment_file_path(anime_name)
    if os.path.exists(filepath):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                if not content: return []
                return json.loads(content)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error loading comments for '{anime_name}' from {filepath}: {e}")
            return []
        except Exception as e:
             print(f"Unexpected error loading comments for '{anime_name}': {e}")
             return []
    return []

# --- Helper function to save comments ---
def save_comments(anime_name, comments):
    filepath = get_comment_file_path(anime_name)
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(comments, f, indent=4, ensure_ascii=False)
        return True
    except IOError as e:
        print(f"Error saving comments for '{anime_name}' to {filepath}: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error saving comments for '{anime_name}': {e}")
        return False

# --- Video Transcoding ---
def generate_transcoded_video(path):
    try:
        subprocess.run(['ffmpeg', '-version'], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except (FileNotFoundError, subprocess.CalledProcessError):
        print("ERROR: ffmpeg not found or not executable. Transcoding will fail.")
        yield b''
        return

    command = [
        'ffmpeg', '-i', path, '-c:v', 'libx264', '-preset', 'ultrafast',
        '-crf', '28', '-c:a', 'aac', '-b:a', '128k',
        '-movflags', 'frag_keyframe+empty_moov', '-f', 'mp4', '-'
    ]
    print(f"Running ffmpeg command: {' '.join(command)}")
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    stderr_output = process.stderr.read().decode('utf-8', errors='ignore')
    if stderr_output:
         print(f"ffmpeg stderr for {os.path.basename(path)}:\n{stderr_output}")

    while True:
        chunk = process.stdout.read(4096)
        if not chunk: break
        yield chunk

    process.stdout.close()
    process.wait()
    if process.returncode != 0:
        print(f"ffmpeg process for {os.path.basename(path)} exited with error code {process.returncode}")


# =============================================
# --- Index Route (MODIFIED) ---
# =============================================
@app.route('/')
def index():
    anime_list = []
    error_message = None # Initialize error message

    if not os.path.isdir(ANIME_DIR):
         error_message = f"Anime directory not found: {ANIME_DIR}"
         print(f"Error: ANIME_DIR '{ANIME_DIR}' not found or is not a directory.")
         return render_template('index.html', anime_list=anime_list, error_message=error_message)

    try:
        # Iterate through items in the ANIME_DIR
        for entry in os.scandir(ANIME_DIR):
            # Check if it's a directory
            if entry.is_dir():
                anime_name = entry.name
                anime_path = entry.path
                icon_filename = None # Reset icon for each anime

                # Try to find an icon file inside the anime directory
                try:
                    for item in os.scandir(anime_path):
                        # Check if it's a file and starts with 'icon.' (case-insensitive)
                        if item.is_file() and item.name.lower().startswith('icon.'):
                            icon_filename = item.name # Store the found icon filename
                            break # Found one, no need to look further
                except OSError as e:
                    print(f"Error reading directory {anime_path} for icon: {e}")
                    # Skip this anime if we can't read its directory
                    continue

                # --- CORE CHANGE: Only add to list IF icon_filename was found ---
                if icon_filename is not None:
                    anime_list.append({
                        'name': anime_name,
                        # Construct the URL using the found icon filename
                        'icon': url_for('serve_anime', subpath=f'{anime_name}/{icon_filename}')
                    })
                # --- End of CORE CHANGE ---

        # Sort the final list alphabetically
        anime_list.sort(key=lambda x: x['name'])

    except OSError as e:
        error_message = "Error reading the main anime directory."
        print(f"Error reading anime directory {ANIME_DIR}: {e}")
    except Exception as e:
        error_message = "An unexpected error occurred while listing anime."
        import traceback
        print(f"Unexpected error in index route: {e}\n{traceback.format_exc()}")

    # Render the template with the filtered list and any potential error message
    return render_template('index.html', anime_list=anime_list, error_message=error_message)
# =============================================
# --- End of Index Route Modification ---
# =============================================


# --- Serve Anime Route (Files and Player Page) ---
@app.route('/anime/<path:subpath>')
def serve_anime(subpath):
    try:
        requested_path = os.path.abspath(os.path.join(ANIME_DIR, subpath))
        if not requested_path.startswith(os.path.abspath(ANIME_DIR)):
             print(f"Forbidden path access attempt: {subpath}")
             return "Forbidden", 403

        full_path = requested_path

        if not os.path.exists(full_path):
             print(f"Path does not exist: {full_path} (from subpath: {subpath})")
             return "Not Found", 404

        path_parts = subpath.split(os.sep, 1)
        anime_name_from_path = path_parts[0] if path_parts else "Unknown Anime"

        if os.path.isdir(full_path):
            episodes = []
            try:
                episodes = sorted([
                    f.name for f in os.scandir(full_path)
                    if f.is_file() and f.name.lower().endswith(('.mp4', '.mkv', '.avi'))
                ])
            except OSError as e:
                print(f"Error listing episodes in directory {full_path}: {e}")

            comments = load_comments(anime_name_from_path)
            print(f"Rendering player for anime: {anime_name_from_path}")
            return render_template('player.html',
                                episodes=episodes,
                                anime_name=anime_name_from_path,
                                comments=comments)

        elif os.path.isfile(full_path):
            print(f"Serving file: {full_path}")
            if full_path.lower().endswith('.mp4'):
                return send_file(full_path, mimetype='video/mp4')

            if full_path.lower().endswith(('.mkv', '.avi')):
                return Response(
                    generate_transcoded_video(full_path),
                    mimetype='video/mp4',
                    headers={'Content-Disposition': f'inline; filename="{os.path.basename(full_path)}.mp4"'}
                )

            from mimetypes import guess_type
            mimetype = guess_type(full_path)[0] or 'application/octet-stream'
            return send_file(full_path, mimetype=mimetype)

        else:
            print(f"Path is neither file nor directory: {full_path}")
            return "Invalid Path", 400

    except Exception as e:
        import traceback
        print(f"!!! Unexpected Error serving subpath '{subpath}' !!!")
        print(traceback.format_exc())
        if app.debug:
             return f"Server Error: {e}", 500
        else:
             return "Internal Server Error", 500


# --- Add Comment Route ---
@app.route('/add_comment', methods=['POST'])
def add_comment():
    if request.method == 'POST':
        try:
            name = request.form.get('name', '').strip()
            comment_text = request.form.get('comment', '').strip()
            anime_name = request.form.get('anime_name', '').strip()

            if not name: return jsonify({'success': False, 'error': 'Name is required.'}), 400
            if not comment_text: return jsonify({'success': False, 'error': 'Comment cannot be empty.'}), 400
            if not anime_name:
                print("Error: 'anime_name' missing from comment submission.")
                return jsonify({'success': False, 'error': 'Anime identifier missing. Cannot save comment.'}), 400
            if len(name) > 50: return jsonify({'success': False, 'error': 'Name cannot exceed 50 characters.'}), 400
            if len(comment_text) > 1000: return jsonify({'success': False, 'error': 'Comment cannot exceed 1000 characters.'}), 400
            if len(anime_name) > 100: return jsonify({'success': False, 'error': 'Invalid anime identifier.'}), 400

            comments = load_comments(anime_name)
            new_comment = {
                'name': name,
                'comment': comment_text,
                'timestamp': datetime.utcnow().isoformat() + "Z"
            }
            comments.append(new_comment)

            if save_comments(anime_name, comments):
                print(f"Comment added successfully for anime: {anime_name}")
                return jsonify({'success': True, 'comment': new_comment})
            else:
                print(f"Failed to save comment for anime: {anime_name}")
                return jsonify({'success': False, 'error': 'Failed to save comment due to a server error.'}), 500

        except Exception as e:
            import traceback
            print(f"!!! Error processing comment for anime '{request.form.get('anime_name')}' !!!")
            print(traceback.format_exc())
            return jsonify({'success': False, 'error': 'Server error processing comment.'}), 500
    else:
        return jsonify({'success': False, 'error': 'Method Not Allowed'}), 405


# --- Run App ---
if __name__ == '__main__':
    if not os.path.isdir(ANIME_DIR):
         print("="*50)
         print(f"WARNING: ANIME_DIR '{ANIME_DIR}' does not exist or is not a directory.")
         print("Please ensure the path is correct and the directory exists.")
         print("="*50)
    app.run(host='0.0.0.0', port=5000, debug=True)

# --- END OF FILE app.py ---