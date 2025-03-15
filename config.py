"""
Configuration settings for the EduRishi Blog application.
"""
import os
import streamlit as st

# Try to load secrets for admin credentials and other sensitive information
try:
    # For Streamlit Cloud deployment
    admin_config = st.secrets.get("admin", {})
    db_config = st.secrets.get("database", {})
except:
    # Fallback if secrets are not available
    admin_config = {}
    db_config = {}

# Application settings
APP_NAME = os.environ.get("APP_NAME", "EduRishi Blog")
APP_ICON = os.environ.get("APP_ICON", "📚")
APP_DESCRIPTION = os.environ.get("APP_DESCRIPTION", "Insights on Technology, Quantum Physics, and AI")

# Database settings
# Use a data directory with proper permissions
import os
DB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
# Create the data directory if it doesn't exist
os.makedirs(DB_DIR, exist_ok=True)
DB_NAME = os.environ.get("DB_NAME", db_config.get("connection_string", os.path.join(DB_DIR, "blog.db")))

# Admin user default credentials
DEFAULT_ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", admin_config.get("username", "admin"))
DEFAULT_ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", admin_config.get("password", "admin123"))
DEFAULT_ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", admin_config.get("email", "admin@edurishi.com"))

# Blog categories
DEFAULT_CATEGORIES = [
    "Technology",
    "Quantum Physics",
    "AI",
    "EduRishi",
    "Education",
    "Research"
]

# Blog tags
DEFAULT_TAGS = [
    "technology",
    "quantum",
    "ai",
    "machine learning",
    "education",
    "research",
    "india",
    "university",
    "science",
    "innovation"
]

# Theme colors - Technology-focused
LIGHT_THEME = {
    "background_color": "#F8F9FA",
    "text_color": "#212529",
    "card_background": "#FFFFFF",
    "accent_color": "#0066FF",  # Bright blue
    "secondary_color": "#6610F2", # Purple
    "highlight_color": "#00B8D9", # Cyan
    "success_color": "#36B37E",  # Green
    "warning_color": "#FFAB00",  # Amber
    "error_color": "#FF5630"     # Red
}

DARK_THEME = {
    "background_color": "#121212",
    "text_color": "#E0E0E0",
    "card_background": "#1E1E1E",
    "accent_color": "#2979FF",  # Bright blue
    "secondary_color": "#7C4DFF", # Purple
    "highlight_color": "#00E5FF", # Cyan
    "success_color": "#00E676",  # Green
    "warning_color": "#FFEA00",  # Amber
    "error_color": "#FF1744"     # Red
}

# Social media links - Replace with your actual social media URLs
SOCIAL_LINKS = {
    "linkedin": "https://www.linkedin.com/in/your-profile/",
    "twitter": "https://twitter.com/your-handle",
    "facebook": "https://www.facebook.com/your-page",
    "github": "https://github.com/your-username",
    "instagram": "https://www.instagram.com/your-handle"
    # You can add or remove social media platforms as needed
}

# Contact information
CONTACT_INFO = {
    "email": "contact@edurishi.com",
    "phone": "+91 XXXXXXXXXX",
    "address": "EduRishi Headquarters\nYour Address Line 1\nCity, State, PIN Code\nIndia"
}

# SEO settings
SEO_SETTINGS = {
    "meta_description": "EduRishi Blog - Insights on Technology, Quantum Physics, and AI for university students, faculty, and industry experts.",
    "meta_keywords": "quantum physics, AI, technology, education, India, research, university",
    "og_image": "https://yourdomain.com/static/images/og-image.jpg"
}