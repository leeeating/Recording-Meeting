import logging
from datetime import datetime, timedelta

from pydantic import ValidationError
from PyQt6.QtCore import QDateTime, Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDateTimeEdit,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.models.schemas import MeetingCreateSchema, MeetingResponseSchema
from frontend.services.api_client import ApiClient
from shared.config import config

from .base_page import BasePage
from .page_config import ALIGNLEFT, ALIGNRIGHT, ALIGNTOP, MEETING_LAYOUT_OPTIONS
from .utils import (
    CustomLineEdit,
    DateTimeInputGroup,
    create_form_block,
    fixed_width_height,
    get_widget_value,
)

logger = logging.getLogger(__name__)


class TaskManagerPage(BasePage):
    pass
