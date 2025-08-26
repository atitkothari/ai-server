"""Model wrapper to interact with Flux based models."""
import os
import threading

import torch
from diffusers.pipelines.flux.pipeline_flux import FluxPipeline

from modules import errors
from modules import schema
from utils import constants

torch.backends.cuda.matmul.allow_tf32 = True
LOCK = threading.Lock()


class FluxModel:
    def __init__(self):
        self.is_adapter_loaded = False
        self.dtype = torch.bfloat16
        try:
            transformer = torch.load(os.path.join(constants.FluxModelPath, "transformer.pt"), weights_only=False, map_location=torch.device("cuda"))
            transformer.eval()
            text_encoder_2 = torch.load(os.path.join(constants.FluxModelPath, "text_encoder_2.pt"), weights_only=False, map_location=torch.device("cuda"))

            self.pipe = FluxPipeline.from_pretrained(
                os.path.join(constants.ModelBaseDir, "hf_repos/flux-dev"),
                text_encoder_2=None,
                transformer=None,
                cache_dir=constants.ModelCacheDir,
                torch_dtype=self.dtype,
            ).to('cuda')
            self.pipe.text_encoder_2 = text_encoder_2
            self.pipe.transformer = transformer
        except Exception as exc:
            raise errors.ModelInitializationFailedError(
                f"Failed to initialize Flux Model. Check traceback for more info.",
                "E-4-3-01",
            ) from exc

    def load_ip_adapter(self):
        self.pipe.load_ip_adapter(
            os.path.join(constants.ModelBaseDir, "hf_repos/flux-ip-adapter"),
            cache_dir=constants.ModelCacheDir,
            weight_name="ip_adapter.safetensors",
            image_encoder_pretrained_model_name_or_path=os.path.join(constants.ModelBaseDir, "hf_repos/openai-clip/")
        )
        self.pipe.set_ip_adapter_scale(0.5)
        self.is_adapter_loaded = True

    def unload_ip_adapter(self):
        self.pipe.unload_ip_adapter()
        self.is_adapter_loaded = False

    def predict(
        self,
        prompt: str,
        params: schema.ImageGenParameters,
        use_ip_adapter: bool = False,
        character_images: list[str] = [],
    ) -> schema.ImageGenResult:
        try:
            LOCK.acquire()
            if params.seed:
                g = torch.Generator(device="cuda")
                g.manual_seed(params.seed)
            with torch.no_grad():
                if use_ip_adapter:
                    if not self.is_adapter_loaded:
                        self.load_ip_adapter()
                    image = self.pipe(
                        prompt=prompt,
                        negative_prompt=params.negative_prompt,
                        width=params.width,
                        height=params.height,
                        num_inference_steps=params.num_inference_steps,
                        generator=g if params.seed else None,
                        guidance_scale=params.guidance_scale,
                        ip_adapter_image=character_images,
                    ).images[0]
                else:
                    if self.is_adapter_loaded:
                        self.unload_ip_adapter()
                    image = self.pipe(
                        prompt=prompt,
                        width=params.width,
                        height=params.height,
                        num_inference_steps=params.num_inference_steps,
                        generator=g if params.seed else None,
                        guidance_scale=params.guidance_scale,
                    ).images[0]

            LOCK.release()
            return image
        except Exception as e:
            raise errors.ModelResponseError(
                f"Failed to generate response for given prompt: {prompt}",
                "E-4-3-02",
            )


