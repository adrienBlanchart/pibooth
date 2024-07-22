# -*- coding: utf-8 -*-

import subprocess
from io import BytesIO
from PIL import Image
import pygame
from pibooth.pictures import sizing
try:
    import picamera2
except ImportError:
    picamera2 = None  # picamera2 is optional
from pibooth.camera.base import BaseCamera
from libcamera import Transform
import time
from pibooth.utils import LOGGER


def get_rpi2_camera_proxy(port=None):
    """Return camera proxy if a Raspberry Pi compatible camera is found
    else return None.

    :param port: look on given port number
    :type port: int
    """
    if not picamera2:
        LOGGER.warning("picamera2 is not installed")
        return None  # picamera2 is not installed
    try:
        picam2 = picamera2.Picamera2()
        picam2.start()
        metadata = picam2.capture_metadata()
        LOGGER.debug("Metadata: %s", metadata)
        LOGGER.debug("controls: %s", picam2.camera_controls)
        picam2.stop()
        if metadata and metadata["ExposureTime"]: # Check if camera is detected by checking if metadata is returned and if ExposureTime is present
            return picam2
    except OSError:
        pass
    LOGGER.warning("picamera2 is not installed or camera not found")
    return None


class RpiCamera2(BaseCamera):

    """Camera management
    """

    #if picamera2:
    #    IMAGE_EFFECTS = list(picamera2.Picamera2.IMAGE_EFFECTS.keys())

    def _specific_initialization(self):
        """Camera initialization.
        """
        self._cam.framerate = 15  # Slower is necessary for high-resolution
        self._cam.video_stabilization = True
        self._cam.vflip = False
        self._cam.hflip = self.capture_flip
        self._cam.resolution = self.resolution
        self._cam.iso = self.preview_iso
        self._cam.rotation = self.preview_rotation

    def _show_overlay(self):
        """Add an image as an overlay.
        """
        # Create an image padded to the required size (required by picamera2)
        size = (((self._rect.width + 31) // 32) * 32, ((self._rect.height + 15) // 16) * 16)

        image = self.build_overlay(size, self._overlay_text, self._overlay_alpha)
        self._overlay = self._cam.add_overlay(image.tobytes(), image.size, layer=3,
                                              window=tuple(self._rect), fullscreen=False)

    def _hide_overlay(self):
        """Remove any existing overlay.
        """
        if self._overlay:
            self._cam.remove_overlay(self._overlay)
            self._overlay = None
            self._overlay_text = None

    def _process_capture(self, capture_data):
        """Rework capture data.

        :param capture_data: binary data as stream
        :type capture_data: :py:class:`io.BytesIO`
        """
        # "Rewind" the stream to the beginning so we can read its content
        capture_data.seek(0)
        return Image.open(capture_data)

    def preview(self, rect, flip=True):
        """Display a preview on the given Rect (flip if necessary).
        """
        LOGGER.debug("Starting preview with rpi camera2")
        """ if self._cam.preview is not None:
            # Already running
            LOGGER.debug("Preview already started; return")
            return """

        # Define Rect() object for resizing preview captures to fit to the defined
        # preview rect keeping same aspect ratio than camera resolution.
        size = sizing.new_size_keep_aspect_ratio(self.resolution, (min(
            rect.width, 3280), min(rect.height, 2464)))
        self._rect = pygame.Rect(rect.centerx - size[0] // 2, rect.centery - size[1] // 2, size[0], size[1])

        self.preview_flip = flip
        """ if self._cam.hflip:
            if self.preview_flip:
                # Don't flip again, already done at init
                flip = False
            else:
                # Flip again because flipped once at init
                flip = True """
        #picam2.start_preview(Preview.QTGL, x=100, y=200, width=800, height=600, transform=Transform(hflip=1))

        #self._cam.start_preview(resolution=(self._rect.width, self._rect.height), hflip=flip,
        #                        fullscreen=False, window=tuple(self._rect))
        LOGGER.debug("Starting preview with rpi camera2")
        self._cam.start_preview(picamera2.Preview.QTGL, width=self._rect.width, height=self._rect.height, transform=Transform(hflip=1 if flip else 0, vflip=0))
        LOGGER.debug("Started rpi camera2")
        self._cam.start()


    def stop_preview(self):
        """Stop the preview.
        """
        self._rect = None
        self._cam.stop_preview()
        self._hide_overlay()

    def get_capture_image(self, effect=None):
        """Capture a new picture in a file.
        """
        try:
            LOGGER.debug("Taking capture with rpi camera")
            if self.capture_iso != self.preview_iso:
                self._cam.iso = self.capture_iso
            if self.capture_rotation != self.preview_rotation:
                self._cam.rotation = self.capture_rotation

            stream = BytesIO()
            self._cam.image_effect = effect
            self._cam.capture(stream, format='jpeg')

            if self.capture_iso != self.preview_iso:
                self._cam.iso = self.preview_iso
            if self.capture_rotation != self.preview_rotation:
                self._cam.rotation = self.preview_rotation

            self._captures.append(stream)
            return stream
        finally:
            self._cam.image_effect = 'none'

    def _specific_cleanup(self):
        """Close the camera driver, it's definitive.
        """
        self._cam.close()
