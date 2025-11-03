import os
import shutil
import random
from PIL import Image, ImageOps, ImageFilter, ImageEnhance
from pathlib import Path
import cv2
import numpy as np
from concurrent.futures import ThreadPoolExecutor, as_completed
from customtkinter import CTkImage 
import tkinter as tk 
from tkinter import filedialog 

# ========== FUNZIONI BASE CON OPENCV (OTTIMIZZATE) ==========

def normalize_frame(img, method="resize", target_size=(1920, 1080)):
    """Normalizza un frame secondo il metodo scelto"""
    h, w = img.shape[:2]
    target_w, target_h = target_size
    
    if method == "resize":
        return cv2.resize(img, target_size, interpolation=cv2.INTER_LANCZOS4)
    elif method == "crop":
        aspect = w / h
        target_aspect = target_w / target_h
        
        if aspect > target_aspect:
            new_w = int(h * target_aspect)
            x = (w - new_w) // 2
            cropped = img[:, x:x+new_w]
        else:
            new_h = int(w / target_aspect)
            y = (h - new_h) // 2
            cropped = img[y:y+new_h, :]
        return cv2.resize(cropped, target_size, interpolation=cv2.INTER_LANCZOS4)
    elif method == "pad":
        aspect = w / h
        target_aspect = target_w / target_h
        
        if aspect > target_aspect:
            new_w = target_w
            new_h = int(target_w / aspect)
        else:
            new_h = target_h
            new_w = int(target_h * aspect)
        
        resized = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_LANCZOS4)
        
        top = (target_h - new_h) // 2
        bottom = target_h - new_h - top
        left = (target_w - new_w) // 2
        right = target_w - new_w - left
        
        return cv2.copyMakeBorder(resized, top, bottom, left, right, 
                                 cv2.BORDER_CONSTANT, value=[0, 0, 0])
    return img

def extract_frames(video_path, output_folder, fps=1, normalize=False, norm_method="resize", resolution="1920x1080", progress_callback=None):
    """Estrae i frame da un video usando OpenCV con opzione di normalizzazione"""
    os.makedirs(output_folder, exist_ok=True)
    
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return 0
    
    video_fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    frame_interval = max(1, int(video_fps / fps))
    
    w, h = map(int, resolution.split('x'))
    target_size = (w, h)
    
    frame_count = 0
    saved_count = 0
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        
        if frame_count % frame_interval == 0:
            if normalize:
                frame = normalize_frame(frame, norm_method, target_size)
            
            output_path = os.path.join(output_folder, f"frame_{saved_count:06d}.png")
            cv2.imwrite(output_path, frame)
            saved_count += 1
            
            if progress_callback:
                progress_callback((frame_count / total_frames) * 100)
        
        frame_count += 1
    
    cap.release()
    return saved_count

def create_video_from_folder(folder, output_path, fps=25, resolution="1920x1080", codec="mp4v", progress_callback=None):
    """Crea un video da una cartella di frame con risoluzione e codec specificati"""
    w, h = map(int, resolution.split('x'))
    
    files = sorted([f for f in os.listdir(folder) 
                    if f.lower().endswith(('.png', '.jpg', '.jpeg'))])
    
    if not files:
        return False
    
    # Scelta codec in base all'estensione
    fourcc = cv2.VideoWriter_fourcc(*codec)
    out = cv2.VideoWriter(output_path, fourcc, fps, (w, h))
    
    if not out.isOpened():
        return False
    
    total = len(files)
    for idx, filename in enumerate(files):
        img_path = os.path.join(folder, filename)
        frame = cv2.imread(img_path)
        
        if frame is None:
            continue
        
        if frame.shape[1] != w or frame.shape[0] != h:
            frame = cv2.resize(frame, (w, h), interpolation=cv2.INTER_LANCZOS4)
        
        out.write(frame)
        
        if progress_callback:
            progress_callback((idx + 1) / total * 100)
    
    out.release()
    return True

def interleave_folders(folders, output_folder, fps=25, resolution="1920x1080", output_format="mp4", progress_callback=None):
    """Mescola i frame da più cartelle in ordine casuale"""
    os.makedirs(output_folder, exist_ok=True)

    frames = []
    for folder in folders:
        for root, _, files in os.walk(folder):
            for f in files:
                if f.lower().endswith((".png", ".jpg", ".jpeg")):
                    frames.append(os.path.join(root, f))

    random.shuffle(frames)

    total = len(frames)
    for idx, src in enumerate(frames):
        dst = os.path.join(output_folder, f"frame_{idx:06d}.png")
        shutil.copy(src, dst)
        if progress_callback:
            # Aggiornamento progresso per la sola fase di copia
            progress_callback((idx + 1) / total * 100) 
    
    return True

def apply_effects(folder, effects, sliders, probability=0.5, overwrite=False, progress_callback=None):
    """Applica uno o più effetti con parametri regolabili (parallelo)"""
    files = sorted([f for f in os.listdir(folder) if f.lower().endswith((".png", ".jpg", ".jpeg"))])
    if not files:
        return 0

    if overwrite:
        out_folder = folder
    else:
        out_folder = os.path.join(folder, "effects_out")
        os.makedirs(out_folder, exist_ok=True)

    total = len(files)
    completed = 0
    
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {}
        for idx, f in enumerate(files):
            path = os.path.join(folder, f)
            out_path = os.path.join(out_folder, f)
            future = executor.submit(process_effect, path, out_path, effects, sliders, probability)
            futures[future] = idx
        
        for future in as_completed(futures):
            future.result()
            completed += 1
            if progress_callback:
                progress_callback((completed / total) * 100)

    return out_folder

def process_effect(input_path, output_path, effects, sliders, probability):
    """Processa un singolo frame con gli effetti"""
    img = Image.open(input_path)
    
    if random.random() < probability:
        if "posterize" in effects:
            bits = int(2 + sliders["posterize"] / 20)
            img = ImageOps.posterize(img, bits)

        if "bw" in effects:
            threshold = int(sliders["bw"] * 2.55)
            # Riconverti in RGB per salvare correttamente anche dopo la manipolazione dei canali
            img = img.convert("L").point(lambda p: 255 if p > threshold else 0).convert("RGB") 
            

        if "blur" in effects:
            radius = sliders["blur"] / 10
            img = img.filter(ImageFilter.GaussianBlur(radius))
        
        if "contrast" in effects:
            factor = 0.5 + (sliders["contrast"] / 50)
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(factor)
        
        if "brightness" in effects:
            factor = 0.5 + (sliders["brightness"] / 50)
            enhancer = ImageEnhance.Brightness(img)
            img = enhancer.enhance(factor)

    img.save(output_path)
    
# ========== FUNZIONI PATTERN & TEXTURE (OTTIMIZZATE) ==========

def apply_pattern_to_image(img, patterns, sliders):
    """Applica i pattern a una singola immagine in modo ottimizzato"""
    if "tile" in patterns:
        times = int(1 + sliders["tile"] / 20)
        w, h = img.size
        if times > 5: times = 5 
        new_img = Image.new("RGB", (w * times, h * times))
        for i in range(times):
            for j in range(times):
                new_img.paste(img, (i * w, j * h))
        img = new_img
    
    if "mirror" in patterns:
        img = ImageOps.mirror(img)
    
    if "stripe" in patterns:
        slices = int(2 + sliders["stripe"] / 20)
        if slices > 20: slices = 20
        w, h = img.size
        slice_w = w // slices
        new_img = Image.new("RGB", (w, h))
        order = list(range(slices))
        random.shuffle(order)
        for i, o in enumerate(order):
            # Assicurati di non sforare se slice_w è imperfetto
            x_start = o * slice_w
            x_end = min((o + 1) * slice_w, w)
            crop = img.crop((x_start, 0, x_end, h))
            new_img.paste(crop, (i * slice_w, 0))
        img = new_img
    
    return img

def apply_patterns(folder, patterns, sliders, sequence=False, progress_callback=None):
    """Applica pattern statici o a sequenza"""
    files = sorted([f for f in os.listdir(folder) if f.lower().endswith((".png", ".jpg", ".jpeg"))])
    if not files:
        return None

    out_folder = os.path.join(folder, "textures_out")
    os.makedirs(out_folder, exist_ok=True)

    if sequence:
        total = len(files)
        for idx, f in enumerate(files):
            img = Image.open(os.path.join(folder, f))
            img = apply_pattern_to_image(img, patterns, sliders)
            img.save(os.path.join(out_folder, f"pattern_{idx:06d}.png"))
            
            if progress_callback:
                progress_callback((idx + 1) / total * 100)
        
        return out_folder
    else:
        # Statico: usa solo la prima immagine e salva
        if not files: return None
        img = Image.open(os.path.join(folder, files[0]))
        img = apply_pattern_to_image(img, patterns, sliders)
        out_path = os.path.join(out_folder, "pattern_static.png")
        img.save(out_path)
        return out_path

# ========== FUNZIONI RINOMINA E CONVERSIONE ==========

def rename_and_convert_multiple(folders, output_folder, base_name, output_format, progress_callback=None):
    """Rinomina e converte i file da più cartelle in un'unica cartella di output"""
    valid_formats = {'.png', '.jpg', '.jpeg', '.bmp', '.gif', '.tiff', '.webp'}
    
    all_files = []
    for folder in folders:
        for root, _, files in os.walk(folder):
            for f in files:
                if Path(f).suffix.lower() in valid_formats:
                    all_files.append(os.path.join(root, f))
    
    if not all_files:
        return 0
    
    all_files.sort()
    total = len(all_files)
    
    os.makedirs(output_folder, exist_ok=True)
    
    for idx, src in enumerate(all_files):
        try:
            img = Image.open(src)
            
            new_name = f"{base_name}_{idx+1:06d}.{output_format}"
            dst = os.path.join(output_folder, new_name)
            
            if output_format.lower() in ['jpg', 'jpeg']:
                img = img.convert('RGB')
            elif output_format.lower() == 'png' and img.mode != 'RGBA':
                img = img.convert('RGBA')

            img.save(dst)
            
            if progress_callback:
                progress_callback((idx + 1) / total * 100)
        except Exception as e:
            print(f"Errore nel processare {src}: {e}")
    
    return total

# ========== FUNZIONI DI UTILITÀ GRAFICA (USATE DALLE GUI) ==========

def create_preview(img, max_size=250):
    """Crea una preview ridimensionata dell'immagine usando CTkImage"""
    preview = img.copy()
    preview.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
    return CTkImage(light_image=preview, dark_image=preview, size=preview.size)

def apply_effects_to_single_image_for_preview(img, effects, slider_values):
    """Applica effetti a una singola immagine per preview in modo sincrono"""
    
    temp_img = img.copy() 
    
    if "posterize" in effects:
        bits = int(2 + slider_values.get("posterize", 0) / 20)
        temp_img = ImageOps.posterize(temp_img, bits)
    
    if "bw" in effects:
        threshold = int(slider_values.get("bw", 0) * 2.55)
        temp_img = temp_img.convert("L").point(lambda p: 255 if p > threshold else 0).convert("RGB")
    
    if "blur" in effects:
        radius = slider_values.get("blur", 0) / 10
        temp_img = temp_img.filter(ImageFilter.GaussianBlur(radius))
    
    if "contrast" in effects:
        factor = 0.5 + (slider_values.get("contrast", 50) / 50)
        enhancer = ImageEnhance.Contrast(temp_img)
        temp_img = enhancer.enhance(factor)
    
    if "brightness" in effects:
        factor = 0.5 + (slider_values.get("brightness", 50) / 50)
        enhancer = ImageEnhance.Brightness(temp_img)
        temp_img = enhancer.enhance(factor)
    
    return temp_img