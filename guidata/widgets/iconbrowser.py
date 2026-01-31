# -*- coding: utf-8 -*-
#
# Licensed under the terms of the BSD 3-Clause
# (see guidata/LICENSE for details)

"""
Icon Browser Widget
====================

A utility widget for browsing icon collections in directories.

Usage
^^^^^

To launch the icon browser from the command line:

.. code-block:: console

    $ # Launch with folder selection dialog
    $ python -m guidata.widgets.iconbrowser
    $ # Or use the command-line tool (after installing guidata):
    $ giconbrowser

    $ # Launch with a specific folder
    $ python -m guidata.widgets.iconbrowser /path/to/icons
    $ # Or use the command-line tool:
    $ giconbrowser /path/to/icons

Features
^^^^^^^^

- Browse icon collections with tree view for folder navigation
- Adjustable thumbnail sizes (16-256 pixels)
- Single-click to open file location in system file explorer
- Support for PNG, SVG, ICO, JPG, GIF, and BMP formats
- Responsive grid layout that adapts to window size
"""

from __future__ import annotations

import argparse
import os
import os.path as osp
import subprocess
import sys
from typing import TYPE_CHECKING

from qtpy import QtCore as QC
from qtpy import QtGui as QG
from qtpy import QtWidgets as QW

from guidata import qthelpers as qth

if TYPE_CHECKING:
    from collections.abc import Sequence


class IconGridWidget(QW.QWidget):
    """Widget displaying a grid of icon thumbnails."""

    def __init__(self, parent: QW.QWidget | None = None, icon_size: int = 64) -> None:
        """Initialize the icon grid widget.

        Args:
            parent: Parent widget
            icon_size: Size of icon thumbnails in pixels
        """
        super().__init__(parent)
        self.icon_size = icon_size
        self.icon_paths: list[str] = []

        # Create scroll area
        self.scroll_area = QW.QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(QC.Qt.ScrollBarAlwaysOff)

        # Create container widget for the grid
        self.container = QW.QWidget()
        self.grid_layout = QW.QGridLayout(self.container)
        self.grid_layout.setSpacing(10)
        self.scroll_area.setWidget(self.container)

        # Main layout
        layout = QW.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.scroll_area)

    def set_icon_size(self, size: int) -> None:
        """Set the icon thumbnail size.

        Args:
            size: New icon size in pixels
        """
        self.icon_size = size
        self.refresh_icons()

    def load_icons(self, icon_paths: Sequence[str]) -> None:
        """Load icons from the given file paths.

        Args:
            icon_paths: List of icon file paths
        """
        self.icon_paths = list(icon_paths)
        self.refresh_icons()

    def refresh_icons(self) -> None:
        """Refresh the icon grid display."""
        # Clear existing layout
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Calculate number of columns based on available width
        available_width = self.scroll_area.viewport().width()
        # Account for margins and spacing
        item_width = self.icon_size + 20  # icon + padding
        columns = max(1, available_width // item_width)

        # Add icons to grid
        for idx, icon_path in enumerate(self.icon_paths):
            row = idx // columns
            col = idx % columns

            icon_widget = self._create_icon_widget(icon_path)
            self.grid_layout.addWidget(icon_widget, row, col)

        # Add stretch to push icons to top
        self.grid_layout.setRowStretch(self.grid_layout.rowCount(), 1)

    def _create_icon_widget(self, icon_path: str) -> QW.QWidget:
        """Create a widget for displaying a single icon.

        Args:
            icon_path: Path to the icon file

        Returns:
            Widget containing the icon and label
        """
        widget = QW.QWidget()
        layout = QW.QVBoxLayout(widget)
        layout.setSpacing(5)
        layout.setContentsMargins(5, 5, 5, 5)

        # Icon label
        icon_label = QW.QLabel()
        icon_label.setFixedSize(self.icon_size, self.icon_size)
        icon_label.setScaledContents(True)
        icon_label.setAlignment(QC.Qt.AlignCenter)

        # Load and set icon
        if icon_path.lower().endswith(".svg"):
            # For SVG files, use QIcon which renders them properly at any size
            icon = QG.QIcon(icon_path)
            pixmap = icon.pixmap(self.icon_size, self.icon_size)
            if not pixmap.isNull():
                icon_label.setPixmap(pixmap)
            else:
                icon_label.setText("Error")
        else:
            # For raster images, use QPixmap
            pixmap = QG.QPixmap(icon_path)
            if not pixmap.isNull():
                scaled_pixmap = pixmap.scaled(
                    self.icon_size,
                    self.icon_size,
                    QC.Qt.KeepAspectRatio,
                    QC.Qt.SmoothTransformation,
                )
                icon_label.setPixmap(scaled_pixmap)
            else:
                icon_label.setText("Error")

        # Filename label
        filename = osp.basename(icon_path)
        text_label = QW.QLabel(filename)
        text_label.setAlignment(QC.Qt.AlignCenter)
        text_label.setWordWrap(True)
        text_label.setMaximumWidth(self.icon_size + 20)
        font = text_label.font()
        font.setPointSize(8)
        text_label.setFont(font)
        text_label.setToolTip(icon_path)

        layout.addWidget(icon_label)
        layout.addWidget(text_label)

        # Make widget clickable (single click)
        widget.setCursor(QC.Qt.PointingHandCursor)
        widget.mousePressEvent = lambda event: self._open_in_explorer(icon_path)

        return widget

    def _open_in_explorer(self, file_path: str) -> None:
        """Open file explorer and select the given file.

        Args:
            file_path: Path to the file to select
        """
        file_path = osp.abspath(file_path)
        if sys.platform == "win32":
            # Windows: use explorer with /select
            subprocess.run(["explorer", "/select,", file_path], check=False)
        elif sys.platform == "darwin":
            # macOS: use open with -R flag
            subprocess.run(["open", "-R", file_path], check=False)
        else:
            # Linux: open directory containing the file
            directory = osp.dirname(file_path)
            subprocess.run(["xdg-open", directory], check=False)

    def resizeEvent(self, event: QG.QResizeEvent) -> None:
        """Handle resize events to adjust grid layout.

        Args:
            event: Resize event
        """
        super().resizeEvent(event)
        # Refresh layout on resize to adjust number of columns
        QC.QTimer.singleShot(100, self.refresh_icons)


class IconBrowserWindow(QW.QMainWindow):
    """Main window for browsing icon collections."""

    def __init__(
        self, parent: QW.QWidget | None = None, init_folder: str | None = None
    ) -> None:
        """Initialize the icon browser window.

        Args:
            parent: Parent widget
            init_folder: Initial folder to open
        """
        super().__init__(parent)
        self.setObjectName("iconbrowser")
        qth.win32_fix_title_bar_background(self)
        self.setWindowTitle("Icon Browser")
        self.setWindowIcon(qth.get_std_icon("FileDialogListView"))
        self.resize(1000, 700)

        self.icon_size = 64
        self.current_folder: str | None = None
        self.icon_dict: dict[str, list[str]] = {}
        self.previous_item: QW.QTreeWidgetItem | None = None

        # Store folder icons
        self.folder_closed_icon = qth.get_std_icon("DirClosedIcon")
        self.folder_open_icon = qth.get_std_icon("DirOpenIcon")

        # Create central widget with splitter
        splitter = QW.QSplitter(QC.Qt.Horizontal)

        # Create tree widget for folder navigation
        self.tree_widget = QW.QTreeWidget()
        self.tree_widget.setHeaderLabel("Folders")
        self.tree_widget.setMinimumWidth(200)
        self.tree_widget.itemClicked.connect(self._on_tree_item_clicked)

        # Create icon grid widget
        self.icon_grid = IconGridWidget(icon_size=self.icon_size)

        # Add widgets to splitter
        splitter.addWidget(self.tree_widget)
        splitter.addWidget(self.icon_grid)
        splitter.setStretchFactor(0, 1)  # Tree takes less space
        splitter.setStretchFactor(1, 4)  # Icon grid takes more space
        # Set initial sizes: 20% for tree, 80% for icon grid
        splitter.setSizes([200, 800])

        self.setCentralWidget(splitter)

        # Create toolbar
        self._create_toolbar()

        # Load initial folder if provided
        if init_folder:
            self.open_folder(init_folder)

    def _create_toolbar(self) -> None:
        """Create the toolbar with actions."""
        toolbar = self.addToolBar("Main Toolbar")
        toolbar.setMovable(False)

        # Open folder action
        open_action = qth.create_action(
            self,
            "Open Folder",
            triggered=self._on_open_folder,
            icon=qth.get_std_icon("DirIcon"),
            tip="Open a folder containing icons",
            shortcut=QG.QKeySequence.Open,
        )
        toolbar.addAction(open_action)

        toolbar.addSeparator()

        refresh_action = qth.create_action(
            self,
            "Refresh",
            triggered=lambda: self.open_folder(self.current_folder)
            if self.current_folder
            else None,
            icon=qth.get_std_icon("BrowserReload"),
            tip="Refresh the current folder",
        )
        toolbar.addAction(refresh_action)

        # Set icon size action
        size_action = qth.create_action(
            self,
            "Set Icon Size",
            triggered=self._on_set_icon_size,
            icon=qth.get_std_icon("FileDialogDetailedView"),
            tip="Set the thumbnail size for icons",
        )
        toolbar.addAction(size_action)

        toolbar.addSeparator()

        # About action
        about_action = qth.create_action(
            self,
            "About",
            triggered=self._on_about,
            icon=qth.get_std_icon("MessageBoxInformation"),
            tip="About Icon Browser",
        )
        toolbar.addAction(about_action)

        toolbar.addSeparator()

        # Quit action
        quit_action = qth.create_action(
            self,
            "Quit",
            triggered=self.close,
            icon=qth.get_std_icon("DialogCloseButton"),
            tip="Quit the application",
            shortcut=QG.QKeySequence.Quit,
        )
        toolbar.addAction(quit_action)

    def _on_open_folder(self) -> None:
        """Handle open folder action."""
        folder = QW.QFileDialog.getExistingDirectory(
            self,
            "Select Folder Containing Icons",
            self.current_folder or "",
            QW.QFileDialog.ShowDirsOnly,
        )
        if folder:
            self.open_folder(folder)

    def _on_set_icon_size(self) -> None:
        """Handle set icon size action."""
        size, ok = QW.QInputDialog.getInt(
            self,
            "Set Icon Size",
            "Enter thumbnail size (pixels):",
            self.icon_size,
            16,
            256,
            1,
        )
        if ok:
            self.icon_size = size
            self.icon_grid.set_icon_size(size)

    def _on_about(self) -> None:
        """Show the About dialog."""
        about_text = """
<h3>Icon Browser</h3>
<p>A utility for browsing icon collections in directories.</p>
<p><b>Features:</b></p>
<ul>
<li>Tree view for folder navigation</li>
<li>Adjustable thumbnail sizes (16-256 pixels)</li>
<li>Single-click to open file location in system explorer</li>
<li>Support for PNG, SVG, ICO, JPG, GIF, and BMP formats</li>
</ul>
<p><b>Part of:</b> guidata - Automatic GUI generation for dataset editing</p>
<p><b>License:</b> BSD 3-Clause</p>
"""
        QW.QMessageBox.about(self, "About Icon Browser", about_text)

    def _on_tree_item_clicked(self, item: QW.QTreeWidgetItem, column: int) -> None:
        """Handle tree item click to display icons for the selected folder.

        Args:
            item: The clicked tree item
            column: The column that was clicked
        """
        # Reset previous item icon to closed folder
        if self.previous_item is not None:
            self.previous_item.setIcon(0, self.folder_closed_icon)

        # Set current item icon to open folder
        item.setIcon(0, self.folder_open_icon)
        self.previous_item = item

        folder_path = item.data(0, QC.Qt.UserRole)
        if folder_path and folder_path in self.icon_dict:
            icon_paths = self.icon_dict[folder_path]
            self.icon_grid.load_icons(icon_paths)

    def _build_tree_structure(
        self, folder: str, icon_dict: dict[str, list[str]]
    ) -> None:
        """Build the tree structure from the icon dictionary.

        Args:
            folder: Root folder path
            icon_dict: Dictionary mapping folder paths to icon file lists
        """
        self.tree_widget.clear()

        # Create a mapping of folder paths to tree items
        path_to_item: dict[str, QW.QTreeWidgetItem] = {}

        # Sort paths to ensure parents are created before children
        sorted_paths = sorted(icon_dict.keys())

        for rel_path in sorted_paths:
            icon_count = len(icon_dict[rel_path])

            # Create item text with icon count
            if rel_path == ".":
                display_name = osp.basename(folder)
            else:
                display_name = osp.basename(rel_path)

            item_text = f"{display_name} ({icon_count})"

            # Determine parent path
            if rel_path == ".":
                # Root item - use closed folder icon initially
                item = QW.QTreeWidgetItem([item_text])
                item.setData(0, QC.Qt.UserRole, rel_path)
                item.setIcon(0, self.folder_closed_icon)
                self.tree_widget.addTopLevelItem(item)
                path_to_item[rel_path] = item
            else:
                # Child item - find parent
                parent_rel_path = osp.dirname(rel_path)
                if parent_rel_path == "":
                    parent_rel_path = "."

                parent_item = path_to_item.get(parent_rel_path)
                if parent_item is not None:
                    item = QW.QTreeWidgetItem(parent_item, [item_text])
                    item.setData(0, QC.Qt.UserRole, rel_path)
                    item.setIcon(0, self.folder_closed_icon)
                    path_to_item[rel_path] = item
                else:
                    # Fallback: add as top-level if parent not found
                    item = QW.QTreeWidgetItem([item_text])
                    item.setData(0, QC.Qt.UserRole, rel_path)
                    item.setIcon(0, self.folder_closed_icon)
                    self.tree_widget.addTopLevelItem(item)
                    path_to_item[rel_path] = item

        # Expand the root item and select it
        if self.tree_widget.topLevelItemCount() > 0:
            root_item = self.tree_widget.topLevelItem(0)
            root_item.setExpanded(True)
            root_item.setIcon(0, self.folder_open_icon)  # Set root as open
            self.tree_widget.setCurrentItem(root_item)
            self.previous_item = root_item  # Track root as selected
            # Load icons for root folder
            root_path = root_item.data(0, QC.Qt.UserRole)
            if root_path in icon_dict:
                self.icon_grid.load_icons(icon_dict[root_path])

    def open_folder(self, folder: str) -> None:
        """Open a folder and populate tree with icon folders.

        Args:
            folder: Path to the folder to open
        """
        self.current_folder = folder

        # Find all icon files recursively
        icon_extensions = (".png", ".svg", ".ico", ".jpg", ".jpeg", ".gif", ".bmp")
        self.icon_dict = {}

        for root, dirs, files in os.walk(folder):
            # Filter icon files
            icon_files = [
                osp.join(root, f) for f in files if f.lower().endswith(icon_extensions)
            ]

            if icon_files:
                # Use relative path for tree structure
                rel_path = osp.relpath(root, folder)
                if rel_path == ".":
                    rel_path = "."
                self.icon_dict[rel_path] = sorted(icon_files)

        # Check if any icons were found
        if not self.icon_dict:
            QW.QMessageBox.information(
                self,
                "No Icons Found",
                f"No icon files found in:\n{folder}\n\n"
                f"Supported formats: {', '.join(icon_extensions)}",
            )
            return

        # Build tree structure
        self._build_tree_structure(folder, self.icon_dict)

        # Update window title
        self.setWindowTitle(f"Icon Browser - {folder}")


def main(args: list[str] | None = None) -> int:
    """Launch the icon browser application.

    Args:
        args: Command-line arguments (if None, uses sys.argv)

    Returns:
        Exit code (0 for success)

    Examples:
        >>> # Launch with folder selection dialog
        >>> main()
        >>> # Launch with specific folder
        >>> main(['/path/to/icons'])
    """
    parser = argparse.ArgumentParser(
        description="Icon Browser - Browse icon collections in directories",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  giconbrowser                    # Open with folder selection dialog
  giconbrowser /path/to/icons    # Open specific folder
  python -m guidata.widgets.iconbrowser ~/Pictures/Icons
        """,
    )
    parser.add_argument(
        "folder",
        nargs="?",
        default=None,
        help="Initial folder to open (optional, prompts if not provided)",
    )

    parsed_args = parser.parse_args(args)

    with qth.qt_app_context(exec_loop=True):
        window = IconBrowserWindow(init_folder=parsed_args.folder)
        window.show()


if __name__ == "__main__":
    main()
