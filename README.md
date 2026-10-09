# ZCode Sync (`zcode-sync`)

[![Tauri v2](https://img.shields.io/badge/Tauri-v2.1-blue.svg?logo=tauri&logoColor=white)](https://tauri.app)
[![Rust](https://img.shields.io/badge/Rust-1.93-orange.svg?logo=rust&logoColor=white)](https://www.rust-lang.org)
[![React](https://img.shields.io/badge/React-19-61dafb.svg?logo=react&logoColor=black)](https://react.dev)
[![Tailwind CSS](https://img.shields.io/badge/TailwindCSS-v3.4-38bdf8.svg?logo=tailwind-css&logoColor=white)](https://tailwindcss.com)
[![Bundle Size](https://img.shields.io/badge/Binary_Size-4.5_MB-success.svg)](https://github.com/mixyoung/zcode-sync/releases)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

> A blazing-fast (<120ms cold start), ultra-lightweight (**4.5 MB** single binary), and beautifully crafted native desktop management center for **ZCode** model providers and AI endpoints.
> Built with **Rust + Tauri v2 + React 19 + Tailwind CSS + Lucide Icons**.
> Supports **S3 / Cloudflare R2** and **WebDAV** cloud sync, remote backup, lifecycle retention policies, and dual light/dark themes.

---

### [📖 简体中文文档](README_zh.md)

---

## 📸 Screenshots

### Modern Dual-Theme Interface (Follows System by Default)

| ☀️ Clean Slate Light Theme | 🌙 Zinc Industrial Dark Theme |
| :---: | :---: |
| ![Light Theme](docs/images/screenshot_light.png) | ![Dark Theme](docs/images/screenshot_dark.png) |

### Cloud Sync Hub & Provider Drawer

| ☁️ S3 / Cloudflare R2 & WebDAV Cloud Hub | ✏️ Provider Visual & JSON Editor Drawer |
| :---: | :---: |
| ![Cloud Sync Hub](docs/images/screenshot_cloud_sync.png) | ![Edit Provider](docs/images/screenshot_edit.png) |

---

## ✨ Key Features

- **☁️ S3 / Cloudflare R2 & WebDAV Cloud Sync (New)**:
  - **S3 & R2 Support**: Native SigV4 HMAC-SHA256 authorization without heavy AWS SDKs. Compatible with Cloudflare R2, AWS S3, MinIO, and Aliyun OSS.
  - **WebDAV Support**: Seamlessly syncs with Nutstore (坚果云), Nextcloud, Synology/QNAP NAS, and AList.
  - **Live Connectivity Test**: One-click handshake verification with clear diagnostic feedback.
- **⏱️ Smart Lifecycle Retention Policies (New)**:
  - **Max Versions (`max_versions`)**: Keep recent 5, 10 (default), 20, 50, or unlimited backups.
  - **Retention Days (`retention_days`)**: Auto-expire backups older than 7, 30 (default), 90, 180 days, or keep forever.
  - **Zero-Empty Safety Guarantee**: The newest backup is *never* deleted, ensuring your remote storage is never accidentally left empty.
  - **Remote Version History**: Browse remote snapshots, perform smart incremental restoration, or delete specific backups.
- **⚡ Ultra-compact Single Binary (~4.5 MB)**:
  - Compressed down to **4.5 MB** using pure Rust machine code, LTO, and system WebView2.
  - Zero Python or Node.js runtime required on target machines. Double-click and run anywhere.
- **🎨 Modern Dual Themes (Default: Follow System)**:
  - **Follow System (`system`)**: Real-time event listener via `window.matchMedia` seamlessly tracks Windows OS Light/Dark theme switching without application restarts.
  - **Manual Override (`light` / `dark`)**: Dedicated 3-segment switcher (`[ 💻 System ]` / `[ ☀️ Light ]` / `[ 🌙 Dark ]`) with smooth 150ms CSS transitions and local storage persistence.
- **🔍 Native Dual-Schema Auto-Discovery**:
  - **Schema 2 Priority (`provider_config.json`)**: Accurately recognizes active modern configuration files (e.g., custom `mgw` endpoints with detailed model rules).
  - **Schema 1 Backward Compatibility (`config.json`)**: Seamlessly reads and edits legacy `provider` dictionaries.
  - Auto-scans `ZCODE_DATA_BASE_DIR`, `ZCODE_HOME`, fixed paths, and standard `~/.zcode` directories.
- **🛡️ Bulletproof Safety & Atomic Writes**:
  - **Double Automatic Backup**: Automatically creates `.bak` and timestamped `.bak.YYYYMMDD_HHMMSS` backups before modifying any target file.
  - **Atomic Replacement**: Writes to `.tmp` first and replaces target files via OS-level atomic rename to prevent corruption during sudden power-off.
- **📝 Form & JSON Bi-directional Editing**:
  - Visual form inputs for Name, Protocol, Base URL, API Key (with plain-text visibility toggle), and model list.
  - Raw JSON code editor with real-time bidirectional synchronization.
- **◈ Cross-Plan Duplicate Model Analysis**:
  - Automatically analyzes overlapping model declarations across packages (BigModel Coding Plan, Start Plan, API Key) and custom endpoints.
- **📋 Safe Multi-Device Sync (Export & Clipboard)**:
  - Fast clipboard copy/import and file export/import.
  - One-click **"Mask API Key on Export"** to share configurations securely without leaking sensitive tokens.

---

## 🚀 Quick Start

### Option 1: Run Precompiled Portable Binary (Recommended)
Download the standalone executable directly from the repository or [Releases](https://github.com/mixyoung/zcode-sync/releases):
```text
zcode-model-sync-tauri.exe   (or release/zcode-model-sync.exe)
```
No installation needed. Double-click to launch immediately on Windows 10 (1809+) and Windows 11.

### Option 2: Run in Development Mode
Prerequisites:
- [Node.js](https://nodejs.org/) (v18+) & [pnpm](https://pnpm.io/)
- [Rust](https://rustup.rs/) (v1.75+)

```bash
# Clone the repository
git clone https://github.com/mixyoung/zcode-sync.git
cd zcode-sync

# Install frontend dependencies
pnpm install

# Start development mode (Vite HMR + Tauri Window)
pnpm dev
# in another terminal:
pnpm tauri dev
```

---

## 📦 Build from Source

To compile the single-file release binary with full optimizations (LTO, stripped symbols):

```bash
# Production single-binary build
pnpm tauri build --no-bundle
```

The resulting executable will be generated at:
```text
src-tauri/target/release/zcode-model-sync.exe   (~4.5 MB)
```

---

## 🏗️ Architecture

```text
┌────────────────────────────────────────────────────────────────────────┐
│                   Frontend Presentation Layer (React 19)               │
│  - Vite + React 19 + TypeScript + Tailwind CSS                         │
│  - Lucide Icons (100% Vector)                                          │
│  - Dual Theme CSS Variable Engine (:root Light & .dark Dark)           │
│  - HeaderNav / ConfigSelector / FilterToolbar / Table / CloudSyncModal │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ Tauri v2 IPC (invoke)
┌───────────────────────────────────▼────────────────────────────────────┐
│                    Rust Core Engine (src-tauri)                        │
│  - cloud_storage: Lightweight S3/R2 SigV4, WebDAV HTTP & Retention     │
│  - path_detector: Scans candidate dirs for provider_config & config.json│
│  - sync_engine: Dual-schema parser, atomic writer, dual backup manager │
│  - models: Strongly typed Serde models (UnifiedProviderItem, Cloud)    │
│  - commands: Tauri IPC command handlers                                │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 📄 License

This project is open-sourced under the [MIT License](LICENSE).
