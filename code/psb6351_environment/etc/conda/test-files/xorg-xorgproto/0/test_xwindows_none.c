#include <X11/X.h>
#include <X11/Xwindows.h>

#ifndef None
#error "Xwindows.h did not restore the X11 None macro"
#endif

#if None != 0L
#error "Xwindows.h changed the value of the X11 None macro"
#endif

int xorgproto_xwindows_none_probe(void)
{
    return None == 0L ? 0 : 1;
}
