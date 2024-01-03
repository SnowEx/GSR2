# Ground Surface Roughness Reconstruction

Process imagery taken during the SnowEx Alaska 2022 and 2023 fall campaign
to reconstruct the snow pit ground surface roughness. 

The initial imagery recording and processing is inspred by Meloche et al. (2021)
with updates to recording setup.

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
