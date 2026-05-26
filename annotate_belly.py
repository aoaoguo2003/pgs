"""
Belly annotation tool — YOLO format, one box per image.

Usage:
  python annotate_belly.py           # annotate train split
  python annotate_belly.py val       # annotate val split

Controls:
  Click + Drag  : Draw belly bounding box
  R             : Clear and redraw
  D  or  →      : Save and go to next image
  A  or  ←      : Go to previous image
  Q             : Quit
"""

import sys
import tkinter as tk
from pathlib import Path

from PIL import Image, ImageTk

MAX_W = 1200
MAX_H = 800


class AnnotationTool:
    def __init__(self, root: tk.Tk, split: str = "train") -> None:
        self.root = root
        self.images_dir = Path(f"belly_yolo_dataset/images/{split}")
        self.labels_dir = Path(f"belly_yolo_dataset/labels/{split}")
        self.labels_dir.mkdir(parents=True, exist_ok=True)

        self.image_paths = sorted(
            p for p in self.images_dir.rglob("*")
            if p.suffix.lower() in {".jpg", ".jpeg", ".png"}
        )
        if not self.image_paths:
            raise FileNotFoundError(f"No images found in {self.images_dir}")

        # Start from the first unannotated image
        self.idx = 0
        for i, p in enumerate(self.image_paths):
            if not (self.labels_dir / (p.stem + ".txt")).exists():
                self.idx = i
                break

        # Drawing state
        self.start_x = self.start_y = None
        self.rect_id = None
        self.box = None          # (x1, y1, x2, y2) in canvas coords
        self.scale = 1.0
        self.offset_x = self.offset_y = 0
        self.orig_w = self.orig_h = 1

        self._build_ui()
        self.root.update()       # let canvas get its real size
        self._load_image()

        self.root.bind("<d>",     lambda e: self._next())
        self.root.bind("<Right>", lambda e: self._next())
        self.root.bind("<a>",     lambda e: self._prev())
        self.root.bind("<Left>",  lambda e: self._prev())
        self.root.bind("<r>",     lambda e: self._redo())
        self.root.bind("<q>",     lambda e: self.root.quit())

    # ------------------------------------------------------------------ UI

    def _build_ui(self) -> None:
        # ── top bar ──────────────────────────────────────────────────────
        top = tk.Frame(self.root, bg="#1e1e1e")
        top.pack(fill=tk.X, padx=6, pady=(4, 0))

        self.progress_var = tk.StringVar()
        tk.Label(top, textvariable=self.progress_var,
                 font=("Arial", 11, "bold"), bg="#1e1e1e", fg="white"
                 ).pack(side=tk.LEFT)

        self.status_var = tk.StringVar()
        tk.Label(top, textvariable=self.status_var,
                 font=("Arial", 11), bg="#1e1e1e", fg="#4caf50"
                 ).pack(side=tk.RIGHT)

        # ── canvas ───────────────────────────────────────────────────────
        self.canvas = tk.Canvas(self.root, cursor="crosshair", bg="#2b2b2b",
                                highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True, padx=6, pady=4)

        self.canvas.bind("<ButtonPress-1>",   self._on_press)
        self.canvas.bind("<B1-Motion>",       self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)

        # ── bottom bar ───────────────────────────────────────────────────
        bot = tk.Frame(self.root, bg="#1e1e1e")
        bot.pack(fill=tk.X, padx=6, pady=(0, 4))

        self.fname_var = tk.StringVar()
        tk.Label(bot, textvariable=self.fname_var,
                 font=("Arial", 8), bg="#1e1e1e", fg="#888"
                 ).pack(side=tk.LEFT)

        tk.Label(bot, text="← A  |  D →  |  R = 重画  |  Q = 退出",
                 font=("Arial", 9), bg="#1e1e1e", fg="#666"
                 ).pack(side=tk.RIGHT)

    # ---------------------------------------------------------- image load

    def _count_annotated(self) -> int:
        return sum(
            1 for p in self.image_paths
            if (self.labels_dir / (p.stem + ".txt")).exists()
        )

    def _load_image(self) -> None:
        path = self.image_paths[self.idx]
        total = len(self.image_paths)
        annotated = self._count_annotated()

        self.progress_var.set(
            f"图片  {self.idx + 1} / {total}    已标注: {annotated} / {total}"
        )
        self.fname_var.set(path.name)

        img = Image.open(path).convert("RGB")
        self.orig_w, self.orig_h = img.size

        cw = self.canvas.winfo_width()  or MAX_W
        ch = self.canvas.winfo_height() or MAX_H

        scale = min(cw / self.orig_w, ch / self.orig_h, 1.0)
        dw = int(self.orig_w * scale)
        dh = int(self.orig_h * scale)
        self.scale    = scale
        self.offset_x = (cw - dw) // 2
        self.offset_y = (ch - dh) // 2

        self.tk_img = ImageTk.PhotoImage(
            img.resize((dw, dh), Image.LANCZOS)
        )
        self.canvas.delete("all")
        self.canvas.create_image(self.offset_x, self.offset_y,
                                  anchor=tk.NW, image=self.tk_img)

        # Reset drawing state
        self.rect_id = None
        self.box     = None
        self.start_x = self.start_y = None

        # Show existing annotation
        label_path = self.labels_dir / (path.stem + ".txt")
        if label_path.exists():
            self._draw_existing(label_path)
            self.status_var.set("✓ 已标注  (R=重画)")
        else:
            self.status_var.set("未标注 — 点击拖动画框")

    def _draw_existing(self, label_path: Path) -> None:
        try:
            parts = label_path.read_text().strip().split()[1:]
            xc, yc, w, h = (float(v) for v in parts)
            x1 = (xc - w / 2) * self.orig_w * self.scale + self.offset_x
            y1 = (yc - h / 2) * self.orig_h * self.scale + self.offset_y
            x2 = (xc + w / 2) * self.orig_w * self.scale + self.offset_x
            y2 = (yc + h / 2) * self.orig_h * self.scale + self.offset_y
            self.box = (x1, y1, x2, y2)
            self.rect_id = self.canvas.create_rectangle(
                x1, y1, x2, y2, outline="cyan", width=3
            )
        except Exception:
            pass

    # ------------------------------------------------------ mouse drawing

    def _on_press(self, event: tk.Event) -> None:
        self._redo()
        self.start_x, self.start_y = event.x, event.y
        self.rect_id = self.canvas.create_rectangle(
            event.x, event.y, event.x, event.y,
            outline="#00ff00", width=3
        )

    def _on_drag(self, event: tk.Event) -> None:
        if self.rect_id is not None:
            self.canvas.coords(
                self.rect_id, self.start_x, self.start_y, event.x, event.y
            )

    def _on_release(self, event: tk.Event) -> None:
        if self.start_x is None:
            return
        x1 = min(self.start_x, event.x)
        y1 = min(self.start_y, event.y)
        x2 = max(self.start_x, event.x)
        y2 = max(self.start_y, event.y)
        if x2 - x1 < 8 or y2 - y1 < 8:   # too small — ignore
            self._redo()
            return
        self.box = (x1, y1, x2, y2)
        self.status_var.set("✓ 画好了 — 按 D 保存并下一张")

    def _redo(self) -> None:
        if self.rect_id is not None:
            self.canvas.delete(self.rect_id)
            self.rect_id = None
        self.box     = None
        self.start_x = self.start_y = None
        label_path = self.labels_dir / (self.image_paths[self.idx].stem + ".txt")
        if label_path.exists():
            self.status_var.set("✓ 已标注  (R=重画)")
        else:
            self.status_var.set("未标注 — 点击拖动画框")

    # ------------------------------------------------------- save / navigate

    def _save(self) -> None:
        if self.box is None:
            return
        x1, y1, x2, y2 = self.box
        x1n = (x1 - self.offset_x) / (self.orig_w * self.scale)
        y1n = (y1 - self.offset_y) / (self.orig_h * self.scale)
        x2n = (x2 - self.offset_x) / (self.orig_w * self.scale)
        y2n = (y2 - self.offset_y) / (self.orig_h * self.scale)
        xc = (x1n + x2n) / 2
        yc = (y1n + y2n) / 2
        w  = x2n - x1n
        h  = y2n - y1n
        # Clamp
        xc = max(0.0, min(1.0, xc))
        yc = max(0.0, min(1.0, yc))
        w  = max(0.001, min(1.0, w))
        h  = max(0.001, min(1.0, h))
        label_path = self.labels_dir / (self.image_paths[self.idx].stem + ".txt")
        label_path.write_text(f"0 {xc:.6f} {yc:.6f} {w:.6f} {h:.6f}\n",
                              encoding="utf-8")

    def _next(self) -> None:
        self._save()
        if self.idx < len(self.image_paths) - 1:
            self.idx += 1
            self._load_image()

    def _prev(self) -> None:
        if self.idx > 0:
            self.idx -= 1
            self._load_image()


# --------------------------------------------------------------------------

def main() -> None:
    split = sys.argv[1] if len(sys.argv) > 1 and sys.argv[1] in ("train", "val") else "train"
    root = tk.Tk()
    root.configure(bg="#1e1e1e")
    root.geometry(f"{MAX_W}x{MAX_H + 70}")
    root.title(f"Belly Annotator — {split}")
    AnnotationTool(root, split)
    root.mainloop()


if __name__ == "__main__":
    main()
