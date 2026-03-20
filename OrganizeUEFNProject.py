import unreal
import tkinter as tk
from tkinter import messagebox
from collections import defaultdict, deque
import re

# ============================================================
# UEFN AUTO TYPE ORGANIZER
#
# Features:
# - Scans a typed-in Content Browser path
# - Detects asset types
# - Lets you choose which asset types to organize
# - Auto-creates destination folders by asset type + guessed category
# - Moves assets using Unreal rename/move behavior
# - Skips assets already inside the organized root
# - Skips assets if the exact destination asset already exists already
# - Optional filter: only include assets referenced by the current level
# - Added types:
#   - Level Sequences
#   - Material Functions
#   - Data Layer Assets
#   - Material Parameter Collections
#   - Widget Blueprints
# ============================================================

DEFAULT_SCAN_ROOT = "/amadeus"
DEFAULT_ORGANIZED_ROOT_NAME = "_Organized"

# ------------------------------------------------------------
# Logging
# ------------------------------------------------------------

def log(msg):
    unreal.log("[AutoTypeOrganizer] " + str(msg))

def warn(msg):
    unreal.log_warning("[AutoTypeOrganizer] " + str(msg))

def err(msg):
    unreal.log_error("[AutoTypeOrganizer] " + str(msg))


# ------------------------------------------------------------
# Path / naming helpers
# ------------------------------------------------------------

def normalize_path(path: str) -> str:
    path = (path or "").replace("\\", "/").strip()
    if not path.startswith("/"):
        path = "/" + path
    while "//" in path:
        path = path.replace("//", "/")
    if len(path) > 1 and path.endswith("/"):
        path = path[:-1]
    return path

def sanitize_folder_name(name: str) -> str:
    name = re.sub(r"[^A-Za-z0-9_ ]+", "", name or "")
    name = re.sub(r"\s+", "_", name).strip("_")
    return name or "Misc"

def get_package_name_str(asset_data) -> str:
    try:
        return str(asset_data.package_name)
    except Exception:
        return ""

def get_package_path_str(asset_data) -> str:
    try:
        return str(asset_data.package_path)
    except Exception:
        pkg = get_package_name_str(asset_data)
        if "/" in pkg:
            return pkg.rsplit("/", 1)[0]
        return "/"

def get_asset_name_str(asset_data) -> str:
    try:
        return str(asset_data.asset_name)
    except Exception:
        pkg = get_package_name_str(asset_data)
        if "/" in pkg:
            return pkg.rsplit("/", 1)[-1]
        return pkg

def get_class_name_str(asset_data) -> str:
    try:
        return str(asset_data.asset_class_path.asset_name)
    except Exception:
        try:
            return str(asset_data.asset_class)
        except Exception:
            return "Unknown"

def package_to_object_path(package_name: str, asset_name: str) -> str:
    return f"{package_name}.{asset_name}"


# ------------------------------------------------------------
# Asset type mapping
# ------------------------------------------------------------

SELECTABLE_TYPES = [
    "Textures",
    "Sounds",
    "Meshes",
    "Materials",
    "MaterialInstances",
    "MaterialFunctions",
    "MaterialParameterCollections",
    "Blueprints",
    "WidgetBlueprints",
    "Niagara",
    "Animations",
    "Data",
    "DataLayerAssets",
    "LevelSequences",
]

CLASS_TO_TYPE = {
    # Textures
    "Texture2D": "Textures",
    "TextureCube": "Textures",
    "TextureRenderTarget2D": "Textures",

    # Sounds
    "SoundWave": "Sounds",
    "SoundCue": "Sounds",
    "MetaSoundSource": "Sounds",
    "MetaSoundPatch": "Sounds",

    # Meshes
    "StaticMesh": "Meshes",
    "SkeletalMesh": "Meshes",

    # Materials
    "Material": "Materials",

    # Material Instances
    "MaterialInstanceConstant": "MaterialInstances",
    "MaterialInstance": "MaterialInstances",

    # Material Functions
    "MaterialFunction": "MaterialFunctions",
    "MaterialFunctionMaterialLayer": "MaterialFunctions",
    "MaterialFunctionMaterialLayerBlend": "MaterialFunctions",

    # Material Parameter Collections
    "MaterialParameterCollection": "MaterialParameterCollections",

    # Blueprints
    "Blueprint": "Blueprints",
    "AnimBlueprint": "Blueprints",

    # Widget Blueprints
    "WidgetBlueprint": "WidgetBlueprints",

    # Niagara
    "NiagaraSystem": "Niagara",
    "NiagaraEmitter": "Niagara",

    # Animation
    "AnimSequence": "Animations",
    "AnimMontage": "Animations",
    "BlendSpace": "Animations",
    "Skeleton": "Animations",
    "PhysicsAsset": "Animations",

    # Data
    "CurveFloat": "Data",
    "CurveVector": "Data",
    "CurveLinearColor": "Data",
    "DataTable": "Data",
    "PrimaryDataAsset": "Data",

    # Data Layers
    "DataLayerAsset": "DataLayerAssets",

    # Sequences
    "LevelSequence": "LevelSequences",
}

def detect_selectable_type(asset_data) -> str:
    class_name = get_class_name_str(asset_data)
    return CLASS_TO_TYPE.get(class_name, "Other")


# ------------------------------------------------------------
# Category guessing
# ------------------------------------------------------------

CATEGORY_RULES = [
    ("Trees", {"tree", "trees", "oak", "pine", "birch", "branch", "stump", "log"}),
    ("Foliage", {"grass", "bush", "fern", "leaf", "shrub", "plant", "ivy", "flower"}),
    ("Rocks", {"rock", "rocks", "stone", "cliff", "boulder", "ore", "pebble"}),
    ("Terrain", {"terrain", "landscape", "ground", "soil", "mud", "sand", "snow", "dirt"}),
    ("Buildings", {"house", "building", "wall", "roof", "door", "window", "tower", "castle"}),
    ("Props", {"prop", "barrel", "crate", "bench", "table", "chair", "lamp", "fence"}),
    ("Roads", {"road", "path", "trail", "bridge", "stairs", "step", "ramp"}),
    ("Water", {"water", "river", "lake", "ocean", "pond", "shore", "wave", "foam"}),
    ("Characters", {"character", "npc", "enemy", "player", "creature", "monster", "humanoid"}),
    ("Weapons", {"weapon", "sword", "bow", "gun", "rifle", "shield", "arrow", "axe"}),
    ("VFX", {"fx", "vfx", "effect", "impact", "explosion", "smoke", "fire", "spark", "dust"}),
    ("UI", {"ui", "widget", "icon", "hud", "menu", "button", "cursor"}),
    ("Music", {"music", "theme", "track", "song", "score"}),
    ("Ambience", {"ambient", "ambience", "wind", "birds", "rain", "waterfall", "forest"}),
    ("SFX", {"sfx", "footstep", "hit", "pickup", "jump", "attack", "swing"}),
    ("Functions", {"function", "functions"}),
    ("Cinematics", {"sequence", "cinematic", "intro", "outro", "cutscene"}),
    ("WorldPartition", {"datalayer", "data_layer", "partition"}),
    ("GlobalParameters", {"mpc", "collection", "global"}),
]

def tokenize_name(name: str):
    base = re.sub(r"([a-z])([A-Z])", r"\1 \2", name)
    base = re.sub(r"[_\-\.]+", " ", base)
    return [t.lower() for t in base.split() if t.strip()]

def guess_category(asset_name: str, selectable_type: str) -> str:
    toks = set(tokenize_name(asset_name))

    for category, keys in CATEGORY_RULES:
        if toks.intersection(keys):
            return category

    if selectable_type == "Sounds":
        return "General"
    if selectable_type == "Textures":
        return "Surface"
    if selectable_type == "Materials":
        return "Surface"
    if selectable_type == "MaterialInstances":
        return "Surface"
    if selectable_type == "MaterialFunctions":
        return "Functions"
    if selectable_type == "MaterialParameterCollections":
        return "GlobalParameters"
    if selectable_type == "Meshes":
        return "Props"
    if selectable_type == "Blueprints":
        return "Gameplay"
    if selectable_type == "WidgetBlueprints":
        return "UI"
    if selectable_type == "Niagara":
        return "VFX"
    if selectable_type == "Animations":
        return "Characters"
    if selectable_type == "Data":
        return "General"
    if selectable_type == "DataLayerAssets":
        return "WorldPartition"
    if selectable_type == "LevelSequences":
        return "Cinematics"

    return "Misc"


# ------------------------------------------------------------
# Unreal helpers
# ------------------------------------------------------------

def ensure_directory(path: str):
    path = normalize_path(path)
    eal = unreal.EditorAssetLibrary
    if not eal.does_directory_exist(path):
        ok = eal.make_directory(path)
        if not ok:
            raise RuntimeError(f"Could not create directory: {path}")

def list_asset_datas(scan_root: str):
    scan_root = normalize_path(scan_root)
    ar = unreal.AssetRegistryHelpers.get_asset_registry()
    assets = ar.get_assets_by_path(scan_root, recursive=True, include_only_on_disk_assets=False) or []

    out = []
    for ad in assets:
        try:
            if ad.is_redirector():
                continue
        except Exception:
            pass
        out.append(ad)
    return out

def move_asset_safe(src_package_name: str, dest_dir: str, dest_asset_name: str):
    src_asset_name = src_package_name.rsplit("/", 1)[-1]
    src_object_path = package_to_object_path(src_package_name, src_asset_name)

    dest_package_name = f"{dest_dir}/{dest_asset_name}"
    dest_object_path = package_to_object_path(dest_package_name, dest_asset_name)

    ok = unreal.EditorAssetLibrary.rename_asset(src_object_path, dest_object_path)
    return ok, dest_package_name, dest_object_path


# ------------------------------------------------------------
# Redirector helpers
# ------------------------------------------------------------

def scan_redirectors(path: str):
    ar = unreal.AssetRegistryHelpers.get_asset_registry()
    out = []
    try:
        assets = ar.get_assets_by_path(normalize_path(path), recursive=True, include_only_on_disk_assets=False) or []
        for ad in assets:
            try:
                if ad.is_redirector():
                    out.append(get_package_name_str(ad))
            except Exception:
                pass
    except Exception as e:
        warn(f"Redirector scan failed: {e}")
    return out


# ------------------------------------------------------------
# Current level reference filtering
# ------------------------------------------------------------

def get_current_level_package_name():
    try:
        world = unreal.EditorLevelLibrary.get_editor_world()
    except Exception as e:
        raise RuntimeError(f"Could not access current editor world: {e}")

    if not world:
        raise RuntimeError("No current editor world was found.")

    try:
        world_path = str(world.get_path_name())
    except Exception as e:
        raise RuntimeError(f"Could not resolve current level path: {e}")

    if not world_path:
        raise RuntimeError("Current level path was empty.")

    return world_path.split(".")[0]

def get_current_level_referenced_packages():
    ar = unreal.AssetRegistryHelpers.get_asset_registry()
    level_package = get_current_level_package_name()

    visited = set()
    queue = deque([level_package])

    try:
        dep_options = unreal.AssetRegistryDependencyOptions(
            include_soft_package_references=True,
            include_hard_package_references=True,
            include_searchable_names=False,
            include_soft_management_references=True,
            include_hard_management_references=True
        )
    except Exception:
        dep_options = None

    while queue:
        pkg = queue.popleft()
        if not pkg or pkg in visited:
            continue

        visited.add(pkg)

        try:
            if dep_options is not None:
                deps = ar.get_dependencies(pkg, dep_options) or []
            else:
                deps = ar.get_dependencies(pkg) or []
        except Exception:
            deps = []

        for dep in deps:
            dep_str = str(dep)
            if dep_str and dep_str not in visited:
                queue.append(dep_str)

    return visited


# ------------------------------------------------------------
# Planning / execution
# ------------------------------------------------------------

def build_plan(scan_root: str, organized_root_name: str, enabled_types: set, include_unused_assets: bool):
    scan_root = normalize_path(scan_root)
    organized_root = normalize_path(f"{scan_root}/{sanitize_folder_name(organized_root_name)}")

    assets = list_asset_datas(scan_root)

    level_referenced_packages = None
    if not include_unused_assets:
        level_referenced_packages = get_current_level_referenced_packages()

    plan = []
    skipped = []

    for ad in assets:
        package_name = get_package_name_str(ad)
        package_path = get_package_path_str(ad)
        asset_name = get_asset_name_str(ad)
        class_name = get_class_name_str(ad)
        selectable_type = detect_selectable_type(ad)

        if not package_name or not asset_name:
            skipped.append((package_name or "<unknown>", "Could not read package or asset name"))
            continue

        if not include_unused_assets:
            if package_name not in level_referenced_packages:
                skipped.append((package_name, "Not used in current level"))
                continue

        if package_path == organized_root or package_path.startswith(organized_root + "/"):
            skipped.append((package_name, "Already inside organized root"))
            continue

        if selectable_type == "Other":
            skipped.append((package_name, f"Unsupported type: {class_name}"))
            continue

        if selectable_type not in enabled_types:
            skipped.append((package_name, f"Type not enabled: {selectable_type}"))
            continue

        category = guess_category(asset_name, selectable_type)

        dest_dir = normalize_path(
            f"{organized_root}/{sanitize_folder_name(selectable_type)}/{sanitize_folder_name(category)}"
        )

        target_package = f"{dest_dir}/{asset_name}"

        if unreal.EditorAssetLibrary.does_asset_exist(target_package):
            skipped.append((package_name, f"Already exists in destination: {target_package}"))
            continue

        plan.append({
            "asset_data": ad,
            "package_name": package_name,
            "package_path": package_path,
            "asset_name": asset_name,
            "class_name": class_name,
            "selectable_type": selectable_type,
            "category": category,
            "dest_dir": dest_dir,
        })

    return plan, skipped, organized_root

def execute_plan(plan, organized_root: str):
    moved = []
    failed = []

    for row in plan:
        try:
            ensure_directory(row["dest_dir"])

            dest_dir = row["dest_dir"]
            dest_name = row["asset_name"]
            target_package = f"{dest_dir}/{dest_name}"

            if unreal.EditorAssetLibrary.does_asset_exist(target_package):
                continue

            ok, final_package_name, final_object_path = move_asset_safe(
                src_package_name=row["package_name"],
                dest_dir=dest_dir,
                dest_asset_name=dest_name
            )

            if ok and unreal.EditorAssetLibrary.does_asset_exist(final_package_name):
                moved.append({
                    **row,
                    "final_package_name": final_package_name
                })
            else:
                failed.append((row, "rename_asset returned False or destination missing"))
        except Exception as e:
            failed.append((row, str(e)))

    try:
        unreal.EditorAssetLibrary.save_directory(organized_root, only_if_is_dirty=False, recursive=True)
    except Exception as e:
        warn(f"Save warning: {e}")

    return moved, failed


# ------------------------------------------------------------
# UI
# ------------------------------------------------------------

class AutoTypeOrganizerApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("UEFN Auto Type Organizer")
        self.root.geometry("1360x930")
        self.root.configure(bg="#1a1a2e")
        self.root.attributes("-topmost", True)

        self.tick_handle = None
        self.plan = []
        self.skipped = []
        self.organized_root = ""
        self.row_widgets = []

        self.build_ui()
        self.start_tick()

    def build_ui(self):
        bg = "#1a1a2e"
        fg = "#e0e0e0"
        ebg = "#16213e"
        acc = "#e94560"

        tk.Label(
            self.root,
            text="UEFN AUTO TYPE ORGANIZER",
            font=("Segoe UI", 16, "bold"),
            fg=acc,
            bg=bg
        ).pack(pady=(12, 4))

        tk.Label(
            self.root,
            text="Scans a folder, detects asset types, auto-creates organized folders, and moves selected assets",
            font=("Segoe UI", 9),
            fg="#9aa4b2",
            bg=bg
        ).pack(pady=(0, 8))

        top = tk.Frame(self.root, bg=bg)
        top.pack(fill="x", padx=14, pady=(0, 8))

        tk.Label(top, text="Scan Root:", fg=fg, bg=bg, font=("Segoe UI", 10, "bold")).pack(side="left")
        self.scan_var = tk.StringVar(value=DEFAULT_SCAN_ROOT)
        tk.Entry(top, textvariable=self.scan_var, bg=ebg, fg=fg, insertbackground=fg, width=36).pack(side="left", padx=(6, 10))

        tk.Label(top, text="Organized Root Name:", fg=fg, bg=bg, font=("Segoe UI", 10, "bold")).pack(side="left")
        self.org_var = tk.StringVar(value=DEFAULT_ORGANIZED_ROOT_NAME)
        tk.Entry(top, textvariable=self.org_var, bg=ebg, fg=fg, insertbackground=fg, width=18).pack(side="left", padx=(6, 10))

        tk.Button(top, text="SCAN", bg=acc, fg="white", relief="flat", command=self.scan, width=10).pack(side="left")
        tk.Button(top, text="ORGANIZE", bg="#b33030", fg="white", relief="flat", command=self.organize, width=12).pack(side="left", padx=(8, 0))

        options_frame = tk.LabelFrame(
            self.root,
            text=" Scan Options ",
            fg=fg,
            bg=bg,
            font=("Segoe UI", 10, "bold")
        )
        options_frame.pack(fill="x", padx=14, pady=(0, 8))

        self.include_unused_var = tk.BooleanVar(value=True)
        tk.Checkbutton(
            options_frame,
            text="Include assets not used by the current level",
            variable=self.include_unused_var,
            fg="#cfd8e3",
            bg=bg,
            selectcolor=ebg,
            activebackground=bg
        ).pack(anchor="w", padx=10, pady=6)

        types_frame = tk.LabelFrame(
            self.root,
            text=" Asset Types To Organize ",
            fg=fg,
            bg=bg,
            font=("Segoe UI", 10, "bold")
        )
        types_frame.pack(fill="x", padx=14, pady=(0, 8))

        self.type_vars = {}
        type_row_1 = tk.Frame(types_frame, bg=bg)
        type_row_1.pack(fill="x", padx=10, pady=(6, 2))
        type_row_2 = tk.Frame(types_frame, bg=bg)
        type_row_2.pack(fill="x", padx=10, pady=(0, 6))

        row1_types = [
            "Textures",
            "Sounds",
            "Meshes",
            "Materials",
            "MaterialInstances",
            "MaterialFunctions",
            "MaterialParameterCollections",
        ]

        row2_types = [
            "Blueprints",
            "WidgetBlueprints",
            "Niagara",
            "Animations",
            "Data",
            "DataLayerAssets",
            "LevelSequences",
        ]

        for t in row1_types:
            var = tk.BooleanVar(value=True)
            self.type_vars[t] = var
            tk.Checkbutton(
                type_row_1,
                text=t,
                variable=var,
                fg="#cfd8e3",
                bg=bg,
                selectcolor=ebg,
                activebackground=bg
            ).pack(side="left", padx=(0, 14))

        for t in row2_types:
            var = tk.BooleanVar(value=True)
            self.type_vars[t] = var
            tk.Checkbutton(
                type_row_2,
                text=t,
                variable=var,
                fg="#cfd8e3",
                bg=bg,
                selectcolor=ebg,
                activebackground=bg
            ).pack(side="left", padx=(0, 14))

        self.summary_lbl = tk.Label(self.root, text="Ready.", fg="#aab4c3", bg=bg, font=("Segoe UI", 9))
        self.summary_lbl.pack(anchor="w", padx=14, pady=(0, 6))

        org_title = tk.Label(self.root, text="ORGANIZE PREVIEW", fg="#e5edf7", bg=bg, font=("Segoe UI", 10, "bold"))
        org_title.pack(anchor="w", padx=14, pady=(0, 4))

        header = tk.Frame(self.root, bg="#101827")
        header.pack(fill="x", padx=14)

        columns = [
            ("Asset", 30),
            ("Class", 24),
            ("Type", 28),
            ("Category", 18),
            ("Destination", 54),
        ]
        for text, width in columns:
            tk.Label(
                header,
                text=text,
                width=width,
                anchor="w",
                fg="#dbe4f0",
                bg="#101827",
                font=("Segoe UI", 9, "bold")
            ).pack(side="left", padx=2, pady=6)

        outer = tk.Frame(self.root, bg=bg)
        outer.pack(fill="both", expand=True, padx=14, pady=(0, 8))

        self.canvas = tk.Canvas(outer, bg="#0f1724", highlightthickness=0, height=650)
        self.scrollbar = tk.Scrollbar(outer, orient="vertical", command=self.canvas.yview)
        self.list_frame = tk.Frame(self.canvas, bg="#0f1724")

        self.list_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.create_window((0, 0), window=self.list_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        self.status_lbl = tk.Label(self.root, text="Ready", fg="#7f8ea3", bg=bg, font=("Segoe UI", 9))
        self.status_lbl.pack(anchor="w", padx=14, pady=(0, 10))

    def set_status(self, text):
        try:
            self.status_lbl.configure(text=text)
        except Exception:
            pass

    def clear_rows(self):
        for w in self.row_widgets:
            try:
                w.destroy()
            except Exception:
                pass
        self.row_widgets = []

    def get_enabled_types(self):
        return {name for name, var in self.type_vars.items() if var.get()}

    def add_row(self, idx, row):
        bg1 = "#132033"
        bg2 = "#101827"
        fg = "#e5edf7"
        bg = bg1 if idx % 2 == 0 else bg2

        frame = tk.Frame(self.list_frame, bg=bg)
        frame.pack(fill="x", pady=1)
        self.row_widgets.append(frame)

        tk.Label(frame, text=row["asset_name"], width=30, anchor="w", fg=fg, bg=bg, font=("Consolas", 9)).pack(side="left", padx=2)
        tk.Label(frame, text=row["class_name"], width=24, anchor="w", fg=fg, bg=bg).pack(side="left", padx=2)
        tk.Label(frame, text=row["selectable_type"], width=28, anchor="w", fg=fg, bg=bg).pack(side="left", padx=2)
        tk.Label(frame, text=row["category"], width=18, anchor="w", fg=fg, bg=bg).pack(side="left", padx=2)
        tk.Label(frame, text=row["dest_dir"], width=54, anchor="w", fg="#9ecbff", bg=bg, font=("Consolas", 8)).pack(side="left", padx=2)

    def scan(self):
        self.clear_rows()

        scan_root = normalize_path(self.scan_var.get().strip() or DEFAULT_SCAN_ROOT)
        org_name = sanitize_folder_name(self.org_var.get().strip() or DEFAULT_ORGANIZED_ROOT_NAME)
        enabled_types = self.get_enabled_types()
        include_unused_assets = self.include_unused_var.get()

        if not unreal.EditorAssetLibrary.does_directory_exist(scan_root):
            messagebox.showerror("Invalid Path", f"Folder does not exist:\n{scan_root}")
            return

        if not enabled_types:
            messagebox.showwarning("No Types Selected", "Enable at least one asset type.")
            return

        self.set_status(f"Scanning {scan_root} ...")
        self.root.update_idletasks()

        try:
            self.plan, self.skipped, self.organized_root = build_plan(
                scan_root,
                org_name,
                enabled_types,
                include_unused_assets
            )

            counts = defaultdict(int)
            for row in self.plan:
                counts[row["selectable_type"]] += 1

            mode_text = "including unused assets" if include_unused_assets else "used by current level only"

            count_text = ", ".join([f"{k}={v}" for k, v in sorted(counts.items())]) if counts else "No supported assets found"

            self.summary_lbl.configure(
                text=(
                    f"Found {len(self.plan)} assets to organize ({mode_text}). {count_text}"
                )
            )

            for i, row in enumerate(self.plan):
                self.add_row(i, row)

            self.set_status(f"Scan complete. Planned moves: {len(self.plan)} | Skipped: {len(self.skipped)}")
            log(f"Scan complete under {scan_root}: {len(self.plan)} planned moves")
        except Exception as e:
            err(f"Scan failed: {e}")
            self.set_status(f"Scan failed: {e}")
            messagebox.showerror("Scan Failed", str(e))

    def organize(self):
        if not self.plan:
            messagebox.showinfo("Nothing To Organize", "Run a scan first.")
            return

        include_unused_assets = self.include_unused_var.get()
        mode_text = (
            "including assets not used by the current level"
            if include_unused_assets else
            "only assets used or referenced by the current level"
        )

        msg = (
            f"This will move {len(self.plan)} assets into:\n{self.organized_root}\n\n"
            f"Scan mode: {mode_text}\n"
            f"Folders will be auto-created by selected asset type and guessed category.\n"
            f"Assets already inside the organized root or already existing at the exact destination are ignored.\n"
            f"Moves use Unreal's asset rename/move behavior so references should remain valid via redirectors.\n\n"
            f"Continue?"
        )

        if not messagebox.askyesno("Confirm Organize", msg):
            return

        self.set_status("Organizing assets ...")
        self.root.update_idletasks()

        try:
            ensure_directory(self.organized_root)

            moved, failed = execute_plan(self.plan, self.organized_root)
            redirectors = scan_redirectors(normalize_path(self.scan_var.get().strip() or DEFAULT_SCAN_ROOT))

            summary = (
                f"Moved: {len(moved)}\n"
                f"Failed: {len(failed)}\n"
                f"Redirectors detected afterward: {len(redirectors)}"
            )

            if failed:
                preview = "\n".join(
                    [f"{f[0]['asset_name']} -> {f[1]}" for f in failed[:20]]
                )
                summary += "\n\nFailures:\n" + preview

            if redirectors:
                summary += "\n\nRedirectors after moves are normal and help keep references intact."

            messagebox.showinfo("Organize Results", summary)
            self.set_status(f"Organize complete. Moved={len(moved)} Failed={len(failed)} Redirectors={len(redirectors)}")

            self.scan()
        except Exception as e:
            err(f"Organize failed: {e}")
            self.set_status(f"Organize failed: {e}")
            messagebox.showerror("Organize Failed", str(e))

    def start_tick(self):
        def on_tick(dt):
            try:
                if not self.root.winfo_exists():
                    self.stop_tick()
                    return
                self.root.update()
            except tk.TclError:
                self.stop_tick()
            except Exception as e:
                warn(f"Tick error: {e}")
                self.stop_tick()

        self.tick_handle = unreal.register_slate_post_tick_callback(on_tick)
        log("Auto Type Organizer opened.")

    def stop_tick(self):
        if self.tick_handle:
            unreal.unregister_slate_post_tick_callback(self.tick_handle)
            self.tick_handle = None
            log("Auto Type Organizer closed.")


AutoTypeOrganizerApp()