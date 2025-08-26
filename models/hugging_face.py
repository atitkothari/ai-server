"""Model wrapper to interact with HuggingFace models."""
import base64
import math
import os
from io import BytesIO

import torch
from PIL import Image
from PIL import ImageDraw
from transformers import AutoModelForCausalLM
from transformers import AutoTokenizer
from transformers import DetrForObjectDetection
from transformers import DetrImageProcessor
from transformers import LogitsProcessorList

from modules import errors
from utils import constants


neg_inf = -8192.0


def safe_str(x):
    x = str(x)
    for _ in range(16):
        x = x.replace("  ", " ")
    return x.strip(",. \r\n")


class EnhancePrompt:
    def __init__(self, base_dir: str, cache_dir: str):
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(
                os.path.join(base_dir, "hf_repos/magicprompt-sd"),
                cache_dir=cache_dir,
            )

            positive_words = (
                open(
                    os.path.join(constants.RefinePromptDir, "positive.txt"),
                    encoding="utf-8",
                )
                .read()
                .splitlines()
            )
            positive_words = ["Ġ" + x.lower() for x in positive_words if x != ""]

            self.logits_bias = (
                torch.zeros((1, len(self.tokenizer.vocab)), dtype=torch.float32)
                + neg_inf
            )

            debug_list = []
            for k, v in self.tokenizer.vocab.items():
                if k in positive_words:
                    self.logits_bias[0, v] = 0
                    debug_list.append(k[1:])

            print(f"EnhancePrompt: Vocab with {len(debug_list)} words.")

            self.model = AutoModelForCausalLM.from_pretrained(
                os.path.join(base_dir, "hf_repos/magicprompt-sd"),
                cache_dir=cache_dir,
                torch_dtype=torch.float16,
            ).to("cuda")
            self.model.eval()
        except Exception as exc:
            raise errors.ModelInitializationFailedError(
                f"Failed to initialize GPT-2 based prompt enhancer model. Check traceback for more details.",
                "E-3-2-34",
            )

    @torch.no_grad()
    @torch.inference_mode()
    def logits_processor(self, input_ids, scores):
        assert scores.ndim == 2 and scores.shape[0] == 1
        self.logits_bias = self.logits_bias.to(scores)

        bias = self.logits_bias.clone()
        bias[0, input_ids[0].to(bias.device).long()] = neg_inf
        bias[0, 11] = 0

        return scores + bias

    @torch.no_grad()
    @torch.inference_mode()
    def __call__(self, prompt):
        try:
            if prompt == "":
                return ""

            prompt = safe_str(prompt) + ","

            tokenized_kwargs = self.tokenizer(prompt, return_tensors="pt")
            tokenized_kwargs.data["input_ids"] = tokenized_kwargs.data["input_ids"].to(
                "cuda"
            )
            tokenized_kwargs.data["attention_mask"] = tokenized_kwargs.data[
                "attention_mask"
            ].to("cuda")

            current_token_length = int(tokenized_kwargs.data["input_ids"].shape[1])
            max_token_length = 75 * int(math.ceil(float(current_token_length) / 75.0))
            max_new_tokens = max_token_length - current_token_length

            if max_new_tokens == 0:
                return prompt[:-1]

            # https://huggingface.co/blog/introducing-csearch
            # https://huggingface.co/docs/transformers/generation_strategies
            features = self.model.generate(
                **tokenized_kwargs,
                top_k=100,
                max_new_tokens=max_new_tokens,
                do_sample=True,
                logits_processor=LogitsProcessorList([self.logits_processor]),
            )

            response = self.tokenizer.batch_decode(features, skip_special_tokens=True)
            result = safe_str(response[0])

            return result
        except Exception as exc:
            raise errors.ModelResponseParseError(
                f"An error occured while parsing response from the GPT-2 based prompt enhancer. Check traceback for more details.",
                "E-3-2-35",
            )


class Resnet:
    def __init__(self, base_dir: str, cache_dir: str):
        try:
            self.processor = DetrImageProcessor.from_pretrained(
                os.path.join(base_dir, "hf_repos/resnet"),
                cache_dir=cache_dir,
            )
            self.model = DetrForObjectDetection.from_pretrained(
                os.path.join(base_dir, "hf_repos/resnet"),
                cache_dir=cache_dir,
            )

        except Exception as exc:
            raise errors.ModelInitializationFailedError(
                f"Failed to initialize Resnet Model. Check traceback for more details.",
                "E-3-1-13",
            )

    @torch.no_grad()
    @torch.inference_mode()
    def __call__(self, raw_base64_image):
        try:
            # Decode base64 string to image
            image_data = base64.b64decode(raw_base64_image)
            image = Image.open(BytesIO(image_data))

            # Get original image size
            original_size = image.size  # (width, height)

            # Prepare image for the model
            inputs = self.processor(images=image, return_tensors="pt")

            # Perform inference
            with torch.no_grad():
                outputs = self.model(**inputs)

            # Post-process results
            target_sizes = torch.tensor([image.size[::-1]])
            results = self.processor.post_process_object_detection(
                outputs, target_sizes=target_sizes, threshold=0.9
            )[0]

            # Create a black image for the mask
            black_image = Image.new("RGB", original_size, color="black")

            # Create drawing object for the mask
            draw_mask = ImageDraw.Draw(black_image)

            # Draw rectangles for each detected person
            for score, label, box in zip(
                results["scores"], results["labels"], results["boxes"]
            ):
                if self.model.config.id2label[label.item()] == "person":
                    box = [round(i) for i in box.tolist()]
                    # Draw white rectangle on black image
                    draw_mask.rectangle(box, outline="white", fill="white")

            # Convert mask image to base64
            buffered_mask = BytesIO()
            black_image.save(buffered_mask, format="PNG")
            mask_image_base64 = base64.b64encode(buffered_mask.getvalue()).decode(
                "utf-8"
            )

            return mask_image_base64

        except Exception as exc:
            raise errors.ModelResponseParseError(
                f"An error occured while parsing response from Resnet Character Mask Generator. Check traceback for more details.",
                "E-3-3-03",
            )
