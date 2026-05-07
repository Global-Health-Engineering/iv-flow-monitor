"""Convert ETH Zürich logo PNG to a KiCad footprint (.kicad_mod) on F.SilkS.

Approach:
1. Load image, convert to binary (black = logo content)
2. Crop to content bounding box
3. Downscale to target width, ensuring min feature >= 0.2mm (JLCPCB silkscreen)
4. Extract horizontal runs of black pixels per row
5. Merge vertically adjacent identical runs into rectangles
6. Output as fp_poly elements on F.SilkS layer
"""

import sys
import uuid
from pathlib import Path
from PIL import Image
import numpy as np


def load_and_threshold(path, threshold=128):
    """Load image, convert to grayscale, threshold to binary.
    For RGBA images, also uses alpha channel to exclude transparent pixels."""
    img = Image.open(path)
    if img.mode == "RGBA":
        # Use alpha to mask out transparent areas
        arr = np.array(img)
        alpha = arr[:, :, 3]
        gray = np.array(img.convert("L"))
        # Content = dark pixels with non-transparent alpha
        binary = (gray < threshold) & (alpha > 128)
    else:
        gray = np.array(img.convert("L"))
        binary = gray < threshold
    return binary


def crop_to_content(binary):
    """Crop binary array to bounding box of True pixels."""
    rows = np.any(binary, axis=1)
    cols = np.any(binary, axis=0)
    rmin, rmax = np.where(rows)[0][[0, -1]]
    cmin, cmax = np.where(cols)[0][[0, -1]]
    return binary[rmin:rmax+1, cmin:cmax+1]


def measure_min_feature(binary):
    """Estimate minimum feature width (horizontal runs) in pixels."""
    min_run = binary.shape[1]  # start with max
    for row in binary:
        in_run = False
        run_len = 0
        for val in row:
            if val:
                run_len += 1
                in_run = True
            else:
                if in_run and run_len > 0:
                    min_run = min(min_run, run_len)
                run_len = 0
                in_run = False
        if in_run and run_len > 0:
            min_run = min(min_run, run_len)

    # Also check vertical runs
    for col in binary.T:
        in_run = False
        run_len = 0
        for val in col:
            if val:
                run_len += 1
                in_run = True
            else:
                if in_run and run_len > 0:
                    min_run = min(min_run, run_len)
                run_len = 0
                in_run = False
        if in_run and run_len > 0:
            min_run = min(min_run, run_len)

    return min_run


def downscale(binary, factor):
    """Downscale binary image by factor using block averaging."""
    h, w = binary.shape
    new_h = h // factor
    new_w = w // factor
    # Crop to multiple of factor
    cropped = binary[:new_h * factor, :new_w * factor]
    # Reshape and average blocks
    blocks = cropped.reshape(new_h, factor, new_w, factor)
    # A block is "on" if more than 50% of pixels are on
    result = blocks.mean(axis=(1, 3)) > 0.5
    return result


def morphological_open(binary, iterations=1):
    """Remove isolated 1px features (anti-aliasing artifacts).
    Erosion then dilation using a 3x3 cross structuring element."""
    result = binary.copy()
    for _ in range(iterations):
        # Erosion: pixel stays on only if itself + all 4 neighbors are on
        eroded = np.zeros_like(result)
        eroded[1:-1, 1:-1] = (
            result[1:-1, 1:-1] &
            result[:-2, 1:-1] &   # top
            result[2:, 1:-1] &    # bottom
            result[1:-1, :-2] &   # left
            result[1:-1, 2:]      # right
        )
        # Dilation: pixel turns on if any of itself + 4 neighbors are on
        dilated = np.zeros_like(eroded)
        dilated[1:-1, 1:-1] = (
            eroded[1:-1, 1:-1] |
            eroded[:-2, 1:-1] |
            eroded[2:, 1:-1] |
            eroded[1:-1, :-2] |
            eroded[1:-1, 2:]
        )
        result = dilated
    return result


def extract_runs(binary):
    """Extract horizontal runs from binary image.
    Returns list of (row, col_start, col_end) tuples."""
    runs = []
    h, w = binary.shape
    for r in range(h):
        c = 0
        while c < w:
            if binary[r, c]:
                start = c
                while c < w and binary[r, c]:
                    c += 1
                runs.append((r, start, c))
            else:
                c += 1
    return runs


def merge_runs_vertically(runs):
    """Merge vertically adjacent runs with same col_start and col_end into rectangles.
    Returns list of (row_start, row_end, col_start, col_end) tuples."""
    if not runs:
        return []

    # Group runs by (col_start, col_end)
    # Sort by col_start, col_end, row
    runs.sort(key=lambda r: (r[1], r[2], r[0]))

    rects = []
    i = 0
    while i < len(runs):
        row, cs, ce = runs[i]
        r_start = row
        r_end = row + 1
        # Try to extend downward
        j = i + 1
        while j < len(runs):
            nr, ncs, nce = runs[j]
            if ncs == cs and nce == ce and nr == r_end:
                r_end = nr + 1
                j += 1
            else:
                break
        rects.append((r_start, r_end, cs, ce))
        i = j

    return rects


def generate_kicad_mod(rects, pixel_size_mm, img_h, img_w, name="ETH_Zurich_Logo"):
    """Generate KiCad footprint file content with fp_poly rectangles on F.SilkS.
    Origin is at the center of the logo."""
    cx = img_w * pixel_size_mm / 2.0
    cy = img_h * pixel_size_mm / 2.0

    lines = []
    lines.append(f'(footprint "{name}"')
    lines.append(f'\t(version 20240108)')
    lines.append(f'\t(generator "logo_to_footprint")')
    lines.append(f'\t(generator_version "1.0")')
    lines.append(f'\t(layer "F.SilkS")')
    lines.append(f'\t(descr "ETH Zurich logo for silkscreen")')
    lines.append(f'\t(attr board_only exclude_from_pos_files exclude_from_bom)')

    # Reference and Value (hidden)
    lines.append(f'\t(fp_text reference "REF**"')
    lines.append(f'\t\t(at 0 {-cy - 1:.2f})')
    lines.append(f'\t\t(layer "F.SilkS")')
    lines.append(f'\t\t(hide yes)')
    lines.append(f'\t\t(effects (font (size 1 1) (thickness 0.15)))')
    lines.append(f'\t)')
    lines.append(f'\t(fp_text value "{name}"')
    lines.append(f'\t\t(at 0 {cy + 1:.2f})')
    lines.append(f'\t\t(layer "F.Fab")')
    lines.append(f'\t\t(hide yes)')
    lines.append(f'\t\t(effects (font (size 1 1) (thickness 0.15)))')
    lines.append(f'\t)')

    # Courtyard
    w_mm = img_w * pixel_size_mm
    h_mm = img_h * pixel_size_mm
    lines.append(f'\t(fp_rect')
    lines.append(f'\t\t(start {-cx - 0.25:.2f} {-cy - 0.25:.2f})')
    lines.append(f'\t\t(end {cx + 0.25 - w_mm + w_mm:.2f} {cy + 0.25 - h_mm + h_mm:.2f})')
    lines.append(f'\t\t(stroke (width 0.05) (type default))')
    lines.append(f'\t\t(layer "F.CrtYd")')
    lines.append(f'\t\t(uuid "{uuid.uuid4()}")')
    lines.append(f'\t)')

    # Generate fp_poly for each rectangle
    for r_start, r_end, c_start, c_end in rects:
        x1 = c_start * pixel_size_mm - cx
        y1 = r_start * pixel_size_mm - cy
        x2 = c_end * pixel_size_mm - cx
        y2 = r_end * pixel_size_mm - cy

        lines.append(f'\t(fp_poly')
        lines.append(f'\t\t(pts')
        lines.append(f'\t\t\t(xy {x1:.3f} {y1:.3f})')
        lines.append(f'\t\t\t(xy {x2:.3f} {y1:.3f})')
        lines.append(f'\t\t\t(xy {x2:.3f} {y2:.3f})')
        lines.append(f'\t\t\t(xy {x1:.3f} {y2:.3f})')
        lines.append(f'\t\t)')
        lines.append(f'\t\t(stroke (width 0) (type solid))')
        lines.append(f'\t\t(fill solid)')
        lines.append(f'\t\t(layer "F.SilkS")')
        lines.append(f'\t\t(uuid "{uuid.uuid4()}")')
        lines.append(f'\t)')

    lines.append(')')
    return '\n'.join(lines)


def main():
    script_dir = Path(__file__).resolve().parent
    default_input = script_dir / "eth_logo.png"
    default_output = script_dir.parent / "IV_Flow_Monitor_Footprints.pretty" / "ETH_Zurich_Logo.kicad_mod"
    input_path = sys.argv[1] if len(sys.argv) > 1 else str(default_input)
    output_path = sys.argv[2] if len(sys.argv) > 2 else str(default_output)
    target_width_mm = float(sys.argv[3]) if len(sys.argv) > 3 else 12.0
    threshold = int(sys.argv[4]) if len(sys.argv) > 4 else 128
    min_feature_mm = 0.20  # JLCPCB silkscreen minimum (0.15mm spec, 0.2mm recommended)

    print(f"Loading image: {input_path} (threshold={threshold})")
    binary = load_and_threshold(input_path, threshold=threshold)
    print(f"  Raw image: {binary.shape[1]} x {binary.shape[0]} px")

    binary = crop_to_content(binary)
    h, w = binary.shape
    print(f"  Cropped to content: {w} x {h} px")

    # Calculate pixel size at target width
    pixel_size = target_width_mm / w
    print(f"  Target width: {target_width_mm} mm")
    print(f"  Pixel size at target: {pixel_size*1000:.1f} um")

    # Measure minimum feature in original
    min_feat_px = measure_min_feature(binary)
    min_feat_mm = min_feat_px * pixel_size
    print(f"  Min feature (original): {min_feat_px} px = {min_feat_mm:.3f} mm")

    # Downscale to reasonable resolution
    # Target: pixel size ~0.05mm so 4px = 0.2mm (JLCPCB min)
    target_pixel_mm = 0.05
    desired_ds = target_pixel_mm / pixel_size
    downsample_factor = max(1, round(desired_ds))

    if downsample_factor > 1:
        binary = downscale(binary, downsample_factor)
        h, w = binary.shape
        pixel_size = target_width_mm / w
        print(f"  Downscaled by {downsample_factor}x: {w} x {h} px")
        print(f"  New pixel size: {pixel_size*1000:.1f} um")

    # Morphological opening to remove 1px anti-aliasing artifacts
    binary = morphological_open(binary, iterations=1)
    # Recrop in case opening removed edge pixels
    if np.any(binary):
        rows = np.any(binary, axis=1)
        cols = np.any(binary, axis=0)
        rmin, rmax = np.where(rows)[0][[0, -1]]
        cmin, cmax = np.where(cols)[0][[0, -1]]
        binary = binary[rmin:rmax+1, cmin:cmax+1]
        h, w = binary.shape
        pixel_size = target_width_mm / w
        print(f"  After morphological cleanup: {w} x {h} px")

    actual_height = h * pixel_size
    print(f"  Final size: {target_width_mm:.2f} x {actual_height:.2f} mm")

    # Extract runs and merge
    runs = extract_runs(binary)
    print(f"  Horizontal runs: {len(runs)}")

    rects = merge_runs_vertically(runs)
    print(f"  After vertical merge: {len(rects)} rectangles")

    # Generate footprint
    import os
    name = os.path.splitext(os.path.basename(output_path))[0]
    content = generate_kicad_mod(rects, pixel_size, h, w, name=name)

    with open(output_path, 'w') as f:
        f.write(content)

    print(f"\nFootprint written to: {output_path}")
    print(f"  Size: {target_width_mm:.2f} x {actual_height:.2f} mm")
    print(f"  Min feature: {min_feat_mm:.3f} mm (JLCPCB min: 0.15mm)")
    print(f"  Polygons: {len(rects)}")


if __name__ == "__main__":
    main()
