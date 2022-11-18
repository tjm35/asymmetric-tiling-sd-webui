# Asymmetric Tiling for stable-diffusion-webui

An always visible script extension for [stable-diffusion-webui](https://github.com/AUTOMATIC1111/stable-diffusion-webui/) to configure seamless image tiling independently for the X and Y axes.

To use, install this repository from the "Extensions" tab in stable-diffusion-webui, restart your server, open the `Asymmetric tiling` foldout on txt2img or img2img, and make it active, and check `Tile X` or `Tile Y` as desired. While this script is active, the `Tiling` checkbox in the main UI will be ignored.

Like existing tiling options this won't guarantee seamless tiling 100% of the time, but it should manage it for most prompts. You can check that images tile seamlessly using online tools like [Seamless Texture Check](https://www.pycheung.com/checker/).

For the old, non-extension version of this script, use the "classic_script" branch.

## X axis tiling examples
![00817-3274117678-midnight cityscape, stunning environment, wide-angle, massive scale, landscape, panoramic, lush vegetation, idyllic](https://user-images.githubusercontent.com/19196175/195132862-8c050327-92f3-44a4-9c02-0f11cce0b609.png)
![01064-1316547214-(((domino run))), domino toppling, line of standing dominoes, domino cascade, domino effect, black dominos](https://user-images.githubusercontent.com/19196175/195137782-e72fc69a-14f1-4ae7-bac2-219734509aea.png)

## Y Axis tiling examples
![00840-2320166501-man climbing ladder, safety diagram](https://user-images.githubusercontent.com/19196175/195132867-1b36848e-135d-4103-8e10-1d760b3a0a4e.png)![01095-949590403-tree, thick branches, photograph, 80mm Sigma f1 4, studio quality, nature photography](https://user-images.githubusercontent.com/19196175/195140638-49b0a4be-fbca-45bc-8e52-6c985202ce29.png)
