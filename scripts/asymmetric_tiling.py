import modules.scripts
import modules.sd_hijack
import modules.shared
import gradio

from modules.processing import process_images
from torch import Tensor
from torch.nn import Conv2d
from torch.nn import functional as F
from torch.nn.modules.utils import _pair
from typing import Optional

# Asymmetric tiling script for stable-diffusion-webui
#
# This script allows seamless tiling to be enabled separately for the X and Y axes.
# When this script is in use, the "Tiling" option in the regular UI is ignored.
class Script(modules.scripts.Script):
    # Override from modules.scripts.Script
    def title(self):
        return "Asymmetric tiling"

    # Override from modules.scripts.Script
    def show(self, is_img2img):
        return modules.scripts.AlwaysVisible
    
    # Override from modules.scripts.Script
    def ui(self, is_img2img):
        with gradio.Accordion("Asymmetric tiling", open=False):
            active = gradio.Checkbox(False, label="Active")
            tileX = gradio.Checkbox(True, label="Tile X")
            tileY = gradio.Checkbox(False, label="Tile Y")
            startStep = gradio.Number(0, label="Start tiling from step N", precision=0)
            stopStep = gradio.Number(-1, label="Stop tiling after step N (-1: Don't stop)", precision=0)

        return [active, tileX, tileY, startStep, stopStep]

    # Override from modules.scripts.Script
    def process(self, p, active, tileX, tileY, startStep, stopStep):
        if (active):
            # Record tiling options chosen for each axis.
            p.extra_generation_params = {
                "Tile X": tileX,
                "Tile Y": tileY,
                "Start Tiling From Step": startStep,
                "Stop Tiling After Step": stopStep,
            }

            # Modify the model's Conv2D layers to perform our chosen tiling.
            self.__hijackConv2DMethods(tileX, tileY, startStep, stopStep)
        else:
            # Restore model behaviour to normal.
            self.__restoreConv2DMethods()

    def postprocess(self, *args):
        # Restore model behaviour to normal.
        self.__restoreConv2DMethods()
    
    # [Private]
    # Go through all the "Conv2D" layers in the model and patch them to use the requested asymmetric tiling mode.
    def __hijackConv2DMethods(self, tileX: bool, tileY: bool,  startStep: int, stopStep: int):
        for layer in modules.sd_hijack.model_hijack.layers:
            if type(layer) == Conv2d:
                layer.padding_modeX = 'circular' if tileX else 'constant'
                layer.padding_modeY = 'circular' if tileY else 'constant'
                layer.paddingX = (layer._reversed_padding_repeated_twice[0], layer._reversed_padding_repeated_twice[1], 0, 0)
                layer.paddingY = (0, 0, layer._reversed_padding_repeated_twice[2], layer._reversed_padding_repeated_twice[3])
                layer.paddingStartStep = startStep
                layer.paddingStopStep = stopStep
                layer._conv_forward = Script.__replacementConv2DConvForward.__get__(layer, Conv2d)

    # [Private]
    # Go through all the "Conv2D" layers in the model and restore them to their origanal behaviour.
    def __restoreConv2DMethods(self):
        for layer in modules.sd_hijack.model_hijack.layers:
            if type(layer) == Conv2d:
                layer._conv_forward = Conv2d._conv_forward.__get__(layer, Conv2d)

    # [Private]
    # A replacement for the Conv2d._conv_forward method that pads axes asymmetrically.
    # This replacement method performs the same operation (as of torch v1.12.1+cu113), but it pads the X and Y axes separately based on the members
    #   padding_modeX (string, either 'circular' or 'constant') 
    #   padding_modeY (string, either 'circular' or 'constant')
    #   paddingX (tuple, cached copy of _reversed_padding_repeated_twice with the last two values zeroed)
    #   paddingY (tuple, cached copy of _reversed_padding_repeated_twice with the first two values zeroed)
    def __replacementConv2DConvForward(self, input: Tensor, weight: Tensor, bias: Optional[Tensor]):
        step = modules.shared.state.sampling_step
        if ((self.paddingStartStep < 0 or step >= self.paddingStartStep) and (self.paddingStopStep < 0 or step <= self.paddingStopStep)):
            working = F.pad(input, self.paddingX, mode=self.padding_modeX)
            working = F.pad(working, self.paddingY, mode=self.padding_modeY)
        else:
            working = F.pad(input, self.paddingX, mode='constant')
            working = F.pad(working, self.paddingY, mode='constant')
        return F.conv2d(working, weight, bias, self.stride, _pair(0), self.dilation, self.groups)
