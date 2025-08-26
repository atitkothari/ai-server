"""Common utility functions used throughout the server."""
import base64
from io import BytesIO
from typing import Union
from urllib.parse import urlparse

import boto3
import numpy as np
from PIL import Image

from modules import schema

Gender = schema.Gender


def get_gender(value: str) -> Gender:
    if value.lower() == "male":
        return Gender.MALE
    elif value.lower() == "female":
        return Gender.FEMALE
    else:
        return Gender.UNKNOWN


def convert_to_b64(image: Image) -> str:
    buffered = BytesIO()
    image.save(buffered, format="JPEG")
    img_b64 = base64.b64encode(buffered.getvalue()).decode("utf-8")
    return img_b64


def read_image_from_s3(image_url: str) -> str:
    return Image.open(BytesIO(fetch_s3_file(image_url)))


def save_array_to_img(img_arr, img_p):
    Image.fromarray(img_arr.astype(np.uint8)).save(img_p)


def load_img_to_array(img_p):
    if isinstance(img_p, Image.Image):  # Check if img_p is a PIL image
        return np.array(img_p)
    else:
        img = Image.open(img_p)
        return np.array(img)


def fetch_s3_file(source: Union[str, dict], region_name: str = "ap-south-1") -> bytes:
    print(f"The url is: {source}")
    s3_client = boto3.client("s3", region_name=region_name)

    if isinstance(source, str):
        # Handle URL input
        parsed_url = urlparse(source)
        bucket_name = parsed_url.netloc.split(".")[0]
        file_path = parsed_url.path.lstrip("/")
    elif isinstance(source, dict):
        # Handle dictionary input
        bucket_name = source.get("bucket_name")
        file_path = source.get("file_key")
        if not bucket_name or not file_path:
            raise ValueError(
                "Dictionary input must contain 'bucket_name' and 'file_key'"
            )

    print(f"Bucket: {bucket_name} and path: {file_path}")
    response = s3_client.get_object(Bucket=bucket_name, Key=file_path)
    file_content = response["Body"].read()

    return file_content
