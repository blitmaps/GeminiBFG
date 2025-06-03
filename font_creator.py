from PIL import Image, ImageDraw, ImageFont, ImageTk
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import os
import math

class FontRasterizerApp:
    def __init__(self, master):
        self.master = master
        master.title("Font Sheet Rasterizer")
        master.geometry("1000x850") # Increased height for new controls
        master.resizable(True, True)

        master.grid_rowconfigure(2, weight=1) # Image frame will expand
        master.grid_columnconfigure(0, weight=1)

        # --- Model Variables ---
        self.font_path = tk.StringVar()
        self.font_size = tk.IntVar(value=16)
        self.bg_color = tk.StringVar(value="#000000")
        self.text_color = tk.StringVar(value="#FFFFFF")
        self.grid_line_color = "grey"

        self.start_char_code = tk.IntVar(value=32)
        self.end_char_code = tk.IntVar(value=126)
        self.start_char_preview = tk.StringVar()
        self.end_char_preview = tk.StringVar()
        self.start_char_code.trace_add("write", self._update_char_previews_and_validate)
        self.end_char_code.trace_add("write", self._update_char_previews_and_validate)

        self.grid_columns = tk.IntVar(value=16)
        self.cell_width = tk.IntVar(value=16)
        self.cell_height = tk.IntVar(value=16)
        self.offset_x = tk.IntVar(value=1)
        self.offset_y = tk.IntVar(value=1)
        self.show_grid = tk.BooleanVar(value=True)

        # --- Viewport/Zoom Variables ---
        self.fit_to_screen = tk.BooleanVar(value=True)
        self.fit_to_screen.trace_add("write", self._on_fit_to_screen_change)
        self.zoom_level = 1.0
        self.zoom_percent = tk.StringVar(value="100%")
        self.pan_start_x = 0
        self.pan_start_y = 0
        self.view_offset_x = 0
        self.view_offset_y = 0

        self.font_sheet_image = None
        self.clean_font_sheet_image = None

        self.create_widgets()
        self.load_initial_font_path()
        self._update_char_previews_and_validate()

    def load_initial_font_path(self):
        # (This function is unchanged)
        system_font_path = None
        potential_paths = [
            "C:/Windows/Fonts/consola.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
            "/System/Library/Fonts/Menlo.ttc", "/usr/share/fonts/truetype/ubuntu/UbuntuMono-R.ttf",
            "/usr/share/fonts/truetype/freefont/FreeMono.ttf",
        ]
        for p in potential_paths:
            if os.path.exists(p):
                system_font_path = p
                break
        if system_font_path:
            self.font_path.set(system_font_path)
        else:
            messagebox.showwarning("Font Not Found", "Could not find a common system font. Please manually select a mono-spaced font file.")

    def create_widgets(self):
        # --- Top Controls ---
        main_controls_frame = ttk.Frame(self.master)
        main_controls_frame.grid(row=0, column=0, padx=10, pady=(10,0), sticky="ew")
        
        # (Font & Character Range Frame is unchanged)
        font_color_frame = ttk.LabelFrame(main_controls_frame, text="Font & Character Range", padding="10")
        font_color_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        font_color_frame.grid_columnconfigure(1, weight=1)
        ttk.Label(font_color_frame, text="Font File:").grid(row=0, column=0, sticky="w", padx=5)
        ttk.Entry(font_color_frame, textvariable=self.font_path, state='readonly').grid(row=0, column=1, columnspan=2, sticky="ew", padx=5)
        ttk.Button(font_color_frame, text="...", command=self.browse_font, width=3).grid(row=0, column=3, padx=5)
        ttk.Label(font_color_frame, text="Font Size:").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        ttk.Spinbox(font_color_frame, from_=8, to_=100, textvariable=self.font_size, width=5).grid(row=1, column=1, sticky="w", padx=5)
        ttk.Label(font_color_frame, text="Start Char (Dec):").grid(row=2, column=0, sticky="w", padx=5, pady=2)
        self.start_char_spinbox = ttk.Spinbox(font_color_frame, from_=0, to_=65535, textvariable=self.start_char_code, width=7)
        self.start_char_spinbox.grid(row=2, column=1, sticky="w", padx=5)
        ttk.Label(font_color_frame, textvariable=self.start_char_preview, font=("Arial", 14, "bold")).grid(row=2, column=2, sticky="w")
        ttk.Label(font_color_frame, text="End Char (Dec):").grid(row=3, column=0, sticky="w", padx=5, pady=2)
        self.end_char_spinbox = ttk.Spinbox(font_color_frame, from_=0, to_=65535, textvariable=self.end_char_code, width=7)
        self.end_char_spinbox.grid(row=3, column=1, sticky="w", padx=5)
        ttk.Label(font_color_frame, textvariable=self.end_char_preview, font=("Arial", 14, "bold")).grid(row=3, column=2, sticky="w")
        ttk.Label(font_color_frame, text="BG Color:").grid(row=4, column=0, sticky="w", padx=5, pady=2)
        ttk.Entry(font_color_frame, textvariable=self.bg_color, width=10).grid(row=4, column=1, sticky="w", padx=5)
        ttk.Label(font_color_frame, text="Text Color:").grid(row=5, column=0, sticky="w", padx=5, pady=2)
        ttk.Entry(font_color_frame, textvariable=self.text_color, width=10).grid(row=5, column=1, sticky="w", padx=5)

        # (Grid & Layout Frame is unchanged)
        grid_layout_frame = ttk.LabelFrame(main_controls_frame, text="Grid & Layout", padding="10")
        grid_layout_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))
        ttk.Label(grid_layout_frame, text="Grid Columns:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        ttk.Spinbox(grid_layout_frame, from_=1, to_=64, textvariable=self.grid_columns, width=5).grid(row=0, column=1, sticky="w", padx=5)
        ttk.Label(grid_layout_frame, text="Cell Width:").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        ttk.Spinbox(grid_layout_frame, from_=1, to_=512, textvariable=self.cell_width, width=5).grid(row=1, column=1, sticky="w", padx=5)
        ttk.Label(grid_layout_frame, text="Cell Height:").grid(row=2, column=0, sticky="w", padx=5, pady=2)
        ttk.Spinbox(grid_layout_frame, from_=1, to_=512, textvariable=self.cell_height, width=5).grid(row=2, column=1, sticky="w", padx=5)
        ttk.Label(grid_layout_frame, text="Offset X:").grid(row=0, column=2, sticky="w", padx=5, pady=2)
        ttk.Spinbox(grid_layout_frame, from_=-100, to_=100, textvariable=self.offset_x, width=5).grid(row=0, column=3, sticky="w", padx=5)
        ttk.Label(grid_layout_frame, text="Offset Y:").grid(row=1, column=2, sticky="w", padx=5, pady=2)
        ttk.Spinbox(grid_layout_frame, from_=-100, to_=100, textvariable=self.offset_y, width=5).grid(row=1, column=3, sticky="w", padx=5)
        ttk.Checkbutton(grid_layout_frame, text="Show Grid Guides", variable=self.show_grid, command=self.generate_font_sheet).grid(row=2, column=2, columnspan=2, sticky="w", padx=5)
        
        # --- Preview Controls ---
        preview_controls_frame = ttk.Frame(self.master)
        preview_controls_frame.grid(row=1, column=0, pady=5, padx=10, sticky="w")
        ttk.Button(preview_controls_frame, text="Generate Font Sheet", command=self.generate_font_sheet).pack(side=tk.LEFT, padx=(0,5))
        self.save_button = ttk.Button(preview_controls_frame, text="Save Font Sheet...", command=self.save_font_sheet, state="disabled")
        self.save_button.pack(side=tk.LEFT, padx=5)
        ttk.Separator(preview_controls_frame, orient='vertical').pack(side=tk.LEFT, padx=10, fill='y')
        ttk.Checkbutton(preview_controls_frame, text="Fit to Screen", variable=self.fit_to_screen).pack(side=tk.LEFT)
        ttk.Button(preview_controls_frame, text="Reset View", command=self.reset_view).pack(side=tk.LEFT, padx=5)
        ttk.Label(preview_controls_frame, text="Zoom:").pack(side=tk.LEFT, padx=(10,0))
        ttk.Label(preview_controls_frame, textvariable=self.zoom_percent).pack(side=tk.LEFT)

        # --- Image Display Area ---
        self.image_frame = ttk.Frame(self.master, relief="sunken", borderwidth=2)
        self.image_frame.grid(row=2, column=0, padx=10, pady=(0,10), sticky="nsew")
        self.image_frame.grid_rowconfigure(0, weight=1)
        self.image_frame.grid_columnconfigure(0, weight=1)
        self.image_label = ttk.Label(self.image_frame)
        self.image_label.grid(row=0, column=0, sticky="nsew")
        self.image_frame.bind("<Configure>", self.on_frame_resize)

        # --- Event Bindings for Zoom/Pan ---
        self.image_label.bind("<MouseWheel>", self._on_mouse_wheel) # Windows
        self.image_label.bind("<Button-4>", self._on_mouse_wheel)   # Linux scroll up
        self.image_label.bind("<Button-5>", self._on_mouse_wheel)   # Linux scroll down
        self.image_label.bind("<ButtonPress-1>", self._on_pan_start)
        self.image_label.bind("<B1-Motion>", self._on_pan_move)
        self.image_label.bind("<ButtonRelease-1>", self._on_pan_end)
        self.image_label.bind("<Double-Button-1>", self.reset_view)
        
        self.master.after(100, self.generate_font_sheet)

    def generate_font_sheet(self):
        self.clean_font_sheet_image = self._generate_image(with_grid_guides=False)
        if self.clean_font_sheet_image is None:
            self.image_label.config(image='')
            self.save_button.config(state="disabled")
            return
        self.font_sheet_image = self._generate_image(with_grid_guides=self.show_grid.get())
        self.save_button.config(state="normal")
        self.update_display_image()
    
    def update_display_image(self):
        if not self.font_sheet_image: return
        if self.fit_to_screen.get():
            self._update_display_fit_to_screen()
        else:
            self._update_display_zoomed()

    def _update_display_fit_to_screen(self):
        """Fits the image to the frame (thumbnail view)."""
        frame_w = self.image_frame.winfo_width()
        frame_h = self.image_frame.winfo_height()
        if frame_w < 2 or frame_h < 2: return

        display_img = self.font_sheet_image.copy()
        original_w, original_h = display_img.size
        display_img.thumbnail((frame_w, frame_h), Image.Resampling.LANCZOS)
        
        # Update zoom level to reflect the thumbnail scale
        if original_w > 0:
            self.zoom_level = display_img.width / original_w
            self.zoom_percent.set(f"{self.zoom_level:.0%}")

        bg = self.bg_color.get()
        final_img = Image.new('RGB', (frame_w, frame_h), bg)
        px, py = (frame_w - display_img.width) // 2, (frame_h - display_img.height) // 2
        final_img.paste(display_img, (px, py))
        self.tk_img = ImageTk.PhotoImage(final_img)
        self.image_label.config(image=self.tk_img)
        self.image_label.image = self.tk_img

    def _update_display_zoomed(self):
        """Crops and displays a section of the image based on zoom and pan."""
        if not self.font_sheet_image: return
        frame_w = self.image_frame.winfo_width()
        frame_h = self.image_frame.winfo_height()
        if frame_w < 2 or frame_h < 2: return

        # Use NEAREST for crisp pixel art style zooming
        scaled_w = int(self.font_sheet_image.width * self.zoom_level)
        scaled_h = int(self.font_sheet_image.height * self.zoom_level)
        scaled_img = self.font_sheet_image.resize((scaled_w, scaled_h), Image.Resampling.NEAREST)

        # Clamp pan offsets so we can't pan past the image edges
        self.view_offset_x = max(0, min(self.view_offset_x, scaled_w - frame_w))
        self.view_offset_y = max(0, min(self.view_offset_y, scaled_h - frame_h))
        
        crop_box = (self.view_offset_x, self.view_offset_y, 
                    self.view_offset_x + frame_w, self.view_offset_y + frame_h)
        display_img = scaled_img.crop(crop_box)

        self.tk_img = ImageTk.PhotoImage(display_img)
        self.image_label.config(image=self.tk_img)
        self.image_label.image = self.tk_img
        self.zoom_percent.set(f"{self.zoom_level:.0%}")

    # --- Event Handlers ---
    def reset_view(self, event=None):
        """Resets the view to fit-to-screen mode."""
        self.fit_to_screen.set(True)

    def _on_fit_to_screen_change(self, *args):
        """Called when the 'Fit to Screen' checkbox changes."""
        self.update_display_image()

    def on_frame_resize(self, event):
        self.update_display_image()

    def _on_mouse_wheel(self, event):
        # Uncheck "Fit to Screen" if we are manually zooming
        if self.fit_to_screen.get():
            self.fit_to_screen.set(False)

        # --- Determine zoom factor ---
        if event.num == 5 or event.delta < 0: # Scroll down (zoom out)
            factor = 0.8
        else: # Scroll up (zoom in)
            factor = 1.25
        
        new_zoom = self.zoom_level * factor
        # Clamp zoom level
        new_zoom = max(0.1, min(new_zoom, 32.0))
        
        # --- Zoom centered on cursor ---
        mouse_x, mouse_y = event.x, event.y
        # Position of mouse on the scaled image
        img_x = self.view_offset_x + mouse_x
        img_y = self.view_offset_y + mouse_y
        # New top-left corner of the view
        self.view_offset_x = (img_x * (new_zoom / self.zoom_level)) - mouse_x
        self.view_offset_y = (img_y * (new_zoom / self.zoom_level)) - mouse_y
        
        self.zoom_level = new_zoom
        self.update_display_image()

    def _on_pan_start(self, event):
        if self.fit_to_screen.get(): return
        self.pan_start_x = event.x
        self.pan_start_y = event.y
        self.image_label.config(cursor="fleur")

    def _on_pan_move(self, event):
        if self.fit_to_screen.get(): return
        dx = event.x - self.pan_start_x
        dy = event.y - self.pan_start_y
        self.view_offset_x -= dx
        self.view_offset_y -= dy
        self.pan_start_x = event.x
        self.pan_start_y = event.y
        self.update_display_image()

    def _on_pan_end(self, event):
        self.image_label.config(cursor="")

    # --- Other Methods (unchanged) ---
    def _update_char_previews_and_validate(self, *args):
        try:
            start_code, end_code = self.start_char_code.get(), self.end_char_code.get()
            self.start_char_preview.set(f"({chr(start_code)})")
            self.end_char_preview.set(f"({chr(end_code)})")
            style = "TSpinbox" if start_code <= end_code else "Error.TSpinbox"
            s = ttk.Style()
            s.configure("Error.TSpinbox", fieldbackground="pink")
            self.start_char_spinbox.config(style=style)
            self.end_char_spinbox.config(style=style)
        except (ValueError, TypeError, tk.TclError):
            self.start_char_preview.set("(?)")
            self.end_char_preview.set("(?)")
    
    def _generate_image(self, with_grid_guides=False):
        try:
            font_size = self.font_size.get()
            bg_color, text_color = self.bg_color.get(), self.text_color.get()
            cols, cell_w, cell_h = self.grid_columns.get(), self.cell_width.get(), self.cell_height.get()
            offset_x, offset_y = self.offset_x.get(), self.offset_y.get()
            start_code, end_code = self.start_char_code.get(), self.end_char_code.get()
        except tk.TclError: return None
        font_path = self.font_path.get()
        if not all([font_path, os.path.exists(font_path)]): return None
        if not all([cols > 0, cell_w > 0, cell_h > 0]): return None
        if start_code > end_code: return None
        try:
            font = ImageFont.truetype(font_path, font_size)
        except Exception: return None
        characters_to_rasterize = ''.join(chr(c) for c in range(start_code, end_code + 1))
        if not characters_to_rasterize: return None
        rows = math.ceil(len(characters_to_rasterize) / cols)
        img_w, img_h = cols * cell_w, rows * cell_h
        img = Image.new('RGB', (img_w, img_h), color=bg_color)
        d = ImageDraw.Draw(img)
        for i, char in enumerate(characters_to_rasterize):
            col, row = i % cols, i // cols
            x, y = (col * cell_w) + offset_x, (row * cell_h) + offset_y
            d.text((x, y), char, font=font, fill=text_color, anchor="lt")
        if with_grid_guides:
            for r in range(1, rows): d.line([(0, r*cell_h), (img_w, r*cell_h)], fill=self.grid_line_color)
            for c in range(1, cols): d.line([(c*cell_w, 0), (c*cell_w, img_h)], fill=self.grid_line_color)
        return img
    
    def browse_font(self):
        path = filedialog.askopenfilename(title="Select Font", filetypes=[("Font Files", "*.ttf *.otf *.ttc"), ("All", "*.*")])
        if path: self.font_path.set(path); self.generate_font_sheet()

    def save_font_sheet(self):
        if not self.clean_font_sheet_image:
            messagebox.showwarning("Warning", "Generate a font sheet first.")
            return
        path = filedialog.asksaveasfilename(title="Save Font Sheet", defaultextension=".png", filetypes=[("PNG", "*.png"), ("BMP", "*.bmp"), ("All", "*.*")])
        if path:
            try:
                self.clean_font_sheet_image.save(path)
                messagebox.showinfo("Success", f"Font sheet saved to:\n{path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save image: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    # A bit of styling for the error state on the spinboxes
    s = ttk.Style()
    s.map("Error.TSpinbox", fieldbackground=[("!disabled", "pink")])
    app = FontRasterizerApp(root)
    root.mainloop()