import modules.scripts
import modules.sd_hijack
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
    def ui(self, is_img2img):
        tileX = gradio.Checkbox(True, label="Tile X")
        tileY = gradio.Checkbox(False, label="Tile Y")

        return [tileX, tileY]

    # Override from modules.scripts.Script
    def run(self, p, tileX, tileY):
        # Record tiling options chosen for each axis.
        p.extra_generation_params = {
            "Tile X": tileX,
            "Tile Y": tileY,
        }

        try:
            # Modify the model's Conv2D layers to perform our chosen tiling.
            self.__hijackConv2DMethods(tileX, tileY)

            # Process images as normal.
            return process_images(p)
        finally:
            # Restore model behaviour to normal, even if something went wrong during processing.
            self.__restoreConv2DMethods()
    
    # [Private]
    # Go through all the "Conv2D" layers in the model and patch them to use the requested asymmetric tiling mode.
    def __hijackConv2DMethods(self, tileX: bool, tileY: bool):
        for layer in modules.sd_hijack.model_hijack.layers:
            if type(layer) == Conv2d:
                layer.padding_modeX = 'circular' if tileX else 'constant'
                layer.padding_modeY = 'circular' if tileY else 'constant'
                layer.paddingX = (layer._reversed_padding_repeated_twice[0], layer._reversed_padding_repeated_twice[1], 0, 0)
                layer.paddingY = (0, 0, layer._reversed_padding_repeated_twice[2], layer._reversed_padding_repeated_twice[3])
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
        working = F.pad(input, self.paddingX, mode=self.padding_modeX)
        working = F.pad(working, self.paddingY, mode=self.padding_modeY)
        return F.conv2d(working, weight, bias, self.stride, _pair(0), self.dilation, self.groups)
