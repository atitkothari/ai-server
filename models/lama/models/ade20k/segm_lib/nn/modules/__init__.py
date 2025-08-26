# -*- coding: utf-8 -*-
# File   : __init__.py
# Author : Jiayuan Mao
# Email  : maojiayuan@gmail.com
# Date   : 27/01/2018
#
# This file is part of Synchronized-BatchNorm-PyTorch.
# https://github.com/vacancy/Synchronized-BatchNorm-PyTorch
# Distributed under MIT License.
from .batchnorm import SynchronizedBatchNorm1d
from .batchnorm import SynchronizedBatchNorm2d
from .batchnorm import SynchronizedBatchNorm3d
from .replicate import DataParallelWithCallback
from .replicate import patch_replication_callback
