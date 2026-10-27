import datetime
import os
import shutil
import tempfile

from ..errors import PrivMetaError, UnsupportedFormat
from ..fsio import backup, collect, resolve_output
from ..image import exif, xmp
from ..output import fail, info, ok, warn
from ..sniff import detect, IMAGE

FIELDS = ("exif", "gps", "xmp", "iptc", "icc", "comments", "thumbnail")


def resolve_plan(args):
    if args.all_fields and (args.drop or args.keep):
        raise PrivMetaError("--all cannot be combined with --drop or --keep")
    if args.drop and args.keep:
        raise PrivMetaError("--drop and --keep cannot be used together")
    if args.drop:
        selected = _parse_list(args.drop, "--drop")
        return {field: field in selected for field in FIELDS}
    if args.keep:
        kept = _parse_list(args.keep, "--keep")
        return {field: field not in kept for field in FIELDS}
    return {field: True for field in FIELDS}


def _parse_list(value, flag):
    items = {item.strip().lower() for item in value.split(",") if item.strip()}
    if not items:
        raise PrivMetaError(f"{flag} must name at least one field")
    unknown = items - set(FIELDS)
    if unknown:
        raise PrivMetaError(f"Unknown fields in {flag}: {', '.join(sorted(unknown))}")
    return items


def _exif_stage(source, stage, plan):
    if plan["exif"]:
        exif.strip_all(source, stage)
        return
    data = exif.read(source)
    dirty = False
    if plan["gps"] and data.get("GPS"):
        data["GPS"] = {}
        dirty = True
    if plan["thumbnail"] and data.get("thumbnail"):
        data["thumbnail"] = None
        data["1st"] = {}
        dirty = True
    if dirty:
        exif.write(source, data, stage)
    else:
        shutil.copy2(source, stage)


def _apply_source_mode(source, target):
    try:
        mode = os.stat(source).st_mode & 0o777
    except OSError:
        return
    try:
        os.chmod(target, mode)
    except OSError:
        pass


def _clean_jpeg(source, target, plan):
    exif_layer = plan["exif"] or plan["gps"] or plan["thumbnail"]
    byte_layer = plan["xmp"] or plan["iptc"] or plan["icc"] or plan["comments"]
    if exif_layer:
        directory = os.path.dirname(os.path.abspath(target)) or "."
        fd, stage = tempfile.mkstemp(dir=directory, prefix=".privmeta.")
        os.close(fd)
        _exif_stage(source, stage, plan)
        byte_source = stage
    else:
        stage = None
        byte_source = source
    if byte_layer:
        xmp.strip(
            byte_source,
            target,
            drop_xmp=plan["xmp"],
            drop_iptc=plan["iptc"],
            drop_icc=plan["icc"],
            drop_comments=plan["comments"],
        )
    else:
        if byte_source != target:
            if os.path.exists(target):
                os.unlink(target)
            os.replace(byte_source, target)
    if stage and os.path.exists(stage) and stage != target:
        os.unlink(stage)


def _clean_image(source, target, plan, label):
    if not any(plan.values()):
        shutil.copy2(source, target)
    elif label == "jpeg":
        _clean_jpeg(source, target, plan)
    else:
        xmp.strip(
            source,
            target,
            drop_xmp=plan["xmp"],
            drop_iptc=plan["iptc"],
            drop_icc=plan["icc"],
            drop_comments=plan["comments"],
            drop_exif=plan["exif"] or plan["gps"],
        )
    _apply_source_mode(source, target)


def _reset_time(path):
    stamp = datetime.datetime(2020, 1, 1, 12, 0, 0).timestamp()
    os.utime(path, (stamp, stamp))


def _rename_neutral(path, index):
    directory = os.path.dirname(os.path.abspath(path))
    extension = os.path.splitext(path)[1]
    base = f"photo_{index:04d}"
    candidate = os.path.join(directory, base + extension)
    counter = 1
    while os.path.exists(candidate):
        candidate = os.path.join(directory, f"{base}_{counter}{extension}")
        counter += 1
    os.rename(path, candidate)
    return candidate


def _handle_one(source, args, plan, index, counters):
    try:
        target = resolve_output(source, args.output_dir)
        if args.dry_run:
            fields = [name for name, active in plan.items() if active]
            info(f"dry run: {source}")
            info(f"fields: {', '.join(fields) if fields else 'none'}")
            counters["dry"] += 1
            return
        family, label = detect(source)
        if family != IMAGE:
            warn(f"skipped (not an image): {source}")
            counters["skipped"] += 1
            return
        _clean_image(source, target, plan, label)
        if args.rename:
            target = _rename_neutral(target, index)
        if args.reset_time:
            _reset_time(target)
        if args.inplace:
            if args.keep_backup:
                backup(source)
            os.replace(target, source)
            target = source
        ok(f"cleaned: {source} -> {target}")
        counters["ok"] += 1
    except (PrivMetaError, UnsupportedFormat, OSError) as exc:
        fail(f"{source}: {exc}")
        counters["fail"] += 1
        if args.fail_fast:
            raise


def run(args):
    plan = resolve_plan(args)
    targets, warnings = collect(args.paths, args.recursive)
    for message in warnings:
        warn(message)
    info(f"plan: {', '.join(name for name, active in plan.items() if active) or 'none'}")
    counters = {"ok": 0, "fail": 0, "skipped": 0, "dry": 0}
    for index, source in enumerate(targets, start=1):
        try:
            _handle_one(source, args, plan, index, counters)
        except PrivMetaError as exc:
            fail(str(exc))
            return 2
    ok(
        f"done: {counters['ok']} ok, {counters['fail']} failed, "
        f"{counters['skipped']} skipped, {counters['dry']} dry"
    )
    return 0 if counters["fail"] == 0 else 2
