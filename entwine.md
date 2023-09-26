Notes on how to convert point clouds in `.laz` format to the cloud
optimized [entwine](https://entwine.io/en/latest/) format. The converted clouds
can be visualized with [potree](https://github.com/potree/potree/).

# Convert `.laz` to entwine
```shell
entwine build -i /path/to/pointcloud.laz -0 /path/to/entwine/out/
```

# Visualize
## Run local HTTP server for entwine directory
```shell
http-server /path/to/entwine/out -p 3001 --cors
```

## Run potree to view
```shell
npm start
```
In a browser:  
http://localhost:1234/examples/ept.html?r=http://127.0.0.1:3001/D768/ept.json

# Installation
## Create new conda env with entwine
```shell
micromamba create -n entwine entwine
```

## Setup local http server
This will serve as data source for potree web app.
```shell
micromamba install nodejs -y
npm install http-server -g
```

## potree
The actual webapp to view the clouds.
```shell
git clone git@github.com:potree/potree.git
npm install
```
