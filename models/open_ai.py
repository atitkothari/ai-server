"""Model wrapper to interact with OpenAI models."""
import abc
from typing import Mapping

import openai

from modules import errors


class OpenAIModel(abc.ABC):
    API_KEY = ""
    # TODO(Maani): Add support for more generation options like:
    # 1. temperature
    # 2. top-p
    # 3. stop sequences
    # 4. num_outputs
    # 5. response_format
    # 6. seed

    def __init__(self, model_name: str, API_KEY: str):
        try:
            self.client = openai.OpenAI(
                # This is the default and can be omitted
                api_key=API_KEY,
            )
            self.model_name = model_name
        except Exception as exc:
            raise errors.ModelInitializationFailedError(
                f"Failed to initialize OpenAI model client. See traceback for more details.",
                "E-3-1-02",
            ) from exc

    def prepare_input(self, prompt_dict: Mapping[str, str]) -> str:
        conversation = []
        try:
            for role, content in prompt_dict.items():
                conversation.append(
                    {
                        "role": role,
                        "content": content,
                    }
                )
            return conversation
        except Exception as exc:
            raise errors.IncompletePromptDictionaryError(
                f"Incomplete Prompt Dictionary Passed. Expected to have atleast a role and it's content.\nPassed dict: {prompt_dict}",
                "E-3-1-01",
            ) from exc

    def generate_response(
        self, prompt_dict: Mapping[str, str], max_output_tokens: int = None
    ) -> str:
        conversation = self.prepare_input(prompt_dict)
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=conversation,
                max_tokens=max_output_tokens if max_output_tokens else None,
            )
            return response.choices[0].message.content
        except Exception as exc:
            raise errors.ModelResponseError(
                f"Exception in generating model response.\nModel name: {self.model_name}\nInput prompt: {str(conversation)}",
                "E-3-2-20",
            ) from exc
