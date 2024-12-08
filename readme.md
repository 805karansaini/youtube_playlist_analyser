# YouTube Playlist Analyzer

YouTube Playlist Analyzer is a web application designed to help you gain insights into your YouTube playlists. With this tool, you can analyze playlists to determine the number of videos, total duration, and playback speed adjustments, all presented with **interactive charts** to help you visualize the data effectively.

Explore it live here: [YouTube Playlist Analyzer](https://ytanalyser.up.railway.app/)

## Features

- Extract and analyze YouTube playlist information
- Calculate the total duration of playlists
- Estimate watching time at different playback speeds
- User-friendly web interface

## Prerequisites

- Python 3.12
- YouTube Data API key
- Docker (optional)

## Setup

### Local Development

1. Clone the repository:
   ```bash
   git clone https://github.com/805karansaini/youtube_playlist_analyser
   cd youtube_playlist_analyser
   ```

2. Create a virtual environment:
   ```bash
   python3 -m venv .venv
   ```

3. Activate the virtual environment:
      - On Windows:
      ```bash
      .venv\Scripts\activate
      ```
      - On macOS/Linux:
      ```bash
      source .venv/bin/activate
      ```

4. Create a `.env` file with your YouTube API key:
   ```bash
   cp .env.example .env
   ```
   Then, open the `.env` file and add your YouTube API key:
   ```
   YOUTUBE_API_KEY=your_api_key_here
   ```

5. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

6. Run the application:
   ```bash
   python app/main.py
   ```
   or
   ```bash
   cd app
   gunicorn --bind 0.0.0.0:5000 main:app
   ```

### Docker Deployment

1. Build the Docker image:
   ```bash
   docker build -t youtube-playlist-analyser .
   ```

2. Run the container:
   ```bash
   docker run -p 5000:5001 youtube-playlist-analyser
   ```

## Usage

1. Access the application at `http://localhost:5000`.
2. Enter a YouTube playlist URL.
3. View the analysis results, including:
      - Total number of videos
      - Average video length
      - Total playlist duration
      - Estimated watching time at different speeds

## Documentation

Documentation is built using MkDocs. To view the documentation locally:

```bash
mkdocs serve
```

You can also view the documentation online at: [https://805karansaini.github.io/youtube_playlist_analyser/](https://805karansaini.github.io/youtube_playlist_analyser/)
