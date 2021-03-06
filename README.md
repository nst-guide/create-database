# NST Guide Data

## Overview

This repository contains code for data pipelines to generate map waypoints and layers of interest from open map data sources.

### Data Sources

- Town Boundaries: for now, these are drawn by hand using local trail knowledge and <https://geojson.io> and saved to `data/pct/polygon/bound/town/{ca,or,wa}/*.geojson`.
- [OpenStreetMap](openstreetmap.org): I use OSM for trail information and town
  waypoints. Initially, I planned to download whole-state extracts from
  [Geofabrik](https://www.geofabrik.de/data/download.html). After discovering
  the [osmnx](https://github.com/gboeing/osmnx) package for Python, I decided to
  use that instead. That calls OSM's [Overpass
  API](https://wiki.openstreetmap.org/wiki/Overpass_API), and then helpfully
  manages the result in a graph. This has a few benefits:

    - No need to download any large files. Using the Geofabrik extracts,
      California is nearly 1GB of compressed data, and most of that is far from
      the trail, and really not necessary for this project.
    - Speed. Unsurprisingly, when you're working with 1GB of compressed data
      just for california, computations aren't going to be super fast.
    - Faster updates. Geofabrik extracts are updated around once a week I think,
      while the Overpass API has near-instant updating. That means that if I fix
      an issue with the data in OSM's editor, then I can get working with the
      new data immediately.

- [Halfmile](pctmap.net): Halfmile has accurate route information and a few
  thousand waypoints for the trail. I have yet to hear final confirmation that
  this is openly licensed, but I've seen other projects using this data, and am
  optimistic that the use will be ok.
- USFS: The US Forest Service is the US governmental body that officially
  stewards the Pacific Crest Trail. As such, they keep an official centerline of
  the trail, but it is much less accurate than the Halfmile or OpenStreetMap
  centerlines. The PCT USFS page is here: <https://www.fs.usda.gov/pct/>.
- GPSTracks: On my hike of the PCT in 2019, I recorded my own GPS data,
  generally at 5-second intervals. This raw data has been copied into
  `data/raw/tracks`. While it's generally not accurate enough to use as an
  official centerline for an app, it will be helpful to use to geocode photos,
  and thus fill in waypoints that are missing from open data sources.
- Wilderness Boundaries: Wilderness boundaries are retrieved from <https://wilderness.net>.
- National Park Boundaries: National Park boundaries are retrieved from the [NPS open data portal](https://public-nps.opendata.arcgis.com/datasets/b1598d3df2c047ef88251016af5b0f1e_0).
- National Forest Boundaries: National Forest boundaries are retrieved from the [USFS website](https://data.fs.usda.gov/geodata/edw/datasets.php?dsetCategory=boundaries), under the heading _Administrative Forest Boundaries_.
- State Boundaries: State boundaries from the Census' [TIGER dataset](https://www2.census.gov/geo/tiger/TIGER2017/STATE/).
- Cell Towers: Cell tower data come from [OpenCellID](www.opencellid.org).
  Ideally at some point I'll implement a simple line-of-sight algorithm and then
  calculate where on the trail has cell service.
- Lightning Counts: daily lightning counts for 0.1-degree bins are available
  since ~1986 from
  [NOAA](https://www.ncdc.noaa.gov/data-access/severe-weather/lightning-products-and-services).
  Note that the raw data of where every lightning strike hits is closed source
  and must be purchased, but a NOAA contract lets daily extracts be made public.
- Transit: I get transit data from the [Transitland](https://transit.land) database.
  This is a bit easier than working with raw GTFS (General Transit Feed
  Specification) data, and they've done a bit of work to deduplicate data and
  connect the same stops in different data extracts from different providers.
- National Elevation Dataset: In the US, the most accurate elevation data comes from the USGS's [3D Elevation Program](https://www.usgs.gov/core-science-systems/ngp/3dep/data-tools). They have a seamless Digital Elevation Model (DEM) at 1/3 arc-second resolution, which is about 10 meters.
- USGS Hydrography: The USGS's [National Hydrography products](https://www.usgs.gov/core-science-systems/ngp/national-hydrography/about-national-hydrography-products) are the premier water source datasets for the US. The Watershed Boundary dataset splits the US into a pyramid of smaller and smaller hydrologic regions. I first use the Watershed Boundary dataset to find the watersheds that the PCT passes through, then go to the National Hydrography dataset to find all streams, lakes, and springs near the trail.
- [PCT Water Report](pctwater.net): The PCT water report is an openly-licensed set of spreadsheets with reports from hikers of which water sources are flowing.
- EPA AirNow: The EPA has an [API](https://docs.airnowapi.org/) where you can access current air quality regions.
- NIFC: National Interagency Fire Center. GeoMAC is closing as of the end of
  April 2020, and NIFC is the new place for retrieving wildfire boundaries.
- CalFire
- Recreation.gov: Recreation.gov has an API for accessing information about features in National Forests.

### Repository Structure

- `data_source/`: This folder contains wrappers for each individual data source.
  Files are generally named by the organization that releases the data I use,
  and there can be more than one loader in each file. These classes attempt to
  abstract reading of the original data, though the classes do not all have the
  same interface. These should hold only function/class definitions, and no code
  should be evaluated when the script is run.
- `geom.py`: This file holds geometric abstractions. Included are functions to
  reproject data between CRS's, truncate precision of geometries, create buffers
  at a given distance around a geometry, and project 3D coordinates onto the 2D
  plane. Again, this file should only define functions and constants, and not
  evaluate anything itself.
- `grid.py`: Helpers for generating intersections with regularly spaced grids.
  For example, USGS elevation files, or topo quads, are packaged for download in
  a regular grid, and this helps to find which files intersect a provided
  geometry. Note that for USGS data, it's probably easier to just use the USGS
  National Map API.
- `main.py`: This should handle delegating commands to other files. I.e. the
  only file that should be run directly from the command line.
- `parse.py`: This is a wrapper for uploading data to my [Parse
  Server](https://docs.parseplatform.org/parse-server/guide/) instance. It wraps
  the [Parse REST API](https://docs.parseplatform.org/rest/guide/) to upload
  Parse's custom classes, like `GeoPoint`s. Also in this file (?) is where
  schema-checking will take place, making sure data uploads conform to the [JSON
  schemas defined here](https://github.com/nst-guide/schema).
- `s3.py`: Wrapper for the AWS S3 CLI. This doesn't use `boto3` directly,
  because I already knew the CLI commands I wanted to use, and didn't want to
  spend the time figuring out boto3.
- `tiles.py`: This holds functions to make working with tiled data easier. Like
  supplying a Polygon and getting the [XYZ or TMS tile
  coordinates](https://wiki.openstreetmap.org/wiki/Slippy_map_tilenames).
- `trail.py`: This holds the meat of taking the data sources and assembling them into a useful dataset.
- `util.py`: Small non-geometric utilities

## Auto-updating layers

There are a few layers that are designed to auto-update:

- National Weather Service forecasts
- EPA AirNow air quality polygons
- National Interagency Fire Center (NIFC) current wildfire polygons

The first is handled in a separate repository:
[nst-guide/ndfd_current](https://github.com/nst-guide/ndfd_current). The second
two are defined within this repository. All three are designed to be run with
AWS Lambda.

### AWS Lambda

From Wikipedia:

> AWS Lambda is an event-driven, serverless computing platform provided by
> Amazon as a part of Amazon Web Services. It is a computing service that runs
> code in response to events and automatically manages the computing resources
> required by that code.

Basically, AWS Lambda is a (somewhat) easy, very cheap way to run small pieces
of code regularly or in response to events. For all of my use cases above, I can
set AWS Lambda to run every few hours.

In my testing of my code to update wildfire perimeters from NIFC, it used 244 MB
of memory and took 8178.56 ms to run. From the [AWS Lambda pricing
page](https://aws.amazon.com/lambda/pricing/), it's roughly $0.0000005 for each
100ms when 320MB of memory is allocated. That means the 8100ms job cost
$0.0000405, and running it every 4 hours would cost $0.00729 every 30 days. Aka
basically free.


#### AWS Lambda Downsides

The biggest downsides of AWS Lambda by far are the hard
[limits](https://docs.aws.amazon.com/lambda/latest/dg/limits.html) on how big
your Deployment Package (aka all unzipped code, including all dependencies) can
be: **250MB**. When some of your dependencies are GDAL, GeoPandas -> pandas ->
numpy, that limit is really easy to surpass. I've been unable to include _either_ GeoPandas or Fiona (on their own, not together) inside the deployment package.

This means that rewriting code to avoid dependencies on any large library, such
as GeoPandas and Fiona, is inevitable.

#### AWS Lambda Dependencies

You can't just `pip install gdal`, or use `conda`, or even use Docker in AWS
Lambda. All your code and dependencies must be pre-built and provided as a Zip
file.

Luckily, AWS Lambda has the concept of _Lambda Layers_. These are code packages created
by you or by others that you can point to and use, without having to package the
code yourself. So you can include a layer for, say, `GDAL`, and then run code
that depends on GDAL libraries without an issue.

You can only use a **maximum of five** with any given function. In practice,
this shouldn't be as bad as it sounds because you could zip multiple
dependencies into a single layer. The bigger problem in practice is hitting
Lambda's 250MB hard limit on repository size.

To use a layer, the easiest way is to include its Amazon Resource Number (ARN).
So, for example, to include `geolambda`, I can go to
```
{my function} > Layers > Add a layer > Provide a layer version ARN
```
and paste
```
arn:aws:lambda:us-east-1:552188055668:layer:geolambda:4
```
the unique identifier for that specific version of `geolambda` that I use. Note
that layers are specific to an AWS region, so the layer referenced by this
specific ARN will only work in US-East-1. Sometimes layers will be pre-built in
multiple regions. For example, `geolambda` is pre-built in US-East-1, US-West-2,
and EU-Central-1. To use the layer in any other AWS region, you'd have to build
and upload the layer yourself to that region.

I use several layers:

- [`geolambda` and
  `geolambda-python`](https://github.com/developmentseed/geolambda/). These are
  immensely helpful layers that provide geospatial libraries within Lambda.
  `geolambda` provides PROJ.5, GEOS, GeoTIFF, HDF4/5, SZIP, NetCDF, OpenJPEG,
  WEBP, ZSTD, and GDAL. `geolambda-python` additionally provides GDAL (the
  Python bindings), rasterio, shapely, pyproj, and numpy. Note that if you want
  to use the Python bindings, you must provide _both_, not just
  `geolambda-python`.

  It is possible to build both `geolambda` and `geolambda-python` layers
  yourself. Their Github READMEs have pretty good documentation, and I was able
  to build `geolambda-python` myself (as you would need to if you wanted to
  modify the package list.)

- `Klayers-python37-requests`.
  [Klayers](https://github.com/keithrozario/Klayers) is a project to provide
  many common Python libraries as lambda layers. This is just an easy way to
  access `requests`, though in this case it would be easy to build yourself.

And a couple packaged by me:

- `nst-guide-fastkml-python37`: provides the
  [`fastkml`](https://github.com/cleder/fastkml) package
- `nst-guide-geojson-python37`: provides the
  [`geojson`](https://github.com/jazzband/geojson) package
- `nst-guide-pyshp-python37`: provides the
  [`pyshp`](https://github.com/GeospatialPython/pyshp) package. Because Fiona
  was too big to be packaged on AWS Lambda, and I needed to read Shapefiles for
  the wildfire perimeters updating, I had to find an alternative. Luckily,
  `pyshp` is able to read shapefiles and is only ~200KB of code.

#### Packaging dependencies for AWS Lambda

As mentioned above, sometimes you'll need to build lambda layers yourself. [This
article](https://dev.to/vealkind/getting-started-with-aws-lambda-layers-4ipk)
was pretty helpful. The general gist is:
```
mkdir -p layer/python
pip install {package_list} -t layer/python
cd layer
zip -r aws-layer.zip python
```
Then go to the AWS Lambda console, choose Layers from the side pane, and upload
the Zip archive as a new layer.

**Python packages must be within a `python/` directory in the Zip archive.** You
won't be able to load the library without the top-level `python` directory.

Also, if the Python packages have any (or depend on any) native code, you should
run the above packaging steps on a Linux machine, so that the layer will work on
Amazon's linux-based architecture. For pure-Python packages, you should be able
build the Zip archive on any OS.

#### AWS Lambda IAM Role

Each of my AWS Lambda functions upload files to AWS S3 in order to be served to
users. This means that the function must be associated with a valid IAM role to
be permitted to access and modify files in my S3 bucket.

Note that in order to use the `ACL='public-read'` option, the IAM role running
the Lambda function [must also have the `S3:putObjectAcl`
permission](https://stackoverflow.com/questions/36272286/getting-access-denied-when-calling-the-putobject-operation-with-bucket-level-per).
