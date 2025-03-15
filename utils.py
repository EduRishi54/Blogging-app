"""
Utility functions for the EduRishi Blog application.
"""

import re
import hashlib
import datetime
import sqlite3
import streamlit as st
from PIL import Image
from io import BytesIO
import base64

def is_valid_email(email):
    """
    Validate email format.
    
    Args:
        email (str): Email address to validate
        
    Returns:
        bool: True if email is valid, False otherwise
    """
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return re.match(pattern, email) is not None

def hash_password(password):
    """
    Hash password using SHA-256.
    
    Args:
        password (str): Plain text password
        
    Returns:
        str: Hashed password
    """
    return hashlib.sha256(password.encode()).hexdigest()

def format_datetime(dt_str):
    """
    Format datetime string for display.
    
    Args:
        dt_str (str): Datetime string from database
        
    Returns:
        str: Formatted datetime string
    """
    if not dt_str:
        return ""
    
    try:
        dt = datetime.datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
        return dt.strftime("%B %d, %Y at %I:%M %p")
    except ValueError:
        return dt_str

def get_image_as_base64(image_file):
    """
    Convert image to base64 for embedding in HTML.
    
    Args:
        image_file: Uploaded image file
        
    Returns:
        str: Base64 encoded image
    """
    img = Image.open(image_file)
    img_byte_arr = BytesIO()
    img.save(img_byte_arr, format=img.format)
    img_byte_arr = img_byte_arr.getvalue()
    encoded = base64.b64encode(img_byte_arr).decode()
    return f"data:image/{img.format.lower()};base64,{encoded}"

def truncate_text(text, max_length=150):
    """
    Truncate text to specified length and add ellipsis.
    
    Args:
        text (str): Text to truncate
        max_length (int): Maximum length before truncation
        
    Returns:
        str: Truncated text with ellipsis if needed
    """
    if len(text) <= max_length:
        return text
    
    # Try to truncate at a space to avoid cutting words
    truncated = text[:max_length]
    last_space = truncated.rfind(' ')
    
    if last_space > max_length * 0.8:  # Only use space if it's not too far back
        truncated = truncated[:last_space]
    
    return truncated + "..."

def create_card_html(title, content, author=None, date=None, category=None, tags=None, post_id=None, image_url=None):
    """
    Generate HTML for a card component.
    
    Args:
        title (str): Card title
        content (str): Card content
        author (str, optional): Author name
        date (str, optional): Post date
        category (str, optional): Post category
        tags (str, optional): Post tags
        post_id (int, optional): Post ID for linking
        image_url (str, optional): URL to featured image
        
    Returns:
        str: HTML for card component
    """
    card_html = '<div class="card">'
    
    if image_url:
        card_html += f'<img src="{image_url}" style="width:100%; border-radius:5px; margin-bottom:10px;">'
    
    card_html += f'<h3>{title}</h3>'
    
    meta_info = []
    if author:
        meta_info.append(f"By {author}")
    if date:
        meta_info.append(format_datetime(date))
    
    if meta_info:
        card_html += f'<p><em>{" on ".join(meta_info)}</em></p>'
    
    if category or tags:
        cat_tag_info = []
        if category:
            cat_tag_info.append(f"Category: {category}")
        if tags:
            cat_tag_info.append(f"Tags: {tags}")
        
        card_html += f'<p>{" | ".join(cat_tag_info)}</p>'
    
    card_html += f'<p>{truncate_text(content)}</p>'
    
    if post_id:
        card_html += f'<a href="?post_id={post_id}">Read more</a>'
    
    card_html += '</div>'
    
    return card_html

def check_scheduled_posts():
    """
    Check for scheduled posts that should be published.
    """
    conn = sqlite3.connect('blog.db')
    c = conn.cursor()
    
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Find scheduled posts that should now be published
    c.execute("""
    UPDATE posts
    SET status = 'published', published_at = ?
    WHERE status = 'scheduled' AND scheduled_for <= ?
    """, (current_time, current_time))
    
    updated_count = c.rowcount
    conn.commit()
    conn.close()
    
    return updated_count

def load_css(css_file):
    """
    Load CSS from file and inject it.
    
    Args:
        css_file (str): Path to CSS file
    """
    with open(css_file, "r") as f:
        css = f.read()
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

def generate_social_share_links(post_title, post_id, base_url="https://edurishi.com/blog"):
    """
    Generate social media sharing links.
    
    Args:
        post_title (str): Title of the post
        post_id (int): ID of the post
        base_url (str): Base URL of the blog
        
    Returns:
        dict: Dictionary of social media platform names and share URLs
    """
    post_url = f"{base_url}/post/{post_id}"
    encoded_title = post_title.replace(" ", "%20")
    encoded_url = post_url.replace(":", "%3A").replace("/", "%2F")
    
    share_links = {
        "Twitter": f"https://twitter.com/intent/tweet?text={encoded_title}&url={encoded_url}",
        "Facebook": f"https://www.facebook.com/sharer/sharer.php?u={encoded_url}",
        "LinkedIn": f"https://www.linkedin.com/shareArticle?mini=true&url={encoded_url}&title={encoded_title}",
        "Email": f"mailto:?subject={encoded_title}&body=Check%20out%20this%20post:%20{encoded_url}"
    }
    
    return share_links