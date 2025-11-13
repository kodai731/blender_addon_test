# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Blender addon project that uses Rust for core functionality, compiled to a Python extension module via PyO3 and Maturin. The addon provides Rust-powered functionality to Blender through Python bindings.

## Architecture

**Hybrid Rust/Python Approach:**
- Rust core (`src/lib.rs`) implements performance-critical functionality using PyO3
- PyO3 exposes Rust functions to Python via the `blender_addon_core` module
- Maturin handles building Rust code into a Python wheel
- The wheel is installed directly into Blender's addon directory

**Build Flow:**
1. Rust code compiled to `cdylib` (C-compatible dynamic library)
2. Maturin packages it as a Python wheel
3. Wheel extracted and copied to Blender's addons folder (`%AppData%\Blender Foundation\Blender\4.0\scripts\addons`)

## Building and Development

**Build the addon:**
```bash
build.bat
```

This script:
- Kills any running Blender instances
- Builds release wheel with `maturin build --release`
- Installs wheel to temporary directory
- Copies `blender_addon_core` to Blender's addon directory
- Cleans up temporary files

**Manual build (development):**
```bash
# Build in debug mode
maturin build

# Build in release mode
maturin build --release

# Install locally for testing
pip install target/wheels/blender_addon_test-*.whl --force-reinstall
```

**Development workflow:**
1. Modify Rust code in `src/lib.rs`
2. Run `build.bat` to rebuild and deploy
3. Restart Blender to load the updated addon

## Key Configuration

**Cargo.toml:**
- Library name: `blender_addon_core` (must match PyModule name in `src/lib.rs`)
- Crate type: `cdylib` (required for Python extension modules)
- PyO3 dependency with `extension-module` feature

**pyproject.toml:**
- Uses Maturin as build backend
- Targets Python 3.8+
- Extension module configuration via `tool.maturin`

## Project Structure

- `src/lib.rs` - Rust core with PyO3 bindings
- `build.bat` - Windows build/deployment script
- `target/` - Rust build artifacts (gitignored)
- `scenes/` - Blender scene files for testing addon functionality
- `.venv/` - Python virtual environment (gitignored)

## Working with PyO3

**Adding Python functions:**
Use `#[pyfunction]` macro and register in the module:
```rust
#[pyfunction]
fn my_function(arg: Type) -> PyResult<ReturnType> {
    // implementation
}

#[pymodule]
fn blender_addon_core(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(my_function, m)?)?;
    Ok(())
}
```

**Important:** The module name in `#[pymodule]` must match the library name in Cargo.toml (`blender_addon_core`).

## 重要
* 回答は日本語で行ってください
* コミットは行わないでください