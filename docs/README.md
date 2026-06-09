# Acro TD Hotkey Manager

Central keyboard-shortcut registry for TouchDesigner components.

## What it does

`AcroHotkeyManager` (`/AcroHotkeyManager`, global shortcut `op.AHM`, extension `ext.AcroHotkeyManager`) lets any component register hotkey combinations that trigger callbacks. The manager owns keyboard input, modifier-state tracking, and conflict resolution; components register what they need and the manager dispatches.

## Quick start

```python
# Register a hotkey
op.AHM.Register(
    'ctrl+alt+shift+n',
    op.ACC.OpenCreateDialog,
    description='Open Component Creator'
)

# Inspect what's registered
op.AHM.Bindings   # → dict of {normalized_hotkey: {callback, description, owner, enabled}}

# Inspect current modifier state
op.AHM.Modifiers  # → {'ctrl': bool, 'alt': bool, 'shift': bool}

# Unregister
op.AHM.Unregister('ctrl+alt+shift+n')

# Disable without removing
op.AHM.SetEnabled('ctrl+alt+shift+n', False)

# Print all bound hotkeys + their descriptions
op.AHM.PrintHelp()
```

The manager itself reserves **`Ctrl+Alt+Shift+H`** to call `PrintHelp()` so you can always see what's currently bound from inside TD.

## Hotkey string format

- **Case-insensitive** — `'Ctrl+Alt+N'` ≡ `'ctrl+alt+n'`
- **Order-insensitive** — `'alt+ctrl+n'` ≡ `'ctrl+alt+n'`
- **Modifiers** — `ctrl`, `alt`, `shift`
- **Keys** — single chars (`n`, `s`) or special keys (`f1`, `space`, `enter`, `esc`, `tab`)
- Exactly one non-modifier key required per binding

The manager normalizes the string internally so equivalent forms map to the same registration.

## Registration patterns

Components typically register their hotkeys in `__init__`:

```python
class MyComponent(CallbacksExt, AcroVersionExt):
    def __init__(self, ownerComp):
        # ... existing init ...
        self._registerHotkeys()

    def _registerHotkeys(self):
        if op.AHM:
            op.AHM.Register('ctrl+alt+m', self.MyMethod,
                            description='Do something')
```

Wrapping the call in `if op.AHM:` keeps the component usable in projects that don't ship the hotkey manager.

## Conflict handling

- **First-registered wins** — a duplicate registration is rejected with a warning unless `force=True` is passed.
- The `owner` field on each binding records the path of the registering component, so `UnregisterOwner('/path/to/comp')` can clean up everything a component owns in one call (useful before reloading an extension).

## Where to go next

- **[API Reference](api)** — Full method signatures (Register/Unregister/SetEnabled/HandleKeyPress/UpdateModifiers), callback shapes, the `MODIFIERS` constant, internal hotkey normalization rules.

## Installation

```bash
git subtree add --prefix=modules/acro-td-hotkey-manager https://github.com/acronym-lol/acro-td-hotkey-manager.git main --squash
```

`setup.ps1` / `setup.sh` register `ACRO_TD_HOTKEY_MANAGER` pointing at the module on disk.
