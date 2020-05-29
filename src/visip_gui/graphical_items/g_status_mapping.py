from PyQt5.QtGui import QColor

from visip.dev.action_instance import ActionInputStatus

color = {ActionInputStatus.ok: QColor(0, 200, 0),
             ActionInputStatus.seems_ok: QColor(200, 200, 0),
             ActionInputStatus.error_type: QColor(200, 0, 0),
             ActionInputStatus.error_value: QColor(200, 0, 0),
             ActionInputStatus.error_impl: QColor(200, 0, 0)}

text = {ActionInputStatus.ok: "Ok",
            ActionInputStatus.seems_ok: "Seems ok",
            ActionInputStatus.error_type: "Connection of incompatible types (error_type)",
            ActionInputStatus.error_value: "(error_value)",
            ActionInputStatus.error_impl: "(error_impl)"}
