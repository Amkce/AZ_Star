# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'form.ui'
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
from PySide6.QtWidgets import (QApplication, QCheckBox, QComboBox, QDateTimeEdit,
    QFormLayout, QGridLayout, QHBoxLayout, QHeaderView,
    QLabel, QLineEdit, QPushButton, QSizePolicy,
    QSlider, QTableWidget, QTableWidgetItem, QVBoxLayout,
    QWidget)

from map_widget import MapTrackWidget
from sky_widget import SkyTrackWidget

class Ui_Form(object):
    def setupUi(self, Form):
        if not Form.objectName():
            Form.setObjectName(u"Form")
        Form.resize(708, 495)
        self.gridLayout_2 = QGridLayout(Form)
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.horizontalLayout_5 = QHBoxLayout()
        self.horizontalLayout_5.setObjectName(u"horizontalLayout_5")
        self.formLayout = QFormLayout()
        self.formLayout.setObjectName(u"formLayout")
        self.label_connect_1 = QLabel(Form)
        self.label_connect_1.setObjectName(u"label_connect_1")

        self.formLayout.setWidget(0, QFormLayout.ItemRole.LabelRole, self.label_connect_1)

        self.pushButton_connect_1 = QPushButton(Form)
        self.pushButton_connect_1.setObjectName(u"pushButton_connect_1")

        self.formLayout.setWidget(0, QFormLayout.ItemRole.FieldRole, self.pushButton_connect_1)

        self.label_connect_2 = QLabel(Form)
        self.label_connect_2.setObjectName(u"label_connect_2")

        self.formLayout.setWidget(1, QFormLayout.ItemRole.LabelRole, self.label_connect_2)

        self.pushButton_connect_2 = QPushButton(Form)
        self.pushButton_connect_2.setObjectName(u"pushButton_connect_2")

        self.formLayout.setWidget(1, QFormLayout.ItemRole.FieldRole, self.pushButton_connect_2)

        self.lineEdit_longitude = QLineEdit(Form)
        self.lineEdit_longitude.setObjectName(u"lineEdit_longitude")

        self.formLayout.setWidget(2, QFormLayout.ItemRole.LabelRole, self.lineEdit_longitude)

        self.pushButton_longitude = QPushButton(Form)
        self.pushButton_longitude.setObjectName(u"pushButton_longitude")

        self.formLayout.setWidget(2, QFormLayout.ItemRole.FieldRole, self.pushButton_longitude)

        self.lineEdit_latitude = QLineEdit(Form)
        self.lineEdit_latitude.setObjectName(u"lineEdit_latitude")

        self.formLayout.setWidget(3, QFormLayout.ItemRole.LabelRole, self.lineEdit_latitude)

        self.pushButton_latitude = QPushButton(Form)
        self.pushButton_latitude.setObjectName(u"pushButton_latitude")

        self.formLayout.setWidget(3, QFormLayout.ItemRole.FieldRole, self.pushButton_latitude)

        self.label_longitude = QLabel(Form)
        self.label_longitude.setObjectName(u"label_longitude")

        self.formLayout.setWidget(4, QFormLayout.ItemRole.LabelRole, self.label_longitude)

        self.label_latitude = QLabel(Form)
        self.label_latitude.setObjectName(u"label_latitude")

        self.formLayout.setWidget(4, QFormLayout.ItemRole.FieldRole, self.label_latitude)

        self.lineEdit_threshold = QLineEdit(Form)
        self.lineEdit_threshold.setObjectName(u"lineEdit_threshold")

        self.formLayout.setWidget(5, QFormLayout.ItemRole.LabelRole, self.lineEdit_threshold)

        self.pushButton_threshold = QPushButton(Form)
        self.pushButton_threshold.setObjectName(u"pushButton_threshold")

        self.formLayout.setWidget(5, QFormLayout.ItemRole.FieldRole, self.pushButton_threshold)

        self.label_threshold = QLabel(Form)
        self.label_threshold.setObjectName(u"label_threshold")

        self.formLayout.setWidget(6, QFormLayout.ItemRole.LabelRole, self.label_threshold)

        self.label_timezone = QLabel(Form)
        self.label_timezone.setObjectName(u"label_timezone")

        self.formLayout.setWidget(6, QFormLayout.ItemRole.FieldRole, self.label_timezone)

        self.lineEdit_timezone = QLineEdit(Form)
        self.lineEdit_timezone.setObjectName(u"lineEdit_timezone")

        self.formLayout.setWidget(7, QFormLayout.ItemRole.LabelRole, self.lineEdit_timezone)

        self.pushButton_timezone = QPushButton(Form)
        self.pushButton_timezone.setObjectName(u"pushButton_timezone")

        self.formLayout.setWidget(7, QFormLayout.ItemRole.FieldRole, self.pushButton_timezone)

        self.label_clock = QLabel(Form)
        self.label_clock.setObjectName(u"label_clock")

        self.formLayout.setWidget(8, QFormLayout.ItemRole.LabelRole, self.label_clock)


        self.horizontalLayout_5.addLayout(self.formLayout)

        self.verticalLayout_6 = QVBoxLayout()
        self.verticalLayout_6.setObjectName(u"verticalLayout_6")
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(-1, 0, -1, -1)
        self.widget_sky = SkyTrackWidget(Form)
        self.widget_sky.setObjectName(u"widget_sky")

        self.horizontalLayout.addWidget(self.widget_sky)

        self.widget_map = MapTrackWidget(Form)
        self.widget_map.setObjectName(u"widget_map")

        self.horizontalLayout.addWidget(self.widget_map)


        self.verticalLayout_6.addLayout(self.horizontalLayout)

        self.horizontalLayout_4 = QHBoxLayout()
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.verticalLayout_4 = QVBoxLayout()
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.tableWidget = QTableWidget(Form)
        self.tableWidget.setObjectName(u"tableWidget")
        self.tableWidget.setMinimumSize(QSize(330, 0))

        self.verticalLayout_4.addWidget(self.tableWidget)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.checkBox_virtual = QCheckBox(Form)
        self.checkBox_virtual.setObjectName(u"checkBox_virtual")

        self.horizontalLayout_2.addWidget(self.checkBox_virtual)

        self.checkBox_pretrack = QCheckBox(Form)
        self.checkBox_pretrack.setObjectName(u"checkBox_pretrack")

        self.horizontalLayout_2.addWidget(self.checkBox_pretrack)

        self.label_time = QLabel(Form)
        self.label_time.setObjectName(u"label_time")

        self.horizontalLayout_2.addWidget(self.label_time)


        self.verticalLayout_4.addLayout(self.horizontalLayout_2)


        self.horizontalLayout_4.addLayout(self.verticalLayout_4)

        self.verticalLayout_5 = QVBoxLayout()
        self.verticalLayout_5.setObjectName(u"verticalLayout_5")
        self.gridLayout = QGridLayout()
        self.gridLayout.setObjectName(u"gridLayout")
        self.pushButton_up = QPushButton(Form)
        self.pushButton_up.setObjectName(u"pushButton_up")

        self.gridLayout.addWidget(self.pushButton_up, 0, 1, 1, 1)

        self.pushButton_left = QPushButton(Form)
        self.pushButton_left.setObjectName(u"pushButton_left")

        self.gridLayout.addWidget(self.pushButton_left, 1, 0, 1, 1)

        self.pushButton_right = QPushButton(Form)
        self.pushButton_right.setObjectName(u"pushButton_right")

        self.gridLayout.addWidget(self.pushButton_right, 1, 2, 1, 1)

        self.pushButton_down = QPushButton(Form)
        self.pushButton_down.setObjectName(u"pushButton_down")

        self.gridLayout.addWidget(self.pushButton_down, 2, 1, 1, 1)

        self.label_speed = QLabel(Form)
        self.label_speed.setObjectName(u"label_speed")

        self.gridLayout.addWidget(self.label_speed, 0, 0, 1, 1)

        self.pushButton_stop = QPushButton(Form)
        self.pushButton_stop.setObjectName(u"pushButton_stop")

        self.gridLayout.addWidget(self.pushButton_stop, 1, 1, 1, 1)


        self.verticalLayout_5.addLayout(self.gridLayout)

        self.horizontalSlider = QSlider(Form)
        self.horizontalSlider.setObjectName(u"horizontalSlider")
        self.horizontalSlider.setOrientation(Qt.Orientation.Horizontal)

        self.verticalLayout_5.addWidget(self.horizontalSlider)

        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.verticalLayout = QVBoxLayout()
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.label_tle = QLabel(Form)
        self.label_tle.setObjectName(u"label_tle")

        self.verticalLayout.addWidget(self.label_tle)

        self.label_tle2 = QLabel(Form)
        self.label_tle2.setObjectName(u"label_tle2")

        self.verticalLayout.addWidget(self.label_tle2)

        self.label_id = QLabel(Form)
        self.label_id.setObjectName(u"label_id")

        self.verticalLayout.addWidget(self.label_id)

        self.label_speed_star = QLabel(Form)
        self.label_speed_star.setObjectName(u"label_speed_star")

        self.verticalLayout.addWidget(self.label_speed_star)

        self.label_ra = QLabel(Form)
        self.label_ra.setObjectName(u"label_ra")

        self.verticalLayout.addWidget(self.label_ra)

        self.label_dec = QLabel(Form)
        self.label_dec.setObjectName(u"label_dec")

        self.verticalLayout.addWidget(self.label_dec)


        self.horizontalLayout_3.addLayout(self.verticalLayout)

        self.verticalLayout_2 = QVBoxLayout()
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.checkBox_ot_up = QCheckBox(Form)
        self.checkBox_ot_up.setObjectName(u"checkBox_ot_up")

        self.verticalLayout_2.addWidget(self.checkBox_ot_up)

        self.checkBox_ot_right = QCheckBox(Form)
        self.checkBox_ot_right.setObjectName(u"checkBox_ot_right")

        self.verticalLayout_2.addWidget(self.checkBox_ot_right)

        self.checkBox_up = QCheckBox(Form)
        self.checkBox_up.setObjectName(u"checkBox_up")

        self.verticalLayout_2.addWidget(self.checkBox_up)

        self.checkBox_down = QCheckBox(Form)
        self.checkBox_down.setObjectName(u"checkBox_down")

        self.verticalLayout_2.addWidget(self.checkBox_down)


        self.horizontalLayout_3.addLayout(self.verticalLayout_2)


        self.verticalLayout_5.addLayout(self.horizontalLayout_3)

        self.verticalLayout_3 = QVBoxLayout()
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.dateTimeEdit_start = QDateTimeEdit(Form)
        self.dateTimeEdit_start.setObjectName(u"dateTimeEdit_start")

        self.verticalLayout_3.addWidget(self.dateTimeEdit_start)

        self.dateTimeEdit_end = QDateTimeEdit(Form)
        self.dateTimeEdit_end.setObjectName(u"dateTimeEdit_end")

        self.verticalLayout_3.addWidget(self.dateTimeEdit_end)

        self.horizontalLayout_mag_limit = QHBoxLayout()
        self.horizontalLayout_mag_limit.setObjectName(u"horizontalLayout_mag_limit")
        self.label_mag_limit = QLabel(Form)
        self.label_mag_limit.setObjectName(u"label_mag_limit")

        self.horizontalLayout_mag_limit.addWidget(self.label_mag_limit)

        self.comboBox_mag_limit = QComboBox(Form)
        self.comboBox_mag_limit.addItem("")
        self.comboBox_mag_limit.addItem("")
        self.comboBox_mag_limit.addItem("")
        self.comboBox_mag_limit.addItem("")
        self.comboBox_mag_limit.addItem("")
        self.comboBox_mag_limit.setObjectName(u"comboBox_mag_limit")

        self.horizontalLayout_mag_limit.addWidget(self.comboBox_mag_limit)


        self.verticalLayout_3.addLayout(self.horizontalLayout_mag_limit)

        self.checkBox_fetch_dawn = QCheckBox(Form)
        self.checkBox_fetch_dawn.setObjectName(u"checkBox_fetch_dawn")

        self.verticalLayout_3.addWidget(self.checkBox_fetch_dawn)

        self.pushButton_seek = QPushButton(Form)
        self.pushButton_seek.setObjectName(u"pushButton_seek")

        self.verticalLayout_3.addWidget(self.pushButton_seek)

        self.lineEdit_local_tle1 = QLineEdit(Form)
        self.lineEdit_local_tle1.setObjectName(u"lineEdit_local_tle1")

        self.verticalLayout_3.addWidget(self.lineEdit_local_tle1)

        self.lineEdit_local_tle2 = QLineEdit(Form)
        self.lineEdit_local_tle2.setObjectName(u"lineEdit_local_tle2")

        self.verticalLayout_3.addWidget(self.lineEdit_local_tle2)

        self.pushButton_use_tle = QPushButton(Form)
        self.pushButton_use_tle.setObjectName(u"pushButton_use_tle")

        self.verticalLayout_3.addWidget(self.pushButton_use_tle)

        self.pushButton_stellarium = QPushButton(Form)
        self.pushButton_stellarium.setObjectName(u"pushButton_stellarium")

        self.verticalLayout_3.addWidget(self.pushButton_stellarium)


        self.verticalLayout_5.addLayout(self.verticalLayout_3)


        self.horizontalLayout_4.addLayout(self.verticalLayout_5)


        self.verticalLayout_6.addLayout(self.horizontalLayout_4)


        self.horizontalLayout_5.addLayout(self.verticalLayout_6)


        self.gridLayout_2.addLayout(self.horizontalLayout_5, 0, 0, 1, 1)


        self.retranslateUi(Form)

        QMetaObject.connectSlotsByName(Form)
    # setupUi

    def retranslateUi(self, Form):
        Form.setWindowTitle(QCoreApplication.translate("Form", u"Form", None))
        self.label_connect_1.setText(QCoreApplication.translate("Form", u"\u672a\u8fde\u63a5", None))
        self.pushButton_connect_1.setText(QCoreApplication.translate("Form", u"\u8fde\u63a5\u8d64\u9053\u4eea", None))
        self.label_connect_2.setText(QCoreApplication.translate("Form", u"\u672a\u8fde\u63a5", None))
        self.pushButton_connect_2.setText(QCoreApplication.translate("Form", u"\u8fde\u63a5\u76f8\u673a", None))
        self.pushButton_longitude.setText(QCoreApplication.translate("Form", u"\u8bbe\u7f6e\u7ecf\u5ea6", None))
        self.pushButton_latitude.setText(QCoreApplication.translate("Form", u"\u8bbe\u7f6e\u7eac\u5ea6", None))
        self.label_longitude.setText(QCoreApplication.translate("Form", u"\u7ecf\u5ea6\u672a\u8bbe\u7f6e", None))
        self.label_latitude.setText(QCoreApplication.translate("Form", u"\u7eac\u5ea6\u672a\u8bbe\u7f6e", None))
        self.lineEdit_threshold.setPlaceholderText(QCoreApplication.translate("Form", u"\u504f\u5dee\u9608\u503c\uff08\u5ea6\uff09", None))
        self.pushButton_threshold.setText(QCoreApplication.translate("Form", u"\u8bbe\u7f6e\u504f\u5dee\u9608\u503c", None))
        self.label_threshold.setText(QCoreApplication.translate("Form", u"\u504f\u5dee\u9608\u503c\u672a\u8bbe\u7f6e", None))
        self.label_timezone.setText(QCoreApplication.translate("Form", u"\u5f53\u524d\u65f6\u533a\uff1aUTC+08:00", None))
        self.lineEdit_timezone.setPlaceholderText(QCoreApplication.translate("Form", u"\u65f6\u533a\uff08\u5982 +8 / +08:00 / -5\uff09", None))
        self.pushButton_timezone.setText(QCoreApplication.translate("Form", u"\u8bbe\u7f6e\u65f6\u533a", None))
        self.label_clock.setText(QCoreApplication.translate("Form", u"\u5f53\u524d\u65f6\u95f4\uff1a----", None))
        self.checkBox_virtual.setText(QCoreApplication.translate("Form", u"\u6a21\u62df\u8ffd\u8e2a\u6a21\u5f0f", None))
        self.checkBox_pretrack.setText(QCoreApplication.translate("Form", u"\u9884\u5907\u8ddf\u8e2a\u6a21\u5f0f", None))
        self.label_time.setText(QCoreApplication.translate("Form", u"\u65f6\u95f4\u672a\u77e5", None))
        self.pushButton_up.setText(QCoreApplication.translate("Form", u"\u4e0a", None))
        self.pushButton_left.setText(QCoreApplication.translate("Form", u"\u5de6", None))
        self.pushButton_right.setText(QCoreApplication.translate("Form", u"\u53f3", None))
        self.pushButton_down.setText(QCoreApplication.translate("Form", u"\u4e0b", None))
        self.label_speed.setText(QCoreApplication.translate("Form", u"\u901f\u5ea6\u672a\u77e5", None))
        self.pushButton_stop.setText(QCoreApplication.translate("Form", u"\u505c\u6b62", None))
        self.label_tle.setText(QCoreApplication.translate("Form", u"TLE\u672a\u77e5", None))
        self.label_tle2.setText(QCoreApplication.translate("Form", u"TLE\u672a\u77e5", None))
        self.label_id.setText(QCoreApplication.translate("Form", u"\u536b\u661fID\u672a\u77e5", None))
        self.label_speed_star.setText(QCoreApplication.translate("Form", u"\u536b\u661f\u901f\u5ea6\u672a\u77e5", None))
        self.label_ra.setText(QCoreApplication.translate("Form", u"\u8d64\u7ecf\u672a\u77e5", None))
        self.label_dec.setText(QCoreApplication.translate("Form", u"\u8d64\u7eac\u672a\u77e5", None))
        self.checkBox_ot_up.setText(QCoreApplication.translate("Form", u"\u7ffb\u8f6c\u4e0a\u4e0bTLE", None))
        self.checkBox_ot_right.setText(QCoreApplication.translate("Form", u"\u7ffb\u8f6c\u5de6\u53f3TLE", None))
        self.checkBox_up.setText(QCoreApplication.translate("Form", u"\u7ffb\u8f6c\u4e0a\u4e0b\u901f\u5ea6", None))
        self.checkBox_down.setText(QCoreApplication.translate("Form", u"\u7ffb\u8f6c\u5de6\u53f3\u901f\u5ea6", None))
        self.label_mag_limit.setText(QCoreApplication.translate("Form", u"\u6700\u4f4e\u4eae\u5ea6", None))
        self.comboBox_mag_limit.setItemText(0, QCoreApplication.translate("Form", u"3.0", None))
        self.comboBox_mag_limit.setItemText(1, QCoreApplication.translate("Form", u"3.5", None))
        self.comboBox_mag_limit.setItemText(2, QCoreApplication.translate("Form", u"4.0", None))
        self.comboBox_mag_limit.setItemText(3, QCoreApplication.translate("Form", u"4.5", None))
        self.comboBox_mag_limit.setItemText(4, QCoreApplication.translate("Form", u"5.0", None))

        self.checkBox_fetch_dawn.setText(QCoreApplication.translate("Form", u"\u51cc\u6668\u6a21\u5f0f\uff08\u9ed8\u8ba4\u508d\u665a\uff09", None))
        self.pushButton_seek.setText(QCoreApplication.translate("Form", u"\u5f00\u59cb\u641c\u7d22", None))
        self.lineEdit_local_tle1.setPlaceholderText(QCoreApplication.translate("Form", u"\u672c\u5730TLE\u7b2c\u4e00\u884c", None))
        self.lineEdit_local_tle2.setPlaceholderText(QCoreApplication.translate("Form", u"\u672c\u5730TLE\u7b2c\u4e8c\u884c", None))
        self.pushButton_use_tle.setText(QCoreApplication.translate("Form", u"\u4f7f\u7528\u672c\u5730TLE\u8ddf\u8e2a", None))
        self.pushButton_stellarium.setText(QCoreApplication.translate("Form", u"Stellarium \u6a21\u62df", None))
    # retranslateUi

