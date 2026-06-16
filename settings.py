"""
Django settings for Latina Dance Academy project.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-0558k^nz=coqjw)15it-8444p=6y1=@(ixj4e_u7bwp^pqke8c')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DEBUG', 'True') == 'True'

ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', 'localhost,127.0.0.1,0.0.0.0').split(',')

# File upload settings for massive bulk uploads (30-100+ files)
DATA_UPLOAD_MAX_MEMORY_SIZE = 524288000  # 500MB
FILE_UPLOAD_MAX_MEMORY_SIZE = 104857600  # 100MB per file
DATA_UPLOAD_MAX_NUMBER_FIELDS = 10000    # Allow many form fields
FILE_UPLOAD_MAX_NUMBER_FILES = 200       # Allow up to 200 files per request
SESSION_COOKIE_AGE = 3600                # 1 hour session for long uploads

# Application definition
INSTALLED_APPS = [
    'modeltranslation',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'multiupload',
    'django_cleanup.apps.CleanupConfig',
    'storages',  # for AWS S3 storage
    'courses',
    'gallery',
    'newsletter',
    'users',
    'payments',
    'programs',
    'pricing',  # New pricing app added
    'slideshow',  # Slideshow app
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.i18n',
            ],
        },
    },
]

WSGI_APPLICATION = 'wsgi.application'

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'en'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True

# Supported languages
LANGUAGES = [
    ('en', 'English'),
    ('sq', 'Shqip'),  # Albanian
]

# Locale paths
LOCALE_PATHS = [
    BASE_DIR / 'locale',
]

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
    BASE_DIR / 'styles',
    BASE_DIR / 'js',
]

# Media files (uploaded content)
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Email Configuration - REAL EMAIL SENDING
# This will send actual emails to users' inboxes

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True

# IMPORTANT: Replace these with your actual Gmail credentials
EMAIL_HOST_USER = 'your-gmail@gmail.com'  # ← REPLACE WITH YOUR GMAIL ADDRESS
EMAIL_HOST_PASSWORD = 'your-app-password'  # ← REPLACE WITH GMAIL APP PASSWORD (NOT regular password)

DEFAULT_FROM_EMAIL = 'your-gmail@gmail.com'  # ← REPLACE WITH YOUR GMAIL ADDRESS

# Stripe configuration
STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY', '')
STRIPE_WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET', '')
STRIPE_PRICE_SUB = os.environ.get('STRIPE_PRICE_SUB', '')
STRIPE_PRICE_ONE_TIME = os.environ.get('STRIPE_PRICE_ONE_TIME', '')
# For frontend - try both VITE and NEXT_PUBLIC prefixes
STRIPE_PUBLISHABLE_KEY = os.environ.get('VITE_STRIPE_PUBLISHABLE_KEY') or os.environ.get('NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY') or os.environ.get('STRIPE_PUBLISHABLE_KEY', '')

# SETUP INSTRUCTIONS:
# 1. Go to Gmail → Settings → Security → 2-Step Verification
# 2. Generate an "App Password" (16-character code)
# 3. Replace 'your-gmail@gmail.com' with your actual Gmail address (2 places above)
# 4. Replace 'your-app-password' with the 16-character App Password from Gmail
# 5. Save this file and restart the server

# Example:
# EMAIL_HOST_USER = 'havabullari@gmail.com'
# EMAIL_HOST_PASSWORD = 'abcd efgh ijkl mnop'  # 16-character App Password
# DEFAULT_FROM_EMAIL = 'havabullari@gmail.com'

# Media files configuration (will be overridden if DigitalOcean Spaces is configured)

# File upload settings for django-multiupload
FILE_UPLOAD_MAX_MEMORY_SIZE = 104857600  # 100MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 524288000  # 500MB
DATA_UPLOAD_MAX_NUMBER_FILES = 500  # Allow up to 500 files per upload
FILE_UPLOAD_PERMISSIONS = 0o644

"""
AWS S3 Configuration for Media Files
Enable by setting environment variables:
  AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_STORAGE_BUCKET_NAME, AWS_S3_REGION_NAME
"""

# AWS S3 Configuration
AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
AWS_STORAGE_BUCKET_NAME = os.environ.get('AWS_STORAGE_BUCKET_NAME')
AWS_S3_REGION_NAME = os.environ.get('AWS_S3_REGION_NAME', 'us-east-1')

# Check if AWS credentials are provided
if all([AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_STORAGE_BUCKET_NAME]):
    # AWS S3 Settings
    AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com'
    AWS_DEFAULT_ACL = 'public-read'
    AWS_S3_OBJECT_PARAMETERS = {
        'CacheControl': 'max-age=86400',
    }
    AWS_S3_FILE_OVERWRITE = False
    AWS_QUERYSTRING_AUTH = False
    
    # Media files location - Store media files on AWS S3
    MEDIAFILES_LOCATION = 'media'
    DEFAULT_FILE_STORAGE = 'custom_storages.MediaStorage'
    
    # Update MEDIA_URL to use AWS S3
    MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/{MEDIAFILES_LOCATION}/'
    
    # Keep static files local for development (CSS/JS served locally)
    # STATIC_URL and STATICFILES_STORAGE remain as defined above for local serving
else:
    # Use local storage for development when AWS S3 is not configured
    DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'
    MEDIA_URL = '/media/'
    MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Authentication settings
LOGIN_URL = '/login/'  # URL where users are redirected if not logged in
LOGIN_REDIRECT_URL = '/dashboard/'  # URL where users are redirected after login
LOGOUT_REDIRECT_URL = '/'  # URL where users are redirected after logout

# Logging configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'payments.views': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}
