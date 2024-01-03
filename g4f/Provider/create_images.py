from __future__ import annotations

import re
from ..typing import CreateResult, Messages
from ..base_provider import BaseProvider, ProviderType
from .. import debug

system_message = """
You can generate custom images with the DALL-E 3 image generator.
To generate a image with a prompt, do this:
<img data-prompt=\"keywords for the image\">
Don't use images with data uri. It is important to use a prompt instead.
<img data-prompt=\"image caption\">
"""

class CreateImagesProvider(BaseProvider):
    def __init__(
        self,
        provider: ProviderType,
        create_images: callable,
        system_message: str = system_message
    ) -> None:
        self.provider = provider
        self.create_images = create_images
        self.system_message = system_message
        self. __name__ = provider.__name__
        if hasattr(provider, "url"):
            self.url = provider.url
        self.working = provider.working
        self.supports_stream = provider.supports_stream

    def create_completion(
        self,
        model: str,
        messages: Messages,
        stream: bool = False,
        **kwargs
    ) -> CreateResult:
        messages.insert(0, {"role": "system", "content": self.system_message})
        image_placeholder = ""
        for chunk in self.provider.create_completion(model, messages, stream, **kwargs):
            if image_placeholder or "<" in chunk:
                image_placeholder += chunk
                if ">" in image_placeholder:
                    result = re.search(r'<img data-prompt="(.*?)"', image_placeholder)
                    if result:
                        prompt = result.group(1)
                        if debug.logging:
                            print(f"Create images with prompt: {prompt}")
                        yield from self.create_images(prompt)
                    else:
                        yield image_placeholder
                    image_placeholder = ""
            else:
                yield chunk

    async def create_async(
        self,
        model: str,
        messages: Messages,
        **kwargs
    ) -> str:
        messages.insert(0, {"role": "system", "content": self.system_message})
        response = await self.provider.create_async(model, messages, **kwargs)
        result = re.search(r'<img data-prompt="(.*?)">', response)
        if result:
            search = result.group(0)
            prompt = result.group(1)
            images = "".join([*self.create_images(prompt)])
            return response.replace(search, images)
        return response