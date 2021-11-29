from django.core.files.base import ContentFile
import base64
import six
import uuid


def get_file_extension(file_name, decoded_file):
    import imghdr

    extension = imghdr.what(file_name, decoded_file)
    extension = "jpg" if extension == "jpeg" else extension

    return extension


def decode_base64_to_image(data):
    # Check if this is a base64 string
    if not isinstance(data, six.string_types):
        return

    # Check if the base64 string is in the "data:" format
    if 'data:' in data and ';base64,' in data:
        # Break out the header from the base64 content
        header, data = data.split(';base64,')

    # Try to decode the file. Return validation error if it fails.
    try:
        decoded_file = base64.b64decode(data)
    except TypeError:
        return

    # Generate file name:
    file_name = str(uuid.uuid4())[:12]  # 12 characters are more than enough.
    # Get the file name extension:
    file_extension = get_file_extension(file_name, decoded_file)

    complete_file_name = f"{file_name}.{file_extension}"

    return ContentFile(decoded_file, name=complete_file_name)
