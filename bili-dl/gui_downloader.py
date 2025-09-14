import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog # Added filedialog
import subprocess
import os
from datetime import datetime
import time 
import threading
import glob # Added import
import re

class BiliDownloaderApp:
    def __init__(self, master):
        self.master = master
        master.title("Bilibili 视频下载器")
        master.geometry("700x550")

        # --- 输入区域 ---
        input_frame = ttk.LabelFrame(master, text="输入参数")
        input_frame.pack(padx=10, pady=10, fill="x")

        ttk.Label(input_frame, text="视频 URL 或 ID:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.url_entry = ttk.Entry(input_frame, width=60)
        self.url_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        self.url_entry.insert(0, "https://www.bilibili.com/video/BV1hx4y1t721/") # 默认示例

        self.is_playlist_var = tk.BooleanVar()
        self.playlist_check = ttk.Checkbutton(input_frame, text="是否为播放列表 (Playlist)", variable=self.is_playlist_var)
        self.playlist_check.grid(row=1, column=0, columnspan=2, padx=5, pady=5, sticky="w")

        ttk.Label(input_frame, text="专辑名 (文件夹名):").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.album_name_entry = ttk.Entry(input_frame, width=60)
        self.album_name_entry.grid(row=2, column=1, padx=5, pady=5, sticky="ew")
        self.album_name_entry.insert(0, datetime.now().strftime("%Y-%m-%d_%H-%M-%S"))

        self.auto_clean_var = tk.BooleanVar()
        self.auto_clean_check = ttk.Checkbutton(input_frame, text="下载完成后自动清理重复文件", variable=self.auto_clean_var)
        self.auto_clean_check.grid(row=3, column=0, padx=5, pady=5, sticky="w")

        ttk.Label(input_frame, text="清理模式:").grid(row=3, column=1, padx=5, pady=5, sticky="w")
        self.clean_mode_var = tk.StringVar(value="保留音频") # 默认保留音频
        self.clean_mode_combo = ttk.Combobox(input_frame, textvariable=self.clean_mode_var, values=["保留音频", "保留视频", "保留两者"], state="readonly", width=10)
        self.clean_mode_combo.grid(row=3, column=1, columnspan=2, padx=5, pady=5, sticky="e")

        ttk.Label(input_frame, text="视频清晰度:").grid(row=4, column=0, padx=5, pady=5, sticky="w")
        self.quality_var = tk.StringVar(value="720p") # 默认720p
        self.quality_combo = ttk.Combobox(input_frame, textvariable=self.quality_var, values=["720p", "480p", "360p"], state="readonly", width=10)
        self.quality_combo.grid(row=4, column=1, padx=5, pady=5, sticky="w")

        input_frame.columnconfigure(1, weight=1) # 使输入框可伸缩

        # --- 操作按钮区域 ---
        action_frame = ttk.Frame(master)
        action_frame.pack(pady=5)

        self.info_button = ttk.Button(action_frame, text="获取视频信息", command=self.get_video_info)
        self.info_button.pack(side=tk.LEFT, padx=5)

        self.download_button = ttk.Button(action_frame, text="开始下载", command=self.download_video)
        self.download_button.pack(side=tk.LEFT, padx=5)

        self.clean_button = ttk.Button(action_frame, text="清理重复文件", command=self.clean_duplicate_files_manual)
        self.clean_button.pack(side=tk.LEFT, padx=5)

        self.clean_current_album_button = ttk.Button(action_frame, text="清理当前专辑文件夹", command=self.clean_current_album_folder)
        self.clean_current_album_button.pack(side=tk.LEFT, padx=5)

        self.rename_mp3_button = ttk.Button(action_frame, text="重命名 MP4 为 MP3", command=self.rename_mp4_to_mp3_in_album)
        self.rename_mp3_button.pack(side=tk.LEFT, padx=5)

        # --- 输出区域 ---
        output_frame = ttk.LabelFrame(master, text="输出信息")
        output_frame.pack(padx=10, pady=10, fill="both", expand=True)

        self.output_text = scrolledtext.ScrolledText(output_frame, wrap=tk.WORD, height=15)
        self.output_text.pack(fill="both", expand=True, padx=5, pady=5)
        self.output_text.configure(state='disabled') # 初始时不可编辑

        # --- 可编辑输出区域 ---
        self.uptodate_output_lines = []
        editable_output_frame = ttk.LabelFrame(master, text="可编辑输出信息")
        editable_output_frame.pack(padx=10, pady=10, fill="both", expand=True)

        self.editable_output_text = scrolledtext.ScrolledText(editable_output_frame, wrap=tk.WORD, height=5)
        self.editable_output_text.pack(fill="both", expand=True, padx=5, pady=5)
        self.editable_output_text.insert(tk.END, "\n".join(self.uptodate_output_lines))
        self.editable_output_text.bind("<<Modified>>", self._on_editable_output_modified)

        # --- Cookies 路径 (固定) ---
        self.cookies_path = "/Users/qiqizhou/Library/Application Support/Firefox/Profiles/hpv7fq1b.default-release/cookies.sqlite"

    # def 


    def _update_text_widget(self, message): # New method for thread-safe UI update
        self.output_text.configure(state='normal')
        self.output_text.insert(tk.END, message + "\n")
        # if "title:" in line of message, append to self.uptodate_output_lines
        title_lines = [line for line in message.split('\n') if "title:" in line]
        # 将找到的标题行添加到输出列表中
        self.uptodate_output_lines.extend(title_lines)
        self.output_text.see(tk.END) # 滚动到底部
        self.output_text.configure(state='disabled')

        # Update editable output text
        self.editable_output_text.delete(1.0, tk.END)
        self.editable_output_text.insert(tk.END, "\n".join(self.uptodate_output_lines))

    def _on_editable_output_modified(self, event):
        # This method is called when the editable_output_text is modified
        # We need to clear the modified flag first
        self.editable_output_text.edit_modified(False)
        # Update the uptodate_output_lines list
        current_content = self.editable_output_text.get(1.0, tk.END).strip()
        self.uptodate_output_lines = current_content.split("\n") if current_content else []


    def _log_output(self, message):
        # Schedule the UI update to be run in the main Tkinter thread
        self.master.after(0, self._update_text_widget, message)

    def _run_command_in_thread(self, command_list, cwd=None): # Renamed and modified for threading
        self._log_output(f">>> 执行命令: {' '.join(command_list)}")
        if cwd:
            self._log_output(f"    工作目录: {cwd}")
        try:
            process = subprocess.Popen(command_list, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1, universal_newlines=True, cwd=cwd, encoding='utf-8', errors='replace')
            for line in process.stdout:
                self._log_output(line.strip())
            process.wait()
            if process.returncode == 0:
                self._log_output("<<< 命令执行成功")
            else:
                self._log_output(f"<<< 命令执行失败, 返回码: {process.returncode}")
            return process.returncode # Return code for sequential operations
        except FileNotFoundError:
            self._log_output("<<< 错误: 'you-get' 命令未找到。请确保已正确安装并配置在系统 PATH 中。")
            self.master.after(0, lambda: messagebox.showerror("错误", "'you-get' 命令未找到。\n请确保已正确安装并配置在系统 PATH 中。"))
            return -1 # Return code for sequential operations
        except Exception as e:
            self._log_output(f"<<< 执行命令时发生错误: {e}")
            self.master.after(0, lambda: messagebox.showerror("执行错误", f"执行命令时发生错误: {e}"))
            return -1 # Return code for sequential operations

    def _clean_files_in_directory(self, target_directory):
        self._log_output(f"--- 开始清理文件夹: {target_directory} ---")
        cleaned_count = 0
        clean_mode = self.clean_mode_var.get()
        self._log_output(f"清理模式: {clean_mode}")

        # Find and delete files based on clean_mode
        mp4_files = glob.glob(os.path.join(target_directory, "*.mp4"))
        for file_path in mp4_files:
            filename = os.path.basename(file_path)
            if clean_mode == "保留音频":
                if "[00]" in filename: # Delete video files (marked with [00])
                    try:
                        os.remove(file_path)
                        self._log_output(f"已删除视频文件 (保留音频): {file_path}")
                        cleaned_count += 1
                    except Exception as e:
                        self._log_output(f"删除文件失败 {file_path}: {e}")
            elif clean_mode == "保留视频":
                if "[01]" in filename: # Delete audio files (marked with [01])
                    try:
                        os.remove(file_path)
                        self._log_output(f"已删除音频文件 (保留视频): {file_path}")
                        cleaned_count += 1
                    except Exception as e:
                        self._log_output(f"删除文件失败 {file_path}: {e}")
            elif clean_mode == "保留两者":
                # Find corresponding [00] (video) and [01] (audio) files
                if "[00]" in filename:
                    base_name = filename.replace("[00]", "").replace(".mp4", "")
                    audio_file = os.path.join(target_directory, f"{base_name}[01].mp4")
                    video_file = file_path

                    if os.path.exists(audio_file):
                        output_file = os.path.join(target_directory, f"{base_name}.mp4")
                        self._log_output(f"正在合并视频 {video_file} 和音频 {audio_file} 到 {output_file}")
                        try:
                            # Use ffmpeg to merge video and audio
                            # -i for input, -c:v copy for video codec copy, -c:a aac for audio codec aac, -strict experimental for non-standard aac
                            # -map 0:v:0 to select video stream from first input, -map 1:a:0 to select audio stream from second input
                            subprocess.run([
                                'ffmpeg',
                                '-i', video_file,
                                '-i', audio_file,
                                '-c:v', 'copy',
                                '-c:a', 'aac',
                                '-strict', 'experimental',
                                output_file
                            ], check=True, capture_output=True, text=True)
                            self._log_output(f"合并成功: {output_file}")
                            # Delete original [00] and [01] files after successful merge
                            os.remove(video_file)
                            os.remove(audio_file)
                            self._log_output(f"已删除原始文件: {video_file} 和 {audio_file}")
                            cleaned_count += 2 # Count both deleted files
                        except FileNotFoundError:
                            self._log_output("<<< 错误: 'ffmpeg' 命令未找到。请确保已正确安装并配置在系统 PATH 中。")
                            self.master.after(0, lambda: messagebox.showerror("错误", "'ffmpeg' 命令未找到。\n请确保已正确安装并配置在系统 PATH 中。"))
                        except subprocess.CalledProcessError as e:
                            self._log_output(f"<<< FFmpeg 合并失败: {e.stderr}")
                            self.master.after(0, lambda: messagebox.showerror("FFmpeg 错误", f"FFmpeg 合并失败: {e.stderr}"))
                        except Exception as e:
                            self._log_output(f"<<< 合并文件时发生错误: {e}")
                            self.master.after(0, lambda: messagebox.showerror("合并错误", f"合并文件时发生错误: {e}"))
        
        # Get all .xml files in the target directory and delete them
        xml_files = glob.glob(os.path.join(target_directory, "*.xml"))
        for file_path in xml_files:
            try:
                os.remove(file_path)
                self._log_output(f"已删除 XML 文件: {file_path}")
                cleaned_count += 1
            except Exception as e:
                self._log_output(f"删除文件失败 {file_path}: {e}")
        
        self._log_output(f"--- 清理完成，共删除 {cleaned_count} 个文件于 {target_directory} ---")
        if cleaned_count > 0:
            self.master.after(0, lambda: messagebox.showinfo("清理完成", f"在 {target_directory} 中成功删除了 {cleaned_count} 个文件。"))
        else:
            self.master.after(0, lambda: messagebox.showinfo("清理完成", f"在 {target_directory} 中未找到需要清理的文件。"))

    def clean_duplicate_files_manual(self):
        folder_selected = filedialog.askdirectory(title="请选择要清理的专辑文件夹")
        if folder_selected:
            # Run cleaning in a separate thread to avoid blocking UI
            thread = threading.Thread(target=self._clean_files_in_directory, args=(folder_selected,), daemon=True)
            thread.start()
        else:
            self._log_output("未选择文件夹，取消清理操作。")

    def clean_current_album_folder(self):
        album_name = self.album_name_entry.get().strip()
        if not album_name:
            messagebox.showwarning("输入错误", "请输入专辑名 (文件夹名)！")
            self._log_output("错误：未指定专辑文件夹名，无法清理。")
            return

        target_directory = os.path.join('/Users/qiqizhou/bili-dl/', album_name)
        if not os.path.isdir(target_directory):
            messagebox.showerror("错误", f"指定的专辑文件夹不存在或不是一个文件夹：\n{target_directory}")
            self._log_output(f"错误：指定的专辑文件夹不存在或不是一个文件夹：{target_directory}")
            return
        
        self._log_output(f"准备清理当前专辑文件夹: {target_directory}")
        # Run cleaning in a separate thread to avoid blocking UI
        thread = threading.Thread(target=self._clean_files_in_directory, args=(target_directory,), daemon=True)
        thread.start()

    def _rename_files_in_directory(self, target_directory):
        #     def clean_filename(filename):
        #         # Extract the part between parentheses
        #         match = re.search(r'\((P\d+\.\s*\d*\.?\s*(.*?)\))', filename)
        #         if match:
        #             # Get the content after the track number
        #             clean_name = match.group(2).strip()
        #             # Remove the [xx] suffix if present
        #             clean_name = re.sub(r'\[\d+\]', '', clean_name)
        #             # return clean_name + '.mp3'
        #             return clean_name + '.mp4'
            
        #         # replace  [01] to empty
        #         # filename = filename.replace("[01]", "")

            # return filename

        def ai_convert_filename_to_clean_song_name(filename):
            # 
            return filename

        self._log_output(f"--- 开始重命名文件夹中的 MP4 文件: {target_directory} ---")
        renamed_count = 0
        mp4_files = glob.glob(os.path.join(target_directory, "*.mp4"))
        for file_path in mp4_files:
            try:
                base, ext = os.path.splitext(file_path)
                directory_of_base = os.path.dirname(base)
                filename_of_base = os.path.basename(base)
                print(f"directory_of_base: {directory_of_base}")
                print(f"filename_of_base: {filename_of_base}")

                filename_of_base = ai_convert_filename_to_clean_song_name(filename_of_base)
                base = os.path.join(directory_of_base, filename_of_base)
                
                new_file_path = base + ".mp3"

                # Convert mp4 file to mp3
                subprocess.run([
                    'ffmpeg',
                    '-i', file_path,
                    '-vn',  # No video
                    '-acodec', 'libmp3lame',  # Use libmp3lame for MP3 encoding
                    '-ab', '128k',  # Bitrate
                    new_file_path
                ])
                # Delete the original mp4 file
                os.remove(file_path)
                self._log_output(f"已将 MP4 文件转换为 MP3: {file_path} -> {new_file_path}")
                renamed_count += 1
                self._log_output(f"即, 已 '重命名' : {file_path} -> {new_file_path}")
                renamed_count += 1
            except Exception as e:
                self._log_output(f"重命名文件失败 {file_path}: {e}")
        
        self._log_output(f"--- 重命名完成，共重命名 {renamed_count} 个文件于 {target_directory} ---")
        if renamed_count > 0:
            self.master.after(0, lambda: messagebox.showinfo("重命名完成", f"在 {target_directory} 中成功重命名了 {renamed_count} 个 MP4 文件为 MP3。 "))
        else:
            self.master.after(0, lambda: messagebox.showinfo("重命名完成", f"在 {target_directory} 中未找到需要重命名的 MP4 文件。 "))

    def rename_mp4_to_mp3_in_album(self):
        album_name = self.album_name_entry.get().strip()
        if not album_name:
            messagebox.showwarning("输入错误", "请输入专辑名 (文件夹名)！")
            self._log_output("错误：未指定专辑文件夹名，无法重命名文件。")
            return

        target_directory = os.path.join('/Users/qiqizhou/bili-dl/', album_name)
        if not os.path.isdir(target_directory):
            messagebox.showerror("错误", f"指定的专辑文件夹不存在或不是一个文件夹：\n{target_directory}")
            self._log_output(f"错误：指定的专辑文件夹不存在或不是一个文件夹：{target_directory}")
            return
        
        self._log_output(f"准备在当前专辑文件夹中重命名 MP4 文件: {target_directory}")
        thread = threading.Thread(target=self._rename_files_in_directory, args=(target_directory,), daemon=True)
        thread.start()

    def get_video_info(self):
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showwarning("输入错误", "请输入视频 URL 或 ID！")
            return

        # 如果是 ID，尝试构造成标准 URL
        if url.lower().startswith("bv") or url.lower().startswith("av"):
            url = f"https://www.bilibili.com/video/{url}"

        self.output_text.configure(state='normal')
        self.output_text.delete('1.0', tk.END)
        self.output_text.configure(state='disabled')

        command = ['you-get', '-i', url, '-c', self.cookies_path]
        if self.is_playlist_var.get():
            command.append('--playlist')

        # ouput to log 
        self._log_output(f">>> TEST: ..........................")

        thread = threading.Thread(target=self._run_command_in_thread, args=(command,), daemon=True)
        thread.start()

    def _download_and_maybe_clean(self, command, download_path):
        return_code = self._run_command_in_thread(command, download_path)
        if return_code == 0 and self.auto_clean_var.get():
            self._log_output("下载完成，开始自动清理...")
            self._clean_files_in_directory(download_path)
        elif return_code != 0:
            self._log_output("下载失败，跳过自动清理。")

    def download_video(self):
        url = self.url_entry.get().strip()
        album_name = self.album_name_entry.get().strip()

        if not url:
            messagebox.showwarning("输入错误", "请输入视频 URL 或 ID！")
            return
        if not album_name:
            messagebox.showwarning("输入错误", "请输入专辑名 (文件夹名)！")
            return

        # 如果是 ID，尝试构造成标准 URL
        if url.lower().startswith("bv") or url.lower().startswith("av"):
            url = f"https://www.bilibili.com/video/{url}"

        self.output_text.configure(state='normal')
        self.output_text.delete('1.0', tk.END)
        self.output_text.configure(state='disabled')

        # 创建专辑文件夹（如果不存在）
        download_path = os.path.join('/Users/qiqizhou/bili-dl/', album_name) # 下载到当前工作目录下的专辑文件夹
        if not os.path.exists(download_path):
            try:
                os.makedirs(download_path)
                self._log_output(f"创建文件夹: {download_path}")
            except OSError as e:
                self._log_output(f"创建文件夹失败: {e}")
                messagebox.showerror("错误", f"创建文件夹 '{album_name}' 失败: {e}")
                return

        selected_quality = self.quality_var.get()
        format_string = "dash-flv720-AVC" # 默认值
        if selected_quality == "720p":
            format_string = "dash-flv720-AVC"
        elif selected_quality == "480p":
            format_string = "dash-flv480-AVC" # 假设的格式，you-get 可能有不同命名
        elif selected_quality == "360p":
            format_string = "dash-flv360-AVC" # 假设的格式

        command = ['you-get', f'--format={format_string}']
        if self.is_playlist_var.get():
            command.append('--playlist')
        command.extend([url, '-c', self.cookies_path])
        
        # you-get 默认下载到当前目录，所以我们用 cwd 参数指定下载目录
        thread = threading.Thread(target=self._download_and_maybe_clean, args=(command, download_path), daemon=True)
        thread.start()

if __name__ == "__main__":
    root = tk.Tk()
    app = BiliDownloaderApp(root)
    root.mainloop()
