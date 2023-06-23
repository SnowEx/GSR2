# Ground Surface Roughness Reconstruction

Process imagery taken during the SnowEx Alaska 2022 fall campaign
to reconstruct the snow pit ground surface roughness. 

The initial imagery recording and processing is based on:
J. Meloche , A. Royer , A. Langlois , N. Rutter & V. Sasseville (2020):
Improvement of microwave emissivity parameterization of frozen Arctic 
soils using roughness measurements derived from photogrammetry, 
International Journal of Digital Earth, 
DOI: [10.1080/17538947.2020.1836049](https://doi.org/10.1080/17538947.2020.1836049)


## Local Development
Below the instructions to develop the Metashape automation locally. This does
not require an installed version with a license of Metashape.

1. Setup conda environment
   ```shell
    conda create -n gsr2 python
   ```
2. Download the Metashape Python package from [their website](https://www.agisoft.com/downloads/installer/)
3. Install into the conda environment
   ```shell
   conda activate gsr2
   pip install /path/to/metashape.whl
   ```
