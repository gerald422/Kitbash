# ---------------------------------------------------------------- UI

class TIOW_AddonPrefs(bpy.types.AddonPreferences):
    bl_idname = __name__

    listening: BoolProperty(
        name="Listen for TIOW", default=True,
        description="Import items sent from TIOW-FTRP's Send to Blender")
    inbox_path: StringProperty(
        name="Inbox Folder", subtype='DIR_PATH', default="",
        description="Empty uses TIOW-FTRP's own: "
                    "%LOCALAPPDATA%\\TIOW-FTRP\\local-data\\blender-inbox")
    builder_inbox: StringProperty(
        name="Squad Builder Inbox", subtype='DIR_PATH',
        default="D:\\Kitbash Library\\_builder\\inbox",
        description="Where the Squad Builder page sends parts: the inbox folder inside your "
                    "library's _builder folder (browsers can't write into AppData). Watched "
                    "only when that _builder folder exists. Empty = off")
    placement: EnumProperty(
        name="Place", default='BOUNDS',
        items=(('BOUNDS', "Centred on 3D Cursor",
                "Move the part so its geometry is centred on the cursor; "
                "the origin stays where the file had it"),
               ('ORIGIN', "Origin at 3D Cursor",
                "Put the file's origin on the cursor"),
               ('FILE', "As in File", "Leave the STL coordinates untouched")))
    by_category: BoolProperty(
        name="Collection per TIOW Category", default=True,
        description="Put each part in a collection named after its TIOW "
                    "category (Arms, Heads...), which Cycle Variant uses as "
                    "its pool")
    fallback_collection: StringProperty(
        name="Uncategorised Collection", default="TIOW Imports")
    millimetres: BoolProperty(
        name="Convert mm to Scene Units", default=False,
        description="Off: 1 STL unit = 1 Blender unit, the same as importing "
                    "by hand, so new parts match the ones already in your "
                    "files. On: treat STL units as millimetres and scale to "
                    "the scene's unit scale")
    max_age_minutes: IntProperty(
        name="Drop Requests Older Than (min)", default=5, min=1, max=1440)
    auto_snap: BoolProperty(
        name="Snap onto Selected Model", default=True,
        description="Put each part on the free socket of its joint in the "
                    "model you have selected (arms on Shoulder, pistols on "
                    "Hand...). Needs Part Sockets")
    replaced: EnumProperty(
        name="Swapped-out Part", default='DELETE',
        items=(('DELETE', "Delete if from TIOW",
                "Parts that came from TIOW are deleted when another part takes "
                "their socket (send them again to get them back); your own "
                "parts go to their Dressing Room home"),
               ('HOME', "Send Home",
                "Every swapped-out part goes to its Dressing Room home, or the "
                "world origin")))
    adaptor_dir: StringProperty(
        name="Body Adaptors", subtype='DIR_PATH', default="D:\\new cults\\body adaptor",
        description="Folder of body adaptors (lower_body_(torso)_1..6 with their "
                    ".sockets.json). Flat-topped legs (Marta, Turtle Ninja) bring one "
                    "onto a Mar Fil torso's Waist")
    stand_on_base: BoolProperty(
        name="Stand on the Base", default=True,
        description="When a base (or terrain) snaps onto the legs' Base socket, turn the whole "
                    "model so the base sits flat on the grid - so the pose reads as it will "
                    "stand. Only the model's root moves; the joints don't change")
    correct_folder: BoolProperty(
        name="Whole Folder", default=False,
        description="Save Correction applies the same move to every part in the folder (one kit's "
                    "arms, its torsos...), not just this file")
    correct_both: BoolProperty(
        name="Both Sides", default=True,
        description="Save Correction also gives the other side the mirror image (left hand, left pad, "
                    "left shoulder, a maker's left copy)")
    adaptor_default: IntProperty(
        name="Adaptor", default=3, min=1, max=99,
        description="Which adaptor flat legs bring (number in the folder, in order); "
                    "Next Adaptor swaps the one on the model")

    def draw(self, ctx):
        col = self.layout.column()
        col.prop(self, "listening")
        col.prop(self, "inbox_path")
        if not self.inbox_path:
            col.label(text=default_inbox(), icon='FILE_FOLDER')
        col.prop(self, "builder_inbox")
        col.prop(self, "placement")
        col.prop(self, "by_category")
        sub = col.row()
        sub.enabled = self.by_category
        sub.prop(self, "fallback_collection")
        col.prop(self, "millimetres")
        col.prop(self, "max_age_minutes")
        col.prop(self, "auto_snap")
        sub = col.row()
        sub.enabled = self.auto_snap
        sub.prop(self, "replaced")
        col.prop(self, "adaptor_dir")
        col.prop(self, "adaptor_default")
        col.prop(self, "stand_on_base")


class TIOW_PT_inbox(bpy.types.Panel):
    bl_label = "TIOW Inbox"
    bl_idname = "TIOW_PT_inbox"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Sockets"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, ctx):
        prefs = get_prefs()
        if prefs is None:
            return
        col = self.layout.column()
        col.prop(prefs, "listening",
                 icon='LINKED' if prefs.listening else 'UNLINKED')
        col.prop(prefs, "placement", text="")
        col.prop(prefs, "auto_snap")
        row = col.row(align=True)
        row.prop(prefs, "stand_on_base", text="Stand on Base")
        row.operator("tiow.stand_on_base", text="Level Now", icon='MESH_PLANE')
        col.operator("tiow.mirror_part", icon='MOD_MIRROR')
        box = self.layout.box()
        box.label(text="Anchors (click on the part)")
        grid = box.grid_flow(columns=2, align=True, row_major=True)
        for a in ANCHORS_THREE + ANCHORS_ONE:
            grid.operator("tiow.place_anchor", text=a).anchor = a
        box.operator("tiow.find_shins", icon='VIEWZOOM')
        box.operator("tiow.save_folder_fit", icon='PINNED')
        box = self.layout.box()
        box.label(text="Save Correction (move the part, then)")
        row = box.row(align=True)
        row.operator("tiow.save_correction", text="Fix the Part", icon='OBJECT_DATA').what = 'PART'
        row.operator("tiow.save_correction", text="Fix the Socket", icon='EMPTY_ARROWS').what = 'SOCKET'
        row = box.row(align=True)
        row.prop(prefs, "correct_folder")
        row.prop(prefs, "correct_both")
        row = self.layout.row(align=True)
        row.prop(prefs, "adaptor_default", text="Adaptor")
        row.operator("tiow.next_adaptor", text="Next Adaptor", icon='FILE_REFRESH')
        if ctx.mode != 'OBJECT' and prefs.listening:
            col.label(text="Waiting for Object Mode", icon='INFO')
        if _state["last"]:
            col.label(text=_state["last"])


def find_adaptor(ob):
    """The body adaptor in the model around `ob` (or `ob` itself)."""
    if ob is None:
        return None
    if ob.get("tiow_category") == "Adapters":
        return ob
    root = ob
    while root.parent is not None:
        root = root.parent
    ps = _part_sockets()
    for o in [root] + list(_descendants(root)):
        if o.get("tiow_category") == "Adapters":
            return o
    if ps is not None:
        _, co = ps
        mine = {root} | set(_descendants(root))
        for o in bpy.context.view_layer.objects:
            if o.get("tiow_category") == "Adapters" and co.snap_socket_of(o) in mine:
                return o
    return None


def next_adaptor(ob, prefs, step=1):
    """Swap the model's body adaptor for the next one in the folder; the legs
    on it move across. Returns a status note."""
    ad = find_adaptor(ob)
    if ad is None:
        return "no body adaptor on the selected model"
    files = adaptor_files(prefs)
    if not files:
        return f"no body adaptors in {prefs.adaptor_dir}"
    cur = os.path.normcase(os.path.abspath(str(ad.get("tiow_src") or "")))
    norm = [os.path.normcase(os.path.abspath(f)) for f in files]
    i = norm.index(cur) if cur in norm else -1
    path = files[(i + step) % len(files)]
    unit = float(ad.get("tiow_unit", 1.0))
    job = {"path": path, "category": "Adapters", "_unit": unit}
    new, meshes, s, made, added = load_stl(path, job, prefs)
    if len(meshes) != 1:
        return "the adaptor file is not one mesh"
    note = auto_snap(meshes[0], job, prefs, ad)
    prefs.adaptor_default = files.index(path) + 1
    return f"{os.path.splitext(os.path.basename(path))[0]}{note}"


class TIOW_OT_stand_on_base(bpy.types.Operator):
    """Turn the selected model so its base (the legs' Base socket) sits flat on
    the grid: only the model's root moves, the joints don't change"""
    bl_idname = "tiow.stand_on_base"
    bl_label = "Stand on Base"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, ctx):
        return ctx.mode == 'OBJECT' and ctx.view_layer.objects.active is not None

    def execute(self, ctx):
        sock = base_socket_of(ctx.view_layer.objects.active)
        if sock is None:
            self.report({'WARNING'}, "No Base socket on the selected model (legs carry it)")
            return {'CANCELLED'}
        tilt = stand_on_base(sock)
        msg = f"Stood {sock.parent.name if sock.parent else 'the model'} on its base (took out {tilt:.1f} deg)"
        _set_status(msg)
        self.report({'INFO'}, msg)
        return {'FINISHED'}


class TIOW_OT_next_adaptor(bpy.types.Operator):
    """Swap the body adaptor on the selected model for the next one in the
    Body Adaptors folder (the legs stay on). It also becomes the one flat legs bring"""
    bl_idname = "tiow.next_adaptor"
    bl_label = "Next Adaptor"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, ctx):
        prefs = get_prefs()
        ob = ctx.view_layer.objects.active
        msg = next_adaptor(ob, prefs)
        _set_status(msg)
        self.report({'INFO'}, msg)
        return {'FINISHED'}


classes = (TIOW_AddonPrefs, TIOW_OT_place_anchor, TIOW_OT_find_shins, TIOW_OT_save_folder_fit, TIOW_OT_save_correction, TIOW_OT_stand_on_base,
           TIOW_OT_next_adaptor, TIOW_OT_mirror_part, TIOW_PT_inbox)


def register():
    for c in classes:
        bpy.utils.register_class(c)
    if not bpy.app.timers.is_registered(_timer):
        bpy.app.timers.register(_timer, first_interval=1.0, persistent=True)


def unregister():
    if bpy.app.timers.is_registered(_timer):
        bpy.app.timers.unregister(_timer)
    for c in reversed(classes):
        bpy.utils.unregister_class(c)

