#!/usr/bin/python
# -*- coding: utf-8 -*-


try:
    from PyQt5.QtGui import *
    from PyQt5.QtCore import *
except ImportError:
    from PyQt4.QtGui import *
    from PyQt4.QtCore import *

from libs.utils import distance
import sys

# ========== 可调整的配置参数 ==========
# 边框线粗细（数值越大线越粗，建议范围: 1.0 - 5.0）
DEFAULT_LINE_WIDTH = 1.0
# =====================================

DEFAULT_LINE_COLOR = QColor(0, 255, 0, 255)
DEFAULT_FILL_COLOR = QColor(255, 0, 0, 80)  # More transparent for better visibility
DEFAULT_SELECT_LINE_COLOR = QColor(255, 255, 255)
DEFAULT_SELECT_FILL_COLOR = QColor(0, 128, 255, 80)  # More transparent
DEFAULT_VERTEX_FILL_COLOR = QColor(0, 255, 0, 255)
DEFAULT_HVERTEX_FILL_COLOR = QColor(255, 0, 0)


class Shape(object):
    P_SQUARE, P_ROUND = range(2)

    MOVE_VERTEX, NEAR_VERTEX = range(2)

    # The following class variables influence the drawing
    # of _all_ shape objects.
    line_color = DEFAULT_LINE_COLOR
    fill_color = DEFAULT_FILL_COLOR
    select_line_color = DEFAULT_SELECT_LINE_COLOR
    select_fill_color = DEFAULT_SELECT_FILL_COLOR
    vertex_fill_color = DEFAULT_VERTEX_FILL_COLOR
    h_vertex_fill_color = DEFAULT_HVERTEX_FILL_COLOR
    point_type = P_ROUND
    point_size = 10  # Reduced from 16 for smaller hover points
    scale = 1.0
    label_font_size = 8

    def __init__(self, label=None, line_color=None, difficult=False, paint_label=False):
        self.label = label
        self.points = []
        self.fill = False
        self.selected = False
        self.difficult = difficult
        self.paint_label = paint_label

        self._highlight_index = None
        self._highlight_mode = self.NEAR_VERTEX
        self._highlight_settings = {
            self.NEAR_VERTEX: (4, self.P_ROUND),
            self.MOVE_VERTEX: (1.5, self.P_SQUARE),
        }

        self._closed = False

        if line_color is not None:
            # Override the class line_color attribute
            # with an object attribute. Currently this
            # is used for drawing the pending line a different color.
            self.line_color = line_color

    def close(self):
        self._closed = True

    def reach_max_points(self):
        if len(self.points) >= 4:
            return True
        return False

    def add_point(self, point):
        if not self.reach_max_points():
            self.points.append(point)

    def pop_point(self):
        if self.points:
            return self.points.pop()
        return None

    def is_closed(self):
        return self._closed

    def set_open(self):
        self._closed = False

    def paint(self, painter, instance_nav_mode=False):
        if self.points:
            color = self.select_line_color if self.selected else self.line_color
            pen = QPen(color)
            # In instance navigation mode, use 2x line width for selected shape
            line_width = DEFAULT_LINE_WIDTH
            if instance_nav_mode and self.selected:
                line_width *= 2
            # Try using integer sizes for smoother drawing(?)
            pen.setWidth(max(1, int(round(line_width / self.scale))))
            painter.setPen(pen)

            line_path = QPainterPath()
            vertex_path = QPainterPath()

            line_path.moveTo(self.points[0])
            # Uncommenting the following line will draw 2 paths
            # for the 1st vertex, and make it non-filled, which
            # may be desirable.
            # self.drawVertex(vertex_path, 0)

            for i, p in enumerate(self.points):
                line_path.lineTo(p)
                # Only draw vertices when highlighted (mouse hovering)
                if self._highlight_index is not None:
                    self.draw_vertex(vertex_path, i)
            if self.is_closed():
                line_path.lineTo(self.points[0])

            painter.drawPath(line_path)
            # Only draw and fill vertex path when highlighted
            if self._highlight_index is not None:
                painter.drawPath(vertex_path)
                painter.fillPath(vertex_path, self.vertex_fill_color)

            # Draw text at the top-left
            if self.paint_label:
                min_x = sys.maxsize
                min_y = sys.maxsize
                min_y_label = int(1.25 * self.label_font_size)
                for point in self.points:
                    min_x = min(min_x, point.x())
                    min_y = min(min_y, point.y())
                if min_x != sys.maxsize and min_y != sys.maxsize:
                    font = QFont()
                    font.setPointSize(self.label_font_size)
                    font.setBold(True)
                    painter.setFont(font)
                    if self.label is None:
                        self.label = ""
                    if min_y < min_y_label:
                        min_y += min_y_label
                    painter.drawText(int(min_x), int(min_y), self.label)

            # Fill with semi-transparent color when hovering or selected
            # In instance navigation mode, don't fill the selected shape
            if not (instance_nav_mode and self.selected):
                if self.fill or self._highlight_index is not None:
                    color = self.select_fill_color if self.selected else self.fill_color
                    painter.fillPath(line_path, color)

    def draw_vertex(self, path, i):
        d = self.point_size / self.scale
        shape = self.point_type
        point = self.points[i]
        if i == self._highlight_index:
            size, shape = self._highlight_settings[self._highlight_mode]
            d *= size
        if self._highlight_index is not None:
            self.vertex_fill_color = self.h_vertex_fill_color
        else:
            self.vertex_fill_color = Shape.vertex_fill_color
        if shape == self.P_SQUARE:
            path.addRect(point.x() - d / 2, point.y() - d / 2, d, d)
        elif shape == self.P_ROUND:
            path.addEllipse(point, d / 2.0, d / 2.0)
        else:
            assert False, "unsupported vertex shape"

    def nearest_vertex(self, point, epsilon):
        index = None
        for i, p in enumerate(self.points):
            dist = distance(p - point)
            if dist <= epsilon:
                index = i
                epsilon = dist
        return index

    def contains_point(self, point):
        # Use polygon containment check for better accuracy
        if len(self.points) < 4:
            return False
        
        # For rectangle, use simple bounding box check
        x_coords = [p.x() for p in self.points]
        y_coords = [p.y() for p in self.points]
        min_x, max_x = min(x_coords), max(x_coords)
        min_y, max_y = min(y_coords), max(y_coords)
        
        return min_x <= point.x() <= max_x and min_y <= point.y() <= max_y

    def make_path(self):
        path = QPainterPath(self.points[0])
        for p in self.points[1:]:
            path.lineTo(p)
        # Close the path for proper contains check
        if self.is_closed():
            path.closeSubpath()
        return path

    def bounding_rect(self):
        return self.make_path().boundingRect()

    def move_by(self, offset):
        self.points = [p + offset for p in self.points]

    def move_vertex_by(self, i, offset):
        self.points[i] = self.points[i] + offset

    def highlight_vertex(self, i, action):
        self._highlight_index = i
        self._highlight_mode = action

    def highlight_clear(self):
        self._highlight_index = None

    def copy(self):
        shape = Shape("%s" % self.label)
        shape.points = [p for p in self.points]
        shape.fill = self.fill
        shape.selected = self.selected
        shape._closed = self._closed
        if self.line_color != Shape.line_color:
            shape.line_color = self.line_color
        if self.fill_color != Shape.fill_color:
            shape.fill_color = self.fill_color
        shape.difficult = self.difficult
        return shape

    def __len__(self):
        return len(self.points)

    def __getitem__(self, key):
        return self.points[key]

    def __setitem__(self, key, value):
        self.points[key] = value
