import os
from dotenv import load_dotenv
load_dotenv()
import cloudinary

from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent

# Read from Render environment, fallback to the insecure one for local use
SECRET_KEY = os.getenv("SECRET_KEY", "django-insecure--*$t%!pj%_6_p#8y1+og3d+m+%oxc%_h*lqv3hzde+18zm)ltz")

# Automatically turns DEBUG off when you deploy to Render
DEBUG = os.getenv("RENDER", "False") == "False"

# Allow Render to connect, plus localhost for testing
ALLOWED_HOSTS = ['*'] 


# Application definition

INSTALLED_APPS = [
    "cloudinary_storage",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "cloudinary",
    'store',
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    'whitenoise.middleware.WhiteNoiseMiddleware',
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "core.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / 'templates'],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                'store.context_processors.categories_processor',
            ],
        },
    },
]

WSGI_APPLICATION = "core.wsgi.application"


# Database Setup
# https://docs.djangoproject.com/en/6.1/ref/settings/#databases

if os.getenv('DATABASE_URL'):
    # This runs if you are on Render (using Neon)
    import dj_database_url
    DATABASES = {
        'default': dj_database_url.config(default=os.getenv('DATABASE_URL'), conn_max_age=0)
    }
else:
    # This runs on your laptop (using SQLite)
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }


# Password validation
# https://docs.djangoproject.com/en/6.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/6.1/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/6.1/howto/static-files/

# Static & Media files
STATIC_URL = 'static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'


# Email
# https://docs.djangoproject.com/en/6.1/topics/email/#topic-email-configuration

MAILERS = {
    "default": {
        "BACKEND": "django.core.mail.backends.console.EmailBackend",
    },
}

# --- CUSTOM SETTINGS ---
UPI_ID = "parwez.adnan@ybl"  # <--- REPLACE WITH YOUR REAL UPI ID (e.g., 9876543210@ybl)
UPI_NAME = "Adnan Parwez"

# New Django 6.1 Email Configuration
MAILERS = {
    "default": {
        "BACKEND": "django.core.mail.backends.smtp.EmailBackend",
        "OPTIONS": {
            "host": "smtp.gmail.com",
            "port": 587,
            "username": "adnan.uc3m@gmail.com",      # <-- Your Gmail
            "password": "lqna jsbk mtiv ajyk",       # <-- Your 16-letter App Password
            "use_tls": True,
        },
    },
}

AUTH_USER_MODEL = 'store.CustomUser'

# --- CLOUDINARY CONFIGURATION ---


CLOUDINARY_STORAGE = {
    'CLOUD_NAME': os.getenv('CLOUDINARY_CLOUD_NAME'),
    'API_KEY': os.getenv('CLOUDINARY_API_KEY'),
    'API_SECRET': os.getenv('CLOUDINARY_API_SECRET')
}

STORAGES = {
    "default": {
        "BACKEND": "cloudinary_storage.storage.MediaCloudinaryStorage",
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}