
# Stereo Processing with MicMac

This project demonstrates how to use [MicMac](https://github.com/micmacIGN/micmac), an open-source photogrammetry suite, for stereo image processing.

---

## 📦 Directory Structure
The input directory should contain:
- At least 2 TIF/TIFF image files (satellite stereo pair)
- Images should be in supported formats (.tif, .TIF, .tiff, .TIFF)
- Optional: RPC metadata files (.XML) with same base names as images
```
your_project_directory/
│
├── img_b.tif                # Backward looking image
├── img_f.tif                # Forward looking image
├── img_b.xml                # RPC file for backward image
├── img_f.xml                # RPC file for forward image
├── WGS84toUTM.xml           # UTM projection definition file (in Proj4 format)
├── mm3d_utils.py            # Utility script (optional)
```

---

## ⚙️ Installation

You can install MicMac either in **Google Colab** or **locally using WSL**. Choose one of the methods below.

---

### 🟢 Option A: Google Colab (Quick Setup for Testing)

```bash
# Set working path
YOUR_PATH = '/content/'  # or your preferred Google Drive folder

# Install dependencies
!apt update
!apt install -y cmake imagemagick proj-bin exiv2
!pip install dlib wget gdown

# Clone MicMac repository
!git clone https://github.com/micmacIGN/micmac.git

# Build MicMac
!mkdir /content/micmac/build
!cd /content/micmac/build && cmake /content/micmac -DBUILD_POISSON=OFF && make install -j28

# Update PATH (for Jupyter usage)
import os
os.environ['PATH'] += ":/content/micmac/bin/"
!echo $PATH
!mm3d
```

---

### 🟠 Option B: Local Installation with WSL + Conda

1. **Install dependencies**

```bash
sudo apt update && sudo apt install -y \
    cmake imagemagick proj-bin exiv2 git build-essential \
    libboost-all-dev libeigen3-dev libtiff-dev libjpeg-dev \
    libpng-dev libx11-dev libxml2-dev libgdal-dev \
    qtbase5-dev qttools5-dev-tools libcurl4-openssl-dev \
    libopencv-dev libdcmtk-dev zlib1g-dev libatlas-base-dev
```

2. **Activate your conda environment**, then install Python dependencies:

```bash
pip install dlib wget gdown
```
```bash
conda install -c conda-forge gdal
```

3. **Clone and build MicMac**

```bash
git clone https://github.com/micmacIGN/micmac.git
cd micmac
mkdir build && cd build
cmake .. -DBUILD_POISSON=OFF
make install -j$(nproc)
```

4. **Add MicMac to PATH**

```bash
echo 'export PATH=$PATH:~/micmac/bin' >> ~/.bashrc
source ~/.bashrc
```

5. **Verify installation**

Activate conda environment and run:
```bash
which mm3d
```

It should return the path to `mm3d` executable.

---

## 📁 Dataset Information

This stereo dataset includes:

- `img_b.tif` and `img_f.tif`: Two TIF images taken from different angles (e.g., forward and backward)
- `img_b.xml` and `img_f.xml`: RPC metadata for the corresponding images
- `WGS84toUTM.xml`: Projection definition in Proj4 format (used for georeferencing)

---

## 🛰️ Running MicMac

### Basic Usage
```bash
python main.py /path/to/input/directory
```

### With verbose output
```bash
python main.py /path/to/input/directory --verbose
```

---
## Processing Steps

The pipeline performs the following steps:

1. **Tie Point Extraction** (Tapioca)
   - Finds matching points between stereo images
   - Creates homologous point files

2. **Image Visualization**
   - Displays input images
   - Plots tie points distribution

3. **Bundle Adjustment** (Convert2GenBundle + Campari)
   - Converts to GenBundle format
   - Performs bundle adjustment for camera calibration

4. **DSM Generation** (Malt)
   - Generates Digital Surface Model
   - Creates orthophoto as byproduct

5. **Visualization**
   - Generates shaded relief visualization
   - Creates orthophoto mosaic

6. **Georeference**
   - Generates gereferecne DSL.tif in geo folder inside the working directory


## Output Files

The processing creates several output directories:

- `Homol/` - Homologous (tie) points
- `MEC-Malt/` - Digital Surface Model and masks
- `Ortho-MEC-Malt/` - Orthophoto mosaic
- Various intermediate processing files

## Key Output Files

- `MEC-Malt/Z_Num8_DeZoom1_STD-MALT.tif` - Digital Surface Model
- `MEC-Malt/Z_Num8_DeZoom1_STD-MALTShade.tif` - Shaded relief
- `Ortho-MEC-Malt/Orthophotomosaic.tif` - Orthophoto mosaic

## Error Handling

- Check that mm3d is installed and in PATH
- Ensure input directory contains at least 2 TIF files
- Processing logs are displayed in console
- Use `--verbose` flag for detailed debugging

## Troubleshooting

1. **"mm3d command not found"**
   - Install MicMac and ensure it's in your PATH

2. **"No TIF files found"**
   - Check that input directory contains .tif/.TIF files
   - Verify file extensions are correct

3. **Processing fails at specific step**
   - Check console output for mm3d error messages
   - Verify input images are valid stereo pairs
   - Ensure sufficient disk space for processing

## Example

```bash
# Process stereo images in satellite_data directory
python main.py satellite_data/

# With verbose logging
python main.py satellite_data/ --verbose
```
The main.py in this repo is created for Spot and Pleiades images seperately (main_spot, main_pleiades). There is no difference in the two main files except the spot one has plotting and visualisation enabled and disabled for pleiades (due to memory issues)

This will process all TIF files in the specified directory and generate DSM, shaded relief, and orthophoto outputs. The final geocoded DEM will stored inside data diractory

## 📌 Notes

- Ensure your image files and RPCs are named consistently (`img_b`/`img_f`).
- Projection XML file should be valid and correctly referenced in the commands.
- You can refer to `mm3d_utils.py` for automation or post-processing utilities.
- The pipeline assumes RPC (Rational Polynomial Coefficients) camera model
- Default parameters are optimized for satellite imagery
- Processing time depends on image size and complexity
- Intermediate files are preserved for inspection

