import os
import threading
from tkinter import filedialog, messagebox
import customtkinter as ctk
from PIL import Image
from tool_logic import apply_patterns, apply_pattern_to_image, create_preview

# ========== SETUP GLOBALE (SOLO PER QUESTO TOOL) ==========
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

pattern_folder = None
current_preview_img_pattern = None

def get_pattern_slider_vars():
    # Helper per raccogliere i valori degli slider
    return {
        "tile": pattern_slider_tile.get(),
        "stripe": pattern_slider_stripe.get()
    }

def update_preview_pattern(preview_label_pattern, sliders):
    global current_preview_img_pattern
    
    if current_preview_img_pattern is None:
        preview_label_pattern.configure(text="Seleziona prima una cartella valida per la preview.")
        return
    
    # Prepara i pattern selezionati
    selected_patterns = []
    if var_tile.get(): selected_patterns.append("tile")
    if var_mirror.get(): selected_patterns.append("mirror")
    if var_stripe.get(): selected_patterns.append("stripe")
    
    if not selected_patterns:
        img_processed = current_preview_img_pattern.copy()
    else:
        # L'applicazione dei pattern avviene su una copia (veloce)
        img_processed = apply_pattern_to_image(current_preview_img_pattern.copy(), selected_patterns, sliders)
    
    # Mostra preview con CTkImage
    preview_ctk = create_preview(img_processed, 250)
    preview_label_pattern.configure(image=preview_ctk, text="") # Rimuovi il testo della label
    preview_label_pattern.image = preview_ctk

# Funzione per il caricamento dell'immagine (eseguita nel thread)
def load_preview_image_pattern(folder, preview_label_pattern, root):
    global current_preview_img_pattern
    
    files = sorted([f for f in os.listdir(folder) if f.lower().endswith((".png", ".jpg", ".jpeg"))])
    if not files:
        root.after(0, lambda: preview_label_pattern.configure(text="Nessun file immagine nella cartella"))
        current_preview_img_pattern = None
        return
        
    img_path = os.path.join(folder, files[0])
    
    try:
        current_preview_img_pattern = Image.open(img_path).convert("RGB")
        root.after(0, lambda: update_preview_pattern(preview_label_pattern, get_pattern_slider_vars()))
    except Exception as e:
        root.after(0, lambda: preview_label_pattern.configure(text=f"Errore caricamento: {e}"))
        current_preview_img_pattern = None


def choose_folder_pattern(entry_pattern_folder, preview_label_pattern, root):
    global pattern_folder
    folder = filedialog.askdirectory(title="Seleziona Cartella Frame Sorgente")
    if folder:
        pattern_folder = folder
        entry_pattern_folder.delete(0, "end")
        entry_pattern_folder.insert(0, folder)
        preview_label_pattern.configure(text="Caricamento immagine in corso...")
        
        # Avvia il caricamento in un thread separato
        threading.Thread(target=load_preview_image_pattern, args=(folder, preview_label_pattern, root), daemon=True).start()

def run_pattern_thread(root, btn_pattern_static, btn_pattern_sequence, progress_var_pattern, static=True):
    if not pattern_folder or not os.path.isdir(pattern_folder):
        messagebox.showerror("Errore", "Seleziona una cartella valida")
        return
    
    selected_patterns = []
    if var_tile.get(): selected_patterns.append("tile")
    if var_mirror.get(): selected_patterns.append("mirror")
    if var_stripe.get(): selected_patterns.append("stripe")
    
    if not selected_patterns:
        messagebox.showerror("Errore", "Nessun pattern selezionato")
        return
    
    btn_pattern_static.configure(state="disabled")
    btn_pattern_sequence.configure(state="disabled")
    
    def pattern_task():
        slider_values = get_pattern_slider_vars()
        
        def progress_update(value):
            root.after(0, lambda: progress_var_pattern.set(value / 100))
        
        result = apply_patterns(pattern_folder, selected_patterns, slider_values, 
                                 sequence=not static, progress_callback=progress_update)
        
        if static:
            root.after(0, lambda: messagebox.showinfo("Completato", f"Texture statica salvata in:\n{result}"))
        else:
            root.after(0, lambda: messagebox.showinfo("Completato", f"Sequenza di pattern salvata in:\n{result}"))
        
        root.after(0, lambda: btn_pattern_static.configure(state="normal"))
        root.after(0, lambda: btn_pattern_sequence.configure(state="normal"))
        root.after(0, lambda: progress_var_pattern.set(0))
    
    threading.Thread(target=pattern_task, daemon=True).start()

# ========== CREAZIONE DELLA GUI PRINCIPALE DEL TOOL ==========
def create_patterns_gui():
    global var_tile, var_mirror, var_stripe
    global pattern_slider_tile, pattern_slider_stripe
    
    root = ctk.CTk()
    root.title("🖼 Tool: Pattern & Texture")
    root.geometry("800x650")

    # Layout Principale
    frame_pattern_main = ctk.CTkFrame(root)
    frame_pattern_main.pack(fill="both", expand=True, padx=10, pady=10)

    # Sinistra: Controlli
    frame_pattern_left = ctk.CTkFrame(frame_pattern_main)
    frame_pattern_left.pack(side="left", fill="both", expand=True, padx=(0, 5))

    # Scelta Cartella
    entry_pattern_folder = ctk.CTkEntry(frame_pattern_left, width=400)
    entry_pattern_folder.pack(pady=5, padx=10)
    btn_choose_pattern = ctk.CTkButton(frame_pattern_left, text="📂 Scegli Cartella", 
                                       command=lambda: choose_folder_pattern(entry_pattern_folder, preview_label_pattern, root))
    btn_choose_pattern.pack(pady=5)
    
    # Helper per l'aggiornamento della preview con i parametri correnti
    preview_update_cmd = lambda x: update_preview_pattern(preview_label_pattern, get_pattern_slider_vars())

    # Variabili
    var_tile = ctk.BooleanVar()
    var_mirror = ctk.BooleanVar()
    var_stripe = ctk.BooleanVar()

    # Checkbox e Slider
    ctk.CTkLabel(frame_pattern_left, text="PATTERN DISPONIBILI", font=("Arial", 12, "bold")).pack(pady=(10, 5))
    
    ctk.CTkCheckBox(frame_pattern_left, text="Tiling (Ripeti l'immagine)", variable=var_tile, command=preview_update_cmd).pack(anchor="w", pady=(5, 0))
    ctk.CTkLabel(frame_pattern_left, text="Tile size (numero di ripetizioni):").pack(anchor="w")
    pattern_slider_tile = ctk.CTkSlider(frame_pattern_left, from_=0, to=100, command=preview_update_cmd)
    pattern_slider_tile.pack(fill="x", pady=5, padx=20)
    
    ctk.CTkCheckBox(frame_pattern_left, text="Mirror (Riflessione Orizzontale)", variable=var_mirror, command=preview_update_cmd).pack(anchor="w", pady=(5, 0))
    
    ctk.CTkCheckBox(frame_pattern_left, text="Stripes (Rimescola Strisce Verticali)", variable=var_stripe, command=preview_update_cmd).pack(anchor="w", pady=(5, 0))
    ctk.CTkLabel(frame_pattern_left, text="Stripe slices (numero di strisce):").pack(anchor="w")
    pattern_slider_stripe = ctk.CTkSlider(frame_pattern_left, from_=0, to=100, command=preview_update_cmd)
    pattern_slider_stripe.pack(fill="x", pady=5, padx=20)
    
    # Destra: Preview
    frame_pattern_right = ctk.CTkFrame(frame_pattern_main, width=300)
    frame_pattern_right.pack(side="right", fill="y", padx=(5, 0))
    frame_pattern_right.pack_propagate(False)

    ctk.CTkLabel(frame_pattern_right, text="PREVIEW", font=("Arial", 14, "bold")).pack(pady=10)
    preview_label_pattern = ctk.CTkLabel(frame_pattern_right, text="Seleziona cartella frame sorgente")
    preview_label_pattern.pack(pady=10)
    
    # Inizializza la preview per mostrare il messaggio iniziale
    update_preview_pattern(preview_label_pattern, get_pattern_slider_vars())

    # Progress e bottoni
    progress_var_pattern = ctk.DoubleVar()
    progress_bar_pattern = ctk.CTkProgressBar(root, variable=progress_var_pattern)
    progress_bar_pattern.pack(fill="x", padx=10, pady=10)
    progress_bar_pattern.set(0)

    frame_pattern_buttons = ctk.CTkFrame(root)
    frame_pattern_buttons.pack(pady=10)

    btn_pattern_static = ctk.CTkButton(frame_pattern_buttons, text="✨ Genera Texture Statica (1 Img)",
                                       command=lambda: run_pattern_thread(root, btn_pattern_static, btn_pattern_sequence, progress_var_pattern, static=True))
    btn_pattern_static.pack(side="left", padx=5)

    btn_pattern_sequence = ctk.CTkButton(frame_pattern_buttons, text="🎥 Genera Sequenza Pattern (Tutti)",
                                         command=lambda: run_pattern_thread(root, btn_pattern_static, btn_pattern_sequence, progress_var_pattern, static=False))
    btn_pattern_sequence.pack(side="left", padx=5)

    root.mainloop()

if __name__ == "__main__":
    create_patterns_gui()