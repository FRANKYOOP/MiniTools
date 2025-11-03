import os
import threading
from tkinter import filedialog, messagebox
import customtkinter as ctk
from tool_logic import rename_and_convert_multiple

# ========== SETUP GLOBALE (SOLO PER QUESTO TOOL) ==========
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

rename_folders = []

def add_folder_rename(folder_list_rename):
    folder = filedialog.askdirectory(title="Aggiungi Cartella Sorgente")
    if folder:
        rename_folders.append(folder)
        folder_list_rename.insert("end", folder + "\n")

def clear_folders_rename(folder_list_rename):
    rename_folders.clear()
    folder_list_rename.delete("1.0", "end")

def choose_output_folder(entry_output_folder):
    folder = filedialog.askdirectory(title="Seleziona Cartella di Output")
    if folder:
        entry_output_folder.delete(0, "end")
        entry_output_folder.insert(0, folder)

def run_rename_thread(root, btn_rename, progress_var_rename, entry_output_folder, entry_base_name, combo_output_format_rename):
    if not rename_folders:
        messagebox.showerror("Errore", "Nessuna cartella sorgente selezionata")
        return
    
    output_folder = entry_output_folder.get()
    base_name = entry_base_name.get()
    output_format = combo_output_format_rename.get().lower()
    
    if not output_folder or not base_name:
        messagebox.showerror("Errore", "Inserisci tutti i parametri (Cartella Output e Nome Base)")
        return

    btn_rename.configure(state="disabled")
    
    def rename_task():
        def progress_update(value):
            root.after(0, lambda: progress_var_rename.set(value / 100))
        
        total_renamed = rename_and_convert_multiple(rename_folders, output_folder, base_name, output_format, progress_callback=progress_update)
        
        root.after(0, lambda: messagebox.showinfo("Completato", f"Rinomina e conversione completate.\nTotale file: {total_renamed} in:\n{output_folder}"))
        root.after(0, lambda: btn_rename.configure(state="normal"))
        root.after(0, lambda: progress_var_rename.set(0))
    
    threading.Thread(target=rename_task, daemon=True).start()

# ========== CREAZIONE DELLA GUI PRINCIPALE DEL TOOL ==========
def create_rename_gui():
    root = ctk.CTk()
    root.title("💾 Tool: Rinomina & Converti Frame")
    root.geometry("600x600")

    # Lista Cartelle Sorgente
    ctk.CTkLabel(root, text="Cartelle Sorgente (i file verranno ordinati):").pack(pady=(10, 5), padx=10, anchor="w")
    folder_list_rename = ctk.CTkTextbox(root, height=120)
    folder_list_rename.pack(padx=10, pady=5, fill="x")

    frame_btns_rename = ctk.CTkFrame(root)
    frame_btns_rename.pack(pady=5)

    btn_add_folder_rename = ctk.CTkButton(frame_btns_rename, text="➕ Aggiungi Cartella", 
                                          command=lambda: add_folder_rename(folder_list_rename))
    btn_add_folder_rename.pack(side="left", padx=5)

    btn_clear_folders_rename = ctk.CTkButton(frame_btns_rename, text="🗑 Ripulisci Lista", 
                                             command=lambda: clear_folders_rename(folder_list_rename))
    btn_clear_folders_rename.pack(side="left", padx=5)

    # Controlli Output
    frame_output = ctk.CTkFrame(root)
    frame_output.pack(pady=20, fill="x", padx=10)

    # Cartella Output
    ctk.CTkLabel(frame_output, text="Cartella Output:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
    entry_output_folder = ctk.CTkEntry(frame_output, width=300)
    entry_output_folder.grid(row=0, column=1, padx=5, pady=5)
    btn_choose_output_folder = ctk.CTkButton(frame_output, text="...", width=30, 
                                            command=lambda: choose_output_folder(entry_output_folder))
    btn_choose_output_folder.grid(row=0, column=2, padx=5, pady=5)

    # Nome Base
    ctk.CTkLabel(frame_output, text="Nome Base File:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
    entry_base_name = ctk.CTkEntry(frame_output, width=300)
    entry_base_name.insert(0, "frame")
    entry_base_name.grid(row=1, column=1, padx=5, pady=5)

    # Formato Output
    ctk.CTkLabel(frame_output, text="Formato Conversione:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
    combo_output_format_rename = ctk.CTkComboBox(frame_output, values=["PNG", "JPG", "BMP"], width=100)
    combo_output_format_rename.set("PNG")
    combo_output_format_rename.grid(row=2, column=1, padx=5, pady=5, sticky="w")

    # Barra di Progresso
    progress_var_rename = ctk.DoubleVar()
    progress_bar_rename = ctk.CTkProgressBar(root, variable=progress_var_rename)
    progress_bar_rename.pack(fill="x", padx=10, pady=20)
    progress_bar_rename.set(0)

    # Pulsante Avvio
    btn_rename = ctk.CTkButton(root, text="💾 Rinomina e Converti", 
                               command=lambda: run_rename_thread(root, btn_rename, progress_var_rename, entry_output_folder, entry_base_name, combo_output_format_rename))
    btn_rename.pack(pady=10)

    root.mainloop()

if __name__ == "__main__":
    create_rename_gui()