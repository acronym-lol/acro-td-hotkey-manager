---
last_reviewed: 2026-08-27
---

# AcroHotkeyManager — Central Hotkey Management

## Overview

`AcroHotkeyManager` provides a centralized keyboard-shortcut registry for TouchDesigner projects. Components register hotkey combinations against callbacks, and the manager dispatches calls when keys are pressed. Bindings live in memory and are re-registered by each component on extension init — there is no persistent serialization to manage.

The manager component lives at `/AcroHotkeyManager` and is exposed as the global shortcut `op.AHM`. It inherits from `CallbacksExt` and `AcroVersionExt`, so it carries the standard Component / Version parameter pages and is discoverable via the `tox_managed` and `version_tracking` tags.

---

## Hotkey String Format

Hotkey strings are normalized before storage, so the following are equivalent:

| Input | Normalized |
|-------|------------|
| `'Ctrl+Alt+N'` | `'alt+ctrl+n'` |
| `'alt+ctrl+n'` | `'alt+ctrl+n'` |
| `'CTRL+SHIFT+H'` | `'ctrl+shift+h'` |

**Rules:**

- **Case-insensitive** — `Ctrl` and `ctrl` are equivalent.
- **Order-insensitive** — modifiers are sorted alphabetically during normalization.
- **Modifiers** — `ctrl`, `alt`, `shift`. Anything else is treated as the key.
- **Exactly one non-modifier key** is required. `'ctrl+alt'` raises `ValueError`.
- **Multiple non-modifier keys** are not allowed. `'ctrl+a+b'` raises `ValueError`.
- **Special keys** — single characters (`n`, `s`) or named keys (`f1`, `space`, `enter`, `esc`, `tab`).

---

## API Reference

### Properties

| Property | Type | Description |
|----------|------|-------------|
| `Bindings` | `dict` | Copy of all registered hotkeys keyed by their normalized form. Each value is a `dict` with `callback`, `description`, `owner`, and `enabled`. |
| `Modifiers` | `dict` | Current modifier state — `{'ctrl': bool, 'alt': bool, 'shift': bool}`. |

### Methods

| Method | Arguments | Returns | Description |
|--------|-----------|---------|-------------|
| `Register(hotkey, callback, description='', force=True)` | `hotkey: str`, `callback: callable`, `description: str`, `force: bool` | `bool` | Register a hotkey binding. When `force=False`, returns `False` and prints a conflict warning if a binding already exists. Default `force=True` overwrites silently. |
| `Unregister(hotkey)` | `hotkey: str` | `bool` | Remove a single hotkey binding. Returns `False` if the hotkey was not registered. |
| `UnregisterOwner(owner_path)` | `owner_path: str` | `int` | Remove every hotkey whose `owner` matches the given path. Returns the count removed. Useful when a component is being destroyed. |
| `SetEnabled(hotkey, enabled)` | `hotkey: str`, `enabled: bool` | `bool` | Toggle a hotkey on/off without removing it. Disabled hotkeys are still tracked and can be re-enabled. |
| `PrintHelp()` | — | `None` | Print every registered hotkey, owner, and description to the textport, sorted alphabetically. |

### Callback Dispatch Methods

These are wired up from the manager's internal `keyboard_callbacks` DAT. You normally do not call them directly.

| Method | Arguments | Description |
|--------|-----------|-------------|
| `UpdateModifiers(ctrl, alt, shift)` | `bool, bool, bool` | Refresh the stored modifier state. Called on every key event. |
| `HandleKeyPress(key, ctrl, alt, shift)` | `str, bool, bool, bool` | Build a normalized hotkey from the event and dispatch the matching callback if one is registered and enabled. |

---

## Owner Tracking

When you register a hotkey from inside an extension, the manager attempts to record the owning component's path automatically. If the callback is a bound method (`self.MyMethod`), the manager inspects `callback.__self__.ownerComp.path` and stores it as the binding's `owner`. This is what makes `UnregisterOwner('/MyComponent')` work.

If the callback is a free function or a lambda, `owner` will be `None` and you'll have to track and unregister those bindings yourself.

---

## Built-in Hotkeys

The manager registers one hotkey for itself during `__init__`:

| Hotkey | Action |
|--------|--------|
| `ctrl+alt+shift+h` | `PrintHelp()` — print all registered hotkeys to the textport |

The AcroCore project component additionally registers:

| Hotkey | Action |
|--------|--------|
| `ctrl+alt+shift+u` | Toggle the AcroCore UI panel |
| `ctrl+alt+shift+t` | Toggle the TD timeline visibility |
| `ctrl+alt+shift+e` | Open the `tdPyEnvManager` CLI (only registered if `/tdPyEnvManager` exists) |

The ComponentCreator registers:

| Hotkey | Action |
|--------|--------|
| `ctrl+alt+shift+n` | Open the Component Creator dialog (when in a network editor pane) |

---

## Registering Hotkeys From Components

Register hotkeys during the component's extension `__init__`. Because bindings are not persisted, every load re-registers them.

```python
class MyComponent(CallbacksExt):
    def __init__(self, ownerComp):
        # ... existing init code ...
        self._registerHotkeys()

    def _registerHotkeys(self):
        if hasattr(op, 'AHM') and op.AHM:
            op.AHM.Register(
                'ctrl+alt+m', self.MyMethod,
                description='Do something useful'
            )
```

Always guard the call with `hasattr(op, 'AHM')`. The manager may not exist in projects derived from this template that have removed it, and components should fail soft.

---

## Conflict Handling

Two registrations targeting the same normalized hotkey behave according to the `force` argument:

| `force` | Behavior |
|---------|----------|
| `True` (default) | The new binding silently replaces the existing one. |
| `False` | The existing binding is kept. The manager prints a warning and `Register()` returns `False`. |

Use `force=False` when you want to defer to a previously-registered binding and surface the conflict to the user.

---

## Custom Callbacks

`AcroHotkeyManager` inherits from `CallbacksExt`, so it dispatches the standard lifecycle callbacks plus two hotkey-specific ones. Implement these in the manager's external `Callbackdat` to hook into every dispatch.

| Callback | Info Keys | Purpose |
|----------|-----------|---------|
| `onInit` | `ownerComp` | Fired during extension init. |
| `onBeforeHotkey` | `hotkey`, `binding` | Fired immediately before a callback is invoked. |
| `onAfterHotkey` | `hotkey`, `binding` | Fired immediately after a callback completes. |

Errors raised by user callbacks are caught and printed; they do not bubble up to the dispatch loop.

---

## Tag Discovery

Like every `AcroVersionExt` component, the manager carries both `tox_managed` and `version_tracking` tags. It is discoverable via `root.findChildren(tags=['version_tracking'])` and participates in the central version manager's update checks.
