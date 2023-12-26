from PIL import Image
from io import BytesIO
import requests
import re

email_pattern = re.compile(r"[^@]+@[^@]+\.[^@]+")
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}
SUCCESSFUL = 200

def is_allowed_format(filename: str) -> bool:
    """Checks if the image has the accepted format.

    Args:
        filename (str): Name of the file.

    Returns:
        bool: True if it's a png, jpg, jpeg, or gif.
    """
    return False if "." not in filename else filename.split(".")[-1].lower() in ALLOWED_EXTENSIONS


def make_pfp(image_binary: bytes, size: int, format="WebP") -> bytes:
    """Makes the received image squared and converts it to WebP

    Args:
        image_binary (bytes): Image information.
        size (int): Size of the sides of the square.

    Returns:
        bytes: WebP image in binary format
    """
    image = Image.open(BytesIO(image_binary)).resize((size, size))
    image_buffer = BytesIO()
    image.save(image_buffer, format=format)
    return image_buffer.getvalue()

def optimize_image(image_binary: bytes, format="WebP", quality=40) -> bytes:
    image = Image.open(BytesIO(image_binary))
    image_buffer = BytesIO()
    image.save(image_buffer, format=format, quality=quality)
    image.save("here.WebP", format=format, quality=quality)
    return image_buffer.getvalue()

def get_country_names(lower: bool) -> list[str]:
    """Gets the country names from source and returns a list with all
    the country names, or a list with only Argentina in it.

    Args:
        lower (bool): Get the names on lower case.

    Returns:
        list[str]: List of country names.
    """
    response = requests.get("https://restcountries.com/v2/all")
    if response.status_code == SUCCESSFUL:
        return [
            country["name"].lower() if lower else country["name"]
            for country in response.json()
        ]
    return ["argentina" if lower else "Argentina"]    