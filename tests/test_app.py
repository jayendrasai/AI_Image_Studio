"""Unit tests for AI Image Studio Pro core logic."""

from io import BytesIO
import urllib.parse
from unittest.mock import MagicMock, patch
from PIL import Image
from app import generate_image


def test_generate_image_success():
    """Test successful image generation and path parameter URL encoding."""
    # Setup mock image content
    img = Image.new("RGB", (512, 512), color="red")
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    mock_content = buffer.getvalue()

    # Mock response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.headers = {"content-type": "image/png"}
    mock_response.content = mock_content

    # Mock requests.get and st.error
    with patch("requests.get", return_value=mock_response) as mock_get, \
         patch("streamlit.error") as mock_st_error:

        result_img, full_prompt = generate_image(
            prompt="A happy dog",
            art_style_val="Anime",
            w=512,
            h=512,
            enhance=False
        )

        assert result_img is not None
        assert result_img.size == (512, 512)
        assert full_prompt == "A happy dog, Anime style"
        mock_get.assert_called_once()
        
        # Check that the prompt was encoded in the URL path segment
        called_url = mock_get.call_args[0][0]
        assert "A%20happy%20dog%2C%20Anime%20style" in called_url
        assert "width=512" in called_url
        assert "height=512" in called_url
        mock_st_error.assert_not_called()


def test_generate_image_enhance():
    """Test enhancement logic adds exact boost phrase correctly."""
    # Mock response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.headers = {"content-type": "image/png"}
    img = Image.new("RGB", (256, 256))
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    mock_response.content = buffer.getvalue()

    with patch("requests.get", return_value=mock_response) as mock_get:
        _, full_prompt = generate_image(
            prompt="A cool cat",
            art_style_val="Cyberpunk",
            w=256,
            h=256,
            enhance=True
        )

        expected_boost = ", masterpiece, 8k resolution, highly detailed, trending on artstation, unreal engine 5 render"
        assert full_prompt == f"A cool cat, Cyberpunk style{expected_boost}"
        called_url = mock_get.call_args[0][0]
        
        # URL path segment must contain the encoded boost words
        encoded_boost = urllib.parse.quote(expected_boost)
        assert encoded_boost in called_url


def test_generate_image_empty_prompt():
    """Test validation fails closed for whitespace/empty prompts."""
    with patch("requests.get") as mock_get:
        result_img, _ = generate_image(
            prompt="   ",
            art_style_val="Fantasy",
            w=512,
            h=512,
            enhance=False
        )
        assert result_img is None
        mock_get.assert_not_called()


def test_generate_image_invalid_dimensions():
    """Test validation fails closed for out of boundary dimensions."""
    with patch("requests.get") as mock_get, \
         patch("streamlit.error") as mock_st_error:
        # Under minimum limit
        result_img_under, _ = generate_image(
            prompt="A spaceship",
            art_style_val="3D Render",
            w=100,
            h=512,
            enhance=False
        )
        assert result_img_under is None

        # Over maximum limit
        result_img_over, _ = generate_image(
            prompt="A spaceship",
            art_style_val="3D Render",
            w=512,
            h=2048,
            enhance=False
        )
        assert result_img_over is None

        mock_get.assert_not_called()
        assert mock_st_error.call_count == 2


def test_generate_image_http_error():
    """Test API error statuses display appropriate messages."""
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_response.content = b"Not Found"

    with patch("requests.get", return_value=mock_response), \
         patch("streamlit.error") as mock_st_error:

        result_img, _ = generate_image(
            prompt="Failed request",
            art_style_val="Oil Painting",
            w=512,
            h=512,
            enhance=False
        )
        assert result_img is None
        mock_st_error.assert_called_once()


def test_display_and_download_naming():
    """Test image is displayed and downloaded with correctly formatted filename."""
    img = Image.new("RGB", (256, 256))

    with patch("streamlit.image") as mock_st_image, \
         patch("streamlit.download_button") as mock_st_download:

        from app import display_and_download
        display_and_download(img, "Oil Painting")

        mock_st_image.assert_called_once_with(img, use_container_width=True)
        mock_st_download.assert_called_once()

        # Check download button parameters
        kwargs = mock_st_download.call_args[1]
        assert kwargs["file_name"] == "oil_painting_image.png"
        assert kwargs["mime"] == "image/png"
