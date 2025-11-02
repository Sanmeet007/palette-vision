from io import BytesIO
from typing import List, Tuple, Optional
import numpy as np
from PIL import Image
from sklearn.cluster import KMeans, MeanShift, estimate_bandwidth
import colorsys


def load_image(file_bytes: bytes, max_size: int = 800) -> np.ndarray:
    """Load an image from bytes and resize if necessary."""
    img = Image.open(BytesIO(file_bytes)).convert("RGB")

    w, h = img.size
    if max(w, h) > max_size:
        scale = max_size / max(w, h)
        try:
            resample = Image.Resampling.LANCZOS  # Pillow ≥ 9
        except AttributeError:
            resample = (
                Image.Resampling.LANCZOS
                if hasattr(Image, "LANCZOS")
                else Image.Resampling.BICUBIC
            )
        img = img.resize((int(w * scale), int(h * scale)), resample=resample)

    return np.array(img, dtype=np.uint8)


def pixels_array(img_arr: np.ndarray) -> np.ndarray:
    """Flatten image array into a 2D array of pixels."""
    return img_arr.reshape(-1, 3).astype(float)


def cluster_kmeans(
    pixels: np.ndarray, n_clusters: int = 3, random_state: int = 42
) -> Tuple[np.ndarray, np.ndarray]:
    model = KMeans(n_clusters=n_clusters, random_state=random_state, n_init=10)
    labels = model.fit_predict(pixels)
    return model.cluster_centers_, labels


def cluster_meanshift(
    pixels: np.ndarray, quantile: float = 0.2
) -> Tuple[np.ndarray, np.ndarray]:
    """Cluster pixels using MeanShift with automatic bandwidth estimation."""
    try:
        bandwidth = estimate_bandwidth(pixels, quantile=quantile, n_samples=500)
        if bandwidth <= 0 or np.isnan(bandwidth):
            raise ValueError
    except Exception:
        bandwidth = 30.0  # safe fallback

    model = MeanShift(bandwidth=bandwidth, bin_seeding=True)
    labels = model.fit_predict(pixels)
    return model.cluster_centers_, labels


def get_top_colors(
    centers: np.ndarray, labels: np.ndarray, top_n: int = 2
) -> List[Tuple[np.ndarray, float]]:
    """Return top N colors and their relative proportions."""
    counts = np.bincount(labels)
    order = np.argsort(-counts)
    total = labels.size
    top_colors = []

    for idx in order[:top_n]:
        color = np.clip(centers[idx], 0, 255).astype(int)
        frac = counts[idx] / total
        top_colors.append((color, frac))

    # If fewer than top_n clusters exist
    while len(top_colors) < top_n:
        top_colors.append((top_colors[0][0], 1.0))

    return top_colors


def rgb_to_hex(rgb: Tuple[int, int, int]) -> str:
    return "#{:02x}{:02x}{:02x}".format(*rgb)


def rgb_to_hsl_string(rgb: Tuple[int, int, int]) -> str:
    r, g, b = [x / 255.0 for x in rgb]
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    return f"hsl({round(h * 360, 2)}deg, {round(s * 100, 2)}%, {round(l * 100, 2)}%)"


def format_color(
    rgb: Tuple[int, int, int], fmt: str = "hex", alpha: Optional[float] = None
) -> str:
    fmt = fmt.lower()
    if fmt == "hex":
        return rgb_to_hex(rgb)
    if fmt == "rgb":
        return f"rgb({rgb[0]}, {rgb[1]}, {rgb[2]})"
    if fmt == "rgba":
        a = 1.0 if alpha is None else alpha
        return f"rgba({rgb[0]}, {rgb[1]}, {rgb[2]}, {a})"
    if fmt == "hsl":
        return rgb_to_hsl_string(rgb)
    return rgb_to_hex(rgb)


def extract_dominant_colors(
    file_bytes: bytes, k: int = 3, algorithm: str = "kmeans", top_n: int = 2
):
    """
    Extract top N dominant colors from an image.

    Args:
        file_bytes: Image bytes
        k: Number of clusters (for KMeans)
        algorithm: "kmeans" or "meanshift"
        top_n: Number of colors to return

    Returns:
        List of (RGB tuple, fraction)
    """
    arr = load_image(file_bytes)
    pixels = pixels_array(arr)

    algorithm = algorithm.lower()
    if algorithm == "meanshift":
        centers, labels = cluster_meanshift(pixels)
    else:
        centers, labels = cluster_kmeans(pixels, n_clusters=max(1, k))

    top = get_top_colors(centers, labels, top_n)
    return [(tuple(map(int, c)), round(frac, 4)) for c, frac in top]
