import streamlit as st
import sqlite3
import pandas as pd
import datetime
import os
import time
from utils import (
    is_valid_email, hash_password, format_datetime, get_image_as_base64,
    truncate_text, create_card_html, check_scheduled_posts, load_css,
    generate_social_share_links
)
from config import (
    APP_NAME, APP_ICON, APP_DESCRIPTION, DB_NAME, DEFAULT_ADMIN_USERNAME,
    DEFAULT_ADMIN_PASSWORD, DEFAULT_ADMIN_EMAIL, DEFAULT_CATEGORIES,
    DEFAULT_TAGS, LIGHT_THEME, DARK_THEME, SOCIAL_LINKS, CONTACT_INFO
)

# Set page configuration
st.set_page_config(
    page_title=APP_NAME,
    page_icon=APP_ICON,
    layout="wide",
    initial_sidebar_state="expanded",
)

# Initialize session states
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = ""
if 'user_role' not in st.session_state:
    st.session_state.user_role = ""
if 'theme' not in st.session_state:
    st.session_state.theme = "light"

# Database setup
def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    # Create users table
    c.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        role TEXT NOT NULL,
        bio TEXT,
        profile_image TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # Create posts table
    c.execute('''
    CREATE TABLE IF NOT EXISTS posts (
        id INTEGER PRIMARY KEY,
        title TEXT NOT NULL,
        content TEXT NOT NULL,
        author_id INTEGER NOT NULL,
        category TEXT NOT NULL,
        tags TEXT,
        featured_image TEXT,
        status TEXT NOT NULL,
        published_at TIMESTAMP,
        scheduled_for TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (author_id) REFERENCES users (id)
    )
    ''')

    # Create comments table
    c.execute('''
    CREATE TABLE IF NOT EXISTS comments (
        id INTEGER PRIMARY KEY,
        post_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        content TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (post_id) REFERENCES posts (id),
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')

    # Create subscribers table
    c.execute('''
    CREATE TABLE IF NOT EXISTS subscribers (
        id INTEGER PRIMARY KEY,
        email TEXT UNIQUE NOT NULL,
        name TEXT,
        subscribed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # Create contact messages table
    c.execute('''
    CREATE TABLE IF NOT EXISTS contact_messages (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        email TEXT NOT NULL,
        subject TEXT NOT NULL,
        message TEXT NOT NULL,
        read BOOLEAN DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # Check if admin user exists, if not create one
    c.execute("SELECT * FROM users WHERE username = ?", (DEFAULT_ADMIN_USERNAME,))
    if not c.fetchone():
        # Create admin user
        hashed_password = hash_password(DEFAULT_ADMIN_PASSWORD)
        c.execute("INSERT INTO users (username, password, email, role) VALUES (?, ?, ?, ?)",
                 (DEFAULT_ADMIN_USERNAME, hashed_password, DEFAULT_ADMIN_EMAIL, 'admin'))

    conn.commit()
    conn.close()

# Initialize database
init_db()

# Authentication functions
def login(username, password):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    hashed_password = hash_password(password)
    c.execute("SELECT id, role FROM users WHERE username = ? AND password = ?", (username, hashed_password))
    user = c.fetchone()

    conn.close()

    if user:
        st.session_state.logged_in = True
        st.session_state.username = username
        st.session_state.user_role = user[1]
        st.session_state.user_id = user[0]
        return True
    return False

def register(username, password, email, role='user', bio=None):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    try:
        hashed_password = hash_password(password)
        c.execute("""
        INSERT INTO users (username, password, email, role, bio)
        VALUES (?, ?, ?, ?, ?)
        """, (username, hashed_password, email, role, bio))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        conn.close()
        return False

def logout():
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.session_state.user_role = ""
    st.session_state.user_id = None

def get_user_profile(user_id):
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    c.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = c.fetchone()

    conn.close()
    return dict(user) if user else None

def update_user_profile(user_id, bio=None, profile_image=None):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    if bio is not None and profile_image is not None:
        c.execute("UPDATE users SET bio = ?, profile_image = ? WHERE id = ?",
                 (bio, profile_image, user_id))
    elif bio is not None:
        c.execute("UPDATE users SET bio = ? WHERE id = ?", (bio, user_id))
    elif profile_image is not None:
        c.execute("UPDATE users SET profile_image = ? WHERE id = ?",
                 (profile_image, user_id))

    conn.commit()
    conn.close()

# Blog post functions
def create_post(title, content, author_id, category, tags, status, featured_image=None, scheduled_for=None):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    published_at = datetime.datetime.now() if status == 'published' else None

    c.execute("""
    INSERT INTO posts (title, content, author_id, category, tags, featured_image, status, published_at, scheduled_for)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (title, content, author_id, category, tags, featured_image, status, published_at, scheduled_for))

    conn.commit()
    conn.close()

def update_post(post_id, title, content, category, tags, status, featured_image=None, scheduled_for=None):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    published_at = datetime.datetime.now() if status == 'published' else None
    updated_at = datetime.datetime.now()

    if featured_image is not None:
        c.execute("""
        UPDATE posts
        SET title = ?, content = ?, category = ?, tags = ?, featured_image = ?, status = ?,
            published_at = ?, scheduled_for = ?, updated_at = ?
        WHERE id = ?
        """, (title, content, category, tags, featured_image, status, published_at, scheduled_for, updated_at, post_id))
    else:
        c.execute("""
        UPDATE posts
        SET title = ?, content = ?, category = ?, tags = ?, status = ?,
            published_at = ?, scheduled_for = ?, updated_at = ?
        WHERE id = ?
        """, (title, content, category, tags, status, published_at, scheduled_for, updated_at, post_id))

    conn.commit()
    conn.close()

def get_post(post_id):
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    c.execute("""
    SELECT p.*, u.username as author_name, u.bio as author_bio, u.profile_image as author_image
    FROM posts p
    JOIN users u ON p.author_id = u.id
    WHERE p.id = ?
    """, (post_id,))

    post = c.fetchone()
    conn.close()

    return dict(post) if post else None

def get_posts(status=None, category=None, tag=None, search_term=None, author_id=None, limit=None):
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    query = """
    SELECT p.*, u.username as author_name
    FROM posts p
    JOIN users u ON p.author_id = u.id
    WHERE 1=1
    """
    params = []

    if status:
        query += " AND p.status = ?"
        params.append(status)

    if category:
        query += " AND p.category = ?"
        params.append(category)

    if tag:
        query += " AND p.tags LIKE ?"
        params.append(f"%{tag}%")

    if search_term:
        query += " AND (p.title LIKE ? OR p.content LIKE ?)"
        params.extend([f"%{search_term}%", f"%{search_term}%"])

    if author_id:
        query += " AND p.author_id = ?"
        params.append(author_id)

    query += " ORDER BY p.created_at DESC"

    if limit:
        query += " LIMIT ?"
        params.append(limit)

    c.execute(query, params)
    posts = [dict(row) for row in c.fetchall()]

    conn.close()
    return posts

def delete_post(post_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    # First delete all comments associated with the post
    c.execute("DELETE FROM comments WHERE post_id = ?", (post_id,))

    # Then delete the post
    c.execute("DELETE FROM posts WHERE id = ?", (post_id,))

    conn.commit()
    conn.close()

def add_comment(post_id, user_id, content):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("""
    INSERT INTO comments (post_id, user_id, content)
    VALUES (?, ?, ?)
    """, (post_id, user_id, content))

    conn.commit()
    conn.close()

def get_comments(post_id):
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    c.execute("""
    SELECT c.*, u.username, u.profile_image
    FROM comments c
    JOIN users u ON c.user_id = u.id
    WHERE c.post_id = ?
    ORDER BY c.created_at DESC
    """, (post_id,))

    comments = [dict(row) for row in c.fetchall()]
    conn.close()

    return comments

def delete_comment(comment_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("DELETE FROM comments WHERE id = ?", (comment_id,))

    conn.commit()
    conn.close()

def add_subscriber(email, name=None):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    try:
        c.execute("INSERT INTO subscribers (email, name) VALUES (?, ?)", (email, name))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        conn.close()
        return False

def get_subscribers():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    c.execute("SELECT * FROM subscribers ORDER BY subscribed_at DESC")
    subscribers = [dict(row) for row in c.fetchall()]

    conn.close()
    return subscribers

def add_contact_message(name, email, subject, message):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("""
    INSERT INTO contact_messages (name, email, subject, message)
    VALUES (?, ?, ?, ?)
    """, (name, email, subject, message))

    conn.commit()
    conn.close()

def get_contact_messages(unread_only=False):
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    if unread_only:
        c.execute("SELECT * FROM contact_messages WHERE read = 0 ORDER BY created_at DESC")
    else:
        c.execute("SELECT * FROM contact_messages ORDER BY created_at DESC")

    messages = [dict(row) for row in c.fetchall()]

    conn.close()
    return messages

def mark_message_as_read(message_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("UPDATE contact_messages SET read = 1 WHERE id = ?", (message_id,))

    conn.commit()
    conn.close()

# Helper functions
def get_categories():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("SELECT DISTINCT category FROM posts")
    categories = [row[0] for row in c.fetchall()]

    # If no categories exist yet, return default categories
    if not categories:
        categories = DEFAULT_CATEGORIES

    conn.close()
    return categories

def get_tags():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("SELECT tags FROM posts")
    tag_lists = [row[0] for row in c.fetchall() if row[0]]

    all_tags = []
    for tag_list in tag_lists:
        tags = [tag.strip() for tag in tag_list.split(',')]
        all_tags.extend(tags)

    unique_tags = list(set(all_tags))

    # If no tags exist yet, return default tags
    if not unique_tags:
        unique_tags = DEFAULT_TAGS

    conn.close()
    return unique_tags

def get_post_count():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("SELECT COUNT(*) FROM posts")
    count = c.fetchone()[0]

    conn.close()
    return count

def get_user_count():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("SELECT COUNT(*) FROM users")
    count = c.fetchone()[0]

    conn.close()
    return count

def get_comment_count():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("SELECT COUNT(*) FROM comments")
    count = c.fetchone()[0]

    conn.close()
    return count

def get_subscriber_count():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("SELECT COUNT(*) FROM subscribers")
    count = c.fetchone()[0]

    conn.close()
    return count

# Apply theme
def apply_theme():
    # Load custom CSS
    try:
        load_css("style.css")
    except:
        pass

    # Set theme based on user preference
    if st.session_state.theme == "dark":
        base_theme = DARK_THEME
        shadow_intensity = "0.3"
        glow_intensity = "0.8"
    else:
        base_theme = LIGHT_THEME
        shadow_intensity = "0.1"
        glow_intensity = "0.3"

    # Create a complete theme with fallbacks for missing keys
    theme = {
        "background_color": base_theme.get("background_color", "#FFFFFF" if st.session_state.theme == "light" else "#121212"),
        "text_color": base_theme.get("text_color", "#333333" if st.session_state.theme == "light" else "#F0F0F0"),
        "card_background": base_theme.get("card_background", "#F9F9F9" if st.session_state.theme == "light" else "#1E1E1E"),
        "accent_color": base_theme.get("accent_color", "#0066FF" if st.session_state.theme == "light" else "#2979FF"),
        "secondary_color": base_theme.get("secondary_color", "#6610F2" if st.session_state.theme == "light" else "#7C4DFF"),
        "highlight_color": base_theme.get("highlight_color", "#00B8D9" if st.session_state.theme == "light" else "#00E5FF"),
        "success_color": base_theme.get("success_color", "#36B37E" if st.session_state.theme == "light" else "#00E676"),
        "warning_color": base_theme.get("warning_color", "#FFAB00" if st.session_state.theme == "light" else "#FFEA00"),
        "error_color": base_theme.get("error_color", "#FF5630" if st.session_state.theme == "light" else "#FF1744")
    }

    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&family=Source+Code+Pro:wght@400;500&display=swap');
    @import url('https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css');

    :root {{
        --background-color: {theme['background_color']};
        --text-color: {theme['text_color']};
        --card-background: {theme['card_background']};
        --accent-color: {theme['accent_color']};
        --secondary-color: {theme['secondary_color']};
        --highlight-color: {theme['highlight_color']};
        --success-color: {theme['success_color']};
        --warning-color: {theme['warning_color']};
        --error-color: {theme['error_color']};
    }}

    .stApp {{
        background-color: var(--background-color);
        color: var(--text-color);
        font-family: 'Roboto', sans-serif;
    }}

    /* Modern input fields */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stSelectbox > div > div,
    .stMultiselect > div > div {{
        background-color: var(--card-background);
        color: var(--text-color);
        border-radius: 8px;
        border: 1px solid rgba(128, 128, 128, 0.2);
        transition: all 0.3s ease;
    }}

    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {{
        border-color: var(--accent-color);
        box-shadow: 0 0 0 2px rgba(var(--accent-color), 0.2);
    }}

    /* Buttons with hover effects */
    .stButton>button {{
        background-color: var(--accent-color);
        color: white;
        border-radius: 8px;
        border: none;
        padding: 0.5rem 1rem;
        font-weight: 500;
        transition: all 0.3s ease;
        box-shadow: 0 2px 5px rgba(0, 0, 0, {shadow_intensity});
    }}

    .stButton>button:hover {{
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0, 0, 0, {shadow_intensity});
        filter: brightness(110%);
    }}

    .stButton>button:active {{
        transform: translateY(0);
    }}

    /* Secondary button style */
    .secondary-button > button {{
        background-color: var(--secondary-color);
    }}

    /* Success button style */
    .success-button > button {{
        background-color: var(--success-color);
    }}

    /* Warning button style */
    .warning-button > button {{
        background-color: var(--warning-color);
    }}

    /* Error button style */
    .error-button > button {{
        background-color: var(--error-color);
    }}

    /* Modern cards with hover effect */
    .card {{
        background-color: var(--card-background);
        padding: 20px;
        border-radius: 12px;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, {shadow_intensity});
        transition: transform 0.3s ease, box-shadow 0.3s ease;
        border: 1px solid rgba(128, 128, 128, 0.1);
    }}

    .card:hover {{
        transform: translateY(-5px);
        box-shadow: 0 8px 15px rgba(0, 0, 0, {shadow_intensity});
    }}

    /* Tech-themed glowing accents */
    .tech-accent {{
        position: relative;
    }}

    .tech-accent::after {{
        content: '';
        position: absolute;
        left: 0;
        bottom: -2px;
        width: 100%;
        height: 2px;
        background-color: var(--highlight-color);
        box-shadow: 0 0 8px rgba(var(--highlight-color), {glow_intensity});
    }}

    /* Links with hover effect */
    a {{
        color: var(--accent-color);
        text-decoration: none;
        transition: all 0.2s ease;
        position: relative;
    }}

    a:hover {{
        color: var(--highlight-color);
    }}

    a:hover::after {{
        content: '';
        position: absolute;
        left: 0;
        bottom: -2px;
        width: 100%;
        height: 1px;
        background-color: var(--highlight-color);
    }}

    /* Headings with tech accent */
    h1, h2, h3, h4, h5, h6 {{
        color: var(--text-color);
        font-weight: 500;
    }}

    /* Blog title with tech styling */
    .blog-title {{
        font-size: 2.5rem;
        font-weight: 700;
        color: var(--accent-color);
        margin-bottom: 1rem;
        text-shadow: 0 0 10px rgba(var(--accent-color), 0.3);
    }}

    .blog-subtitle {{
        font-size: 1.2rem;
        color: var(--secondary-color);
        margin-bottom: 2rem;
        font-weight: 300;
    }}

    /* Code blocks with tech styling */
    code {{
        font-family: 'Source Code Pro', monospace;
        background-color: rgba(0, 0, 0, 0.1);
        padding: 2px 5px;
        border-radius: 4px;
        font-size: 0.9em;
    }}

    /* Sidebar styling */
    .css-1d391kg, .css-163ttbj {{  /* Target sidebar */
        background-color: var(--card-background);
        border-right: 1px solid rgba(128, 128, 128, 0.1);
    }}

    /* User profile section in sidebar */
    .user-profile {{
        background: linear-gradient(135deg, var(--accent-color) 0%, var(--secondary-color) 100%);
        padding: 15px;
        border-radius: 10px;
        color: white;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, {shadow_intensity});
    }}

    /* Footer styling */
    .footer {{
        text-align: center;
        padding: 2rem 0;
        margin-top: 3rem;
        border-top: 1px solid rgba(128, 128, 128, 0.2);
        font-size: 0.9rem;
    }}
    </style>
    """, unsafe_allow_html=True)

apply_theme()

# Check for scheduled posts that should be published
published_count = check_scheduled_posts()
if published_count > 0:
    st.toast(f"{published_count} scheduled posts have been published")

# Sidebar
with st.sidebar:
    st.title(APP_NAME)

    # User Authentication Section at the top
    if not st.session_state.logged_in:
        # User not logged in - show login/register options
        st.markdown("""
        <div class="card" style="background: linear-gradient(135deg, #0066FF20 0%, #6610F220 100%);">
            <h3 style="margin-top:0;">Welcome!</h3>
            <p>Sign in to access all features</p>
        </div>
        """, unsafe_allow_html=True)

        auth_option = st.radio("", ["Login", "Register"], horizontal=True)

        if auth_option == "Login":
            with st.form("login_form"):
                st.subheader("Login")
                login_username = st.text_input("Username", key="login_username")
                login_password = st.text_input("Password", type="password", key="login_password")

                login_button = st.form_submit_button("Login")

                if login_button:
                    if login(login_username, login_password):
                        st.success("Logged in successfully!")
                        st.rerun()
                    else:
                        st.error("Invalid username or password")

        else:
            with st.form("register_form"):
                st.subheader("Register")
                reg_username = st.text_input("Username", key="reg_username")
                reg_email = st.text_input("Email", key="reg_email")
                reg_password = st.text_input("Password", type="password", key="reg_password")
                reg_confirm_password = st.text_input("Confirm Password", type="password", key="reg_confirm_password")

                register_button = st.form_submit_button("Register")

                if register_button:
                    if not reg_username or not reg_email or not reg_password:
                        st.error("All fields are required")
                    elif not is_valid_email(reg_email):
                        st.error("Invalid email format")
                    elif reg_password != reg_confirm_password:
                        st.error("Passwords do not match")
                    else:
                        if register(reg_username, reg_password, reg_email):
                            st.success("Registration successful! Please login.")
                        else:
                            st.error("Username or email already exists")

    else:
        # User is logged in - show profile section
        st.markdown(f"""
        <div class="user-profile">
            <h3 style="margin-top:0;">👋 Hello, {st.session_state.username}!</h3>
            <p>Role: <span class="tech-accent">{st.session_state.user_role.capitalize()}</span></p>
        </div>
        """, unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            if st.button("My Profile", use_container_width=True):
                st.query_params.update({"profile": "view"})
        with col2:
            if st.button("Logout", use_container_width=True):
                logout()
                st.rerun()

        # Admin panel
        if st.session_state.user_role == "admin":
            st.markdown("<hr style='margin: 15px 0; opacity: 0.3;'>", unsafe_allow_html=True)
            st.markdown("<h3 style='margin-bottom:10px;'>Admin Panel</h3>", unsafe_allow_html=True)

            # Initialize admin_page in session state if not present
            if 'admin_page' not in st.session_state:
                st.session_state.admin_page = "Dashboard"

            # Use radio button to update the admin_page in session state
            admin_page = st.radio("", ["Dashboard", "Manage Posts", "Manage Users", "Messages", "Subscribers"],
                                 index=["Dashboard", "Manage Posts", "Manage Users", "Messages", "Subscribers"].index(st.session_state.admin_page),
                                 horizontal=True,
                                 key="admin_page_radio")

            # Update session state when radio button changes
            st.session_state.admin_page = admin_page

            # Show unread message count for admin
            unread_messages = get_contact_messages(unread_only=True)
            if unread_messages:
                st.markdown(f"""
                <div style="background-color: var(--warning-color); color: black; padding: 8px 12px; border-radius: 8px; margin-top: 10px;">
                    <strong>📬 {len(unread_messages)} unread messages</strong>
                </div>
                """, unsafe_allow_html=True)

    st.divider()

    # Theme toggle
    st.subheader("🎨 Appearance")
    theme_cols = st.columns(2)
    with theme_cols[0]:
        light_theme = st.button("☀️ Light", use_container_width=True,
                               help="Switch to light theme",
                               disabled=st.session_state.theme=="light")
        if light_theme and st.session_state.theme != "light":
            st.session_state.theme = "light"
            st.rerun()

    with theme_cols[1]:
        dark_theme = st.button("🌙 Dark", use_container_width=True,
                              help="Switch to dark theme",
                              disabled=st.session_state.theme=="dark")
        if dark_theme and st.session_state.theme != "dark":
            st.session_state.theme = "dark"
            st.rerun()

    st.divider()

    # Navigation
    st.subheader("🧭 Navigation")
    page = st.radio("", ["Home", "About", "Contact", "Search"], horizontal=True)

    st.divider()

    # Categories
    st.subheader("📚 Categories")
    categories = get_categories()
    if categories:
        selected_category = st.selectbox("", ["All"] + categories)
        if selected_category != "All" and page == "Home":
            st.markdown(f"""
            <div style="background-color: var(--highlight-color); color: black; padding: 8px 12px; border-radius: 8px; margin-top: 10px;">
                <strong>Category:</strong> {selected_category}
            </div>
            """, unsafe_allow_html=True)

    # Tags
    st.subheader("🏷️ Popular Tags")
    tags = get_tags()
    if tags:
        selected_tags = st.multiselect("", tags)
        if selected_tags and page == "Home":
            st.markdown(f"""
            <div style="background-color: var(--secondary-color); color: white; padding: 8px 12px; border-radius: 8px; margin-top: 10px;">
                <strong>Tags:</strong> {', '.join(selected_tags)}
            </div>
            """, unsafe_allow_html=True)

    # Newsletter subscription
    st.divider()
    st.subheader("📧 Subscribe to Newsletter")

    with st.form("newsletter_form"):
        subscriber_name = st.text_input("Name (optional)", key="subscriber_name")
        subscriber_email = st.text_input("Email", key="subscriber_email")
        subscribe_button = st.form_submit_button("Subscribe")

        if subscribe_button:
            if not subscriber_email:
                st.error("Email is required")
            elif not is_valid_email(subscriber_email):
                st.error("Invalid email format")
            else:
                if add_subscriber(subscriber_email, subscriber_name):
                    st.success("Subscribed successfully!")
                else:
                    st.info("You are already subscribed")

    # Footer
    st.divider()
    st.markdown("""
    <div class="footer">
        <p>© 2024 EduRishi. All rights reserved.</p>
        <p style="font-size: 0.8rem; opacity: 0.7;">Powered by Streamlit</p>
    </div>
    """, unsafe_allow_html=True)

# Main content
def show_home():
    # Hero section with tech-themed styling
    st.markdown(f"""
    <div style="text-align: center; padding: 40px 20px; margin-bottom: 30px; background: linear-gradient(135deg, rgba(0,102,255,0.1) 0%, rgba(102,16,242,0.1) 100%); border-radius: 15px;">
        <h1 class="blog-title">{APP_NAME}</h1>
        <p class="blog-subtitle">{APP_DESCRIPTION}</p>
        <div style="width: 100px; height: 3px; background: linear-gradient(90deg, var(--accent-color), var(--secondary-color)); margin: 20px auto;"></div>
        <p style="max-width: 700px; margin: 0 auto; font-size: 1.1rem;">
            Exploring the frontiers of technology, quantum physics, and artificial intelligence to shape the future of education and research.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Filter posts based on sidebar selections
    category_filter = None if 'selected_category' not in locals() or selected_category == "All" else selected_category
    tag_filter = selected_tags[0] if 'selected_tags' in locals() and selected_tags else None

    # Featured posts with enhanced styling
    st.markdown("""
    <h2 class="tech-accent" style="display: inline-block; margin-bottom: 20px;">
        <span style="background: linear-gradient(90deg, var(--accent-color), var(--secondary-color)); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
            Featured Posts
        </span>
    </h2>
    """, unsafe_allow_html=True)

    featured_posts = get_posts(status="published", category=category_filter, tag=tag_filter, limit=3)

    if featured_posts:
        cols = st.columns(min(len(featured_posts), 3))
        for i, post in enumerate(featured_posts):
            with cols[i % 3]:
                image_html = ""
                if post.get('featured_image'):
                    image_html = f'<img src="{post["featured_image"]}" style="width:100%; height:180px; object-fit:cover; border-radius:8px; margin-bottom:15px;">'
                else:
                    # Default image if none provided
                    image_html = f'<div style="width:100%; height:180px; background:linear-gradient(135deg, var(--accent-color) 0%, var(--secondary-color) 100%); border-radius:8px; margin-bottom:15px; display:flex; align-items:center; justify-content:center;"><span style="color:white; font-size:3rem;">📚</span></div>'

                st.markdown(f"""
                <div class="card">
                    {image_html}
                    <span style="color:var(--secondary-color); font-size:0.8rem; text-transform:uppercase; letter-spacing:1px;">{post['category']}</span>
                    <h3 style="margin-top:5px;">{post['title']}</h3>
                    <p style="color:var(--highlight-color); font-size:0.9rem;"><em>By {post['author_name']} • {format_datetime(post['published_at'])[:10]}</em></p>
                    <p>{truncate_text(post['content'], 100)}</p>
                    <a href="?post_id={post['id']}" style="display:inline-block; margin-top:10px; font-weight:500;">Read more →</a>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="background-color:var(--card-background); padding:30px; border-radius:10px; text-align:center; border:1px dashed rgba(128,128,128,0.3);">
            <h3 style="margin-top:0;">No posts available yet</h3>
            <p>We're working on creating amazing content for you. Stay tuned!</p>
        </div>
        """, unsafe_allow_html=True)

    # Recent posts with enhanced styling
    st.markdown("""
    <h2 class="tech-accent" style="display: inline-block; margin: 40px 0 20px 0;">
        <span style="background: linear-gradient(90deg, var(--accent-color), var(--secondary-color)); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
            Recent Posts
        </span>
    </h2>
    """, unsafe_allow_html=True)

    recent_posts = get_posts(status="published", category=category_filter, tag=tag_filter, limit=5)

    for post in recent_posts:
        image_html = ""
        if post.get('featured_image'):
            image_html = f'<img src="{post["featured_image"]}" style="width:100%; height:200px; object-fit:cover; border-radius:8px;">'
        else:
            # Default image with gradient if none provided
            image_html = f'<div style="width:100%; height:200px; background:linear-gradient(135deg, var(--accent-color) 0%, var(--secondary-color) 100%); border-radius:8px; display:flex; align-items:center; justify-content:center;"><span style="color:white; font-size:3rem;">📚</span></div>'

        # Format tags with tech styling
        if post.get('tags'):
            tags_list = post['tags'].split(',')
            tags_html = '<div style="margin-top:10px;">'
            for tag in tags_list:
                tag = tag.strip()
                tags_html += f'<span style="display:inline-block; background-color:rgba(0,0,0,0.1); padding:3px 8px; border-radius:15px; font-size:0.8rem; margin-right:5px; margin-bottom:5px;">{tag}</span>'
            tags_html += '</div>'
        else:
            tags_html = ""

        st.markdown(f"""
        <div class="card">
            <div style="display:flex; flex-wrap:wrap; gap:20px;">
                <div style="flex:1; min-width:200px; max-width:300px;">
                    {image_html}
                </div>
                <div style="flex:2; min-width:300px;">
                    <span style="color:var(--secondary-color); font-size:0.8rem; text-transform:uppercase; letter-spacing:1px;">{post['category']}</span>
                    <h2 style="margin-top:5px; margin-bottom:10px;">{post['title']}</h2>
                    <p style="color:var(--highlight-color); font-size:0.9rem;"><em>By {post['author_name']} • {format_datetime(post['published_at'])[:10]}</em></p>
                    <p>{truncate_text(post['content'], 200)}</p>
                    {tags_html}
                    <a href="?post_id={post['id']}" style="display:inline-block; margin-top:15px; font-weight:500; padding:8px 15px; background-color:var(--accent-color); color:white; border-radius:5px; text-decoration:none;">Read more →</a>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

def show_post(post_id):
    post = get_post(post_id)

    if not post:
        st.error("Post not found")
        return

    # Increase view count or analytics could be added here

    # Featured image as header with title overlay for a modern look
    if post.get('featured_image'):
        st.markdown(f"""
        <div style="position: relative; margin-bottom: 30px;">
            <img src="{post['featured_image']}" style="width: 100%; height: 350px; object-fit: cover; border-radius: 15px; filter: brightness(0.7);">
            <div style="position: absolute; bottom: 0; left: 0; right: 0; padding: 30px; background: linear-gradient(0deg, rgba(0,0,0,0.7) 0%, rgba(0,0,0,0) 100%);">
                <span style="color: white; font-size: 0.9rem; text-transform: uppercase; letter-spacing: 1px; background-color: var(--accent-color); padding: 5px 10px; border-radius: 4px;">{post['category']}</span>
                <h1 style="color: white; margin-top: 10px; margin-bottom: 5px; font-size: 2.5rem; text-shadow: 0 2px 4px rgba(0,0,0,0.5);">{post['title']}</h1>
                <p style="color: rgba(255,255,255,0.9); margin-bottom: 0;">By <strong>{post['author_name']}</strong> • {format_datetime(post['published_at'])}</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        # If no featured image, use a gradient background
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, var(--accent-color) 0%, var(--secondary-color) 100%); padding: 40px; border-radius: 15px; margin-bottom: 30px;">
            <span style="color: white; font-size: 0.9rem; text-transform: uppercase; letter-spacing: 1px; background-color: rgba(255,255,255,0.2); padding: 5px 10px; border-radius: 4px;">{post['category']}</span>
            <h1 style="color: white; margin-top: 15px; margin-bottom: 10px; font-size: 2.5rem; text-shadow: 0 2px 4px rgba(0,0,0,0.3);">{post['title']}</h1>
            <p style="color: rgba(255,255,255,0.9); margin-bottom: 0;">By <strong>{post['author_name']}</strong> • {format_datetime(post['published_at'])}</p>
        </div>
        """, unsafe_allow_html=True)

    # Author info and metadata in a card
    st.markdown("""
    <div style="display: flex; margin-bottom: 30px;">
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([1, 3])

    with col1:
        # Author profile
        if post.get('author_image'):
            st.image(post['author_image'], width=120)
        else:
            st.markdown("""
            <div style="width: 120px; height: 120px; background-color: var(--accent-color); border-radius: 50%; display: flex; align-items: center; justify-content: center; color: white; font-size: 2.5rem;">
                👤
            </div>
            """, unsafe_allow_html=True)

    with col2:
        # Author info
        st.markdown(f"""
        <h3 style="margin-top: 0; margin-bottom: 5px;">{post['author_name']}</h3>
        <p style="color: var(--secondary-color); margin-bottom: 10px;">Author</p>
        """, unsafe_allow_html=True)

        if post.get('author_bio'):
            st.markdown(f"""
            <p>{post['author_bio']}</p>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <p style="opacity: 0.7;">This author hasn't added a bio yet.</p>
            """, unsafe_allow_html=True)

    # Tags with modern styling
    if post.get('tags'):
        tags_list = post['tags'].split(',')
        tags_html = '<div style="margin-bottom: 30px;">'
        for tag in tags_list:
            tag = tag.strip()
            tags_html += f'<span style="display: inline-block; background-color: rgba(0,0,0,0.05); padding: 5px 12px; border-radius: 20px; font-size: 0.9rem; margin-right: 8px; margin-bottom: 8px;"># {tag}</span>'
        tags_html += '</div>'
        st.markdown(tags_html, unsafe_allow_html=True)

    # Post content with enhanced styling
    st.markdown(f"""
    <div class="blog-content" style="font-size: 1.1rem; line-height: 1.7; margin-bottom: 40px;">
        {post["content"]}
    </div>
    """, unsafe_allow_html=True)

    # Social sharing buttons with modern styling
    st.markdown("""
    <div style="background-color: var(--card-background); padding: 20px; border-radius: 10px; margin-bottom: 30px;">
        <h3 style="margin-top: 0;">Share this post</h3>
        <div style="display: flex; gap: 10px; flex-wrap: wrap;">
    """, unsafe_allow_html=True)

    share_links = generate_social_share_links(post['title'], post_id)

    cols = st.columns(4)
    with cols[0]:
        st.markdown(f"""
        <a href='{share_links['Twitter']}' target='_blank' style="display: inline-block; padding: 8px 15px; background-color: #1DA1F2; color: white; border-radius: 5px; text-decoration: none; width: 100%; text-align: center;">
            Twitter
        </a>
        """, unsafe_allow_html=True)
    with cols[1]:
        st.markdown(f"""
        <a href='{share_links['Facebook']}' target='_blank' style="display: inline-block; padding: 8px 15px; background-color: #4267B2; color: white; border-radius: 5px; text-decoration: none; width: 100%; text-align: center;">
            Facebook
        </a>
        """, unsafe_allow_html=True)
    with cols[2]:
        st.markdown(f"""
        <a href='{share_links['LinkedIn']}' target='_blank' style="display: inline-block; padding: 8px 15px; background-color: #0077B5; color: white; border-radius: 5px; text-decoration: none; width: 100%; text-align: center;">
            LinkedIn
        </a>
        """, unsafe_allow_html=True)
    with cols[3]:
        st.markdown(f"""
        <a href='{share_links['Email']}' target='_blank' style="display: inline-block; padding: 8px 15px; background-color: #EA4335; color: white; border-radius: 5px; text-decoration: none; width: 100%; text-align: center;">
            Email
        </a>
        """, unsafe_allow_html=True)

    st.markdown("""
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Related posts with enhanced styling
    st.markdown("""
    <h2 class="tech-accent" style="display: inline-block; margin-bottom: 20px;">
        <span style="background: linear-gradient(90deg, var(--accent-color), var(--secondary-color)); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
            Related Posts
        </span>
    </h2>
    """, unsafe_allow_html=True)

    related_posts = get_posts(
        status="published",
        category=post['category'],
        limit=3
    )

    related_posts = [p for p in related_posts if p['id'] != post['id']][:3]

    if related_posts:
        cols = st.columns(min(len(related_posts), 3))
        for i, related in enumerate(related_posts):
            with cols[i]:
                image_html = ""
                if related.get('featured_image'):
                    image_html = f'<img src="{related["featured_image"]}" style="width:100%; height:120px; object-fit:cover; border-radius:8px; margin-bottom:10px;">'
                else:
                    # Default image if none provided
                    image_html = f'<div style="width:100%; height:120px; background:linear-gradient(135deg, var(--accent-color) 0%, var(--secondary-color) 100%); border-radius:8px; margin-bottom:10px; display:flex; align-items:center; justify-content:center;"><span style="color:white; font-size:2rem;">📚</span></div>'

                st.markdown(f"""
                <div class="card">
                    {image_html}
                    <h4 style="margin-top:0;">{related['title']}</h4>
                    <p><em>By {related['author_name']}</em></p>
                    <a href="?post_id={related['id']}" style="display:inline-block; margin-top:10px;">Read more →</a>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="background-color: var(--card-background); padding: 20px; border-radius: 10px; text-align: center; margin-bottom: 30px;">
            <p style="margin: 0;">No related posts found</p>
        </div>
        """, unsafe_allow_html=True)

    # Comments section with enhanced styling
    st.markdown("""
    <h2 class="tech-accent" style="display: inline-block; margin: 30px 0 20px 0;">
        <span style="background: linear-gradient(90deg, var(--accent-color), var(--secondary-color)); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
            Comments
        </span>
    </h2>
    """, unsafe_allow_html=True)

    comments = get_comments(post_id)

    if comments:
        for comment in comments:
            profile_img = comment.get('profile_image', '')
            if profile_img:
                profile_html = f'<img src="{profile_img}" style="width:50px; height:50px; border-radius:50%; margin-right:15px;">'
            else:
                profile_html = f'<div style="width:50px; height:50px; background-color:var(--accent-color); border-radius:50%; margin-right:15px; display:flex; align-items:center; justify-content:center; color:white; font-weight:bold;">{comment["username"][0].upper()}</div>'

            st.markdown(f"""
            <div class="card" style="margin-bottom:15px;">
                <div style="display:flex; align-items:center;">
                    {profile_html}
                    <div>
                        <p style="margin:0; font-weight:500;">{comment['username']}</p>
                        <p style="margin:0; font-size:0.8rem; opacity:0.7;">{format_datetime(comment['created_at'])}</p>
                    </div>
                </div>
                <div style="margin-top:15px; padding-left:65px;">
                    <p style="margin:0;">{comment['content']}</p>
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="background-color: var(--card-background); padding: 30px; border-radius: 10px; text-align: center; margin-bottom: 20px; border: 1px dashed rgba(128,128,128,0.3);">
            <h3 style="margin-top:0;">No comments yet</h3>
            <p>Be the first to share your thoughts!</p>
        </div>
        """, unsafe_allow_html=True)

    # Add comment with enhanced styling
    if st.session_state.logged_in:
        st.markdown("""
        <h3 style="margin-top:30px; margin-bottom:15px;">Add a Comment</h3>
        """, unsafe_allow_html=True)

        with st.form("comment_form"):
            comment_text = st.text_area("Your comment", height=120)
            submit_button = st.form_submit_button("Submit Comment")

            if submit_button:
                if comment_text:
                    add_comment(post_id, st.session_state.user_id, comment_text)
                    st.success("Comment added successfully!")
                    st.rerun()
                else:
                    st.error("Comment cannot be empty")
    else:
        st.markdown("""
        <div style="background-color: var(--card-background); padding: 20px; border-radius: 10px; margin-top: 20px; text-align: center;">
            <p style="margin:0;">Please <a href="#">login</a> to add a comment</p>
        </div>
        """, unsafe_allow_html=True)

def show_about():
    st.title("About Me & EduRishi")

    col1, col2 = st.columns([1, 2])

    with col1:
        # Placeholder for profile image
        st.image("https://via.placeholder.com/300", caption="Your Name")

    with col2:
        st.header("About Me")
        st.write("""
        I am a passionate educator and researcher with expertise in Quantum Physics, Technology, and Artificial Intelligence.
        Through this blog, I aim to share insights, research findings, and educational content that bridges the gap between
        complex scientific concepts and practical applications.

        My background includes extensive research in quantum computing and its applications in solving complex problems.
        I've worked with leading institutions across India to develop innovative educational methodologies that make
        advanced scientific concepts accessible to students at all levels.
        """)

    st.header("About EduRishi")
    st.write("""
    EduRishi is an educational platform dedicated to advancing knowledge in cutting-edge fields like Quantum Physics,
    Technology, and Artificial Intelligence. Our mission is to make complex scientific concepts accessible to students,
    educators, and professionals across India and beyond.

    We believe in the power of education to transform lives and drive innovation. Through our resources, workshops,
    and collaborative initiatives, we aim to inspire the next generation of scientists, engineers, and thinkers.
    """)

    st.header("Our Mission")
    st.write("""
    - To democratize access to advanced scientific knowledge
    - To bridge the gap between theoretical concepts and practical applications
    - To foster a community of lifelong learners and innovators
    - To contribute to India's growth in science and technology sectors
    """)

    st.header("Our Approach")
    st.write("""
    At EduRishi, we believe that complex concepts become accessible when presented in the right context. Our approach combines:

    1. **Clear, Jargon-Free Explanations**: We break down complex topics into understandable components
    2. **Visual Learning**: We use diagrams, animations, and interactive models to illustrate abstract concepts
    3. **Real-World Applications**: We connect theoretical knowledge to practical applications
    4. **Community Learning**: We foster discussion and collaborative problem-solving
    """)

    st.header("Connect With Me")
    cols = st.columns(len(SOCIAL_LINKS))
    for i, (platform, link) in enumerate(SOCIAL_LINKS.items()):
        with cols[i]:
            st.markdown(f"[{platform.capitalize()}]({link})")

def show_contact():
    st.title("Contact Me")

    st.write("""
    Have questions, suggestions, or collaboration ideas? I'd love to hear from you!
    Fill out the form below, and I'll get back to you as soon as possible.
    """)

    contact_name = st.text_input("Name")
    contact_email = st.text_input("Email")
    contact_subject = st.text_input("Subject")
    contact_message = st.text_area("Message", height=150)

    if st.button("Send Message"):
        if not contact_name or not contact_email or not contact_subject or not contact_message:
            st.error("All fields are required")
        elif not is_valid_email(contact_email):
            st.error("Invalid email format")
        else:
            add_contact_message(contact_name, contact_email, contact_subject, contact_message)
            st.success("Message sent successfully! I'll get back to you soon.")
            # Clear form
            st.rerun()

    st.divider()

    st.header("Other Ways to Reach Me")
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Email")
        st.write(CONTACT_INFO['email'])

        st.subheader("Phone")
        st.write(CONTACT_INFO['phone'])

    with col2:
        st.subheader("Social Media")
        for platform, link in SOCIAL_LINKS.items():
            st.write(f"{platform.capitalize()}: [{platform.capitalize()}]({link})")

        st.subheader("Address")
        st.write(CONTACT_INFO['address'])

def show_search():
    st.title("Search Blog Posts")

    search_term = st.text_input("Search for posts", placeholder="Enter keywords...")

    col1, col2 = st.columns(2)
    with col1:
        search_category = st.selectbox("Filter by Category", ["All"] + get_categories())
    with col2:
        search_tags = st.multiselect("Filter by Tags", get_tags())

    if st.button("Search") or search_term or search_category != "All" or search_tags:
        category_filter = None if search_category == "All" else search_category
        tag_filter = search_tags[0] if search_tags else None

        search_results = get_posts(
            status="published",
            category=category_filter,
            tag=tag_filter,
            search_term=search_term
        )

        if search_results:
            st.success(f"Found {len(search_results)} results")
            for post in search_results:
                image_html = ""
                if post.get('featured_image'):
                    image_html = f'<img src="{post["featured_image"]}" style="width:100px; height:100px; object-fit:cover; border-radius:5px; margin-right:15px; float:left;">'

                st.markdown(f"""
                <div class="card">
                    {image_html}
                    <h3>{post['title']}</h3>
                    <p><em>By {post['author_name']} on {format_datetime(post['published_at'])[:10]}</em></p>
                    <p>Category: {post['category']} {f"| Tags: {post['tags']}" if post.get('tags') else ""}</p>
                    <p>{truncate_text(post['content'], 150)}</p>
                    <div style="clear:both;"></div>
                    <a href="?post_id={post['id']}">Read more</a>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No posts found matching your criteria")

def show_user_profile():
    if not st.session_state.logged_in:
        st.error("Please login to view your profile")
        return

    user_id = st.session_state.user_id
    user = get_user_profile(user_id)

    if not user:
        st.error("User profile not found")
        return

    st.title("My Profile")

    tab1, tab2, tab3 = st.tabs(["Profile Info", "My Posts", "My Comments"])

    with tab1:
        col1, col2 = st.columns([1, 2])

        with col1:
            if user.get('profile_image'):
                st.image(user['profile_image'], width=200)
            else:
                st.image("https://via.placeholder.com/200?text=Profile", width=200)

            if st.button("Upload Profile Picture"):
                st.info("Feature coming soon!")

        with col2:
            st.subheader(user['username'])
            st.write(f"Email: {user['email']}")
            st.write(f"Role: {user['role']}")
            st.write(f"Joined: {format_datetime(user['created_at'])[:10]}")

            current_bio = user.get('bio', '')
            new_bio = st.text_area("Bio", value=current_bio, height=150)

            if st.button("Update Profile"):
                if new_bio != current_bio:
                    update_user_profile(user_id, bio=new_bio)
                    st.success("Profile updated successfully!")
                    st.rerun()

    with tab2:
        st.subheader("My Posts")
        user_posts = get_posts(author_id=user_id)

        if user_posts:
            for post in user_posts:
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown(f"""
                    <div class="card">
                        <h3>{post['title']}</h3>
                        <p><em>Status: {post['status'].capitalize()} | Created: {format_datetime(post['created_at'])[:10]}</em></p>
                        <p>Category: {post['category']}</p>
                        <a href="?post_id={post['id']}">View</a>
                    </div>
                    """, unsafe_allow_html=True)

                with col2:
                    st.button("Edit", key=f"edit_{post['id']}",
                             on_click=lambda id=post['id']: st.query_params.update({"edit_post_id": id}))
        else:
            st.info("You haven't created any posts yet")

        if st.button("Create New Post"):
            st.query_params.update({"create_post": "true"})

    with tab3:
        st.subheader("My Comments")

        conn = sqlite3.connect(DB_NAME)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()

        c.execute("""
        SELECT c.*, p.title as post_title, p.id as post_id
        FROM comments c
        JOIN posts p ON c.post_id = p.id
        WHERE c.user_id = ?
        ORDER BY c.created_at DESC
        """, (user_id,))

        user_comments = [dict(row) for row in c.fetchall()]
        conn.close()

        if user_comments:
            for comment in user_comments:
                st.markdown(f"""
                <div class="card">
                    <p><strong>On post:</strong> <a href="?post_id={comment['post_id']}">{comment['post_title']}</a></p>
                    <p><em>Posted on {format_datetime(comment['created_at'])}</em></p>
                    <p>{comment['content']}</p>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("You haven't made any comments yet")

def admin_dashboard():
    st.title("Admin Dashboard")

    # Stats
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Posts", get_post_count())

        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM posts WHERE status = 'published'")
        published_posts = c.fetchone()[0]
        conn.close()

        st.metric("Published Posts", published_posts)

    with col2:
        st.metric("Total Users", get_user_count())
        st.metric("Total Comments", get_comment_count())

    with col3:
        st.metric("Newsletter Subscribers", get_subscriber_count())

        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM contact_messages WHERE read = 0")
        unread_messages = c.fetchone()[0]
        conn.close()

        st.metric("Unread Messages", unread_messages)

    # Recent activity
    st.header("Recent Posts")
    recent_posts = get_posts(limit=5)

    if recent_posts:
        posts_df = pd.DataFrame(recent_posts)
        posts_df = posts_df[['id', 'title', 'author_name', 'status', 'created_at']]
        posts_df['created_at'] = posts_df['created_at'].apply(lambda x: x[:10] if x else '')
        posts_df.columns = ['ID', 'Title', 'Author', 'Status', 'Created At']
        st.dataframe(posts_df)

    # Scheduled posts
    st.header("Scheduled Posts")
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    c.execute("""
    SELECT p.*, u.username as author_name
    FROM posts p
    JOIN users u ON p.author_id = u.id
    WHERE p.status = 'scheduled' AND p.scheduled_for > datetime('now')
    ORDER BY p.scheduled_for ASC
    """)

    scheduled_posts = [dict(row) for row in c.fetchall()]
    conn.close()

    if scheduled_posts:
        for post in scheduled_posts:
            st.markdown(f"""
            <div class="card">
                <h3>{post['title']}</h3>
                <p><em>By {post['author_name']}</em></p>
                <p>Scheduled for: {format_datetime(post['scheduled_for'])}</p>
                <a href="?edit_post_id={post['id']}">Edit</a>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No scheduled posts")

    # Quick actions
    st.header("Quick Actions")
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("Create New Post", key="dashboard_new_post"):
            st.query_params.update({"create_post": "true"})

    with col2:
        if st.button("View All Messages", key="dashboard_messages"):
            st.session_state.admin_page = "Messages"
            st.rerun()

    with col3:
        if st.button("Manage Users", key="dashboard_users"):
            st.session_state.admin_page = "Manage Users"
            st.rerun()

def create_new_post():
    st.title("Create New Post")

    post_title = st.text_input("Title")

    # Rich text editor placeholder (Streamlit doesn't have a built-in rich text editor)
    st.write("Content (supports Markdown)")
    post_content = st.text_area("", height=300, placeholder="Write your post content here...")

    col1, col2 = st.columns(2)
    with col1:
        existing_categories = get_categories()
        post_category = st.selectbox("Category", existing_categories + ["New Category"])

        if post_category == "New Category":
            post_category = st.text_input("Enter new category")

    with col2:
        existing_tags = get_tags()
        suggested_tags = ", ".join(existing_tags[:3]) if existing_tags else "technology, education"
        post_tags = st.text_input("Tags (comma separated)", value=suggested_tags)

    # Featured image upload (placeholder - would need file storage in a real app)
    st.subheader("Featured Image")
    st.info("Image upload functionality would be implemented with cloud storage in a production app")
    featured_image_url = st.text_input("Image URL (optional)", placeholder="https://example.com/image.jpg")

    col1, col2 = st.columns(2)
    with col1:
        post_status = st.selectbox("Status", ["draft", "published", "scheduled"])

    with col2:
        if post_status == "scheduled":
            post_schedule_date = st.date_input("Schedule Date", datetime.datetime.now() + datetime.timedelta(days=1))
            post_schedule_time = st.time_input("Schedule Time", datetime.time(9, 0))
            scheduled_datetime = datetime.datetime.combine(post_schedule_date, post_schedule_time)
        else:
            scheduled_datetime = None

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Create Post"):
            if not post_title or not post_content or not post_category:
                st.error("Title, content, and category are required")
            else:
                create_post(
                    post_title,
                    post_content,
                    st.session_state.user_id,
                    post_category,
                    post_tags,
                    post_status,
                    featured_image_url if featured_image_url else None,
                    scheduled_datetime
                )
                st.success("Post created successfully!")
                st.query_params.clear()
                st.rerun()

    with col2:
        if st.button("Cancel"):
            st.query_params.clear()
            st.rerun()

def manage_posts():
    st.title("Manage Posts")

    tab1, tab2, tab3 = st.tabs(["All Posts", "Published", "Drafts & Scheduled"])

    with tab1:
        posts = get_posts()

        if posts:
            for post in posts:
                col1, col2 = st.columns([3, 1])
                with col1:
                    status_color = {
                        "published": "green",
                        "draft": "gray",
                        "scheduled": "blue"
                    }.get(post['status'], "gray")

                    st.markdown(f"""
                    <div class="card">
                        <h3>{post['title']}</h3>
                        <p><em>By {post['author_name']} | Status: <span style="color:{status_color}">{post['status'].capitalize()}</span></em></p>
                        <p>Category: {post['category']} {f"| Tags: {post['tags']}" if post.get('tags') else ""}</p>
                        <a href="?post_id={post['id']}">View</a>
                    </div>
                    """, unsafe_allow_html=True)

                with col2:
                    st.button("Edit", key=f"edit_{post['id']}",
                             on_click=lambda id=post['id']: st.query_params.update({"edit_post_id": id}))

                    if st.button("Delete", key=f"delete_{post['id']}"):
                        if st.session_state.get(f"confirm_delete_{post['id']}", False):
                            delete_post(post['id'])
                            st.success("Post deleted successfully!")
                            st.rerun()
                        else:
                            st.session_state[f"confirm_delete_{post['id']}"] = True
                            st.warning("Click again to confirm deletion")
        else:
            st.info("No posts available")

    with tab2:
        published_posts = get_posts(status="published")

        if published_posts:
            for post in published_posts:
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown(f"""
                    <div class="card">
                        <h3>{post['title']}</h3>
                        <p><em>By {post['author_name']} | Published: {format_datetime(post['published_at'])[:10]}</em></p>
                        <p>Category: {post['category']}</p>
                        <a href="?post_id={post['id']}">View</a>
                    </div>
                    """, unsafe_allow_html=True)

                with col2:
                    st.button("Edit", key=f"edit_pub_{post['id']}",
                             on_click=lambda id=post['id']: st.query_params.update({"edit_post_id": id}))
        else:
            st.info("No published posts")

    with tab3:
        draft_scheduled_posts = get_posts(status="draft") + get_posts(status="scheduled")

        if draft_scheduled_posts:
            for post in draft_scheduled_posts:
                col1, col2 = st.columns([3, 1])
                with col1:
                    status_text = f"Scheduled for: {format_datetime(post['scheduled_for'])}" if post['status'] == "scheduled" else "Draft"

                    st.markdown(f"""
                    <div class="card">
                        <h3>{post['title']}</h3>
                        <p><em>By {post['author_name']} | {status_text}</em></p>
                        <p>Category: {post['category']}</p>
                        <a href="?post_id={post['id']}">View</a>
                    </div>
                    """, unsafe_allow_html=True)

                with col2:
                    st.button("Edit", key=f"edit_ds_{post['id']}",
                             on_click=lambda id=post['id']: st.query_params.update({"edit_post_id": id}))
        else:
            st.info("No drafts or scheduled posts")

    st.divider()
    if st.button("Create New Post", key="manage_create_post"):
        st.query_params.update({"create_post": "true"})

def edit_post(post_id):
    post = get_post(post_id)

    if not post:
        st.error("Post not found")
        return

    st.title("Edit Post")

    post_title = st.text_input("Title", value=post['title'])
    post_content = st.text_area("Content", value=post['content'], height=300)

    col1, col2 = st.columns(2)
    with col1:
        existing_categories = get_categories()
        if post['category'] not in existing_categories:
            existing_categories.append(post['category'])

        post_category = st.selectbox("Category", existing_categories + ["New Category"],
                                    index=existing_categories.index(post['category']) if post['category'] in existing_categories else 0)

        if post_category == "New Category":
            post_category = st.text_input("Enter new category")

    with col2:
        post_tags = st.text_input("Tags (comma separated)", value=post['tags'] if post['tags'] else "")

    # Featured image
    st.subheader("Featured Image")
    if post.get('featured_image'):
        st.image(post['featured_image'], width=300)
        st.write("Current featured image URL:", post['featured_image'])

    featured_image_url = st.text_input("New Image URL (leave empty to keep current)", "")

    col1, col2 = st.columns(2)
    with col1:
        status_options = ["draft", "published", "scheduled"]
        default_index = status_options.index(post['status']) if post['status'] in status_options else 0
        post_status = st.selectbox("Status", status_options, index=default_index)

    with col2:
        if post_status == "scheduled":
            if post.get('scheduled_for'):
                try:
                    if isinstance(post['scheduled_for'], str):
                        scheduled_date = datetime.datetime.strptime(post['scheduled_for'], "%Y-%m-%d %H:%M:%S").date()
                        scheduled_time = datetime.datetime.strptime(post['scheduled_for'], "%Y-%m-%d %H:%M:%S").time()
                    else:
                        scheduled_date = post['scheduled_for'].date()
                        scheduled_time = post['scheduled_for'].time()
                except (ValueError, AttributeError):
                    scheduled_date = datetime.datetime.now().date() + datetime.timedelta(days=1)
                    scheduled_time = datetime.time(9, 0)
            else:
                scheduled_date = datetime.datetime.now().date() + datetime.timedelta(days=1)
                scheduled_time = datetime.time(9, 0)

            post_schedule_date = st.date_input("Schedule Date", scheduled_date)
            post_schedule_time = st.time_input("Schedule Time", scheduled_time)
            scheduled_datetime = datetime.datetime.combine(post_schedule_date, post_schedule_time)
        else:
            scheduled_datetime = None

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Update Post"):
            if not post_title or not post_content or not post_category:
                st.error("Title, content, and category are required")
            else:
                # Use the new image URL if provided, otherwise keep the existing one
                image_to_use = featured_image_url if featured_image_url else post.get('featured_image')

                update_post(
                    post_id,
                    post_title,
                    post_content,
                    post_category,
                    post_tags,
                    post_status,
                    image_to_use,
                    scheduled_datetime
                )
                st.success("Post updated successfully!")
                # Remove query param and refresh
                st.query_params.clear()
                st.rerun()

    with col2:
        if st.button("Cancel"):
            st.query_params.clear()
            st.rerun()

def manage_users():
    st.title("Manage Users")

    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    c.execute("SELECT * FROM users ORDER BY created_at DESC")
    users = [dict(row) for row in c.fetchall()]

    conn.close()

    if users:
        for user in users:
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                profile_img = user.get('profile_image', '')
                profile_html = f'<img src="{profile_img}" style="width:50px; height:50px; border-radius:50%; margin-right:10px; float:left;">' if profile_img else ''

                st.markdown(f"""
                <div class="card">
                    {profile_html}
                    <h3>{user['username']}</h3>
                    <p>Email: {user['email']}</p>
                    <p>Role: {user['role']}</p>
                    <p>Joined: {format_datetime(user['created_at'])[:10]}</p>
                </div>
                """, unsafe_allow_html=True)

            with col2:
                new_role = st.selectbox(
                    "Change Role",
                    ["user", "admin"],
                    index=0 if user['role'] == "user" else 1,
                    key=f"role_{user['id']}"
                )

            with col3:
                if st.button("Update", key=f"update_{user['id']}"):
                    conn = sqlite3.connect(DB_NAME)
                    c = conn.cursor()
                    c.execute("UPDATE users SET role = ? WHERE id = ?", (new_role, user['id']))
                    conn.commit()
                    conn.close()
                    st.success(f"User {user['username']} updated to {new_role}")
                    st.rerun()

                if user['username'] != DEFAULT_ADMIN_USERNAME and st.button("Delete", key=f"delete_{user['id']}"):
                    if st.session_state.get(f"confirm_delete_user_{user['id']}", False):
                        conn = sqlite3.connect(DB_NAME)
                        c = conn.cursor()

                        # Delete user's comments
                        c.execute("DELETE FROM comments WHERE user_id = ?", (user['id'],))

                        # Set user's posts to admin
                        admin_id = 1  # Assuming admin has ID 1
                        c.execute("UPDATE posts SET author_id = ? WHERE author_id = ?", (admin_id, user['id']))

                        # Delete the user
                        c.execute("DELETE FROM users WHERE id = ?", (user['id'],))

                        conn.commit()
                        conn.close()
                        st.success(f"User {user['username']} deleted")
                        st.rerun()
                    else:
                        st.session_state[f"confirm_delete_user_{user['id']}"] = True
                        st.warning("Click again to confirm deletion")
    else:
        st.info("No users found")

def view_messages():
    st.title("Contact Messages")

    tab1, tab2 = st.tabs(["All Messages", "Unread Messages"])

    with tab1:
        messages = get_contact_messages()
        display_messages(messages)

    with tab2:
        unread_messages = get_contact_messages(unread_only=True)
        if unread_messages:
            display_messages(unread_messages)
        else:
            st.info("No unread messages")

def display_messages(messages):
    if messages:
        for msg in messages:
            read_status = "" if msg.get('read', 0) else "🔵 "
            with st.expander(f"{read_status}{msg['subject']} - from {msg['name']} ({format_datetime(msg['created_at'])[:10]})"):
                st.write(f"**From:** {msg['name']} ({msg['email']})")
                st.write(f"**Date:** {format_datetime(msg['created_at'])}")
                st.write(f"**Subject:** {msg['subject']}")
                st.write("**Message:**")
                st.write(msg['message'])

                col1, col2 = st.columns(2)
                with col1:
                    if not msg.get('read', 0):
                        if st.button("Mark as Read", key=f"read_{msg['id']}"):
                            mark_message_as_read(msg['id'])
                            st.success("Message marked as read")
                            st.rerun()

                with col2:
                    if st.button("Delete", key=f"delete_msg_{msg['id']}"):
                        conn = sqlite3.connect(DB_NAME)
                        c = conn.cursor()
                        c.execute("DELETE FROM contact_messages WHERE id = ?", (msg['id'],))
                        conn.commit()
                        conn.close()
                        st.success("Message deleted")
                        st.rerun()
    else:
        st.info("No messages found")

def manage_subscribers():
    st.title("Newsletter Subscribers")

    subscribers = get_subscribers()

    if subscribers:
        # Display subscriber count
        st.metric("Total Subscribers", len(subscribers))

        # Export option
        if st.button("Export Subscribers CSV"):
            subscribers_df = pd.DataFrame(subscribers)
            subscribers_df = subscribers_df[['email', 'name', 'subscribed_at']]
            subscribers_df.columns = ['Email', 'Name', 'Subscribed At']

            # Convert to CSV
            csv = subscribers_df.to_csv(index=False)

            # Create download button
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name="subscribers.csv",
                mime="text/csv"
            )

        # Display subscribers in a table
        subscribers_df = pd.DataFrame(subscribers)
        subscribers_df['subscribed_at'] = subscribers_df['subscribed_at'].apply(lambda x: format_datetime(x)[:10] if x else '')
        subscribers_df = subscribers_df[['email', 'name', 'subscribed_at']]
        subscribers_df.columns = ['Email', 'Name', 'Subscribed At']

        st.dataframe(subscribers_df)

        # Bulk actions
        st.subheader("Bulk Actions")
        st.warning("In a production app, this would connect to an email service to send newsletters")

        subject = st.text_input("Email Subject")
        message = st.text_area("Email Message")

        if st.button("Send Test Email"):
            st.success("Test email would be sent in a production environment")

        if st.button("Send to All Subscribers"):
            if not subject or not message:
                st.error("Subject and message are required")
            else:
                st.success(f"Newsletter would be sent to {len(subscribers)} subscribers in a production environment")
    else:
        st.info("No subscribers yet")

# Main app logic
query_params = st.query_params.to_dict()

# Handle query parameters for navigation
if "post_id" in query_params:
    show_post(int(query_params["post_id"][0]))
elif "edit_post_id" in query_params and st.session_state.logged_in and st.session_state.user_role == "admin":
    edit_post(int(query_params["edit_post_id"][0]))
elif "create_post" in query_params and st.session_state.logged_in:
    create_new_post()
elif "profile" in query_params and st.session_state.logged_in:
    show_user_profile()
# Admin panel
elif st.session_state.logged_in and st.session_state.user_role == "admin" and 'admin_page' in st.session_state:
    if st.session_state.admin_page == "Dashboard":
        admin_dashboard()
    elif st.session_state.admin_page == "Manage Posts":
        manage_posts()
    elif st.session_state.admin_page == "Manage Users":
        manage_users()
    elif st.session_state.admin_page == "Messages":
        view_messages()
    elif st.session_state.admin_page == "Subscribers":
        manage_subscribers()
# Regular navigation
else:
    if 'page' in locals():
        if page == "Home":
            show_home()
        elif page == "About":
            show_about()
        elif page == "Contact":
            show_contact()
        elif page == "Search":
            show_search()
    else:
        # Default to home if no page is selected
        show_home()

# Footer with social media links from config
social_links_html = ""
for platform, url in SOCIAL_LINKS.items():
    icon_class = f"fab fa-{platform.lower()}"
    social_links_html += f'<a href="{url}" target="_blank" style="margin: 0 10px;"><i class="{icon_class}"></i> {platform.capitalize()}</a>'

st.markdown(f"""
<div class="footer">
    <div style="display: flex; justify-content: center; margin-bottom: 15px; flex-wrap: wrap;">
        {social_links_html}
    </div>
    <p>© 2024 EduRishi. All rights reserved.</p>
    <p style="font-size: 0.8rem; opacity: 0.7;">Exploring Technology, Quantum Physics, and AI</p>
    <div style="width: 50px; height: 3px; background: linear-gradient(90deg, var(--accent-color), var(--secondary-color)); margin: 15px auto;"></div>
</div>
""", unsafe_allow_html=True)