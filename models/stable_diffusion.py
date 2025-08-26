"""Model wrapper to interact with Stable diffusion based models."""
import base64
import os
import random
import threading
from io import BytesIO
from typing import Any

import imageio
import torch
from compel import Compel
from compel import ReturnedEmbeddingsType
from diffusers import StableDiffusionXLImg2ImgPipeline
from diffusers import StableDiffusionXLPipeline
from diffusers import StableVideoDiffusionPipeline
from PIL import Image
from transformers import CLIPVisionModelWithProjection

from modules import errors
from modules import schema
from utils import constants

torch.backends.cuda.matmul.allow_tf32 = True
LOCK = threading.Lock()


class SDXLText2ImageModel:
    def __init__(self, base_dir: str, cache_dir: str):
        self.is_adapter_loaded = False
        try:
            self.pipe = StableDiffusionXLPipeline.from_pretrained(
                os.path.join(base_dir, "hf_repos/xl_base_1.0"),
                cache_dir=cache_dir,
                torch_dtype=torch.float16,
                variant="fp16",
                use_safetensors=True,
            ).to("cuda")
            self.pipe.load_lora_weights(
                os.path.join(base_dir, "hf_repos/xl_base_1.0"),
                cache_dir=cache_dir,
                weight_name="sd_xl_offset_example-lora_1.0.safetensors",
                adapter_name="offset",
            )
            self.pipe.set_adapters(["offset"], adapter_weights=[0.2])

            self.refiner = StableDiffusionXLImg2ImgPipeline.from_pretrained(
                os.path.join(base_dir, "hf_repos/xl_refiner_1.0"),
                cache_dir=cache_dir,
                torch_dtype=torch.float16,
                use_safetensors=True,
                variant="fp16",
            ).to("cuda")
        except Exception as exc:
            raise errors.ModelInitializationFailedError(
                f"Failed to initialize SDXL Model. Check traceback for more info.",
                "E-3-3-01",
            ) from exc

    def load_ip_adapter(self):
        image_encoder = CLIPVisionModelWithProjection.from_pretrained(
            os.path.join(constants.ModelBaseDir, "hf_repos/ip_adapter"),
            cache_dir=constants.ModelCacheDir,
            subfolder="models/image_encoder",
            torch_dtype=torch.float16,
        ).to("cuda")
        self.pipe.image_encoder = image_encoder
        self.pipe.load_ip_adapter(
            os.path.join(constants.ModelBaseDir, "hf_repos/ip_adapter"),
            cache_dir=constants.ModelCacheDir,
            subfolder="sdxl_models",
            weight_name=["ip-adapter-plus-face_sdxl_vit-h.safetensors"],
        )
        self.pipe.set_ip_adapter_scale(0.5)
        self.is_adapter_loaded = True

    def unload_ip_adapter(self):
        self.pipe.unload_ip_adapter()
        self.is_adapter_loaded = False

    def prepare_image_embeds(self, character_images: list[str]):
        return self.pipe.prepare_ip_adapter_image_embeds(
            ip_adapter_image=[character_images],
            ip_adapter_image_embeds=None,
            device="cuda",
            num_images_per_prompt=1,
            do_classifier_free_guidance=True,
        )

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
                compel = Compel(
                    tokenizer=[self.pipe.tokenizer, self.pipe.tokenizer_2],
                    text_encoder=[self.pipe.text_encoder, self.pipe.text_encoder_2],
                    returned_embeddings_type=ReturnedEmbeddingsType.PENULTIMATE_HIDDEN_STATES_NON_NORMALIZED,
                    requires_pooled=[False, True],
                    truncate_long_prompts=False,
                )
                conditioning, pooled = compel([prompt, params.negative_prompt])
                if use_ip_adapter:
                    if not self.is_adapter_loaded:
                        self.load_ip_adapter()
                    image_embeds = self.prepare_image_embeds(character_images)
                    image = self.pipe(
                        prompt_embeds=conditioning[0:1],
                        pooled_prompt_embeds=pooled[0:1],
                        negative_prompt_embeds=conditioning[1:2],
                        negative_pooled_prompt_embeds=pooled[1:2],
                        ip_adapter_image_embeds=image_embeds,
                        guidance_scale=params.guidance_scale
                        * 1.2,  # Increase guidance scale
                        num_inference_steps=params.num_inference_steps,
                        height=params.height,
                        width=params.width,
                        denoising_end=0.8,
                        output_type="latent",
                        control_guidance_start=0.55,  # Earlier start for stronger conditioning
                        control_guidance_end=0.75,  # Extended end for better feature preservation
                        generator=g if params.seed else None,
                    ).images
                else:
                    if self.is_adapter_loaded:
                        self.unload_ip_adapter()
                    image = self.pipe(
                        prompt_embeds=conditioning[0:1],
                        pooled_prompt_embeds=pooled[0:1],
                        negative_prompt_embeds=conditioning[1:2],
                        negative_pooled_prompt_embeds=pooled[1:2],
                        guidance_scale=params.guidance_scale * 1.2,
                        num_inference_steps=params.num_inference_steps,
                        height=params.height,
                        width=params.width,
                        denoising_end=0.8,
                        output_type="latent",
                        generator=g if params.seed else None
                    ).images

                # For refiner, use original prompt/negative_prompt instead of embeddings
                image = self.refiner(
                    prompt=prompt,
                    negative_prompt=params.negative_prompt,
                    image=image,
                    denoising_start=0.8,
                    guidance_scale=params.guidance_scale * 1.2,
                    num_inference_steps=params.num_inference_steps,
                    height=params.height,
                    width=params.width,
                    generator=g if params.seed else None
                ).images[0]
            LOCK.release()
            return image
        except Exception as e:
            raise errors.ModelResponseError(
                f"Failed to generate response for given prompt: {prompt}",
                "E-3-3-02",
            )


class SdxlImage2Gif:
    def __init__(self, base_dir: str):
        try:
            # Initialize the model
            self.pipeline = StableVideoDiffusionPipeline.from_pretrained(
                os.path.join(base_dir, "hf_repos/sdxl-video"),
                torch_dtype=torch.float16,
                variant="fp16",
            ).to("cuda")
            self.pipeline.unet = torch.compile(
                self.pipeline.unet, mode="reduce-overhead", fullgraph=True
            )
        except Exception as exc:
            raise errors.ModelInitializationFailedError(
                "Failed to initialize the model for video diffusion.", "E-3-3-04"
            ) from exc

    def predict(self, base64_image: str, height: int, width: int) -> str:
        try:
            # Decode the base64 image
            image_data = base64.b64decode(base64_image)
            image = Image.open(BytesIO(image_data))

            params = {(16 / 9): (576, 1024, 130), (9 / 16): (1024, 576, 130)}.get(
                width / height, (512, 512, 130)
            )

            height, width, motion_bucket_id = params
            frames = self.pipeline(
                image,
                decode_chunk_size=8,
                generator=torch.manual_seed(random.randint(1, 2**32)),
                height=height,
                width=width,
                motion_bucket_id=motion_bucket_id,
                noise_aug_strength=0.1,
            ).frames[0]

            with BytesIO() as gif_buffer:
                imageio.mimsave(gif_buffer, frames, format="GIF", fps=7)
                gif_base64 = base64.b64encode(gif_buffer.getvalue()).decode("utf-8")
            return gif_base64

        except Exception as exc:
            raise errors.ModelResponseError(
                "Failed to generate GIF from the Image", "E-3-3-05"
            ) from exc
