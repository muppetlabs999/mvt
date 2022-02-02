# Mobile Verification Toolkit (MVT)
# Copyright (c) 2021-2022 The MVT Project Authors.
# Use of this software is governed by the MVT License 1.1 that can be found at
#   https://license.mvt.re/1.1/

import logging

from mvt.android.modules.adb.dumpsys_battery_daily import DumpsysBatteryDaily

from .base import BugReportModule

log = logging.getLogger(__name__)


class BatteryDaily(BugReportModule):
    """This module extracts records from battery daily updates."""

    def __init__(self, file_path=None, base_folder=None, output_folder=None,
                 serial=None, fast_mode=False, log=None, results=[]):
        super().__init__(file_path=file_path, base_folder=base_folder,
                         output_folder=output_folder, fast_mode=fast_mode,
                         log=log, results=results)

    def serialize(self, record):
        return {
            "timestamp": record["from"],
            "module": self.__class__.__name__,
            "event": "battery_daily",
            "data": f"Recorded update of package {record['package_name']} with vers {record['vers']}"
        }

    def check_indicators(self):
        if not self.indicators:
            return

        for result in self.results:
            ioc = self.indicators.check_app_id(result["package_name"])
            if ioc:
                result["matched_indicator"] = ioc
                self.detected.append(result)
                continue

    def run(self):
        dumpstate_files = self._get_files_by_pattern("dumpstate-*")
        if not dumpstate_files:
            return

        content = self._get_file_content(dumpstate_files[0])
        if not content:
            return

        lines = []
        in_batterystats = False
        in_daily = False
        for line in content.decode().splitlines():
            if line.strip() == "DUMP OF SERVICE batterystats:":
                in_batterystats = True
                continue

            if not in_batterystats:
                continue

            if line.strip() == "Daily stats:":
                lines.append(line)
                in_daily = True
                continue

            if not in_daily:
                continue

            if line.strip() == "":
                break

            lines.append(line)

        self.results = DumpsysBatteryDaily.parse_battery_daily("\n".join(lines))
