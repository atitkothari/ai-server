import logging
from io import BytesIO
from urllib.parse import urlparse

import torch

import utils.common as common
import utils.constants as constants
from models.lama.saicinpainting.training.trainers.default import (
    DefaultInpaintingTrainingModule,
)


def get_training_model_class(kind):
    if kind == "default":
        return DefaultInpaintingTrainingModule

    raise ValueError(f"Unknown trainer module {kind}")


def make_training_model(config):
    kind = config.training_model.kind
    kwargs = dict(config.training_model)
    kwargs.pop("kind")
    kwargs["use_ddp"] = config.trainer.kwargs.get("accelerator", None) == "ddp"

    logging.info(f"Make training model {kind}")

    cls = get_training_model_class(kind)
    return cls(config, **kwargs)


def load_checkpoint(train_config, map_location="cuda", strict=True):
    model: torch.nn.Module = make_training_model(train_config)
    model_bytes = common.fetch_s3_file(
        {
            "bucket_name": urlparse(constants.S3_BUCKET_PATH).hostname.split(".")[0],
            "file_key": urlparse(constants.S3_MODEL_PATH).path.lstrip("/"),
        }
    )
    state = torch.load(BytesIO(model_bytes), map_location=torch.device("cpu"))
    model.load_state_dict(state["state_dict"], strict=strict)
    model.on_load_checkpoint(state)
    return model
