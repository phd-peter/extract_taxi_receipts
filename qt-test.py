from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QPushButton,
    QFileDialog,
    QMessageBox,
    QProgressBar,
    QVBoxLayout,
    QHBoxLayout,
    QPlainTextEdit,
    QLabel,
)
from PyQt5.QtCore import QThread, pyqtSignal
import sys, os

# -- 백그라운드 작업 쓰레드 ----------------------------------------------


class ExtractWorker(QThread):
    finished = pyqtSignal(str)  # CSV 경로
    error = pyqtSignal(str)
    cancelled = pyqtSignal()
    progress = pyqtSignal(int)  # 0~100
    log = pyqtSignal(str)       # 로그 메시지

    def __init__(self, folder: str):
        super().__init__()
        self.folder = folder
        self._abort = False

    def stop(self):
        """작업 중단 요청."""
        self._abort = True

    def run(self):
        """이미지 추출을 진행하며 진행률 신호를 방출."""

        try:
            from extract_taxi_receipts import (
                extract_from_images,
                pair_images_from_dir,
            )
            import pandas as pd
            import datetime as dt
            import os

            pairs = pair_images_from_dir(self.folder)
            total = len(pairs)
            if total == 0:
                raise RuntimeError("선택한 폴더에 처리할 이미지가 없습니다.")

            rows = []
            self.log.emit(f"총 {total}개 이미지 쌍 처리 시작…")
            self.log.emit(f"----- 진행 로그 [이미지 파일명 → 추출된 데이터] -------")
            for idx, (front, back) in enumerate(pairs, 1):
                if self._abort:
                    self.log.emit("[사용자 중단] 작업이 취소되었습니다.")
                    self.cancelled.emit()
                    return
                try:
                    data = extract_from_images(front, back)
                    rows.append(data)
                    self.log.emit(f"✓ Parsed [{os.path.basename(front)} & {os.path.basename(back)}] → {data}")
                except Exception as e:  # CoreError 포함
                    self.log.emit(f"✗ Failed on {os.path.basename(front)}: {e}")
                # 진행률 계산
                self.progress.emit(int(idx / total * 100))

            df = pd.DataFrame(rows)
            if not df.empty:
                ordered_cols = ["paid_at", "name", "route", "fare"]
                df = df[ordered_cols]

            ts = dt.datetime.now().strftime("%Y%m%d_%H%M")
            out_path = os.path.join(os.getcwd(), f"receipts_{ts}.csv")
            df.to_csv(out_path, index=False, encoding="utf-8-sig")
            self.log.emit(f"Saved {len(df)} rows → {out_path}")

            if not self._abort:
                self.finished.emit(out_path)
        except Exception as e:
            self.error.emit(str(e))


# -------------------------------------------------------------------------


class ImageProcessor(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🚕 택시 영수증 자동 추출 GUI")
        self.resize(750, 600)  # 창 크기 확대

        self.info_label = QLabel(
            "<b>사용 방법</b>\n<ul>"
            "<li>📁 <b>이미지 폴더 선택</b> 버튼을 눌러 영수증 앞/뒷면 이미지가 있는 폴더를 선택하여 데이터를 추출합니다.</li>"
            "<li> 폴더 내에 영수증 앞/뒷면 이미지는 이름 내림차순으로 정렬되어 있어야합니다.</li>"
            "<li> 자세한 설명은 <a href='https://i.ibb.co/svyTWHs0/1.png' target='_blank'>설명파일 링크</a>를 참고하세요.</li>"
            "<li>OPENAI의 Vison api를 활용하여 사진에 있는 데이터를 추출합니다. 시간이 다소 소요됩니다. 진행률과 로그를 확인하세요.</li>"
            "<li>💾 <b>작업 로그</b>는 log 폴더에 저장됩니다.</li>"
            "</ul>"
        )
        self.info_label.setWordWrap(True)
        self.info_label.setOpenExternalLinks(True)

        self.btn = QPushButton("이미지 폴더 선택")
        self.btn.clicked.connect(self.select_folder)

        self.cancel_btn = QPushButton("작업 중단")
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.clicked.connect(self.cancel_worker)

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)

        self.log_view = QPlainTextEdit()
        self.log_view.setReadOnly(True)

        top_layout = QHBoxLayout()
        top_layout.addWidget(self.btn)
        top_layout.addWidget(self.progress)
        top_layout.addWidget(self.cancel_btn)

        layout = QVBoxLayout()
        layout.addWidget(self.info_label)
        layout.addLayout(top_layout)
        layout.addWidget(self.log_view)

        # 작성자 정보
        self.author_label = QLabel(
            '<span style="color:gray;">© 2025 ExtractTaxiReceipts | Developer: 연구개발부 조광원 | 문의: kwjo@senkuzo.com</span>'
        )
        layout.addWidget(self.author_label)
        self.setLayout(layout)

        # 로그 저장을 위한 버퍼
        self.log_lines = []

    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "이미지 폴더 선택")
        if folder:
            self.btn.setEnabled(False)
            self.progress.setValue(0)
            self.worker = ExtractWorker(folder)
            self.worker.finished.connect(self.on_finished)
            self.worker.error.connect(self.on_error)
            self.worker.progress.connect(self.progress.setValue)
            self.worker.log.connect(self.append_log)
            self.worker.cancelled.connect(self.on_cancelled)
            self.cancel_btn.setEnabled(True)
            self.worker.start()

    def on_finished(self, csv_path: str):
        reply = QMessageBox.question(
            self,
            "작업 완료",
            f"CSV 저장 완료:\n{csv_path}\n\n파일을 열어보시겠습니까?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes,
        )

        if reply == QMessageBox.Yes:
            try:
                if sys.platform.startswith("win"):
                    os.startfile(csv_path)
                elif sys.platform == "darwin":
                    import subprocess

                    subprocess.call(["open", csv_path])
                else:
                    import subprocess

                    subprocess.call(["xdg-open", csv_path])
            except Exception as e:
                self.append_log(f"[WARN] CSV 자동 열기 실패: {e}")

        self.append_log("--------------------------------")
        self.append_log("처리가 완료되었습니다.")
        self.save_log_to_file()
        self.btn.setEnabled(True)
        self.progress.setValue(100)
        self.cancel_btn.setEnabled(False)

    def on_error(self, msg: str):
        QMessageBox.critical(self, "오류", msg)
        self.append_log(f"[ERROR] {msg}")
        self.btn.setEnabled(True)
        self.progress.setValue(0)
        self.save_log_to_file()
        self.cancel_btn.setEnabled(False)

    def append_log(self, msg: str):
        self.log_view.appendPlainText(msg)
        self.log_lines.append(msg)

    def save_log_to_file(self):
        import datetime as _dt, os as _os

        if not self.log_lines:
            return

        log_dir = _os.path.join(_os.getcwd(), "log")
        _os.makedirs(log_dir, exist_ok=True)
        filename = f"{_dt.date.today().isoformat()}_process_log.txt"
        path = _os.path.join(log_dir, filename)
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write("\n".join(self.log_lines))
            self.append_log(f"로그 파일 저장 완료 → log/{filename}")
        except Exception as e:
            self.append_log(f"[WARN] 로그 저장 실패: {e}")

    def cancel_worker(self):
        if hasattr(self, "worker") and self.worker.isRunning():
            self.append_log("[INFO] 작업 중단 요청 중…")
            self.worker.stop()
            self.cancel_btn.setEnabled(False)

    def on_cancelled(self):
        self.append_log("[INFO] 작업이 중단되었습니다.")
        self.btn.setEnabled(True)
        self.progress.setValue(0)
        self.cancel_btn.setEnabled(False)
        self.save_log_to_file()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = ImageProcessor()
    w.show()
    sys.exit(app.exec_())
