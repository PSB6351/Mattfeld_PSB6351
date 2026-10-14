# When cross-compiling, or installing for a different platform, the commands
# can't be executed. So we catch errors and print a message instead of failing.
{ # try block
    "${PREFIX}/bin/glib-compile-schemas" "${PREFIX}/share/glib-2.0/schemas" 2>>"${PREFIX}/.messages.txt" &&
    "${PREFIX}/bin/gtk-update-icon-cache" -f -t -q "${PREFIX}/share/icons/hicolor" 2>>"${PREFIX}/.messages.txt" &&
    "${PREFIX}/bin/gtk-query-immodules-3.0" --update-cache 2>>"${PREFIX}/.messages.txt"
} ||
{ # catch block
    echo "ERROR: Failed to complete gtk3's post-link script."
    echo "To fix this, activate the environment and run:"
    echo "    glib-compile-schemas \"${PREFIX}/share/glib-2.0/schemas\""
    echo "    gtk-update-icon-cache -f -t \"${PREFIX}/share/icons/hicolor\""
    echo "    gtk-query-immodules-3.0 --update-cache"
} >> "${PREFIX}/.messages.txt"
