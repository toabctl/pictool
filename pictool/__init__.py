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

import utils_opencv
import utils_gexiv


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
            data = _do_gps_get(metadata)
            if data:
                print('{}: {} °N {} °W {} m'.format(
                    path, data[0], data[1], data[2]))
            else:
                print('{}: No GPS info'.format(path))


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


def parse_args():
    parser = argparse.ArgumentParser(
        description='Working with images and image metadata')

    subparsers = parser.add_subparsers(title='sub-command help')

    # GPS setter
    parser_gps_set = subparsers.add_parser('gps-set', help='Modify GPS data')
    parser_gps_set.add_argument('--force', action='store_true',
                                help='Override GPS data')
    parser_gps_set.add_argument('longitude', type=float, help='Longitude [°N]')
    parser_gps_set.add_argument('latitude', type=float, help='Latitude [°W]')
    parser_gps_set.add_argument('altitude', type=float, help='Altitude [m]')
    parser_gps_set.add_argument('path', type=str, nargs='+',
                                help='file or directory')
    parser_gps_set.set_defaults(func=gps_set)

    # GPS getter
    parser_gps_get = subparsers.add_parser('gps-get', help='Show GPS location')
    parser_gps_get.add_argument('path', type=str, nargs='+',
                                help='file or directory')
    parser_gps_get.set_defaults(func=gps_get)

    # location setter
    parser_location_set = subparsers.add_parser('location-set',
                                                help='Set location info based '
                                                'on the available GPS data')
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
        '--opencv-data-dir', type=str, default='/usr/share/OpenCV/',
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

    args = parser.parse_args()
    return args


def main():
    args = parse_args()

    args.func(args)
    sys.exit(0)


# for debugging
if __name__ == "__main__":
    main()
