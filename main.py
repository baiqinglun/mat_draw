import os
import pandas as pd
import matplotlib.pyplot as plt
import tkinter as tk
from tkinter import messagebox, filedialog,ttk
from PIL import Image, ImageTk
import numpy as np
import scipy.io
import json

def load_cache(file_path):
    """从 JSON 文件加载缓存数据"""
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            return json.load(f)
    return {}

def save_cache(file_path, data):
    """将缓存数据保存到 JSON 文件"""
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=4)

class CurvePlotterApp:
    def __init__(self, master):
        self.master = master
        self.cache_file = 'app_cache.json'  # 缓存文件名
        self.cache = load_cache(self.cache_file)  # 加载缓存

        # 初始化路径
        self.last_opened_path = self.cache.get('last_opened_path', '')
        self.save_dir = self.cache.get('save_dir', '')

        self.master.title("Curve Plotter")

        # 设置输出目录
        self.output_dir = 'csv_output'
        self.csv_files = []
        self.images = []  # 存储绘制的图像

        # 创建界面元素
        self.convert_button = tk.Button(master, text="转换 .mat 为 .csv", command=self.convert_mat_to_csv)
        self.convert_button.grid(row=0, column=0, padx=5, pady=5)

        self.label = tk.Label(master, text="选择绘制方式:")
        self.label.grid(row=1, column=0, sticky='w', padx=5, pady=5)

        self.plot_type_var = tk.StringVar(value='1')
        self.radio1 = tk.Radiobutton(master, text="分别绘制", variable=self.plot_type_var, value='1')
        self.radio2 = tk.Radiobutton(master, text="组合绘制", variable=self.plot_type_var, value='2')
        self.radio1.grid(row=1, column=1, padx=5)
        self.radio2.grid(row=1, column=2, padx=5)

        self.all_or_some_var = tk.StringVar(value='n')
        self.all_button = tk.Radiobutton(master, text="全部绘制", variable=self.all_or_some_var, value='y', command=self.select_all_files)
        self.some_button = tk.Radiobutton(master, text="选择部分绘制", variable=self.all_or_some_var, value='n', command=self.clear_selection)
        self.all_button.grid(row=2, column=1, padx=5)
        self.some_button.grid(row=2, column=2, padx=5)

        self.select_button = tk.Button(master, text="选择 CSV 文件", command=self.load_csv_files)
        self.select_button.grid(row=3, column=0, padx=5, pady=5)

        self.save_button = tk.Button(master, text="选择保存位置", command=self.select_save_directory)
        self.save_button.grid(row=3, column=1, padx=5, pady=5)

        self.plot_button = tk.Button(master, text="绘制图形", command=self.plot_curves)
        self.plot_button.grid(row=3, column=2, padx=5, pady=5)

        self.save_path_label = tk.Label(master, text="保存路径: 尚未选择")
        self.save_path_label.grid(row=4, column=0, columnspan=3, sticky='w', padx=5, pady=5)

        self.file_listbox = tk.Listbox(master, selectmode=tk.MULTIPLE)
        self.file_listbox.grid(row=5, column=0, columnspan=3, sticky='nsew', padx=5, pady=5)

        # 创建进度条
        self.progress = ttk.Progressbar(master, orient="horizontal", length=300, mode="determinate")
        self.progress.grid(row=6, column=0, columnspan=3, pady=10)

        # 创建滚动区域
        self.scroll_frame = tk.Frame(master)
        self.scroll_frame.grid(row=0, column=3, rowspan=5, sticky='nsew', padx=5, pady=5)

        self.canvas = tk.Canvas(self.scroll_frame)
        self.scrollbar = tk.Scrollbar(self.scroll_frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        # 调整行列权重
        master.grid_rowconfigure(4, weight=1)
        master.grid_columnconfigure(0, weight=1)
        master.grid_columnconfigure(1, weight=1)
        master.grid_columnconfigure(2, weight=1)
        master.grid_columnconfigure(3, weight=1)

    def convert_mat_to_csv(self):
        # 选择 .mat 文件
        mat_file_path = filedialog.askopenfilename(filetypes=[("MAT files", "*.mat")])
        if not mat_file_path:
            return  # 用户取消选择

        # 创建输出目录
        output_dir = 'csv_output'
        os.makedirs(output_dir, exist_ok=True)

        # 读取 .mat 文件
        data = scipy.io.loadmat(mat_file_path)

        caijilv = 200000  # 采集率

        # 打印所有变量的名称和大小
        for variable_name in data:
            if not variable_name.startswith('__'):  # 排除系统变量
                variable_data = data[variable_name]

                # 生成时间数组
                time = np.arange(0, len(variable_data) / caijilv, 1 / caijilv)

                # 处理变量名，去掉 '\x00'
                variable_name1 = variable_name.replace('\x00', '')

                # 创建 DataFrame，并将时间数组作为第一列
                df = pd.DataFrame(variable_data)
                df.insert(0, 'Time', time)  # 将时间数组插入为第一列

                # 保存为 CSV 文件
                csv_file_path = os.path.join(output_dir, f"{variable_name1}.csv")
                print(f"保存文件: {csv_file_path}")
                df.to_csv(csv_file_path, index=False, header=True)  # 不保存索引，保存列名

        messagebox.showinfo("信息", "转换完成，所有文件已保存。")


    def load_csv_files(self):
        # 选择文件夹并加载 CSV 文件
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            self.output_dir = folder_selected
            self.csv_files = [f for f in os.listdir(self.output_dir) if f.endswith('.csv')]
            self.file_listbox.delete(0, tk.END)  # 清空列表框
            for file in self.csv_files:
                self.file_listbox.insert(tk.END, file)  # 添加文件到列表框

    def select_all_files(self):
        # 自动选择所有文件
        self.file_listbox.select_set(0, tk.END)  # 选择列表框中的所有项

    def clear_selection(self):
        # 清空列表框中的选择
        self.file_listbox.selection_clear(0, tk.END)

    def select_save_directory(self):
        # 选择保存目录
        self.save_dir = filedialog.askdirectory(title="选择保存图像的位置")
        if self.save_dir:
            self.save_path_label.config(text=f"保存路径: {self.save_dir}")  # 更新保存路径标签

    def plot_curves(self):
        # 清空之前的图像
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        selected_indices = self.file_listbox.curselection()
        if not selected_indices and self.all_or_some_var.get() == 'n':
            messagebox.showwarning("警告", "请先选择 CSV 文件。")
            return

        if not self.save_dir:
            messagebox.showwarning("警告", "请先选择保存位置。")
            return

        self.images.clear()  # 清空之前的图像

        if self.plot_type_var.get() == '1':
            if self.all_or_some_var.get() == 'y':
                selected_indices = range(len(self.csv_files))  # 选择所有文件

            # 初始化进度条
            self.progress['maximum'] = len(selected_indices)
            self.progress['value'] = 0

            for index in selected_indices:
                self.plot_single_curve(index)
                self.progress['value'] += 1  # 更新进度条
                self.master.update_idletasks()  # 更新界面

            self.progress['value'] = 0  # 重置进度条

            messagebox.showinfo("信息", "所有图像已成功保存。")

        elif self.plot_type_var.get() == '2':
            self.plot_combined_curve(selected_indices)

    def plot_single_curve(self, index):
        csv_file = self.csv_files[index]
        csv_file_path = os.path.join(self.output_dir, csv_file)

        # 读取 CSV 文件
        df = pd.read_csv(csv_file_path)
        time = df['Time']
        data_columns = df.columns[1:]

        plt.figure(figsize=(10, 6))
        for column in data_columns:
            plt.plot(time, df[column], label=column)

        plt.title(f'Curve Plot for {csv_file}')
        plt.xlabel('Time (s)')
        plt.ylabel('Value')
        plt.legend()
        image_path = os.path.join(self.save_dir, f"{csv_file.replace('.csv', '.png')}")
        plt.savefig(image_path)
        plt.close()

        # 加载并显示图像
        self.display_image(image_path)

    def plot_combined_curve(self, selected_indices):
        plt.figure(figsize=(10, 6))

        for index in selected_indices:
            csv_file = self.csv_files[index]
            csv_file_path = os.path.join(self.output_dir, csv_file)

            df = pd.read_csv(csv_file_path)
            time = df['Time']
            data_columns = df.columns[1:]

            for column in data_columns:
                plt.plot(time, df[column], label=f"{csv_file} - {column}")

        plt.title('Combined Curve Plot')
        plt.xlabel('Time (s)')
        plt.ylabel('Value')
        plt.legend()
        combined_image_path = os.path.join(self.save_dir, 'combined_plot.png')
        plt.savefig(combined_image_path)
        plt.close()

        # 加载并显示组合图像
        self.display_image(combined_image_path)

        messagebox.showinfo("信息", "组合图像已成功保存。")

    def display_image(self, image_path):
        # 加载图像并显示
        image = Image.open(image_path)
        image.thumbnail((300, 200))  # 调整图像大小
        photo = ImageTk.PhotoImage(image)

        label = tk.Label(self.scrollable_frame, image=photo)
        label.image = photo  # 保持引用
        label.pack(pady=5)

        # 为图像添加点击事件
        label.bind("<Button-1>", lambda e: self.open_image_viewer(image_path))

    def open_image_viewer(self, image_path):
        viewer = ImageViewer(image_path)

    def select_file(self):
        """选择文件并更新缓存"""
        file_path = filedialog.askopenfilename(initialdir=self.last_opened_path)
        if file_path:
            self.last_opened_path = os.path.dirname(file_path)
            self.cache['last_opened_path'] = self.last_opened_path
            save_cache(self.cache_file, self.cache)  # 保存缓存
             # 更新标签显示选择的文件路径
            self.file_path_label.config(text=f"选择的文件路径: {file_path}")

    def select_save_directory(self):
        """选择保存目录并更新缓存"""
        directory = filedialog.askdirectory(initialdir=self.save_dir)
        if directory:
            self.save_dir = directory
            self.cache['save_dir'] = self.save_dir
            save_cache(self.cache_file, self.cache)  # 保存缓存

import subprocess
import platform

class ImageViewer:
    def __init__(self, image_path):
        self.image_path = image_path
        self.open_image_with_default_viewer()

    def open_image_with_default_viewer(self):
        # 根据操作系统选择打开方式
        if platform.system() == "Windows":
            subprocess.run(["start", "", self.image_path], shell=True)
        elif platform.system() == "Darwin":  # macOS
            subprocess.run(["open", self.image_path])
        else:  # Linux
            subprocess.run(["xdg-open", self.image_path])

if __name__ == "__main__":
    root = tk.Tk()
    app = CurvePlotterApp(root)
    root.mainloop()
