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


import os
import math

# openCV
import cv2


def _image_resize(image, max_w_or_h=4096):
    """
    resize an image but keep the aspect ratio

    :param image: the full path to the image
    :param max_w_or_h: The maximum width or height (in px) of the image
    :returns: the resized image, or the original one if no resize was done
"""
    max_dim = max(image.shape[0], image.shape[1])
    if max_dim > max_w_or_h:
        scale_factor = max_w_or_h / max_dim
        h = int(image.shape[0] * scale_factor)
        w = int(image.shape[1] * scale_factor)
        image_resized = cv2.resize(image, (w, h), cv2.INTER_AREA)
        return image_resized
    return image


def _detect_faces(cascade_path, image):
    """
    detect faces in an image
    """
    cascade_classifier = cv2.CascadeClassifier(cascade_path)
    side = math.sqrt(image.size)
    minlen = int(side / 20)
    maxlen = int(side / 2)
    flags = cv2.CASCADE_DO_CANNY_PRUNING
    faces = cascade_classifier.detectMultiScale(
        image, 1.1, 4, flags, (minlen, minlen), (maxlen, maxlen))
    print('Found %s face(s)' % (len(faces)))
    return faces
    # for i, (x, y, w, h) in enumerate(faces, 1):
    #     cv2.rectangle(image_resize, (x, y), (x + w , y + h), (255, 0, 0), 2)
    #     cv2.imshow('img',image_resize)
    #     cv2.waitKey(0)
    #     cv2.destroyAllWindows()


def _detect_eyes(cascade_path, image):
    """get the eye coords for the given image file"""
    cascade_classifier = cv2.CascadeClassifier(cascade_path)
    minlen = 50
    flags = cv2.CASCADE_DO_CANNY_PRUNING
    eyes = cascade_classifier.detectMultiScale(
        image, 1.1, 4, flags, (minlen, minlen))
    print('Found %s eye(s)' % (len(eyes)))
    return eyes


def normalize_face(image_input_path, image_output_dir,
                   face_cascade_path, eye_cascade_path):
    """
    Normalize the given image and write it out
    :param image_input_path: The full path to the image file
    :param image_output_dir: The directory where to write the normalized
    images to
    :param face_cascade_path: A openCV face cascade classifier definition
    file path
    :param eye_cascade_path: A openCV eye cascade classifier definition
    file path
    """
    image_org = cv2.imread(image_input_path, cv2.IMREAD_GRAYSCALE)
    image_resize = _image_resize(image_org)
    image_name = os.path.basename(image_input_path)

    # iterate over all found faces
    for i, face in enumerate(
            _detect_faces(face_cascade_path, image_resize), 1):
        face_x, face_y, face_w, face_h = face
        image_face = image_resize[face_y:(face_y + face_h),
                                  face_x:(face_x + face_w)]
        # iterate over all found eyes in the the current face
        for eye in _detect_eyes(eye_cascade_path, image_face):
            eye_x, eye_y, eye_w, eye_h = eye
            cv2.rectangle(image_face, (eye_x, eye_y),
                          (eye_x + eye_w, eye_y + eye_h), (255, 0, 0), 2)
        image_face_name = 'face%02i-%s' % (i, image_name)
        image_face_path = os.path.join(image_output_dir, image_face_name)
        cv2.imwrite(image_face_path, image_face)
