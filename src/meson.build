pkgdatadir = get_option('prefix') / get_option('datadir') / meson.project_name()
moduledir = pkgdatadir / 'gtk_ollama'
gnome = import('gnome')

gnome.compile_resources('gtk_ollama',
  'gtk_ollama.gresource.xml',
  gresource_bundle: true,
  install: true,
  install_dir: pkgdatadir,
)

python = import('python')

conf = configuration_data()
conf.set('PYTHON', python.find_installation('python3').full_path())
conf.set('VERSION', meson.project_version())
conf.set('localedir', get_option('prefix') / get_option('localedir'))
conf.set('pkgdatadir', pkgdatadir)

configure_file(
  input: 'gtk_ollama.in',
  output: 'gtk_ollama',
  configuration: conf,
  install: true,
  install_dir: get_option('bindir'),
  install_mode: 'r-xr-xr-x'
)

gtk_ollama_sources = [
  '__init__.py',
  'main.py',
  'window.py',
  'ollama_tools/ollama_client.py',
  'ollama_tools/ollama_model.py',
  'ollama_tools/ollama_get_models.py',
  'gtk/help_overlay/help_overlay.py',
  'widgets/message_widget.py',
  'utils/voice_recognizer.py'
]

install_data(gtk_ollama_sources, install_dir: moduledir)
