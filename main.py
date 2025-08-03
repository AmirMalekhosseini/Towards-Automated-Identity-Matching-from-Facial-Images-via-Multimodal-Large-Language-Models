import sys
import types
import ssl
from src.pipelines.main_flow import run
ssl._create_default_https_context = ssl._create_unverified_context

module_name = 'torchvision.transforms.functional_tensor'
if module_name not in sys.modules:
    stub = types.ModuleType(module_name)

    def rgb_to_grayscale(input_tensor, *args, **kwargs):
        from torchvision.transforms.functional import rgb_to_grayscale as _rgb_to_grayscale
        return _rgb_to_grayscale(input_tensor, *args, **kwargs)

    stub.rgb_to_grayscale = rgb_to_grayscale
    sys.modules[module_name] = stub


if __name__ == "__main__":

  run()




