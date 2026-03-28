# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'stellarium_panel.ui'
##
## Created by: Qt User Interface Compiler version 6.10.1
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QAbstractItemView, QApplication, QComboBox, QDialog,
    QFormLayout, QHBoxLayout, QHeaderView, QLabel,
    QPlainTextEdit, QPushButton, QSizePolicy, QSplitter,
    QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget)

class Ui_StellariumDialog(object):
    def setupUi(self, StellariumDialog):
        if not StellariumDialog.objectName():
            StellariumDialog.setObjectName(u"StellariumDialog")
        StellariumDialog.resize(1060, 620)
        self.verticalLayout_root = QVBoxLayout(StellariumDialog)
        self.verticalLayout_root.setObjectName(u"verticalLayout_root")
        self.splitter_main = QSplitter(StellariumDialog)
        self.splitter_main.setObjectName(u"splitter_main")
        self.splitter_main.setOrientation(Qt.Orientation.Horizontal)
        self.widget_left = QWidget(self.splitter_main)
        self.widget_left.setObjectName(u"widget_left")
        self.verticalLayout_left = QVBoxLayout(self.widget_left)
        self.verticalLayout_left.setObjectName(u"verticalLayout_left")
        self.verticalLayout_left.setContentsMargins(0, 0, 0, 0)
        self.label_targets_title = QLabel(self.widget_left)
        self.label_targets_title.setObjectName(u"label_targets_title")

        self.verticalLayout_left.addWidget(self.label_targets_title)

        self.table_targets = QTableWidget(self.widget_left)
        if (self.table_targets.columnCount() < 4):
            self.table_targets.setColumnCount(4)
        __qtablewidgetitem = QTableWidgetItem()
        self.table_targets.setHorizontalHeaderItem(0, __qtablewidgetitem)
        __qtablewidgetitem1 = QTableWidgetItem()
        self.table_targets.setHorizontalHeaderItem(1, __qtablewidgetitem1)
        __qtablewidgetitem2 = QTableWidgetItem()
        self.table_targets.setHorizontalHeaderItem(2, __qtablewidgetitem2)
        __qtablewidgetitem3 = QTableWidgetItem()
        self.table_targets.setHorizontalHeaderItem(3, __qtablewidgetitem3)
        self.table_targets.setObjectName(u"table_targets")
        self.table_targets.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table_targets.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table_targets.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table_targets.setWordWrap(False)

        self.verticalLayout_left.addWidget(self.table_targets)

        self.splitter_main.addWidget(self.widget_left)
        self.widget_right = QWidget(self.splitter_main)
        self.widget_right.setObjectName(u"widget_right")
        self.verticalLayout_right = QVBoxLayout(self.widget_right)
        self.verticalLayout_right.setObjectName(u"verticalLayout_right")
        self.verticalLayout_right.setContentsMargins(0, 0, 0, 0)
        self.formLayout_info = QFormLayout()
        self.formLayout_info.setObjectName(u"formLayout_info")
        self.label_status_title = QLabel(self.widget_right)
        self.label_status_title.setObjectName(u"label_status_title")

        self.formLayout_info.setWidget(0, QFormLayout.ItemRole.LabelRole, self.label_status_title)

        self.label_status = QLabel(self.widget_right)
        self.label_status.setObjectName(u"label_status")

        self.formLayout_info.setWidget(0, QFormLayout.ItemRole.FieldRole, self.label_status)

        self.label_name_title = QLabel(self.widget_right)
        self.label_name_title.setObjectName(u"label_name_title")

        self.formLayout_info.setWidget(1, QFormLayout.ItemRole.LabelRole, self.label_name_title)

        self.label_name = QLabel(self.widget_right)
        self.label_name.setObjectName(u"label_name")

        self.formLayout_info.setWidget(1, QFormLayout.ItemRole.FieldRole, self.label_name)

        self.label_stellarium_name_title = QLabel(self.widget_right)
        self.label_stellarium_name_title.setObjectName(u"label_stellarium_name_title")

        self.formLayout_info.setWidget(2, QFormLayout.ItemRole.LabelRole, self.label_stellarium_name_title)

        self.label_stellarium_name = QLabel(self.widget_right)
        self.label_stellarium_name.setObjectName(u"label_stellarium_name")

        self.formLayout_info.setWidget(2, QFormLayout.ItemRole.FieldRole, self.label_stellarium_name)

        self.label_sat_id_title = QLabel(self.widget_right)
        self.label_sat_id_title.setObjectName(u"label_sat_id_title")

        self.formLayout_info.setWidget(3, QFormLayout.ItemRole.LabelRole, self.label_sat_id_title)

        self.label_sat_id = QLabel(self.widget_right)
        self.label_sat_id.setObjectName(u"label_sat_id")

        self.formLayout_info.setWidget(3, QFormLayout.ItemRole.FieldRole, self.label_sat_id)

        self.label_mag_title = QLabel(self.widget_right)
        self.label_mag_title.setObjectName(u"label_mag_title")

        self.formLayout_info.setWidget(4, QFormLayout.ItemRole.LabelRole, self.label_mag_title)

        self.label_mag = QLabel(self.widget_right)
        self.label_mag.setObjectName(u"label_mag")

        self.formLayout_info.setWidget(4, QFormLayout.ItemRole.FieldRole, self.label_mag)

        self.label_window_title = QLabel(self.widget_right)
        self.label_window_title.setObjectName(u"label_window_title")

        self.formLayout_info.setWidget(5, QFormLayout.ItemRole.LabelRole, self.label_window_title)

        self.label_window = QLabel(self.widget_right)
        self.label_window.setObjectName(u"label_window")

        self.formLayout_info.setWidget(5, QFormLayout.ItemRole.FieldRole, self.label_window)

        self.label_location_title = QLabel(self.widget_right)
        self.label_location_title.setObjectName(u"label_location_title")

        self.formLayout_info.setWidget(6, QFormLayout.ItemRole.LabelRole, self.label_location_title)

        self.label_location = QLabel(self.widget_right)
        self.label_location.setObjectName(u"label_location")

        self.formLayout_info.setWidget(6, QFormLayout.ItemRole.FieldRole, self.label_location)


        self.verticalLayout_right.addLayout(self.formLayout_info)

        self.horizontalLayout_row1 = QHBoxLayout()
        self.horizontalLayout_row1.setObjectName(u"horizontalLayout_row1")
        self.button_launch = QPushButton(self.widget_right)
        self.button_launch.setObjectName(u"button_launch")

        self.horizontalLayout_row1.addWidget(self.button_launch)

        self.button_check = QPushButton(self.widget_right)
        self.button_check.setObjectName(u"button_check")

        self.horizontalLayout_row1.addWidget(self.button_check)

        self.button_one_click = QPushButton(self.widget_right)
        self.button_one_click.setObjectName(u"button_one_click")

        self.horizontalLayout_row1.addWidget(self.button_one_click)


        self.verticalLayout_right.addLayout(self.horizontalLayout_row1)

        self.horizontalLayout_row2 = QHBoxLayout()
        self.horizontalLayout_row2.setObjectName(u"horizontalLayout_row2")
        self.button_write_sat = QPushButton(self.widget_right)
        self.button_write_sat.setObjectName(u"button_write_sat")

        self.horizontalLayout_row2.addWidget(self.button_write_sat)

        self.button_sync_location = QPushButton(self.widget_right)
        self.button_sync_location.setObjectName(u"button_sync_location")

        self.horizontalLayout_row2.addWidget(self.button_sync_location)

        self.button_sync_start = QPushButton(self.widget_right)
        self.button_sync_start.setObjectName(u"button_sync_start")

        self.horizontalLayout_row2.addWidget(self.button_sync_start)

        self.button_focus = QPushButton(self.widget_right)
        self.button_focus.setObjectName(u"button_focus")

        self.horizontalLayout_row2.addWidget(self.button_focus)


        self.verticalLayout_right.addLayout(self.horizontalLayout_row2)

        self.horizontalLayout_row3 = QHBoxLayout()
        self.horizontalLayout_row3.setObjectName(u"horizontalLayout_row3")
        self.label_rate_title = QLabel(self.widget_right)
        self.label_rate_title.setObjectName(u"label_rate_title")

        self.horizontalLayout_row3.addWidget(self.label_rate_title)

        self.combo_rate = QComboBox(self.widget_right)
        self.combo_rate.addItem("")
        self.combo_rate.addItem("")
        self.combo_rate.addItem("")
        self.combo_rate.addItem("")
        self.combo_rate.addItem("")
        self.combo_rate.setObjectName(u"combo_rate")

        self.horizontalLayout_row3.addWidget(self.combo_rate)

        self.button_play = QPushButton(self.widget_right)
        self.button_play.setObjectName(u"button_play")

        self.horizontalLayout_row3.addWidget(self.button_play)

        self.button_pause = QPushButton(self.widget_right)
        self.button_pause.setObjectName(u"button_pause")

        self.horizontalLayout_row3.addWidget(self.button_pause)

        self.button_realtime = QPushButton(self.widget_right)
        self.button_realtime.setObjectName(u"button_realtime")

        self.horizontalLayout_row3.addWidget(self.button_realtime)


        self.verticalLayout_right.addLayout(self.horizontalLayout_row3)

        self.text_tle = QPlainTextEdit(self.widget_right)
        self.text_tle.setObjectName(u"text_tle")
        self.text_tle.setReadOnly(True)

        self.verticalLayout_right.addWidget(self.text_tle)

        self.text_log = QPlainTextEdit(self.widget_right)
        self.text_log.setObjectName(u"text_log")
        self.text_log.setReadOnly(True)

        self.verticalLayout_right.addWidget(self.text_log)

        self.splitter_main.addWidget(self.widget_right)

        self.verticalLayout_root.addWidget(self.splitter_main)


        self.retranslateUi(StellariumDialog)

        QMetaObject.connectSlotsByName(StellariumDialog)
    # setupUi

    def retranslateUi(self, StellariumDialog):
        StellariumDialog.setWindowTitle(QCoreApplication.translate("StellariumDialog", u"Stellarium \u8054\u52a8", None))
        self.label_targets_title.setText(QCoreApplication.translate("StellariumDialog", u"\u5f53\u524d\u5df2\u6293\u53d6\u536b\u661f", None))
        ___qtablewidgetitem = self.table_targets.horizontalHeaderItem(0)
        ___qtablewidgetitem.setText(QCoreApplication.translate("StellariumDialog", u"\u540d\u79f0", None));
        ___qtablewidgetitem1 = self.table_targets.horizontalHeaderItem(1)
        ___qtablewidgetitem1.setText(QCoreApplication.translate("StellariumDialog", u"\u661f\u7b49", None));
        ___qtablewidgetitem2 = self.table_targets.horizontalHeaderItem(2)
        ___qtablewidgetitem2.setText(QCoreApplication.translate("StellariumDialog", u"\u8d77\u59cb\u65f6\u95f4", None));
        ___qtablewidgetitem3 = self.table_targets.horizontalHeaderItem(3)
        ___qtablewidgetitem3.setText(QCoreApplication.translate("StellariumDialog", u"\u7ed3\u675f\u65f6\u95f4", None));
        self.label_status_title.setText(QCoreApplication.translate("StellariumDialog", u"\u8fde\u63a5\u72b6\u6001", None))
        self.label_status.setText(QCoreApplication.translate("StellariumDialog", u"\u8fde\u63a5\u72b6\u6001\uff1a\u672a\u68c0\u67e5", None))
        self.label_name_title.setText(QCoreApplication.translate("StellariumDialog", u"\u5f53\u524d\u536b\u661f", None))
        self.label_name.setText(QCoreApplication.translate("StellariumDialog", u"\u672a\u9009\u62e9", None))
        self.label_stellarium_name_title.setText(QCoreApplication.translate("StellariumDialog", u"Stellarium \u540d\u79f0", None))
        self.label_stellarium_name.setText(QCoreApplication.translate("StellariumDialog", u"\u672a\u9009\u62e9", None))
        self.label_sat_id_title.setText(QCoreApplication.translate("StellariumDialog", u"NORAD ID", None))
        self.label_sat_id.setText(QCoreApplication.translate("StellariumDialog", u"\u672a\u9009\u62e9", None))
        self.label_mag_title.setText(QCoreApplication.translate("StellariumDialog", u"\u661f\u7b49", None))
        self.label_mag.setText(QCoreApplication.translate("StellariumDialog", u"\u672a\u9009\u62e9", None))
        self.label_window_title.setText(QCoreApplication.translate("StellariumDialog", u"\u7a97\u53e3\u65f6\u95f4", None))
        self.label_window.setText(QCoreApplication.translate("StellariumDialog", u"\u672a\u9009\u62e9", None))
        self.label_location_title.setText(QCoreApplication.translate("StellariumDialog", u"\u89c2\u6d4b\u5730", None))
        self.label_location.setText(QCoreApplication.translate("StellariumDialog", u"\u672a\u8bbe\u7f6e", None))
        self.button_launch.setText(QCoreApplication.translate("StellariumDialog", u"\u542f\u52a8 Stellarium", None))
        self.button_check.setText(QCoreApplication.translate("StellariumDialog", u"\u68c0\u67e5\u8fde\u63a5", None))
        self.button_one_click.setText(QCoreApplication.translate("StellariumDialog", u"\u795e\u79d8\u8d85\u7edd\u4e00\u952e\u8bbe\u7f6e", None))
        self.button_write_sat.setText(QCoreApplication.translate("StellariumDialog", u"\u5199\u5165/\u66f4\u65b0\u536b\u661f", None))
        self.button_sync_location.setText(QCoreApplication.translate("StellariumDialog", u"\u540c\u6b65\u89c2\u6d4b\u5730", None))
        self.button_sync_start.setText(QCoreApplication.translate("StellariumDialog", u"\u8df3\u5230\u8d77\u59cb\u65f6\u523b", None))
        self.button_focus.setText(QCoreApplication.translate("StellariumDialog", u"\u5b9a\u4f4d\u5230\u536b\u661f", None))
        self.label_rate_title.setText(QCoreApplication.translate("StellariumDialog", u"\u56de\u653e\u500d\u7387", None))
        self.combo_rate.setItemText(0, QCoreApplication.translate("StellariumDialog", u"1x", None))
        self.combo_rate.setItemText(1, QCoreApplication.translate("StellariumDialog", u"10x", None))
        self.combo_rate.setItemText(2, QCoreApplication.translate("StellariumDialog", u"30x", None))
        self.combo_rate.setItemText(3, QCoreApplication.translate("StellariumDialog", u"60x", None))
        self.combo_rate.setItemText(4, QCoreApplication.translate("StellariumDialog", u"120x", None))

        self.button_play.setText(QCoreApplication.translate("StellariumDialog", u"\u5f00\u59cb\u6a21\u62df", None))
        self.button_pause.setText(QCoreApplication.translate("StellariumDialog", u"\u6682\u505c\u6a21\u62df", None))
        self.button_realtime.setText(QCoreApplication.translate("StellariumDialog", u"\u6062\u590d\u5b9e\u65f6", None))
        self.text_tle.setPlaceholderText(QCoreApplication.translate("StellariumDialog", u"TLE", None))
        self.text_log.setPlaceholderText(QCoreApplication.translate("StellariumDialog", u"\u8054\u52a8\u65e5\u5fd7", None))
    # retranslateUi

