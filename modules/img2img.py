"""Code for various image-2-image operations."""
import base64
import json
import os
from io import BytesIO
from typing import Mapping

import numpy as np
from PIL import Image as PILImage

from models import hugging_face
from modules import errors
# from modules import lama_inpaint
from modules import schema
from utils import common
from utils import constants

InpaintAction = schema.InpaintAction

# RESNET_MODEL = hugging_face.Resnet(
#     base_dir=constants.ModelBaseDir, cache_dir=constants.ModelCacheDir
# )


def prepare_inpaint_config(
    request: schema.InpaintSceneRequest, prompt: str
) -> Mapping[str, str]:
    """Edit values in the inpaint config based on the action specified."""
    try:
        if request.inpaint_action == InpaintAction.REMOVE_OBJECT:
            base_img = common.load_img_to_array(
                PILImage.open(BytesIO(base64.b64decode(request.base_image)))
            )
            mask_img = common.load_img_to_array(
                PILImage.open(BytesIO(base64.b64decode(request.mask_image)))
            )
            img_inpainted = lama_inpaint.inpaint_img_with_lama(
                base_img,
                mask_img,
                "models/lama/configs/prediction/default.yaml",
                constants.S3_BUCKET_PATH,
                device="cuda",
            )

            # Convert the inpainted image array back to a PIL image and then to base64
            inpainted_img_pil = PILImage.fromarray(img_inpainted)
            buffered = BytesIO()
            inpainted_img_pil.save(buffered, format="PNG")
            image_base64 = base64.b64encode(buffered.getvalue()).decode("utf-8")

            if image_base64:
                return {
                    "data": image_base64,
                }

        inpaint_action = str(request.inpaint_action.value).lower()
        config = json.load(
            open(
                os.path.join(constants.InpaintConfigDir, f"{inpaint_action}.json"),
                encoding="utf-8",
            )
        )
        config["payload"]["prompt"] = prompt
        config["payload"]["init_images"] = [request.base_image]
        config["payload"]["height"] = request.parameters.height
        config["payload"]["width"] = request.parameters.width
        if request.parameters.negative_prompt:
            config["payload"]["negative_prompt"] = request.parameters.negative_prompt

        if (
            request.inpaint_action == InpaintAction.ADD_OBJECT
            or request.inpaint_action == InpaintAction.CHANGE_EXPRESSION
            or request.inpaint_action == InpaintAction.CHANGE_COLOR
            or request.inpaint_action == InpaintAction.CHANGE_BACKGROUND
        ):
            config["payload"]["mask"] = request.mask_image

        if (
            request.inpaint_action == InpaintAction.CHANGE_WEATHER
            or request.inpaint_action == InpaintAction.CHANGE_COLOR
        ):
            if request.inpaint_action == InpaintAction.CHANGE_WEATHER:
                config["payload"]["alwayson_scripts"]["ControlNet"]["args"][1]["image"][
                    "image"
                ] = request.base_image
                config["payload"]["mask"] = RESNET_MODEL(request.base_image)
            config["payload"]["alwayson_scripts"]["ControlNet"]["args"][0]["image"][
                "image"
            ] = request.base_image

        return config
    except KeyError as exc:
        raise errors.InvalidConfigError(
            f"Invalid Key for inpaint config generation. Check traceback for more info.",
            "E-3-1-03",
        ) from exc
    except json.decoder.JSONDecodeError as exc:
        raise errors.InvalidConfigError(
            f"Invalid json for inpaint config generation. Check traceback for more info.",
            "E-3-1-04",
        ) from exc
    except errors.ModelResponseParseError as exc:
        raise exc
    except Exception as exc:
        raise errors.UnknownErrorOccured(
            f"An error occurred while generating config for image inpainting.",
            "E-3-1-05",
        )


def prepare_reference_image_config(
    request: schema.RegenerateSceneRequest, prompt: str
) -> Mapping[str, str]:
    try:
        config = json.load(
            open(
                os.path.join(
                    constants.ReferenceImageConfigDir,
                    f"{str(request.options.value).lower()}.json",
                ),
                encoding="utf-8",
            )
        )
        config["payload"]["prompt"] = prompt
        config["payload"]["alwayson_scripts"]["ControlNet"]["args"][0]["image"][
            "image"
        ] = request.request.reference_image
        config["payload"]["height"] = request.request.parameters.height
        config["payload"]["width"] = request.request.parameters.width
        config["payload"][
            "negative_prompt"
        ] = request.request.parameters.negative_prompt
        return config
    except KeyError as exc:
        raise errors.InvalidConfigError(
            f"Invalid Key for reference image generation. Check traceback for more info.",
            "E-3-1-06",
        ) from exc
    except json.decoder.JSONDecodeError as exc:
        raise errors.InvalidConfigError(
            f"Invalid json for reference image generation. Check traceback for more info.",
            "E-3-1-07",
        ) from exc
    except Exception as exc:
        raise errors.UnknownErrorOccured(
            f"An error occurred while generating config for reference image generation.",
            "E-3-1-08",
        )
