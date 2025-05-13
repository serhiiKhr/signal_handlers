import tkinter as tk
import numpy as np
from scipy.signal import find_peaks
from tkinter import ttk, filedialog
import matplotlib.pyplot as plt
import os
from datetime import datetime
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from utils.language_manager import LanguageManager

lang = LanguageManager()
class PlotRenderer:
    def __init__(self, title=lang.get("plot.title"), xlabel=lang.get("plot.xlabel"), ylabel=lang.get("ui.amplitude"), description="",
                 xdata=None, ydata=None, xlim=None, ylim=None, peaks=None):
        self.title = title
        self.xlabel = xlabel
        self.ylabel = ylabel
        self.description = description
        self.xdata = xdata if xdata is not None else []
        self.ydata = ydata if ydata is not None else []
        self.xlim = xlim
        self.ylim = ylim
        self.peaks = peaks if peaks is not None else []

    def set_title(self, title=""): self.title = title
    def set_xlabel(self, xlabel=""): self.xlabel = xlabel
    def set_ylabel(self, ylabel=""): self.ylabel = ylabel
    def set_description(self, description=""): self.description = description
    def set_xlim(self, xlim): self.xlim = xlim
    def set_ylim(self, ylim): self.ylim = ylim
    def set_peaks(self, peaks): self.peaks = peaks

    def show(self):
        figure, ax = plt.subplots(dpi=125)
        window = tk.Toplevel()
        window.title(self.title or "Plot Window")

        self._create_figure(ax)

        figure.tight_layout(pad=1.0)
        canvas = FigureCanvasTkAgg(figure, master=window)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Control panel
        control_frame = tk.Frame(window)
        control_frame.pack(fill=tk.X, padx=10, pady=5)

        # Title, Labels, Description inputs
        tk.Label(control_frame, text="Title:").grid(row=0, column=0, sticky="e")
        title_entry = ttk.Entry(control_frame)
        title_entry.insert(0, self.title)
        title_entry.grid(row=0, column=1, sticky="ew", padx=5)

        tk.Label(control_frame, text="X label:").grid(row=1, column=0, sticky="e")
        xlabel_entry = ttk.Entry(control_frame)
        xlabel_entry.insert(0, self.xlabel)
        xlabel_entry.grid(row=1, column=1, sticky="ew", padx=5)

        tk.Label(control_frame, text="Y label:").grid(row=2, column=0, sticky="e")
        ylabel_entry = ttk.Entry(control_frame)
        ylabel_entry.insert(0, self.ylabel)
        ylabel_entry.grid(row=2, column=1, sticky="ew", padx=5)

        tk.Label(control_frame, text="Description:").grid(row=3, column=0, sticky="ne")
        desc_text = tk.Text(control_frame, height=4, width=40)
        desc_text.insert("1.0", self.description)
        desc_text.grid(row=3, column=1, sticky="ew", padx=5)

        # Save button (aligned right)
        save_btn = ttk.Button(control_frame, text=lang.get("ui.save"), command=lambda: self._save_dialog(
            title_entry.get(), xlabel_entry.get(), ylabel_entry.get(), desc_text.get("1.0", "end").strip()))
        save_btn.grid(row=4, column=1, sticky="e", pady=(5, 0))

        control_frame.columnconfigure(1, weight=1)

        # does not block the main interface
        window.update_idletasks()
        x = 100 + len(window.master.winfo_children()) * 40
        y = 100 + len(window.master.winfo_children()) * 30
        window.geometry(f"+{x}+{y}")
        
    @classmethod
    def save_multiply(cls, plots: list, path: str = None, show_graph: bool = False, dpi: int = 100):
        if not plots:
            return

        n = len(plots)
        fig_height = 3 * n
        fig, axes = plt.subplots(n, 1, figsize=(8.27, fig_height), dpi=dpi, constrained_layout=True)

        if n == 1:
            axes = [axes]

        for plot, ax in zip(plots, axes):
            plot._create_figure(ax)

        if path:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            fig.savefig(path, dpi=dpi)

        if show_graph:
            fig.tight_layout(pad=2.0)
            window = tk.Toplevel()
            window.title(lang.get("plot.graphs"))

            canvas = FigureCanvasTkAgg(fig, master=window)
            canvas.draw()
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

            window.update_idletasks()
            x = 100 + len(window.master.winfo_children()) * 40
            y = 100 + len(window.master.winfo_children()) * 30
            window.geometry(f"+{x}+{y}")
        else:
            plt.close(fig)
   
    @classmethod
    def save_multiple_on_single_plot(cls, plots: list, path: str, dpi: int = 100, show_graph: bool = False):
        if not plots:
            return

        fig, ax = plt.subplots(figsize=(8.27, 6), dpi=dpi)
        peaks = []

        for plot in plots:
            title = plot.title or lang.get("plot.without_name")
            label = f"{title}\n{plot.description}" if plot.description else title

            ax.plot(plot.xdata, plot.ydata, label=label, linewidth=1)
            peaks.extend(plot.peaks)

        # Set axis limits
        xlims = [plot.xlim for plot in plots if plot.xlim]
        ylims = [plot.ylim for plot in plots if plot.ylim]

        if xlims:
            ax.set_xlim(min(x[0] for x in xlims), max(x[1] for x in xlims))
        if ylims:
            ax.set_ylim(min(y[0] for y in ylims), max(y[1] for y in ylims))

        for peak in peaks:
            ax.scatter(peak['x'], peak['y'], color='red', zorder=5,
                    marker='o', facecolors='none', edgecolors='red', s=50)

        ax.set_title(lang.get("plot.summary_plot"))
        ax.set_xlabel(lang.get("plot.xlabel"))
        ax.set_ylabel(lang.get("plot.ylabel"))
        ax.grid(True)

        if len(plots) > 1:
            ax.legend()

        fig.tight_layout(pad=1.0)

        # Save image
        os.makedirs(os.path.dirname(path), exist_ok=True)
        fig.savefig(path, dpi=dpi)

        # Show or close
        if show_graph:
            plt.show(block=False)
        else:
            plt.close(fig)


    def save(self, path: str, dpi: int = 300):
        fig, ax = plt.subplots(dpi=dpi)
        self._create_figure(ax)

        os.makedirs(os.path.dirname(path), exist_ok=True)
        fig.tight_layout(pad=1.0)
        fig.savefig(path, dpi=dpi)
        plt.close(fig)
         
    def _create_figure(self, ax):
        # Apply plot settings
        ax.plot(self.xdata, self.ydata, linewidth=1, markersize=4)
        ax.set_title(self.title)
        ax.set_xlabel(self.xlabel)
        ax.set_ylabel(self.ylabel)
        ax.grid(True)
        if self.xlim: ax.set_xlim(*self.xlim)
        if self.ylim: ax.set_ylim(*self.ylim)
        
        for peak in self.peaks:
            ax.scatter(peak['x'], peak['y'], color='red', zorder=5, marker='o', facecolors='none', edgecolors='red', s=50, label=lang.get("ui.max"))
        
        if self.description:
            ax.text(0.02, 0.97, 
                    self.description,
                    transform=ax.transAxes,
                    fontsize=9, 
                    verticalalignment='top',
                    horizontalalignment='left',
                    bbox=dict(facecolor='white', alpha=0.8, edgecolor='black'))

    def _save_dialog(self, title, xlabel, ylabel, description):
        self.title = title
        self.xlabel = xlabel
        self.ylabel = ylabel
        self.description = description

        now = datetime.now().strftime("%d-%m-%Y_%H-%M")
        if self.title:
            default_filename = f"{self.title}_{now}.png"
        else:
            default_filename = f"plot_{now}.png"

        path = filedialog.asksaveasfilename(
            defaultextension=".png",
            initialfile=default_filename,
            filetypes=[("PNG files", "*.png"), ("All files", "*.*")]
        )
        if path:
            self.save(path)
            
    
