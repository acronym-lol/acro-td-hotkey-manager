"""
AcroHotkeyManager - Central hotkey management for TouchDesigner components.

Provides a simple API for components to register hotkey combinations that
trigger callbacks. Handles keyboard input, modifier tracking, and conflict
resolution.

Usage:
    # Register a hotkey
    op.HotkeyManager.Register('ctrl+alt+shift+n', myComp.MyMethod,
                               description='Open Component Creator')

    # Unregister
    op.HotkeyManager.Unregister('ctrl+alt+shift+n')

    # List all bindings
    print(op.HotkeyManager.Bindings)
"""
from json import loads, dumps
import traceback

from CallbacksExt import CallbacksExt
from AcroVersionExt import AcroVersionExt
from TDStoreTools import StorageManager

TDF = op.TDModules.mod.TDFunctions


class AcroHotkeyManager(CallbacksExt, AcroVersionExt):
    """
    Central hotkey manager that allows components to register keyboard shortcuts.
    """

    # Valid modifier keys
    MODIFIERS = {'ctrl', 'alt', 'shift'}

    def __init__(self, ownerComp):
        self.ownerComp = ownerComp

        # Initialize callbacks
        self.callbackDat = self.ownerComp.par.Callbackdat.eval()
        try:
            CallbacksExt.__init__(self, ownerComp)
        except:
            self.ownerComp.addScriptError(traceback.format_exc() +
                    "Error in CallbacksExt __init__. See textport.")
            print()
            print("Error initializing callbacks - " + self.ownerComp.path)
            print(traceback.format_exc())

        # Run onInit callback
        try:
            self.DoCallback('onInit', {'ownerComp': self.ownerComp})
        except:
            self.ownerComp.addScriptError(traceback.format_exc() +
                    "Error in custom onInit callback. See textport.")
            print(traceback.format_exc())

        # Storage for modifier state
        self.dataComp = ownerComp.op('data')
        storedItems = [
            {'name': 'Modifiers', 'default': {'ctrl': False, 'alt': False, 'shift': False},
             'readOnly': False, 'property': True, 'dependable': True},
        ]
        self.stored = StorageManager(self, self.dataComp, storedItems)

        # Initialize version tracking
        AcroVersionExt.__init__(self, ownerComp)

        # In-memory bindings registry (not persisted - components re-register on load)
        self._bindings = {}

        # register hotkey for print help ctrl+alt+shift+h
        self.Register('ctrl+alt+shift+h', self.PrintHelp, description='Print registered hotkeys to textport')

    # =========================================================================
    # PUBLIC PROPERTIES
    # =========================================================================

    @property
    def Bindings(self) -> dict:
        """Get all registered hotkey bindings."""
        return self._bindings.copy()

    @property
    def Modifiers(self) -> dict:
        """Get current modifier state {'ctrl': bool, 'alt': bool, 'shift': bool}."""
        return self.stored['Modifiers']

    # =========================================================================
    # PUBLIC METHODS
    # =========================================================================

    def Register(self, hotkey: str, callback: callable,
                 description: str = '', force: bool = True) -> bool:
        """
        Register a hotkey binding.

        Args:
            hotkey: Key combination string (e.g., 'ctrl+alt+shift+n')
            callback: Function to call when hotkey is pressed
            description: Human-readable description for help
            force: If True, overwrite existing binding

        Returns:
            True if registered, False if conflict (and force=False)
        """
        key = self._normalizeHotkey(hotkey)

        if key in self._bindings and not force:
            existing = self._bindings[key]
            debug(f"HotkeyManager: Warning - '{hotkey}' already bound to {existing['owner']}")
            return False

        # Determine owner path from callback
        owner = None
        if hasattr(callback, '__self__'):
            obj = callback.__self__
            if hasattr(obj, 'ownerComp'):
                owner = obj.ownerComp.path

        self._bindings[key] = {
            'callback': callback,
            'description': description,
            'owner': owner,
            'enabled': True
        }

        # debug(f"HotkeyManager: Registered '{hotkey}' -> {description or callback.__name__}")
        return True

    def Unregister(self, hotkey: str) -> bool:
        """
        Remove a hotkey binding.

        Args:
            hotkey: Key combination string to unregister

        Returns:
            True if unregistered, False if not found
        """
        key = self._normalizeHotkey(hotkey)

        if key not in self._bindings:
            return False

        del self._bindings[key]
        # debug(f"HotkeyManager: Unregistered '{hotkey}'")
        return True

    def UnregisterOwner(self, owner_path: str) -> int:
        """
        Remove all hotkeys registered by a specific component.

        Args:
            owner_path: Component path (e.g., '/ComponentCreator')

        Returns:
            Number of bindings removed
        """
        to_remove = [key for key, binding in self._bindings.items()
                     if binding['owner'] == owner_path]

        for key in to_remove:
            del self._bindings[key]

        if to_remove:
            print(f"HotkeyManager: Unregistered {len(to_remove)} hotkey(s) from {owner_path}")

        return len(to_remove)

    def SetEnabled(self, hotkey: str, enabled: bool) -> bool:
        """
        Enable or disable a hotkey without removing it.

        Args:
            hotkey: Key combination string
            enabled: True to enable, False to disable

        Returns:
            True if found and updated, False if not found
        """
        key = self._normalizeHotkey(hotkey)

        if key not in self._bindings:
            return False

        self._bindings[key]['enabled'] = enabled
        status = "enabled" if enabled else "disabled"
        print(f"HotkeyManager: {hotkey} {status}")
        return True

    def PrintHelp(self):
        """Print all registered hotkeys to textport."""
        print("=" * 60)
        version_str = self.VersionString
        print(f"AcroHotkeyManager - {version_str}")
        print("REGISTERED HOTKEYS")

        if not self._bindings:
            print("No hotkeys registered.")
        else:
            for key, binding in sorted(self._bindings.items()):
                status = "" if binding['enabled'] else " [disabled]"
                owner = binding['owner'] or "unknown"
                desc = binding['description'] or binding['callback'].__name__
                # Format the key for display
                display_key = key.replace('+', ' + ').upper()
                print(f"  {display_key}{status}")
                print(f"    {desc}")
                print(f"    Owner: {owner}")
                print()

        print("=" * 60)

    # =========================================================================
    # KEYBOARD HANDLING (called from keyboard_callbacks DAT)
    # =========================================================================

    def UpdateModifiers(self, ctrl: bool, alt: bool, shift: bool):
        """Update the current modifier state. Called on every key event."""
        self.stored['Modifiers'] = {
            'ctrl': ctrl,
            'alt': alt,
            'shift': shift
        }

    def HandleKeyPress(self, key: str, ctrl: bool, alt: bool, shift: bool):
        """
        Handle a key press event and dispatch to registered callback if matched.

        Args:
            key: The key that was pressed (e.g., 'n', 'f1')
            ctrl: True if Ctrl is held
            alt: True if Alt is held
            shift: True if Shift is held
        """
        # Build the normalized hotkey string for this event
        hotkey = self._buildHotkeyFromEvent(key, ctrl, alt, shift)

        if hotkey in self._bindings:
            binding = self._bindings[hotkey]
            if binding['enabled']:
                self._executeCallback(hotkey, binding)

    # =========================================================================
    # INTERNAL METHODS
    # =========================================================================

    def _normalizeHotkey(self, hotkey: str) -> str:
        """
        Normalize hotkey string to canonical form.
        'Ctrl+Alt+N' -> 'alt+ctrl+n' (sorted modifiers + key, lowercase)
        """
        parts = [p.strip().lower() for p in hotkey.split('+')]

        # Separate modifiers from the key
        modifiers = sorted([p for p in parts if p in self.MODIFIERS])
        keys = [p for p in parts if p not in self.MODIFIERS]

        if not keys:
            raise ValueError(f"Hotkey '{hotkey}' must include a non-modifier key")

        if len(keys) > 1:
            raise ValueError(f"Hotkey '{hotkey}' has multiple non-modifier keys: {keys}")

        # Return normalized form: sorted modifiers + key
        return '+'.join(modifiers + keys)

    def _buildHotkeyFromEvent(self, key: str, ctrl: bool, alt: bool, shift: bool) -> str:
        """Build a normalized hotkey string from a key event."""
        parts = []
        if alt:
            parts.append('alt')
        if ctrl:
            parts.append('ctrl')
        if shift:
            parts.append('shift')
        parts.append(key.lower())
        return '+'.join(parts)

    def _executeCallback(self, hotkey: str, binding: dict):
        """Execute the callback for a hotkey binding with error handling."""
        try:
            self.DoCallback('onBeforeHotkey', {
                'hotkey': hotkey,
                'binding': binding
            })

            binding['callback']()

            self.DoCallback('onAfterHotkey', {
                'hotkey': hotkey,
                'binding': binding
            })
        except Exception as e:
            print(f"HotkeyManager: Error executing callback for '{hotkey}': {e}")
            print(traceback.format_exc())

    def onStart(self):
        run(self.PrintHelp, delayFrames=1)

    # =========================================================================
    # PULSE HANDLERS
    # =========================================================================

    def pulse_Editextension(self):
        """Pulse handler for Edit Extension button."""
        self.ownerComp.op('AcroHotkeyManager').par.edit.pulse()

    def pulse_Printmappings(self):
        """Pulse handler for Print Help button."""
        self.PrintHelp()
