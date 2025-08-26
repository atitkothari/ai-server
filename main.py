"""Driver code for AI server."""
import json
import re
import tempfile
import time
from urllib.parse import urlparse

import requests
from fastapi import FastAPI
from fastapi import Request

from models import hugging_face
from models import open_ai
# from models import stable_diffusion
from models import flux
from modules import errors
from modules import img2img
from modules import parse
from modules import prompt
from modules import schema
from utils import common
from utils import constants
from utils import logging as custom_logger

app = FastAPI()

# Global Model objects
GPT_4_O_MODEL = open_ai.OpenAIModel("gpt-4o", constants.OPEN_AI_API_KEY)
# SDXL_MODEL = stable_diffusion.SDXLText2ImageModel(
#     base_dir=constants.ModelBaseDir, cache_dir=constants.ModelCacheDir
# )
# Just to cache things in the start for faster iterations later.
# SDXL_MODEL.load_ip_adapter()
FLUX_MODEL = flux.FluxModel()
FLUX_MODEL.load_ip_adapter()
# PROMPT_ENHANCER = hugging_face.EnhancePrompt(
#     base_dir=constants.ModelBaseDir, cache_dir=constants.ModelCacheDir
# )
# SDXL_VIDEO = stable_diffusion.SdxlImage2Gif(base_dir=constants.ModelBaseDir)

LOGGER = custom_logger.initialize_logger("ai-server")


@app.middleware("http")
async def add_request_id_header(request: Request, call_next):
    """Middleware to intercept request-id from each request and set it for the logger."""
    if request.method == "POST":
        request_id = request.headers.get("X-Request-ID", "default-request-id")
        request.state.request_id = request_id
        token = custom_logger.request_id_var.set(request_id)
        response = await call_next(request)
        custom_logger.request_id_var.reset(token)
    else:
        response = await call_next(request)
    return response


@app.get("/")
def read_root():
    return "All models initialized"


@app.post("/extract_shot_breakdown")
def extract_shot_breakdown(
    request: schema.ExtractShotBreakdownRequest,
) -> schema.ExtractShotBreakdownResponse:
    """Callback function to extract scenes and characters related details from script.

    Responsible for handling requests for extracting details about all the
    scenes and character profiles from a given script such that the
    prompt carries both script context and character level consistency.

    Args:
        request: A ExtractDetailsRequest object.

    Returns:
        An object of ExtractDetailsResponse populated with scene and
    character details.

    Raises:
        InternalServerError: If there is an error in the internal code.
    """
    try:
        start_time = time.time()
        LOGGER.info(f"Processing request for extract_shot_breakdown endpoint!")
        prompt_dict = prompt.prepare_prompt_to_extract_shot_breakdown(request)
        model_response = GPT_4_O_MODEL.generate_response(prompt_dict)
        characters = parse.parse_characters(model_response)
        frames, ts = parse.parse_frames(model_response, characters)
        total_frames = ts if request.num_frames == 0 else request.num_frames
        LOGGER.info(
            f"{len(frames)} frames extracted. {len(characters)} characters extracted."
        )
        if len(frames) < total_frames:
            # In the scenario where we're not getting the required number of frames,
            # we call the model again in a conversation loop to generate the
            # next `n` frames required with the cap for max no of retries.
            prompt_dict.update(
                {
                    "assistant": model_response,
                }
            )
            max_tries = 3
            while len(frames) < total_frames or max_tries > 0:
                frames_left = total_frames - len(frames)
                prompt_dict.update(
                    {
                        "user": f"Great! Can you generate the details for the remaining {frames_left} frames?"
                    }
                )
                model_response = GPT_4_O_MODEL.generate_response(prompt_dict)
                sc, _ = parse.parse_frames(model_response, characters)
                frames.extend(sc)
                prompt_dict.update(
                    {
                        "assistant": model_response,
                    }
                )
                max_tries -= 1
                LOGGER.info(f"Extracted {len(sc)} more frames.")

            if total_frames > len(frames):
                LOGGER.warn(f"E-3-2-32:: Model generated less frames than desired.")
        LOGGER.info(
            f"Time taken to extract shot breakdown: {(time.time() - start_time):.2f} seconds"
        )
        LOGGER.info(
            f"Processed request for extract_shot_breakdown endpoint successfully!!"
        )
        return schema.ExtractShotBreakdownResponse(
            script=request.script,
            scenes=frames,
            characters=characters,
        )
    except errors.BaseCustomError as exc:
        custom_logger.log_exceptions(LOGGER, exc)
        raise errors.InternalServerError(
            "An error occured while generating shot breakdown. Please refer logs for more details."
        )


@app.post("/generate_character_profile")
def generate_character_profile(
    request: schema.CharacterProfileRequest,
) -> schema.CharacterProfileResponse:
    """Callback function to generate profiles for a character.

    Responsible for handling requests for generates profiles images for the
    given character characteristics.

    Args:
        request: A CharacterProfileRequest object.

    Returns:
        An object of CharacterProfileResponse populated with the character profile
    and a description.

    Raises:
        InternalServerError: If there is an error in the internal code.
    """
    try:
        start_time = time.time()
        LOGGER.info(f"Processing request for generate_character_profile endpoint!")
        model_response = GPT_4_O_MODEL.generate_response(
            prompt_dict=prompt.prepare_prompt_to_generate_character_profile(request),
        )
        modified_prompt, neg_prompt = prompt.enhance_prompt(
            model_response,
            request.parameters,
        )
        if request.parameters.negative_prompt == "":
            request.parameters.negative_prompt = neg_prompt

        image = FLUX_MODEL.predict(
            prompt=modified_prompt,
            params=request.parameters,
            use_ip_adapter=False,
            character_images=[],
        )
        b64_results = common.convert_to_b64(image)
        end_time = time.time() - start_time
        LOGGER.info(f"Time taken to generate a frame: {end_time:.2f} seconds")
        LOGGER.info(
            f"Processed request for generate_character_profile endpoint successfully!!"
        )
        return schema.CharacterProfileResponse(
            description=model_response,
            result=schema.ImageGenResult(
                prompt=modified_prompt,
                data=b64_results,
                time_taken=str(end_time),
            ),
        )
    except errors.BaseCustomError as exc:
        custom_logger.log_exceptions(LOGGER, exc)
        raise errors.InternalServerError(
            "An error occured while generating the frame. Please refer logs for more details."
        )


@app.post("/generate_scene")
def generate_frame(
    request: schema.GenerateSceneRequest,
) -> schema.GenerateSceneResponse:
    """Callback function to handle frame generation.

    Responsible for handling requests for generating image frames w.r.t
    the given prompt and (sometimes) negative-prompt as well such that the frame
    carries both prompt context and character level consistency.

    Args:
        request: A GenerateFrameRequest object.

    Returns:
        An object of GenerateFrameResponse populated with scene image encoded in
    base64 along with time taken and the prompt used to generate it.

    Raises:
        InternalServerError: If there is an error in the internal code.
    """
    try:
        start_time = time.time()
        LOGGER.info(f"Processing request for generate_scene endpoint!")
        model_response = GPT_4_O_MODEL.generate_response(
            prompt_dict=prompt.prepare_prompt_to_generate_frame(request),
        )
        modified_prompt, neg_prompt = prompt.enhance_prompt(
            model_response,
            request.parameters,
        )
        print(modified_prompt)
        if request.parameters.negative_prompt == "":
            request.parameters.negative_prompt = neg_prompt

        use_ip_adapter = False
        character_images = []
        if request.characters:
            character_images = [
                common.read_image_from_s3(img_path) for img_path in request.characters
            ]
            use_ip_adapter = True

        image = FLUX_MODEL.predict(
            prompt=modified_prompt,
            params=request.parameters,
            use_ip_adapter=use_ip_adapter,
            character_images=character_images,
        )
        b64_results = common.convert_to_b64(image)
        end_time = time.time() - start_time
        LOGGER.info(f"Time taken to generate a frame: {end_time:.2f} seconds")
        LOGGER.info(f"Processed request for generate_scene endpoint successfully!!")
        return schema.GenerateSceneResponse(
            description=model_response,
            result=schema.ImageGenResult(
                prompt=modified_prompt,
                data=b64_results,
                time_taken=str(end_time),
            ),
        )
    except errors.BaseCustomError as exc:
        custom_logger.log_exceptions(LOGGER, exc)
        raise errors.InternalServerError(
            "An error occured while generating the frame. Please refer logs for more details."
        )


@app.post("/regenerate_scene")
def regenerate_scene(
    request: schema.RegenerateSceneRequest,
) -> schema.ImageGenResult:
    """Callback function to regnerate frame based on the provided prompt.

    Responsible for handling requests for generating image frames w.r.t
    the given prompt and (sometimes) negative-prompt.

    Args:
        request: A RegenerateSceneRequest object.

    Returns:
        An object of ImageGenResult populated with scene image encoded in base64 along with time taken.

    Raises:
        InternalServerError: If there is an error in the internal code.
    """
    try:
        start_time = time.time()
        LOGGER.info(f"Processing request for regenerate_scene endpoint!")
        modified_prompt, neg_prompt = prompt.enhance_prompt(
            request.request.prompt,
            request.request.parameters,
        )
        if request.request.parameters.negative_prompt == "":
            request.request.parameters.negative_prompt = neg_prompt

        b64_image = ""
        if request.request.reference_image != "":
            config = img2img.prepare_reference_image_config(request, modified_prompt)
            config["url"] = config["url"].replace(
                "WEB_UI_IP", constants.WEBUI_INSTANCE_IP
            )
            LOGGER.info(f"It is a ReferenceImage request.")
            # LOGGER.info(f"Url: {config['url']} and payload:")
            # LOGGER.info(json.dumps(config["payload"], indent=2))
            response = requests.request(
                "POST",
                config["url"],
                headers={"Content-Type": "application/json"},
                data=json.dumps(config["payload"]),
            )
            b64_image = response.json()["images"][0]
        else:
            LOGGER.info(f"It is a Regenerate request.")
            use_ip_adapter = False
            character_images = []
            if request.characters:
                character_images = [
                    common.read_image_from_s3(img_path)
                    for img_path in request.characters
                ]
                use_ip_adapter = True
            image = FLUX_MODEL.predict(
                prompt=modified_prompt,
                params=request.request.parameters,
                use_ip_adapter=use_ip_adapter,
                character_images=character_images,
            )
            b64_image = common.convert_to_b64(image)
        end_time = time.time() - start_time
        LOGGER.info(f"Time taken to generate a frame: {end_time:.2f} seconds")
        LOGGER.info(f"Processed request for regenerate_scene endpoint successfully!!")
        return schema.ImageGenResult(
            prompt=modified_prompt,
            data=b64_image,
            time_taken=str(end_time),
        )
    except (errors.BaseCustomError, KeyError) as exc:
        custom_logger.log_exceptions(LOGGER, exc)
        raise errors.InternalServerError(
            "An error occured while regenerating the frame. Please refer logs for more details."
        )


@app.post("/inpaint_scene")
def inpaint_frame(request: schema.InpaintSceneRequest) -> schema.ImageGenResult:
    """Callback function to handle all inpaint scene requests.

    Responsible for handling requests for inpainting related requests e.g.
        1) Add object
        2) Remove object
        3) Expression change
        4) Weather Change
        5) Color Change
        6) Background Change
    using the given prompt and (sometimes) negative-prompt as well such that
    the masked part of the scene gets inpainted.

    Args:
        request: An InpaintSceneRequest object.

    Returns:
        An object of ImageGenResult populated with scene image encoded in
    base64 along with time taken.

    Raises:
        InternalServerError: If there is an error in the internal code.
    """
    # Based on the InpaintAction defined in the request, construct the request object
    # to send to the inpainting service.
    try:
        start = time.time()
        LOGGER.info(f"Processing request for inpaint_scene endpoint!")
        LOGGER.info(f"Request type: {str(request.inpaint_action.value).lower()}")

        modified_prompt, neg_prompt = prompt.enhance_prompt(
            request.inpainting_prompt,
            request.parameters,
        )

        if request.parameters.negative_prompt == "":
            request.parameters.negative_prompt = neg_prompt
        config = img2img.prepare_inpaint_config(request, request.inpainting_prompt)
        config["url"] = config["url"].replace("WEB_UI_IP", constants.WEBUI_INSTANCE_IP)

        if request.inpaint_action == request.inpaint_action.REMOVE_OBJECT:
            base64_image = config["data"]
        else:
            # LOGGER.info(f"Url: {config['url']} and pa`yload:")
            # LOGGER.info(json.dumps(config["payload"], indent=2))
            response = requests.request(
                "POST",
                config["url"],
                headers={"Content-Type": "application/json"},
                data=json.dumps(config["payload"]),
            )
            base64_image = response.json()["images"][0]
        LOGGER.info(f"Processed request for inpaint_scene endpoint successfully!!")
        return schema.ImageGenResult(
            prompt=modified_prompt,
            data=base64_image,
            time_taken=str(time.time() - start),
        )
    except (errors.BaseCustomError, KeyError) as exc:
        custom_logger.log_exceptions(LOGGER, exc)
        raise errors.InternalServerError(
            "An error occured while inpainting the frame. Please refer logs for more details."
        )


@app.post("/split_script")
def split_script(request: schema.ExtractScenesRequest) -> schema.ExtractScenesResponse:
    try:
        LOGGER.info("Received request to split script.")

        parsed_url = urlparse(request.filename_url)
        if parsed_url.scheme != "https":
            LOGGER.info(
                "Unsupported URL scheme. Only 'https' URLs are supported for S3."
            )
            raise errors.HTTPException(
                "Unsupported URL scheme. Only 'https' URLs are supported for S3",
                "E-3-1-11",
            )

        # Fetch the file content using the URL string
        file_content = common.fetch_s3_file(request.filename_url)
        LOGGER.info("File fetched successfully from S3.")

        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(file_content)
            temp_file_path = temp_file.name

        file_path = parsed_url.path.lstrip("/")
        if file_path.endswith(".fountain"):
            LOGGER.info("Parsing .fountain script.")
            scenes = parse.split_script_fountain(temp_file_path)
        elif file_path.endswith((".pdf", ".txt")):
            LOGGER.info("Parsing .pdf or .txt script.")
            scenes = parse.split_script(temp_file_path, file_path)
        else:
            LOGGER.info("Unsupported file format.")
            raise errors.UnsupportedFileFormat(
                "Unsupported file format, only .pdf, .txt and .fountain are supported.",
                "E-3-1-12",
            )

        # formatted_scene = parse.format_scenes(scenes)
        LOGGER.info("Script parsed and formatted successfully.")
        return schema.ExtractScenesResponse(scenes=scenes)

    except errors.BaseCustomError as exc:
        custom_logger.log_exceptions(LOGGER, exc)
        raise errors.InternalServerError(
            "An error occurred while Scene exctration. Please refer to the logs for more details."
        )

@app.post("/generate_image")
def generate_image(
    request: schema.FrameGenerationRequest,
) -> schema.FrameGenerationResponse:
    try:
        start_time = time.time()
        LOGGER.info("Processing request for generate_image endpoint!")
        modified_prompt, neg_prompt = prompt.enhance_prompt(
            request.prompt, request.parameters
        )
        request.parameters.negative_prompt += neg_prompt
        use_ip_adapter = False
        character_images = []
        
        if request.characters:
            LOGGER.info("Loading character images from S3...")
            character_images = [
                common.read_image_from_s3(img_path) for img_path in request.characters
            ]
            use_ip_adapter = True

        LOGGER.info("Generating image with modified prompt and parameters...")
        image = FLUX_MODEL.predict(
            prompt=modified_prompt,
            params=request.parameters,
            use_ip_adapter=use_ip_adapter,
            character_images=character_images,
        )

        b64_results = common.convert_to_b64(image)
        end_time = time.time() - start_time
        LOGGER.info(f"Time taken to generate image: {end_time:.2f} seconds")
        LOGGER.info("Processed request for generate_image endpoint successfully!!")

        return schema.FrameGenerationResponse(prompt=modified_prompt, image=b64_results)
    except errors.BaseCustomError as exc:
        custom_logger.log_exceptions(LOGGER, exc)
        raise errors.InternalServerError(
            "An error occurred while Comic Image Generation. Please refer to the logs for more details."
        )
    except Exception as e:
        custom_logger.log_exceptions(LOGGER, e)
        raise errors.InternalServerError(
            "An unexpected error occurred. Please check the logs for more details."
        )


# @app.post("/generate_image")
# def generate_image(
#     request: schema.FrameGenerationRequest,
# ) -> schema.FrameGenerationResponse:
#     try:
#         modified_prompt, neg_prompt = prompt.enhance_prompt(
#             request.prompt, request.parameters, PROMPT_ENHANCER if request.use_prompt_enhancer else None
#         )
#         request.parameters.negative_prompt += neg_prompt
#         use_ip_adapter = False
#         character_images = []
#         if request.characters:
#             character_images = [
#                 common.read_image_from_s3(img_path) for img_path in request.characters
#             ]
#             use_ip_adapter = True
#         image = SDXL_MODEL.predict(
#             prompt=modified_prompt,
#             params=request.parameters,
#             use_ip_adapter=use_ip_adapter,
#             character_images=character_images,
#         )
#         b64_results = common.convert_to_b64(image)
#         return schema.FrameGenerationResponse(prompt=modified_prompt, image=b64_results)
#     except Exception as e:
#         custom_logger.log_exceptions(LOGGER, e)
#         raise errors.InternalServerError(
#             "An error occurred while Comic Image Generation. Please refer to the logs for more details."
#         )


# @app.post("/create_animation")
# def create_animation(request: schema.AnimaionRequest) -> schema.AnimationResponse:
#     """
#     Generate an animation from a base64-encoded image.
#     Args:
#         request (schema.AnimaionRequest): Request object containing base64 image, height, and width.
#     Returns:
#         schema.AnimationResponse: Response object with base64-encoded GIF of the animation.
#     """
#     try:
#         # Process the image
#         LOGGER.info("Starting animation generation process...")
#         gif_base64 = SDXL_VIDEO.predict(
#             request.reference_image, request.height, request.width
#         )
#         LOGGER.info("Animation completed successfully.")
#         return schema.AnimationResponse(gif_base64=gif_base64)
#     except errors.BaseCustomError as exc:
#         custom_logger.log_exceptions(LOGGER, exc)
#         raise errors.InternalServerError(
#             "An error occurred while generating the animation. Please refer to the logs for more details."
#         )
