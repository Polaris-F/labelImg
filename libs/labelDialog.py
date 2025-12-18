try:
    from PyQt5.QtGui import *
    from PyQt5.QtCore import *
    from PyQt5.QtWidgets import *
except ImportError:
    from PyQt4.QtGui import *
    from PyQt4.QtCore import *

from libs.utils import new_icon, label_validator, trimmed

BB = QDialogButtonBox


class LabelDialog(QDialog):

    def __init__(self, text="Enter object label", parent=None, list_item=None):
        super(LabelDialog, self).__init__(parent)
        
        self.delete_requested = False  # Flag to indicate delete was clicked

        self.edit = QLineEdit()
        self.edit.setText(text)
        self.edit.setValidator(label_validator())
        self.edit.editingFinished.connect(self.post_process)

        model = QStringListModel()
        model.setStringList(list_item)
        completer = QCompleter()
        completer.setModel(model)
        self.edit.setCompleter(completer)

        self.button_box = bb = BB(BB.Ok | BB.Cancel, Qt.Horizontal, self)
        bb.button(BB.Ok).setIcon(new_icon('done'))
        bb.button(BB.Cancel).setIcon(new_icon('undo'))
        
        # Add Delete button
        self.delete_button = bb.addButton('Delete 删除', BB.ActionRole)
        self.delete_button.setIcon(new_icon('delete'))
        self.delete_button.clicked.connect(self.delete_label)
        
        bb.accepted.connect(self.validate)
        bb.rejected.connect(self.reject)

        layout = QVBoxLayout()
        layout.addWidget(bb, alignment=Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self.edit)

        if list_item is not None and len(list_item) > 0:
            self.list_widget = QListWidget(self)
            for item in list_item:
                self.list_widget.addItem(item)
            self.list_widget.itemClicked.connect(self.list_item_click)
            self.list_widget.itemDoubleClicked.connect(self.list_item_double_click)
            # Install event filter for keyboard navigation
            self.list_widget.installEventFilter(self)
            layout.addWidget(self.list_widget)
        else:
            self.list_widget = None

        self.setLayout(layout)

    def eventFilter(self, obj, event):
        """Handle keyboard events for list widget"""
        if obj == self.list_widget and event.type() == QEvent.KeyPress:
            key = event.key()
            if key == Qt.Key_Return or key == Qt.Key_Enter:
                # Enter key on list item selects it and closes dialog
                current_item = self.list_widget.currentItem()
                if current_item:
                    self.list_item_click(current_item)
                    self.validate()
                    return True
        return super(LabelDialog, self).eventFilter(obj, event)

    def validate(self):
        if trimmed(self.edit.text()):
            self.accept()
    
    def delete_label(self):
        """Handle delete button click"""
        self.delete_requested = True
        self.reject()  # Close dialog

    def post_process(self):
        self.edit.setText(trimmed(self.edit.text()))

    def pop_up(self, text='', move=True):
        """
        Shows the dialog, setting the current text to `text`, and blocks the caller until the user has made a choice.
        If the user entered a label, that label is returned, otherwise (i.e. if the user cancelled the action)
        `None` is returned.
        """
        self.edit.setText(text)
        self.edit.setSelection(0, len(text))
        
        # If list widget exists and has items, focus on it first for keyboard navigation
        if self.list_widget and self.list_widget.count() > 0:
            # Find and select the current label in the list
            for i in range(self.list_widget.count()):
                if self.list_widget.item(i).text() == text:
                    self.list_widget.setCurrentRow(i)
                    break
            self.list_widget.setFocus(Qt.PopupFocusReason)
        else:
            self.edit.setFocus(Qt.PopupFocusReason)
            
        if move:
            cursor_pos = QCursor.pos()

            # move OK button below cursor
            btn = self.button_box.buttons()[0]
            self.adjustSize()
            btn.adjustSize()
            offset = btn.mapToGlobal(btn.pos()) - self.pos()
            offset += QPoint(btn.size().width() // 4, btn.size().height() // 2)
            cursor_pos.setX(max(0, cursor_pos.x() - offset.x()))
            cursor_pos.setY(max(0, cursor_pos.y() - offset.y()))

            parent_bottom_right = self.parentWidget().geometry()
            max_x = parent_bottom_right.x() + parent_bottom_right.width() - self.sizeHint().width()
            max_y = parent_bottom_right.y() + parent_bottom_right.height() - self.sizeHint().height()
            max_global = self.parentWidget().mapToGlobal(QPoint(max_x, max_y))
            if cursor_pos.x() > max_global.x():
                cursor_pos.setX(max_global.x())
            if cursor_pos.y() > max_global.y():
                cursor_pos.setY(max_global.y())
            self.move(cursor_pos)
        return trimmed(self.edit.text()) if self.exec_() else None

    def list_item_click(self, t_qlist_widget_item):
        text = trimmed(t_qlist_widget_item.text())
        self.edit.setText(text)

    def list_item_double_click(self, t_qlist_widget_item):
        self.list_item_click(t_qlist_widget_item)
        self.validate()
