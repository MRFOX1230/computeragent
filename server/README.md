<h1 align="center">WAN2.1 VACE</a>
<h3>Text2Video, Image2Video and StartImage+EndImage2Video models in one</h3>

<p>
• <a href="#overview">Overview</a><br>
• <a href="#features">Features</a><br>
• <a href="#installation">Installation</a>
</p>

## Overview

WAN2.1 VACE is a multimodal video generation system that combines three powerful capabilities:
- **Text-to-Video**: Generate videos from textual descriptions
- **Image-to-Video**: Animate static images into dynamic videos
- **Start+End Image-to-Video**: Create smooth transitions between two images

## Features

- 🚀 Three-in-one model architecture
- 🖼️ Supports multiple input modalities
- ⚡ Fast inference with optimized pipelines
- 🎨 High-quality video output
- 🔧 Control via ComfyUI

## Installation

First you need to copy the repository:

```bash
# Clone the repository
git clone https://git.g-309.ru/trust-ai-lab/showroom/t2v.git
cd t2v
```

After that download the archive from the link below and unzip its contents into the ComfyUI folder:
https://disk.yandex.ru/d/XyOcTVdlqkUICQ


Finally, compile the image and run the container:

```bash
# Generate Docker image and create container
docker build -t t2v .
docker run -it --gpus all t2v bash
```

