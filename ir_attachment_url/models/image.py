from odoo import tools
import re


supper_image_resize_images = tools.image_resize_images


def image_resize_images(vals, big_name='image', medium_name='image_medium',
                        small_name='image_small', sizes=None):
    """ Update ``vals`` with image fields resized as expected. """
    if not sizes:
        sizes = {}
    url = [vals[key] for key in vals if check_url(vals[key])]
    if big_name not in vals and medium_name not in vals and \
            small_name not in vals:
        url = False
    if url and check_url(url[0]):
        url = url[0]
    if url:
        vals.update({big_name: url,
                     medium_name: url,
                     small_name: url})
    else:
        print("$$$$$$$$$$$image_resize_images")
        supper_image_resize_images(vals, big_name, medium_name, small_name,
                            sizes=sizes)


def check_url(value):
    if value:
        return isinstance(value, str) and re.findall(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', value)


super_image_resize_image = tools.image_resize_image


def image_resize_image(base64_source, size=(1024, 1024), encoding='base64', filetype=None, avoid_if_small=False, upper_limit=False):
    source_for_check = base64_source.decode("utf-8") if isinstance(base64_source, bytes) else base64_source
    if check_url(source_for_check):
        return source_for_check
    return super_image_resize_image(base64_source, size=size, encoding=encoding, filetype=filetype, avoid_if_small=avoid_if_small, upper_limit=upper_limit)


def image_resize_image_big(base64_source, size=(1024, 1024), encoding='base64', filetype=None, avoid_if_small=True):
    return image_resize_image(base64_source, size, encoding, filetype, avoid_if_small)


def image_resize_image_medium(base64_source, size=(128, 128), encoding='base64', filetype=None, avoid_if_small=False):
    return image_resize_image(base64_source, size, encoding, filetype, avoid_if_small)


def image_resize_image_small(base64_source, size=(64, 64), encoding='base64', filetype=None, avoid_if_small=False):
    return image_resize_image(base64_source, size, encoding, filetype, avoid_if_small)


def image_get_resized_images(base64_source, return_big=False, return_medium=True, return_small=True,
                                     big_name='image', medium_name='image_medium', small_name='image_small',
                                     avoid_resize_big=True, avoid_resize_medium=False, avoid_resize_small=False, sizes=None):
    if not sizes:
        sizes = {}
    return_dict = dict()
    size_big = sizes.get(big_name, (1024, 1024))
    size_medium = sizes.get(medium_name, (128, 128))
    size_small = sizes.get(small_name, (64, 64))
    if isinstance(base64_source, tools.pycompat.text_type):
        base64_source = base64_source.encode('ascii')
    if return_big:
        return_dict[big_name] = image_resize_image_big(base64_source, avoid_if_small=avoid_resize_big, size=size_big)
    if return_medium:
        return_dict[medium_name] = image_resize_image_medium(base64_source, avoid_if_small=avoid_resize_medium, size=size_medium)
    if return_small:
        return_dict[small_name] = image_resize_image_small(base64_source, avoid_if_small=avoid_resize_small, size=size_small)
    return return_dict


tools.image_resize_images = image_resize_images
tools.image_resize_image = image_resize_image
tools.image_resize_image_big = image_resize_image_big
tools.image_resize_image_medium = image_resize_image_medium
tools.image_resize_image_small = image_resize_image_small
tools.image_get_resized_images = image_get_resized_images
