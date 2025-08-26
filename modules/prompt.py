"""Library for generating prompts."""
import re
from typing import Mapping

import jinja2

from modules import errors
from modules import schema
from presets import extract_shot_breakdown
from presets import generate_character_profile
from presets import generate_frame

PromptDict = Mapping[str, str]


def prepare_prompt_to_extract_shot_breakdown(
    request: schema.ExtractShotBreakdownRequest,
) -> PromptDict:
    """Generate the prompt dictionary for extracting shot breakdown from a script."""

    # Generate the user facing prompt involving details like the actual script,
    # shoot location, genre, etc.
    user_script = jinja2.Template(source=extract_shot_breakdown.USER_SCRIPT).render(
        {
            "SCRIPT": request.script,
            "ADDITIONAL_INFO": jinja2.Template(
                source=extract_shot_breakdown.SCENE_ADDITIONAL_INFO
            ).render(
                {
                    "LOCATION": request.location,
                    "FRAMES": request.num_frames,
                    "GENRE": request.genre,
                }
            ),
        }
    )

    # Populate the preamble part to be supplied to the model along with the
    # user script.
    #
    # Note: We explicitly pass an example output format for consistency reasons.
    preamble = jinja2.Template(source=extract_shot_breakdown.PREAMBLE).render(
        {"sample_output": extract_shot_breakdown.SAMPLE_OUTPUT}
    )
    return {"system": preamble, "user": user_script}


def prepare_prompt_for_comic(request: schema.ExtractShotBreakdownRequest) -> PromptDict:
    """Create a prompt for comic generation using a text2image model."""
    user_script = jinja2.Template(extract_shot_breakdown.COMIC_PREAMBLE).render(
        {"sample_output": extract_shot_breakdown.SAMPLE_OUTPUT}
    )
    return {"system": user_script, "user": request.script}


def prepare_prompt_to_generate_frame(
    request: schema.GenerateSceneRequest,
) -> PromptDict:
    """Create a prompt for generating frame images using text2image models."""

    visual_style = request.parameters.visual_style

    # Render the preamble template based on the visual style.
    preamble = jinja2.Template(generate_frame.STORYBOARD_PREAMBLE).render(
        {"SAMPLE_PROMPT": generate_frame.styles[visual_style]["SAMPLE"]}
    )
    user_script = f"The scene details are as below:\n{request.scene}\n"
    # user_script += f"The associated character profiles are:\n{request.characters}"

    return {"system": preamble, "user": user_script}


def prepare_prompt_to_generate_comic(
    request: schema.FrameGenerationRequest,
) -> PromptDict:
    """Create a prompt for generating frame images using text2image models."""

    visual_style = request.parameters.visual_style
    preamble = jinja2.Template(generate_frame.COMIC_PREAMBLE).render(
        {"SAMPLE_PROMPT": generate_frame.styles[visual_style]["SAMPLE"]}
    )
    user_script = f"The panels details are as below:\n{request.scene}\n"
    # user_script += f"The associated character profiles are:\n{request.characters}"
    return {"system": preamble, "user": user_script}


def prepare_prompt_to_generate_character_profile(
    request: schema.CharacterProfileRequest,
) -> PromptDict:
    """Create a prompt for generating character profiles images using text2image models."""

    # Populate the preamble with a sample prompt output based on the frame visual style.
    preamble = jinja2.Template(source=generate_character_profile.PREAMBLE).render()
    user_script = (
        f"The details about the person are as below:\n{str(request.character)}"
    )
    return {"system": preamble, "user": user_script}


def enhance_prompt(
    initial_prompt: str,
    request_params: schema.ImageGenParameters,
    prompt_model: callable = None,
) -> tuple[str, str]:
    """Enhance the prompt based on visual style and shot type."""

    try:
        combined_prompt = {
            "PROMPT": "",
            "NEGATIVE": "",
        }
        if request_params.visual_style != schema.VisualStyle.UNKNOWN:
            prompt = generate_frame.styles.get(request_params.visual_style)
            combined_prompt["PROMPT"] += prompt["PROMPT"].format(prompt=initial_prompt)
            combined_prompt["NEGATIVE"] += prompt["NEGATIVE"]
        else:
            combined_prompt["PROMPT"] += initial_prompt
            combined_prompt[
                "NEGATIVE"
            ] += "disfigured, unrealistic lips, misshapen teeth, unfinished face, low quality, blurry, low contrast, ugly, deformed, pixelated, extra organs, bad quality, distorted mouth, unfinished"

        if request_params.shot_type != schema.ShotType.UNKNOWN:
            prompt = generate_frame.shot_types.get(request_params.shot_type)
            combined_prompt["PROMPT"] += f", {prompt['PROMPT']}"
            combined_prompt["NEGATIVE"] += f", {prompt['NEGATIVE']}"

        if request_params.genre != schema.Genre.UNKNOWN:
            prompt = generate_frame.genres.get(request_params.genre)
            combined_prompt["PROMPT"] += f", {prompt['PROMPT']}"
            combined_prompt["NEGATIVE"] += f", {prompt['NEGATIVE']}"

        if prompt_model:
            combined_prompt["PROMPT"] = prompt_model(combined_prompt["PROMPT"])
        return combined_prompt["PROMPT"], combined_prompt["NEGATIVE"]

    except KeyError as exc:
        raise errors.InvalidVisualStyleSelectionError(
            f"Selected Visual Style: {request_params.visual_style} is either invalid or unsupported.",
            "E-3-2-33",
        ) from exc
    except Exception as exc:
        raise errors.UnknownErrorOccured(
            f"An error occurred while enhancing prompt for image generation. Check traceback for more details.",
            "E-3-2-36",
        )
