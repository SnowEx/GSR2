import Metashape


class Accuracy:
    CAMERA_LOCATION = Metashape.Vector([0.5, 0.5, 0.5])  # in meter
    CAMERA_ROTATION = Metashape.Vector([5, 5, 5])  # in degrees
    MARKERS = Metashape.Vector([0.01, 0.01, 0.01])  # in meter
    MARKER_PROJECTION = 1.0  # in pixel
    TIEPOINT_ACCURACY = 1.0  # in pixel
    SCALEBAR = 0.01  # in meter
