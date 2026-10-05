# SPDX-License-Identifier: GPL-3.0-only OR LicenseRef-KymoStudio-Commercial
# Copyright (c) 2026 Christof Seidel
from PySide6.QtCore import QObject

class TelnetConfig(QObject):

    def __init__(self, default_config: dict = None):
        super(TelnetConfig, self).__init__()

        self.port = 0
        self.url = ""
        self.setup = default_config

    @property
    def setup(self):
        return {
            "port": self.port,
            "url": self.url
        }

    @setup.setter
    def setup(self, config: dict):
        self.port = config["port"]
        self.url = config["url"]
