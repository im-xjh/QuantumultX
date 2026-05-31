#!/usr/bin/env python3
"""Observe Claude client connections and infer the active egress IP on macOS.

This tool does not inspect HTTPS contents. It only reads local process tables,
socket tables, route information, system proxy settings, and public IP echo
services.
"""

from __future__ import annotations

import argparse
import dataclasses
import ipaddress
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import time
from collections import defaultdict
from typing import Iterable


CLAUDE_DOMAINS = (
    "claude.ai",
    "www.claude.ai",
    "api.anthropic.com",
    "anthropic.com",
    "console.anthropic.com",
)

IP_ECHO_URLS = (
    "https://api.ipify.org?format=json",
    "https://checkip.amazonaws.com/",
    "https://icanhazip.com/",
)

DEFAULT_SECONDS = 45
DEFAULT_INTERVAL = 1.0
COMMAND_TIMEOUT = 6


@dataclasses.dataclass(frozen=True)
class ProcessInfo:
    pid: int
    ppid: int
    command: str

    @property
    def name(self) -> str:
        return friendly_process_name(self.command)


@dataclasses.dataclass(frozen=True)
class Connection:
    pid: int
    command: str
    proto: str
    remote_ip: str
    remote_port: str

    @property
    def remote(self) -> str:
        if ":" in self.remote_ip and not self.remote_ip.startswith("["):
            return f"[{self.remote_ip}]:{self.remote_port}"
        return f"{self.remote_ip}:{self.remote_port}"


@dataclasses.dataclass
class Observation:
    target: str
    process: str
    pid: int
    proto: str
    remote_ip: str
    remote_port: str
    route_if: str
    egress_ip: str
    confidence: str
    note: str
    first_seen: float
    last_seen: float
    count: int = 1

    @property
    def remote(self) -> str:
        if ":" in self.remote_ip and not self.remote_ip.startswith("["):
            return f"[{self.remote_ip}]:{self.remote_port}"
        return f"{self.remote_ip}:{self.remote_port}"


@dataclasses.dataclass(frozen=True)
class EgressResult:
    context: str
    ip: str
    confidence: str
    source: str
    proxy: str
    error: str


def run_command(
    args: list[str],
    *,
    timeout: int | float = COMMAND_TIMEOUT,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            args,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout,
            env=env,
        )
    except FileNotFoundError as exc:
        return subprocess.CompletedProcess(args, 127, "", str(exc))
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout if isinstance(exc.stdout, str) else ""
        stderr = exc.stderr if isinstance(exc.stderr, str) else f"Timed out after {timeout}s"
        return subprocess.CompletedProcess(args, 124, stdout, stderr)


def friendly_process_name(command: str) -> str:
    lower = command.lower()
    if "google chrome" in lower:
        return "Google Chrome"
    if "brave browser" in lower:
        return "Brave Browser"
    if "microsoft edge" in lower:
        return "Microsoft Edge"
    if "arc.app" in lower or "/arc" in lower:
        return "Arc"
    if "safari" in lower and "com.apple.safari" in lower:
        return "Safari"
    if "/applications/claude.app" in lower:
        if "chrome-native-host" in lower:
            return "chrome-native-host"
        if "helper" in lower:
            return "Claude Helper"
        return "Claude"
    if "claude-code" in lower or "@anthropic-ai" in lower:
        return "Claude Code"
    if re.search(r"(^|/|\s)claude(\s|$)", lower):
        return "claude"
    if re.search(r"(^|/|\s)node(\s|$)", lower):
        return "node"
    token = command.strip().split(" ", 1)[0] if command.strip() else "unknown"
    return os.path.basename(token) or token


def read_process_table() -> dict[int, ProcessInfo]:
    result = run_command(["ps", "axww", "-o", "pid=", "-o", "ppid=", "-o", "command="])
    processes: dict[int, ProcessInfo] = {}
    if result.returncode != 0:
        return processes
    for line in result.stdout.splitlines():
        parts = line.strip().split(None, 2)
        if len(parts) < 3:
            continue
        try:
            pid = int(parts[0])
            ppid = int(parts[1])
        except ValueError:
            continue
        processes[pid] = ProcessInfo(pid=pid, ppid=ppid, command=parts[2])
    return processes


def descendants(processes: dict[int, ProcessInfo], roots: Iterable[int]) -> set[int]:
    children: dict[int, list[int]] = defaultdict(list)
    for proc in processes.values():
        children[proc.ppid].append(proc.pid)

    seen: set[int] = set()
    stack = list(roots)
    while stack:
        pid = stack.pop()
        if pid in seen:
            continue
        seen.add(pid)
        stack.extend(children.get(pid, []))
    return seen


def discover_pids(
    target: str,
    *,
    browser: str | None = None,
    explicit_pids: list[int] | None = None,
) -> tuple[dict[int, ProcessInfo], set[int], list[str]]:
    processes = read_process_table()
    warnings: list[str] = []
    if explicit_pids:
        roots = {pid for pid in explicit_pids if pid in processes}
        missing = sorted(set(explicit_pids) - roots)
        if missing:
            warnings.append(f"PID not found: {', '.join(str(pid) for pid in missing)}")
        return processes, descendants(processes, roots), warnings

    own_pid = os.getpid()
    own_ppid = os.getppid()
    roots: set[int] = set()
    claude_bin = shutil.which("claude")
    claude_bin_lower = claude_bin.lower() if claude_bin else ""

    for pid, proc in processes.items():
        if pid in (own_pid, own_ppid):
            continue
        command = proc.command
        lower = command.lower()
        if "claude_ip_check.py" in lower:
            continue

        if target == "desktop":
            if (
                "/applications/claude.app" in lower
                or "claude helper" in lower
                or ("chrome-native-host" in lower and "claude" in lower)
            ):
                roots.add(pid)
        elif target == "cli":
            if "/applications/claude.app" in lower:
                continue
            if claude_bin_lower and claude_bin_lower in lower:
                roots.add(pid)
            elif "claude-code" in lower or "@anthropic-ai" in lower:
                roots.add(pid)
            elif re.search(r"(^|/|\s)claude(\s|$)", lower):
                roots.add(pid)
        elif target == "web":
            if not browser:
                warnings.append("web target requires --browser or --pid")
                break
            if browser.lower() in lower:
                roots.add(pid)

    return processes, descendants(processes, roots), warnings


def parse_remote_endpoint(endpoint: str) -> tuple[str, str] | None:
    endpoint = endpoint.strip().strip(",")
    if endpoint.startswith("["):
        match = re.match(r"^\[([^\]]+)\]:(\d+|[A-Za-z][A-Za-z0-9_-]*)$", endpoint)
        if not match:
            return None
        ip, port = match.groups()
    else:
        if endpoint.count(":") == 0:
            return None
        ip, port = endpoint.rsplit(":", 1)
    ip = ip.strip("[]")
    try:
        ipaddress.ip_address(ip)
    except ValueError:
        return None
    return ip, port


def parse_lsof_output(output: str, proto: str, allowed_pids: set[int]) -> list[Connection]:
    connections: list[Connection] = []
    for line in output.splitlines():
        if not line or line.startswith("COMMAND "):
            continue
        parts = line.split(None, 8)
        if len(parts) < 9:
            continue
        try:
            pid = int(parts[1])
        except ValueError:
            continue
        if pid not in allowed_pids:
            continue
        name = parts[8]
        if "->" not in name:
            continue
        remote_part = name.split("->", 1)[1].split(None, 1)[0]
        parsed = parse_remote_endpoint(remote_part)
        if not parsed:
            continue
        remote_ip, remote_port = parsed
        connections.append(
            Connection(
                pid=pid,
                command=parts[0],
                proto=proto,
                remote_ip=remote_ip,
                remote_port=remote_port,
            )
        )
    return connections


def collect_connections(allowed_pids: set[int], *, include_udp: bool = False) -> list[Connection]:
    if not allowed_pids:
        return []
    tcp = run_command(["lsof", "-nP", "-iTCP", "-sTCP:ESTABLISHED"], timeout=4)
    connections = parse_lsof_output(tcp.stdout, "tcp", allowed_pids) if tcp.returncode in (0, 1) else []
    if include_udp:
        udp = run_command(["lsof", "-nP", "-iUDP"], timeout=4)
        if udp.returncode in (0, 1):
            connections.extend(parse_lsof_output(udp.stdout, "udp", allowed_pids))
    return connections


def resolve_candidate_ips(domains: Iterable[str] = CLAUDE_DOMAINS) -> dict[str, set[str]]:
    resolved: dict[str, set[str]] = {}
    original_timeout = socket.getdefaulttimeout()
    socket.setdefaulttimeout(2)
    try:
        for domain in domains:
            ips: set[str] = set()
            try:
                infos = socket.getaddrinfo(domain, 443, proto=socket.IPPROTO_TCP)
            except OSError:
                resolved[domain] = ips
                continue
            for info in infos:
                address = info[4][0]
                try:
                    ips.add(str(ipaddress.ip_address(address)))
                except ValueError:
                    continue
            resolved[domain] = ips
    finally:
        socket.setdefaulttimeout(original_timeout)
    return resolved


def classify_connection(remote_ip: str, resolved: dict[str, set[str]]) -> str:
    matched = sorted(domain for domain, ips in resolved.items() if remote_ip in ips)
    if matched:
        return "dns-match:" + ",".join(matched[:2])
    return "process-observed"


def route_interface(remote_ip: str, cache: dict[str, str]) -> str:
    if remote_ip in cache:
        return cache[remote_ip]
    try:
        ip_obj = ipaddress.ip_address(remote_ip)
    except ValueError:
        cache[remote_ip] = "-"
        return "-"
    args = ["route", "-n", "get"]
    if ip_obj.version == 6:
        args.append("-inet6")
    args.append(remote_ip)
    result = run_command(args, timeout=3)
    interface = "-"
    if result.returncode == 0:
        for line in result.stdout.splitlines():
            stripped = line.strip()
            if stripped.startswith("interface:"):
                interface = stripped.split(":", 1)[1].strip() or "-"
                break
    cache[remote_ip] = interface
    return interface


def parse_scutil_proxy() -> dict[str, str]:
    result = run_command(["scutil", "--proxy"], timeout=3)
    values: dict[str, str] = {}
    if result.returncode != 0:
        return values
    for line in result.stdout.splitlines():
        match = re.match(r"^\s*([A-Za-z0-9_]+)\s*:\s*(.*?)\s*$", line)
        if match:
            values[match.group(1)] = match.group(2)
    return values


def system_proxy_url(values: dict[str, str]) -> str:
    if values.get("HTTPSEnable") == "1" and values.get("HTTPSProxy") and values.get("HTTPSPort"):
        return f"http://{values['HTTPSProxy']}:{values['HTTPSPort']}"
    if values.get("HTTPEnable") == "1" and values.get("HTTPProxy") and values.get("HTTPPort"):
        return f"http://{values['HTTPProxy']}:{values['HTTPPort']}"
    if values.get("SOCKSEnable") == "1" and values.get("SOCKSProxy") and values.get("SOCKSPort"):
        return f"socks5h://{values['SOCKSProxy']}:{values['SOCKSPort']}"
    return ""


def proxy_summary(values: dict[str, str]) -> str:
    parts: list[str] = []
    if values.get("HTTPEnable") == "1":
        parts.append(f"HTTP={values.get('HTTPProxy', '?')}:{values.get('HTTPPort', '?')}")
    if values.get("HTTPSEnable") == "1":
        parts.append(f"HTTPS={values.get('HTTPSProxy', '?')}:{values.get('HTTPSPort', '?')}")
    if values.get("SOCKSEnable") == "1":
        parts.append(f"SOCKS={values.get('SOCKSProxy', '?')}:{values.get('SOCKSPort', '?')}")
    return ", ".join(parts) if parts else "-"


def parse_ip_echo(text: str) -> str:
    text = text.strip()
    if not text:
        return ""
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        data = None
    if isinstance(data, dict) and isinstance(data.get("ip"), str):
        candidate = data["ip"].strip()
    else:
        match = re.search(r"([0-9]{1,3}(?:\.[0-9]{1,3}){3}|[0-9A-Fa-f:]{3,})", text)
        candidate = match.group(1) if match else ""
    try:
        return str(ipaddress.ip_address(candidate))
    except ValueError:
        return ""


def curl_ip(url: str, *, proxy: str = "", env: dict[str, str] | None = None) -> tuple[str, str]:
    args = ["curl", "-fsSL", "--max-time", "6", "-A", "claude-ip-check/1.0"]
    if proxy:
        args.extend(["--proxy", proxy])
    args.append(url)
    result = run_command(args, timeout=8, env=env)
    if result.returncode != 0:
        return "", result.stderr.strip() or f"curl exited {result.returncode}"
    ip = parse_ip_echo(result.stdout)
    if not ip:
        return "", "no IP found in echo response"
    return ip, ""


def get_egress(context: str) -> EgressResult:
    if context not in {"system", "shell"}:
        raise ValueError(f"Unsupported egress context: {context}")

    proxy = ""
    env = os.environ.copy()
    confidence = f"inferred-{context}"
    if context == "system":
        proxy = system_proxy_url(parse_scutil_proxy())
        # Avoid shell proxy variables overriding explicit macOS proxy probing.
        for key in ("http_proxy", "https_proxy", "all_proxy", "HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY"):
            env.pop(key, None)

    errors: list[str] = []
    for url in IP_ECHO_URLS:
        ip, error = curl_ip(url, proxy=proxy, env=env)
        if ip:
            return EgressResult(
                context=context,
                ip=ip,
                confidence=confidence,
                source=url,
                proxy=proxy or "-",
                error="",
            )
        errors.append(f"{url}: {error}")

    return EgressResult(
        context=context,
        ip="-",
        confidence=f"unavailable-{context}",
        source="-",
        proxy=proxy or "-",
        error="; ".join(errors),
    )


def get_egress_for_target(target: str, explicit_context: str) -> EgressResult:
    if explicit_context == "none":
        return EgressResult(target, "-", "not-collected", "-", "-", "")
    if explicit_context in {"system", "shell"}:
        return get_egress(explicit_context)
    if target == "cli":
        return get_egress("shell")
    return get_egress("system")


def load_quantumult_hint(config_path: str | None) -> str:
    if not config_path:
        default_path = os.path.join(os.getcwd(), "quantumult_20260409.conf")
        config_path = default_path if os.path.exists(default_path) else ""
    if not config_path or not os.path.exists(config_path):
        return ""
    try:
        with open(config_path, "r", encoding="utf-8", errors="replace") as handle:
            text = handle.read()
    except OSError:
        return ""
    if "Ai-All-In-One" in text and "force-policy=美国IP" in text:
        return "Quantumult X hint: AI rules appear to force-policy=美国IP. Treat this as policy intent, not measured egress."
    if re.search(r"AI.*force-policy=美国IP|force-policy=美国IP.*AI", text, flags=re.IGNORECASE):
        return "Quantumult X hint: AI rules appear to force-policy=美国IP. Treat this as policy intent, not measured egress."
    return ""


def print_table(rows: list[dict[str, object]], columns: list[str]) -> None:
    if not rows:
        print("(no rows)")
        return
    widths: dict[str, int] = {}
    for column in columns:
        widths[column] = max(len(column), *(len(str(row.get(column, ""))) for row in rows))
    header = "  ".join(column.ljust(widths[column]) for column in columns)
    separator = "  ".join("-" * widths[column] for column in columns)
    print(header)
    print(separator)
    for row in rows:
        print("  ".join(str(row.get(column, "")).ljust(widths[column]) for column in columns))


def observations_to_rows(observations: list[Observation]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for obs in sorted(observations, key=lambda item: (item.target, item.process, item.pid, item.remote)):
        rows.append(
            {
                "target": obs.target,
                "process": obs.process,
                "pid": obs.pid,
                "proto": obs.proto,
                "remote_ip:port": obs.remote,
                "route_if": obs.route_if,
                "egress_ip": obs.egress_ip,
                "confidence": obs.confidence,
                "seen": obs.count,
                "note": obs.note,
            }
        )
    return rows


def observe_once(
    *,
    target: str,
    pids: set[int],
    processes: dict[int, ProcessInfo],
    egress: EgressResult,
    resolved: dict[str, set[str]],
    route_cache: dict[str, str],
    include_udp: bool,
) -> list[Observation]:
    now = time.time()
    observations: list[Observation] = []
    for conn in collect_connections(pids, include_udp=include_udp):
        process = processes.get(conn.pid)
        process_name = process.name if process else friendly_process_name(conn.command)
        note = classify_connection(conn.remote_ip, resolved)
        observations.append(
            Observation(
                target=target,
                process=process_name,
                pid=conn.pid,
                proto=conn.proto,
                remote_ip=conn.remote_ip,
                remote_port=conn.remote_port,
                route_if=route_interface(conn.remote_ip, route_cache),
                egress_ip=egress.ip,
                confidence=egress.confidence,
                note=note,
                first_seen=now,
                last_seen=now,
            )
        )
    return observations


def merge_observations(store: dict[tuple[int, str, str, str], Observation], observations: list[Observation]) -> None:
    for obs in observations:
        key = (obs.pid, obs.proto, obs.remote_ip, obs.remote_port)
        existing = store.get(key)
        if existing is None:
            store[key] = obs
            continue
        existing.last_seen = obs.last_seen
        existing.count += 1
        existing.route_if = obs.route_if
        existing.egress_ip = obs.egress_ip
        existing.confidence = obs.confidence
        existing.note = obs.note


def command_egress(args: argparse.Namespace) -> int:
    contexts = ["system", "shell"] if args.context == "both" else [args.context]
    rows: list[dict[str, object]] = []
    for context in contexts:
        result = get_egress(context)
        rows.append(
            {
                "context": result.context,
                "egress_ip": result.ip,
                "confidence": result.confidence,
                "source": result.source,
                "proxy": result.proxy,
                "error": result.error,
            }
        )
    if args.json:
        print(json.dumps(rows, ensure_ascii=False, indent=2))
    else:
        print_table(rows, ["context", "egress_ip", "confidence", "source", "proxy", "error"])
        scutil = parse_scutil_proxy()
        print(f"\nSystem proxy: {proxy_summary(scutil)}")
    return 0 if all(row["egress_ip"] != "-" for row in rows) else 2


def command_snapshot(args: argparse.Namespace) -> int:
    processes, pids, warnings = discover_pids(
        args.target,
        explicit_pids=args.pid,
    )
    for warning in warnings:
        print(f"warning: {warning}", file=sys.stderr)
    if not pids:
        print("error: no matching PID found", file=sys.stderr)
        return 2

    egress = get_egress_for_target(args.target, args.egress_context)
    resolved = resolve_candidate_ips()
    route_cache: dict[str, str] = {}
    observations = observe_once(
        target=args.target,
        pids=pids,
        processes=processes,
        egress=egress,
        resolved=resolved,
        route_cache=route_cache,
        include_udp=args.include_udp,
    )
    rows = observations_to_rows(observations)
    if args.json:
        print(json.dumps(rows, ensure_ascii=False, indent=2))
    else:
        print_table(
            rows,
            ["target", "process", "pid", "proto", "remote_ip:port", "route_if", "egress_ip", "confidence", "seen", "note"],
        )
    return 0 if rows else 1


def command_watch(args: argparse.Namespace) -> int:
    if args.target == "web" and not args.browser and not args.pid:
        print("error: watch web requires --browser or --pid", file=sys.stderr)
        return 2
    seconds = max(1, int(args.seconds))
    interval = max(0.25, float(args.interval))
    egress = get_egress_for_target(args.target, args.egress_context)
    resolved = resolve_candidate_ips()
    route_cache: dict[str, str] = {}
    observations: dict[tuple[int, str, str, str], Observation] = {}

    deadline = time.time() + seconds
    first_iteration = True
    last_pids: set[int] = set()
    warnings_seen: set[str] = set()

    if not args.json:
        print(
            f"Watching target={args.target} seconds={seconds} egress={egress.ip} "
            f"confidence={egress.confidence}"
        )
        if args.target in {"desktop", "web"}:
            hint = load_quantumult_hint(args.config)
            if hint:
                print(hint)

    while time.time() < deadline:
        processes, pids, warnings = discover_pids(
            args.target,
            browser=args.browser,
            explicit_pids=args.pid,
        )
        for warning in warnings:
            if warning not in warnings_seen and not args.json:
                print(f"warning: {warning}", file=sys.stderr)
                warnings_seen.add(warning)

        if pids:
            last_pids = pids
            batch = observe_once(
                target=args.target,
                pids=pids,
                processes=processes,
                egress=egress,
                resolved=resolved,
                route_cache=route_cache,
                include_udp=args.include_udp,
            )
            merge_observations(observations, batch)
        elif first_iteration and not args.json:
            print("No matching process yet. Open/activate the Claude client and trigger one request.")

        first_iteration = False
        time.sleep(min(interval, max(0.0, deadline - time.time())))

    rows = observations_to_rows(list(observations.values()))
    if args.json:
        print(json.dumps(rows, ensure_ascii=False, indent=2))
    else:
        if not rows:
            print("\nNo established Claude-client connections were observed.")
            if not last_pids:
                print("No matching process was found during the watch window.")
            print("Try increasing --seconds, passing --pid, or using a clean browser profile/window for web.")
        else:
            print()
            print_table(
                rows,
                ["target", "process", "pid", "proto", "remote_ip:port", "route_if", "egress_ip", "confidence", "seen", "note"],
            )
    return 0 if rows else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Observe Claude Web/Desktop/CLI target IPs and infer macOS egress IP.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    egress = subparsers.add_parser("egress", help="Show inferred public egress IP.")
    egress.add_argument("--context", choices=("both", "system", "shell"), default="both")
    egress.add_argument("--json", action="store_true", help="Emit JSON.")
    egress.set_defaults(func=command_egress)

    snapshot = subparsers.add_parser("snapshot", help="Snapshot established connections for PID(s).")
    snapshot.add_argument("--pid", action="append", type=int, required=True, help="PID to inspect. Can be repeated.")
    snapshot.add_argument("--target", choices=("snapshot", "web", "desktop", "cli"), default="snapshot")
    snapshot.add_argument("--egress-context", choices=("auto", "system", "shell", "none"), default="auto")
    snapshot.add_argument("--include-udp", action="store_true", help="Also inspect UDP sockets with lsof.")
    snapshot.add_argument("--json", action="store_true", help="Emit JSON.")
    snapshot.set_defaults(func=command_snapshot)

    watch = subparsers.add_parser("watch", help="Watch a Claude target for a short time window.")
    watch.add_argument("target", choices=("web", "desktop", "cli"))
    watch.add_argument("--browser", help='Browser process name for web target, e.g. "Google Chrome".')
    watch.add_argument("--pid", action="append", type=int, help="PID to inspect instead of target discovery. Can be repeated.")
    watch.add_argument("--seconds", type=int, default=DEFAULT_SECONDS)
    watch.add_argument("--interval", type=float, default=DEFAULT_INTERVAL)
    watch.add_argument("--egress-context", choices=("auto", "system", "shell", "none"), default="auto")
    watch.add_argument("--include-udp", action="store_true", help="Also inspect UDP sockets with lsof.")
    watch.add_argument("--config", help="Quantumult X config path for optional policy hint.")
    watch.add_argument("--json", action="store_true", help="Emit JSON.")
    watch.set_defaults(func=command_watch)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
