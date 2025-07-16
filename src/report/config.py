# ******************************************************************************
# Copyright (c) 2025 Huawei Technologies Co., Ltd.
# jiuwen-deepsearch is licensed under Mulan PSL v2.
# You can use this software according to the terms and conditions of the Mulan PSL v2.
# You may obtain a copy of Mulan PSL v2 at:
#          http://license.coscl.org.cn/MulanPSL2
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND,
# EITHER EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT,
# MERCHANTABILITY OR FIT FOR A PARTICULAR PURPOSE.
# See the Mulan PSL v2 for more details.
# ******************************************************************************/

import enum

from .report_processor import DefaultReportFormatProcessor, ReportMarkdown


class ReportStyle(enum.Enum):
    SCHOLARLY = "scholarly"
    SCIENCE_COMMUNICATION = "science_communication"
    NEWS_REPORT = "news_report"
    SELF_MEDIA = "self_media"


class ReportFormat(enum.Enum):
    MARKDOWN = ReportMarkdown
    WORD = None
    PPT = None
    EXCEL = None
    HTML = None
    PDF = None

    def get_name(self):
        return self.name.lower()

    def get_processor(self) -> DefaultReportFormatProcessor:
        processor = self.value
        if not processor:
            return DefaultReportFormatProcessor()
        return processor()


class ReportLang(enum.Enum):
    EN = "en-US"
    ZN = "zh-CN"
