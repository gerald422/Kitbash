# ---------------------------------------------------------------- polling

def _beat(inbox):
    now = time.time()
    if now - _state["beat"].get(inbox, 0.0) < HEARTBEAT_SECONDS:
        return
    _state["beat"][inbox] = now
    p = os.path.join(inbox, HEARTBEAT)
    try:
        with open(p, "a"):
            pass
        os.utime(p, None)
    except OSError:
        pass


def _redraw():
    wm = bpy.context.window_manager
    for win in getattr(wm, "windows", []):
        for area in win.screen.areas:
            if area.type == 'VIEW_3D':
                area.tag_redraw()


def _set_status(msg):
    _state["last"] = msg
    print(f"[TIOW Inbox] {msg}")
    _redraw()


def process_inbox():
    """Handle every waiting request. Returns how many were imported."""
    prefs = get_prefs()
    if prefs is None or not prefs.listening:
        return 0
    jobs = []
    for inbox in inbox_dirs(prefs):
        try:
            os.makedirs(inbox, exist_ok=True)
        except OSError:
            continue
        _beat(inbox)
        if bpy.context.mode != 'OBJECT':
            # leave requests unclaimed; they import when you Tab back out
            continue
        try:
            jobs += [(inbox, n) for n in sorted(os.listdir(inbox)) if n.endswith(".json")]
        except OSError:
            continue

    done = 0
    for inbox, name in jobs:
        src = os.path.join(inbox, name)
        claimed = f"{src}.{os.getpid()}.claimed"
        try:
            os.replace(src, claimed)      # a second Blender loses this race
        except OSError:
            continue
        try:
            age = time.time() - os.path.getmtime(claimed)
            with open(claimed, encoding="utf-8") as f:
                job = json.load(f)
            if not isinstance(job, dict):
                raise ValueError("not a request")
            if age > prefs.max_age_minutes * 60:
                _set_status(f"Skipped stale request for "
                            f"{job.get('name', name)} "
                            f"({int(age // 60)} min old)")
                continue
            new = import_request(job, prefs)
            where = new[0].users_collection[0].name if new[0].users_collection else "scene"
            extra = ""
            if job.get("_sockets"):
                extra = f" with {job['_sockets']} socket(s)"
            if job.get("_types"):
                extra += f", fit types added: {', '.join(job['_types'])}"
            extra += (job.get("_found") or "") + (job.get("_snap") or "")
            _set_status(f"Imported {new[0].name} into {where}{extra}")
            done += 1
        except (OSError, ValueError, RuntimeError) as exc:
            _set_status(f"Could not import {name}: {exc}")
        finally:
            try:
                os.remove(claimed)
            except OSError:
                pass
    return done


def _timer():
    try:
        process_inbox()
    except Exception as exc:          # a timer that raises is unregistered
        print(f"[TIOW Inbox] {exc!r}")
    return POLL_SECONDS

