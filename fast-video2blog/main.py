import os
import sys
import subprocess
import tempfile
import numpy as np
import torch
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QFileDialog, QLabel, QProgressBar, QTextEdit, QCheckBox)
from PyQt5.QtCore import QThread, pyqtSignal, Qt, QObject
from PyQt5.QtGui import QTextCursor
import whisper
from pyannote.audio import Pipeline
from pydub import AudioSegment
import mlx_whisper
import time # 导入 time 模块

class AudioProcessor(QThread):
    progress = pyqtSignal(int)
    message = pyqtSignal(str)
    result = pyqtSignal(str)
    finished = pyqtSignal()
    audio_duration = pyqtSignal(float) # 新增信号，用于传递音频时长

    def __init__(self, video_path, diarize=True):
        super().__init__()
        self.video_path = video_path
        self.diarize = diarize
        self.device = "mps" if torch.backends.mps.is_available() else "cpu"
        os.environ["PYTORCH_ENABLE_MPS_FALLBACK"] = "1"

        self.improvement_prompt = "加标点符号并排版，整理成一篇博客文章，尽量内容完整：\n"
        self.improvement_prompt_en = "加标点符号并排版，整理成一篇博客文章，要英文版本：\n"
        # self.improvement_prompt = "加标点符号并排版，整理成一篇博客文章，可能有一些错别字，如果错误非常明显你可以根据上下文改一下，不明显就不要改：\n"

    def extract_audio(self, video_path):
        """提取视频音轨为WAV格式"""
        self.message.emit("提取音频中...")
        audio = AudioSegment.from_file(video_path)
        duration_seconds = len(audio) / 1000.0 # 获取音频时长（秒）
        self.audio_duration.emit(duration_seconds) # 发送音频时长
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmpfile:
            audio.export(tmpfile.name, format="wav")
            return tmpfile.name

    def transcribe_with_speakers(self, audio_path):
        """执行语音识别和说话人分离"""
        # 加载模型
        self.message.emit("加载语音识别模型...")
        model = whisper.load_model("medium", device=self.device)
        
        self.message.emit("加载说话人识别模型...")
        diarization_pipeline = Pipeline.from_pretrained(
            "pyannote/speaker-diarization-3.1",
            use_auth_token=YOUR_HF_TOKEN  # 替换为你的HuggingFace token
        ).to(torch.device(self.device))

        # 执行说话人分离
        self.message.emit("识别说话人...")
        diarization = diarization_pipeline(audio_path)
        
        # 加载音频数据
        self.message.emit("加载音频数据...")
        audio = whisper.load_audio(audio_path)
        
        # 转录音频
        self.message.emit("转录音频中...")
        result_text = model.transcribe(audio_path, verbose=False) # verbose=False to avoid printing to console
        self.progress.emit(50) # Placeholder progress

        if not self.diarize:
            self.progress.emit(100)
            return result_text["text"]

        # 如果需要说话人识别，继续执行
        self.message.emit("加载说话人识别模型...")
        diarization_pipeline = Pipeline.from_pretrained(
            "pyannote/speaker-diarization-3.1",
            use_auth_token=YOUR_HF_TOKEN  # 替换为你的HuggingFace token
        ).to(torch.device(self.device))

        # 执行说话人分离
        self.message.emit("识别说话人...")
        diarization = diarization_pipeline(audio_path)
        self.progress.emit(75) # Placeholder progress
        
        # 将转录结果与说话人对应
        # 注意：这里的对应逻辑可能需要根据 whisper 和 pyannote 的输出格式进行调整
        # 这是一个简化的示例，实际应用中可能需要更复杂的对齐逻辑
        final_result = []
        # 获取每个词的时间戳
        segments = result_text["segments"]
        
        # 创建一个函数来查找给定时间点属于哪个说话人
        def get_speaker_for_time(time_sec):
            for turn, _, speaker in diarization.itertracks(yield_label=True):
                if turn.start <= time_sec < turn.end:
                    return speaker
            return "未知说话人"

        current_speaker = None
        current_speech = ""

        for segment in segments:
            segment_start_time = segment['start']
            # 尝试获取片段中间时间的说话人，以提高准确性
            # 如果片段很短，就用开始时间
            time_to_check = segment_start_time
            if 'end' in segment and (segment['end'] - segment_start_time > 0.1):
                 time_to_check = (segment_start_time + segment['end']) / 2.0

            speaker = get_speaker_for_time(time_to_check)
            
            if speaker != current_speaker and current_speech:
                final_result.append(f"{current_speaker}: {current_speech.strip()}")
                current_speech = ""
            
            current_speaker = speaker
            current_speech += segment['text'] + " "

        if current_speech: # 添加最后一段语音
            final_result.append(f"{current_speaker}: {current_speech.strip()}")
        
        self.progress.emit(100)
        return "\n".join(final_result)

    def transcribe_text_only(self, audio_path):
        """仅执行语音识别，不进行说话人分离"""
        self.message.emit("加载语音识别模型...")
        # model = whisper.load_model("medium", device="cpu")
        # 
        # model = model.to("mps").half()
        self.message.emit("转录音频中...")
        # 使用基础的 transcribe 方法
        # result = model.transcribe(audio_path, verbose=False)
        result = mlx_whisper.transcribe(audio_path, path_or_hf_repo="mlx-community/whisper-medium-mlx")
        self.progress.emit(100) # 假设转录完成占100%进度
        return result["text"]

    def run(self):
        try:
            # 步骤1: 提取音频
            audio_path = self.extract_audio(self.video_path)
            self.message.emit(f"音频已提取到: {audio_path}")
            
            # 步骤2: 根据设置选择转录方式
            if self.diarize:
                self.message.emit("开始转录和说话人识别...")
                transcript = self.transcribe_with_speakers(audio_path)
            else:
                self.message.emit("开始仅文本转录...")
                transcript = self.transcribe_text_only(audio_path)
            
            # 清理临时文件
            os.unlink(audio_path)
            
            # 发送结果
            self.result.emit(transcript)
            self.message.emit("处理完成!")
        except Exception as e:
            self.message.emit(f"错误: {str(e)}")
        finally:
            self.finished.emit()

class VideoTranscriberApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("视频转文字工具")
        self.setGeometry(100, 100, 800, 600)
        
        # 创建主部件
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        
        # 布局
        layout = QVBoxLayout()
        main_widget.setLayout(layout)
        
        # 文件选择区域
        file_layout = QHBoxLayout()
        self.file_label = QLabel("未选择文件")
        file_btn = QPushButton("选择视频文件")
        file_btn.clicked.connect(self.select_file)
        file_layout.addWidget(self.file_label)
        file_layout.addWidget(file_btn)
        layout.addLayout(file_layout)

        # 说话人识别选项
        self.diarize_checkbox = QCheckBox("识别说话人 (实验性，可能不准确)")
        self.diarize_checkbox.setChecked(False) # 默认勾选
        layout.addWidget(self.diarize_checkbox)
        
        # 进度区域
        self.progress_label = QLabel("准备就绪")
        self.progress_bar = QProgressBar()
        layout.addWidget(self.progress_label)
        layout.addWidget(self.progress_bar)
        
        # 操作按钮
        self.process_btn = QPushButton("开始转换")
        self.process_btn.clicked.connect(self.start_processing)
        self.process_btn.setEnabled(False)
        layout.addWidget(self.process_btn)
        
        # 结果区域
        self.result_area = QTextEdit()
        self.result_area.setReadOnly(True)
        self.result_area.setFixedHeight(200) # 设置一个初始高度
        layout.addWidget(self.result_area)

        # 添加 improvement_prompt 选项
        self.add_prompt_checkbox = QCheckBox("复制时添加优化提示词")
        self.add_prompt_checkbox.setChecked(True) # 默认勾选
        layout.addWidget(self.add_prompt_checkbox)

        # 添加 improvement_prompt_en 选项
        self.add_prompt_en_checkbox = QCheckBox("复制时添加英文优化提示词")
        self.add_prompt_en_checkbox.setChecked(False) # 默认不勾选
        layout.addWidget(self.add_prompt_en_checkbox)

        # 复制按钮
        self.copy_button = QPushButton("复制结果")
        self.copy_button.clicked.connect(self.copy_result_to_clipboard)
        self.copy_button.setEnabled(False) # 初始禁用
        layout.addWidget(self.copy_button)

        # 日志输出区域
        log_label = QLabel("日志输出:")
        layout.addWidget(log_label)
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.setFixedHeight(150) # 设置一个初始高度
        layout.addWidget(self.log_area)
        
        # 状态变量
        self.current_file = None
        self.worker = None
        self.audio_duration_seconds = 0.0

    def select_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择视频文件", "", 
            "视频文件 (*.mp4 *.avi *.mov *.mkv *.flv)"
        )
        if file_path:
            self.current_file = file_path
            self.file_label.setText(os.path.basename(file_path))
            self.process_btn.setEnabled(True)

    def start_processing(self):
        if not self.current_file:
            return
            
        self.process_btn.setEnabled(False)
        self.result_area.clear()
        self.progress_bar.setValue(0)
        self.progress_label.setText("处理中...")
        self.start_time = time.time() # 记录开始时间
        
        # 创建工作线程
        diarize_enabled = self.diarize_checkbox.isChecked()
        self.worker = AudioProcessor(self.current_file, diarize=diarize_enabled)
        self.worker.message.connect(self.update_log_and_progress_label)
        self.worker.progress.connect(self.progress_bar.setValue)
        self.worker.result.connect(self.on_result)
        self.worker.finished.connect(self.on_finished)
        self.worker.audio_duration.connect(self.display_audio_duration) # 连接信号
        self.worker.start()

    def update_log_and_progress_label(self, message_text):
        self.progress_label.setText(message_text)
        self.log_area.append(message_text)
        self.log_area.moveCursor(QTextCursor.End)

    def append_to_log(self, text):
        self.log_area.append(text.strip()) # strip to remove extra newlines from print
        self.log_area.moveCursor(QTextCursor.End)

    def on_result(self, result):
        # 在结果开头添加文件名信息
        file_name = os.path.basename(self.current_file)
        formatted_result = f"文件名: {file_name}\n\n{result}"
        self.result_area.setText(formatted_result)

    def on_finished(self):
        self.process_btn.setEnabled(True)
        self.copy_button.setEnabled(True) # 处理完成后启用复制按钮
        end_time = time.time() # 记录结束时间
        elapsed_time = end_time - self.start_time # 计算用时
        minutes = int(self.audio_duration_seconds // 60)
        seconds = int(self.audio_duration_seconds % 60)
        self.progress_label.setText(f"处理完成！视频时长: {minutes} 分 {seconds} 秒，用时: {elapsed_time:.2f} 秒")
        self.log_area.append(f"处理完成！总用时: {elapsed_time:.2f} 秒")
        self.log_area.moveCursor(QTextCursor.End)

    def copy_result_to_clipboard(self):
        clipboard = QApplication.clipboard()
        text_to_copy = self.result_area.toPlainText()
        if self.add_prompt_checkbox.isChecked():
            # 获取 AudioProcessor 实例的 improvement_prompt
            # 这里需要确保 worker 已经被创建并且 improvement_prompt 属性可用
            if self.worker and hasattr(self.worker, 'improvement_prompt'):
                if self.add_prompt_en_checkbox.isChecked():
                    text_to_copy = self.worker.improvement_prompt_en + text_to_copy
                else:
                    text_to_copy = self.worker.improvement_prompt + text_to_copy
            else:
                self.log_area.append("警告: 无法获取优化提示词，将仅复制转录结果。")
        clipboard.setText(text_to_copy)
        self.log_area.append("转录结果已复制到剪贴板！")
        self.log_area.moveCursor(QTextCursor.End)

    def display_audio_duration(self, duration):
        minutes = int(duration // 60)
        seconds = int(duration % 60)
        self.audio_duration_seconds = duration
        self.log_area.append(f"视频时长: {minutes} 分 {seconds} 秒")
        self.log_area.moveCursor(QTextCursor.End)

# 自定义流以捕获stdout/stderr
class QTextEditLogger(QObject):
    messageWritten = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

    def write(self, message):
        if message.strip(): #只发送非空消息
            self.messageWritten.emit(str(message))

    def flush(self):
        # 这个方法是必须的，即使它什么也不做
        pass

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    window = VideoTranscriberApp()

    # 重定向stdout和stderr
    stdout_logger = QTextEditLogger()
    stdout_logger.messageWritten.connect(window.append_to_log)
    sys.stdout = stdout_logger

    stderr_logger = QTextEditLogger()
    stderr_logger.messageWritten.connect(window.append_to_log) # 也可连接到不同的处理函数，例如用红色显示错误
    sys.stderr = stderr_logger

    # 检查GPU可用性 (现在会输出到log_area)
    if torch.cuda.is_available():
        print("检测到GPU，将使用CUDA加速")
    else:
        print("警告: 未检测到GPU，处理速度可能较慢")
    
    window.show()
    sys.exit(app.exec_())
