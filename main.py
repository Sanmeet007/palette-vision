from pallete_vision.color_utils import extract_dominant_colors, format_color
from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Body
from fastapi.responses import JSONResponse, RedirectResponse
from pydantic import BaseModel, Field
from typing import Optional, Literal
import base64

MAX_LIMIT = 10 * 1024 * 1024 # 10MB

app = FastAPI(title="PaletteVision – Image Color Analyzer", version="0.1")


@app.get("/", include_in_schema=False)
async def home():
    """Redirect root to the interactive docs."""
    return RedirectResponse(url="/docs")


@app.post("/dominant-colors")
async def dominant_colors(
    file: UploadFile = File(...),
    format: str = Form("hex"),
    algorithm: str = Form("kmeans"),
    k: int = Form(3),
    top_n: int = Form(2),
    include_percentage: bool = Form(True),
):
    """Extract and return the dominant color palette from an uploaded image."""
    contents = await file.read()
    if not contents:
        raise HTTPException(status_code=400, detail="Empty file")

    if len(contents) > MAX_LIMIT:
        raise HTTPException(status_code=413, detail="File size exceeds 10 MB limit")

    fmt = format.lower()
    alg = algorithm.lower()

    if fmt not in ("hex", "rgb", "rgba", "hsl"):
        raise HTTPException(status_code=400, detail="Invalid color format")

    if alg not in ("kmeans", "meanshift", "mean_shift", "mean-shift"):
        raise HTTPException(status_code=400, detail="Unsupported algorithm")

    try:
        colors = extract_dominant_colors(contents, k=k, algorithm=alg, top_n=top_n)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Color extraction failed: {e}")

    result = []
    for rgb, frac in colors:
        r, g, b = rgb[:3]
        entry = {"value": format_color((r, g, b), fmt)}
        if include_percentage:
            entry["percentage"] = round(float(frac) * 100, 4)  # type: ignore
        result.append(entry)

    return JSONResponse({"colors": result, "algorithm": alg, "format": fmt})


class Base64ImageRequest(BaseModel):
    image_base64: str = Field(
        description="Base64-encoded image string. May include or exclude a data URL prefix (e.g., 'data:image/png;base64,').",
    )
    format: Optional[Literal["hex", "rgb", "rgba", "hsl"]] = Field(
        default="hex",
        description="Output color format. Options: 'hex', 'rgb', 'rgba', or 'hsl'.",
    )
    algorithm: Optional[Literal["kmeans", "meanshift", "mean_shift", "mean-shift"]] = (
        Field(
            default="kmeans",
            description="Color extraction algorithm to use. Supported: 'kmeans' or 'meanshift'.",
        )
    )
    k: Optional[int] = Field(
        default=3,
        description="Number of clusters (dominant colors) to extract when using K-Means.",
    )
    top_n: Optional[int] = Field(
        default=2,
        description="Number of top dominant colors to include in the response.",
    )
    include_percentage: Optional[bool] = Field(
        default=True,
        description="Whether to include each color's percentage composition in the output.",
    )


@app.post("/dominant-colors/base64")
async def dominant_colors_base64(payload: Base64ImageRequest = Body(...)):
    """Extract and return the dominant color palette from base64-encoded image string."""
    s = payload.image_base64
    if not s:
        raise HTTPException(status_code=400, detail="image_base64 is required")

    # Handle data URL prefix
    if s.startswith("data:"):
        try:
            s = s.split(",", 1)[1]
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid data URL")

    try:
        contents = base64.b64decode(s)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid base64 image data")

    if len(contents) > MAX_LIMIT:
        raise HTTPException(status_code=413, detail="Image size exceeds 10 MB limit")

    fmt = (payload.format or "hex").lower()
    alg = (payload.algorithm or "kmeans").lower()

    if fmt not in ("hex", "rgb", "rgba", "hsl"):
        raise HTTPException(status_code=400, detail="Invalid color format")

    if alg not in ("kmeans", "meanshift", "mean_shift", "mean-shift"):
        raise HTTPException(status_code=400, detail="Unsupported algorithm")

    try:
        colors = extract_dominant_colors(
            contents, k=payload.k or 3, algorithm=alg, top_n=payload.top_n or 2
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Color extraction failed: {e}")

    result = []
    for rgb, frac in colors:
        r, g, b = rgb[:3]
        entry = {"value": format_color((r, g, b), fmt)}
        if payload.include_percentage:
            entry["percentage"] = round(float(frac) * 100, 4)  # type: ignore
        result.append(entry)

    return JSONResponse({"colors": result, "algorithm": alg, "format": fmt})


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", port=8000, reload=True)
