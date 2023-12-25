from PIL import Image
from io import BytesIO

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}


def is_allowed_format(name: str) -> bool:
    """Checks if the image has the accepted format .

    Args:
        name (str): name of the file.

    Returns:
        bool: true if it's a png, jpg, jpeg or gif.
    """
    print(name.split(".")[-1].lower())
    if "." in name:
        return name.split(".")[-1].lower() in ALLOWED_EXTENSIONS
    return False


def make_pfp(image_binary, size):
    """Makes the recived image squared and converts it to WebP

    Args:
        image_binary (_type_): _description_
        size (_type_): _description_

    Returns:
        _type_: _description_
    """    
    image = Image.open(BytesIO(image_binary)).resize((size, size))
    image_buffer = BytesIO()
    image.save(image_buffer, format="WebP")
    return image_buffer.getvalue()
