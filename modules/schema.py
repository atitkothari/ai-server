"""Collection of all request/response schemas used by the Model server."""
import enum
from typing import List

from pydantic import BaseModel

Enum = enum.Enum


class VisualStyle(str, Enum):
    UNKNOWN = "UNKNOWN"
    CINEMATIC = "CINEMATIC"
    SKETCH = "SKETCH"
    VECTOR_ART = "VECTOR_ART"
    ANIME = "ANIME"
    DOODLE = "DOODLE"
    WATERCOLOR = "WATERCOLOR"
    COLOR_SKETCH = "COLOR_SKETCH"
    ADORABLE_3D = "ADORABLE_3D"
    MANGA_COMIC = "MANGA_COMIC"
    ANIME_COMIC = "ANIME_COMIC"
    ANIME_COMIC_MUTED = "ANIME_COMIC_MUTED"
    DIGITAL_PAINTING = "DIGITAL_PAINTING"
    FLUX_COMIC = "FLUX_COMIC"
    GHIBLI_COMIC = "GHIBLI_COMIC"
    DARK = "DARK"
    MOODY_EARTHY = "MOODY_EARTHY"
    ROMANTIC_REALISM = "ROMANTIC_REALISM"
    DARK_FANTASY = "DARK_FANTASY"
    
    # HORROR = "HORROR"
    # ACTION = "ACTION"
    # MYTHOLOGY = "MYTHOLOGY"
    # ROMANTIC = "ROMANTIC"
    # ADVENTURE = "ADVENTURE"
    # THRILLER = "THRILLER"


class ShotType(str, Enum):
    UNKNOWN = "UNKNOWN"
    WIDE_SHOT = "WIDE_SHOT"
    MEDIUM_SHOT = "MEDIUM_SHOT"
    CLOSE_UP = "CLOSE_UP"
    EXTREME_CLOSE_UP = "EXTREME_CLOSE_UP"


class Genre(str, Enum):
    UNKNOWN = "UNKNOWN"
    INDIAN = "INDIAN"
    HOLLYWOOD = "HOLLYWOOD"
    JAPANESE = "JAPANESE"


class ImageStyle(str, Enum):
    STORYBOARD = "STORYBOARD"
    COMIC = "COMIC"


class ExtractShotBreakdownRequest(BaseModel):
    script: str
    location: str = ""
    num_frames: int = 0
    genre: str = ""


class Gender(str, Enum):
    UNKNOWN = "UNKNOWN"
    MALE = "MALE"
    FEMALE = "FEMALE"


class Character(BaseModel):
    character_id: str
    name: str = ""
    age: str = None
    gender: str = ""
    description: str = ""


class CharacterExpression(BaseModel):
    character_id: str
    expression: str


class Scene(BaseModel):
    scene_id: str
    prompt: str
    shot_type: ShotType = ShotType.MEDIUM_SHOT
    camera_angle: str = ""
    location: str
    character_expressions: list[CharacterExpression]
    director_tips: str = ""
    original_script_chunk: str = ""


class ExtractShotBreakdownResponse(BaseModel):
    script: str
    scenes: list[Scene]
    characters: list[Character]


class ImageGenParameters(BaseModel):
    positive_prompt: str = ""
    negative_prompt: str = ""
    visual_style: VisualStyle = VisualStyle.UNKNOWN
    shot_type: ShotType = ShotType.UNKNOWN
    genre: Genre = Genre.UNKNOWN
    height: int = 1024
    width: int = 1024
    num_inference_steps: int = 15
    guidance_scale: float = 7.5
    seed: int = None


class ImageGenRequest(BaseModel):
    prompt: str
    reference_image: str = ""
    characters: list[str] = []  # path of character images stored inside S3 bucket.
    use_refiner: bool = True
    parameters: ImageGenParameters


class ImageGenResult(BaseModel):
    prompt: str
    data: str  # base64 encoded Image
    time_taken: str


class GenerateSceneRequest(BaseModel):
    scene: Scene
    characters: list[str] = []  # path of character images stored inside S3 bucket.
    use_refiner: bool = True
    parameters: ImageGenParameters


class GenerateSceneResponse(BaseModel):
    description: str
    result: ImageGenResult


class CharacterProfileRequest(BaseModel):
    character: Character
    use_refiner: bool = True
    parameters: ImageGenParameters


class CharacterProfileResponse(BaseModel):
    description: str
    result: ImageGenResult


class RegenerateOptions(str, Enum):
    UNKNOWN = "UNKNOWN"
    POSE = "POSE"
    STRUCTURE = "STRUCTURE"


class RegenerateSceneRequest(BaseModel):
    options: RegenerateOptions
    characters: list[str] = []
    request: ImageGenRequest


class InpaintAction(str, Enum):
    UNKNOWN = "UNKNOWN"
    ADD_OBJECT = "ADD_OBJECT"
    REMOVE_OBJECT = "REMOVE_OBJECT"
    CHANGE_BACKGROUND = "CHANGE_BACKGROUND"
    CHANGE_WEATHER = "CHANGE_WEATHER"
    CHANGE_EXPRESSION = "CHANGE_EXPRESSION"
    CHANGE_COLOR = "CHANGE_COLOR"


class InpaintSceneRequest(BaseModel):
    base_image: str
    mask_image: str = ""  # Not required always
    inpainting_prompt: str
    inpaint_action: InpaintAction
    parameters: ImageGenParameters


class GenerateCharacterPortrait(BaseModel):
    character: Character
    parameters: ImageGenParameters


class ExtractScenesRequest(BaseModel):
    filename_url: str


class Frame(BaseModel):
    idx: int
    heading: str
    text: str


class ExtractScenesResponse(BaseModel):
    scenes: List[Frame]


class AnimaionRequest(BaseModel):
    reference_image: str
    height: int
    width: int


class AnimationResponse(BaseModel):
    gif_base64: str


class FrameGenerationRequest(BaseModel):
    prompt: str
    characters: list[str] = []
    use_refiner: bool = True
    use_prompt_enhancer: bool = False
    parameters: ImageGenParameters


class FrameGenerationResponse(BaseModel):
    prompt: str
    image: str
