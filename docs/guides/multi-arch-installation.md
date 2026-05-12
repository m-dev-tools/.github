# m-dev-tools install — multi-arch fix plan

## Problem

On Apple Silicon (`darwin/arm64`), `bash <(curl ...setup.sh)` fails after a green
pre-flight. The wrapper hands off to `make bootstrap` which calls `m engine install`,
which calls `docker pull ghcr.io/m-dev-tools/m-test-engine:0.1.0`. The image is
published linux/amd64-only, so the pull dies with:

```
no matching manifest for linux/arm64/v8 in the manifest list entries
```

The user sees `make: *** [bootstrap] Error 1` with the Docker daemon error
buried one line above — no actionable remediation surfaced.

Verified by `docker manifest inspect`: only `linux/amd64` is published.

## Root cause

The installer confuses **prerequisite presence** with **prerequisite
compatibility**. Every pre-flight check asks "is X installed?" but none ask
"will X work for this host's architecture?" The OS is detected (`setup.sh:91`)
but `arch` is never read or branched on, and no manifest inspection is done
against the images the bootstrap will pull.

This is one root cause expressed at three layers. Fix in priority order:

---

## Layer 1 — Publish a multi-arch engine image (proper fix)

**Repo:** `m-dev-tools/m-test-engine`

The `r2.02` YDB binaries inside the image are the only thing keeping it
architecture-specific. YDB does ship arm64 builds, so a multi-arch build is
feasible.

**Plan:**

1. Convert the image build to `docker buildx` with `--platform linux/amd64,linux/arm64`.
2. If the Dockerfile fetches YDB binaries by URL, parameterize the URL on
   `$TARGETARCH` (buildx exposes this automatically inside the build).
3. Push as a manifest list to GHCR:
   ```
   docker buildx build \
     --platform linux/amd64,linux/arm64 \
     --tag ghcr.io/m-dev-tools/m-test-engine:0.1.1 \
     --push .
   ```
4. Add CI matrix (`.github/workflows/release.yml`) so every tag publishes both
   architectures by default.
5. Bump `default_tag` in `dist/m-test-engine.json` to `0.1.1`. Re-vendor into
   `m-cli/dist/m-test-engine.json` (the Makefile already has a vendoring rule
   at `m-cli/Makefile:166–170`).
6. Verification: `docker manifest inspect ghcr.io/m-dev-tools/m-test-engine:0.1.1`
   should list both `linux/amd64` and `linux/arm64` platforms.

Once shipped, layers 2 and 3 become defense-in-depth rather than hard
requirements — but still worth doing for the next time an arch gap appears.

---

## Layer 2 — `engine_driver.py` honors a platform override (architectural fix)

**Repo:** `m-dev-tools/m-cli`

Even with a multi-arch image, the driver should support pinning a platform
(e.g. for reproducing amd64-only bugs from an arm64 host, or for images that
genuinely can't go multi-arch).

**Plan:**

1. Extend `dist/m-test-engine.json` schema with an optional field:
   ```json
   "platforms": ["linux/amd64", "linux/arm64"],
   "platform_override_env": "M_ENGINE_PLATFORM"
   ```
   Update `m-test-engine.schema.json` accordingly.
2. In `src/m_cli/engine_manifest.py`, parse the new fields.
3. In `src/m_cli/engine_driver.py`, when issuing `docker pull` / `docker run` /
   `docker create`, append `--platform <value>` if either:
   - `$M_ENGINE_PLATFORM` is set, or
   - the local arch is not in the manifest's `platforms` list and a fallback
     is configured.
4. `m doctor` gains a check: if the running container's platform differs from
   the host's native platform, print an info line (not a warning) noting
   Rosetta/qemu emulation is in effect.
5. Tests: add a unit test for `engine_driver` that asserts `--platform` is
   passed when `M_ENGINE_PLATFORM` is set in the env.

---

## Layer 3 — `setup.sh` pre-flight surfaces arch mismatch (defense-in-depth)

**Repo:** `m-dev-tools/.github`, file `setup.sh`

The wrapper script currently detects OS but not arch, and never inspects the
images the bootstrap will pull. A 5-line pre-flight check would have turned
this session's cryptic failure into a clear, actionable warning.

**Plan:**

1. After OS detection (`setup.sh:97`), add arch detection:
   ```bash
   ARCH=$(uname -m)
   case "$ARCH" in
     arm64|aarch64) ARCH=arm64 ;;
     x86_64|amd64)  ARCH=amd64 ;;
     *) warn "Unknown arch: $ARCH — proceeding without arch checks" ;;
   esac
   info "Detected arch: $ARCH"
   ```
2. After the Docker-daemon check (`setup.sh:193`), inspect the engine image's
   manifest list. Hardcoding the image string here is acceptable since the
   wrapper is purpose-built for this toolchain — or fetch it from the
   vendored `dist/m-test-engine.json` once available:
   ```bash
   IMAGE="ghcr.io/m-dev-tools/m-test-engine:0.1.0"
   if ! docker manifest inspect "$IMAGE" 2>/dev/null \
        | grep -q "\"architecture\": \"$ARCH\""; then
     warn "Engine image $IMAGE has no $ARCH manifest."
     warn "Bootstrap will set DOCKER_DEFAULT_PLATFORM=linux/amd64 to run under emulation."
     export DOCKER_DEFAULT_PLATFORM=linux/amd64
   fi
   ```
3. Fix the stale cask name at `setup.sh:131`: replace
   `brew install --cask docker` with `brew install --cask docker-desktop`.
   The old cask was renamed; the current line sends users to a dead path.
4. Optional: gate `make bootstrap` behind a final confirmation when
   `DOCKER_DEFAULT_PLATFORM` was force-set, so the user understands they're
   opting into emulation.

---

## Other issues found during this install

| Issue | Location | Fix |
|---|---|---|
| Old cask name in hint | `setup.sh:131` | `docker` → `docker-desktop` |
| Failure mode is opaque | `make bootstrap` (Makefile:76) | wrap `m engine install` in a trap that prints the actionable remediation when Docker pull errors mention "no matching manifest" |
| `engine_driver` swallows the underlying Docker error in some paths | `engine_driver.py` | propagate Docker stderr to the user verbatim on engine-install failure |

---

## Verification (post-fix)

On a clean Apple Silicon Mac with Docker Desktop running:

```
bash <(curl -fsSL https://raw.githubusercontent.com/m-dev-tools/.github/main/setup.sh) -y
```

Expected outcome:
- Pre-flight prints `Detected arch: arm64` and either confirms the engine
  image has an arm64 manifest, or auto-sets `DOCKER_DEFAULT_PLATFORM` with a
  visible warning.
- `make bootstrap` completes without intervention.
- `m doctor` reports 7/7 OK.
- `docker inspect m-test-engine --format '{{.Platform}}'` shows `linux/arm64`
  (after Layer 1) or `linux/amd64` with an info line about emulation (Layer 2
  + 3 fallback).

## Out of scope

- Migrating off Docker entirely (e.g. a native YDB install path) — separate
  initiative.
- Windows support — `setup.sh` already targets macOS + Linux only.
