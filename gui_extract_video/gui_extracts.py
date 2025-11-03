import os
import threading
from tkinter import filedialog, messagebox
import customtkinter as ctk
from tool_logic import extract_frames, normalize_frame

# ========== SETUP GLOBALE (SOLO PER QUESTO TOOL) ==========
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

videos = []

def add_videos(video_list):
    files = filedialog.askopenfilenames(filetypes=[("Video files", "*.mp4;*.mov;*.avi;*.mkv;*.flv;*.wmv")])
    for f in files:
        videos.append(f)
        video_list.insert("end", f + "\n")

def clear_videos(video_list):
    videos.clear()
    video_list.delete("1.0", "end")

def run_extract_thread(root, btn_extract, progress_var_extract, entry_fps, var_normalize, combo_norm_method, combo_resolution_extract):
    if not videos:
        messagebox.showerror("Errore", "Nessun video selezionato")
        return
    out = filedialog.askdirectory(title="Seleziona Cartella di Output")
    if not out:
        return
    
    btn_extract.configure(state="disabled")
    
    def extract_task():
        try:
            fps = int(entry_fps.get())
        except ValueError:
            root.after(0, lambda: messagebox.showerror("Errore", "FPS non valido"))
            root.after(0, lambda: btn_extract.configure(state="normal"))
            return
            
        normalize = var_normalize.get()
        norm_method = combo_norm_method.get()
        resolution = combo_resolution_extract.get()
        
        total_videos = len(videos)
        saved_frames_total = 0
        
        for idx, v in enumerate(videos):
            video_name = os.path.splitext(os.path.basename(v))[0]
            video_folder = os.path.join(out, video_name)
            
            def progress_update(value):
                # Aggiorna la barra di progresso in base al video corrente
                root.after(0, lambda: progress_var_extract.set(value / 100))
            
            saved_count = extract_frames(v, video_folder, fps=fps, normalize=normalize, 
                             norm_method=norm_method, resolution=resolution, 
                             progress_callback=progress_update)
            saved_frames_total += saved_count
            
            # Reset della barra tra un video e l'altro (o alla fine se è l'ultimo)
            if idx < total_videos - 1:
                root.after(0, lambda: progress_var_extract.set(0))
        
        root.after(0, lambda: messagebox.showinfo("Completato", f"Estrazione completata da {total_videos} video.\nTotale frame salvati: {saved_frames_total} in:\n{out}"))
        root.after(0, lambda: btn_extract.configure(state="normal"))
        root.after(0, lambda: progress_var_extract.set(0))
    
    threading.Thread(target=extract_task, daemon=True).start()

# ========== CREAZIONE DELLA GUI PRINCIPALE DEL TOOL ==========
def create_extract_gui():
    root = ctk.CTk()
    root.title("🎞 Tool: Estrazione Frame Video")
    root.geometry("600x650")
    
    # Lista Video
    video_list = ctk.CTkTextbox(root, height=120)
    video_list.pack(padx=10, pady=10, fill="both")

    frame_btns_extract = ctk.CTkFrame(root)
    frame_btns_extract.pack(pady=5)

    btn_add_video = ctk.CTkButton(frame_btns_extract, text="➕ Aggiungi Video", command=lambda: add_videos(video_list))
    btn_add_video.pack(side="left", padx=5)

    btn_clear_videos = ctk.CTkButton(frame_btns_extract, text="🗑 Ripulisci Lista", command=lambda: clear_videos(video_list))
    btn_clear_videos.pack(side="left", padx=5)

    # Controlli FPS
    ctk.CTkLabel(root, text="Frame per Secondo (FPS) da estrarre:").pack(pady=(10, 0))
    entry_fps = ctk.CTkEntry(root, width=100)
    entry_fps.insert(0, "1")
    entry_fps.pack(pady=5)

    # Controlli Normalizzazione
    var_normalize = ctk.BooleanVar()
    ctk.CTkCheckBox(root, text="Normalizza Frame", variable=var_normalize).pack(pady=(10, 5))

    ctk.CTkLabel(root, text="Metodo Normalizzazione:").pack()
    combo_norm_method = ctk.CTkComboBox(root, values=["resize", "crop", "pad"], width=200)
    combo_norm_method.set("resize")
    combo_norm_method.pack(pady=5)

    ctk.CTkLabel(root, text="Risoluzione Target:").pack()
    combo_resolution_extract = ctk.CTkComboBox(root, values=["1280x720", "1920x1080", "3840x2160"], width=200)
    combo_resolution_extract.set("1920x1080")
    combo_resolution_extract.pack(pady=5)

    # Barra di Progresso
    progress_var_extract = ctk.DoubleVar()
    progress_bar_extract = ctk.CTkProgressBar(root, variable=progress_var_extract)
    progress_bar_extract.pack(fill="x", padx=10, pady=20)
    progress_bar_extract.set(0)

    # Pulsante Avvio
    btn_extract = ctk.CTkButton(root, text="🎞 Estrai Frame", 
        command=lambda: run_extract_thread(root, btn_extract, progress_var_extract, entry_fps, var_normalize, combo_norm_method, combo_resolution_extract))
    btn_extract.pack(pady=10)

    root.mainloop()

if __name__ == "__main__":
    create_extract_gui()