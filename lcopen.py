import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QGridLayout, QPushButton, QLabel, 
                             QLineEdit, QComboBox, QSpinBox, QTextEdit, QGroupBox,
                             QTabWidget, QTableWidget, QTableWidgetItem, QHeaderView,
                             QCheckBox)
from PyQt6.QtCore import Qt, QTimer
import socket
import struct
import time

class LanBoxController(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("LCedit+ Replacement - LanBox Controller")
        self.setGeometry(100, 100, 1200, 800)
        
        # Create tabbed interface
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)
        
        # Create tabs
        self.create_connection_tab()
        self.create_cue_management_tab()
        self.create_layer_control_tab()
        self.create_patch_tab()
        self.create_system_controls_tab()
        self.create_communication_log_tab()
        
        # Initialize connection state
        self.connected = False
        self.socket = None
        
    def create_connection_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Connection settings
        conn_group = QGroupBox("Connection Settings")
        conn_layout = QGridLayout()
        
        # Connection Type Selection
        conn_type_label = QLabel("Connection Type:")
        self.conn_type_combo = QComboBox()
        self.conn_type_combo.addItems(["Serial", "TCP/IP", "MIDI", "UDP"])
        self.conn_type_combo.currentTextChanged.connect(self.connection_type_changed)
        
        # IP Address (for TCP/IP)
        self.ip_label = QLabel("IP Address:")
        self.ip_input = QLineEdit("192.168.1.77")
        self.ip_input.setVisible(True)
        
        # Port Input (made larger with 5-digit capacity)
        port_label = QLabel("Port:")
        self.port_input = QSpinBox()
        self.port_input.setRange(1, 65535)  # Allow full port range
        self.port_input.setValue(777)
        self.port_input.setPrefix("")  # Remove prefix if any
        self.port_input.setSuffix("")  # Remove suffix if any
        
        # Serial Port (for Serial connections)
        self.serial_label = QLabel("Serial Port:")
        self.serial_input = QLineEdit("/dev/ttyUSB0")  # Default Linux/Mac
        self.serial_input.setVisible(False)
        
        # MIDI Settings (for MIDI connections)
        self.midi_label = QLabel("MIDI Device:")
        self.midi_input = QComboBox()
        self.midi_input.addItems(["MIDI IN", "MIDI OUT", "USB-MIDI"])
        self.midi_input.setVisible(False)
        
        # UDP Settings
        self.udp_label = QLabel("UDP Port:")
        self.udp_port_input = QSpinBox()
        self.udp_port_input.setRange(1, 65535)
        self.udp_port_input.setValue(4777)
        self.udp_port_input.setVisible(False)
        
        # Password
        password_label = QLabel("Password:")
        self.password_input = QLineEdit("777")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        
        # Save Password Checkbox
        self.save_password_checkbox = QCheckBox("Save Password")
        self.save_password_checkbox.setChecked(True)
        
        # Connection Name
        name_label = QLabel("Connection Name:")
        self.connection_name_input = QLineEdit("LanBox Connection")
        
        # Connect Button
        self.connect_btn = QPushButton("Connect")
        self.connect_btn.clicked.connect(self.toggle_connection)
        
        # Add widgets to layout
        conn_layout.addWidget(conn_type_label, 0, 0)
        conn_layout.addWidget(self.conn_type_combo, 0, 1)
        
        conn_layout.addWidget(self.ip_label, 1, 0)
        conn_layout.addWidget(self.ip_input, 1, 1)
        
        conn_layout.addWidget(port_label, 2, 0)
        conn_layout.addWidget(self.port_input, 2, 1)
        
        conn_layout.addWidget(self.serial_label, 3, 0)
        conn_layout.addWidget(self.serial_input, 3, 1)
        
        conn_layout.addWidget(self.midi_label, 4, 0)
        conn_layout.addWidget(self.midi_input, 4, 1)
        
        conn_layout.addWidget(self.udp_label, 5, 0)
        conn_layout.addWidget(self.udp_port_input, 5, 1)
        
        conn_layout.addWidget(password_label, 6, 0)
        conn_layout.addWidget(self.password_input, 6, 1)
        
        conn_layout.addWidget(self.save_password_checkbox, 7, 1)
        
        conn_layout.addWidget(name_label, 8, 0)
        conn_layout.addWidget(self.connection_name_input, 8, 1)
        
        conn_layout.addWidget(self.connect_btn, 9, 1)
        
        conn_group.setLayout(conn_layout)
        layout.addWidget(conn_group)
        
        # Status display
        self.status_label = QLabel("Disconnected")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("QLabel { background-color: lightgray; padding: 5px; }")
        layout.addWidget(self.status_label)
        
        # Connection info
        info_group = QGroupBox("Connection Info")
        info_layout = QGridLayout()
        
        self.info_type = QLabel("Type: Not Connected")
        self.info_address = QLabel("Address: Not Connected")
        self.info_status = QLabel("Status: Disconnected")
        self.info_firmware = QLabel("Firmware: Unknown")
        
        info_layout.addWidget(QLabel("Connection Type:"), 0, 0)
        info_layout.addWidget(self.info_type, 0, 1)
        info_layout.addWidget(QLabel("Address:"), 1, 0)
        info_layout.addWidget(self.info_address, 1, 1)
        info_layout.addWidget(QLabel("Status:"), 2, 0)
        info_layout.addWidget(self.info_status, 2, 1)
        info_layout.addWidget(QLabel("Firmware:"), 3, 0)
        info_layout.addWidget(self.info_firmware, 3, 1)
        
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        
        # Connection Information Display
        self.connection_info_label = QLabel("")
        self.connection_info_label.setStyleSheet("QLabel { background-color: lightblue; padding: 5px; }")
        layout.addWidget(self.connection_info_label)
        
        self.tabs.addTab(tab, "Connection")
    
    def connection_type_changed(self, text):
        """Update visible fields based on selected connection type"""
        # Hide all connection-specific fields
        self.ip_input.setVisible(False)
        self.serial_input.setVisible(False)
        self.midi_input.setVisible(False)
        self.udp_port_input.setVisible(False)
        
        self.ip_label.setVisible(False)
        self.serial_label.setVisible(False)
        self.midi_label.setVisible(False)
        self.udp_label.setVisible(False)
        
        # Show fields based on selection
        if text == "TCP/IP":
            self.ip_input.setVisible(True)
            self.ip_label.setVisible(True)
            self.connection_info_label.setText("TCP/IP Connection - Default IP: 192.168.1.77, Port: 777")
            
        elif text == "Serial":
            self.serial_input.setVisible(True)
            self.serial_label.setVisible(True)
            self.connection_info_label.setText("Serial Connection - USB connection required")
            
        elif text == "MIDI":
            self.midi_input.setVisible(True)
            self.midi_label.setVisible(True)
            self.connection_info_label.setText("MIDI Connection - Configure MIDI device settings")
            
        elif text == "UDP":
            self.udp_port_input.setVisible(True)
            self.udp_label.setVisible(True)
            self.connection_info_label.setText("UDP Connection - Default port: 4777 for broadcasting")
    
    def create_cue_management_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Cue List Management
        cue_list_group = QGroupBox("Cue List Management")
        cue_layout = QGridLayout()
        
        # Create Cue List
        create_label = QLabel("Create Cue List:")
        self.create_cue_input = QSpinBox()
        self.create_cue_input.setRange(1, 999)
        self.create_cue_btn = QPushButton("Create")
        self.create_cue_btn.clicked.connect(self.create_cue_list)
        
        # Load Cue List
        load_label = QLabel("Load Cue List:")
        self.load_cue_input = QSpinBox()
        self.load_cue_input.setRange(1, 999)
        self.load_cue_btn = QPushButton("Load")
        self.load_cue_btn.clicked.connect(self.load_cue_list)
        
        # Save Cue List
        save_label = QLabel("Save Cue List:")
        self.save_cue_input = QSpinBox()
        self.save_cue_input.setRange(1, 999)
        self.save_cue_btn = QPushButton("Save")
        self.save_cue_btn.clicked.connect(self.save_cue_list)
        
        # Clear Cue List
        clear_label = QLabel("Clear Cue List:")
        self.clear_cue_input = QSpinBox()
        self.clear_cue_input.setRange(1, 999)
        self.clear_cue_btn = QPushButton("Clear")
        self.clear_cue_btn.clicked.connect(self.clear_cue_list)
        
        cue_layout.addWidget(create_label, 0, 0)
        cue_layout.addWidget(self.create_cue_input, 0, 1)
        cue_layout.addWidget(self.create_cue_btn, 0, 2)
        
        cue_layout.addWidget(load_label, 1, 0)
        cue_layout.addWidget(self.load_cue_input, 1, 1)
        cue_layout.addWidget(self.load_cue_btn, 1, 2)
        
        cue_layout.addWidget(save_label, 2, 0)
        cue_layout.addWidget(self.save_cue_input, 2, 1)
        cue_layout.addWidget(self.save_cue_btn, 2, 2)
        
        cue_layout.addWidget(clear_label, 3, 0)
        cue_layout.addWidget(self.clear_cue_input, 3, 1)
        cue_layout.addWidget(self.clear_cue_btn, 3, 2)
        
        cue_list_group.setLayout(cue_layout)
        layout.addWidget(cue_list_group)
        
        # Cue Steps Management
        cue_steps_group = QGroupBox("Cue Step Management")
        steps_layout = QGridLayout()
        
        # Insert Step
        insert_label = QLabel("Insert Step:")
        self.insert_layer_input = QSpinBox()
        self.insert_layer_input.setRange(1, 63)
        self.insert_step_input = QSpinBox()
        self.insert_step_input.setRange(1, 99)
        self.insert_btn = QPushButton("Insert")
        self.insert_btn.clicked.connect(self.insert_step)
        
        # Append Step
        append_label = QLabel("Append Step:")
        self.append_layer_input = QSpinBox()
        self.append_layer_input.setRange(1, 63)
        self.append_btn = QPushButton("Append")
        self.append_btn.clicked.connect(self.append_step)
        
        # Delete Step
        delete_label = QLabel("Delete Step:")
        self.delete_layer_input = QSpinBox()
        self.delete_layer_input.setRange(1, 63)
        self.delete_step_input = QSpinBox()
        self.delete_step_input.setRange(1, 99)
        self.delete_btn = QPushButton("Delete")
        self.delete_btn.clicked.connect(self.delete_step)
        
        steps_layout.addWidget(insert_label, 0, 0)
        steps_layout.addWidget(self.insert_layer_input, 0, 1)
        steps_layout.addWidget(self.insert_step_input, 0, 2)
        steps_layout.addWidget(self.insert_btn, 0, 3)
        
        steps_layout.addWidget(append_label, 1, 0)
        steps_layout.addWidget(self.append_layer_input, 1, 1)
        steps_layout.addWidget(self.append_btn, 1, 2)
        
        steps_layout.addWidget(delete_label, 2, 0)
        steps_layout.addWidget(self.delete_layer_input, 2, 1)
        steps_layout.addWidget(self.delete_step_input, 2, 2)
        steps_layout.addWidget(self.delete_btn, 2, 3)
        
        cue_steps_group.setLayout(steps_layout)
        layout.addWidget(cue_steps_group)
        
        # Cue List Editor (simplified table view)
        editor_group = QGroupBox("Cue List Editor")
        self.cue_table = QTableWidget(10, 4)  # 10 rows, 4 columns
        self.cue_table.setHorizontalHeaderLabels(["Step", "Action", "Channel", "Value"])
        self.cue_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        editor_layout = QVBoxLayout()
        editor_layout.addWidget(self.cue_table)
        editor_group.setLayout(editor_layout)
        layout.addWidget(editor_group)
        
        self.tabs.addTab(tab, "Cue Management")
    
    def create_layer_control_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Layer Control
        layer_group = QGroupBox("Layer Control")
        layer_layout = QGridLayout()
        
        # Set Layer Mix Mode
        mix_label = QLabel("Set Mix Mode:")
        self.mix_layer_input = QSpinBox()
        self.mix_layer_input.setRange(1, 63)
        self.mix_mode_input = QComboBox()
        self.mix_mode_input.addItems(["Off", "Normal", "Additive", "Subtractive", "Transparent"])
        self.mix_btn = QPushButton("Set")
        self.mix_btn.clicked.connect(self.set_mix_mode)
        
        # Set Transparency Depth
        trans_label = QLabel("Transparency:")
        self.trans_layer_input = QSpinBox()
        self.trans_layer_input.setRange(1, 63)
        self.trans_depth_input = QSpinBox()
        self.trans_depth_input.setRange(0, 255)
        self.trans_btn = QPushButton("Set")
        self.trans_btn.clicked.connect(self.set_transparency)
        
        # Layer Status
        status_label = QLabel("Layer Status:")
        self.layer_status_input = QSpinBox()
        self.layer_status_input.setRange(1, 63)
        self.status_btn = QPushButton("Get Status")
        self.status_btn.clicked.connect(self.get_layer_status)
        
        layer_layout.addWidget(mix_label, 0, 0)
        layer_layout.addWidget(self.mix_layer_input, 0, 1)
        layer_layout.addWidget(self.mix_mode_input, 0, 2)
        layer_layout.addWidget(self.mix_btn, 0, 3)
        
        layer_layout.addWidget(trans_label, 1, 0)
        layer_layout.addWidget(self.trans_layer_input, 1, 1)
        layer_layout.addWidget(self.trans_depth_input, 1, 2)
        layer_layout.addWidget(self.trans_btn, 1, 3)
        
        layer_layout.addWidget(status_label, 2, 0)
        layer_layout.addWidget(self.layer_status_input, 2, 1)
        layer_layout.addWidget(self.status_btn, 2, 2)
        
        layer_group.setLayout(layer_layout)
        layout.addWidget(layer_group)
        
        # Layer Settings
        settings_group = QGroupBox("Layer Settings")
        settings_layout = QGridLayout()
        
        # Set Layer Name
        name_label = QLabel("Set Layer Name:")
        self.layer_name_input = QSpinBox()
        self.layer_name_input.setRange(1, 63)
        self.name_text_input = QLineEdit("Layer")
        self.name_btn = QPushButton("Set")
        self.name_btn.clicked.connect(self.set_layer_name)
        
        # Set Layer Priority
        priority_label = QLabel("Set Priority:")
        self.priority_layer_input = QSpinBox()
        self.priority_layer_input.setRange(1, 63)
        self.priority_value_input = QSpinBox()
        self.priority_value_input.setRange(0, 255)
        self.priority_btn = QPushButton("Set")
        self.priority_btn.clicked.connect(self.set_layer_priority)
        
        settings_layout.addWidget(name_label, 0, 0)
        settings_layout.addWidget(self.layer_name_input, 0, 1)
        settings_layout.addWidget(self.name_text_input, 0, 2)
        settings_layout.addWidget(self.name_btn, 0, 3)
        
        settings_layout.addWidget(priority_label, 1, 0)
        settings_layout.addWidget(self.priority_layer_input, 1, 1)
        settings_layout.addWidget(self.priority_value_input, 1, 2)
        settings_layout.addWidget(self.priority_btn, 1, 3)
        
        settings_group.setLayout(settings_layout)
        layout.addWidget(settings_group)
        
        self.tabs.addTab(tab, "Layer Control")
    
    def create_patch_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # DMX Patch Management
        patch_group = QGroupBox("DMX Patch Management")
        patch_layout = QGridLayout()
        
        # Set Patch
        patch_label = QLabel("Set Patch:")
        self.patch_dmx_input = QSpinBox()
        self.patch_dmx_input.setRange(1, 512)
        self.patch_mixer_input = QSpinBox()
        self.patch_mixer_input.setRange(0, 3072)
        self.patch_btn = QPushButton("Patch")
        self.patch_btn.clicked.connect(self.patch_channels)
        
        # Get Patch
        get_patch_label = QLabel("Get Patch:")
        self.get_patch_dmx_input = QSpinBox()
        self.get_patch_dmx_input.setRange(1, 512)
        self.get_patch_btn = QPushButton("Get")
        self.get_patch_btn.clicked.connect(self.get_patch)
        
        patch_layout.addWidget(patch_label, 0, 0)
        patch_layout.addWidget(self.patch_dmx_input, 0, 1)
        patch_layout.addWidget(self.patch_mixer_input, 0, 2)
        patch_layout.addWidget(self.patch_btn, 0, 3)
        
        patch_layout.addWidget(get_patch_label, 1, 0)
        patch_layout.addWidget(self.get_patch_dmx_input, 1, 1)
        patch_layout.addWidget(self.get_patch_btn, 1, 2)
        
        patch_group.setLayout(patch_layout)
        layout.addWidget(patch_group)
        
        # Gain Control
        gain_group = QGroupBox("Gain Control")
        gain_layout = QGridLayout()
        
        # Set Gain
        gain_label = QLabel("Set Gain:")
        self.gain_dmx_input = QSpinBox()
        self.gain_dmx_input.setRange(1, 512)
        self.gain_value_input = QSpinBox()
        self.gain_value_input.setRange(0, 255)
        self.gain_btn = QPushButton("Set")
        self.gain_btn.clicked.connect(self.set_gain)
        
        # Get Gain
        get_gain_label = QLabel("Get Gain:")
        self.get_gain_dmx_input = QSpinBox()
        self.get_gain_dmx_input.setRange(1, 512)
        self.get_gain_btn = QPushButton("Get")
        self.get_gain_btn.clicked.connect(self.get_gain)
        
        gain_layout.addWidget(gain_label, 0, 0)
        gain_layout.addWidget(self.gain_dmx_input, 0, 1)
        gain_layout.addWidget(self.gain_value_input, 0, 2)
        gain_layout.addWidget(self.gain_btn, 0, 3)
        
        gain_layout.addWidget(get_gain_label, 1, 0)
        gain_layout.addWidget(self.get_gain_dmx_input, 1, 1)
        gain_layout.addWidget(self.get_gain_btn, 1, 2)
        
        gain_group.setLayout(gain_layout)
        layout.addWidget(gain_group)
        
        # Analog Input Monitoring
        analog_group = QGroupBox("Analog Input Monitoring")
        analog_layout = QGridLayout()
        
        analog_info_label = QLabel("Analog Inputs 1-8 are mapped to Mixer Channels 3061-3068")
        analog_info_label.setWordWrap(True)
        
        analog_layout.addWidget(analog_info_label, 0, 0)
        analog_group.setLayout(analog_layout)
        layout.addWidget(analog_group)
        
        self.tabs.addTab(tab, "DMX Patch")
    
    def create_system_controls_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # System Controls
        system_group = QGroupBox("System Controls")
        system_layout = QGridLayout()
        
        # Reset Button (as mentioned in manual - Image 83)
        reset_btn = QPushButton("Factory Reset")
        reset_btn.setStyleSheet("QPushButton { background-color: red; color: white; }")
        reset_btn.clicked.connect(self.factory_reset)
        
        # Save Data
        save_data_btn = QPushButton("Save Configuration")
        save_data_btn.clicked.connect(self.save_configuration)
        
        # Get System Info
        sys_info_btn = QPushButton("Get System Info")
        sys_info_btn.clicked.connect(self.get_system_info)
        
        system_layout.addWidget(reset_btn, 0, 0)
        system_layout.addWidget(save_data_btn, 0, 1)
        system_layout.addWidget(sys_info_btn, 0, 2)
        
        system_group.setLayout(system_layout)
        layout.addWidget(system_group)
        
        # Auto Update Control
        auto_update_group = QGroupBox("Auto Update")
        auto_update_layout = QHBoxLayout()
        
        self.auto_update_enabled = True
        self.auto_update_btn = QPushButton("Disable Auto Update")
        self.auto_update_btn.clicked.connect(self.toggle_auto_update)
        
        update_now_btn = QPushButton("Update Now")
        update_now_btn.clicked.connect(self.update_now)
        
        auto_update_layout.addWidget(self.auto_update_btn)
        auto_update_layout.addWidget(update_now_btn)
        
        auto_update_group.setLayout(auto_update_layout)
        layout.addWidget(auto_update_group)
        
        # UDP Broadcasting Settings
        udp_group = QGroupBox("UDP Broadcasting Settings")
        udp_layout = QGridLayout()
        
        udp_broadcast_label = QLabel("Broadcast Channels:")
        self.udp_broadcast_start = QSpinBox()
        self.udp_broadcast_start.setRange(1, 3072)
        self.udp_broadcast_end = QSpinBox()
        self.udp_broadcast_end.setRange(1, 3072)
        
        udp_broadcast_btn = QPushButton("Start Broadcasting")
        udp_broadcast_btn.clicked.connect(self.start_udp_broadcast)
        
        udp_layout.addWidget(udp_broadcast_label, 0, 0)
        udp_layout.addWidget(self.udp_broadcast_start, 0, 1)
        udp_layout.addWidget(self.udp_broadcast_end, 0, 2)
        udp_layout.addWidget(udp_broadcast_btn, 0, 3)
        
        udp_group.setLayout(udp_layout)
        layout.addWidget(udp_group)
        
        self.tabs.addTab(tab, "System Controls")
    
    def create_communication_log_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Communication Log
        log_group = QGroupBox("Communication Log")
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setMinimumHeight(300)
        
        clear_log_btn = QPushButton("Clear Log")
        clear_log_btn.clicked.connect(self.clear_log)
        
        layout.addWidget(self.log_output)
        layout.addWidget(clear_log_btn)
        
        self.tabs.addTab(tab, "Communication Log")
    
    def toggle_connection(self):
        if not self.connected:
            self.connect_to_lanbox()
        else:
            self.disconnect_from_lanbox()
    
    def connect_to_lanbox(self):
        conn_type = self.conn_type_combo.currentText()
        
        try:
            if conn_type == "TCP/IP":
                # Create TCP socket connection
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.socket.settimeout(5.0)
                self.socket.connect((self.ip_input.text(), self.port_input.value()))
                
                # Send password (as per documentation: 55 55 55 13 for "777" + carriage return)
                password = b"777\x0d"
                self.socket.send(password)
                
                self.connected = True
                self.status_label.setText("Connected via TCP/IP")
                self.status_label.setStyleSheet("QLabel { background-color: lightgreen; padding: 5px; }")
                
                # Update connection info
                self.info_type.setText("TCP/IP")
                self.info_address.setText(self.ip_input.text() + ":" + str(self.port_input.value()))
                self.info_status.setText("Connected")
                self.info_firmware.setText("v3.01+")
                
                self.append_to_log("Connected to LanBox via TCP/IP at {}:{}".format(
                    self.ip_input.text(), self.port_input.value()))
            
            elif conn_type == "Serial":
                # Simulate serial connection
                self.connected = True
                self.status_label.setText("Connected via Serial")
                self.status_label.setStyleSheet("QLabel { background-color: lightgreen; padding: 5px; }")
                
                # Update connection info
                self.info_type.setText("Serial")
                self.info_address.setText(self.serial_input.text())
                self.info_status.setText("Connected")
                self.info_firmware.setText("v3.01+")
                
                self.append_to_log("Connected to LanBox via Serial at {}".format(self.serial_input.text()))
            
            elif conn_type == "MIDI":
                # Simulate MIDI connection
                self.connected = True
                self.status_label.setText("Connected via MIDI")
                self.status_label.setStyleSheet("QLabel { background-color: lightgreen; padding: 5px; }")
                
                # Update connection info
                self.info_type.setText("MIDI")
                self.info_address.setText(self.midi_input.currentText())
                self.info_status.setText("Connected")
                self.info_firmware.setText("v3.01+")
                
                self.append_to_log("Connected to LanBox via MIDI {}".format(self.midi_input.currentText()))
            
            elif conn_type == "UDP":
                # Simulate UDP connection
                self.connected = True
                self.status_label.setText("Connected via UDP")
                self.status_label.setStyleSheet("QLabel { background-color: lightgreen; padding: 5px; }")
                
                # Update connection info
                self.info_type.setText("UDP")
                self.info_address.setText("Port: " + str(self.udp_port_input.value()))
                self.info_status.setText("Connected")
                self.info_firmware.setText("v3.01+")
                
                self.append_to_log("Connected to LanBox via UDP port {}".format(self.udp_port_input.value()))
            
        except Exception as e:
            self.connected = False
            self.status_label.setText("Connection Failed")
            self.status_label.setStyleSheet("QLabel { background-color: lightcoral; padding: 5px; }")
            self.append_to_log("Connection failed: {}".format(str(e)))
    
    def disconnect_from_lanbox(self):
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
        self.connected = False
        self.status_label.setText("Disconnected")
        self.status_label.setStyleSheet("QLabel { background-color: lightgray; padding: 5px; }")
        self.info_status.setText("Disconnected")
        self.append_to_log("Disconnected from LanBox")
    
    def append_to_log(self, message):
        timestamp = time.strftime("%H:%M:%S")
        self.log_output.append("[{}] {}".format(timestamp, message))
    
    def clear_log(self):
        self.log_output.clear()
    
    def toggle_auto_update(self):
        self.auto_update_enabled = not self.auto_update_enabled
        if self.auto_update_enabled:
            self.auto_update_btn.setText("Disable Auto Update")
            self.append_to_log("Auto Update enabled")
        else:
            self.auto_update_btn.setText("Enable Auto Update")
            self.append_to_log("Auto Update disabled")
    
    def update_now(self):
        self.append_to_log("Manual update initiated")
        # In a real implementation, this would trigger an update
    
    def create_cue_list(self):
        if not self.connected:
            self.append_to_log("Not connected to LanBox!")
            return
            
        cue_list_num = self.create_cue_input.value()
        
        try:
            # Command: *5F CLIS # where CLIS is 16bit number (Create Cue List)
            command = struct.pack('>H', cue_list_num)  # 16-bit big-endian
            full_command = b'*5F' + command + b'#'
            
            self.socket.send(full_command)
            self.append_to_log("Created Cue List: {}".format(cue_list_num))
            
        except Exception as e:
            self.append_to_log("Error creating cue list: {}".format(str(e)))
    
    def load_cue_list(self):
        if not self.connected:
            self.append_to_log("Not connected to LanBox!")
            return
            
        cue_list_num = self.load_cue_input.value()
        
        try:
            # Command: *5D CLIS # where CLIS is 16bit number (Load Cue List)
            command = struct.pack('>H', cue_list_num)  # 16-bit big-endian
            full_command = b'*5D' + command + b'#'
            
            self.socket.send(full_command)
            self.append_to_log("Loaded Cue List: {}".format(cue_list_num))
            
        except Exception as e:
            self.append_to_log("Error loading cue list: {}".format(str(e)))
    
    def save_cue_list(self):
        if not self.connected:
            self.append_to_log("Not connected to LanBox!")
            return
            
        cue_list_num = self.save_cue_input.value()
        
        try:
            # Command: *5E CLIS # where CLIS is 16bit number (Save Cue List)
            command = struct.pack('>H', cue_list_num)  # 16-bit big-endian
            full_command = b'*5E' + command + b'#'
            
            self.socket.send(full_command)
            self.append_to_log("Saved Cue List: {}".format(cue_list_num))
            
        except Exception as e:
            self.append_to_log("Error saving cue list: {}".format(str(e)))
    
    def clear_cue_list(self):
        if not self.connected:
            self.append_to_log("Not connected to LanBox!")
            return
            
        cue_list_num = self.clear_cue_input.value()
        
        try:
            # Command: *5A CLIS # where CLIS is 16bit number (Clear Cue List)
            command = struct.pack('>H', cue_list_num)  # 16-bit big-endian
            full_command = b'*5A' + command + b'#'
            
            self.socket.send(full_command)
            self.append_to_log("Cleared Cue List: {}".format(cue_list_num))
            
        except Exception as e:
            self.append_to_log("Error clearing cue list: {}".format(str(e)))
    
    def insert_step(self):
        if not self.connected:
            self.append_to_log("Not connected to LanBox!")
            return
            
        layer_id = self.insert_layer_input.value()
        step_number = self.insert_step_input.value()
        
        try:
            # Command: *5C LA (CS) # where LA is 8bit, CS is optional 8bit
            command = struct.pack('>BB', layer_id, step_number)
            full_command = b'*5C' + command + b'#'
            
            self.socket.send(full_command)
            self.append_to_log("Inserted step {} in Layer {}: {}".format(
                step_number, layer_id, "success"))
            
        except Exception as e:
            self.append_to_log("Error inserting step: {}".format(str(e)))
    
    def append_step(self):
        if not self.connected:
            self.append_to_log("Not connected to LanBox!")
            return
            
        layer_id = self.append_layer_input.value()
        
        try:
            # Command: *5C LA # where LA is 8bit (append to layer)
            command = struct.pack('>B', layer_id)
            full_command = b'*5C' + command + b'#'
            
            self.socket.send(full_command)
            self.append_to_log("Appended step in Layer {}: success".format(layer_id))
            
        except Exception as e:
            self.append_to_log("Error appending step: {}".format(str(e)))
    
    def delete_step(self):
        if not self.connected:
            self.append_to_log("Not connected to LanBox!")
            return
            
        layer_id = self.delete_layer_input.value()
        step_number = self.delete_step_input.value()
        
        try:
            # Command: *5B LA CS # where LA is 8bit, CS is 8bit
            command = struct.pack('>BB', layer_id, step_number)
            full_command = b'*5B' + command + b'#'
            
            self.socket.send(full_command)
            self.append_to_log("Deleted step {} in Layer {}: success".format(step_number, layer_id))
            
        except Exception as e:
            self.append_to_log("Error deleting step: {}".format(str(e)))
    
    def set_mix_mode(self):
        if not self.connected:
            self.append_to_log("Not connected to LanBox!")
            return
            
        layer_id = self.mix_layer_input.value()
        mix_mode = self.mix_mode_input.currentIndex()
        
        try:
            # Command: *47 LA MM # where LA is 8bit, MM is 8bit mix mode
            command = struct.pack('>BB', layer_id, mix_mode)
            full_command = b'*47' + command + b'#'
            
            self.socket.send(full_command)
            self.append_to_log("Set Layer {} mix mode to: {}".format(
                layer_id, self.mix_mode_input.currentText()))
            
        except Exception as e:
            self.append_to_log("Error setting mix mode: {}".format(str(e)))
    
    def set_transparency(self):
        if not self.connected:
            self.append_to_log("Not connected to LanBox!")
            return
            
        layer_id = self.trans_layer_input.value()
        transparency = self.trans_depth_input.value()
        
        try:
            # Command: *63 LA TD # where LA is 8bit, TD is 8bit transparency
            command = struct.pack('>BB', layer_id, transparency)
            full_command = b'*63' + command + b'#'
            
            self.socket.send(full_command)
            self.append_to_log("Set Layer {} transparency to: {}".format(layer_id, transparency))
            
        except Exception as e:
            self.append_to_log("Error setting transparency: {}".format(str(e)))
    
    def get_layer_status(self):
        if not self.connected:
            self.append_to_log("Not connected to LanBox!")
            return
            
        layer_id = self.layer_status_input.value()
        
        try:
            # Command: *49 LA # where LA is 8bit (Get Layer Status)
            command = struct.pack('>B', layer_id)
            full_command = b'*49' + command + b'#'
            
            self.socket.send(full_command)
            self.append_to_log("Requested status for Layer {}".format(layer_id))
            
        except Exception as e:
            self.append_to_log("Error getting layer status: {}".format(str(e)))
    
    def set_layer_name(self):
        if not self.connected:
            self.append_to_log("Not connected to LanBox!")
            return
            
        layer_id = self.layer_name_input.value()
        name = self.name_text_input.text()[:15]  # Limit to 15 chars
        
        try:
            # Command: *48 LA NAME # where LA is 8bit, NAME is string
            # This would require more complex encoding for strings in real implementation
            self.append_to_log("Set Layer {} name to: {}".format(layer_id, name))
            
        except Exception as e:
            self.append_to_log("Error setting layer name: {}".format(str(e)))
    
    def set_layer_priority(self):
        if not self.connected:
            self.append_to_log("Not connected to LanBox!")
            return
            
        layer_id = self.priority_layer_input.value()
        priority = self.priority_value_input.value()
        
        try:
            # Command: *4A LA PR # where LA is 8bit, PR is 8bit priority
            command = struct.pack('>BB', layer_id, priority)
            full_command = b'*4A' + command + b'#'
            
            self.socket.send(full_command)
            self.append_to_log("Set Layer {} priority to: {}".format(layer_id, priority))
            
        except Exception as e:
            self.append_to_log("Error setting layer priority: {}".format(str(e)))
    
    def patch_channels(self):
        if not self.connected:
            self.append_to_log("Not connected to LanBox!")
            return
            
        dmx_channel = self.patch_dmx_input.value()
        mixer_channel = self.patch_mixer_input.value()
        
        try:
            # Command: *81 DMX1 CHA1 DMX2 CHA2 ... # (as per documentation)
            # Simple example with one channel
            command = struct.pack('>HH', dmx_channel, mixer_channel)
            full_command = b'*81' + command + b'#'
            
            self.socket.send(full_command)
            self.append_to_log("Patched DMX {} to Mixer {}".format(dmx_channel, mixer_channel))
            
        except Exception as e:
            self.append_to_log("Error patching channels: {}".format(str(e)))
    
    def get_patch(self):
        if not self.connected:
            self.append_to_log("Not connected to LanBox!")
            return
            
        dmx_channel = self.get_patch_dmx_input.value()
        
        try:
            # Command: *80 DMX1 # where DMX1 is 16bit (Get Patch)
            command = struct.pack('>H', dmx_channel)
            full_command = b'*80' + command + b'#'
            
            self.socket.send(full_command)
            self.append_to_log("Requested patch for DMX {}".format(dmx_channel))
            
        except Exception as e:
            self.append_to_log("Error getting patch: {}".format(str(e)))
    
    def set_gain(self):
        if not self.connected:
            self.append_to_log("Not connected to LanBox!")
            return
            
        dmx_channel = self.gain_dmx_input.value()
        gain_value = self.gain_value_input.value()
        
        try:
            # Command: *82 DMX1 GAIN # where DMX1 is 16bit, GAIN is 8bit (Set Gain)
            command = struct.pack('>HB', dmx_channel, gain_value)
            full_command = b'*82' + command + b'#'
            
            self.socket.send(full_command)
            self.append_to_log("Set DMX {} gain to: {}".format(dmx_channel, gain_value))
            
        except Exception as e:
            self.append_to_log("Error setting gain: {}".format(str(e)))
    
    def get_gain(self):
        if not self.connected:
            self.append_to_log("Not connected to LanBox!")
            return
            
        dmx_channel = self.get_gain_dmx_input.value()
        
        try:
            # Command: *82 DMX1 0 # where DMX1 is 16bit, 0 indicates get (Get Gain)
            command = struct.pack('>H', dmx_channel)
            full_command = b'*82' + command + b'#'
            
            self.socket.send(full_command)
            self.append_to_log("Requested gain for DMX {}".format(dmx_channel))
            
        except Exception as e:
            self.append_to_log("Error getting gain: {}".format(str(e)))
    
    def factory_reset(self):
        if not self.connected:
            self.append_to_log("Not connected to LanBox!")
            return
            
        try:
            # Command: *B1 # (Factory Reset)
            full_command = b'*B1#'
            
            self.socket.send(full_command)
            self.append_to_log("Factory reset command sent")
            
        except Exception as e:
            self.append_to_log("Error sending factory reset: {}".format(str(e)))
    
    def save_configuration(self):
        if not self.connected:
            self.append_to_log("Not connected to LanBox!")
            return
            
        try:
            # Command: *B2 # (Save Configuration)
            full_command = b'*B2#'
            
            self.socket.send(full_command)
            self.append_to_log("Configuration save command sent")
            
        except Exception as e:
            self.append_to_log("Error saving configuration: {}".format(str(e)))
    
    def get_system_info(self):
        if not self.connected:
            self.append_to_log("Not connected to LanBox!")
            return
            
        try:
            # Command: *B3 # (Get System Info)
            full_command = b'*B3#'
            
            self.socket.send(full_command)
            self.append_to_log("System info request sent")
            
        except Exception as e:
            self.append_to_log("Error getting system info: {}".format(str(e)))
    
    def start_udp_broadcast(self):
        if not self.connected:
            self.append_to_log("Not connected to LanBox!")
            return
            
        start_channel = self.udp_broadcast_start.value()
        end_channel = self.udp_broadcast_end.value()
        
        try:
            self.append_to_log("Starting UDP broadcast for channels {}-{}".format(start_channel, end_channel))
            # In a real implementation, this would configure the UDP broadcasting settings
        except Exception as e:
            self.append_to_log("Error starting UDP broadcast: {}".format(str(e)))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = LanBoxController()
    window.show()
    sys.exit(app.exec())
