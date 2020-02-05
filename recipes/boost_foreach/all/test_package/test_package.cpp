#include <cstdlib>
#include <iostream>
#include <string>
#include <boost/foreach.hpp>

int main()
{
    std::string hello("boost foreach\n");
    BOOST_FOREACH(char c, hello) {
        std::cout << c;
    }
    return EXIT_SUCCESS;
}
