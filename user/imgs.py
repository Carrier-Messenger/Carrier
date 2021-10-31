from PIL import Image
from io import BytesIO
from django.core.files.base import ContentFile


def crop_center(pil_img, crop_width, crop_height):
    img_width, img_height = pil_img.size
    return pil_img.crop(((img_width - crop_width) // 2,
                         (img_height - crop_height) // 2,
                         (img_width + crop_width) // 2,
                         (img_height + crop_height) // 2))


def crop_max_square(pil_img):
    return crop_center(pil_img, min(pil_img.size), min(pil_img.size))


def cut(img, user):
    filename = img.name
    img = Image.open(img)

    img = img.convert('RGB')

    img = crop_max_square(img).resize((256, 256), Image.LANCZOS)

    f = BytesIO()
    try:
        img.save(f, format='jpeg')
        user.pfp.save(filename, ContentFile(f.getvalue()))
        user.save()
    finally:
        f.close()
