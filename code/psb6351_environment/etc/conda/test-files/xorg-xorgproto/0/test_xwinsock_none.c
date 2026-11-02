#define _WILLWINSOCK_
#include <X11/Xos.h>
#include <X11/X.h>
#include <X11/Xmd.h>
#include <X11/Xwinsock.h>

#ifndef None
#error "Xwinsock.h did not restore the X11 None macro"
#endif

#if None != 0L
#error "Xwinsock.h changed the value of the X11 None macro"
#endif

int xorgproto_xwinsock_none_probe(void)
{
    return None == 0L ? 0 : 1;
}
