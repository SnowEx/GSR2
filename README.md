# Ground Surface Roughness Reconstruction

Process imagery taken during the SnowEx Alaska 2022 and 2023 fall campaign
to reconstruct the snow pit ground surface roughness. The used ground control
markers when capturing the images can be found under the [docs](docs/markers/README.md) 
folder. 

The initial imagery recording and processing is inspred by Meloche et al. (2021)
with updates to recording setup.

## Processing script
Central entry point to pass to Agisoft Metashape is the 
[process-images.py](metashape/process-images.py) script. A sample call can be 
found under the [RCS](RCS) folder. 

Linux example usage:
```shell
metashape.sh -platform offscreen -r process-images __options__

required options:
  -pn/--project-name
  -op/--output-path
  -if/--image-folder
  -mf/--marker-file

all options:
  -h, --help            show this help message and exit
  -pn PROJECT_NAME, --project-name PROJECT_NAME
                        Name of project.
  -op OUTPUT_PATH, --output-path OUTPUT_PATH
                        Output directory for the Metashape project.
  -if IMAGE_FOLDER, --image-folder IMAGE_FOLDER
                        Location of images relative to base-path.
  -it IMAGE_TYPE, --image-type IMAGE_TYPE
                        Type of images - default to .jpg
  -mf MARKER_FILE, --marker-file MARKER_FILE
                        Path to CSV file with marker distances
  -dcq {1,2,4}, --dense-cloud-quality {1,2,4}
                        Integer for dense point cloud quality. 
                        Highest -> 1 (Default) High -> 2 Medium -> 4
  -exp, --export        Export the PDF report and LAZ point cloud
  --export-only         Only run the export for the PDF report and LAZ point cloud. 
                        NO processing will be performed.
```

## Local point cloud visualization
See the [entwine](docs/entwine.md) instructions on how to visualize points clouds 
with a cloud optimized data format on your local computer.

## Local Development
Below the instructions to develop the Metashape automation locally. This does
not require an installed version with a license of Metashape.

1. Setup conda environment
   ```shell
    conda create -n gsr2 python
   ```
2. Download the Metashape Python package from [their website](https://www.agisoft.com/downloads/installer/)
   ```shell
   pip install /path/to/downloaded/metashape.whl
   ```
3. Install into the conda environment
   ```shell
   conda activate gsr2
   pip install /path/to/metashape.whl
   ```
 
# References
J. Meloche , A. Royer , A. Langlois , N. Rutter & V. Sasseville (2020):
Improvement of microwave emissivity parameterization of frozen Arctic 
soils using roughness measurements derived from photogrammetry, 
International Journal of Digital Earth, 
DOI: [10.1080/17538947.2020.1836049](https://doi.org/10.1080/17538947.2020.1836049)
