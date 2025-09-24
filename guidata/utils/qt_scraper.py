# Copyright (c) DataLab Platform Developers, BSD 3-Clause license, see LICENSE file.

"""Generic Qt scraper for Sphinx-Gallery.

This module provides a scraper that can capture any Qt top-level widgets and convert
them to images for use in Sphinx-Gallery documentation. The scraper automatically
detects all visible top-level Qt widgets created during example execution.

The scraper works by:
1. Detecting all visible Qt top-level widgets after code block execution
2. Capturing screenshots of these widgets
3. Converting the screenshots to appropriate formats for Sphinx-Gallery
4. Saving the images in the expected location for gallery generation

Usage:
    This module is automatically used by Sphinx-Gallery when configured in conf.py:

    sphinx_gallery_conf = {
        'image_scrapers': [guidata.utils.qt_scraper.qt_scraper],
        # other configuration...
    }

    Or use the helper function:

    from guidata.utils.qt_scraper import get_qt_scraper_config
    sphinx_gallery_conf = get_qt_scraper_config()
"""

from __future__ import annotations

import logging
import os
import time
from pathlib import Path
from typing import Any

try:
    from qtpy.QtCore import Qt
    from qtpy.QtWidgets import QApplication, QDialog, QMainWindow, QWidget

    QT_AVAILABLE = True
except ImportError:
    QT_AVAILABLE = False

# Set up logging
logger = logging.getLogger(__name__)


def _find_qt_top_widgets() -> list[QWidget]:
    """Find all visible Qt top-level widgets.

    Returns:
        List of visible Qt top-level widgets.
    """
    if not QT_AVAILABLE:
        return []

    try:
        app = QApplication.instance()
        if app is None:
            return []

        widgets = []
        for widget in app.topLevelWidgets():
            # Skip if widget is not visible
            if not widget.isVisible():
                continue

            # Skip widgets that are hidden or minimized
            if widget.isMinimized() or widget.isHidden():
                continue

            # Include main windows, dialogs, and other top-level widgets
            # Exclude tool tips, pop-ups, and other transient widgets
            if isinstance(widget, (QMainWindow, QDialog)) or (
                isinstance(widget, QWidget)
                and widget.windowFlags() & Qt.Window
                and not widget.windowFlags() & Qt.Tool
                and not widget.windowFlags() & Qt.Popup
            ):
                widgets.append(widget)

        return widgets
    except (AttributeError, RuntimeError) as exc:
        logger.warning("Failed to find Qt widgets: %s", exc)
        return []


def _capture_widget(widget: QWidget, output_path: str | Path) -> bool:
    """Capture a screenshot of a Qt widget and save it.

    Args:
        widget: The Qt widget to capture.
        output_path: Path where to save the PNG screenshot.

    Returns:
        True if capture was successful, False otherwise.
    """
    if not hasattr(widget, "grab"):
        logger.warning("Widget does not support grab() method")
        return False

    try:
        # Make sure the widget is visible and rendered
        widget.show()
        widget.raise_()
        widget.activateWindow()

        # Process events to ensure the widget is fully rendered
        app = QApplication.instance()
        if app:
            app.processEvents()

        # Small delay to ensure rendering is complete
        time.sleep(0.1)

        # Capture the screenshot
        pixmap = widget.grab()
        if not pixmap.isNull():
            success = pixmap.save(str(output_path), "PNG")
            if success:
                logger.debug("Successfully captured widget to %s", output_path)
            else:
                logger.warning("Failed to save screenshot to %s", output_path)
            return success

        logger.warning("Captured pixmap is null")
        return False

    except Exception as exc:
        logger.error("Failed to capture Qt widget: %s", exc)
        return False


def _ensure_qapplication() -> QApplication | None:
    """Ensure a QApplication instance exists.

    Returns:
        QApplication instance or None if creation failed.
    """
    if not QT_AVAILABLE:
        logger.warning("Qt not available for scraping")
        return None

    try:
        app = QApplication.instance()
        if app is None:
            # Create minimal QApplication for gallery building
            app = QApplication([])
            logger.debug("Created QApplication for Qt scraper")
        return app
    except Exception as exc:
        logger.error("Could not initialize QApplication: %s", exc)
        return None


def _get_image_directory(gallery_conf: dict[str, Any]) -> Path | None:
    """Get the image directory for saving screenshots.

    Args:
        gallery_conf: Sphinx-Gallery configuration.

    Returns:
        Path to image directory or None if cannot be determined.
    """
    if not gallery_conf or "src_dir" not in gallery_conf:
        logger.warning("Invalid gallery configuration")
        return None

    src_dir = Path(gallery_conf["src_dir"])
    gallery_dirs = gallery_conf.get("gallery_dirs", ["auto_examples"])

    # Handle both string and list cases for gallery_dirs
    if isinstance(gallery_dirs, list):
        gallery_dir = gallery_dirs[0] if gallery_dirs else "auto_examples"
    else:
        gallery_dir = gallery_dirs

    img_dir = src_dir / gallery_dir / "images"
    img_dir.mkdir(parents=True, exist_ok=True)
    return img_dir


def _generate_rst_block(
    image_name: str, gallery_conf: dict[str, Any], widget_index: int
) -> str:
    """Generate RST code block for an image.

    Args:
        image_name: Name of the image file.
        gallery_conf: Sphinx-Gallery configuration.
        widget_index: Index of the widget (for alt text).

    Returns:
        RST code block.
    """
    gallery_dirs = gallery_conf.get("gallery_dirs", ["auto_examples"])
    if isinstance(gallery_dirs, list):
        rst_gallery_dir = gallery_dirs[0] if gallery_dirs else "auto_examples"
    else:
        rst_gallery_dir = gallery_dirs

    return f"""
.. image:: /{rst_gallery_dir}/images/{image_name}
   :alt: Qt widget {widget_index + 1}
   :class: sphx-glr-single-img
"""


def qt_scraper(
    block: str, block_vars: dict[str, Any], gallery_conf: dict[str, Any], **kwargs: Any
) -> str:
    """Scraper for Qt widgets in Sphinx-Gallery.

    This function is called by Sphinx-Gallery after executing each code block
    to capture any Qt top-level widgets that were created.

    Args:
        block: The code block that was executed (unused).
        block_vars: Variables from the executed code block (unused).
        gallery_conf: Sphinx-Gallery configuration.
        **kwargs: Additional arguments (unused).

    Returns:
        RST code to include the captured images.
    """
    if not QT_AVAILABLE:
        logger.warning("Qt not available for scraping")
        return ""

    # Set environment variable to indicate we're building gallery
    os.environ["SPHINX_GALLERY_BUILDING"] = "1"

    # Ensure QApplication exists
    app = _ensure_qapplication()
    if app is None:
        return ""

    # Find all Qt top-level widgets
    widgets = _find_qt_top_widgets()
    logger.info("Found %d Qt top-level widgets", len(widgets))

    if not widgets:
        return ""

    # Get image directory
    img_dir = _get_image_directory(gallery_conf)
    if img_dir is None:
        logger.error("Cannot determine image directory")
        return ""

    timestamp = int(time.time() * 1000)  # milliseconds for uniqueness

    # Capture each widget
    rst_blocks = []
    for i, widget in enumerate(widgets):
        try:
            # Generate unique image path
            image_name = f"sphx_glr_qt_{timestamp}_{i:03d}.png"
            image_path = img_dir / image_name

            logger.debug(
                "Attempting to capture widget %d/%d to %s",
                i + 1,
                len(widgets),
                image_path,
            )

            # Capture the widget
            success = _capture_widget(widget, image_path)

            if success:
                rst_block = _generate_rst_block(image_name, gallery_conf, i)
                rst_blocks.append(rst_block)
                logger.debug("Successfully captured widget %d", i + 1)
            else:
                logger.warning("Failed to capture widget %d", i + 1)

            # Close the widget to prevent accumulation (if it has a close method)
            if hasattr(widget, "close") and hasattr(widget, "deleteLater"):
                try:
                    widget.close()
                    # Don't call deleteLater() immediately as it may interfere
                    # with other widgets or the application
                except Exception as exc:
                    logger.warning("Failed to close widget %d: %s", i + 1, exc)

        except Exception as exc:
            logger.error("Failed to process Qt widget %d: %s", i, exc)
            continue

    return "".join(rst_blocks)


def _get_qt_version() -> str | None:
    """Get Qt version if available.

    Returns:
        Qt version string or None if not available.
    """
    if not QT_AVAILABLE:
        return None

    try:
        from qtpy.QtCore import QT_VERSION_STR

        return QT_VERSION_STR
    except ImportError:
        return None


def setup_qt_scraper(app: Any, config: Any) -> None:  # noqa: ARG001
    """Setup function to register the Qt scraper with Sphinx.

    Args:
        app: Sphinx application instance (unused).
        config: Sphinx configuration object.
    """
    if hasattr(config, "sphinx_gallery_conf"):
        scrapers = config.sphinx_gallery_conf.get("image_scrapers", [])
        if qt_scraper not in scrapers:
            scrapers.append(qt_scraper)
            config.sphinx_gallery_conf["image_scrapers"] = scrapers


def get_qt_scraper() -> Any:
    """Return the Qt scraper function for use in Sphinx-Gallery configuration.

    Returns:
        The qt_scraper function.
    """
    return qt_scraper


def get_qt_scraper_config() -> dict[str, Any]:
    """Return a configuration dict for Qt scraper.

    Returns:
        Configuration dictionary for Sphinx-Gallery.
    """
    config = {
        "image_scrapers": ["guidata.utils.qt_scraper.qt_scraper"],
        "examples_dirs": "examples",  # Path to example scripts
        "gallery_dirs": "auto_examples",  # Output directory for gallery
        "filename_pattern": "plot_",  # Pattern for example files
        "reset_modules": (),  # Can be customized by the user
        "remove_config_comments": False,
        "expected_failing_examples": [],
        "capture_repr": ("_repr_html_", "__repr__"),
        "matplotlib_animations": False,
        "download_all_examples": False,
        "show_memory": False,
        "plot_gallery": True,  # Enable gallery plotting
        "run_stale_examples": False,  # Force run all examples
    }

    # Add Qt version info if available
    version = _get_qt_version()
    if version:
        config["qt_version"] = version

    return config
