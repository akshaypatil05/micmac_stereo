#!/usr/bin/env python3
"""
Utility functions for stereo processing
"""

import os
import subprocess
import logging
from pathlib import Path
from typing import List, Optional
import numpy as np
import cv2
from osgeo import gdal
import matplotlib.pyplot as plt
import xml.etree.ElementTree as ET

logger = logging.getLogger(__name__)


class MM3DUtils:
    """Utility functions for running MM3D commands"""
    
    @staticmethod
    def run_command(command: str, description: str = ""):
        """Run a shell command and log output"""
        logger.info(f"Running: {description if description else command}")
        logger.debug(f"Command: {command}")
        
        try:
            result = subprocess.run(command, shell=True, check=True, 
                                  capture_output=True, text=True)
            logger.info(f"Command completed successfully")
            if result.stdout:
                logger.debug(f"Output: {result.stdout}")
        except subprocess.CalledProcessError as e:
            logger.error(f"Command failed with return code {e.returncode}")
            logger.error(f"Error output: {e.stderr}")
            raise
    
    @staticmethod
    def run_tapioca():
        """Run Tapioca for tie point extraction"""
        command = 'mm3d Tapioca All ".*.TIF" -1 ExpTxt=1 @ExitOnBrkp'
        MM3DUtils.run_command(command, "Tapioca tie point extraction")
    
    @staticmethod
    def run_convert2genbundle():
        """Run Convert2GenBundle"""
        command = 'mm3d Convert2GenBundle "(.*).TIF" "\\$1.XML" RPC-d0 ChSys=WGS84toUTM.xml Degre=0 @ExitOnBrkp'
        MM3DUtils.run_command(command, "Convert2GenBundle")
    
    @staticmethod
    def run_campari():
        """Run Campari for bundle adjustment"""
        command = 'mm3d Campari ".*TIF" RPC-d0 RPC-d0-adj ExpTxt=1 @ExitOnBrkp'
        MM3DUtils.run_command(command, "Campari bundle adjustment")
    
    @staticmethod
    def run_malt():
        """Run Malt for DSM generation"""
        command = 'mm3d Malt UrbanMNE ".*TIF" RPC-d0-adj SzW=2 Regul=0.2 DoOrtho=1 NbVI=2 EZA=1 @ExitOnBrkp'
        MM3DUtils.run_command(command, "Malt DSM generation")
    
    @staticmethod
    def run_grshade():
        """Run GrShade for shaded relief"""
        command = 'mm3d GrShade MEC-Malt/Z_Num8_DeZoom1_STD-MALT.tif ModeOmbre=IgnE Mask=MEC-Malt/Masq_STD-MALT_DeZoom1.tif @ExitOnBrkp'
        MM3DUtils.run_command(command, "GrShade shaded relief")
    
    @staticmethod
    def run_tawny():
        """Run Tawny for orthophoto generation"""
        command = 'mm3d Tawny Ortho-MEC-Malt/ @ExitOnBrkp'
        MM3DUtils.run_command(command, "Tawny orthophoto generation")
    
    @staticmethod
    def load_tie_points(tif_files: List[Path]) -> np.ndarray:
        """Load tie points from Homol directory"""
        if len(tif_files) < 2:
            return np.array([])
        
        # Try to find homol file
        img1_name = tif_files[0].name
        img2_name = tif_files[1].name
        
        homol_file = Path(f"Homol/Pastis{img2_name}/{img1_name}.txt")
        if not homol_file.exists():
            homol_file = Path(f"Homol/Pastis{img1_name}/{img2_name}.txt")
        
        if not homol_file.exists():
            logger.warning("No homol file found")
            return np.array([])
        
        logger.info(f"Loading tie points from: {homol_file}")
        
        try:
            tie_points = []
            with open(homol_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        parts = line.split()
                        if len(parts) >= 4:
                            x1, y1, x2, y2 = map(float, parts[:4])
                            tie_points.append([x1, y1, x2, y2])
            
            if tie_points:
                points_array = np.array(tie_points)
                logger.info(f"Loaded {len(points_array)} tie points")
                return points_array
            else:
                logger.warning("No valid tie points found in file")
                return np.array([])
                
        except Exception as e:
            logger.error(f"Error loading tie points: {e}")
            return np.array([])


class ImageUtils:
    """Utility functions for image processing and visualization"""
    
    @staticmethod
    def load_stereo_images(tif_files: List[Path]):
        """Load the first two TIF images"""
        if len(tif_files) < 2:
            raise ValueError("At least 2 TIF files required")
        
        img1_path = tif_files[0]
        img2_path = tif_files[1]
        
        logger.info(f"Loading images: {img1_path.name} and {img2_path.name}")
        
        img1 = cv2.imread(str(img1_path), cv2.IMREAD_IGNORE_ORIENTATION)
        img2 = cv2.imread(str(img2_path), cv2.IMREAD_IGNORE_ORIENTATION)
        
        if img1 is None:
            raise ValueError(f"Failed to load image: {img1_path}")
        if img2 is None:
            raise ValueError(f"Failed to load image: {img2_path}")
        
        return img1, img2
    
    @staticmethod
    def plot_images(images: List[np.ndarray], titles: List[str] = None):
        """Plot multiple images side by side"""
        n_images = len(images)
        fig, axes = plt.subplots(1, n_images, figsize=(20, 10))
        
        if n_images == 1:
            axes = [axes]
        
        for i, img in enumerate(images):
            if len(img.shape) == 3:
                img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            else:
                img_rgb = img
            
            axes[i].imshow(img_rgb)
            if titles and i < len(titles):
                axes[i].set_title(titles[i])
            axes[i].axis('off')
        
        plt.tight_layout()
        plt.show()
    
    @staticmethod
    def plot_tie_points(tie_points: np.ndarray):
        """Plot tie points"""
        if len(tie_points) == 0:
            logger.warning("No tie points to plot")
            return
        
        # Limit points for visualization
        max_points = 100
        if len(tie_points) > max_points:
            indices = np.random.choice(len(tie_points), max_points, replace=False)
            points_to_plot = tie_points[indices]
        else:
            points_to_plot = tie_points
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
        
        # Plot points from first image
        ax1.scatter(points_to_plot[:, 0], points_to_plot[:, 1], 
                   c='red', s=2, alpha=0.7)
        ax1.set_title(f'Tie Points - Image 1 ({len(points_to_plot)} points)')
        ax1.set_xlabel('X')
        ax1.set_ylabel('Y')
        ax1.invert_yaxis()
        
        # Plot points from second image
        ax2.scatter(points_to_plot[:, 2], points_to_plot[:, 3], 
                   c='blue', s=2, alpha=0.7)
        ax2.set_title(f'Tie Points - Image 2 ({len(points_to_plot)} points)')
        ax2.set_xlabel('X')
        ax2.set_ylabel('Y')
        ax2.invert_yaxis()
        
        plt.tight_layout()
        plt.show()
    
    @staticmethod
    def display_shaded_relief():
        """Display shaded relief image"""
        shade_file = "MEC-Malt/Z_Num8_DeZoom1_STD-MALTShade.tif"
        
        if not Path(shade_file).exists():
            logger.warning(f"Shaded relief file not found: {shade_file}")
            return
        
        surface_shade = cv2.imread(shade_file, cv2.IMREAD_IGNORE_ORIENTATION)
        
        if surface_shade is None:
            logger.error("Failed to load shaded relief image")
            return
        
        fig, ax = plt.subplots(figsize=(30, 10))
        ax.imshow(surface_shade, cmap="gray")
        ax.set_title("Shaded Relief")
        ax.axis('off')
        plt.tight_layout()
        plt.show()
    
    @staticmethod
    def display_orthophoto():
        """Display orthophoto"""
        ortho_file = "Ortho-MEC-Malt/Orthophotomosaic.tif"
        
        if not Path(ortho_file).exists():
            logger.warning(f"Orthophoto file not found: {ortho_file}")
            return
        
        ortho_img = cv2.imread(ortho_file, cv2.IMREAD_IGNORE_ORIENTATION)
        
        if ortho_img is None:
            logger.error("Failed to load orthophoto image")
            return
        
        fig, ax = plt.subplots(figsize=(30, 10))
        ax.imshow(ortho_img, cmap='grey', vmin=0, vmax=50)
        ax.set_title("Orthophoto Mosaic")
        ax.axis('off')
        plt.tight_layout()
        plt.show()


class FileUtils:
    """Utility functions for file operations"""
    
    @staticmethod
    def find_tif_files(directory: Path) -> List[Path]:
        """Find all TIF files in directory"""
        tif_files = []
        
        # Look for different TIF extensions
        for pattern in ['*.tif', '*.TIF', '*.tiff', '*.TIFF']:
            tif_files.extend(directory.glob(pattern))
        
        # Sort files for consistent ordering
        tif_files.sort()
        
        return tif_files


class GeoUtils:
    """Utility functions for georeferencing operations"""
    
    @staticmethod
    def read_tfw_file(tfw_file: str) -> dict:
        """Read TFW world file and return parameters"""
        logger.info(f"Reading TFW file: {tfw_file}")
        
        try:
            with open(tfw_file, 'r') as f:
                lines = f.readlines()
            
            if len(lines) < 6:
                raise ValueError(f"Invalid TFW file format. Expected 6 lines, got {len(lines)}")
            
            tfw_params = {
                'pixel_size_x': float(lines[0].strip()),      # meters per pixel (X direction)
                'rotation_y': float(lines[1].strip()),        # rotation about Y-axis
                'rotation_x': float(lines[2].strip()),        # rotation about X-axis
                'pixel_size_y': float(lines[3].strip()),      # meters per pixel (Y direction)
                'upper_left_x': float(lines[4].strip()),      # X-coordinate of upper-left
                'upper_left_y': float(lines[5].strip())       # Y-coordinate of upper-left
            }
            
            logger.info(f"TFW parameters loaded: {tfw_params}")
            return tfw_params
            
        except Exception as e:
            logger.error(f"Error reading TFW file: {e}")
            raise
    
    @staticmethod
    def read_xml_dimensions(xml_file: str) -> tuple:
        """Read image dimensions from XML file"""
        logger.info(f"Reading XML file: {xml_file}")
        
        try:
            tree = ET.parse(xml_file)
            root = tree.getroot()
            
            nb_pixel_elem = root.find("NombrePixels")
            if nb_pixel_elem is None:
                raise ValueError("NombrePixels element not found in XML")
            
            nb_pixel = nb_pixel_elem.text
            image_width, image_height = map(int, nb_pixel.split())
            
            logger.info(f"Image dimensions: {image_width} x {image_height}")
            return image_width, image_height
            
        except Exception as e:
            logger.error(f"Error reading XML file: {e}")
            raise
    
    @staticmethod
    def calculate_bounds(tfw_params: dict, image_width: int, image_height: int) -> dict:
        """Calculate geographic bounds from TFW parameters and image dimensions"""
        upper_left_x = tfw_params['upper_left_x']
        upper_left_y = tfw_params['upper_left_y']
        pixel_size_x = tfw_params['pixel_size_x']
        pixel_size_y = tfw_params['pixel_size_y']
        
        # Calculate lower-right coordinates
        lower_right_x = upper_left_x + (image_width * pixel_size_x)
        lower_right_y = upper_left_y + (image_height * pixel_size_y)
        
        bounds = {
            'upper_left_x': upper_left_x,
            'upper_left_y': upper_left_y,
            'lower_right_x': lower_right_x,
            'lower_right_y': lower_right_y
        }
        
        logger.info(f"Calculated bounds: {bounds}")
        logger.info(f"Calculation: X={upper_left_x} + ({image_width} × {pixel_size_x}) = {lower_right_x}")
        logger.info(f"Calculation: Y={upper_left_y} + ({image_height} × {pixel_size_y}) = {lower_right_y}")
        
        return bounds
    
    @staticmethod
    def georeference_dsm(tfw_file: str, xml_file: str, dsm_file: str, 
                        output_file: str, epsg_code: str = "EPSG:32638"):
        """Georeference DSM using TFW and XML files"""
        logger.info(f"Georeferencing DSM: {dsm_file}")
        
        try:
            # Read TFW parameters
            tfw_params = GeoUtils.read_tfw_file(tfw_file)
            
            # Read image dimensions from XML
            image_width, image_height = GeoUtils.read_xml_dimensions(xml_file)
            
            # Calculate bounds
            bounds = GeoUtils.calculate_bounds(tfw_params, image_width, image_height)
            
            # Build gdal_translate command
            command = (
                f"gdal_translate -of GTiff -a_srs {epsg_code} "
                f"-a_ullr {bounds['upper_left_x']} {bounds['upper_left_y']} "
                f"{bounds['lower_right_x']} {bounds['lower_right_y']} "
                f'"{dsm_file}" "{output_file}"'
            )
            
            logger.info(f"Running gdal_translate command:")
            logger.info(f"  Command: {command}")
            
            # Execute gdal_translate
            result = subprocess.run(command, shell=True, check=True, 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info(f"Successfully georeferenced DSM to: {output_file}")
                if result.stdout:
                    logger.debug(f"gdal_translate output: {result.stdout}")
            else:
                logger.error(f"gdal_translate failed with return code: {result.returncode}")
                if result.stderr:
                    logger.error(f"gdal_translate error: {result.stderr}")
                raise subprocess.CalledProcessError(result.returncode, command)
            
        except Exception as e:
            logger.error(f"Error georeferencing DSM: {e}")
            raise