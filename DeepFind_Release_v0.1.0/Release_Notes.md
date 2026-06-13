# DeepFind v0.1.0

Welcome to the first packaged release of **DeepFind**, a local-first AI file search desktop application.

## Minimum Requirements
- **OS**: Windows 10 or Windows 11 (64-bit)
- **RAM**: 8 GB minimum (16 GB recommended for smooth semantic search)
- **Storage**: ~1.2 GB of free disk space for installation, plus additional space for local database indexing.
- **Network**: Internet is **NOT** required. DeepFind runs 100% locally and offline.

## Release Features
- **Instant File Search**: Search by exact filename, path, or extension globally.
- **Content Search (FTS5)**: Fast text search inside PDFs, Word documents, TXTs, and Code files.
- **Semantic Search**: Ask conceptual questions. The bundled `all-MiniLM-L6-v2` model processes your queries offline and matches them against document embeddings natively using FAISS.
- **Automated Background Indexing**: DeepFind automatically monitors your user folders (Documents, Downloads, Desktop) and indexes new files without manual intervention.

## Important Limitations
- **Unsigned Installer**: The current `DeepFind-Setup-0.1.0.exe` installer is not signed with a Microsoft Authenticode Certificate. When launching the installer, Windows SmartScreen will display a "Windows protected your PC" warning. To proceed, click **More info** -> **Run anyway**.
- **Installation Size**: The installer includes a bundled local AI model and the PyTorch runtime, resulting in a large installation footprint (~1.1 GB installed). Future updates will transition to optimized runtime formats (ONNX).
- **Default Branding**: A temporary default Electron application icon is currently used. 

## Uninstallation
To completely remove DeepFind from your system, use the "Add or remove programs" feature in Windows.
By default, the uninstaller **preserves your indexed databases and settings** in `%APPDATA%\DeepFind` so you do not lose your search history upon upgrading or reinstalling.
