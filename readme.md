# Audio Analysis Application
A real-time audio analysis application using Google Cloud's Gemini 1.5 Pro model.

## Live Demo
https://voicellapp.uc.r.appspot.com/

## Prerequisites
- Python 3.9 or higher
- Google Cloud account
- Git

## Local Setup Instructions

### 1. Clone the Repository
```bash
git clone [your-repository-url]
cd audio-analysis-app
```

### 2. Set Up Python Virtual Environment
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# For Windows:
venv\Scripts\activate
# For macOS/Linux:
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

Create requirements.txt with:
```
fastapi==0.68.0
uvicorn==0.15.0
google-cloud-texttospeech==2.8.0
vertexai==1.0.0
pydub==0.25.1
python-multipart==0.0.5
jinja2==3.0.1
python-dotenv==0.19.0
gunicorn==20.1.0
```

### 4. Google Cloud Setup

1. Create a new project in Google Cloud Console
2. Enable these APIs in your project:
   - Vertex AI API
   - Cloud Text-to-Speech API

3. Create service account credentials:
   - Go to Google Cloud Console > IAM & Admin > Service Accounts
   - Create a new service account
   - Download the JSON key file
   - Rename it to 'application_default_credentials.json'
   - Place it in the project root directory

### 5. Environment Configuration

Create a .env file in the project root:
```
GOOGLE_APPLICATION_CREDENTIALS=application_default_credentials.json
PROJECT_ID=your-project-id-here
LOCATION=us-central1
```

### 6. File Structure
Ensure your project structure looks like this:
```
audio-analysis-app/
├── main.py
├── requirements.txt
├── .env
├── application_default_credentials.json
├── static/
│   └── css/
└── templates/
    └── index.html
```

### 7. Run the Application
```bash
# Development server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Access the application at: http://localhost:8000

## Common Issues and Solutions

### Permission Issues
If you encounter permission errors:
1. Verify Google Cloud credentials file path
2. Check service account permissions
3. Ensure all required APIs are enabled

### Audio Recording Issues
If audio recording doesn't work:
1. Use a supported browser (Chrome recommended)
2. Grant microphone permissions
3. Check browser console for errors

### API Rate Limits
If you hit rate limits:
1. Check your quota in Google Cloud Console
2. Implement rate limiting in your application
3. Consider upgrading your Google Cloud account

## Testing the Setup

1. Open http://localhost:8000 in your browser
2. Try recording a short audio clip
3. Try uploading an audio file
4. Check if transcription and analysis work

## Development Notes

- The application uses FastAPI's automatic API documentation
- Access the API docs at http://localhost:8000/docs
- The /health endpoint can be used to verify the server is running

## Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Google Cloud Documentation](https://cloud.google.com/docs)
- [Vertex AI Documentation](https://cloud.google.com/vertex-ai/docs)

## Support

For issues and questions:
1. Check the troubleshooting guide above
2. Review Google Cloud documentation
3. Create an issue in the repository

## Security Notes

- Never commit credentials to version control
- Keep your .env file secure
- Regularly rotate your service account keys
- Monitor your Google Cloud Console for unusual activity