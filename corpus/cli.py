"""CLI: `corpus list | build <id>|--all | stats <id>|--all | manifest | export`."""

import argparse
import json
import logging
from pathlib import Path

from corpus.export import export
from corpus.manifest import build_manifest
from corpus.pipeline import ingest_source, load_source, write_jsonl

REPO_ROOT = Path(__file__).resolve().parent.parent
SOURCES_DIR = REPO_ROOT / "sources"
NORMALIZED_DIR = REPO_ROOT / "data" / "normalized"

# GitHub blocks pushes of files over 100MB; warn before a build gets close.
GIT_SIZE_WARN_BYTES = 90 * 1024 * 1024


def _iter_source_dirs():
    if not SOURCES_DIR.exists():
        return
    for d in sorted(SOURCES_DIR.iterdir()):
        if d.is_dir() and (d / "source.yaml").exists():
            yield d


def _resolve_source_ids(args) -> list[str]:
    if args.all:
        return [d.name for d in _iter_source_dirs()]
    if not args.source_id:
        raise SystemExit("Specify a source_id or pass --all")
    return [args.source_id]


def cmd_list(_args):
    rows = []
    for d in _iter_source_dirs():
        meta = load_source(d)
        rows.append((meta.source_id, meta.source_name, meta.license))
    if not rows:
        print("No sources configured. Add one under sources/<id>/.")
        return
    width = max(len(r[0]) for r in rows)
    for sid, name, lic in rows:
        print(f"{sid:<{width}}  {name}  [{lic}]")


def cmd_build(args):
    for sid in _resolve_source_ids(args):
        source_dir = SOURCES_DIR / sid
        if not source_dir.exists():
            raise SystemExit(f"Source not found: {source_dir}")
        output_path = NORMALIZED_DIR / f"{sid}.jsonl"
        n = write_jsonl(ingest_source(source_dir), output_path)
        print(f"Wrote {n:,} documents to {output_path}")
        size = output_path.stat().st_size
        if size > GIT_SIZE_WARN_BYTES:
            print(
                f"  WARNING: {output_path.name} is {size / 1_000_000:.0f}MB, near GitHub's "
                f"100MB limit. Move data/normalized/*.jsonl to Git LFS (see README)."
            )


def cmd_stats(args):
    sids = (
        [d.name for d in _iter_source_dirs()]
        if args.all
        else ([args.source_id] if args.source_id else [])
    )
    if not sids:
        raise SystemExit("Specify a source_id or pass --all")
    total_docs = 0
    total_chars = 0
    for sid in sids:
        path = NORMALIZED_DIR / f"{sid}.jsonl"
        if not path.exists():
            print(f"{sid}: not built")
            continue
        n_docs = 0
        n_chars = 0
        with open(path, encoding="utf-8") as f:
            for line in f:
                n_docs += 1
                n_chars += len(json.loads(line)["text"])
        print(f"{sid:<30} {n_docs:>8,} docs  {n_chars:>14,} chars")
        total_docs += n_docs
        total_chars += n_chars
    if args.all:
        print(f"{'TOTAL':<30} {total_docs:>8,} docs  {total_chars:>14,} chars")


def cmd_manifest(_args):
    manifest = build_manifest(NORMALIZED_DIR, SOURCES_DIR)
    out_path = NORMALIZED_DIR / "manifest.json"
    out_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    totals = manifest["totals"]
    print(f"Wrote {out_path.name}: {totals['source_count']} sources, {totals['doc_count']:,} docs")


def _csv_set(value: str | None) -> set[str] | None:
    return {v.strip() for v in value.split(",") if v.strip()} if value else None


def cmd_export(args):
    out_path = Path(args.output)
    if not out_path.is_absolute():
        out_path = REPO_ROOT / out_path
    result = export(
        NORMALIZED_DIR,
        SOURCES_DIR,
        out_path,
        genres=_csv_set(args.genre),
        license_categories=_csv_set(args.license_category),
        scripts=_csv_set(args.script),
        text_only=args.text_only,
    )
    n_docs = result["doc_count"]
    n_src = len(result["sources"])
    print(f"Exported {n_docs:,} docs from {n_src} sources -> {result['output']}")
    print(f"  sources: {', '.join(result['sources']) or '(none matched)'}")
    print(f"  license_category: {', '.join(result['license_categories']) or '-'}")


def main():
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
    )
    p = argparse.ArgumentParser(prog="corpus")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("list", help="List configured sources").set_defaults(func=cmd_list)

    build = sub.add_parser("build", help="Ingest one source (or --all) into normalized JSONL")
    build.add_argument("source_id", nargs="?")
    build.add_argument("--all", action="store_true", help="Build every configured source")
    build.set_defaults(func=cmd_build)

    stats = sub.add_parser("stats", help="Show doc/char counts for a built source (or --all)")
    stats.add_argument("source_id", nargs="?")
    stats.add_argument("--all", action="store_true")
    stats.set_defaults(func=cmd_stats)

    sub.add_parser(
        "manifest", help="Write data/normalized/manifest.json (per-source genre/license/counts)"
    ).set_defaults(func=cmd_manifest)

    exp = sub.add_parser("export", help="Write a filtered training JSONL (by genre/license/script)")
    exp.add_argument("-o", "--output", default="data/export/corpus.jsonl")
    exp.add_argument("--genre", help="comma-separated genres, e.g. prose,news")
    exp.add_argument("--license-category", help="comma-separated, e.g. permissive,share_alike")
    exp.add_argument("--script", help="comma-separated, e.g. han,hanlo")
    exp.add_argument("--text-only", action="store_true", help="emit {id, source_id, text} only")
    exp.set_defaults(func=cmd_export)

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
