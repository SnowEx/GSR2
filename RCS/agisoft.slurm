#!/usr/bin/env bash

#SBATCH --job-name=Agisoft_SnowEx
#SBATCH --account=jmeyer
#SBATCH --partition=ondemand-p100

#SBATCH --time=0:30:00 
#SBATCH --ntasks=28
#SBATCH --mem=0
#SBATCH --nodelist=gpu107
#SBATCH --gres=gpu:P100:2

#SBATCH --chdir=/bsuscratch/jmeyer/
#SBATCH --output=slurm-%j.out-%N
#SBATCH --error=slurm-%j.err-%N

module load singularity

run_agisoft -r /bsuhome/jmeyer/projects/GSR2/metashape/process-images.py \
  -if /data/202310-SnowEx/20231017/A765/Sony/ \
  -it .JPG --project-name A765-Sony \
  -op /data/202310-SnowEx/Metashape/ \
  -mf /data/202310-SnowEx/markers.csv \
  --export

