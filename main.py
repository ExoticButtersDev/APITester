import sys
import json
import requests
import queue
import threading
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QLineEdit, QPushButton,
                             QTabWidget, QTableWidget, QTableWidgetItem, QRadioButton, QButtonGroup, QTextEdit,
                             QHeaderView, QMessageBox, QStackedWidget, QLabel, QFileDialog, QDialog, QDialogButtonBox)
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtCore import Qt, QUrl, QTimer
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
import tempfile
import os

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

class JsonDlg(QDialog):
    def __init__(self, parent=None, is_arr=False):
        super().__init__(parent)
        self.setWindowTitle("Edit JSON")
        self.is_arr = is_arr
        self._setup_ui()
        self.setWindowIcon(QIcon(resource_path("icon.ico")))

    def _setup_ui(self):
        lyt = QVBoxLayout()
        self.tbl = QTableWidget()
        self.tbl.setColumnCount(3 if not self.is_arr else 2)
        self.tbl.setHorizontalHeaderLabels(["Key", "Value", "Type"] if not self.is_arr else ["Value", "Type"])
        self.tbl.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        lyt.addWidget(self.tbl)
        btn_lyt = QHBoxLayout()
        add_btn = QPushButton("Add Row")
        add_btn.clicked.connect(self._add_row)
        rm_btn = QPushButton("Remove Selected")
        rm_btn.clicked.connect(self._rm_row)
        btn_lyt.addWidget(add_btn)
        btn_lyt.addWidget(rm_btn)
        lyt.addLayout(btn_lyt)
        btn_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btn_box.accepted.connect(self.accept)
        btn_box.rejected.connect(self.reject)
        lyt.addWidget(btn_box)
        self.setLayout(lyt)
        self._add_row()

    def _add_row(self):
        row = self.tbl.rowCount()
        self.tbl.insertRow(row)
        if not self.is_arr:
            self.tbl.setItem(row, 0, QTableWidgetItem(""))
        self.tbl.setItem(row, 1 if not self.is_arr else 0, QTableWidgetItem(""))
        type_cb = QComboBox()
        type_cb.addItems(["string", "number", "boolean", "object", "array"])
        self.tbl.setCellWidget(row, 2 if not self.is_arr else 1, type_cb)

    def _rm_row(self):
        sel = self.tbl.selectedItems()
        if sel and self.tbl.rowCount() > 1:
            row = sel[0].row()
            self.tbl.removeRow(row)

    def get_json(self):
        return self._build_arr() if self.is_arr else self._build_obj()

    def _build_obj(self):
        obj = {}
        for row in range(self.tbl.rowCount()):
            key_item = self.tbl.item(row, 0)
            val_item = self.tbl.item(row, 1)
            type_cb = self.tbl.cellWidget(row, 2)
            if key_item and val_item and type_cb:
                key = key_item.text().strip()
                val = val_item.text().strip()
                typ = type_cb.currentText()
                if key:
                    try:
                        obj[key] = self._parse_val(val, typ)
                    except ValueError as e:
                        raise ValueError(f"Invalid value for '{key}': {e}")
        return obj

    def _build_arr(self):
        arr = []
        for row in range(self.tbl.rowCount()):
            val_item = self.tbl.item(row, 0)
            type_cb = self.tbl.cellWidget(row, 1)
            if val_item and type_cb:
                val = val_item.text().strip()
                typ = type_cb.currentText()
                try:
                    arr.append(self._parse_val(val, typ))
                except ValueError as e:
                    raise ValueError(f"Invalid array value: {e}")
        return arr

    def _parse_val(self, val, typ):
        if not val and typ not in ["object", "array"]:
            return ""
        if typ == "string":
            return val
        elif typ == "number":
            try:
                return int(val) if '.' not in val else float(val)
            except ValueError:
                raise ValueError(f"'{val}' not a number")
        elif typ == "boolean":
            if val.lower() in ["true", "false"]:
                return val.lower() == "true"
            raise ValueError(f"'{val}' not boolean")
        elif typ in ["object", "array"]:
            return json.loads(val) if val else ({} if typ == "object" else [])
        return val

class Tstr(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("API Tester")
        self.setWindowIcon(QIcon(resource_path("icon.ico")))
        self.resize(800, 600)
        self.q = queue.Queue()
        self.tmr = QTimer()
        self.tmr.timeout.connect(self._chk_q)
        self.resp = None
        self.audio = None
        self.plr = QMediaPlayer()
        self.tmp = None
        self._setup_ui()

    def _setup_ui(self):
        wgt = QWidget()
        main_lyt = QVBoxLayout()
        top_lyt = QHBoxLayout()
        self.mtd = QComboBox()
        self.mtd.addItems(["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"])
        top_lyt.addWidget(self.mtd, 1)
        self.url = QLineEdit()
        self.url.setPlaceholderText("Enter URL")
        top_lyt.addWidget(self.url, 4)
        self.send_btn = QPushButton("Send")
        self.send_btn.clicked.connect(self._send_req)
        top_lyt.addWidget(self.send_btn, 1)
        main_lyt.addLayout(top_lyt)
        self.tabs = QTabWidget()
        main_lyt.addWidget(self.tabs, 2)
        self._setup_hdr_tab()
        self._setup_bdy_tab()
        self.resp_tabs = QTabWidget()
        main_lyt.addWidget(self.resp_tabs, 3)
        self._setup_resp_tabs()
        wgt.setLayout(main_lyt)
        self.setCentralWidget(wgt)
        self.statusBar().showMessage("Ready")

    def _setup_hdr_tab(self):
        hdr_tab = QWidget()
        hdr_lyt = QVBoxLayout()
        hdr_top = QHBoxLayout()
        self.common_hdr = QComboBox()
        self.common_hdr.addItem("Select header")
        self.common_hdr.addItems(["Content-Type", "Accept", "Authorization", "User-Agent", "Cache-Control"])
        hdr_top.addWidget(self.common_hdr)
        self.add_sel_btn = QPushButton("Add Selected")
        self.add_sel_btn.clicked.connect(self._add_sel_hdr)
        hdr_top.addWidget(self.add_sel_btn)
        self.add_cust_btn = QPushButton("Add Custom")
        self.add_cust_btn.clicked.connect(self._add_cust_hdr)
        hdr_top.addWidget(self.add_cust_btn)
        hdr_lyt.addLayout(hdr_top)
        self.hdr_tbl = QTableWidget()
        self.hdr_tbl.setColumnCount(2)
        self.hdr_tbl.setHorizontalHeaderLabels(["Key", "Value"])
        self.hdr_tbl.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        hdr_lyt.addWidget(self.hdr_tbl)
        hdr_tab.setLayout(hdr_lyt)
        self.tabs.addTab(hdr_tab, "Headers")

    def _setup_bdy_tab(self):
        bdy_tab = QWidget()
        bdy_lyt = QVBoxLayout()
        self.bdy_grp = QButtonGroup()
        self.no_bdy = QRadioButton("No Body")
        self.txt_bdy = QRadioButton("Text")
        self.json_bdy = QRadioButton("JSON")
        self.bdy_grp.addButton(self.no_bdy, 0)
        self.bdy_grp.addButton(self.txt_bdy, 1)
        self.bdy_grp.addButton(self.json_bdy, 2)
        self.no_bdy.setChecked(True)
        self.bdy_grp.buttonClicked.connect(self._on_bdy_chg)
        bdy_lyt.addWidget(self.no_bdy)
        bdy_lyt.addWidget(self.txt_bdy)
        bdy_lyt.addWidget(self.json_bdy)
        self.bdy_stk = QStackedWidget()
        self.empty = QWidget()
        self.txt_edt = QTextEdit()
        self.txt_edt.setPlaceholderText("Enter text body")
        json_wgt = QWidget()
        json_lyt = QVBoxLayout()
        self.json_tbl = QTableWidget()
        self.json_tbl.setColumnCount(4)
        self.json_tbl.setHorizontalHeaderLabels(["Key", "Value", "Type", "Edit"])
        self.json_tbl.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        json_lyt.addWidget(self.json_tbl)
        json_btns = QHBoxLayout()
        add_btn = QPushButton("Add Row")
        add_btn.clicked.connect(self._add_json_row)
        rm_btn = QPushButton("Remove Selected")
        rm_btn.clicked.connect(self._rm_json_row)
        json_btns.addWidget(add_btn)
        json_btns.addWidget(rm_btn)
        json_lyt.addLayout(json_btns)
        json_wgt.setLayout(json_lyt)
        self.bdy_stk.addWidget(self.empty)
        self.bdy_stk.addWidget(self.txt_edt)
        self.bdy_stk.addWidget(json_wgt)
        bdy_lyt.addWidget(self.bdy_stk)
        bdy_tab.setLayout(bdy_lyt)
        self.tabs.addTab(bdy_tab, "Body")

    def _setup_resp_tabs(self):
        txt_tab = QWidget()
        txt_lyt = QVBoxLayout()
        self.resp_txt = QTextEdit()
        self.resp_txt.setReadOnly(True)
        self.resp_txt.setPlaceholderText("Text response")
        txt_lyt.addWidget(self.resp_txt)
        txt_tab.setLayout(txt_lyt)
        self.resp_tabs.addTab(txt_tab, "Text")
        img_tab = QWidget()
        img_lyt = QVBoxLayout()
        self.img_lbl = QLabel("No image")
        self.img_lbl.setAlignment(Qt.AlignCenter)
        img_lyt.addWidget(self.img_lbl)
        img_tab.setLayout(img_lyt)
        self.resp_tabs.addTab(img_tab, "Image")
        aud_tab = QWidget()
        aud_lyt = QVBoxLayout()
        self.play_btn = QPushButton("Play")
        self.play_btn.clicked.connect(self._play_aud)
        self.stop_btn = QPushButton("Stop")
        self.stop_btn.clicked.connect(self._stop_aud)
        aud_lyt.addWidget(self.play_btn)
        aud_lyt.addWidget(self.stop_btn)
        aud_tab.setLayout(aud_lyt)
        self.resp_tabs.addTab(aud_tab, "Audio")
        file_tab = QWidget()
        file_lyt = QVBoxLayout()
        self.save_btn = QPushButton("Save File")
        self.save_btn.clicked.connect(self._save_file)
        file_lyt.addWidget(self.save_btn)
        file_tab.setLayout(file_lyt)
        self.resp_tabs.addTab(file_tab, "File")
        dbg_tab = QWidget()
        dbg_lyt = QVBoxLayout()
        self.dbg_txt = QTextEdit()
        self.dbg_txt.setReadOnly(True)
        self.dbg_txt.setPlaceholderText("Debug info")
        dbg_lyt.addWidget(self.dbg_txt)
        dbg_tab.setLayout(dbg_lyt)
        self.resp_tabs.addTab(dbg_tab, "Debug")

    def _add_sel_hdr(self):
        sel = self.common_hdr.currentText()
        if sel != "Select header":
            self._add_hdr_row(sel, "")

    def _add_cust_hdr(self):
        self._add_hdr_row("", "")

    def _add_hdr_row(self, key, val):
        row = self.hdr_tbl.rowCount()
        self.hdr_tbl.insertRow(row)
        self.hdr_tbl.setItem(row, 0, QTableWidgetItem(key))
        self.hdr_tbl.setItem(row, 1, QTableWidgetItem(val))

    def _on_bdy_chg(self, btn):
        self.bdy_stk.setCurrentIndex(self.bdy_grp.id(btn))

    def _add_json_row(self):
        row = self.json_tbl.rowCount()
        self.json_tbl.insertRow(row)
        self.json_tbl.setItem(row, 0, QTableWidgetItem(""))
        self.json_tbl.setItem(row, 1, QTableWidgetItem(""))
        type_cb = QComboBox()
        type_cb.addItems(["string", "number", "boolean", "object", "array"])
        self.json_tbl.setCellWidget(row, 2, type_cb)
        edt_btn = QPushButton("Edit")
        edt_btn.clicked.connect(lambda _, r=row: self._edt_json(r))
        self.json_tbl.setCellWidget(row, 3, edt_btn)

    def _rm_json_row(self):
        sel = self.json_tbl.selectedItems()
        if sel and self.json_tbl.rowCount() > 1:
            row = sel[0].row()
            self.json_tbl.removeRow(row)

    def _edt_json(self, row):
        type_cb = self.json_tbl.cellWidget(row, 2)
        typ = type_cb.currentText()
        if typ in ["object", "array"]:
            dlg = JsonDlg(self, is_arr=(typ == "array"))
            if dlg.exec_():
                nested = dlg.get_json()
                self.json_tbl.item(row, 1).setText(json.dumps(nested, separators=(',', ':')))

    def _send_req(self):
        mtd = self.mtd.currentText()
        url = self.url.text().strip()
        if not url:
            QMessageBox.warning(self, "Error", "Enter a URL")
            return
        hdrs = self._get_hdrs()
        kwargs = self._prep_bdy()
        if kwargs is None:
            return
        self.send_btn.setEnabled(False)
        self.statusBar().showMessage("Sending...")
        def req_fn():
            try:
                resp = requests.request(mtd, url, headers=hdrs, timeout=10, **kwargs)
                self.q.put(('resp', resp))
            except requests.exceptions.RequestException as e:
                self.q.put(('err', str(e)))
        threading.Thread(target=req_fn).start()
        self.tmr.start(100)

    def _get_hdrs(self):
        hdrs = {}
        for row in range(self.hdr_tbl.rowCount()):
            key_item = self.hdr_tbl.item(row, 0)
            val_item = self.hdr_tbl.item(row, 1)
            if key_item and val_item:
                key = key_item.text().strip()
                val = val_item.text().strip()
                if key:
                    hdrs[key] = val
        return hdrs

    def _prep_bdy(self):
        bdy_typ = self.bdy_grp.checkedId()
        if bdy_typ == 0:
            return {}
        elif bdy_typ == 1:
            bdy = self.txt_edt.toPlainText().strip()
            return {'data': bdy} if bdy else {}
        elif bdy_typ == 2:
            try:
                json_obj = self._build_json()
                return {'json': json_obj} if json_obj else {}
            except ValueError as e:
                QMessageBox.warning(self, "Error", str(e))
                return None

    def _chk_q(self):
        if not self.q.empty():
            typ, res = self.q.get()
            if typ == 'resp':
                self._on_req_done(res)
            else:
                self._on_req_err(res)
            self.tmr.stop()
            self.send_btn.setEnabled(True)

    def _on_req_done(self, resp):
        self.resp = resp
        ct = resp.headers.get('Content-Type', '').lower()
        disp = resp.headers.get('Content-Disposition', '').lower()
        if 'attachment' in disp or 'application/octet-stream' in ct:
            self._handle_file()
        elif 'image' in ct:
            self._handle_img()
        elif 'audio' in ct:
            self._handle_aud()
        else:
            self._handle_txt()
        self._show_dbg()
        self.statusBar().showMessage(f"Response: {resp.status_code} {resp.reason}")

    def _on_req_err(self, err):
        self.resp_txt.setPlainText(f"Error: {err}")
        self.resp_tabs.setCurrentWidget(self.resp_txt.parentWidget())
        self.statusBar().showMessage(f"Error: {err}")

    def _handle_txt(self):
        txt = self.resp.text
        if 'application/json' in self.resp.headers.get('Content-Type', '').lower():
            try:
                json_obj = self.resp.json()
                txt = json.dumps(json_obj, indent=2)
            except ValueError:
                pass
        self.resp_txt.setPlainText(txt)
        self.resp_tabs.setCurrentWidget(self.resp_txt.parentWidget())

    def _handle_img(self):
        pix = QPixmap()
        if pix.loadFromData(self.resp.content):
            self.img_lbl.setPixmap(pix.scaled(600, 400, Qt.KeepAspectRatio))
        else:
            self.img_lbl.setText("Image load failed")
        self.resp_tabs.setCurrentWidget(self.img_lbl.parentWidget())

    def _handle_aud(self):
        self.audio = self.resp.content
        self.resp_tabs.setCurrentWidget(self.play_btn.parentWidget())
        self.play_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)

    def _handle_file(self):
        self.resp_tabs.setCurrentWidget(self.save_btn.parentWidget())
        self.save_btn.setEnabled(True)

    def _play_aud(self):
        if self.audio:
            if self.tmp:
                os.remove(self.tmp)
            self.tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3').name
            with open(self.tmp, 'wb') as f:
                f.write(self.audio)
            self.plr.setMedia(QMediaContent(QUrl.fromLocalFile(self.tmp)))
            self.plr.play()
            self.play_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)
            self.plr.stateChanged.connect(self._on_plr_state)

    def _stop_aud(self):
        self.plr.stop()
        self.play_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)

    def _on_plr_state(self, state):
        if state == QMediaPlayer.StoppedState:
            self.play_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)
            if self.tmp and os.path.exists(self.tmp):
                os.remove(self.tmp)
                self.tmp = None

    def _save_file(self):
        if not self.resp:
            QMessageBox.warning(self, "Error", "No file to save")
            return
        name = self.resp.headers.get('Content-Disposition', '').split('filename=')[-1].strip('"') or "download"
        file, _ = QFileDialog.getSaveFileName(self, "Save File", name, "All Files (*)")
        if file:
            try:
                with open(file, 'wb') as f:
                    f.write(self.resp.content)
                QMessageBox.information(self, "Success", "File saved")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Save failed: {e}")

    def _show_dbg(self):
        if not self.resp:
            return
        req_hdrs = '\n'.join(f"{k}: {v}" for k, v in self.resp.request.headers.items())
        resp_hdrs = '\n'.join(f"{k}: {v}" for k, v in self.resp.headers.items())
        dbg = (
            f"Method: {self.resp.request.method}\n"
            f"URL: {self.resp.request.url}\n"
            f"Request Headers:\n{req_hdrs}\n\n"
            f"Status: {self.resp.status_code} {self.resp.reason}\n"
            f"Response Headers:\n{resp_hdrs}\n\n"
            f"Body (first 1000 chars):\n{self.resp.text[:1000]}..."
        )
        self.dbg_txt.setPlainText(dbg)

    def _build_json(self):
        obj = {}
        for row in range(self.json_tbl.rowCount()):
            key_item = self.json_tbl.item(row, 0)
            val_item = self.json_tbl.item(row, 1)
            type_cb = self.json_tbl.cellWidget(row, 2)
            if key_item and val_item and type_cb:
                key = key_item.text().strip()
                val = val_item.text().strip()
                typ = type_cb.currentText()
                if key:
                    try:
                        obj[key] = self._parse_json_val(val, typ)
                    except ValueError as e:
                        raise ValueError(f"Invalid '{key}': {e}")
        return obj

    def _parse_json_val(self, val, typ):
        if not val and typ not in ["object", "array"]:
            return ""
        if typ == "string":
            return val
        elif typ == "number":
            try:
                return int(val) if '.' not in val else float(val)
            except ValueError:
                raise ValueError(f"'{val}' not number")
        elif typ == "boolean":
            if val.lower() in ["true", "false"]:
                return val.lower() == "true"
            raise ValueError(f"'{val}' not boolean")
        elif typ in ["object", "array"]:
            try:
                return json.loads(val) if val else ({} if typ == "object" else [])
            except json.JSONDecodeError:
                raise ValueError(f"Invalid {typ}: {val}")
        return val

    def closeEvent(self, evt):
        if self.tmp and os.path.exists(self.tmp):
            os.remove(self.tmp)
        super().closeEvent(evt)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = Tstr()
    win.show()
    sys.exit(app.exec_())