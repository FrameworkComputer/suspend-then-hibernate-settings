import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GLib
import subprocess
import os
import urllib.request
import shutil
import threading
import tempfile
import time
import json

class SleepConfigApp(Gtk.Window):
    def __init__(self):
        print("Initializing application...")
        Gtk.Window.__init__(self, title="Lid Close and Hibernate Settings")
        self.set_border_width(20)
        self.set_default_size(400, 600)

        # Apply a CSS style to the window
        self.apply_styles()

        # Connect the delete-event signal to close the application properly
        self.connect("delete-event", Gtk.main_quit)

        # Create the main vertical box layout
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        vbox.set_halign(Gtk.Align.CENTER)
        vbox.set_valign(Gtk.Align.CENTER)
        self.add(vbox)

        # Header label
        header = Gtk.Label()
        header.set_markup("<span size='x-large' weight='bold' foreground='#3A3A3A'>Lid Close and Hibernate Settings</span>")
        header.set_margin_bottom(20)
        vbox.pack_start(header, False, False, 0)

        # Progress bar
        self.progress_bar = Gtk.ProgressBar()
        self.progress_bar.set_margin_bottom(20)
        vbox.pack_start(self.progress_bar, False, False, 0)

        # Buttons in specified order

        # 1) Install Dependencies
        dependencies_button = self.create_button("1) Install Dependencies", "system-software-install")
        dependencies_button.connect("clicked", self.install_dependencies)
        vbox.pack_start(dependencies_button, True, True, 0)

        # 2) Configure Hibernate
        configure_button = self.create_button("2) Configure Hibernate", "system-software-install")
        configure_button.connect("clicked", self.configure_hibernation)
        vbox.pack_start(configure_button, True, True, 0)

        # 3) Manage Hibernate Extension
        extension_button = self.create_button("3) Manage Hibernate Extension", "system-software-install")
        extension_button.connect("clicked", self.manage_gnome_extension)
        vbox.pack_start(extension_button, True, True, 0)

        # 4) (Optional) Set Suspend-then-Hibernate Time
        suspend_time_button = self.create_button("4) (Optional) Set Suspend-then-Hibernate Time", "system-run")
        suspend_time_button.connect("clicked", self.set_suspend_then_hibernate_time)
        vbox.pack_start(suspend_time_button, True, True, 0)

        # 5) (Optional) Set Lid Close Action
        lid_action_button = self.create_button("5) (Optional) Set Lid Close Action", "system-shutdown")
        lid_action_button.connect("clicked", self.set_lid_close_action)
        vbox.pack_start(lid_action_button, True, True, 0)

        # 6) (Optional) Check Hibernation Settings
        status_button = self.create_button("6) (Optional) Check Hibernation Settings", "dialog-information")
        status_button.connect("clicked", self.check_status)
        vbox.pack_start(status_button, True, True, 0)

        # Exit button
        exit_button = self.create_button("Exit", "application-exit")
        exit_button.connect("clicked", self.on_exit_clicked)
        vbox.pack_start(exit_button, True, True, 0)

        self.show_all()
        print("Application initialized.")

    def create_button(self, label, icon_name):
        button = Gtk.Button()
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=20)
        icon = Gtk.Image.new_from_icon_name(icon_name, Gtk.IconSize.BUTTON)
        label_widget = Gtk.Label(label=label)
        box.pack_start(icon, False, False, 0)
        box.pack_start(label_widget, False, False, 0)
        button.add(box)
        button.set_margin_start(20)
        button.set_margin_end(20)
        button.set_margin_bottom(10)
        button.get_style_context().add_class("custom-button")
        return button

    def apply_styles(self):
        css = b"""
        * {
            font-family: Roboto, Arial, sans-serif;
        }
        window {
            background: linear-gradient(to bottom, #f0f4f8, #dce4ec);
        }
        button.custom-button {
            padding: 12px;
            background-image: linear-gradient(to bottom, #7a9cbf, #6688a3);
            color: #ffffff;
            border-radius: 8px;
            font-weight: bold;
            font-size: 14px;
            text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.3);
            box-shadow: 1px 1px 4px rgba(0, 0, 0, 0.1);
        }
        button.custom-button:hover {
            background-image: linear-gradient(to bottom, #89a9d0, #7a9cbf);
            box-shadow: 2px 2px 6px rgba(0, 0, 0, 0.15);
        }
        button.custom-button:active {
            background-image: linear-gradient(to bottom, #536a80, #4a5f70);
        }
        label {
            color: #3A3A3A;
            font-weight: bold;
        }
        dialog {
            border-radius: 8px;
            box-shadow: 2px 2px 10px rgba(0, 0, 0, 0.2);
        }
        """
        style_provider = Gtk.CssProvider()
        style_provider.load_from_data(css)
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(), style_provider, Gtk.STYLE_PROVIDER_PRIORITY_USER
        )

    # 1) Install Dependencies
    def install_dependencies(self, button):
        print("Installing dependencies...")
        required_packages = ["python3-gobject", "polkit", "gettext"]
        missing_packages = []

        for package in required_packages:
            result = subprocess.run(["rpm", "-q", package], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if result.returncode != 0:
                print(f"Package {package} is missing.")
                missing_packages.append(package)
            else:
                print(f"Package {package} is already installed.")

        if missing_packages:
            self.show_message_dialog(f"Installing missing packages: {' '.join(missing_packages)}")
            install_command = ["pkexec", "dnf", "install", "-y"] + missing_packages
            self.run_command(install_command)
            self.show_message_dialog("Dependencies installed successfully.")
        else:
            self.show_message_dialog("All required packages are already installed.")
        print("Dependency installation completed.")

    # 2) Configure Hibernate
    def configure_hibernation(self, button):
        print("Configuring hibernation...")
        self.progress_bar.set_fraction(0.0)
        threading.Thread(target=self.run_configuration_script).start()

    def run_configuration_script(self):
        steps = 6  # Number of steps in the configuration process
        progress_increment = 1.0 / steps

        with tempfile.NamedTemporaryFile(delete=False) as temp_script:
            temp_script.write(b"#!/bin/bash\n")
            temp_script.write(b"set -e\n")

            # Check and install required packages
            temp_script.write(b"REQUIRED_PACKAGES=\"audit policycoreutils-python-utils libnotify\"\n")
            temp_script.write(b"for PACKAGE in $REQUIRED_PACKAGES; do\n")
            temp_script.write(b"    if ! rpm -q $PACKAGE &>/dev/null; then\n")
            temp_script.write(b"        dnf install -y $PACKAGE\n")
            temp_script.write(b"    fi\n")
            temp_script.write(b"done\n")

            # Create /etc/systemd/sleep.conf immediately
            temp_script.write(b"mkdir -p /etc/systemd/\n")
            temp_script.write(b"touch /etc/systemd/sleep.conf\n")

        temp_script_path = temp_script.name
        os.chmod(temp_script_path, 0o755)
        print(f"Temporary script created at {temp_script_path}")

        # Update progress bar for the initial step
        self.update_progress_bar(progress_increment)

        # Run the temporary script with pkexec
        print("Running configuration script with pkexec...")
        result = self.pkexec_command([temp_script_path])

        # Clean up the temporary file
        os.remove(temp_script_path)
        print("Temporary script removed.")

        # Update progress bar for each completed step
        for i in range(1, steps):
            self.update_progress_bar(progress_increment * (i + 1))
            time.sleep(0.5)  # Simulate time delay for each step

        # Show completion message
        GLib.idle_add(self.show_message_dialog, "Hibernate configuration completed. Please reboot for the changes to take effect.")
        print("Hibernate configuration completed.")

    def update_progress_bar(self, fraction):
        GLib.idle_add(self.progress_bar.set_fraction, fraction)
        print(f"Progress bar updated to {fraction * 100}%")

    def pkexec_command(self, command):
        try:
            print(f"Executing command with pkexec: {' '.join(command)}")
            return self.run_command(["pkexec"] + command)
        except subprocess.CalledProcessError:
            GLib.idle_add(
                self.show_message_dialog,
                "An error occurred while executing a command with pkexec. Please check your system logs for details.",
            )
            return None

    def run_command(self, command):
        try:
            print(f"Running command: {' '.join(command)}")
            result = subprocess.run(
                command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True, text=True
            )
            print(f"Command output: {result.stdout}")
            return result.stdout
        except subprocess.CalledProcessError as e:
            error_message = (
                f"An error occurred while executing the command: {' '.join(command)}\n"
                f"Exit Code: {e.returncode}\n"
                f"Output: {e.stdout}\n"
                f"Error Output: {e.stderr}"
            )
            print(error_message)
            GLib.idle_add(self.show_message_dialog, error_message)
            return None

    def show_message_dialog(self, message):
        print(f"Displaying message dialog: {message}")
        dialog = Gtk.MessageDialog(
            transient_for=self,
            flags=0,
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK,
            text=message,
        )
        dialog.run()
        dialog.destroy()

    # 3) Manage Hibernate Extension
    def manage_gnome_extension(self, button):
        print("Managing GNOME extension...")
        dialog = Gtk.Dialog(title="GNOME Extension Setup", transient_for=self, flags=0)
        dialog.add_buttons(Gtk.STOCK_OK, Gtk.ResponseType.OK, Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL)
        dialog.set_default_size(300, 100)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        install_button = Gtk.RadioButton(label="Install Extension")
        uninstall_button = Gtk.RadioButton(group=install_button, label="Uninstall Extension")
        box.pack_start(install_button, False, False, 0)
        box.pack_start(uninstall_button, False, False, 0)

        content_area = dialog.get_content_area()
        content_area.add(box)
        dialog.show_all()

        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            if install_button.get_active():
                self.download_extension()
                self.install_extension()
            elif uninstall_button.get_active():
                self.uninstall_extension()
        dialog.destroy()
        print("GNOME extension management completed.")

    def download_extension(self):
        EXTENSION_URL = "https://github.com/ctsdownloads/gnome-shell-extension-hibernate-status/archive/refs/heads/master.zip"
        ZIP_FILE = "gnome-shell-extension-hibernate-status-master.zip"

        if not os.path.isfile(ZIP_FILE):
            self.show_message_dialog("Downloading extension zip file...")
            print(f"Downloading extension from {EXTENSION_URL}")
            urllib.request.urlretrieve(EXTENSION_URL, ZIP_FILE)
            print("Extension downloaded.")
        else:
            self.show_message_dialog("Extension zip file already downloaded.")
            print("Extension zip file already exists.")

    def install_extension(self):
        ZIP_FILE = "gnome-shell-extension-hibernate-status-master.zip"

        # Extract the zip file to a temporary directory
        with tempfile.TemporaryDirectory() as tmpdirname:
            print(f"Extracting {ZIP_FILE} to {tmpdirname}")
            subprocess.run(["unzip", "-o", ZIP_FILE, "-d", tmpdirname], check=True)

            # Find the extracted extension directory
            extracted_dir = os.path.join(tmpdirname, 'gnome-shell-extension-hibernate-status-master')
            if not os.path.isdir(extracted_dir):
                self.show_message_dialog("Failed to find the extracted extension directory.")
                print("Extracted extension directory not found.")
                return

            # Read the UUID from metadata.json
            metadata_path = os.path.join(extracted_dir, 'metadata.json')
            if not os.path.isfile(metadata_path):
                self.show_message_dialog("Failed to find metadata.json in the extension directory.")
                print("metadata.json not found in the extracted extension.")
                return

            with open(metadata_path, "r") as f:
                metadata = json.load(f)
                extension_uuid = metadata.get("uuid")
                if not extension_uuid:
                    self.show_message_dialog("Failed to get UUID from metadata.json.")
                    print("UUID not found in metadata.json.")
                    return

                print(f"Extension UUID: {extension_uuid}")

            # Install the extension manually
            self.show_message_dialog("Installing the extension...")
            print("Installing the extension...")

            # Create the extensions directory if it doesn't exist
            extensions_dir = os.path.expanduser("~/.local/share/gnome-shell/extensions")
            os.makedirs(extensions_dir, exist_ok=True)

            # Copy the extension to the extensions directory
            target_dir = os.path.join(extensions_dir, extension_uuid)
            if os.path.exists(target_dir):
                shutil.rmtree(target_dir)
                print(f"Existing extension directory {target_dir} removed.")
            shutil.copytree(extracted_dir, target_dir)
            print(f"Extension copied to {target_dir}")

            # Compile schemas if the extension has any
            schemas_dir = os.path.join(target_dir, 'schemas')
            if os.path.exists(schemas_dir):
                print("Compiling schemas...")
                subprocess.run(['glib-compile-schemas', schemas_dir], check=True)
                print("Schemas compiled.")
            else:
                print("No schemas directory found; skipping schema compilation.")

            # Reload GNOME Shell extensions
            print("Reloading GNOME Shell extensions...")
            subprocess.run(["dbus-send", "--session", "--dest=org.gnome.Shell", "--type=method_call",
                            "/org/gnome/Shell", "org.gnome.Shell.Eval", "string:'Main.extensionManager.reloadExtensions()'"],
                           check=True)
            print("GNOME Shell extensions reloaded.")

            # Enable the extension
            try:
                self.show_message_dialog("Extension installed. Enabling the extension...")
                print("Enabling the extension...")
                subprocess.run(["gnome-extensions", "enable", extension_uuid], check=True)
                self.show_message_dialog(
                    "Extension installed and enabled. Please reboot your system for the extension to take effect."
                )
                print("Extension installation and activation completed.")
            except subprocess.CalledProcessError as e:
                print(f"Failed to enable the extension. Reboot is required. Error: {e}")
                self.show_message_dialog("Extension installed, but a reboot is required to enable it. Please reboot now.")

    def uninstall_extension(self):
        print("Uninstalling extension...")
        # List installed extensions to get accurate UUIDs
        result = subprocess.run(["gnome-extensions", "list"], capture_output=True, text=True)
        installed_extensions = result.stdout.strip().split('\n')
        print(f"Installed extensions: {installed_extensions}")

        # Filter extensions that have 'hibernate-status' in their UUID
        extension_uuids = [uuid for uuid in installed_extensions if 'hibernate-status' in uuid]

        if not extension_uuids:
            self.show_message_dialog("Extension is not installed.")
            print("Extension is not installed.")
            return

        for extension_uuid in extension_uuids:
            self.show_message_dialog(f"Uninstalling the extension {extension_uuid}...")
            print(f"Uninstalling extension {extension_uuid}...")
            subprocess.run(["gnome-extensions", "uninstall", extension_uuid], check=True)
            print(f"Extension {extension_uuid} uninstalled.")

        self.show_message_dialog("Extension(s) successfully uninstalled. Please reboot your system to complete the changes.")

    # 4) (Optional) Set Suspend-then-Hibernate Time
    def set_suspend_then_hibernate_time(self, button):
        print("Setting Suspend-then-Hibernate Time...")
        dialog = Gtk.Dialog(title="Set Suspend-then-Hibernate Time", transient_for=self, flags=0)
        dialog.add_buttons(Gtk.STOCK_OK, Gtk.ResponseType.OK, Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL)
        dialog.set_default_size(300, 100)
        content_area = dialog.get_content_area()
        content_area.set_spacing(10)

        label = Gtk.Label(label="Enter the time in seconds for the system to suspend-then-hibernate:")
        content_area.add(label)
        entry = Gtk.Entry()
        entry.set_placeholder_text("Time in seconds (e.g., 600 for 10 minutes)")
        content_area.add(entry)
        dialog.show_all()

        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            sth_time = entry.get_text()
            if sth_time.isdigit():
                # Overwrite existing /etc/systemd/sleep.conf with new time
                command = f"""
                    echo '[Sleep]' | sudo tee /etc/systemd/sleep.conf;
                    echo 'HibernateDelaySec={sth_time}' | sudo tee -a /etc/systemd/sleep.conf;
                """
                self.pkexec_command(["bash", "-c", command])
                self.show_message_dialog("Suspend-then-hibernate time updated successfully.")
            else:
                self.show_message_dialog("Invalid input. Please enter a valid number in seconds.")
        dialog.destroy()

    # 5) (Optional) Set Lid Close Action
    def set_lid_close_action(self, button):
        print("Setting Lid Close Action...")
        dialog = Gtk.Dialog(title="Set Lid Close Action", transient_for=self, flags=0)
        dialog.add_buttons(Gtk.STOCK_OK, Gtk.ResponseType.OK, Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL)
        dialog.set_default_size(300, 150)
        content_area = dialog.get_content_area()
        content_area.set_spacing(10)

        label = Gtk.Label(label="Select the action to perform when the lid is closed:")
        content_area.add(label)

        suspend_radio = Gtk.RadioButton.new_with_label_from_widget(None, "Suspend")
        hibernate_radio = Gtk.RadioButton.new_with_label_from_widget(suspend_radio, "Hibernate")
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.pack_start(suspend_radio, False, False, 0)
        box.pack_start(hibernate_radio, False, False, 0)
        content_area.add(box)

        dialog.show_all()

        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            if suspend_radio.get_active():
                lid_choice = "suspend"
            elif hibernate_radio.get_active():
                lid_choice = "hibernate"
            else:
                lid_choice = None

            if lid_choice:
                command = [
                    "bash", "-c",
                    (
                        "mkdir -p /etc/systemd && "
                        "touch /etc/systemd/logind.conf && "
                        f"echo -e '[Login]\\nHandleLidSwitch={lid_choice}' > /etc/systemd/logind.conf"
                    )
                ]
                self.pkexec_command(command)
                self.show_message_dialog(f"Lid close action set to {lid_choice}. Please power off and restart your system for the changes to take effect.")
        dialog.destroy()

    # 6) (Optional) Check Hibernation Settings
    def check_status(self, button):
        print("Checking Hibernation Settings...")
        required_packages = ["python3-gobject", "polkit"]
        missing_packages = []
        for package in required_packages:
            result = subprocess.run(["rpm", "-q", package], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if result.returncode != 0:
                missing_packages.append(package)

        dependencies_status = "All required packages are installed." if not missing_packages else f"Missing packages: {', '.join(missing_packages)}"

        EXTENSION_UUID = "hibernate-status@ctsdownloads"
        installed_extensions = subprocess.run(["gnome-extensions", "list"], capture_output=True, text=True).stdout
        extension_status = "Installed" if EXTENSION_UUID in installed_extensions else "Not Installed"

        hibernate_delay = "Not Set"
        if os.path.exists("/etc/systemd/sleep.conf"):
            with open("/etc/systemd/sleep.conf", "r") as file:
                lines = file.readlines()
                for line in lines:
                    if line.strip().startswith("HibernateDelaySec="):
                        hibernate_delay = line.strip().split('=')[1]
                        break

        lid_action = "Unknown"
        if os.path.exists("/etc/systemd/logind.conf"):
            with open("/etc/systemd/logind.conf", "r") as file:
                for line in file:
                    if line.strip().startswith("HandleLidSwitch="):
                        lid_action = line.strip().split('=')[1]
                        break

        status_message = (
            f"Dependencies: {dependencies_status}\n"
            f"GNOME Extension: {extension_status}\n"
            f"Suspend-then-Hibernate Time: {hibernate_delay}\n"
            f"Lid Close Action: {lid_action}"
        )
        self.show_message_dialog(status_message)

    def on_exit_clicked(self, button):
        print("Exiting application...")
        Gtk.main_quit()

if __name__ == "__main__":
    app = SleepConfigApp()
    Gtk.main()
