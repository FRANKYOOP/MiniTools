import os
import threading
from tkinter import filedialog, messagebox
import customtkinter as ctk
from PIL import Image
from tool_logic import apply_effects, create_preview, apply_effects_to_single_image_for_preview

# ========== SETUP GLOBALE (SOLO PER QUESTO TOOL) ==========
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

effect_folder = None
current_preview_img = None 
global_root_ref = None # Riferimento alla root per l'accesso dai thread

def get_slider_vars():
    # Helper per raccogliere i valori degli slider
    return {
        "posterize": slider_posterize.get(),
        "bw": slider_bw.get(),
        "blur": slider_blur.get(),
        "contrast": slider_contrast.get(),
        "brightness": slider_brightness.get()
    }

def update_preview_effect(preview_label_effect, sliders):
    global current_preview_img
    
    if current_preview_img is None:
        preview_label_effect.configure(text="Seleziona prima una cartella valida per la preview.")
        return
    
    # Prepara gli effetti selezionati
    selected_effects = []
    if var_posterize.get(): selected_effects.append("posterize")
    if var_bw.get(): selected_effects.append("bw")
    if var_blur.get(): selected_effects.append("blur")
    if var_contrast.get(): selected_effects.append("contrast")
    if var_brightness.get(): selected_effects.append("brightness")
    
    # L'elaborazione della preview è veloce (su immagine piccola), la manteniamo nel thread GUI
    img_processed = apply_effects_to_single_image_for_preview(current_preview_img, selected_effects, sliders)
    
    # Mostra preview con CTkImage
    preview_ctk = create_preview(img_processed, 250)
    preview_label_effect.configure(image=preview_ctk, text="") # Rimuovi il testo della label
    preview_label_effect.image = preview_ctk 

# Funzione per il caricamento dell'immagine (eseguita nel thread)
def load_preview_image(folder, preview_label_effect, root):
    global current_preview_img
    
    files = sorted([f for f in os.listdir(folder) if f.lower().endswith((".png", ".jpg", ".jpeg"))])
    
    if not files:
        root.after(0, lambda: preview_label_effect.configure(text="Nessun file immagine nella cartella"))
        current_preview_img = None
        return
        
    img_path = os.path.join(folder, files[0])
    
    try:
        current_preview_img = Image.open(img_path).convert("RGB")
        # Aggiorna la preview nel thread della GUI
        root.after(0, lambda: update_preview_effect(preview_label_effect, get_slider_vars()))
    except Exception as e:
        root.after(0, lambda: preview_label_effect.configure(text=f"Errore caricamento: {e}"))
        current_preview_img = None


def choose_folder_effect(entry_effect_folder, preview_label_effect, root):
    global effect_folder
    folder = filedialog.askdirectory(title="Seleziona Cartella Frame da Modificare")
    if folder:
        effect_folder = folder
        entry_effect_folder.delete(0, "end")
        entry_effect_folder.insert(0, folder)
        preview_label_effect.configure(text="Caricamento immagine in corso...")
        
        # Avvia il caricamento in un thread separato
        threading.Thread(target=load_preview_image, args=(folder, preview_label_effect, root), daemon=True).start()

def run_effects_thread(root, btn_apply_effects, progress_var_effect, var_overwrite):
    if not effect_folder or not os.path.isdir(effect_folder):
        messagebox.showerror("Errore", "Seleziona una cartella valida")
        return
    
    selected_effects = []
    if var_posterize.get(): selected_effects.append("posterize")
    if var_bw.get(): selected_effects.append("bw")
    if var_blur.get(): selected_effects.append("blur")
    if var_contrast.get(): selected_effects.append("contrast")
    if var_brightness.get(): selected_effects.append("brightness")
    
    if not selected_effects:
        messagebox.showerror("Errore", "Nessun effetto selezionato")
        return
    
    btn_apply_effects.configure(state="disabled")
    
    def effects_task():
        slider_values = get_slider_vars()
        overwrite = var_overwrite.get()
        
        def progress_update(value):
            root.after(0, lambda: progress_var_effect.set(value / 100))
        
        out_folder = apply_effects(effect_folder, selected_effects, slider_values, 
                                 probability=0.7, overwrite=overwrite,
                                 progress_callback=progress_update)
        
        root.after(0, lambda: messagebox.showinfo("Completato", f"Effetti applicati.\nCartella output: {out_folder}"))
        root.after(0, lambda: btn_apply_effects.configure(state="normal"))
        root.after(0, lambda: progress_var_effect.set(0))
    
    threading.Thread(target=effects_task, daemon=True).start()

# ========== CREAZIONE DELLA GUI PRINCIPALE DEL TOOL ==========
def create_effects_gui():
    global var_posterize, var_bw, var_blur, var_contrast, var_brightness
    global slider_posterize, slider_bw, slider_blur, slider_contrast, slider_brightness
    global global_root_ref
    
    root = ctk.CTk()
    global_root_ref = root # Salva il riferimento
    root.title("✨ Tool: Applicazione Effetti Frame")
    root.geometry("800x700")

    # Layout Principale
    frame_effect_main = ctk.CTkFrame(root)
    frame_effect_main.pack(fill="both", expand=True, padx=10, pady=10)

    # Sinistra: Controlli
    frame_effect_left = ctk.CTkFrame(frame_effect_main)
    frame_effect_left.pack(side="left", fill="both", expand=True, padx=(0, 5))

    # Scelta Cartella
    entry_effect_folder = ctk.CTkEntry(frame_effect_left, width=400)
    entry_effect_folder.pack(pady=5, padx=10)
    btn_choose_folder = ctk.CTkButton(frame_effect_left, text="📂 Scegli Cartella", 
                                      command=lambda: choose_folder_effect(entry_effect_folder, preview_label_effect, root))
    btn_choose_folder.pack(pady=5)
    
    # Checkbox Sovrascrivi
    var_overwrite = ctk.BooleanVar()
    ctk.CTkCheckBox(frame_effect_left, text="Sovrascrivi file originali", variable=var_overwrite).pack(pady=5)

    # Frame Scrollable per Effetti e Slider
    frame_effects = ctk.CTkScrollableFrame(frame_effect_left, height=350)
    frame_effects.pack(fill="both", expand=True, padx=10, pady=10)

    # Helper per l'aggiornamento della preview con i parametri correnti
    preview_update_cmd = lambda x: update_preview_effect(preview_label_effect, get_slider_vars())

    # Variabili
    var_posterize = ctk.BooleanVar()
    var_bw = ctk.BooleanVar()
    var_blur = ctk.BooleanVar()
    var_contrast = ctk.BooleanVar()
    var_brightness = ctk.BooleanVar()

    # Checkbox e Slider (inclusi nel codice precedente)
    ctk.CTkCheckBox(frame_effects, text="Posterize", variable=var_posterize, command=preview_update_cmd).pack(anchor="w", pady=(5, 0))
    ctk.CTkLabel(frame_effects, text="Posterize (livelli colore - min 2):").pack(anchor="w")
    slider_posterize = ctk.CTkSlider(frame_effects, from_=0, to=100, command=preview_update_cmd)
    slider_posterize.pack(fill="x", pady=5, padx=20)
    
    ctk.CTkCheckBox(frame_effects, text="Bianco e Nero (Puro)", variable=var_bw, command=preview_update_cmd).pack(anchor="w", pady=(5, 0))
    ctk.CTkLabel(frame_effects, text="Soglia B/N (0=scuro, 100=chiaro):").pack(anchor="w")
    slider_bw = ctk.CTkSlider(frame_effects, from_=0, to=100, command=preview_update_cmd)
    slider_bw.set(50)
    slider_bw.pack(fill="x", pady=5, padx=20)
    
    ctk.CTkCheckBox(frame_effects, text="Blur", variable=var_blur, command=preview_update_cmd).pack(anchor="w", pady=(5, 0))
    ctk.CTkLabel(frame_effects, text="Blur (raggio 0-10):").pack(anchor="w")
    slider_blur = ctk.CTkSlider(frame_effects, from_=0, to=100, command=preview_update_cmd)
    slider_blur.pack(fill="x", pady=5, padx=20)
    
    ctk.CTkCheckBox(frame_effects, text="Contrasto", variable=var_contrast, command=preview_update_cmd).pack(anchor="w", pady=(5, 0))
    ctk.CTkLabel(frame_effects, text="Contrasto (0=min, 50=default, 100=max):").pack(anchor="w")
    slider_contrast = ctk.CTkSlider(frame_effects, from_=0, to=100, command=preview_update_cmd)
    slider_contrast.set(50)
    slider_contrast.pack(fill="x", pady=5, padx=20)
    
    ctk.CTkCheckBox(frame_effects, text="Luminosità", variable=var_brightness, command=preview_update_cmd).pack(anchor="w", pady=(5, 0))
    ctk.CTkLabel(frame_effects, text="Luminosità (0=min, 50=default, 100=max):").pack(anchor="w")
    slider_brightness = ctk.CTkSlider(frame_effects, from_=0, to=100, command=preview_update_cmd)
    slider_brightness.set(50)
    slider_brightness.pack(fill="x", pady=5, padx=20)

    # Destra: Preview
    frame_effect_right = ctk.CTkFrame(frame_effect_main, width=300)
    frame_effect_right.pack(side="right", fill="y", padx=(5, 0))
    frame_effect_right.pack_propagate(False)

    ctk.CTkLabel(frame_effect_right, text="PREVIEW", font=("Arial", 14, "bold")).pack(pady=10)
    preview_label_effect = ctk.CTkLabel(frame_effect_right, text="Seleziona cartella frame sorgente")
    preview_label_effect.pack(pady=10)
    
    # Inizializza la preview per mostrare il messaggio iniziale
    update_preview_effect(preview_label_effect, get_slider_vars())

    # Progress e bottone
    progress_var_effect = ctk.DoubleVar()
    progress_bar_effect = ctk.CTkProgressBar(root, variable=progress_var_effect)
    progress_bar_effect.pack(fill="x", padx=10, pady=10)
    progress_bar_effect.set(0)

    btn_apply_effects = ctk.CTkButton(root, text="✨ Applica Effetti a Sequenza", 
                                      command=lambda: run_effects_thread(root, btn_apply_effects, progress_var_effect, var_overwrite))
    btn_apply_effects.pack(pady=10)

    root.mainloop()

if __name__ == "__main__":
    create_effects_gui()