#include <cstdlib>
#include <iostream>
#include <string>
#include <ios>
#include <boost/crc.hpp>

int main()
{
    std::string s("bincrafters");
    boost::crc_32_type crc32;
    crc32.process_bytes(s.c_str(), s.size());
    std::cout << "CRC32 of " << s << " is: " << std::hex << "0x" << crc32.checksum() << std::endl;
    return EXIT_SUCCESS;
}
