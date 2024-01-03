import argparse
import csv
import glob
import pathlib
import sys
from string import Template

import Metashape

from accuracy import Accuracy
from filter import Filter
from image_matching import ImageMatching


class ImageProcessor:
    PROJECT_TYPE = '.psx'
    EXPORT_LAZ = '.laz'
    EXPORT_PDF = '.pdf'

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
    KEYPOINT_LIMIT = 50_000
    TIEPOINT_LIMIT = 10_000

    # Percentage threshold for sparse point cloud filter
    FIFTY_PERCENT = 0.5

    # Distance in meters where images were taken.
    # Needs to be a string when set.
    CAPTURE_DISTANCE = '1'

    def __init__(self, options: argparse.Namespace):
        self._project_name = options.project_name
        # Location for Metashape outputs
        self._project_path = pathlib.Path(options.output_path)

        self.setup_application()

        self._project = self.open_or_create_new_project(
            options.image_folder, options.image_type
        )

    @property
    def project_path(self):
        """
        Base path where project will be saved or loaded from.
        """
        return self._project_path.joinpath(
            self._project_name + self.PROJECT_TYPE
        )

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

    def open_or_create_new_project(
        self, image_folder: str, image_type: str,
    ) -> Metashape.Document:
        """
        Create or open the project under given project path from script
        arguments.

        Executes the following when a new project is created:

        * Set the camera settings (See :py:meth:`.setup_camera`)
        * Add the images (See :py:meth:`.load_images`)
        * Detect markers in images

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
            self.setup_camera()
            self._project.chunk.detectMarkers(tolerance=25)
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
        self._project.chunk.marker_projection_accuracy = \
            Accuracy.MARKER_PROJECTION
        self._project.chunk.tiepoint_accuracy = Accuracy.TIEPOINT_ACCURACY
        self._project.chunk.meta['subject_distance'] = self.CAPTURE_DISTANCE

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

    def add_scalebars(self, marker_file: str) -> None:
        """
        Add scale bar to marker pairs that were successfully detected.
        Each pair will create a scalebar with distance given by the
        marker file.

        Expected format in CSV file is:
            marker_ID_from, marker_ID_to, marker_distance

        Example: 1,2,0.33

        :param marker_file: Path to CSV marker file
        """
        # Read marker metadata from user given csv
        with open(marker_file, 'r', newline='') as csvfile:
            marker_list = list(csv.reader(csvfile, delimiter=','))

        # Transform to check for detection
        marker_dict = {
            marker.label: marker for marker in self._project.chunk.markers
        }

        for marker_pair in marker_list:
            marker_1 = self.MARKER_STRING.substitute(id=marker_pair[0])
            marker_2 = self.MARKER_STRING.substitute(id=marker_pair[1])

            if marker_1 in marker_dict.keys() and \
                    marker_2 in marker_dict.keys():
                scale_bar = self._project.chunk.addScalebar(
                    marker_dict[marker_1], marker_dict[marker_2]
                )
                scale_bar.reference.accuracy = Accuracy.SCALEBAR
                scale_bar.reference.distance = float(marker_pair[2])
            else:
                print('** WARNING ** Marker pair')
                print(f'   {marker_1} to {marker_2}')
                print('    NOT found in images')

        self._project.chunk.updateTransform()
        self._project.save()

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
            reference_preselection=True,
            reference_preselection_mode=preselection_mode,
            keypoint_limit=ImageProcessor.KEYPOINT_LIMIT,
            tiepoint_limit=ImageProcessor.TIEPOINT_LIMIT,
            reset_matches=True,
        )
        self._project.chunk.alignCameras()
        self._project.save()

    def count_sparse_points(
        self, filtered: bool = True
    ) -> int:
        """
        Count points in the sparse point cloud.

        :param filtered: Boolean - Whether to only count selected points
        :return: Integer - Number of points
        """
        sparse_points = self._project.chunk.tie_points.points
        return len(
            [
                True for point in sparse_points
                if point.valid is True and point.selected is filtered]
        )

    def threshold_for_percent(
        self,
        point_filter: Metashape.TiePoints.Filter,
        threshold: float,
        step_size: float,
        max_percent: float,
    ) -> float:
        """
        Calculate percentage of points selected via the filter and adjust the
        filter threshold value to stay below given maximum percent. This method
        incrementally increases the threshold value by 0.25.

        :param point_filter: Instance of Metashape.TiePoints.Filter
        :param threshold: Threshold value for the given filter
        :param step_size: Value to increase the threshold when max_removed
                          should be achieved.
        :param max_percent: int - Percent value to stay below

        :return: Filter threshold value to match needed maximum percentage
        """
        sparse_points = self.count_sparse_points(False)

        point_filter.selectPoints(threshold)
        selected_points = self.count_sparse_points()
        percent_selected = selected_points / sparse_points

        while percent_selected > max_percent:
            threshold += step_size
            point_filter.selectPoints(threshold)

            selected_points = self.count_sparse_points()
            percent_selected = selected_points / sparse_points

        return threshold

    def remove_by_criteria(
        self, criteria: Metashape.TiePoints.Filter,
        threshold: float,
        step_size: float = 0,
        max_removed: float = 0,
    ) -> None:
        """
        Wrapper function to execute a Metashape point cloud filter.

        :param criteria: Child class from Metashape.TiePoints.Filter
        :param threshold: Threshold value for the given criteria
        :param step_size: Value to increase the threshold when max_removed
                          should be achieved.
        :param max_removed: Threshold for maximum percent of points removed
                            with this filter. Default: 0 (no maximum)
        """
        point_cloud_filter = Metashape.TiePoints.Filter()
        point_cloud_filter.init(self._project.chunk, criterion=criteria)

        if max_removed > 0:
            threshold = self.threshold_for_percent(
                point_cloud_filter, threshold, step_size, max_removed
            )

        point_cloud_filter.removePoints(threshold)

    def filter_sparse_cloud(self) -> None:
        """
        Executes a three-level filter over the sparse point cloud to improve
        camera location accuracy. The cameras are optimized after each filter.

        Each filter is described in Over et al. (2021):
            https://doi.org/10.3133/ofr20211039
            https://code.usgs.gov/pcmsc/AgisoftAlignmentErrorReduction
        """
        self.remove_by_criteria(
            Metashape.TiePoints.Filter.ReconstructionUncertainty,
            Filter.RECONSTRUCTION_UNCERTAINTY,
            max_removed=self.FIFTY_PERCENT,
            step_size=Filter.RECONSTRUCTION_UNCERTAINTY_STEP,
        )
        self._project.chunk.optimizeCameras()
        self.remove_by_criteria(
            Metashape.TiePoints.Filter.ProjectionAccuracy,
            Filter.PROJECTION_ACCURACY,
        )
        self._project.chunk.optimizeCameras()
        self.remove_by_criteria(
            Metashape.TiePoints.Filter.ReprojectionError,
            Filter.REPROJECTION_ERROR,
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
        self._project.chunk.buildPointCloud(
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
        point_cloud = self._project.chunk.point_cloud
        point_cloud.setConfidenceFilter(0, Filter.DEPTH_MAP_MINIMUM)
        point_cloud.removePoints(self.ALL_VISIBLE_POINTS)
        point_cloud.resetFilters()

        # Decimate to four points per millimeter to speed up analysis
        task = Metashape.Tasks.FilterPointCloud()
        task.point_spacing = Filter.DENSE_CLOUD_POINT_SPACING
        task.point_cloud = point_cloud.key
        task.apply(self._project.chunk)

        self._project.save()

    def build_point_cloud(self, options: argparse.Namespace) -> None:
        """
        Wrapper function to run:
            * Image alignment
            * Camera optimization
            * Adding scalebars
            * Build sparse cloud
            * Build dense cloud

        :param options: Quality for dense cloud
                        (See :py:class:`DepthMapQuality`)
        """
        self.align_images(Metashape.ReferencePreselectionSequential)
        self.filter_sparse_cloud()
        self.add_scalebars(options.marker_file)
        self.build_dense_cloud(options.dense_cloud_quality)
        self.filter_dense_cloud()

    def export(self) -> None:
        """
        Export a project point cloud as .laz file along with the processing
        report.
        """
        self._project.chunk.exportPointCloud(
            self._project_path.joinpath(
                self._project_name + self.EXPORT_LAZ
            ).as_posix(),
            format=Metashape.PointCloudFormatLAZ
        )
        self._project.chunk.exportReport(
            self._project_path.joinpath(
                self._project_name + self.EXPORT_PDF
            ).as_posix(),
            title=self._project_name,
            page_numbers=True,
        )
