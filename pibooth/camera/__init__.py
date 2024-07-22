# -*- coding: utf-8 -*-

from pibooth.utils import LOGGER
from pibooth.camera.rpi import RpiCamera, get_rpi_camera_proxy
from pibooth.camera.rpi2 import RpiCamera2, get_rpi2_camera_proxy
from pibooth.camera.gphoto import GpCamera, get_gp_camera_proxy
from pibooth.camera.opencv import CvCamera, get_cv_camera_proxy
from pibooth.camera.libcamera import LibCamera, get_libcamera_camera_proxy
from pibooth.camera.hybrid import HybridLibCamera, HybridRpiCamera, HybridCvCamera


def close_proxy(rpi_cam_proxy, gp_cam_proxy, cv_cam_proxy, lib_cam_proxy, is_rpi2_proxy):
    """Close proxy drivers.
    """
    if rpi_cam_proxy:
        if is_rpi2_proxy:
            RpiCamera2(rpi_cam_proxy).quit()
        else:
            RpiCamera(rpi_cam_proxy).quit()
    if gp_cam_proxy:
        GpCamera(gp_cam_proxy).quit()
    if cv_cam_proxy:
        CvCamera(cv_cam_proxy).quit()
    if lib_cam_proxy:
        LibCamera(lib_cam_proxy).quit()


def find_camera():
    """Initialize the camera depending of the connected one. The priority order
    is chosen in order to have best rendering during preview and to take captures.
    The gPhoto2 camera is first (drivers most restrictive) to avoid connection
    concurence in case of DSLR compatible with OpenCV.
    """
    rpi_cam_proxy_1 = get_rpi_camera_proxy()
    rpi2_cam_proxy_2 = get_rpi2_camera_proxy()
    rpi_cam_proxy = rpi2_cam_proxy_2 if rpi2_cam_proxy_2 else rpi_cam_proxy_1
    is_rpi2_proxy = True if rpi2_cam_proxy_2 else False

    #If both RpiCamera and RpiCamera2 are detected, close the one that is not used
    if rpi_cam_proxy:
        close_proxy(rpi_cam_proxy, None, None, None, not is_rpi2_proxy)

    gp_cam_proxy = get_gp_camera_proxy()
    cv_cam_proxy = get_cv_camera_proxy()
    lib_cam_proxy = get_libcamera_camera_proxy()

    if lib_cam_proxy and gp_cam_proxy:
        LOGGER.info("Configuring hybrid camera (Libcamera + gPhoto2) ...")
        close_proxy(rpi_cam_proxy, None, cv_cam_proxy, None, is_rpi2_proxy)
        return HybridLibCamera(lib_cam_proxy, gp_cam_proxy)
    if rpi_cam_proxy and gp_cam_proxy:
        LOGGER.info("Configuring hybrid camera (Picamera + gPhoto2) ...")
        close_proxy(None, None, cv_cam_proxy, lib_cam_proxy, is_rpi2_proxy)
        return HybridRpiCamera(rpi_cam_proxy, gp_cam_proxy)
    if cv_cam_proxy and gp_cam_proxy:
        LOGGER.info("Configuring hybrid camera (OpenCV + gPhoto2) ...")
        close_proxy(rpi_cam_proxy, None, None, lib_cam_proxy, is_rpi2_proxy)
        return HybridCvCamera(cv_cam_proxy, gp_cam_proxy)
    if gp_cam_proxy:
        LOGGER.info("Configuring gPhoto2 camera ...")
        close_proxy(rpi_cam_proxy, None, cv_cam_proxy, lib_cam_proxy, is_rpi2_proxy)
        return GpCamera(gp_cam_proxy)
    if rpi_cam_proxy:
        LOGGER.info("Configuring Picamera camera ...")
        close_proxy(None, gp_cam_proxy, cv_cam_proxy, lib_cam_proxy, is_rpi2_proxy)
        if is_rpi2_proxy:
            return RpiCamera2(rpi_cam_proxy)
        return RpiCamera(rpi_cam_proxy)
    if lib_cam_proxy:
        LOGGER.info("Configuring Libcamera camera ...")
        close_proxy(rpi_cam_proxy, gp_cam_proxy, cv_cam_proxy, None, is_rpi2_proxy)
        return LibCamera(lib_cam_proxy)
    if cv_cam_proxy:
        LOGGER.info("Configuring OpenCV camera ...")
        close_proxy(rpi_cam_proxy, gp_cam_proxy, None, lib_cam_proxy, is_rpi2_proxy)
        return CvCamera(cv_cam_proxy)

    raise EnvironmentError("Neither Raspberry Pi nor GPhoto2 nor Libcamera nor OpenCV camera detected")
