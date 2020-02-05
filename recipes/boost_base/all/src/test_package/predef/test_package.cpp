#include <cstdlib>
#include <iostream>
#include <boost/predef.h>

int main()
{
    std::cout << "architecture: ";
#if BOOST_ARCH_ARM
    std::cout << "ARM" << std::endl;
#endif
#if BOOST_ARCH_X86_32
    std::cout << "x86" << std::endl;
#endif
#if BOOST_ARCH_X86_64
    std::cout << "x64" << std::endl;
#endif
    std::cout << "compiler: ";
#if BOOST_COMP_CLANG
    std::cout << "Clang" << std::endl;
#endif
#if BOOST_COMP_GNUC
    std::cout << "GCC" << std::endl;
#endif
#if BOOST_COMP_MSVC
    std::cout << "MSVC" << std::endl;
#endif
    std::cout << "os: ";
#if BOOST_OS_ANDROID
    std::cout << "Android" << std::endl;
#endif
#if BOOST_OS_IOS
    std::cout << "iOS" << std::endl;
#endif
#if BOOST_OS_LINUX
    std::cout << "Linux" << std::endl;
#endif
#if BOOST_OS_MACOS
    std::cout << "macOS" << std::endl;
#endif
#if BOOST_OS_WINDOWS
    std::cout << "Windows" << std::endl;
#endif
    return EXIT_SUCCESS;
}
