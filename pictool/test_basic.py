from argparse import Namespace
import pytest
import pictool
from datetime import datetime
from pathlib import Path


@pytest.mark.parametrize(
    "date_string,expected",
    [
        ('2022-01-20_18:07:50_7700.jpg',
         datetime(year=2022, month=1, day=20, hour=18, minute=7, second=50)),
        ('21-07-01 12-34-42 3162.jpg', None),
    ],
)
def test__datetime_from_str(date_string, expected):
    assert pictool._datetime_from_str(date_string) == expected


def test_image_rename_by_filename(tmp_path):
    orig_path = Path(tmp_path.joinpath('2022-01-20_18:07:50_7700.jpg'))
    orig_path.touch()
    pictool.image_rename(Namespace(output_format_date='%Y%m%d_%H%M%S',
                                   output_format_prefix='IMG_',
                                   path=[tmp_path.as_posix()]))
    renamed_path = Path(tmp_path.joinpath('IMG_20220120_180750.jpg'))
    assert renamed_path.is_file()
    assert not orig_path.exists()


def test_image_rename_by_filename_path_exists(tmp_path):
    orig_path = Path(tmp_path.joinpath('2022-01-20_18:07:50_7700.jpg'))
    orig_path.touch()
    renamed_path_exists = Path(tmp_path.joinpath('IMG_20220120_180750.jpg'))
    renamed_path_exists.touch()
    pictool.image_rename(Namespace(output_format_date='%Y%m%d_%H%M%S',
                                   output_format_prefix='IMG_',
                                   path=[orig_path.as_posix()]))
    renamed_path = Path(tmp_path.joinpath('IMG_20220120_180750_1.jpg'))
    # renamed file should be there
    assert renamed_path.is_file()
    # existing file should still be there
    assert renamed_path_exists.is_file()
    # old file should not be there
    assert not orig_path.exists()
