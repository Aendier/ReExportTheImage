import os
import tkinter as tk
from PIL import Image
from tkinterdnd2 import TkinterDnD
from tkinter import filedialog, messagebox, ttk


def on_drop(event):
    """处理拖放文件事件"""
    file_paths = event.data.split() if hasattr(event.data, 'split') else [event.data]
    image_exts = ['.png', '.jpg', '.jpeg', '.gif', '.bmp']
    image_paths = [
        path.strip('{}') for path in file_paths
        if any(path.lower().endswith(ext) for ext in image_exts)
    ]

    if image_paths:
        for path in image_paths:
            listbox.insert(tk.END, path)
    else:
        messagebox.showwarning("提示", "拖入的文件不是图片！")


def browse_file():
    """浏览并选择图片文件"""
    file_paths = filedialog.askopenfilenames(
        filetypes=[("图片文件", "*.png;*.jpg;*.jpeg;*.gif;*.bmp")]
    )
    for file_path in file_paths:
        listbox.insert(tk.END, file_path)


def import_from_text():
    """从文本文件导入图片路径"""
    text_path = filedialog.askopenfilename(
        filetypes=[("文本文件", "*.txt")]
    )
    if not text_path:
        return

    try:
        with open(text_path, 'r', encoding='utf-8') as f:
            for line in f:
                path = line.strip()
                if path:  # 跳过空行
                    listbox.insert(tk.END, path)
    except Exception as e:
        messagebox.showerror("错误", f"读取文件失败: {str(e)}")


def format_size(size):
    """格式化文件大小显示"""
    for unit in ['B', 'KB', 'MB']:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} GB"


def reexport_keep_format(base_path, image_paths, compress_level):
    """
    重新导出图片并保持原始格式，返回处理前后的文件大小信息
    """
    results = {
        "processed_files": [],
        "total_original_size": 0,
        "total_new_size": 0,
        "skipped_files": []
    }

    for img_path in image_paths:
        file_info = {
            "filename": "",
            "original_size": 0,
            "new_size": 0,
            "success": False,
            "message": ""
        }

        try:
            img_path = img_path.strip()
            if not img_path:
                continue

            # 处理路径
            full_path = os.path.join(base_path, img_path) if base_path else img_path
            full_path = os.path.abspath(full_path)
            filename = os.path.basename(full_path)
            file_info["filename"] = filename

            if not os.path.exists(full_path):
                file_info["message"] = f"文件不存在: {full_path}"
                results["skipped_files"].append(file_info)
                continue

            original_size = os.path.getsize(full_path)
            file_info["original_size"] = original_size
            results["total_original_size"] += original_size

            ext = os.path.splitext(full_path)[1].lower()

            # 只处理支持的格式
            if ext not in ('.png', '.jpg', '.jpeg'):
                file_info["message"] = f"跳过不支持格式的文件: {filename}"
                results["skipped_files"].append(file_info)
                continue

            with Image.open(full_path) as img:
                temp_path = f"{full_path}.tmp"

                try:
                    if ext == '.png':
                        img.save(temp_path, format='PNG', optimize=True, compress_level=int(compress_level))
                    else:  # jpg/jpeg
                        img.save(temp_path, format='JPEG', quality=100, optimize=True, subsampling=0)

                    if os.path.exists(temp_path):
                        os.replace(temp_path, full_path)
                        new_size = os.path.getsize(full_path)
                        file_info["new_size"] = new_size
                        file_info["success"] = True
                        file_info["message"] = "处理成功"
                        results["total_new_size"] += new_size
                    else:
                        file_info["message"] = "处理失败: 临时文件未创建"

                except Exception as save_error:
                    file_info["message"] = f"保存错误: {str(save_error)}"
                    if os.path.exists(temp_path):
                        os.remove(temp_path)

        except Exception as e:
            file_info["message"] = f"处理出错: {str(e)}"

        results["processed_files"].append(file_info)

    return results


def show_result_window(result):
    """显示处理结果的窗口"""
    result_window = tk.Toplevel()
    result_window.title("处理结果")
    result_window.geometry("800x600")

    # 主框架
    main_frame = ttk.Frame(result_window)
    main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    # 统计信息
    stats_frame = ttk.LabelFrame(main_frame, text="统计信息")
    stats_frame.pack(fill=tk.X, pady=5)

    original_size = format_size(result["total_original_size"])
    new_size = format_size(result["total_new_size"])
    saved = format_size(result["total_original_size"] - result["total_new_size"])
    ratio = (1 - result["total_new_size"] / result["total_original_size"]) * 100 if result[
                                                                                        "total_original_size"] > 0 else 0

    stats_labels = [
        f"处理文件数: {len(result['processed_files'])}",
        f"跳过文件数: {len(result['skipped_files'])}",
        f"原始总大小: {original_size}",
        f"处理后总大小: {new_size}",
        f"节省空间: {saved} ({ratio:.2f}%)"
    ]

    for label in stats_labels:
        ttk.Label(stats_frame, text=label).pack(anchor=tk.W)

    # 处理结果表格
    processed_frame = ttk.LabelFrame(main_frame, text="处理结果")
    processed_frame.pack(fill=tk.BOTH, expand=True, pady=5)

    # 创建Treeview表格
    tree = ttk.Treeview(processed_frame, columns=("filename", "original", "new", "saved", "status"), show="headings")
    tree.heading("filename", text="文件名")
    tree.heading("original", text="原始大小")
    tree.heading("new", text="新大小")
    tree.heading("saved", text="节省空间")
    tree.heading("status", text="状态")

    tree.column("filename", width=200)
    tree.column("original", width=100, anchor=tk.E)
    tree.column("new", width=100, anchor=tk.E)
    tree.column("saved", width=100, anchor=tk.E)
    tree.column("status", width=250)

    # 添加滚动条
    scrollbar = ttk.Scrollbar(processed_frame, orient=tk.VERTICAL, command=tree.yview)
    tree.configure(yscrollcommand=scrollbar.set)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    tree.pack(fill=tk.BOTH, expand=True)

    # 添加数据
    for file in result["processed_files"]:
        saved_size = file["original_size"] - file["new_size"] if file["success"] else 0
        tree.insert("", tk.END, values=(
            file["filename"],
            format_size(file["original_size"]),
            format_size(file["new_size"]) if file["success"] else "-",
            format_size(saved_size) if file["success"] else "-",
            file["message"]
        ))

    # 跳过文件列表
    if result["skipped_files"]:
        skipped_frame = ttk.LabelFrame(main_frame, text="跳过的文件")
        skipped_frame.pack(fill=tk.X, pady=5)

        skipped_text = tk.Text(skipped_frame, height=4, wrap=tk.WORD)
        skipped_scroll = ttk.Scrollbar(skipped_frame, orient=tk.VERTICAL, command=skipped_text.yview)
        skipped_text.configure(yscrollcommand=skipped_scroll.set)
        skipped_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        skipped_text.pack(fill=tk.X)

        for file in result["skipped_files"]:
            skipped_text.insert(tk.END, f"{file['filename']}: {file['message']}\n")
        skipped_text.configure(state=tk.DISABLED)


def export_images():
    """导出图片并显示结果窗口"""
    if listbox.size() == 0:
        messagebox.showwarning("警告", "请先添加要处理的图片")
        return

    # 禁用导出按钮避免重复操作
    btn_export.config(state=tk.DISABLED)
    root.update()  # 立即更新界面

    try:
        # 创建处理中对话框
        progress = tk.Toplevel(root)
        progress.title("处理中...")
        progress.geometry("300x100")
        progress.resizable(False, False)
        ttk.Label(progress, text="正在处理图片，请稍候...").pack(pady=20)
        progress.grab_set()
        root.update()

        # 获取所有图片路径
        image_paths = listbox.get(0, tk.END)

        # 调用处理函数
        result = reexport_keep_format(
            entry_prefix_path.get().strip(),
            image_paths,
            compress_level_combo.get()
        )

        # 关闭处理中对话框
        progress.destroy()

        # 显示结果窗口
        show_result_window(result)

    except Exception as e:
        messagebox.showerror("错误", f"处理过程中发生错误: {str(e)}")
    finally:
        # 重新启用导出按钮
        btn_export.config(state=tk.NORMAL)


# 创建主窗口
root = TkinterDnD.Tk()
style = ttk.Style()
style.theme_use("clam")

root.title("图片重新导出工具")
root.geometry("600x400")

# ========== 主框架 ==========
main_frame = ttk.Frame(root)
main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

# 标签
ttk.Label(main_frame, text="请拖入图片文件或手动选择图片 ↓").pack(pady=5, padx=5, anchor=tk.W)

# 列表框
listbox = tk.Listbox(main_frame, width=80, selectmode=tk.EXTENDED)
listbox.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
listbox.drop_target_register('DND_Files')
listbox.dnd_bind('<<Drop>>', on_drop)

# ========== 按钮框架1 ==========
frame1 = ttk.Frame(main_frame)
frame1.pack(fill=tk.X, pady=5)

btn_clear = ttk.Button(frame1, text="清空列表", command=lambda: listbox.delete(0, tk.END))
btn_clear.pack(side=tk.LEFT, padx=5)

# ========== 按钮框架2 ==========
frame2 = ttk.Frame(main_frame)
frame2.pack(fill=tk.X, pady=5)

btn_browse = ttk.Button(frame2, text="手动选择图片", command=browse_file)
btn_browse.pack(side=tk.LEFT, padx=5)

btn_import_text = ttk.Button(frame2, text="从文本导入路径", command=import_from_text)
btn_import_text.pack(side=tk.LEFT, padx=5)

# 前缀路径输入框
label_prefix_path = ttk.Label(frame2, text="前缀路径:")
label_prefix_path.pack(side=tk.RIGHT, padx=5)
entry_prefix_path = ttk.Entry(frame2, width=38)
entry_prefix_path.pack(side=tk.RIGHT, padx=5)

# ========== 压缩级别设置 ==========
frame3 = ttk.Frame(main_frame)
frame3.pack(fill=tk.X)

ttk.Label(frame3, text="请选择压缩等级:").pack(side=tk.LEFT, padx=5)
compress_level_combo = ttk.Combobox(frame3, values=["1", "2", "3", "4", "5", "6", "7", "8", "9"], width=3)
compress_level_combo.pack(side=tk.LEFT, padx=5)
compress_level_combo.set("6")

btn_export = ttk.Button(frame3, text="导出图片", command=export_images)
btn_export.pack(side=tk.RIGHT, padx=5)

# 压缩级别提示
frame4 = ttk.Frame(main_frame)
frame4.pack(fill=tk.X)
ttk.Label(frame4, text="（压缩级别不影响图像质量，只影响编码效率）").pack(side=tk.LEFT)

root.mainloop()