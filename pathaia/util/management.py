"""
Helpful function to extract and organize data.

It takes advantage of the common structure of pathaia projects to enable
datasets creation and experiment monitoring/evaluation.
"""

import pandas as pd
import os
import warnings


class Error(Exception):
    """
    Base of custom errors.

    **********************
    """

    pass


class LevelNotFoundError(Error):
    """
    Raise when trying to access unknown level.

    *********************************************
    """

    pass


class EmptyProjectError(Error):
    """
    Raise when trying to access unknown level.

    *********************************************
    """

    pass


class SlideNotFoundError(Error):
    """
    Raise when trying to access unknown level.

    *********************************************
    """

    pass


class PatchesNotFoundError(Error):
    """
    Raise when trying to access unknown level.

    *********************************************
    """

    pass


class UnknownColumnError(Error):
    """
    Raise when trying to access unknown level.

    *********************************************
    """

    pass


def get_patch_csv_from_patch_folder(patch_folder):
    """
    Give csv of patches given the slide patch folder.

    Check existence of the path and return absolute path of the csv.

    Args:
        patch_folder (str): absolute path to a pathaia slide folder.

    Returns:
        str: absolute path of csv patch file.

    """
    if os.path.isdir(patch_folder):
        patch_file = os.path.join(patch_folder, "patches.csv")
        if os.path.exists(patch_file):
            return patch_file
        raise PatchesNotFoundError(
            "Could not find extracted patches for the slide: {}".format(patch_folder)
        )
    raise SlideNotFoundError(
        "Could not find a patch folder at: {}!!!".format(patch_folder)
    )


def get_patch_folders_in_project(project_folder, exclude=["annotation"]):
    """
    Give pathaia slide folders from a pathaia project folder (direct subfolders).

    Check existence of the project and yield slide folders inside.

    Args:
        project_folder (str): absolute path to a pathaia project folder.
        exclude (list of str): a list of str to exclude from subfolders of the project.
    Yields:
        tuple of str: name of the slide and absolute path to its pathaia folder.

    """
    if not os.path.isdir(project_folder):
        raise EmptyProjectError(
            "Did not find any project at: {}".format(project_folder)
        )
    for name in os.listdir(project_folder):
        keep = True
        for ex in exclude:
            if ex in name:
                keep = False
        if keep:
            patch_folder = os.path.join(project_folder, name)
            if os.path.isdir(patch_folder):
                yield name, patch_folder


def get_slide_file(slide_folder, slide_name):
    """
    Give the absolute path to a slide file.

    Get the slide absolute path if slide name and slide folder are provided.

    Args:
        slide_folder (str): absolute path to a folder of WSIs.
        slide_name (str): basename of the slide.
    Returns:
        str: absolute path of the WSI.

    """
    if not os.path.isdir(slide_folder):
        raise SlideNotFoundError(
            "Could not find a slide folder at: {}!!!".format(slide_folder)
        )
    for name in os.listdir(slide_folder):
        if name.endswith(".mrxs") and not name.startswith("."):
            base, _ = os.path.splitext(name)
            if slide_name == base:
                return os.path.join(slide_folder, name)
    raise SlideNotFoundError(
        "Could not find an mrxs slide file for: {} in {}!!!".format(slide_name,
                                                                    slide_folder)
    )


def handle_labeled_patches(patch_file, level, column):
    """
    Read a patch file.

    Read lines of the patch csv looking for 'column' label.

    Args:
        patch_file (str): absolute path to a csv patch file.
        level (int): pyramid level to query patches in the csv.
        column (str): header of the column to use to label individual patches.

    Yields:
        tuple: position and label of patches (x, y, label).

    """
    df = pd.read_csv(patch_file)
    level_df = df[df["level"] == level]
    if column not in level_df:
        raise UnknownColumnError(
            "Column {} does not exists in {}!!!".format(column, patch_file)
        )
    for _, row in level_df.iterrows():
        yield row["x"], row["y"], row[column]


class PathaiaHandler(object):
    """
    A class to handle simple patch datasets.

    It usually computes the input of tf datasets proposed in pathaia.data.
    """

    def __init__(self, project_folder, slide_folder):
        """
        Create the patch handler.

        Args:
            project_folder (str): absolute path to a pathaia project.
            slide_folder (str): absolute path to a slide folder.

        """
        self.slide_folder = slide_folder
        self.project_folder = project_folder

    def list_patches(self, level, dim, label):
        """
        Create labeled patch dataset.

        Args:
            level (int): pyramid level to extract patches in csv.
            dim (tuple of int): dimensions of the patches in pixels.
            label (str): column header in csv to use as a category.
        Returns:
            tuple: (list of ndarray images, list of labels of any type)

        """
        patch_list = []
        labels = []
        for name, patch_folder in get_patch_folders_in_project(self.project_folder):
            try:
                slide_path = get_slide_file(self.slide_folder, name)
                patch_file = get_patch_csv_from_patch_folder(patch_folder)
                # read patch file and get the right level
                for x, y, lab in handle_labeled_patches(patch_file, level, label):
                    patch_list.append(
                        {"slide": slide_path, "x": x, "y": y,
                         "level": level, "dimensions": dim}
                    )
                    labels.append(lab)
            except (PatchesNotFoundError, UnknownColumnError, SlideNotFoundError) as e:
                warnings.warn(str(e))
        return patch_list, labels