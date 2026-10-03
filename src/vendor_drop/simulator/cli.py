import argparse
import os
from pathlib import Path

from vendor_drop.simulator.build import build_all

DEFAULT_PERIODS = "202601,202602,202603"


def cmd_build(args: argparse.Namespace) -> None:
    if not args.data_dir:
        raise SystemExit("set the FREDDIE_DATA_DIR environment variable or pass --data-dir")
    data_dir = Path(args.data_dir)
    periods = [p.strip() for p in args.periods.split(",") if p.strip()]
    build_all(
        orig_path=data_dir / "sample_orig_2023.txt",
        perf_path=data_dir / "sample_perf_2023.txt",
        periods=periods,
        out_dir=Path(args.out),
    )


def cmd_drop(args: argparse.Namespace) -> None:
    from databricks.sdk import WorkspaceClient  # imported here so `build` works without Databricks

    w = WorkspaceClient()  # uses the same profile as the CLI (DATABRICKS_CONFIG_PROFILE=free)
    out_dir = Path(args.out)
    if args.all:
        folders = sorted(p for p in out_dir.glob("*/*") if p.is_dir())
    else:
        folders = [out_dir / args.servicer / args.period]
    for folder in folders:
        servicer, period = folder.parent.name, folder.name
        remote_dir = f"/Volumes/vendor_drop_{args.env}/landing/inbound/{servicer}/{period}"
        w.files.create_directory(remote_dir)
        for local in sorted(folder.glob("*.txt")) + [folder / "manifest.json"]:  # manifest last
            with open(local, "rb") as f:
                w.files.upload(f"{remote_dir}/{local.name}", f, overwrite=True)
            print(f"uploaded {remote_dir}/{local.name}")


def main() -> None:
    parser = argparse.ArgumentParser(prog="vendor_drop.simulator")
    sub = parser.add_subparsers(dest="command", required=True)

    b = sub.add_parser("build", help="generate drop folders locally")
    b.add_argument("--periods", default=DEFAULT_PERIODS)
    b.add_argument("--out", default="out")
    b.add_argument("--data-dir", default=os.environ.get("FREDDIE_DATA_DIR", ""))
    b.set_defaults(func=cmd_build)

    d = sub.add_parser("drop", help="upload drop folders to the landing volume")
    d.add_argument("--env", default="dev")
    d.add_argument("--out", default="out")
    group = d.add_mutually_exclusive_group(required=True)
    group.add_argument("--all", action="store_true")
    group.add_argument("--servicer")
    d.add_argument("--period")
    d.set_defaults(func=cmd_drop)

    args = parser.parse_args()
    if args.command == "drop" and args.servicer and not args.period:
        parser.error("--period is required with --servicer")
    args.func(args)


if __name__ == "__main__":
    main()
