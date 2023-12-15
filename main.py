import os
import sys
import subprocess
from PyQt5.QtWidgets import QApplication, QMainWindow, QDockWidget, QPushButton, QListWidget, QLabel, QWidget, QVBoxLayout, QInputDialog, QMessageBox, QMenu
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QObject
from PyQt5.QtGui import QIcon

class Worker(QObject):
    result_signal = pyqtSignal(list)

    def run(self):
        try:
            # Run pip list command
            pip_list_output = subprocess.check_output([sys.executable, '-m', 'pip', 'list']).decode('utf-8')

            # Extract package names
            packages = [line.split(' ')[0] for line in pip_list_output.split('\n')[2:] if line]

            self.result_signal.emit(packages)

        except Exception as e:
            print(f"Error fetching package list: {e}")

class PackageExplorer(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Package Explorer")
        self.setGeometry(100, 100, 800, 600)

        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)

        self.create_dock_widget()

        self.install_button = QPushButton('Install Package', self)
        self.install_button.clicked.connect(self.install_package)
        self.sidebar_layout.addWidget(self.install_button)

        self.package_list_label = QLabel("Package List:", self)
        self.sidebar_layout.addWidget(self.package_list_label)

        self.package_list_widget = QListWidget(self)
        self.package_list_widget.itemDoubleClicked.connect(self.open_in_file_explorer)
        self.package_list_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.package_list_widget.customContextMenuRequested.connect(self.show_context_menu)
        self.sidebar_layout.addWidget(self.package_list_widget)

        self.worker = Worker()
        self.worker_thread = QThread(self)
        self.worker.moveToThread(self.worker_thread)
        self.worker.result_signal.connect(self.show_package_list)
        self.worker_thread.started.connect(self.worker.run)
        self.worker_thread.start()

        self.show()

    def create_dock_widget(self):
        self.dock = QDockWidget("Sidebar", self)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.dock)

        self.sidebar_widget = QWidget(self)
        self.dock.setWidget(self.sidebar_widget)

        self.sidebar_layout = QVBoxLayout(self.sidebar_widget)

        self.delete_button = QPushButton(QIcon.fromTheme('user-trash'), 'Delete Package', self)
        self.delete_button.clicked.connect(self.delete_package)

        # Adding the delete button to the top right of the main window
        delete_button_layout = QVBoxLayout()
        delete_button_layout.addWidget(self.delete_button, alignment=Qt.AlignTop | Qt.AlignRight)

        self.central_layout = QVBoxLayout(self.central_widget)
        self.central_layout.addLayout(delete_button_layout)
        self.central_layout.addStretch(1)

        self.refresh_button = QPushButton(QIcon.fromTheme('view-refresh'), 'Refresh', self)
        self.refresh_button.clicked.connect(self.refresh)
        delete_button_layout.addWidget(self.refresh_button, alignment=Qt.AlignTop | Qt.AlignRight)

    def show_package_list(self, packages):
        self.package_list_widget.clear()
        self.package_list_widget.addItems(packages)

        # Show or hide delete button based on selection
        self.update_delete_button_visibility()

    def install_package(self):
        package_name, ok_pressed = QInputDialog.getText(self, "Install Package", "Enter the package name to install:")

        if ok_pressed and package_name:
            subprocess.Popen([sys.executable, '-m', 'pip', 'install', package_name])

    def delete_package(self):
        current_item = self.package_list_widget.currentItem()

        if current_item is not None:
            selected_package = current_item.text()

            # Prompt user for delete or uninstall
            choice = self.delete_option_prompt()

            if choice == "Delete":
                folder_path = os.path.join(sys.prefix, 'Lib', 'site-packages', selected_package)

                if not os.path.exists(folder_path):
                    return
                try:
                    os.rmdir(folder_path)
                except Exception as e:
                    print(f"Error deleting folder: {e}")
            elif choice == "Uninstall":
                try:
                    subprocess.Popen([sys.executable, '-m', 'pip', 'uninstall', '-y', selected_package])
                except Exception as e:
                    print(f"Error uninstalling package: {e}")
        else:
            QMessageBox.warning(self, "No Package Selected", "Please select a package to delete.")

        self.refresh()

    def delete_option_prompt(self):
        options = ["Delete", "Uninstall"]
        choice, _ = QInputDialog.getItem(self, "Delete Option", "Select delete option:", options, 0, False)
        return choice

    def refresh(self):
        self.worker_thread.quit()
        self.worker_thread.wait()
        self.worker_thread.start()

    def show_context_menu(self, pos):
        context_menu = QMenu(self)

        open_action = context_menu.addAction('Open with File Explorer')
        open_action.triggered.connect(lambda: self.open_in_file_explorer(self.package_list_widget.itemAt(pos)))

        delete_action = context_menu.addAction('Delete 🗑️')
        delete_action.triggered.connect(self.delete_package)

        refresh_action = context_menu.addAction('Refresh 🔃')
        refresh_action.triggered.connect(self.refresh)

        context_menu.exec_(self.package_list_widget.mapToGlobal(pos))

    def update_delete_button_visibility(self):
        self.delete_button.setVisible(self.package_list_widget.currentItem() is not None)

    def open_in_file_explorer(self, item):
        selected_package = item.text()
        folder_path = os.path.join(sys.prefix, 'Lib', 'site-packages', selected_package)

        if os.path.exists(folder_path):
            subprocess.Popen(['explorer', folder_path])

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PackageExplorer()
    sys.exit(app.exec_())
