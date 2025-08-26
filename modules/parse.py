"""Code for model response parsing logic."""
import hashlib
import re
import xml.etree.ElementTree as ET

import pdfplumber

from modules import errors
from modules import schema

Gender = schema.Gender
Character = schema.Character
CharacterExpression = schema.CharacterExpression
Characters = list[Character]
Scene = schema.Scene
Scenes = list[Scene]


def generate_character_id(name: str) -> str:
    """Generates a unique character id for each character."""
    hash_val = hashlib.shake_256(name.encode("utf-8")).hexdigest(4)
    return f"{name}-{hash_val}"


def get_shot_type(shot_type: str):
    if shot_type == "WIDE_SHOT" or shot_type == "MEDIUM_SHOT" or shot_type == "CLOSE_UP" or shot_type == "EXTREME_CLOSE_UP":
        return shot_type
    else:
        return "MEDIUM_SHOT"


def map_character_ids(
    character_expressions: list[tuple[str]], characters: Characters
) -> list[CharacterExpression]:
    character_exps = []
    try:
        for char in character_expressions:
            for c in characters:
                if char[0] == c.name:
                    character_exps.append(
                        CharacterExpression(
                            character_id=c.character_id, expression=char[1]
                        )
                    )
                    break
        return character_exps
    except Exception as exc:
        raise errors.InvalidFrameBreakdownError(
            f"Unable to fetch character expressions for the current frame.\nSome or all characters mentioned does not exist: {character_expressions}.\nAll characters: {[c.name for c in characters]}",
            "E-3-2-31",
        ) from exc


def parse_characters(model_response: str) -> Characters:
    """Parses the model response to extract out character profiles."""
    match_group = re.search("(```characters[^```]*```)", model_response)
    if not match_group:
        raise errors.ModelResponseParseError(
            f"No character profiles found in model response.\nModel response: {model_response}",
            "E-3-2-21",
        )

    try:
        match_string = match_group.group(0).strip("```characters").strip()
        lines = match_string.split("\n")
        total_characters = int(re.search("[0-9]+", lines[0]).group(0))
        characters = eval("".join(lines[1:]))
    except Exception as exc:
        raise errors.ModelResponseParseError(
            f"Faced an error while trying to parse character profiles.\nModel response: {model_response}",
            "E-3-2-22",
        ) from exc

    character_profiles = []
    for character in characters:
        try:
            char_id = generate_character_id(character["name"])
            if not char_id:
                raise errors.InvalidCharacterIdError(
                    f"Unable to generate a character-id.\nCharacter profile was: {character}",
                    "E-3-2-23",
                )

            character_profiles.append(
                Character(
                    character_id=char_id,
                    name=character["name"],
                    age=str(character["age"]),
                    gender=str(character["gender"]),
                    description=character["description"],
                )
            )
        except KeyError as exc:
            raise errors.InvalidCharacterProfileError(
                f"Missing key in Character profile: {character}",
                "E-3-2-24",
            ) from exc
        except errors.InvalidCharacterIdError as exc:
            raise exc
        except Exception as exc:
            raise errors.InvalidCharacterProfileError(
                f"Invalid Character Profile: {character}",
                "E-3-2-25",
            )

    return character_profiles


def parse_frames(model_response: str, characters: Characters) -> list[Scenes, int]:
    """Parses the model response to extract out frame details."""
    match_group = re.search("(```frames[^```]*```)", model_response)
    if not match_group:
        raise errors.ModelResponseParseError(
            f"No frame breakdowns found in model response.\nModel response: {model_response}",
            "E-3-2-27",
        )
    try:
        match_string = match_group.group(0).strip("```frames").strip()
        lines = match_string.split("\n")
        total_frames = int(re.search("[0-9]+", lines[0]).group(0))
        frames_dict = eval("".join(lines[1:]))
    except Exception as exc:
        raise errors.ModelResponseParseError(
            f"Faced an error while trying to parse frame breakdown.\nModel response: {model_response}",
            "E-3-2-28",
        ) from exc

    frames = []
    for scene in frames_dict:
        try:
            frames.append(
                Scene(
                    scene_id=scene["frame_id"],
                    prompt=scene["description"],
                    shot_type=get_shot_type(scene["shot_type"]),
                    camera_angle=scene.get("camera_angle", ""),
                    location=scene["location"],
                    character_expressions=map_character_ids(
                        scene["character_expressions"], characters
                    ),
                    director_tips=scene.get("director_tips", ""),
                    original_script_chunk=scene.get("original_script_chunk", ""),
                )
            )
        except KeyError as exc:
            raise errors.InvalidFrameBreakdownError(
                f"Missing key in Frame breakdown: {scene}",
                "E-3-2-29",
            ) from exc
        except errors.InvalidFrameBreakdownError as exc:
            raise exc
        except Exception as exc:
            raise errors.InvalidFrameBreakdownError(
                f"Invalid Frame breakdown: {scene}",
                "E-3-2-30",
            )

    return frames, total_frames


def split_script_fountain(filename):
    """
    Parses a Fountain script file and extracts scenes.

    Args:
    - filename (str): The path to the Fountain script file.

    Returns:
    - list of dicts: List of scenes extracted from the Fountain script file. Each scene is represented as a dictionary with keys:
        - "id" (int): The ID of the scene.
        - "heading" (str): The heading of the scene.
        - "text" (str): Text content of the scene including scene heading and dialogue/action.
    """
    scenes = []
    current_scene_lines = []  # List to store current scene's lines
    current_scene_heading = None  # Current scene heading
    scene_id = 1  # Starting scene ID

    try:
        with open(filename, "r", encoding="utf-8") as file:
            lines = file.readlines()

            for line in lines:
                line = line.strip()

                if line == "":
                    continue

                elif line.startswith("."):  # Scene Heading
                    # Add the previous scene if it exists
                    if current_scene_heading and current_scene_lines:
                        scenes.append(
                            {
                                "id": scene_id,
                                "heading": current_scene_heading,
                                "text": f"{current_scene_heading}\n"
                                + "\n".join(current_scene_lines),
                            }
                        )
                        current_scene_lines = []  # Reset current scene lines
                        scene_id += 1  # Increment scene ID

                    # Process the new scene heading
                    current_scene_heading = line.strip(".").strip()

                else:
                    # Add the line to the current scene lines if a valid scene heading exists
                    if current_scene_heading:
                        # Check if it's an action or transition and strip the leading character
                        if line.startswith("!"):
                            current_scene_lines.append(line.lstrip("!").strip())
                        elif line.startswith(">"):
                            current_scene_lines.append(line.lstrip(">").strip())
                        else:
                            current_scene_lines.append(line)

            # Add the last scene if exists
            if current_scene_heading and current_scene_lines:
                scenes.append(
                    {
                        "idx": scene_id,
                        "heading": current_scene_heading,
                        "text": f"{current_scene_heading}\n"
                        + "\n".join(current_scene_lines),
                    }
                )

    except FileNotFoundError as exc:
        raise FileNotFoundError(
            f"File '{filename}' not found or cannot be accessed."
        ) from exc
    except Exception as exc:
        raise Exception(
            f"An unknown error occurred while processing '{filename}'."
        ) from exc

    return scenes


def split_script(filename, file_path):
    """
    Parses a script file (PDF or text) and extracts scenes.

    Args:
    - filename (str): The path to the script file.
    - file_path (str): The type of file, either ".pdf" or ".txt".

    Returns:
    - list of dicts: List of scenes extracted from the script file. Each scene is represented as a dictionary with keys:
        - "idx" (int): Index of the scene.
        - "heading" (str): The heading of the scene.
        - "text" (str): Text content of the scene including scene heading and dialogue/action.
    """
    scenes = []
    current_scene_lines = []  # List to store current scene's lines
    current_scene_heading = None  # Current scene heading
    current_idx = 0  # Scene index

    try:
        if file_path.endswith(".pdf"):
            with pdfplumber.open(filename) as pdf:
                entire_text = ""
                for page in pdf.pages:
                    entire_text += page.extract_text() + "\n"
            lines = entire_text.split("\n")
        else:
            with open(filename, "r", encoding="utf-8") as file:
                lines = file.readlines()

        for line in lines:
            line = line.strip()
            if not line or "CONTINUED" in line:
                continue

            elif "INT" in line or "EXT" in line:  # Scene Heading
                if current_scene_lines:  # Add the previous scene if exists
                    text = f"{current_scene_heading}\n" + "\n".join(current_scene_lines)
                    scenes.append(
                        {
                            "idx": current_idx,
                            "heading": current_scene_heading,
                            "text": text,
                        }
                    )
                    current_scene_lines = []  # Reset current scene lines

                # Process the new scene heading
                current_scene_heading = line
                current_idx += 1  # Increment scene index

            else:
                if current_scene_heading:
                    current_scene_lines.append(line)
        if current_scene_lines and current_scene_heading:
            text = f"{current_scene_heading}\n" + "\n".join(current_scene_lines)
            scenes.append(
                {"idx": current_idx, "heading": current_scene_heading, "text": text}
            )

    except FileNotFoundError as exc:
        raise errors.FileNotFoundError(
            f"File '{filename}' not found or cannot be accessed.", "E-3-1-10"
        ) from exc
    except Exception as exc:
        raise errors.UnknownErrorOccured(
            f"An unknown error occurred while processing '{filename}'.", "E-3-1-09"
        ) from exc

    return scenes
