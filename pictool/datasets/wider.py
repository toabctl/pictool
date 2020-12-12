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


"""
wider.py can handle images and annotations for the WIDER FACE dataset.
See http://mmlab.ie.cuhk.edu.hk/projects/WIDERFace/ for more details on
the data
"""


from enum import Enum
import os
import sys


class WIDERBBoxInfoBlur(Enum):
    CLEAR = 0
    NORMAL = 1
    HEAVY = 2


class WIDERBBoxInfoExpression(Enum):
    TYPICAL = 0
    EXAGGERATE = 1


class WIDERBBoxInfoIllumination(Enum):
    NORMAL = 0
    EXTREME = 1


class WIDERBBoxInfoOcclusion(Enum):
    NO = 0
    PARTIAL = 1
    HEAVY = 2


class WIDERBBoxInfoPose(Enum):
    TYPICAL = 0
    ATYPICAL = 1


class WIDERBBoxInfoInvalid(Enum):
    FALSE = 0  # valid image
    TRUE = 1  # invalid image


class WIDERBBoxInfo(object):
    """
    :py:class:`WIDERBBoxInfo` represent a bounding box expressed
    in the WIDER FACE dataset.
    The file format and the meaning of the different values in described
    in the readme.txt which is included in the dataset. Here is the current
    (2018-05-17) description::
    The format of txt ground truth.
    File name
    Number of bounding box
    x1, y1, w, h, blur, expression, illumination, invalid, occlusion, pose
    """
    def __init__(self, raw_data):
        """
        :param raw_data: a raw data string (eg. "78 238 14 17 2 0 0 0 0 0 ")
        """
        self._raw_data = raw_data.strip().split()
        self._x = int(self._raw_data[0])
        self._y = int(self._raw_data[1])
        self._width = int(self._raw_data[2])
        self._height = int(self._raw_data[3])
        self._blur = WIDERBBoxInfoBlur(int(self._raw_data[4]))
        self._expression = WIDERBBoxInfoExpression(int(self._raw_data[5]))
        self._illumination = WIDERBBoxInfoIllumination(int(self._raw_data[6]))
        self._invalid = WIDERBBoxInfoInvalid(int(self._raw_data[7]))
        self._occlusion = WIDERBBoxInfoOcclusion(int(self._raw_data[8]))
        self._pose = WIDERBBoxInfoPose(int(self._raw_data[9]))

    @property
    def x(self):
        return self._x

    @property
    def y(self):
        return self._y

    @property
    def w(self):
        return self._width

    @property
    def h(self):
        return self._height

    @property
    def invalid(self):
        return self._invalid

    def __str__(self):
        return u'{} x: {} y: {} width: {} heigth: {} {}'.format(
            self.__class__.__name__, self.x, self.y, self.w, self.h,
            self.invalid)


class WIDERAnnotations(object):
    def __init__(self, annotation_path):
        """
        :param annotation_path: the filesystem path to the annotation file
                                (eg wider_face_train_bbx_gt.txt)
        """
        self._annotation_path = annotation_path
        with open(self._annotation_path, 'r') as f:
            self._annotations = f.read().splitlines()

    def bounding_boxes(self, image_name):
        """
        get bounding boxes information about the given image from the WIDER
        dataset
        :param image_name: the name of the image or a full path to the image
        :returns: list -- of :py:class:`WIDERBBoxInfo` objects for the given
        image name
        :raises: Exception
        """
        boxes = []
        for i, line in enumerate(self._annotations):
            if line.endswith(os.path.basename(image_name)):
                boxes_count = int(self._annotations[i + 1])
                for b in range(0, boxes_count):
                    boxes.append(WIDERBBoxInfo(self._annotations[i + 2 + b]))
                return boxes
        raise Exception('Image name "{}" not found in "{}"'.format(
            image_name, self._annotation_path))


# for debugging
if __name__ == "__main__":
    # import cv2 here. we don't need it in the module itself
    import cv2 # noqa
    if len(sys.argv) != 3:
        print('Usage: %s wider-annotation-file-path wider-image-name' %
              (sys.argv[0]))
        sys.exit(1)

    wider_annotation_path = sys.argv[1]
    wider_image_path = sys.argv[2]
    annotations = WIDERAnnotations(wider_annotation_path)

    boxes = annotations.bounding_boxes(wider_image_path)
    image = cv2.imread(wider_image_path)
    for b in boxes:
        cv2.rectangle(image, (b.x, b.y), (b.x + b.w, b.y + b.h),
                      (255, 0, 0), 2)
    cv2.imshow('img', image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
