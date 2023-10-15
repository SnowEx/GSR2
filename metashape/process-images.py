# Example command line execution:
#
# * Mac OS
# ./MetashapePro -r process-images.py \
#                --base-path /project/root/path \
#                --project-name test
#
# * Windows
# .\Metashape.exe -r process-images.py \
#                 --base-path C:\project\root\path \
#                 --project-name test
#
# * Linux (headless)
# metashape.sh -platform offscreen \
#              -r process-images.py \
#              --base-path /project/root/path \
#              --project-name test
#

import argparse
import glob
import pathlib
import sys
from string import Template

import Metashape


class Accuracy:
    CAMERA_LOCATION = Metashape.Vector([0.5, 0.5, 0.5])  # in meter
    CAMERA_ROTATION = Metashape.Vector([5, 5, 5])  # in degrees
    MARKERS = Metashape.Vector([0.05, 0.05, 0.05])  # in meter
    MARKER_PROJECTION = 1.0  # in pixel
    SCALEBAR = 0.03  # in meter


class Filter:
    RECONSTRUCTION_UNCERTAINTY = 10.0  # no units
    REPROJECTION_ERROR = 0.3  # in pixels
    PROJECTION_ACCURACY = 5.0  # in pixels
    DEPTH_MAP_MINIMUM = 1  # Count number
    DENSE_CLOUD_POINT_SPACING = 0.00025  # in meters


class ImageMatching:
    HIGHEST = 0
    HIGH = 1
    MEDIUM = 2


class DepthMapQuality:
    ULTRA = 1
    HIGH = 2
    MEDIUM = 4


class ImageProcessor:
    PROJECT_TYPE = '.psx'
    EXPORT_LAZ = '.laz'

    IMAGE_CHUNK_LABEL = 'Snowpit'
    IMAGE_FOLDER_GLOB = '**/*'
    SOURCE_IMAGE_TYPE = '.jpg'

    MARKER_STRING = Template('target ${id}')

    LOCAL_CRS = Metashape.CoordinateSystem(
        'LOCAL_CS['
        '"Local Coordinates (m)",'
        'LOCAL_DATUM["Local Datum",0],'
        'UNIT["metre",1,AUTHORITY["EPSG","9001"]]'
        ']'
    )

    # From https://www.agisoft.com/forum/index.php?topic=12114.0
    ALL_VISIBLE_POINTS = list(range(128))

    # Use a high keypoint limit and filter through the gradual selection in
    # a second step (See :py:meth:`.filter_sparse_cloud`)
    KEYPOINT_LIMIT = 100_000
    TIEPOINT_LIMIT = 10_000

    def __init__(self, options: argparse.Namespace):
        self._project_name = options.project_name
        # Location for Metashape outputs
        self._project_path = pathlib.Path(options.output_path)

        self.setup_application()

        self._project = self.open_or_create_new_project(
            options.image_folder, options.image_type
        )

    @property
    def project_name(self):
        return self._project_name + self.PROJECT_TYPE

    @property
    def project_path(self):
        """
        Base path where project will be saved or loaded from.
        """
        return self._project_path.joinpath(self.project_name)

    def save_and_exit(self):
        """
        Saves the project and exits the execution with a negative return status
        """
        self._project.save()
        sys.exit(-1)

    @staticmethod
    def setup_application():
        """
        General app settings
        """
        app = Metashape.Application()

        number_of_gpus = len(Metashape.app.enumGPUDevices())
        # Use all available (binary mask)
        mask = int(str('1' * number_of_gpus).rjust(8, '0'), 2)
        app.gpu_mask = mask
        app.cpu_enable = False

    def open_or_create_new_project(self, image_folder: str, image_type: str) \
            -> Metashape.Document:
        """
        Create or open the project under given project path from script
        arguments.

        Executes the following when a new project is created:

        * Set the camera settings (See :py:meth:`.setup_camera`)
        * Add the images (See :py:meth:`.load_images`)
        * Detect markers in images (See :py:meth:`.detect_and_scale_markers`)

        :param image_folder: Image folder from script arguments
        :param image_type: Type of images to load
        :return: The opened Metashape project
        """
        project = Metashape.Document()
        if self.project_path.exists():
            print(f"** Opening: {self.project_path.as_posix()}")
            project.open(self.project_path.as_posix())
        else:
            print(f"** Creating: {self.project_path.as_posix()}")
            project.chunk = project.addChunk()
            project.chunk.label = self.IMAGE_CHUNK_LABEL
            project.save(path=self.project_path.as_posix())

            self._project = project
            self.load_images(image_folder, image_type)
            self.detect_and_scale_markers()
            self.setup_camera()
            project.save()

        return project

    def setup_camera(self) -> None:
        """
        Set project chunk camera reference settings
        """
        self._project.chunk.crs = self.LOCAL_CRS

        self._project.chunk.camera_location_accuracy = Accuracy.CAMERA_LOCATION
        self._project.chunk.camera_rotation_accuracy = Accuracy.CAMERA_ROTATION
        self._project.chunk.marker_location_accuracy = Accuracy.MARKERS
        self._project.chunk.scalebar_accuracy = Accuracy.SCALEBAR

    def load_images(self, folder: str, image_type: str) -> None:
        """
        Find all images recursively under the given folder.
        Only images with the specified file ending will be found.
        Default image file ending is defined with
        :py:const:`ImageProcessor.SOURCE_IMAGE_TYPE.`

        :param folder: Absolute path of the image folder location
        :param image_type: Image types to look for in the folder
        """
        image_folder = pathlib.Path(folder)

        # Not using Path.rglob since we the result as a list of strings and
        # using Path will return a list of Path objects.
        images = sorted(
            glob.glob(
                image_folder.as_posix() + self.IMAGE_FOLDER_GLOB + image_type
            )
        )

        if len(images) == 0:
            print(
                f' ** ERROR ** No {image_type} files found in directory:'
            )
            print('    ' + image_folder.as_posix())
            self.save_and_exit()

        self._project.chunk.addPhotos(images)

    @staticmethod
    def set_xyz_origin(markers: list) -> None:
        """
        Set detected marker #3 as the XYZ origin
        20231015 - Currently unused. Trial runs showed no improvement for model
                   orientation.

        :param markers: list - All detected markers
        """
        for marker in markers:
            if marker.label == ImageProcessor.MARKER_STRING.substitute(id=3):
                markers[2].reference.location = Metashape.Vector([0, 0, 0])

    def add_scalebars(self, markers: list, distance: float) -> None:
        """
        Add scale bar to marker pairs that were successfully detected.

        :param markers: list - All detected markers
        :param distance: float - Distance between the two markers
        """
        # Transform to check for detection
        marker_dict = {marker.label: marker for marker in markers}

        for marker_start in range(1, 6, 2):
            marker_1 = self.MARKER_STRING.substitute(id=marker_start)
            marker_2 = self.MARKER_STRING.substitute(id=marker_start + 1)

            if marker_1 in marker_dict.keys() and \
                    marker_2 in marker_dict.keys():
                scale_bar = self._project.chunk.addScalebar(
                    marker_dict[marker_1], marker_dict[marker_2]
                )
                scale_bar.reference.accuracy = Accuracy.SCALEBAR
                scale_bar.reference.distance = distance

    def detect_and_scale_markers(
        self, marker_count: int = 6, distance: float = 0.35,
    ) -> None:
        """
        Find the specified markers placed in scene and add scalebars.
        Each pair is expected to have a fixed distance between them.

        Will stop execution and save the project if not all markers were
        successfully found.

        :param marker_count: Number of expected markers in all images
        :param distance: Distance between markers in meter
        """
        self._project.chunk.detectMarkers()

        markers = self._project.chunk.markers

        # User feedback
        if len(markers) < marker_count:
            print('** WARNING ** Not all markers detected in scene')
        else:
            print(f"** Found {marker_count} markers")

        self.add_scalebars(markers, distance)

    def align_images(
        self, preselection_mode=Metashape.ReferencePreselectionMode
    ) -> None:
        """
        Align the images based on given reference preselection mode.

        :param preselection_mode: Option from the Metashape 'Align Photos'
                                  processing step
        """
        self._project.chunk.matchPhotos(
            downscale=ImageMatching.HIGHEST,
            generic_preselection=True,
            reference_preselection=False,
            reset_matches=True,
            reference_preselection_mode=preselection_mode,
            keypoint_limit=ImageProcessor.KEYPOINT_LIMIT,
            tiepoint_limit=ImageProcessor.TIEPOINT_LIMIT,
        )
        self._project.chunk.alignCameras()
        self._project.chunk.optimizeCameras()
        self._project.save()

    def remove_by_criteria(
        self, criteria: Metashape.PointCloud.Filter, threshold: float
    ) -> None:
        """
        Wrapper function to execute a Metashape point cloud filter.

        :param criteria: Child class from Metashape.PointCloud.Filter
        :param threshold: Threshold value for the given criteria
        """
        point_cloud_filter = Metashape.PointCloud.Filter()
        point_cloud_filter.init(self._project.chunk, criterion=criteria)
        point_cloud_filter.removePoints(threshold)

    def filter_sparse_cloud(self) -> None:
        """
        Executes a three-level filter over the sparse point cloud to improve
        camera location accuracy. The cameras are optimized after each filter.

        # TODO: describe each filter

        Inspired by: https://code.usgs.gov/pcmsc/AgisoftAlignmentErrorReduction
        """
        self.remove_by_criteria(
            Metashape.PointCloud.Filter.ReprojectionError,
            Filter.REPROJECTION_ERROR,
        )
        self._project.chunk.optimizeCameras()
        self.remove_by_criteria(
            Metashape.PointCloud.Filter.ReconstructionUncertainty,
            Filter.RECONSTRUCTION_UNCERTAINTY,
        )
        self._project.chunk.optimizeCameras()
        self.remove_by_criteria(
            Metashape.PointCloud.Filter.ProjectionAccuracy,
            Filter.PROJECTION_ACCURACY,
        )
        self._project.chunk.optimizeCameras()
        self._project.save()

    def build_dense_cloud(self, downscale: int) -> None:
        """
        Build the depth maps and dense point cloud.

        :param downscale: Depth Map quality
        """
        self._project.chunk.buildDepthMaps(
            downscale=downscale,
            filter_mode=Metashape.MildFiltering,
        )
        self._project.chunk.buildDenseCloud(
            point_confidence=True,
        )

        self._project.save()

    def filter_dense_cloud(self) -> None:
        """
        Two step filter:
          * Remove points that have only one depth map
          * Decimate the point cloud to four points per millimeter
        """
        # Remove points with one depth map
        point_cloud = self._project.chunk.dense_cloud
        point_cloud.setConfidenceFilter(0, Filter.DEPTH_MAP_MINIMUM)
        point_cloud.removePoints(self.ALL_VISIBLE_POINTS)
        point_cloud.resetFilters()

        # Decimate to four points per millimeter to speed up analysis
        task = Metashape.Tasks.FilterDenseCloud()
        task.point_spacing = Filter.DENSE_CLOUD_POINT_SPACING
        task.asset = point_cloud.key
        task.apply(self._project.chunk)

        self._project.save()

    def build_point_cloud(self, options: argparse.Namespace) -> None:
        """
        Wrapper function to run:
            * Camera optimization
            * Build sparse cloud
            * Build dense cloud

        :param options: Quality for dense cloud
                        (See :py:class:`DepthMapQuality`)
        """
        self.align_images(Metashape.ReferencePreselectionSequential)
        self.filter_sparse_cloud()
        self.build_dense_cloud(options.dense_cloud_quality)
        self.filter_dense_cloud()

    def export(self) -> None:
        """
        Export a project point cloud as .laz file
        """
        self._project.chunk.exportPoints(
            self._project_path.joinpath(
                self._project_name + self.EXPORT_LAZ
            ).as_posix(),
            format=Metashape.PointsFormatLAZ
        )


def argument_parser():
    parser = argparse.ArgumentParser(
        "Process snow pit ground surface imagery"
    )
    parser.add_argument(
        '-pn', '--project-name',
        required=True,
        help='Name of project.',
    )
    parser.add_argument(
        '-op', '--output-path',
        required=True,
        help='Output directory for the Metashape project.',
    )
    parser.add_argument(
        '-if', '--image-folder',
        required=True,
        help='Location of images relative to base-path.',
    )
    parser.add_argument(
        '-it', '--image-type',
        default=ImageProcessor.SOURCE_IMAGE_TYPE,
        help=f'Type of images - default to {ImageProcessor.SOURCE_IMAGE_TYPE}',
    )
    parser.add_argument(
        '-dcq', '--dense-cloud-quality',
        type=int,
        required=False,
        default=DepthMapQuality.ULTRA,
        choices=[
            DepthMapQuality.ULTRA,
            DepthMapQuality.HIGH,
            DepthMapQuality.MEDIUM,
        ],
        help="Integer for dense point cloud quality.\n"
             f" Highest -> {str(DepthMapQuality.ULTRA)} (Default)\n"
             f" High    -> {str(DepthMapQuality.HIGH)}\n"
             f" Medium  -> {str(DepthMapQuality.MEDIUM)}"
    )
    parser.add_argument(
        '-exp', '--export',
        action="store_true",
        help="Export the result in a .laz file"
    )

    return parser


if __name__ == '__main__':
    arguments = argument_parser().parse_args()
    image_processor = ImageProcessor(arguments)
    if arguments.export:
        image_processor.export()
    else:
        image_processor.build_point_cloud(arguments)
