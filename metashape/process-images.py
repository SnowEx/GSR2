import argparse

from depth_map_quality import DepthMapQuality
from image_processor import ImageProcessor


def argument_parser():
    parser = argparse.ArgumentParser(
        "Process snow pit ground surface imagery with Agisoft Metashape.\n"
        "Example command line execution: \n"
        " * Mac OS\n"
        "   ./MetashapePro -r process-images.py __options__ \n"
        "\n"
        " * Windows\n"
        "   .\Metashape.exe -r process-images.py __options__ \n"
        "\n"
        " * Linux (headless)\n"
        "   metashape.sh -platform offscreen __options__ \n"
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
        '-mf', '--marker-file',
        required=True,
        help='Path to CSV file with marker distances',
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
        help="Export the PDF report and LAZ point cloud"
    )
    parser.add_argument(
        '--export-only',
        action="store_true",
        help="Only run the export for the PDF report and LAZ point cloud. "
             "NO processing will be performed."
    )

    return parser


if __name__ == '__main__':
    arguments = argument_parser().parse_args()
    image_processor = ImageProcessor(arguments)

    if arguments.export_only:
        image_processor.export()
    else:
        image_processor.build_point_cloud(arguments)
        if arguments.export:
            image_processor.export()
