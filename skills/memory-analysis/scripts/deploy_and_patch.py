"""kubectl helpers for capability A: bring up a sleep pod from a deployment yaml,
push patched sglang code, then launch sglang and collect the memory logs.

These wrap kubectl and REQUIRE a reachable cluster (kubeconfig from the input
material). They are intentionally thin so the Agent/user can review each command
before it runs. Nothing here is destructive beyond creating a pod the user asked
for; deletion is left to the user.
"""

import subprocess
from typing import List, Optional


def _run(cmd: List[str], kubeconfig: Optional[str] = None, check=True) -> str:
    env_prefix = ["kubectl"]
    if kubeconfig:
        env_prefix += ["--kubeconfig", kubeconfig]
    full = env_prefix + cmd
    print("+", " ".join(full))
    r = subprocess.run(full, capture_output=True, text=True)
    if check and r.returncode != 0:
        raise RuntimeError(f"kubectl failed: {r.stderr.strip()}")
    return r.stdout


def make_sleep_yaml(src_yaml: str, dst_yaml: str) -> str:
    """Rewrite the container command to `sleep infinity` so we can exec/patch
    before launching sglang ourselves.

    CONSTRAINT: all probes (livenessProbe / readinessProbe / startupProbe) are
    STRIPPED from every container. A sleeping container never serves the
    health endpoint, so a surviving liveness probe would keep failing and
    kubelet would restart/rebuild the pod mid-analysis (losing the patched
    code and the launched server)."""
    import yaml
    with open(src_yaml) as f:
        docs = [d for d in yaml.safe_load_all(f) if d]

    _PROBES = ("livenessProbe", "readinessProbe", "startupProbe")

    def patch(obj):
        if isinstance(obj, dict):
            if "containers" in obj and isinstance(obj["containers"], list):
                for c in obj["containers"]:
                    for probe in _PROBES:
                        if c.pop(probe, None) is not None:
                            print(f"[sleep-yaml] stripped {probe} from "
                                  f"container {c.get('name', '?')}")
                    blob = " ".join(map(str, (c.get("command") or []) +
                                        (c.get("args") or [])))
                    if "launch_server" in blob or "sglang" in blob:
                        c["command"] = ["/bin/sh", "-c", "sleep infinity"]
                        c.pop("args", None)
            for v in obj.values():
                patch(v)
        elif isinstance(obj, list):
            for it in obj:
                patch(it)

    for d in docs:
        patch(d)
    with open(dst_yaml, "w") as f:
        yaml.safe_dump_all(docs, f)
    return dst_yaml


def apply(dst_yaml: str, kubeconfig=None) -> str:
    return _run(["apply", "-f", dst_yaml], kubeconfig)


def _pods_of_yaml(src_yaml: str, ns: str, kubeconfig) -> List[str]:
    """Resolve the pod name(s) a yaml creates: kind Pod -> metadata.name;
    workloads (Deployment/StatefulSet/...) -> template-label selector lookup."""
    import yaml
    with open(src_yaml) as f:
        docs = [d for d in yaml.safe_load_all(f) if d]
    names: List[str] = []
    for d in docs:
        kind = (d.get("kind") or "").lower()
        if kind == "pod":
            names.append(d["metadata"]["name"])
            continue
        labels = (((d.get("spec") or {}).get("template") or {})
                  .get("metadata") or {}).get("labels") or {}
        if labels:
            sel = ",".join(f"{k}={v}" for k, v in labels.items())
            out = _run(["get", "pods", "-n", ns, "-l", sel,
                        "-o", "jsonpath={.items[*].metadata.name}"],
                       kubeconfig, check=False)
            cand = out.split()
            # Template labels may be SHARED across unrelated workloads in the
            # namespace; a bare selector would then match other people's live
            # pods. Keep only pods whose name is prefixed by this workload's
            # own metadata.name (Deployment/FedDeployment pods are named
            # <workload>-<hash>-...).
            wl_name = (d.get("metadata") or {}).get("name")
            if wl_name:
                owned = [p for p in cand if p.startswith(wl_name + "-")]
                if not owned and cand:
                    print(f"[pods-of-yaml] WARNING: selector matched only "
                          f"foreign pods (none prefixed by {wl_name}-); "
                          f"ignoring them")
                cand = owned
            names.extend(cand)
    return names


def ensure_sleep_pod(src_yaml: str, dst_yaml: str, ns="default", kubeconfig=None,
                     timeout_s=600, poll=10) -> List[str]:
    """One call = rewrite to `sleep infinity` (probes stripped -- see
    make_sleep_yaml, otherwise liveness failures rebuild the pod mid-analysis)
    + apply + WAIT until Ready.

    Idempotent: re-applying an existing sleep pod is a no-op. Returns the pod
    name list (raises on timeout so the full-auto flow stops with a reason
    instead of exec-ing into a Pending pod)."""
    import time
    make_sleep_yaml(src_yaml, dst_yaml)
    apply(dst_yaml, kubeconfig)
    deadline = time.time() + timeout_s
    pods: List[str] = []
    while time.time() < deadline:
        pods = _pods_of_yaml(dst_yaml, ns, kubeconfig)
        if pods:
            ready = []
            for pod in pods:
                phase = _run(["get", "pod", "-n", ns, pod,
                              "-o", "jsonpath={.status.phase}"],
                             kubeconfig, check=False).strip()
                ready.append(phase == "Running")
            if ready and all(ready):
                print(f"[sleep-pod] ready: {pods}")
                return pods
        time.sleep(poll)
    raise RuntimeError(
        f"sleep pod not Running within {timeout_s}s (pods={pods or 'none'}); "
        f"check quota/scheduling: kubectl describe -f {dst_yaml}")


def cp_into_pod(pod: str, local: str, remote: str, ns="default", kubeconfig=None):
    return _run(["cp", local, f"{ns}/{pod}:{remote}"], kubeconfig)


def exec_in_pod(pod: str, sh_cmd: str, ns="default", kubeconfig=None, check=True):
    return _run(["exec", "-n", ns, pod, "--", "/bin/sh", "-c", sh_cmd],
                kubeconfig, check=check)


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        raise SystemExit("usage: deploy_and_patch.py <src.yaml> <dst_sleep.yaml>")
    print("wrote:", make_sleep_yaml(sys.argv[1], sys.argv[2]))
    print("Next: kubectl apply -f the sleep yaml, then cp_into_pod/exec_in_pod.")
