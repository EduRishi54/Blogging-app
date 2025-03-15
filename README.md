# EduRishi Blog - Technology-Themed Blogging Platform

A modern, technology-themed blogging platform built with Streamlit.

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://share.streamlit.io/yourusername/blogging-app/main/app.py)

## Getting Started

### Prerequisites
- Python 3.7 or newer
- pip (Python package installer)

### Local Installation

1. Clone this repository or download the files
2. Install required packages:
   ```bash
   pip install -r requirements.txt
   ```
3. Set up secrets (optional):
   - Copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml`
   - Edit the values in `secrets.toml` with your own credentials

4. Run the application:
   ```bash
   streamlit run app.py
   ```

### Deployment to GitHub and Streamlit Cloud

1. **Create a GitHub repository**:
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git remote add origin https://github.com/YOUR-USERNAME/blogging-app.git
   git push -u origin main
   ```

2. **Deploy on Streamlit Cloud**:
   - Go to [Streamlit Cloud](https://streamlit.io/cloud)
   - Sign in with your GitHub account
   - Click "New app"
   - Select your repository, branch (main), and the main file path (app.py)
   - Click "Deploy"

3. **Add secrets to Streamlit Cloud**:
   - In your app settings on Streamlit Cloud, navigate to the "Secrets" section
   - Add the following secrets:
     ```toml
     [admin]
     username = "your_admin_username"
     password = "your_admin_password"
     email = "your_admin_email"

     [database]
     connection_string = "sqlite:///blog.db"
     ```

### Deployment to Heroku

1. **Install Heroku CLI**:
   - Download and install from [Heroku CLI](https://devcenter.heroku.com/articles/heroku-cli)

2. **Login and create app**:
   ```bash
   heroku login
   heroku create your-app-name
   ```

3. **Add PostgreSQL (optional but recommended)**:
   ```bash
   heroku addons:create heroku-postgresql:hobby-dev
   ```

4. **Deploy to Heroku**:
   ```bash
   git push heroku main
   ```

5. **Set environment variables**:
   ```bash
   heroku config:set ADMIN_USERNAME=your_admin_username
   heroku config:set ADMIN_PASSWORD=your_admin_password
   heroku config:set ADMIN_EMAIL=your_admin_email
   ```

## Admin Access

The application comes with a default admin account:
- Username: `admin`
- Password: `admin123`

## Customizing Your Blog

### Social Media Links

To customize your social media links, edit the `config.py` file:

```python
# Social media links - Replace with your actual social media URLs
SOCIAL_LINKS = {
    "linkedin": "https://www.linkedin.com/in/your-profile/",
    "twitter": "https://twitter.com/your-handle",
    "facebook": "https://www.facebook.com/your-page",
    "github": "https://github.com/your-username",
    "instagram": "https://www.instagram.com/your-handle"
    # You can add or remove social media platforms as needed
}
```

Replace the placeholder URLs with your actual social media profile links. You can add or remove platforms as needed.

### Contact Information

Update your contact information in the `config.py` file:

```python
# Contact information
CONTACT_INFO = {
    "email": "your-email@example.com",
    "phone": "+1 (123) 456-7890",
    "address": "Your Address\nCity, State, ZIP\nCountry"
}
```

### Theme Customization

You can customize the light and dark themes by modifying the color values in `config.py`:

```python
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
```

## Admin Features

As an admin, you can:

1. **Manage Posts**
   - Create, edit, and delete blog posts
   - Schedule posts for future publication
   - Categorize and tag posts

2. **Manage Users**
   - View all registered users
   - Change user roles (admin/user)
   - Delete users

3. **View Messages**
   - Read and respond to contact form submissions
   - Mark messages as read

4. **Manage Subscribers**
   - View newsletter subscribers
   - Export subscriber list as CSV

### Deployment with Docker

1. **Build and run with Docker**:
   ```bash
   docker build -t blogging-app .
   docker run -p 8501:8501 blogging-app
   ```

2. **Using Docker Compose**:
   ```bash
   docker-compose up
   ```

3. **Access the app**:
   - Open your browser and go to `http://localhost:8501`

## Continuous Integration/Deployment

This repository includes a GitHub Actions workflow that:
1. Runs tests when you push to the main branch
2. Prepares for deployment

The actual deployment happens automatically through Streamlit Cloud when connected to your GitHub repository.

## Environment Variables

The following environment variables can be set to customize the application:

| Variable | Description | Default |
|----------|-------------|---------|
| APP_NAME | Name of the blog | "EduRishi Blog" |
| APP_ICON | Icon for the blog | "📚" |
| APP_DESCRIPTION | Blog description | "Insights on Technology, Quantum Physics, and AI" |
| DB_NAME | Database name or connection string | "blog.db" |
| ADMIN_USERNAME | Admin username | "admin" |
| ADMIN_PASSWORD | Admin password | "admin123" |
| ADMIN_EMAIL | Admin email | "admin@edurishi.com" |

## Troubleshooting

### Admin Panel Navigation Issues

If you experience issues with the admin panel navigation:

1. Make sure you're logged in as an admin
2. Try refreshing the page
3. Check that your browser allows cookies and local storage

### Social Media Icons Not Displaying

If social media icons aren't displaying:

1. Check your internet connection (icons are loaded from a CDN)
2. Try a different browser
3. Make sure you haven't modified the Font Awesome import in the code

### Deployment Issues

If you encounter issues during deployment:

1. Check your requirements.txt file for compatibility
2. Ensure all environment variables are properly set
3. For Streamlit Cloud, verify that your secrets are correctly configured
4. For Heroku, check the logs with `heroku logs --tail`

## License

This project is licensed under the MIT License - see the LICENSE file for details.# EduRishi Blog

A personal blogging platform built with Streamlit for sharing insights on technology, Quantum Physics, and AI. This application is designed for university professors, researchers, and educators who want to build their personal brand and share knowledge with students, faculty members, and industry experts.

![EduRishi Blog Screenshot](https://via.placeholder.com/800x400?text=EduRishi+Blog)

## Features

- **Blog Posts Management**: Create, edit, publish, and schedule blog posts
- **Rich Text Formatting**: Support for Markdown formatting including headings, lists, images, and code snippets
- **User Authentication**: Admin and user roles with secure login
- **Comments System**: Allow readers to engage with your content
- **Categories and Tags**: Organize content for better discoverability
- **Search Functionality**: Find posts by keywords, categories, and tags
- **Contact Form**: Allow visitors to reach out
- **Newsletter Subscription**: Build your audience
- **Responsive Design**: Works on all devices
- **Dark/Light Theme**: Choose your preferred viewing experience
- **Admin Dashboard**: Comprehensive admin interface for content management
- **User Profiles**: Personalized profiles for all users

## Quick Start

### For Linux/Mac:
```bash
# Clone the repository
git clone <repository-url>
cd edurishi-blog

# Run the setup script
chmod +x run.sh
./run.sh
```

### For Windows:
```
# Clone the repository
git clone <repository-url>
cd edurishi-blog

# Run the setup script
run.bat
```

## Manual Installation

1. Clone this repository:
```bash
git clone <repository-url>
cd edurishi-blog
```

2. Create and activate a virtual environment (optional but recommended):
```bash
# For Linux/Mac
python3 -m venv venv
source venv/bin/activate

# For Windows
python -m venv venv
venv\Scripts\activate
```

3. Install the required dependencies:
```bash
pip install -r requirements.txt
```

4. Run the application:
```bash
streamlit run app.py
```

5. Open your browser and navigate to:
```
http://localhost:8501
```

## Initial Setup

When you first run the application, it will:
1. Create a SQLite database (`blog.db`)
2. Set up all necessary tables
3. Create an admin user with the following credentials:
   - Username: `admin`
   - Password: `admin123`

**Important**: Change the admin password after your first login for security.

## Usage

### For Admins

1. Log in with admin credentials
2. Use the admin dashboard to:
   - View site statistics
   - Create and manage blog posts
   - Schedule posts for future publication
   - Manage user accounts
   - View and respond to contact messages
   - Manage newsletter subscribers

### For Content Creators

1. Create an account or log in
2. Create, edit, and publish blog posts
3. Organize content with categories and tags
4. Schedule posts for future publication
5. Engage with readers through comments

### For Readers

1. Browse blog posts on the home page
2. Filter content by categories and tags
3. Search for specific topics
4. Comment on posts (requires registration)
5. Subscribe to the newsletter
6. Contact the blog owner

## Customization

You can customize the blog by editing the following files:

1. `config.py` - Change application settings, default categories, and contact information
2. `style.css` - Modify the visual appearance
3. `app.py` - Extend functionality or modify existing features

### Branding

To customize the branding:

1. Update the `APP_NAME` and `APP_DESCRIPTION` in `config.py`
2. Replace placeholder images with your own
3. Modify the color scheme in `LIGHT_THEME` and `DARK_THEME` in `config.py`

## Development

### Project Structure

```
edurishi-blog/
├── app.py              # Main application file
├── config.py           # Configuration settings
├── utils.py            # Utility functions
├── style.css           # Custom CSS styles
├── requirements.txt    # Python dependencies
├── run.sh              # Linux/Mac startup script
├── run.bat             # Windows startup script
├── .gitignore          # Git ignore file
└── README.md           # This file
```

### Adding New Features

The application is built with Streamlit, which makes it easy to extend. To add new features:

1. Define new functions in `app.py` or create new modules
2. Update the database schema in the `init_db()` function if needed
3. Add new UI elements using Streamlit components

## Deployment

For production deployment, consider:

1. Using a more robust database like PostgreSQL
2. Setting up proper authentication with OAuth
3. Implementing a CDN for media storage
4. Deploying on a platform like Streamlit Cloud, Heroku, or AWS

## License

[Your License Information]

## Contact

For questions or support, please contact [your contact information]