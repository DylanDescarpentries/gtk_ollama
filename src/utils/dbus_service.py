# dbus_service.py - À ajouter dans votre projet GTK
import gi
gi.require_version('Gio', '2.0')
from gi.repository import Gio, GLib

class ChatAssistantDBusService:
    """Service D-Bus pour contrôler l'application depuis l'extension"""
    
    INTERFACE_NAME = 'org.descarpentries.gtk_ollama.Control'
    OBJECT_PATH = '/org/descarpentries/gtk_ollama/Control'
    
    # XML de définition de l'interface D-Bus
    INTERFACE_XML = '''
    <node>
        <interface name='org.descarpentries.gtk_ollama.Control'>
            <method name='ToggleWindow'>
                <arg type='b' name='is_visible' direction='out'/>
            </method>
            <method name='ShowWindow'>
            </method>
            <method name='HideWindow'>
            </method>
            <method name='IsWindowVisible'>
                <arg type='b' name='visible' direction='out'/>
            </method>
            <method name='GetStatus'>
                <arg type='s' name='status' direction='out'/>
            </method>
            <signal name='WindowStateChanged'>
                <arg type='b' name='visible'/>
            </signal>
        </interface>
    </node>
    '''
    
    def __init__(self, application):
        self.application = application
        self.connection = None
        self.registration_id = None
        
        # Enregistrer le service D-Bus
        self._setup_dbus()
    
    def _setup_dbus(self):
        """Configuration du service D-Bus"""
        try:
            # Obtenir la connexion au bus de session
            self.connection = Gio.bus_get_sync(Gio.BusType.SESSION, None)
            
            # Créer l'interface depuis le XML
            introspection = Gio.DBusNodeInfo.new_for_xml(self.INTERFACE_XML)
            interface = introspection.interfaces[0]
            
            # Enregistrer l'objet D-Bus
            self.registration_id = self.connection.register_object(
                self.OBJECT_PATH,
                interface,
                self._handle_method_call,
                None,  # get_property
                None   # set_property
            )
            
            # Acquérir le nom sur le bus
            self.connection.call_sync(
                'org.freedesktop.DBus',
                '/org/freedesktop/DBus',
                'org.freedesktop.DBus',
                'RequestName',
                GLib.Variant('(su)', ('org.descarpentries.gtk_ollama', 0)),
                GLib.VariantType('(u)'),
                Gio.DBusCallFlags.NONE,
                -1,
                None
            )
            
            print("Service D-Bus enregistré avec succès")
            
        except Exception as e:
            print(f"Erreur lors de la configuration D-Bus: {e}")
    
    def _handle_method_call(self, connection, sender, object_path, interface_name, method_name, parameters, invocation):
        """Gestionnaire des appels de méthodes D-Bus"""
        try:
            if method_name == 'ToggleWindow':
                is_visible = self._toggle_window()
                invocation.return_value(GLib.Variant('(b)', (is_visible,)))
                
            elif method_name == 'ShowWindow':
                self._show_window()
                invocation.return_value(None)
                
            elif method_name == 'HideWindow':
                self._hide_window()
                invocation.return_value(None)
                
            elif method_name == 'IsWindowVisible':
                is_visible = self._is_window_visible()
                invocation.return_value(GLib.Variant('(b)', (is_visible,)))
                
            elif method_name == 'GetStatus':
                status = self._get_status()
                invocation.return_value(GLib.Variant('(s)', (status,)))
                
            else:
                invocation.return_error_literal(
                    Gio.dbus_error_quark(),
                    Gio.DBusError.UNKNOWN_METHOD,
                    f"Méthode inconnue: {method_name}"
                )
                
        except Exception as e:
            invocation.return_error_literal(
                Gio.dbus_error_quark(),
                Gio.DBusError.FAILED,
                f"Erreur lors de l'exécution: {str(e)}"
            )
    
    def _toggle_window(self):
        """Toggle la visibilité de la fenêtre"""
        window = self.application.props.active_window
        if window:
            if window.get_visible():
                window.hide()
                self._emit_window_state_changed(False)
                return False
            else:
                window.present()
                self._emit_window_state_changed(True)
                return True
        return False
    
    def _show_window(self):
        """Affiche la fenêtre"""
        window = self.application.props.active_window
        if window:
            window.present()
            self._emit_window_state_changed(True)
    
    def _hide_window(self):
        """Cache la fenêtre"""
        window = self.application.props.active_window
        if window:
            window.hide()
            self._emit_window_state_changed(False)
    
    def _is_window_visible(self):
        """Vérifie si la fenêtre est visible"""
        window = self.application.props.active_window
        return window.get_visible() if window else False
    
    def _get_status(self):
        """Retourne le statut de l'application"""
        window = self.application.props.active_window
        if window:
            return "Actif" if window.get_visible() else "Caché"
        return "Inactif"
    
    def _emit_window_state_changed(self, visible):
        """Émet le signal de changement d'état de la fenêtre"""
        if self.connection:
            try:
                self.connection.emit_signal(
                    None,  # destination
                    self.OBJECT_PATH,
                    self.INTERFACE_NAME,
                    'WindowStateChanged',
                    GLib.Variant('(b)', (visible,))
                )
            except Exception as e:
                print(f"Erreur lors de l'émission du signal: {e}")
    
    def cleanup(self):
        """Nettoie les ressources D-Bus"""
        if self.connection and self.registration_id:
            self.connection.unregister_object(self.registration_id)
            print("Service D-Bus désenregistré")