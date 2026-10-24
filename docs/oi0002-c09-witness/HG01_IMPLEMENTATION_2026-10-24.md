# C09/R3 HG-01 governed implementation

## BP-01 frozen development build profile

Status: `PASS / PROFILE_FROZEN / NO EXECUTABLE YET`.

Host evidence: CPython `3.14.2`, Windows amd64, and installed pywin32 `312`. PyInstaller was not preinstalled. The selected profile uses PyInstaller `6.22.3` in `onedir` mode with `--clean`, no UPX and three distinct role-specific executables/directories. `onedir` preserves observable role-specific executable paths and avoids one-file temporary extraction. PyInstaller is a packaging tool only and introduces no runtime authority.

`requirements-hg01-build.txt` pins PyInstaller, pywin32 and all build-time transitive dependencies to exact versions and downloaded wheel SHA-256 values. Installation is binary-only with `--require-hashes`. The frozen machine-readable profile is `config/c09-r3/hg01-build-profile.json`.

Two clean builds are mandatory. Whole output trees must be compared by relative path and SHA-256. Bit-for-bit reproducibility may be claimed only if every entry matches; otherwise every difference must be recorded and the package remains not approval-ready. Development artifacts are unsigned. Operational Authenticode signing remains a separate Human Gate and custody decision.

Focused build-profile/security verification: `35 passed`. No package was installed, no executable was built, no service source or host state changed, and no reproducibility claim is made.

Exact continuation: `HG01-I01` three explicit service entry points and non-privileged lifecycle harnesses, followed by focused tests and checkpointing.
