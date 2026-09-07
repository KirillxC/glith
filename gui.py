import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk, ImageChops, ImageGrab
import random
import io
import subprocess
import os
import tempfile

class Tooltip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip = None
        self.widget.bind("<Enter>", self.show)
        self.widget.bind("<Leave>", self.hide)

    def show(self, event=None):
        x, y, _, _ = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 25
        self.tooltip = tk.Toplevel(self.widget)
        self.tooltip.wm_overrideredirect(True)
        self.tooltip.wm_geometry(f"+{x}+{y}")
        label = tk.Label(self.tooltip, text=self.text, background="#ffffe0", relief="solid", borderwidth=1)
        label.pack()

    def hide(self, event=None):
        if self.tooltip:
            self.tooltip.destroy()
            self.tooltip = None

class GlitchApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Glitch Art Pro")
        self.geometry("900x750")

        self.original_img = None
        self.glitched_img = None

        self.setup_ui()

    def setup_ui(self):
        style = ttk.Style()
        style.theme_use('clam')

        # Main Layout
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=0) # Controls
        self.rowconfigure(1, weight=1) # Image

        # Toolbar
        toolbar = ttk.Frame(self, padding=5)
        toolbar.grid(row=0, column=0, sticky="ew")

        b_open = ttk.Button(toolbar, text="📂", width=3, command=self.select_file)
        b_open.pack(side=tk.LEFT, padx=2)
        Tooltip(b_open, "Open File")
        
        b_paste = ttk.Button(toolbar, text="📋", width=3, command=self.paste_from_clipboard)
        b_paste.pack(side=tk.LEFT, padx=2)
        Tooltip(b_paste, "Paste from Clipboard")
        
        self.path_entry = ttk.Entry(toolbar)
        self.path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        ttk.Button(toolbar, text="Load", command=self.load_image).pack(side=tk.LEFT, padx=5)

        # Image Display Area
        self.image_container = tk.Frame(self, bg="#2d2d2d")
        self.image_container.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        self.image_label = tk.Label(self.image_container, text="Drag & Drop / Paste (Ctrl+V) / Load", bg="#2d2d2d", fg="#aaa")
        self.image_label.pack(expand=True)
        
        # Action Buttons Area (Bottom)
        actions = ttk.Frame(self, padding=10)
        actions.grid(row=2, column=0, sticky="ew")
        
        self.intensity_slider = ttk.Scale(actions, from_=0, to=100, orient=tk.HORIZONTAL)
        self.intensity_slider.set(20)
        self.intensity_slider.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        b_glitch = ttk.Button(actions, text="⚡ Glitch", command=self.glitch_and_display)
        b_glitch.pack(side=tk.LEFT, padx=5)
        Tooltip(b_glitch, "Apply Glitch Effect")
        
        b_copy = ttk.Button(actions, text="💾 Copy", command=self.copy_to_clipboard)
        b_copy.pack(side=tk.LEFT, padx=5)
        Tooltip(b_copy, "Copy Result to Clipboard")
        
        # Clear Button (Bottom Right)
        b_clear = ttk.Button(actions, text="❌", width=3, command=self.clear_image)
        b_clear.pack(side=tk.RIGHT, padx=5)
        Tooltip(b_clear, "Clear Image")
        
        # Keyboard Shortcuts
        self.bind('<Control-v>', lambda e: self.paste_from_clipboard())
        self.bind('<Control-V>', lambda e: self.paste_from_clipboard())

    # --- Methods ---
    def clear_image(self):
        self.original_img = None
        self.glitched_img = None
        self.path_entry.delete(0, tk.END)
        self.image_label.config(image='', text="Paste (Ctrl+V) or Load Image")

    def paste_from_clipboard(self):
        img = ImageGrab.grabclipboard()
        if isinstance(img, Image.Image):
            self.original_img = img
            self.display_image(img)
            self.path_entry.delete(0, tk.END)
            self.path_entry.insert(0, "Clipboard Image")
        else:
            messagebox.showwarning("Warning", "No image found in clipboard")

    def select_file(self):
        path = filedialog.askopenfilename()
        if path:
            self.path_entry.delete(0, tk.END)
            self.path_entry.insert(0, path)
            self.load_image()

    def load_image(self):
        path = self.path_entry.get().strip()
        try:
            self.original_img = Image.open(path)
            self.display_image(self.original_img)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load: {e}")

    def display_image(self, img):
        display_img = img.copy()
        display_img.thumbnail((800, 500))
        self.glitched_img_tk = ImageTk.PhotoImage(display_img)
        self.image_label.config(image=self.glitched_img_tk, text="")
        self.glitched_img = img

    def glitch_and_display(self):
        if not self.original_img: return
        intensity = self.intensity_slider.get() / 100.0
        self.glitched_img = self.apply_artistic_glitch(self.original_img.copy(), intensity)
        self.display_image(self.glitched_img)

    def apply_artistic_glitch(self, img, intensity):
        img = img.convert("RGB")
        width, height = img.size
        r, g, b = img.split()
        offset = int(intensity * 40)
        r = ImageChops.offset(r, offset, 0)
        b = ImageChops.offset(b, -offset, 0)
        img = Image.merge("RGB", (r, g, b))
        if intensity > 0.2:
            for _ in range(int(intensity * 1000)):
                x, y = random.randint(0, width - 10), random.randint(0, height - 10)
                box = (x, y, x + 5, y + 5)
                block = img.crop(box)
                img.paste(block, (x + random.randint(-3, 3), y + random.randint(-3, 3)))
        return img

    def copy_to_clipboard(self):
        if not self.glitched_img: return
        try:
            tmp_file = tempfile.NamedTemporaryFile(suffix='.bmp', delete=False)
            tmp_path = tmp_file.name
            self.glitched_img.convert("RGB").save(tmp_path, "BMP")
            subprocess.run(['xclip', '-selection', 'clipboard', '-t', 'image/bmp', tmp_path], check=True)
            os.remove(tmp_path)
            messagebox.showinfo("Success", "Copied to clipboard!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to copy: {e}")

if __name__ == "__main__":
    app = GlitchApp()
    app.mainloop()
