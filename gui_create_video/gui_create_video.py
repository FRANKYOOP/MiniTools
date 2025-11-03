import os
import shutil
import threading
from tkinter import filedialog, messagebox
import customtkinter as ctk
from tool_logic import interleave_folders, create_video_from_folder
from pathlib import Path
# ========== SETUP GLOBALE (SOLO PER QUESTO TOOL) ==========
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

folders = []

def add_folder(folder_list):
    folder = filedialog.askdirectory(title="Seleziona Cartella Frame")
    if folder:
        folders.append(folder)
        folder_list.insert("end", folder + "\n")

def clear_folders(folder_list):
    folders.clear()
    folder_list.delete("1.0", "end")

def run_merge_thread(root, btn_merge, progress_var, entry_fps_merge, combo_resolution, combo_output_format):
    if not folders:
        messagebox.showerror("Errore", "Nessuna cartella selezionata")
        return
    
    btn_merge.configure(state="disabled")
    
    def merge_task():
        try:
            fps = int(entry_fps_merge.get())
        except ValueError:
            root.after(0, lambda: messagebox.showerror("Errore", "FPS non valido"))
            root.after(0, lambda: btn_merge.configure(state="normal"))
            return
            
        resolution_full = combo_resolution.get()
        resolution = resolution_full.split(' ')[0]
        output_format = combo_output_format.get().lower()
        
        codec_map = {
            "mp4": ("mp4v", "*.mp4"),
            "avi": ("XVID", "*.avi"),
            "mkv": ("X264", "*.mkv"),
            "mov": ("mp4v", "*.mov")
        }
        
        # 1. Chiedi il percorso di salvataggio del video finale
        ext = codec_map.get(output_format, ("mp4v", "*.mp4"))[1]
        out_path_video = filedialog.asksaveasfilename(
            defaultextension=f".{output_format}",
            filetypes=[(f"Video {output_format.upper()}", ext)]
        )
        
        if not out_path_video:
            root.after(0, lambda: messagebox.showinfo("Annullato", "Creazione video annullata"))
            root.after(0, lambda: btn_merge.configure(state="normal"))
            root.after(0, lambda: progress_var.set(0))
            return
            
        tmp_folder = "frames_interleaved_temp"
        shutil.rmtree(tmp_folder, ignore_errors=True)
        os.makedirs(tmp_folder, exist_ok=True)
        
        # 2. Interleaving (copia e rimescola frame) - Copia al 50%
        def interleave_progress(value):
            root.after(0, lambda: progress_var.set(value / 200)) # Copia fino al 50%
            
        interleave_folders(folders, tmp_folder, progress_callback=interleave_progress)
        
        # 3. Creazione del video finale - Video dal 50% al 100%
        ext = Path(out_path_video).suffix[1:].lower()
        codec = codec_map.get(ext, ("mp4v", ""))[0]
        
        def video_progress(value):
            root.after(0, lambda: progress_var.set(50 + (value / 200))) 
            
        success = create_video_from_folder(tmp_folder, out_path_video, fps, resolution, codec, progress_callback=video_progress)
        
        shutil.rmtree(tmp_folder, ignore_errors=True) 

        if success:
            root.after(0, lambda: messagebox.showinfo("Completato", f"Video creato in:\n{out_path_video}"))
        else:
            root.after(0, lambda: messagebox.showerror("Errore", "Errore nella creazione del video"))
        
        root.after(0, lambda: btn_merge.configure(state="normal"))
        root.after(0, lambda: progress_var.set(0))
    
    threading.Thread(target=merge_task, daemon=True).start()

# ========== CREAZIONE DELLA GUI PRINCIPALE DEL TOOL ==========
def create_create_video_gui():
    root = ctk.CTk()
    root.title("🎥 Tool: Crea Video e Interfoliazione")
    root.geometry("600x600")

    # Lista Cartelle
    folder_list = ctk.CTkTextbox(root, height=120)
    folder_list.pack(padx=10, pady=10, fill="both")

    frame_btns_merge = ctk.CTkFrame(root)
    frame_btns_merge.pack(pady=5)

    btn_add_folder = ctk.CTkButton(frame_btns_merge, text="➕ Aggiungi Cartella", command=lambda: add_folder(folder_list))
    btn_add_folder.pack(side="left", padx=5)

    btn_clear_folders = ctk.CTkButton(frame_btns_merge, text="🗑 Ripulisci Lista", command=lambda: clear_folders(folder_list))
    btn_clear_folders.pack(side="left", padx=5)

    # Controlli Parametri
    frame_settings = ctk.CTkFrame(root)
    frame_settings.pack(pady=20, fill="x", padx=10)

    ctk.CTkLabel(frame_settings, text="FPS Output:").grid(row=0, column=0, padx=5, pady=5)
    entry_fps_merge = ctk.CTkEntry(frame_settings, width=80)
    entry_fps_merge.insert(0, "25")
    entry_fps_merge.grid(row=0, column=1, padx=5, pady=5)

    ctk.CTkLabel(frame_settings, text="Risoluzione:").grid(row=0, column=2, padx=5, pady=5)
    combo_resolution = ctk.CTkComboBox(frame_settings, values=["1280x720 (HD)", "1920x1080 (Full HD)", "3840x2160 (4K)"], width=180)
    combo_resolution.set("1920x1080 (Full HD)")
    combo_resolution.grid(row=0, column=3, padx=5, pady=5)

    ctk.CTkLabel(frame_settings, text="Formato:").grid(row=1, column=0, padx=5, pady=5)
    combo_output_format = ctk.CTkComboBox(frame_settings, values=["MP4", "AVI", "MKV", "MOV"], width=100)
    combo_output_format.set("MP4")
    combo_output_format.grid(row=1, column=1, padx=5, pady=5)

    # Barra di Progresso
    progress_var = ctk.DoubleVar()
    progress_bar = ctk.CTkProgressBar(root, variable=progress_var)
    progress_bar.pack(fill="x", padx=10, pady=20)
    progress_bar.set(0)

    # Pulsante Avvio
    btn_merge = ctk.CTkButton(root, text="🎥 Crea Video (Interfolia)", 
        command=lambda: run_merge_thread(root, btn_merge, progress_var, entry_fps_merge, combo_resolution, combo_output_format))
    btn_merge.pack(pady=10)

    root.mainloop()

if __name__ == "__main__":
    create_create_video_gui()