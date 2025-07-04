#!/usr/bin/env python3
"""
Simple Stereo Processing Pipeline using MicMac (mm3d)
Takes input directory and runs stereo processing steps
"""

import os
import sys
import argparse
import logging
from pathlib import Path
import cv2
import numpy as np
import matplotlib.pyplot as plt

from utils import MM3DUtils, ImageUtils, FileUtils, GeoUtils

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def main():
    """Main processing function"""
    parser = argparse.ArgumentParser(description="Stereo Processing using MicMac")
    parser.add_argument("input_dir", help="Input directory containing TIF images")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    input_dir = Path(args.input_dir)
    
    # Validate input directory
    if not input_dir.exists():
        logger.error(f"Input directory does not exist: {input_dir}")
        sys.exit(1)
    
    if not input_dir.is_dir():
        logger.error(f"Input path is not a directory: {input_dir}")
        sys.exit(1)
    
    # Check for TIF files
    tif_files = FileUtils.find_tif_files(input_dir)
    if len(tif_files) < 2:
        logger.error(f"At least 2 TIF files required, found {len(tif_files)}")
        sys.exit(1)
    
    logger.info(f"Found {len(tif_files)} TIF files")
    for tif_file in tif_files:
        logger.info(f"  - {tif_file.name}")
    
    # Create output directory for georeferenced results
    geo_output_dir = input_dir / "geo"
    geo_output_dir.mkdir(exist_ok=True)
    logger.info(f"Created geo output directory: {geo_output_dir}")
    
    # Change to input directory
    original_dir = os.getcwd()
    os.chdir(input_dir)
    logger.info(f"Changed to working directory: {input_dir}")
    
    try:
        # Step 1: Run Tapioca for tie point extraction
        logger.info("Step 1: Running Tapioca for tie point extraction...")
        MM3DUtils.run_tapioca()
        
        # Step 2: Load and visualize images and tie points
        logger.info("Step 2: Loading images and visualizing tie points...")
        img1, img2 = ImageUtils.load_stereo_images(tif_files)
        tie_points = MM3DUtils.load_tie_points(tif_files)
        
        if len(tie_points) > 0:
            ImageUtils.plot_images([img1, img2], ["Image 1", "Image 2"])
            ImageUtils.plot_tie_points(tie_points)
        
        # Step 3: Convert to GenBundle
        logger.info("Step 3: Converting to GenBundle format...")
        MM3DUtils.run_convert2genbundle()
        
        # Step 4: Run Campari for bundle adjustment
        logger.info("Step 4: Running Campari for bundle adjustment...")
        MM3DUtils.run_campari()
        
        # Step 5: Generate DSM using Malt
        logger.info("Step 5: Generating DSM using Malt...")
        MM3DUtils.run_malt()
        
        # Step 6: Generate shaded relief
        logger.info("Step 6: Generating shaded relief...")
        MM3DUtils.run_grshade()
        ImageUtils.display_shaded_relief()
        
        # Step 7: Generate orthophoto
        logger.info("Step 7: Generating orthophoto...")
        MM3DUtils.run_tawny()
        ImageUtils.display_orthophoto()
        
        # Step 8: Georeference the DSM
        logger.info("Step 8: Georeferencing DSM...")
        tfw_file = "MEC-Malt/Z_Num8_DeZoom1_STD-MALT.tfw"
        xml_file = "MEC-Malt/Z_Num8_DeZoom1_STD-MALT.xml"
        dsm_file = "MEC-Malt/Z_Num8_DeZoom1_STD-MALT.tif"
        
        # Check if required files exist
        if not Path(tfw_file).exists():
            logger.error(f"TFW file not found: {tfw_file}")
            sys.exit(1)
        if not Path(xml_file).exists():
            logger.error(f"XML file not found: {xml_file}")
            sys.exit(1)
        if not Path(dsm_file).exists():
            logger.error(f"DSM file not found: {dsm_file}")
            sys.exit(1)
        
        # Output georeferenced DSM
        geo_dsm_output = geo_output_dir / "DSM.tif"
        
        GeoUtils.georeference_dsm(
            tfw_file=tfw_file,
            xml_file=xml_file,
            dsm_file=dsm_file,
            output_file=str(geo_dsm_output),
            epsg_code="EPSG:32638"
        )
        
        logger.info(f"Georeferenced DSM saved to: {geo_dsm_output}")
        logger.info("Stereo processing completed successfully!")
        
    except Exception as e:
        logger.error(f"Processing failed: {e}")
        sys.exit(1)
    finally:
        # Return to original directory
        os.chdir(original_dir)


if __name__ == "__main__":
    main()