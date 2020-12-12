#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Copyright 2018 Thomas Bechtold <thomasbechtold@jpberlin.de>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


import argparse
import os
import requests
import time
import sys

import pictool.utils_opencv as utils_opencv
import pictool.utils_gexiv as utils_gexiv


def _wait():
    """ wait a second
    requests to http://nominatim.openstreetmap.org/ should be max. 1 per second
    see https://operations.osmfoundation.org/policies/nominatim/
    """
    if 'LAST_WAIT_CALL' not in _wait.__dict__:
        _wait.LAST_WAIT_CALL = None

    if _wait.LAST_WAIT_CALL:
        diff = time.time() - _wait.LAST_WAIT_CALL
        if diff < 1:
            wait_for = 1 - diff
            time.sleep(wait_for)
    _wait.LAST_WAIT_CALL = time.time()


def _get_long_lat_from_query(query, email, countrycodes):
    """get GPS coords from a given query (usually a address)"""
    payload = {
        'format': 'json',
        'polygon_geojson': 1,
        'q': query
    }
    if email:
        payload['email'] = email
    if countrycodes:
        payload['countrycodes'] = ','.join(countrycodes)
    r = requests.get('http://nominatim.openstreetmap.org/search',
                     params=payload)
    if r.status_code != 200:
        r.raise_for_status()
    return r.json()


def _get_location_data(longitude, latitude, email):
    """get location data as json for the given long/lat"""
    payload = {
        'format': 'jsonv2',
        'accept-language': 'en-US',
        'zoom': 10,
        'lat': latitude,
        'lon': longitude}
    if email:
        payload['email'] = email
    _wait()
    r = requests.get('http://nominatim.openstreetmap.org/reverse',
                     params=payload)
    if r.status_code != 200:
        r.raise_for_status()
    return r.json()


def _loop_path(path):
    """loop over the given path argument"""
    for p in path:
        if os.path.isfile(p):
            yield os.path.abspath(p)
        elif os.path.isdir(p):
            for root, dirs, files in os.walk(p):
                for file_path in files:
                    yield os.path.join(root, file_path)
        else:
            raise Exception('"%s" is not a file or a dir' % (p))


def gps_set(args):
    for path in _loop_path(args.path):
        metadata = utils_gexiv.get_metadata(path)
        if metadata:
            # do not override if there is already GPS data
            if not _do_gps_get(metadata) or args.force:
                metadata.set_gps_info(
                    args.longitude, args.latitude, args.altitude)
                metadata.save_file(path)
            else:
                print('{}: GPS data already available. '
                      'Not writing'.format(path))


def _do_gps_get(metadata):
    lon, lat, alt = metadata.get_gps_info()
    # FIXME: This check is not fully correct (how to handle GError in py?)
    if lon == 0 and lat == 0 and alt == 0:
        return None
    else:
        return lon, lat, alt


def gps_get(args=None):
    """print GPS information"""
    for path in _loop_path(args.path):
        metadata = utils_gexiv.get_metadata(path)
        if metadata:
            gps_data = _do_gps_get(metadata)
            if gps_data:
                if args.include_address:
                    location_data = _get_location_data(gps_data[0],
                                                       gps_data[1],
                                                       None)
                    address = location_data.get('address', "")
                else:
                    address = ""

                print('{}: {} °N {} °W {} m {}'.format(
                    path, gps_data[0], gps_data[1], gps_data[2], address))
            else:
                print('{}: No GPS info'.format(path))


def gps_get_from_query(args):
    res = _get_long_lat_from_query(args.query, args.email, None)
    if res:
        if 'lon' in res[0] and 'lat' in res[0]:
            link = 'https://www.openstreetmap.org/?mlat={coords[lat]}&mlon=' \
                '{coords[lon]}#map=19/{coords[lat]}/{coords[lon]}'. \
                format(coords=res[0])
            print('{} °N {} °W {}'.format(res[0]['lon'], res[0]['lat'], link))


def location_set(args):
    """set the location information based on the GPS data"""
    for path in _loop_path(args.path):
        metadata = utils_gexiv.get_metadata(path)
        if not metadata:
            continue
        gps_data = _do_gps_get(metadata)
        if not gps_data:
            continue
        location_data = _get_location_data(gps_data[0],
                                           gps_data[1],
                                           args.email)
        address = location_data.get('address', {})
        dirty = False
        if 'country_code' in address:
            metadata.set_tag_string('Iptc.Application2.CountryCode',
                                    address['country_code'])
            metadata.set_tag_string('Xmp.iptcExt.CountryCode',
                                    address['country_code'])

            dirty = True
        if 'country' in address:
            metadata.set_tag_string('Iptc.Application2.CountryName',
                                    address['country'])
            metadata.set_tag_string('Xmp.iptcExt.CountryName',
                                    address['country'])
            dirty = True
        if 'state' in address:
            metadata.set_tag_string('Iptc.Application2.ProvinceState',
                                    address['state'])
            metadata.set_tag_string('Xmp.iptcExt.ProvinceState',
                                    address['state'])
            dirty = True
        if 'city' in address:
            metadata.set_tag_string('Iptc.Application2.City',
                                    address['city'])
            metadata.set_tag_string('Xmp.iptcExt.City',
                                    address['city'])
            dirty = True
        if 'city_district' in address:
            metadata.set_tag_string('Iptc.Application2.SubLocation',
                                    address['city_district'])
            metadata.set_tag_string('Xmp.iptcExt.SubLocation',
                                    address['city_district'])
            dirty = True
        if dirty:
            metadata.save_file(path)
            print('"{}" Updated location tags'.format(path))


def face_normalize(args):
    """normalize faces from images"""
    face_cascade_path = os.path.join(args.opencv_data_dir,
                                     args.opencv_face_cascade)
    eye_cascade_path = os.path.join(args.opencv_data_dir,
                                    args.opencv_eye_cascade)
    if not os.path.exists(face_cascade_path):
        raise Exception(
            "OpenCV face cascade '%s' does not exist" % (face_cascade_path))
    if not os.path.exists(eye_cascade_path):
        raise Exception(
            "OpenCV eye cascade '%s' does not exist" % (eye_cascade_path))

    # loop over all given images
    for path in _loop_path(args.path):
        image_dest_dir = args.dest_dir or os.path.dirname(path)
        if not os.path.exists(image_dest_dir):
            os.makedirs(image_dest_dir)

        utils_opencv.normalize_face(path, image_dest_dir,
                                    face_cascade_path, eye_cascade_path)


def _set_xmp_region(metadata, region_number,
                    area_unit, area_width, area_height, area_x, area_y,
                    name=None, description=None, type_=None):
    """
    Create a XMP region tag with the given properties

    Note: The metadata object needs to be saved after calling this function!
    """
    # array index must be > 0
    if region_number == 0:
        region_number = 1

    # a single region
    region_list_entry = 'Xmp.mwg-rs.Regions/mwg-rs:RegionList[%d]' % (
        region_number)
    metadata.set_tag_string('%s/mwg-rs:Area/stArea:unit' % (region_list_entry),
                            area_unit)
    metadata.set_tag_string('%s/mwg-rs:Area/stArea:w' % (region_list_entry),
                            area_width)
    metadata.set_tag_string('%s/mwg-rs:Area/stArea:h' % (region_list_entry),
                            area_height)
    metadata.set_tag_string('%s/mwg-rs:Area/stArea:x' % (region_list_entry),
                            area_x)
    metadata.set_tag_string('%s/mwg-rs:Area/stArea:y' % (region_list_entry),
                            area_y)
    if name:
        metadata.set_tag_string('%s/mwg-rs:Name' % (region_list_entry),
                                name)
    if description:
        metadata.set_tag_string('%s/mwg-rs:Description' % (region_list_entry),
                                description)
    if type_:
        metadata.set_tag_string('%s/mwg-rs:Type' % (region_list_entry), type_)


def _image_region_sync_dimensions(metadata):
    """
    Sync the dimension fields for the regions (dest) with the image dimensions
    from the metadata (src).

    Note: The metadata object needs to be saved after calling this function!
    """
    metadata.set_xmp_tag_struct('Xmp.mwg-rs.Regions/mwg-rs:RegionList',
                                utils_gexiv.GExiv2.StructureType.BAG)
    metadata.set_tag_string(
        'Xmp.mwg-rs.Regions/mwg-rs:AppliedToDimensions/stDim:unit', 'pixel')
    metadata.set_tag_long(
        'Xmp.mwg-rs.Regions/mwg-rs:AppliedToDimensions/stDim:w',
        metadata.get_pixel_width())
    metadata.set_tag_long(
        'Xmp.mwg-rs.Regions/mwg-rs:AppliedToDimensions/stDim:h',
        metadata.get_pixel_height())


def image_region_add(args):
    """
    Add a Xmp.mwg-rs.Regions
    """
    metadata = utils_gexiv.get_metadata(args.path)
    if not metadata:
        return
    if not metadata.has_tag('Xmp.mwg-rs.Regions/mwg-rs:RegionList'):
        _image_region_sync_dimensions(metadata)
    _set_xmp_region(metadata, args.region, 'pixel',
                    str(args.width), str(args.height),
                    str(args.x), str(args.y),
                    args.name, args.desc, args.type)
    if not metadata.save_file(args.path):
        print('Not saved!')


def image_region_remove(args):
    """
    Remove a Xmp.mwg-rs.Regions tag for the given region number
    """
    metadata = utils_gexiv.get_metadata(args.path)
    if not metadata:
        return
    dirty = False
    for tag in metadata.get_xmp_tags():
        tag_prefix = 'Xmp.mwg-rs.Regions/mwg-rs:RegionList[{}]'.format(
            args.region)
        if tag.startswith(tag_prefix):
            if not metadata.clear_tag(tag):
                print('Can not remove region tag {}'.format(tag))
            else:
                dirty = True
    if dirty:
        if not metadata.save_file(args.path):
            print('Not saved!')


def md_tag_list(args):
    """
    List metadata tags for the given image(s)
    """
    for path in _loop_path(args.path):
        metadata = utils_gexiv.get_metadata(path)
        if not metadata:
            continue
        tags = []
        tags += metadata.get_exif_tags()
        tags += metadata.get_iptc_tags()
        tags += metadata.get_xmp_tags()
        print('{:<55} {:<10}: {}'.format('tag name', 'tag type', 'value'))
        for tag in tags:
            print('{:<65} {:<10}: {}'.format(
                tag, metadata.get_tag_type(tag) or 'unknown',
                metadata.get_tag_interpreted_string(tag)))


def parse_args():
    parser = argparse.ArgumentParser(
        description='Working with images and image metadata')

    subparsers = parser.add_subparsers(title='sub-command help')

    # metadata list all tags
    parser_md_tag_list = subparsers.add_parser(
        'md-tag-list', help='List all metadata tags for the given '
        'picture(s)')
    parser_md_tag_list.add_argument('path', type=str, nargs='+',
                                    help='file or directory')
    parser_md_tag_list.set_defaults(func=md_tag_list)

    # image regions add
    parser_image_region_add = subparsers.add_parser(
        'image-region-add',
        help='Add image metadata region to the given picture(s)')
    parser_image_region_add.add_argument('path', type=str, help='file')
    parser_image_region_add.add_argument('region', type=int,
                                         help='Region number (must be >= 1)')
    parser_image_region_add.add_argument('width', type=int,
                                         help='Width [px]')
    parser_image_region_add.add_argument('height', type=int,
                                         help='Height [px]')
    parser_image_region_add.add_argument('x', type=int,
                                         help='x coordinate [px]')
    parser_image_region_add.add_argument('y', type=int,
                                         help='y coordinate [px]')
    parser_image_region_add.add_argument('--name', type=str, help='Name')
    parser_image_region_add.add_argument('--desc', type=str,
                                         help='Description')
    parser_image_region_add.add_argument('--type', type=str, help='Type')
    parser_image_region_add.set_defaults(func=image_region_add)

    # image regions remove
    parser_image_region_remove = subparsers.add_parser(
        'image-region-remove', help='Remove image metadata region')
    parser_image_region_remove.add_argument('path', type=str, help='file')
    parser_image_region_remove.add_argument(
        'region', type=int, help='Region number')
    parser_image_region_remove.set_defaults(func=image_region_remove)

    # GPS setter
    parser_gps_set = subparsers.add_parser(
        'gps-set', help='Modify GPS data for the given picture(s). '
        'This does not set the GPS data if the picture(s) already '
        'contains GPS data.')
    parser_gps_set.add_argument('--force', action='store_true',
                                help='Override GPS data even if the '
                                'picture(s) already contain GPS data')
    parser_gps_set.add_argument('longitude', type=float, help='Longitude [°N]')
    parser_gps_set.add_argument('latitude', type=float, help='Latitude [°W]')
    parser_gps_set.add_argument('altitude', type=float, help='Altitude [m]')
    parser_gps_set.add_argument('path', type=str, nargs='+',
                                help='file or directory')
    parser_gps_set.set_defaults(func=gps_set)

    # GPS getter
    parser_gps_get = subparsers.add_parser('gps-get', help='Show GPS location')
    parser_gps_get.add_argument('--include-address', action='store_true',
                                help='Also get address for GPS data')
    parser_gps_get.add_argument('path', type=str, nargs='+',
                                help='file or directory')
    parser_gps_get.set_defaults(func=gps_get)

    # location setter
    parser_location_set = subparsers.add_parser(
        'location-set',
        help='Set location info based on the available GPS data for the '
        'given picture(s). This sets tags like Iptc.Application2.CountryCode')
    parser_location_set.add_argument('--email', type=str, default=None,
                                     help='This should be used if you plan '
                                     'todo a large number of requests against '
                                     'http://nominatim.openstreetmap.org')
    parser_location_set.add_argument('path', type=str, nargs='+',
                                     help='file or directory')
    parser_location_set.set_defaults(func=location_set)

    # face normalization parser
    parser_face_normalize = subparsers.add_parser(
        'face-normalize',
        help='Normalize faces from images and store results in new images')
    # openCV related arguments
    group_opencv = parser_face_normalize.add_argument_group(
        'opencv parameters')
    group_opencv.add_argument(
        '--opencv-data-dir', type=str, default='/usr/share/opencv4/',
        help='This might be different depending on your openCV installation. '
        'Defaults to "%(default)s".')
    group_opencv.add_argument(
        '--opencv-face-cascade', type=str,
        default='haarcascades/haarcascade_frontalface_alt.xml',
        help='A openCV face cascade classifier definition. This is relative '
        'to the base direcectory given via "--opencv-data-dir". '
        'Defaults to "%(default)s".')
    group_opencv.add_argument(
        '--opencv-eye-cascade', type=str,
        default='haarcascades/haarcascade_eye.xml',
        help='A openCV eye cascade classifier definition. This is relative to '
        'the base direcectory given via "--opencv-data-dir". '
        'Defaults to "%(default)s".')

    parser_face_normalize.add_argument(
        '--file-name-prefix', type=str, default='face',
        help='The prefix for the saved normalized image.'
        'Defaults to "%(default)s".')
    parser_face_normalize.add_argument(
        '--dest-dir', type=str,
        help='The destination dir where the face images are stored.'
        'If not given, the images are stored next to the source images.')
    parser_face_normalize.add_argument('path', type=str, nargs='+',
                                       help='file or directory')
    parser_face_normalize.set_defaults(func=face_normalize)

    # helper - get GPS from address query
    parser_gps_get_from_query = subparsers.add_parser(
        'gps-get-from-query',
        help='Get the GPS coords from a given (address) query. '
        'This command does *not* use any picture(s). It is just a helper.'
        'It uses the nominatim service from openstreetmap')
    parser_gps_get_from_query.add_argument(
        '--email', type=str, default=None,
        help='This should be used if you plan todo a large number of requests '
        'against http://nominatim.openstreetmap.org')
    parser_gps_get_from_query.add_argument(
        'query', type=str, help='A query. Usually a address name')
    parser_gps_get_from_query.set_defaults(func=gps_get_from_query)

    return parser


def main():
    parser = parse_args()
    args = parser.parse_args()
    if 'func' not in args:
        sys.exit(parser.print_help())
    args.func(args)
    sys.exit(0)


# for debugging
if __name__ == "__main__":
    main()
