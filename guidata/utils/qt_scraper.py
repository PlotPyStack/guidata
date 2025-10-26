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

Configuration Options:
    The scraper supports several configuration options for customizing behavior:

    - thumbnail_widget: Which widget to use as thumbnail
        * "first": Use the first successfully captured widget
        * "last": Use the last successfully captured widget (default)
        * None: Use default sphinx-gallery thumbnail behavior

    - hide_toolbars: Hide all toolbars when capturing widgets (default: False)
        * True: Temporarily hide QToolBar widgets during capture
        * False: Keep toolbars visible in screenshots

    - capture_inside_layout: Capture only widget content, excluding decorations
        * True: Capture content area only (no title bars, window borders)
        * False: Capture entire widget including window decorations (default)

Usage:
    Basic usage in conf.py:

    sphinx_gallery_conf = {
        'image_scrapers': ['guidata.utils.qt_scraper.qt_scraper'],
        # other configuration...
    }

    Advanced configuration with custom options:

    from guidata.utils.qt_scraper import set_qt_scraper_config

    # Configure before running examples
    set_qt_scraper_config(
        thumbnail_source="last",
        hide_toolbars=True,
        capture_inside_layout=True
    )

    Or use the helper function for basic configuration:

    from guidata.utils.qt_scraper import get_sphinx_gallery_conf
    sphinx_gallery_conf = get_sphinx_gallery_conf()
"""

from __future__ import annotations

import logging
import os
import time
from pathlib import Path
from typing import Any

try:
    from qtpy.QtCore import Qt
    from qtpy.QtWidgets import QApplication, QDialog, QMainWindow, QToolBar, QWidget

    QT_AVAILABLE = True
except ImportError:
    QT_AVAILABLE = False

# Set up logging
logger = logging.getLogger(__name__)

# Configuration for Qt scraper (module-level)
_qt_scraper_config = {
    "thumbnail_widget": "last",  # "first", "last", or None
    "hide_toolbars": False,  # Hide all toolbars when capturing widgets
    "capture_inside_layout": False,  # Capture only the central widget inside layouts
}


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
        if _qt_scraper_config.get("hide_toolbars", False):
            # Hide all toolbars temporarily
            toolbars = widget.findChildren(QToolBar)
            for tb in toolbars:
                tb.setVisible(False)

        # Make sure the widget is visible and rendered
        widget.show()
        widget.raise_()
        widget.activateWindow()

        # Process events to ensure the widget is fully rendered
        app = QApplication.instance()
        app.processEvents()

        # Small delay to ensure rendering is complete
        time.sleep(0.1)

        # Capture the screenshot
        if _qt_scraper_config.get("capture_inside_layout", False):
            # Capture only the content inside the window, excluding title bar
            if isinstance(widget, QDialog):
                # For dialogs, grab the entire client area excluding decorations
                content_rect = widget.contentsRect()
                pixmap = widget.grab(content_rect)
            elif isinstance(widget, QMainWindow):
                # For main windows, grab the central widget if available
                central_widget = widget.centralWidget()
                if central_widget:
                    pixmap = central_widget.grab()
                else:
                    # Fallback to content rect
                    content_rect = widget.contentsRect()
                    pixmap = widget.grab(content_rect)
            else:
                # For other widgets, use content rect
                content_rect = widget.contentsRect()
                pixmap = widget.grab(content_rect)
        else:
            # Default behavior: capture the entire widget including title bar
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


def _get_example_subdirectory(
    gallery_conf: dict[str, Any], block_vars: dict[str, Any] | None
) -> str:
    """Extract subdirectory from example source file path.

    Args:
        gallery_conf: Sphinx-Gallery configuration.
        block_vars: Variables from the executed code block.

    Returns:
        Subdirectory name (e.g., "features", "advanced") or empty string if not found.
    """
    if not block_vars or "src_file" not in block_vars:
        return ""

    src_file = Path(str(block_vars["src_file"]))
    examples_dirs = gallery_conf.get("examples_dirs", "examples")

    # Handle both string and list cases for examples_dirs
    if isinstance(examples_dirs, list):
        examples_dir = examples_dirs[0] if examples_dirs else "examples"
    else:
        examples_dir = examples_dirs

    # Try to extract subdirectory from source file path
    # e.g., "examples/features/convolution.py" -> "features"
    try:
        if examples_dir in src_file.parts:
            idx = src_file.parts.index(examples_dir)
            # Check if there's a subdirectory between examples_dir and the file
            if idx + 2 < len(src_file.parts):
                subdirectory = src_file.parts[idx + 1]
                logger.debug("Detected subdirectory: %s", subdirectory)
                return subdirectory
    except (ValueError, IndexError) as exc:
        logger.debug("Could not determine subdirectory: %s", exc)

    return ""


def _get_image_directory(
    gallery_conf: dict[str, Any], block_vars: dict[str, Any] | None = None
) -> Path | None:
    """Get the image directory for saving screenshots.

    Args:
        gallery_conf: Sphinx-Gallery configuration.
        block_vars: Variables from the executed code block (optional).
         Used to determine subdirectory for examples in subsections.

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

    # Determine subdirectory from source file if available
    subdirectory = _get_example_subdirectory(gallery_conf, block_vars)

    if subdirectory:
        img_dir = src_dir / gallery_dir / subdirectory / "images"
    else:
        img_dir = src_dir / gallery_dir / "images"

    img_dir.mkdir(parents=True, exist_ok=True)
    return img_dir


def _generate_rst_block(
    image_name: str,
    gallery_conf: dict[str, Any],
    widget_index: int,
    block_vars: dict[str, Any] | None = None,
) -> str:
    """Generate RST code block for an image.

    Args:
        image_name: Name of the image file.
        gallery_conf: Sphinx-Gallery configuration.
        widget_index: Index of the widget (for alt text).
        block_vars: Variables from the executed code block (optional).
         Used to determine subdirectory for examples in subsections.

    Returns:
        RST code block.
    """
    gallery_dirs = gallery_conf.get("gallery_dirs", ["auto_examples"])
    if isinstance(gallery_dirs, list):
        rst_gallery_dir = gallery_dirs[0] if gallery_dirs else "auto_examples"
    else:
        rst_gallery_dir = gallery_dirs

    # Determine subdirectory from source file if available
    subdirectory = _get_example_subdirectory(gallery_conf, block_vars)

    if subdirectory:
        image_path = f"/{rst_gallery_dir}/{subdirectory}/images/{image_name}"
    else:
        image_path = f"/{rst_gallery_dir}/images/{image_name}"

    return f"""
.. image:: {image_path}
   :alt: Qt widget {widget_index + 1}
   :class: sphx-glr-single-img
"""


def _save_as_thumbnail(widget: QWidget, img_dir: Path, example_name: str) -> bool:
    """Save a widget as the thumbnail for sphinx-gallery.

    Args:
        widget: The Qt widget to use as thumbnail.
        img_dir: Directory to save images.
        example_name: Name of the example (without extension).

    Returns:
        True if thumbnail was saved successfully, False otherwise.
    """
    try:
        # Create thumbnail directory following sphinx-gallery convention
        thumb_dir = img_dir / "thumb"
        thumb_dir.mkdir(parents=True, exist_ok=True)

        thumb_name = f"sphx_glr_{example_name}_thumb.png"
        thumb_path = thumb_dir / thumb_name

        # Capture the widget as thumbnail
        success = _capture_widget(widget, thumb_path)
        if success:
            logger.info("Saved thumbnail: %s", thumb_path)
            return True
        else:
            logger.warning("Failed to save thumbnail: %s", thumb_path)
            return False

    except Exception as exc:
        logger.error("Failed to save thumbnail: %s", exc)
        return False


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

    # Get image directory (pass block_vars to determine subdirectory)
    img_dir = _get_image_directory(gallery_conf, block_vars)
    if img_dir is None:
        logger.error("Cannot determine image directory")
        return ""

    timestamp = int(time.time() * 1000)  # milliseconds for uniqueness

    # Get thumbnail configuration from module config
    thumbnail_config = _qt_scraper_config.get("thumbnail_widget", None)

    # Capture each widget and collect successful captures
    rst_blocks = []
    successful_widgets = []
    successful_indices = []

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
                rst_block = _generate_rst_block(image_name, gallery_conf, i, block_vars)
                rst_blocks.append(rst_block)
                successful_widgets.append(widget)
                successful_indices.append(i)
                logger.debug("Successfully captured widget %d", i + 1)
            else:
                logger.warning("Failed to capture widget %d", i + 1)

        except Exception as exc:
            logger.error("Failed to process Qt widget %d: %s", i, exc)
            continue

    # Handle thumbnail generation based on configuration
    if thumbnail_config and successful_widgets:
        if "src_file" in block_vars:
            example_name = Path(str(block_vars["src_file"])).stem
        else:
            raise RuntimeError(
                "Unable to determine example name: src_file not found in block_vars"
            )
        logger.info("Detected example name: %s", example_name)
        try:
            if thumbnail_config == "first":
                thumbnail_widget = successful_widgets[0]
                widget_idx = successful_indices[0]
                logger.info("Using first widget (index %d) as thumbnail", widget_idx)
            elif thumbnail_config == "last":
                thumbnail_widget = successful_widgets[-1]
                widget_idx = successful_indices[-1]
                logger.info("Using last widget (index %d) as thumbnail", widget_idx)
            else:
                thumbnail_widget = None

            if thumbnail_widget:
                success = _save_as_thumbnail(thumbnail_widget, img_dir, example_name)
                if success:
                    logger.info("Thumbnail generated successfully")
                else:
                    logger.warning("Failed to generate thumbnail")

        except Exception as exc:
            logger.error("Failed to generate thumbnail: %s", exc)

    # Close all widgets to prevent accumulation
    for i, widget in enumerate(widgets):
        if hasattr(widget, "close") and hasattr(widget, "deleteLater"):
            try:
                widget.close()
            except Exception as exc:
                logger.warning("Failed to close widget %d: %s", i + 1, exc)

    return "".join(rst_blocks)


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


def set_qt_scraper_config(
    thumbnail_source: str | None = "last",
    hide_toolbars: bool = False,
    capture_inside_layout: bool = False,
) -> None:
    """Set the Qt scraper thumbnail configuration.

    Args:
        thumbnail_source: Which widget to use as thumbnail. Options are "first" (use
         the first successfully captured widget), "last" (use the last successfully
         captured widget), or None (no automatic thumbnail generation).
        hide_toolbars: If True, hide all toolbars when capturing widgets.
        capture_inside_layout: If True, capture only the central widget inside layouts.
    """
    global _qt_scraper_config
    if thumbnail_source not in ("first", "last", None):
        raise ValueError("widget must be 'first', 'last', or None")
    _qt_scraper_config["thumbnail_widget"] = thumbnail_source
    _qt_scraper_config["hide_toolbars"] = hide_toolbars
    _qt_scraper_config["capture_inside_layout"] = capture_inside_layout
    logger.info("Qt scraper thumbnail config set to: %s", thumbnail_source)
    logger.info("Qt scraper hide_toolbars config set to: %s", hide_toolbars)
    logger.info(
        "Qt scraper capture_inside_layout config set to: %s", capture_inside_layout
    )


def get_sphinx_gallery_conf(**kwargs) -> dict[str, Any]:
    """Return a Sphinx-Gallery configuration dict for Qt scraper."""
    config = {
        "image_scrapers": ["guidata.utils.qt_scraper.qt_scraper"],
        "examples_dirs": "examples",  # Path to example scripts
        "gallery_dirs": "auto_examples",  # Output directory for gallery
        "filename_pattern": "",  # Pattern for example files
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
    config.update(kwargs)
    return config
