"""AI Image Studio Pro.

A Streamlit web application that interfaces with the Pollinations.ai API to
generate high-quality images with customized settings and a glassmorphism style.
"""

import logging
from io import BytesIO
import os
import random
from typing import Optional, Tuple
import urllib.parse
from dotenv import load_dotenv
import requests
from PIL import Image
import streamlit as st

# -----------------------------------------------------------------------------
# ENVIRONMENT CONFIGURATION
# -----------------------------------------------------------------------------
# Load variables from .env file if it exists
load_dotenv()

# Resolve configuration variables with production-ready fallbacks
POLLINATIONS_API_URL = os.getenv(
    "POLLINATIONS_API_URL", "https://image.pollinations.ai"
).rstrip("/")
API_TIMEOUT_SECONDS = int(os.getenv("API_TIMEOUT_SECONDS", "60"))
LOG_LEVEL_NAME = os.getenv("LOG_LEVEL", "INFO").upper()

# -----------------------------------------------------------------------------
# LOGGING SETUP
# -----------------------------------------------------------------------------
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL_NAME, logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("ai_image_studio")

# Predefined prompts for Surprise Me button
SURPRISE_PROMPTS = [
    "An astronaut riding a horse on Mars",
    "A cyberpunk street food vendor in Tokyo at night",
    "A mystical forest with glowing mushrooms and a hidden waterfall",
    "A futuristic city under a glass dome underwater",
    "A majestic dragon perched on top of a snow-covered mountain peak",
]

# -----------------------------------------------------------------------------
# CORE IMAGE GENERATION LOGIC
# -----------------------------------------------------------------------------
def generate_image(
    prompt: str, art_style_val: str, w: int, h: int, enhance: bool
) -> Tuple[Optional[Image.Image], str]:
    """Generates an image from the Pollinations.ai API based on parameters.

    Args:
        prompt: The main textual description.
        art_style_val: Art style selection (e.g. Anime, Cyberpunk).
        w: Image width (between 256 and 1024).
        h: Image height (between 256 and 1024).
        enhance: If True, appends masterwork modifiers to prompt.

    Returns:
        A tuple of (PIL Image object or None, full prompt string sent to API).
    """
    # Combines prompt and art style
    full_prompt = f"{prompt}, {art_style_val} style"

    # Task 3 Logic: Prepend/append boost words if enhance checkbox is enabled
    if enhance:
        full_prompt += ", masterpiece, 8k resolution, highly detailed, trending on artstation, unreal engine 5 render"

    # Input validation boundaries
    if not prompt.strip():
        logger.warning("Empty prompt text provided for generation.")
        return None, full_prompt

    if not (256 <= w <= 1024) or not (256 <= h <= 1024):
        logger.error(
            "Input boundary validation failed: width=%d, height=%d", w, h
        )
        st.error("Width and height must be between 256 and 1024 pixels.")
        return None, full_prompt

    # Safe quoting of the prompt path variable
    safe_prompt_path = urllib.parse.quote(full_prompt)
    url = f"{POLLINATIONS_API_URL}/prompt/{safe_prompt_path}?width={w}&height={h}"

    logger.info("[AUDIT] Requesting image generation with URL: %s", url)

    try:
        response = requests.get(url, timeout=API_TIMEOUT_SECONDS)
        if response.status_code == 200:
            content_type = response.headers.get("content-type", "")
            if "image" not in content_type:
                logger.error(
                    "API did not return an image content-type: %s", content_type
                )
                st.error("API did not return a valid image payload.")
                return None, full_prompt

            img = Image.open(BytesIO(response.content))
            logger.info("[AUDIT] Successfully completed image generation.")
            return img, full_prompt
        else:
            logger.error(
                "API returned error status code: %d", response.status_code
            )
            st.error(
                f"Generation failed: API returned status code {response.status_code}."
            )
            return None, full_prompt

    except requests.RequestException as e:
        logger.exception("Network connection failed during image generation.")
        st.error(f"Network error: {str(e)}")
        return None, full_prompt
    except Exception as e:
        logger.exception("An unexpected error occurred during image generation.")
        st.error(f"Unexpected error: {str(e)}")
        return None, full_prompt


# -----------------------------------------------------------------------------
# DOWNLOAD AND DISPLAY LOGIC
# -----------------------------------------------------------------------------
def display_and_download(img: Image.Image, art_style_val: str) -> None:
    """Displays the image and provides a download button.

    Args:
        img: PIL image to display and package.
        art_style_val: Current art style for dynamic file naming.
    """
    st.image(img, use_container_width=True)

    try:
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)

        # Task 2 Fix: Dynamic naming based on art style, ending in .png
        clean_style_name = art_style_val.lower().replace(" ", "_")
        file_name = f"{clean_style_name}_image.png"

        st.download_button(
            label="💾 Download Image (PNG)",
            data=buffer,
            file_name=file_name,
            mime="image/png",
            use_container_width=True,
        )
        logger.info("[AUDIT] Image package ready for download as: %s", file_name)
    except Exception as e:
        logger.exception("Failed to buffer image content for download.")
        st.error(f"Failed to prepare download: {str(e)}")


# -----------------------------------------------------------------------------
# MAIN APP ENTRYPOINT
# -----------------------------------------------------------------------------
def main() -> None:
    """Executes the Streamlit layout and user interaction logic."""
    # -------------------------------------------------------------------------
    # PAGE CONFIGURATION
    # -------------------------------------------------------------------------
    st.set_page_config(
        page_title="AI Image Studio Pro",
        page_icon="🎨",
        layout="centered",
    )

    # -------------------------------------------------------------------------
    # CUSTOM PREMIUM CSS STYLING
    # -------------------------------------------------------------------------
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&display=swap');
        
        /* Global styling */
        html, body, [class*="css"], .stMarkdown {
            font-family: 'Outfit', -apple-system, BlinkMacSystemFont, sans-serif;
        }
        
        /* Header Gradient styling */
        .header-container {
            text-align: center;
            padding: 1.5rem 0;
            margin-bottom: 2rem;
        }
        
        .title-gradient {
            background: linear-gradient(90deg, #FF4B4B, #FF8F8F, #8F3CFF);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-weight: 800;
            font-size: 2.8rem;
            margin-bottom: 0.2rem;
        }
        
        .subtitle-text {
            color: #94A3B8;
            font-size: 1.1rem;
            font-weight: 300;
        }
        
        /* Glassmorphism elements */
        .glass-panel {
            background: rgba(255, 255, 255, 0.03);
            border-radius: 16px;
            border: 1px solid rgba(255, 255, 255, 0.07);
            padding: 20px;
            margin-bottom: 20px;
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
        }
        
        /* Interactive button styles */
        .stButton>button {
            background: linear-gradient(135deg, #6366F1 0%, #4F46E5 100%) !important;
            color: white !important;
            border: none !important;
            padding: 0.6rem 1.5rem !important;
            font-weight: 600 !important;
            border-radius: 12px !important;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
            box-shadow: 0 4px 12px rgba(79, 70, 229, 0.3) !important;
        }
        
        .stButton>button:hover {
            background: linear-gradient(135deg, #4F46E5 0%, #3730A3 100%) !important;
            transform: translateY(-2px) !important;
            box-shadow: 0 6px 20px rgba(79, 70, 229, 0.4) !important;
        }
        
        .stButton>button:active {
            transform: translateY(1px) !important;
        }
        
        /* Download button specific styles */
        .stDownloadButton>button {
            background: linear-gradient(135deg, #10B981 0%, #059669 100%) !important;
            color: white !important;
            border: none !important;
            padding: 0.6rem 1.5rem !important;
            font-weight: 600 !important;
            border-radius: 12px !important;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
            box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3) !important;
        }
        
        .stDownloadButton>button:hover {
            background: linear-gradient(135deg, #059669 0%, #047857 100%) !important;
            transform: translateY(-2px) !important;
            box-shadow: 0 6px 20px rgba(16, 185, 129, 0.4) !important;
        }
        
        .stDownloadButton>button:active {
            transform: translateY(1px) !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="header-container">
            <h1 class="title-gradient">AI Image Studio Pro</h1>
            <p class="subtitle-text">Unleash your creativity with advanced AI image generation</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # -------------------------------------------------------------------------
    # SESSION STATE MANAGEMENT
    # -------------------------------------------------------------------------
    if "prompt_input" not in st.session_state:
        st.session_state.prompt_input = ""
    if "active_image" not in st.session_state:
        st.session_state.active_image = None
    if "active_full_prompt" not in st.session_state:
        st.session_state.active_full_prompt = ""
    if "active_style" not in st.session_state:
        st.session_state.active_style = ""
    if "active_prompt" not in st.session_state:
        st.session_state.active_prompt = ""

    # -------------------------------------------------------------------------
    # UI LAYOUT - SIDEBAR
    # -------------------------------------------------------------------------
    st.sidebar.markdown("### ⚙️ Settings")

    width = st.sidebar.slider(
        label="Width (pixels)",
        min_value=256,
        max_value=1024,
        value=512,
        step=64,
    )

    height = st.sidebar.slider(
        label="Height (pixels)",
        min_value=256,
        max_value=1024,
        value=512,
        step=64,
    )

    art_styles = [
        "Photorealistic",
        "Anime",
        "Cyberpunk",
        "Oil Painting",
        "Watercolor",
        "3D Render",
        "Pixel Art",
        "Fantasy",
    ]
    art_style = st.sidebar.selectbox("Art Style", options=art_styles)

    # Task 3: Magic Enhance Checkbox
    magic_enhance = st.sidebar.checkbox("✨ Enable Magic Enhance", value=False)

    # -------------------------------------------------------------------------
    # UI LAYOUT - MAIN CONTENT AREA
    # -------------------------------------------------------------------------
    user_prompt = st.text_input(
        "Enter your prompt text:",
        value=st.session_state.prompt_input,
        placeholder="Describe the image you want to create...",
    )

    # Update prompt state when user types
    if user_prompt != st.session_state.prompt_input:
        st.session_state.prompt_input = user_prompt

    # Column layout for actions
    col1, col2 = st.columns(2)

    with col1:
        generate_btn = st.button("🚀 Generate Image", use_container_width=True)

    with col2:
        surprise_btn = st.button("🎲 Surprise Me!", use_container_width=True)

    # -------------------------------------------------------------------------
    # ACTION HANDLERS
    # -------------------------------------------------------------------------
    if generate_btn:
        if not user_prompt.strip():
            st.warning("⚠️ Please enter a prompt before generating.")
        else:
            with st.spinner("🎨 Generating image from prompt..."):
                img, full_p = generate_image(
                    user_prompt, art_style, width, height, magic_enhance
                )
                if img is not None:
                    st.session_state.active_image = img
                    st.session_state.active_full_prompt = full_p
                    st.session_state.active_style = art_style
                    st.session_state.active_prompt = user_prompt

    elif surprise_btn:
        random_prompt = random.choice(SURPRISE_PROMPTS)
        st.session_state.prompt_input = random_prompt
        logger.info("[AUDIT] Surprise Me triggered. Selected: %s", random_prompt)
        with st.spinner("🎲 Generating surprise image..."):
            img, full_p = generate_image(
                random_prompt, art_style, width, height, magic_enhance
            )
            if img is not None:
                st.session_state.active_image = img
                st.session_state.active_full_prompt = full_p
                st.session_state.active_style = art_style
                st.session_state.active_prompt = random_prompt
                # Rerun to update text input value instantly
                st.rerun()

    # -------------------------------------------------------------------------
    # DISPLAY SECTION
    # -------------------------------------------------------------------------
    if st.session_state.active_image is not None:
        st.markdown('<div class="glass-panel">', unsafe_allow_html=True)
        st.success("✨ Masterpiece generated successfully!")
        
        # Display the specific prompt that was used if it was a surprise prompt
        if st.session_state.active_prompt in SURPRISE_PROMPTS:
            st.info(f"🎲 Surprise prompt used: **{st.session_state.active_prompt}**")

        # Expander showing full prompt sent to AI
        with st.expander("🔍 Show Full Prompt Sent to AI"):
            st.code(st.session_state.active_full_prompt, language="text")

        display_and_download(
            st.session_state.active_image, st.session_state.active_style
        )
        st.markdown('</div>', unsafe_allow_html=True)


if __name__ == "__main__":
    main()
