import json

import click


@click.command()
@click.option(
    '-n',
    '--name',
    required=False,
    default=None,
    type=str,
    help='Name of tileset')
@click.option(
    '-d',
    '--desc',
    required=False,
    default=None,
    type=str,
    help='Description of tileset')
@click.option(
    '--url', required=True, type=str, multiple=True, help='Tile endpoints.')
@click.option(
    '-a',
    '--attribution',
    required=False,
    default=None,
    type=str,
    help='Attribution text')
@click.argument(
    'file',
    required=True,
    type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True))
def metadata_json_to_tile_json(name, desc, url, attribution, file):
    """Convert metadata.json from Tippecanoe to tile JSON
    """
    with open(file) as f:
        meta = json.load(f)

    tj = {
        'tilejson': '2.2.0',
        'scheme': 'xyz',
        'tiles': list(url),
        'minzoom': int(meta['minzoom']),
        'maxzoom': int(meta['maxzoom']),
        'bounds': list(map(float, meta['bounds'].split(','))),
        'center': list(map(float, meta['center'].split(','))),
    }

    if name is not None:
        tj['name'] = name
    else:
        tj['name'] = meta['name']

    if desc is not None:
        tj['description'] = desc

    if attribution is not None:
        tj['attribution'] = attribution

    click.echo(json.dumps(tj))
