# -*- coding: utf-8 -*-

import time
import pygame
import pibooth
from pibooth import camera
from pibooth.utils import LOGGER
from pibooth import evts
import traceback


class CameraPlugin(object):

    """Plugin to manage the camera captures.
    """

    name = 'pibooth-core:camera'

    def __init__(self, plugin_manager):
        self._pm = plugin_manager
        self.count = 0

    @pibooth.hookimpl(hookwrapper=True)
    def pibooth_setup_camera(self, cfg):
        outcome = yield  # all corresponding hookimpls are invoked here
        cam = outcome.get_result()

        if not cam:
            LOGGER.debug("Fallback to pibooth default camera management system")
            cam = camera.find_camera()

        cam.initialize(cfg.gettuple('CAMERA', 'iso', (int, str), 2),
                       cfg.gettyped('CAMERA', 'resolution'),
                       cfg.gettuple('CAMERA', 'rotation', int, 2),
                       cfg.getboolean('CAMERA', 'flip'),
                       cfg.getboolean('CAMERA', 'delete_internal_memory'))
        outcome.force_result(cam)

    @pibooth.hookimpl
    def pibooth_cleanup(self, app):
        app.camera.quit()

    @pibooth.hookimpl
    def state_failsafe_enter(self, app):
        """Reset variables set in this plugin.
        """
        app.capture_date = None
        app.capture_nbr = None
        app.camera.drop_captures()  # Flush previous captures

    @pibooth.hookimpl
    def state_wait_enter(self, app):
        app.capture_date = None
        if len(app.capture_choices) > 1:
            app.capture_nbr = None
        else:
            app.capture_nbr = app.capture_choices[0]

    @pibooth.hookimpl
    def state_preview_enter(self, cfg, app, win):
        LOGGER.info("Show preview before next capture")
        if not app.capture_date:
            app.capture_date = time.strftime("%Y-%m-%d-%H-%M-%S")
        app.camera.preview(win)

    @pibooth.hookimpl
    def state_capture_enter(self, cfg, app):
        effects = cfg.gettyped('PICTURE', 'captures_effects')
        if not app.capture_date:
            app.capture_date = time.strftime("%Y-%m-%d-%H-%M-%S")		 
        if not isinstance(effects, (list, tuple)):
            # Same effect for all captures
            effect = effects
        elif len(effects) >= app.capture_nbr:
            # Take the effect corresponding to the current capture
            effect = effects[self.capture_count]
        else:
            # Not possible
            raise ValueError(f"Not enough effects defined for {app.capture_nbr} captures {effects}")
        LOGGER.info("Take a capture")								
        app.camera.capture(effect)

    @pibooth.hookimpl
    def state_preview_do(self, cfg, app):
        stack = traceback.format_stack()
        # Loggez la pile d'appels
        LOGGER.info("Call stack:\n%s", ''.join(stack))
        pygame.event.pump()  # Before blocking actions
        LOGGER.info("Show preview before next capture")
        if cfg.getboolean('WINDOW', 'preview_countdown'):
            app.camera.preview_countdown(cfg.getint('WINDOW', 'preview_delay'))
        else:
            app.camera.preview_wait(cfg.getint('WINDOW', 'preview_delay'))
    
    @pibooth.hookimpl
    def state_preview_validate(self):
        return 'capture'


    @pibooth.hookimpl
    def state_capture_do(self, events):
        LOGGER.info("Capture done")
        event = evts.find_event(events, evts.EVT_PIBOOTH_CAM_CAPTURE)
        if event:
            self.count += 1

    @pibooth.hookimpl
    def state_processing_enter(self, app):
        self.count = 0
        LOGGER.info("Stopping preview")
        app.camera.stop_preview()