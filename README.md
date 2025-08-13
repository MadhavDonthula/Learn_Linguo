# Learn Linguo - Language Learning Platform

Learn Linguo is a Django-based web application designed to help students learn languages through interactive assignments, flashcards, and interpersonal speaking exercises. The platform supports French and Spanish language learning with AI-powered speech recognition and evaluation.

## Features

### 🎯 Core Features
- **Interactive Language Assignments**: Create and complete speaking assignments with AI evaluation
- **Flashcard System**: Study vocabulary with audio pronunciation and progress tracking
- **Interpersonal Sessions**: Practice conversational skills with AI-powered feedback
- **Class Management**: Organize students into classes with unique codes
- **Progress Tracking**: Monitor student progress across assignments and flashcard sets
- **Audio Recording**: Record and transcribe speech using OpenAI's Whisper model
- **AI Evaluation**: Get instant feedback on pronunciation and language accuracy

### 🛠 Technical Features
- **Speech Recognition**: Powered by OpenAI's Whisper API
- **AI Evaluation**: Custom prompts for language assessment
- **Cloud Storage**: Audio files stored on Backblaze B2
- **Database**: PostgreSQL for production, SQLite for development
- **User Authentication**: Django's built-in authentication system
- **Responsive Design**: Modern UI with CSS and JavaScript

## Tech Stack

- **Backend**: Django 5.0
- **Database**: PostgreSQL (production), SQLite (development)
- **AI/ML**: OpenAI API (Whisper for transcription, GPT for evaluation)
- **Cloud Storage**: Backblaze B2 (S3-compatible)
- **Frontend**: HTML, CSS, JavaScript
- **Deployment**: Vercel-ready configuration

## Installation

### Prerequisites
- Python 3.8+
- pip
- PostgreSQL (for production)

### Setup Instructions

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd Learn_Linguo-1
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` file with your actual values:
   ```env
   # Django Settings
   DJANGO_SECRET_KEY=your-django-secret-key-here
   DEBUG=True
   
   # Database
   DATABASE_URL=postgresql://username:password@host:port/database_name
   
   # OpenAI API
   OPENAI_API_KEY=your-openai-api-key-here
   
   # AWS/B2 Cloud Storage Settings
   AWS_ACCESS_KEY_ID=your-aws-access-key-id
   AWS_SECRET_ACCESS_KEY=your-aws-secret-access-key
   AWS_STORAGE_BUCKET_NAME=your-bucket-name
   AWS_S3_ENDPOINT_URL=https://s3.us-west-004.backblazeb2.com
   AWS_S3_REGION_NAME=us-west-002
   ```

5. **Run database migrations**
   ```bash
   python manage.py migrate
   ```

6. **Create a superuser**
   ```bash
   python manage.py createsuperuser
   ```

7. **Run the development server**
   ```bash
   python manage.py runserver
   ```

8. **Access the application**
   - Main app: http://localhost:8000
   - Admin panel: http://localhost:8000/admin

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `DJANGO_SECRET_KEY` | Django secret key for security | Yes |
| `DEBUG` | Enable/disable debug mode | Yes |
| `DATABASE_URL` | Database connection string | Yes |
| `OPENAI_API_KEY` | OpenAI API key for speech recognition | Yes |
| `AWS_ACCESS_KEY_ID` | Backblaze B2 access key | Yes |
| `AWS_SECRET_ACCESS_KEY` | Backblaze B2 secret key | Yes |
| `AWS_STORAGE_BUCKET_NAME` | B2 bucket name | Yes |
| `AWS_S3_ENDPOINT_URL` | B2 S3-compatible endpoint | Yes |
| `AWS_S3_REGION_NAME` | B2 region name | Yes |

## Project Structure

```
Learn_Linguo-1/
├── voice_transcription/          # Django project settings
│   ├── settings.py              # Main settings file
│   ├── urls.py                  # Project URL configuration
│   └── wsgi.py                  # WSGI configuration
├── transcription/               # Main Django app
│   ├── models.py               # Database models
│   ├── views.py                # View functions
│   ├── forms.py                # Django forms
│   ├── admin.py                # Admin interface
│   ├── urls.py                 # App URL configuration
│   └── templates/              # HTML templates
├── static/                     # Static files (CSS, JS, images)
├── interpersonal_questions/    # Audio question files
├── requirements.txt            # Python dependencies
├── manage.py                   # Django management script
└── vercel.json                 # Vercel deployment config
```

## Models Overview

### Core Models
- **ClassCode**: Represents a language class with unique codes
- **Assignment**: Language assignments with questions
- **Question**: Individual questions within assignments
- **FlashcardSet**: Collections of vocabulary flashcards
- **Flashcard**: Individual vocabulary cards
- **InterpersonalSession**: Conversational practice sessions
- **InterpersonalQuestion**: Questions for interpersonal practice

### User Progress Models
- **UserClassEnrollment**: Tracks student enrollment in classes
- **UserFlashcardProgress**: Tracks flashcard completion progress
- **UserQuestionProgress**: Tracks assignment question progress
- **UserQuestionAttempts**: Stores attempt history for questions

## API Endpoints

### Authentication
- `POST /login/` - User login
- `POST /register/` - User registration
- `GET /logout/` - User logout

### Assignments
- `POST /save_audio/` - Save and evaluate audio responses
- `GET /questions/<assignment_id>/` - Get assignment questions

### Flashcards
- `POST /save_flashcard_audio/` - Save flashcard audio responses
- `POST /update_progress/` - Update flashcard progress
- `POST /save_flashcard_index/` - Save current flashcard position

### Interpersonal Sessions
- `POST /save_interpersonal_audio/` - Save interpersonal session audio

## Deployment

### Vercel Deployment
The project includes `vercel.json` configuration for easy deployment on Vercel.

### Environment Setup for Production
1. Set `DEBUG=False` in production
2. Use a strong `DJANGO_SECRET_KEY`
3. Configure production database
4. Set up proper CORS and security headers

## Security Considerations

- ✅ All API keys moved to environment variables
- ✅ Django secret key secured
- ✅ Database credentials protected
- ✅ Cloud storage credentials secured
- ⚠️ CSRF protection disabled (consider enabling for production)
- ⚠️ Debug mode should be disabled in production

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions, please open an issue in the GitHub repository.

## Acknowledgments

- OpenAI for providing the Whisper and GPT APIs
- Backblaze for cloud storage services
- Django community for the excellent web framework 