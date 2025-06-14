# Project Structure

The project follows a clean and organized directory structure:

```
└── 805karansaini-youtube_playlist_analyser
    ├── app/                         # Main application directory
    │   ├── core/                    # Core configurations
    │   ├── exceptions/              # Custom exceptions
    │   ├── helper/                  # Helper utilities
    │   ├── routes/                  # API routes
    │   ├── services/                # Service layer
    │   ├── static/                  # Static assets
    │   ├── templates/               # HTML templates
    │   └── main.py                  # Application entry point
    │
    ├── docs/                        # Documentation
    │   ├── reference/               # API reference docs
    │   └── index.md                 # Documentation home
    │
    ├── .env.example                 # Environment variables template
    ├── Dockerfile                   # Docker configuration
    ├── docker-compose.yaml          # Docker compose setup
    ├── mkdocs.yml                   # Documentation configuration
    ├── Procfile                     # Heroku deployment config
    ├── readme.md                    # Project readme
    ├── requirements.txt             # Python dependencies
    └── vercel.json                  # Vercel deployment config
```

## Key Components

- `app/`: Contains the core application logic
- `docs/`: Houses project documentation
- `Dockerfile` & `docker-compose.yaml`: Container configurations
- Configuration files for various deployment platforms
