# Anime Streamer

A simple and small project web application built with Flask to browse and stream your local anime collection directly in your browser, including a basic commenting system per anime series.

## Features

*   **Browse Local Collection:** Displays anime found in your configured directory. **Requires an icon file in each anime folder to be listed.**
*   **MP4 Video Streaming:** Plays `.mp4` files directly in the browser. **Other video formats are not supported for playback.**
*   **Episode Listing:** Automatically lists `.mp4` video files found within each anime's directory on the player page.
*   **Simple Commenting:** Allows users to leave comments (Name + Comment) on each anime page. Comments are stored locally in JSON files.
*   **Download Link:** Provides a direct download link for the currently playing `.mp4` episode.
*   **Configurable:** Set your main anime directory easily in the `app.py` file.

## Screenshots

**Main Library Page:**
*(Showing the grid view of available anime)*
![Main Anime Library Page](https://github.com/user-attachments/assets/deb9ad1b-4322-4d27-aeb0-66f00d4660c6)

**Anime Player Page:**
*(Showing the video player, episode list, and comment section)*
![Anime Player Page](https://github.com/user-attachments/assets/d281f38b-4c5f-4936-b3e6-0f8c81c56269)

## Requirements

*   **Python 3.7+**
*   **Flask:** (`pip install Flask`)

## Setup & Installation

1.  **Clone the Repository:**
    ```bash
    git clone <your-repository-url>
    cd <repository-folder>
    ```
2.  **Install Flask:**
    ```bash
    pip install Flask
    # or if you have a requirements.txt
    # pip install -r requirements.txt
    ```
3.  **Create Comments Directory:** The application needs a place to store comment files. Create it in the project root:
    ```bash
    mkdir comments
    ```
    (The application will try to create this automatically if it doesn't exist).

## Configuration

1.  **Set Anime Directory:** Open the `app.py` file and modify the `ANIME_DIR` variable to point to the **absolute path** of your main anime library folder:
    ```python
    # In app.py
    ANIME_DIR = "/path/to/your/anime/collection" # <--- CHANGE THIS
    ```
2.  **Prepare Anime Folders & Icons:**
    *   Ensure your `ANIME_DIR` contains subdirectories, where each subdirectory represents one anime series.
    *   **IMPORTANT:** For an anime series to be displayed on the main page and function correctly, you **must** place an icon file inside its folder. Name the icon file starting with `icon.` followed by a common image extension (e.g., `icon.jpg`, `icon.png`, `icon.webp`).
        *   Example: `/path/to/your/anime/collection/Attack on Titan/icon.png`
    *   Video files (episodes) **must be in MP4 format (`.mp4`)** and placed directly inside their respective anime series folders (e.g., `/path/to/your/anime/collection/Attack on Titan/S01E01.mp4`).

## Running the Application

1.  Navigate to the project directory in your terminal.
2.  Run the Flask application:
    ```bash
    python app.py
    ```
3.  Open your web browser and go to: `http://localhost:5000` or `http://<your-server-ip>:5000` if accessing from another device on your network.

**Note:** The application runs in debug mode by default (`debug=True`). For any kind of deployment or long-term use, set `debug=False` in the `app.run()` call in `app.py`.

## How It Works

*   **Backend:** Flask handles routing, serving `.mp4` video files and static assets (CSS, JS, icons), and comment loading/saving.
*   **Frontend:** Standard HTML, CSS, and vanilla JavaScript for the user interface, video player control, and comment submission via `fetch`.
*   **Comments Storage:** Comments are stored as simple `.json` files within the `comments/` directory, with one JSON file per anime series.

## Future Improvements

*   User accounts and authentication.
*   Tracking watched status for episodes.
*   Database integration (e.g., SQLite) for comments and metadata instead of JSON files.
*   Implementing the "Download All (ZIP)" feature.
*   Search and filtering functionality for the library.
*   More robust error handling and logging.
*   Improved UI/UX.
*   Client-side subtitle support (e.g., using `<track>` elements with VTT files).
