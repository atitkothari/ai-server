"""Constants to be used across the server."""
import os

from dotenv import load_dotenv

load_dotenv()
OPEN_AI_API_KEY = os.environ.get("OPENAI_KEY")
os.environ["AWS_ACCESS_KEY_ID"] = os.environ.get("AWS_ACCESS_KEY_ID")
os.environ["AWS_SECRET_ACCESS_KEY"] = os.environ.get("AWS_SECRET_ACCESS_KEY")

# Directories to cache various model tensors.
ModelBaseDir = "/home/immer-dev/hf"
ModelCacheDir = os.path.join(ModelBaseDir, "hf_cache")
FluxModelPath = "/home/immer-dev/model2"


# Directory to store API specific presets.
RefinePromptDir = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "presets", "refine_prompt"
)
InpaintConfigDir = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "presets", "inpainting"
)
ReferenceImageConfigDir = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "presets", "reference_image"
)

S3_BUCKET_PATH = os.environ.get("S3_BUCKET_PATH")
S3_MODEL_PATH = os.environ.get("S3_MODEL_PATH")
WEBUI_INSTANCE_IP = os.environ.get("WEBUI_INSTANCE_IP")
