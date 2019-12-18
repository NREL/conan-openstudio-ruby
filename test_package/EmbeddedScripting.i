%module EmbeddedScripting

#define UTILITIES_API

%include <std_string.i>

#ifdef SWIGRUBY
%begin %{
// this must be included early because ruby.h 2.0.0  breaks Qt
//#include <QByteArray>
//#include <QString>

// xkeycheck.h emits warning 4505 if any C++ keyword is redefined, ruby.h does redefine many keywords
// for some reason our undefs below are not sufficient to avoid this warning
// Qt headers QByteArray and QString (now removed) included some workaround for this which I did not find
// we can use #define _ALLOW_KEYWORD_MACROS 1
// other option is to patch ruby.h and config.h to remove keyword redefinitions (e.g. #define inline __inline)
#ifdef _MSC_VER
  #define _ALLOW_KEYWORD_MACROS 1
#endif

%}

%header %{
// Must undo more of the damage caused by ruby/win32.h 2.0.0
#ifdef access
#undef access
#endif

#ifdef truncate
#undef truncate
#endif

#ifdef inline
#undef inline
#endif
%}

#endif

%include <embedded_files.hxx>
%include "EmbeddedHelp.hpp"


%{
#include <embedded_files.hxx>
#include "EmbeddedHelp.hpp"

%}


