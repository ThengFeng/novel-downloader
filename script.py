import tkinter as tk
from tkinter import messagebox, filedialog, scrolledtext
import requests
from bs4 import BeautifulSoup
import re
import os
import time

chapters = []
base_url = ''
book_title = ''

def get_chapters():
    global chapters, base_url, book_title
    url = url_entry.get().strip()
    if not url:
        messagebox.showwarning("警告", "请输入目录页链接")
        return

    try:
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
        response.encoding = 'gb2312'
        soup = BeautifulSoup(response.text, 'html.parser')

        base_url = url.rsplit('/', 1)[0] + '/'
        title_tag = soup.find('title')
        book_title = title_tag.text.split(',')[0].strip() if title_tag else '小说'

        folder_entry.delete(0, tk.END)
        folder_entry.insert(0, book_title)

        links = soup.select('a[href$=".html"]')
        chapters = []
        chapter_listbox.delete(0, tk.END)
        for link in links:
            href = link.get('href')
            title = link.text.strip()
            if href.endswith('.html'):
                chapters.append((base_url + href, title))
                chapter_listbox.insert(tk.END, title)

        if auto_select_all.get():
            select_all()
        messagebox.showinfo("成功", f"获取 {len(chapters)} 章：{book_title}")
    except Exception as e:
        messagebox.showerror("错误", str(e))

def select_all():
    chapter_listbox.select_set(0, tk.END)

def clear_selection():
    chapter_listbox.select_clear(0, tk.END)

def toggle_select_all():
    if auto_select_all.get():
        select_all()
    else:
        clear_selection()

def download_selected():
    selected_indices = chapter_listbox.curselection()
    if not selected_indices:
        messagebox.showwarning("提示", "请选择要下载的章节")
        return

    folder_name = folder_entry.get().strip()
    if not folder_name:
        messagebox.showwarning("提示", "请输入保存文件夹名称")
        return

    save_dir = filedialog.askdirectory(title="选择保存路径")
    if not save_dir:
        return

    full_path = save_dir  # 不再自动创建书名子目录
    os.makedirs(full_path, exist_ok=True)

    selected_chapters = [chapters[i] for i in selected_indices]

    if len(selected_chapters) == 1:
        # 单章：文件名 = 章节名
        url, title = selected_chapters[0]
        filename = f"{full_path}/{title}.txt"
        download_single_chapter(url, title, filename)
    else:
        # 多章：每50章合成一个txt
        for i in range(0, len(selected_chapters), 50):
            part = selected_chapters[i:i+50]
            start = i + 1
            end = i + len(part)
            filename = f"{full_path}/第{start:03d}章_至第{end:03d}章.txt"
            with open(filename, 'w', encoding='utf-8') as f:
                for idx, (url, title) in enumerate(part, start=start):
                    content = download_chapter_content(url, title)
                    if content:
                        f.write(f"{title}\n{'=' * len(title)}\n{content}\n\n")
                        log_box.insert(tk.END, f"✅ 下载：{title}\n")
                        log_box.yview_moveto(1.0)
                        root.update()
                        time.sleep(0.2)

    messagebox.showinfo("完成", f"保存完成，共 {len(selected_chapters)} 章")

def download_single_chapter(url, title, filename):
    content = download_chapter_content(url, title)
    if content:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"{title}\n{'=' * len(title)}\n{content}\n")
        log_box.insert(tk.END, f"✅ 已保存为：{title}.txt\n")
        log_box.yview_moveto(1.0)

def download_chapter_content(url, title):
    try:
        r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
        r.encoding = 'gb2312'
        matches = re.findall(r'&nbsp;&nbsp;&nbsp;&nbsp;(.*?)<br\s*/?>', r.text, re.DOTALL)
        paragraphs = [BeautifulSoup(p, 'html.parser').text.strip() for p in matches]
        content = '\n\n'.join(paragraphs)
        return content
        
    except Exception as e:
        log_box.insert(tk.END, f"❌ 下载失败：{title} -> {e}\n")
        root.update()
        return None

# === GUI ===
root = tk.Tk()
root.title("📘 小说下载器（自定义路径 + 单章/多章分批）")

auto_select_all = tk.BooleanVar(value=False)

tk.Label(root, text="目录页链接：").pack()
url_entry = tk.Entry(root, width=60)
url_entry.pack()

tk.Checkbutton(root, text="自动全选章节", variable=auto_select_all, command=toggle_select_all).pack(pady=2)

tk.Button(root, text="获取章节列表", command=get_chapters).pack(pady=5)

tk.Label(root, text="章节列表（可多选）：").pack()
chapter_listbox = tk.Listbox(root, selectmode=tk.MULTIPLE, width=60, height=15)
chapter_listbox.pack()

tk.Frame(root, height=5).pack()
tk.Button(root, text="全选", command=select_all).pack(side=tk.LEFT, padx=10)
tk.Button(root, text="取消全选", command=clear_selection).pack(side=tk.LEFT)

tk.Label(root, text="\n保存文件夹名称（用于单章文件命名参考）：").pack()
folder_entry = tk.Entry(root, width=40)
folder_entry.pack()

tk.Button(root, text="开始下载", command=download_selected).pack(pady=10)

tk.Label(root, text="下载日志：").pack()
log_box = scrolledtext.ScrolledText(root, width=70, height=12)
log_box.pack()

root.mainloop()
