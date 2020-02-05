#include <cstdlib>
#include <iostream>
#include <boost/lexical_cast.hpp>

int main()
{
    std::cout << "int 10 to string " << boost::lexical_cast<std::string>(10) << std::endl;
    std::cout << "string 10 to int " << boost::lexical_cast<int>("10") << std::endl;
    std::cout << "float 36.6 to string " << boost::lexical_cast<std::string>(36.6) << std::endl;
    std::cout << "string 36.6 to float " << boost::lexical_cast<float>("36.6") << std::endl;
    return EXIT_SUCCESS;
}
