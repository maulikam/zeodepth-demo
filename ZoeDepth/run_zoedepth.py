import torch
from PIL import Image
from zoedepth.models.builder import build_model
from zoedepth.utils.config import get_config
from zoedepth.utils.misc import pil_to_batched_tensor, colorize, save_raw_16bit

# Fetch MiDaS repository
torch.hub.help("intel-isl/MiDaS", "DPT_BEiT_L_384", force_reload=True)

# Load the ZoeD_N model
conf = get_config("zoedepth", "infer")
model_zoe_n = build_model(conf)
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
zoe = model_zoe_n.to(DEVICE)

# Load and process an image
image_path = "1.jpg"  # Update with your image path
image = Image.open(image_path).convert("RGB")

# Predict depth
depth_numpy = zoe.infer_pil(image)  # Get depth as numpy array
depth_pil = zoe.infer_pil(image, output_type="pil")  # Get depth as 16-bit PIL Image
depth_tensor = zoe.infer_pil(image, output_type="tensor")  # Get depth as torch tensor

scale_factor = 1.0
depth_metric = depth_numpy * scale_factor

# Print depth values
print("Depth values (in meters):")
print(depth_metric)

# Save the depth image
fpath = "output.png"  # Update with your desired output path
save_raw_16bit(depth_numpy, fpath)

# Colorize and save the depth output
colored = colorize(depth_numpy)
fpath_colored = "output_colored.png"  # Update with your desired output path
Image.fromarray(colored).save(fpath_colored)
