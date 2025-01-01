project('gtk_ollama',
    version: '0.1.0',
    meson_version: '>= 1.0.0',
    default_options: ['warning_level=2', 'werror=false'],
)

i18n = import('i18n')
gnome = import('gnome')

# Find pytest as an external program
pytest = find_program('pytest', required: true)

# Unit test using pytest as external program
test(
    'unit_tests',
    pytest,
    args: [
        '-v',
        join_paths(meson.project_source_root(), 'tests', 'test_message_widget.py'),
        join_paths(meson.project_source_root(), 'tests', 'test_main.py'),
        join_paths(meson.project_source_root(), 'tests', 'test_ollama_client.py')
    ],
)

subdir('data')
subdir('src')
subdir('po')

gnome.post_install(
    glib_compile_schemas: true,
    gtk_update_icon_cache: true,
    update_desktop_database: true,
)