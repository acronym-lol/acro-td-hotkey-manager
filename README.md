# Acro TD Hotkey Manager

[![Docs](https://img.shields.io/badge/docs-GitHub%20Pages-blue)](https://acronym-lol.github.io/acro-td-hotkey-manager/)

Central hotkey management for TouchDesigner components.

**Documentation:** https://acronym-lol.github.io/acro-td-hotkey-manager/

## Features

- Simple API for registering hotkey combinations
- Modifier state tracking (ctrl, alt, shift)
- Conflict handling — replace by default, or defer to existing bindings with `force=False`
- Enable/disable hotkeys without removing them

## Usage

```python
# Register a hotkey
op.HotkeyManager.Register('ctrl+alt+shift+n', myCallback,
                          description='Do something')

# Unregister
op.HotkeyManager.Unregister('ctrl+alt+shift+n')

# Get all bindings
op.HotkeyManager.Bindings

# Get modifier state
op.HotkeyManager.Modifiers  # {'ctrl': bool, 'alt': bool, 'shift': bool}

# Print help
op.HotkeyManager.PrintHelp()
```

## Hotkey Format

- Case-insensitive: `'Ctrl+Alt+N'` = `'ctrl+alt+n'`
- Order-insensitive: `'alt+ctrl+n'` = `'ctrl+alt+n'`
- Modifiers: `ctrl`, `alt`, `shift`
- Keys: single characters or special keys (`f1`, `space`, `enter`, etc.)

## Installation

This module is typically installed as a git subtree in the acro-td-core template.

```bash
git subtree add --prefix=modules/acro-td-hotkey-manager https://github.com/acronym-lol/acro-td-hotkey-manager.git main --squash
```
