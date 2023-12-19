# Helper scripts to run on BSU RCS systems

## `run_agisoft`
Wrapper to run the Agisoft Singularity image headless via command line.

### Important Singularity flags
`--nv` - Allows access to all GPUs within the image  
`--bind` of `bsushare` to `/data`; allows writing to the shared drive.

