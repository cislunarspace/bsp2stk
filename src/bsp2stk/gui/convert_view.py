from pathlib import Path

from PyQt6.QtCore import QThread, Qt, pyqtSignal, QObject
from PyQt6.QtGui import QMouseEvent
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QFileDialog,
    QTextEdit,
    QProgressBar,
    QGroupBox,
    QFormLayout,
    QDoubleSpinBox,
    QSpinBox,
    QComboBox,
    QScrollArea,
    QCheckBox,
    QFrame,
    QSizePolicy,
)

from bsp2stk.core import convert as convert_mod

# STK 头常用选项（与 STK 场景/星历约定一致的可选值）
STK_INTERPOLATION_CHOICES: tuple[str, ...] = (
    "Lagrange",
    "Hermite",
    "Linear",
)
STK_CENTRAL_BODY_CHOICES: tuple[str, ...] = (
    "Earth",
    "Moon",
    "Sun",
    "Mars",
    "Jupiter",
    "Saturn",
    "Uranus",
    "Neptune",
    "Pluto",
    "Venus",
    "Mercury",
)
STK_COORDINATE_CHOICES: tuple[str, ...] = (
    "J2000",
    "EME2000",
    "ICRF",
    "Fixed",
    "TOD",
    "TrueOfDate",
)

from bsp2stk.core.info import get_segment_info
from bsp2stk.gui.paths import BSP_DIR, STK_DIR, bsp_open_dialog_start
from bsp2stk.io.handlers import load_bsp


class SegmentCard(QFrame):
    """单条 Segment：卡片布局、大号复选框、点击卡片空白处可切换勾选。"""

    toggled = pyqtSignal()

    def __init__(self, index: int, info: dict, checked: bool, parent: QWidget | None = None):
        super().__init__(parent)
        self.index = index
        self.setObjectName("segmentCard")
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setLineWidth(1)

        self.checkbox = QCheckBox()
        self.checkbox.setChecked(checked)
        self.checkbox.stateChanged.connect(self.toggled.emit)

        title = QLabel(
            f"Segment {index}　·　Center {info['center']}　→　Target {info['target']}"
        )
        title.setWordWrap(True)
        title.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)

        lbl_start = QLabel(f"开始：{info['start_time']}")
        lbl_end = QLabel(f"结束：{info['end_time']}")
        for lb in (lbl_start, lbl_end):
            lb.setWordWrap(True)
            lb.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
            lb.setProperty("subtle", True)
        for w in (title, lbl_start, lbl_end):
            w.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)

        text_col = QVBoxLayout()
        text_col.setSpacing(6)
        text_col.addWidget(title)
        text_col.addWidget(lbl_start)
        text_col.addWidget(lbl_end)

        row = QHBoxLayout(self)
        row.setContentsMargins(12, 12, 12, 12)
        row.setSpacing(14)
        row.addWidget(self.checkbox, 0, Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        row.addLayout(text_col, 1)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.checkbox.setChecked(not self.checkbox.isChecked())
        else:
            super().mousePressEvent(event)


class ConvertWorker(QObject):
    progress = pyqtSignal(float)
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(
        self,
        bsp_path: str,
        segment_indices: list[int],
        stk_dir: Path,
        bsp_stem: str,
        step_seconds: float,
        interpolation_method: str,
        interpolation_order: int,
        central_body: str,
        coordinate_system: str,
    ):
        super().__init__()
        self.bsp_path = bsp_path
        self.segment_indices = segment_indices
        self.stk_dir = stk_dir
        self.bsp_stem = bsp_stem
        self.step_seconds = step_seconds
        self.interpolation_method = interpolation_method
        self.interpolation_order = interpolation_order
        self.central_body = central_body
        self.coordinate_system = coordinate_system

    def run(self):
        from bsp2stk.core.convert import convert_bsp_to_stk

        n = len(self.segment_indices)
        try:
            for k, seg_idx in enumerate(self.segment_indices):
                stk_path = self.stk_dir / f"{self.bsp_stem}_seg{seg_idx}.stk"
                ephem_name = f"{self.bsp_stem}_seg{seg_idx}"

                def segment_progress(local: float, completed: int = k) -> None:
                    self.progress.emit((completed + local) / n)

                convert_bsp_to_stk(
                    self.bsp_path,
                    str(stk_path),
                    segment_index=seg_idx,
                    step_seconds=self.step_seconds,
                    ephemeris_name=ephem_name,
                    interpolation_method=self.interpolation_method,
                    interpolation_order=self.interpolation_order,
                    central_body=self.central_body,
                    coordinate_system=self.coordinate_system,
                    progress_callback=segment_progress,
                )
            self.finished.emit()
        except Exception as e:
            self.error.emit(str(e))


class ConvertView(QWidget):
    bsp_path_changed = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.selected_bsp: str | None = None
        self._pending_stk_paths: list[str] = []
        self._worker: ConvertWorker | None = None
        self._worker_thread: QThread | None = None
        self._segment_cards: list[SegmentCard] = []
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # 文件选择
        file_layout = QHBoxLayout()
        self.file_label = QLabel("未选择文件")
        btn_select = QPushButton("选择 BSP 文件")
        btn_select.clicked.connect(self._select_file)
        file_layout.addWidget(QLabel("BSP 文件:"))
        file_layout.addWidget(self.file_label, 1)
        file_layout.addWidget(btn_select)
        layout.addLayout(file_layout)

        layout.addWidget(QLabel("要转换的 Segment（可多选，点击整行也可勾选）:"))
        seg_toolbar = QHBoxLayout()
        btn_all = QPushButton("全选")
        btn_none = QPushButton("全不选")
        btn_all.clicked.connect(self._select_all_segments)
        btn_none.clicked.connect(self._deselect_all_segments)
        seg_toolbar.addWidget(btn_all)
        seg_toolbar.addWidget(btn_none)
        seg_toolbar.addStretch()
        layout.addLayout(seg_toolbar)

        self.segment_scroll = QScrollArea()
        self.segment_scroll.setWidgetResizable(True)
        self.segment_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        # 限制列表区域高度，避免内部卡片撑高最小尺寸后挤扁下方 STK 分组
        self.segment_scroll.setMinimumHeight(140)
        self.segment_scroll.setMaximumHeight(300)
        self.segment_scroll.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred,
        )
        self.segment_inner = QWidget()
        self.segment_layout = QVBoxLayout(self.segment_inner)
        self.segment_layout.setContentsMargins(0, 0, 8, 0)
        self.segment_layout.setSpacing(12)
        self.segment_layout.addStretch()
        self.segment_inner.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Minimum,
        )
        self.segment_scroll.setWidget(self.segment_inner)
        layout.addWidget(self.segment_scroll, 0)

        self._apply_segment_list_styles()

        stk_group = QGroupBox("STK 星历格式")
        stk_group.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Minimum,
        )
        stk_form = QFormLayout(stk_group)
        stk_form.setSpacing(10)
        stk_form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        stk_form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapLongRows)
        self.spin_step = QDoubleSpinBox()
        self.spin_step.setRange(0.1, 86400.0)
        self.spin_step.setDecimals(2)
        self.spin_step.setSingleStep(1.0)
        self.spin_step.setValue(convert_mod.DEFAULT_STEP_SECONDS)
        stk_form.addRow("时间步长 (秒):", self.spin_step)

        self.combo_interp_method = QComboBox()
        self.combo_interp_method.setEditable(False)
        self.combo_interp_method.setMinimumWidth(200)
        self._fill_stk_combo(self.combo_interp_method, STK_INTERPOLATION_CHOICES, convert_mod.INTERPOLATION_METHOD)
        stk_form.addRow("插值方法:", self.combo_interp_method)

        self.spin_interp_order = QSpinBox()
        self.spin_interp_order.setRange(1, 20)
        self.spin_interp_order.setValue(convert_mod.INTERPOLATION_ORDER)
        stk_form.addRow("插值阶数:", self.spin_interp_order)

        self.combo_central_body = QComboBox()
        self.combo_central_body.setEditable(False)
        self.combo_central_body.setMinimumWidth(200)
        self._fill_stk_combo(self.combo_central_body, STK_CENTRAL_BODY_CHOICES, convert_mod.CENTRAL_BODY)
        stk_form.addRow("中心天体 (CentralBody):", self.combo_central_body)

        self.combo_coord_system = QComboBox()
        self.combo_coord_system.setEditable(False)
        self.combo_coord_system.setMinimumWidth(200)
        self._fill_stk_combo(self.combo_coord_system, STK_COORDINATE_CHOICES, convert_mod.COORDINATE_SYSTEM)
        stk_form.addRow("坐标系 (CoordinateSystem):", self.combo_coord_system)

        btn_defaults = QPushButton("恢复默认格式")
        btn_defaults.clicked.connect(self._restore_stk_defaults)
        stk_form.addRow(btn_defaults)

        # 转换按钮
        self.btn_convert = QPushButton("开始转换")
        self.btn_convert.clicked.connect(self._do_convert)
        self.btn_convert.setEnabled(False)

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)

        # 仅 STK 表单放入滚动区；「开始转换」与进度条固定在外侧，窗口再矮也能看到
        work_inner = QWidget()
        work_layout = QVBoxLayout(work_inner)
        work_layout.setContentsMargins(0, 0, 0, 0)
        work_layout.setSpacing(0)
        work_layout.addWidget(stk_group)
        work_inner.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Minimum,
        )

        self.work_scroll = QScrollArea()
        self.work_scroll.setWidgetResizable(True)
        self.work_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.work_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.work_scroll.setWidget(work_inner)
        self.work_scroll.setMinimumHeight(160)
        self.work_scroll.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )
        layout.addWidget(self.work_scroll, 1)

        self.btn_convert.setMinimumHeight(40)
        layout.addWidget(self.btn_convert, 0)
        layout.addWidget(self.progress_bar, 0)

        # 结果显示
        self.result = QTextEdit()
        self.result.setReadOnly(True)
        self.result.setMinimumHeight(100)
        layout.addWidget(QLabel("输出说明与结果:"), 0)
        layout.addWidget(self.result, 2)

    @staticmethod
    def _fill_stk_combo(combo: QComboBox, choices: tuple[str, ...], default: str) -> None:
        combo.clear()
        combo.addItems(list(choices))
        idx = combo.findText(default)
        if idx >= 0:
            combo.setCurrentIndex(idx)
        else:
            combo.insertItem(0, default)
            combo.setCurrentIndex(0)

    def _apply_segment_list_styles(self) -> None:
        self.setStyleSheet(
            self.styleSheet()
            + """
            QFrame#segmentCard {
                border: 1px solid palette(mid);
                border-radius: 8px;
                background: palette(base);
                color: palette(window-text);
            }
            QFrame#segmentCard:hover {
                background: palette(alternate-base);
                color: palette(window-text);
            }
            QFrame#segmentCard QCheckBox {
                color: palette(window-text);
                spacing: 10px;
            }
            QFrame#segmentCard QCheckBox::indicator {
                width: 22px;
                height: 22px;
            }
            QFrame#segmentCard QLabel {
                color: palette(window-text);
                background: transparent;
            }
            QFrame#segmentCard QLabel[subtle="true"] {
                color: palette(placeholder-text);
                font-size: 12px;
            }
            """
        )

    def _clear_segment_cards(self) -> None:
        while self.segment_layout.count() > 1:
            item = self.segment_layout.takeAt(0)
            w = item.widget()
            if w is not None:
                w.deleteLater()
        self._segment_cards.clear()

    def _set_result_help(self, stem: str) -> None:
        example = f"{stem}_seg0.stk"
        html = f"""<div style="line-height:1.45">
<p style="margin:0 0 8px 0"><b>输出说明</b></p>
<ul style="margin:0;padding-left:22px">
<li>每个已勾选的 Segment 会生成 <b>一个</b> STK 文件。</li>
<li>文件名：<code style="font-size:12px">{stem}_seg<b>索引</b>.stk</code>
（索引为列表中的 Segment 编号）。</li>
</ul>
<p style="margin:10px 0 0 0"><small>示例：<code>{example}</code></small></p>
</div>"""
        self.result.setHtml(html)

    def _set_result_success(self, paths: list[str]) -> None:
        items = "".join(
            f"<li style='margin:6px 0'><code style='font-size:12px'>{p}</code></li>" for p in paths
        )
        html = (
            "<div style='line-height:1.45'>"
            f"<p style='margin:0 0 8px 0'><b>转换成功</b>（共 {len(paths)} 个文件）</p>"
            f"<ul style='margin:0;padding-left:22px'>{items}</ul>"
            "</div>"
        )
        self.result.setHtml(html)

    def _restore_stk_defaults(self) -> None:
        self.spin_step.setValue(convert_mod.DEFAULT_STEP_SECONDS)
        self._fill_stk_combo(self.combo_interp_method, STK_INTERPOLATION_CHOICES, convert_mod.INTERPOLATION_METHOD)
        self.spin_interp_order.setValue(convert_mod.INTERPOLATION_ORDER)
        self._fill_stk_combo(self.combo_central_body, STK_CENTRAL_BODY_CHOICES, convert_mod.CENTRAL_BODY)
        self._fill_stk_combo(self.combo_coord_system, STK_COORDINATE_CHOICES, convert_mod.COORDINATE_SYSTEM)

    def _read_stk_format(self) -> tuple[float, str, int, str, str]:
        method = self.combo_interp_method.currentText().strip() or convert_mod.INTERPOLATION_METHOD
        body = self.combo_central_body.currentText().strip() or convert_mod.CENTRAL_BODY
        coords = self.combo_coord_system.currentText().strip() or convert_mod.COORDINATE_SYSTEM
        return (
            float(self.spin_step.value()),
            method,
            int(self.spin_interp_order.value()),
            body,
            coords,
        )

    def set_shared_bsp(self, path: str) -> None:
        """由主窗口从「查看信息」页同步已选 BSP。"""
        if self.selected_bsp == path and len(self._segment_cards) > 0:
            return
        prev = self.selected_bsp
        self.selected_bsp = path
        self.file_label.setText(Path(path).name)
        self._refresh_segment_list(path)
        if prev != path and len(self._segment_cards) > 0:
            self._set_result_help(Path(path).stem)

    def _update_convert_enabled(self) -> None:
        self.btn_convert.setEnabled(
            self.selected_bsp is not None and len(self._checked_segment_indices()) > 0
        )

    def _checked_segment_indices(self) -> list[int]:
        return sorted(c.index for c in self._segment_cards if c.checkbox.isChecked())

    def _select_all_segments(self) -> None:
        for c in self._segment_cards:
            c.checkbox.blockSignals(True)
            c.checkbox.setChecked(True)
            c.checkbox.blockSignals(False)
        self._update_convert_enabled()

    def _deselect_all_segments(self) -> None:
        for c in self._segment_cards:
            c.checkbox.blockSignals(True)
            c.checkbox.setChecked(False)
            c.checkbox.blockSignals(False)
        self._update_convert_enabled()

    def _refresh_segment_list(self, bsp_path: str) -> None:
        self._clear_segment_cards()
        try:
            kernel = load_bsp(bsp_path)
        except OSError as e:
            self.result.setPlainText(f"无法读取 Segment 列表: {e}")
            self._update_convert_enabled()
            return
        segments_list = list(kernel.segments)
        if not segments_list:
            self.result.setPlainText("该 BSP 中没有 Segment。")
            self._update_convert_enabled()
            return
        for i, segment in enumerate(segments_list):
            info = get_segment_info(segment)
            card = SegmentCard(i, info, checked=(i == 0))
            card.toggled.connect(self._update_convert_enabled)
            self._segment_cards.append(card)
            self.segment_layout.insertWidget(self.segment_layout.count() - 1, card)
        self._update_convert_enabled()

    def _select_file(self):
        start = bsp_open_dialog_start()
        if not BSP_DIR.is_dir() or not any(BSP_DIR.glob("*.bsp")):
            self.result.setPlainText(
                "提示：项目 bsp/ 目录下没有示例 .bsp 文件，您仍可在文件对话框中选择任意路径下的 BSP。"
            )
        path, _ = QFileDialog.getOpenFileName(self, "选择 BSP 文件", start, "BSP Files (*.bsp)")
        if path:
            self.selected_bsp = path
            self.file_label.setText(Path(path).name)
            self._refresh_segment_list(path)
            if len(self._segment_cards) > 0:
                self._set_result_help(Path(path).stem)
            self.bsp_path_changed.emit(path)

    def _do_convert(self):
        if not self.selected_bsp:
            return
        if self._worker_thread is not None and self._worker_thread.isRunning():
            return

        indices = self._checked_segment_indices()
        if not indices:
            return

        bsp_path = self.selected_bsp
        bsp_stem = Path(bsp_path).stem
        STK_DIR.mkdir(parents=True, exist_ok=True)
        self._pending_stk_paths = [str(STK_DIR / f"{bsp_stem}_seg{i}.stk") for i in indices]

        step, interp_m, interp_o, body, coords = self._read_stk_format()

        self.btn_convert.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.result.setPlainText("转换中…")

        worker = ConvertWorker(
            bsp_path,
            indices,
            STK_DIR,
            bsp_stem,
            step,
            interp_m,
            interp_o,
            body,
            coords,
        )
        thread = QThread()
        self._worker = worker
        self._worker_thread = thread

        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.finished.connect(thread.quit)
        worker.error.connect(thread.quit)
        worker.finished.connect(self._on_worker_finished)
        worker.error.connect(self._on_worker_error)
        worker.progress.connect(self._on_progress)
        thread.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        thread.finished.connect(self._on_worker_thread_finished)

        thread.start()

    def _on_progress(self, progress: float):
        self.progress_bar.setValue(int(progress * 100))

    def _on_worker_finished(self):
        self.progress_bar.setVisible(False)
        if self._pending_stk_paths:
            self._set_result_success(self._pending_stk_paths)

    def _on_worker_error(self, error_msg: str):
        self.progress_bar.setVisible(False)
        self.result.setPlainText(f"转换失败:\n\n{error_msg}")

    def _on_worker_thread_finished(self):
        self.btn_convert.setEnabled(True)
        self._worker_thread = None
        self._worker = None
        self._update_convert_enabled()
